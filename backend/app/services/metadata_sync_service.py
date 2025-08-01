"""
元数据双向同步服务

提供仓库元数据与README.md之间的双向同步功能
确保数据库字段(tags, license, base_model)与YAML frontmatter保持一致
支持classifications的双向同步
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.repository import Repository, RepositoryFile, RepositoryClassification
from app.models.classification import Classification
from app.utils.yaml_parser import YAMLFrontmatterParser
from app.services.minio_service import MinIOService

logger = logging.getLogger(__name__)


class MetadataSyncService:
    """元数据双向同步服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.yaml_parser = YAMLFrontmatterParser()
        self.minio_service = MinIOService()
    
    async def sync_repository_to_readme(self, repository: Repository) -> str:
        """
        将数据库中的仓库字段同步到README.md的YAML frontmatter
        
        Args:
            repository: 仓库对象
            
        Returns:
            更新后的README.md内容
        """
        try:
            # 生成YAML frontmatter
            yaml_metadata = await self._build_yaml_from_repository(repository)
            
            # 获取现有README内容并提取markdown部分
            markdown_content = await self._extract_markdown_content(repository)
            
            # 组合新的README内容
            if yaml_metadata:
                yaml_content = self._format_yaml_content(yaml_metadata)
                updated_readme = f"---\n{yaml_content}\n---\n\n{markdown_content}"
            else:
                updated_readme = markdown_content
            
            return updated_readme
            
        except Exception as e:
            logger.error(f"Failed to sync repository to README: {e}")
            return repository.readme_content or ""
    
    async def sync_readme_to_repository(self, repository: Repository, readme_content: str) -> bool:
        """
        将README.md的YAML frontmatter同步到数据库字段
        
        Args:
            repository: 仓库对象
            readme_content: README.md内容
            
        Returns:
            是否同步成功
        """
        try:
            # 解析YAML frontmatter
            metadata = self.yaml_parser.parse(readme_content)
            
            if not metadata:
                return True  # 没有metadata不算错误
            
            # 同步基础字段
            await self._sync_basic_fields(repository, metadata)
            
            # 同步分类字段
            await self._sync_classifications(repository, metadata)
            
            # 更新repo_metadata
            await self._update_repo_metadata(repository, metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync README to repository: {e}")
            return False
    
    async def ensure_bidirectional_sync(self, repository: Repository, readme_content: Optional[str] = None) -> str:
        """
        确保双向同步
        
        Args:
            repository: 仓库对象
            readme_content: 新的README内容（可选）
            
        Returns:
            最终的README内容
        """
        try:
            if readme_content:
                # README被更新，同步到数据库
                success = await self.sync_readme_to_repository(repository, readme_content)
                if not success:
                    logger.warning("Failed to sync README to repository")
                return readme_content
            else:
                # 数据库字段被更新，同步到README
                return await self.sync_repository_to_readme(repository)
                
        except Exception as e:
            logger.error(f"Failed to ensure bidirectional sync: {e}")
            return repository.readme_content or ""
    
    # 私有方法
    
    async def _build_yaml_from_repository(self, repository: Repository) -> Dict[str, Any]:
        """从仓库对象构建YAML元数据"""
        yaml_data = {}
        
        # 基础字段
        if repository.license:
            yaml_data["license"] = repository.license
        
        if repository.tags:
            yaml_data["tags"] = repository.tags
        
        if repository.base_model:
            yaml_data["base_model"] = repository.base_model
        
        # Pipeline tag 基于仓库类型 (removed automatic assignment for models)
        pipeline_tags = {
            "dataset": "dataset",
            "space": "space",
        }
        if repository.repo_type in pipeline_tags:
            yaml_data["pipeline_tag"] = pipeline_tags[repository.repo_type]
        
        # 从关联分类获取classifications
        try:
            classifications = await self._get_repository_classifications(repository.id)
            if classifications:
                yaml_data["classifications"] = classifications
        except Exception as e:
            logger.warning(f"Failed to load classifications for repository {repository.id}: {e}")
        
        # 从repo_metadata获取其他字段
        if repository.repo_metadata:
            for key in ["model_type", "task", "language", "architectures", "datasets", "metrics"]:
                if key in repository.repo_metadata:
                    yaml_data[key] = repository.repo_metadata[key]
        
        return yaml_data
    
    async def _extract_markdown_content(self, repository: Repository) -> str:
        """提取README的markdown内容（去除YAML frontmatter）"""
        current_readme = repository.readme_content or ""
        
        if not current_readme:
            # 生成默认内容
            repo_type_names = {"model": "模型", "dataset": "数据集", "space": "空间"}
            repo_type_desc = repo_type_names.get(repository.repo_type, "项目")
            
            return f"""# {repository.name}

{repository.description or f"这是一个新创建的{repo_type_desc}仓库。"}

## 描述

请在这里添加关于你的{repo_type_desc}的详细描述。

## 使用方法

请在这里添加使用说明。

## 许可证

本项目使用 {repository.license or 'MIT'} 许可证。

## 贡献

欢迎提交 Pull Request 或者 Issue。
"""
        
        # 提取markdown内容（去除YAML frontmatter）
        _, markdown_content = self.yaml_parser.extract_content(current_readme)
        return markdown_content or current_readme
    
    def _format_yaml_content(self, yaml_data: Dict[str, Any]) -> str:
        """格式化YAML内容"""
        yaml_lines = []
        
        # 按固定顺序排列字段
        field_order = ["license", "tags", "base_model", "pipeline_tag", "classifications", 
                      "model_type", "task", "language", "architectures", "datasets", "metrics"]
        
        for field in field_order:
            if field in yaml_data:
                value = yaml_data[field]
                if isinstance(value, list):
                    yaml_lines.append(f"{field}:")
                    for item in value:
                        yaml_lines.append(f"  - {item}")
                elif isinstance(value, dict):
                    yaml_lines.append(f"{field}:")
                    for k, v in value.items():
                        yaml_lines.append(f"  {k}: {v}")
                else:
                    yaml_lines.append(f"{field}: {value}")
        
        # 添加其他字段
        for field, value in yaml_data.items():
            if field not in field_order:
                if isinstance(value, list):
                    yaml_lines.append(f"{field}:")
                    for item in value:
                        yaml_lines.append(f"  - {item}")
                elif isinstance(value, dict):
                    yaml_lines.append(f"{field}:")
                    for k, v in value.items():
                        yaml_lines.append(f"  {k}: {v}")
                else:
                    yaml_lines.append(f"{field}: {value}")
        
        return "\n".join(yaml_lines)
    
    async def _sync_basic_fields(self, repository: Repository, metadata: Dict[str, Any]):
        """同步基础字段"""
        if "license" in metadata:
            repository.license = metadata["license"]
        
        if "tags" in metadata and isinstance(metadata["tags"], list):
            repository.tags = metadata["tags"]
        
        if "base_model" in metadata:
            repository.base_model = metadata["base_model"]
    
    async def _sync_classifications(self, repository: Repository, metadata: Dict[str, Any]):
        """同步分类字段"""
        if "classifications" in metadata and isinstance(metadata["classifications"], list):
            # 清除现有分类
            await self._remove_repository_classifications(repository.id)
            
            # 添加新分类
            for classification_name in metadata["classifications"]:
                classification = await self._find_classification_by_name(classification_name)
                if classification:
                    await self._add_repository_classification(repository.id, classification.id)
    
    async def _update_repo_metadata(self, repository: Repository, metadata: Dict[str, Any]):
        """更新repo_metadata字段"""
        if not repository.repo_metadata:
            repository.repo_metadata = {}
        
        repo_metadata = repository.repo_metadata.copy()
        
        # 同步其他元数据字段
        metadata_fields = ["pipeline_tag", "model_type", "task", "language", 
                          "architectures", "datasets", "metrics", "base_model"]
        
        for field in metadata_fields:
            if field in metadata:
                repo_metadata[field] = metadata[field]
        
        repository.repo_metadata = repo_metadata
    
    async def _get_repository_classifications(self, repository_id: int) -> List[str]:
        """获取仓库的分类名称列表，只返回最小级别（最具体）的分类"""
        # 获取所有关联的分类及其层级信息
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
        classification_ids = set(classification_map.keys())
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
    
    async def _find_classification_by_name(self, name: str) -> Optional[Classification]:
        """根据名称查找分类"""
        query = select(Classification).where(
            and_(
                Classification.name == name,
                Classification.is_active == True
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _remove_repository_classifications(self, repository_id: int):
        """移除仓库的所有分类关联"""
        query = select(RepositoryClassification).where(
            RepositoryClassification.repository_id == repository_id
        )
        
        result = await self.db.execute(query)
        classifications = result.scalars().all()
        
        for classification in classifications:
            await self.db.delete(classification)
    
    async def _add_repository_classification(self, repository_id: int, classification_id: int):
        """添加仓库分类关联"""
        # 获取分类及其层级
        classification_query = select(Classification).where(Classification.id == classification_id)
        classification_result = await self.db.execute(classification_query)
        classification = classification_result.scalar_one_or_none()
        
        if not classification:
            return
        
        # 创建关联记录
        repo_classification = RepositoryClassification(
            repository_id=repository_id,
            classification_id=classification_id,
            level=classification.level
        )
        
        self.db.add(repo_classification)