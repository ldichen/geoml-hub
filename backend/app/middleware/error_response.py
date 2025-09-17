"""
统一错误响应格式和错误处理中间件
"""
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import traceback
import logging

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """错误详情模型"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    field: Optional[str] = Field(None, description="相关字段（验证错误时使用）")
    context: Optional[Dict[str, Any]] = Field(None, description="错误上下文信息")


class StandardErrorResponse(BaseModel):
    """标准错误响应格式"""
    success: bool = Field(False, description="请求是否成功")
    error: ErrorDetail = Field(..., description="错误详情")
    request_id: Optional[str] = Field(None, description="请求ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="错误发生时间")
    path: Optional[str] = Field(None, description="请求路径")


class ErrorCodes:
    """错误代码常量"""
    # 通用错误
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    BAD_REQUEST = "BAD_REQUEST"

    # 仓库相关错误
    REPOSITORY_NOT_FOUND = "REPOSITORY_NOT_FOUND"
    REPOSITORY_ALREADY_EXISTS = "REPOSITORY_ALREADY_EXISTS"
    REPOSITORY_CREATE_FAILED = "REPOSITORY_CREATE_FAILED"
    INVALID_REPOSITORY_NAME = "INVALID_REPOSITORY_NAME"

    # 文件相关错误
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"

    # 用户相关错误
    USER_NOT_FOUND = "USER_NOT_FOUND"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"

    # 存储相关错误
    STORAGE_ERROR = "STORAGE_ERROR"

    # 外部服务错误
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # 数据库错误
    DATABASE_ERROR = "DATABASE_ERROR"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    FOREIGN_KEY_VIOLATION = "FOREIGN_KEY_VIOLATION"


class ErrorResponseBuilder:
    """错误响应构建器"""

    @staticmethod
    def build_error_response(
        status_code: int,
        error_code: str,
        message: str,
        field: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        path: Optional[str] = None
    ) -> JSONResponse:
        """构建标准错误响应"""
        error_detail = ErrorDetail(
            code=error_code,
            message=message,
            field=field,
            context=context
        )

        error_response = StandardErrorResponse(
            error=error_detail,
            request_id=request_id,
            path=path
        )

        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump(mode='json')
        )


class BusinessException(Exception):
    """业务异常基类"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        field: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.field = field
        self.context = context or {}
        super().__init__(message)


class RepositoryException(BusinessException):
    """仓库相关异常"""

    def __init__(self, message: str, error_code: str = ErrorCodes.REPOSITORY_CREATE_FAILED, **kwargs):
        super().__init__(message, error_code, **kwargs)


class FileException(BusinessException):
    """文件相关异常"""

    def __init__(self, message: str, error_code: str = ErrorCodes.FILE_UPLOAD_FAILED, **kwargs):
        super().__init__(message, error_code, **kwargs)


class UserException(BusinessException):
    """用户相关异常"""

    def __init__(self, message: str, error_code: str = ErrorCodes.USER_NOT_FOUND, **kwargs):
        super().__init__(message, error_code, **kwargs)


class StorageException(BusinessException):
    """存储相关异常"""

    def __init__(self, message: str, error_code: str = ErrorCodes.STORAGE_ERROR, **kwargs):
        super().__init__(message, error_code, status_code=507, **kwargs)


class ExternalServiceException(BusinessException):
    """外部服务异常"""

    def __init__(self, message: str, error_code: str = ErrorCodes.EXTERNAL_SERVICE_ERROR, **kwargs):
        super().__init__(message, error_code, status_code=502, **kwargs)


class DatabaseException(BusinessException):
    """数据库异常"""

    def __init__(self, message: str, error_code: str = ErrorCodes.DATABASE_ERROR, **kwargs):
        super().__init__(message, error_code, status_code=500, **kwargs)


# 为了兼容旧代码的常用异常别名
class NotFoundError(BusinessException):
    """资源未找到异常"""

    def __init__(self, message: str = "资源不存在", **kwargs):
        super().__init__(message, ErrorCodes.NOT_FOUND, status_code=404, **kwargs)


class AuthorizationError(BusinessException):
    """权限不足异常"""

    def __init__(self, message: str = "权限不足", **kwargs):
        super().__init__(message, ErrorCodes.AUTHORIZATION_ERROR, status_code=403, **kwargs)


