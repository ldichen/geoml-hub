from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.database import get_async_db
from app.models import Repository, User, RepositoryFile
from app.dependencies.auth import get_current_active_user, get_repository_access
from app.services.repository_service import RepositoryService
from app.services.metadata_service import MetadataService, MetadataValidationResult, MetadataTemplate
from app.dependencies.minio import get_minio_service
from app.services.minio_service import MinIOService
import logging
import yaml
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()


class MetadataUpdateRequest(BaseModel):
    """元数据更新请求"""

    metadata: Dict[str, Any]
    update_readme: bool = True


class MetadataValidateRequest(BaseModel):
    """元数据验证请求"""

    metadata: Dict[str, Any]
    schema_type: str = "model"  # model, dataset, space


class MetadataTemplate(BaseModel):
    """元数据模板"""

    name: str
    description: str
    schema_type: str
    template: Dict[str, Any]


@router.get("/{username}/{repo_name}/metadata")
async def get_yaml_metadata(
    username: str = Path(..., description="用户名"),
    repo_name: str = Path(..., description="仓库名"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
    minio_service: MinIOService = Depends(get_minio_service),
):
    """获取仓库YAML元数据"""

    repository = await get_repository_access(username, repo_name, current_user, db)
    
    metadata_service = MetadataService(db, minio_service)
    
    try:
        metadata = await metadata_service.get_repository_metadata(repository)
        
        return {
            "metadata": metadata,
            "has_yaml": bool(metadata),
            "repository_id": repository.id,
            "last_updated": repository.updated_at.isoformat() if repository.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get metadata for {username}/{repo_name}: {e}")
        raise HTTPException(status_code=500, detail="获取元数据失败")


@router.put("/{username}/{repo_name}/metadata")
async def update_metadata(
    request: MetadataUpdateRequest,
    username: str = Path(..., description="用户名"),
    repo_name: str = Path(..., description="仓库名"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
    minio_service: MinIOService = Depends(get_minio_service),
):
    """更新仓库元数据"""

    repository = await get_repository_access(username, repo_name, current_user, db)

    # 检查写权限
    if repository.owner_id != current_user.id and not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="无权限修改此仓库")

    metadata_service = MetadataService(db, minio_service)
    
    try:
        success = await metadata_service.update_repository_metadata(
            repository, request.metadata, request.update_readme
        )
        
        if success:
            return {
                "success": True,
                "message": "元数据更新成功",
                "metadata": request.metadata
            }
        else:
            raise HTTPException(status_code=500, detail="元数据更新失败")
            
    except Exception as e:
        logger.error(f"Failed to update metadata for {username}/{repo_name}: {e}")
        raise HTTPException(status_code=500, detail="更新元数据失败")


@router.post("/{username}/{repo_name}/parse-readme")
async def parse_readme_metadata(
    username: str = Path(..., description="用户名"),
    repo_name: str = Path(..., description="仓库名"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """解析README.md文件中的元数据"""

    repository = await get_repository_access(username, repo_name, current_user, db)

    # 获取README.md文件
    readme_query = select(RepositoryFile).where(
        and_(
            RepositoryFile.repository_id == repository.id,
            RepositoryFile.filename == "README.md",
            RepositoryFile.is_deleted == False,
        )
    )

    readme_result = await db.execute(readme_query)
    readme_file = readme_result.scalar_one_or_none()

    if not readme_file:
        raise HTTPException(status_code=404, detail="README.md文件不存在")

    try:
        # 从MinIO获取文件内容
        readme_content = await minio_service.get_file_content(
            bucket_name=getattr(readme_file, "minio_bucket"),
            object_key=readme_file.minio_object_name,
        )

        # 解析YAML frontmatter
        parser = YAMLFrontmatterParser()
        metadata = parser.parse(readme_content.decode("utf-8")) or {}

        # 如果找到了元数据，更新到数据库
        if metadata:
            setattr(repository, "repo_metadata", metadata)
            await db.commit()

            _, content_only = parser.extract_content(readme_content.decode("utf-8"))
            return {
                "message": "README.md解析成功并已更新到数据库",
                "metadata": metadata,
                "content_preview": (
                    content_only[:200] + "..."
                    if len(content_only) > 200
                    else content_only
                ),
            }
        else:
            content_str = readme_content.decode("utf-8")
            return {
                "message": "README.md中未找到YAML frontmatter",
                "metadata": {},
                "content_preview": (
                    content_str[:200] + "..." if len(content_str) > 200 else content_str
                ),
            }

    except Exception as e:
        logger.error(f"Failed to parse README metadata for {username}/{repo_name}: {e}")
        raise HTTPException(status_code=500, detail="解析README.md失败")


@router.get("/{username}/{repo_name}/model-card")
async def get_model_card(
    username: str = Path(..., description="用户名"),
    repo_name: str = Path(..., description="仓库名"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """获取格式化的Model Card"""

    repository = await get_repository_access(username, repo_name, current_user, db)

    # 获取元数据
    metadata = repository.repo_metadata or {}

    # 构建Model Card结构
    model_card = {
        "model_name": repository.name,
        "model_description": repository.description,
        "repository_info": {
            "owner": username,
            "name": repo_name,
            "full_name": repository.full_name,
            "created_at": repository.created_at,
            "updated_at": repository.updated_at,
            "stars": repository.stars_count,
            "downloads": repository.downloads_count,
            "views": repository.views_count,
        },
        "metadata": metadata,
        "model_details": {
            "license": metadata.get("license", "未指定"),
            "tags": metadata.get("tags", []),
            "language": metadata.get("language", []),
            "pipeline_tag": metadata.get("pipeline_tag", ""),
            "base_model": metadata.get("base_model", ""),
            "datasets": metadata.get("datasets", []),
            "metrics": metadata.get("metrics", []),
        },
        "model_usage": {
            "inference": metadata.get("inference", {}),
            "training": metadata.get("training", {}),
            "evaluation": metadata.get("evaluation", {}),
        },
        "technical_details": {
            "model_size": metadata.get("model_size", ""),
            "parameters": metadata.get("parameters", ""),
            "architecture": metadata.get("architecture", ""),
            "framework": metadata.get("framework", ""),
        },
    }

    return model_card


@router.get("/schema")
async def get_metadata_schema(
    schema_type: str = Query(
        "model", regex="^(model|dataset|space)$", description="模式类型"
    ),
):
    """获取元数据模式定义"""

    schemas = {
        "model": {
            "type": "object",
            "properties": {
                "license": {"type": "string", "description": "许可证"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "标签",
                },
                "language": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "语言",
                },
                "pipeline_tag": {"type": "string", "description": "管道标签"},
                "base_model": {"type": "string", "description": "基础模型"},
                "datasets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "数据集",
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "评估指标",
                },
                "model_size": {"type": "string", "description": "模型大小"},
                "parameters": {"type": "string", "description": "参数数量"},
                "architecture": {"type": "string", "description": "架构"},
                "framework": {"type": "string", "description": "框架"},
            },
            "required": ["license"],
        },
        "dataset": {
            "type": "object",
            "properties": {
                "license": {"type": "string", "description": "许可证"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "标签",
                },
                "language": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "语言",
                },
                "dataset_size": {"type": "string", "description": "数据集大小"},
                "format": {"type": "string", "description": "数据格式"},
                "splits": {"type": "object", "description": "数据分割"},
                "task_categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "任务类别",
                },
                "source": {"type": "string", "description": "数据来源"},
            },
            "required": ["license"],
        },
        "space": {
            "type": "object",
            "properties": {
                "license": {"type": "string", "description": "许可证"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "标签",
                },
                "sdk": {"type": "string", "description": "SDK"},
                "sdk_version": {"type": "string", "description": "SDK版本"},
                "python_version": {"type": "string", "description": "Python版本"},
                "app_file": {"type": "string", "description": "应用文件"},
                "models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "使用的模型",
                },
                "datasets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "使用的数据集",
                },
            },
            "required": ["license", "sdk"],
        },
    }

    return {
        "schema_type": schema_type,
        "schema": schemas.get(schema_type, {}),
        "examples": _get_schema_examples(schema_type),
    }


