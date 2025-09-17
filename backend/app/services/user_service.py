from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any, List
from app.models import User, UserFollow, UserStorage, Repository
from app.schemas.user import UserCreate, UserUpdate
from app.middleware.error_response import NotFoundError, ConflictError
from fastapi import HTTPException


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """创建新用户"""
        # 检查外部用户ID是否已存在
        existing_query = select(User).where(
            or_(
                User.external_user_id == user_data.external_user_id,
                User.username == user_data.username,
                User.email == user_data.email,
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_user = existing_result.scalar_one_or_none()

        if existing_user:
            if getattr(existing_user, "external_user_id") == user_data.external_user_id:
                raise HTTPException(status_code=400, detail="外部用户ID已存在")
            elif getattr(existing_user, "username") == user_data.username:
                raise HTTPException(status_code=400, detail="用户名已存在")
            elif getattr(existing_user, "email") == user_data.email:
                raise HTTPException(status_code=400, detail="邮箱已存在")

        # 创建新用户
        db_user = User(
            external_user_id=user_data.external_user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            avatar_url=user_data.avatar_url,
            bio=user_data.bio,
            website=user_data.website,
            location=user_data.location,
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        # 创建用户存储记录
        user_storage = UserStorage(user_id=db_user.id)
        self.db.add(user_storage)
        await self.db.commit()

        return db_user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        query = select(User).where(
            and_(User.username == username, User.is_active == True)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_external_id(self, external_user_id: str) -> Optional[User]:
        """根据外部用户ID获取用户"""
        query = select(User).where(
            and_(User.external_user_id == external_user_id, User.is_active == True)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_user(
        self, user_identifier: str, user_data: Dict[str, Any]
    ) -> User:
        """更新用户信息 - 支持通过username或user_id更新"""
        # 尝试通过不同方式查找用户
        if user_identifier.isdigit():
            query = select(User).where(User.id == int(user_identifier))
        else:
            query = select(User).where(User.username == user_identifier)

        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("用户不存在")

        # 更新字段
        for field, value in user_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user_by_username(
        self, username: str, user_data: UserUpdate
    ) -> User:
        """通过用户名更新用户信息（保持向后兼容）"""
        user = await self.get_user_by_username(username)
        if not user:
            raise NotFoundError("用户不存在")

        # 更新字段
        update_data = {}
        if user_data.full_name is not None:
            update_data["full_name"] = user_data.full_name
        if user_data.avatar_url is not None:
            update_data["avatar_url"] = user_data.avatar_url
        if user_data.bio is not None:
            update_data["bio"] = user_data.bio
        if user_data.website is not None:
            update_data["website"] = user_data.website
        if user_data.location is not None:
            update_data["location"] = user_data.location

        return await self.update_user(str(user.id), update_data)

    async def follow_user(self, current_user_id: int, target_username: str) -> None:
        """关注用户"""
        # 获取目标用户
        target_user = await self.get_user_by_username(target_username)
        if not target_user:
            raise HTTPException(status_code=404, detail="目标用户不存在")

        if current_user_id == target_user.id:
            raise HTTPException(status_code=400, detail="不能关注自己")

        # 检查是否已经关注
        existing_query = select(UserFollow).where(
            and_(
                UserFollow.follower_id == current_user_id,
                UserFollow.following_id == target_user.id,
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_follow = existing_result.scalar_one_or_none()

        if existing_follow:
            raise HTTPException(status_code=400, detail="已经关注该用户")

        # 创建关注关系
        follow = UserFollow(follower_id=current_user_id, following_id=target_user.id)
        self.db.add(follow)

        # 更新统计计数
        # 更新关注者的following_count
        current_user_query = select(User).where(User.id == current_user_id)
        current_user_result = await self.db.execute(current_user_query)
        current_user = current_user_result.scalar_one()
        setattr(
            current_user,
            "following_count",
            getattr(current_user, "following_count") + 1,
        )

        # 更新被关注者的followers_count
        setattr(
            target_user, "followers_count", getattr(target_user, "followers_count") + 1
        )

        await self.db.commit()

    async def unfollow_user(self, current_user_id: int, target_username: str) -> None:
        """取消关注用户"""
        target_user = await self.get_user_by_username(target_username)
        if not target_user:
            raise HTTPException(status_code=404, detail="目标用户不存在")

        # 查找关注关系
        follow_query = select(UserFollow).where(
            and_(
                UserFollow.follower_id == current_user_id,
                UserFollow.following_id == target_user.id,
            )
        )
        follow_result = await self.db.execute(follow_query)
        follow = follow_result.scalar_one_or_none()

        if not follow:
            raise HTTPException(status_code=400, detail="未关注该用户")

        # 删除关注关系
        from sqlalchemy import delete

        delete_stmt = delete(UserFollow).where(
            and_(
                UserFollow.follower_id == current_user_id,
                UserFollow.following_id == target_user.id,
            )
        )
        await self.db.execute(delete_stmt)

        # 更新统计计数
        current_user_query = select(User).where(User.id == current_user_id)
        current_user_result = await self.db.execute(current_user_query)
        current_user = current_user_result.scalar_one()
        setattr(
            current_user,
            "following_count",
            max(0, getattr(current_user, "following_count") - 1),
        )

        setattr(
            target_user,
            "followers_count",
            max(0, getattr(target_user, "followers_count") - 1),
        )

        await self.db.commit()

    async def get_user_stats(self, username: str) -> Dict[str, Any]:
        """获取用户统计信息"""
        user = await self.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 获取仓库统计
        repo_stats_query = select(
            func.count(Repository.id).label("total_repos"),
            func.sum(Repository.stars_count).label("total_stars"),
            func.sum(Repository.downloads_count).label("total_downloads"),
            func.sum(Repository.views_count).label("total_views"),
        ).where(and_(Repository.owner_id == user.id, Repository.is_active == True))

        repo_stats_result = await self.db.execute(repo_stats_query)
        repo_stats = repo_stats_result.first()

        # 获取存储统计
        storage_query = select(UserStorage).where(UserStorage.user_id == user.id)
        storage_result = await self.db.execute(storage_query)
        storage = storage_result.scalar_one_or_none()

        return {
            "user_id": user.id,
            "username": user.username,
            "followers_count": user.followers_count,
            "following_count": user.following_count,
            "repositories": {
                "total": getattr(repo_stats, "total_repos", 0) or 0,
                "total_stars": getattr(repo_stats, "total_stars", 0) or 0,
                "total_downloads": getattr(repo_stats, "total_downloads", 0) or 0,
                "total_views": getattr(repo_stats, "total_views", 0) or 0,
            },
            "storage": {
                "total_files": storage.total_files if storage else 0,
                "total_size": storage.total_size if storage else 0,
                "quota": user.storage_quota,
                "used": user.storage_used,
            },
        }

    async def update_storage_stats(self, user_id: int) -> None:
        """更新用户存储统计"""
        # 计算用户所有仓库的文件总数和总大小
        repo_query = select(Repository.id).where(
            and_(Repository.owner_id == user_id, Repository.is_active == True)
        )
        repo_result = await self.db.execute(repo_query)
        repo_ids = [row[0] for row in repo_result.fetchall()]

        if not repo_ids:
            return

        # 计算总的文件统计
        from app.models import RepositoryFile

        file_stats_query = select(
            func.count(RepositoryFile.id).label("total_files"),
            func.sum(RepositoryFile.file_size).label("total_size"),
        ).where(
            and_(
                RepositoryFile.repository_id.in_(repo_ids),
                RepositoryFile.is_deleted == False,
            )
        )

        file_stats_result = await self.db.execute(file_stats_query)
        file_stats = file_stats_result.first()

        # 更新用户的存储使用量
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one()

        setattr(user, "storage_used", getattr(file_stats, "total_size", 0) or 0)

        # 更新或创建存储统计记录
        storage_query = select(UserStorage).where(UserStorage.user_id == user_id)
        storage_result = await self.db.execute(storage_query)
        storage = storage_result.scalar_one_or_none()

        if storage:
            setattr(storage, "total_files", getattr(file_stats, "total_files", 0) or 0)
            setattr(storage, "total_size", getattr(file_stats, "total_size", 0) or 0)
        else:
            storage = UserStorage(
                user_id=user_id,
                total_files=getattr(file_stats, "total_files", 0) or 0,
                total_size=getattr(file_stats, "total_size", 0) or 0,
            )
            self.db.add(storage)

        await self.db.commit()
