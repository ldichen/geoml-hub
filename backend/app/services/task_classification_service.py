"""
Task Classification Service
Author: Claude
Date: 2025-10-09
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from app.models.task_classification import TaskClassification
from app.models.repository import Repository, RepositoryTaskClassification
from app.schemas.task_classification import (
    TaskClassificationCreate,
    TaskClassificationUpdate,
    TaskClassification as TaskClassificationSchema,
)


class TaskClassificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self, active_only: bool = True
    ) -> List[TaskClassificationSchema]:
        """获取所有任务分类"""
        stmt = select(TaskClassification).order_by(TaskClassification.sort_order, TaskClassification.name)

        if active_only:
            stmt = stmt.where(TaskClassification.is_active == True)

        result = await self.db.execute(stmt)
        classifications = result.scalars().all()

        return [TaskClassificationSchema.model_validate(c) for c in classifications]

    async def get_by_id(self, classification_id: int) -> Optional[TaskClassificationSchema]:
        """根据ID获取任务分类"""
        stmt = select(TaskClassification).where(TaskClassification.id == classification_id)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()

        if classification:
            return TaskClassificationSchema.model_validate(classification)
        return None

    async def get_by_name(self, name: str) -> Optional[TaskClassificationSchema]:
        """根据名称获取任务分类"""
        stmt = select(TaskClassification).where(TaskClassification.name == name)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()

        if classification:
            return TaskClassificationSchema.model_validate(classification)
        return None

    async def create(
        self, data: TaskClassificationCreate
    ) -> TaskClassificationSchema:
        """创建任务分类"""
        # Check if name already exists
        existing = await self.get_by_name(data.name)
        if existing:
            raise ValueError(f"Task classification with name '{data.name}' already exists")

        classification = TaskClassification(**data.model_dump())
        self.db.add(classification)
        await self.db.commit()
        await self.db.refresh(classification)

        return TaskClassificationSchema.model_validate(classification)

    async def update(
        self, classification_id: int, data: TaskClassificationUpdate
    ) -> Optional[TaskClassificationSchema]:
        """更新任务分类"""
        stmt = select(TaskClassification).where(TaskClassification.id == classification_id)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()

        if not classification:
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(classification, field, value)

        await self.db.commit()
        await self.db.refresh(classification)

        return TaskClassificationSchema.model_validate(classification)

    async def delete(self, classification_id: int) -> bool:
        """删除任务分类"""
        stmt = select(TaskClassification).where(TaskClassification.id == classification_id)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()

        if not classification:
            return False

        await self.db.delete(classification)
        await self.db.commit()
        return True

    async def get_repositories_by_task(
        self, task_classification_id: int, skip: int = 0, limit: int = 50
    ) -> List[Repository]:
        """获取使用该任务分类的所有仓库"""
        stmt = (
            select(Repository)
            .join(RepositoryTaskClassification)
            .where(
                and_(
                    RepositoryTaskClassification.task_classification_id == task_classification_id,
                    Repository.is_active == True
                )
            )
            .order_by(Repository.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        repositories = result.scalars().all()
        return repositories

    async def add_to_repository(
        self, repository_id: int, task_classification_id: int
    ) -> bool:
        """为仓库添加任务分类"""
        # Check if association already exists
        stmt = select(RepositoryTaskClassification).where(
            and_(
                RepositoryTaskClassification.repository_id == repository_id,
                RepositoryTaskClassification.task_classification_id == task_classification_id
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return False  # Already exists

        # Create association
        association = RepositoryTaskClassification(
            repository_id=repository_id,
            task_classification_id=task_classification_id
        )
        self.db.add(association)
        await self.db.commit()
        return True

    async def remove_from_repository(
        self, repository_id: int, task_classification_id: int
    ) -> bool:
        """从仓库移除任务分类"""
        stmt = select(RepositoryTaskClassification).where(
            and_(
                RepositoryTaskClassification.repository_id == repository_id,
                RepositoryTaskClassification.task_classification_id == task_classification_id
            )
        )
        result = await self.db.execute(stmt)
        association = result.scalar_one_or_none()

        if not association:
            return False

        await self.db.delete(association)
        await self.db.commit()
        return True

    async def get_repository_tasks(
        self, repository_id: int
    ) -> List[TaskClassificationSchema]:
        """获取仓库的所有任务分类"""
        stmt = (
            select(TaskClassification)
            .join(RepositoryTaskClassification)
            .where(RepositoryTaskClassification.repository_id == repository_id)
            .order_by(TaskClassification.sort_order)
        )

        result = await self.db.execute(stmt)
        classifications = result.scalars().all()

        return [TaskClassificationSchema.model_validate(c) for c in classifications]
