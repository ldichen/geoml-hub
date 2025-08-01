"""
MinIO service dependency for FastAPI
"""
from typing import Annotated
from fastapi import Depends
from app.services.minio_service import MinIOService

# MinIO service instance
_minio_service = None


def get_minio_service() -> MinIOService:
    """
    Get MinIO service instance.
    This function creates a singleton MinIO service instance.
    """
    global _minio_service
    
    if _minio_service is None:
        _minio_service = MinIOService()
    
    return _minio_service


# Type alias for dependency injection
MinIOServiceDep = Annotated[MinIOService, Depends(get_minio_service)]