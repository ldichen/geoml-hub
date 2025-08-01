from sqlalchemy import Column, Integer, String, DateTime, Boolean, BIGINT, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PersonalFile(Base):
    """用户个人文件表 - 独立于仓库的个人数据空间"""
    __tablename__ = "personal_files"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 文件基本信息
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)  # 在个人空间中的路径
    file_size = Column(BIGINT, nullable=False, default=0)
    file_type = Column(String(100))  # 文件类型: image, document, data, model, other
    mime_type = Column(String(200))
    file_hash = Column(String(128), index=True)  # 文件内容哈希
    
    # MinIO 存储信息
    minio_bucket = Column(String(255), nullable=False)
    minio_object_key = Column(String(1000), nullable=False, index=True)
    
    # 文件元数据
    description = Column(Text)
    tags = Column(Text)  # 用逗号分隔的标签
    is_public = Column(Boolean, default=False)  # 是否公开
    
    # 状态信息
    is_deleted = Column(Boolean, default=False, index=True)
    upload_status = Column(String(20), default="completed", index=True)  # pending, uploading, completed, failed
    
    # 统计信息
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed_at = Column(DateTime(timezone=True))
    
    # 关系
    user = relationship("User", back_populates="personal_files")
    downloads = relationship("PersonalFileDownload", back_populates="file", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'file_path', 'filename', name='unique_user_file_path_name'),
    )


class PersonalFileDownload(Base):
    """个人文件下载记录表"""
    __tablename__ = "personal_file_downloads"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("personal_files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))  # 下载者，可以为空（匿名下载）
    ip_address = Column(String(45))  # IPv4/IPv6 地址
    user_agent = Column(String(500))
    download_size = Column(BIGINT)  # 实际下载的字节数
    download_status = Column(String(20), default="completed")  # completed, failed, cancelled
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 关系
    file = relationship("PersonalFile", back_populates="downloads")
    user = relationship("User")


class PersonalFolder(Base):
    """个人文件夹表 - 支持文件夹结构"""
    __tablename__ = "personal_folders"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 文件夹信息
    name = Column(String(255), nullable=False, index=True)
    path = Column(String(1000), nullable=False, index=True)  # 完整路径
    parent_id = Column(Integer, ForeignKey("personal_folders.id", ondelete="CASCADE"))  # 父文件夹
    
    # 元数据
    description = Column(Text)
    color = Column(String(7))  # 文件夹颜色（十六进制）
    is_public = Column(Boolean, default=False)
    
    # 状态
    is_deleted = Column(Boolean, default=False, index=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User")
    parent = relationship("PersonalFolder", remote_side=[id], back_populates="children")
    children = relationship("PersonalFolder", back_populates="parent", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'path', name='unique_user_folder_path'),
    )