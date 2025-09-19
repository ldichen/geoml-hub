from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_async_db
from datetime import datetime, timezone, timedelta
import logging
from app.models import (
    Repository,
    RepositoryFile,
    RepositoryStar,
    User,
    RepositoryClassification,
)
from app.utils.repository_utils import enrich_repositories_with_classification_paths
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryUpdate,
    Repository as RepositorySchema,
    RepositoryListItem,
    RepositoryFile as RepositoryFileSchema,
    RepositoryStats,
    RepositoryStar as RepositoryStarSchema,
    RepositorySettings,
    RepositorySettingsUpdate,
    RepositoryListResponse,
)
from app.services.repository_service import RepositoryService
from app.services.file_upload_service import FileUploadService
from app.dependencies.auth import (
    get_current_user,
    get_current_active_user,
    require_repository_owner,
    require_repository_access,
)
from app.middleware.error_response import NotFoundError, AuthorizationError
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/test")
async def test_repositories():
    """测试端点"""
    return {"message": "Repositories API is working", "count": 1}


@router.get("/", response_model=RepositoryListResponse)
async def list_repositories(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    skip: Optional[int] = Query(None, ge=0, description="跳过数量（兼容参数）"),
    limit: Optional[int] = Query(
        None, ge=1, le=100, description="限制数量（兼容参数）"
    ),
    search: Optional[str] = Query(None, description="搜索仓库名称或描述"),
    q: Optional[str] = Query(None, description="搜索查询（兼容参数）"),
    repo_type: Optional[str] = Query(None, regex="^(model|dataset|space)$"),
    visibility: str = Query("public", regex="^(public|private|all)$"),
    classification_id: Optional[int] = Query(None, description="分类ID筛选"),
    classification_ids: Optional[List[int]] = Query(None, description="多个分类ID筛选"),
    tags: Optional[str] = Query(None, description="标签筛选，逗号分隔"),
    licenses: Optional[str] = Query(None, description="许可证筛选，逗号分隔"),
    sort_by: str = Query(
        "updated",
        regex="^(updated|updated_at|created|created_at|stars|stars_count|downloads|views)$",
    ),
    sort_order: Optional[str] = Query(
        None, regex="^(asc|desc)$", description="排序方向（兼容参数）"
    ),
    order: str = Query("desc", regex="^(asc|desc)$"),
    featured_only: bool = Query(False, description="只显示精选仓库"),
    is_featured: Optional[bool] = Query(None, description="精选仓库（兼容参数）"),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库列表"""

    # 处理兼容参数
    if skip is not None and limit is not None:
        # 使用旧的 skip/limit 方式计算 page
        page = (skip // limit) + 1 if limit > 0 else 1
        per_page = limit
    if q is not None:
        search = q
    if sort_order is not None:
        order = sort_order
    if is_featured is not None:
        featured_only = is_featured

    # 计算实际的 skip 值
    calculated_skip = (page - 1) * per_page

    # 处理排序字段映射
    sort_field_map = {
        "updated_at": "updated",
        "created_at": "created",
        "stars_count": "stars",
    }
    sort_by = sort_field_map.get(sort_by, sort_by)

    query = select(Repository).where(Repository.is_active == True)

    # 可见性筛选 - 非认证用户只能看公开仓库
    if visibility != "all":
        query = query.where(Repository.visibility == visibility)
    else:
        # 默认只显示公开仓库，除非是管理员
        query = query.where(Repository.visibility == "public")

    # 搜索
    if search:
        query = query.where(
            or_(
                Repository.name.ilike(f"%{search}%"),
                Repository.description.ilike(f"%{search}%"),
                Repository.full_name.ilike(f"%{search}%"),
            )
        )

    # 仓库类型筛选
    if repo_type:
        query = query.where(Repository.repo_type == repo_type)

    # 分类筛选
    if classification_id:
        # Convert single classification to list for unified handling
        classification_ids = [classification_id]

    # 多分类筛选 (OR 关系)
    if classification_ids:
        # Use EXISTS subquery instead of JOIN to avoid potential issues
        subquery = select(RepositoryClassification.repository_id).where(
            RepositoryClassification.classification_id.in_(classification_ids)
        )
        query = query.where(Repository.id.in_(subquery))

    # 标签筛选
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.where(Repository.tags.any(tag))

    # 许可证筛选
    if licenses:
        license_list = [license.strip() for license in licenses.split(",")]
        query = query.where(Repository.license.in_(license_list))

    # 精选筛选
    if featured_only:
        query = query.where(Repository.is_featured == True)

    # 排序
    sort_field = {
        "updated": Repository.updated_at,
        "created": Repository.created_at,
        "stars": Repository.stars_count,
        "downloads": Repository.downloads_count,
        "views": Repository.views_count,
    }[sort_by]

    if order == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)

    # 获取总数（在应用分页之前）
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # 分页
    query = query.offset(calculated_skip).limit(per_page)

    # 加载关联数据
    query = query.options(selectinload(Repository.owner))

    result = await db.execute(query)
    repositories = result.scalars().all()

    # 丰富仓库数据
    enriched_repositories = await enrich_repositories_with_classification_paths(
        repositories, db
    )

    # 计算分页信息
    total_pages = (total + per_page - 1) // per_page  # 向上取整
    has_next = page < total_pages
    has_prev = page > 1

    return RepositoryListResponse(
        items=enriched_repositories,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
    )


@router.get("/{owner}/{repo_name}", response_model=RepositorySchema)
async def get_repository(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库详情"""
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    # 检查私有仓库访问权限
    if getattr(repository, "visibility") == "private":
        if not current_user or getattr(current_user, "username") != owner:
            raise AuthorizationError("无权访问私有仓库")

    # 记录访问 - 暂时禁用view记录功能
    # TODO: 修复RepositoryView表相关问题
    # try:
    #     user_id = getattr(current_user, "id") if current_user else None
    #     await repo_service.record_view(
    #         getattr(repository, "id"), user_id=user_id, ip_address="127.0.0.1"
    #     )
    # except Exception as e:
    #     # 记录访问失败不应该影响仓库获取
    #     print(f"Failed to record view: {e}")
    #     pass

    # 添加分类路径信息 - 手动添加而不使用列表专用的enrich函数
    try:
        from app.services.classification import ClassificationService
        from app.models import RepositoryClassification
        from sqlalchemy import select

        classification_service = ClassificationService(db)

        # 获取仓库的分类关联
        classification_query = (
            select(RepositoryClassification)
            .where(RepositoryClassification.repository_id == repository.id)
            .order_by(RepositoryClassification.level.desc())
        )

        result = await db.execute(classification_query)
        repo_classifications = result.scalars().all()

        # 获取最深层级的分类路径
        classification_path = []
        if repo_classifications:
            # 取第一个（最深层级的）分类
            deepest_classification = repo_classifications[0]
            classification_path = await classification_service.get_classification_path(
                deepest_classification.classification_id
            )

        # 创建包含分类路径的仓库数据
        repo_dict = repository.__dict__.copy()
        repo_dict["classification_path"] = classification_path

        # 返回原始仓库对象，但添加classification_path属性
        setattr(repository, "classification_path", classification_path)

    except Exception as e:
        logger.error(f"Failed to add classification path: {e}")

    return repository


@router.get("/{owner}/{repo_name}/files", response_model=List[RepositoryFileSchema])
async def list_repository_files(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    path: Optional[str] = Query("", description="文件路径前缀"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库文件列表"""
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    # 检查私有仓库访问权限
    if getattr(repository, "visibility") == "private":
        if not current_user or getattr(current_user, "username") != owner:
            raise AuthorizationError("无权访问私有仓库文件")

    query = select(RepositoryFile).where(
        and_(
            RepositoryFile.repository_id == repository.id,
            RepositoryFile.is_deleted == False,
        )
    )

    if path:
        query = query.where(RepositoryFile.file_path.startswith(path))

    query = query.offset(skip).limit(limit).order_by(RepositoryFile.file_path)

    result = await db.execute(query)
    files = result.scalars().all()

    return files


@router.get("/{owner}/{repo_name}/stars", response_model=List[RepositoryStarSchema])
async def list_repository_stars(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库收藏者列表"""
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    # 检查私有仓库访问权限
    if getattr(repository, "visibility") == "private":
        if not current_user or getattr(current_user, "username") != owner:
            raise AuthorizationError("无权访问私有仓库信息")

    query = (
        select(RepositoryStar)
        .where(RepositoryStar.repository_id == repository.id)
        .options(selectinload(RepositoryStar.user))
        .offset(skip)
        .limit(limit)
        .order_by(desc(RepositoryStar.created_at))
    )

    result = await db.execute(query)
    stars = result.scalars().all()

    return stars


@router.get("/{owner}/{repo_name}/stats", response_model=RepositoryStats)
async def get_repository_stats(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库统计信息"""
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    # 检查私有仓库访问权限
    if getattr(repository, "visibility") == "private":
        if not current_user or getattr(current_user, "username") != owner:
            raise AuthorizationError("无权访问私有仓库统计")

    stats = await repo_service.get_repository_stats(getattr(repository, "id"))
    return stats


@router.post("/", response_model=RepositorySchema)
async def create_repository(
    repo_data: RepositoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """创建新仓库 - 需要认证"""
    repo_service = RepositoryService(db)
    repository = await repo_service.create_repository(
        owner_id=getattr(current_user, "id"), repo_data=repo_data
    )
    return repository


async def parse_repo_data_from_form(
    repo_data: str = Form(..., description="仓库数据JSON字符串")
) -> RepositoryCreate:
    """从FormData中解析仓库数据的依赖项"""
    import json
    from pydantic import ValidationError

    try:
        # 解析JSON字符串为字典
        repo_data_dict = json.loads(repo_data)
        # 验证并创建RepositoryCreate对象
        return RepositoryCreate(**repo_data_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="仓库数据格式错误：无效的JSON")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"仓库数据验证失败：{e}")


@router.post("/with-readme", response_model=RepositorySchema)
async def create_repository_with_readme(
    repo_data: RepositoryCreate = Depends(parse_repo_data_from_form),
    readme_file: UploadFile = File(..., description="README.md文件"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """创建带README.md文件的新仓库 - 需要认证"""
    repo_service = RepositoryService(db)
    repository = await repo_service.create_repository_with_readme_file(
        owner_id=getattr(current_user, "id"),
        repo_data=repo_data,
        readme_file=readme_file,
    )
    return repository


@router.put("/{owner}/{repo_name}", response_model=RepositorySchema)
async def update_repository(
    repo_data: RepositoryUpdate,
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """更新仓库信息 - 需要仓库所有者权限"""
    # 验证用户是否是仓库所有者
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以更新仓库信息")

    repo_service = RepositoryService(db)
    repository = await repo_service.update_repository(f"{owner}/{repo_name}", repo_data)

    # 如果更新数据中包含classification_id，则更新仓库分类
    if (
        hasattr(repo_data, "classification_id")
        and repo_data.classification_id is not None
    ):
        # 先移除现有分类
        await repo_service.remove_repository_classification(getattr(repository, "id"))

        # 添加新分类
        await repo_service.add_repository_classification(
            getattr(repository, "id"), repo_data.classification_id
        )

    return repository


@router.post("/{owner}/{repo_name}/star")
async def star_repository(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """收藏仓库 - 需要认证"""
    repo_service = RepositoryService(db)
    await repo_service.star_repository(
        user_id=getattr(current_user, "id"), repository_full_name=f"{owner}/{repo_name}"
    )
    return {"message": f"已收藏仓库 {owner}/{repo_name}"}


@router.delete("/{owner}/{repo_name}/star")
async def unstar_repository(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """取消收藏仓库 - 需要认证"""
    repo_service = RepositoryService(db)
    await repo_service.unstar_repository(
        user_id=getattr(current_user, "id"), repository_full_name=f"{owner}/{repo_name}"
    )
    return {"message": f"已取消收藏仓库 {owner}/{repo_name}"}


@router.post("/{owner}/{repo_name}/check-upload")
async def check_upload_conflict(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    file_path: str = Query(..., description="文件在仓库中的路径"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """检查文件上传是否有冲突"""
    repo_service = RepositoryService(db)

    # 检查仓库是否存在
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")
    if not repository:
        raise HTTPException(status_code=404, detail="仓库不存在")

    # 验证用户是否是仓库所有者
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以上传文件")

    # 检查上传冲突
    conflict_result = await repo_service.check_upload_conflict(
        repository_id=getattr(repository, "id"), file_path=file_path
    )
    return conflict_result


@router.post("/{owner}/{repo_name}/upload")
async def upload_file(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    file: UploadFile = File(...),
    file_path: str = Query(..., description="文件在仓库中的路径"),
    confirmed: bool = Query(False, description="是否已确认替换特殊文件"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """上传文件到仓库"""
    repo_service = RepositoryService(db)

    # 检查仓库是否存在
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")
    if not repository:
        raise HTTPException(status_code=404, detail="仓库不存在")

    # 验证用户是否是仓库所有者
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以上传文件")

    # 上传文件
    upload_result = await repo_service.upload_file(
        repository_id=getattr(repository, "id"),
        file=file,
        file_path=file_path,
        confirmed=confirmed,
    )

    # 返回详细的上传信息
    return {
        "message": upload_result["message"],
        "file": upload_result["file"],
        "upload_info": {
            "original_filename": upload_result["original_filename"],
            "final_filename": upload_result["final_filename"],
            "action": upload_result["action"],
        },
    }


@router.post("/{owner}/{repo_name}/upload/init")
async def init_file_upload(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    file_name: str = Query(..., description="文件名"),
    file_size: int = Query(..., description="文件大小（字节）"),
    file_path: str = Query(..., description="文件在仓库中的路径"),
    content_type: Optional[str] = Query(None, description="文件类型"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """初始化文件上传会话 - 支持大文件分片上传"""
    # 验证用户权限
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以上传文件")

    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    upload_service = FileUploadService(db)
    session_info = await upload_service.initiate_upload_session(
        repository_id=getattr(repository, "id"),
        file_name=file_name,
        file_size=file_size,
        file_path=file_path,
        content_type=content_type,
        user_id=getattr(current_user, "id"),
    )

    return session_info


@router.post("/{owner}/{repo_name}/upload/{session_id}/chunk/{chunk_number}")
async def upload_file_chunk(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    session_id: int = Path(..., description="上传会话ID"),
    chunk_number: int = Path(..., description="分片编号"),
    file: UploadFile = File(...),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """上传文件分片"""
    # 验证用户权限
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以上传文件")

    # 读取分片数据
    chunk_data = await file.read()

    upload_service = FileUploadService(db)
    result = await upload_service.upload_chunk(
        session_id=session_id, chunk_number=chunk_number, chunk_data=chunk_data
    )

    return result


@router.post("/{owner}/{repo_name}/upload/{session_id}/complete")
async def complete_file_upload(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    session_id: int = Path(..., description="上传会话ID"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """完成文件上传"""
    # 验证用户权限
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以上传文件")

    upload_service = FileUploadService(db)
    result = await upload_service.complete_upload(session_id)

    return result


@router.delete("/{owner}/{repo_name}/upload/{session_id}")
async def abort_file_upload(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    session_id: int = Path(..., description="上传会话ID"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """取消文件上传"""
    # 验证用户权限
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以上传文件")

    upload_service = FileUploadService(db)
    await upload_service.abort_upload(session_id)

    return {"message": "文件上传已取消"}


@router.get("/{owner}/{repo_name}/upload/{session_id}/status")
async def get_upload_status(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    session_id: int = Path(..., description="上传会话ID"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """获取上传状态"""
    # 验证用户权限
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以查看上传状态")

    upload_service = FileUploadService(db)
    status = await upload_service.get_upload_status(session_id)

    return status


@router.get("/{owner}/{repo_name}/download/{file_path:path}")
async def download_file(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    file_path: str = Path(..., description="文件路径"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """下载仓库文件"""
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    # 检查私有仓库访问权限
    if getattr(repository, "visibility") == "private":
        if not current_user or getattr(current_user, "username") != owner:
            raise AuthorizationError("无权下载私有仓库文件")

    # 查找文件
    query = select(RepositoryFile).where(
        and_(
            RepositoryFile.repository_id == repository.id,
            RepositoryFile.file_path == file_path,
            RepositoryFile.is_deleted == False,
        )
    )
    result = await db.execute(query)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise NotFoundError("文件不存在")

    # 记录下载并获取下载URL
    user_id = getattr(current_user, "id") if current_user else None
    download_url = await repo_service.download_file(
        file_id=getattr(file_record, "id"), user_id=user_id, ip_address="127.0.0.1"
    )

    return {
        "download_url": download_url,
        "file_name": getattr(file_record, "filename"),
        "file_size": getattr(file_record, "file_size"),
        "content_type": getattr(file_record, "mime_type"),
        "expires_in": 3600,
    }


@router.get("/{owner}/{repo_name}/raw/{file_path:path}")
async def serve_file_directly(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    file_path: str = Path(..., description="文件路径"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """直接提供文件内容（主要用于README中的图片显示）"""
    from app.dependencies.minio import get_minio_service
    from fastapi.responses import Response

    # 获取 MinIO 服务
    minio_service = get_minio_service()

    try:
        # 获取仓库
        repo_service = RepositoryService(db)
        repository = await repo_service.get_repository_by_full_name(
            f"{owner}/{repo_name}"
        )

        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 检查私有仓库访问权限
        if repository.visibility == "private":
            if not current_user or current_user.username != owner:
                raise HTTPException(status_code=403, detail="无权访问私有仓库文件")

        # 查找文件
        query = select(RepositoryFile).where(
            and_(
                RepositoryFile.repository_id == repository.id,
                RepositoryFile.file_path == file_path,
                RepositoryFile.is_deleted == False,
            )
        )

        result = await db.execute(query)
        file_obj = result.scalar_one_or_none()

        if not file_obj:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 从MinIO获取文件内容
        try:
            file_content = await minio_service.get_file_content(
                bucket_name=file_obj.minio_bucket, object_key=file_obj.minio_object_key
            )

            # 设置适当的Content-Type
            content_type = file_obj.mime_type or "application/octet-stream"

            # 返回文件内容
            return Response(
                content=file_content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"inline; filename={file_obj.filename}",
                    "Cache-Control": "public, max-age=3600",  # 缓存1小时
                },
            )

        except Exception as e:
            logger.error(f"Error reading file from MinIO: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"读取文件内容失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in serve_file_directly: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")


@router.get("/{owner}/{repo_name}/blob/{file_path:path}")
async def get_file_content(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    file_path: str = Path(..., description="文件路径"),
    version: Optional[str] = Query("latest", description="文件版本"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取文件内容（用于文件查看页面）"""
    from app.dependencies.minio import get_minio_service

    # 获取 MinIO 服务
    minio_service = get_minio_service()

    try:
        # 获取仓库
        repo_service = RepositoryService(db)
        repository = await repo_service.get_repository_by_full_name(
            f"{owner}/{repo_name}"
        )

        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 检查私有仓库访问权限
        if repository.visibility == "private":
            if not current_user or current_user.username != owner:
                raise HTTPException(status_code=403, detail="无权访问私有仓库文件")

        # 查找文件
        query = select(RepositoryFile).where(
            and_(
                RepositoryFile.repository_id == repository.id,
                RepositoryFile.file_path == file_path,
                RepositoryFile.is_deleted == False,
            )
        )

        result = await db.execute(query)
        file_obj = result.scalar_one_or_none()

        if not file_obj:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 从MinIO获取文件内容
        try:
            # 获取文件内容 - 使用正确的参数名
            file_content = await minio_service.get_file_content(
                bucket_name=file_obj.minio_bucket, object_key=file_obj.minio_object_key
            )

            # 尝试解码为文本（用于文本文件）
            content_text = None
            is_text_file = False

            try:
                # 检查是否为文本文件 - 使用正确的字段名
                if file_obj.mime_type and file_obj.mime_type.startswith("text/"):
                    content_text = file_content.decode("utf-8")
                    is_text_file = True
                elif file_obj.filename.endswith(
                    (
                        ".md",
                        ".txt",
                        ".py",
                        ".js",
                        ".ts",
                        ".json",
                        ".yaml",
                        ".yml",
                        ".xml",
                        ".csv",
                    )
                ):
                    content_text = file_content.decode("utf-8")
                    is_text_file = True
            except UnicodeDecodeError:
                # 不是文本文件或编码问题
                pass

            return {
                "id": file_obj.id,
                "filename": file_obj.filename,
                "file_path": file_obj.file_path,
                "file_type": file_obj.file_type,
                "mime_type": file_obj.mime_type,  # 正确的字段名
                "file_size": file_obj.file_size,
                "content": content_text,
                "is_text_file": is_text_file,
                "download_count": file_obj.download_count,
                "created_at": file_obj.created_at,
                "updated_at": file_obj.updated_at,
                "repository": {
                    "id": repository.id,
                    "name": repository.name,
                    "full_name": repository.full_name,
                    "owner": {
                        "username": (
                            repository.owner.username if repository.owner else owner
                        )
                    },
                },
            }

        except Exception as e:
            logger.error(f"Error reading file from MinIO: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"读取文件内容失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_file_content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文件内容失败: {str(e)}")


from pydantic import BaseModel


class FileUpdateRequest(BaseModel):
    content: str
    commit_message: str


@router.put("/{owner}/{repo_name}/blob/{file_path:path}")
async def update_file_content(
    request: FileUpdateRequest,
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    file_path: str = Path(..., description="文件路径"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """更新文件内容"""
    from app.dependencies.minio import get_minio_service
    import io
    from datetime import datetime

    # 获取 MinIO 服务
    minio_service = get_minio_service()

    try:
        # 获取仓库
        repo_service = RepositoryService(db)
        repository = await repo_service.get_repository_by_full_name(
            f"{owner}/{repo_name}"
        )

        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 检查权限（暂时简化，实际应该检查用户是否有写权限）
        if repository.visibility == "private":
            if not current_user or current_user.username != owner:
                raise HTTPException(status_code=403, detail="无权修改此仓库文件")

        # 查找文件
        query = select(RepositoryFile).where(
            and_(
                RepositoryFile.repository_id == repository.id,
                RepositoryFile.file_path == file_path,
                RepositoryFile.is_deleted == False,
            )
        )

        result = await db.execute(query)
        file_obj = result.scalar_one_or_none()

        if not file_obj:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 将内容转换为字节
        content_bytes = request.content.encode("utf-8")
        content_size = len(content_bytes)

        # 上传新内容到MinIO
        await minio_service.upload_file_stream(
            bucket_name=file_obj.minio_bucket,
            object_key=file_obj.minio_object_key,
            file_stream=io.BytesIO(content_bytes),
            file_size=content_size,
            content_type=file_obj.mime_type or "text/plain",
        )

        # 更新数据库记录
        file_obj.file_size = content_size
        file_obj.updated_at = datetime.utcnow()

        # 更新仓库的最后修改时间
        repository.updated_at = datetime.utcnow()
        repository.last_commit_message = request.commit_message
        repository.last_commit_at = datetime.utcnow()

        # 如果更新的是README.md文件，同步metadata到数据库
        if file_path.lower() in ["readme.md", "README.md"]:
            from app.services.metadata_sync_service import MetadataSyncService

            metadata_sync = MetadataSyncService(db)
            # 更新数据库中的readme_content字段
            repository.readme_content = request.content
            # 同步YAML frontmatter到数据库字段
            await metadata_sync.sync_readme_to_repository(repository, request.content)

        # 提交数据库更改
        await db.commit()

        logger.info(f"File updated successfully: {owner}/{repo_name}/{file_path}")

        return {
            "success": True,
            "message": "文件更新成功",
            "file_info": {
                "id": file_obj.id,
                "filename": file_obj.filename,
                "file_path": file_obj.file_path,
                "file_size": file_obj.file_size,
                "updated_at": file_obj.updated_at.isoformat(),
            },
            "commit_info": {
                "commit_message": request.commit_message,
                "committed_at": repository.last_commit_at.isoformat(),
                "author": current_user.username if current_user else owner,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file content: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新文件失败: {str(e)}")


@router.delete("/{owner}/{repo_name}")
async def delete_repository(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """删除仓库 - 需要仓库所有者权限"""
    # 验证用户是否是仓库所有者
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以删除仓库")

    repo_service = RepositoryService(db)
    await repo_service.delete_repository(f"{owner}/{repo_name}")

    return {"message": f"仓库 {owner}/{repo_name} 已删除"}


@router.get("/{owner}/{repo_name}/classifications")
async def get_repository_classifications(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库分类信息"""
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    # 检查私有仓库访问权限
    if getattr(repository, "visibility") == "private":
        if not current_user or getattr(current_user, "username") != owner:
            raise AuthorizationError("无权访问私有仓库信息")

    classifications = await repo_service.get_repository_classifications(
        getattr(repository, "id")
    )
    return {"classifications": classifications}


@router.post("/{owner}/{repo_name}/classifications")
async def add_repository_classification(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    classification_id: int = Query(..., description="要添加的分类ID"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """为仓库添加分类 - 需要仓库所有者权限"""
    # 验证用户是否是仓库所有者
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以修改仓库分类")

    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    classifications = await repo_service.add_repository_classification(
        getattr(repository, "id"), classification_id
    )

    return {"message": "分类添加成功", "classifications": classifications}


@router.delete("/{owner}/{repo_name}/classifications")
async def remove_repository_classifications(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """移除仓库的所有分类关联 - 需要仓库所有者权限"""
    # 验证用户是否是仓库所有者
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以修改仓库分类")

    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    success = await repo_service.remove_repository_classification(
        getattr(repository, "id")
    )

    if success:
        return {"message": "仓库分类已全部移除"}
    else:
        raise HTTPException(status_code=400, detail="移除分类失败")


@router.get("/{owner}/{repo_name}/settings", response_model=RepositorySettings)
async def get_repository_settings(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库设置 - 需要仓库所有者权限"""
    # 验证用户是否是仓库所有者
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以查看仓库设置")

    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    return {
        "name": repository.name,
        "description": repository.description,
        "visibility": repository.visibility,
        "tags": repository.tags or [],
        "license": repository.license,
        "repo_type": repository.repo_type,
        "is_featured": repository.is_featured,
    }


@router.put("/{owner}/{repo_name}/settings", response_model=RepositorySettings)
async def update_repository_settings(
    settings_data: RepositorySettingsUpdate,
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """更新仓库设置 - 需要仓库所有者权限"""
    # 验证用户是否是仓库所有者
    if getattr(current_user, "username") != owner:
        raise AuthorizationError("只有仓库所有者可以修改仓库设置")

    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    # 更新仓库设置
    update_data = settings_data.model_dump(exclude_unset=True)
    updated_repository = await repo_service.update_repository(
        full_name=f"{owner}/{repo_name}", repo_data=RepositoryUpdate(**update_data)
    )

    return {
        "name": updated_repository.name,
        "description": updated_repository.description,
        "visibility": updated_repository.visibility,
        "tags": updated_repository.tags or [],
        "license": updated_repository.license,
        "repo_type": updated_repository.repo_type,
        "is_featured": updated_repository.is_featured,
    }


@router.get("/{owner}/{repo_name}/tree/main")
async def get_repository_file_tree(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库文件树结构"""
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    # 检查私有仓库访问权限
    if getattr(repository, "visibility") == "private":
        if not current_user or getattr(current_user, "username") != owner:
            raise AuthorizationError("无权访问私有仓库")

    # 查询所有文件
    query = (
        select(RepositoryFile)
        .where(
            and_(
                RepositoryFile.repository_id == repository.id,
                RepositoryFile.is_deleted == False,
            )
        )
        .order_by(RepositoryFile.file_path)
    )

    result = await db.execute(query)
    files = result.scalars().all()

    # 构建文件树结构
    file_tree = {}

    for file in files:
        path_parts = file.file_path.split("/")
        current_node = file_tree

        # 构建目录结构
        for i, part in enumerate(path_parts[:-1]):
            if part not in current_node:
                current_node[part] = {"type": "directory", "children": {}}
            current_node = current_node[part]["children"]

        # 添加文件
        filename = path_parts[-1]
        current_node[filename] = {
            "type": "file",
            "file_id": file.id,
            "file_path": file.file_path,
            "file_size": file.file_size,
            "mime_type": file.mime_type,
            "created_at": file.created_at.isoformat(),
            "updated_at": file.updated_at.isoformat(),
        }

    return {
        "repository": {
            "name": repository.name,
            "full_name": repository.full_name,
            "total_files": repository.total_files,
            "total_size": repository.total_size,
        },
        "tree": file_tree,
    }


@router.get("/{owner}/{repo_name}/tree/main/{path:path}")
async def get_repository_path_content(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    path: str = Path(..., description="文件或目录路径"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库指定路径的内容"""
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(f"{owner}/{repo_name}")

    if not repository:
        raise NotFoundError("仓库不存在")

    # 检查私有仓库访问权限
    if getattr(repository, "visibility") == "private":
        if not current_user or getattr(current_user, "username") != owner:
            raise AuthorizationError("无权访问私有仓库")

    # 查询指定路径的文件或目录
    query = (
        select(RepositoryFile)
        .where(
            and_(
                RepositoryFile.repository_id == repository.id,
                RepositoryFile.is_deleted == False,
                or_(
                    RepositoryFile.file_path == path,  # 精确匹配文件
                    RepositoryFile.file_path.like(f"{path}/%"),  # 匹配子目录
                ),
            )
        )
        .order_by(RepositoryFile.file_path)
    )

    result = await db.execute(query)
    files = result.scalars().all()

    if not files:
        raise NotFoundError("路径不存在")

    # 检查是否是单个文件
    exact_file = next((f for f in files if str(f.file_path) == str(path)), None)
    if exact_file:
        return {
            "type": "file",
            "file_id": exact_file.id,
            "file_path": exact_file.file_path,
            "filename": exact_file.filename,
            "file_size": exact_file.file_size,
            "mime_type": exact_file.mime_type,
            "created_at": exact_file.created_at.isoformat(),
            "updated_at": exact_file.updated_at.isoformat(),
        }

    # 构建目录内容
    directory_contents = []
    processed_dirs = set()

    for file in files:
        relative_path = file.file_path[len(path) :].lstrip("/")
        if "/" in relative_path:
            # 这是子目录中的文件
            dir_name = relative_path.split("/")[0]
            if dir_name not in processed_dirs:
                processed_dirs.add(dir_name)
                directory_contents.append(
                    {
                        "type": "directory",
                        "name": dir_name,
                        "path": f"{path}/{dir_name}".lstrip("/"),
                    }
                )
        else:
            # 这是当前目录中的文件
            directory_contents.append(
                {
                    "type": "file",
                    "name": relative_path,
                    "file_id": file.id,
                    "file_path": file.file_path,
                    "file_size": file.file_size,
                    "mime_type": file.mime_type,
                    "created_at": file.created_at.isoformat(),
                    "updated_at": file.updated_at.isoformat(),
                }
            )

    return {"type": "directory", "path": path, "contents": directory_contents}


@router.get("/{owner}/{repo_name}/views")
async def get_repository_views(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    period: str = Query(
        "week", regex="^(day|week|month|year|all)$", description="时间范围"
    ),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库访问统计"""

    # 验证仓库访问权限
    repository = await require_repository_access(owner, repo_name, current_user, db)

    from datetime import datetime, timedelta

    # 基础统计
    stats = {
        "repository_id": repository.id,
        "repository_name": repository.full_name,
        "total_views": repository.views_count,
        "total_stars": repository.stars_count,
        "total_downloads": repository.downloads_count,
        "period": period,
        "generated_at": datetime.now(timezone.utc),
    }

    # 如果需要详细的时间范围统计，可以在这里添加
    # 目前简化处理，返回基础统计信息
    if period != "all":
        time_ranges = {
            "day": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "year": timedelta(days=365),
        }
        since_date = datetime.now(timezone.utc) - time_ranges[period]

        # 这里可以添加更详细的时间范围统计查询
        # 目前返回基础信息
        stats["since_date"] = since_date.isoformat()

    return stats


@router.post("/{owner}/{repo_name}/view")
async def record_repository_view(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """记录仓库访问（自动调用）"""

    # 验证仓库访问权限
    repository = await require_repository_access(owner, repo_name, current_user, db)

    try:
        # 增加访问计数
        repository.views_count += 1
        await db.commit()

        return {
            "message": "访问已记录",
            "repository_id": repository.id,
            "current_views": repository.views_count,
            "recorded_at": datetime.now(timezone.utc),
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to record view for {owner}/{repo_name}: {e}")
        # 访问记录失败不应该影响用户体验，返回成功
        return {
            "message": "访问记录失败，但不影响正常使用",
            "repository_id": repository.id,
            "error": str(e),
        }


@router.post("/{owner}/{repo_name}/upload/batch")
async def batch_upload_files(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    files: List[UploadFile] = File(..., description="要上传的文件列表"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """批量上传文件"""

    # 验证仓库访问权限
    repository = await require_repository_access(owner, repo_name, current_user, db)

    # 检查上传权限
    if repository.owner_id != current_user.id and not getattr(
        current_user, "is_admin", False
    ):
        raise HTTPException(status_code=403, detail="无权限上传文件到此仓库")

    if len(files) > 10:  # 限制批量上传数量
        raise HTTPException(status_code=400, detail="批量上传文件数量不能超过10个")

    repo_service = RepositoryService(db)
    upload_results = []

    for file in files:
        try:
            # 验证文件
            if getattr(file, "size") > 10 * 1024 * 1024 * 1024:  # 10GB限制
                upload_results.append(
                    {
                        "filename": file.filename,
                        "status": "error",
                        "error": "文件大小超过10GB限制",
                    }
                )
                continue
            if file.filename is None:
                upload_results.append(
                    {
                        "filename": "unknown",
                        "status": "error",
                        "error": "文件名不能为空",
                    }
                )
                continue
            # 上传文件
            upload_result = await repo_service.upload_file(
                repository_id=getattr(repository, "id"),
                file=file,
                file_path=file.filename,  # 使用原始文件名作为路径
            )

            file_record = upload_result["file"]
            upload_results.append(
                {
                    "filename": file.filename,
                    "status": "success",
                    "file_id": file_record.id,
                    "file_path": file_record.file_path,
                    "file_size": file_record.file_size,
                    "upload_info": {
                        "original_filename": upload_result["original_filename"],
                        "final_filename": upload_result["final_filename"],
                        "action": upload_result["action"],
                        "message": upload_result["message"],
                    },
                }
            )

        except Exception as e:
            upload_results.append(
                {"filename": file.filename, "status": "error", "error": str(e)}
            )

    # 统计结果
    success_count = sum(1 for result in upload_results if result["status"] == "success")
    error_count = len(upload_results) - success_count

    return {
        "message": f"批量上传完成，成功{success_count}个，失败{error_count}个",
        "total_files": len(files),
        "success_count": success_count,
        "error_count": error_count,
        "results": upload_results,
    }


@router.get("/{owner}/{repo_name}/analytics")
async def get_repository_analytics(
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    period: str = Query(
        "month", regex="^(day|week|month|quarter|year|all)$", description="时间范围"
    ),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库详细分析数据"""

    # 验证仓库访问权限
    from app.dependencies.auth import get_repository_access

    repository = await get_repository_access(owner, repo_name, current_user, db)

    # 只有仓库所有者或管理员可以查看详细分析
    if not current_user or (
        getattr(repository, "owner_id") != current_user.id
        and not getattr(current_user, "is_admin", False)
    ):
        raise HTTPException(status_code=403, detail="无权限查看仓库分析数据")

    # 计算时间范围
    time_ranges = {
        "day": timedelta(days=1),
        "week": timedelta(days=7),
        "month": timedelta(days=30),
        "quarter": timedelta(days=90),
        "year": timedelta(days=365),
    }

    since_date = None
    if period != "all":
        since_date = datetime.now(timezone.utc) - time_ranges[period]

    # 获取仓库统计数据
    stars_count = getattr(repository, "stars_count", 0) or 0
    views_count = getattr(repository, "views_count", 0) or 0
    downloads_count = getattr(repository, "downloads_count", 0) or 0
    total_size = getattr(repository, "total_size", 0) or 0
    total_files = getattr(repository, "total_files", 0) or 0

    # 基础统计
    basic_stats = {
        "repository_id": repository.id,
        "repository_name": repository.full_name,
        "owner": owner,
        "created_at": repository.created_at,
        "updated_at": repository.updated_at,
        "total_stars": stars_count,
        "total_views": views_count,
        "total_downloads": downloads_count,
        "total_files": total_files,
        "total_size": total_size,
        "repo_type": repository.repo_type,
        "visibility": repository.visibility,
        "is_featured": repository.is_featured,
        "period": period,
        "since_date": since_date.isoformat() if since_date else None,
    }

    # 文件类型分析
    file_type_conditions = [
        RepositoryFile.repository_id == repository.id,
        RepositoryFile.is_deleted == False,
    ]
    if since_date:
        file_type_conditions.append(RepositoryFile.created_at >= since_date)

    file_type_stats = await db.execute(
        select(
            RepositoryFile.file_type,
            func.count(RepositoryFile.id).label("count"),
            func.sum(RepositoryFile.file_size).label("total_size"),
            func.avg(RepositoryFile.file_size).label("avg_size"),
            func.sum(RepositoryFile.download_count).label("total_downloads"),
        )
        .where(and_(*file_type_conditions))
        .group_by(RepositoryFile.file_type)
    )

    file_analysis = {}
    for row in file_type_stats:
        file_analysis[row.file_type or "other"] = {
            "count": row.count,
            "total_size": row.total_size or 0,
            "avg_size": row.avg_size or 0,
            "total_downloads": row.total_downloads or 0,
        }

    # 最受欢迎的文件
    popular_files_conditions = [
        RepositoryFile.repository_id == repository.id,
        RepositoryFile.is_deleted == False,
    ]
    if since_date:
        popular_files_conditions.append(RepositoryFile.created_at >= since_date)

    popular_files = await db.execute(
        select(
            RepositoryFile.filename,
            RepositoryFile.file_path,
            RepositoryFile.file_type,
            RepositoryFile.file_size,
            RepositoryFile.download_count,
        )
        .where(and_(*popular_files_conditions))
        .order_by(RepositoryFile.download_count.desc())
        .limit(10)
    )

    top_files = [
        {
            "filename": row.filename,
            "file_path": row.file_path,
            "file_type": row.file_type,
            "file_size": row.file_size,
            "download_count": row.download_count,
        }
        for row in popular_files
    ]

    # 存储使用分析
    storage_analysis = {
        "total_size": total_size,
        "total_files": total_files,
        "avg_file_size": (total_size / total_files if total_files > 0 else 0),
        "file_type_distribution": file_analysis,
        "storage_efficiency": _calculate_storage_efficiency(total_size, total_files),
        "growth_trend": _calculate_growth_trend(repository, since_date),
    }

    # 用户互动分析
    engagement_stats = {
        "stars_to_views_ratio": (stars_count / views_count if views_count > 0 else 0),
        "downloads_to_views_ratio": (
            downloads_count / views_count if views_count > 0 else 0
        ),
        "popularity_score": _calculate_popularity_score(repository),
        "engagement_level": _get_engagement_level(repository),
    }

    # 建议和优化
    recommendations = _get_repository_recommendations(
        repository, file_analysis, engagement_stats
    )

    return {
        "basic_stats": basic_stats,
        "file_analysis": file_analysis,
        "top_files": top_files,
        "storage_analysis": storage_analysis,
        "engagement_stats": engagement_stats,
        "recommendations": recommendations,
        "generated_at": datetime.now(timezone.utc),
    }


def _calculate_storage_efficiency(total_size: int, total_files: int) -> str:
    """计算存储效率"""
    if total_files == 0:
        return "无文件"

    avg_size = total_size / total_files
    if avg_size > 100 * 1024 * 1024:  # 100MB
        return "大文件为主"
    elif avg_size > 10 * 1024 * 1024:  # 10MB
        return "中等文件"
    else:
        return "小文件为主"


def _calculate_growth_trend(repository, since_date) -> str:
    """计算增长趋势"""
    if not since_date:
        return "全时段数据"

    days = (datetime.now(timezone.utc) - since_date).days
    if days > 0:
        total_size = getattr(repository, "total_size", 0) or 0
        daily_growth = total_size / days
        if daily_growth > 100 * 1024 * 1024:  # 100MB/day
            return "快速增长"
        elif daily_growth > 10 * 1024 * 1024:  # 10MB/day
            return "稳定增长"
        else:
            return "缓慢增长"
    return "无增长数据"


def _calculate_popularity_score(repository) -> float:
    """计算受欢迎程度得分"""
    # 综合评分算法
    stars_count = getattr(repository, "stars_count", 0) or 0
    views_count = getattr(repository, "views_count", 0) or 0
    downloads_count = getattr(repository, "downloads_count", 0) or 0

    stars_score = min(stars_count / 100, 1.0) * 0.4
    views_score = min(views_count / 1000, 1.0) * 0.3
    downloads_score = min(downloads_count / 500, 1.0) * 0.3

    return round((stars_score + views_score + downloads_score) * 100, 2)


def _get_engagement_level(repository) -> str:
    """获取用户互动水平"""
    stars_count = getattr(repository, "stars_count", 0) or 0
    views_count = getattr(repository, "views_count", 0) or 0
    downloads_count = getattr(repository, "downloads_count", 0) or 0

    total_interactions = stars_count + views_count + downloads_count

    if total_interactions > 10000:
        return "高度活跃"
    elif total_interactions > 1000:
        return "中等活跃"
    elif total_interactions > 100:
        return "低度活跃"
    else:
        return "较少互动"


def _get_repository_recommendations(
    repository, file_analysis: dict, engagement_stats: dict
) -> List[str]:
    """生成仓库优化建议"""
    recommendations = []

    # 存储优化建议
    total_size = getattr(repository, "total_size", 0) or 0
    total_files = getattr(repository, "total_files", 0) or 0

    if total_size > 1 * 1024 * 1024 * 1024:  # 1GB
        recommendations.append("仓库体积较大，建议使用Git LFS管理大文件")

    if total_files > 1000:
        recommendations.append("文件数量较多，建议整理目录结构")

    # 互动优化建议
    if engagement_stats["stars_to_views_ratio"] < 0.05:
        recommendations.append("星标率较低，建议优化仓库描述和README")

    if engagement_stats["downloads_to_views_ratio"] < 0.1:
        recommendations.append("下载率较低，建议提供更清晰的使用说明")

    # 内容建议
    description = getattr(repository, "description", None)
    readme_content = getattr(repository, "readme_content", None)
    is_featured = getattr(repository, "is_featured", False)

    if not description:
        recommendations.append("建议添加仓库描述以提高可发现性")

    if not readme_content:
        recommendations.append("建议添加README文件以介绍仓库内容")

    # 分类建议
    if not is_featured and engagement_stats["popularity_score"] > 70:
        recommendations.append("仓库表现优秀，可申请推荐展示")

    if len(recommendations) == 0:
        recommendations.append("仓库状态良好，继续保持")

    return recommendations


@router.post("/{owner}/{repo_name}/files/rename")
async def rename_file(
    rename_data: dict,
    owner: str = Path(..., description="仓库所有者用户名"),
    repo_name: str = Path(..., description="仓库名称"),
    current_user: User = Depends(require_repository_owner),
    db: AsyncSession = Depends(get_async_db),
):
    """重命名仓库中的文件"""

    try:
        # 检查仓库是否存在
        repo_service = RepositoryService(db)
        repository = await repo_service.get_repository_by_full_name(
            f"{owner}/{repo_name}"
        )
        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 验证用户是否是仓库所有者
        if getattr(current_user, "username") != owner:
            raise AuthorizationError("只有仓库所有者可以重命名文件")

        # 获取请求参数
        old_path = rename_data.get("old_path", "")
        new_filename = rename_data.get("new_filename", "")
        commit_message = rename_data.get(
            "commit_message", f"重命名文件: {old_path} -> {new_filename}"
        )

        if not old_path or not new_filename:
            raise HTTPException(
                status_code=400, detail="old_path 和 new_filename 不能为空"
            )

        # 调用 service 层方法
        result = await repo_service.rename_file(
            repository_id=repository.id,
            old_path=old_path,
            new_filename=new_filename,
            commit_message=commit_message,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件重命名失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件重命名失败: {str(e)}")
