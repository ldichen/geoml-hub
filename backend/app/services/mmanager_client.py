"""
mManager 客户端服务
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.container_registry import MManagerController
from app.models.service import ModelService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MManagerClient:
    """mManager 客户端"""

    def __init__(self, controller_url: str, api_key: str):
        self.controller_url = controller_url.rstrip("/")
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=180)

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """通用请求方法"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.request(
                    method,
                    f"{self.controller_url}{endpoint}",
                    headers=headers,
                    **kwargs,
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise Exception(
                            f"mManager API Error: {response.status} - {error_text}"
                        )

                    return await response.json()
        except asyncio.TimeoutError:
            raise Exception(f"请求 {self.controller_url} 超时")
        except aiohttp.ClientError as e:
            raise Exception(f"连接 {self.controller_url} 失败: {str(e)}")

    async def health_check(self) -> Dict:
        """健康检查"""
        return await self._request("GET", "/health")

    async def create_container(self, config: Dict) -> Dict:
        """创建容器"""
        return await self._request("POST", "/containers/", json=config)

    async def start_container(self, container_id: str) -> Dict:
        """启动容器"""
        return await self._request("POST", f"/containers/{container_id}/start")

    async def stop_container(self, container_id: str, timeout: int = 10) -> Dict:
        """停止容器"""
        return await self._request(
            "POST", f"/containers/{container_id}/stop", params={"timeout": timeout}
        )

    async def remove_container(self, container_id: str, force: bool = True) -> Dict:
        """删除容器"""
        return await self._request(
            "DELETE",
            f"/containers/{container_id}",
            params={"force": str(force).lower()},
        )

    async def get_container_info(self, container_id: str) -> Dict:
        """获取容器信息"""
        return await self._request("GET", f"/containers/{container_id}")

    async def get_container_stats(self, container_id: str) -> Dict:
        """获取容器统计信息"""
        return await self._request("GET", f"/containers/{container_id}/stats")

    async def get_container_logs(self, container_id: str, lines: int = 100) -> Dict:
        """获取容器日志"""
        return await self._request(
            "GET", f"/containers/{container_id}/logs", params={"lines": lines}
        )

    async def list_containers(self, all_containers: bool = False) -> Dict:
        """列出容器"""
        return await self._request(
            "GET", "/containers/", params={"all": str(all_containers).lower()}
        )


