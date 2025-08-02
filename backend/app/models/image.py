"""
镜像管理数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Image(Base):
    """镜像模型 - 管理仓库绑定的镜像"""
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True, comment="镜像ID")
    
    # 基本信息
    name = Column(String(255), nullable=False, comment="镜像名称")
    tag = Column(String(100), nullable=False, comment="镜像标签")
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, comment="所属仓库ID")
    
    # Harbor相关信息
    harbor_project = Column(String(255), nullable=False, comment="Harbor项目名称")
    harbor_repository = Column(String(500), nullable=False, comment="Harbor仓库路径")
    harbor_digest = Column(String(255), comment="镜像摘要")
    harbor_size = Column(Integer, comment="镜像大小(字节)")
    
    # 镜像元数据
    description = Column(Text, comment="镜像描述")
    dockerfile_content = Column(Text, comment="Dockerfile内容")
    build_context = Column(JSON, comment="构建上下文信息")
    
    # 状态信息
    status = Column(String(50), default="uploading", comment="镜像状态: uploading, ready, failed, deleted")
    upload_progress = Column(Integer, default=0, comment="上传进度(0-100)")
    error_message = Column(Text, comment="错误信息")
    
    # 访问控制
    is_public = Column(Boolean, default=False, comment="是否公开")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建用户ID")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    repository = relationship("Repository", back_populates="images")
    creator = relationship("User", foreign_keys=[created_by])
    services = relationship("Service", back_populates="image", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('ix_images_repository_status', 'repository_id', 'status'),
        Index('ix_images_harbor_path', 'harbor_project', 'harbor_repository'),
        Index('ix_images_created_by', 'created_by'),
    )
    
    def __repr__(self):
        return f"<Image(id={self.id}, name={self.name}:{self.tag}, repository_id={self.repository_id})>"
    
    @property
    def full_name(self):
        """完整的镜像名称"""
        return f"{self.harbor_project}/{self.harbor_repository}:{self.tag}"
    
    @property
    def service_count(self):
        """当前镜像创建的服务数量"""
        return len([s for s in self.services if s.status != 'deleted'])
    
    @property
    def can_create_service(self):
        """是否可以创建新服务（每个镜像最多2个服务）"""
        return self.service_count < 2 and self.status == 'ready'


class ImageBuildLog(Base):
    """镜像构建日志"""
    __tablename__ = "image_build_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False, comment="镜像ID")
    
    # 日志内容
    stage = Column(String(100), comment="构建阶段")
    message = Column(Text, comment="日志消息")
    level = Column(String(20), default="info", comment="日志级别: debug, info, warning, error")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    image = relationship("Image")
    
    # 索引
    __table_args__ = (
        Index('ix_build_logs_image_created', 'image_id', 'created_at'),
    )