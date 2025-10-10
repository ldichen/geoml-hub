"""
Task Classification Schemas
Author: Claude
Date: 2025-10-09
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TaskClassificationBase(BaseModel):
    """任务分类基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="English name")
    name_zh: str = Field(..., min_length=1, max_length=100, description="Chinese name")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    sort_order: int = Field(default=0, description="Sort order")
    icon: Optional[str] = Field(None, max_length=50, description="Icon identifier")
    is_active: bool = Field(default=True, description="Is active")


class TaskClassificationCreate(TaskClassificationBase):
    """创建任务分类"""
    pass


class TaskClassificationUpdate(BaseModel):
    """更新任务分类"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    name_zh: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = None
    icon: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class TaskClassification(TaskClassificationBase):
    """任务分类响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskClassificationList(BaseModel):
    """任务分类列表响应"""
    task_classifications: List[TaskClassification]
    total: int = 0


class RepositoryTaskClassificationBase(BaseModel):
    """仓库任务分类关联基础"""
    repository_id: int
    task_classification_id: int


class RepositoryTaskClassificationCreate(RepositoryTaskClassificationBase):
    """创建仓库任务分类关联"""
    pass


class RepositoryTaskClassification(RepositoryTaskClassificationBase):
    """仓库任务分类关联响应"""
    id: int
    created_at: datetime
    task_classification: TaskClassification

    class Config:
        from_attributes = True
