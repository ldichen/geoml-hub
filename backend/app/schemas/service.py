"""
模型服务管理相关的Pydantic模式

这个模块包含了模型服务管理系统的所有数据验证和序列化模式：
- 服务创建、更新、响应模式
- 服务实例相关模式
- 服务日志和健康检查模式
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ServiceStatus(str, Enum):
    """服务状态枚举"""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running" 
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    IDLE = "idle"


class InstanceStatus(str, Enum):
    """实例状态枚举"""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping" 
    STOPPED = "stopped"
    ERROR = "error"


class HealthStatus(str, Enum):
    """健康检查状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"


class LogLevel(str, Enum):
    """日志级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class EventType(str, Enum):
    """事件类型枚举"""
    CREATE = "create"
    START = "start"
    STOP = "stop"
    ACCESS = "access"
    ERROR = "error"
    HEALTH_CHECK = "health_check"


# 服务基础模式
class ServiceBase(BaseModel):
    """服务基础模式"""
    service_name: str = Field(..., min_length=1, max_length=30, description="服务名称")
    model_id: str = Field("172.21.252.206", min_length=1, max_length=255, description="模型标识符")
    model_ip: str = Field(..., min_length=1, max_length=255, description="模型服务器IP地址")
    description: Optional[str] = Field(None, description="服务描述")
    cpu_limit: str = Field("0.3", description="CPU限制")
    memory_limit: str = Field("256Mi", description="内存限制")
    is_public: bool = Field(False, description="是否公开访问")
    priority: int = Field(2, ge=0, le=3, description="启动优先级，数值越小优先级越高")

    @validator('service_name')
    def validate_service_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('服务名称只能包含字母、数字、下划线和连字符')
        return v


class ServiceCreate(BaseModel):
    """创建服务请求模式"""
    service_name: str = Field(..., min_length=1, max_length=30, description="服务名称")
    model_id: str = Field(..., min_length=1, max_length=255, description="模型标识符")
    description: Optional[str] = Field(None, description="服务描述")
    cpu_limit: str = Field("0.3", description="CPU限制")
    memory_limit: str = Field("256Mi", description="内存限制")
    is_public: bool = Field(False, description="是否公开访问")
    priority: int = Field(2, ge=0, le=3, description="启动优先级，数值越小优先级越高")
    example_data: Optional[str] = Field(None, description="示例数据（base64编码或文件路径）")
    
    # model_ip 在后端自动设置，前端不需要传递
    model_ip: str = Field("172.21.252.206", exclude=True, description="模型服务器IP地址")
    
    @validator('service_name')
    def validate_service_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('服务名称只能包含字母、数字、下划线和连字符')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "geoml-classifier-v1",
                "model_id": "geo-classification-model",
                "description": "地理数据分类模型服务",
                "cpu_limit": "0.3",
                "memory_limit": "256Mi",
                "is_public": True,
                "priority": 2,
                "example_data": "base64:encoded_data_here"
            }
        }


class ServiceUpdate(BaseModel):
    """更新服务请求模式"""
    service_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    cpu_limit: Optional[str] = None
    memory_limit: Optional[str] = None
    is_public: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "description": "更新后的服务描述",
                "cpu_limit": "2.0",
                "memory_limit": "2Gi",
                "is_public": False
            }
        }


class ServiceResponse(ServiceBase):
    """服务响应模式"""
    id: int
    repository_id: int
    user_id: int
    status: ServiceStatus
    gradio_port: Optional[int] = None
    service_url: Optional[str] = None
    container_id: Optional[str] = None
    access_token: Optional[str] = None
    
    # 重试相关字段
    auto_start_retry_count: int = 0
    last_failure_reason: Optional[str] = None
    failure_type: Optional[str] = None
    
    # 统计信息
    access_count: int = 0
    start_count: int = 0
    total_runtime_minutes: int = 0
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    last_started_at: Optional[datetime] = None
    last_stopped_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None

    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """服务列表响应模式"""
    services: List[ServiceResponse]
    total: int
    page: int
    size: int
    auto_start_result: Optional[Dict[str, Any]] = None  # 自动启动结果


# 服务实例相关模式
class ServiceInstanceBase(BaseModel):
    """服务实例基础模式"""
    container_id: str = Field(..., description="容器ID")
    container_name: Optional[str] = None
    image_name: Optional[str] = None
    host_port: Optional[int] = None
    container_port: int = Field(7860, description="容器端口")


class ServiceInstanceCreate(ServiceInstanceBase):
    """创建服务实例请求模式"""
    pass


class ServiceInstanceResponse(ServiceInstanceBase):
    """服务实例响应模式"""
    id: int
    service_id: int
    status: InstanceStatus
    pid: Optional[int] = None
    cpu_usage_percent: Optional[float] = None
    memory_usage_bytes: Optional[int] = None
    
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None

    class Config:
        from_attributes = True


# 服务日志相关模式
class ServiceLogBase(BaseModel):
    """服务日志基础模式"""
    log_level: LogLevel
    message: str = Field(..., min_length=1, description="日志消息")
    event_type: Optional[EventType] = None
    metadata: Optional[Dict[str, Any]] = None


class ServiceLogCreate(ServiceLogBase):
    """创建服务日志请求模式"""
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ServiceLogResponse(ServiceLogBase):
    """服务日志响应模式"""
    id: int
    service_id: int
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceLogListResponse(BaseModel):
    """服务日志列表响应模式"""
    logs: List[ServiceLogResponse]
    total: int
    page: int
    size: int


# 健康检查相关模式
class ServiceHealthCheckBase(BaseModel):
    """健康检查基础模式"""
    status: HealthStatus
    response_time_ms: Optional[int] = None
    check_type: str = Field("http", description="检查类型")
    endpoint: Optional[str] = None
    http_status_code: Optional[int] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class ServiceHealthCheckCreate(ServiceHealthCheckBase):
    """创建健康检查请求模式"""
    pass


class ServiceHealthCheckResponse(ServiceHealthCheckBase):
    """健康检查响应模式"""
    id: int
    service_id: int
    checked_at: datetime

    class Config:
        from_attributes = True


class ServiceHealthCheckListResponse(BaseModel):
    """健康检查列表响应模式"""
    checks: List[ServiceHealthCheckResponse]
    total: int
    page: int
    size: int


# 服务控制相关模式
class ServiceStartRequest(BaseModel):
    """启动服务请求模式"""
    force_restart: bool = Field(False, description="是否强制重启")
    
    class Config:
        json_schema_extra = {
            "example": {
                "force_restart": False
            }
        }


class ServiceStopRequest(BaseModel):
    """停止服务请求模式"""
    force_stop: bool = Field(False, description="是否强制停止")
    timeout_seconds: int = Field(30, description="停止超时时间(秒)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "force_stop": False,
                "timeout_seconds": 30
            }
        }


class ServiceStatusResponse(BaseModel):
    """服务状态响应模式"""
    id: int
    service_name: str
    status: ServiceStatus
    is_healthy: bool
    uptime_seconds: Optional[int] = None
    resource_usage: Optional[Dict[str, Any]] = None
    last_health_check: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "service_name": "geoml-classifier-v1",
                "status": "running",
                "is_healthy": True,
                "uptime_seconds": 3600,
                "resource_usage": {
                    "cpu_percent": 15.5,
                    "memory_mb": 512,
                    "memory_percent": 25.0
                },
                "last_health_check": "2024-01-15T10:30:00Z",
                "error_message": None
            }
        }


# 批量操作相关模式
class BatchServiceRequest(BaseModel):
    """批量服务操作请求模式"""
    service_ids: List[int] = Field(..., min_items=1, description="服务ID列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_ids": [1, 2, 3]
            }
        }


class BatchServiceResponse(BaseModel):
    """批量服务操作响应模式"""
    successful: List[int] = Field(..., description="操作成功的服务ID")
    failed: List[Dict[str, Any]] = Field(..., description="操作失败的服务信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "successful": [1, 2],
                "failed": [
                    {
                        "service_id": 3,
                        "error": "Service is already running"
                    }
                ]
            }
        }


# 服务访问相关模式
class ServiceAccessRequest(BaseModel):
    """服务访问请求模式"""
    regenerate_token: bool = Field(False, description="是否重新生成访问令牌")


class ServiceAccessResponse(BaseModel):
    """服务访问响应模式"""
    service_url: str = Field(..., description="服务访问URL")
    access_token: Optional[str] = Field(None, description="访问令牌")
    demo_url: str = Field(..., description="Gradio Demo URL")
    is_public: bool = Field(..., description="是否公开访问")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_url": "http://localhost:7860",
                "access_token": "sk-1234567890abcdef",
                "demo_url": "http://localhost:7860/gradio",
                "is_public": True
            }
        }