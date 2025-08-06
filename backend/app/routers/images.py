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
    ImageListResponse, ImageUploadResponse, ServiceListResponse, 
    BuildLogsResponse, ImageDeleteResponse, ServiceFromImageCreate,
    ErrorResponse
)
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
    current_user: User = Depends(get_current_user)
):
    """
    上传Docker镜像tar包到Harbor
    """
    try:
        # 验证文件类型
        if not image_file.filename or not image_file.filename.endswith(('.tar', '.tar.gz', '.tgz')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持tar格式的镜像文件(.tar, .tar.gz, .tgz)"
            )
        
        # 验证文件大小 (5GB限制)
        if image_file.size and image_file.size > 5 * 1024 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="镜像文件过大，最大支持5GB"
            )
        
        # 验证镜像名称格式
        if not name.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="镜像名称只能包含字母、数字、连字符、下划线和点"
            )
        
        result = await image_management_service.upload_image_from_tar(
            db=db,
            repository_id=repository_id,
            tar_file=image_file,
            image_name=name,
            tag=tag,
            description=description,
            user_id=current_user.id
        )
        
        return ImageUploadResponse(
            success=True,
            data=result,
            message="镜像上传已开始，请稍后查看状态"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"镜像上传API失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内部错误: {str(e)}"
        )


@router.get("/repositories/{repository_id}")
async def list_images(
    repository_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    列出仓库的所有镜像
    """
    try:
        # 对于公开仓库，允许匿名访问
        user_id = current_user.id if current_user else None
        images = await image_management_service.list_repository_images(
            db=db,
            repository_id=repository_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "data": images,
            "total": len(images)
        }
        
    except Exception as e:
        logger.error(f"列出镜像API失败: {e}")
        if "仓库不存在" in str(e):
            from app.middleware.error_handler import NotFoundError
            raise NotFoundError(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{image_id}/services")
async def list_image_services(
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取镜像的所有服务
    """
    try:
        services = await image_management_service.get_image_services(
            db=db,
            image_id=image_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "data": services,
            "total": len(services)
        }
        
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
    current_user: User = Depends(get_current_user)
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
                "GRADIO_SERVER_PORT": "7860"
            },
            "restart_policy": "unless-stopped"
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
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "data": result,
            "message": "服务创建成功"
        }
        
    except Exception as e:
        logger.error(f"创建服务API失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    force: bool = False,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除镜像（需要先删除所有相关服务）
    """
    try:
        # 检查是否有关联的服务
        services = await image_management_service.get_image_services(
            db=db,
            image_id=image_id,
            user_id=current_user.id
        )
        
        active_services = [s for s in services if s["status"] not in ["deleted", "stopped"]]
        if active_services and not force:
            raise HTTPException(
                status_code=400, 
                detail=f"镜像还有 {len(active_services)} 个活跃服务，请先停止服务或使用 force=true"
            )
        
        # TODO: 实现删除逻辑
        # 1. 从Harbor删除镜像
        # 2. 从mManager控制器删除镜像
        # 3. 更新数据库状态
        
        return {
            "success": True,
            "message": "镜像删除功能开发中"
        }
        
    except Exception as e:
        logger.error(f"删除镜像API失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{image_id}/build-logs")
async def get_image_build_logs(
    image_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取镜像构建日志
    """
    try:
        from sqlalchemy import select
        from app.models.image import ImageBuildLog
        
        # 验证权限
        await image_management_service._get_image_with_validation(db, image_id, current_user.id)
        
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
                "created_at": log.created_at
            }
            for log in logs
        ]
        
        return {
            "success": True,
            "data": log_data,
            "total": len(log_data)
        }
        
    except Exception as e:
        logger.error(f"获取构建日志API失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))