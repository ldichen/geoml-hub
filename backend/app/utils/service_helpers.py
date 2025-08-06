"""
服务管理辅助工具 - 减少重复逻辑
"""

from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.user import User
from app.models.repository import Repository
from app.models.service import ModelService
from app.models.image import Image


class ServicePermissionManager:
    """服务权限管理器"""

    @staticmethod
    def check_repository_owner_permission(
        repository: Repository, current_user: User, action: str = "操作"
    ):
        """检查仓库所有者权限"""
        if repository.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail=f"只有仓库所有者可以{action}")

    @staticmethod
    def check_service_owner_permission(
        service: ModelService, current_user: User, action: str = "操作"
    ):
        """检查服务所有者权限"""
        if service.user_id != current_user.id:
            raise HTTPException(status_code=403, detail=f"只有服务所有者可以{action}")


class ServiceValidator:
    """服务验证器"""

    @staticmethod
    async def validate_image_for_service(
        db: AsyncSession, image_id: int, repository_id: int
    ) -> Image:
        """验证镜像是否可用于创建服务"""
        from sqlalchemy.orm import selectinload

        image_query = (
            select(Image)
            .options(selectinload(Image.services))
            .where(and_(Image.id == image_id, Image.repository_id == repository_id))
        )
        result = await db.execute(image_query)
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(status_code=404, detail="指定的镜像不存在")
        if image.status != "ready":
            raise HTTPException(status_code=400, detail="镜像尚未就绪，无法创建服务")

        # 手动计算service_count来避免lazy loading
        active_service_count = len([s for s in image.services if s.status != "deleted"])
        if active_service_count >= 2:
            raise HTTPException(status_code=400, detail="该镜像已达到最大服务数量限制")

        return image

    @staticmethod
    async def validate_services_belong_to_repository(
        db: AsyncSession, service_ids: List[int], repository_id: int
    ) -> tuple[List[ModelService], List[int]]:
        """批量验证服务属于指定仓库"""
        valid_services = []
        invalid_service_ids = []

        for service_id in service_ids:
            service_query = select(ModelService).where(
                and_(
                    ModelService.id == service_id,
                    ModelService.repository_id == repository_id,
                )
            )
            result = await db.execute(service_query)
            service = result.scalar_one_or_none()

            if service:
                valid_services.append(service)
            else:
                invalid_service_ids.append(service_id)

        return valid_services, invalid_service_ids


class ServiceCreationManager:
    """服务创建管理器"""

    @staticmethod
    async def create_service_from_image(
        db: AsyncSession,
        service_data,
        repository: Repository,
        current_user: User,
        service_manager,
    ):
        """基于已有镜像创建服务的通用逻辑"""
        # 1. 检查权限
        ServicePermissionManager.check_repository_owner_permission(
            repository, current_user, "创建服务"
        )

        # 2. 验证镜像
        image = await ServiceValidator.validate_image_for_service(
            db, service_data.image_id, repository.id
        )

        # 3. 创建服务
        service = await service_manager.create_service(
            db=db,
            service_data=service_data,
            repository_id=repository.id,
            user_id=current_user.id,
        )

        return service, image


class BatchOperationManager:
    """批量操作管理器"""

    @staticmethod
    async def execute_batch_service_operation(
        db: AsyncSession,
        service_ids: List[int],
        repository: Repository,
        current_user: User,
        operation_func,
        background_tasks,
        operation_name: str,
    ):
        """执行批量服务操作的通用逻辑"""
        # 1. 检查权限
        ServicePermissionManager.check_repository_owner_permission(
            repository, current_user, f"批量{operation_name}服务"
        )

        # 2. 验证服务
        valid_services, invalid_service_ids = (
            await ServiceValidator.validate_services_belong_to_repository(
                db, service_ids, repository.id
            )
        )

        # 3. 执行操作
        successful = []
        failed = []

        # 处理无效服务
        for service_id in invalid_service_ids:
            failed.append(
                {"service_id": service_id, "error": "服务不存在或不属于该仓库"}
            )

        # 处理有效服务
        for service in valid_services:
            try:
                background_tasks.add_task(
                    operation_func,
                    db=db,
                    service_id=service.id,
                    user_id=current_user.id,
                )
                successful.append(service.id)
            except Exception as e:
                failed.append({"service_id": service.id, "error": str(e)})

        return successful, failed
