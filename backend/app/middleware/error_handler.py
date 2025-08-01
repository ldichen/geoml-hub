"""
Global error handling middleware for FastAPI
"""

import traceback
from typing import Union, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import logging

# Set up logger
logger = logging.getLogger(__name__)


class GeoMLHubException(Exception):
    """Base exception for GeoML-Hub application"""

    def __init__(
        self, message: str, status_code: int = 500, error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class AuthenticationError(GeoMLHubException):
    """Authentication related errors"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_ERROR")


class AuthorizationError(GeoMLHubException):
    """Authorization/permission related errors"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "AUTHORIZATION_ERROR")


class NotFoundError(GeoMLHubException):
    """Resource not found errors"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND, "NOT_FOUND_ERROR")


class ConflictError(GeoMLHubException):
    """Resource conflict errors"""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT, "CONFLICT_ERROR")


class DataValidationError(GeoMLHubException):
    """Data validation errors"""

    def __init__(self, message: str = "Validation error"):
        super().__init__(
            message, status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR"
        )


class StorageError(GeoMLHubException):
    """File storage related errors"""

    def __init__(self, message: str = "Storage operation failed"):
        super().__init__(message, status.HTTP_507_INSUFFICIENT_STORAGE, "STORAGE_ERROR")


class ExternalServiceError(GeoMLHubException):
    """External service integration errors"""

    def __init__(self, message: str = "External service error"):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY, "EXTERNAL_SERVICE_ERROR")


async def geoml_hub_exception_handler(
    request: Request, exc: GeoMLHubException
) -> JSONResponse:
    """Handle custom GeoML-Hub exceptions"""
    logger.error(f"GeoML-Hub exception: {exc.error_code} - {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "type": "application_error",
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def http_exception_handler(
    request: Request, exc: Union[HTTPException, StarletteHTTPException]
) -> JSONResponse:
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "type": "http_error",
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")

    # Format validation errors for better user experience
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append(
            {"field": field_path, "message": error["msg"], "type": error["type"]}
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "type": "validation_error",
                "details": formatted_errors,
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    logger.error(f"Database error: {type(exc).__name__} - {str(exc)}")

    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        if "duplicate key value" in str(exc).lower():
            message = "Resource already exists"
            code = "DUPLICATE_RESOURCE"
            status_code = status.HTTP_409_CONFLICT
        elif "foreign key constraint" in str(exc).lower():
            message = "Referenced resource not found"
            code = "FOREIGN_KEY_VIOLATION"
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            message = "Data integrity error"
            code = "INTEGRITY_ERROR"
            status_code = status.HTTP_400_BAD_REQUEST
    else:
        message = "Database operation failed"
        code = "DATABASE_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code, "message": message, "type": "database_error"},
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unexpected exceptions"""
    # Log the full traceback for debugging
    logger.error(f"Unexpected error: {type(exc).__name__} - {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    # Don't expose internal error details in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "type": "internal_error",
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


def add_exception_handlers(app):
    """Add all exception handlers to FastAPI app"""

    # Custom application exceptions
    app.add_exception_handler(GeoMLHubException, geoml_hub_exception_handler)

    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Database exceptions
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # General exceptions (catch-all)
    app.add_exception_handler(Exception, general_exception_handler)
