"""
容器注册表和控制器健康状态模型
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class ContainerRegistry(Base):
    """容器注册表 - 记录容器在哪个mManager控制器"""
    __tablename__ = "container_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String(255), unique=True, index=True, nullable=False)
    service_id = Column(Integer, ForeignKey("model_services.id"), nullable=True)
    
    # mManager 控制器信息
    controller_id = Column(String(255), index=True, nullable=False)
    controller_url = Column(String(500), nullable=False)
    controller_type = Column(String(50), default='mmanager')  # 控制器类型
    
    # 容器基本信息
    container_name = Column(String(255), nullable=False)
    image_name = Column(String(500), nullable=False)
    status = Column(String(50), default='unknown')  # running, stopped, error, etc.
    
    # 服务器信息
    server_info = Column(JSON, default=lambda: {})  # 服务器类型、规格等
    
    # 资源分配信息
    resource_allocation = Column(JSON, default=lambda: {})  # CPU、内存等资源分配
    resource_usage = Column(JSON, default=lambda: {})  # 实时资源使用情况
    
    # 端口映射
    port_mappings = Column(JSON, default=lambda: {})
    host_port = Column(Integer, nullable=True)  # 主要端口
    container_port = Column(Integer, default=7860)  # 容器内端口
    
    # 网络信息
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    networks = Column(JSON, default=lambda: {})
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # 健康状态
    health_status = Column(String(50), default='unknown')  # healthy, unhealthy, checking
    last_health_check = Column(DateTime, nullable=True)
    
    # 关联关系
    service = relationship("ModelService", back_populates="container_registry")

class MManagerController(Base):
    """mManager 控制器注册表"""
    __tablename__ = "mmanager_controllers"
    
    id = Column(Integer, primary_key=True, index=True)
    controller_id = Column(String(255), unique=True, index=True, nullable=False)
    controller_url = Column(String(500), nullable=False)
    
    # 服务器信息
    server_type = Column(String(50), nullable=False)  # cpu, gpu, edge
    server_location = Column(String(255), nullable=True)  # 地理位置或机房
    
    # 状态信息
    status = Column(String(50), default='unknown')  # healthy, unhealthy, unreachable
    last_check_at = Column(DateTime, default=datetime.utcnow)
    
    # 健康数据
    health_data = Column(JSON, default=lambda: {})  # 控制器返回的健康检查数据
    error_message = Column(Text, nullable=True)
    
    # 统计信息
    consecutive_failures = Column(Integer, default=0)
    total_checks = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    
    # 容器统计
    current_containers = Column(Integer, default=0)
    max_containers = Column(Integer, default=100)
    
    # 资源信息
    cpu_cores = Column(Integer, nullable=True)
    memory_total_gb = Column(Float, nullable=True)
    memory_available_gb = Column(Float, nullable=True)
    disk_total_gb = Column(Float, nullable=True)
    disk_available_gb = Column(Float, nullable=True)
    
    # 服务器能力
    capabilities = Column(JSON, default=lambda: {})  # GPU、特殊硬件等能力
    
    # 负载信息
    load_percentage = Column(Float, default=0.0)  # 当前负载百分比
    
    # 优先级和权重
    priority = Column(Integer, default=100)  # 优先级，数值越小优先级越高
    weight = Column(Integer, default=100)   # 负载均衡权重
    
    # 启用状态
    enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContainerOperation(Base):
    """容器操作记录"""
    __tablename__ = "container_operations"
    
    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String(255), index=True)
    service_id = Column(Integer, ForeignKey("model_services.id"), nullable=True)
    controller_id = Column(String(255), index=True)
    
    # 操作信息
    operation_type = Column(String(50))  # create, start, stop, remove, migrate
    operation_status = Column(String(50))  # success, failed, in_progress
    
    # 操作详情
    operation_details = Column(JSON, default=lambda: {})
    error_message = Column(Text, nullable=True)
    
    # 时间信息
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # 用户信息
    user_id = Column(Integer, nullable=True)
    automated = Column(Boolean, default=False)  # 是否为自动化操作
    
    # 关联关系
    service = relationship("ModelService", foreign_keys=[service_id])

class ServiceDeploymentHistory(Base):
    """服务部署历史"""
    __tablename__ = "service_deployment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("model_services.id"), nullable=False)
    
    # 部署信息
    deployment_version = Column(String(50), nullable=False)
    controller_id = Column(String(255), nullable=False)
    container_id = Column(String(255), nullable=False)
    
    # 配置信息
    deployment_config = Column(JSON, default=lambda: {})  # 部署时的配置
    
    # 状态信息
    status = Column(String(50), nullable=False)  # deploying, deployed, failed, terminated
    
    # 时间信息
    deployed_at = Column(DateTime, default=datetime.utcnow)
    terminated_at = Column(DateTime, nullable=True)
    
    # 性能数据
    performance_metrics = Column(JSON, default=lambda: {})
    
    # 关联关系
    service = relationship("ModelService", foreign_keys=[service_id])