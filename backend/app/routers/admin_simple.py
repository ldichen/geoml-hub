"""
管理员API路由 - 简化版本
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from app.database import get_async_db
from app.models import User
from app.dependencies.auth import require_admin
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard")
async def get_admin_dashboard(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """管理员仪表板 - 简化版本"""
    
    try:
        # 简单的用户统计
        total_users_query = select(func.count(User.id)).where(User.is_active == True)
        total_users_result = await db.execute(total_users_query)
        total_users = total_users_result.scalar() or 0
        
        return {
            "users": {
                "total": total_users,
                "active": total_users,
                "verified": 1,
            },
            "repositories": {
                "total": 0,
                "public": 0,
                "private": 0,
            },
            "storage": {
                "total_size_bytes": 0,
                "total_files": 0,
                "active_files": 0,
                "storage_health": {"healthy": True},
            },
            "activity_7d": {
                "uploads": 0,
                "views": 0,
                "downloads": 0,
            },
            "system_health": {
                "minio_status": True,
                "database_status": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"仪表板数据获取失败: {str(e)}")


@router.get("/users")
async def get_admin_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """管理员用户列表 - 简化版本"""
    
    try:
        # 获取用户列表
        users_query = select(User).where(User.is_active == True).offset(skip).limit(limit)
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()
        
        # 获取总数
        count_query = select(func.count(User.id)).where(User.is_active == True)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return {
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": getattr(user, "is_active", False),
                    "is_admin": getattr(user, "is_admin", False),
                    "is_verified": getattr(user, "is_verified", False),
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                }
                for user in users
            ],
            "total": total,
            "page": skip // limit + 1,
            "pages": (total + limit - 1) // limit,
        }
        
    except Exception as e:
        logger.error(f"Admin users error: {e}")
        raise HTTPException(status_code=500, detail=f"用户列表获取失败: {str(e)}")