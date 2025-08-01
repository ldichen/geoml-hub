"""
元数据管理服务

提供仓库元数据的解析、验证、更新和管理功能
支持 YAML frontmatter 格式和 Hugging Face 兼容的元数据结构
"""

import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel, ValidationError

from app.models.repository import Repository, RepositoryFile
from app.models.user import User
from app.utils.yaml_parser import YAMLFrontmatterParser
from app.services.minio_service import MinIOService

logger = logging.getLogger(__name__)


class MetadataSchema(BaseModel):
    """元数据验证模式"""
    
    # 基础信息
    license: Optional[str] = None
    language: Optional[List[str]] = None
    library_name: Optional[str] = None
    
    # 任务相关
    pipeline_tag: Optional[str] = None
    task_categories: Optional[List[str]] = None
    task_ids: Optional[List[str]] = None
    
    # 模型相关
    base_model: Optional[str] = None
    model_type: Optional[str] = None
    architectures: Optional[List[str]] = None
    
    # 标签和分类
    tags: Optional[List[str]] = None
    datasets: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    
    # 自定义字段
    extra_fields: Optional[Dict[str, Any]] = None


class MetadataTemplate(BaseModel):
    """元数据模板"""
    
    id: Optional[int] = None
    name: str
    description: str
    schema_type: str  # model, dataset, space
    template: Dict[str, Any]
    is_system: bool = False
    created_at: Optional[datetime] = None


class MetadataValidationResult(BaseModel):
    """元数据验证结果"""
    
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
    score: float = 0.0  # 0-100分