class MManagerControllerManager:
    """mManager 控制器管理器"""

    def __init__(self):
        self.controllers: Dict[str, MManagerClient] = {}
        self.health_check_interval = 30  # 秒
        self.last_health_check = {}

    async def initialize(self, db: AsyncSession):
        """初始化控制器管理器"""
        await self._load_controllers_from_config()
        await self._register_controllers_to_db(db)

        # 启动健康检查
        asyncio.create_task(self._periodic_health_check(db))

        logger.info(
            f"mManager控制器管理器初始化完成，已注册 {len(self.controllers)} 个控制器"
        )

    async def _load_controllers_from_config(self):
        """从配置加载控制器"""
        # 从配置文件或环境变量加载控制器列表
        controller_configs = getattr(settings, "mmanager_controllers", [])

        if not controller_configs:
            # 默认配置
            controller_configs = [
                {
                    "id": "mmanager-default",
                    "url": "http://localhost:8000",
                    "server_type": "cpu",
                    "enabled": True,
                }
            ]

        for config in controller_configs:
            if config.get("enabled", True):
                client = MManagerClient(
                    controller_url=config["url"],
                    api_key=getattr(
                        settings, "mmanager_api_key", "mmanager-default-key"
                    ),
                )
                self.controllers[config["id"]] = client
                logger.info(f"注册mManager控制器: {config['id']} -> {config['url']}")

    async def _register_controllers_to_db(self, db: AsyncSession):
        """将控制器注册到数据库，更新现有控制器信息，清理废弃控制器"""
        try:
            # 获取配置中的控制器ID列表
            config_controller_ids = set(self.controllers.keys())

            # 1. 获取数据库中所有控制器
            result = await db.execute(select(MManagerController))
            db_controllers = {c.controller_id: c for c in result.scalars()}
            db_controller_ids = set(db_controllers.keys())

            # 2. 清理废弃的控制器（配置中没有但数据库中存在的）
            deprecated_ids = db_controller_ids - config_controller_ids
            if deprecated_ids:
                logger.info(f"清理废弃的控制器: {list(deprecated_ids)}")
                await db.execute(
                    delete(MManagerController).where(
                        MManagerController.controller_id.in_(deprecated_ids)
                    )
                )

                # 容器信息现在直接存储在 ModelService 中，无需单独清理

            # 3. 注册或更新配置中的控制器
            for controller_id, client in self.controllers.items():
                existing = db_controllers.get(controller_id)

                if existing:
                    # 更新现有控制器的URL和其他信息
                    if existing.controller_url != client.controller_url:
                        logger.info(
                            f"更新控制器 {controller_id} 的URL: {existing.controller_url} -> {client.controller_url}"
                        )
                        existing.controller_url = client.controller_url
                        existing.updated_at = func.now()
                        existing.status = "unknown"  # 重置状态，等待健康检查
                else:
                    # 创建新控制器记录
                    controller = MManagerController(
                        controller_id=controller_id,
                        controller_url=client.controller_url,
                        server_type="unknown",  # 稍后通过健康检查获取
                        status="unknown",
                    )
                    db.add(controller)
                    logger.info(f"将新控制器 {controller_id} 注册到数据库")

            await db.commit()
            logger.info(
                f"控制器同步完成，活跃控制器: {len(config_controller_ids)}, 清理废弃控制器: {len(deprecated_ids)}"
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"控制器注册和同步失败: {e}")
            raise

    async def get_healthy_controllers(self, db: AsyncSession) -> List[Dict]:
        """获取健康的控制器列表"""
        result = await db.execute(
            select(MManagerController).where(
                and_(
                    MManagerController.status == "healthy",
                    MManagerController.enabled == True,
                )
            )
        )

        controllers = []
        for controller in result.scalars():
            if controller.controller_id in self.controllers:
                controllers.append(
                    {
                        "id": controller.controller_id,
                        "url": controller.controller_url,
                        "server_type": controller.server_type,
                        "load_percentage": controller.load_percentage,
                        "capabilities": controller.capabilities,
                        "client": self.controllers[controller.controller_id],
                    }
                )

        return controllers

    def get_client(self, controller_id: str) -> MManagerClient:
        """获取指定控制器的客户端"""
        if controller_id not in self.controllers:
            raise ValueError(f"控制器 {controller_id} 不存在")

        return self.controllers[controller_id]

    async def select_optimal_controller(
        self, db: AsyncSession, requirements: Dict = None
    ) -> Dict:
        """选择最优控制器"""
        healthy_controllers = await self.get_healthy_controllers(db)

        if not healthy_controllers:
            raise Exception("没有可用的健康控制器")

        # 根据需求筛选控制器
        suitable_controllers = []

        for controller in healthy_controllers:
            capabilities = controller.get("capabilities", {})

            # 检查GPU需求
            if requirements and requirements.get("gpu_required", False):
                if not capabilities.get("gpu_support", False):
                    continue

            # 检查内存需求
            if requirements and requirements.get("memory_gb", 0) > 0:
                required_memory = requirements["memory_gb"]
                max_memory = capabilities.get("max_memory_gb", 0)
                if required_memory > max_memory:
                    continue

            # 检查负载
            if controller["load_percentage"] >= 90:  # 负载过高
                continue

            suitable_controllers.append(controller)

        if not suitable_controllers:
            # 如果没有完全匹配的，选择负载最低的
            suitable_controllers = healthy_controllers

        # 选择负载最低的控制器
        best_controller = min(suitable_controllers, key=lambda x: x["load_percentage"])

        return best_controller

    async def find_container_location(
        self, db: AsyncSession, container_id: str
    ) -> Optional[Dict]:
        """查找容器位置"""
        logger.info(f"查找容器位置: {container_id}")

        # 从 ModelService 表查找容器信息
        result = await db.execute(
            select(ModelService).where(ModelService.container_id == container_id)
        )
        service = result.scalar_one_or_none()

        if service:
            logger.info(f"在数据库中找到服务记录，model_ip: {service.model_ip}")
        else:
            logger.warning(f"数据库中未找到容器 {container_id} 的服务记录")

        # Get list of controller IPs for debugging
        controller_ips = [
            client.controller_url.split("://")[1].split(":")[0]
            for client in self.controllers.values()
            if "://" in client.controller_url
        ]
        logger.info(f"可用的控制器IPs: {controller_ips}")

        if service and service.model_ip in controller_ips:
            controller_id = next(
                (
                    cid
                    for cid, client in self.controllers.items()
                    if "://" in client.controller_url
                    and service.model_ip
                    == client.controller_url.split("://")[1].split(":")[0]
                ),
                None,
            )
            if controller_id:
                return {
                    "controller_id": controller_id,
                    "client": self.controllers[controller_id],
                    "service": service,
                }
        # 如果 ModelService 中没有，广播查询所有控制器
        logger.info(
            f"数据库匹配失败，开始广播查询所有控制器: {list(self.controllers.keys())}"
        )

        for controller_id, client in self.controllers.items():
            try:
                logger.debug(f"查询控制器 {controller_id} 是否有容器 {container_id}")
                container_info = await client.get_container_info(container_id)
                if container_info:
                    logger.warning(
                        f"在控制器 {controller_id} 发现未注册容器: {container_id}"
                    )
                    return {
                        "controller_id": controller_id,
                        "client": client,
                        "service": None,
                    }
            except Exception as e:
                logger.debug(f"控制器 {controller_id} 查询容器失败: {e}")
                continue

        logger.error(f"容器 {container_id} 在所有控制器中都未找到")
        return None  # 容器不存在

    async def _periodic_health_check(self, db: AsyncSession):
        """定期健康检查"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_all_controllers_health(db)
            except Exception as e:
                logger.error(f"定期健康检查失败: {e}")

    async def _check_all_controllers_health(self, db: AsyncSession):
        """检查所有配置中的控制器健康状态"""
        for controller_id, client in self.controllers.items():
            try:
                # 调用健康检查接口
                health_data = await client.health_check()

                # 更新数据库记录
                await db.execute(
                    update(MManagerController)
                    .where(MManagerController.controller_id == controller_id)
                    .values(
                        status="healthy",
                        last_check_at=func.now(),
                        health_data=health_data,
                        error_message=None,
                        consecutive_failures=0,
                        current_containers=health_data.get("containers", {}).get(
                            "running", 0
                        ),
                        max_containers=health_data.get("containers", {}).get(
                            "max_allowed", 100
                        ),
                        cpu_cores=health_data.get("resources", {}).get("cpu_cores"),
                        memory_total_gb=health_data.get("resources", {}).get(
                            "memory_total_gb"
                        ),
                        memory_available_gb=health_data.get("resources", {}).get(
                            "memory_available_gb"
                        ),
                        load_percentage=health_data.get("load_percentage", 0),
                        server_type=health_data.get("server_type", "unknown"),
                        capabilities=health_data.get("capabilities", {}),
                    )
                )

                self.last_health_check[controller_id] = datetime.now()

            except Exception as e:
                logger.warning(f"控制器 {controller_id} 健康检查失败: {e}")

                # 更新失败状态
                await db.execute(
                    update(MManagerController)
                    .where(MManagerController.controller_id == controller_id)
                    .values(
                        status="unhealthy",
                        last_check_at=func.now(),
                        error_message=str(e),
                        consecutive_failures=MManagerController.consecutive_failures
                        + 1,
                        total_failures=MManagerController.total_failures + 1,
                    )
                )

        await db.commit()

    async def sync_controllers(self, db: AsyncSession):
        """手动同步控制器配置"""
        logger.info("开始手动同步控制器配置...")

        # 重新加载配置
        await self._load_controllers_from_config()

        # 同步到数据库
        await self._register_controllers_to_db(db)

        # 立即执行一次健康检查
        await self._check_all_controllers_health(db)

        logger.info("控制器配置同步完成")

    async def get_controller_status(self, db: AsyncSession) -> Dict:
        """获取所有控制器状态概览"""
        result = await db.execute(select(MManagerController))
        controllers = result.scalars().all()

        status_summary = {
            "total": len(controllers),
            "healthy": len([c for c in controllers if c.status == "healthy"]),
            "unhealthy": len([c for c in controllers if c.status == "unhealthy"]),
            "unknown": len([c for c in controllers if c.status == "unknown"]),
            "controllers": [],
        }

        for controller in controllers:
            controller_info = {
                "id": controller.controller_id,
                "url": controller.controller_url,
                "status": controller.status,
                "server_type": controller.server_type,
                "last_check": (
                    controller.last_check_at.isoformat()
                    if controller.last_check_at
                    else None
                ),
                "current_containers": controller.current_containers,
                "max_containers": controller.max_containers,
                "load_percentage": controller.load_percentage,
                "enabled": controller.enabled,
                "consecutive_failures": controller.consecutive_failures,
            }
            status_summary["controllers"].append(controller_info)

        return status_summary

    # ================== 镜像管理方法 ==================

    async def pull_image(
        self, controller_id: str, image_name: str, auth_config: Optional[Dict] = None
    ) -> Dict:
        """在指定控制器上拉取镜像"""
        if controller_id not in self.controllers:
            raise Exception(f"控制器 {controller_id} 不存在")

        client = self.controllers[controller_id]

        pull_data = {"image": image_name, "auth": auth_config}

        result = await client._request("POST", "/images/pull", json=pull_data)
        logger.info(f"控制器 {controller_id} 拉取镜像 {image_name}: {result}")
        return result

    async def list_images(self, controller_id: str) -> List[Dict]:
        """列出控制器上的所有镜像"""
        if controller_id not in self.controllers:
            raise Exception(f"控制器 {controller_id} 不存在")

        client = self.controllers[controller_id]
        result = await client._request("GET", "/images/")
        return result.get("images", []) if result else []

    async def remove_image(
        self, controller_id: str, image_name: str, force: bool = False
    ) -> bool:
        """删除控制器上的镜像"""
        if controller_id not in self.controllers:
            raise Exception(f"控制器 {controller_id} 不存在")

        client = self.controllers[controller_id]

        try:
            params = {"force": str(force).lower()}
            # URL编码镜像名称，处理特殊字符
            import urllib.parse

            encoded_image_name = urllib.parse.quote(image_name, safe="")

            # Docker删除操作使用DEBUG级别，减少输出噪音
            logger.debug(f"开始删除镜像: {image_name} (控制器: {controller_id})")
            result = await client._request(
                "DELETE", f"/images/{encoded_image_name}", params=params
            )

            # 删除成功的详细信息也设为DEBUG
            if "Untagged" in str(result) or "Deleted" in str(result):
                logger.debug(f"Docker镜像删除详情: {result}")

            logger.info(f"控制器 {controller_id} 成功删除镜像 {image_name}")
            return True
        except Exception as e:
            logger.error(f"控制器 {controller_id} 删除镜像失败: {e}")
            return False

    async def get_image_info(
        self, controller_id: str, image_name: str
    ) -> Optional[Dict]:
        """获取镜像详细信息
        返回:
        - Dict: 镜像存在时返回镜像信息
        - None: 镜像不存在（正常业务状态）
        - 抛异常: 系统错误（网络、权限等问题）
        """
        if controller_id not in self.controllers:
            raise Exception(f"控制器 {controller_id} 不存在")

        client = self.controllers[controller_id]
        # URL编码镜像名称，处理特殊字符
        import urllib.parse

        encoded_image_name = urllib.parse.quote(image_name, safe="")

        try:
            result = await client._request("GET", f"/images/{encoded_image_name}")

            # 检查新的API响应格式
            if result and result.get("exists") == True:
                # 镜像存在，返回镜像信息
                return result
            elif result and result.get("exists") == False:
                # 镜像不存在，返回None（不是异常）
                return None

        except Exception as e:
            # 区分不同类型的错误
            error_msg = str(e).lower()
            if (
                "404" in error_msg
                or "not found" in error_msg
                or "no such image" in error_msg
                or "镜像不存在" in error_msg
            ):
                # 镜像不存在，返回None
                return None
            else:
                # 真正的系统错误，重新抛出
                raise Exception(f"查询镜像信息失败: {e}")

    async def clean_unused_images(self, controller_id: str) -> Dict:
        """清理未使用的镜像"""
        if controller_id not in self.controllers:
            raise Exception(f"控制器 {controller_id} 不存在")

        client = self.controllers[controller_id]
        result = await client._request("POST", "/images/prune")
        logger.info(f"控制器 {controller_id} 清理未使用镜像: {result}")
        return result

    async def ensure_image_available(
        self, controller_id: str, image_name: str, harbor_auth: Optional[Dict] = None
    ) -> bool:
        """确保镜像在控制器上可用，如不存在则拉取"""
        try:
            logger.info(f"开始检查镜像 {image_name} 在控制器 {controller_id} 上的状态")

            # 1. 检查镜像是否已存在
            image_info = await self.get_image_info(controller_id, image_name)

            if image_info:
                logger.info(f"镜像 {image_name} 已存在于控制器 {controller_id}")
                return True
            else:
                logger.info(
                    f"镜像 {image_name} 不存在，开始拉取到控制器 {controller_id}"
                )

            # 2. 镜像不存在，尝试拉取
            pull_result = await self.pull_image(controller_id, image_name, harbor_auth)

            # 3. 验证拉取是否成功
            if pull_result.get("status") == "success":
                logger.info(f"镜像 {image_name} 成功拉取到控制器 {controller_id}")

                # 4. 拉取成功后，等待一小段时间，然后再次验证
                import asyncio

                await asyncio.sleep(1)

                verify_info = await self.get_image_info(controller_id, image_name)
                if verify_info:
                    logger.info(
                        f"验证成功：镜像 {image_name} 现在可用于控制器 {controller_id}"
                    )
                    return True
                else:
                    logger.warning(
                        f"验证失败：拉取成功但镜像仍不可用，可能需要更多时间"
                    )
                    return False

            else:
                logger.error(f"镜像 {image_name} 拉取失败: {pull_result}")
                return False

        except Exception as e:
            logger.error(f"确保镜像可用过程中发生系统错误: {e}")
            return False

    async def cleanup_image_from_all_controllers(
        self, image_name: str
    ) -> Dict[str, Any]:
        """从所有控制器清理指定镜像"""
        cleanup_results = {
            "image_name": image_name,
            "controllers_processed": 0,
            "successful_removals": 0,
            "failed_removals": 0,
            "results": [],
            "errors": [],
        }

        try:
            # 遍历所有控制器
            for controller_id in list(self.controllers.keys()):
                cleanup_results["controllers_processed"] += 1

                try:
                    # 检查镜像是否存在
                    image_info = await self.get_image_info(controller_id, image_name)

                    if image_info:
                        # 镜像存在，尝试删除
                        success = await self.remove_image(
                            controller_id, image_name, force=True
                        )

                        if success:
                            cleanup_results["successful_removals"] += 1
                            cleanup_results["results"].append(
                                {
                                    "controller_id": controller_id,
                                    "status": "removed",
                                    "message": "镜像成功删除",
                                }
                            )
                            logger.info(
                                f"成功从控制器 {controller_id} 删除镜像 {image_name}"
                            )
                        else:
                            cleanup_results["failed_removals"] += 1
                            cleanup_results["results"].append(
                                {
                                    "controller_id": controller_id,
                                    "status": "failed",
                                    "message": "删除操作失败",
                                }
                            )
                            logger.warning(
                                f"从控制器 {controller_id} 删除镜像 {image_name} 失败"
                            )
                    else:
                        # 镜像不存在，标记为已清理
                        cleanup_results["results"].append(
                            {
                                "controller_id": controller_id,
                                "status": "not_found",
                                "message": "镜像不存在，无需删除",
                            }
                        )
                        logger.info(f"控制器 {controller_id} 上不存在镜像 {image_name}")

                except Exception as e:
                    cleanup_results["failed_removals"] += 1
                    error_msg = f"控制器 {controller_id} 清理失败: {str(e)}"
                    cleanup_results["errors"].append(error_msg)
                    cleanup_results["results"].append(
                        {
                            "controller_id": controller_id,
                            "status": "error",
                            "message": str(e),
                        }
                    )
                    logger.error(error_msg)

            logger.info(
                f"镜像清理完成: {image_name}, 成功: {cleanup_results['successful_removals']}, 失败: {cleanup_results['failed_removals']}"
            )
            return cleanup_results

        except Exception as e:
            logger.error(f"清理镜像过程中发生系统错误: {e}")
            cleanup_results["errors"].append(f"系统错误: {str(e)}")
            return cleanup_results


# 全局控制器管理器实例
mmanager_client = MManagerControllerManager()
