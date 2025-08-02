"""
镜像管理相关的Pydantic模式
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ImageBase(BaseModel):
    """镜像基础模式"""
    name: str = Field(..., min_length=1, max_length=255, description="镜像名称")
    tag: str = Field("latest", min_length=1, max_length=100, description="镜像标签")
    description: Optional[str] = Field(None, max_length=1000, description="镜像描述")
    is_public: bool = Field(False, description="是否公开")


class ImageCreate(ImageBase):
    """创建镜像的请求模式"""
    pass


class ImageUpdate(BaseModel):
    """更新镜像的请求模式"""
    description: Optional[str] = Field(None, max_length=1000, description="镜像描述")
    is_public: Optional[bool] = Field(None, description="是否公开")


class ImageInfo(ImageBase):
    """镜像信息响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    repository_id: int
    harbor_project: str
    harbor_repository: str
    harbor_digest: Optional[str] = None
    harbor_size: Optional[int] = None
    status: str
    upload_progress: int
    error_message: Optional[str] = None
    service_count: int
    can_create_service: bool
    full_name: str
    created_by: int
    created_at: datetime
    updated_at: datetime


class ImageListResponse(BaseModel):
    """镜像列表响应"""
    success: bool
    data: List[ImageInfo]
    total: int
    message: Optional[str] = None


class ImageUploadResponse(BaseModel):
    """镜像上传响应"""
    success: bool
    data: Dict[str, Any]
    message: str


class ServiceFromImageCreate(BaseModel):
    """基于镜像创建服务的请求模式"""
    service_name: str = Field(..., min_length=1, max_length=255, description="服务名称")
    description: Optional[str] = Field("", max_length=1000, description="服务描述")
    cpu_limit: str = Field("0.5", description="CPU限制")
    memory_limit: str = Field("512m", description="内存限制")
    gradio_port: Optional[int] = Field(None, ge=1024, le=65535, description="Gradio端口")
    is_public: bool = Field(False, description="是否公开")
    priority: int = Field(2, ge=0, le=3, description="优先级")


class ServiceInfo(BaseModel):
    """服务信息模式"""
    id: int
    service_name: str
    status: str
    health_status: str
    service_url: Optional[str] = None
    created_at: datetime


class ServiceListResponse(BaseModel):
    """服务列表响应"""
    success: bool
    data: List[ServiceInfo]
    total: int
    message: Optional[str] = None


class ImageBuildLogInfo(BaseModel):
    """镜像构建日志模式"""
    id: int
    stage: Optional[str]
    message: Optional[str]
    level: str
    created_at: datetime


class BuildLogsResponse(BaseModel):
    """构建日志响应"""
    success: bool
    data: List[ImageBuildLogInfo]
    total: int
    message: Optional[str] = None


class ImageDeleteResponse(BaseModel):
    """镜像删除响应"""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """错误响应模式"""
    success: bool = False
    error: str
    detail: Optional[str] = None