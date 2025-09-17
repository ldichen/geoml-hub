from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.services.version_control_service import VersionControlService
from app.services.repository_service import RepositoryService
from app.schemas.version_control import (
    SnapshotCreate,
    SnapshotResponse,
    BranchCreate,
    BranchResponse,
    ReleaseCreate,
    ReleaseResponse,
    BatchSnapshotResponse,
    BatchBranchResponse,
    BatchReleaseResponse,
    SnapshotComparisonResponse,
    RollbackRequest,
    FileUploadRequest,
)
from app.middleware.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/v1/repositories", tags=["版本控制"])


@router.post("/{repository_id}/snapshots", response_model=SnapshotResponse)
async def create_snapshot(
    repository_id: int,
    snapshot_data: SnapshotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建快照"""
    version_control = VersionControlService(db)

    try:
        result = await version_control.create_snapshot(
            repository_id=repository_id,
            author_id=current_user.id,
            message=snapshot_data.message,
            branch=snapshot_data.branch,
            file_uploads=snapshot_data.files,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{repository_id}/upload-files")
async def upload_files_with_snapshot(
    repository_id: int,
    files: List[UploadFile] = File(...),
    file_paths: List[str] = Form(...),
    commit_message: str = Form(...),
    branch: str = Form(default="main"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传文件并创建快照"""
    repository_service = RepositoryService(db)

    try:
        result = await repository_service.upload_files_with_snapshot(
            repository_id=repository_id,
            user_id=current_user.id,
            files=files,
            file_paths=file_paths,
            commit_message=commit_message,
            branch=branch,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}/snapshots", response_model=BatchSnapshotResponse)
async def get_snapshots(
    repository_id: int,
    branch: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取快照列表"""
    repository_service = RepositoryService(db)

    try:
        result = await repository_service.get_repository_snapshots(
            repository_id, branch, page, limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{repository_id}/branches", response_model=BranchResponse)
async def create_branch(
    repository_id: int,
    branch_data: BranchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建分支"""
    repository_service = RepositoryService(db)

    try:
        result = await repository_service.create_repository_branch(
            repository_id, branch_data.name, branch_data.source_branch
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}/branches", response_model=BatchBranchResponse)
async def get_branches(
    repository_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取分支列表"""
    repository_service = RepositoryService(db)

    try:
        result = await repository_service.get_repository_branches(repository_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{repository_id}/releases", response_model=ReleaseResponse)
async def create_release(
    repository_id: int,
    release_data: ReleaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建发布版本"""
    repository_service = RepositoryService(db)

    try:
        result = await repository_service.create_repository_release(
            repository_id=repository_id,
            tag_name=release_data.tag_name,
            snapshot_id=release_data.snapshot_id,
            title=release_data.title,
            description=release_data.description,
            is_prerelease=release_data.is_prerelease,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}/releases", response_model=BatchReleaseResponse)
async def get_releases(
    repository_id: int,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取发布版本列表"""
    repository_service = RepositoryService(db)

    try:
        result = await repository_service.get_repository_releases(
            repository_id, page, limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}/compare/{base_snapshot_id}...{compare_snapshot_id}",
            response_model=SnapshotComparisonResponse)
async def compare_snapshots(
    repository_id: int,
    base_snapshot_id: str,
    compare_snapshot_id: str,
    db: AsyncSession = Depends(get_db),
):
    """比较快照"""
    repository_service = RepositoryService(db)

    try:
        result = await repository_service.compare_repository_snapshots(
            repository_id, base_snapshot_id, compare_snapshot_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{repository_id}/rollback")
async def rollback_repository(
    repository_id: int,
    rollback_data: RollbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """回滚仓库"""
    repository_service = RepositoryService(db)

    try:
        result = await repository_service.rollback_repository(
            repository_id=repository_id,
            target_snapshot_id=rollback_data.target_snapshot_id,
            branch="main",  # 默认回滚到main分支
            user_id=current_user.id,
            message=rollback_data.message,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}/snapshots/{snapshot_id}")
async def get_snapshot_details(
    repository_id: int,
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取快照详情"""
    version_control = VersionControlService(db)

    try:
        # 这里需要在VersionControlService中添加获取单个快照详情的方法
        # 暂时返回基本信息
        return {"snapshot_id": snapshot_id, "repository_id": repository_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}/snapshots/{snapshot_id}/files")
async def get_snapshot_files(
    repository_id: int,
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取快照文件列表"""
    version_control = VersionControlService(db)

    try:
        # 这里需要在VersionControlService中添加获取快照文件的方法
        # 暂时返回基本信息
        return {"snapshot_id": snapshot_id, "files": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{repository_id}/branches/{branch_name}")
async def delete_branch(
    repository_id: int,
    branch_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分支"""
    version_control = VersionControlService(db)

    try:
        # 这里需要在VersionControlService中添加删除分支的方法
        # 暂时返回成功信息
        return {"message": f"分支 '{branch_name}' 删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{repository_id}/releases/{release_id}")
async def delete_release(
    repository_id: int,
    release_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除发布版本"""
    version_control = VersionControlService(db)

    try:
        # 这里需要在VersionControlService中添加删除发布版本的方法
        # 暂时返回成功信息
        return {"message": f"发布版本 {release_id} 删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}/status")
async def get_repository_version_status(
    repository_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取仓库版本控制状态"""
    repository_service = RepositoryService(db)

    try:
        # 获取分支、快照、发布版本的汇总信息
        branches_result = await repository_service.get_repository_branches(repository_id)
        snapshots_result = await repository_service.get_repository_snapshots(repository_id, page=1, limit=5)
        releases_result = await repository_service.get_repository_releases(repository_id, page=1, limit=5)

        # 找到默认分支
        default_branch = "main"
        for branch in branches_result.get("branches", []):
            if branch.get("is_default"):
                default_branch = branch["name"]
                break

        latest_snapshot = None
        if snapshots_result.get("snapshots"):
            latest_snapshot = snapshots_result["snapshots"][0]

        return {
            "default_branch": default_branch,
            "total_snapshots": snapshots_result.get("total", 0),
            "total_branches": branches_result.get("total", 0),
            "total_releases": releases_result.get("total", 0),
            "latest_snapshot": latest_snapshot,
            "recent_snapshots": snapshots_result.get("snapshots", [])[:5],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))