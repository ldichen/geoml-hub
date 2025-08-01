from fastapi import APIRouter, Depends, Query, Path, UploadFile, File, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List

from app.database import get_async_db
from app.models import User, PersonalFile
from app.services.personal_files_service import PersonalFilesService
from app.dependencies.minio import get_minio_service
from app.schemas.personal_files import (
    PersonalFileResponse, PersonalFileListItem, PersonalFolderResponse,
    PersonalSpaceStats, PersonalSpaceBrowse,
    UploadUrlResponse, FileUploadCompleteRequest, CreateFolderRequest,
    UpdateFileRequest, UpdateFolderRequest
)
from app.dependencies.auth import get_current_user, get_current_user_required
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/personal-files", tags=["personal-files"])


@router.get("/{username}/stats", response_model=PersonalSpaceStats)
async def get_personal_space_stats(
    username: str = Path(..., description="用户名"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    minio_service = Depends(get_minio_service)
):
    """获取用户个人空间统计信息"""
    # 获取目标用户
    from app.services.user_service import UserService
    user_service = UserService(db)
    target_user = await user_service.get_user_by_username(username)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限：只有用户自己或管理员可以查看详细统计
    is_owner = current_user and current_user.id == target_user.id
    is_admin = current_user and getattr(current_user, "is_admin", False)
    
    if not is_owner and not is_admin:
        # 非所有者只能看到基本公开统计
        service = PersonalFilesService(db, minio_service)
        stats = await service.get_user_personal_space_stats(target_user.id)
        # 只返回公开信息
        return PersonalSpaceStats(
            total_files=stats.public_files,
            total_folders=0,  # 不显示文件夹统计
            total_size=0,  # 不显示大小统计
            file_type_breakdown={},  # 不显示详细分类
            public_files=stats.public_files,
            recent_files=[]  # 不显示最近文件
        )
    
    service = PersonalFilesService(db, minio_service)
    return await service.get_user_personal_space_stats(target_user.id)


@router.get("/{username}/browse", response_model=PersonalSpaceBrowse)
async def browse_personal_space(
    username: str = Path(..., description="用户名"),
    path: str = Query("/", description="浏览路径"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    minio_service = Depends(get_minio_service)
):
    """浏览用户个人空间"""
    # 获取目标用户
    from app.services.user_service import UserService
    user_service = UserService(db)
    target_user = await user_service.get_user_by_username(username)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限
    is_owner = current_user and current_user.id == target_user.id
    is_admin = current_user and getattr(current_user, "is_admin", False)
    
    if not is_owner and not is_admin:
        # 只能浏览公开文件
        pass  # TODO: 在服务层实现公开文件过滤
    
    service = PersonalFilesService(db, minio_service)
    return await service.browse_personal_space(target_user.id, path)



@router.post("/{username}/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    username: str = Path(..., description="用户名"),
    filename: str = Query(..., description="文件名"),
    file_size: int = Query(..., description="文件大小"),
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db),
    minio_service = Depends(get_minio_service)
):
    """获取文件上传URL"""
    # 检查权限
    if current_user.username != username:
        raise HTTPException(status_code=403, detail="只能向自己的个人空间上传文件")
    
    service = PersonalFilesService(db, minio_service)
    upload_info = await service.get_upload_url(current_user.id, filename, file_size)
    
    return UploadUrlResponse(**upload_info)


@router.post("/{username}/complete-upload", response_model=PersonalFileResponse)
async def complete_upload(
    username: str = Path(..., description="用户名"),
    upload_data: FileUploadCompleteRequest = ...,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db),
    minio_service = Depends(get_minio_service)
):
    """完成文件上传"""
    # 检查权限
    if current_user.username != username:
        raise HTTPException(status_code=403, detail="只能完成自己的文件上传")
    
    service = PersonalFilesService(db, minio_service)
    file = await service.complete_upload(
        current_user.id, 
        upload_data.model_dump()
    )
    
    return PersonalFileResponse.model_validate(file)


