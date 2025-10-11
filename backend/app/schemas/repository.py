from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from app.schemas.user import UserPublic
from app.schemas.task_classification import TaskClassification

T = TypeVar("T")


class RepositoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    repo_type: str = Field(default="model", pattern="^(model|dataset|space)$")
    visibility: str = Field(default="public", pattern="^(public|private)$")
    tags: Optional[List[str]] = []
    license: Optional[str] = Field(None, max_length=100)
    base_model: Optional[str] = Field(None, max_length=255)


class RepositoryCreate(RepositoryBase):
    readme_content: Optional[str] = None
    repo_metadata: Optional[Dict[str, Any]] = None
    classification_id: Optional[int] = None
    task_classification_ids: Optional[List[int]] = None


class RepositoryUpdate(BaseModel):
    description: Optional[str] = None
    visibility: Optional[str] = Field(None, pattern="^(public|private)$")
    tags: Optional[List[str]] = None
    license: Optional[str] = Field(None, max_length=100)
    base_model: Optional[str] = Field(None, max_length=255)
    readme_content: Optional[str] = None
    repo_metadata: Optional[Dict[str, Any]] = None
    classification_id: Optional[int] = None


class RepositorySettings(BaseModel):
    """仓库设置"""

    name: str
    description: Optional[str] = None
    visibility: str
    tags: Optional[List[str]] = []
    license: Optional[str] = None
    base_model: Optional[str] = None
    repo_type: str
    is_featured: bool = False


class RepositorySettingsUpdate(BaseModel):
    """仓库设置更新"""

    description: Optional[str] = None
    visibility: Optional[str] = Field(None, pattern="^(public|private)$")
    tags: Optional[List[str]] = None
    license: Optional[str] = Field(None, max_length=100)
    base_model: Optional[str] = Field(None, max_length=255)


class Repository(RepositoryBase):
    id: int
    full_name: str
    owner_id: int
    owner: UserPublic
    repo_metadata: Optional[Dict[str, Any]] = None
    readme_content: Optional[str] = None
    classification_path: Optional[List[str]] = []
    task_classifications_data: Optional[List[TaskClassification]] = (
        []
    )  # 新增：任务分类列表
    stars_count: int = 0
    downloads_count: int = 0
    views_count: int = 0
    forks_count: int = 0
    total_files: int = 0
    total_size: int = 0
    is_active: bool = True
    is_featured: bool = False
    created_at: datetime
    updated_at: datetime
    last_commit_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RepositoryListItem(BaseModel):
    """仓库列表项（简化信息）"""

    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    owner: UserPublic
    repo_type: str
    visibility: str
    tags: Optional[List[str]] = []
    license: Optional[str] = None
    base_model: Optional[str] = None
    classification_path: Optional[List[str]] = []
    task_classifications_data: Optional[List[TaskClassification]] = (
        []
    )  # 新增：任务分类列表
    stars_count: int = 0
    downloads_count: int = 0
    views_count: int = 0
    total_files: int = 0
    total_size: int = 0
    is_active: bool = True
    is_featured: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RepositoryFile(BaseModel):
    id: int
    repository_id: int
    filename: str
    file_path: str
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: int
    file_hash: Optional[str] = None
    version: str = "latest"
    download_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RepositoryFileCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=500)
    file_path: str = Field(..., min_length=1, max_length=1000)
    file_type: Optional[str] = Field(None, max_length=100)
    mime_type: Optional[str] = Field(None, max_length=200)
    file_size: int = Field(..., gt=0)
    file_hash: Optional[str] = Field(None, max_length=128)
    version: str = Field(default="latest", max_length=50)


class RepositoryStar(BaseModel):
    id: int
    user: UserPublic
    repository_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RepositoryView(BaseModel):
    id: int
    repository_id: int
    user: Optional[UserPublic] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referer: Optional[str] = None
    view_type: str = "page_view"
    target_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RepositoryStats(BaseModel):
    """仓库统计信息"""

    stars_count: int
    downloads_count: int
    views_count: int
    forks_count: int
    total_files: int
    total_size: int
    daily_downloads: int
    daily_views: int
    top_files: List[RepositoryFile]


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模式"""

    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class RepositoryListResponse(PaginatedResponse[RepositoryListItem]):
    """仓库列表分页响应"""

    pass
