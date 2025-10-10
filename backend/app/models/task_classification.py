"""
Task Classification Models
Author: Claude
Date: 2025-10-09

Single-level task classification system for repositories.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TaskClassification(Base):
    """任务分类表（单级扁平结构）"""
    __tablename__ = "task_classifications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)  # English name
    name_zh = Column(String(100), nullable=False, index=True)  # Chinese name
    description = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0, index=True)
    icon = Column(String(50), nullable=True)  # Optional icon identifier
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to repository associations
    repository_associations = relationship(
        "RepositoryTaskClassification",
        back_populates="task_classification",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TaskClassification(id={self.id}, name='{self.name}', name_zh='{self.name_zh}')>"
