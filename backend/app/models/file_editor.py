from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, BIGINT, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class FileVersionType(enum.Enum):
    """文件版本类型枚举"""
    INITIAL = "initial"     # 初始版本
    EDIT = "edit"          # 编辑版本
    MERGE = "merge"        # 合并版本
    BRANCH = "branch"      # 分支版本


class FileVersion(Base):
    """文件版本表"""
    __tablename__ = "file_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    
    # 版本信息
    version_number = Column(Integer, nullable=False)  # 版本号（从1开始）
    version_hash = Column(String(64), nullable=False, unique=True, index=True)  # 版本哈希（前8位commit hash）
    version_type = Column(Enum(FileVersionType), default=FileVersionType.EDIT)
    
    # 提交信息
    commit_message = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    author_name = Column(String(255))  # 提交时的作者名
    author_email = Column(String(255))  # 提交时的作者邮箱
    
    # 文件内容
    content_hash = Column(String(128), nullable=False)  # 文件内容SHA256
    file_size = Column(BIGINT, nullable=False)
    
    # MinIO存储信息
    minio_bucket = Column(String(255), nullable=False)
    minio_object_key = Column(String(1000), nullable=False)
    
    # 差异信息
    parent_version_id = Column(Integer, ForeignKey("file_versions.id", ondelete="SET NULL"), nullable=True)
    diff_summary = Column(JSON)  # 差异摘要：{lines_added: 10, lines_removed: 5, lines_changed: 2}
    
    # 元数据
    encoding = Column(String(50), default="utf-8")
    mime_type = Column(String(200))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    file = relationship("RepositoryFile")
    author = relationship("User")
    parent_version = relationship("FileVersion", remote_side=[id])
    child_versions = relationship("FileVersion", back_populates="parent_version")


class FileEditSession(Base):
    """文件编辑会话表"""
    __tablename__ = "file_edit_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 编辑状态
    is_active = Column(Boolean, default=True)
    is_readonly = Column(Boolean, default=False)
    
    # 编辑内容
    current_content = Column(Text)  # 当前编辑内容
    base_version_id = Column(Integer, ForeignKey("file_versions.id", ondelete="CASCADE"), nullable=False)
    
    # 自动保存
    auto_save_interval = Column(Integer, default=30)  # 秒
    last_auto_save = Column(DateTime(timezone=True))
    
    # 协作信息
    cursor_position = Column(JSON)  # 光标位置：{line: 10, column: 5}
    selection_range = Column(JSON)  # 选择范围：{start: {line: 1, column: 0}, end: {line: 2, column: 10}}
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # 关系
    file = relationship("RepositoryFile")
    user = relationship("User")
    base_version = relationship("FileVersion")


class FileEditPermission(Base):
    """文件编辑权限表"""
    __tablename__ = "file_edit_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 权限类型
    can_read = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    can_commit = Column(Boolean, default=False)
    can_manage = Column(Boolean, default=False)  # 管理权限（修改权限等）
    
    # 权限来源
    permission_source = Column(String(50))  # owner, collaborator, public
    granted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # 关系
    file = relationship("RepositoryFile")
    user = relationship("User", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])


class FileDraft(Base):
    """文件草稿表"""
    __tablename__ = "file_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 草稿内容
    draft_content = Column(Text)  # 草稿内容
    base_version_id = Column(Integer, ForeignKey("file_versions.id", ondelete="CASCADE"), nullable=False)
    
    # 编辑信息
    cursor_position = Column(JSON)  # 保存的光标位置
    selection_range = Column(JSON)  # 保存的选择范围
    
    # 草稿元数据
    title = Column(String(255))  # 草稿标题（可选）
    description = Column(Text)  # 草稿描述（可选）
    
    # 状态信息
    is_auto_saved = Column(Boolean, default=True)  # 是否自动保存
    auto_save_count = Column(Integer, default=0)  # 自动保存次数
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_access = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    file = relationship("RepositoryFile")
    user = relationship("User")
    base_version = relationship("FileVersion")


class FileTemplate(Base):
    """文件模板表"""
    __tablename__ = "file_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # 模板内容
    template_content = Column(Text, nullable=False)
    file_extension = Column(String(20))
    language = Column(String(50))
    
    # 分类和标签
    category = Column(String(100))  # python, javascript, markdown, config等
    tags = Column(JSON)  # ["ml", "pytorch", "config"]
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    
    # 作者和权限
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_public = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # 系统内置模板
    is_active = Column(Boolean, default=True)  # 模板状态
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    author = relationship("User")