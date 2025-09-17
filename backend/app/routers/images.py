"""
镜像管理API路由
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.image_service import image_management_service
from app.schemas.image import (
    ImageListResponse,
    ImageUploadResponse,
    ServiceListResponse,
    BuildLogsResponse,
    ImageDeleteResponse,
    ServiceFromImageCreate,
    ErrorResponse,
)
from app.config import settings
from app.utils.logger import logger

router = APIRouter()


@router.post("/repositories/{repository_id}/upload", response_model=ImageUploadResponse)
async def upload_image(
    repository_id: int,
    image_file: UploadFile = File(..., description="Docker镜像tar包"),
    name: str = Form(..., min_length=1, max_length=255, description="镜像名称"),
    tag: str = Form("latest", min_length=1, max_length=100, description="镜像标签"),
    description: str = Form("", max_length=1000, description="镜像描述"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传Docker镜像tar包到Harbor
    """
    try:
        # 验证文件类型
        if not image_file.filename or not image_file.filename.endswith(
            (".tar", ".tar.gz", ".tgz")
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持tar格式的镜像文件(.tar, .tar.gz, .tgz)",
            )

        # 验证文件大小 (5GB限制)
        if image_file.size and image_file.size > 5 * 1024 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="镜像文件过大，最大支持5GB",
            )

        # 验证镜像名称格式
        if not name.replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="镜像名称只能包含字母、数字、连字符、下划线和点",
            )

        result = await image_management_service.upload_image_from_tar(
            db=db,
            repository_id=repository_id,
            tar_file=image_file,
            image_name=name,
            tag=tag,
            description=description,
            user_id=current_user.id,
        )

        return ImageUploadResponse(
            success=True, data=result, message="镜像上传已开始，请稍后查看状态"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"镜像上传API失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内部错误: {str(e)}",
        )


