"""
容器相关数据模型
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import re

class ContainerStatus(str, Enum):
    """容器状态枚举"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"

class RestartPolicy(str, Enum):
    """重启策略枚举"""
    NO = "no"
    ALWAYS = "always"
    UNLESS_STOPPED = "unless-stopped"
    ON_FAILURE = "on-failure"

class ContainerCreateRequest(BaseModel):
    """创建容器请求"""
    name: str = Field(..., pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', description="容器名称")
    image: str = Field(..., description="Docker镜像")
    command: Optional[str] = Field(None, description="启动命令")
    working_dir: Optional[str] = Field("/app", description="工作目录")
    
    # 环境变量
    environment: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    
    # 端口映射
    ports: Dict[str, int] = Field(default_factory=dict, description="端口映射 {'container_port/tcp': host_port}")
    
    # 卷挂载
    volumes: Dict[str, str] = Field(default_factory=dict, description="卷挂载 {'host_path': 'container_path'}")
    
    # 资源限制
    memory_limit: str = Field("512m", description="内存限制")
    cpu_limit: float = Field(1.0, description="CPU限制")
    
    # 重启策略
    restart_policy: RestartPolicy = Field(RestartPolicy.UNLESS_STOPPED, description="重启策略")
    
    # 网络配置
    network_mode: Optional[str] = Field(None, description="网络模式")
    networks: List[str] = Field(default_factory=list, description="加入的网络")
    
    # 标签
    labels: Dict[str, str] = Field(default_factory=dict, description="容器标签")
    
    # 其他配置
    auto_remove: bool = Field(False, description="退出时自动删除")
    detach: bool = Field(True, description="后台运行")
    
    @validator('memory_limit')
    def validate_memory_limit(cls, v):
        """验证内存限制格式和范围"""
        pattern = r'^(\d+)(b|k|m|g|kb|mb|gb|K|M|G|KB|MB|GB)$'
        if not re.match(pattern, v):
            raise ValueError('内存限制格式错误，应为如：512m, 2g, 1024M')
        
        # 转换为MB进行范围检查
        value = int(re.match(pattern, v).group(1))
        unit = re.match(pattern, v).group(2).lower()
        
        multipliers = {'b': 1/(1024*1024), 'k': 1/1024, 'kb': 1/1024, 'm': 1, 'mb': 1, 'g': 1024, 'gb': 1024}
        memory_mb = value * multipliers.get(unit, 1)
        
        if memory_mb < 128:  # 最小128MB
            raise ValueError('内存限制不能小于128MB')
        if memory_mb > 32768:  # 最大32GB
            raise ValueError('内存限制不能超过32GB')
        
        return v
    
    @validator('cpu_limit')
    def validate_cpu_limit(cls, v):
        """验证CPU限制范围"""
        if v <= 0 or v > 64:  # 假设最大64核
            raise ValueError('CPU限制应在0.1-64之间')
        return v
    
    @validator('ports')
    def validate_ports(cls, v):
        """验证端口映射"""
        for container_port, host_port in v.items():
            # 验证主机端口范围
            if not (1024 <= host_port <= 65535):
                raise ValueError(f'主机端口 {host_port} 应在1024-65535范围内')
        return v

class ContainerInfo(BaseModel):
    """容器信息"""
    id: str = Field(..., description="容器ID")
    name: str = Field(..., description="容器名称")
    image: str = Field(..., description="镜像名称")
    status: ContainerStatus = Field(..., description="容器状态")
    
    # 时间信息
    created_at: str = Field(..., description="创建时间")
    started_at: Optional[str] = Field(None, description="启动时间")
    finished_at: Optional[str] = Field(None, description="结束时间")
    
    # 网络信息
    ports: Dict[str, int] = Field(default_factory=dict, description="端口映射")
    networks: Dict[str, Any] = Field(default_factory=dict, description="网络配置")
    ip_address: Optional[str] = Field(None, description="IP地址")
    
    # 资源信息
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="资源限制")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="资源使用情况")
    
    # 其他信息
    labels: Dict[str, str] = Field(default_factory=dict, description="标签")
    environment: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    mounts: List[Dict[str, Any]] = Field(default_factory=list, description="挂载点")

class ContainerStatsResponse(BaseModel):
    """容器统计信息"""
    container_id: str = Field(..., description="容器ID")
    
    # CPU 统计
    cpu_percent: float = Field(0.0, description="CPU使用百分比")
    cpu_usage: Dict[str, Any] = Field(default_factory=dict, description="CPU详细使用情况")
    
    # 内存统计
    memory_usage_mb: float = Field(0.0, description="内存使用量(MB)")
    memory_limit_mb: float = Field(0.0, description="内存限制(MB)")
    memory_percent: float = Field(0.0, description="内存使用百分比")
    
    # 网络统计
    network_rx_bytes: int = Field(0, description="网络接收字节数")
    network_tx_bytes: int = Field(0, description="网络发送字节数")
    
    # 块IO统计
    block_read_bytes: int = Field(0, description="磁盘读取字节数")
    block_write_bytes: int = Field(0, description="磁盘写入字节数")
    
    # 进程数
    pids: int = Field(0, description="进程数")
    
    # 时间戳
    timestamp: str = Field(..., description="统计时间")

class ContainerLogsResponse(BaseModel):
    """容器日志响应"""
    container_id: str = Field(..., description="容器ID")
    logs: str = Field(..., description="日志内容")
    lines: int = Field(..., description="日志行数")
    timestamp: str = Field(..., description="获取时间")

class ContainerListResponse(BaseModel):
    """容器列表响应"""
    containers: List[ContainerInfo] = Field(..., description="容器列表")
    total: int = Field(..., description="总数量")
    running: int = Field(..., description="运行中的容器数")
    stopped: int = Field(..., description="已停止的容器数")

class ContainerOperationResponse(BaseModel):
    """容器操作响应"""
    success: bool = Field(..., description="操作是否成功")
    container_id: str = Field(..., description="容器ID")
    message: str = Field(..., description="响应消息")
    operation: str = Field(..., description="操作类型")
    timestamp: str = Field(..., description="操作时间")
    details: Optional[Dict[str, Any]] = Field(None, description="操作详情")

class ImageInfo(BaseModel):
    """镜像信息"""
    id: str = Field(..., description="镜像ID")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    size: int = Field(..., description="镜像大小(字节)")
    created: str = Field(..., description="创建时间")
    
class SystemInfo(BaseModel):
    """系统信息"""
    docker_version: str = Field(..., description="Docker版本")
    containers_total: int = Field(..., description="容器总数")
    containers_running: int = Field(..., description="运行中容器数")
    containers_stopped: int = Field(..., description="停止的容器数")
    images_total: int = Field(..., description="镜像总数")
    cpu_cores: int = Field(..., description="CPU核心数")
    memory_total_gb: float = Field(..., description="总内存(GB)")
    memory_available_gb: float = Field(..., description="可用内存(GB)")
    disk_usage: Dict[str, Any] = Field(default_factory=dict, description="磁盘使用情况")