from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from app.database import get_async_db
from app.models import RepositoryFile, Repository, User
from app.dependencies.auth import get_current_active_user, require_admin, get_current_user
from app.services.repository_service import RepositoryService
from app.services.minio_service import MinIOService
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
minio_service = MinIOService()


@router.get("/")
async def get_all_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="搜索文件名"),
    file_type: Optional[str] = Query(None, description="文件类型"),
    repository_id: Optional[int] = Query(None, description="仓库ID"),
    sort_by: str = Query("created", regex="^(created|updated|size|downloads|name)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """获取所有文件列表（管理员）"""

    query = (
        select(RepositoryFile)
        .options(selectinload(RepositoryFile.repository))
        .where(RepositoryFile.is_deleted == False)
    )

    # 搜索条件
    if search:
        search_pattern = f"%{search}%"
        query = query.where(RepositoryFile.filename.ilike(search_pattern))

    if file_type:
        query = query.where(RepositoryFile.file_type == file_type)

    if repository_id:
        query = query.where(RepositoryFile.repository_id == repository_id)

    # 排序
    sort_field = {
        "created": RepositoryFile.created_at,
        "updated": RepositoryFile.updated_at,
        "size": RepositoryFile.file_size,
        "downloads": RepositoryFile.download_count,
        "name": RepositoryFile.filename,
    }[sort_by]

    if order == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)

    # 分页
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    files = result.scalars().all()

    # 总数查询
    count_query = select(func.count(RepositoryFile.id)).where(
        RepositoryFile.is_deleted == False
    )
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(RepositoryFile.filename.ilike(search_pattern))
    if file_type:
        count_query = count_query.where(RepositoryFile.file_type == file_type)
    if repository_id:
        count_query = count_query.where(RepositoryFile.repository_id == repository_id)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return {
        "files": files,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/{file_id}")
async def get_file_details(
    file_id: int = Path(..., description="文件ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取文件详细信息"""

    query = (
        select(RepositoryFile)
        .options(selectinload(RepositoryFile.repository).selectinload(Repository.owner))
        .where(and_(RepositoryFile.id == file_id, RepositoryFile.is_deleted == False))
    )

    result = await db.execute(query)
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查访问权限
    if file.repository.visibility == "private":
        if not current_user or (
            file.repository.owner_id != current_user.id
            and not getattr(current_user, "is_admin", False)
        ):
            raise HTTPException(status_code=403, detail="无权限访问此文件")

    return file


@router.get("/{file_id}/download")
async def download_file_by_id(
    file_id: int = Path(..., description="文件ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """通过文件ID下载文件"""

    query = (
        select(RepositoryFile)
        .options(selectinload(RepositoryFile.repository).selectinload(Repository.owner))
        .where(and_(RepositoryFile.id == file_id, RepositoryFile.is_deleted == False))
    )

    result = await db.execute(query)
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查访问权限
    if file.repository.visibility == "private":
        if not current_user or (
            file.repository.owner_id != current_user.id
            and not getattr(current_user, "is_admin", False)
        ):
            raise HTTPException(status_code=403, detail="无权限下载此文件")

    # 生成下载链接
    try:
        download_url = await minio_service.get_download_url(
            bucket_name=getattr(file, "minio_bucket"), object_key=file.minio_object_name
        )

        # 更新下载统计
        setattr(file, "download_count", file.download_count + 1)
        await db.commit()

        return {
            "download_url": download_url,
            "filename": file.filename,
            "file_size": file.file_size,
            "content_type": file.content_type,
        }

    except Exception as e:
        logger.error(f"Failed to generate download URL for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="生成下载链接失败")


@router.put("/{file_id}")
async def update_file_info(
    file_id: int = Path(..., description="文件ID"),
    filename: Optional[str] = Query(None, description="新文件名"),
    file_path: Optional[str] = Query(None, description="新文件路径"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """更新文件信息"""

    query = (
        select(RepositoryFile)
        .options(selectinload(RepositoryFile.repository))
        .where(and_(RepositoryFile.id == file_id, RepositoryFile.is_deleted == False))
    )

    result = await db.execute(query)
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查权限
    if file.repository.owner_id != current_user.id and not getattr(
        current_user, "is_admin", False
    ):
        raise HTTPException(status_code=403, detail="无权限修改此文件")

    # 更新文件信息
    if filename:
        setattr(file, "filename", filename)
    if file_path:
        # 检查路径冲突
        existing_query = select(RepositoryFile).where(
            and_(
                RepositoryFile.repository_id == file.repository_id,
                RepositoryFile.file_path == file_path,
                RepositoryFile.id != file_id,
                RepositoryFile.is_deleted == False,
            )
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="文件路径已存在")

        setattr(file, "file_path", file_path)

    await db.commit()

    return {"message": "文件信息已更新", "file": file}


@router.delete("/{file_id}")
async def delete_file(
    file_id: int = Path(..., description="文件ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """删除文件"""

    query = (
        select(RepositoryFile)
        .options(selectinload(RepositoryFile.repository))
        .where(and_(RepositoryFile.id == file_id, RepositoryFile.is_deleted == False))
    )

    result = await db.execute(query)
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查权限
    if file.repository.owner_id != current_user.id and not getattr(
        current_user, "is_admin", False
    ):
        raise HTTPException(status_code=403, detail="无权限删除此文件")

    try:
        # 从MinIO删除文件
        await minio_service.delete_file(
            bucket_name=file.minio_bucket, object_key=file.minio_object_key
        )

        # 标记为已删除
        setattr(file, "is_deleted", True)

        # 更新仓库统计
        repository = file.repository
        repository.total_files = max(0, repository.total_files - 1)
        repository.total_size = max(0, repository.total_size - file.file_size)

        await db.commit()

        return {"message": "文件已删除"}

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="删除文件失败")


@router.get("/{file_id}/stats")
async def get_file_stats(
    file_id: int = Path(..., description="文件ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取文件统计信息"""

    query = (
        select(RepositoryFile)
        .options(selectinload(RepositoryFile.repository))
        .where(and_(RepositoryFile.id == file_id, RepositoryFile.is_deleted == False))
    )

    result = await db.execute(query)
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查访问权限
    if file.repository.visibility == "private":
        if not current_user or (
            file.repository.owner_id != current_user.id
            and not getattr(current_user, "is_admin", False)
        ):
            raise HTTPException(status_code=403, detail="无权限访问此文件")

    return {
        "file_id": file.id,
        "filename": file.filename,
        "file_size": file.file_size,
        "download_count": file.download_count,
        "created_at": file.created_at,
        "updated_at": file.updated_at,
        "repository": {
            "id": file.repository.id,
            "name": file.repository.name,
            "owner": file.repository.owner.username if file.repository.owner else None,
        },
    }


@router.post("/{file_id}/move")
async def move_file(
    file_id: int = Path(..., description="文件ID"),
    new_path: str = Query(..., description="新文件路径"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """移动文件"""

    query = (
        select(RepositoryFile)
        .options(selectinload(RepositoryFile.repository))
        .where(and_(RepositoryFile.id == file_id, RepositoryFile.is_deleted == False))
    )

    result = await db.execute(query)
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查权限
    if file.repository.owner_id != current_user.id and not getattr(
        current_user, "is_admin", False
    ):
        raise HTTPException(status_code=403, detail="无权限移动此文件")

    # 检查目标路径是否存在
    existing_query = select(RepositoryFile).where(
        and_(
            RepositoryFile.repository_id == file.repository_id,
            RepositoryFile.file_path == new_path,
            RepositoryFile.is_deleted == False,
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="目标路径已存在文件")

    # 更新文件路径
    old_path = file.file_path
    setattr(file, "file_path", new_path)

    await db.commit()

    return {"message": "文件已移动", "old_path": old_path, "new_path": new_path}


@router.post("/{file_id}/copy")
async def copy_file(
    file_id: int = Path(..., description="文件ID"),
    new_path: str = Query(..., description="新文件路径"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """复制文件"""

    query = (
        select(RepositoryFile)
        .options(selectinload(RepositoryFile.repository))
        .where(and_(RepositoryFile.id == file_id, RepositoryFile.is_deleted == False))
    )

    result = await db.execute(query)
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查权限
    if file.repository.owner_id != current_user.id and not getattr(
        current_user, "is_admin", False
    ):
        raise HTTPException(status_code=403, detail="无权限复制此文件")

    # 检查目标路径是否存在
    existing_query = select(RepositoryFile).where(
        and_(
            RepositoryFile.repository_id == file.repository_id,
            RepositoryFile.file_path == new_path,
            RepositoryFile.is_deleted == False,
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="目标路径已存在文件")

    try:
        # 在MinIO中复制文件
        new_object_name = f"{file.repository.full_name}/{new_path}"
        await minio_service.copy_file(
            source_bucket=getattr(file, "minio_bucket"),
            source_object=file.minio_object_name,
            dest_bucket=getattr(file, "minio_bucket"),
            dest_object=new_object_name,
        )

        # 创建新的文件记录
        new_file = RepositoryFile(
            repository_id=file.repository_id,
            filename=new_path.split("/")[-1],
            file_path=new_path,
            file_type=file.file_type,
            content_type=file.content_type,
            file_size=file.file_size,
            file_hash=file.file_hash,
            minio_bucket=file.minio_bucket,
            minio_object_name=new_object_name,
        )

        db.add(new_file)

        # 更新仓库统计
        repository = file.repository
        repository.total_files += 1
        repository.total_size += file.file_size

        await db.commit()

        return {
            "message": "文件已复制",
            "original_file_id": file_id,
            "new_file_id": new_file.id,
            "new_path": new_path,
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to copy file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="复制文件失败")


@router.get("/search")
async def search_files(
    q: str = Query(..., description="搜索关键词"),
    file_type: Optional[str] = Query(None, description="文件类型"),
    repository_id: Optional[int] = Query(None, description="仓库ID"),
    size_min: Optional[int] = Query(None, description="最小文件大小"),
    size_max: Optional[int] = Query(None, description="最大文件大小"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """搜索文件"""

    # 基础查询
    query = (
        select(RepositoryFile)
        .options(selectinload(RepositoryFile.repository).selectinload(Repository.owner))
        .join(Repository)
        .where(and_(RepositoryFile.is_deleted == False, Repository.is_active == True))
    )

    # 权限过滤：只显示公开仓库的文件或用户自己的文件
    if current_user:
        if not getattr(current_user, "is_admin", False):
            query = query.where(
                or_(
                    Repository.visibility == "public",
                    Repository.owner_id == current_user.id,
                )
            )
    else:
        query = query.where(Repository.visibility == "public")

    # 搜索条件
    search_pattern = f"%{q}%"
    query = query.where(
        or_(
            RepositoryFile.filename.ilike(search_pattern),
            RepositoryFile.file_path.ilike(search_pattern),
        )
    )

    if file_type:
        query = query.where(RepositoryFile.file_type == file_type)

    if repository_id:
        query = query.where(RepositoryFile.repository_id == repository_id)

    if size_min is not None:
        query = query.where(RepositoryFile.file_size >= size_min)

    if size_max is not None:
        query = query.where(RepositoryFile.file_size <= size_max)

    # 按相关度排序（文件名匹配优先）
    query = query.order_by(
        RepositoryFile.filename.ilike(search_pattern).desc(),
        desc(RepositoryFile.created_at),
    )

    # 分页
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    files = result.scalars().all()

    # 获取总数（不带分页）
    count_query = (
        select(func.count(RepositoryFile.id))
        .join(Repository)
        .where(and_(RepositoryFile.is_deleted == False, Repository.is_active == True))
    )

    # 权限过滤
    if current_user:
        if not getattr(current_user, "is_admin", False):
            count_query = count_query.where(
                or_(
                    Repository.visibility == "public",
                    Repository.owner_id == current_user.id,
                )
            )
    else:
        count_query = count_query.where(Repository.visibility == "public")

    # 应用搜索条件
    search_pattern = f"%{q}%"
    count_query = count_query.where(
        or_(
            RepositoryFile.filename.ilike(search_pattern),
            RepositoryFile.file_path.ilike(search_pattern),
        )
    )

    if file_type:
        count_query = count_query.where(RepositoryFile.file_type == file_type)

    if repository_id:
        count_query = count_query.where(RepositoryFile.repository_id == repository_id)

    if size_min is not None:
        count_query = count_query.where(RepositoryFile.file_size >= size_min)

    if size_max is not None:
        count_query = count_query.where(RepositoryFile.file_size <= size_max)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return {
        "files": files,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
        "query": q,
    }

