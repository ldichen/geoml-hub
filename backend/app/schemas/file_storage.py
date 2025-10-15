from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class UploadStatusEnum(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileUploadSessionCreate(BaseModel):
    repository_id: Optional[int] = None
    filename: str = Field(..., min_length=1, max_length=500)
    file_path: str = Field(..., min_length=1, max_length=1000)
    file_size: int = Field(..., gt=0)
    mime_type: Optional[str] = Field(None, max_length=200)
    file_hash: Optional[str] = Field(None, max_length=128)
    chunk_size: int = Field(default=5242880, gt=0)  # 5MB default


class FileUploadSession(BaseModel):
    id: int
    session_id: str
    user_id: int
    repository_id: Optional[int] = None
    filename: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    file_hash: Optional[str] = None
    chunk_size: int
    total_chunks: int
    uploaded_chunks: int = 0
    chunk_status: Optional[Dict[str, Any]] = None
    minio_bucket: Optional[str] = None
    minio_object_key: Optional[str] = None
    minio_upload_id: Optional[str] = None
    status: UploadStatusEnum = UploadStatusEnum.PENDING
    progress_percentage: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileUploadChunk(BaseModel):
    session_id: str
    chunk_number: int = Field(..., ge=1)
    is_last_chunk: bool = False


class FileUploadProgress(BaseModel):
    session_id: str
    uploaded_chunks: int
    total_chunks: int
    progress_percentage: int
    status: UploadStatusEnum
    error_message: Optional[str] = None


class SystemStorage(BaseModel):
    id: int
    date: datetime
    total_users: int = 0
    total_repositories: int = 0
    total_files: int = 0
    total_size: int = 0
    public_repos: int = 0
    private_repos: int = 0
    model_repos: int = 0
    dataset_repos: int = 0
    model_files_size: int = 0
    dataset_files_size: int = 0
    image_files_size: int = 0
    document_files_size: int = 0
    other_files_size: int = 0
    daily_downloads: int = 0
    daily_uploads: int = 0
    daily_views: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class MinIOServiceHealth(BaseModel):
    id: int
    endpoint: str
    is_healthy: bool = True
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    available_space: Optional[int] = None
    used_space: Optional[int] = None
    total_space: Optional[int] = None
    checked_at: datetime
    total_buckets: int = 0
    total_objects: int = 0

    class Config:
        from_attributes = True


class StorageStats(BaseModel):
    """存储统计概览"""
    total_size: int
    total_files: int
    by_type: Dict[str, Dict[str, int]]  # {"model": {"size": 123, "files": 5}}
    growth_trend: List[Dict[str, Any]]  # 时间序列数据