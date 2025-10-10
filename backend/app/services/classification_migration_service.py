"""
分类迁移服务 - 自动同步README
用于在分类修改时批量更新所有相关仓库的README

核心原则：
- 数据库是数据源（Single Source of Truth）
- README是显示层（自动同步）
- 用户无需手动修改README
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.repository import Repository, RepositoryFile, RepositoryClassification, RepositoryTaskClassification
from app.models.classification import Classification
from app.models.task_classification import TaskClassification
from app.utils.yaml_parser import YAMLFrontmatterParser
from app.services.minio_service import MinIOService
import io

logger = logging.getLogger(__name__)


class ClassificationMigrationService:
    """分类迁移服务 - 自动更新README"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.yaml_parser = YAMLFrontmatterParser()
        self.minio_service = MinIOService()

    async def sync_repository_readme(self, repository_id: int) -> Dict:
        """
        同步单个仓库的README
        从数据库读取分类信息，更新到README

        Args:
            repository_id: 仓库ID

        Returns:
            同步结果
        """
        try:
            # 获取仓库
            query = select(Repository).where(Repository.id == repository_id)
            result = await self.db.execute(query)
            repository = result.scalar_one_or_none()

            if not repository:
                return {"success": False, "error": "Repository not found"}

            # 获取当前README内容
            readme_content = repository.readme_content or self._generate_default_readme(repository)

            # 解析README
            metadata, content = self.yaml_parser.extract_content(readme_content)
            if metadata is None:
                metadata = {}

            # 从数据库获取最新分类信息
            sphere_classifications = await self._get_repository_sphere_classifications(repository_id)
            task_classifications = await self._get_repository_task_classifications(repository_id)

            # 更新元数据
            metadata["classifications"] = sphere_classifications
            metadata["tasks"] = task_classifications  # 使用 "tasks" 而不是 "task_classifications"

            # 重新生成README
            updated_readme = self.yaml_parser.create_frontmatter(metadata, content)

            # 更新数据库
            repository.readme_content = updated_readme

            # 更新MinIO中的README文件
            await self._update_readme_in_minio(repository, updated_readme)

            logger.info(f"Successfully synced README for repository {repository_id}")

            return {
                "success": True,
                "repository_id": repository_id,
                "sphere_classifications": sphere_classifications,
                "task_classifications": task_classifications
            }

        except Exception as e:
            logger.error(f"Failed to sync README for repository {repository_id}: {e}")
            return {"success": False, "error": str(e)}

    async def batch_sync_readmes_for_sphere_classification(
        self,
        classification_id: int
    ) -> Dict:
        """
        批量同步使用某个sphere分类的所有仓库README

        Args:
            classification_id: Sphere分类ID

        Returns:
            批量同步结果
        """
        logger.info(f"Starting batch sync for sphere classification {classification_id}")

        # 获取所有使用该分类的仓库
        repositories = await self._get_repositories_with_sphere_classification(classification_id)

        results = {
            "classification_id": classification_id,
            "total_repositories": len(repositories),
            "updated": 0,
            "failed": 0,
            "details": []
        }

        for repository in repositories:
            result = await self.sync_repository_readme(repository.id)

            if result["success"]:
                results["updated"] += 1
                results["details"].append({
                    "repository_id": repository.id,
                    "full_name": repository.full_name,
                    "status": "updated"
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "repository_id": repository.id,
                    "full_name": repository.full_name,
                    "status": "failed",
                    "error": result.get("error")
                })

        # 提交所有更改
        await self.db.commit()

        logger.info(f"Batch sync completed: {results}")
        return results

    async def batch_sync_readmes_for_task_classification(
        self,
        task_classification_id: int
    ) -> Dict:
        """
        批量同步使用某个task分类的所有仓库README

        Args:
            task_classification_id: Task分类ID

        Returns:
            批量同步结果
        """
        logger.info(f"Starting batch sync for task classification {task_classification_id}")

        # 获取所有使用该分类的仓库
        repositories = await self._get_repositories_with_task_classification(task_classification_id)

        results = {
            "task_classification_id": task_classification_id,
            "total_repositories": len(repositories),
            "updated": 0,
            "failed": 0,
            "details": []
        }

        for repository in repositories:
            result = await self.sync_repository_readme(repository.id)

            if result["success"]:
                results["updated"] += 1
                results["details"].append({
                    "repository_id": repository.id,
                    "full_name": repository.full_name,
                    "status": "updated"
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "repository_id": repository.id,
                    "full_name": repository.full_name,
                    "status": "failed",
                    "error": result.get("error")
                })

        # 提交所有更改
        await self.db.commit()

        logger.info(f"Batch sync completed: {results}")
        return results

    async def _get_repository_sphere_classifications(self, repository_id: int) -> List[str]:
        """获取仓库的sphere分类名称列表（只返回最小级别）"""
        query = (
            select(Classification.id, Classification.name, Classification.level, Classification.parent_id)
            .select_from(RepositoryClassification)
            .join(Classification)
            .where(RepositoryClassification.repository_id == repository_id)
            .order_by(Classification.level.desc(), Classification.name)
        )

        result = await self.db.execute(query)
        all_classifications = result.fetchall()

        if not all_classifications:
            return []

        # 构建分类ID到信息的映射
        classification_map = {
            cls.id: {"name": cls.name, "level": cls.level, "parent_id": cls.parent_id}
            for cls in all_classifications
        }

        # 找出最小级别的分类（即没有子分类被选中的分类）
        leaf_classifications = []

        for cls_id, cls_info in classification_map.items():
            # 检查是否有子分类也被选中
            has_selected_child = False
            for other_id, other_info in classification_map.items():
                if other_info["parent_id"] == cls_id:
                    has_selected_child = True
                    break

            # 如果没有子分类被选中，则这是一个叶子节点
            if not has_selected_child:
                leaf_classifications.append(cls_info["name"])

        return sorted(leaf_classifications)

    async def _get_repository_task_classifications(self, repository_id: int) -> List[str]:
        """获取仓库的task分类名称列表"""
        query = (
            select(TaskClassification.name)
            .select_from(RepositoryTaskClassification)
            .join(TaskClassification)
            .where(RepositoryTaskClassification.repository_id == repository_id)
            .order_by(TaskClassification.sort_order)
        )

        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]

    async def _get_repositories_with_sphere_classification(
        self,
        classification_id: int
    ) -> List[Repository]:
        """获取使用某个sphere分类的所有仓库"""
        query = (
            select(Repository)
            .join(RepositoryClassification)
            .where(RepositoryClassification.classification_id == classification_id)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _get_repositories_with_task_classification(
        self,
        task_classification_id: int
    ) -> List[Repository]:
        """获取使用某个task分类的所有仓库"""
        query = (
            select(Repository)
            .join(RepositoryTaskClassification)
            .where(RepositoryTaskClassification.task_classification_id == task_classification_id)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _update_readme_in_minio(self, repository: Repository, content: str):
        """更新MinIO中的README文件"""
        # 查找README文件记录
        query = select(RepositoryFile).where(
            and_(
                RepositoryFile.repository_id == repository.id,
                RepositoryFile.file_path.ilike("README.md"),
                RepositoryFile.is_deleted == False
            )
        )
        result = await self.db.execute(query)
        readme_file = result.scalar_one_or_none()

        if readme_file:
            # 上传新内容到MinIO
            content_bytes = content.encode('utf-8')

            await self.minio_service.upload_file_stream(
                bucket_name=readme_file.minio_bucket,
                object_key=readme_file.minio_object_key,
                file_stream=io.BytesIO(content_bytes),
                file_size=len(content_bytes),
                content_type="text/markdown"
            )

            # 更新文件大小
            readme_file.file_size = len(content_bytes)

            logger.info(f"Updated README in MinIO for repository {repository.id}")

    def _generate_default_readme(self, repository: Repository) -> str:
        """生成默认README内容"""
        return f"""---
license: {repository.license or 'mit'}
classifications: []
tasks: []
---

# {repository.name}

{repository.description or '这是一个新创建的仓库。'}

## 描述

请在这里添加详细描述。

## 使用方法

请在这里添加使用说明。
"""
