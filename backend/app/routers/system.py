from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.database import get_async_db
from app.models import User
from app.dependencies.auth import require_admin
from app.config import settings
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class SystemConfigUpdate(BaseModel):
    """系统配置更新请求"""

    config_key: str
    config_value: Any
    description: Optional[str] = None


class SystemConfig(BaseModel):
    """系统配置项"""

    key: str
    value: Any
    description: str
    type: str
    editable: bool = True
    category: str = "general"


@router.get("/config")
async def get_system_config(
    category: Optional[str] = Query(None, description="配置分类"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """获取系统配置"""

    # 基础系统配置
    system_configs = {
        "general": [
            SystemConfig(
                key="site_name",
                value="GeoML-Hub",
                description="网站名称",
                type="string",
                category="general",
            ),
            SystemConfig(
                key="site_description",
                value="地理科学机器学习模型仓库平台",
                description="网站描述",
                type="string",
                category="general",
            ),
            SystemConfig(
                key="maintenance_mode",
                value=False,
                description="维护模式",
                type="boolean",
                category="general",
            ),
            SystemConfig(
                key="registration_enabled",
                value=True,
                description="是否允许用户注册",
                type="boolean",
                category="general",
            ),
            SystemConfig(
                key="max_file_size",
                value=10 * 1024 * 1024 * 1024,  # 10GB
                description="最大文件上传大小（字节）",
                type="integer",
                category="general",
            ),
            SystemConfig(
                key="default_storage_quota",
                value=10 * 1024 * 1024 * 1024,  # 10GB
                description="默认用户存储配额（字节）",
                type="integer",
                category="general",
            ),
        ],
        "security": [
            SystemConfig(
                key="jwt_expiration_hours",
                value=24,
                description="JWT令牌过期时间（小时）",
                type="integer",
                category="security",
            ),
            SystemConfig(
                key="password_min_length",
                value=8,
                description="密码最小长度",
                type="integer",
                category="security",
            ),
            SystemConfig(
                key="max_login_attempts",
                value=5,
                description="最大登录尝试次数",
                type="integer",
                category="security",
            ),
            SystemConfig(
                key="require_email_verification",
                value=True,
                description="是否需要邮箱验证",
                type="boolean",
                category="security",
            ),
        ],
        "storage": [
            SystemConfig(
                key="minio_endpoint",
                value=settings.minio_endpoint,
                description="MinIO存储端点",
                type="string",
                category="storage",
                editable=False,
            ),
            SystemConfig(
                key="minio_bucket",
                value=settings.minio_default_bucket,
                description="MinIO存储桶",
                type="string",
                category="storage",
                editable=False,
            ),
            SystemConfig(
                key="cleanup_interval_hours",
                value=24,
                description="清理任务间隔（小时）",
                type="integer",
                category="storage",
            ),
            SystemConfig(
                key="file_retention_days",
                value=30,
                description="删除文件保留天数",
                type="integer",
                category="storage",
            ),
        ],
        "database": [
            SystemConfig(
                key="database_url",
                value=settings.database_url,
                description="数据库连接地址",
                type="string",
                category="database",
                editable=False,
            ),
            SystemConfig(
                key="connection_pool_size",
                value=10,
                description="连接池大小",
                type="integer",
                category="database",
            ),
            SystemConfig(
                key="query_timeout_seconds",
                value=30,
                description="查询超时时间（秒）",
                type="integer",
                category="database",
            ),
        ],
        "features": [
            SystemConfig(
                key="enable_social_features",
                value=True,
                description="启用社交功能",
                type="boolean",
                category="features",
            ),
            SystemConfig(
                key="enable_file_upload",
                value=True,
                description="启用文件上传",
                type="boolean",
                category="features",
            ),
            SystemConfig(
                key="enable_search",
                value=True,
                description="启用搜索功能",
                type="boolean",
                category="features",
            ),
            SystemConfig(
                key="enable_analytics",
                value=True,
                description="启用分析功能",
                type="boolean",
                category="features",
            ),
        ],
    }

    # 如果指定了分类，只返回该分类的配置
    if category:
        if category not in system_configs:
            raise HTTPException(status_code=404, detail="配置分类不存在")
        return {
            "category": category,
            "configs": [config.dict() for config in system_configs[category]],
            "total": len(system_configs[category]),
        }

    # 返回所有配置
    all_configs = {}
    total_count = 0

    for cat, configs in system_configs.items():
        all_configs[cat] = [config.dict() for config in configs]
        total_count += len(configs)

    return {
        "categories": all_configs,
        "total": total_count,
        "generated_at": datetime.utcnow(),
    }


@router.put("/config")
async def update_system_config(
    config_update: SystemConfigUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """更新系统配置"""

    # 定义可编辑的配置项
    editable_configs = {
        "site_name": {"type": "string", "category": "general"},
        "site_description": {"type": "string", "category": "general"},
        "maintenance_mode": {"type": "boolean", "category": "general"},
        "registration_enabled": {"type": "boolean", "category": "general"},
        "max_file_size": {
            "type": "integer",
            "category": "general",
            "min": 1024,
            "max": 1024 * 1024 * 1024,
        },
        "default_storage_quota": {
            "type": "integer",
            "category": "general",
            "min": 1024 * 1024 * 1024,
            "max": 1024 * 1024 * 1024 * 1024,
        },
        "jwt_expiration_hours": {
            "type": "integer",
            "category": "security",
            "min": 1,
            "max": 168,
        },
        "password_min_length": {
            "type": "integer",
            "category": "security",
            "min": 6,
            "max": 50,
        },
        "max_login_attempts": {
            "type": "integer",
            "category": "security",
            "min": 1,
            "max": 20,
        },
        "require_email_verification": {"type": "boolean", "category": "security"},
        "cleanup_interval_hours": {
            "type": "integer",
            "category": "storage",
            "min": 1,
            "max": 168,
        },
        "file_retention_days": {
            "type": "integer",
            "category": "storage",
            "min": 1,
            "max": 365,
        },
        "connection_pool_size": {
            "type": "integer",
            "category": "database",
            "min": 1,
            "max": 100,
        },
        "query_timeout_seconds": {
            "type": "integer",
            "category": "database",
            "min": 1,
            "max": 300,
        },
        "enable_social_features": {"type": "boolean", "category": "features"},
        "enable_file_upload": {"type": "boolean", "category": "features"},
        "enable_search": {"type": "boolean", "category": "features"},
        "enable_analytics": {"type": "boolean", "category": "features"},
    }

    config_key = config_update.config_key
    config_value = config_update.config_value

    # 检查配置项是否存在且可编辑
    if config_key not in editable_configs:
        raise HTTPException(status_code=400, detail="配置项不存在或不可编辑")

    config_info = editable_configs[config_key]

    # 验证配置值类型
    if config_info["type"] == "boolean":
        if not isinstance(config_value, bool):
            raise HTTPException(status_code=400, detail="配置值必须是布尔类型")
    elif config_info["type"] == "integer":
        if not isinstance(config_value, int):
            raise HTTPException(status_code=400, detail="配置值必须是整数类型")
        # 检查范围
        if "min" in config_info and config_value < config_info["min"]:
            raise HTTPException(
                status_code=400, detail=f"配置值不能小于{config_info['min']}"
            )
        if "max" in config_info and config_value > config_info["max"]:
            raise HTTPException(
                status_code=400, detail=f"配置值不能大于{config_info['max']}"
            )
    elif config_info["type"] == "string":
        if not isinstance(config_value, str):
            raise HTTPException(status_code=400, detail="配置值必须是字符串类型")
        if len(config_value.strip()) == 0:
            raise HTTPException(status_code=400, detail="配置值不能为空")

    try:
        # 这里可以将配置保存到数据库或文件
        # 现在只是记录日志和返回确认
        logger.info(
            f"Admin {admin_user.username} updated config {config_key} to {config_value}"
        )

        # 对于一些特殊配置，可能需要重启服务才能生效
        requires_restart = config_key in [
            "jwt_expiration_hours",
            "connection_pool_size",
            "query_timeout_seconds",
        ]

        return {
            "message": "配置更新成功",
            "config_key": config_key,
            "old_value": None,  # 这里可以从数据库获取旧值
            "new_value": config_value,
            "updated_by": admin_user.username,
            "updated_at": datetime.utcnow(),
            "requires_restart": requires_restart,
            "description": config_update.description,
        }

    except Exception as e:
        logger.error(f"Failed to update config {config_key}: {e}")
        raise HTTPException(status_code=500, detail="更新配置失败")


@router.get("/health")
async def get_system_health(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """获取系统健康状态（公共访问）"""

    # 复用admin模块的健康检查逻辑
    from app.routers.admin import get_system_health as admin_health_check

    # 调用管理员健康检查
    health_data = await admin_health_check(admin_user, db)

    # 返回简化的健康状态
    return {
        "status": health_data["status"],
        "timestamp": health_data["timestamp"],
        "services": {
            "database": health_data["database"]["status"],
            "storage": health_data["storage"]["status"],
            "filesystem": health_data["filesystem"]["status"],
        },
        "uptime": health_data.get("uptime", "unknown"),
    }


@router.get("/info")
async def get_system_info(
    admin_user: User = Depends(require_admin),
):
    """获取系统信息"""

    import platform
    import psutil
    import sys

    try:
        # 系统信息
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": sys.version,
            "hostname": platform.node(),
            "cpu_cores": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": {
                "total": psutil.disk_usage("/").total,
                "used": psutil.disk_usage("/").used,
                "free": psutil.disk_usage("/").free,
            },
        }

        # 应用信息
        app_info = {
            "name": "GeoML-Hub",
            "version": "2.0.0",
            "environment": getattr(settings, "environment", "production"),
            "debug_mode": getattr(settings, "debug", False),
            "database_url": (
                settings.database_url.split("@")[1]
                if "@" in settings.database_url
                else "***"
            ),
            "minio_endpoint": settings.minio_endpoint,
            "cors_origins": settings.cors_origins,
        }

        return {
            "system": system_info,
            "application": app_info,
            "generated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="获取系统信息失败")


@router.post("/maintenance")
async def toggle_maintenance_mode(
    enabled: bool = Query(..., description="是否启用维护模式"),
    message: Optional[str] = Query(None, description="维护消息"),
    admin_user: User = Depends(require_admin),
):
    """切换维护模式"""

    try:
        # 这里可以设置维护模式的状态
        # 实际实现时可能需要写入配置文件或数据库
        logger.info(
            f"Admin {admin_user.username} {'enabled' if enabled else 'disabled'} maintenance mode"
        )

        return {
            "message": f"维护模式已{'启用' if enabled else '禁用'}",
            "maintenance_enabled": enabled,
            "maintenance_message": message
            or ("系统维护中，请稍后再试" if enabled else None),
            "updated_by": admin_user.username,
            "updated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Failed to toggle maintenance mode: {e}")
        raise HTTPException(status_code=500, detail="切换维护模式失败")


@router.post("/restart")
async def restart_system(
    component: str = Query(
        "all", regex="^(all|api|worker|scheduler)$", description="要重启的组件"
    ),
    admin_user: User = Depends(require_admin),
):
    """重启系统组件"""

    # 这个功能在生产环境中需要谨慎实现
    # 通常需要与容器编排系统或进程管理器集成

    logger.warning(f"Admin {admin_user.username} requested restart of {component}")

    return {
        "message": f"重启请求已提交：{component}",
        "component": component,
        "requested_by": admin_user.username,
        "requested_at": datetime.utcnow(),
        "status": "pending",
        "note": "实际重启需要系统管理员手动执行",
    }
