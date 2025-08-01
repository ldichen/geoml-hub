from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class FileVersionType(str, Enum):
    """文件版本类型枚举"""
    INITIAL = "initial"
    EDIT = "edit"
    MERGE = "merge"
    BRANCH = "branch"


class FileVersionCreate(BaseModel):
    """创建文件版本请求"""
    content: str
    commit_message: str
    encoding: str = "utf-8"
    parent_version_id: Optional[int] = None


class FileVersionResponse(BaseModel):
    """文件版本响应"""
    id: int
    file_id: int
    version_number: int
    version_hash: str
    version_type: FileVersionType
    commit_message: Optional[str]
    author_id: Optional[int]
    author_name: Optional[str]
    author_email: Optional[str]
    content_hash: str
    file_size: int
    diff_summary: Optional[Dict[str, int]]
    encoding: str
    mime_type: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileVersionContentResponse(BaseModel):
    """文件版本内容响应"""
    content: str
    encoding: str
    version_id: int
    version_hash: str


class FileEditSessionCreate(BaseModel):
    """创建编辑会话请求"""
    base_version_id: int
    is_readonly: bool = False


class FileEditSessionUpdate(BaseModel):
    """更新编辑会话请求"""
    content: str
    cursor_position: Optional[Dict] = None
    selection_range: Optional[Dict] = None


class FileEditSessionResponse(BaseModel):
    """编辑会话响应"""
    id: int
    session_id: str
    file_id: int
    user_id: int
    is_active: bool
    is_readonly: bool
    current_content: Optional[str]
    base_version_id: int
    auto_save_interval: int
    last_auto_save: Optional[datetime]
    cursor_position: Optional[Dict]
    selection_range: Optional[Dict]
    created_at: datetime
    updated_at: datetime
    last_activity: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class FilePermissionCreate(BaseModel):
    """创建文件权限请求"""
    user_id: int
    can_read: bool = True
    can_edit: bool = False
    can_commit: bool = False
    can_manage: bool = False
    expires_hours: Optional[int] = None


class FilePermissionResponse(BaseModel):
    """文件权限响应"""
    id: int
    file_id: int
    user_id: int
    can_read: bool
    can_edit: bool
    can_commit: bool
    can_manage: bool
    permission_source: Optional[str]
    granted_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class FilePermissionCheck(BaseModel):
    """权限检查响应"""
    has_permission: bool
    permission_type: str
    file_id: int
    user_id: int


class FileTemplateCreate(BaseModel):
    """创建文件模板请求"""
    name: str
    description: Optional[str] = None
    template_content: str
    file_extension: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = True


class FileTemplateUpdate(BaseModel):
    """更新文件模板请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    template_content: Optional[str] = None
    file_extension: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class FileTemplateResponse(BaseModel):
    """文件模板响应"""
    id: int
    name: str
    description: Optional[str]
    template_content: str
    file_extension: Optional[str]
    language: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    usage_count: int
    author_id: Optional[int]
    is_public: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FileDiffResponse(BaseModel):
    """文件差异响应"""
    old_version_id: int
    new_version_id: int
    diff_summary: Dict[str, int]
    diff_content: Optional[str] = None


class FileHistoryResponse(BaseModel):
    """文件历史响应"""
    file_id: int
    total_versions: int
    versions: List[FileVersionResponse]


class CollaborationStatusResponse(BaseModel):
    """协作状态响应"""
    file_id: int
    active_sessions: List[FileEditSessionResponse]
    total_active_users: int
    can_edit: bool
    is_locked: bool


class FileDraftCreate(BaseModel):
    """创建文件草稿请求"""
    file_id: int
    base_version_id: int
    draft_content: str
    title: Optional[str] = None
    description: Optional[str] = None
    cursor_position: Optional[Dict] = None
    selection_range: Optional[Dict] = None


class FileDraftUpdate(BaseModel):
    """更新文件草稿请求"""
    draft_content: str
    title: Optional[str] = None
    description: Optional[str] = None
    cursor_position: Optional[Dict] = None
    selection_range: Optional[Dict] = None


class FileDraftResponse(BaseModel):
    """文件草稿响应"""
    id: int
    file_id: int
    user_id: int
    draft_content: str
    base_version_id: int
    title: Optional[str]
    description: Optional[str]
    cursor_position: Optional[Dict]
    selection_range: Optional[Dict]
    is_auto_saved: bool
    auto_save_count: int
    created_at: datetime
    updated_at: datetime
    last_access: datetime
    
    class Config:
        from_attributes = True


class UserDraftsResponse(BaseModel):
    """用户草稿列表响应"""
    total_drafts: int
    drafts: List[FileDraftResponse]