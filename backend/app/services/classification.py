from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.classification import Classification
from app.schemas.classification import (
    ClassificationCreate,
    ClassificationUpdate,
    Classification as ClassificationSchema,
    ClassificationWithChildren,
)


class ClassificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_classification_tree(
        self, level: Optional[int] = None, active_only: bool = True
    ) -> List[ClassificationWithChildren]:
        """获取分类树结构（优化版本）"""
        # 一次性获取所有分类数据
        stmt = select(Classification)
        if active_only:
            stmt = stmt.filter(Classification.is_active == True)
        if level:
            stmt = stmt.filter(Classification.level <= level)
        
        stmt = stmt.order_by(Classification.sort_order, Classification.name)
        result = await self.db.execute(stmt)
        all_classifications = result.scalars().all()
        
        # 构建分类映射和路径缓存
        classification_map = {c.id: c for c in all_classifications}
        path_cache = {}
        
        def get_path_cached(classification_id: int) -> List[str]:
            if classification_id in path_cache:
                return path_cache[classification_id]
            
            path = []
            current_id = classification_id
            while current_id is not None:
                if current_id in classification_map:
                    classification = classification_map[current_id]
                    path.insert(0, classification.name)
                    current_id = classification.parent_id
                else:
                    break
            
            path_cache[classification_id] = path
            return path
        
        # 构建树结构
        def build_tree_node(classification: Classification) -> ClassificationWithChildren:
            return ClassificationWithChildren(
                id=classification.id,
                name=classification.name,
                level=classification.level,
                parent_id=classification.parent_id,
                is_active=classification.is_active,
                sort_order=classification.sort_order,
                created_at=classification.created_at,
                updated_at=classification.updated_at,
                path=get_path_cached(classification.id),
                children=[]
            )
        
        # 构建节点映射
        nodes = {c.id: build_tree_node(c) for c in all_classifications}
        
        # 建立父子关系
        root_nodes = []
        for classification in all_classifications:
            node = nodes[classification.id]
            if classification.parent_id is None:
                root_nodes.append(node)
            elif classification.parent_id in nodes:
                parent_node = nodes[classification.parent_id]
                parent_node.children.append(node)
        
        return root_nodes

    async def _build_classification_tree(
        self,
        classification: Classification,
        max_level: Optional[int] = None,
        active_only: bool = True,
    ) -> ClassificationWithChildren:
        """递归构建分类树"""
        # 构建路径
        path = await self.get_classification_path(getattr(classification, "id"))

        # 转换为响应模型
        tree_node = ClassificationWithChildren(
            id=getattr(classification, "id"),
            name=getattr(classification, "name"),
            level=getattr(classification, "level"),
            parent_id=getattr(classification, "parent_id"),
            is_active=getattr(classification, "is_active", True),
            sort_order=getattr(classification, "sort_order", 0),
            created_at=getattr(classification, "created_at"),
            updated_at=getattr(classification, "updated_at"),
            path=path,
            children=[],
        )

        if max_level and getattr(classification, "level") >= max_level:
            return tree_node

        # 获取子分类
        stmt = select(Classification).filter(
            Classification.parent_id == classification.id
        )
        if active_only:
            stmt = stmt.filter(Classification.is_active == True)

        stmt = stmt.order_by(Classification.sort_order, Classification.name)
        result = await self.db.execute(stmt)
        children = result.scalars().all()

        # 递归构建子分类
        for child in children:
            child_node = await self._build_classification_tree(
                child, max_level, active_only
            )
            tree_node.children.append(child_node)

        return tree_node

    async def get_classifications(
        self,
        level: Optional[int] = None,
        parent_id: Optional[int] = None,
        active_only: bool = True,
    ) -> List[ClassificationSchema]:
        """获取分类列表"""
        stmt = select(Classification)

        if level:
            stmt = stmt.filter(Classification.level == level)

        if parent_id is not None:
            stmt = stmt.filter(Classification.parent_id == parent_id)
        elif parent_id is None and level == 1:
            stmt = stmt.filter(Classification.parent_id.is_(None))

        if active_only:
            stmt = stmt.filter(Classification.is_active == True)

        stmt = stmt.order_by(Classification.sort_order, Classification.name)
        result = await self.db.execute(stmt)
        classifications = result.scalars().all()

        return [ClassificationSchema.model_validate(c) for c in classifications]

    async def get_classification_by_id(
        self, classification_id: int
    ) -> Optional[ClassificationWithChildren]:
        """获取单个分类详情"""
        stmt = select(Classification).filter(Classification.id == classification_id)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()

        if not classification:
            return None

        return await self._build_classification_tree(classification, active_only=False)

    async def create_classification(
        self, classification_data: ClassificationCreate
    ) -> ClassificationSchema:
        """创建分类"""
        # 验证父分类
        if classification_data.parent_id:
            stmt = select(Classification).filter(
                Classification.id == classification_data.parent_id
            )
            result = await self.db.execute(stmt)
            parent = result.scalar_one_or_none()
            if not parent:
                raise ValueError("父分类不存在")

            # 验证级别关系
            if classification_data.level != parent.level + 1:
                raise ValueError("分类级别不正确")
        else:
            if classification_data.level != 1:
                raise ValueError("一级分类不能有父分类")

        # 检查同级名称唯一性
        stmt = select(Classification).filter(
            and_(
                Classification.name == classification_data.name,
                Classification.parent_id == classification_data.parent_id,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("同级分类名称已存在")

        classification = Classification(**classification_data.model_dump())
        self.db.add(classification)
        await self.db.commit()
        await self.db.refresh(classification)

        return ClassificationSchema.model_validate(classification)

    async def update_classification(
        self, classification_id: int, classification_data: ClassificationUpdate
    ) -> Optional[ClassificationSchema]:
        """更新分类"""
        stmt = select(Classification).filter(Classification.id == classification_id)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()

        if not classification:
            return None

        # 检查名称唯一性
        if classification_data.name:
            stmt = select(Classification).filter(
                and_(
                    Classification.name == classification_data.name,
                    Classification.parent_id == classification.parent_id,
                    Classification.id != classification_id,
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                raise ValueError("同级分类名称已存在")

        # 更新字段
        update_data = classification_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(classification, field, value)

        await self.db.commit()
        await self.db.refresh(classification)

        return ClassificationSchema.model_validate(classification)

    async def delete_classification(self, classification_id: int) -> bool:
        """删除分类"""
        stmt = select(Classification).filter(Classification.id == classification_id)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()

        if not classification:
            return False

        # 检查是否有子分类
        from sqlalchemy import func

        stmt = select(func.count(Classification.id)).filter(
            Classification.parent_id == classification_id
        )
        result = await self.db.execute(stmt)
        children_count = result.scalar()
        if children_count is None:
            raise ValueError("分类不存在")

        if children_count > 0:
            raise ValueError("存在子分类，无法删除")

        # Note: In V2.0, we check for repository classifications instead of model classifications
        # This check is removed as it's handled by RepositoryClassification in repository.py

        await self.db.delete(classification)
        await self.db.commit()

        return True

    async def get_children(
        self, classification_id: int, active_only: bool = True
    ) -> List[ClassificationSchema]:
        """获取分类的子分类"""
        stmt = select(Classification).filter(
            Classification.parent_id == classification_id
        )

        if active_only:
            stmt = stmt.filter(Classification.is_active == True)

        stmt = stmt.order_by(Classification.sort_order, Classification.name)
        result = await self.db.execute(stmt)
        children = result.scalars().all()

        return [ClassificationSchema.model_validate(c) for c in children]

    async def get_classification_path(self, classification_id: int) -> List[str]:
        """获取分类路径（单查询优化版本）"""
        from sqlalchemy import text
        
        # 使用递归CTE获取完整路径
        query = text("""
            WITH RECURSIVE classification_path AS (
                -- 基础查询：获取目标分类
                SELECT id, name, parent_id, level, 0 as depth
                FROM classifications 
                WHERE id = :classification_id
                
                UNION ALL
                
                -- 递归查询：获取父级分类
                SELECT c.id, c.name, c.parent_id, c.level, cp.depth + 1
                FROM classifications c
                INNER JOIN classification_path cp ON c.id = cp.parent_id
            )
            SELECT name FROM classification_path 
            ORDER BY depth DESC
        """)
        
        result = await self.db.execute(query, {"classification_id": classification_id})
        names = result.scalars().all()
        
        return list(names)

    async def get_classification_descendants(self, classification_id: int) -> List[int]:
        """获取分类的所有后代ID（用于筛选）"""
        descendants = [classification_id]

        async def get_children_recursive(parent_id: int):
            stmt = select(Classification).filter(Classification.parent_id == parent_id)
            result = await self.db.execute(stmt)
            children = result.scalars().all()

            for child in children:
                descendants.append(getattr(child, "id"))
                await get_children_recursive(getattr(child, "id"))

        await get_children_recursive(classification_id)
        return descendants

    async def add_repository_classification(
        self, repository_id: int, classification_id: int
    ) -> List[dict]:
        """为仓库添加分类，自动处理层次关系"""
        from app.models.repository import RepositoryClassification

        # 获取选择的分类
        stmt = select(Classification).filter(Classification.id == classification_id)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()

        if not classification:
            raise ValueError("分类不存在")

        # 删除该仓库的所有现有分类
        from sqlalchemy import delete

        stmt = delete(RepositoryClassification).filter(
            RepositoryClassification.repository_id == repository_id
        )
        await self.db.execute(stmt)

        result = []

        # 添加选择的分类
        repo_classification = RepositoryClassification(
            repository_id=repository_id,
            classification_id=classification_id,
            level=classification.level,
        )
        self.db.add(repo_classification)
        result.append(
            {
                "id": classification_id,
                "name": classification.name,
                "level": classification.level,
                "selected_level": classification.level,
            }
        )

        # 自动添加父级分类
        current_classification = classification
        while current_classification.parent_id is not None:
            stmt = select(Classification).filter(
                Classification.id == current_classification.parent_id
            )
            result_parent = await self.db.execute(stmt)
            parent = result_parent.scalar_one_or_none()

            if parent:
                parent_repo_classification = RepositoryClassification(
                    repository_id=repository_id,
                    classification_id=parent.id,
                    level=classification.level,  # 记录用户选择的是哪一级
                )
                self.db.add(parent_repo_classification)
                result.append(
                    {
                        "id": parent.id,
                        "name": parent.name,
                        "level": parent.level,
                        "selected_level": classification.level,
                    }
                )
                current_classification = parent
            else:
                break

        await self.db.commit()

        # 返回所有关联的分类
        return await self.get_repository_classifications(repository_id)

    async def get_repository_classifications(self, repository_id: int) -> List[dict]:
        """获取仓库的所有分类"""
        from app.models.repository import RepositoryClassification

        stmt = select(RepositoryClassification).filter(
            RepositoryClassification.repository_id == repository_id
        )
        result_rc = await self.db.execute(stmt)
        repo_classifications = result_rc.scalars().all()

        result = []
        for rc in repo_classifications:
            path = await self.get_classification_path(getattr(rc, "classification_id"))
            stmt = select(Classification).filter(
                Classification.id == rc.classification_id
            )
            result_class = await self.db.execute(stmt)
            classification = result_class.scalar_one_or_none()

            if classification:
                result.append(
                    {
                        "id": rc.id,
                        "repository_id": rc.repository_id,
                        "classification_id": rc.classification_id,
                        "level": rc.level,
                        "created_at": rc.created_at,
                        "classification": {
                            "id": classification.id,
                            "name": classification.name,
                            "level": classification.level,
                            "parent_id": classification.parent_id,
                        },
                        "path": path,
                    }
                )

        return result

    async def remove_repository_classification(self, repository_id: int) -> bool:
        """移除仓库的所有分类关联"""
        from app.models.repository import RepositoryClassification
        from sqlalchemy import delete

        stmt = delete(RepositoryClassification).filter(
            RepositoryClassification.repository_id == repository_id
        )
        result = await self.db.execute(stmt)

        await self.db.commit()
        return result.rowcount > 0

    async def get_repositories_by_classification(
        self, classification_id: int, include_children: bool = True
    ) -> List[int]:
        """根据分类获取仓库ID列表"""
        from app.models.repository import RepositoryClassification

        classification_ids = [classification_id]

        if include_children:
            # 获取所有子分类
            descendants = await self.get_classification_descendants(classification_id)
            classification_ids.extend(descendants)

        stmt = (
            select(RepositoryClassification.repository_id)
            .filter(RepositoryClassification.classification_id.in_(classification_ids))
            .distinct()
        )
        result = await self.db.execute(stmt)
        repo_classifications = result.scalars().all()

        return list(repo_classifications)
