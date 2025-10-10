from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_async_db
from app.models.classification import Classification
from app.models.user import User
from app.schemas.classification import (
    ClassificationCreate,
    ClassificationUpdate,
    Classification as ClassificationSchema,
    ClassificationWithChildren,
    ClassificationTree,
)
from app.services.classification import ClassificationService
from app.services.classification_migration_service import ClassificationMigrationService
from app.dependencies.auth import require_admin

router = APIRouter()


@router.get("/tree", response_model=ClassificationTree)
async def get_classification_tree(
    level: Optional[int] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_async_db)
):
    """获取分类树结构"""
    service = ClassificationService(db)
    classifications = await service.get_classification_tree(level=level, active_only=active_only)
    return ClassificationTree(classifications=classifications)


@router.get("/", response_model=List[ClassificationSchema])
async def get_classifications(
    level: Optional[int] = None,
    parent_id: Optional[int] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_async_db)
):
    """获取分类列表"""
    service = ClassificationService(db)
    classifications = await service.get_classifications(
        level=level, 
        parent_id=parent_id, 
        active_only=active_only
    )
    return classifications


@router.get("/{classification_id}", response_model=ClassificationWithChildren)
async def get_classification(
    classification_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取单个分类详情"""
    service = ClassificationService(db)
    classification = await service.get_classification_by_id(classification_id)
    if not classification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    return classification


@router.post("/", response_model=ClassificationSchema)
async def create_classification(
    classification: ClassificationCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建分类"""
    service = ClassificationService(db)
    try:
        return await service.create_classification(classification)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{classification_id}", response_model=ClassificationSchema)
async def update_classification(
    classification_id: int,
    classification: ClassificationUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin)
):
    """更新分类（需要管理员权限）- 自动同步所有相关仓库的README"""
    service = ClassificationService(db)
    try:
        # 检查是否修改了名称
        old_classification = await service.get_classification_by_id(classification_id)
        if not old_classification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        name_changed = (
            classification.name and
            classification.name != old_classification.name
        )

        # 更新分类
        updated = await service.update_classification(classification_id, classification)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        # 如果名称被修改，批量同步所有使用该分类的仓库README
        if name_changed:
            migration_service = ClassificationMigrationService(db)
            sync_result = await migration_service.batch_sync_readmes_for_sphere_classification(
                classification_id
            )
            # 记录同步结果到日志
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.info(
                f"Classification {classification_id} updated. "
                f"Synced {sync_result['updated']} repositories, "
                f"failed {sync_result['failed']} repositories."
            )

        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{classification_id}")
async def delete_classification(
    classification_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """删除分类"""
    service = ClassificationService(db)
    success = await service.delete_classification(classification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    return {"message": "分类删除成功"}


@router.get("/{classification_id}/children", response_model=List[ClassificationSchema])
async def get_classification_children(
    classification_id: int,
    active_only: bool = True,
    db: AsyncSession = Depends(get_async_db)
):
    """获取分类的子分类"""
    service = ClassificationService(db)
    children = await service.get_children(classification_id, active_only)
    return children


@router.get("/{classification_id}/path", response_model=List[str])
async def get_classification_path(
    classification_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取分类路径"""
    service = ClassificationService(db)
    path = await service.get_classification_path(classification_id)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    return path