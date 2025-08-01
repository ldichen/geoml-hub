"""
Security utilities using the application SECRET_KEY
"""
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class SecurityTokenManager:
    """
    Manages various security tokens using the application SECRET_KEY
    """
    
    def __init__(self):
        self.serializer = URLSafeTimedSerializer(settings.secret_key)
    
    def generate_password_reset_token(self, email: str) -> str:
        """
        Generate a password reset token
        
        Args:
            email: User email address
            
        Returns:
            str: Password reset token
        """
        try:
            token = self.serializer.dumps(email, salt='password-reset')
            logger.info(f"Generated password reset token for {email}")
            return token
        except Exception as e:
            logger.error(f"Failed to generate password reset token: {e}")
            raise
    
    def verify_password_reset_token(self, token: str, max_age: int = 3600) -> Optional[str]:
        """
        Verify a password reset token
        
        Args:
            token: Password reset token
            max_age: Maximum age in seconds (default: 1 hour)
            
        Returns:
            str: Email address if valid, None if invalid
        """
        try:
            email = self.serializer.loads(
                token, 
                salt='password-reset', 
                max_age=max_age
            )
            logger.info(f"Verified password reset token for {email}")
            return email
        except SignatureExpired:
            logger.warning("Password reset token expired")
            return None
        except BadSignature:
            logger.warning("Invalid password reset token signature")
            return None
        except Exception as e:
            logger.error(f"Error verifying password reset token: {e}")
            return None
    
    def generate_email_verification_token(self, user_id: str) -> str:
        """
        Generate an email verification token
        
        Args:
            user_id: User ID
            
        Returns:
            str: Email verification token
        """
        try:
            token = self.serializer.dumps(user_id, salt='email-verification')
            logger.info(f"Generated email verification token for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to generate email verification token: {e}")
            raise
    
    def verify_email_verification_token(self, token: str, max_age: int = 86400) -> Optional[str]:
        """
        Verify an email verification token
        
        Args:
            token: Email verification token
            max_age: Maximum age in seconds (default: 24 hours)
            
        Returns:
            str: User ID if valid, None if invalid
        """
        try:
            user_id = self.serializer.loads(
                token, 
                salt='email-verification', 
                max_age=max_age
            )
            logger.info(f"Verified email verification token for user {user_id}")
            return user_id
        except SignatureExpired:
            logger.warning("Email verification token expired")
            return None
        except BadSignature:
            logger.warning("Invalid email verification token signature")
            return None
        except Exception as e:
            logger.error(f"Error verifying email verification token: {e}")
            return None
    
    def generate_api_key_token(self, user_id: str, api_key_id: str) -> str:
        """
        Generate an API key token
        
        Args:
            user_id: User ID
            api_key_id: API key ID
            
        Returns:
            str: API key token
        """
        try:
            data = {"user_id": user_id, "api_key_id": api_key_id}
            token = self.serializer.dumps(data, salt='api-key')
            logger.info(f"Generated API key token for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to generate API key token: {e}")
            raise
    
    def verify_api_key_token(self, token: str) -> Optional[dict]:
        """
        Verify an API key token
        
        Args:
            token: API key token
            
        Returns:
            dict: Token data if valid, None if invalid
        """
        try:
            data = self.serializer.loads(token, salt='api-key')
            logger.info(f"Verified API key token for user {data.get('user_id')}")
            return data
        except BadSignature:
            logger.warning("Invalid API key token signature")
            return None
        except Exception as e:
            logger.error(f"Error verifying API key token: {e}")
            return None

# 全局实例
security_token_manager = SecurityTokenManager()