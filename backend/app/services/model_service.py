"""
模型服务管理器 - 使用mManager架构
分布式Docker容器管理服务
"""

import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload

from app.models.service import ModelService, ServiceInstance, ServiceLog, ServiceHealthCheck
from app.models.container_registry import ContainerRegistry, ContainerOperation
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
from app.services.mmanager_client import mmanager_controller_manager

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
        await mmanager_controller_manager.initialize(db)
        logger.info("模型服务管理器初始化完成")
    
    async def create_service(
        self,
        db: AsyncSession,
        service_data: ServiceCreate,
        repository_id: int,
        user_id: int,
    ) -> ServiceResponse:
        """创建模型服务"""
        
        # 检查用户服务配额
        await self._check_user_quota(db, user_id)
        
        # 检查服务名称唯一性
        await self._check_service_name_unique(
            db, repository_id, service_data.service_name
        )
        
        # 验证资源限制
        limits = resource_manager.validate_resource_limits(
            service_data.cpu_limit, service_data.memory_limit
        )
        if not limits.is_valid:
            raise ValueError(limits.error_message)
        
        # 创建服务记录
        service = ModelService(
            repository_id=repository_id,
            user_id=user_id,
            service_name=service_data.service_name,
            model_id=service_data.model_id,
            model_ip="172.21.252.206",  # 模型服务器IP
            description=service_data.description,
            cpu_limit=service_data.cpu_limit,
            memory_limit=service_data.memory_limit,
            is_public=service_data.is_public,
            priority=service_data.priority,
            status=ServiceStatus.CREATED,
            access_token=self._generate_access_token(),
            docker_image=service_data.model_id,  # 使用model_id作为镜像名
            health_status="unknown"
        )
        
        # 处理示例数据
        if service_data.example_data:
            example_data_path = await self._save_example_data(
                service_data.example_data, repository_id, service_data.service_name
            )
            service.example_data_path = example_data_path
        
        db.add(service)
        await db.commit()
        await db.refresh(service)
        
        # 记录创建日志
        await self._log_service_event(
            db, service.id, LogLevel.INFO, "服务创建成功", EventType.CREATE, user_id
        )
        
        return ServiceResponse.from_orm(service)
    
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
            return ServiceResponse.from_orm(service)
        
        try:
            # 如果是重启，先停止现有容器
            if force_restart and service.container_registry:
                await self._stop_container_via_mmanager(
                    db, service.container_registry.container_id
                )
            
            # 更新状态为启动中
            service.status = ServiceStatus.STARTING
            service.last_started_at = datetime.utcnow()
            service.start_count += 1
            await db.commit()
            
            # 选择最优控制器
            requirements = {
                'gpu_required': 'gpu' in service.docker_image.lower() or 'tensorflow-gpu' in service.docker_image.lower(),
                'memory_gb': self._parse_memory_limit(service.memory_limit),
                'cpu_cores': float(service.cpu_limit)
            }
            
            controller = await mmanager_controller_manager.select_optimal_controller(
                db, requirements
            )
            
            # 分配端口
            port = await resource_manager.allocate_port(db)
            
            # 构建容器配置
            container_config = {
                'name': f"geoml-service-{service.id}-{uuid.uuid4().hex[:8]}",
                'image': service.docker_image,
                'command': None,
                'working_dir': '/app',
                'environment': {
                    'MODEL_IP': service.model_ip,
                    'MODEL_ID': service.model_id,
                    'GRADIO_SERVER_PORT': str(port),
                    'SERVICE_NAME': service.service_name,
                    'EXAMPLE_DATA_PATH': '/app/examples' if service.example_data_path else None
                },
                'ports': {f'{port}/tcp': port},
                'volumes': {},
                'memory_limit': service.memory_limit,
                'cpu_limit': float(service.cpu_limit),
                'restart_policy': 'unless-stopped',
                'labels': {
                    'geoml.service.id': str(service.id),
                    'geoml.service.name': service.service_name,
                    'geoml.managed': 'true'
                }
            }
            
            # 添加卷挂载
            if service.example_data_path:
                container_config['volumes'][service.example_data_path] = '/app/examples'
            
            # 通过控制器创建容器
            create_result = await controller['client'].create_container(container_config)
            
            if not create_result.get('success', False):
                raise Exception(f"创建容器失败: {create_result.get('message', '未知错误')}")
            
            container_id = create_result['container_id']
            
            # 启动容器
            start_result = await controller['client'].start_container(container_id)
            
            if not start_result.get('success', False):
                # 创建失败，清理容器
                try:
                    await controller['client'].remove_container(container_id, force=True)
                except:
                    pass
                raise Exception(f"启动容器失败: {start_result.get('message', '未知错误')}")
            
            # 注册容器到注册表
            container_registry = ContainerRegistry(
                container_id=container_id,
                service_id=service.id,
                controller_id=controller['id'],
                controller_url=controller['url'],
                container_name=container_config['name'],
                image_name=service.docker_image,
                status='running',
                server_info={
                    'server_type': controller.get('server_type', 'unknown'),
                    'capabilities': controller.get('capabilities', {})
                },
                resource_allocation={
                    'cpu_limit': service.cpu_limit,
                    'memory_limit': service.memory_limit
                },
                port_mappings={f'{port}/tcp': port},
                host_port=port,
                container_port=7860,
                health_status='unknown',
                started_at=datetime.utcnow()
            )
            
            db.add(container_registry)
            
            # 创建服务实例记录（保持兼容）
            instance = ServiceInstance(
                service_id=service.id,
                container_id=container_id,
                container_name=container_config['name'],
                image_name=service.docker_image,
                host_port=port,
                container_port=7860,
                status="running",
            )
            db.add(instance)
            
            # 更新服务信息
            service.container_id = container_id
            service.gradio_port = port
            service.service_url = f"http://{settings.service_domain}:{port}"
            service.status = ServiceStatus.RUNNING
            service.health_status = "unknown"
            
            await db.commit()
            await db.refresh(service)
            
            # 记录容器操作
            await self._record_container_operation(
                db, container_id, service.id, controller['id'], 
                'start', 'success', {'port': port}, user_id
            )
            
            # 记录启动日志
            await self._log_service_event(
                db,
                service.id,
                LogLevel.INFO,
                f"服务启动成功，端口: {port}，控制器: {controller['id']}",
                EventType.START,
                user_id,
            )
            
            # 启动健康检查
            asyncio.create_task(self._start_health_monitoring(db, service.id))
            
            return ServiceResponse.from_orm(service)
            
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
        timeout_seconds: int = 30,
    ) -> ServiceResponse:
        """停止模型服务"""
        
        service = await self._get_service_by_id(db, service_id)
        
        # 检查权限
        if service.user_id != user_id:
            raise PermissionError("无权限操作此服务")
        
        # 检查当前状态
        if service.status in [ServiceStatus.STOPPED, ServiceStatus.STOPPING]:
            return ServiceResponse.from_orm(service)
        
        try:
            # 更新状态为停止中
            service.status = ServiceStatus.STOPPING
            await db.commit()
            
            # 通过mManager停止容器
            if service.container_registry:
                await self._stop_container_via_mmanager(
                    db, service.container_registry.container_id, timeout_seconds
                )
            
            # 更新服务状态
            service.status = ServiceStatus.STOPPED
            service.last_stopped_at = datetime.utcnow()
            service.container_id = None
            service.gradio_port = None
            service.service_url = None
            service.health_status = "unknown"
            
            # 更新容器注册表
            if service.container_registry:
                service.container_registry.status = 'stopped'
                service.container_registry.stopped_at = datetime.utcnow()
            
            # 更新服务实例状态
            if service.instances:
                for instance in service.instances:
                    instance.status = "stopped"
                    instance.stopped_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(service)
            
            # 记录停止日志
            await self._log_service_event(
                db, service.id, LogLevel.INFO, "服务停止成功", EventType.STOP, user_id
            )
            
            return ServiceResponse.from_orm(service)
            
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
            if service.container_registry:
                await self._remove_container_via_mmanager(
                    db, service.container_registry.container_id
                )
            
            # 清理示例数据文件
            if service.example_data_path:
                await self._cleanup_example_data(service.example_data_path)
            
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
        if service.container_registry:
            try:
                location = await mmanager_controller_manager.find_container_location(
                    db, service.container_registry.container_id
                )
                if location:
                    container_info = await location['client'].get_container_info(
                        service.container_registry.container_id
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
                (datetime.utcnow() - service.last_started_at).total_seconds()
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
            "resource_usage": container_info.get("resource_usage") if container_info else None,
            "last_health_check": (
                latest_health_check.checked_at if latest_health_check else None
            ),
            "error_message": service.error_message,
            "controller_info": {
                "controller_id": service.container_registry.controller_id if service.container_registry else None,
                "controller_url": service.container_registry.controller_url if service.container_registry else None,
                "server_info": service.container_registry.server_info if service.container_registry else None
            }
        }
    
    async def get_service_logs(
        self, db: AsyncSession, service_id: int, lines: int = 100
    ) -> Dict[str, Any]:
        """获取服务日志"""
        
        service = await self._get_service_by_id(db, service_id)
        
        if not service.container_registry:
            return {
                "service_id": service_id,
                "logs": "服务未运行，无容器日志可用",
                "lines": 0
            }
        
        try:
            location = await mmanager_controller_manager.find_container_location(
                db, service.container_registry.container_id
            )
            if not location:
                return {
                    "service_id": service_id,
                    "logs": "无法找到容器位置",
                    "lines": 0
                }
            
            logs_response = await location['client'].get_container_logs(
                service.container_registry.container_id, lines
            )
            return logs_response
            
        except Exception as e:
            logger.error(f"获取服务日志失败: {e}")
            return {
                "service_id": service_id,
                "logs": f"获取日志失败: {str(e)}",
                "lines": 0
            }
    
    # 私有方法
    async def _stop_container_via_mmanager(
        self, db: AsyncSession, container_id: str, timeout: int = 30
    ):
        """通过mManager停止容器"""
        
        location = await mmanager_controller_manager.find_container_location(
            db, container_id
        )
        if not location:
            raise Exception(f"无法找到容器 {container_id}")
        
        try:
            result = await location['client'].stop_container(container_id, timeout)
            if not result.get('success', False):
                raise Exception(f"停止容器失败: {result.get('message', '未知错误')}")
            
            logger.info(f"容器 {container_id} 停止成功")
            
        except Exception as e:
            logger.error(f"停止容器 {container_id} 失败: {e}")
            raise
    
    async def _remove_container_via_mmanager(
        self, db: AsyncSession, container_id: str
    ):
        """通过mManager删除容器"""
        
        location = await mmanager_controller_manager.find_container_location(
            db, container_id
        )
        if not location:
            logger.warning(f"容器 {container_id} 不存在，跳过删除")
            return
        
        try:
            result = await location['client'].remove_container(container_id, force=True)
            if not result.get('success', False):
                logger.warning(f"删除容器失败，但继续处理: {result.get('message', '未知错误')}")
            else:
                logger.info(f"容器 {container_id} 删除成功")
            
        except Exception as e:
            logger.warning(f"删除容器 {container_id} 失败，但继续处理: {e}")
    
    async def _record_container_operation(
        self,
        db: AsyncSession,
        container_id: str,
        service_id: int,
        controller_id: str,
        operation_type: str,
        operation_status: str,
        operation_details: Dict = None,
        user_id: int = None
    ):
        """记录容器操作"""
        
        operation = ContainerOperation(
            container_id=container_id,
            service_id=service_id,
            controller_id=controller_id,
            operation_type=operation_type,
            operation_status=operation_status,
            operation_details=operation_details or {},
            user_id=user_id,
            automated=user_id is None,
            completed_at=datetime.utcnow()
        )
        
        db.add(operation)
        await db.commit()
    
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
                timeout = aiohttp.ClientTimeout(total=10)
                
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
        health_check = ServiceHealthCheck(service_id=service_id, **check_result.dict())
        db.add(health_check)
        
        # 更新服务的健康状态
        service.last_health_check = datetime.utcnow()
        service.health_status = check_result.status.value
        
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
    
    async def _check_service_name_unique(
        self, db: AsyncSession, repository_id: int, service_name: str
    ):
        """检查服务名称唯一性"""
        
        existing_service_query = select(ModelService).where(
            and_(
                ModelService.repository_id == repository_id,
                ModelService.service_name == service_name,
            )
        )
        
        result = await db.execute(existing_service_query)
        existing_service = result.scalar_one_or_none()
        
        if existing_service:
            raise ValueError(f"服务名称 '{service_name}' 已存在")
    
    async def _get_service_by_id(
        self, db: AsyncSession, service_id: int
    ) -> ModelService:
        """根据ID获取服务"""
        
        service_query = select(ModelService).options(
            selectinload(ModelService.container_registry),
            selectinload(ModelService.instances)
        ).where(ModelService.id == service_id)
        
        result = await db.execute(service_query)
        service = result.scalar_one_or_none()
        
        if not service:
            raise ValueError(f"服务 {service_id} 不存在")
        
        return service
    
    def _generate_access_token(self) -> str:
        """生成访问令牌"""
        return f"geoml-{uuid.uuid4().hex[:16]}"
    
    def _parse_memory_limit(self, memory_limit: str) -> float:
        """解析内存限制字符串为GB数值"""
        memory_limit = memory_limit.lower()
        if 'gi' in memory_limit or 'gb' in memory_limit:
            return float(memory_limit.replace('gi', '').replace('gb', ''))
        elif 'mi' in memory_limit or 'mb' in memory_limit:
            return float(memory_limit.replace('mi', '').replace('mb', '')) / 1024
        else:
            # 默认按MB处理
            return float(memory_limit.replace('m', '')) / 1024
    
    async def _save_example_data(
        self, example_data: str, repository_id: int, service_name: str
    ) -> str:
        """保存示例数据"""
        try:
            import os
            import json
            
            # 创建目录
            data_dir = f"/data/examples/{repository_id}/{service_name}"
            os.makedirs(data_dir, exist_ok=True)
            
            # 保存数据
            file_path = f"{data_dir}/example_data.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json.loads(example_data), f, ensure_ascii=False, indent=2)
            
            logger.info(f"示例数据已保存到: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存示例数据失败: {e}")
            raise RuntimeError(f"保存示例数据失败: {str(e)}")

    async def _cleanup_example_data(self, example_data_path: str):
        """清理示例数据文件"""
        try:
            import os
            import shutil
            
            if os.path.exists(example_data_path):
                # 如果是文件，删除文件和其父目录（如果为空）
                if os.path.isfile(example_data_path):
                    os.remove(example_data_path)
                    parent_dir = os.path.dirname(example_data_path)
                    try:
                        os.rmdir(parent_dir)  # 只删除空目录
                    except OSError:
                        pass  # 目录不为空，忽略
                # 如果是目录，删除整个目录
                elif os.path.isdir(example_data_path):
                    shutil.rmtree(example_data_path)
                
                logger.info(f"示例数据已清理: {example_data_path}")
                
        except Exception as e:
            logger.warning(f"清理示例数据失败（但继续处理）: {e}")
    
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