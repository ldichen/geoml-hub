"""
模型服务管理相关的数据库模型

这个模块包含了模型服务管理系统的所有数据库模型：
- ModelService: 模型服务主表
- ServiceInstance: 服务实例表  
- ServiceLog: 服务日志表
- ServiceHealthCheck: 服务健康检查表
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, BIGINT, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ModelService(Base):
    """模型服务表 - 直接包含容器信息的一体化模型"""
    __tablename__ = "model_services"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关系
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=True, comment="关联的镜像ID")
    
    # 服务基本信息
    service_name = Column(String(255), nullable=False, comment="服务名称")
    model_ip = Column(String(255), nullable=False, comment="模型服务器IP地址")
    description = Column(Text, comment="服务描述")
    
    # 容器基本信息 - 创建服务时确定
    container_id = Column(String(255), comment="容器ID")
    
    # 网络配置 - 创建服务时确定
    gradio_port = Column(Integer, comment="服务端口（主机端口和容器端口统一）")
    service_url = Column(String(500), comment="服务访问URL")
    
    # 资源配置 - 创建服务时确定
    cpu_limit = Column(String(50), default="0.5", comment="CPU限制")
    memory_limit = Column(String(50), default="512Mi", comment="内存限制")
    
    # 服务配置
    example_data_path = Column(String(1000), comment="示例数据路径")
    is_public = Column(Boolean, default=False, comment="是否公开访问")
    access_token = Column(String(255), comment="访问令牌")
    priority = Column(Integer, default=100, comment="启动优先级，数值越小优先级越高")
    
    # 运行时状态 - 启动/停止时更新
    status = Column(String(50), default="created", comment="服务状态: created, starting, running, stopping, stopped, error, idle")
    health_status = Column(String(50), default="unknown", comment="健康状态: healthy, unhealthy, unknown, timeout")
    error_message = Column(Text, comment="错误信息")
    pid = Column(Integer, comment="容器进程ID")
    
    # 健康检查和重试
    last_health_check = Column(DateTime(timezone=True), comment="最后健康检查时间")
    auto_start_retry_count = Column(Integer, default=0, comment="自动启动重试次数")
    last_failure_reason = Column(Text, comment="最后一次失败原因")
    failure_type = Column(String(50), comment="失败类型: temporary, permanent, unknown")
    
    # 资源使用统计
    cpu_usage_percent = Column(DECIMAL(5, 2), comment="CPU使用率")
    memory_usage_bytes = Column(BIGINT, comment="内存使用量")
    access_count = Column(Integer, default=0, comment="访问次数")
    start_count = Column(Integer, default=0, comment="启动次数")
    total_runtime_minutes = Column(Integer, default=0, comment="总运行时间(分钟)")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_accessed_at = Column(DateTime(timezone=True), comment="最后访问时间")
    last_started_at = Column(DateTime(timezone=True), comment="最后启动时间")
    last_stopped_at = Column(DateTime(timezone=True), comment="最后停止时间")
    last_heartbeat = Column(DateTime(timezone=True), comment="最后心跳时间")
    
    # 约束
    __table_args__ = (
        UniqueConstraint('repository_id', 'service_name', name='uq_repo_service_name'),
        UniqueConstraint('container_id', name='uq_container_id'),  # 容器ID唯一性约束
        Index('idx_model_services_repo', 'repository_id'),
        Index('idx_model_services_user', 'user_id'),
        Index('idx_model_services_status', 'status'),
        Index('idx_model_services_image', 'image_id'),
        Index('idx_model_services_container', 'container_id'),
    )
    
    # 关系
    repository = relationship("Repository", back_populates="model_services")
    user = relationship("User", back_populates="model_services")
    image = relationship("Image", back_populates="services")
    logs = relationship("ServiceLog", back_populates="service", cascade="all, delete-orphan")
    health_checks = relationship("ServiceHealthCheck", back_populates="service", cascade="all, delete-orphan")


# ServiceInstance 表已删除 - 容器信息直接存储在 ModelService 中


class ServiceLog(Base):
    """服务日志表"""
    __tablename__ = "service_logs"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关系
    service_id = Column(Integer, ForeignKey("model_services.id", ondelete="CASCADE"), nullable=False)
    
    # 日志信息
    log_level = Column(String(20), nullable=False, comment="日志级别: info, warning, error, debug")
    message = Column(Text, nullable=False, comment="日志消息")
    event_type = Column(String(50), comment="事件类型: create, start, stop, access, error, health_check")
    
    # 上下文信息
    user_id = Column(Integer, ForeignKey("users.id"), comment="操作用户")
    ip_address = Column(INET, comment="操作IP")
    user_agent = Column(Text, comment="用户代理")
    
    # 元数据
    extra_data = Column(JSONB, comment="额外的日志数据")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 索引
    __table_args__ = (
        Index('idx_service_logs_service', 'service_id'),
        Index('idx_service_logs_user', 'user_id'),
        Index('idx_service_logs_event_type', 'event_type'),
        Index('idx_service_logs_created_at', 'created_at'),
    )
    
    # 关系
    service = relationship("ModelService", back_populates="logs")
    user = relationship("User")


class ServiceHealthCheck(Base):
    """服务健康监控表"""
    __tablename__ = "service_health_checks"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关系
    service_id = Column(Integer, ForeignKey("model_services.id", ondelete="CASCADE"), nullable=False)
    
    # 健康状态
    status = Column(String(50), nullable=False, comment="健康状态: healthy, unhealthy, unknown, timeout")
    response_time_ms = Column(Integer, comment="响应时间(ms)")
    
    # 检查详情
    check_type = Column(String(50), default="http", comment="检查类型: http, tcp, process")
    endpoint = Column(String(500), comment="检查端点")
    http_status_code = Column(Integer, comment="HTTP状态码")
    
    # 错误信息
    error_message = Column(Text, comment="错误信息")
    error_code = Column(String(50), comment="错误代码")
    
    # 时间戳
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), comment="检查时间")
    
    # 索引
    __table_args__ = (
        Index('idx_service_health_checks_service', 'service_id'),
        Index('idx_service_health_checks_status', 'status'),
        Index('idx_service_health_checks_checked_at', 'checked_at'),
    )
    
    # 关系
    service = relationship("ModelService", back_populates="health_checks")