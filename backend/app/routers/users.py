from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_async_db
from app.models import User, UserFollow, Repository, RepositoryStar
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserProfile,
    UserPublic,
    UserFollow as UserFollowSchema,
    UserStorage as UserStorageSchema,
)
from app.schemas.repository import RepositoryListItem
from app.utils.repository_utils import enrich_repositories_with_classification_paths
from app.services.user_service import UserService
from app.dependencies.auth import get_current_user, get_current_active_user
from app.middleware.error_response import NotFoundError, AuthorizationError

router = APIRouter()


@router.get("/", response_model=List[UserPublic])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="搜索用户名或全名"),
    verified_only: bool = Query(False, description="只显示已验证用户"),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户列表"""
    query = select(User).where(User.is_active == True)

    if search:
        query = query.where(
            or_(User.username.ilike(f"%{search}%"), User.full_name.ilike(f"%{search}%"))
        )

    if verified_only:
        query = query.where(User.is_verified == True)

    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    return users


@router.get("/{username}", response_model=UserProfile)
async def get_user_by_username(
    username: str = Path(..., description="用户名"), db: AsyncSession = Depends(get_async_db)
):
    """根据用户名获取用户详情"""
    query = select(User).where(and_(User.username == username, User.is_active == True))

    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user


@router.get("/{username}/repositories", response_model=List[RepositoryListItem])
async def get_user_repositories(
    username: str = Path(..., description="用户名"),
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    visibility: Optional[str] = Query(None, regex="^(public|private)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户的仓库列表"""
    # 首先检查用户是否存在
    user_query = select(User).where(
        and_(User.username == username, User.is_active == True)
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        raise NotFoundError("用户不存在")

    # 检查是否是用户本人
    is_owner = current_user and getattr(current_user, "username") == username

    # 查询用户的仓库
    query = (
        select(Repository)
        .where(and_(Repository.owner_id == user.id, Repository.is_active == True))
        .options(selectinload(Repository.owner))
    )

    if repo_type:
        query = query.where(Repository.repo_type == repo_type)

    if visibility:
        if visibility == "private" and not is_owner:
            raise AuthorizationError("无权访问私有仓库")
        query = query.where(Repository.visibility == visibility)
    else:
        # 如果是用户本人，显示所有仓库；否则只显示公开仓库
        if not is_owner:
            query = query.where(Repository.visibility == "public")

    query = query.offset(skip).limit(limit).order_by(Repository.updated_at.desc())

    result = await db.execute(query)
    repositories = result.scalars().all()

    # 添加分类路径信息
    enriched_repositories = await enrich_repositories_with_classification_paths(repositories, db)
    return enriched_repositories


@router.get("/{username}/followers", response_model=List[UserPublic])
async def get_user_followers(
    username: str = Path(..., description="用户名"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户的关注者列表"""
    # 首先检查用户是否存在
    user_query = select(User).where(
        and_(User.username == username, User.is_active == True)
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 查询关注者
    query = (
        select(User)
        .join(UserFollow, UserFollow.follower_id == User.id)
        .where(UserFollow.following_id == user.id)
        .offset(skip)
        .limit(limit)
        .order_by(UserFollow.created_at.desc())
    )

    result = await db.execute(query)
    followers = result.scalars().all()

    return followers


@router.get("/{username}/following", response_model=List[UserPublic])
async def get_user_following(
    username: str = Path(..., description="用户名"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户关注的人列表"""
    # 首先检查用户是否存在
    user_query = select(User).where(
        and_(User.username == username, User.is_active == True)
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 查询关注的人
    query = (
        select(User)
        .join(UserFollow, UserFollow.following_id == User.id)
        .where(UserFollow.follower_id == user.id)
        .offset(skip)
        .limit(limit)
        .order_by(UserFollow.created_at.desc())
    )

    result = await db.execute(query)
    following = result.scalars().all()

    return following


@router.post("/", response_model=UserProfile)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """创建新用户"""
    user_service = UserService(db)
    user = await user_service.create_user(user_data)
    return user


@router.put("/{username}", response_model=UserProfile)
async def update_user(
    user_data: UserUpdate,
    username: str = Path(..., description="用户名"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """更新用户信息 - 需要认证且只能更新自己的信息"""
    # 检查是否是用户本人
    if getattr(current_user, "username") != username:
        raise AuthorizationError("只能更新自己的用户信息")
    user_service = UserService(db)
    user = await user_service.update_user(username, user_data.model_dump(exclude_unset=True))
    return user


@router.post("/{username}/follow")
async def follow_user(
    username: str = Path(..., description="要关注的用户名"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """关注用户 - 需要认证"""
    # 不能关注自己
    if getattr(current_user, "username") == username:
        raise HTTPException(status_code=400, detail="不能关注自己")

    user_service = UserService(db)
    await user_service.follow_user(current_user_id=getattr(current_user, "id"), target_username=username)

    return {"message": f"已关注用户 {username}"}


@router.delete("/{username}/follow")
async def unfollow_user(
    username: str = Path(..., description="要取消关注的用户名"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """取消关注用户 - 需要认证"""
    user_service = UserService(db)
    await user_service.unfollow_user(current_user_id=getattr(current_user, "id"), target_username=username)

    return {"message": f"已取消关注用户 {username}"}


@router.get("/{username}/starred", response_model=List[RepositoryListItem])
async def get_user_starred_repositories(
    username: str = Path(..., description="用户名"),
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户收藏的仓库列表"""
    # 首先检查用户是否存在
    user_query = select(User).where(
        and_(User.username == username, User.is_active == True)
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 查询用户收藏的仓库
    query = (
        select(Repository)
        .join(RepositoryStar, RepositoryStar.repository_id == Repository.id)
        .where(
            and_(
                RepositoryStar.user_id == user.id,
                Repository.is_active == True,
                Repository.visibility == "public"  # 只显示公开仓库
            )
        )
        .options(selectinload(Repository.owner))
    )

    if repo_type:
        query = query.where(Repository.repo_type == repo_type)

    query = query.offset(skip).limit(limit).order_by(RepositoryStar.created_at.desc())

    result = await db.execute(query)
    repositories = result.scalars().all()

    # 添加分类路径信息
    enriched_repositories = await enrich_repositories_with_classification_paths(repositories, db)
    return enriched_repositories


@router.get("/{username}/stats")
async def get_user_stats(
    username: str = Path(..., description="用户名"), db: AsyncSession = Depends(get_async_db)
):
    """获取用户统计信息"""
    user_service = UserService(db)
    stats = await user_service.get_user_stats(username)
    return stats


@router.get("/{username}/storage")
async def get_user_storage(
    username: str = Path(..., description="用户名"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取用户存储使用情况"""
    
    # 检查用户是否存在
    user_query = select(User).where(
        and_(User.username == username, User.is_active == True)
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限：只有用户自己或管理员可以查看详细存储信息
    is_owner = current_user and current_user.id == user.id
    is_admin = current_user and getattr(current_user, "is_admin", False)
    
    if not is_owner and not is_admin:
        # 非所有者只能看到基本信息，但也需要计算真实的存储使用量
        from app.models import RepositoryFile
        
        # 计算真实的存储使用量
        real_storage_query = await db.execute(
            select(
                func.sum(RepositoryFile.file_size).label("total_storage_used")
            ).join(Repository).where(
                and_(
                    Repository.owner_id == user.id,
                    Repository.is_active == True,
                    RepositoryFile.is_deleted == False
                )
            )
        )
        real_storage_row = real_storage_query.first()
        real_storage_used = real_storage_row.total_storage_used or 0
        
        storage_quota = user.storage_quota if user.storage_quota else 500 * 1024 * 1024 * 1024  # 500GB默认
        return {
            "username": user.username,
            "public_repositories": user.public_repos_count,
            "storage_used": real_storage_used,  # 使用真实存储使用量
            "storage_quota": storage_quota,
            "storage_usage_percentage": (real_storage_used / storage_quota) * 100
        }
    
    # 获取详细存储信息
    from app.models import RepositoryFile
    
    # 计算总的文件统计（实时计算真实数据）
    total_stats = await db.execute(
        select(
            func.count(RepositoryFile.id).label("total_files"),
            func.sum(RepositoryFile.file_size).label("total_storage_used")
        ).join(Repository).where(
            and_(
                Repository.owner_id == user.id,
                Repository.is_active == True,
                RepositoryFile.is_deleted == False
            )
        )
    )
    total_stats_row = total_stats.first()
    real_total_files = total_stats_row.total_files or 0
    real_storage_used = total_stats_row.total_storage_used or 0
    
    # 计算各类型文件的存储使用
    storage_by_type = await db.execute(
        select(
            RepositoryFile.file_type,
            func.count(RepositoryFile.id).label("count"),
            func.sum(RepositoryFile.file_size).label("total_size")
        ).join(Repository).where(
            and_(
                Repository.owner_id == user.id,
                Repository.is_active == True,
                RepositoryFile.is_deleted == False
            )
        ).group_by(RepositoryFile.file_type)
    )
    
    storage_breakdown = {}
    for row in storage_by_type:
        storage_breakdown[row.file_type or "other"] = {
            "count": row.count,
            "total_size": row.total_size or 0
        }
    
    # 获取仓库存储分布（实时计算每个仓库的文件数量和大小）
    repo_storage = await db.execute(
        select(
            Repository.name,
            Repository.repo_type,
            func.count(RepositoryFile.id).label("files"),
            func.sum(RepositoryFile.file_size).label("size")
        ).join(RepositoryFile, Repository.id == RepositoryFile.repository_id)
        .where(
            and_(
                Repository.owner_id == user.id,
                Repository.is_active == True,
                RepositoryFile.is_deleted == False
            )
        )
        .group_by(Repository.id, Repository.name, Repository.repo_type)
        .order_by(func.sum(RepositoryFile.file_size).desc())
        .limit(3)  # 只显示前3个最大的仓库
    )
    
    largest_repositories = [
        {
            "name": row.name,
            "type": row.repo_type,
            "files": row.files or 0,  # 使用实时计算的文件数量
            "size": row.size or 0     # 使用实时计算的大小
        }
        for row in repo_storage
    ]
    
    # 计算存储配额使用率（使用真实存储使用量）
    storage_quota = user.storage_quota or 500 * 1024 * 1024 * 1024  # 500GB默认
    usage_percentage = (real_storage_used / storage_quota) * 100 if storage_quota > 0 else 0
    
    return {
        "username": user.username,
        "storage_used": real_storage_used,  # 使用实时计算的真实存储使用量
        "storage_quota": storage_quota,
        "storage_usage_percentage": usage_percentage,
        "storage_breakdown": storage_breakdown,
        "largest_repositories": largest_repositories,
        "total_repositories": user.public_repos_count,
        "total_files": real_total_files,  # 使用实时计算的真实文件总数
        "recommendations": _get_storage_recommendations(real_storage_used, storage_quota, storage_breakdown)
    }


def _get_storage_recommendations(storage_used: int, storage_quota: int, storage_breakdown: dict) -> List[str]:
    """生成存储优化建议"""
    recommendations = []
    
    usage_percentage = (storage_used / storage_quota) * 100 if storage_quota > 0 else 0
    
    if usage_percentage > 80:
        recommendations.append("存储空间使用率超过80%，建议清理不必要的文件")
    
    if usage_percentage > 90:
        recommendations.append("存储空间即将耗尽，请尽快清理文件或申请扩容")
    
    # 检查大文件类型
    total_size = sum(item["total_size"] for item in storage_breakdown.values())
    if total_size > 0:
        for file_type, data in storage_breakdown.items():
            if data["total_size"] / total_size > 0.5:
                recommendations.append(f"{file_type}文件占用超过50%的存储空间，建议优化")
    
    if len(recommendations) == 0:
        recommendations.append("存储使用状况良好")
    
    return recommendations
