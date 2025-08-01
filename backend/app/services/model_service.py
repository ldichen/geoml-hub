"""
模型服务管理器

这个模块提供了模型服务的完整生命周期管理：
- 服务创建、启动、停止、删除
- 容器编排和资源管理
- 健康检查和监控
- 自动清理和故障恢复
"""

import asyncio
import os
import time
import uuid
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

import docker
from docker.errors import DockerException, NotFound, APIError

from app.models.service import (
    ModelService,
    ServiceInstance,
    ServiceLog,
    ServiceHealthCheck,
)
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

logger = logging.getLogger(__name__)


class FailureType:
    """服务启动失败类型枚举"""

    TEMPORARY = "temporary"  # 临时错误，可以重试
    PERMANENT = "permanent"  # 永久错误，不应重试
    UNKNOWN = "unknown"  # 未知错误类型


class ServiceFailureAnalyzer:
    """服务启动失败分析器"""

    # 永久性错误关键词
    PERMANENT_ERROR_KEYWORDS = [
        "镜像不存在",
        "image not found",
        "repository does not exist",
        "配置错误",
        "configuration error",
        "invalid configuration",
        "权限不足",
        "permission denied",
        "access denied",
        "端口被占用",
        "port already in use",
        "address already in use",
        "磁盘空间不足",
        "no space left on device",
        "Docker守护进程未运行",
        "docker daemon not running",
        "无效的容器配置",
        "invalid container config",
        "证书验证失败",
        "certificate verification failed",
    ]

    # 临时性错误关键词
    TEMPORARY_ERROR_KEYWORDS = [
        "资源不足",
        "insufficient resources",
        "resource exhausted",
        "网络超时",
        "network timeout",
        "connection timeout",
        "连接被拒绝",
        "connection refused",
        "connection reset",
        "服务不可用",
        "service unavailable",
        "temporarily unavailable",
        "内存不足",
        "out of memory",
        "cannot allocate memory",
        "CPU使用率过高",
        "cpu usage too high",
        "系统繁忙",
        "system busy",
        "server busy",
        "Docker API超时",
        "docker api timeout",
    ]

    @classmethod
    def analyze_failure(cls, error_message: str) -> str:
        """分析错误消息，返回失败类型"""
        if not error_message:
            return FailureType.UNKNOWN

        error_message_lower = error_message.lower()

        # 检查是否为永久性错误
        for keyword in cls.PERMANENT_ERROR_KEYWORDS:
            if keyword.lower() in error_message_lower:
                return FailureType.PERMANENT

        # 检查是否为临时性错误
        for keyword in cls.TEMPORARY_ERROR_KEYWORDS:
            if keyword.lower() in error_message_lower:
                return FailureType.TEMPORARY

        return FailureType.UNKNOWN

    @classmethod
    def should_retry(cls, failure_type: str, retry_count: int) -> bool:
        """判断是否应该重试"""
        if failure_type == FailureType.PERMANENT:
            return False

        if retry_count >= settings.max_auto_start_retries:
            return False

        return True

    @classmethod
    def get_retry_delay(cls, retry_count: int) -> int:
        """计算重试延迟时间（指数退避）"""
        if not settings.exponential_backoff_enabled:
            return settings.startup_failure_retry_interval

        # 指数退避：60秒, 120秒, 240秒, 480秒...
        base_delay = settings.startup_failure_retry_interval
        exponential_delay = base_delay * (2**retry_count)

        # 不超过最大延迟时间
        return min(exponential_delay, settings.max_retry_delay)


