"""
镜像管理数据库模型
"""

import re
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Image(Base):
    """镜像模型 - 管理仓库绑定的镜像"""

    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True, comment="镜像ID")

    # 用户上传的原始信息
    original_name = Column(String(255), nullable=False, comment="原始镜像名称")
    original_tag = Column(String(100), nullable=False, comment="原始镜像标签")
    repository_id = Column(
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属仓库ID",
    )

    # Harbor存储信息（自动计算，不直接存储）
    harbor_digest = Column(String(255), comment="镜像摘要")
    harbor_size = Column(BigInteger, comment="镜像大小(字节)")

    # 镜像元数据
    description = Column(Text, comment="镜像描述")
    dockerfile_content = Column(Text, comment="Dockerfile内容")
    build_context = Column(JSON, comment="构建上下文信息")

    # 状态信息
    status = Column(
        String(50),
        default="uploading",
        comment="镜像状态: uploading, ready, failed, deleted",
    )
    upload_progress = Column(Integer, default=0, comment="上传进度(0-100)")
    error_message = Column(Text, comment="错误信息")

    # 访问控制
    is_public = Column(Boolean, default=False, comment="是否公开")
    created_by = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="创建用户ID"
    )

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    # 关系
    repository = relationship("Repository", back_populates="images")
    creator = relationship("User", foreign_keys=[created_by])
    services = relationship(
        "ModelService", back_populates="image", cascade="all, delete-orphan"
    )

    # 索引和约束
    __table_args__ = (
        # 唯一约束：同一仓库中original_name:original_tag必须唯一
        UniqueConstraint(
            "original_name",
            "original_tag",
            "repository_id",
            name="uq_image_original_name_tag_repo",
        ),
        # 索引
        Index("ix_images_repository_status", "repository_id", "status"),
        Index("ix_images_created_by", "created_by"),
    )

    def __repr__(self):
        return f"<Image(id={self.id}, original_name={self.original_name}:{self.original_tag}, repository_id={self.repository_id})>"

    @property
    def harbor_storage_name(self):
        """Harbor中的存储名称：原始名称-ID"""
        # 规范化原始名称，确保符合Docker命名规范
        normalized_name = re.sub(r"[^a-z0-9.-]", "-", self.original_name.lower())
        # 去除连续的分隔符和首尾分隔符
        normalized_name = re.sub(r"[-_.]{2,}", "-", normalized_name)
        normalized_name = normalized_name.strip("-_.")
        return f"{normalized_name}-{self.id}"

    @property
    def harbor_repository_path(self):
        """Harbor仓库路径（简化版）"""
        return self.harbor_storage_name

    @property
    def display_name(self):
        """用户界面显示名称"""
        return f"{self.original_name}:{self.original_tag}"

    @property
    def full_name(self):
        """完整的镜像名称（保持向后兼容）"""
        return self.display_name

    @property
    def full_docker_image_name(self):
        """完整Docker镜像地址"""
        from app.config import settings

        harbor_url = settings.harbor_url

        # 处理Harbor URL，提取主机地址（去除协议，保留端口）
        if "://" in harbor_url:
            harbor_host = harbor_url.split("://")[-1]
        else:
            harbor_host = harbor_url

        # 如果没有指定端口，且是HTTPS，则不需要端口号；如果是HTTP且不是80端口，需要指定端口
        # Harbor默认端口：HTTP为80，HTTPS为443
        if ":" not in harbor_host:
            if harbor_url.startswith("https://"):
                # HTTPS默认443端口，Harbor通常在443端口
                pass  # 不添加端口
            else:
                # HTTP协议，Harbor可能在其他端口，这里我们根据实际情况处理
                # 根据你的配置，Harbor在172.21.252.230上，可能需要端口
                if harbor_host != "localhost" and harbor_host != "127.0.0.1":
                    # 生产环境的Harbor，检查是否需要添加端口
                    pass

        harbor_project = settings.harbor_default_project
        return f"{harbor_host}/{harbor_project}/{self.harbor_storage_name}:{self.original_tag}"

    @property
    def full_image_name_with_registry(self):
        """包含Harbor仓库地址的完整镜像名称，用于Docker拉取（保持向后兼容）"""
        return self.full_docker_image_name

    @property
    def service_count(self):
        """当前镜像创建的服务数量"""
        return len([s for s in self.services if s.status != "deleted"])

    @property
    def can_create_service(self):
        """是否可以创建新服务（每个镜像最多2个服务）"""
        return self.service_count < 2 and self.status == "ready"


class ImageBuildLog(Base):
    """镜像构建日志"""

    __tablename__ = "image_build_logs"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    image_id = Column(
        Integer,
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        comment="镜像ID",
    )

    # 日志内容
    stage = Column(String(100), comment="构建阶段")
    message = Column(Text, comment="日志消息")
    level = Column(
        String(20), default="info", comment="日志级别: debug, info, warning, error"
    )

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    # 关系
    image = relationship("Image")

    # 索引
    __table_args__ = (Index("ix_build_logs_image_created", "image_id", "created_at"),)
