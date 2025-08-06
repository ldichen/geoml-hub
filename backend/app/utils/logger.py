"""
统一日志配置管理 - 解决日志重复输出问题
"""
import logging
import sys
from typing import Optional
from app.config import settings

# 全局标记，防止重复配置
_logging_configured = False

def setup_logging():
    """
    统一配置应用日志，防止重复输出
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # 清除所有现有的handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 设置根logger级别
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 创建控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 创建格式化器
    formatter = logging.Formatter(settings.log_format)
    console_handler.setFormatter(formatter)
    
    # 添加handler到根logger
    root_logger.addHandler(console_handler)
    
    # 设置特定logger的级别
    configure_specific_loggers()
    
    _logging_configured = True

def configure_specific_loggers():
    """配置特定模块的日志级别"""
    
    # Docker相关日志设为INFO级别，避免详细输出
    logging.getLogger("app.services.mmanager_client").setLevel(logging.INFO)
    
    # 设置第三方库日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # 对于需要详细调试的模块，保持INFO级别
    critical_modules = [
        "app.services.model_service",
        "app.routers.services", 
        "app.services.harbor_client"
    ]
    
    for module in critical_modules:
        logger = logging.getLogger(module)
        logger.setLevel(logging.INFO)
        # 防止向上传播到root logger，避免重复
        logger.propagate = True

def get_logger(name: str = __name__, level: Optional[str] = None) -> logging.Logger:
    """
    获取logger实例，确保不重复配置handler
    
    Args:
        name: Logger名称，通常是 __name__
        level: Log level (ignored, uses global config)
        
    Returns:
        配置好的logger实例
    """
    # 确保全局日志已配置
    setup_logging()
    
    # 直接返回logger，不添加额外handler
    return logging.getLogger(name)

def set_docker_operations_debug():
    """
    将Docker操作相关日志设置为DEBUG级别
    在需要详细调试时调用
    """
    docker_loggers = [
        "app.services.mmanager_client",
        "docker",
        "urllib3.connectionpool"
    ]
    
    for logger_name in docker_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

def set_docker_operations_quiet():
    """
    将Docker操作相关日志设置为WARNING级别，减少输出
    在正常运行时调用
    """
    docker_loggers = [
        "app.services.mmanager_client",
        "docker", 
        "urllib3.connectionpool"
    ]
    
    for logger_name in docker_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)

# 便捷的默认logger实例
logger = get_logger("app")