class ModelServiceManager:
    """模型服务管理器"""

    def __init__(self):
        self.docker_client = None
        self.port_range_start = settings.service_port_start
        self.port_range_end = settings.service_port_end
        self.max_services_per_user = settings.max_services_per_user
        self.idle_timeout_minutes = settings.service_idle_timeout
        self.health_check_interval = settings.health_check_interval
        self.startup_timeout = settings.service_startup_timeout
        self.shutdown_timeout = settings.service_shutdown_timeout
        self.docker_image = settings.docker_image_name

        # 初始化Docker客户端
        self._init_docker_client()

    def _init_docker_client(self):
        """初始化Docker客户端"""
        try:
            # 根据配置连接Docker
            if settings.docker_ms_host.startswith("tcp://"):
                # TCP连接（可能需要TLS）
                if settings.docker_ms_tls_verify:
                    import ssl

                    # 优先使用单独的证书文件配置
                    if (
                        settings.docker_ms_ca_cert
                        and settings.docker_ms_client_cert
                        and settings.docker_ms_client_key
                    ):
                        tls_config = docker.tls.TLSConfig(
                            client_cert=(
                                settings.docker_ms_client_cert,
                                settings.docker_ms_client_key,
                            ),
                            ca_cert=settings.docker_ms_ca_cert,
                            verify=True,
                        )
                    # 使用证书目录配置
                    elif settings.docker_ms_cert_path:
                        tls_config = docker.tls.TLSConfig(
                            client_cert=(
                                f"{settings.docker_ms_cert_path}/cert.pem",
                                f"{settings.docker_ms_cert_path}/key.pem",
                            ),
                            ca_cert=f"{settings.docker_ms_cert_path}/ca.pem",
                            verify=True,
                        )
                    else:
                        raise ValueError("TLS验证已启用但未配置证书文件")

                    self.docker_client = docker.DockerClient(
                        base_url=settings.docker_ms_host,
                        tls=tls_config,
                        timeout=settings.docker_ms_timeout,
                    )
                    logger.info(
                        f"Docker TLS连接初始化成功，连接到: {settings.docker_ms_host}"
                    )
                else:
                    # 不使用TLS的TCP连接
                    self.docker_client = docker.DockerClient(
                        base_url=settings.docker_ms_host,
                        timeout=settings.docker_ms_timeout,
                    )
                    logger.info(
                        f"Docker TCP连接初始化成功，连接到: {settings.docker_ms_host}"
                    )
            elif settings.docker_ms_host.startswith("ssh://"):
                # SSH连接
                self.docker_client = docker.DockerClient(
                    base_url=settings.docker_ms_host, timeout=settings.docker_ms_timeout
                )
                logger.info(
                    f"Docker SSH连接初始化成功，连接到: {settings.docker_ms_host}"
                )
            else:
                # Unix socket或其他连接方式
                self.docker_client = docker.DockerClient(
                    base_url=settings.docker_ms_host, timeout=settings.docker_ms_timeout
                )
                logger.info(f"Docker连接初始化成功，连接到: {settings.docker_ms_host}")

            # 测试连接
            self.docker_client.ping()
            logger.info("Docker客户端连接测试成功")
        except Exception as e:
            logger.error(f"Docker客户端初始化失败: {e}")
            self.docker_client = None

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

        # 检查仓库服务数量限制
        await self._check_repository_service_limit(db, repository_id)

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
            model_id=service_data.model_id,  # 用户输入的模型ID
            model_ip="172.21.252.206",  # 固定的模型服务器IP
            description=service_data.description,
            cpu_limit=service_data.cpu_limit,
            memory_limit=service_data.memory_limit,
            is_public=service_data.is_public,
            priority=service_data.priority,
            status=ServiceStatus.CREATED,
            access_token=self._generate_access_token(),
            # 新增Docker相关字段
            docker_image=service_data.model_id,  # 将model_id用作Docker镜像名
            health_status="unknown",
            error_message=None,
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
            # 停止现有容器（如果存在）
            if service.container_id and force_restart:
                await self._stop_container(service.container_id)

            # 更新状态为启动中
            service.status = ServiceStatus.STARTING
            service.last_started_at = datetime.utcnow()
            service.start_count += 1
            await db.commit()

            # 检查资源可用性
            is_available, message = await resource_manager.check_resource_availability(
                db, service.cpu_limit, service.memory_limit
            )
            if not is_available:
                raise ValueError(f"资源不足: {message}")

            # 分配端口
            port = await resource_manager.allocate_port(db)

            # 启动容器
            container_info = await self._start_container(service, port)

            # 创建服务实例记录
            instance = ServiceInstance(
                service_id=service.id,
                container_id=container_info["container_id"],
                container_name=container_info["container_name"],
                image_name=container_info.get("image_name", "geoml-service:latest"),
                host_port=port,
                container_port=7860,
                status="starting",
            )
            db.add(instance)

            # 更新服务信息
            service.container_id = container_info["container_id"]
            service.gradio_port = port

            # 根据TLS配置生成服务URL
            if settings.service_tls_enabled:
                service.service_url = f"https://{settings.service_domain}:{port}"
            else:
                service.service_url = f"http://{settings.service_domain}:{port}"

            service.status = ServiceStatus.RUNNING

            await db.commit()
            await db.refresh(service)

            # 记录启动日志
            await self._log_service_event(
                db,
                service.id,
                LogLevel.INFO,
                f"服务启动成功，端口: {port}",
                EventType.START,
                user_id,
            )

            # 启动健康检查
            asyncio.create_task(self._start_health_monitoring(db, service.id))

            return ServiceResponse.from_orm(service)

        except Exception as e:
            # 启动失败，更新状态
            service.status = ServiceStatus.ERROR
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

        # 检查当前状态
        if service.status in [ServiceStatus.STOPPED, ServiceStatus.STOPPING]:
            return ServiceResponse.from_orm(service)

        try:
            # 更新状态为停止中
            service.status = ServiceStatus.STOPPING
            await db.commit()

            # 停止容器
            if service.container_id:
                await self._stop_container(service.container_id, timeout_seconds)

            # 更新服务实例状态
            instance_query = select(ServiceInstance).where(
                ServiceInstance.service_id == service_id
            )
            result = await db.execute(instance_query)
            instance = result.scalar_one_or_none()

            if instance:
                instance.status = "stopped"
                instance.stopped_at = datetime.utcnow()

            # 更新服务状态
            service.status = ServiceStatus.STOPPED
            service.last_stopped_at = datetime.utcnow()
            service.container_id = None
            service.gradio_port = None
            service.service_url = None

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
                await self.stop_service(db, service_id, user_id, force_stop=True)

            # 清理相关数据
            if service.container_id:
                await self._cleanup_container(service.container_id)

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

        # 获取最新的健康检查结果
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

        # 获取资源使用情况
        resource_usage = None
        if service.container_id:
            resource_usage = await self._get_container_resource_usage(
                service.container_id
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
            "resource_usage": resource_usage,
            "last_health_check": (
                latest_health_check.checked_at if latest_health_check else None
            ),
            "error_message": (
                latest_health_check.error_message
                if latest_health_check
                and latest_health_check.status != HealthStatus.HEALTHY
                else None
            ),
        }

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
                # 执行HTTP健康检查
                import aiohttp
                import asyncio

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

        # 更新服务的最后健康检查时间
        service.last_health_check = datetime.utcnow()

        await db.commit()
        await db.refresh(health_check)

        return health_check

    async def cleanup_idle_services(self, db: AsyncSession):
        """清理空闲服务"""

        idle_threshold = datetime.utcnow() - timedelta(
            minutes=self.idle_timeout_minutes
        )

        # 查找空闲服务
        idle_services_query = select(ModelService).where(
            and_(
                ModelService.status == ServiceStatus.RUNNING,
                or_(
                    ModelService.last_accessed_at < idle_threshold,
                    ModelService.last_accessed_at.is_(None),
                ),
            )
        )

        result = await db.execute(idle_services_query)
        idle_services = result.scalars().all()

        cleaned_count = 0
        for service in idle_services:
            try:
                # 标记为空闲状态
                service.status = ServiceStatus.IDLE
                await db.commit()

                # 记录日志
                await self._log_service_event(
                    db,
                    service.id,
                    LogLevel.INFO,
                    "服务因空闲被自动停止",
                    EventType.STOP,
                    None,
                )

                # 停止容器但保留服务记录
                if service.container_id:
                    await self._stop_container(service.container_id)
                    service.container_id = None
                    service.gradio_port = None
                    service.service_url = None

                cleaned_count += 1

            except Exception as e:
                logger.error(f"清理空闲服务 {service.id} 失败: {e}")

        logger.info(f"已清理 {cleaned_count} 个空闲服务")
        return cleaned_count

    async def auto_start_repository_services(
        self, db: AsyncSession, repository_id: int, user_id: int
    ) -> Dict[str, Any]:
        """自动启动仓库下的所有服务"""

        if not settings.auto_start_on_visit:
            return {"auto_start_enabled": False, "services": []}

        # 获取仓库下的所有服务
        if settings.startup_priority_enabled:
            # 按优先级排序，然后按创建时间排序
            services_query = (
                select(ModelService)
                .where(ModelService.repository_id == repository_id)
                .order_by(ModelService.priority.asc(), ModelService.created_at.asc())
            )
        else:
            # 只按创建时间排序
            services_query = (
                select(ModelService)
                .where(ModelService.repository_id == repository_id)
                .order_by(ModelService.created_at.asc())
            )

        result = await db.execute(services_query)
        services = result.scalars().all()

        if not services:
            return {
                "auto_start_enabled": True,
                "services": [],
                "message": "该仓库暂无服务",
            }

        # 检查用户当前运行的服务数量
        current_running = await self._get_user_running_services_count(db, user_id)
        available_slots = settings.max_services_per_user - current_running

        startup_results = []
        started_count = 0

        for service in services:
            if started_count >= min(available_slots, len(services)):
                # 已达到可启动的服务数量限制
                startup_results.append(
                    {
                        "service_id": service.id,
                        "service_name": service.service_name,
                        "status": "queued",
                        "message": "资源不足，已加入启动队列",
                    }
                )
                continue

            try:
                # 如果服务已经在运行，跳过
                if service.status == ServiceStatus.RUNNING:
                    startup_results.append(
                        {
                            "service_id": service.id,
                            "service_name": service.service_name,
                            "status": "already_running",
                            "service_url": service.service_url,
                            "priority": service.priority,
                        }
                    )
                    continue

                # 检查服务是否处于错误状态且需要重试
                if service.status == ServiceStatus.ERROR:
                    # 智能重试判断
                    failure_type = service.failure_type or FailureType.UNKNOWN
                    retry_count = service.auto_start_retry_count or 0

                    # 检查是否应该重试
                    if not ServiceFailureAnalyzer.should_retry(
                        failure_type, retry_count
                    ):
                        if failure_type == FailureType.PERMANENT:
                            startup_results.append(
                                {
                                    "service_id": service.id,
                                    "service_name": service.service_name,
                                    "status": "permanently_failed",
                                    "message": f"永久性错误，不再重试: {service.last_failure_reason}",
                                    "priority": service.priority,
                                    "retry_count": retry_count,
                                    "failure_type": failure_type,
                                }
                            )
                        else:
                            startup_results.append(
                                {
                                    "service_id": service.id,
                                    "service_name": service.service_name,
                                    "status": "retry_exhausted",
                                    "message": f"已达到最大重试次数({settings.max_auto_start_retries})，停止重试",
                                    "priority": service.priority,
                                    "retry_count": retry_count,
                                    "failure_type": failure_type,
                                }
                            )
                        continue

                    # 检查重试冷却时间
                    if service.last_started_at:
                        from datetime import datetime, timedelta

                        time_since_failure = datetime.utcnow() - service.last_started_at
                        required_delay = ServiceFailureAnalyzer.get_retry_delay(
                            retry_count
                        )

                        if time_since_failure.total_seconds() < required_delay:
                            remaining_time = required_delay - int(
                                time_since_failure.total_seconds()
                            )
                            startup_results.append(
                                {
                                    "service_id": service.id,
                                    "service_name": service.service_name,
                                    "status": "retry_pending",
                                    "message": f"重试冷却中，{remaining_time}秒后可重试 (第{retry_count + 1}次重试)",
                                    "priority": service.priority,
                                    "retry_count": retry_count,
                                    "failure_type": failure_type,
                                    "next_retry_in": remaining_time,
                                }
                            )
                            continue

                # 尝试启动服务
                updated_service = await self.start_service(
                    db, service.id, user_id, force_restart=False
                )
                started_count += 1

                startup_results.append(
                    {
                        "service_id": service.id,
                        "service_name": service.service_name,
                        "status": "starting",
                        "message": "服务启动中...",
                        "service_url": updated_service.service_url,
                        "priority": service.priority,
                    }
                )

            except ValueError as e:
                # 资源不足等业务逻辑错误
                error_message = str(e)
                failure_type = ServiceFailureAnalyzer.analyze_failure(error_message)

                # 更新服务状态和重试信息
                service.auto_start_retry_count = (
                    service.auto_start_retry_count or 0
                ) + 1
                service.last_failure_reason = error_message
                service.failure_type = failure_type
                await db.commit()

                startup_results.append(
                    {
                        "service_id": service.id,
                        "service_name": service.service_name,
                        "status": "resource_error",
                        "message": error_message,
                        "priority": service.priority,
                        "retry_count": service.auto_start_retry_count,
                        "failure_type": failure_type,
                    }
                )

                # 记录启动失败日志
                await self._log_service_event(
                    db,
                    service.id,
                    LogLevel.WARNING,
                    f"自动启动失败(资源问题): {error_message}",
                    EventType.ERROR,
                    user_id,
                )

            except Exception as e:
                # 其他系统错误
                error_message = str(e)
                failure_type = ServiceFailureAnalyzer.analyze_failure(error_message)

                # 更新服务状态和重试信息
                service.auto_start_retry_count = (
                    service.auto_start_retry_count or 0
                ) + 1
                service.last_failure_reason = error_message
                service.failure_type = failure_type
                await db.commit()

                startup_results.append(
                    {
                        "service_id": service.id,
                        "service_name": service.service_name,
                        "status": "system_error",
                        "message": f"系统错误: {error_message}",
                        "priority": service.priority,
                        "retry_count": service.auto_start_retry_count,
                        "failure_type": failure_type,
                    }
                )

                # 记录启动失败日志
                await self._log_service_event(
                    db,
                    service.id,
                    LogLevel.ERROR,
                    f"自动启动失败(系统错误): {error_message}",
                    EventType.ERROR,
                    user_id,
                )

        return {
            "auto_start_enabled": True,
            "services": startup_results,
            "started_count": started_count,
            "total_services": len(services),
            "available_slots": available_slots,
        }

    # 私有方法
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

    async def _get_user_running_services_count(
        self, db: AsyncSession, user_id: int
    ) -> int:
        """获取用户当前运行的服务数量"""

        active_services_query = select(func.count(ModelService.id)).where(
            and_(
                ModelService.user_id == user_id,
                ModelService.status.in_(
                    [ServiceStatus.RUNNING, ServiceStatus.STARTING]
                ),
            )
        )

        result = await db.execute(active_services_query)
        return result.scalar() or 0

    async def _check_repository_service_limit(
        self, db: AsyncSession, repository_id: int
    ):
        """检查仓库服务数量限制"""

        repository_services_query = select(func.count(ModelService.id)).where(
            ModelService.repository_id == repository_id
        )

        result = await db.execute(repository_services_query)
        service_count = result.scalar()

        if service_count >= settings.max_services_per_repository:
            raise ValueError(
                f"该仓库已达到最大服务数量限制 ({settings.max_services_per_repository})"
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

        service_query = select(ModelService).where(ModelService.id == service_id)
        result = await db.execute(service_query)
        service = result.scalar_one_or_none()

        if not service:
            raise ValueError(f"服务 {service_id} 不存在")

        return service

    def _generate_access_token(self) -> str:
        """生成访问令牌"""
        return f"geoml-{uuid.uuid4().hex[:16]}"

    async def _start_container(
        self, service: ModelService, port: int
    ) -> Dict[str, str]:
        """启动Docker容器"""

        if not self.docker_client:
            raise RuntimeError("Docker客户端未初始化")

        container_name = f"geoml-service-{service.id}-{uuid.uuid4().hex[:8]}"

        try:
            # 准备容器配置
            container_config = {
                "image": self.docker_image,
                "name": container_name,
                "environment": {
                    "MODEL_IP": service.model_ip,
                    "MODEL_ID": service.model_id,
                    "GRADIO_SERVER_PORT": str(port),
                    "EXAMPLE_DATA_PATH": "/app/examples",  # 固定容器内路径
                    "SERVICE_NAME": service.service_name,
                },
                "ports": {f"{port}/tcp": port},
                "mem_limit": service.memory_limit,
                "cpu_period": 100000,
                "cpu_quota": int(float(service.cpu_limit) * 100000),  # CPU限制转换
                "detach": True,
                "remove": False,
                "labels": {
                    "geoml.service.id": str(service.id),
                    "geoml.service.name": service.service_name,
                    "geoml.managed": "true",
                },
            }

            # 配置volume挂载
            volumes = {}

            # 如果有examples文件，添加volume挂载
            if service.example_data_path and os.path.exists(service.example_data_path):
                volumes[service.example_data_path] = {
                    "bind": "/app/examples",
                    "mode": "ro",  # 只读挂载
                }

            # 如果启用了TLS，挂载证书文件
            if settings.service_tls_enabled:
                if settings.service_tls_cert_path and os.path.exists(
                    settings.service_tls_cert_path
                ):
                    volumes[settings.service_tls_cert_path] = {
                        "bind": "/app/certs/cert.pem",
                        "mode": "ro",
                    }

                if settings.service_tls_key_path and os.path.exists(
                    settings.service_tls_key_path
                ):
                    volumes[settings.service_tls_key_path] = {
                        "bind": "/app/certs/key.pem",
                        "mode": "ro",
                    }

                # 添加TLS环境变量
                container_config["environment"]["TLS_ENABLED"] = "true"
                container_config["environment"]["TLS_CERT_PATH"] = "/app/certs/cert.pem"
                container_config["environment"]["TLS_KEY_PATH"] = "/app/certs/key.pem"

            if volumes:
                container_config["volumes"] = volumes

            container = self.docker_client.containers.run(**container_config)

            return {
                "container_id": container.id,
                "container_name": container_name,
                "image_name": self.docker_image,
            }

        except DockerException as e:
            logger.error(f"启动容器失败: {e}")
            raise RuntimeError(f"容器启动失败: {str(e)}")

    async def _stop_container(self, container_id: str, timeout: int = 30):
        """停止Docker容器"""

        if not self.docker_client:
            return

        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=timeout or self.shutdown_timeout)
            logger.info(f"容器 {container_id} 停止成功")
        except NotFound:
            logger.warning(f"容器 {container_id} 不存在")
        except Exception as e:
            logger.error(f"停止容器 {container_id} 失败: {e}")
            raise

    async def _cleanup_container(self, container_id: str):
        """清理Docker容器"""

        if not self.docker_client:
            return

        try:
            container = self.docker_client.containers.get(container_id)
            container.remove(force=True)
            logger.info(f"容器 {container_id} 清理成功")
        except NotFound:
            logger.info(f"容器 {container_id} 已不存在")
        except Exception as e:
            logger.error(f"清理容器 {container_id} 失败: {e}")

    async def _get_container_resource_usage(
        self, container_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取容器资源使用情况"""

        if not self.docker_client:
            return None

        try:
            container = self.docker_client.containers.get(container_id)
            stats = container.stats(stream=False)

            # 计算CPU使用率
            cpu_percent = 0.0
            if "cpu_stats" in stats and "precpu_stats" in stats:
                cpu_stats = stats["cpu_stats"]
                precpu_stats = stats["precpu_stats"]

                cpu_delta = (
                    cpu_stats["cpu_usage"]["total_usage"]
                    - precpu_stats["cpu_usage"]["total_usage"]
                )
                system_delta = (
                    cpu_stats["system_cpu_usage"] - precpu_stats["system_cpu_usage"]
                )

                if system_delta > 0:
                    cpu_percent = (
                        (cpu_delta / system_delta)
                        * len(cpu_stats["cpu_usage"]["percpu_usage"])
                        * 100.0
                    )

            # 计算内存使用情况
            memory_usage = stats.get("memory_stats", {}).get("usage", 0)
            memory_limit = stats.get("memory_stats", {}).get("limit", 0)
            memory_percent = (
                (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
            )

            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_mb": round(memory_usage / 1024 / 1024, 2),
                "memory_percent": round(memory_percent, 2),
            }

        except Exception as e:
            logger.error(f"获取容器 {container_id} 资源使用情况失败: {e}")
            return None

    async def _save_example_data(
        self, example_data: str, repository_id: int, service_name: str
    ) -> str:
        """保存示例数据"""
        # 这里应该实现示例数据的保存逻辑
        # 可以保存到MinIO或本地文件系统
        # 返回保存后的文件路径
        return f"/data/examples/{repository_id}/{service_name}/example_data.json"

    async def _cleanup_example_data(self, example_data_path: str):
        """清理示例数据文件"""
        # 实现示例数据文件的清理逻辑
        pass

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
                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"健康监控服务 {service_id} 失败: {e}")
                await asyncio.sleep(self.health_check_interval)
                break