@router.get("/repositories/{repository_id}")
async def list_images(
    repository_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    列出仓库的所有镜像
    """
    try:
        # 对于公开仓库，允许匿名访问
        user_id = current_user.id if current_user else None
        images = await image_management_service.list_repository_images(
            db=db, repository_id=repository_id, user_id=user_id
        )

        return {"success": True, "data": images, "total": len(images)}

    except Exception as e:
        logger.error(f"列出镜像API失败: {e}")
        if "仓库不存在" in str(e):
            from app.middleware.error_response import RepositoryException, ErrorCodes

            raise RepositoryException(str(e), ErrorCodes.REPOSITORY_NOT_FOUND, status_code=404)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{image_id}/services")
async def list_image_services(
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取镜像的所有服务
    """
    try:
        services = await image_management_service.get_image_services(
            db=db, image_id=image_id, user_id=current_user.id
        )

        return {"success": True, "data": services, "total": len(services)}

    except Exception as e:
        logger.error(f"获取镜像服务API失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{image_id}/services/create")
async def create_service_from_image(
    image_id: int,
    description: str = Form("", description="服务描述"),
    cpu_limit: str = Form("0.5", description="CPU限制"),
    memory_limit: str = Form("512m", description="内存限制"),
    gradio_port: Optional[int] = Form(None, description="Gradio端口"),
    is_public: bool = Form(False, description="是否公开"),
    priority: int = Form(2, description="优先级"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    基于镜像创建模型服务（服务名称将根据镜像信息自动生成）
    """
    try:
        # 构建服务配置（服务名称将自动生成）
        service_config = {
            "service_name": "temp",  # 临时名称，实际会被自动生成的名称覆盖
            "description": description,
            "cpu_limit": cpu_limit,
            "memory_limit": memory_limit,
            "gradio_port": gradio_port,
            "is_public": is_public,
            "priority": priority,
            "ports": {"7860/tcp": gradio_port} if gradio_port else {"7860/tcp": None},
            "environment": {
                "GRADIO_SERVER_NAME": "0.0.0.0",
                "GRADIO_SERVER_PORT": "7860",
            },
            "restart_policy": "unless-stopped",
        }

        # 从镜像信息推断repository_id
        from sqlalchemy import select
        from app.models.image import Image

        result = await db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()
        if not image:
            raise HTTPException(status_code=404, detail="镜像不存在")

        result = await image_management_service.create_service_with_image(
            db=db,
            repository_id=image.repository_id,
            image_id=image_id,
            service_config=service_config,
            user_id=current_user.id,
        )

        return {"success": True, "data": result, "message": "服务创建成功"}

    except Exception as e:
        logger.error(f"创建服务API失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    force: bool = False,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除镜像（硬删除，同时删除所有关联服务）
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.image import Image
    from app.services.model_service import service_manager
    from app.services.harbor_client import HarborClient
    from app.services.mmanager_client import mmanager_client

    try:
        # 1. 获取镜像信息（包含关联的服务）
        image_query = (
            select(Image)
            .options(selectinload(Image.services), selectinload(Image.repository))
            .where(Image.id == image_id)
        )

        result = await db.execute(image_query)
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(status_code=404, detail="镜像不存在")

        # 2. 权限检查
        if image.repository.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="只有仓库所有者可以删除镜像")

        # 3. 获取所有关联服务
        services = image.services
        active_services = [
            s for s in services if s.status not in ["deleted", "stopped"]
        ]

        if active_services and not force:
            raise HTTPException(
                status_code=400,
                detail=f"镜像还有 {len(active_services)} 个活跃服务，请使用 force=true 强制删除",
            )

        deletion_summary = {
            "image_id": image_id,
            "image_name": f"{image.original_name}:{image.original_tag}",
            "services_deleted": 0,
            "harbor_cleanup_success": False,
            "mmanager_cleanup": [],
            "errors": [],
        }

        # 4. 删除所有关联服务
        for service in services:
            try:
                # 停止服务（如果正在运行）
                if service.status in ["running", "starting"]:
                    await service_manager.stop_service(db, service.id, current_user.id)

                # 删除服务（包括容器）
                await service_manager.delete_service(db, service.id, current_user.id)

                if service.container_id:
                    deletion_summary["mmanager_cleanup"].append(
                        {
                            "container_id": service.container_id,
                            "service_name": service.service_name,
                            "status": "deleted",
                        }
                    )

                deletion_summary["services_deleted"] += 1

            except Exception as e:
                error_msg = f"删除服务 {service.id} 失败: {str(e)}"
                deletion_summary["errors"].append(error_msg)
                logger.warning(error_msg)

        # 5. 从Harbor删除镜像
        try:
            async with HarborClient() as harbor_client:
                await harbor_client.delete_repository(
                    project_name=settings.harbor_default_project,
                    repository_name=image.harbor_repository_path,
                )
            deletion_summary["harbor_cleanup_success"] = True
            logger.info(f"Harbor镜像删除成功: {image.harbor_repository_path}")
        except Exception as e:
            error_msg = f"Harbor镜像删除失败: {str(e)}"
            deletion_summary["errors"].append(error_msg)
            logger.warning(error_msg)

        # 6. 从mManager控制器清理镜像
        try:
            await mmanager_client.cleanup_image_from_all_controllers(
                image.full_docker_image_name
            )
            logger.info(f"mManager镜像清理成功: {image.full_docker_image_name}")
        except Exception as e:
            error_msg = f"mManager镜像清理失败: {str(e)}"
            deletion_summary["errors"].append(error_msg)
            logger.warning(error_msg)

        # 7. 删除数据库记录（SQLAlchemy级联删除会处理关联的服务记录）
        await db.delete(image)
        await db.commit()

        return {
            "success": True,
            "message": f"镜像 {image.original_name}:{image.original_tag} 及所有关联服务已删除",
            "deletion_summary": deletion_summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除镜像失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除镜像失败: {str(e)}")


@router.get("/{image_id}/build-logs")
async def get_image_build_logs(
    image_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取镜像构建日志
    """
    try:
        from sqlalchemy import select
        from app.models.image import ImageBuildLog

        # 验证权限
        await image_management_service._get_image_with_validation(
            db, image_id, current_user.id
        )

        # 获取构建日志
        result = await db.execute(
            select(ImageBuildLog)
            .where(ImageBuildLog.image_id == image_id)
            .order_by(ImageBuildLog.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

        log_data = [
            {
                "id": log.id,
                "stage": log.stage,
                "message": log.message,
                "level": log.level,
                "created_at": log.created_at,
            }
            for log in logs
        ]

        return {"success": True, "data": log_data, "total": len(log_data)}

    except Exception as e:
        logger.error(f"获取构建日志API失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
