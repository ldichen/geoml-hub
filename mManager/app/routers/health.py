"""
健康检查和系统信息路由
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any

from app.config import settings, get_server_capabilities
from app.models.container import SystemInfo
from app.services.docker_service import docker_service

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查接口"""
    try:
        # 获取系统信息
        system_info = await docker_service.get_system_info()
        
        # 计算负载百分比
        load_percentage = (system_info.containers_running / settings.max_containers) * 100
        
        # 检查系统状态
        status = "healthy"
        if system_info.containers_running >= settings.max_containers * 0.9:
            status = "warning"  # 90%以上负载告警
        elif system_info.memory_available_gb < 1.0:
            status = "critical"  # 可用内存小于1GB
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "server_id": settings.server_id,
            "server_type": settings.server_type,
            "docker_version": system_info.docker_version,
            "containers": {
                "total": system_info.containers_total,
                "running": system_info.containers_running,
                "stopped": system_info.containers_stopped,
                "max_allowed": settings.max_containers
            },
            "resources": {
                "cpu_cores": system_info.cpu_cores,
                "memory_total_gb": system_info.memory_total_gb,
                "memory_available_gb": system_info.memory_available_gb,
                "memory_usage_percent": round((system_info.memory_total_gb - system_info.memory_available_gb) / system_info.memory_total_gb * 100, 2),
                "disk_usage": system_info.disk_usage
            },
            "load_percentage": round(load_percentage, 2),
            "capabilities": get_server_capabilities(),
            "uptime": "healthy"  # 可以添加更详细的运行时间统计
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "server_id": settings.server_id,
            "error": str(e)
        }

@router.get("/system", response_model=SystemInfo)
async def get_system_info():
    """获取详细系统信息"""
    try:
        return await docker_service.get_system_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """获取服务器能力配置"""
    capabilities = get_server_capabilities()
    return {
        "server_id": settings.server_id,
        "server_type": settings.server_type,
        "max_containers": settings.max_containers,
        **capabilities
    }

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """获取Prometheus格式的指标"""
    try:
        system_info = await docker_service.get_system_info()
        container_list = await docker_service.list_containers(all_containers=True)
        
        metrics = {
            "mmanager_containers_total": container_list.total,
            "mmanager_containers_running": container_list.running,
            "mmanager_containers_stopped": container_list.stopped,
            "mmanager_containers_max": settings.max_containers,
            "mmanager_memory_total_bytes": system_info.memory_total_gb * 1024 * 1024 * 1024,
            "mmanager_memory_available_bytes": system_info.memory_available_gb * 1024 * 1024 * 1024,
            "mmanager_cpu_cores": system_info.cpu_cores,
            "mmanager_disk_total_bytes": system_info.disk_usage["total_gb"] * 1024 * 1024 * 1024,
            "mmanager_disk_used_bytes": system_info.disk_usage["used_gb"] * 1024 * 1024 * 1024,
            "mmanager_load_percentage": (container_list.running / settings.max_containers) * 100,
            "mmanager_up": 1,
            "mmanager_info": {
                "server_id": settings.server_id,
                "server_type": settings.server_type,
                "docker_version": system_info.docker_version
            }
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))