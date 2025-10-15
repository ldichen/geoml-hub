from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, BIGINT, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UploadStatus(enum.Enum):
    """文件上传状态枚举"""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileUploadSession(Base):
    """文件上传会话表 - 支持分块上传"""
    __tablename__ = "file_upload_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True)
    
    # 文件信息
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)  # 目标路径
    file_size = Column(BIGINT, nullable=False)
    mime_type = Column(String(200))
    file_hash = Column(String(128))  # 客户端提供的文件哈希
    
    # 分块上传信息
    chunk_size = Column(Integer, default=5242880)  # 5MB 默认块大小
    total_chunks = Column(Integer, nullable=False)
    uploaded_chunks = Column(Integer, default=0)
    chunk_status = Column(JSON)  # 记录每个块的上传状态
    
    # MinIO 信息
    minio_bucket = Column(String(255))
    minio_object_key = Column(String(1000))
    minio_upload_id = Column(String(255))  # MultipartUpload ID
    
    # 状态和进度
    status = Column(Enum(UploadStatus), default=UploadStatus.PENDING)
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))  # 会话过期时间
    
    # 关系
    user = relationship("User", back_populates="file_uploads")
    repository = relationship("Repository")


class SystemStorage(Base):
    """系统存储统计表"""
    __tablename__ = "system_storage"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, unique=True)
    
    # 总体统计
    total_users = Column(Integer, default=0)
    total_repositories = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    total_size = Column(BIGINT, default=0)
    
    # 按类型统计
    public_repos = Column(Integer, default=0)
    private_repos = Column(Integer, default=0)
    model_repos = Column(Integer, default=0)
    dataset_repos = Column(Integer, default=0)
    
    # 按文件类型统计
    model_files_size = Column(BIGINT, default=0)
    dataset_files_size = Column(BIGINT, default=0)
    image_files_size = Column(BIGINT, default=0)
    document_files_size = Column(BIGINT, default=0)
    other_files_size = Column(BIGINT, default=0)
    
    # 活跃度统计
    daily_downloads = Column(Integer, default=0)
    daily_uploads = Column(Integer, default=0)
    daily_views = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MinIOServiceHealth(Base):
    """MinIO 服务健康状态表"""
    __tablename__ = "minio_service_health"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(500), nullable=False)
    
    # 健康状态
    is_healthy = Column(Boolean, default=True)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    
    # 存储信息
    available_space = Column(BIGINT)
    used_space = Column(BIGINT)
    total_space = Column(BIGINT)
    
    # 检查时间
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 统计信息
    total_buckets = Column(Integer, default=0)
    total_objects = Column(Integer, default=0)