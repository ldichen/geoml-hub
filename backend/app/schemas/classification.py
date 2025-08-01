from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ClassificationBase(BaseModel):
    """分类基础模式"""
    name: str = Field(..., min_length=1, max_length=255, description="分类名称")
    level: int = Field(..., ge=1, le=3, description="分类级别: 1=一级, 2=二级, 3=三级")
    parent_id: Optional[int] = Field(None, description="父级分类ID")
    sort_order: int = Field(default=0, description="排序顺序")
    is_active: bool = Field(default=True, description="是否启用")


class ClassificationCreate(ClassificationBase):
    """创建分类"""
    pass


class ClassificationUpdate(BaseModel):
    """更新分类"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="分类名称")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否启用")


class Classification(ClassificationBase):
    """分类响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClassificationWithChildren(Classification):
    """带子分类的分类响应"""
    children: List['ClassificationWithChildren'] = Field(default_factory=list)
    path: List[str] = Field(default_factory=list, description="分类路径")
    
    class Config:
        from_attributes = True


class ClassificationTree(BaseModel):
    """分类树响应"""
    classifications: List[ClassificationWithChildren]


# Note: V1.0 ModelClassification schemas removed in V2.0
# Model classification functionality has been moved to RepositoryClassification
# These schemas are preserved only for migration purposes


# 解决前向引用问题
ClassificationWithChildren.model_rebuild()