"""
模型服务管理API路由

这个模块提供了模型服务管理的所有API端点：
- 服务的CRUD操作
- 服务生命周期控制（启动、停止、重启）
- 服务状态监控和健康检查
- 批量操作和访问管理
"""

import logging
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.database import get_async_db
from app.dependencies.auth import get_current_user, get_current_user_required
from app.models.user import User
from app.models.repository import Repository
from app.models.service import ModelService, ServiceLog, ServiceHealthCheck
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
    ServiceStartRequest,
    ServiceStopRequest,
    ServiceStatusResponse,
    ServiceLogListResponse,
    ServiceHealthCheckListResponse,
    BatchServiceRequest,
    BatchServiceResponse,
    ServiceAccessRequest,
    ServiceAccessResponse,
)
from app.services.model_service import ModelServiceManager
from app.services.container_service import container_file_service

router = APIRouter(prefix="/api", tags=["services"])
service_manager = ModelServiceManager()
logger = logging.getLogger(__name__)


# 依赖函数
async def get_repository_with_permission(
    username: str,
    repo_name: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Repository:
    """获取仓库并检查权限"""

    # 查找仓库
    repo_query = (
        select(Repository)
        .join(User)
        .where(and_(User.username == username, Repository.name == repo_name))
        .options(selectinload(Repository.owner))
    )

    result = await db.execute(repo_query)
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(status_code=404, detail="仓库不存在")

    # 检查权限：公开仓库允许游客访问，私有仓库需要仓库所有者
    if repository.visibility == "public":
        # 公开仓库，任何人都可以访问（包括未登录用户）
        return repository
    
    # 私有仓库需要认证且为仓库所有者
    if not current_user:
        raise HTTPException(
            status_code=401, 
            detail="访问私有仓库需要登录",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if repository.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限访问此私有仓库")

    return repository


async def get_service_with_permission(
    service_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> ModelService:
    """获取服务并检查权限"""

    service_query = (
        select(ModelService)
        .where(ModelService.id == service_id)
        .options(selectinload(ModelService.repository), selectinload(ModelService.user))
    )

    result = await db.execute(service_query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    # 检查权限：公开服务允许游客访问，私有服务需要服务所有者
    if service.is_public:
        # 公开服务，任何人都可以访问（包括未登录用户）
        return service
    
    # 私有服务需要认证且为服务所有者
    if not current_user:
        raise HTTPException(
            status_code=401, 
            detail="访问私有服务需要登录",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if service.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限访问此私有服务")

    return service


# 服务管理API
@router.get("/{username}/{repo_name}/services", response_model=ServiceListResponse)
async def list_repository_services(
    repository: Repository = Depends(get_repository_with_permission),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    auto_start: bool = Query(False, description="是否自动启动服务"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取仓库服务列表，支持自动启动"""
    
    try:
        logger.info(f"获取仓库 {repository.id} 服务列表，auto_start={auto_start}")
        if current_user:
            logger.info(f"当前用户: {current_user.id}")
        else:
            logger.info("当前为游客用户")

        # 构建查询 - 对于游客，只显示公开服务
        query = select(ModelService).where(ModelService.repository_id == repository.id)
        
        # 如果是游客用户，只能看到公开服务
        if not current_user:
            query = query.where(ModelService.is_public == True)
        # 如果是登录用户但不是仓库所有者，只能看到公开服务
        elif current_user.id != repository.owner_id:
            query = query.where(ModelService.is_public == True)

        # 自动启动功能仅对仓库所有者有效
        auto_start_result = None
        if auto_start and current_user and repository.owner_id == current_user.id:
            logger.info(f"自动启动功能暂时禁用用于调试")
            # try:
            #     logger.info(f"尝试自动启动仓库 {repository.id} 的服务，用户 {current_user.id}")
            #     auto_start_result = await service_manager.auto_start_repository_services(
            #         db=db, repository_id=repository.id, user_id=current_user.id
            #     )
            #     logger.info(f"自动启动完成: {auto_start_result}")
            # except Exception as e:
            #     # 自动启动失败不影响服务列表获取
            #     logger.error(f"自动启动仓库 {repository.id} 服务失败: {e}", exc_info=True)

        if status:
            query = query.where(ModelService.status == status)

        # 分页查询总数
        total_query = select(func.count(ModelService.id)).where(
            ModelService.repository_id == repository.id
        )
        
        # 应用相同的权限过滤
        if not current_user:
            total_query = total_query.where(ModelService.is_public == True)
        elif current_user.id != repository.owner_id:
            total_query = total_query.where(ModelService.is_public == True)
            
        if status:
            total_query = total_query.where(ModelService.status == status)

        total_result = await db.execute(total_query)
        total = total_result.scalar()

        # 获取服务列表
        services_query = (
            query.order_by(ModelService.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        services_result = await db.execute(services_query)
        services = services_result.scalars().all()

        # 构建响应
        response = ServiceListResponse(
            services=[ServiceResponse.model_validate(service) for service in services],
            total=total,
            page=page,
            size=size,
        )

        # 添加自动启动结果
        if auto_start_result:
            response.auto_start_result = auto_start_result

        return response

    except Exception as e:
        logger.error(f"获取仓库服务列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取服务列表失败: {str(e)}")


@router.post(
    "/{username}/{repo_name}/services", response_model=ServiceResponse, status_code=201
)
async def create_service(
    service_data: ServiceCreate,
    repository: Repository = Depends(get_repository_with_permission),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """创建模型服务"""

    # 检查创建权限（仓库所有者）
    if repository.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有仓库所有者可以创建服务")

    try:
        service = await service_manager.create_service(
            db=db,
            service_data=service_data,
            repository_id=repository.id,
            user_id=current_user.id,
        )
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建服务失败: {str(e)}")


@router.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(service: ModelService = Depends(get_service_with_permission)):
    """获取服务详情"""
    return ServiceResponse.model_validate(service)


@router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_data: ServiceUpdate,
    service: ModelService = Depends(get_service_with_permission),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """更新服务配置"""

    # 检查修改权限（服务所有者）
    if service.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有服务所有者可以修改配置")

    try:
        # 更新服务字段
        update_data = service_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(service, field, value)

        await db.commit()
        await db.refresh(service)

        return ServiceResponse.model_validate(service)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新服务失败: {str(e)}")


@router.delete("/services/{service_id}", status_code=204)
async def delete_service(
    service: ModelService = Depends(get_service_with_permission),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """删除服务"""

    # 检查删除权限（服务所有者）
    if service.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有服务所有者可以删除服务")

    try:
        await service_manager.delete_service(
            db=db, service_id=service.id, user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除服务失败: {str(e)}")


# 服务生命周期控制API
@router.post("/services/{service_id}/start", response_model=ServiceResponse)
async def start_service(
    start_request: ServiceStartRequest,
    service: ModelService = Depends(get_service_with_permission),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """启动服务"""

    # 检查操作权限（服务所有者）
    if service.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有服务所有者可以启动服务")

    try:
        updated_service = await service_manager.start_service(
            db=db,
            service_id=service.id,
            user_id=current_user.id,
            force_restart=start_request.force_restart,
        )
        return updated_service
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动服务失败: {str(e)}")


@router.post("/services/{service_id}/stop", response_model=ServiceResponse)
async def stop_service(
    stop_request: ServiceStopRequest,
    service: ModelService = Depends(get_service_with_permission),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """停止服务"""

    # 检查操作权限（服务所有者）
    if service.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有服务所有者可以停止服务")

    try:
        updated_service = await service_manager.stop_service(
            db=db,
            service_id=service.id,
            user_id=current_user.id,
            force_stop=stop_request.force_stop,
            timeout_seconds=stop_request.timeout_seconds,
        )
        return updated_service
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止服务失败: {str(e)}")


@router.post("/services/{service_id}/restart", response_model=ServiceResponse)
async def restart_service(
    service: ModelService = Depends(get_service_with_permission),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """重启服务"""

    # 检查操作权限（服务所有者）
    if service.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有服务所有者可以重启服务")

    try:
        # 先停止再启动
        await service_manager.stop_service(
            db=db, service_id=service.id, user_id=current_user.id, force_stop=True
        )

        updated_service = await service_manager.start_service(
            db=db, service_id=service.id, user_id=current_user.id, force_restart=True
        )
        return updated_service
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重启服务失败: {str(e)}")


@router.get("/services/{service_id}/status", response_model=ServiceStatusResponse)
async def get_service_status(
    service: ModelService = Depends(get_service_with_permission),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取服务状态"""

    try:
        status_info = await service_manager.get_service_status(
            db=db, service_id=service.id
        )
        return ServiceStatusResponse(**status_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务状态失败: {str(e)}")


@router.get("/services/{service_id}/logs", response_model=ServiceLogListResponse)
async def get_service_logs(
    service: ModelService = Depends(get_service_with_permission),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页数量"),
    level: Optional[str] = Query(None, description="按日志级别筛选"),
    event_type: Optional[str] = Query(None, description="按事件类型筛选"),
    db: AsyncSession = Depends(get_async_db),
):
    """获取服务日志"""

    # 构建查询
    query = select(ServiceLog).where(ServiceLog.service_id == service.id)

    if level:
        query = query.where(ServiceLog.log_level == level)
    if event_type:
        query = query.where(ServiceLog.event_type == event_type)

    # 分页
    total_query = select(func.count(ServiceLog.id)).where(
        ServiceLog.service_id == service.id
    )
    if level:
        total_query = total_query.where(ServiceLog.log_level == level)
    if event_type:
        total_query = total_query.where(ServiceLog.event_type == event_type)

    total_result = await db.execute(total_query)
    total = total_result.scalar()

    # 获取日志列表
    logs_query = (
        query.order_by(ServiceLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    logs_result = await db.execute(logs_query)
    logs = logs_result.scalars().all()

    return ServiceLogListResponse(logs=logs, total=total, page=page, size=size)


# 服务访问管理API
@router.get("/services/{service_id}/demo")
async def access_service_demo(
    service: ModelService = Depends(get_service_with_permission),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """访问Gradio界面（重定向）"""

    if not service.service_url:
        raise HTTPException(status_code=400, detail="服务未运行")

    # 更新访问统计和时间
    service.access_count += 1
    service.last_accessed_at = func.now()
    await db.commit()

    # 记录访问日志（区分登录用户和游客）
    if current_user:
        await service_manager._log_service_event(
            db=db,
            service_id=service.id,
            level="info",
            message=f"用户 {current_user.username} 访问了服务",
            event_type="access",
            user_id=current_user.id,
        )
    else:
        await service_manager._log_service_event(
            db=db,
            service_id=service.id,
            level="info",
            message="游客用户访问了服务",
            event_type="access",
            user_id=None,
        )

    # 返回重定向响应
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=service.service_url)


@router.post(
    "/services/{service_id}/access-token", response_model=ServiceAccessResponse
)
async def regenerate_access_token(
    access_request: ServiceAccessRequest,
    service: ModelService = Depends(get_service_with_permission),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """重新生成访问令牌"""

    # 检查权限（服务所有者）
    if service.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="只有服务所有者可以重新生成访问令牌"
        )

    if access_request.regenerate_token:
        service.access_token = service_manager._generate_access_token()
        await db.commit()

    return ServiceAccessResponse(
        service_url=service.service_url or "",
        access_token=service.access_token,
        demo_url=f"{service.service_url}/gradio" if service.service_url else "",
        is_public=service.is_public,
    )


@router.put("/services/{service_id}/visibility", response_model=ServiceResponse)
async def update_service_visibility(
    visibility_data: dict,
    service: ModelService = Depends(get_service_with_permission),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """更新服务可见性"""

    # 检查权限（服务所有者）
    if service.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有服务所有者可以修改可见性")

    is_public = visibility_data.get("is_public")
    if is_public is not None:
        service.is_public = is_public
        await db.commit()
        await db.refresh(service)

    return ServiceResponse.model_validate(service)


# 服务监控API
@router.get(
    "/services/{service_id}/health", response_model=ServiceHealthCheckListResponse
)
async def get_service_health_history(
    service: ModelService = Depends(get_service_with_permission),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取服务健康检查历史"""

    # 分页查询
    total_query = select(func.count(ServiceHealthCheck.id)).where(
        ServiceHealthCheck.service_id == service.id
    )
    total_result = await db.execute(total_query)
    total = total_result.scalar()

    checks_query = (
        select(ServiceHealthCheck)
        .where(ServiceHealthCheck.service_id == service.id)
        .order_by(ServiceHealthCheck.checked_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    checks_result = await db.execute(checks_query)
    checks = checks_result.scalars().all()

    return ServiceHealthCheckListResponse(
        checks=checks, total=total, page=page, size=size
    )


@router.post("/services/{service_id}/health-check")
async def trigger_health_check(
    service: ModelService = Depends(get_service_with_permission),
    db: AsyncSession = Depends(get_async_db),
):
    """手动触发健康检查"""

    try:
        health_check = await service_manager.perform_health_check(
            db=db, service_id=service.id
        )
        return health_check
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/services/{service_id}/metrics")
async def get_service_metrics(
    service: ModelService = Depends(get_service_with_permission),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取服务性能指标"""

    # 基础指标（公开服务允许游客查看基本指标）
    metrics = {
        "service_id": service.id,
        "service_name": service.service_name,
        "status": service.status,
        "access_count": service.access_count,
        "start_count": service.start_count,
        "total_runtime_minutes": service.total_runtime_minutes,
        "created_at": service.created_at,
        "last_accessed_at": service.last_accessed_at,
        "last_started_at": service.last_started_at,
    }

    # 获取最近的健康检查结果
    recent_health_query = (
        select(ServiceHealthCheck)
        .where(ServiceHealthCheck.service_id == service.id)
        .order_by(ServiceHealthCheck.checked_at.desc())
        .limit(5)
    )

    health_result = await db.execute(recent_health_query)
    recent_health_checks = health_result.scalars().all()

    metrics["recent_health_checks"] = [
        {
            "status": check.status,
            "response_time_ms": check.response_time_ms,
            "checked_at": check.checked_at,
        }
        for check in recent_health_checks
    ]

    return metrics


@router.get("/services/{service_id}/resource-usage")
async def get_service_resource_usage(
    service: ModelService = Depends(get_service_with_permission),
    db: AsyncSession = Depends(get_async_db),
):
    """获取服务资源使用情况"""

    if not service.container_id:
        raise HTTPException(status_code=400, detail="服务未运行")

    try:
        resource_usage = await service_manager._get_container_resource_usage(
            service.container_id
        )
        return resource_usage or {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源使用情况失败: {str(e)}")


# 批量操作API
@router.post(
    "/{username}/{repo_name}/services/batch/start", response_model=BatchServiceResponse
)
async def batch_start_services(
    batch_request: BatchServiceRequest,
    repository: Repository = Depends(get_repository_with_permission),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_db),
):
    """批量启动服务"""

    # 检查权限（仓库所有者）
    if repository.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有仓库所有者可以批量操作服务")

    successful = []
    failed = []

    for service_id in batch_request.service_ids:
        try:
            # 验证服务属于该仓库
            service_query = select(ModelService).where(
                and_(
                    ModelService.id == service_id,
                    ModelService.repository_id == repository.id,
                )
            )
            result = await db.execute(service_query)
            service = result.scalar_one_or_none()

            if not service:
                failed.append(
                    {"service_id": service_id, "error": "服务不存在或不属于该仓库"}
                )
                continue

            # 异步启动服务
            background_tasks.add_task(
                service_manager.start_service,
                db=db,
                service_id=service_id,
                user_id=current_user.id,
            )
            successful.append(service_id)

        except Exception as e:
            failed.append({"service_id": service_id, "error": str(e)})

    return BatchServiceResponse(successful=successful, failed=failed)


@router.post(
    "/{username}/{repo_name}/services/batch/stop", response_model=BatchServiceResponse
)
async def batch_stop_services(
    batch_request: BatchServiceRequest,
    repository: Repository = Depends(get_repository_with_permission),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_db),
):
    """批量停止服务"""

    # 检查权限（仓库所有者）
    if repository.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有仓库所有者可以批量操作服务")

    successful = []
    failed = []

    for service_id in batch_request.service_ids:
        try:
            # 验证服务属于该仓库
            service_query = select(ModelService).where(
                and_(
                    ModelService.id == service_id,
                    ModelService.repository_id == repository.id,
                )
            )
            result = await db.execute(service_query)
            service = result.scalar_one_or_none()

            if not service:
                failed.append(
                    {"service_id": service_id, "error": "服务不存在或不属于该仓库"}
                )
                continue

            # 异步停止服务
            background_tasks.add_task(
                service_manager.stop_service,
                db=db,
                service_id=service_id,
                user_id=current_user.id,
            )
            successful.append(service_id)

        except Exception as e:
            failed.append({"service_id": service_id, "error": str(e)})

    return BatchServiceResponse(successful=successful, failed=failed)


@router.delete(
    "/{username}/{repo_name}/services/batch", response_model=BatchServiceResponse
)
async def batch_delete_services(
    batch_request: BatchServiceRequest,
    repository: Repository = Depends(get_repository_with_permission),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_db),
):
    """批量删除服务"""

    # 检查权限（仓库所有者）
    if repository.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有仓库所有者可以批量操作服务")

    successful = []
    failed = []

    for service_id in batch_request.service_ids:
        try:
            # 验证服务属于该仓库
            service_query = select(ModelService).where(
                and_(
                    ModelService.id == service_id,
                    ModelService.repository_id == repository.id,
                )
            )
            result = await db.execute(service_query)
            service = result.scalar_one_or_none()

            if not service:
                failed.append(
                    {"service_id": service_id, "error": "服务不存在或不属于该仓库"}
                )
                continue

            # 异步删除服务
            background_tasks.add_task(
                service_manager.delete_service,
                db=db,
                service_id=service_id,
                user_id=current_user.id,
            )
            successful.append(service_id)

        except Exception as e:
            failed.append({"service_id": service_id, "error": str(e)})

    return BatchServiceResponse(successful=successful, failed=failed)


# 后台任务：定期清理空闲服务
@router.post("/services/cleanup-idle", include_in_schema=False)
async def cleanup_idle_services_endpoint(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_async_db)
):
    """手动触发空闲服务清理（管理员功能）"""

    background_tasks.add_task(service_manager.cleanup_idle_services, db)
    return {"message": "空闲服务清理任务已启动"}


# 系统监控和统计API
@router.get("/admin/services/statistics")
async def get_system_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取系统资源和服务统计信息（管理员功能）"""

    # TODO: 添加管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        from app.utils.resource_manager import resource_manager

        stats = await resource_manager.get_resource_statistics(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/admin/services/overview")
async def get_services_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取服务概览信息（管理员功能）"""

    # TODO: 添加管理员权限检查

    try:
        # 获取各状态服务数量
        from sqlalchemy import func, case

        status_stats_query = select(
            ModelService.status, func.count(ModelService.id).label("count")
        ).group_by(ModelService.status)

        result = await db.execute(status_stats_query)
        status_stats = {row.status: row.count for row in result}

        # 获取用户服务分布
        user_stats_query = (
            select(
                ModelService.user_id, func.count(ModelService.id).label("service_count")
            )
            .group_by(ModelService.user_id)
            .order_by(func.count(ModelService.id).desc())
            .limit(10)
        )

        user_result = await db.execute(user_stats_query)
        user_stats = [
            {"user_id": row.user_id, "service_count": row.service_count}
            for row in user_result
        ]

        # 获取最近活跃的服务
        from datetime import datetime, timedelta

        recent_threshold = datetime.utcnow() - timedelta(hours=24)

        recent_services_query = (
            select(ModelService)
            .where(ModelService.last_accessed_at >= recent_threshold)
            .order_by(ModelService.last_accessed_at.desc())
            .limit(10)
        )

        recent_result = await db.execute(recent_services_query)
        recent_services = [
            {
                "id": service.id,
                "service_name": service.service_name,
                "status": service.status,
                "last_accessed_at": service.last_accessed_at,
                "access_count": service.access_count,
            }
            for service in recent_result.scalars()
        ]

        return {
            "status_distribution": status_stats,
            "top_users_by_service_count": user_stats,
            "recent_active_services": recent_services,
            "summary": {
                "total_services": sum(status_stats.values()),
                "running_services": status_stats.get("running", 0),
                "error_services": status_stats.get("error", 0),
                "idle_services": status_stats.get("idle", 0),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务概览失败: {str(e)}")


@router.post("/admin/services/maintenance")
async def perform_system_maintenance(
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_db),
):
    """执行系统维护任务（管理员功能）"""

    # TODO: 添加管理员权限检查

    async def maintenance_task():
        """维护任务"""
        try:
            # 清理空闲服务
            idle_cleaned = await service_manager.cleanup_idle_services(db)

            # 清理未使用的端口
            from app.utils.resource_manager import resource_manager

            ports_cleaned = await resource_manager.cleanup_unused_ports(db)

            # 执行健康检查
            running_services_query = select(ModelService).where(
                ModelService.status == "running"
            )
            result = await db.execute(running_services_query)
            running_services = result.scalars().all()

            health_checked = 0
            for service in running_services:
                try:
                    await service_manager.perform_health_check(db, service.id)
                    health_checked += 1
                except Exception as e:
                    logger.error(f"健康检查服务 {service.id} 失败: {e}")

            logger.info(
                f"系统维护完成: 清理空闲服务 {idle_cleaned} 个, "
                f"清理端口 {ports_cleaned} 个, 健康检查 {health_checked} 个服务"
            )

        except Exception as e:
            logger.error(f"系统维护任务失败: {e}")

    background_tasks.add_task(maintenance_task)
    return {"message": "系统维护任务已启动"}


@router.get("/services/health-summary")
async def get_services_health_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取服务健康状态摘要"""

    try:
        # 获取用户有权限查看的服务
        user_services_query = select(ModelService).where(
            or_(ModelService.user_id == current_user.id, ModelService.is_public == True)
        )

        result = await db.execute(user_services_query)
        services = result.scalars().all()

        # 统计健康状态
        health_summary = {
            "total": len(services),
            "running": 0,
            "healthy": 0,
            "unhealthy": 0,
            "unknown": 0,
            "stopped": 0,
            "error": 0,
        }

        for service in services:
            if service.status == "running":
                health_summary["running"] += 1

                # 获取最近的健康检查结果
                latest_check_query = (
                    select(ServiceHealthCheck)
                    .where(ServiceHealthCheck.service_id == service.id)
                    .order_by(ServiceHealthCheck.checked_at.desc())
                    .limit(1)
                )

                check_result = await db.execute(latest_check_query)
                latest_check = check_result.scalar_one_or_none()

                if latest_check:
                    if latest_check.status == "healthy":
                        health_summary["healthy"] += 1
                    elif latest_check.status in ["unhealthy", "timeout"]:
                        health_summary["unhealthy"] += 1
                    else:
                        health_summary["unknown"] += 1
                else:
                    health_summary["unknown"] += 1

            elif service.status == "error":
                health_summary["error"] += 1
            else:
                health_summary["stopped"] += 1

        return health_summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取健康状态摘要失败: {str(e)}")


# 容器文件管理API
@router.post("/services/{service_id}/files/update")
async def update_service_files(
    service_id: int,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db),
    gogogo_file: Optional[UploadFile] = File(None, description="gogogo.py启动文件"),
    mc_config_file: Optional[UploadFile] = File(None, description="mc.json配置文件"),
    model_archive: Optional[UploadFile] = File(None, description="model目录压缩包"),
    examples_archive: Optional[UploadFile] = File(None, description="examples目录压缩包"),
):
    """
    更新服务文件
    
    支持的文件类型：
    - gogogo_file: Python启动脚本 (.py)
    - mc_config_file: JSON配置文件 (.json)
    - model_archive: 模型文件压缩包 (.zip, .tar, .tar.gz)
    - examples_archive: 示例数据压缩包 (.zip, .tar, .tar.gz)
    """
    try:
        # 检查是否至少上传了一个文件
        file_updates = {}
        
        if gogogo_file:
            if not gogogo_file.filename.endswith('.py'):
                raise HTTPException(status_code=400, detail="gogogo文件必须是Python文件(.py)")
            file_updates['gogogo'] = gogogo_file
            
        if mc_config_file:
            if not mc_config_file.filename.endswith('.json'):
                raise HTTPException(status_code=400, detail="配置文件必须是JSON文件(.json)")
            file_updates['mc_config'] = mc_config_file
            
        if model_archive:
            if not any(model_archive.filename.lower().endswith(ext) for ext in ['.zip', '.tar', '.tar.gz', '.tgz']):
                raise HTTPException(status_code=400, detail="模型压缩包格式不支持")
            file_updates['model'] = model_archive
            
        if examples_archive:
            if not any(examples_archive.filename.lower().endswith(ext) for ext in ['.zip', '.tar', '.tar.gz', '.tgz']):
                raise HTTPException(status_code=400, detail="示例数据压缩包格式不支持")
            file_updates['examples'] = examples_archive
            
        if not file_updates:
            raise HTTPException(status_code=400, detail="请至少上传一个文件")
            
        # 调用容器文件更新服务
        result = await container_file_service.update_service_files(
            db, service_id, file_updates, current_user.id
        )
        
        return {
            "message": "文件更新完成",
            "result": result
        }
        
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限操作此服务")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新服务 {service_id} 文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件更新失败: {str(e)}")


@router.post("/services/create-with-tar")
async def create_service_with_docker_tar(
    username: str,
    repo_name: str,
    docker_tar: UploadFile = File(..., description="Docker镜像tar包"),
    description: Optional[str] = Form(None, description="服务描述"),
    cpu_limit: str = Form("0.3", description="CPU限制"),
    memory_limit: str = Form("256Mi", description="内存限制"),
    is_public: bool = Form(False, description="是否公开访问"),
    priority: int = Form(2, ge=0, le=3, description="启动优先级"),
    examples_archive: Optional[UploadFile] = File(None, description="可选的examples目录压缩包"),
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    使用Docker tar包创建模型服务
    
    该接口用于上传Docker镜像tar包来创建服务，镜像必须包含：
    - gogogo.py: 模型服务启动文件
    - mc.json: 配置文件  
    - model/: 模型文件夹
    """
    try:
        # 验证tar包文件
        if not docker_tar.filename.lower().endswith(('.tar', '.tar.gz', '.tgz')):
            raise HTTPException(status_code=400, detail="Docker镜像必须是tar包格式")
        
        # 验证文件大小 (最大2GB)
        max_size = 2 * 1024 * 1024 * 1024
        if docker_tar.size and docker_tar.size > max_size:
            raise HTTPException(status_code=400, detail="Docker镜像tar包大小不能超过2GB")
        
        # 获取仓库
        repository = await get_repository_with_permission(username, repo_name, current_user, db)
        
        # 从tar包文件名生成服务名称
        import os
        service_name = os.path.splitext(os.path.splitext(docker_tar.filename)[0])[0]
        service_name = service_name.replace('.', '-').replace('_', '-').lower()
        
        # 确保服务名称符合要求
        if len(service_name) > 30:
            service_name = service_name[:30]
        if not service_name or not service_name.replace('-', '').isalnum():
            service_name = f"service-{current_user.id}-{int(time.time())}"
        
        # 构建服务创建数据
        service_data = ServiceCreate(
            service_name=service_name,
            model_id=service_name,  # 使用服务名称作为model_id
            description=description,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
            is_public=is_public,
            priority=priority,
        )
        
        # 创建服务
        service = await service_manager.create_service(
            db, service_data, repository.id, current_user.id
        )
        
        # 更新Docker镜像信息
        await db.refresh(service)
        service.docker_image = docker_tar.filename  # 保存原始文件名
        await db.commit()
        
        # TODO: 处理Docker tar包 - 这里需要实现tar包的加载和验证逻辑
        # 可以考虑：
        # 1. 保存tar包到临时目录
        # 2. 验证tar包中包含必需文件
        # 3. 加载Docker镜像到Docker引擎
        # 4. 验证镜像可以正常启动
        
        # 如果上传了examples文件，处理它
        if examples_archive:
            file_updates = {'examples': examples_archive}
            try:
                await container_file_service.update_service_files(
                    db, service.id, file_updates, current_user.id
                )
            except Exception as e:
                logger.warning(f"上传examples文件失败，但服务创建成功: {e}")
        
        return {
            "message": "服务创建成功",
            "service": ServiceResponse.model_validate(service),
            "docker_tar_filename": docker_tar.filename,
            "examples_uploaded": examples_archive is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建服务失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务创建失败: {str(e)}")


@router.get("/services/{service_id}/container-info")
async def get_service_container_info(
    service: ModelService = Depends(get_service_with_permission),
    current_user: Optional[User] = Depends(get_current_user),
):
    """获取服务容器信息"""
    
    try:
        return {
            "service_id": service.id,
            "service_name": service.service_name,
            "docker_image": service.docker_image,
            "container_id": service.container_id,
            "health_status": service.health_status,
            "error_message": service.error_message,
            "last_updated": service.last_updated,
            "gradio_port": service.gradio_port,
            "service_url": service.service_url,
            "status": service.status
        }
        
    except Exception as e:
        logger.error(f"获取容器信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取容器信息失败: {str(e)}")


@router.post("/services/{service_id}/validate-environment")
async def validate_service_environment(
    service_id: int,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    验证服务环境
    
    检查容器是否包含必需的文件和依赖，用于识别环境问题
    """
    try:
        # 获取服务
        service = await service_manager._get_service_by_id(db, service_id)
        
        # 检查权限
        if service.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限操作此服务")
            
        if not service.container_id:
            raise HTTPException(status_code=400, detail="服务容器不存在")
            
        # 验证容器环境
        validation_result = await _validate_container_environment(service.container_id)
        
        # 更新服务状态
        if validation_result['is_valid']:
            service.health_status = "healthy"
            service.error_message = None
        else:
            service.health_status = "unhealthy"
            service.error_message = f"环境验证失败: {validation_result['error']}"
            
        await db.commit()
        
        return {
            "service_id": service_id,
            "validation_result": validation_result,
            "health_status": service.health_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证服务环境失败: {e}")
        raise HTTPException(status_code=500, detail=f"环境验证失败: {str(e)}")
        

async def _validate_container_environment(container_id: str) -> Dict[str, Any]:
    """验证容器环境"""
    
    try:
        if not service_manager.docker_client:
            return {
                'is_valid': False,
                'error': 'Docker客户端未初始化'
            }
            
        container = service_manager.docker_client.containers.get(container_id)
        
        # 检查必需文件
        required_files = ['/app/gogogo.py', '/app/mc.json', '/app/model']
        missing_files = []
        
        for file_path in required_files:
            try:
                result = container.exec_run(f'test -e {file_path}')
                if result.exit_code != 0:
                    missing_files.append(file_path)
            except Exception:
                missing_files.append(file_path)
                
        if missing_files:
            return {
                'is_valid': False,
                'error': f'缺少必需文件: {", ".join(missing_files)}',
                'missing_files': missing_files
            }
            
        # 检查Python环境
        try:
            result = container.exec_run('python --version')
            if result.exit_code != 0:
                return {
                    'is_valid': False,
                    'error': 'Python环境不可用'
                }
        except Exception:
            return {
                'is_valid': False,
                'error': 'Python环境检查失败'
            }
            
        return {
            'is_valid': True,
            'message': '环境验证通过'
        }
        
    except Exception as e:
        return {
            'is_valid': False,
            'error': f'验证过程出错: {str(e)}'
        }
