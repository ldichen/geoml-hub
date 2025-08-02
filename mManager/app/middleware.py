"""
mManager 中间件
"""

import time
import logging
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """API密钥认证中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer()
    
    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查和文档接口的认证
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # 检查Authorization头
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization format")
        
        token = authorization.replace("Bearer ", "")
        if token != settings.api_key:
            logger.warning(f"Invalid API key attempt from {request.client.host}")
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return await call_next(request)

class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 记录请求开始
        logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
        
        # 处理请求
        response = await call_next(request)
        
        # 记录请求完成
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Server-ID"] = settings.server_id
        
        return response