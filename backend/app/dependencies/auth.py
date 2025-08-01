"""
Authentication dependencies for FastAPI routes
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.config import settings
from app.services.user_service import UserService
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_db),
) -> Optional[User]:
    """
    Get current authenticated user from JWT token
    Returns None if no token provided or invalid token
    """
    if not credentials:
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.algorithm],
        )
        external_user_id = payload.get("sub")
        if external_user_id is None:
            return None

    except JWTError:
        return None

    user_service = UserService(db)
    user = await user_service.get_user_by_external_id(external_user_id)
    return user


async def get_current_user_required(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Get current authenticated user, raise 401 if not authenticated
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """
    Get current active user, raise 403 if user is inactive
    """
    if not getattr(current_user, "is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


async def verify_repository_access(
    repository_full_name: str,
    current_user: Optional[User],
    db: AsyncSession,
    require_owner: bool = False,
) -> bool:
    """
    Verify if user has access to repository

    Args:
        repository_full_name: Repository full name (owner/repo)
        current_user: Current authenticated user (can be None)
        db: Database session
        require_owner: If True, requires user to be repository owner

    Returns:
        bool: True if user has access, False otherwise
    """
    from app.services.repository_service import RepositoryService

    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(repository_full_name)

    if not repository:
        return False

    # Public repositories are accessible to everyone
    if getattr(repository, "visibility") == "public" and not require_owner:
        return True

    # Private repositories require authentication
    if not current_user:
        return False

    # Owner always has access
    if repository.owner_id == current_user.id:
        return True

    # For private repos, only owner has access (for now)
    # TODO: Implement collaborator system
    if getattr(repository, "visibility") == "private":
        return False

    return True


async def require_repository_owner(
    owner: str,
    repo_name: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Dependency to check if current user owns the repository
    """
    repository_full_name = f"{owner}/{repo_name}"

    has_access = await verify_repository_access(
        repository_full_name=repository_full_name,
        current_user=current_user,
        db=db,
        require_owner=True,
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only repository owner can perform this action",
        )

    return current_user


async def require_repository_access(
    owner: str,
    repo_name: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Dependency to check if current user has access to the repository
    Returns the repository if access is granted
    """
    from app.services.repository_service import RepositoryService
    
    repository_full_name = f"{owner}/{repo_name}"
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(repository_full_name)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    has_access = await verify_repository_access(
        repository_full_name=repository_full_name,
        current_user=current_user,
        db=db,
        require_owner=False,
    )

    if not has_access:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this repository",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this repository",
            )

    return repository


async def get_repository_access(
    owner: str,
    repo_name: str,
    current_user: Optional[User],
    db: AsyncSession
):
    """
    Get repository if user has access to it
    """
    from app.services.repository_service import RepositoryService
    
    repository_full_name = f"{owner}/{repo_name}"
    repo_service = RepositoryService(db)
    repository = await repo_service.get_repository_by_full_name(repository_full_name)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    # Public repositories are accessible to everyone
    if getattr(repository, "visibility") == "public":
        return repository

    # Private repositories require authentication
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this repository",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Owner always has access
    if repository.owner_id == current_user.id:
        return repository

    # For private repos, only owner has access (for now)
    # TODO: Implement collaborator system
    if getattr(repository, "visibility") == "private":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this repository",
        )

    return repository


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to check if current user has admin privileges
    """
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
