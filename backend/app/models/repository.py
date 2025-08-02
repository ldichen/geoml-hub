from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, ARRAY, JSON, BIGINT, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Repository(Base):
    """模型仓库表"""
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    full_name = Column(String(512), nullable=False, unique=True, index=True)  # owner/repo_name
    description = Column(Text)
    
    # 所有者信息
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 仓库类型和可见性
    repo_type = Column(String(50), default="model")  # model, dataset, space
    visibility = Column(String(20), default="public")  # public, private
    
    # README.md 解析的元数据
    repo_metadata = Column(JSON)  # YAML frontmatter 解析结果
    readme_content = Column(Text)  # README.md 内容
    
    # 标签和分类
    tags = Column(ARRAY(String))
    license = Column(String(100))
    base_model = Column(String(255))  # 基础模型名称
    
    # 统计信息
    stars_count = Column(Integer, default=0, index=True)
    downloads_count = Column(Integer, default=0, index=True)
    views_count = Column(Integer, default=0, index=True)
    forks_count = Column(Integer, default=0)
    
    # 文件和存储信息
    total_files = Column(Integer, default=0)
    total_size = Column(BIGINT, default=0)
    
    # 文件编辑和版本控制信息 (v2.0 扩展)
    total_commits = Column(Integer, default=0)
    last_commit_message = Column(Text)
    
    # 状态
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    last_commit_at = Column(DateTime(timezone=True))
    
    # 关系
    owner = relationship("User", back_populates="repositories")
    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")
    stars = relationship("RepositoryStar", back_populates="repository", cascade="all, delete-orphan")
    views = relationship("RepositoryView", back_populates="repository", cascade="all, delete-orphan")
    classifications = relationship("RepositoryClassification", back_populates="repository", cascade="all, delete-orphan")
    model_services = relationship("ModelService", back_populates="repository", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="repository", cascade="all, delete-orphan")
    
    @property
    def image_count(self):
        """当前仓库的镜像数量"""
        return len([img for img in self.images if img.status != 'deleted'])
    
    @property
    def can_add_image(self):
        """是否可以添加新镜像（每个仓库最多3个镜像）"""
        return self.image_count < 3


class RepositoryFile(Base):
    """仓库文件表"""
    __tablename__ = "repository_files"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # 文件信息
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)  # 仓库内相对路径
    file_type = Column(String(100))  # 文件类型分类
    mime_type = Column(String(200))
    file_size = Column(BIGINT, nullable=False)
    
    # MinIO 存储信息
    minio_bucket = Column(String(255), nullable=False)
    minio_object_key = Column(String(1000), nullable=False)
    file_hash = Column(String(128))  # SHA256
    
    # 版本和状态
    version = Column(String(50), default="latest")
    is_deleted = Column(Boolean, default=False)
    
    # 文件编辑和版本控制信息 (v2.0 扩展)
    current_version = Column(Integer, default=1)
    last_edit_session_id = Column(String(255))
    is_text_file = Column(Boolean, default=False)
    encoding = Column(String(20), default="utf-8")
    
    # 下载统计
    download_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('repository_id', 'file_path', name='unique_file_per_repo'),
    )
    
    # 关系
    repository = relationship("Repository", back_populates="files")
    downloads = relationship("FileDownload", back_populates="file", cascade="all, delete-orphan")


class RepositoryStar(Base):
    """仓库收藏表"""
    __tablename__ = "repository_stars"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'repository_id', name='unique_user_star'),
    )
    
    # 关系
    user = relationship("User", back_populates="stars")
    repository = relationship("Repository", back_populates="stars")


class RepositoryView(Base):
    """仓库访问记录表"""
    __tablename__ = "repository_views"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # 可以是匿名访问
    ip_address = Column(String(45))  # IPv6 支持
    user_agent = Column(Text)
    referer = Column(String(1000))
    
    # 访问详情
    view_type = Column(String(50), default="page_view")  # page_view, file_view, download
    target_path = Column(String(1000))  # 访问的具体路径或文件
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    repository = relationship("Repository", back_populates="views")
    user = relationship("User", back_populates="repository_views")


class RepositoryClassification(Base):
    """仓库分类关联表"""
    __tablename__ = "repository_classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    classification_id = Column(Integer, ForeignKey("classifications.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(Integer, nullable=False, index=True)  # 记录选择的是哪一级分类
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('repository_id', 'classification_id', name='unique_repo_classification'),
    )
    
    # 关系
    repository = relationship("Repository", back_populates="classifications")
    classification = relationship("Classification")