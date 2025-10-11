"""
仓库相关的工具函数
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Sequence
from app.models import Repository, RepositoryClassification, RepositoryTaskClassification
from app.models.task_classification import TaskClassification
from app.schemas.repository import RepositoryListItem
from app.schemas.task_classification import TaskClassification as TaskClassificationSchema
from app.services.classification import ClassificationService


async def enrich_repositories_with_classification_paths(
    repositories: Sequence[Repository], db: AsyncSession
) -> List[RepositoryListItem]:
    """为仓库添加分类路径信息（优化版本）"""
    if not repositories:
        return []
    
    from app.models.classification import Classification
    from sqlalchemy import text
    
    # 获取所有仓库的ID
    repo_ids = [repo.id for repo in repositories]
    
    # 一次性获取所有仓库的分类关联信息
    classification_query = select(RepositoryClassification).where(
        RepositoryClassification.repository_id.in_(repo_ids)
    ).order_by(RepositoryClassification.repository_id, RepositoryClassification.level.desc())
    
    result = await db.execute(classification_query)
    all_repo_classifications = result.scalars().all()
    
    # 构建仓库ID到分类的映射
    repo_to_classifications = {}
    for rc in all_repo_classifications:
        if rc.repository_id not in repo_to_classifications:
            repo_to_classifications[rc.repository_id] = []
        repo_to_classifications[rc.repository_id].append(rc)

    # 获取所有相关的分类ID
    all_classification_ids = list(set([rc.classification_id for rc in all_repo_classifications]))

    # 一次性获取所有仓库的任务分类关联信息
    task_classification_query = (
        select(RepositoryTaskClassification, TaskClassification)
        .join(TaskClassification)
        .where(RepositoryTaskClassification.repository_id.in_(repo_ids))
        .order_by(RepositoryTaskClassification.repository_id, TaskClassification.sort_order)
    )

    task_result = await db.execute(task_classification_query)
    all_repo_task_classifications = task_result.all()

    # 构建仓库ID到任务分类的映射
    repo_to_task_classifications = {}
    for rtc, task_class in all_repo_task_classifications:
        if rtc.repository_id not in repo_to_task_classifications:
            repo_to_task_classifications[rtc.repository_id] = []
        repo_to_task_classifications[rtc.repository_id].append(
            TaskClassificationSchema(
                id=task_class.id,
                name=task_class.name,
                name_zh=task_class.name_zh,
                description=task_class.description,
                icon=task_class.icon,
                sort_order=task_class.sort_order,
                is_active=task_class.is_active,
                created_at=task_class.created_at,
                updated_at=task_class.updated_at,
            )
        )
    
    # 批量获取分类路径
    classification_paths = {}
    if all_classification_ids:
        # 使用优化的批量路径查询
        path_query = text("""
            WITH RECURSIVE classification_paths AS (
                -- 基础查询：获取所有目标分类
                SELECT id, name, parent_id, level, id as original_id, 0 as depth
                FROM classifications 
                WHERE id = ANY(:classification_ids)
                
                UNION ALL
                
                -- 递归查询：获取父级分类
                SELECT c.id, c.name, c.parent_id, c.level, cp.original_id, cp.depth + 1
                FROM classifications c
                INNER JOIN classification_paths cp ON c.id = cp.parent_id
            )
            SELECT original_id, array_agg(name ORDER BY depth DESC) as path_names
            FROM classification_paths 
            GROUP BY original_id
        """)
        
        result = await db.execute(path_query, {"classification_ids": all_classification_ids})
        path_results = result.fetchall()
        
        for row in path_results:
            classification_paths[row.original_id] = row.path_names
    
    # 构建结果
    enriched_repos = []
    for repo in repositories:
        # 获取该仓库的分类路径
        classification_path = []
        repo_classifications = repo_to_classifications.get(repo.id, [])
        if repo_classifications:
            # 取最深层级的分类路径
            deepest_classification = repo_classifications[0]
            classification_path = classification_paths.get(
                deepest_classification.classification_id, []
            )

        # 获取该仓库的任务分类
        task_classifications_data = repo_to_task_classifications.get(repo.id, [])

        # 创建RepositoryListItem
        repo_dict = {
            "id": repo.id,
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "owner": repo.owner,
            "repo_type": repo.repo_type,
            "visibility": repo.visibility,
            "tags": repo.tags or [],
            "license": repo.license,
            "base_model": repo.base_model,
            "classification_path": classification_path,
            "task_classifications_data": task_classifications_data,
            "stars_count": repo.stars_count,
            "downloads_count": repo.downloads_count,
            "views_count": repo.views_count,
            "total_files": repo.total_files,
            "total_size": repo.total_size,
            "is_active": repo.is_active,
            "is_featured": repo.is_featured,
            "created_at": repo.created_at,
            "updated_at": repo.updated_at,
        }

        enriched_repos.append(RepositoryListItem(**repo_dict))

    return enriched_repos