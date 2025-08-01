import os
import hashlib
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models import PersonalFile, PersonalFolder, PersonalFileDownload, User
from app.schemas.personal_files import (
    PersonalFileCreate, PersonalFileUpdate, PersonalFolderCreate, PersonalFolderUpdate,
    PersonalSpaceStats, PersonalSpaceBrowse, PersonalFileListItem, PersonalFolderResponse
)
from app.services.minio_service import MinIOService
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class PersonalFilesService:
    """个人文件服务"""
    
    def __init__(self, db: AsyncSession, minio_service: MinIOService):
        self.db = db
        self.minio = minio_service
        self.bucket_name = "personal-files"
    
    async def get_user_personal_space_stats(self, user_id: int) -> PersonalSpaceStats:
        """获取用户个人空间统计信息"""
        # 文件统计
        files_query = select(
            func.count(PersonalFile.id).label("total_files"),
            func.sum(PersonalFile.file_size).label("total_size"),
            func.count(PersonalFile.id).filter(PersonalFile.is_public == True).label("public_files")
        ).where(
            and_(
                PersonalFile.user_id == user_id,
                PersonalFile.is_deleted == False
            )
        )
        
        files_result = await self.db.execute(files_query)
        files_stats = files_result.first()
        
        # 文件夹统计
        folders_query = select(func.count(PersonalFolder.id)).where(
            and_(
                PersonalFolder.user_id == user_id,
                PersonalFolder.is_deleted == False
            )
        )
        folders_result = await self.db.execute(folders_query)
        total_folders = folders_result.scalar() or 0
        
        # 按文件类型统计
        type_query = select(
            PersonalFile.file_type,
            func.count(PersonalFile.id).label("count"),
            func.sum(PersonalFile.file_size).label("size")
        ).where(
            and_(
                PersonalFile.user_id == user_id,
                PersonalFile.is_deleted == False
            )
        ).group_by(PersonalFile.file_type)
        
        type_result = await self.db.execute(type_query)
        file_type_breakdown = {}
        for row in type_result:
            file_type_breakdown[row.file_type or "other"] = {
                "count": row.count,
                "size": row.size or 0
            }
        
        # 最近文件
        recent_query = select(PersonalFile).where(
            and_(
                PersonalFile.user_id == user_id,
                PersonalFile.is_deleted == False
            )
        ).order_by(desc(PersonalFile.created_at)).limit(5)
        
        recent_result = await self.db.execute(recent_query)
        recent_files = [
            PersonalFileListItem.model_validate(file) 
            for file in recent_result.scalars().all()
        ]
        
        return PersonalSpaceStats(
            total_files=files_stats.total_files or 0,
            total_folders=total_folders,
            total_size=files_stats.total_size or 0,
            file_type_breakdown=file_type_breakdown,
            public_files=files_stats.public_files or 0,
            recent_files=recent_files
        )
    
    async def browse_personal_space(self, user_id: int, path: str = "/") -> PersonalSpaceBrowse:
        """浏览个人空间"""
        # 规范化路径
        if not path.startswith("/"):
            path = "/" + path
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        
        # 简化文件夹查询逻辑：直接查询所有文件夹，然后在Python中过滤
        all_folders_query = select(PersonalFolder).where(
            and_(
                PersonalFolder.user_id == user_id,
                PersonalFolder.is_deleted == False
            )
        )
        
        all_folders_result = await self.db.execute(all_folders_query)
        all_folders = all_folders_result.scalars().all()
        
        # 过滤出当前路径的直接子文件夹
        folders = []
        for folder in all_folders:
            folder_path = folder.path
            should_include = False
            
            if path == "/":
                # 根目录：查找 /xxx 格式的文件夹（不包含更多斜杠）
                if folder_path.startswith("/") and folder_path.count("/") == 1 and len(folder_path) > 1:
                    should_include = True
            else:
                # 特定目录：查找 /parent/child 格式的文件夹
                if folder_path.startswith(f"{path}/") and folder_path.count("/") == path.count("/") + 1:
                    should_include = True
            
            if should_include:
                # 计算文件夹中的文件数量
                file_count_query = select(func.count(PersonalFile.id)).where(
                    and_(
                        PersonalFile.user_id == user_id,
                        PersonalFile.file_path.startswith(folder_path),
                        PersonalFile.is_deleted == False
                    )
                )
                file_count_result = await self.db.execute(file_count_query)
                file_count = file_count_result.scalar() or 0
                
                # 创建响应对象并设置file_count
                folder_response = PersonalFolderResponse.model_validate(folder)
                folder_response.file_count = file_count
                folders.append(folder_response)
        
        # 获取当前路径下的文件
        if path == "/":
            # 根目录下的文件（不在子文件夹中的文件）
            files_query = select(PersonalFile).where(
                and_(
                    PersonalFile.user_id == user_id,
                    PersonalFile.file_path == "/",  # 直接在根目录的文件
                    PersonalFile.is_deleted == False
                )
            )
        else:
            # 特定文件夹下的文件
            files_query = select(PersonalFile).where(
                and_(
                    PersonalFile.user_id == user_id,
                    PersonalFile.file_path == path,  # 完全匹配路径
                    PersonalFile.is_deleted == False
                )
            )
        
        files_result = await self.db.execute(files_query)
        files = [
            PersonalFileListItem.model_validate(file) 
            for file in files_result.scalars().all()
        ]
        
        # 生成面包屑导航
        breadcrumbs = self._generate_breadcrumbs(path)
        
        return PersonalSpaceBrowse(
            current_path=path,
            folders=folders,
            files=files,
            breadcrumbs=breadcrumbs
        )
    
    def _generate_breadcrumbs(self, path: str) -> List[Dict[str, str]]:
        """生成面包屑导航"""
        breadcrumbs = [{"name": "根目录", "path": "/"}]
        
        if path != "/" and path.strip("/"):
            parts = path.strip("/").split("/")
            current_path = ""
            for part in parts:
                current_path += "/" + part
                breadcrumbs.append({
                    "name": part,
                    "path": current_path
                })
        
        return breadcrumbs
    
    async def create_folder(self, user_id: int, folder_data: PersonalFolderCreate) -> PersonalFolder:
        """创建文件夹"""
        # 检查路径是否已存在
        existing_query = select(PersonalFolder).where(
            and_(
                PersonalFolder.user_id == user_id,
                PersonalFolder.path == folder_data.path,
                PersonalFolder.is_deleted == False
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_folder = existing_result.scalar_one_or_none()
        
        if existing_folder:
            raise HTTPException(status_code=400, detail="文件夹路径已存在")
        
        folder = PersonalFolder(
            user_id=user_id,
            **folder_data.model_dump()
        )
        
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)
        
        return folder
    
    async def get_upload_url(self, user_id: int, filename: str, file_size: int) -> Dict[str, Any]:
        """获取文件上传URL"""
        # 生成文件键
        file_key = f"user_{user_id}/{self._generate_file_key(filename)}"
        
        # 获取预签名上传URL
        upload_url = await self.minio.get_upload_url(
            bucket_name=self.bucket_name,
            object_key=file_key,
            expires=3600  # 1小时
        )
        
        return {
            "upload_url": upload_url,
            "file_key": file_key,
            "expires_in": 3600
        }
    
    def _generate_file_key(self, filename: str) -> str:
        """生成文件键"""
        import uuid
        import time
        
        # 获取文件扩展名
        name, ext = os.path.splitext(filename)
        
        # 生成唯一键
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{timestamp}_{unique_id}_{name}{ext}"
    
    async def complete_upload(self, user_id: int, upload_data: Dict[str, Any]) -> PersonalFile:
        """完成文件上传"""
        # 验证文件是否已上传到MinIO
        file_exists = await self.minio.file_exists(
            bucket_name=self.bucket_name,
            object_key=upload_data["file_key"]
        )
        
        if not file_exists:
            raise HTTPException(status_code=400, detail="文件上传未完成")
        
        # 计算文件哈希
        file_hash = await self._calculate_file_hash(upload_data["file_key"])
        
        # 确定文件类型
        file_type = self._determine_file_type(upload_data.get("mime_type", ""))
        
        personal_file = PersonalFile(
            user_id=user_id,
            filename=upload_data["filename"],
            original_filename=upload_data["filename"],
            file_path=upload_data.get("file_path", "/"),
            file_size=upload_data["file_size"],
            file_type=file_type,
            mime_type=upload_data.get("mime_type"),
            file_hash=file_hash,
            minio_bucket=self.bucket_name,
            minio_object_key=upload_data["file_key"],
            description=upload_data.get("description"),
            tags=upload_data.get("tags"),
            is_public=upload_data.get("is_public", False),
            upload_status="completed"
        )
        
        self.db.add(personal_file)
        await self.db.commit()
        await self.db.refresh(personal_file)
        
        return personal_file
    
    async def _calculate_file_hash(self, file_key: str) -> str:
        """计算文件哈希"""
        try:
            # 从MinIO下载文件内容计算哈希
            file_data = await self.minio.get_file_content(
                bucket_name=self.bucket_name,
                object_key=file_key
            )
            return hashlib.sha256(file_data).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate file hash for {file_key}: {e}")
            return ""
    
    def _determine_file_type(self, mime_type: str) -> str:
        """根据MIME类型确定文件分类"""
        if not mime_type:
            return "other"
        
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type in ["application/pdf", "text/plain", "text/markdown"]:
            return "document"
        elif "model" in mime_type or "pytorch" in mime_type:
            return "model"
        elif "csv" in mime_type or "json" in mime_type or "xml" in mime_type:
            return "data"
        else:
            return "other"
    
    async def get_file(self, file_id: int, user_id: Optional[int] = None) -> PersonalFile:
        """获取文件信息"""
        query = select(PersonalFile).where(PersonalFile.id == file_id)
        result = await self.db.execute(query)
        file = result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查权限
        if file.user_id != user_id and not file.is_public:
            raise HTTPException(status_code=403, detail="无权访问此文件")
        
        return file
    
    async def get_download_url(self, file_id: int, user_id: Optional[int] = None) -> str:
        """获取文件下载URL"""
        file = await self.get_file(file_id, user_id)
        
        # 生成预签名下载URL
        download_url = await self.minio.get_download_url(
            bucket_name=file.minio_bucket,
            object_key=file.minio_object_key,
            expires=3600
        )
        
        # 记录下载
        await self._record_download(file_id, user_id)
        
        return download_url
    
    async def _record_download(self, file_id: int, user_id: Optional[int] = None):
        """记录文件下载"""
        download_record = PersonalFileDownload(
            file_id=file_id,
            user_id=user_id,
            download_status="completed"
        )
        
        self.db.add(download_record)
        
        # 更新文件下载计数
        file_query = select(PersonalFile).where(PersonalFile.id == file_id)
        file_result = await self.db.execute(file_query)
        file = file_result.scalar_one()
        file.download_count += 1
        
        await self.db.commit()
    
    async def delete_file(self, file_id: int, user_id: int) -> bool:
        """删除文件"""
        file = await self.get_file(file_id, user_id)
        
        if file.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权删除此文件")
        
        # 软删除
        file.is_deleted = True
        await self.db.commit()
        
        return True
    
    async def search_files(self, user_id: int, query: str, file_type: Optional[str] = None) -> List[PersonalFile]:
        """搜索个人文件"""
        search_query = select(PersonalFile).where(
            and_(
                PersonalFile.user_id == user_id,
                PersonalFile.is_deleted == False,
                or_(
                    PersonalFile.filename.ilike(f"%{query}%"),
                    PersonalFile.description.ilike(f"%{query}%"),
                    PersonalFile.tags.ilike(f"%{query}%")
                )
            )
        )
        
        if file_type:
            search_query = search_query.where(PersonalFile.file_type == file_type)
        
        result = await self.db.execute(search_query)
        return result.scalars().all()
    
    async def create_folder(self, user_id: int, name: str, parent_path: str, is_public: bool = False) -> PersonalFolder:
        """创建文件夹"""
        logger.info(f"Creating folder - user_id: {user_id}, name: {name}, parent_path: {parent_path}")
        
        # 构建完整路径
        if parent_path == "/" or parent_path.endswith('/'):
            full_path = f"{parent_path.rstrip('/')}/{name}" if parent_path != "/" else f"/{name}"
        else:
            full_path = f"{parent_path}/{name}"
        
        logger.info(f"Full path will be: {full_path}")
        
        # 检查是否已存在同名文件夹
        existing_query = select(PersonalFolder).where(
            and_(
                PersonalFolder.user_id == user_id,
                PersonalFolder.path == full_path,
                PersonalFolder.is_deleted == False
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_folder = existing_result.scalar_one_or_none()
        
        if existing_folder:
            logger.warning(f"Folder already exists at path: {full_path}")
            raise HTTPException(status_code=400, detail="文件夹已存在")
        
        try:
            folder = PersonalFolder(
                user_id=user_id,
                name=name,
                path=full_path,
                is_public=is_public
            )
            
            self.db.add(folder)
            await self.db.commit()
            await self.db.refresh(folder)
            
            logger.info(f"Successfully created folder with id: {folder.id}")
            return folder
            
        except Exception as e:
            logger.error(f"Error creating folder: {str(e)}")
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"创建文件夹失败: {str(e)}")
    
    async def delete_folder(self, folder_id: int, user_id: int) -> bool:
        """删除文件夹"""
        folder_query = select(PersonalFolder).where(PersonalFolder.id == folder_id)
        folder_result = await self.db.execute(folder_query)
        folder = folder_result.scalar_one_or_none()
        
        if not folder:
            raise HTTPException(status_code=404, detail="文件夹不存在")
        
        if folder.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权删除此文件夹")
        
        # 删除文件夹下的所有文件（软删除）
        files_query = select(PersonalFile).where(
            and_(
                PersonalFile.user_id == user_id,
                PersonalFile.file_path.startswith(folder.path),
                PersonalFile.is_deleted == False
            )
        )
        files_result = await self.db.execute(files_query)
        files = files_result.scalars().all()
        
        for file in files:
            file.is_deleted = True
        
        # 删除子文件夹（软删除）
        subfolders_query = select(PersonalFolder).where(
            and_(
                PersonalFolder.user_id == user_id,
                PersonalFolder.path.startswith(folder.path + "/"),
                PersonalFolder.is_deleted == False
            )
        )
        subfolders_result = await self.db.execute(subfolders_query)
        subfolders = subfolders_result.scalars().all()
        
        for subfolder in subfolders:
            subfolder.is_deleted = True
        
        # 删除文件夹（软删除）
        folder.is_deleted = True
        await self.db.commit()
        
        return True
    
    async def update_folder(self, folder_id: int, user_id: int, **kwargs) -> PersonalFolder:
        """更新文件夹信息"""
        folder_query = select(PersonalFolder).where(PersonalFolder.id == folder_id)
        folder_result = await self.db.execute(folder_query)
        folder = folder_result.scalar_one_or_none()
        
        if not folder:
            raise HTTPException(status_code=404, detail="文件夹不存在")
        
        if folder.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权修改此文件夹")
        
        # 更新字段
        for key, value in kwargs.items():
            if value is not None and hasattr(folder, key):
                setattr(folder, key, value)
        
        await self.db.commit()
        await self.db.refresh(folder)
        
        return folder
    
    async def update_file(self, file_id: int, user_id: int, **kwargs) -> PersonalFile:
        """更新文件信息"""
        file = await self.get_file(file_id, user_id)
        
        if file.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权修改此文件")
        
        # 更新允许的字段
        if 'is_public' in kwargs:
            file.is_public = kwargs['is_public']
        if 'description' in kwargs:
            file.description = kwargs['description']
        if 'tags' in kwargs:
            file.tags = kwargs['tags']
        
        await self.db.commit()
        await self.db.refresh(file)
        
        return file