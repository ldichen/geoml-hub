from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Classification(Base):
    """分类表（支持三级层次结构）"""
    __tablename__ = "classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    level = Column(Integer, nullable=False)  # 1=一级, 2=二级, 3=三级
    parent_id = Column(Integer, ForeignKey("classifications.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 约束：一级分类parent_id为NULL，其他级别必须有parent_id
    __table_args__ = (
        CheckConstraint(
            "(level = 1 AND parent_id IS NULL) OR (level > 1 AND parent_id IS NOT NULL)",
            name="check_level_parent_consistency"
        ),
        UniqueConstraint('name', 'parent_id', name='unique_name_per_parent'),
    )
    
    # Self-referential relationship for hierarchical structure
    parent = relationship("Classification", remote_side=[id], back_populates="children")
    children = relationship("Classification", back_populates="parent", cascade="all, delete-orphan")
    
    # Note: model_classifications relationship removed in V2.0
    # Classification relationships now handled by RepositoryClassification


# Note: ModelClassification removed in V2.0 - replaced by RepositoryClassification
# This class is preserved only for migration purposes and will be removed
# All model classification functionality has been moved to RepositoryClassification