from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from app.database import get_async_db
from app.models import (
    Repository,
    User,
    FileUploadSession,
    RepositoryFile,
    UserStorage,
    RepositoryView,
    FileDownload,
    RepositoryStar,
)
from app.dependencies.auth import get_current_active_user, require_admin
from app.schemas.user import UserProfile
from app.schemas.repository import RepositoryListItem
from app.services.minio_service import minio_service
from app.services.file_upload_service import FileUploadService
from app.services.mmanager_client import mmanager_client
from app.services.harbor_client import HarborClient
from app.config import settings
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()



@router.get("/dashboard")
async def get_admin_dashboard(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """管理员仪表板"""
    
    try:
        # 用户统计
        total_users_query = select(func.count(User.id)).where(User.is_active == True)
        active_users_query = select(func.count(User.id)).where(
            and_(
                User.is_active == True,
                User.last_seen_at >= datetime.now(timezone.utc) - timedelta(days=30),
            )
        )

        total_users_result = await db.execute(total_users_query)
        active_users_result = await db.execute(active_users_query)

        total_users = total_users_result.scalar() or 0
        active_users = active_users_result.scalar() or 0

        # 仓库统计
        total_repos_query = select(func.count(Repository.id)).where(Repository.is_active == True)
        public_repos_query = select(func.count(Repository.id)).where(
            and_(Repository.is_active == True, Repository.visibility == "public")
        )

        total_repos_result = await db.execute(total_repos_query)
        public_repos_result = await db.execute(public_repos_query)

        total_repositories = total_repos_result.scalar() or 0
        public_repositories = public_repos_result.scalar() or 0

        # 存储统计
        storage_stats_query = select(
            func.sum(User.storage_used).label("total_size"),
            func.count(User.id).label("total_files")
        ).where(User.is_active == True)

        storage_result = await db.execute(storage_stats_query)
        storage_stats = storage_result.first()

        # 活跃文件统计
        total_files_query = select(func.count(RepositoryFile.id)).where(
            RepositoryFile.is_deleted == False
        )
        total_files_result = await db.execute(total_files_query)
        total_files = total_files_result.scalar() or 0

        # MinIO健康检查
        minio_health = await minio_service.check_health()

        # 7天内活动统计
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        # 最近上传
        recent_uploads_query = select(func.count(FileUploadSession.id)).where(
            FileUploadSession.created_at >= seven_days_ago
        )
        recent_uploads_result = await db.execute(recent_uploads_query)
        recent_uploads = recent_uploads_result.scalar() or 0

        # 最近浏览
        recent_views_query = select(func.count(RepositoryView.id)).where(
            RepositoryView.created_at >= seven_days_ago
        )
        recent_views_result = await db.execute(recent_views_query)
        recent_views = recent_views_result.scalar() or 0

        # 最近下载
        recent_downloads_query = select(func.count(FileDownload.id)).where(
            FileDownload.started_at >= seven_days_ago
        )
        recent_downloads_result = await db.execute(recent_downloads_query)
        recent_downloads = recent_downloads_result.scalar() or 0

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": 0,  # TODO: 计算已验证用户数
            },
            "repositories": {
                "total": total_repositories,
                "public": public_repositories,
                "private": total_repositories - public_repositories,
            },
            "storage": {
                "total_size_bytes": getattr(storage_stats, "total_size") or 0,
                "total_files": getattr(storage_stats, "total_files") or 0,
                "active_files": total_files,
                "storage_health": minio_health,
            },
            "activity_7d": {
                "uploads": recent_uploads,
                "views": recent_views,
                "downloads": recent_downloads,
            },
            "system_health": {
                "minio_status": minio_health.get("healthy", False),
                "database_status": True,  # 如果能执行查询说明数据库正常
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
    
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"仪表板数据获取失败: {str(e)}")


