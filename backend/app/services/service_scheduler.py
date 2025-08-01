"""
服务调度器
负责定期执行服务管理任务，如健康检查、空闲服务清理、资源统计等
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_db
from app.models.service import ModelService
from app.services.model_service import ModelServiceManager
from app.utils.resource_manager import resource_manager
from app.config import settings

logger = logging.getLogger(__name__)


class ServiceScheduler:
    """服务调度器"""
    
    def __init__(self):
        self.service_manager = ModelServiceManager()
        self.is_running = False
        self._tasks = []
    
    async def start(self):
        """启动调度器"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("服务调度器启动")
        
        # 启动各种定期任务
        self._tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._cleanup_idle_services_loop()),
            asyncio.create_task(self._resource_monitoring_loop()),
            asyncio.create_task(self._port_cleanup_loop()),
            asyncio.create_task(self._retry_failed_services_loop())
        ]
    
    async def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("服务调度器停止中...")
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 等待所有任务完成
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        logger.info("服务调度器已停止")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self.is_running:
            try:
                async for db in get_async_db():
                    # 获取所有运行中的服务
                    running_services_query = select(ModelService).where(
                        ModelService.status == 'running'
                    )
                    result = await db.execute(running_services_query)
                    running_services = result.scalars().all()
                    
                    # 对每个服务执行健康检查
                    for service in running_services:
                        try:
                            await self.service_manager.perform_health_check(db, service.id)
                        except Exception as e:
                            logger.error(f"服务 {service.id} 健康检查失败: {e}")
                    
                    break  # 跳出异步生成器循环
                
                # 等待下次检查
                await asyncio.sleep(settings.health_check_interval)
                
            except Exception as e:
                logger.error(f"健康检查循环出错: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟再重试
    
    async def _cleanup_idle_services_loop(self):
        """清理空闲服务循环"""
        while self.is_running:
            try:
                async for db in get_async_db():
                    cleaned_count = await self.service_manager.cleanup_idle_services(db)
                    if cleaned_count > 0:
                        logger.info(f"清理了 {cleaned_count} 个空闲服务")
                    break
                
                # 每10分钟检查一次
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"空闲服务清理循环出错: {e}")
                await asyncio.sleep(300)  # 出错时等待5分钟再重试
    
    async def _resource_monitoring_loop(self):
        """资源监控循环"""
        while self.is_running:
            try:
                async for db in get_async_db():
                    # 获取资源统计
                    stats = await resource_manager.get_resource_statistics(db)
                    
                    # 记录资源使用情况
                    system_resources = stats["system_resources"]
                    service_resources = stats["service_resources"]
                    
                    if system_resources["cpu_usage_percent"] > 80:
                        logger.warning(f"系统CPU使用率过高: {system_resources['cpu_usage_percent']:.1f}%")
                    
                    if system_resources["memory_usage_percent"] > 80:
                        logger.warning(f"系统内存使用率过高: {system_resources['memory_usage_percent']:.1f}%")
                    
                    if system_resources["disk_usage_percent"] > 90:
                        logger.warning(f"系统磁盘使用率过高: {system_resources['disk_usage_percent']:.1f}%")
                    
                    # 记录服务资源使用情况
                    logger.debug(f"运行中服务: {service_resources['running_services']}, "
                               f"CPU占用: {service_resources['cpu_utilization']:.1f}%, "
                               f"内存占用: {service_resources['memory_utilization']:.1f}%")
                    
                    break
                
                # 每5分钟监控一次
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"资源监控循环出错: {e}")
                await asyncio.sleep(300)
    
    async def _port_cleanup_loop(self):
        """端口清理循环"""
        while self.is_running:
            try:
                async for db in get_async_db():
                    cleaned_count = await resource_manager.cleanup_unused_ports(db)
                    if cleaned_count > 0:
                        logger.info(f"清理了 {cleaned_count} 个未使用的端口记录")
                    break
                
                # 每30分钟清理一次
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.error(f"端口清理循环出错: {e}")
                await asyncio.sleep(600)
    
    async def _retry_failed_services_loop(self):
        """重试失败服务循环"""
        while self.is_running:
            try:
                async for db in get_async_db():
                    # 查找需要重试的服务
                    retry_threshold = datetime.utcnow() - timedelta(minutes=5)
                    
                    failed_services_query = select(ModelService).where(
                        ModelService.status == 'error',
                        ModelService.auto_start_retry_count < settings.max_auto_start_retries,
                        ModelService.failure_type != 'permanent',
                        ModelService.last_started_at < retry_threshold
                    )
                    
                    result = await db.execute(failed_services_query)
                    failed_services = result.scalars().all()
                    
                    for service in failed_services:
                        try:
                            # 检查重试延迟
                            from app.services.model_service import ServiceFailureAnalyzer
                            
                            retry_count = service.auto_start_retry_count or 0
                            required_delay = ServiceFailureAnalyzer.get_retry_delay(retry_count)
                            
                            if service.last_started_at:
                                time_since_failure = datetime.utcnow() - service.last_started_at
                                if time_since_failure.total_seconds() < required_delay:
                                    continue  # 还未到重试时间
                            
                            # 尝试重新启动服务
                            logger.info(f"尝试重启失败的服务 {service.id} (第{retry_count + 1}次重试)")
                            
                            await self.service_manager.start_service(
                                db=db,
                                service_id=service.id,
                                user_id=service.user_id,
                                force_restart=True
                            )
                            
                        except Exception as e:
                            logger.error(f"重试启动服务 {service.id} 失败: {e}")
                            # 更新失败信息
                            service.auto_start_retry_count = (service.auto_start_retry_count or 0) + 1
                            service.last_failure_reason = str(e)
                            await db.commit()
                    
                    break
                
                # 每2分钟检查一次
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"重试失败服务循环出错: {e}")
                await asyncio.sleep(300)


# 全局调度器实例
service_scheduler = ServiceScheduler()