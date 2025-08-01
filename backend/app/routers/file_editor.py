from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.dependencies.minio import get_minio_service
from app.services.minio_service import MinIOService
from app.services.file_editor_service import (
    FileVersionService, FileEditSessionService, FilePermissionService, FileTemplateService, FileDraftService
)
from app.schemas.file_editor import (
    FileVersionCreate, FileVersionResponse, FileVersionContentResponse,
    FileEditSessionCreate, FileEditSessionUpdate, FileEditSessionResponse,
    FilePermissionCreate, FilePermissionResponse, FilePermissionCheck,
    FileTemplateCreate, FileTemplateUpdate, FileTemplateResponse,
    FileDiffResponse, FileHistoryResponse, CollaborationStatusResponse,
    FileDraftCreate, FileDraftUpdate, FileDraftResponse, UserDraftsResponse
)

router = APIRouter(prefix="/file-editor", tags=["文件编辑器"])


# 文件版本相关路由
@router.get("/files/{file_id}/versions", response_model=FileHistoryResponse)
async def get_file_versions(
    file_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_service: MinIOService = Depends(get_minio_service)
):
    """获取文件版本历史"""
    permission_service = FilePermissionService(db)
    has_permission = await permission_service.check_file_permission(
        file_id, current_user.id, "read"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to read this file"
        )
    
    version_service = FileVersionService(db, minio_service)
    versions = await version_service.get_file_versions(file_id, limit, offset)
    total_versions = await version_service.get_file_version_count(file_id)
    
    return FileHistoryResponse(
        file_id=file_id,
        total_versions=total_versions,
        versions=[FileVersionResponse.model_validate(v) for v in versions]
    )


