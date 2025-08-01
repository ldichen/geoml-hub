"""
Mock external authentication service for development
"""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MockExternalAuthService:
    """
    Mock external authentication service for development and testing
    """
    
    def __init__(self):
        self.users = {
            # 模拟用户数据库
            "admin@geoml-hub.com": {
                "password": "admin123",
                "user_id": "mock_admin",
                "username": "admin",
                "display_name": "系统管理员",
                "avatar_url": "https://ui-avatars.com/api/?name=Admin&background=random"
            },
            "user@example.com": {
                "password": "user123",
                "user_id": "ext_user",
                "username": "testuser",
                "display_name": "Test User",
                "avatar_url": "https://ui-avatars.com/api/?name=Test+User&background=random"
            }
        }
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dict: User information if valid, None if invalid
        """
        user = self.users.get(email)
        if user and user["password"] == password:
            logger.info(f"Mock auth success for {email}")
            return {
                "external_user_id": user["user_id"],
                "username": user["username"],
                "email": email,
                "display_name": user["display_name"],
                "avatar_url": user["avatar_url"]
            }
        
        logger.warning(f"Mock auth failed for {email}")
        return None
    
    def create_external_token(self, email: str, password: str) -> Optional[str]:
        """
        Create external token for user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            str: JWT token if valid credentials, None if invalid
        """
        user_info = self.authenticate_user(email, password)
        if not user_info:
            return None
        
        # Create JWT token with user information
        token_data = {
            "sub": user_info["external_user_id"],
            "email": user_info["email"],
            "username": user_info["username"],
            "name": user_info["display_name"],
            "avatar_url": user_info["avatar_url"],
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "iss": "mock-auth-service"
        }
        
        token = jwt.encode(
            token_data,
            settings.external_auth_secret_key,
            algorithm="HS256"
        )
        
        logger.info(f"Created external token for {email}")
        return token
    
    def add_user(self, email: str, password: str, username: str, display_name: str = None):
        """
        Add a new user to the mock service
        
        Args:
            email: User email
            password: User password
            username: Username
            display_name: Display name (optional)
        """
        self.users[email] = {
            "password": password,
            "user_id": f"ext_{username}",
            "username": username,
            "display_name": display_name or username,
            "avatar_url": f"https://ui-avatars.com/api/?name={username}&background=random"
        }
        logger.info(f"Added mock user: {email}")

# 全局实例
mock_external_auth = MockExternalAuthService()