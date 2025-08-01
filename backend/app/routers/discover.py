from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_async_db
from app.models import Repository, User
from app.schemas.repository import RepositoryListItem
from app.dependencies.auth import get_current_user
from app.utils.repository_utils import enrich_repositories_with_classification_paths
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/featured", response_model=List[RepositoryListItem])
async def get_featured_repositories(
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    classification_id: Optional[int] = Query(None, description="分类ID筛选"),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取推荐仓库"""
    
    # 基础查询 - 推荐仓库
    query = select(Repository).where(
        and_(
            Repository.is_active == True,
            Repository.visibility == "public",
            Repository.is_featured == True  # 只显示推荐的仓库
        )
    ).options(selectinload(Repository.owner))

    # 仓库类型筛选
    if repo_type:
        query = query.where(Repository.repo_type == repo_type)

    # 分类筛选
    if classification_id:
        query = query.join(Repository.classifications).where(
            Repository.classifications.any(classification_id=classification_id)
        )

    # 按推荐权重排序（按星标数和更新时间综合排序）
    query = query.order_by(
        desc(Repository.stars_count * 0.6 + Repository.views_count * 0.4),
        desc(Repository.updated_at)
    ).limit(limit)

    result = await db.execute(query)
    repositories = result.scalars().all()

    return await enrich_repositories_with_classification_paths(repositories, db)


@router.get("/recent", response_model=List[RepositoryListItem])
async def get_recent_repositories(
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    classification_id: Optional[int] = Query(None, description="分类ID筛选"),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取最新仓库"""
    
    # 基础查询 - 最新仓库
    query = select(Repository).where(
        and_(
            Repository.is_active == True,
            Repository.visibility == "public"
        )
    ).options(selectinload(Repository.owner))

    # 仓库类型筛选
    if repo_type:
        query = query.where(Repository.repo_type == repo_type)

    # 分类筛选
    if classification_id:
        query = query.join(Repository.classifications).where(
            Repository.classifications.any(classification_id=classification_id)
        )

    # 按创建时间排序
    query = query.order_by(desc(Repository.created_at)).limit(limit)

    result = await db.execute(query)
    repositories = result.scalars().all()

    return await enrich_repositories_with_classification_paths(repositories, db)


@router.get("/popular", response_model=List[RepositoryListItem])
async def get_popular_repositories(
    period: str = Query("all", regex="^(day|week|month|year|all)$"),
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    classification_id: Optional[int] = Query(None, description="分类ID筛选"),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取受欢迎仓库"""
    
    # 基础查询
    query = select(Repository).where(
        and_(
            Repository.is_active == True,
            Repository.visibility == "public"
        )
    ).options(selectinload(Repository.owner))

    # 时间范围筛选
    if period != "all":
        time_ranges = {
            "day": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "year": timedelta(days=365)
        }
        since_date = datetime.utcnow() - time_ranges[period]
        query = query.where(Repository.created_at >= since_date)

    # 仓库类型筛选
    if repo_type:
        query = query.where(Repository.repo_type == repo_type)

    # 分类筛选
    if classification_id:
        query = query.join(Repository.classifications).where(
            Repository.classifications.any(classification_id=classification_id)
        )

    # 按受欢迎程度排序（综合星标数、下载数、浏览数）
    query = query.order_by(
        desc(
            Repository.stars_count * 0.5 + 
            Repository.downloads_count * 0.3 + 
            Repository.views_count * 0.2
        ),
        desc(Repository.created_at)
    ).limit(limit)

    result = await db.execute(query)
    repositories = result.scalars().all()

    return await enrich_repositories_with_classification_paths(repositories, db)


@router.get("/trending", response_model=List[RepositoryListItem])
async def get_trending_repositories(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    classification_id: Optional[int] = Query(None, description="分类ID筛选"),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取趋势仓库"""
    
    # 计算时间范围
    time_ranges = {
        "day": timedelta(days=1),
        "week": timedelta(days=7),
        "month": timedelta(days=30),
        "year": timedelta(days=365)
    }
    
    since_date = datetime.utcnow() - time_ranges[period]
    
    # 基础查询
    query = select(Repository).where(
        and_(
            Repository.is_active == True,
            Repository.visibility == "public",
            Repository.created_at >= since_date
        )
    ).options(selectinload(Repository.owner))

    # 仓库类型筛选
    if repo_type:
        query = query.where(Repository.repo_type == repo_type)

    # 分类筛选
    if classification_id:
        query = query.join(Repository.classifications).where(
            Repository.classifications.any(classification_id=classification_id)
        )

    # 趋势排序
    query = query.order_by(
        desc(
            Repository.stars_count * 0.4 + 
            Repository.views_count * 0.3 + 
            Repository.downloads_count * 0.3
        ),
        desc(Repository.updated_at)
    ).limit(limit)

    result = await db.execute(query)
    repositories = result.scalars().all()

    return await enrich_repositories_with_classification_paths(repositories, db)