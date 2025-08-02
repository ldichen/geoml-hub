"""
mManager 客户端服务
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.container_registry import ContainerRegistry, MManagerController
from app.models.service import ModelService

logger = logging.getLogger(__name__)

class MManagerClient:
    """mManager 客户端"""
    
    def __init__(self, controller_url: str, api_key: str):
        self.controller_url = controller_url.rstrip('/')
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """通用请求方法"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.request(
                    method, 
                    f"{self.controller_url}{endpoint}", 
                    headers=headers, 
                    **kwargs
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise Exception(f"mManager API Error: {response.status} - {error_text}")
                    
                    return await response.json()
        except asyncio.TimeoutError:
            raise Exception(f"请求 {self.controller_url} 超时")
        except aiohttp.ClientError as e:
            raise Exception(f"连接 {self.controller_url} 失败: {str(e)}")
    
    async def health_check(self) -> Dict:
        """健康检查"""
        return await self._request('GET', '/health')
    
    async def create_container(self, config: Dict) -> Dict:
        """创建容器"""
        return await self._request('POST', '/containers/', json=config)
    
    async def start_container(self, container_id: str) -> Dict:
        """启动容器"""
        return await self._request('POST', f'/containers/{container_id}/start')
    
    async def stop_container(self, container_id: str, timeout: int = 10) -> Dict:
        """停止容器"""
        return await self._request(
            'POST', 
            f'/containers/{container_id}/stop',
            params={'timeout': timeout}
        )
    
    async def remove_container(self, container_id: str, force: bool = True) -> Dict:
        """删除容器"""
        return await self._request(
            'DELETE', 
            f'/containers/{container_id}',
            params={'force': force}
        )
    
    async def get_container_info(self, container_id: str) -> Dict:
        """获取容器信息"""
        return await self._request('GET', f'/containers/{container_id}')
    
    async def get_container_stats(self, container_id: str) -> Dict:
        """获取容器统计信息"""
        return await self._request('GET', f'/containers/{container_id}/stats')
    
    async def get_container_logs(self, container_id: str, lines: int = 100) -> Dict:
        """获取容器日志"""
        return await self._request(
            'GET', 
            f'/containers/{container_id}/logs',
            params={'lines': lines}
        )
    
    async def list_containers(self, all_containers: bool = False) -> Dict:
        """列出容器"""
        return await self._request(
            'GET', 
            '/containers/',
            params={'all': all_containers}
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
        
        logger.info(f"mManager控制器管理器初始化完成，已注册 {len(self.controllers)} 个控制器")
    
    async def _load_controllers_from_config(self):
        """从配置加载控制器"""
        # 从配置文件或环境变量加载控制器列表
        controller_configs = getattr(settings, 'mmanager_controllers', [])
        
        if not controller_configs:
            # 默认配置
            controller_configs = [
                {
                    'id': 'mmanager-default',
                    'url': 'http://localhost:8001',
                    'server_type': 'cpu',
                    'enabled': True
                }
            ]
        
        for config in controller_configs:
            if config.get('enabled', True):
                client = MManagerClient(
                    controller_url=config['url'],
                    api_key=getattr(settings, 'mmanager_api_key', 'mmanager-default-key')
                )
                self.controllers[config['id']] = client
                logger.info(f"注册mManager控制器: {config['id']} -> {config['url']}")
    
    async def _register_controllers_to_db(self, db: AsyncSession):
        """将控制器注册到数据库"""
        for controller_id, client in self.controllers.items():
            try:
                # 检查数据库中是否已存在
                result = await db.execute(
                    select(MManagerController).where(
                        MManagerController.controller_id == controller_id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    # 创建新记录
                    controller = MManagerController(
                        controller_id=controller_id,
                        controller_url=client.controller_url,
                        server_type='unknown',  # 稍后通过健康检查获取
                        status='unknown'
                    )
                    db.add(controller)
                    logger.info(f"将控制器 {controller_id} 注册到数据库")
                
                await db.commit()
                
            except Exception as e:
                logger.error(f"注册控制器 {controller_id} 到数据库失败: {e}")
    
    async def get_healthy_controllers(self, db: AsyncSession) -> List[Dict]:
        """获取健康的控制器列表"""
        result = await db.execute(
            select(MManagerController).where(
                and_(
                    MManagerController.status == 'healthy',
                    MManagerController.enabled == True
                )
            )
        )
        
        controllers = []
        for controller in result.scalars():
            if controller.controller_id in self.controllers:
                controllers.append({
                    'id': controller.controller_id,
                    'url': controller.controller_url,
                    'server_type': controller.server_type,
                    'load_percentage': controller.load_percentage,
                    'capabilities': controller.capabilities,
                    'client': self.controllers[controller.controller_id]
                })
        
        return controllers
    
    async def select_optimal_controller(
        self, 
        db: AsyncSession, 
        requirements: Dict = None
    ) -> Dict:
        """选择最优控制器"""
        healthy_controllers = await self.get_healthy_controllers(db)
        
        if not healthy_controllers:
            raise Exception("没有可用的健康控制器")
        
        # 根据需求筛选控制器
        suitable_controllers = []
        
        for controller in healthy_controllers:
            capabilities = controller.get('capabilities', {})
            
            # 检查GPU需求
            if requirements and requirements.get('gpu_required', False):
                if not capabilities.get('gpu_support', False):
                    continue
            
            # 检查内存需求
            if requirements and requirements.get('memory_gb', 0) > 0:
                required_memory = requirements['memory_gb']
                max_memory = capabilities.get('max_memory_gb', 0)
                if required_memory > max_memory:
                    continue
            
            # 检查负载
            if controller['load_percentage'] >= 90:  # 负载过高
                continue
            
            suitable_controllers.append(controller)
        
        if not suitable_controllers:
            # 如果没有完全匹配的，选择负载最低的
            suitable_controllers = healthy_controllers
        
        # 选择负载最低的控制器
        best_controller = min(
            suitable_controllers, 
            key=lambda x: x['load_percentage']
        )
        
        return best_controller
    
    async def find_container_location(
        self, 
        db: AsyncSession, 
        container_id: str
    ) -> Optional[Dict]:
        """查找容器位置"""
        # 先从注册表查找
        result = await db.execute(
            select(ContainerRegistry).where(
                ContainerRegistry.container_id == container_id
            )
        )
        registry = result.scalar_one_or_none()
        
        if registry and registry.controller_id in self.controllers:
            return {
                'controller_id': registry.controller_id,
                'client': self.controllers[registry.controller_id],
                'registry': registry
            }
        
        # 如果注册表中没有，广播查询所有控制器
        for controller_id, client in self.controllers.items():
            try:
                container_info = await client.get_container_info(container_id)
                if container_info:
                    logger.warning(f"在控制器 {controller_id} 发现未注册容器: {container_id}")
                    return {
                        'controller_id': controller_id,
                        'client': client,
                        'registry': None
                    }
            except:
                continue
        
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
        """检查所有控制器健康状态"""
        for controller_id, client in self.controllers.items():
            try:
                # 调用健康检查接口
                health_data = await client.health_check()
                
                # 更新数据库记录
                await db.execute(
                    update(MManagerController)
                    .where(MManagerController.controller_id == controller_id)
                    .values(
                        status='healthy',
                        last_check_at=datetime.utcnow(),
                        health_data=health_data,
                        error_message=None,
                        consecutive_failures=0,
                        current_containers=health_data.get('containers', {}).get('running', 0),
                        max_containers=health_data.get('containers', {}).get('max_allowed', 100),
                        cpu_cores=health_data.get('resources', {}).get('cpu_cores'),
                        memory_total_gb=health_data.get('resources', {}).get('memory_total_gb'),
                        memory_available_gb=health_data.get('resources', {}).get('memory_available_gb'),
                        load_percentage=health_data.get('load_percentage', 0),
                        server_type=health_data.get('server_type', 'unknown'),
                        capabilities=health_data.get('capabilities', {})
                    )
                )
                
                self.last_health_check[controller_id] = datetime.utcnow()
                
            except Exception as e:
                logger.warning(f"控制器 {controller_id} 健康检查失败: {e}")
                
                # 更新失败状态
                await db.execute(
                    update(MManagerController)
                    .where(MManagerController.controller_id == controller_id)
                    .values(
                        status='unhealthy',
                        last_check_at=datetime.utcnow(),
                        error_message=str(e),
                        consecutive_failures=MManagerController.consecutive_failures + 1,
                        total_failures=MManagerController.total_failures + 1
                    )
                )
        
        await db.commit()
    
    # ================== 镜像管理方法 ==================
    
    async def pull_image(self, controller_id: str, image_name: str, 
                        auth_config: Optional[Dict] = None) -> Dict:
        """在指定控制器上拉取镜像"""
        if controller_id not in self.controllers:
            raise Exception(f"控制器 {controller_id} 不存在")
            
        client = self.controllers[controller_id]
        
        pull_data = {
            "image": image_name,
            "auth": auth_config
        }
        
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
    
    async def remove_image(self, controller_id: str, image_name: str, force: bool = False) -> bool:
        """删除控制器上的镜像"""
        if controller_id not in self.controllers:
            raise Exception(f"控制器 {controller_id} 不存在")
            
        client = self.controllers[controller_id]
        
        try:
            params = {"force": force}
            await client._request("DELETE", f"/images/{image_name}", params=params)
            logger.info(f"控制器 {controller_id} 删除镜像 {image_name}")
            return True
        except Exception as e:
            logger.error(f"控制器 {controller_id} 删除镜像失败: {e}")
            return False
    
    async def get_image_info(self, controller_id: str, image_name: str) -> Optional[Dict]:
        """获取镜像详细信息"""
        if controller_id not in self.controllers:
            raise Exception(f"控制器 {controller_id} 不存在")
            
        client = self.controllers[controller_id]
        result = await client._request("GET", f"/images/{image_name}")
        return result
    
    async def clean_unused_images(self, controller_id: str) -> Dict:
        """清理未使用的镜像"""
        if controller_id not in self.controllers:
            raise Exception(f"控制器 {controller_id} 不存在")
            
        client = self.controllers[controller_id]
        result = await client._request("POST", "/images/prune")
        logger.info(f"控制器 {controller_id} 清理未使用镜像: {result}")
        return result
    
    async def ensure_image_available(self, controller_id: str, image_name: str, 
                                   harbor_auth: Optional[Dict] = None) -> bool:
        """确保镜像在控制器上可用，如不存在则拉取"""
        try:
            # 1. 检查镜像是否已存在
            image_info = await self.get_image_info(controller_id, image_name)
            if image_info:
                logger.info(f"镜像 {image_name} 已存在于控制器 {controller_id}")
                return True
            
            # 2. 镜像不存在，尝试拉取
            logger.info(f"镜像 {image_name} 不存在，开始拉取到控制器 {controller_id}")
            pull_result = await self.pull_image(controller_id, image_name, harbor_auth)
            
            # 3. 验证拉取是否成功
            if pull_result.get("status") == "success":
                logger.info(f"镜像 {image_name} 成功拉取到控制器 {controller_id}")
                return True
            else:
                logger.error(f"镜像 {image_name} 拉取失败: {pull_result}")
                return False
                
        except Exception as e:
            logger.error(f"确保镜像可用失败: {e}")
            return False

# 全局控制器管理器实例
mmanager_controller_manager = MManagerControllerManager()