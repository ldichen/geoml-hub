"""
Authentication service for handling JWT tokens and user authentication
Enhanced with OpenGMS user server integration
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.user_service import UserService
from app.services.opengms_user_service import opengms_user_service
from app.models.user import User
from app.schemas.auth import TokenData, UserInfo
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Service for handling authentication and JWT tokens
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token

        Args:
            data: Data to encode in token
            expires_delta: Token expiration time

        Returns:
            str: JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.algorithm
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verify JWT token and extract data

        Args:
            token: JWT token to verify

        Returns:
            TokenData: Extracted token data or None if invalid
        """
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.algorithm]
            )
            external_user_id = payload.get("sub")
            if external_user_id is None:
                return None
            return TokenData(external_user_id=external_user_id)
        except JWTError:
            return None

    async def authenticate_user(self, external_user_id: str) -> Optional[User]:
        """
        Authenticate user by external user ID

        Args:
            external_user_id: External user ID from auth service

        Returns:
            User: User object or None if not found
        """
        return await self.user_service.get_user_by_external_id(external_user_id)

    async def sync_user_from_external(self, user_info: UserInfo) -> User:
        """
        Sync user information from external authentication service

        Args:
            user_info: User information from external service

        Returns:
            User: Created or updated user
        """
        # Check if user already exists
        existing_user = await self.user_service.get_user_by_external_id(
            user_info.external_user_id
        )

        if existing_user:
            # Update existing user information
            user_data = {
                "email": user_info.email,
                "full_name": user_info.display_name,
                "avatar_url": user_info.avatar_url,
                "updated_at": datetime.utcnow(),
            }
            return await self.user_service.update_user(str(existing_user.id), user_data)
        else:
            # Create new user
            from app.schemas.user import UserCreate

            user_create = UserCreate(
                external_user_id=user_info.external_user_id,
                username=user_info.username,
                email=user_info.email,
                full_name=user_info.display_name,
                avatar_url=user_info.avatar_url,
                bio=None,
                website=None,
                location=None,
            )
            return await self.user_service.create_user(user_create)

    async def create_user_token(self, user: User) -> str:
        """
        Create access token for user

        Args:
            user: User object

        Returns:
            str: JWT access token
        """
        token_data = {"sub": user.external_user_id, "username": user.username}
        return self.create_access_token(token_data)

    async def refresh_user_token(self, refresh_token: str) -> Optional[str]:
        """
        Refresh user access token

        Args:
            refresh_token: Refresh token

        Returns:
            str: New access token or None if invalid refresh token
        """
        token_data = self.verify_token(refresh_token)
        if not token_data:
            return None

        user = await self.authenticate_user(token_data.external_user_id)
        if not user:
            return None

        return await self.create_user_token(user)

    async def revoke_user_tokens(self, user_id: str) -> bool:
        """
        Revoke all tokens for a user
        Note: This is a placeholder for token blacklist implementation

        Args:
            user_id: User ID

        Returns:
            bool: True if successful
        """
        # TODO: Implement token blacklist in Redis
        # For now, we'll just log the revocation
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Tokens revoked for user {user_id}")
        return True

    async def register_with_opengms(
        self, email: str, password: str, **kwargs
    ) -> Dict[str, Any]:
        """
        在OpenGMS用户服务器注册用户并同步到本地

        Args:
            email: 用户邮箱
            password: 原始密码
            **kwargs: 其他用户信息

        Returns:
            Dict包含注册结果
        """
        # 1. 在OpenGMS用户服务器注册
        register_result = await opengms_user_service.register_user(
            email, password, **kwargs
        )

        if not register_result["success"]:
            return register_result

        # 2. 获取OAuth2 token
        token_result = await opengms_user_service.get_oauth2_token(email, password)

        if not token_result["success"]:
            return {
                "success": False,
                "message": "注册成功但登录失败，请手动登录",
                "data": None,
            }

        # 3. 获取用户信息
        access_token = token_result["data"]["access_token"]
        user_info_result = await opengms_user_service.get_user_info(
            access_token, "127.0.0.1"
        )

        if not user_info_result["success"]:
            return {
                "success": False,
                "message": "注册成功但获取用户信息失败",
                "data": None,
            }

        # 4. 同步到本地数据库
        local_user = await opengms_user_service.sync_user_to_local(
            self.db, user_info_result["data"]
        )

        if not local_user:
            return {"success": False, "message": "用户信息同步失败", "data": None}

        # 5. 生成内部JWT token
        internal_token = await self.create_user_token(local_user)

        from app.schemas.user import UserPublic

        return {
            "success": True,
            "message": "注册成功",
            "data": {
                "user": UserPublic.model_validate(local_user).model_dump(),
                "access_token": internal_token,
                "opengms_token": token_result["data"],
            },
        }

    async def login_with_opengms(
        self, email: str, password: str, ip_address: str = ""
    ) -> Dict[str, Any]:
        """
        使用OpenGMS用户服务器进行登录

        Args:
            email: 用户邮箱
            password: 原始密码
            ip_address: 客户端IP地址

        Returns:
            Dict包含登录结果
        """
        # 1. 获取OAuth2 token
        token_result = await opengms_user_service.get_oauth2_token(
            email, password, ip_address
        )

        if not token_result["success"]:
            return token_result

        # 2. 获取用户信息
        access_token = token_result["data"]["access_token"]
        user_info_result = await opengms_user_service.get_user_info(
            access_token, ip_address
        )

        if not user_info_result["success"]:
            return {"success": False, "message": "获取用户信息失败", "data": None}

        # 3. 同步到本地数据库
        local_user = await opengms_user_service.sync_user_to_local(
            self.db, user_info_result["data"]
        )

        if not local_user:
            return {"success": False, "message": "用户信息同步失败", "data": None}

        # 4. 生成内部JWT token
        internal_token = await self.create_user_token(local_user)

        from app.schemas.user import UserPublic

        return {
            "success": True,
            "message": "登录成功",
            "data": {
                "user": UserPublic.model_validate(local_user).model_dump(),
                "access_token": internal_token,
                "opengms_token": token_result["data"],
            },
        }

    async def refresh_opengms_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新OpenGMS访问令牌

        Args:
            refresh_token: OpenGMS刷新令牌

        Returns:
            Dict包含新的token信息
        """
        return await opengms_user_service.refresh_token(refresh_token)

    def validate_external_token(self, external_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate token from external authentication service

        Args:
            external_token: Token from external service

        Returns:
            Dict: User information from external service or None if invalid
        """
        try:
            # Decode JWT token with external auth secret key
            payload = jwt.decode(
                external_token, settings.external_auth_secret_key, algorithms=["HS256"]
            )

            # Extract user information from payload
            user_info = {
                "external_user_id": payload.get("sub"),
                "username": payload.get("username")
                or payload.get("preferred_username"),
                "email": payload.get("email"),
                "display_name": payload.get("name") or payload.get("display_name"),
                "avatar_url": payload.get("avatar_url") or payload.get("picture"),
            }

            # Validate required fields
            if not user_info.get("external_user_id") or not user_info.get("email"):
                logger.warning(f"Invalid external token: missing required fields")
                return None

            logger.info(
                f"Successfully validated external token for user: {user_info.get('username')}"
            )
            return user_info

        except JWTError as e:
            logger.error(f"JWT validation failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in token validation: {str(e)}")
            return None
