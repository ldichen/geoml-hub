import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from sqlalchemy.orm import selectinload

from app.models.file_editor import (
    FileVersion, FileEditSession, FileEditPermission, FileTemplate, FileDraft,
    FileVersionType
)
from app.models.repository import RepositoryFile
from app.models.user import User
from app.services.minio_service import MinIOService


class FileVersionService:
    """文件版本控制服务"""
    
    def __init__(self, db: AsyncSession, minio_service: MinIOService):
        self.db = db
        self.minio_service = minio_service
    
    async def get_file_version_count(self, file_id: int) -> int:
        """获取文件版本总数"""
        from sqlalchemy import func
        
        query = select(func.count(FileVersion.id)).where(
            FileVersion.file_id == file_id
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_version_info(self, version_id: int) -> FileVersion:
        """获取版本信息"""
        query = select(FileVersion).where(FileVersion.id == version_id)
        result = await self.db.execute(query)
        version = result.scalar_one_or_none()
        
        if not version:
            raise ValueError(f"Version with id {version_id} not found")
        
        return version
    
    async def get_version_diff(self, old_version_id: int, new_version_id: int, include_content: bool = False) -> Dict[str, Any]:
        """获取版本差异"""
        old_version = await self.get_version_info(old_version_id)
        new_version = await self.get_version_info(new_version_id)
        
        diff_info = {
            "old_version_id": old_version_id,
            "new_version_id": new_version_id,
            "diff_summary": new_version.diff_summary or {}
        }
        
        if include_content:
            old_content = await self.get_version_content(old_version_id)
            new_content = await self.get_version_content(new_version_id)
            
            # 简单的差异显示，实际可以使用更复杂的diff算法
            diff_info["diff_content"] = f"--- Version {old_version.version_number}\n+++ Version {new_version.version_number}\n"
        
        return diff_info
    
    async def create_initial_version(
        self,
        file_id: int,
        author_id: int,
        content: str,
        mime_type: str = "text/plain",
        encoding: str = "utf-8"
    ) -> FileVersion:
        """创建文件的初始版本"""
        
        # 生成内容哈希
        content_hash = hashlib.sha256(content.encode(encoding)).hexdigest()
        
        # 生成版本哈希（基于文件ID和时间戳）
        version_hash = hashlib.sha256(f"{file_id}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8]
        
        # 获取文件信息
        file_query = select(RepositoryFile).where(RepositoryFile.id == file_id)
        file_result = await self.db.execute(file_query)
        file_obj = file_result.scalar_one_or_none()
        
        if not file_obj:
            raise ValueError(f"File with id {file_id} not found")
        
        # 存储到MinIO
        bucket_name = file_obj.minio_bucket
        object_key = f"versions/{file_id}/{version_hash}"
        
        await self.minio_service.upload_text(
            bucket_name=bucket_name,
            object_name=object_key,
            content=content,
            content_type=mime_type
        )
        
        # 创建版本记录
        file_version = FileVersion(
            file_id=file_id,
            version_number=1,
            version_hash=version_hash,
            version_type=FileVersionType.INITIAL,
            commit_message="Initial version",
            author_id=author_id,
            content_hash=content_hash,
            file_size=len(content.encode(encoding)),
            minio_bucket=bucket_name,
            minio_object_key=object_key,
            encoding=encoding,
            mime_type=mime_type
        )
        
        self.db.add(file_version)
        await self.db.commit()
        await self.db.refresh(file_version)
        
        return file_version
    
    async def create_new_version(
        self,
        file_id: int,
        author_id: int,
        content: str,
        commit_message: str,
        parent_version_id: Optional[int] = None,
        encoding: str = "utf-8"
    ) -> FileVersion:
        """创建新版本"""
        
        # 获取最新版本号
        latest_version_query = select(FileVersion).where(
            FileVersion.file_id == file_id
        ).order_by(desc(FileVersion.version_number)).limit(1)
        
        latest_result = await self.db.execute(latest_version_query)
        latest_version = latest_result.scalar_one_or_none()
        
        if not latest_version:
            raise ValueError("No initial version found. Create initial version first.")
        
        # 生成内容哈希
        content_hash = hashlib.sha256(content.encode(encoding)).hexdigest()
        
        # 检查内容是否有变化
        if content_hash == latest_version.content_hash:
            raise ValueError("No changes detected in file content")
        
        # 生成版本哈希
        version_hash = hashlib.sha256(f"{file_id}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8]
        
        # 获取文件信息
        file_query = select(RepositoryFile).where(RepositoryFile.id == file_id)
        file_result = await self.db.execute(file_query)
        file_obj = file_result.scalar_one_or_none()
        
        # 存储到MinIO
        bucket_name = file_obj.minio_bucket
        object_key = f"versions/{file_id}/{version_hash}"
        
        await self.minio_service.upload_text(
            bucket_name=bucket_name,
            object_name=object_key,
            content=content,
            content_type=latest_version.mime_type
        )
        
        # 计算差异摘要
        diff_summary = await self._calculate_diff_summary(
            latest_version.content_hash,
            content_hash,
            latest_version.minio_bucket,
            latest_version.minio_object_key,
            content
        )
        
        # 创建新版本记录
        file_version = FileVersion(
            file_id=file_id,
            version_number=latest_version.version_number + 1,
            version_hash=version_hash,
            version_type=FileVersionType.EDIT,
            commit_message=commit_message,
            author_id=author_id,
            content_hash=content_hash,
            file_size=len(content.encode(encoding)),
            minio_bucket=bucket_name,
            minio_object_key=object_key,
            parent_version_id=parent_version_id or latest_version.id,
            diff_summary=diff_summary,
            encoding=encoding,
            mime_type=latest_version.mime_type
        )
        
        self.db.add(file_version)
        await self.db.commit()
        await self.db.refresh(file_version)
        
        return file_version
    
    async def get_file_versions(
        self,
        file_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[FileVersion]:
        """获取文件版本历史"""
        
        query = select(FileVersion).where(
            FileVersion.file_id == file_id
        ).options(
            selectinload(FileVersion.author)
        ).order_by(desc(FileVersion.version_number)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_version_content(self, version_id: int) -> str:
        """获取指定版本的内容"""
        
        version_query = select(FileVersion).where(FileVersion.id == version_id)
        version_result = await self.db.execute(version_query)
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise ValueError(f"Version with id {version_id} not found")
        
        # 从MinIO获取内容
        content = await self.minio_service.get_text_content(
            bucket_name=version.minio_bucket,
            object_name=version.minio_object_key
        )
        
        return content
    
    async def _calculate_diff_summary(
        self,
        old_content_hash: str,
        new_content_hash: str,
        old_bucket: str,
        old_object_key: str,
        new_content: str
    ) -> Dict[str, int]:
        """计算差异摘要"""
        
        try:
            # 获取旧内容
            old_content = await self.minio_service.get_text_content(old_bucket, old_object_key)
            
            # 简单的行差异计算
            old_lines = old_content.splitlines()
            new_lines = new_content.splitlines()
            
            # 这里使用简单的逻辑，实际可以使用更复杂的diff算法
            lines_added = max(0, len(new_lines) - len(old_lines))
            lines_removed = max(0, len(old_lines) - len(new_lines))
            lines_changed = min(len(old_lines), len(new_lines))
            
            return {
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "lines_changed": lines_changed
            }
        except Exception:
            return {"lines_added": 0, "lines_removed": 0, "lines_changed": 0}


class FileEditSessionService:
    """文件编辑会话服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_edit_session(
        self,
        file_id: int,
        user_id: int,
        base_version_id: int,
        is_readonly: bool = False
    ) -> FileEditSession:
        """创建编辑会话"""
        
        # 检查是否已有活跃会话
        existing_query = select(FileEditSession).where(
            and_(
                FileEditSession.file_id == file_id,
                FileEditSession.user_id == user_id,
                FileEditSession.is_active == True
            )
        )
        
        existing_result = await self.db.execute(existing_query)
        existing_session = existing_result.scalar_one_or_none()
        
        if existing_session:
            # 更新现有会话
            existing_session.last_activity = datetime.utcnow()
            existing_session.expires_at = datetime.utcnow() + timedelta(hours=2)
            await self.db.commit()
            return existing_session
        
        # 创建新会话
        session_id = str(uuid.uuid4())
        session = FileEditSession(
            session_id=session_id,
            file_id=file_id,
            user_id=user_id,
            base_version_id=base_version_id,
            is_readonly=is_readonly,
            expires_at=datetime.utcnow() + timedelta(hours=2)
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def update_session_content(
        self,
        session_id: str,
        content: str,
        cursor_position: Optional[Dict] = None,
        selection_range: Optional[Dict] = None
    ) -> FileEditSession:
        """更新会话内容"""
        
        session_query = select(FileEditSession).where(
            FileEditSession.session_id == session_id
        )
        
        result = await self.db.execute(session_query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Edit session {session_id} not found")
        
        if not session.is_active:
            raise ValueError("Edit session is not active")
        
        # 更新会话
        session.current_content = content
        session.last_activity = datetime.utcnow()
        session.last_auto_save = datetime.utcnow()
        
        if cursor_position:
            session.cursor_position = cursor_position
        
        if selection_range:
            session.selection_range = selection_range
        
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def get_active_sessions(self, file_id: int) -> List[FileEditSession]:
        """获取文件的所有活跃编辑会话"""
        
        query = select(FileEditSession).where(
            and_(
                FileEditSession.file_id == file_id,
                FileEditSession.is_active == True,
                FileEditSession.expires_at > datetime.utcnow()
            )
        ).options(selectinload(FileEditSession.user))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def close_session(self, session_id: str) -> bool:
        """关闭编辑会话"""
        
        session_query = select(FileEditSession).where(
            FileEditSession.session_id == session_id
        )
        
        result = await self.db.execute(session_query)
        session = result.scalar_one_or_none()
        
        if not session:
            return False
        
        session.is_active = False
        await self.db.commit()
        
        return True


class FilePermissionService:
    """文件权限服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_file_permission(
        self,
        file_id: int,
        user_id: int,
        permission_type: str
    ) -> bool:
        """检查文件权限"""
        
        # 获取文件信息
        file_query = select(RepositoryFile).options(
            selectinload(RepositoryFile.repository)
        ).where(RepositoryFile.id == file_id)
        
        file_result = await self.db.execute(file_query)
        file_obj = file_result.scalar_one_or_none()
        
        if not file_obj:
            return False
        
        # 检查是否是仓库所有者
        if file_obj.repository.owner_id == user_id:
            return True
        
        # 检查公开仓库的读权限
        if file_obj.repository.visibility == "public" and permission_type == "read":
            return True
        
        # 检查显式权限
        permission_query = select(FileEditPermission).where(
            and_(
                FileEditPermission.file_id == file_id,
                FileEditPermission.user_id == user_id,
                or_(
                    FileEditPermission.expires_at.is_(None),
                    FileEditPermission.expires_at > datetime.utcnow()
                )
            )
        )
        
        permission_result = await self.db.execute(permission_query)
        permission = permission_result.scalar_one_or_none()
        
        if not permission:
            return False
        
        # 检查具体权限
        if permission_type == "read":
            return permission.can_read
        elif permission_type == "edit":
            return permission.can_edit
        elif permission_type == "commit":
            return permission.can_commit
        elif permission_type == "manage":
            return permission.can_manage
        
        return False
    
    async def grant_file_permission(
        self,
        file_id: int,
        user_id: int,
        granted_by: int,
        permissions: Dict[str, bool],
        expires_at: Optional[datetime] = None
    ) -> FileEditPermission:
        """授予文件权限"""
        
        # 检查是否已有权限记录
        existing_query = select(FileEditPermission).where(
            and_(
                FileEditPermission.file_id == file_id,
                FileEditPermission.user_id == user_id
            )
        )
        
        existing_result = await self.db.execute(existing_query)
        existing_permission = existing_result.scalar_one_or_none()
        
        if existing_permission:
            # 更新现有权限
            existing_permission.can_read = permissions.get("can_read", existing_permission.can_read)
            existing_permission.can_edit = permissions.get("can_edit", existing_permission.can_edit)
            existing_permission.can_commit = permissions.get("can_commit", existing_permission.can_commit)
            existing_permission.can_manage = permissions.get("can_manage", existing_permission.can_manage)
            existing_permission.granted_by = granted_by
            existing_permission.expires_at = expires_at
            existing_permission.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(existing_permission)
            return existing_permission
        
        # 创建新权限记录
        permission = FileEditPermission(
            file_id=file_id,
            user_id=user_id,
            can_read=permissions.get("can_read", True),
            can_edit=permissions.get("can_edit", False),
            can_commit=permissions.get("can_commit", False),
            can_manage=permissions.get("can_manage", False),
            permission_source="granted",
            granted_by=granted_by,
            expires_at=expires_at
        )
        
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        
        return permission


class FileTemplateService:
    """文件模板服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_templates(
        self,
        category: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[FileTemplate]:
        """获取文件模板列表"""
        query = select(FileTemplate).where(FileTemplate.is_active == True)
        
        if category:
            query = query.where(FileTemplate.category == category)
        
        if language:
            query = query.where(FileTemplate.language == language)
        
        query = query.order_by(desc(FileTemplate.usage_count)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_template(self, template_id: int) -> Optional[FileTemplate]:
        """获取模板详情"""
        query = select(FileTemplate).where(
            and_(
                FileTemplate.id == template_id,
                FileTemplate.is_active == True
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_template(
        self,
        name: str,
        description: str,
        template_content: str,
        category: str,
        language: str,
        file_extension: str,
        tags: Optional[List[str]] = None,
        author_id: Optional[int] = None
    ) -> FileTemplate:
        """创建文件模板"""
        template = FileTemplate(
            name=name,
            description=description,
            template_content=template_content,
            category=category,
            language=language,
            file_extension=file_extension,
            tags=tags or [],
            author_id=author_id
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        
        return template
    
    async def increment_usage(self, template_id: int) -> bool:
        """增加模板使用次数"""
        query = select(FileTemplate).where(FileTemplate.id == template_id)
        result = await self.db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            return False
        
        template.usage_count += 1
        await self.db.commit()
        
        return True


class FileDraftService:
    """文件草稿服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_draft(
        self,
        file_id: int,
        user_id: int,
        base_version_id: int,
        draft_content: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        cursor_position: Optional[Dict] = None,
        selection_range: Optional[Dict] = None
    ) -> FileDraft:
        """创建草稿"""
        
        # 检查是否已有草稿
        existing_query = select(FileDraft).where(
            and_(
                FileDraft.file_id == file_id,
                FileDraft.user_id == user_id
            )
        )
        
        existing_result = await self.db.execute(existing_query)
        existing_draft = existing_result.scalar_one_or_none()
        
        if existing_draft:
            # 更新现有草稿
            existing_draft.draft_content = draft_content
            existing_draft.base_version_id = base_version_id
            existing_draft.title = title
            existing_draft.description = description
            existing_draft.cursor_position = cursor_position
            existing_draft.selection_range = selection_range
            existing_draft.updated_at = datetime.utcnow()
            existing_draft.last_access = datetime.utcnow()
            existing_draft.auto_save_count += 1
            
            await self.db.commit()
            await self.db.refresh(existing_draft)
            return existing_draft
        
        # 创建新草稿
        draft = FileDraft(
            file_id=file_id,
            user_id=user_id,
            base_version_id=base_version_id,
            draft_content=draft_content,
            title=title,
            description=description,
            cursor_position=cursor_position,
            selection_range=selection_range,
            auto_save_count=1
        )
        
        self.db.add(draft)
        await self.db.commit()
        await self.db.refresh(draft)
        
        return draft
    
    async def get_draft(self, file_id: int, user_id: int) -> Optional[FileDraft]:
        """获取用户在指定文件的草稿"""
        
        query = select(FileDraft).where(
            and_(
                FileDraft.file_id == file_id,
                FileDraft.user_id == user_id
            )
        )
        
        result = await self.db.execute(query)
        draft = result.scalar_one_or_none()
        
        if draft:
            # 更新最后访问时间
            draft.last_access = datetime.utcnow()
            await self.db.commit()
        
        return draft
    
    async def get_user_drafts(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[FileDraft]:
        """获取用户的所有草稿"""
        
        query = select(FileDraft).where(
            FileDraft.user_id == user_id
        ).options(
            selectinload(FileDraft.file),
            selectinload(FileDraft.base_version)
        ).order_by(desc(FileDraft.updated_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_draft(
        self,
        draft_id: int,
        user_id: int,
        draft_content: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        cursor_position: Optional[Dict] = None,
        selection_range: Optional[Dict] = None
    ) -> FileDraft:
        """更新草稿"""
        
        query = select(FileDraft).where(
            and_(
                FileDraft.id == draft_id,
                FileDraft.user_id == user_id
            )
        )
        
        result = await self.db.execute(query)
        draft = result.scalar_one_or_none()
        
        if not draft:
            raise ValueError(f"Draft with id {draft_id} not found for user {user_id}")
        
        draft.draft_content = draft_content
        if title is not None:
            draft.title = title
        if description is not None:
            draft.description = description
        if cursor_position is not None:
            draft.cursor_position = cursor_position
        if selection_range is not None:
            draft.selection_range = selection_range
        
        draft.updated_at = datetime.utcnow()
        draft.last_access = datetime.utcnow()
        draft.auto_save_count += 1
        
        await self.db.commit()
        await self.db.refresh(draft)
        
        return draft
    
    async def delete_draft(self, draft_id: int, user_id: int) -> bool:
        """删除草稿"""
        
        query = select(FileDraft).where(
            and_(
                FileDraft.id == draft_id,
                FileDraft.user_id == user_id
            )
        )
        
        result = await self.db.execute(query)
        draft = result.scalar_one_or_none()
        
        if not draft:
            return False
        
        await self.db.delete(draft)
        await self.db.commit()
        
        return True
    
    async def get_draft_count(self, user_id: int) -> int:
        """获取用户草稿总数"""
        from sqlalchemy import func
        
        query = select(func.count(FileDraft.id)).where(
            FileDraft.user_id == user_id
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0