class ConflictError(BusinessException):
    """资源冲突异常"""

    def __init__(self, message: str = "资源冲突", **kwargs):
        super().__init__(message, ErrorCodes.CONFLICT, status_code=409, **kwargs)


class DataValidationError(BusinessException):
    """数据验证异常"""

    def __init__(self, message: str = "数据验证失败", **kwargs):
        super().__init__(message, ErrorCodes.VALIDATION_ERROR, status_code=422, **kwargs)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理器"""

    # 获取请求ID（如果有的话）
    request_id = getattr(request.state, 'request_id', None)
    path = str(request.url.path) if request.url else None

    # 处理业务异常
    if isinstance(exc, BusinessException):
        logger.warning(f"Business exception: {exc.error_code} - {exc.message}")
        return ErrorResponseBuilder.build_error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            field=exc.field,
            context=exc.context,
            request_id=request_id,
            path=path
        )

    # 处理 FastAPI HTTPException
    if isinstance(exc, HTTPException):
        error_code = _map_http_status_to_error_code(exc.status_code)
        return ErrorResponseBuilder.build_error_response(
            status_code=exc.status_code,
            error_code=error_code,
            message=str(exc.detail),
            request_id=request_id,
            path=path
        )

    # 处理验证错误
    if isinstance(exc, RequestValidationError):
        validation_errors = []
        for error in exc.errors():
            field_name = ".".join(str(loc) for loc in error["loc"])
            validation_errors.append({
                "field": field_name,
                "message": error["msg"],
                "type": error["type"]
            })

        return ErrorResponseBuilder.build_error_response(
            status_code=422,
            error_code=ErrorCodes.VALIDATION_ERROR,
            message="输入数据验证失败",
            context={"validation_errors": validation_errors},
            request_id=request_id,
            path=path
        )

    # 处理数据库错误
    if isinstance(exc, SQLAlchemyError):
        logger.error(f"Database error: {type(exc).__name__} - {str(exc)}")

        if isinstance(exc, IntegrityError):
            error_str = str(exc).lower()
            if "duplicate key value" in error_str or "unique constraint" in error_str:
                return ErrorResponseBuilder.build_error_response(
                    status_code=409,
                    error_code=ErrorCodes.DUPLICATE_RESOURCE,
                    message="资源已存在",
                    context={"database_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)},
                    request_id=request_id,
                    path=path
                )
            elif "foreign key constraint" in error_str:
                return ErrorResponseBuilder.build_error_response(
                    status_code=400,
                    error_code=ErrorCodes.FOREIGN_KEY_VIOLATION,
                    message="引用的资源不存在",
                    context={"database_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)},
                    request_id=request_id,
                    path=path
                )

        # 其他数据库错误
        return ErrorResponseBuilder.build_error_response(
            status_code=500,
            error_code=ErrorCodes.DATABASE_ERROR,
            message="数据库操作失败",
            context={"database_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)},
            request_id=request_id,
            path=path
        )

    # 处理未捕获的异常
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)

    # 生产环境不暴露详细错误信息
    import os
    is_development = os.getenv("ENVIRONMENT", "development") == "development"

    if is_development:
        error_message = f"{type(exc).__name__}: {str(exc)}"
        context = {
            "traceback": traceback.format_exc(),
            "exception_type": type(exc).__name__
        }
    else:
        error_message = "服务器内部错误，请稍后重试"
        context = None

    return ErrorResponseBuilder.build_error_response(
        status_code=500,
        error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
        message=error_message,
        context=context,
        request_id=request_id,
        path=path
    )


def _map_http_status_to_error_code(status_code: int) -> str:
    """将 HTTP 状态码映射到错误代码"""
    mapping = {
        400: ErrorCodes.BAD_REQUEST,
        401: ErrorCodes.AUTHENTICATION_ERROR,
        403: ErrorCodes.AUTHORIZATION_ERROR,
        404: ErrorCodes.NOT_FOUND,
        409: ErrorCodes.CONFLICT,
        422: ErrorCodes.VALIDATION_ERROR,
        500: ErrorCodes.INTERNAL_SERVER_ERROR,
    }
    return mapping.get(status_code, ErrorCodes.INTERNAL_SERVER_ERROR)