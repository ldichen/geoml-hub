"""
模型服务管理器 - 使用mManager架构
分布式Docker容器管理服务
"""

import asyncio
import uuid
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload

from app.models.service import (
    ModelService,
    ServiceLog,
    ServiceHealthCheck,
)

# ContainerRegistry 和 ContainerOperation 表已删除
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceStatus,
    ServiceLogCreate,
    ServiceHealthCheckCreate,
    LogLevel,
    EventType,
    HealthStatus,
)
from app.config import settings
from app.utils.resource_manager import resource_manager
from app.services.mmanager_client import mmanager_client

logger = logging.getLogger(__name__)


class ModelServiceManager:
    """模型服务管理器 - 基于mManager分布式架构"""

    def __init__(self):
        self.max_services_per_user = settings.max_services_per_user
        self.idle_timeout_minutes = settings.service_idle_timeout
        self.startup_timeout = settings.service_startup_timeout
        self.shutdown_timeout = settings.service_shutdown_timeout

    async def initialize(self, db: AsyncSession):
        """初始化服务管理器"""
        await mmanager_client.initialize(db)
        logger.info("模型服务管理器初始化完成")

    async def create_service(
        self,
        db: AsyncSession,
        service_data: ServiceCreate,
        repository_id: int,
        user_id: int,
    ) -> ServiceResponse:
        """
        创建模型服务并立即创建容器

        不管是基于已有镜像还是基于tar包，这里都负责拉取指定镜像并创建容器
        """

        # 检查用户服务配额
        await self._check_user_quota(db, user_id)

        # 验证资源限制
        limits = resource_manager.validate_resource_limits(
            service_data.cpu_limit, service_data.memory_limit
        )
        if not limits.is_valid:
            raise ValueError(limits.error_message)

        # 从ServiceCreate中获取image_id，这是必需的
        image_id = service_data.image_id

        # 获取镜像信息
        from app.models.image import Image

        image_query = select(Image).where(Image.id == image_id)
        result = await db.execute(image_query)
        image = result.scalar_one_or_none()

        if not image or image.status != "ready":
            raise ValueError("镜像不存在或未准备就绪")

        # 基于镜像信息生成唯一的服务名
        auto_service_name = self._generate_service_name(image)

        # 分配端口
        allocated_port = await resource_manager.allocate_port(db)

        # 初始化变量
        controller_ip = None
        container_id = None

        # 直接创建容器（不管是基于已有镜像还是tar包）
        docker_image_name = image.full_image_name_with_registry

        # 选择最优控制器
        requirements = {
            "gpu_required": "gpu" in docker_image_name.lower(),
            "memory_gb": self._parse_memory_limit(service_data.memory_limit),
            "cpu_cores": (
                float(service_data.cpu_limit) if service_data.cpu_limit else 0.3
            ),
        }

        controller = await mmanager_client.select_optimal_controller(db, requirements)
        if not controller:
            raise ValueError("没有可用的控制器")
        controller_id = controller.get("id")
        # Extract IP/host from controller URL
        controller_url = controller.get("url", "")
        if "://" in controller_url:
            controller_ip = controller_url.split("://")[1].split(":")[0]
        else:
            controller_ip = "127.0.0.1"

        # 确保镜像在目标控制器上可用
        try:
            logger.info(f"确保镜像在控制器 {controller_id} 上可用: {docker_image_name}")

            # 使用 mmanager_client 的 ensure_image_available 方法
            image_available = await mmanager_client.ensure_image_available(
                controller_id, docker_image_name
            )

            if not image_available:
                raise RuntimeError(
                    f"无法在控制器 {controller_id} 上获取镜像 {docker_image_name}"
                )

            logger.info(f"镜像确认可用: {docker_image_name}")

        except Exception as e:
            logger.error(f"确保镜像可用失败: {e}")
            raise RuntimeError(f"确保镜像在控制器上可用失败: {str(e)}")

        # 准备容器配置
        container_config = {
            "name": auto_service_name,
            "image": docker_image_name,
            "command": None,
            "working_dir": "/app",
            "environment": {
                "GRADIO_SERVER_PORT": str(allocated_port),
                "EXAMPLES_PATH": "/app/examples",
            },
            "ports": {f"{allocated_port}/tcp": allocated_port},
            "volumes": {},
            "memory_limit": self._convert_memory_to_docker_format(
                service_data.memory_limit
            ),
            "cpu_limit": (
                float(service_data.cpu_limit) if service_data.cpu_limit else 1.0
            ),
            "restart_policy": "unless-stopped",
            "network_mode": None,
            "networks": [],
            "labels": {
                "geoml.service_name": auto_service_name,
                "geoml.created_by": "geoml-backend",
            },
            "auto_remove": False,
            "detach": True,
        }

        try:
            # 获取控制器客户端并创建容器
            logger.info(f"=== Backend 发送容器配置 ===")
            logger.info(f"创建容器: {auto_service_name} 在控制器 {controller_id}")
            logger.info(f"发送的配置: {container_config}")

            controller_client = mmanager_client.get_client(controller_id)
            container_result = await controller_client.create_container(
                container_config
            )
            container_id = container_result.get("container_id")

            if not container_id:
                raise RuntimeError("创建容器失败: 未返回容器ID")

            logger.info(f"容器创建成功: {container_id}")

        except Exception as e:
            logger.error(f"创建容器失败: {e}")
            # 释放已分配的端口
            raise RuntimeError(f"创建容器失败: {str(e)}")

        # 创建服务记录
        service = ModelService(
            repository_id=repository_id,
            user_id=user_id,
            image_id=image_id,
            service_name=auto_service_name,
            model_ip=controller_ip,  # 可能为None（未部署时）
            description=service_data.description,
            # 容器信息
            container_id=container_id,  # 可能为None（未部署时）
            # 网络配置
            gradio_port=allocated_port,
            service_url=(
                f"http://{controller_ip}:{allocated_port}" if controller_ip else None
            ),
            # 资源配置
            cpu_limit=service_data.cpu_limit,
            memory_limit=service_data.memory_limit,
            # 服务配置
            is_public=service_data.is_public,
            priority=service_data.priority,
            access_token=self._generate_access_token(),
            # 状态 - 创建服务时容器已创建，状态为created
            status=ServiceStatus.CREATED,
            health_status=HealthStatus.UNKNOWN,
        )


        db.add(service)
        await db.commit()
        await db.refresh(service)

        # 记录创建日志
        log_message = (
            f"服务和容器创建成功 (Container ID: {container_id})"
            if container_id
            else "服务记录创建成功，等待部署"
        )
        await self._log_service_event(
            db, service.id, LogLevel.INFO, log_message, EventType.CREATE, user_id
        )

        return ServiceResponse.model_validate(service)

    async def start_service(
        self,
        db: AsyncSession,
        service_id: int,
        user_id: int,
        force_restart: bool = False,
    ) -> ServiceResponse:
        """启动模型服务"""
        service = await self._get_service_by_id(db, service_id)

        # 检查权限
        if service.user_id != user_id:
            raise PermissionError("无权限操作此服务")

        # 检查当前状态
        if service.status == ServiceStatus.RUNNING and not force_restart:
            return ServiceResponse.model_validate(service)

        # 验证服务是否有容器
        if not service.container_id:
            raise ValueError("服务没有关联的容器，请重新创建服务")

        try:
            # 如果是重启，先停止容器
            if force_restart:
                try:
                    # 找到容器位置
                    location = await mmanager_client.find_container_location(
                        db, service.container_id
                    )
                    if location:
                        controller_client = mmanager_client.get_client(
                            location["controller_id"]
                        )
                        await controller_client.stop_container(service.container_id)
                    logger.info(f"容器 {service.container_id} 已停止，准备重启")
                except Exception as e:
                    logger.warning(f"停止容器失败，但继续尝试启动: {e}")

            # 更新状态为启动中
            service.status = ServiceStatus.STARTING
            service.last_started_at = datetime.now(timezone.utc)
            service.start_count += 1
            await db.commit()

            # 启动容器
            logger.info(f"启动容器: {service.container_id}")
            # 获取容器所在的控制器客户端
            location = await mmanager_client.find_container_location(
                db, service.container_id
            )
            if not location:
                raise ValueError(f"无法找到容器 {service.container_id} 的位置")

            controller_client = mmanager_client.get_client(location["controller_id"])
            start_result = await controller_client.start_container(service.container_id)

            if not start_result.get("success", False):
                raise Exception(
                    f"启动容器失败: {start_result.get('message', '未知错误')}"
                )

            # 更新服务状态
            service.status = ServiceStatus.RUNNING
            service.health_status = HealthStatus.UNKNOWN
            service.last_heartbeat = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(service)

            # 记录启动日志
            await self._log_service_event(
                db,
                service.id,
                LogLevel.INFO,
                f"服务启动成功，容器ID: {service.container_id}，端口: {service.gradio_port}",
                EventType.START,
                user_id,
            )

            # 启动健康检查
            asyncio.create_task(self._start_health_monitoring(db, service.id))

            return ServiceResponse.model_validate(service)

        except Exception as e:
            # 启动失败，更新状态
            service.status = ServiceStatus.ERROR
            service.error_message = str(e)
            await db.commit()

            await self._log_service_event(
                db,
                service.id,
                LogLevel.ERROR,
                f"服务启动失败: {str(e)}",
                EventType.ERROR,
                user_id,
            )

            raise RuntimeError(f"服务启动失败: {str(e)}")

    async def stop_service(
        self,
        db: AsyncSession,
        service_id: int,
        user_id: int,
        force_stop: bool = False,
        timeout_seconds: int = 30,
    ) -> ServiceResponse:
        """停止模型服务"""

        service = await self._get_service_by_id(db, service_id)

        # 检查权限
        if service.user_id != user_id:
            raise PermissionError("无权限操作此服务")

        # 检查当前状态（除非强制停止）
        if not force_stop and service.status in [
            ServiceStatus.STOPPED,
            ServiceStatus.STOPPING,
        ]:
            return ServiceResponse.model_validate(service)

        try:
            # 更新状态为停止中
            service.status = ServiceStatus.STOPPING
            await db.commit()

            # 通过mManager停止容器
            if service.container_id:
                await self._stop_container_via_mmanager(
                    db, service.container_id, timeout_seconds, force_stop
                )

            # 更新服务状态
            service.status = ServiceStatus.STOPPED
            service.last_stopped_at = datetime.now(timezone.utc)
            service.health_status = HealthStatus.UNKNOWN

            await db.commit()
            await db.refresh(service)

            # 记录停止日志
            await self._log_service_event(
                db, service.id, LogLevel.INFO, "服务停止成功", EventType.STOP, user_id
            )

            return ServiceResponse.model_validate(service)

        except Exception as e:
            # 停止失败，记录错误但不回滚状态
            await self._log_service_event(
                db,
                service.id,
                LogLevel.ERROR,
                f"服务停止失败: {str(e)}",
                EventType.ERROR,
                user_id,
            )
            raise RuntimeError(f"服务停止失败: {str(e)}")

    async def delete_service(
        self, db: AsyncSession, service_id: int, user_id: int
    ) -> bool:
        """删除模型服务"""

        service = await self._get_service_by_id(db, service_id)

        # 检查权限
        if service.user_id != user_id:
            raise PermissionError("无权限操作此服务")

        try:
            # 先停止服务
            if service.status == ServiceStatus.RUNNING:
                await self.stop_service(db, service_id, user_id)

            # 删除容器
            if service.container_id:
                await self._remove_container_via_mmanager(db, service.container_id)


            # 删除数据库记录（级联删除相关表）
            await db.delete(service)
            await db.commit()

            logger.info(f"服务 {service_id} 删除成功")
            return True

        except Exception as e:
            logger.error(f"删除服务 {service_id} 失败: {e}")
            raise RuntimeError(f"服务删除失败: {str(e)}")

    async def get_service_status(
        self, db: AsyncSession, service_id: int
    ) -> Dict[str, Any]:
        """获取服务状态"""

        service = await self._get_service_by_id(db, service_id)

        # 获取容器实时状态
        container_info = None
        if service.container_id:
            try:
                location = await mmanager_client.find_container_location(
                    db, service.container_id
                )
                if location:
                    container_info = await location["client"].get_container_info(
                        service.container_id
                    )
            except Exception as e:
                logger.warning(f"获取容器状态失败: {e}")

        # 获取最新健康检查
        health_check_query = (
            select(ServiceHealthCheck)
            .where(ServiceHealthCheck.service_id == service_id)
            .order_by(ServiceHealthCheck.checked_at.desc())
            .limit(1)
        )

        result = await db.execute(health_check_query)
        latest_health_check = result.scalar_one_or_none()

        # 计算运行时间
        uptime_seconds = None
        if service.last_started_at and service.status == ServiceStatus.RUNNING:
            uptime_seconds = int(
                (datetime.now(timezone.utc) - service.last_started_at).total_seconds()
            )

        return {
            "id": service.id,
            "service_name": service.service_name,
            "status": service.status,
            "is_healthy": (
                latest_health_check.status == HealthStatus.HEALTHY
                if latest_health_check
                else False
            ),
            "uptime_seconds": uptime_seconds,
            "container_info": container_info,
            "resource_usage": (
                container_info.get("resource_usage") if container_info else None
            ),
            "last_health_check": (
                latest_health_check.checked_at if latest_health_check else None
            ),
            "error_message": service.error_message,
            "controller_info": {
                "model_ip": service.model_ip,
                "container_id": service.container_id,
                "container_name": service.service_name,
            },
        }

    async def get_service_logs(
        self, db: AsyncSession, service_id: int, lines: int = 100
    ) -> Dict[str, Any]:
        """获取服务日志"""

        service = await self._get_service_by_id(db, service_id)

        if not service.container_id:
            return {
                "service_id": service_id,
                "logs": "服务未运行，无容器日志可用",
                "lines": 0,
            }

        try:
            location = await mmanager_client.find_container_location(
                db, service.container_id
            )
            if not location:
                return {
                    "service_id": service_id,
                    "logs": "无法找到容器位置",
                    "lines": 0,
                }

            logs_response = await location["client"].get_container_logs(
                service.container_id, lines
            )
            return logs_response

        except Exception as e:
            logger.error(f"获取服务日志失败: {e}")
            return {
                "service_id": service_id,
                "logs": f"获取日志失败: {str(e)}",
                "lines": 0,
            }

    # 私有方法
    async def _stop_container_via_mmanager(
        self,
        db: AsyncSession,
        container_id: str,
        timeout: int = 30,
        force: bool = False,
    ):
        """通过mManager停止容器

        Args:
            db: 数据库会话
            container_id: 容器ID
            timeout: 停止超时时间（秒）
            force: 是否强制停止（预留参数，可用于未来扩展）
        """

        location = await mmanager_client.find_container_location(db, container_id)
        if not location:
            raise Exception(f"无法找到容器 {container_id}")

        try:
            result = await location["client"].stop_container(container_id, timeout)
            if not result.get("success", False):
                raise Exception(f"停止容器失败: {result.get('message', '未知错误')}")

            logger.info(f"容器 {container_id} 停止成功")

        except Exception as e:
            logger.error(f"停止容器 {container_id} 失败: {e}")
            raise

    async def _remove_container_via_mmanager(self, db: AsyncSession, container_id: str):
        """通过mManager删除容器"""

        location = await mmanager_client.find_container_location(db, container_id)
        if not location:
            logger.warning(f"容器 {container_id} 不存在，跳过删除")
            return

        try:
            result = await location["client"].remove_container(container_id, force=True)
            if not result.get("success", False):
                logger.warning(
                    f"删除容器失败，但继续处理: {result.get('message', '未知错误')}"
                )
            else:
                logger.info(f"容器 {container_id} 删除成功")

        except Exception as e:
            logger.warning(f"删除容器 {container_id} 失败，但继续处理: {e}")

    # _record_container_operation 已删除 - 操作记录通过 ServiceLog 处理

    async def _start_health_monitoring(self, db: AsyncSession, service_id: int):
        """启动健康监控"""

        await asyncio.sleep(10)  # 等待服务启动

        while True:
            try:
                # 检查服务是否还在运行
                service = await self._get_service_by_id(db, service_id)
                if service.status != ServiceStatus.RUNNING:
                    break

                # 执行健康检查
                await self.perform_health_check(db, service_id)

                # 等待下次检查
                await asyncio.sleep(30)  # 30秒检查一次

            except Exception as e:
                logger.error(f"健康监控服务 {service_id} 失败: {e}")
                await asyncio.sleep(30)
                break

    async def perform_health_check(
        self, db: AsyncSession, service_id: int
    ) -> ServiceHealthCheck:
        """执行健康检查"""

        service = await self._get_service_by_id(db, service_id)

        check_result = ServiceHealthCheckCreate(
            status=HealthStatus.UNKNOWN, check_type="http"
        )

        if service.status == ServiceStatus.RUNNING and service.service_url:
            try:
                import aiohttp
                import asyncio
                import time

                start_time = time.time()
                timeout = aiohttp.ClientTimeout(total=30)

                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(f"{service.service_url}/health") as response:
                        response_time_ms = int((time.time() - start_time) * 1000)

                        if response.status == 200:
                            check_result.status = HealthStatus.HEALTHY
                            check_result.http_status_code = response.status
                            check_result.response_time_ms = response_time_ms
                        else:
                            check_result.status = HealthStatus.UNHEALTHY
                            check_result.error_message = f"HTTP {response.status}"
                            check_result.http_status_code = response.status

            except asyncio.TimeoutError:
                check_result.status = HealthStatus.TIMEOUT
                check_result.error_message = "健康检查超时"
            except Exception as e:
                check_result.status = HealthStatus.UNHEALTHY
                check_result.error_message = str(e)
        else:
            check_result.status = HealthStatus.UNHEALTHY
            check_result.error_message = f"服务状态: {service.status}"

        # 保存健康检查结果
        health_check = ServiceHealthCheck(
            service_id=service_id, **check_result.model_dump()
        )
        db.add(health_check)

        # 更新服务的健康状态
        service.last_health_check = datetime.now(timezone.utc)
        service.health_status = check_result.status

        await db.commit()
        await db.refresh(health_check)

        return health_check

    # 辅助方法
    async def _check_user_quota(self, db: AsyncSession, user_id: int):
        """检查用户服务配额"""

        active_services_query = select(func.count(ModelService.id)).where(
            and_(
                ModelService.user_id == user_id,
                ModelService.status.in_(
                    [ServiceStatus.RUNNING, ServiceStatus.STARTING]
                ),
            )
        )

        result = await db.execute(active_services_query)
        active_count = result.scalar()

        if active_count >= self.max_services_per_user:
            raise ValueError(
                f"已达到最大同时运行服务数量限制 ({self.max_services_per_user})"
            )

    # 移除服务名称唯一性检查，因为现在服务名称是自动生成的，包含UUID，不会重复
    # async def _check_service_name_unique(
    #     self, db: AsyncSession, repository_id: int, service_name: str
    # ):
    #     """检查服务名称唯一性"""
    #
    #     existing_service_query = select(ModelService).where(
    #         and_(
    #             ModelService.repository_id == repository_id,
    #             ModelService.service_name == service_name,
    #         )
    #     )
    #
    #     result = await db.execute(existing_service_query)
    #     existing_service = result.scalar_one_or_none()
    #
    #     if existing_service:
    #         raise ValueError(f"服务名称 '{service_name}' 已存在")

    async def _get_service_by_id(
        self, db: AsyncSession, service_id: int
    ) -> ModelService:
        """根据ID获取服务"""

        service_query = select(ModelService).where(ModelService.id == service_id)

        result = await db.execute(service_query)
        service = result.scalar_one_or_none()

        if not service:
            raise ValueError(f"服务 {service_id} 不存在")

        return service

    def _generate_access_token(self) -> str:
        """生成访问令牌"""
        return f"geoml-{uuid.uuid4().hex[:16]}"

    def _generate_service_name(self, image: Optional[object] = None) -> str:
        """
        自动生成服务名称
        格式: {original_name}-{image_id}-{short_uuid}
        如果没有镜像信息，使用默认格式: service-{short_uuid}
        """
        short_uuid = uuid.uuid4().hex[:8]

        if image and hasattr(image, "original_name") and hasattr(image, "id"):
            # 使用镜像的 original_name 和 id
            original_name = image.original_name
            # 规范化名称，确保符合Docker命名规范
            normalized_name = re.sub(r"[^a-zA-Z0-9_.-]", "-", original_name.lower())
            normalized_name = re.sub(r"[-_.]{2,}", "-", normalized_name)
            normalized_name = normalized_name.strip("-_.")

            return f"{normalized_name}-{image.id}-{short_uuid}"
        else:
            raise ValueError("无法生成服务名称: 必须提供镜像信息")

    def _parse_memory_limit(self, memory_limit: str) -> float:
        """解析内存限制字符串为GB数值"""
        memory_limit = memory_limit.lower()
        if "gi" in memory_limit or "gb" in memory_limit:
            return float(memory_limit.replace("gi", "").replace("gb", ""))
        elif "mi" in memory_limit or "mb" in memory_limit:
            return float(memory_limit.replace("mi", "").replace("mb", "")) / 1024
        else:
            # 默认按MB处理
            return float(memory_limit.replace("m", "")) / 1024

    def _convert_memory_to_docker_format(self, memory_limit: str) -> str:
        """将Kubernetes格式的内存限制转换为Docker格式
        例如: 256Mi -> 256m, 2Gi -> 2g, 1024Mi -> 1024m
        """
        if not memory_limit:
            return "512m"  # 默认值

        memory_limit = memory_limit.strip()

        # 处理Kubernetes格式 (Mi, Gi)
        if memory_limit.endswith("Mi"):
            value = memory_limit[:-2]
            return f"{value}m"
        elif memory_limit.endswith("Gi"):
            value = memory_limit[:-2]
            return f"{value}g"
        elif memory_limit.endswith("Ki"):
            # Ki转换为m (1Ki = 1024bytes, 1m = 1MB = 1024*1024bytes)
            value = int(memory_limit[:-2])
            mb_value = value / 1024  # 转换为MB
            return f"{int(mb_value)}m"

        # 如果已经是Docker格式，直接返回
        if memory_limit.endswith(("m", "g", "M", "G", "mb", "gb", "MB", "GB")):
            return memory_limit.lower()

        # 默认当作MB处理
        if memory_limit.isdigit():
            return f"{memory_limit}m"

        return "512m"  # 默认值


    async def _log_service_event(
        self,
        db: AsyncSession,
        service_id: int,
        level: LogLevel,
        message: str,
        event_type: EventType,
        user_id: Optional[int] = None,
    ):
        """记录服务事件日志"""

        log_entry = ServiceLog(
            service_id=service_id,
            log_level=level,
            message=message,
            event_type=event_type,
            user_id=user_id,
        )

        db.add(log_entry)
        await db.commit()


# 全局服务管理器实例
service_manager = ModelServiceManager()
