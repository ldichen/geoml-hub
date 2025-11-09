"""
Author: DiChen
Date: 2025-08-06 02:06:03
LastEditors: DiChen
LastEditTime: 2025-11-06 21:38:59
"""

"""
Author: DiChen
Date: 2025-08-02 03:16:01
LastEditors: DiChen
LastEditTime: 2025-08-04 12:31:54
"""

"""
mManager 配置文件
"""

import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """mManager 配置"""

    # API 配置
    api_key: str = os.getenv("MMANAGER_API_KEY", "mmanager-default-key")
    host: str = "0.0.0.0"
    port: int = 8001

    # Docker 配置
    docker_host: str = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
    docker_timeout: int = 60

    # 服务器信息
    server_id: str = os.getenv("SERVER_ID", "mmanager-local-01")
    server_type: str = os.getenv("SERVER_TYPE", "cpu")  # cpu, gpu, edge
    max_containers: int = int(os.getenv("MAX_CONTAINERS", "100"))

    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "/tmp/logs/mmanager.log")

    # 监控配置
    metrics_enabled: bool = True
    health_check_interval: int = 30

    # 容器默认配置
    default_memory_limit: str = "512m"
    default_cpu_limit: float = 1.0
    default_restart_policy: str = "unless-stopped"

    # 网络配置
    default_network: str = ""  # 空字符串表示使用默认网络模式
    allowed_origins: List[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")

    # 存储配置
    data_dir: str = "/app/data"
    temp_dir: str = "/tmp/mmanager"

    # 服务发现配置
    consul_enabled: bool = False
    consul_host: str = "localhost"
    consul_port: int = 8500

    class Config:
        env_file = ".env"


# 全局配置实例
settings = Settings()

# 服务器能力配置
SERVER_CAPABILITIES = {
    "cpu": {
        "max_cpu_cores": 16,
        "max_memory_gb": 32,
        "gpu_support": False,
        "features": ["basic_compute", "file_processing"],
    },
    "gpu": {
        "max_cpu_cores": 32,
        "max_memory_gb": 64,
        "gpu_support": True,
        "gpu_count": 4,
        "features": ["ml_training", "inference", "cuda_compute"],
    },
    "edge": {
        "max_cpu_cores": 4,
        "max_memory_gb": 8,
        "gpu_support": False,
        "features": ["edge_inference", "iot_processing"],
    },
}


def get_server_capabilities() -> Dict[str, Any]:
    """获取当前服务器能力配置"""
    return SERVER_CAPABILITIES.get(settings.server_type, SERVER_CAPABILITIES["cpu"])
