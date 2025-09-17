from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, BIGINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Snapshot(Base):
    """快照表 (对应Git的commit)"""
    __tablename__ = "snapshots"

    id = Column(String(12), primary_key=True)  # 短hash ID
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)  # 提交信息
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    branch = Column(String(255), default="main")  # 所属分支
    parent_snapshot_id = Column(String(12), nullable=True)  # 父快照
    created_at = Column(DateTime, default=func.now())

    # 关联关系
    repository = relationship("Repository", back_populates="snapshots")
    author = relationship("User")
    files = relationship("SnapshotFile", back_populates="snapshot", cascade="all, delete-orphan")


class Branch(Base):
    """分支表"""
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)  # 分支名称
    head_snapshot_id = Column(String(12), ForeignKey("snapshots.id", ondelete="SET NULL"), nullable=True)  # 最新快照
    is_default = Column(Boolean, default=False)  # 是否为默认分支
    created_at = Column(DateTime, default=func.now())

    # 关联关系
    repository = relationship("Repository", back_populates="branches")
    head_snapshot = relationship("Snapshot")

    # 唯一约束：同一仓库内分支名不能重复
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class Release(Base):
    """发布版本表"""
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    tag_name = Column(String(100), nullable=False)  # v1.0, v2.0
    snapshot_id = Column(String(12), ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    is_prerelease = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # 关联关系
    repository = relationship("Repository", back_populates="releases")
    snapshot = relationship("Snapshot")

    # 唯一约束：同一仓库内标签名不能重复
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class SnapshotFile(Base):
    """快照文件关联表"""
    __tablename__ = "snapshot_files"

    snapshot_id = Column(String(12), ForeignKey("snapshots.id", ondelete="CASCADE"), primary_key=True)
    file_path = Column(String(1000), primary_key=True)  # 文件在仓库中的路径
    storage_path = Column(String(1000), nullable=False)  # 在MinIO中的实际路径
    file_hash = Column(String(64))  # 文件内容hash (SHA-256)
    file_size = Column(BIGINT)
    content_type = Column(String(200))
    created_at = Column(DateTime, default=func.now())

    # 关联关系
    snapshot = relationship("Snapshot", back_populates="files")