@router.get("/files/{file_id}", response_model=PersonalFileResponse)
async def get_file_info(
    file_id: int = Path(..., description="文件ID"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    minio_service = Depends(get_minio_service)
):
    """获取文件详细信息"""
    service = PersonalFilesService(db, minio_service)
    user_id = current_user.id if current_user else None
    file = await service.get_file(file_id, user_id)
    return PersonalFileResponse.model_validate(file)


@router.get("/{username}/files/{file_id}/download")
async def download_file(
    username: str = Path(..., description="用户名"),
    file_id: int = Path(..., description="文件ID"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    minio_service = Depends(get_minio_service)
):
    """获取文件下载URL"""
    service = PersonalFilesService(db, minio_service)
    user_id = current_user.id if current_user else None
    download_url = await service.get_download_url(file_id, user_id)
    
    return {"download_url": download_url}


@router.delete("/{username}/files/{file_id}")
async def delete_file(
    username: str = Path(..., description="用户名"),
    file_id: int = Path(..., description="文件ID"),
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db),
    minio_service = Depends(get_minio_service)
):
    """删除文件"""
    # 获取目标用户
    from app.services.user_service import UserService
    user_service = UserService(db)
    target_user = await user_service.get_user_by_username(username)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限
    if current_user.id != target_user.id:
        raise HTTPException(status_code=403, detail="无权限访问")
    
    service = PersonalFilesService(db, minio_service)
    success = await service.delete_file(file_id, target_user.id)
    
    return {"message": "文件删除成功" if success else "文件删除失败"}


@router.get("/{username}/search", response_model=List[PersonalFileListItem])
async def search_files(
    username: str = Path(..., description="用户名"),
    q: str = Query(..., description="搜索关键词"),
    file_type: Optional[str] = Query(None, description="文件类型过滤"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    minio_service = Depends(get_minio_service)
):
    """搜索个人文件"""
    # 获取目标用户
    from app.services.user_service import UserService
    user_service = UserService(db)
    target_user = await user_service.get_user_by_username(username)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限
    is_owner = current_user and current_user.id == target_user.id
    is_admin = current_user and getattr(current_user, "is_admin", False)
    
    if not is_owner and not is_admin:
        # 只能搜索公开文件
        pass  # TODO: 在服务层实现公开文件过滤
    
    service = PersonalFilesService(db, minio_service)
    files = await service.search_files(target_user.id, q, file_type)
    
    return [PersonalFileListItem.model_validate(file) for file in files]


@router.post("/{username}/folders", response_model=PersonalFolderResponse)
async def create_folder(
    username: str = Path(..., description="用户名"),
    folder_data: CreateFolderRequest = Body(..., description="文件夹信息"),
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db)
):
    """创建文件夹"""
    logger.info(f"Create folder request - username: {username}, folder_data: {folder_data}, current_user: {current_user.username if current_user else None}")
    
    # 获取目标用户
    from app.services.user_service import UserService
    user_service = UserService(db)
    target_user = await user_service.get_user_by_username(username)
    
    if not target_user:
        logger.error(f"Target user not found: {username}")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限
    if current_user.id != target_user.id:
        raise HTTPException(status_code=403, detail="无权限访问")
    
    service = PersonalFilesService(db, None)
    folder = await service.create_folder(
        user_id=target_user.id,
        name=folder_data.name,
        parent_path=folder_data.parent_path,
        is_public=folder_data.is_public
    )
    
    return PersonalFolderResponse.model_validate(folder)


@router.put("/{username}/folders/{folder_id}", response_model=PersonalFolderResponse)
async def update_folder(
    username: str = Path(..., description="用户名"),
    folder_id: int = Path(..., description="文件夹ID"),
    folder_data: UpdateFolderRequest = Body(..., description="文件夹更新信息"),
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db)
):
    """更新文件夹信息"""
    # 获取目标用户
    from app.services.user_service import UserService
    user_service = UserService(db)
    target_user = await user_service.get_user_by_username(username)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限
    if current_user.id != target_user.id:
        raise HTTPException(status_code=403, detail="无权限访问")
    
    service = PersonalFilesService(db, None)
    folder = await service.update_folder(
        folder_id=folder_id,
        user_id=target_user.id,
        is_public=folder_data.is_public,
        name=folder_data.name,
        description=folder_data.description,
        color=folder_data.color
    )
    
    # 需要重新计算file_count
    file_count_query = select(func.count(PersonalFile.id)).where(
        and_(
            PersonalFile.user_id == target_user.id,
            PersonalFile.file_path.startswith(folder.path),
            PersonalFile.is_deleted == False
        )
    )
    file_count_result = await db.execute(file_count_query)
    file_count = file_count_result.scalar() or 0
    
    folder_response = PersonalFolderResponse.model_validate(folder)
    folder_response.file_count = file_count
    
    return folder_response


@router.delete("/{username}/folders/{folder_id}")
async def delete_folder(
    username: str = Path(..., description="用户名"),
    folder_id: int = Path(..., description="文件夹ID"),
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db),
    minio_service = Depends(get_minio_service)
):
    """删除文件夹"""
    # 获取目标用户
    from app.services.user_service import UserService
    user_service = UserService(db)
    target_user = await user_service.get_user_by_username(username)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限
    if current_user.id != target_user.id:
        raise HTTPException(status_code=403, detail="无权限访问")
    
    service = PersonalFilesService(db, minio_service)
    success = await service.delete_folder(folder_id, target_user.id)
    
    return {"message": "文件夹删除成功" if success else "文件夹删除失败"}


@router.put("/{username}/files/{file_id}", response_model=PersonalFileResponse)
async def update_file(
    username: str = Path(..., description="用户名"),
    file_id: int = Path(..., description="文件ID"),
    file_data: UpdateFileRequest = Body(..., description="文件更新信息"),
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db)
):
    """更新文件信息"""
    # 获取目标用户
    from app.services.user_service import UserService
    user_service = UserService(db)
    target_user = await user_service.get_user_by_username(username)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查权限
    if current_user.id != target_user.id:
        raise HTTPException(status_code=403, detail="无权限访问")
    
    service = PersonalFilesService(db, None)
    file = await service.update_file(
        file_id=file_id,
        user_id=target_user.id,
        is_public=file_data.is_public,
        description=file_data.description,
        tags=file_data.tags
    )
    
    return PersonalFileResponse.model_validate(file)