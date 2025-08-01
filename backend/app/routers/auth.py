"""
Authentication API endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user, get_current_active_user
from app.schemas.auth import (
    LoginRequest,
    LoginCredentials,
    RegisterRequest,
    AuthResponse,
    ExternalTokenRequest,
    UserInfo,
    Token,
    TokenRefresh,
    LogoutRequest,
)
from app.schemas.user import UserPublic
from app.models.user import User
from app.config import settings
from datetime import datetime, timedelta, timezone
from app.utils.mock_external_auth import mock_external_auth

router = APIRouter()
security = HTTPBearer()


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    forwarded = request.headers.get("x-forwarded")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "127.0.0.1"


@router.post(
    "/register", response_model=AuthResponse, summary="Register new user with OpenGMS"
)
async def register(
    register_request: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Register a new user with OpenGMS user server
    
    - **email**: User email address
    - **password**: User password (will be encrypted)
    - **username**: Optional username
    - **full_name**: Optional full name
    
    Returns user information and access token
    """
    auth_service = AuthService(db)
    client_ip = get_client_ip(request)
    
    # 准备注册数据
    register_data = {
        "username": register_request.username or register_request.email.split("@")[0],
        "fullName": register_request.full_name,
    }
    
    # 使用OpenGMS注册
    result = await auth_service.register_with_opengms(
        register_request.email,
        register_request.password,
        **register_data
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    user_data = result["data"]
    
    return AuthResponse(
        access_token=user_data["access_token"],
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_data["user"],
        refresh_token=user_data["opengms_token"]["refresh_token"],
    )


@router.post(
    "/login/credentials", response_model=AuthResponse, summary="Login with email and password"
)
async def login_credentials(
    login_request: LoginCredentials,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Login with email and password using OpenGMS user server
    
    - **email**: User email address
    - **password**: User password
    
    Returns user information and access token
    """
    auth_service = AuthService(db)
    client_ip = get_client_ip(request)
    
    # 使用OpenGMS登录
    result = await auth_service.login_with_opengms(
        login_request.email,
        login_request.password,
        client_ip
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = result["data"]
    
    return AuthResponse(
        access_token=user_data["access_token"],
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_data["user"],
        refresh_token=user_data["opengms_token"]["refresh_token"],
    )


@router.post(
    "/login", response_model=AuthResponse, summary="User login with external token"
)
async def login(
    login_request: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Login user with external authentication token

    - **external_token**: JWT token from external authentication service

    Returns user information and access token for this service
    """
    auth_service = AuthService(db)

    # Validate external token and get user info
    import logging
    logger = logging.getLogger(__name__)
    
    user_info_dict = auth_service.validate_external_token(login_request.external_token)
    if not user_info_dict:
        logger.error("Login failed: Invalid external token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid external token. Please check your authentication credentials."
        )

    # Convert to UserInfo schema
    user_info = UserInfo(**user_info_dict)

    # Sync user information from external service
    user = await auth_service.sync_user_from_external(user_info)

    # Update last login information
    # TODO: 临时注释掉，调试完成后再启用
    # from datetime import datetime
    # await auth_service.user_service.update_user(
    #     str(user.id),
    #     {
    #         "last_active_at": datetime.now(timezone.utc),
    #         "last_seen_at": datetime.now(timezone.utc),
    #     },
    # )

    # Create access token
    access_token = await auth_service.create_user_token(user)

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.full_name,
            "avatar_url": user.avatar_url,
        },
    )


@router.post("/verify", response_model=UserPublic, summary="Verify current token")
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """
    Verify current JWT token and return user information

    This endpoint can be used by frontend to check if token is still valid
    """
    return UserPublic.model_validate(current_user)


@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(
    token_refresh: TokenRefresh, db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh access token using OpenGMS refresh token

    - **refresh_token**: Valid OpenGMS refresh token

    Returns new access token
    """
    auth_service = AuthService(db)
    
    # 使用OpenGMS刷新token
    result = await auth_service.refresh_opengms_token(token_refresh.refresh_token)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = result["data"]
    
    return Token(
        access_token=token_data["access_token"],
        token_type="bearer",
        expires_in=token_data["expires_in"],
    )


@router.post("/logout", summary="Logout user")
async def logout(
    logout_request: LogoutRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Logout user and revoke tokens

    - **token**: Optional token to revoke (if not provided, uses current user's tokens)
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    auth_service = AuthService(db)
    await auth_service.revoke_user_tokens(str(current_user.id))

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserPublic, summary="Get current user")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information
    """
    return UserPublic.model_validate(current_user)


@router.post(
    "/sync", response_model=UserPublic, summary="Sync user from external service"
)
async def sync_user(
    external_token_request: ExternalTokenRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Sync user information from external authentication service

    This endpoint allows updating user information based on external auth service data
    """
    auth_service = AuthService(db)

    # Validate external token
    import logging
    logger = logging.getLogger(__name__)
    
    user_info_dict = auth_service.validate_external_token(
        external_token_request.external_token
    )
    if not user_info_dict:
        logger.error("Token sync failed: Invalid external token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid external token. Please check your authentication credentials."
        )

    user_info = UserInfo(**user_info_dict)
    user = await auth_service.sync_user_from_external(user_info)

    return UserPublic.model_validate(user)


@router.post("/mock-external-auth", summary="Mock external authentication (dev only)")
async def mock_external_auth_endpoint(
    request: dict,  # {"email": "...", "password": "..."}
):
    """
    Mock external authentication endpoint for development
    
    This endpoint simulates what an external authentication service would do:
    1. Validate user credentials
    2. Return a signed JWT token
    
    Only use this in development!
    """
    email = request.get("email")
    password = request.get("password")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )
    
    # Create external token using mock service
    external_token = mock_external_auth.create_external_token(email, password)
    if not external_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    return {
        "external_token": external_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "message": "Mock external authentication successful"
    }


@router.get("/health", summary="Authentication service health check")
async def auth_health_check():
    """
    Health check endpoint for authentication service
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "2.0.0",
    }