@router.get("/files/{file_id}/versions/{version_id}/content", response_model=FileVersionContentResponse)
async def get_version_content(
    file_id: int,
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_service: MinIOService = Depends(get_minio_service)
):
    """获取指定版本的内容"""
    permission_service = FilePermissionService(db)
    has_permission = await permission_service.check_file_permission(
        file_id, current_user.id, "read"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to read this file"
        )
    
    version_service = FileVersionService(db, minio_service)
    
    try:
        version_info = await version_service.get_version_info(version_id)
        content = await version_service.get_version_content(version_id)
        
        return FileVersionContentResponse(
            content=content,
            encoding=version_info.encoding,
            version_id=version_id,
            version_hash=version_info.version_hash
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/files/{file_id}/versions", response_model=FileVersionResponse)
async def create_file_version(
    file_id: int,
    request: FileVersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_service: MinIOService = Depends(get_minio_service)
):
    """创建新版本"""
    permission_service = FilePermissionService(db)
    has_permission = await permission_service.check_file_permission(
        file_id, current_user.id, "commit"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to commit changes to this file"
        )
    
    version_service = FileVersionService(db, minio_service)
    
    try:
        version = await version_service.create_new_version(
            file_id=file_id,
            author_id=current_user.id,
            content=request.content,
            commit_message=request.commit_message,
            parent_version_id=request.parent_version_id,
            encoding=request.encoding
        )
        
        return FileVersionResponse.model_validate(version)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/files/{file_id}/versions/{old_version_id}/diff/{new_version_id}", response_model=FileDiffResponse)
async def get_version_diff(
    file_id: int,
    old_version_id: int,
    new_version_id: int,
    include_content: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_service: MinIOService = Depends(get_minio_service)
):
    """获取版本差异"""
    permission_service = FilePermissionService(db)
    has_permission = await permission_service.check_file_permission(
        file_id, current_user.id, "read"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to read this file"
        )
    
    version_service = FileVersionService(db, minio_service)
    
    try:
        diff_info = await version_service.get_version_diff(
            old_version_id, new_version_id, include_content
        )
        
        return FileDiffResponse(**diff_info)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# 编辑会话相关路由
@router.post("/files/{file_id}/edit-session", response_model=FileEditSessionResponse)
async def create_edit_session(
    file_id: int,
    request: FileEditSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建编辑会话"""
    permission_service = FilePermissionService(db)
    permission_type = "read" if request.is_readonly else "edit"
    has_permission = await permission_service.check_file_permission(
        file_id, current_user.id, permission_type
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No permission to {permission_type} this file"
        )
    
    session_service = FileEditSessionService(db)
    session = await session_service.create_edit_session(
        file_id=file_id,
        user_id=current_user.id,
        base_version_id=request.base_version_id,
        is_readonly=request.is_readonly
    )
    
    return FileEditSessionResponse.model_validate(session)


@router.put("/edit-sessions/{session_id}")
async def update_edit_session(
    session_id: str,
    request: FileEditSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新编辑会话内容"""
    session_service = FileEditSessionService(db)
    
    try:
        session = await session_service.update_session_content(
            session_id=session_id,
            content=request.content,
            cursor_position=request.cursor_position,
            selection_range=request.selection_range
        )
        
        return {
            "success": True,
            "last_auto_save": session.last_auto_save.isoformat() if session.last_auto_save else None,
            "session_id": session_id
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/files/{file_id}/collaboration", response_model=CollaborationStatusResponse)
async def get_collaboration_status(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取文件协作状态"""
    permission_service = FilePermissionService(db)
    has_permission = await permission_service.check_file_permission(
        file_id, current_user.id, "read"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to read this file"
        )
    
    session_service = FileEditSessionService(db)
    sessions = await session_service.get_active_sessions(file_id)
    
    can_edit = await permission_service.check_file_permission(
        file_id, current_user.id, "edit"
    )
    
    # 检查文件是否被锁定（有活跃的非只读会话）
    is_locked = any(not s.is_readonly for s in sessions)
    
    return CollaborationStatusResponse(
        file_id=file_id,
        active_sessions=[FileEditSessionResponse.model_validate(s) for s in sessions],
        total_active_users=len(set(s.user_id for s in sessions)),
        can_edit=can_edit,
        is_locked=is_locked
    )


@router.delete("/edit-sessions/{session_id}")
async def close_edit_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """关闭编辑会话"""
    session_service = FileEditSessionService(db)
    success = await session_service.close_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edit session not found"
        )
    
    return {"success": True}


# 权限管理相关路由
@router.post("/files/{file_id}/permissions", response_model=FilePermissionResponse)
async def grant_file_permission(
    file_id: int,
    request: FilePermissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """授予文件权限"""
    permission_service = FilePermissionService(db)
    has_permission = await permission_service.check_file_permission(
        file_id, current_user.id, "manage"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to manage file permissions"
        )
    
    # 计算过期时间
    expires_at = None
    if request.expires_hours:
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(hours=request.expires_hours)
    
    permissions = {
        "can_read": request.can_read,
        "can_edit": request.can_edit,
        "can_commit": request.can_commit,
        "can_manage": request.can_manage
    }
    
    permission = await permission_service.grant_file_permission(
        file_id=file_id,
        user_id=request.user_id,
        granted_by=current_user.id,
        permissions=permissions,
        expires_at=expires_at
    )
    
    return FilePermissionResponse.model_validate(permission)


@router.get("/files/{file_id}/permissions/check", response_model=FilePermissionCheck)
async def check_file_permission(
    file_id: int,
    permission_type: str = Query(..., regex="^(read|edit|commit|manage)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """检查文件权限"""
    permission_service = FilePermissionService(db)
    has_permission = await permission_service.check_file_permission(
        file_id, current_user.id, permission_type
    )
    
    return FilePermissionCheck(
        has_permission=has_permission,
        permission_type=permission_type,
        file_id=file_id,
        user_id=current_user.id
    )


# 文件模板相关路由
@router.get("/templates", response_model=List[FileTemplateResponse])
async def get_file_templates(
    category: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取文件模板列表"""
    template_service = FileTemplateService(db)
    templates = await template_service.get_templates(category, language, limit, offset)
    
    return [FileTemplateResponse.model_validate(t) for t in templates]


@router.get("/templates/{template_id}", response_model=FileTemplateResponse)
async def get_file_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模板详情"""
    template_service = FileTemplateService(db)
    template = await template_service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # 增加使用次数
    await template_service.increment_usage(template_id)
    
    return FileTemplateResponse.model_validate(template)


@router.post("/templates", response_model=FileTemplateResponse)
async def create_file_template(
    request: FileTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建文件模板"""
    template_service = FileTemplateService(db)
    
    try:
        template = await template_service.create_template(
            name=request.name,
            description=request.description,
            template_content=request.template_content,
            category=request.category,
            language=request.language,
            file_extension=request.file_extension,
            tags=request.tags,
            author_id=current_user.id
        )
        
        return FileTemplateResponse.model_validate(template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# 草稿管理相关路由
@router.post("/files/{file_id}/drafts", response_model=FileDraftResponse)
async def create_file_draft(
    file_id: int,
    request: FileDraftCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """保存文件草稿"""
    draft_service = FileDraftService(db)
    
    try:
        draft = await draft_service.create_draft(
            file_id=file_id,
            user_id=current_user.id,
            base_version_id=request.base_version_id,
            draft_content=request.draft_content,
            title=request.title,
            description=request.description,
            cursor_position=request.cursor_position,
            selection_range=request.selection_range
        )
        
        return FileDraftResponse.model_validate(draft)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/files/{file_id}/drafts", response_model=Optional[FileDraftResponse])
async def get_file_draft(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取文件草稿"""
    draft_service = FileDraftService(db)
    
    draft = await draft_service.get_draft(file_id, current_user.id)
    
    if not draft:
        return None
    
    return FileDraftResponse.model_validate(draft)


@router.put("/drafts/{draft_id}", response_model=FileDraftResponse)
async def update_file_draft(
    draft_id: int,
    request: FileDraftUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新文件草稿"""
    draft_service = FileDraftService(db)
    
    try:
        draft = await draft_service.update_draft(
            draft_id=draft_id,
            user_id=current_user.id,
            draft_content=request.draft_content,
            title=request.title,
            description=request.description,
            cursor_position=request.cursor_position,
            selection_range=request.selection_range
        )
        
        return FileDraftResponse.model_validate(draft)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/drafts/{draft_id}")
async def delete_file_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除文件草稿"""
    draft_service = FileDraftService(db)
    
    success = await draft_service.delete_draft(draft_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    return {"success": True}


@router.get("/drafts", response_model=UserDraftsResponse)
async def get_user_drafts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户所有草稿"""
    draft_service = FileDraftService(db)
    
    drafts = await draft_service.get_user_drafts(current_user.id, limit, offset)
    total_drafts = await draft_service.get_draft_count(current_user.id)
    
    return UserDraftsResponse(
        total_drafts=total_drafts,
        drafts=[FileDraftResponse.model_validate(d) for d in drafts]
    )