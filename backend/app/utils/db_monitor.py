"""
数据库连接池监控工具
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import QueuePool
from app.database import engine

logger = logging.getLogger(__name__)


class DatabaseConnectionMonitor:
    """数据库连接监控器"""
    
    @staticmethod
    def get_pool_status(engine: AsyncEngine) -> Dict[str, Any]:
        """获取连接池状态"""
        pool = engine.pool
        
        if isinstance(pool, QueuePool):
            return {
                "pool_type": "QueuePool",
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "total_connections": pool.size() + pool.overflow(),
                "available_connections": pool.size() - pool.checkedout(),
            }
        else:
            return {
                "pool_type": type(pool).__name__,
                "size": getattr(pool, 'size', lambda: 'N/A')(),
                "checked_in": getattr(pool, 'checkedin', lambda: 'N/A')(),
                "checked_out": getattr(pool, 'checkedout', lambda: 'N/A')(),
            }
    
    @staticmethod
    def log_pool_status(engine: AsyncEngine, operation: str = ""):
        """记录连接池状态到日志"""
        try:
            status = DatabaseConnectionMonitor.get_pool_status(engine)
            logger.info(f"DB Pool Status{' - ' + operation if operation else ''}: {status}")
        except Exception as e:
            logger.warning(f"无法获取连接池状态: {e}")
    
    @staticmethod
    def check_pool_health(engine: AsyncEngine) -> bool:
        """检查连接池健康状态"""
        try:
            status = DatabaseConnectionMonitor.get_pool_status(engine)
            
            # 检查是否有连接泄漏的迹象
            if isinstance(engine.pool, QueuePool):
                checked_out = status.get('checked_out', 0)
                size = status.get('size', 0)
                overflow = status.get('overflow', 0)
                
                # 如果检出的连接数过多，可能存在泄漏
                if checked_out > size + overflow * 0.8:
                    logger.warning(f"可能存在连接泄漏: checked_out={checked_out}, size={size}, overflow={overflow}")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"检查连接池健康状态失败: {e}")
            return False


# 创建全局监控实例
db_monitor = DatabaseConnectionMonitor()


def log_db_operation(operation_name: str):
    """装饰器：记录数据库操作的连接池状态"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            db_monitor.log_pool_status(engine, f"before {operation_name}")
            try:
                result = await func(*args, **kwargs)
                db_monitor.log_pool_status(engine, f"after {operation_name}")
                return result
            except Exception as e:
                db_monitor.log_pool_status(engine, f"error in {operation_name}")
                raise
        return wrapper
    return decorator