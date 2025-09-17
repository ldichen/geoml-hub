from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, update
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any, List, Sequence
from fastapi import HTTPException, UploadFile
from app.middleware.error_response import RepositoryException, FileException, UserException, ErrorCodes
from app.models import (
    Repository,
    RepositoryFile,
    RepositoryStar,
    RepositoryView,
    RepositoryClassification,
    User,
    FileDownload,
)
from app.schemas.repository import RepositoryCreate, RepositoryUpdate
from app.utils.yaml_parser import YAMLFrontmatterParser
from app.services.minio_service import MinIOService
from app.services.metadata_sync_service import MetadataSyncService
from app.services.version_control_service import VersionControlService
import uuid
from datetime import datetime, timezone
import os


class RepositoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.yaml_parser = YAMLFrontmatterParser()
        self.minio_service = MinIOService()
        self.metadata_sync = MetadataSyncService(db)
        self.version_control = VersionControlService(db)

    async def create_repository(
        self, owner_id: int, repo_data: RepositoryCreate
    ) -> Repository:
        """创建新仓库"""
        # 检查用户是否存在
        owner_query = select(User).where(User.id == owner_id)
        owner_result = await self.db.execute(owner_query)
        owner = owner_result.scalar_one_or_none()

        if not owner:
            raise UserException("用户不存在", ErrorCodes.USER_NOT_FOUND, status_code=404)

        # 生成完整仓库名称
        full_name = f"{owner.username}/{repo_data.name}"

        # 检查仓库名是否已存在
        existing_query = select(Repository).where(Repository.full_name == full_name)
        existing_result = await self.db.execute(existing_query)
        existing_repo = existing_result.scalar_one_or_none()

        if existing_repo:
            raise RepositoryException(
                f"仓库 '{full_name}' 已存在",
                ErrorCodes.REPOSITORY_ALREADY_EXISTS,
                status_code=409,
                context={"repository_name": full_name}
            )

        # 如果没有提供README内容，自动生成默认README
        readme_content = repo_data.readme_content
        if not readme_content:
            readme_content = self._generate_default_readme(
                repo_data, getattr(owner, "username")
            )

        # 解析README.md的YAML frontmatter
        metadata = None
        if readme_content:
            try:
                metadata = self.yaml_parser.parse(readme_content)
            except Exception as e:
                # 如果解析失败，记录错误但不阻止仓库创建
                print(f"YAML frontmatter parsing failed: {e}")

        # 创建仓库
        db_repo = Repository(
            name=repo_data.name,
            full_name=full_name,
            description=repo_data.description,
            owner_id=owner_id,
            repo_type=repo_data.repo_type,
            visibility=repo_data.visibility,
            repo_metadata=metadata or repo_data.repo_metadata,
            readme_content=readme_content,
            tags=repo_data.tags or [],
            license=repo_data.license,
            base_model=getattr(repo_data, "base_model", None),
        )

        self.db.add(db_repo)
        await self.db.commit()
        await self.db.refresh(db_repo)

        # 处理分类关联
        classification_id = None
        if hasattr(repo_data, "classification_id") and repo_data.classification_id:
            classification_id = repo_data.classification_id
        elif metadata:
            # 首先检查是否有直接的classification_id
            if "classification_id" in metadata:
                classification_id = metadata["classification_id"]
            else:
                print(f"classification_id not found in metadata: {metadata}")
                # 使用YAML解析器提取分类信息
                classification_info = self.yaml_parser.extract_classification_info(
                    metadata
                )
                print(f"Extracted classification_info: {classification_info}")
                if classification_info:
                    # 尝试通过分类名称查找分类
                    classification = await self._find_classification_by_name(
                        classification_info
                    )
                    if classification:
                        classification_id = classification.id

        # 添加分类关联
        if classification_id is not None:
            try:
                await self.add_repository_classification(db_repo.id, classification_id)
                # 重新加载repository以获取分类关联
                await self.db.refresh(db_repo)
            except Exception as e:
                print(f"Failed to add classification: {e}")

        # 使用元数据同步服务生成包含所有信息的README
        final_readme = await self.metadata_sync.sync_repository_to_readme(db_repo)

        # 创建实体的README.md文件
        await self._create_readme_file(db_repo.id, final_readme)

        # 更新数据库中的readme_content
        db_repo.readme_content = final_readme
        await self.db.commit()

        # 更新用户的仓库计数
        if repo_data.visibility == "public":
            setattr(
                owner, "public_repos_count", getattr(owner, "public_repos_count") + 1
            )
            await self.db.commit()

        # 初始化默认分支 (main) - 直接在数据库中创建
        try:
            from app.models.version_control import Branch
            main_branch = Branch(
                repository_id=db_repo.id,
                name="main",
                head_snapshot_id=None,  # 初始时没有快照
                is_default=True,
            )
            self.db.add(main_branch)
            await self.db.commit()
        except Exception as e:
            # 分支创建失败不应该阻止仓库创建
            print(f"Failed to create main branch: {e}")

        # 加载关联数据
        await self.db.refresh(db_repo)
        query = (
            select(Repository)
            .where(Repository.id == db_repo.id)
            .options(
                selectinload(Repository.owner), selectinload(Repository.classifications)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create_repository_with_readme_file(
        self, owner_id: int, repo_data: RepositoryCreate, readme_file: UploadFile
    ) -> Repository:
        """创建带README.md文件的新仓库"""

        # 验证上传的文件是README.md
        if not readme_file.filename or not readme_file.filename.lower().endswith(".md"):
            raise FileException(
                "只能上传Markdown文件(.md)",
                ErrorCodes.INVALID_FILE_TYPE,
                context={"filename": readme_file.filename, "allowed_types": [".md"]}
            )

        try:
            # 读取README内容
            readme_content = await readme_file.read()
            readme_text = readme_content.decode("utf-8")

            # 解析YAML frontmatter
            metadata = None
            try:
                metadata = self.yaml_parser.parse(readme_text)
            except Exception as e:
                print(f"YAML frontmatter parsing failed: {e}")

            # 更新repo_data中的metadata和readme内容
            if metadata:
                if not repo_data.repo_metadata:
                    repo_data.repo_metadata = {}
                repo_data.repo_metadata.update(metadata)

                # 从metadata中提取常用字段
                if "license" in metadata and not repo_data.license:
                    repo_data.license = metadata["license"]
                if "tags" in metadata and not repo_data.tags:
                    repo_data.tags = metadata["tags"]
                if (
                    "base_model" in metadata
                    and hasattr(repo_data, "base_model")
                    and not repo_data.base_model
                ):
                    repo_data.base_model = metadata["base_model"]

            # 设置README内容
            repo_data.readme_content = readme_text

            # 创建仓库（这会自动处理README的数据库存储和MinIO存储）
            repository = await self.create_repository(
                owner_id=owner_id, repo_data=repo_data
            )

            return repository

        except UnicodeDecodeError:
            raise FileException(
                "无法解码README文件，请确保文件为UTF-8编码",
                ErrorCodes.INVALID_FILE_TYPE,
                context={"filename": readme_file.filename, "encoding": "UTF-8"}
            )
        except Exception as e:
            print(f"创建带README的仓库失败: {e}")
            raise RepositoryException(
                f"创建仓库失败: {str(e)}",
                ErrorCodes.REPOSITORY_CREATE_FAILED,
                status_code=500,
                context={"original_error": str(e)}
            )

    def _generate_default_readme(
        self, repo_data: RepositoryCreate, username: str
    ) -> str:
        """生成默认的README.md内容"""
        repo_type_names = {"model": "模型", "dataset": "数据集", "space": "空间"}

        repo_type_desc = repo_type_names.get(repo_data.repo_type, "项目")

        # 生成简化的YAML frontmatter（符合Hugging Face模式）
        yaml_parts = []

        # License
        if repo_data.license:
            yaml_parts.append(f"license: {repo_data.license}")

        # Tags
        if repo_data.tags:
            yaml_parts.append("tags:")
            for tag in repo_data.tags:
                yaml_parts.append(f"  - {tag}")

        # Pipeline tag based on repo type (removed automatic assignment for models)
        pipeline_tags = {
            "dataset": "dataset",
            "space": "space",
        }
        if repo_data.repo_type in pipeline_tags:
            yaml_parts.append(f"pipeline_tag: {pipeline_tags[repo_data.repo_type]}")

        # Base model (从repo_data的base_model字段或metadata中获取)
        base_model = getattr(repo_data, "base_model", None)
        if (
            not base_model
            and repo_data.repo_metadata
            and isinstance(repo_data.repo_metadata, dict)
        ):
            base_model = repo_data.repo_metadata.get("base_model")

        if base_model:
            yaml_parts.append(f"base_model: {base_model}")

        yaml_content = "\n".join(yaml_parts) if yaml_parts else "license: mit"

        # 生成包含简化YAML frontmatter的README
        readme_content = f"""---
{yaml_content}
---

# {repo_data.name}

{repo_data.description or f"这是一个新创建的{repo_type_desc}仓库。"}

## 描述

请在这里添加关于你的{repo_type_desc}的详细描述。

## 使用方法

请在这里添加使用说明。

## 许可证

本项目使用 {repo_data.license or 'MIT'} 许可证。

## 贡献

欢迎提交 Pull Request 或者 Issue。
"""
        return readme_content

    async def _sync_metadata_with_readme(self, repository: Repository) -> str:
        """同步数据库字段与README.md中的YAML元数据"""
        # 从数据库字段生成YAML frontmatter
        yaml_parts = []

        # License
        if repository.license is not None:
            yaml_parts.append(f"license: {repository.license}")

        # Tags
        if repository.tags is not None:
            yaml_parts.append("tags:")
            for tag in repository.tags:
                yaml_parts.append(f"  - {tag}")

        # Pipeline tag based on repo type (removed automatic assignment for models)
        pipeline_tags = {
            "dataset": "dataset",
            "space": "space",
        }
        if repository.repo_type in pipeline_tags:
            yaml_parts.append(
                f"pipeline_tag: {pipeline_tags[getattr(repository, 'repo_type')]}"
            )

        # Base model (从数据库字段或metadata中获取)
        base_model = getattr(repository, "base_model", None)
        if (
            not base_model
            and getattr(repository, "repo_metadata")
            and isinstance(repository.repo_metadata, dict)
        ):
            base_model = repository.repo_metadata.get("base_model")

        if base_model:
            yaml_parts.append(f"base_model: {base_model}")

        # Classifications (从关联的分类中获取)
        if hasattr(repository, "classifications") and repository.classifications:
            classifications = []
            for repo_classification in repository.classifications:
                if (
                    hasattr(repo_classification, "classification")
                    and repo_classification.classification
                ):
                    classifications.append(repo_classification.classification.name)

            if classifications:
                yaml_parts.append("classifications:")
                for classification in classifications:
                    yaml_parts.append(f"  - {classification}")

        yaml_content = "\n".join(yaml_parts) if yaml_parts else "license: mit"

        # 获取现有README内容的markdown部分（去除YAML frontmatter）
        current_readme = getattr(repository, "readme_content") or ""

        # 移除现有的YAML frontmatter，保留markdown内容
        import re

        markdown_content = re.sub(
            r"^---\s*\n.*?\n---\s*\n", "", current_readme, 0, re.DOTALL
        )

        # 如果没有markdown内容，生成默认内容
        if not markdown_content.strip():
            repo_type_names = {"model": "模型", "dataset": "数据集", "space": "空间"}
            repo_type_desc = repo_type_names.get(
                getattr(repository, "repo_type"), "项目"
            )

            markdown_content = f"""# {repository.name}

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

        # 重新组合README内容
        updated_readme = f"""---
{yaml_content}
---

{markdown_content}"""

        return updated_readme

    async def _sync_database_from_yaml(
        self, repository: Repository, readme_content: str
    ) -> None:
        """从YAML frontmatter同步数据库字段"""
        try:
            # 解析YAML frontmatter
            metadata = self.yaml_parser.parse(readme_content)

            if metadata:
                # 更新数据库字段
                if "license" in metadata:
                    repository.license = metadata["license"]

                if "tags" in metadata and isinstance(metadata["tags"], list):
                    repository.tags = metadata["tags"]

                # 更新base_model字段
                if "base_model" in metadata:
                    repository.base_model = metadata["base_model"]

                # 更新repo_metadata中的其他字段
                if not repository.repo_metadata:
                    repository.repo_metadata = {}

                # 同步其他元数据到repo_metadata
                repo_metadata = (
                    repository.repo_metadata.copy() if repository.repo_metadata else {}
                )
                for key in [
                    "pipeline_tag",
                    "datasets",
                    "model_type",
                    "task",
                    "language",
                    "architectures",
                ]:
                    if key in metadata:
                        repo_metadata[key] = metadata[key]

                # 保持base_model同时在数据库字段和metadata中
                if "base_model" in metadata:
                    repo_metadata["base_model"] = metadata["base_model"]

                repository.repo_metadata = repo_metadata

                # 处理分类信息
                if "classifications" in metadata:
                    classification_info = self.yaml_parser.extract_classification_info(
                        metadata
                    )
                    if classification_info:
                        # 移除现有分类
                        await self.remove_repository_classification(
                            getattr(repository, "id")
                        )

                        # 查找并添加新分类
                        classification = await self._find_classification_by_name(
                            classification_info
                        )
                        if classification:
                            await self.add_repository_classification(
                                getattr(repository, "id"), getattr(classification, "id")
                            )

        except Exception as e:
            print(f"Failed to sync database from YAML: {e}")

    async def _create_readme_file(self, repository_id: int, readme_content: str):
        """创建实体的README.md文件"""
        try:
            # 创建README.md文件记录
            readme_file = RepositoryFile(
                repository_id=repository_id,
                filename="README.md",
                file_path="README.md",
                file_type="documentation",
                mime_type="text/markdown",
                file_size=len(readme_content.encode("utf-8")),
                minio_bucket="repositories",
                minio_object_key=f"repository_{repository_id}/README.md",
                is_deleted=False,
            )

            # 保存到数据库
            self.db.add(readme_file)

            # 上传到MinIO
            await self.minio_service.upload_file(
                bucket_name="repositories",
                object_key=f"repository_{repository_id}/README.md",
                file_data=readme_content.encode("utf-8"),
                content_type="text/markdown",
            )

            await self.db.commit()

        except Exception as e:
            print(f"Failed to create README.md file: {e}")
            # 不要因为README文件创建失败而阻止仓库创建
            pass

    async def _update_readme_file(self, repository_id: int, readme_content: str):
        """更新MinIO中的README.md文件"""
        try:
            # 查找现有的README.md文件记录
            readme_file_query = select(RepositoryFile).where(
                and_(
                    RepositoryFile.repository_id == repository_id,
                    RepositoryFile.filename == "README.md",
                    RepositoryFile.is_deleted == False,
                )
            )
            readme_file_result = await self.db.execute(readme_file_query)
            readme_file = readme_file_result.scalar_one_or_none()

            if readme_file:
                # 更新MinIO中的文件
                await self.minio_service.upload_file(
                    bucket_name=getattr(readme_file, "minio_bucket"),
                    object_key=getattr(readme_file, "minio_object_key"),
                    file_data=readme_content.encode("utf-8"),
                    content_type="text/markdown",
                )

                # 更新文件记录
                setattr(readme_file, "file_size", len(readme_content.encode("utf-8")))
                setattr(readme_file, "last_modified", datetime.now(timezone.utc))

                await self.db.commit()

        except Exception as e:
            print(f"Failed to update README.md file: {e}")

    async def get_repository_by_full_name(self, full_name: str) -> Optional[Repository]:
        """根据完整名称获取仓库"""
        query = (
            select(Repository)
            .where(
                and_(Repository.full_name == full_name, Repository.is_active == True)
            )
            .options(selectinload(Repository.owner))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_repository(
        self, full_name: str, repo_data: RepositoryUpdate
    ) -> Repository:
        """更新仓库信息"""
        repository = await self.get_repository_by_full_name(full_name)
        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 标记是否需要同步README
        needs_readme_sync = False
        readme_updated = False

        # 更新字段
        if repo_data.description is not None:
            setattr(repository, "description", repo_data.description)
        if repo_data.visibility is not None:
            old_visibility = repository.visibility
            setattr(repository, "visibility", repo_data.visibility)

            # 更新用户的公开仓库计数
            if str(old_visibility) != str(repo_data.visibility):
                owner_query = select(User).where(User.id == repository.owner_id)
                owner_result = await self.db.execute(owner_query)
                owner = owner_result.scalar_one()

                if (
                    str(old_visibility) == "public"
                    and str(repo_data.visibility) == "private"
                ):
                    setattr(
                        owner,
                        "public_repos_count",
                        max(0, getattr(owner, "public_repos_count") - 1),
                    )
                elif (
                    str(old_visibility) == "private"
                    and str(repo_data.visibility) == "public"
                ):
                    setattr(
                        owner,
                        "public_repos_count",
                        getattr(owner, "public_repos_count") + 1,
                    )

        if repo_data.tags is not None:
            setattr(repository, "tags", repo_data.tags)
            needs_readme_sync = True
        if repo_data.license is not None:
            setattr(repository, "license", repo_data.license)
            needs_readme_sync = True

        if hasattr(repo_data, "base_model") and repo_data.base_model is not None:
            setattr(repository, "base_model", repo_data.base_model)
            needs_readme_sync = True
        if repo_data.readme_content is not None:
            setattr(repository, "readme_content", repo_data.readme_content)
            readme_updated = True

            # 从README同步到数据库字段
            await self._sync_database_from_yaml(repository, repo_data.readme_content)

        if repo_data.repo_metadata is not None:
            setattr(repository, "repo_metadata", repo_data.repo_metadata)
            needs_readme_sync = True

        # 使用增强的双向同步服务
        if readme_updated:
            # README被更新，同步到数据库字段
            await self.metadata_sync.sync_readme_to_repository(
                repository, repo_data.readme_content
            )
        elif needs_readme_sync:
            # 数据库字段被更新，同步到README
            updated_readme = await self.metadata_sync.sync_repository_to_readme(
                repository
            )
            setattr(repository, "readme_content", updated_readme)
            # 同步更新MinIO中的README.md文件
            try:
                await self._update_readme_file(repository.id, updated_readme)
            except Exception as e:
                print(f"Failed to update README.md file in MinIO: {e}")

        await self.db.commit()
        await self.db.refresh(repository)

        return repository

    async def delete_repository(self, full_name: str) -> None:
        """删除仓库（软删除）"""
        repository = await self.get_repository_by_full_name(full_name)
        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 软删除
        setattr(repository, "is_active", False)

        # 更新用户的公开仓库计数
        if str(getattr(repository, "visibility")) == "public":
            owner_query = select(User).where(User.id == repository.owner_id)
            owner_result = await self.db.execute(owner_query)
            owner = owner_result.scalar_one()
            setattr(
                owner,
                "public_repos_count",
                max(0, getattr(owner, "public_repos_count") - 1),
            )

        await self.db.commit()

    async def star_repository(self, user_id: int, repository_full_name: str) -> None:
        """收藏仓库"""
        repository = await self.get_repository_by_full_name(repository_full_name)
        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 检查是否已经收藏
        existing_query = select(RepositoryStar).where(
            and_(
                RepositoryStar.user_id == user_id,
                RepositoryStar.repository_id == repository.id,
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_star = existing_result.scalar_one_or_none()

        if existing_star:
            raise HTTPException(status_code=400, detail="已经收藏该仓库")

        # 创建收藏记录
        star = RepositoryStar(user_id=user_id, repository_id=repository.id)
        self.db.add(star)

        # 更新仓库的收藏计数
        setattr(repository, "stars_count", getattr(repository, "stars_count") + 1)

        await self.db.commit()

    async def unstar_repository(self, user_id: int, repository_full_name: str) -> None:
        """取消收藏仓库"""
        repository = await self.get_repository_by_full_name(repository_full_name)
        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 查找收藏记录
        star_query = select(RepositoryStar).where(
            and_(
                RepositoryStar.user_id == user_id,
                RepositoryStar.repository_id == repository.id,
            )
        )
        star_result = await self.db.execute(star_query)
        star = star_result.scalar_one_or_none()

        if not star:
            raise HTTPException(status_code=400, detail="未收藏该仓库")

        # 删除收藏记录
        from sqlalchemy import delete

        delete_stmt = delete(RepositoryStar).where(
            and_(
                RepositoryStar.user_id == user_id,
                RepositoryStar.repository_id == repository.id,
            )
        )
        await self.db.execute(delete_stmt)

        # 更新仓库的收藏计数
        setattr(
            repository, "stars_count", max(0, getattr(repository, "stars_count") - 1)
        )

        await self.db.commit()

    async def record_view(
        self,
        repository_id: int,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
        view_type: str = "page_view",
        target_path: Optional[str] = None,
    ) -> None:
        """记录仓库访问"""
        view = RepositoryView(
            repository_id=repository_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            view_type=view_type,
            target_path=target_path,
        )

        self.db.add(view)

        # 更新仓库的访问计数（可以考虑使用异步任务来避免影响响应性能）
        repo_query = select(Repository).where(Repository.id == repository_id)
        repo_result = await self.db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()

        if repository:
            setattr(repository, "views_count", getattr(repository, "views_count") + 1)

        await self.db.commit()

    async def upload_file(
        self, repository_id: int, file: UploadFile, file_path: str
    ) -> RepositoryFile:
        """上传文件到仓库"""
        # 检查仓库是否存在
        repo_query = select(Repository).where(Repository.id == repository_id)
        repo_result = await self.db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()

        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 生成唯一的对象键
        if file.filename:
            file_extension = os.path.splitext(file.filename)[1]
        else:
            file_extension = ""
        object_key = f"{repository.full_name}/{file_path}"

        # 上传到MinIO
        try:
            file_content = await file.read()
            file_size = len(file_content)

            upload_result = await self.minio_service.upload_file(
                bucket_name="repositories",
                object_key=object_key,
                file_data=file_content,
                content_type=file.content_type,
            )

            # 创建文件记录
            db_file = RepositoryFile(
                repository_id=repository_id,
                filename=file.filename,
                file_path=file_path,
                file_type=self._get_file_type(file.filename or ""),
                mime_type=file.content_type,
                file_size=file_size,
                minio_bucket="repositories",
                minio_object_key=object_key,
                file_hash=upload_result.get("etag"),
            )

            self.db.add(db_file)

            # 更新仓库的文件统计
            setattr(repository, "total_files", getattr(repository, "total_files") + 1)
            setattr(
                repository, "total_size", getattr(repository, "total_size") + file_size
            )
            setattr(repository, "last_commit_at", datetime.now(timezone.utc))

            # 如果上传的是README.md，处理分类信息更新
            if (
                file_path.lower() == "readme.md"
                and file.content_type
                and file.content_type.startswith("text/")
            ):
                try:
                    # 解析文件内容中的YAML frontmatter
                    content_str = file_content.decode("utf-8")
                    metadata = self.yaml_parser.parse(content_str)

                    if metadata:
                        # 更新仓库元数据
                        setattr(db_file, "repo_metadata", metadata)

                        # 提取并更新分类信息
                        classification_info = (
                            self.yaml_parser.extract_classification_info(metadata)
                        )
                        if classification_info:
                            # 先移除现有分类
                            await self.remove_repository_classification(repository_id)

                            # 查找分类并添加新的关联
                            classification = await self._find_classification_by_name(
                                classification_info
                            )
                            if classification:
                                await self.add_repository_classification(
                                    repository_id, getattr(classification, "id")
                                )
                except Exception as e:
                    # README.md分类更新失败不应该阻止文件上传
                    print(f"README.md classification update failed: {e}")

            await self.db.commit()
            await self.db.refresh(db_file)

            return db_file

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    async def upload_files_with_snapshot(
        self,
        repository_id: int,
        user_id: int,
        files: List[UploadFile],
        file_paths: List[str],
        commit_message: str,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """上传文件并创建快照 (版本控制)"""

        if len(files) != len(file_paths):
            raise HTTPException(status_code=400, detail="文件数量与路径数量不匹配")

        # 检查仓库是否存在
        repo_query = select(Repository).where(Repository.id == repository_id)
        repo_result = await self.db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()

        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        try:
            # 准备文件上传信息
            file_uploads = []
            for file, file_path in zip(files, file_paths):
                content = await file.read()
                file_uploads.append({
                    "file_name": file.filename or file_path.split("/")[-1],
                    "file_path": file_path,
                    "file_size": len(content),
                    "content_type": file.content_type,
                    "content": content.decode('utf-8') if file.content_type and file.content_type.startswith('text/') else None,
                })

            # 创建快照
            snapshot_result = await self.version_control.create_snapshot(
                repository_id=repository_id,
                author_id=user_id,
                message=commit_message,
                branch=branch,
                file_uploads=file_uploads,
            )

            return {
                "success": True,
                "snapshot": snapshot_result,
                "message": f"成功上传 {len(files)} 个文件并创建快照",
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件上传和快照创建失败: {str(e)}")

    # 版本控制相关方法
    async def get_repository_snapshots(
        self, repository_id: int, branch: Optional[str] = None, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """获取仓库快照列表"""
        return await self.version_control.get_snapshots(repository_id, branch, page, limit)

    async def get_repository_branches(self, repository_id: int) -> Dict[str, Any]:
        """获取仓库分支列表"""
        return await self.version_control.get_branches(repository_id)

    async def get_repository_releases(
        self, repository_id: int, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """获取仓库发布版本列表"""
        return await self.version_control.get_releases(repository_id, page, limit)

    async def create_repository_branch(
        self, repository_id: int, name: str, source_branch: str = "main"
    ) -> Dict[str, Any]:
        """创建仓库分支"""
        return await self.version_control.create_branch(repository_id, name, source_branch)

    async def create_repository_release(
        self,
        repository_id: int,
        tag_name: str,
        snapshot_id: str,
        title: str,
        description: Optional[str] = None,
        is_prerelease: bool = False,
    ) -> Dict[str, Any]:
        """创建仓库发布版本"""
        return await self.version_control.create_release(
            repository_id, tag_name, snapshot_id, title, description, is_prerelease
        )

    async def compare_repository_snapshots(
        self, repository_id: int, base_snapshot_id: str, compare_snapshot_id: str
    ) -> Dict[str, Any]:
        """比较仓库快照"""
        return await self.version_control.compare_snapshots(
            repository_id, base_snapshot_id, compare_snapshot_id
        )

    async def rollback_repository(
        self,
        repository_id: int,
        target_snapshot_id: str,
        branch: str,
        user_id: int,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """回滚仓库到指定快照"""
        return await self.version_control.rollback_to_snapshot(
            repository_id, target_snapshot_id, branch, user_id, message
        )

    async def download_file(
        self,
        file_id: int,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
    ) -> str:
        """下载文件（返回预签名URL）"""
        # 获取文件信息
        file_query = (
            select(RepositoryFile)
            .where(
                and_(RepositoryFile.id == file_id, RepositoryFile.is_deleted == False)
            )
            .options(selectinload(RepositoryFile.repository))
        )

        file_result = await self.db.execute(file_query)
        file_obj = file_result.scalar_one_or_none()

        if not file_obj:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 检查仓库访问权限（如果是私有仓库）
        if file_obj.repository.visibility == "private":
            # TODO: 检查用户权限
            pass

        # 记录下载
        download = FileDownload(
            file_id=file_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
        )
        self.db.add(download)

        # 更新下载计数
        setattr(
            file_obj.repository,
            "downloads_count",
            getattr(file_obj.repository, "downloads_count") + 1,
        )

        await self.db.commit()

        # 生成预签名下载URL
        try:
            download_url = await self.minio_service.get_download_url(
                bucket_name=getattr(file_obj, "minio_bucket"),
                object_key=getattr(file_obj, "minio_object_key"),
                expires=3600,  # 1小时有效期
            )
            return download_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成下载链接失败: {str(e)}")

    async def get_repository_stats(self, repository_id: int) -> Dict[str, Any]:
        """获取仓库统计信息"""
        repo_query = select(Repository).where(Repository.id == repository_id)
        repo_result = await self.db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()

        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 获取热门文件（按下载量排序）
        top_files_query = (
            select(RepositoryFile)
            .where(
                and_(
                    RepositoryFile.repository_id == repository_id,
                    RepositoryFile.is_deleted == False,
                )
            )
            .order_by(desc(RepositoryFile.download_count))
            .limit(10)
        )

        top_files_result = await self.db.execute(top_files_query)
        top_files = top_files_result.scalars().all()

        # 获取今日统计（简化版本，实际应该使用时间范围查询）
        today_downloads_query = select(func.count(FileDownload.id)).where(
            FileDownload.file_id.in_(
                select(RepositoryFile.id).where(
                    RepositoryFile.repository_id == repository_id
                )
            )
        )
        today_downloads_result = await self.db.execute(today_downloads_query)
        daily_downloads = today_downloads_result.scalar() or 0

        today_views_query = select(func.count(RepositoryView.id)).where(
            RepositoryView.repository_id == repository_id
        )
        today_views_result = await self.db.execute(today_views_query)
        daily_views = today_views_result.scalar() or 0

        return {
            "stars_count": repository.stars_count,
            "downloads_count": repository.downloads_count,
            "views_count": repository.views_count,
            "forks_count": repository.forks_count,
            "total_files": repository.total_files,
            "total_size": repository.total_size,
            "daily_downloads": daily_downloads,
            "daily_views": daily_views,
            "top_files": top_files,
        }

    def _get_file_type(self, filename: str) -> str:
        """根据文件名判断文件类型"""
        extension = os.path.splitext(filename)[1].lower()

        model_extensions = [".pkl", ".pth", ".pt", ".h5", ".pb", ".onnx", ".tflite"]
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"]
        document_extensions = [".md", ".txt", ".pdf", ".doc", ".docx", ".readme"]
        data_extensions = [".csv", ".json", ".xml", ".yaml", ".yml", ".parquet"]

        if extension in model_extensions:
            return "model"
        elif extension in image_extensions:
            return "image"
        elif extension in document_extensions:
            return "document"
        elif extension in data_extensions:
            return "dataset"
        else:
            return "other"

    async def search_repositories(
        self,
        query: str,
        repo_type: Optional[str] = None,
        classification_ids: Optional[List[int]] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "relevance",
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Repository]:
        """搜索仓库"""
        # 构建基础查询
        base_query = select(Repository).where(
            and_(Repository.is_active == True, Repository.visibility == "public")
        )

        # 添加搜索条件
        if query:
            base_query = base_query.where(
                or_(
                    Repository.name.ilike(f"%{query}%"),
                    Repository.description.ilike(f"%{query}%"),
                    Repository.full_name.ilike(f"%{query}%"),
                )
            )

        if repo_type:
            base_query = base_query.where(Repository.repo_type == repo_type)

        if tags:
            for tag in tags:
                base_query = base_query.where(Repository.tags.any(tag))

        if classification_ids:
            base_query = base_query.join(Repository.classifications).where(
                RepositoryClassification.classification_id.in_(classification_ids)
            )

        # 排序
        if sort_by == "stars":
            base_query = base_query.order_by(desc(Repository.stars_count))
        elif sort_by == "downloads":
            base_query = base_query.order_by(desc(Repository.downloads_count))
        elif sort_by == "updated":
            base_query = base_query.order_by(desc(Repository.updated_at))
        elif sort_by == "created":
            base_query = base_query.order_by(desc(Repository.created_at))
        else:  # relevance
            base_query = base_query.order_by(
                desc(Repository.stars_count + Repository.views_count)
            )

        # 分页
        base_query = base_query.offset(skip).limit(limit)

        # 加载关联数据
        base_query = base_query.options(selectinload(Repository.owner))

        result = await self.db.execute(base_query)
        return result.scalars().all()

    async def _find_classification_by_name(self, classification_name: str):
        """通过分类名称查找分类"""
        from app.models.classification import Classification

        query = select(Classification).where(
            Classification.name.ilike(f"%{classification_name}%")
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_repository_classification(
        self, repository_id: int, classification_id: int
    ) -> List[dict]:
        """为仓库添加分类，自动处理层次关系"""
        from app.models.classification import Classification

        # 获取指定分类及其层次关系
        classification_query = select(Classification).where(
            Classification.id == classification_id
        )
        result = await self.db.execute(classification_query)
        classification = result.scalar_one_or_none()

        if not classification:
            raise HTTPException(status_code=404, detail="分类不存在")

        # 收集需要关联的分类（包括父级分类）
        classifications_to_add = []
        current = classification

        while current:
            classifications_to_add.append(current.id)
            if current.parent_id is not None:
                parent_query = select(Classification).where(
                    Classification.id == current.parent_id
                )
                parent_result = await self.db.execute(parent_query)
                current = parent_result.scalar_one_or_none()
            else:
                current = None

        # 先清除现有的分类关联
        delete_query = RepositoryClassification.__table__.delete().where(
            RepositoryClassification.repository_id == repository_id
        )
        await self.db.execute(delete_query)

        # 添加新的分类关联
        for classification_id in classifications_to_add:
            # 检查是否已存在关联
            existing_query = select(RepositoryClassification).where(
                and_(
                    RepositoryClassification.repository_id == repository_id,
                    RepositoryClassification.classification_id == classification_id,
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if not existing:
                new_association = RepositoryClassification(
                    repository_id=repository_id,
                    classification_id=classification_id,
                    level=(
                        3
                        if classification_id == classification.id
                        else (
                            2 if classification_id in classifications_to_add[1:2] else 1
                        )
                    ),
                )
                self.db.add(new_association)

        await self.db.commit()

        # 返回关联的分类信息
        return await self.get_repository_classifications(repository_id)

    async def get_repository_classifications(self, repository_id: int) -> List[dict]:
        """获取仓库的所有分类"""
        from app.models.classification import Classification

        query = (
            select(Classification, RepositoryClassification.level)
            .join(
                RepositoryClassification,
                Classification.id == RepositoryClassification.classification_id,
            )
            .where(RepositoryClassification.repository_id == repository_id)
            .order_by(RepositoryClassification.level)
        )

        result = await self.db.execute(query)
        rows = result.fetchall()

        classifications = []
        for classification, level in rows:
            classifications.append(
                {
                    "id": classification.id,
                    "name": classification.name,
                    "name_en": classification.name_en,
                    "level": level,
                    "parent_id": classification.parent_id,
                    "description": classification.description,
                }
            )

        return classifications

    async def remove_repository_classification(self, repository_id: int) -> bool:
        """移除仓库的所有分类关联"""
        delete_query = RepositoryClassification.__table__.delete().where(
            RepositoryClassification.repository_id == repository_id
        )
        result = await self.db.execute(delete_query)
        await self.db.commit()
        return getattr(result, "rowcount") > 0
