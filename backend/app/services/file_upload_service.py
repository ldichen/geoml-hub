from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Dict, Any, Optional, List
from app.models import FileUploadSession, RepositoryFile, Repository
from app.services.minio_service import minio_service
from app.config import settings
from app.middleware.error_response import NotFoundError, DataValidationError
import hashlib
import time
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class FileUploadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def initiate_upload_session(
        self,
        repository_id: int,
        file_name: str,
        file_size: int,
        file_path: str,
        content_type: Optional[str] = None,
        user_id: Optional[int] = None,
        custom_storage_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """初始化文件上传会话"""

        # 检查文件大小限制
        max_size = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            raise DataValidationError(f"文件大小超过限制 {settings.max_file_size_mb}MB")

        # 生成对象键 - 支持自定义存储路径或使用默认路径
        if custom_storage_path:
            object_key = f"{custom_storage_path}/{file_path}"
        else:
            # 保持向后兼容性的默认路径
            timestamp = int(time.time())
            object_key = f"repositories/{repository_id}/{timestamp}_{file_name}"

        # 计算分片数量
        chunk_size = settings.chunk_size_mb * 1024 * 1024
        total_chunks = (file_size + chunk_size - 1) // chunk_size

        # 如果文件较小，使用直接上传
        if file_size <= chunk_size:
            upload_session = FileUploadSession(
                repository_id=repository_id,
                file_name=file_name,
                file_size=file_size,
                file_path=file_path,
                content_type=content_type,
                minio_object_key=object_key,
                upload_type="direct",
                status="pending",
                total_chunks=1,
                user_id=user_id,
                expires_at=datetime.utcnow()
                + timedelta(hours=settings.upload_session_expires_hours),
            )
        else:
            # 创建分片上传
            upload_id = await minio_service.create_multipart_upload(
                bucket_name=settings.minio_default_bucket,
                object_key=object_key,
                content_type=content_type,
            )

            upload_session = FileUploadSession(
                repository_id=repository_id,
                file_name=file_name,
                file_size=file_size,
                file_path=file_path,
                content_type=content_type,
                minio_object_key=object_key,
                minio_upload_id=upload_id,
                upload_type="multipart",
                status="pending",
                total_chunks=total_chunks,
                user_id=user_id,
                expires_at=datetime.utcnow()
                + timedelta(hours=settings.upload_session_expires_hours),
            )

        self.db.add(upload_session)
        await self.db.commit()
        await self.db.refresh(upload_session)

        return {
            "session_id": getattr(upload_session, "id"),
            "upload_type": upload_session.upload_type,
            "total_chunks": total_chunks,
            "chunk_size": chunk_size,
            "expires_at": upload_session.expires_at.isoformat(),
            "minio_upload_id": upload_session.minio_upload_id,
        }

    async def upload_chunk(
        self, session_id: int, chunk_number: int, chunk_data: bytes
    ) -> Dict[str, Any]:
        """上传文件分片"""

        # 获取上传会话
        query = select(FileUploadSession).where(FileUploadSession.id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundError("上传会话不存在")

        if getattr(session, "status") != "pending":
            raise DataValidationError(f"上传会话状态无效: {session.status}")

        if getattr(session, "expires_at") < datetime.now(timezone.utc):
            await self._abort_upload_session(session)
            raise DataValidationError("上传会话已过期")

        # 上传分片到MinIO
        try:
            etag = await minio_service.upload_part(
                bucket_name=settings.minio_default_bucket,
                object_key=getattr(session, "minio_object_key"),
                upload_id=getattr(session, "minio_upload_id"),
                part_number=chunk_number,
                data=chunk_data,
            )

            # 更新上传进度
            if session.uploaded_parts is None:
                session.uploaded_parts = {}

            session.uploaded_parts[str(chunk_number)] = {
                "etag": etag,
                "size": len(chunk_data),
                "uploaded_at": datetime.utcnow().isoformat(),
            }

            # 检查是否所有分片都已上传
            uploaded_count = len(session.uploaded_parts)
            if uploaded_count >= getattr(session, "total_chunks"):
                setattr(session, "status", "ready_to_complete")

            await self.db.commit()

            return {
                "chunk_number": chunk_number,
                "etag": etag,
                "uploaded_chunks": uploaded_count,
                "total_chunks": session.total_chunks,
                "status": session.status,
            }

        except Exception as e:
            logger.error(
                f"Failed to upload chunk {chunk_number} for session {session_id}: {e}"
            )
            raise DataValidationError(f"分片上传失败: {str(e)}")

    async def complete_upload(self, session_id: int) -> Dict[str, Any]:
        """完成文件上传"""

        # 获取上传会话
        query = select(FileUploadSession).where(FileUploadSession.id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundError("上传会话不存在")

        if getattr(session, "status") != "ready_to_complete":
            raise DataValidationError(f"上传会话状态无效: {session.status}")

        try:
            # 完成分片上传
            if session.upload_type == "multipart":
                parts = []
                for part_num, part_info in session.uploaded_parts.items():
                    parts.append(
                        {"part_number": int(part_num), "etag": part_info["etag"]}
                    )

                # 按分片号排序
                parts.sort(key=lambda x: x["part_number"])

                result = await minio_service.complete_multipart_upload(
                    bucket_name=settings.minio_default_bucket,
                    object_key=getattr(session, "minio_object_key"),
                    upload_id=getattr(session, "minio_upload_id"),
                    parts=parts,
                )

                final_etag = result["etag"]
            else:
                # 直接上传已经完成
                final_etag = list(session.uploaded_parts.values())[0]["etag"]

            # 创建仓库文件记录
            repository_file = RepositoryFile(
                repository_id=session.repository_id,
                filename=session.file_name,
                file_path=session.file_path,
                file_size=session.file_size,
                mime_type=session.content_type,
                minio_bucket=settings.minio_default_bucket,
                minio_object_key=session.minio_object_key,
                file_hash=final_etag,
            )

            self.db.add(repository_file)

            # 更新会话状态
            setattr(session, "status", "completed")
            setattr(session, "completed_at", datetime.now(timezone.utc))

            await self.db.commit()
            await self.db.refresh(repository_file)

            # 更新用户存储使用量
            try:
                from app.services.storage_service import storage_service
                repository_query = await self.db.execute(
                    select(Repository).where(Repository.id == session.repository_id)
                )
                repository = repository_query.scalar_one_or_none()
                if repository:
                    await storage_service.increment_user_storage(
                        self.db, repository.owner_id, session.file_size
                    )
            except Exception as storage_error:
                logger.warning(f"Failed to update user storage: {storage_error}")

            # 如果上传的是README.md，自动同步元数据
            if session.file_path.lower() == "readme.md":
                try:
                    # 从MinIO获取README内容
                    content = await minio_service.get_file_content(
                        bucket_name=settings.minio_default_bucket,
                        object_key=session.minio_object_key
                    )
                    readme_content = content.decode('utf-8')

                    # 获取仓库
                    repository_query = await self.db.execute(
                        select(Repository).where(Repository.id == session.repository_id)
                    )
                    repository = repository_query.scalar_one_or_none()

                    if repository:
                        # 更新仓库的readme_content字段
                        repository.readme_content = readme_content

                        # 同步YAML frontmatter到数据库
                        from app.services.metadata_sync_service import MetadataSyncService
                        metadata_sync = MetadataSyncService(self.db)
                        await metadata_sync.sync_readme_to_repository(repository, readme_content)

                        await self.db.commit()
                        logger.info(f"README.md metadata synced for repository {session.repository_id}")
                except Exception as readme_error:
                    logger.warning(f"Failed to sync README metadata: {readme_error}")

            logger.info(
                f"Upload completed for session {session_id}, file: {session.file_name}"
            )

            return {
                "file_id": repository_file.id,
                "file_name": repository_file.filename,
                "file_size": repository_file.file_size,
                "file_path": repository_file.file_path,
                "content_type": repository_file.mime_type,
                "etag": final_etag,
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Failed to complete upload for session {session_id}: {e}")
            # 标记会话为失败
            setattr(session, "status", "failed")
            setattr(session, "error_message", str(e))
            await self.db.commit()
            raise DataValidationError(f"完成上传失败: {str(e)}")

    async def abort_upload(self, session_id: int) -> None:
        """取消文件上传"""

        query = select(FileUploadSession).where(FileUploadSession.id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundError("上传会话不存在")

        await self._abort_upload_session(session)

    async def _abort_upload_session(self, session: FileUploadSession) -> None:
        """内部方法：取消上传会话"""
        try:
            if getattr(session, "upload_type") == "multipart" and getattr(
                session, "minio_upload_id"
            ):
                await minio_service.abort_multipart_upload(
                    bucket_name=settings.minio_default_bucket,
                    object_key=getattr(session, "minio_object_key"),
                    upload_id=getattr(session, "minio_upload_id"),
                )

            setattr(session, "status", "aborted")
            await self.db.commit()

            logger.info(f"Upload session {session.id} aborted")

        except Exception as e:
            logger.error(f"Failed to abort upload session {session.id}: {e}")

    async def get_upload_status(self, session_id: int) -> Dict[str, Any]:
        """获取上传状态"""

        query = select(FileUploadSession).where(FileUploadSession.id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundError("上传会话不存在")

        uploaded_parts = getattr(session, "uploaded_parts")
        uploaded_chunks = len(uploaded_parts) if uploaded_parts else 0
        total_chunks = getattr(session, "total_chunks")
        progress = (uploaded_chunks / total_chunks) * 100 if total_chunks > 0 else 0

        return {
            "session_id": getattr(session, "id"),
            "status": getattr(session, "status"),
            "progress": round(progress, 2),
            "uploaded_chunks": uploaded_chunks,
            "total_chunks": total_chunks,
            "file_name": getattr(session, "file_name"),
            "file_size": getattr(session, "file_size"),
            "created_at": getattr(session, "created_at").isoformat(),
            "expires_at": getattr(session, "expires_at").isoformat(),
            "error_message": getattr(session, "error_message"),
        }

    async def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """清理过期的上传会话"""

        # 查找过期的会话
        expired_query = select(FileUploadSession).where(
            and_(
                FileUploadSession.expires_at < datetime.utcnow(),
                FileUploadSession.status.in_(["pending", "ready_to_complete"]),
            )
        )

        result = await self.db.execute(expired_query)
        expired_sessions = result.scalars().all()

        cleaned_count = 0
        for session in expired_sessions:
            try:
                await self._abort_upload_session(session)
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to cleanup expired session {getattr(session, 'id')}: {e}")

        return {
            "cleaned_sessions": cleaned_count,
            "total_expired": len(expired_sessions),
        }
