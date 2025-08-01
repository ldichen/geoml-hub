from sqlalchemy import Column, Integer, String, DateTime, Boolean, BIGINT, Text, JSON, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """用户表 - 基于外部认证系统的用户信息"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    # 外部认证系统的用户ID
    external_user_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    bio = Column(Text)
    website = Column(String(500))
    location = Column(String(255))
    
    # 社交统计
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    public_repos_count = Column(Integer, default=0)
    
    # 存储配额 (bytes)
    storage_quota = Column(BIGINT, default=536870912000)  # 500GB 默认配额
    storage_used = Column(BIGINT, default=0)
    
    # 账户状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    repositories = relationship("Repository", back_populates="owner", cascade="all, delete-orphan")
    stars = relationship("RepositoryStar", back_populates="user", cascade="all, delete-orphan")
    follows_as_follower = relationship("UserFollow", foreign_keys="UserFollow.follower_id", back_populates="follower", cascade="all, delete-orphan")
    follows_as_following = relationship("UserFollow", foreign_keys="UserFollow.following_id", back_populates="following", cascade="all, delete-orphan")
    file_uploads = relationship("FileUploadSession", back_populates="user", cascade="all, delete-orphan")
    repository_views = relationship("RepositoryView", back_populates="user", cascade="all, delete-orphan")
    personal_files = relationship("PersonalFile", back_populates="user", cascade="all, delete-orphan")
    model_services = relationship("ModelService", back_populates="user", cascade="all, delete-orphan")


class UserFollow(Base):
    """用户关注关系表"""
    __tablename__ = "user_follows"
    
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='unique_user_follow'),
        CheckConstraint('follower_id != following_id', name='no_self_follow'),
    )
    
    # 关系
    follower = relationship("User", foreign_keys=[follower_id], back_populates="follows_as_follower")
    following = relationship("User", foreign_keys=[following_id], back_populates="follows_as_following")


class UserStorage(Base):
    """用户存储统计表"""
    __tablename__ = "user_storage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_files = Column(Integer, default=0)
    total_size = Column(BIGINT, default=0)
    
    # 按文件类型统计
    model_files_count = Column(Integer, default=0)
    model_files_size = Column(BIGINT, default=0)
    dataset_files_count = Column(Integer, default=0)
    dataset_files_size = Column(BIGINT, default=0)
    image_files_count = Column(Integer, default=0)
    image_files_size = Column(BIGINT, default=0)
    document_files_count = Column(Integer, default=0)
    document_files_size = Column(BIGINT, default=0)
    other_files_count = Column(Integer, default=0)
    other_files_size = Column(BIGINT, default=0)
    
    last_calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User")