@router.post("/validate")
async def validate_metadata(
    request: MetadataValidateRequest,
    db: AsyncSession = Depends(get_async_db),
    minio_service: MinIOService = Depends(get_minio_service),
):
    """验证元数据格式"""

    metadata_service = MetadataService(db, minio_service)
    
    try:
        result = await metadata_service.validate_metadata(request.metadata, request.schema_type)
        
        return {
            "valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "suggestions": result.suggestions,
            "score": result.score,
            "completeness": f"{result.score}%"
        }

    except Exception as e:
        logger.error(f"Failed to validate metadata: {e}")
        return {"valid": False, "errors": [f"验证过程中出错: {str(e)}"]}



@router.get("/templates")
async def get_metadata_templates(
    schema_type: Optional[str] = Query(
        None, regex="^(model|dataset|space)$", description="模式类型"
    ),
    db: AsyncSession = Depends(get_async_db),
    minio_service: MinIOService = Depends(get_minio_service),
):
    """获取元数据模板"""
    
    metadata_service = MetadataService(db, minio_service)
    templates_list = await metadata_service.get_metadata_templates(schema_type)
    
    return {"templates": [template.dict() for template in templates_list]}


@router.get("/stats")
async def get_metadata_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
    minio_service: MinIOService = Depends(get_minio_service),
):
    """获取元数据统计信息"""

    metadata_service = MetadataService(db, minio_service)
    
    try:
        stats = await metadata_service.get_metadata_statistics()
        return stats

    except Exception as e:
        logger.error(f"Failed to get metadata stats: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


def _get_schema_examples(schema_type: str) -> Dict[str, Any]:
    """获取模式示例"""
    
    examples = {
        "model": {
            "license": "mit",
            "tags": ["machine-learning", "pytorch", "text-classification"],
            "language": ["en"],
            "pipeline_tag": "text-classification",
            "base_model": "bert-base-uncased",
            "datasets": ["imdb"],
            "metrics": ["accuracy", "f1"],
            "model_size": "110M",
            "parameters": "110M",
            "architecture": "bert",
            "framework": "pytorch"
        },
        "dataset": {
            "license": "cc-by-4.0",
            "tags": ["dataset", "text-classification"],
            "language": ["en"],
            "dataset_size": "50K examples",
            "format": "json",
            "splits": {
                "train": {"num_examples": 25000},
                "test": {"num_examples": 25000}
            },
            "task_categories": ["text-classification"],
            "source": "Movie reviews"
        },
        "space": {
            "license": "apache-2.0",
            "tags": ["gradio", "demo"],
            "sdk": "gradio",
            "sdk_version": "3.0.0",
            "python_version": "3.8",
            "app_file": "app.py",
            "models": ["bert-base-uncased"],
            "datasets": ["imdb"]
        }
    }
    
    return examples.get(schema_type, {})
