from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from app.database import get_async_db
from app.models import Repository, User, Classification
from app.schemas.repository import RepositoryListItem
from app.schemas.user import UserPublic
from app.dependencies.auth import get_current_user
from app.utils.repository_utils import enrich_repositories_with_classification_paths
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# 创建一个独立的路由模块用于顶级趋势端点
trending_router = APIRouter()


@router.get("/repositories", response_model=List[RepositoryListItem])
async def search_repositories(
    q: str = Query(..., description="搜索关键词"),
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    classification_id: Optional[int] = Query(None, description="分类ID筛选"),
    tags: Optional[str] = Query(None, description="标签筛选，逗号分隔"),
    sort_by: str = Query("relevance", regex="^(relevance|updated|created|stars|downloads|views)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """搜索仓库"""
    
    # 基础查询 - 只显示公开仓库
    query = select(Repository).where(
        and_(
            Repository.is_active == True,
            Repository.visibility == "public"
        )
    ).options(selectinload(Repository.owner))

    # 全文搜索
    search_conditions = []
    if q:
        search_terms = q.split()
        for term in search_terms:
            term_pattern = f"%{term}%"
            search_conditions.append(
                or_(
                    Repository.name.ilike(term_pattern),
                    Repository.description.ilike(term_pattern),
                    Repository.full_name.ilike(term_pattern),
                    Repository.readme_content.ilike(term_pattern)
                )
            )
    
    if search_conditions:
        query = query.where(and_(*search_conditions))

    # 仓库类型筛选
    if repo_type:
        query = query.where(Repository.repo_type == repo_type)

    # 分类筛选
    if classification_id:
        query = query.join(Repository.classifications).where(
            Repository.classifications.any(classification_id=classification_id)
        )

    # 标签筛选
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.where(Repository.tags.any(tag))

    # 排序
    if sort_by == "relevance" and q:
        # 简单的相关性排序 - 按名称匹配 > 描述匹配 > 更新时间
        query = query.order_by(
            desc(Repository.name.ilike(f"%{q}%")),
            desc(Repository.description.ilike(f"%{q}%")),
            desc(Repository.updated_at)
        )
    else:
        sort_field = {
            "updated": Repository.updated_at,
            "created": Repository.created_at,
            "stars": Repository.stars_count,
            "downloads": Repository.downloads_count,
            "views": Repository.views_count,
            "relevance": Repository.updated_at  # 默认按更新时间
        }[sort_by]

        if order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)

    # 分页
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    repositories = result.scalars().all()

    return await enrich_repositories_with_classification_paths(repositories, db)


@router.get("/users", response_model=List[UserPublic])
async def search_users(
    q: str = Query(..., description="搜索关键词"),
    verified_only: bool = Query(False, description="只显示已验证用户"),
    sort_by: str = Query("relevance", regex="^(relevance|created|followers|repositories)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """搜索用户"""
    
    query = select(User).where(User.is_active == True)

    # 搜索条件
    if q:
        search_pattern = f"%{q}%"
        query = query.where(
            or_(
                User.username.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
                User.bio.ilike(search_pattern)
            )
        )

    # 已验证用户筛选
    if verified_only:
        query = query.where(User.is_verified == True)

    # 排序
    if sort_by == "relevance" and q:
        query = query.order_by(
            desc(User.username.ilike(f"%{q}%")),
            desc(User.full_name.ilike(f"%{q}%")),
            desc(User.created_at)
        )
    else:
        sort_field = {
            "created": User.created_at,
            "followers": User.followers_count,
            "repositories": User.public_repos_count,
            "relevance": User.created_at
        }[sort_by]

        if order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)

    # 分页
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    return users


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
    
    since_date = datetime.now(timezone.utc) - time_ranges[period]
    
    # 基础查询
    query = select(Repository).where(
        and_(
            Repository.is_active == True,
            Repository.visibility == "public",
            Repository.created_at >= since_date  # 在时间范围内创建或更新的仓库
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

    # 趋势排序：综合考虑星标数、下载数、浏览数和最近活跃度
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


@trending_router.get("/", response_model=List[RepositoryListItem])
async def get_trending_repositories_top_level(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    classification_id: Optional[int] = Query(None, description="分类ID筛选"),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取趋势仓库（顶级路由）"""
    
    # 复用search模块的trending逻辑
    time_ranges = {
        "day": timedelta(days=1),
        "week": timedelta(days=7),
        "month": timedelta(days=30),
        "year": timedelta(days=365)
    }
    
    since_date = datetime.now(timezone.utc) - time_ranges[period]
    
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


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="搜索关键词前缀"),
    type: str = Query("all", regex="^(all|repositories|users|tags)$"),
    limit: int = Query(10, ge=1, le=20),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, List[Dict[str, Any]]]:
    """获取搜索建议"""
    
    suggestions = {
        "repositories": [],
        "users": [],
        "tags": []
    }
    
    if not q or len(q) < 2:
        return suggestions
    
    search_pattern = f"{q}%"
    
    # 仓库建议
    if type in ["all", "repositories"]:
        repo_query = select(Repository.name, Repository.full_name, Repository.description).where(
            and_(
                Repository.is_active == True,
                Repository.visibility == "public",
                or_(
                    Repository.name.ilike(search_pattern),
                    Repository.full_name.ilike(search_pattern)
                )
            )
        ).limit(limit)
        
        repo_result = await db.execute(repo_query)
        for row in repo_result:
            suggestions["repositories"].append({
                "name": row.name,
                "full_name": row.full_name,
                "description": row.description[:100] if row.description else None
            })
    
    # 用户建议
    if type in ["all", "users"]:
        user_query = select(User.username, User.full_name, User.bio).where(
            and_(
                User.is_active == True,
                or_(
                    User.username.ilike(search_pattern),
                    User.full_name.ilike(search_pattern)
                )
            )
        ).limit(limit)
        
        user_result = await db.execute(user_query)
        for row in user_result:
            suggestions["users"].append({
                "username": row.username,
                "full_name": row.full_name,
                "bio": row.bio[:100] if row.bio else None
            })
    
    # 标签建议
    if type in ["all", "tags"]:
        # 这里简化处理，实际应该从仓库的tags字段中提取热门标签
        tag_query = select(Repository.tags).where(
            and_(
                Repository.is_active == True,
                Repository.visibility == "public",
                Repository.tags.op("&&")(text(f"ARRAY['{q}%']"))  # PostgreSQL数组操作
            )
        ).limit(limit)
        
        try:
            tag_result = await db.execute(tag_query)
            unique_tags = set()
            for row in tag_result:
                if row.tags:
                    for tag in row.tags:
                        if tag.lower().startswith(q.lower()):
                            unique_tags.add(tag)
                            if len(unique_tags) >= limit:
                                break
            
            suggestions["tags"] = [{"tag": tag} for tag in unique_tags]
        except Exception as e:
            logger.warning(f"Tag search failed: {e}")
            suggestions["tags"] = []
    
    return suggestions


@router.get("/stats")
async def get_search_stats(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """获取搜索相关统计信息"""
    
    # 总体统计
    repo_count_query = select(func.count(Repository.id)).where(
        and_(Repository.is_active == True, Repository.visibility == "public")
    )
    user_count_query = select(func.count(User.id)).where(User.is_active == True)
    
    repo_count_result = await db.execute(repo_count_query)
    user_count_result = await db.execute(user_count_query)
    
    total_repositories = repo_count_result.scalar()
    total_users = user_count_result.scalar()
    
    # 分类统计
    repo_by_type_query = select(
        Repository.repo_type,
        func.count(Repository.id).label("count")
    ).where(
        and_(Repository.is_active == True, Repository.visibility == "public")
    ).group_by(Repository.repo_type)
    
    type_result = await db.execute(repo_by_type_query)
    repositories_by_type = {row.repo_type: row.count for row in type_result}
    
    return {
        "total_repositories": total_repositories,
        "total_users": total_users,
        "repositories_by_type": repositories_by_type,
        "search_features": [
            "全文搜索",
            "分类筛选", 
            "标签搜索",
            "用户搜索",
            "趋势发现",
            "搜索建议"
        ]
    }


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
        since_date = datetime.now(timezone.utc) - time_ranges[period]
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