from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Snapshot相关Schema
class SnapshotFileInfo(BaseModel):
    """快照文件信息"""
    file_path: str = Field(..., description="文件在仓库中的相对路径")
    file_size: int = Field(..., description="文件大小(字节)")
    content_type: Optional[str] = Field(None, description="文件MIME类型")
    file_hash: Optional[str] = Field(None, description="文件SHA-256哈希")


class SnapshotCreate(BaseModel):
    """创建快照请求"""
    message: str = Field(..., min_length=1, max_length=1000, description="提交信息")
    branch: str = Field(default="main", max_length=255, description="分支名称")
    files: Optional[List[SnapshotFileInfo]] = Field(default=[], description="文件信息列表")


class SnapshotResponse(BaseModel):
    """快照响应"""
    id: str = Field(..., description="快照ID")
    repository_id: int = Field(..., description="仓库ID")
    message: str = Field(..., description="提交信息")
    branch: str = Field(..., description="所属分支")
    parent_snapshot_id: Optional[str] = Field(None, description="父快照ID")
    created_at: datetime = Field(..., description="创建时间")

    # 作者信息
    author: Dict[str, Any] = Field(..., description="作者信息")

    # 文件信息
    files: List[SnapshotFileInfo] = Field(default=[], description="快照包含的文件")

    class Config:
        from_attributes = True


# Branch相关Schema
class BranchCreate(BaseModel):
    """创建分支请求"""
    name: str = Field(..., min_length=1, max_length=255, description="分支名称")
    source_branch: str = Field(default="main", description="基于的源分支")


class BranchResponse(BaseModel):
    """分支响应"""
    id: int = Field(..., description="分支ID")
    repository_id: int = Field(..., description="仓库ID")
    name: str = Field(..., description="分支名称")
    head_snapshot_id: Optional[str] = Field(None, description="最新快照ID")
    is_default: bool = Field(..., description="是否为默认分支")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


# Release相关Schema
class ReleaseCreate(BaseModel):
    """创建发布版本请求"""
    tag_name: str = Field(..., min_length=1, max_length=100, description="版本标签")
    snapshot_id: str = Field(..., description="基于的快照ID")
    title: str = Field(..., min_length=1, max_length=255, description="发布标题")
    description: Optional[str] = Field(None, description="发布描述")
    is_prerelease: bool = Field(default=False, description="是否为预发布版本")


class ReleaseResponse(BaseModel):
    """发布版本响应"""
    id: int = Field(..., description="发布版本ID")
    repository_id: int = Field(..., description="仓库ID")
    tag_name: str = Field(..., description="版本标签")
    snapshot_id: str = Field(..., description="快照ID")
    title: str = Field(..., description="发布标题")
    description: Optional[str] = Field(None, description="发布描述")
    is_prerelease: bool = Field(..., description="是否为预发布版本")
    download_count: int = Field(..., description="下载次数")
    created_at: datetime = Field(..., description="创建时间")

    # 快照信息
    snapshot: SnapshotResponse = Field(..., description="关联的快照信息")

    class Config:
        from_attributes = True


# 文件上传相关Schema
class FileUploadRequest(BaseModel):
    """文件上传请求"""
    commit_message: str = Field(..., min_length=1, max_length=1000, description="提交信息")
    branch: str = Field(default="main", max_length=255, description="目标分支")


# 回滚请求Schema
class RollbackRequest(BaseModel):
    """回滚请求"""
    target_snapshot_id: str = Field(..., description="目标快照ID")
    message: Optional[str] = Field(None, description="回滚信息")


# 版本对比Schema
class FileChangeInfo(BaseModel):
    """文件变更信息"""
    file_path: str = Field(..., description="文件路径")
    change_type: str = Field(..., description="变更类型: added, modified, deleted")
    old_size: Optional[int] = Field(None, description="旧文件大小")
    new_size: Optional[int] = Field(None, description="新文件大小")
    old_hash: Optional[str] = Field(None, description="旧文件哈希")
    new_hash: Optional[str] = Field(None, description="新文件哈希")


class SnapshotComparisonResponse(BaseModel):
    """快照对比响应"""
    base_snapshot_id: str = Field(..., description="基础快照ID")
    compare_snapshot_id: str = Field(..., description="对比快照ID")
    changes: List[FileChangeInfo] = Field(..., description="文件变更列表")

    # 统计信息
    stats: Dict[str, int] = Field(..., description="变更统计")  # {"added": 5, "modified": 3, "deleted": 1}


# 批量操作Schema
class BatchSnapshotResponse(BaseModel):
    """批量快照响应"""
    snapshots: List[SnapshotResponse] = Field(..., description="快照列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    limit: int = Field(..., description="每页数量")


class BatchBranchResponse(BaseModel):
    """批量分支响应"""
    branches: List[BranchResponse] = Field(..., description="分支列表")
    total: int = Field(..., description="总数量")


class BatchReleaseResponse(BaseModel):
    """批量发布版本响应"""
    releases: List[ReleaseResponse] = Field(..., description="发布版本列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    limit: int = Field(..., description="每页数量")


# 仓库版本控制状态Schema
class RepositoryVersionStatus(BaseModel):
    """仓库版本控制状态"""
    default_branch: str = Field(..., description="默认分支")
    total_snapshots: int = Field(..., description="总快照数")
    total_branches: int = Field(..., description="总分支数")
    total_releases: int = Field(..., description="总发布版本数")
    latest_snapshot: Optional[SnapshotResponse] = Field(None, description="最新快照")
    recent_snapshots: List[SnapshotResponse] = Field(..., description="最近快照列表")


# 下载相关Schema
class DownloadRequest(BaseModel):
    """下载请求"""
    format: str = Field(default="zip", description="下载格式: zip, tar.gz")


class DownloadResponse(BaseModel):
    """下载响应"""
    download_url: str = Field(..., description="下载链接")
    expires_in: int = Field(..., description="链接有效期(秒)")
    file_name: str = Field(..., description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小")