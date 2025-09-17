from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from typing import Dict, Any, Optional, List
from app.models import Snapshot, Branch, Release, SnapshotFile, Repository, User
from app.services.file_upload_service import FileUploadService
from app.middleware.error_response import NotFoundError, DataValidationError, PermissionError
import hashlib
import secrets
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class VersionControlService:
    """版本控制服务：管理快照、分支和发布版本"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_upload_service = FileUploadService(db)

    def _generate_snapshot_id(self) -> str:
        """生成唯一的快照ID (12位短hash)"""
        return secrets.token_hex(6)

    def _generate_storage_path(self, username: str, repo_name: str, snapshot_id: str) -> str:
        """生成版本控制存储路径"""
        return f"users/{username}/repositories/{repo_name}/snapshots/{snapshot_id}"

    async def create_snapshot(
        self,
        repository_id: int,
        author_id: int,
        message: str,
        branch: str = "main",
        file_uploads: Optional[List[Dict[str, Any]]] = None,
        parent_snapshot_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建快照"""

        # 获取仓库信息
        repo_query = select(Repository).where(Repository.id == repository_id)
        repo_result = await self.db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()

        if not repository:
            raise NotFoundError("仓库不存在")

        # 获取用户信息
        user_query = select(User).where(User.id == author_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise NotFoundError("用户不存在")

        # 生成快照ID
        snapshot_id = self._generate_snapshot_id()

        # 确保快照ID唯一
        while True:
            existing_query = select(Snapshot).where(Snapshot.id == snapshot_id)
            existing_result = await self.db.execute(existing_query)
            if not existing_result.scalar_one_or_none():
                break
            snapshot_id = self._generate_snapshot_id()

        # 生成存储路径
        storage_path = self._generate_storage_path(user.username, repository.name, snapshot_id)

        # 创建快照记录
        snapshot = Snapshot(
            id=snapshot_id,
            repository_id=repository_id,
            message=message,
            author_id=author_id,
            branch=branch,
            parent_snapshot_id=parent_snapshot_id,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(snapshot)

        # 处理文件上传
        snapshot_files = []
        if file_uploads:
            for file_info in file_uploads:
                # 使用FileUploadService处理文件上传，指定自定义存储路径
                upload_result = await self.file_upload_service.initiate_upload_session(
                    repository_id=repository_id,
                    file_name=file_info["file_name"],
                    file_size=file_info["file_size"],
                    file_path=file_info["file_path"],
                    content_type=file_info.get("content_type"),
                    user_id=author_id,
                    custom_storage_path=storage_path,
                )

                # 创建快照文件记录
                snapshot_file = SnapshotFile(
                    snapshot_id=snapshot_id,
                    file_path=file_info["file_path"],
                    storage_path=f"{storage_path}/{file_info['file_path']}",
                    file_size=file_info["file_size"],
                    content_type=file_info.get("content_type"),
                )

                # 如果有文件内容，计算hash
                if "content" in file_info:
                    content_hash = hashlib.sha256(file_info["content"].encode()).hexdigest()
                    snapshot_file.file_hash = content_hash

                self.db.add(snapshot_file)
                snapshot_files.append(snapshot_file)

        # 更新分支头指针
        await self._update_branch_head(repository_id, branch, snapshot_id)

        # 更新仓库统计信息
        repository.total_commits += 1
        repository.last_commit_message = message
        repository.last_commit_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(snapshot)

        logger.info(f"Created snapshot {snapshot_id} for repository {repository_id}")

        return {
            "snapshot_id": snapshot_id,
            "repository_id": repository_id,
            "message": message,
            "branch": branch,
            "author": {"id": user.id, "username": user.username},
            "created_at": snapshot.created_at.isoformat(),
            "storage_path": storage_path,
            "files": [
                {
                    "file_path": sf.file_path,
                    "storage_path": sf.storage_path,
                    "file_size": sf.file_size,
                    "content_type": sf.content_type,
                    "file_hash": sf.file_hash,
                }
                for sf in snapshot_files
            ],
        }

    async def _update_branch_head(self, repository_id: int, branch_name: str, snapshot_id: str):
        """更新分支头指针"""
        branch_query = select(Branch).where(
            and_(
                Branch.repository_id == repository_id,
                Branch.name == branch_name,
            )
        )
        branch_result = await self.db.execute(branch_query)
        branch = branch_result.scalar_one_or_none()

        if not branch:
            # 创建新分支
            branch = Branch(
                repository_id=repository_id,
                name=branch_name,
                head_snapshot_id=snapshot_id,
                is_default=(branch_name == "main"),
            )
            self.db.add(branch)
        else:
            # 更新现有分支
            branch.head_snapshot_id = snapshot_id

    async def create_branch(
        self, repository_id: int, name: str, source_branch: str = "main"
    ) -> Dict[str, Any]:
        """创建分支"""

        # 检查分支名是否已存在
        existing_query = select(Branch).where(
            and_(
                Branch.repository_id == repository_id,
                Branch.name == name,
            )
        )
        existing_result = await self.db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise DataValidationError(f"分支 '{name}' 已存在")

        # 获取源分支
        source_query = select(Branch).where(
            and_(
                Branch.repository_id == repository_id,
                Branch.name == source_branch,
            )
        )
        source_result = await self.db.execute(source_query)
        source_branch_obj = source_result.scalar_one_or_none()

        if not source_branch_obj:
            raise NotFoundError(f"源分支 '{source_branch}' 不存在")

        # 创建新分支
        new_branch = Branch(
            repository_id=repository_id,
            name=name,
            head_snapshot_id=source_branch_obj.head_snapshot_id,
            is_default=False,
        )

        self.db.add(new_branch)
        await self.db.commit()
        await self.db.refresh(new_branch)

        logger.info(f"Created branch '{name}' from '{source_branch}' for repository {repository_id}")

        return {
            "id": new_branch.id,
            "name": new_branch.name,
            "repository_id": new_branch.repository_id,
            "head_snapshot_id": new_branch.head_snapshot_id,
            "is_default": new_branch.is_default,
            "created_at": new_branch.created_at.isoformat(),
        }

    async def create_release(
        self,
        repository_id: int,
        tag_name: str,
        snapshot_id: str,
        title: str,
        description: Optional[str] = None,
        is_prerelease: bool = False,
    ) -> Dict[str, Any]:
        """创建发布版本"""

        # 检查标签名是否已存在
        existing_query = select(Release).where(
            and_(
                Release.repository_id == repository_id,
                Release.tag_name == tag_name,
            )
        )
        existing_result = await self.db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise DataValidationError(f"标签 '{tag_name}' 已存在")

        # 检查快照是否存在
        snapshot_query = select(Snapshot).where(
            and_(
                Snapshot.id == snapshot_id,
                Snapshot.repository_id == repository_id,
            )
        )
        snapshot_result = await self.db.execute(snapshot_query)
        if not snapshot_result.scalar_one_or_none():
            raise NotFoundError("快照不存在")

        # 创建发布版本
        release = Release(
            repository_id=repository_id,
            tag_name=tag_name,
            snapshot_id=snapshot_id,
            title=title,
            description=description,
            is_prerelease=is_prerelease,
        )

        self.db.add(release)
        await self.db.commit()
        await self.db.refresh(release)

        logger.info(f"Created release '{tag_name}' for repository {repository_id}")

        return {
            "id": release.id,
            "tag_name": release.tag_name,
            "repository_id": release.repository_id,
            "snapshot_id": release.snapshot_id,
            "title": release.title,
            "description": release.description,
            "is_prerelease": release.is_prerelease,
            "download_count": release.download_count,
            "created_at": release.created_at.isoformat(),
        }

    async def get_snapshots(
        self,
        repository_id: int,
        branch: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """获取快照列表"""

        query = select(Snapshot).where(Snapshot.repository_id == repository_id)

        if branch:
            query = query.where(Snapshot.branch == branch)

        query = query.order_by(desc(Snapshot.created_at))

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        snapshots = result.scalars().all()

        # 获取总数
        count_query = select(func.count(Snapshot.id)).where(Snapshot.repository_id == repository_id)
        if branch:
            count_query = count_query.where(Snapshot.branch == branch)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return {
            "snapshots": [
                {
                    "id": s.id,
                    "message": s.message,
                    "branch": s.branch,
                    "author_id": s.author_id,
                    "parent_snapshot_id": s.parent_snapshot_id,
                    "created_at": s.created_at.isoformat(),
                }
                for s in snapshots
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def get_branches(self, repository_id: int) -> Dict[str, Any]:
        """获取分支列表"""

        query = select(Branch).where(Branch.repository_id == repository_id)
        result = await self.db.execute(query)
        branches = result.scalars().all()

        return {
            "branches": [
                {
                    "id": b.id,
                    "name": b.name,
                    "head_snapshot_id": b.head_snapshot_id,
                    "is_default": b.is_default,
                    "created_at": b.created_at.isoformat(),
                }
                for b in branches
            ],
            "total": len(branches),
        }

    async def get_releases(
        self, repository_id: int, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """获取发布版本列表"""

        query = select(Release).where(Release.repository_id == repository_id)
        query = query.order_by(desc(Release.created_at))

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        releases = result.scalars().all()

        # 获取总数
        count_query = select(func.count(Release.id)).where(Release.repository_id == repository_id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return {
            "releases": [
                {
                    "id": r.id,
                    "tag_name": r.tag_name,
                    "snapshot_id": r.snapshot_id,
                    "title": r.title,
                    "description": r.description,
                    "is_prerelease": r.is_prerelease,
                    "download_count": r.download_count,
                    "created_at": r.created_at.isoformat(),
                }
                for r in releases
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def compare_snapshots(
        self, repository_id: int, base_snapshot_id: str, compare_snapshot_id: str
    ) -> Dict[str, Any]:
        """比较两个快照"""

        # 获取两个快照的文件列表
        base_files_query = select(SnapshotFile).where(SnapshotFile.snapshot_id == base_snapshot_id)
        base_files_result = await self.db.execute(base_files_query)
        base_files = {f.file_path: f for f in base_files_result.scalars().all()}

        compare_files_query = select(SnapshotFile).where(SnapshotFile.snapshot_id == compare_snapshot_id)
        compare_files_result = await self.db.execute(compare_files_query)
        compare_files = {f.file_path: f for f in compare_files_result.scalars().all()}

        changes = []
        stats = {"added": 0, "modified": 0, "deleted": 0}

        # 检查新增和修改的文件
        for file_path, compare_file in compare_files.items():
            if file_path not in base_files:
                # 新增文件
                changes.append({
                    "file_path": file_path,
                    "change_type": "added",
                    "new_size": compare_file.file_size,
                    "new_hash": compare_file.file_hash,
                })
                stats["added"] += 1
            elif base_files[file_path].file_hash != compare_file.file_hash:
                # 修改文件
                changes.append({
                    "file_path": file_path,
                    "change_type": "modified",
                    "old_size": base_files[file_path].file_size,
                    "new_size": compare_file.file_size,
                    "old_hash": base_files[file_path].file_hash,
                    "new_hash": compare_file.file_hash,
                })
                stats["modified"] += 1

        # 检查删除的文件
        for file_path, base_file in base_files.items():
            if file_path not in compare_files:
                changes.append({
                    "file_path": file_path,
                    "change_type": "deleted",
                    "old_size": base_file.file_size,
                    "old_hash": base_file.file_hash,
                })
                stats["deleted"] += 1

        return {
            "base_snapshot_id": base_snapshot_id,
            "compare_snapshot_id": compare_snapshot_id,
            "changes": changes,
            "stats": stats,
        }

    async def rollback_to_snapshot(
        self,
        repository_id: int,
        target_snapshot_id: str,
        branch: str,
        author_id: int,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """回滚到指定快照"""

        # 检查目标快照是否存在
        target_query = select(Snapshot).where(
            and_(
                Snapshot.id == target_snapshot_id,
                Snapshot.repository_id == repository_id,
            )
        )
        target_result = await self.db.execute(target_query)
        target_snapshot = target_result.scalar_one_or_none()

        if not target_snapshot:
            raise NotFoundError("目标快照不存在")

        # 获取目标快照的文件列表
        files_query = select(SnapshotFile).where(SnapshotFile.snapshot_id == target_snapshot_id)
        files_result = await self.db.execute(files_query)
        target_files = files_result.scalars().all()

        # 创建新快照作为回滚结果
        rollback_message = message or f"回滚到 {target_snapshot_id[:8]}"

        file_uploads = [
            {
                "file_path": f.file_path,
                "file_size": f.file_size,
                "content_type": f.content_type,
                "file_name": f.file_path.split("/")[-1],
            }
            for f in target_files
        ]

        # 获取当前分支头快照作为父快照
        branch_query = select(Branch).where(
            and_(
                Branch.repository_id == repository_id,
                Branch.name == branch,
            )
        )
        branch_result = await self.db.execute(branch_query)
        current_branch = branch_result.scalar_one_or_none()
        parent_snapshot_id = current_branch.head_snapshot_id if current_branch else None

        return await self.create_snapshot(
            repository_id=repository_id,
            author_id=author_id,
            message=rollback_message,
            branch=branch,
            file_uploads=file_uploads,
            parent_snapshot_id=parent_snapshot_id,
        )