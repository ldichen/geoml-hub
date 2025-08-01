"""
OpenGMS用户服务器集成服务
基于OpenGMS架构实现OAuth2 Password Grant流程
"""

import hashlib
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenGMSUserService:
    """OpenGMS用户服务器集成服务"""

    def __init__(self):
        self.base_url = settings.opengms_user_server_url
        self.client_id = settings.opengms_oauth2_client_id
        self.client_secret = settings.opengms_oauth2_client_secret
        self.timeout = settings.opengms_auth_timeout

    def _encrypt_password(self, password: str) -> str:
        """双重密码加密，与OpenGMS保持一致"""
        # 第一层：MD5
        md5_hash = hashlib.md5(password.encode()).hexdigest()
        # 第二层：SHA256
        sha256_hash = hashlib.sha256(md5_hash.encode()).hexdigest()
        return sha256_hash

    def _process_avatar_url(self, avatar_path: str) -> str:
        """处理头像URL，将相对路径转换为完整URL"""
        if not avatar_path:
            return avatar_path

        # 如果已经是完整URL，直接返回
        if avatar_path.startswith("http://") or avatar_path.startswith("https://"):
            return avatar_path

        # 确保路径以/开头
        if not avatar_path.startswith("/"):
            avatar_path = "/" + avatar_path

        # 拼接完整URL
        return f"{self.base_url}{avatar_path}"

    async def register_user(
        self, email: str, password: str, **kwargs
    ) -> Dict[str, Any]:
        """
        在OpenGMS用户服务器注册用户

        Args:
            email: 用户邮箱
            password: 原始密码
            **kwargs: 其他用户信息

        Returns:
            Dict包含注册结果和用户信息
        """
        encrypted_password = self._encrypt_password(password)

        # 构建注册数据
        register_data = {"email": email, "password": encrypted_password, **kwargs}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/user",
                    json=register_data,
                    headers={"Content-Type": "application/json;charset=UTF-8"},
                )

                result = response.json()
                logger.info(f"OpenGMS register response: {result}")

                return {
                    "success": result.get("code") == 0,
                    "message": result.get("msg", ""),
                    "data": result.get("data"),
                    "code": result.get("code"),
                }

        except Exception as e:
            logger.error(f"OpenGMS register error: {str(e)}")
            return {
                "success": False,
                "message": f"注册失败: {str(e)}",
                "data": None,
                "code": -1,
            }

    async def get_oauth2_token(
        self, email: str, password: str, ip_address: str = ""
    ) -> Dict[str, Any]:
        """
        获取OAuth2访问令牌（Password Grant模式）

        Args:
            email: 用户邮箱
            password: 原始密码
            ip_address: 客户端IP地址

        Returns:
            Dict包含token信息
        """
        encrypted_password = self._encrypt_password(password)

        # OAuth2 Password Grant参数
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": email,
            "password": encrypted_password,
            "scope": "all",
            "grant_type": "password",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/oauth/token",
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    return {"success": False, "message": "获取token失败", "data": None}

                token_result = response.json()
                logger.info(f"OpenGMS token response: {token_result}")

                return {
                    "success": True,
                    "data": {
                        "access_token": token_result.get("access_token"),
                        "refresh_token": token_result.get("refresh_token"),
                        "expires_in": token_result.get("expires_in"),
                        "invalid_time": token_result.get("invalidTime"),
                    },
                }

        except Exception as e:
            logger.error(f"OpenGMS get token error: {str(e)}")
            return {"success": False, "message": f"登录失败: {str(e)}", "data": None}

    async def get_user_info(
        self, access_token: str, ip_address: str = ""
    ) -> Dict[str, Any]:
        """
        使用access_token获取用户信息

        Args:
            access_token: OAuth2访问令牌
            ip_address: 客户端IP地址

        Returns:
            Dict包含用户信息
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/auth/login/{ip_address}",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": "获取用户信息失败",
                        "data": None,
                    }

                result = response.json()
                logger.info(f"OpenGMS user info response: {result}")

                if result.get("data") is None:
                    return {
                        "success": False,
                        "message": "用户信息获取失败",
                        "data": None,
                    }

                return {"success": True, "data": result.get("data")}

        except Exception as e:
            logger.error(f"OpenGMS get user info error: {str(e)}")
            return {
                "success": False,
                "message": f"获取用户信息失败: {str(e)}",
                "data": None,
            }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            Dict包含新的token信息
        """
        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/oauth/token",
                    data=refresh_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    return {"success": False, "message": "刷新token失败", "data": None}

                token_result = response.json()
                logger.info(f"OpenGMS refresh token response: {token_result}")

                return {
                    "success": True,
                    "data": {
                        "access_token": token_result.get("access_token"),
                        "refresh_token": token_result.get("refresh_token"),
                        "expires_in": token_result.get("expires_in"),
                        "invalid_time": token_result.get("invalidTime"),
                    },
                }

        except Exception as e:
            logger.error(f"OpenGMS refresh token error: {str(e)}")
            return {
                "success": False,
                "message": f"刷新token失败: {str(e)}",
                "data": None,
            }

    async def verify_token(self, access_token: str) -> Dict[str, Any]:
        """
        验证访问令牌并获取用户信息

        Args:
            access_token: OAuth2访问令牌

        Returns:
            Dict包含验证结果和用户信息
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/auth/userInfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                if response.status_code != 200:
                    return {"success": False, "message": "token验证失败", "data": None}

                result = response.json()
                logger.info(f"OpenGMS verify token response: {result}")

                if result.get("code") != 0:
                    return {
                        "success": False,
                        "message": result.get("msg", "token无效"),
                        "data": None,
                    }

                return {"success": True, "data": result.get("data")}

        except Exception as e:
            logger.error(f"OpenGMS verify token error: {str(e)}")
            return {
                "success": False,
                "message": f"token验证失败: {str(e)}",
                "data": None,
            }

    async def sync_user_to_local(
        self, db: AsyncSession, opengms_user_data: Dict[str, Any]
    ) -> Optional[User]:
        """
        将OpenGMS用户信息同步到本地数据库

        Args:
            db: 数据库会话
            opengms_user_data: OpenGMS返回的用户数据

        Returns:
            本地用户对象
        """
        try:
            # 查找是否已存在用户
            user_id = opengms_user_data.get("userId")
            email = opengms_user_data.get("email")

            if not user_id or not email:
                logger.error("OpenGMS用户数据缺少必要字段")
                return None

            # 先通过external_user_id查找
            stmt = select(User).where(User.external_user_id == user_id)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # 更新现有用户信息
                existing_user.username = opengms_user_data.get(
                    "name"
                ) or opengms_user_data.get("username", existing_user.username)
                existing_user.email = email
                avatar_path = opengms_user_data.get("avatar", existing_user.avatar_url)
                existing_user.avatar_url = (
                    self._process_avatar_url(avatar_path)
                    if avatar_path
                    else existing_user.avatar_url
                )
                existing_user.updated_at = datetime.utcnow()

                await db.commit()
                await db.refresh(existing_user)
                logger.info(f"更新本地用户: {existing_user.username}")
                return existing_user
            else:
                # 创建新用户
                avatar_path = opengms_user_data.get("avatar")
                new_user = User(
                    username=opengms_user_data.get("name")
                    or opengms_user_data.get("username")
                    or f"user_{user_id[:8]}",
                    email=email,
                    external_user_id=user_id,
                    avatar_url=(
                        self._process_avatar_url(avatar_path) if avatar_path else None
                    ),
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                logger.info(f"创建新本地用户: {new_user.username}")
                return new_user

        except Exception as e:
            logger.error(f"同步用户到本地数据库失败: {str(e)}")
            await db.rollback()
            return None


# 全局实例
opengms_user_service = OpenGMSUserService()
