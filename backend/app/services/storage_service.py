"""
Author: DiChen
Date: 2025-10-06
Description: 存储统计服务 - 用户存储使用量的计算和更新
"""

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Repository, RepositoryFile
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StorageService:
    """存储统计服务"""

    @staticmethod
    async def calculate_user_storage(db: AsyncSession, user_id: int) -> int:
        """
        计算用户的实时存储使用量

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            存储使用量（字节）
        """
        try:
            storage_query = await db.execute(
                select(func.sum(RepositoryFile.file_size).label("total_storage"))
                .join(Repository, RepositoryFile.repository_id == Repository.id)
                .where(
                    and_(
                        Repository.owner_id == user_id,
                        Repository.is_active == True,
                        RepositoryFile.is_deleted == False
                    )
                )
            )
            storage_row = storage_query.first()
            return storage_row.total_storage or 0
        except Exception as e:
            logger.error(f"Failed to calculate storage for user {user_id}: {e}")
            return 0

    @staticmethod
    async def update_user_storage(db: AsyncSession, user_id: int) -> bool:
        """
        更新用户的存储使用量字段

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            是否更新成功
        """
        try:
            # 计算实时存储使用量
            real_storage = await StorageService.calculate_user_storage(db, user_id)

            # 更新用户的 storage_used 字段
            user_query = await db.execute(select(User).where(User.id == user_id))
            user = user_query.scalar_one_or_none()

            if user:
                user.storage_used = real_storage
                await db.commit()
                logger.info(f"Updated storage for user {user_id}: {real_storage} bytes")
                return True
            else:
                logger.warning(f"User {user_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to update storage for user {user_id}: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def sync_all_users_storage(db: AsyncSession) -> dict:
        """
        同步所有用户的存储使用量

        Args:
            db: 数据库会话

        Returns:
            同步结果统计
        """
        try:
            # 获取所有活跃用户
            users_query = await db.execute(
                select(User).where(User.is_active == True)
            )
            users = users_query.scalars().all()

            success_count = 0
            failed_count = 0
            total_storage = 0

            for user in users:
                try:
                    real_storage = await StorageService.calculate_user_storage(db, user.id)
                    user.storage_used = real_storage
                    total_storage += real_storage
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync storage for user {user.id}: {e}")
                    failed_count += 1

            # 提交所有更新
            await db.commit()

            result = {
                "total_users": len(users),
                "success_count": success_count,
                "failed_count": failed_count,
                "total_storage_bytes": total_storage,
            }

            logger.info(f"Storage sync completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to sync all users storage: {e}")
            await db.rollback()
            return {
                "total_users": 0,
                "success_count": 0,
                "failed_count": 0,
                "total_storage_bytes": 0,
                "error": str(e)
            }

    @staticmethod
    async def increment_user_storage(
        db: AsyncSession, user_id: int, size_delta: int
    ) -> bool:
        """
        增量更新用户存储使用量（用于文件上传）

        Args:
            db: 数据库会话
            user_id: 用户ID
            size_delta: 存储变化量（字节，可以为负数表示删除）

        Returns:
            是否更新成功
        """
        try:
            user_query = await db.execute(select(User).where(User.id == user_id))
            user = user_query.scalar_one_or_none()

            if user:
                user.storage_used = max(0, (user.storage_used or 0) + size_delta)
                await db.commit()
                logger.info(f"Incremented storage for user {user_id}: {size_delta:+d} bytes (total: {user.storage_used})")
                return True
            else:
                logger.warning(f"User {user_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to increment storage for user {user_id}: {e}")
            await db.rollback()
            return False


# 创建服务实例
storage_service = StorageService()
