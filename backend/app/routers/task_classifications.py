"""
Task Classifications API Router
Author: Claude
Date: 2025-10-09
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_async_db
from app.models.user import User
from app.dependencies.auth import require_admin, get_current_user
from app.schemas.task_classification import (
    TaskClassificationCreate,
    TaskClassificationUpdate,
    TaskClassification,
    TaskClassificationList,
)
from app.services.task_classification_service import TaskClassificationService

router = APIRouter()


@router.get("/", response_model=TaskClassificationList)
async def get_task_classifications(
    active_only: bool = Query(True, description="Only return active classifications"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有任务分类"""
    service = TaskClassificationService(db)
    classifications = await service.get_all(active_only=active_only)
    return TaskClassificationList(
        task_classifications=classifications,
        total=len(classifications)
    )


@router.get("/{classification_id}", response_model=TaskClassification)
async def get_task_classification(
    classification_id: int = Path(..., description="Task classification ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取单个任务分类"""
    service = TaskClassificationService(db)
    classification = await service.get_by_id(classification_id)

    if not classification:
        raise HTTPException(status_code=404, detail="Task classification not found")

    return classification


@router.post("/", response_model=TaskClassification)
async def create_task_classification(
    data: TaskClassificationCreate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """创建任务分类（管理员）"""
    service = TaskClassificationService(db)

    try:
        classification = await service.create(data)
        return classification
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{classification_id}", response_model=TaskClassification)
async def update_task_classification(
    classification_id: int = Path(..., description="Task classification ID"),
    data: TaskClassificationUpdate = ...,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """更新任务分类（管理员）"""
    service = TaskClassificationService(db)
    classification = await service.update(classification_id, data)

    if not classification:
        raise HTTPException(status_code=404, detail="Task classification not found")

    return classification


@router.delete("/{classification_id}")
async def delete_task_classification(
    classification_id: int = Path(..., description="Task classification ID"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """删除任务分类（管理员）"""
    service = TaskClassificationService(db)
    success = await service.delete(classification_id)

    if not success:
        raise HTTPException(status_code=404, detail="Task classification not found")

    return {"message": "Task classification deleted successfully"}


@router.get("/{classification_id}/repositories")
async def get_repositories_by_task(
    classification_id: int = Path(..., description="Task classification ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """获取使用该任务分类的仓库列表"""
    service = TaskClassificationService(db)

    # Verify task classification exists
    classification = await service.get_by_id(classification_id)
    if not classification:
        raise HTTPException(status_code=404, detail="Task classification not found")

    repositories = await service.get_repositories_by_task(
        classification_id, skip=skip, limit=limit
    )

    return {
        "task_classification": classification,
        "repositories": repositories,
        "total": len(repositories)
    }
