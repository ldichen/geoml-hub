"""
容器注册表和控制器健康状态模型
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

# ContainerRegistry 表已删除 - 容器信息直接存储在 ModelService 中

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

# ContainerOperation 和 ServiceDeploymentHistory 表已删除 - 操作记录通过 ServiceLog 处理