class MetadataService:
    """元数据管理服务"""
    
    def __init__(self, db: AsyncSession, minio_service: MinIOService):
        self.db = db
        self.minio_service = minio_service
        self.yaml_parser = YAMLFrontmatterParser()
    
    async def get_repository_metadata(
        self, 
        repository: Repository
    ) -> Dict[str, Any]:
        """获取仓库的YAML元数据"""
        
        # 首先从数据库获取缓存的元数据
        if repository.repo_metadata:
            return repository.repo_metadata
        
        # 如果没有缓存，从README.md解析
        readme_file = await self._get_readme_file(repository.id)
        if not readme_file:
            return {}
        
        try:
            # 从MinIO获取文件内容
            content = await self.minio_service.get_text_content(
                bucket_name=readme_file.minio_bucket,
                object_name=readme_file.minio_object_key
            )
            
            # 解析YAML frontmatter
            metadata = self.yaml_parser.parse(content)
            
            # 缓存到数据库
            if metadata:
                repository.repo_metadata = metadata
                await self.db.commit()
            
            return metadata or {}
            
        except Exception as e:
            logger.error(f"Failed to parse metadata for repository {repository.id}: {e}")
            return {}
    
    async def update_repository_metadata(
        self,
        repository: Repository,
        metadata: Dict[str, Any],
        update_readme: bool = True
    ) -> bool:
        """更新仓库元数据"""
        
        try:
            # 验证元数据
            validation_result = await self.validate_metadata(metadata, repository.repo_type)
            if not validation_result.is_valid:
                logger.warning(f"Metadata validation failed: {validation_result.errors}")
            
            # 更新数据库中的元数据
            repository.repo_metadata = metadata
            
            # 如果需要更新README.md
            if update_readme:
                success = await self._update_readme_metadata(repository, metadata)
                if not success:
                    logger.warning("Failed to update README.md, but database metadata was updated")
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata for repository {repository.id}: {e}")
            await self.db.rollback()
            return False
    
    async def validate_metadata(
        self,
        metadata: Dict[str, Any],
        schema_type: str = "model"
    ) -> MetadataValidationResult:
        """验证元数据格式和内容"""
        
        result = MetadataValidationResult(is_valid=True)
        
        try:
            # 基础验证
            if not isinstance(metadata, dict):
                result.is_valid = False
                result.errors.append("Metadata must be a dictionary")
                return result
            
            # 使用Pydantic进行结构验证
            try:
                MetadataSchema(**metadata)
                result.score += 50
            except ValidationError as e:
                result.warnings.extend([str(error) for error in e.errors()])
            
            # 特定字段验证
            result = await self._validate_specific_fields(metadata, schema_type, result)
            
            # 计算最终分数
            if result.is_valid:
                result.score = min(100, result.score + 30)
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating metadata: {e}")
            result.is_valid = False
            result.errors.append(f"Validation error: {str(e)}")
            return result
    
    async def get_metadata_templates(
        self,
        schema_type: Optional[str] = None
    ) -> List[MetadataTemplate]:
        """获取元数据模板列表"""
        
        # 内置模板
        templates = [
            MetadataTemplate(
                id=1,
                name="基础模型模板",
                description="适用于机器学习模型的基础元数据模板",
                schema_type="model",
                is_system=True,
                template={
                    "license": "mit",
                    "tags": ["machine-learning", "geospatial"],
                    "pipeline_tag": "text-classification",
                    "language": ["en"],
                    "datasets": ["dataset-name"],
                    "metrics": ["accuracy", "f1"],
                    "base_model": "bert-base-uncased",
                    "model_type": "bert"
                }
            ),
            MetadataTemplate(
                id=2,
                name="地理空间模型模板",
                description="专门用于地理空间AI模型的元数据模板",
                schema_type="model",
                is_system=True,
                template={
                    "license": "apache-2.0",
                    "tags": ["geospatial", "earth-observation", "satellite-imagery"],
                    "pipeline_tag": "image-classification",
                    "task_categories": ["computer-vision"],
                    "datasets": ["landsat-8", "sentinel-2"],
                    "metrics": ["accuracy", "iou", "dice"],
                    "library_name": "pytorch",
                    "architectures": ["resnet", "unet"]
                }
            ),
            MetadataTemplate(
                id=3,
                name="数据集模板",
                description="适用于数据集的基础元数据模板",
                schema_type="dataset",
                is_system=True,
                template={
                    "license": "cc-by-4.0",
                    "tags": ["dataset", "geospatial"],
                    "task_categories": ["image-classification"],
                    "language": ["en"],
                    "size_categories": ["10K<n<100K"],
                    "format": "parquet"
                }
            )
        ]
        
        if schema_type:
            templates = [t for t in templates if t.schema_type == schema_type]
        
        return templates
    
    async def generate_model_card(
        self,
        repository: Repository,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成模型卡片内容"""
        
        if not metadata:
            metadata = await self.get_repository_metadata(repository)
        
        # 生成模型卡片内容
        card_content = f"# {repository.name}\n\n"
        
        if repository.description:
            card_content += f"{repository.description}\n\n"
        
        # 添加元数据信息
        if metadata:
            card_content += "## 模型信息\n\n"
            
            if metadata.get("pipeline_tag"):
                card_content += f"- **任务类型**: {metadata['pipeline_tag']}\n"
            
            if metadata.get("base_model"):
                card_content += f"- **基础模型**: {metadata['base_model']}\n"
            
            if metadata.get("license"):
                card_content += f"- **许可证**: {metadata['license']}\n"
            
            if metadata.get("tags"):
                tags = ", ".join(metadata["tags"])
                card_content += f"- **标签**: {tags}\n"
            
            card_content += "\n"
        
        # 添加使用示例
        card_content += "## 使用方法\n\n"
        card_content += "```python\n"
        card_content += f"# 下载并使用 {repository.name}\n"
        card_content += "# 具体使用方法请参考仓库文档\n"
        card_content += "```\n\n"
        
        return card_content
    
    async def search_by_metadata(
        self,
        query_metadata: Dict[str, Any],
        limit: int = 20,
        offset: int = 0
    ) -> List[Repository]:
        """基于元数据搜索仓库"""
        
        # 构建搜索查询
        query = select(Repository).where(Repository.is_active == True)
        
        # 添加元数据条件
        if query_metadata:
            for key, value in query_metadata.items():
                if isinstance(value, list):
                    # 数组字段搜索
                    query = query.where(
                        Repository.repo_metadata.op("->>")(key).op("&&")(value)
                    )
                else:
                    # 简单字段搜索
                    query = query.where(
                        Repository.repo_metadata.op("->>")(key) == str(value)
                    )
        
        query = query.order_by(desc(Repository.updated_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_metadata_statistics(self) -> Dict[str, Any]:
        """获取元数据统计信息"""
        
        try:
            # 总仓库数
            total_repos_query = select(func.count(Repository.id)).where(
                Repository.is_active == True
            )
            total_repos_result = await self.db.execute(total_repos_query)
            total_repos = total_repos_result.scalar() or 0
            
            # 有元数据的仓库数
            with_metadata_query = select(func.count(Repository.id)).where(
                and_(
                    Repository.is_active == True,
                    Repository.repo_metadata.isnot(None)
                )
            )
            with_metadata_result = await self.db.execute(with_metadata_query)
            with_metadata = with_metadata_result.scalar() or 0
            
            # 计算覆盖率
            coverage_rate = (with_metadata / total_repos * 100) if total_repos > 0 else 0
            
            return {
                "total_repositories": total_repos,
                "repositories_with_metadata": with_metadata,
                "metadata_coverage_rate": round(coverage_rate, 2),
                "most_common_tags": await self._get_common_tags(),
                "most_common_licenses": await self._get_common_licenses(),
                "task_distribution": await self._get_task_distribution()
            }
            
        except Exception as e:
            logger.error(f"Error getting metadata statistics: {e}")
            return {}
    
    # 私有方法
    
    async def _get_readme_file(self, repository_id: int) -> Optional[RepositoryFile]:
        """获取README.md文件"""
        
        query = select(RepositoryFile).where(
            and_(
                RepositoryFile.repository_id == repository_id,
                RepositoryFile.filename == "README.md",
                RepositoryFile.is_deleted == False
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _update_readme_metadata(
        self,
        repository: Repository,
        metadata: Dict[str, Any]
    ) -> bool:
        """更新README.md中的YAML frontmatter"""
        
        try:
            readme_file = await self._get_readme_file(repository.id)
            if not readme_file:
                return False
            
            # 获取现有内容
            current_content = await self.minio_service.get_text_content(
                bucket_name=readme_file.minio_bucket,
                object_name=readme_file.minio_object_key
            )
            
            # 生成新的YAML frontmatter
            yaml_content = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
            
            # 提取现有的markdown内容（去除frontmatter）
            _, markdown_content = self.yaml_parser.extract_content(current_content)
            
            # 合并新内容
            new_content = f"---\n{yaml_content}---\n\n{markdown_content}"
            
            # 上传更新的内容
            await self.minio_service.upload_text(
                bucket_name=readme_file.minio_bucket,
                object_name=readme_file.minio_object_key,
                content=new_content
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update README metadata: {e}")
            return False
    
    async def _validate_specific_fields(
        self,
        metadata: Dict[str, Any],
        schema_type: str,
        result: MetadataValidationResult
    ) -> MetadataValidationResult:
        """验证特定字段"""
        
        # 验证许可证
        if "license" in metadata:
            valid_licenses = [
                "mit", "apache-2.0", "gpl-3.0", "bsd-3-clause", 
                "cc-by-4.0", "cc-by-sa-4.0", "other"
            ]
            if metadata["license"] not in valid_licenses:
                result.warnings.append(f"License '{metadata['license']}' is not commonly used")
            else:
                result.score += 10
        
        # 验证标签
        if "tags" in metadata:
            if isinstance(metadata["tags"], list) and len(metadata["tags"]) > 0:
                result.score += 10
            else:
                result.warnings.append("Tags should be a non-empty list")
        
        # 验证任务类型
        if schema_type == "model" and "pipeline_tag" in metadata:
            valid_tasks = [
                "text-classification", "text-generation", "image-classification",
                "object-detection", "semantic-segmentation", "question-answering"
            ]
            if metadata["pipeline_tag"] in valid_tasks:
                result.score += 10
            else:
                result.suggestions.append("Consider using a standard pipeline_tag for better discoverability")
        
        return result
    
    async def _get_common_tags(self) -> List[Dict[str, Any]]:
        """获取最常用的标签"""
        
        # 这里简化实现，实际应该从数据库统计
        return [
            {"tag": "machine-learning", "count": 150},
            {"tag": "geospatial", "count": 120},
            {"tag": "pytorch", "count": 90},
            {"tag": "computer-vision", "count": 85},
            {"tag": "satellite-imagery", "count": 70}
        ]
    
    async def _get_common_licenses(self) -> List[Dict[str, Any]]:
        """获取最常用的许可证"""
        
        return [
            {"license": "mit", "count": 80},
            {"license": "apache-2.0", "count": 60},
            {"license": "cc-by-4.0", "count": 40},
            {"license": "gpl-3.0", "count": 20}
        ]
    
    async def _get_task_distribution(self) -> List[Dict[str, Any]]:
        """获取任务类型分布"""
        
        return [
            {"task": "image-classification", "count": 100},
            {"task": "text-classification", "count": 80},
            {"task": "object-detection", "count": 60},
            {"task": "semantic-segmentation", "count": 40}
        ]