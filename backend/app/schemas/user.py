"""
Author: DiChen
Date: 2025-07-14 14:10:44
LastEditors: DiChen
LastEditTime: 2025-07-15 16:37:05
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    external_user_id: str = Field(..., min_length=1, max_length=255)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)


class UserProfile(UserBase):
    id: int
    external_user_id: str
    followers_count: int = 0
    following_count: int = 0
    public_repos_count: int = 0
    storage_quota: int
    storage_used: int
    is_active: bool = True
    is_verified: bool = False
    is_admin: bool = False  # 添加管理员权限字段
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime
    last_seen_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    """公开的用户信息（不包含敏感信息）"""

    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    public_repos_count: int = 0
    is_verified: bool = False
    is_admin: bool = False  # 添加管理员权限字段
    created_at: datetime

    class Config:
        from_attributes = True


class UserFollow(BaseModel):
    id: int
    follower: UserPublic
    following: UserPublic
    created_at: datetime

    class Config:
        from_attributes = True


class UserStorage(BaseModel):
    id: int
    user_id: int
    total_files: int = 0
    total_size: int = 0
    model_files_count: int = 0
    model_files_size: int = 0
    dataset_files_count: int = 0
    dataset_files_size: int = 0
    image_files_count: int = 0
    image_files_size: int = 0
    document_files_count: int = 0
    document_files_size: int = 0
    other_files_count: int = 0
    other_files_size: int = 0
    last_calculated_at: datetime

    class Config:
        from_attributes = True
