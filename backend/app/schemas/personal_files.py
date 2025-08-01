from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class PersonalFileBase(BaseModel):
    """个人文件基础模式"""
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    description: Optional[str] = Field(None, description="文件描述")
    tags: Optional[str] = Field(None, description="文件标签（逗号分隔）")
    is_public: bool = Field(False, description="是否公开")


class PersonalFileCreate(PersonalFileBase):
    """创建个人文件的请求模式"""
    pass


class PersonalFileUpdate(BaseModel):
    """更新个人文件的请求模式"""
    filename: Optional[str] = Field(None, description="文件名")
    file_path: Optional[str] = Field(None, description="文件路径")
    description: Optional[str] = Field(None, description="文件描述")
    tags: Optional[str] = Field(None, description="文件标签")
    is_public: Optional[bool] = Field(None, description="是否公开")


class PersonalFileResponse(PersonalFileBase):
    """个人文件响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    original_filename: str
    file_size: int
    file_type: Optional[str]
    mime_type: Optional[str]
    file_hash: Optional[str]
    upload_status: str
    download_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime]


class PersonalFileListItem(BaseModel):
    """个人文件列表项模式（简化版）"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    filename: str
    file_path: str
    file_size: int
    file_type: Optional[str]
    mime_type: Optional[str]
    is_public: bool
    download_count: int
    created_at: datetime
    upload_status: str


class PersonalFileDownloadResponse(BaseModel):
    """个人文件下载响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    file_id: int
    user_id: Optional[int]
    download_size: Optional[int]
    download_status: str
    downloaded_at: datetime


class PersonalFolderBase(BaseModel):
    """个人文件夹基础模式"""
    name: str = Field(..., description="文件夹名称")
    path: str = Field(..., description="文件夹路径")
    description: Optional[str] = Field(None, description="文件夹描述")
    color: Optional[str] = Field(None, description="文件夹颜色")
    is_public: bool = Field(False, description="是否公开")


class PersonalFolderCreate(PersonalFolderBase):
    """创建个人文件夹的请求模式"""
    parent_id: Optional[int] = Field(None, description="父文件夹ID")


class PersonalFolderUpdate(BaseModel):
    """更新个人文件夹的请求模式"""
    name: Optional[str] = Field(None, description="文件夹名称")
    description: Optional[str] = Field(None, description="文件夹描述")
    color: Optional[str] = Field(None, description="文件夹颜色")
    is_public: Optional[bool] = Field(None, description="是否公开")


class PersonalFolderResponse(PersonalFolderBase):
    """个人文件夹响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    file_count: int = Field(0, description="文件夹中的文件数量")


class PersonalSpaceStats(BaseModel):
    """个人空间统计模式"""
    total_files: int = Field(..., description="文件总数")
    total_folders: int = Field(..., description="文件夹总数")
    total_size: int = Field(..., description="总大小（字节）")
    file_type_breakdown: dict = Field(..., description="按文件类型统计")
    public_files: int = Field(..., description="公开文件数")
    recent_files: List[PersonalFileListItem] = Field(..., description="最近文件")


class PersonalSpaceBrowse(BaseModel):
    """个人空间浏览模式"""
    current_path: str = Field(..., description="当前路径")
    folders: List[PersonalFolderResponse] = Field(..., description="子文件夹")
    files: List[PersonalFileListItem] = Field(..., description="文件列表")
    breadcrumbs: List[dict] = Field(..., description="面包屑导航")


class UploadUrlResponse(BaseModel):
    """上传URL响应模式"""
    upload_url: str = Field(..., description="MinIO预签名上传URL")
    file_key: str = Field(..., description="文件在MinIO中的键")
    expires_in: int = Field(..., description="URL过期时间（秒）")


class FileUploadCompleteRequest(BaseModel):
    """文件上传完成请求模式"""
    file_key: str = Field(..., description="文件键")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    description: Optional[str] = Field(None, description="文件描述")
    tags: Optional[str] = Field(None, description="文件标签")
    is_public: bool = Field(False, description="是否公开")


class CreateFolderRequest(BaseModel):
    """创建文件夹请求模式"""
    name: str = Field(..., description="文件夹名称")
    parent_path: str = Field("/", description="父路径")
    is_public: bool = Field(False, description="是否公开")
    description: Optional[str] = Field(None, description="文件夹描述")


class UpdateFileRequest(BaseModel):
    """更新文件请求模式"""
    is_public: Optional[bool] = Field(None, description="是否公开")
    description: Optional[str] = Field(None, description="文件描述")
    tags: Optional[str] = Field(None, description="文件标签")


class UpdateFolderRequest(BaseModel):
    """更新文件夹请求模式"""
    is_public: Optional[bool] = Field(None, description="是否公开")
    name: Optional[str] = Field(None, description="文件夹名称")
    description: Optional[str] = Field(None, description="文件夹描述")
    color: Optional[str] = Field(None, description="文件夹颜色")