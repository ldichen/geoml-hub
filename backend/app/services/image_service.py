"""
镜像管理服务
负责协调Harbor、mManager和数据库之间的镜像操作
"""

import asyncio
import tempfile
from typing import Dict, List, Optional, BinaryIO
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from fastapi import UploadFile

from app.models.image import Image, ImageBuildLog
from app.models.repository import Repository
from app.models.service import ModelService
from app.services.harbor_client import HarborClient
from app.services.mmanager_client import mmanager_client
from app.utils.logger import logger
from app.config import settings


class ImageManagementService:
    """镜像管理服务 - 三层架构的协调中心"""

    def __init__(self):
        self.harbor_auth = {
            "username": settings.harbor_username,
            "password": settings.harbor_password,
        }

    # ================== 镜像上传和管理 ==================

    async def upload_image_from_tar(
        self,
        db: AsyncSession,
        repository_id: int,
        tar_file: UploadFile,
        image_name: str,
        tag: str = "latest",
        description: str = "",
        user_id: int = None,
    ) -> Dict:
        """
        从tar文件上传镜像到Harbor，并记录到数据库
        """
        try:
            # 1. 验证仓库和权限
            repository = await self._get_repository_with_validation(
                db, repository_id, user_id, require_ownership=True
            )

            # 2. 检查仓库镜像数量限制
            if not repository.can_add_image:
                raise Exception(f"仓库 {repository.name} 已达到最大镜像数量限制(3个)")

            # 3. 检查镜像名称是否重复
            existing_image = await db.execute(
                select(Image).where(
                    and_(
                        Image.repository_id == repository_id,
                        Image.name == image_name,
                        Image.tag == tag,
                        Image.status != "deleted",
                    )
                )
            )
            if existing_image.scalar_one_or_none():
                raise Exception(f"镜像 {image_name}:{tag} 已存在")

            # 4. 创建数据库记录
            project_name = repository.owner.username  # 使用用户名作为Harbor项目名
            harbor_repository = f"{repository.name}/{image_name}"

            image_record = Image(
                name=image_name,
                tag=tag,
                repository_id=repository_id,
                harbor_project=project_name,
                harbor_repository=harbor_repository,
                description=description,
                status="uploading",
                upload_progress=0,
                created_by=user_id,
            )

            db.add(image_record)
            await db.commit()
            await db.refresh(image_record)

            # 5. 异步上传到Harbor
            upload_task = asyncio.create_task(
                self._upload_to_harbor_async(
                    db, image_record.id, tar_file, project_name, harbor_repository, tag
                )
            )

            return {
                "image_id": image_record.id,
                "name": image_name,
                "tag": tag,
                "status": "uploading",
                "message": "镜像上传已开始",
            }

        except Exception as e:
            logger.error(f"镜像上传失败: {e}")
            raise

    async def _upload_to_harbor_async(
        self,
        db: AsyncSession,
        image_id: int,
        tar_file: UploadFile,
        project_name: str,
        repository_name: str,
        tag: str,
    ):
        """异步上传镜像到Harbor"""

        async def progress_callback(progress, stage):
            """更新上传进度"""
            try:
                await db.execute(
                    update(Image)
                    .where(Image.id == image_id)
                    .values(
                        upload_progress=progress if isinstance(progress, int) else 50,
                        updated_at=datetime.utcnow(),
                    )
                )
                await db.commit()
                logger.debug(f"镜像 {image_id} 上传进度: {progress}% - {stage}")
            except Exception as e:
                logger.warning(f"更新上传进度失败: {e}")

        try:
            # 重置文件指针
            await tar_file.seek(0)

            # 记录开始上传
            await self._add_build_log(
                db, image_id, "upload", "开始上传镜像到Harbor", "info"
            )

            # 上传到Harbor
            async with HarborClient() as harbor:
                result = await harbor.push_image_from_tar(
                    project_name, repository_name, tag, tar_file.file, progress_callback
                )

                # 验证上传结果
                if result.get("status") != "success":
                    raise Exception(f"Harbor返回失败状态: {result}")

                # 更新数据库记录
                await db.execute(
                    update(Image)
                    .where(Image.id == image_id)
                    .values(
                        status="ready",
                        upload_progress=100,
                        harbor_digest=result.get("digest"),
                        harbor_size=result.get("size"),
                        error_message=None,
                        updated_at=datetime.utcnow(),
                    )
                )
                await db.commit()

                # 记录成功日志
                await self._add_build_log(
                    db,
                    image_id,
                    "upload",
                    f"镜像上传成功 - 大小: {result.get('size', 'unknown')}, 摘要: {result.get('digest', 'unknown')[:12]}...",
                    "info",
                )

                logger.info(f"镜像 {image_id} 上传成功: {result.get('full_name')}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"镜像 {image_id} 上传失败: {error_msg}")

            try:
                # 更新失败状态
                await db.execute(
                    update(Image)
                    .where(Image.id == image_id)
                    .values(
                        status="failed",
                        error_message=error_msg,
                        updated_at=datetime.utcnow(),
                    )
                )
                await db.commit()

                # 记录错误日志
                await self._add_build_log(
                    db, image_id, "upload", f"镜像上传失败: {error_msg}", "error"
                )

            except Exception as db_error:
                logger.error(f"更新镜像失败状态时出错: {db_error}")

        finally:
            # 确保文件资源被释放
            try:
                if hasattr(tar_file, "file") and hasattr(tar_file.file, "close"):
                    tar_file.file.close()
            except Exception:
                pass

    # ================== 服务创建协调 ==================

    async def create_service_with_image(
        self,
        db: AsyncSession,
        repository_id: int,
        image_id: int,
        service_config: Dict,
        user_id: int,
    ) -> Dict:
        """
        基于镜像创建模型服务
        协调Harbor、mManager和数据库的操作
        """
        try:
            # 1. 验证镜像和权限
            image = await self._get_image_with_validation(db, image_id, user_id)

            # 2. 检查镜像是否可以创建服务
            if not image.can_create_service:
                raise Exception(
                    f"镜像 {image.name}:{image.tag} 无法创建服务（状态: {image.status}，已有服务: {image.service_count}/2）"
                )

            # 3. 选择最优控制器
            controller_info = await mmanager_client.select_optimal_controller(
                db, service_config.get("requirements", {})
            )
            if not controller_info:
                raise Exception("没有可用的mManager控制器")

            controller_id = controller_info["id"]
            full_image_name = image.full_name

            # 4. 确保镜像在目标控制器上可用
            image_available = await mmanager_client.ensure_image_available(
                controller_id, full_image_name, self.harbor_auth
            )
            if not image_available:
                raise Exception(
                    f"无法在控制器 {controller_id} 上获取镜像 {full_image_name}"
                )

            # 5. 创建容器配置
            container_config = {
                "image": full_image_name,
                "name": service_config.get("service_name"),
                "ports": service_config.get("ports", {}),
                "environment": service_config.get("environment", {}),
                "volumes": service_config.get("volumes", {}),
                "command": service_config.get("command"),
                "restart_policy": service_config.get(
                    "restart_policy", "unless-stopped"
                ),
                "resource_limits": {
                    "cpu": service_config.get("cpu_limit", "0.5"),
                    "memory": service_config.get("memory_limit", "512m"),
                },
            }

            # 6. 在mManager控制器上创建容器
            create_result = await mmanager_client.create_container(
                controller_id, container_config
            )

            # 7. 创建服务数据库记录
            service_record = ModelService(
                repository_id=repository_id,
                user_id=user_id,
                image_id=image_id,
                service_name=service_config.get("service_name"),
                model_id=create_result.get("container_id"),
                model_ip=controller_info.get("host", "localhost"),
                description=service_config.get("description", ""),
                docker_image=full_image_name,
                gradio_port=service_config.get("gradio_port"),
                service_url=f"http://{controller_info.get('host')}:{service_config.get('gradio_port', 7860)}",
                status="created",
                health_status="unknown",
                cpu_limit=service_config.get("cpu_limit", "0.5"),
                memory_limit=service_config.get("memory_limit", "512m"),
                is_public=service_config.get("is_public", False),
                priority=service_config.get("priority", 2),
            )

            db.add(service_record)
            await db.commit()
            await db.refresh(service_record)

            # 8. 启动容器
            start_result = await mmanager_client.start_container(
                controller_id, create_result.get("container_id")
            )

            if start_result.get("status") == "running":
                await db.execute(
                    update(ModelService)
                    .where(ModelService.id == service_record.id)
                    .values(status="running", health_status="healthy")
                )
                await db.commit()

            return {
                "service_id": service_record.id,
                "container_id": create_result.get("container_id"),
                "controller_id": controller_id,
                "status": "created",
                "service_url": service_record.service_url,
                "message": "服务创建成功",
            }

        except Exception as e:
            logger.error(f"服务创建失败: {e}")
            raise

    # ================== 工具方法 ==================

    async def _get_repository_with_validation(
        self,
        db: AsyncSession,
        repository_id: int,
        user_id: Optional[int],
        require_ownership: bool = False,
    ) -> Repository:
        """获取仓库并验证权限"""
        result = await db.execute(
            select(Repository).where(Repository.id == repository_id)
        )
        repository = result.scalar_one_or_none()
        if not repository:
            raise Exception(f"仓库不存在")

        # 如果需要所有权（如上传、删除操作），必须有用户且为拥有者
        if require_ownership:
            if not user_id or repository.owner_id != user_id:
                raise Exception(f"无权限访问仓库 {repository.name}")

        # 如果只是查看操作，检查仓库可见性
        elif not require_ownership and repository.visibility == "private":
            # 私有仓库需要用户且为拥有者
            if not user_id or repository.owner_id != user_id:
                raise Exception(f"无权限访问仓库 {repository.name}")

        return repository

    async def _get_image_with_validation(
        self, db: AsyncSession, image_id: int, user_id: int
    ) -> Image:
        """获取镜像并验证权限"""
        result = await db.execute(
            select(Image)
            .join(Repository)
            .where(and_(Image.id == image_id, Repository.owner_id == user_id))
        )
        image = result.scalar_one_or_none()

        if not image:
            raise Exception(f"镜像 {image_id} 不存在或无权限访问")

        return image

    async def _add_build_log(
        self,
        db: AsyncSession,
        image_id: int,
        stage: str,
        message: str,
        level: str = "info",
    ):
        """添加构建日志"""
        log_record = ImageBuildLog(
            image_id=image_id, stage=stage, message=message, level=level
        )
        db.add(log_record)
        await db.commit()

    # ================== 查询方法 ==================

    async def list_repository_images(
        self, db: AsyncSession, repository_id: int, user_id: Optional[int]
    ) -> List[Dict]:
        """列出仓库的所有镜像"""
        repository = await self._get_repository_with_validation(
            db, repository_id, user_id, require_ownership=False
        )
        
        # 检查用户是否为仓库所有者
        is_owner = user_id is not None and repository.owner_id == user_id

        # 构建查询条件
        conditions = [
            Image.repository_id == repository_id,
            Image.status != "deleted"
        ]
        
        # 如果不是仓库所有者，只显示公开镜像
        if not is_owner:
            conditions.append(Image.is_public == True)

        result = await db.execute(
            select(Image)
            .options(selectinload(Image.services))
            .where(and_(*conditions))
            .order_by(Image.created_at.desc())
        )
        images = result.scalars().all()

        return [
            {
                "id": img.id,
                "name": img.original_name,
                "tag": img.original_tag,
                "description": img.description,
                "status": img.status,
                "upload_progress": img.upload_progress,
                "size": img.harbor_size,
                "created_at": img.created_at,
                "is_public": img.is_public,
                "service_count": len(img.services) if hasattr(img, 'services') and img.services else 0,
                "can_create_service": img.status == "ready" and (len(img.services) if hasattr(img, 'services') and img.services else 0) < 2,
            }
            for img in images
        ]

    async def get_image_services(
        self, db: AsyncSession, image_id: int, user_id: int
    ) -> List[Dict]:
        """获取镜像的所有服务"""
        await self._get_image_with_validation(db, image_id, user_id)

        result = await db.execute(
            select(ModelService)
            .where(
                and_(
                    ModelService.image_id == image_id, ModelService.status != "deleted"
                )
            )
            .order_by(ModelService.created_at.desc())
        )
        services = result.scalars().all()

        return [
            {
                "id": svc.id,
                "service_name": svc.service_name,
                "status": svc.status,
                "health_status": svc.health_status,
                "service_url": svc.service_url,
                "created_at": svc.created_at,
            }
            for svc in services
        ]


# 全局镜像管理服务实例
image_management_service = ImageManagementService()