@router.get("/users")
async def get_admin_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="搜索用户名或邮箱"),
    is_active: Optional[bool] = Query(None, description="是否活跃"),
    is_verified: Optional[bool] = Query(None, description="是否已验证"),
    sort_by: str = Query(
        "created", regex="^(created|updated|username|repositories|storage)$"
    ),
    order: str = Query("desc", regex="^(asc|desc)$"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """管理员用户列表"""

    query = select(User)

    # 搜索条件
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
            )
        )

    # 筛选条件
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    if is_verified is not None:
        query = query.where(User.is_verified == is_verified)

    # 排序
    sort_field = {
        "created": User.created_at,
        "updated": User.updated_at,
        "username": User.username,
        "repositories": User.public_repos_count,
        "storage": User.storage_used,
    }[sort_by]

    if order == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)

    # 分页
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    # 总数查询
    count_query = select(func.count(User.id))
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
            )
        )
    if is_active is not None:
        count_query = count_query.where(User.is_active == is_active)
    if is_verified is not None:
        count_query = count_query.where(User.is_verified == is_verified)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return {
        "users": [UserProfile.model_validate(user) for user in users],
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
    }


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int = Path(..., description="用户ID"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_verified: Optional[bool] = Query(None, description="是否已验证"),
    is_admin: Optional[bool] = Query(None, description="是否管理员"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """更新用户状态"""

    user_query = select(User).where(User.id == user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 防止管理员禁用自己
    if user_id == admin_user.id and is_active is False:
        raise HTTPException(status_code=400, detail="不能禁用自己")

    # 更新状态
    if is_active is not None:
        setattr(user, "is_active", is_active)
    if is_verified is not None:
        setattr(user, "is_verified", is_verified)
    if is_admin is not None:
        setattr(user, "is_admin", is_admin)

    await db.commit()

    return {"message": f"用户 {user.username} 状态已更新"}


@router.get("/storage/stats")
async def get_storage_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """存储统计信息"""

    # 用户存储统计
    user_storage_query = select(
        func.sum(UserStorage.total_size).label("total_user_storage"),
        func.avg(UserStorage.total_size).label("avg_user_storage"),
        func.max(UserStorage.total_size).label("max_user_storage"),
        func.count(UserStorage.user_id).label("users_with_storage"),
    )

    user_storage_result = await db.execute(user_storage_query)
    user_storage_stats = user_storage_result.first()

    # 文件类型分布
    file_type_query = (
        select(
            RepositoryFile.mime_type,
            func.count(RepositoryFile.id).label("count"),
            func.sum(RepositoryFile.file_size).label("total_size"),
        )
        .where(RepositoryFile.is_deleted == False)
        .group_by(RepositoryFile.mime_type)
        .order_by(desc("total_size"))
    )

    file_type_result = await db.execute(file_type_query)
    file_types = [
        {
            "mime_type": row.mime_type,
            "count": row.count,
            "total_size": row.total_size,
        }
        for row in file_type_result
    ]

    # MinIO存储桶使用情况
    bucket_usage = await minio_service.get_bucket_usage(settings.minio_default_bucket)

    return {
        "user_storage": {
            "total_bytes": getattr(user_storage_stats, "total_user_storage") or 0,
            "average_bytes": float(getattr(user_storage_stats, "avg_user_storage") or 0),
            "max_bytes": getattr(user_storage_stats, "max_user_storage") or 0,
            "users_count": getattr(user_storage_stats, "users_with_storage") or 0,
        },
        "file_types": file_types[:20],  # 前20种文件类型
        "minio_bucket": bucket_usage,
        "quotas": {
            "default_user_quota_gb": settings.max_total_size_gb,
            "max_file_size_mb": settings.max_file_size_mb,
        },
    }


@router.post("/storage/cleanup")
async def cleanup_storage(
    cleanup_orphaned: bool = Query(True, description="清理孤儿文件"),
    cleanup_expired_sessions: bool = Query(True, description="清理过期上传会话"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """存储清理"""

    cleanup_results = {}

    # 清理过期上传会话
    if cleanup_expired_sessions:
        upload_service = FileUploadService(db)
        session_cleanup = await upload_service.cleanup_expired_sessions()
        cleanup_results["expired_sessions"] = session_cleanup

    # 清理孤儿文件
    if cleanup_orphaned:
        # 获取数据库中所有有效的MinIO对象键
        valid_objects_query = select(RepositoryFile.minio_object_name).where(
            RepositoryFile.is_deleted == False
        )
        valid_objects_result = await db.execute(valid_objects_query)
        valid_object_keys = [row[0] for row in valid_objects_result.fetchall()]

        # 清理MinIO中的孤儿文件
        orphan_cleanup = await minio_service.cleanup_orphaned_files(
            bucket_name=settings.minio_default_bucket,
            valid_object_keys=valid_object_keys,
        )
        cleanup_results["orphaned_files"] = orphan_cleanup

    return cleanup_results


@router.get("/system/health")
async def get_system_health(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """系统健康检查"""

    health_status = {
        "overall": "healthy",
        "services": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 数据库健康检查
    try:
        test_query = select(func.count(User.id)).limit(1)
        await db.execute(test_query)
        health_status["services"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0,  # 简化处理
        }
    except Exception as e:
        health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["overall"] = "degraded"

    # MinIO健康检查
    minio_health = await minio_service.check_health()
    health_status["services"]["minio"] = minio_health

    if not minio_health.get("healthy", False):
        health_status["overall"] = "degraded"

    # 磁盘空间检查（简化版）
    import shutil

    try:
        disk_usage = shutil.disk_usage("/")
        free_percentage = (disk_usage.free / disk_usage.total) * 100

        health_status["services"]["disk"] = {
            "status": "healthy" if free_percentage > 10 else "warning",
            "free_percentage": round(free_percentage, 2),
            "free_bytes": disk_usage.free,
            "total_bytes": disk_usage.total,
        }

        if free_percentage <= 5:
            health_status["overall"] = "critical"
        elif free_percentage <= 10:
            health_status["overall"] = "warning"

    except Exception as e:
        health_status["services"]["disk"] = {"status": "unknown", "error": str(e)}

    return health_status


@router.get("/logs")
async def get_system_logs(
    level: str = Query("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    limit: int = Query(100, ge=1, le=1000),
    admin_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """获取系统日志（简化版）"""

    # 这里应该连接到实际的日志系统
    # 现在返回模拟数据

    sample_logs = [
        {
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=i)).isoformat(),
            "level": level,
            "message": f"Sample log entry {i}",
            "module": "app.main" if i % 2 == 0 else "app.routers.repositories",
        }
        for i in range(min(limit, 50))
    ]

    return {
        "logs": sample_logs,
        "total": len(sample_logs),
        "level": level,
        "note": "This is a simplified log endpoint. In production, integrate with proper logging system.",
    }


# 仓库管理相关 API


@router.get("/repositories")
async def get_admin_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="搜索仓库名称或描述"),
    visibility: Optional[str] = Query(None, regex="^(public|private)$"),
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    is_active: Optional[bool] = Query(None, description="是否活跃"),
    is_featured: Optional[bool] = Query(None, description="是否推荐"),
    owner_username: Optional[str] = Query(None, description="所有者用户名"),
    sort_by: str = Query(
        "updated", regex="^(created|updated|stars|downloads|views|size)$"
    ),
    order: str = Query("desc", regex="^(asc|desc)$"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """管理员仓库列表（包括软删除的仓库）"""

    from sqlalchemy.orm import selectinload

    query = select(Repository).options(selectinload(Repository.owner))

    # 搜索条件
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Repository.name.ilike(search_pattern),
                Repository.description.ilike(search_pattern),
                Repository.full_name.ilike(search_pattern),
            )
        )

    # 筛选条件
    if visibility is not None:
        query = query.where(Repository.visibility == visibility)

    if repo_type is not None:
        query = query.where(Repository.repo_type == repo_type)

    if is_active is not None:
        query = query.where(Repository.is_active == is_active)

    if is_featured is not None:
        query = query.where(Repository.is_featured == is_featured)

    if owner_username:
        query = query.join(Repository.owner).where(User.username == owner_username)

    # 排序
    sort_field = {
        "created": Repository.created_at,
        "updated": Repository.updated_at,
        "stars": Repository.stars_count,
        "downloads": Repository.downloads_count,
        "views": Repository.views_count,
        "size": Repository.total_size,
    }[sort_by]

    if order == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)

    # 分页
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    repositories = result.scalars().all()

    # 总数查询
    count_query = select(func.count(Repository.id))
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            or_(
                Repository.name.ilike(search_pattern),
                Repository.description.ilike(search_pattern),
                Repository.full_name.ilike(search_pattern),
            )
        )
    if visibility is not None:
        count_query = count_query.where(Repository.visibility == visibility)
    if repo_type is not None:
        count_query = count_query.where(Repository.repo_type == repo_type)
    if is_active is not None:
        count_query = count_query.where(Repository.is_active == is_active)
    if is_featured is not None:
        count_query = count_query.where(Repository.is_featured == is_featured)
    if owner_username:
        count_query = count_query.join(Repository.owner).where(
            User.username == owner_username
        )

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return {
        "repositories": [RepositoryListItem.model_validate(repo) for repo in repositories],
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
    }


@router.put("/repositories/{repository_id}/status")
async def update_repository_status(
    repository_id: int = Path(..., description="仓库ID"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_featured: Optional[bool] = Query(None, description="是否推荐"),
    visibility: Optional[str] = Query(None, regex="^(public|private)$"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """更新仓库状态"""

    repo_query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(repo_query)
    repository = repo_result.scalar_one_or_none()

    if not repository:
        raise HTTPException(status_code=404, detail="仓库不存在")

    # 更新状态
    if is_active is not None:
        setattr(repository, "is_active", is_active)

    if is_featured is not None:
        setattr(repository, "is_featured", is_featured)

    if visibility is not None:
        old_visibility = repository.visibility
        setattr(repository, "visibility", visibility)

        # 更新用户的公开仓库计数
        if str(old_visibility) != str(visibility):
            owner_query = select(User).where(User.id == repository.owner_id)
            owner_result = await db.execute(owner_query)
            owner = owner_result.scalar_one()

            if str(old_visibility) == "public" and str(visibility) == "private":
                setattr(
                    owner,
                    "public_repos_count",
                    max(0, getattr(owner, "public_repos_count") - 1),
                )
            elif str(old_visibility) == "private" and str(visibility) == "public":
                setattr(
                    owner,
                    "public_repos_count",
                    getattr(owner, "public_repos_count") + 1,
                )

    await db.commit()

    return {"message": f"仓库 {repository.full_name} 状态已更新"}


@router.post("/repositories/{repository_id}/restore")
async def restore_repository(
    repository_id: int = Path(..., description="仓库ID"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """恢复软删除的仓库"""

    # 查询包括非活跃仓库
    repo_query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(repo_query)
    repository = repo_result.scalar_one_or_none()

    if not repository:
        raise HTTPException(status_code=404, detail="仓库不存在")

    if getattr(repository, "is_active", True):
        raise HTTPException(status_code=400, detail="仓库未被删除，无需恢复")

    # 恢复仓库
    setattr(repository, "is_active", True)

    # 更新用户的公开仓库计数
    if str(getattr(repository, "visibility")) == "public":
        owner_query = select(User).where(User.id == repository.owner_id)
        owner_result = await db.execute(owner_query)
        owner = owner_result.scalar_one()
        setattr(owner, "public_repos_count", getattr(owner, "public_repos_count") + 1)

    await db.commit()

    return {"message": f"仓库 {repository.full_name} 已恢复"}


@router.delete("/repositories/{repository_id}/hard-delete")
async def hard_delete_repository(
    repository_id: int = Path(..., description="仓库ID"),
    confirm: bool = Query(False, description="确认永久删除"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """永久删除仓库（硬删除）"""

    if not confirm:
        raise HTTPException(status_code=400, detail="需要确认删除操作")

    # 查询包括非活跃仓库
    repo_query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(repo_query)
    repository = repo_result.scalar_one_or_none()

    if not repository:
        raise HTTPException(status_code=404, detail="仓库不存在")

    from app.services.repository_service import RepositoryService

    repo_service = RepositoryService(db)

    try:
        # 删除MinIO中的所有文件
        files_query = select(RepositoryFile).where(
            RepositoryFile.repository_id == repository_id
        )
        files_result = await db.execute(files_query)
        files = files_result.scalars().all()

        for file in files:
            try:
                await repo_service.minio_service.delete_file(
                    bucket_name=getattr(file, "minio_bucket"),
                    object_key=getattr(file, "minio_object_key"),
                )
            except Exception as e:
                logger.warning(f"Failed to delete file {file.minio_object_key}: {e}")

        # 删除数据库记录（级联删除会处理关联表）
        await db.delete(repository)
        await db.commit()

        return {"message": f"仓库 {repository.full_name} 已永久删除"}

    except Exception as e:
        await db.rollback()
        logger.error(f"Hard delete repository failed: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/repositories/stats")
async def get_repositories_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """仓库统计信息"""

    # 基本统计
    total_repos_query = select(func.count(Repository.id))
    active_repos_query = select(func.count(Repository.id)).where(
        Repository.is_active == True
    )
    featured_repos_query = select(func.count(Repository.id)).where(
        Repository.is_featured == True
    )

    total_result = await db.execute(total_repos_query)
    total_count = total_result.scalar() or 0
    
    active_result = await db.execute(active_repos_query)
    active_count = active_result.scalar() or 0
    
    featured_result = await db.execute(featured_repos_query)
    featured_count = featured_result.scalar() or 0

    # 按类型统计
    type_stats_query = (
        select(Repository.repo_type, func.count(Repository.id).label("count"))
        .where(Repository.is_active == True)
        .group_by(Repository.repo_type)
    )
    type_stats_result = await db.execute(type_stats_query)
    type_stats = {row.repo_type: row.count for row in type_stats_result}

    # 按可见性统计
    visibility_stats_query = (
        select(Repository.visibility, func.count(Repository.id).label("count"))
        .where(Repository.is_active == True)
        .group_by(Repository.visibility)
    )
    visibility_stats_result = await db.execute(visibility_stats_query)
    visibility_stats = {row.visibility: row.count for row in visibility_stats_result}

    # 热门仓库（按星标数）
    top_repos_query = (
        select(Repository)
        .where(Repository.is_active == True)
        .order_by(desc(Repository.stars_count))
        .limit(10)
        .options(selectinload(Repository.owner))
    )
    top_repos_result = await db.execute(top_repos_query)
    top_repos = top_repos_result.scalars().all()

    return {
        "overview": {
            "total": total_count,
            "active": active_count,
            "featured": featured_count,
            "deleted": total_count - active_count,
        },
        "by_type": type_stats,
        "by_visibility": visibility_stats,
        "top_repositories": [
            {
                "id": repo.id,
                "full_name": repo.full_name,
                "stars_count": repo.stars_count,
                "downloads_count": repo.downloads_count,
                "owner": repo.owner.username if repo.owner else None,
            }
            for repo in top_repos
        ],
    }


# mManager控制器管理相关API

@router.get("/mmanager/controllers")
async def get_mmanager_controllers(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """获取mManager控制器状态"""
    try:
        status = await mmanager_client.get_controller_status(db)
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"获取控制器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取控制器状态失败: {str(e)}")


@router.post("/mmanager/controllers/sync")
async def sync_mmanager_controllers(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """手动同步mManager控制器配置"""
    try:
        await mmanager_client.sync_controllers(db)
        return {
            "status": "success",
            "message": "控制器配置同步完成"
        }
    except Exception as e:
        logger.error(f"控制器同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"控制器同步失败: {str(e)}")


@router.post("/mmanager/controllers/{controller_id}/health-check")
async def trigger_controller_health_check(
    controller_id: str = Path(..., description="控制器ID"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """触发特定控制器的健康检查"""
    try:
        if controller_id not in mmanager_client.controllers:
            raise HTTPException(status_code=404, detail="控制器不存在")
        
        client = mmanager_client.controllers[controller_id]
        health_data = await client.health_check()
        
        # 更新数据库
        from sqlalchemy import update
        from app.models.container_registry import MManagerController
        
        await db.execute(
            update(MManagerController)
            .where(MManagerController.controller_id == controller_id)
            .values(
                status="healthy",
                last_check_at=func.now(),
                health_data=health_data,
                error_message=None,
                consecutive_failures=0,
            )
        )
        await db.commit()
        
        return {
            "status": "success",
            "message": f"控制器 {controller_id} 健康检查完成",
            "health_data": health_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"控制器健康检查失败: {e}")
        
        # 更新失败状态
        from sqlalchemy import update
        from app.models.container_registry import MManagerController
        
        await db.execute(
            update(MManagerController)
            .where(MManagerController.controller_id == controller_id)
            .values(
                status="unhealthy",
                last_check_at=func.now(),
                error_message=str(e),
                consecutive_failures=MManagerController.consecutive_failures + 1,
            )
        )
        await db.commit()
        
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/mmanager/containers")
async def get_mmanager_containers(
    controller_id: Optional[str] = Query(None, description="筛选特定控制器"),
    status: Optional[str] = Query(None, description="筛选容器状态"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """获取所有容器注册信息"""
    try:
        from app.models.service import ModelService
        
        query = select(ModelService).options(selectinload(ModelService.image)).where(ModelService.container_id.isnot(None))
        
        if controller_id:
            query = query.where(ModelService.model_ip == controller_id)
        
        if status:
            query = query.where(ModelService.status == status)
        
        query = query.order_by(desc(ModelService.created_at))
        
        result = await db.execute(query)
        services = result.scalars().all()
        
        container_list = []
        for service in services:
            container_info = {
                "id": service.id,
                "container_id": service.container_id,
                "service_id": service.id,
                "controller_id": service.model_ip,
                "controller_url": f"http://{service.model_ip}:8000",
                "container_name": service.service_name,
                "image_name": service.image.docker_image if service.image else "unknown",
                "status": service.status,
                "host_port": service.gradio_port,
                "container_port": service.gradio_port,
                "ip_address": service.model_ip,
                "created_at": service.created_at.isoformat() if service.created_at else None,
                "last_sync_at": service.last_heartbeat.isoformat() if service.last_heartbeat else None,
                "health_status": service.health_status,
                "resource_allocation": {"cpu": service.cpu_limit, "memory": service.memory_limit},
                "resource_usage": {
                    "cpu_percent": float(service.cpu_usage_percent) if service.cpu_usage_percent else 0,
                    "memory_bytes": service.memory_usage_bytes or 0
                },
            }
            container_list.append(container_info)
        
        return {
            "status": "success",
            "data": {
                "containers": container_list,
                "total": len(container_list),
                "filters": {
                    "controller_id": controller_id,
                    "status": status
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取容器信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取容器信息失败: {str(e)}")


@router.delete("/mmanager/containers/{container_id}")
async def cleanup_container_registry(
    container_id: str = Path(..., description="容器ID"),
    force: bool = Query(False, description="强制清理（即使容器仍在运行）"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """清理容器注册记录"""
    try:
        from app.models.container_registry import ContainerRegistry
        
        # 查找容器记录
        result = await db.execute(
            select(ContainerRegistry).where(ContainerRegistry.container_id == container_id)
        )
        container = result.scalar_one_or_none()
        
        if not container:
            raise HTTPException(status_code=404, detail="容器记录不存在")
        
        # 检查容器是否还在运行
        if not force and container.status in ["running", "starting"]:
            raise HTTPException(
                status_code=400, 
                detail="容器仍在运行中，使用 force=true 强制清理"
            )
        
        # 删除记录
        await db.delete(container)
        await db.commit()
        
        return {
            "status": "success",
            "message": f"容器 {container_id} 注册记录已清理"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理容器记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理容器记录失败: {str(e)}")


@router.get("/mmanager/operations")
async def get_container_operations(
    controller_id: Optional[str] = Query(None, description="筛选特定控制器"),
    service_id: Optional[int] = Query(None, description="筛选特定服务"),
    operation_type: Optional[str] = Query(None, description="操作类型"),
    limit: int = Query(50, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """获取容器操作历史"""
    try:
        from app.models.container_registry import ContainerOperation
        
        query = select(ContainerOperation)
        
        if controller_id:
            query = query.where(ContainerOperation.controller_id == controller_id)
        
        if service_id:
            query = query.where(ContainerOperation.service_id == service_id)
        
        if operation_type:
            query = query.where(ContainerOperation.operation_type == operation_type)
        
        query = query.order_by(desc(ContainerOperation.started_at)).limit(limit)
        
        result = await db.execute(query)
        operations = result.scalars().all()
        
        operation_list = []
        for op in operations:
            operation_info = {
                "id": op.id,
                "container_id": op.container_id,
                "service_id": op.service_id,
                "controller_id": op.controller_id,
                "operation_type": op.operation_type,
                "operation_status": op.operation_status,
                "operation_details": op.operation_details,
                "error_message": op.error_message,
                "started_at": op.started_at.isoformat() if op.started_at else None,
                "completed_at": op.completed_at.isoformat() if op.completed_at else None,
                "duration_seconds": op.duration_seconds,
                "user_id": op.user_id,
                "automated": op.automated,
            }
            operation_list.append(operation_info)
        
        return {
            "status": "success",
            "data": {
                "operations": operation_list,
                "total": len(operation_list),
                "filters": {
                    "controller_id": controller_id,
                    "service_id": service_id,
                    "operation_type": operation_type,
                    "limit": limit
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取操作历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取操作历史失败: {str(e)}")


# Harbor镜像管理相关API

@router.get("/harbor/images/check")
async def check_harbor_image_consistency(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """检查Harbor镜像与数据库记录的一致性"""
    try:
        from app.models.image import Image
        
        # 获取数据库中的所有镜像记录
        db_images_query = select(Image).where(Image.status == 'ready')
        db_images_result = await db.execute(db_images_query)
        db_images = db_images_result.scalars().all()
        
        # 转换为字典格式便于Harbor客户端处理
        db_images_data = [
            {
                'id': img.id,
                'original_name': img.original_name,
                'original_tag': img.original_tag,
                'harbor_storage_name': img.harbor_storage_name,
                'status': img.status,
                'created_at': img.created_at.isoformat() if img.created_at else None,
                'repository_id': img.repository_id
            }
            for img in db_images
        ]
        
        # 使用Harbor客户端检查一致性
        async with HarborClient() as harbor_client:
            consistency_check = await harbor_client.compare_with_database_images(db_images_data)
            storage_usage = await harbor_client.get_harbor_storage_usage()
        
        return {
            "status": "success",
            "consistency_check": consistency_check,
            "storage_usage": storage_usage,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Harbor镜像一致性检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")


@router.post("/harbor/images/cleanup")
async def cleanup_harbor_orphan_images(
    dry_run: bool = Query(True, description="是否为模拟运行（不实际删除）"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """清理Harbor中的孤立镜像"""
    try:
        from app.models.image import Image
        
        # 获取数据库中的所有镜像记录
        db_images_query = select(Image).where(Image.status == 'ready')
        db_images_result = await db.execute(db_images_query)
        db_images = db_images_result.scalars().all()
        
        # 转换为字典格式
        db_images_data = [
            {
                'id': img.id,
                'original_name': img.original_name,
                'original_tag': img.original_tag,
                'harbor_storage_name': img.harbor_storage_name,
                'status': img.status,
                'created_at': img.created_at.isoformat() if img.created_at else None,
                'repository_id': img.repository_id
            }
            for img in db_images
        ]
        
        # 获取孤立镜像并清理
        async with HarborClient() as harbor_client:
            # 检查一致性获取孤立镜像
            consistency_check = await harbor_client.compare_with_database_images(db_images_data)
            orphan_images = consistency_check.get('orphan_images', [])
            
            if not orphan_images:
                return {
                    "status": "success",
                    "message": "没有发现孤立镜像",
                    "summary": consistency_check.get('summary', {}),
                    "dry_run": dry_run,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # 清理孤立镜像
            cleanup_results = await harbor_client.cleanup_orphan_images(orphan_images, dry_run=dry_run)
        
        return {
            "status": "success",
            "message": f"{'模拟' if dry_run else '实际'}清理完成",
            "cleanup_results": cleanup_results,
            "summary": consistency_check.get('summary', {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Harbor镜像清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@router.get("/harbor/images/list")
async def list_harbor_images(
    project_name: Optional[str] = Query(None, description="项目名称"),
    admin_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """列出Harbor中的所有镜像"""
    try:
        async with HarborClient() as harbor_client:
            # 检查Harbor连接
            connectivity = await harbor_client.check_harbor_connectivity()
            if connectivity.get('status') != 'connected':
                raise HTTPException(status_code=503, detail=f"Harbor连接失败: {connectivity.get('message')}")
            
            # 获取所有镜像
            harbor_images = await harbor_client.get_all_harbor_images(project_name)
            storage_usage = await harbor_client.get_harbor_storage_usage()
        
        return {
            "status": "success",
            "images": harbor_images,
            "storage_usage": storage_usage,
            "total_images": len(harbor_images),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Harbor镜像列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取镜像列表失败: {str(e)}")


@router.delete("/harbor/images/{project_name}/{repository_name}")
async def delete_harbor_repository(
    project_name: str = Path(..., description="项目名称"),
    repository_name: str = Path(..., description="仓库名称"),
    confirm: bool = Query(False, description="确认删除"),
    admin_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """删除Harbor中的特定仓库（及其所有镜像）"""
    if not confirm:
        raise HTTPException(status_code=400, detail="需要确认删除操作")
    
    try:
        async with HarborClient() as harbor_client:
            # 检查仓库是否存在
            repository_info = await harbor_client.get_repository(project_name, repository_name)
            if not repository_info:
                raise HTTPException(status_code=404, detail="仓库不存在")
            
            # 删除仓库
            success = await harbor_client.delete_repository(project_name, repository_name)
            
            if success:
                return {
                    "status": "success",
                    "message": f"仓库 {project_name}/{repository_name} 已删除",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                raise HTTPException(status_code=500, detail="删除操作失败")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除Harbor仓库失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.delete("/harbor/images/{project_name}/{repository_name}/{digest}")
async def delete_harbor_artifact(
    project_name: str = Path(..., description="项目名称"),
    repository_name: str = Path(..., description="仓库名称"),
    digest: str = Path(..., description="镜像摘要"),
    confirm: bool = Query(False, description="确认删除"),
    admin_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """删除Harbor中的特定镜像artifact"""
    if not confirm:
        raise HTTPException(status_code=400, detail="需要确认删除操作")
    
    try:
        async with HarborClient() as harbor_client:
            # 删除artifact
            success = await harbor_client.delete_artifact(project_name, repository_name, digest)
            
            if success:
                return {
                    "status": "success",
                    "message": f"镜像 {project_name}/{repository_name}@{digest} 已删除",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                raise HTTPException(status_code=500, detail="删除操作失败")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除Harbor镜像失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/harbor/status")
async def get_harbor_status(
    admin_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """获取Harbor服务状态"""
    try:
        async with HarborClient() as harbor_client:
            connectivity = await harbor_client.check_harbor_connectivity()
            
            if connectivity.get('status') == 'connected':
                storage_usage = await harbor_client.get_harbor_storage_usage()
                return {
                    "status": "connected",
                    "harbor_info": connectivity,
                    "storage_usage": storage_usage,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "status": "disconnected",
                    "error": connectivity.get('message'),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
    except Exception as e:
        logger.error(f"获取Harbor状态失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
