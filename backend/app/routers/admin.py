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
