"""
Authentication related Pydantic schemas
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class TokenData(BaseModel):
    """JWT token payload data"""
    external_user_id: str


class UserInfo(BaseModel):
    """User information from external authentication service"""
    external_user_id: str = Field(..., description="External user ID from auth service")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    display_name: Optional[str] = Field(None, max_length=100, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=128, description="User password")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")


class LoginCredentials(BaseModel):
    """Direct login with email and password"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=128, description="User password")


class Token(BaseModel):
    """Access token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., description="Refresh token")


class ExternalTokenRequest(BaseModel):
    """External token validation request"""
    external_token: str = Field(..., description="Token from external auth service")


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: dict = Field(..., description="User information")
    refresh_token: Optional[str] = Field(None, description="Refresh token from OpenGMS")


class LoginRequest(BaseModel):
    """Login request with external token"""
    external_token: str = Field(..., description="Token from external authentication service")


class LogoutRequest(BaseModel):
    """Logout request"""
    token: Optional[str] = Field(None, description="Token to revoke")


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class TwoFactorSetupRequest(BaseModel):
    """Two-factor authentication setup request"""
    enable: bool = Field(..., description="Enable or disable 2FA")
    secret: Optional[str] = Field(None, description="2FA secret key")


class TwoFactorVerifyRequest(BaseModel):
    """Two-factor authentication verification request"""
    code: str = Field(..., min_length=6, max_length=6, description="2FA verification code")


class SessionInfo(BaseModel):
    """User session information"""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")


class ApiKeyCreate(BaseModel):
    """API key creation request"""
    name: str = Field(..., max_length=100, description="API key name")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    scopes: Optional[list[str]] = Field(default=[], description="API key scopes")


class ApiKeyResponse(BaseModel):
    """API key response"""
    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    description: Optional[str] = Field(None, description="API key description")
    key: str = Field(..., description="API key value (only shown once)")
    created_at: datetime = Field(..., description="Creation time")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    last_used: Optional[datetime] = Field(None, description="Last used time")
    is_active: bool = Field(..., description="Whether key is active")


class ApiKeyInfo(BaseModel):
    """API key information (without the key value)"""
    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    description: Optional[str] = Field(None, description="API key description")
    created_at: datetime = Field(..., description="Creation time")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    last_used: Optional[datetime] = Field(None, description="Last used time")
    is_active: bool = Field(..., description="Whether key is active")