"""
资源管理工具

这个模块提供了系统资源管理的功能：
- 端口分配和释放
- 资源限制验证
- 系统资源监控
- 配额管理
"""

import re
import psutil
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.service import ModelService
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_usage_gb: float
    disk_percent: float
    network_io: Dict[str, int]


@dataclass
class ResourceLimits:
    """资源限制"""
    cpu_cores: float
    memory_mb: int
    is_valid: bool
    error_message: Optional[str] = None


class ResourceManager:
    """资源管理器"""
    
    def __init__(self):
        self.port_range_start = settings.service_port_start
        self.port_range_end = settings.service_port_end
        self.max_cpu_limit = settings.max_cpu_limit
        self.max_memory_limit = settings.max_memory_limit
        self.default_cpu_limit = settings.default_cpu_limit
        self.default_memory_limit = settings.default_memory_limit
    
    async def allocate_port(self, db: AsyncSession, exclude_ports: Optional[Set[int]] = None) -> int:
        """分配可用端口"""
        
        # 获取已使用的端口
        used_ports_query = select(ModelService.gradio_port).where(
            ModelService.gradio_port.isnot(None)
        )
        result = await db.execute(used_ports_query)
        used_ports = {port for (port,) in result.fetchall() if port}
        
        # 添加排除的端口
        if exclude_ports:
            used_ports.update(exclude_ports)
        
        # 检查系统端口使用情况
        system_used_ports = self._get_system_used_ports()
        used_ports.update(system_used_ports)
        
        # 查找可用端口
        available_ports = set(range(self.port_range_start, self.port_range_end)) - used_ports
        
        if not available_ports:
            raise RuntimeError(f"端口范围 {self.port_range_start}-{self.port_range_end} 内没有可用端口")
        
        # 返回最小可用端口
        allocated_port = min(available_ports)
        logger.info(f"分配端口: {allocated_port}")
        return allocated_port
    
    def _get_system_used_ports(self) -> Set[int]:
        """获取系统已使用的端口"""
        used_ports = set()
        
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.laddr and self.port_range_start <= conn.laddr.port <= self.port_range_end:
                    used_ports.add(conn.laddr.port)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            logger.warning("无法获取系统端口使用情况，可能需要管理员权限")
        
        return used_ports
    
    def validate_resource_limits(self, cpu_limit: str, memory_limit: str) -> ResourceLimits:
        """验证资源限制"""
        
        try:
            # 验证CPU限制
            cpu_cores = self._parse_cpu_limit(cpu_limit)
            max_cpu_cores = self._parse_cpu_limit(self.max_cpu_limit)
            
            if cpu_cores <= 0 or cpu_cores > max_cpu_cores:
                return ResourceLimits(
                    cpu_cores=0,
                    memory_mb=0,
                    is_valid=False,
                    error_message=f"CPU限制必须在 0 到 {max_cpu_cores} 核之间"
                )
            
            # 验证内存限制
            memory_mb = self._parse_memory_limit(memory_limit)
            max_memory_mb = self._parse_memory_limit(self.max_memory_limit)
            
            if memory_mb <= 0 or memory_mb > max_memory_mb:
                return ResourceLimits(
                    cpu_cores=0,
                    memory_mb=0,
                    is_valid=False,
                    error_message=f"内存限制必须在 0 到 {max_memory_mb}MB 之间"
                )
            
            return ResourceLimits(
                cpu_cores=cpu_cores,
                memory_mb=memory_mb,
                is_valid=True
            )
            
        except ValueError as e:
            return ResourceLimits(
                cpu_cores=0,
                memory_mb=0,
                is_valid=False,
                error_message=f"资源限制格式错误: {str(e)}"
            )
    
    def _parse_cpu_limit(self, cpu_limit: str) -> float:
        """解析CPU限制"""
        if not cpu_limit:
            raise ValueError("CPU限制不能为空")
        
        try:
            # 支持格式: "1.0", "1", "500m" (millicores)
            cpu_limit = cpu_limit.strip().lower()
            
            if cpu_limit.endswith('m'):
                # millicores格式
                millicores = int(cpu_limit[:-1])
                return millicores / 1000.0
            else:
                # 直接的浮点数格式
                return float(cpu_limit)
                
        except ValueError:
            raise ValueError(f"无效的CPU限制格式: {cpu_limit}")
    
    def _parse_memory_limit(self, memory_limit: str) -> int:
        """解析内存限制，返回MB"""
        if not memory_limit:
            raise ValueError("内存限制不能为空")
        
        try:
            memory_limit = memory_limit.strip().upper()
            
            # 解析数字和单位
            match = re.match(r'^(\d+(?:\.\d+)?)([KMGT]?I?B?)$', memory_limit)
            if not match:
                raise ValueError(f"无效的内存限制格式: {memory_limit}")
            
            value, unit = match.groups()
            value = float(value)
            
            # 转换为MB
            unit_multipliers = {
                '': 1,  # 默认为字节
                'B': 1,
                'K': 1024,
                'KB': 1024,
                'KI': 1024,
                'KIB': 1024,
                'M': 1024 * 1024,
                'MB': 1024 * 1024,
                'MI': 1024 * 1024,
                'MIB': 1024 * 1024,
                'G': 1024 * 1024 * 1024,
                'GB': 1024 * 1024 * 1024,
                'GI': 1024 * 1024 * 1024,
                'GIB': 1024 * 1024 * 1024,
                'T': 1024 * 1024 * 1024 * 1024,
                'TB': 1024 * 1024 * 1024 * 1024,
                'TI': 1024 * 1024 * 1024 * 1024,
                'TIB': 1024 * 1024 * 1024 * 1024,
            }
            
            if unit not in unit_multipliers:
                raise ValueError(f"不支持的内存单位: {unit}")
            
            bytes_value = value * unit_multipliers[unit]
            mb_value = int(bytes_value / (1024 * 1024))
            
            return mb_value
            
        except (ValueError, AttributeError):
            raise ValueError(f"无效的内存限制格式: {memory_limit}")
    
    def get_system_resource_usage(self) -> ResourceUsage:
        """获取系统资源使用情况"""
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            memory_percent = memory.percent
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_usage_gb = disk.used / 1024 / 1024 / 1024
            disk_percent = disk.percent
            
            # 网络IO
            network_io = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv
            }
            
            return ResourceUsage(
                cpu_percent=round(cpu_percent, 2),
                memory_mb=round(memory_mb, 2),
                memory_percent=round(memory_percent, 2),
                disk_usage_gb=round(disk_usage_gb, 2),
                disk_percent=round(disk_percent, 2),
                network_io=network_stats
            )
            
        except Exception as e:
            logger.error(f"获取系统资源使用情况失败: {e}")
            return ResourceUsage(
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                disk_usage_gb=0.0,
                disk_percent=0.0,
                network_io={}
            )
    
    async def check_resource_availability(
        self, 
        db: AsyncSession, 
        cpu_limit: str, 
        memory_limit: str
    ) -> Tuple[bool, str]:
        """检查资源可用性"""
        
        # 验证资源限制格式
        limits = self.validate_resource_limits(cpu_limit, memory_limit)
        if not limits.is_valid:
            return False, limits.error_message
        
        # 获取当前系统资源使用情况
        system_usage = self.get_system_resource_usage()
        
        # 获取所有运行中服务的资源占用
        running_services_query = select(ModelService).where(
            ModelService.status == 'running'
        )
        result = await db.execute(running_services_query)
        running_services = result.scalars().all()
        
        # 计算已分配的资源
        allocated_cpu = 0.0
        allocated_memory = 0
        
        for service in running_services:
            try:
                service_cpu = self._parse_cpu_limit(service.cpu_limit)
                service_memory = self._parse_memory_limit(service.memory_limit)
                allocated_cpu += service_cpu
                allocated_memory += service_memory
            except ValueError:
                logger.warning(f"服务 {service.id} 的资源限制格式错误")
                continue
        
        # 检查CPU可用性
        total_cpu_cores = psutil.cpu_count()
        available_cpu = total_cpu_cores - (system_usage.cpu_percent / 100 * total_cpu_cores) - allocated_cpu
        
        if limits.cpu_cores > available_cpu:
            return False, f"CPU资源不足，需要 {limits.cpu_cores} 核，可用 {available_cpu:.2f} 核"
        
        # 检查内存可用性
        total_memory_mb = psutil.virtual_memory().total / 1024 / 1024
        available_memory = total_memory_mb - system_usage.memory_mb - allocated_memory
        
        if limits.memory_mb > available_memory:
            return False, f"内存资源不足，需要 {limits.memory_mb}MB，可用 {available_memory:.0f}MB"
        
        return True, "资源充足"
    
    async def get_resource_statistics(self, db: AsyncSession) -> Dict[str, any]:
        """获取资源统计信息"""
        
        # 系统资源
        system_usage = self.get_system_resource_usage()
        
        # 服务统计
        total_services_query = select(func.count(ModelService.id))
        running_services_query = select(func.count(ModelService.id)).where(
            ModelService.status == 'running'
        )
        
        total_result = await db.execute(total_services_query)
        running_result = await db.execute(running_services_query)
        
        total_services = total_result.scalar()
        running_services = running_result.scalar()
        
        # 端口使用情况
        used_ports_query = select(func.count(ModelService.gradio_port)).where(
            ModelService.gradio_port.isnot(None)
        )
        used_ports_result = await db.execute(used_ports_query)
        used_ports_count = used_ports_result.scalar()
        
        total_ports = self.port_range_end - self.port_range_start
        available_ports = total_ports - used_ports_count
        
        # 计算资源利用率
        running_services_list_query = select(ModelService).where(
            ModelService.status == 'running'
        )
        services_result = await db.execute(running_services_list_query)
        services_list = services_result.scalars().all()
        
        allocated_cpu = 0.0
        allocated_memory = 0
        
        for service in services_list:
            try:
                allocated_cpu += self._parse_cpu_limit(service.cpu_limit)
                allocated_memory += self._parse_memory_limit(service.memory_limit)
            except ValueError:
                continue
        
        total_cpu_cores = psutil.cpu_count()
        total_memory_mb = psutil.virtual_memory().total / 1024 / 1024
        
        return {
            "system_resources": {
                "cpu_cores": total_cpu_cores,
                "cpu_usage_percent": system_usage.cpu_percent,
                "total_memory_mb": int(total_memory_mb),
                "memory_usage_mb": system_usage.memory_mb,
                "memory_usage_percent": system_usage.memory_percent,
                "disk_usage_gb": system_usage.disk_usage_gb,
                "disk_usage_percent": system_usage.disk_percent
            },
            "service_resources": {
                "total_services": total_services,
                "running_services": running_services,
                "allocated_cpu_cores": allocated_cpu,
                "allocated_memory_mb": allocated_memory,
                "cpu_utilization": (allocated_cpu / total_cpu_cores) * 100,
                "memory_utilization": (allocated_memory / total_memory_mb) * 100
            },
            "port_management": {
                "total_ports": total_ports,
                "used_ports": used_ports_count,
                "available_ports": available_ports,
                "port_range": f"{self.port_range_start}-{self.port_range_end}"
            },
            "limits": {
                "max_services_per_user": settings.max_services_per_user,
                "max_cpu_limit": self.max_cpu_limit,
                "max_memory_limit": self.max_memory_limit,
                "service_idle_timeout_minutes": settings.service_idle_timeout
            }
        }
    
    def format_resource_limit(self, cpu_limit: str, memory_limit: str) -> str:
        """格式化资源限制显示"""
        try:
            cpu_cores = self._parse_cpu_limit(cpu_limit)
            memory_mb = self._parse_memory_limit(memory_limit)
            
            # 格式化显示
            cpu_str = f"{cpu_cores} cores" if cpu_cores >= 1 else f"{int(cpu_cores * 1000)}m"
            
            if memory_mb >= 1024:
                memory_str = f"{memory_mb / 1024:.1f}Gi"
            else:
                memory_str = f"{memory_mb}Mi"
            
            return f"CPU: {cpu_str}, Memory: {memory_str}"
            
        except ValueError:
            return f"CPU: {cpu_limit}, Memory: {memory_limit}"
    
    async def cleanup_unused_ports(self, db: AsyncSession) -> int:
        """清理未使用的端口记录"""
        
        # 获取数据库中记录的端口
        db_ports_query = select(ModelService.gradio_port).where(
            ModelService.gradio_port.isnot(None)
        )
        result = await db.execute(db_ports_query)
        db_ports = {port for (port,) in result.fetchall() if port}
        
        # 获取系统实际使用的端口
        system_ports = self._get_system_used_ports()
        
        # 找到数据库中记录但系统未使用的端口
        unused_ports = db_ports - system_ports
        
        # 清理未使用的端口记录
        if unused_ports:
            cleanup_query = select(ModelService).where(
                ModelService.gradio_port.in_(unused_ports)
            )
            cleanup_result = await db.execute(cleanup_query)
            services_to_cleanup = cleanup_result.scalars().all()
            
            for service in services_to_cleanup:
                if service.status not in ['running', 'starting']:
                    service.gradio_port = None
                    logger.info(f"清理服务 {service.id} 的未使用端口 {service.gradio_port}")
            
            await db.commit()
        
        return len(unused_ports)


# 全局资源管理器实例
resource_manager = ResourceManager()