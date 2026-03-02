"""
Authorization decorators and permission checks for PDP Automation v.3

Provides:
- @require_admin decorator
- @require_role decorator
- @require_owner_or_admin decorator
"""

from typing import List, Callable, Optional
from functools import wraps
from uuid import UUID
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User, Project
from app.models.enums import UserRole
from app.services.user_service import user_service

logger = logging.getLogger(__name__)


def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin role.

    Usage:
        @router.delete("/projects/{project_id}")
        @require_admin
        async def delete_project(
            project_id: str,
            current_user: User = Depends(get_current_user)
        ):
            ...

    Args:
        func: Async function to wrap

    Returns:
        Wrapped function with admin check
    """
    @wraps(func)
    async def wrapper(*args, current_user: User, **kwargs):
        if current_user.role != UserRole.ADMIN:
            logger.warning(
                f"Unauthorized admin access attempt by {current_user.email} "
                f"(role: {current_user.role})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ADMIN_REQUIRED"
            )
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper


def require_role(allowed_roles: List[UserRole]) -> Callable:
    """
    Decorator to require specific roles.

    Usage:
        @router.post("/prompts")
        @require_role([UserRole.ADMIN])
        async def create_prompt(
            data: PromptCreate,
            current_user: User = Depends(get_current_user)
        ):
            ...

    Args:
        allowed_roles: List of allowed roles

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User, **kwargs):
            if current_user.role not in allowed_roles:
                logger.warning(
                    f"Unauthorized role access attempt by {current_user.email} "
                    f"(role: {current_user.role}, required: {allowed_roles})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"FORBIDDEN: Requires one of {[r.value for r in allowed_roles]}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


async def check_project_ownership(
    project_id: UUID,
    current_user: User,
    db: AsyncSession
) -> Project:
    """
    Check if user owns project or is admin.

    Args:
        project_id: Project UUID
        current_user: Current user
        db: Database session

    Returns:
        Project instance

    Raises:
        HTTPException: If project not found or access denied
    """
    from sqlalchemy import select

    # Get project
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PROJECT_NOT_FOUND"
        )

    # Check ownership or admin
    if project.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        logger.warning(
            f"Unauthorized project access attempt: user {current_user.email} "
            f"tried to access project {project_id} owned by {project.created_by}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NOT_PROJECT_OWNER"
        )

    return project


def require_owner_or_admin(func: Callable) -> Callable:
    """
    Decorator to require project ownership or admin role.

    The decorated function must have project_id and current_user parameters.

    Usage:
        @router.put("/projects/{project_id}")
        @require_owner_or_admin
        async def update_project(
            project_id: UUID,
            updates: ProjectUpdate,
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db)
        ):
            ...

    Args:
        func: Async function to wrap

    Returns:
        Wrapped function with ownership check
    """
    @wraps(func)
    async def wrapper(
        *args,
        project_id: UUID,
        current_user: User,
        db: AsyncSession,
        **kwargs
    ):
        # Check ownership
        project = await check_project_ownership(project_id, current_user, db)

        # Call original function
        return await func(
            *args,
            project_id=project_id,
            current_user=current_user,
            db=db,
            **kwargs
        )
    return wrapper


async def check_resource_ownership(
    resource_type: str,
    resource_id: UUID,
    user_id_field: str,
    current_user: User,
    db: AsyncSession
):
    """
    Generic resource ownership check.

    Args:
        resource_type: Type of resource (e.g., "project", "job")
        resource_id: Resource UUID
        user_id_field: Name of the user ID field (e.g., "created_by", "user_id")
        current_user: Current user
        db: Database session

    Raises:
        HTTPException: If resource not found or access denied
    """
    from sqlalchemy import select, inspect

    # Map resource types to models
    model_map = {
        "project": Project,
        "job": "Job",  # Import as needed
    }

    model_class = model_map.get(resource_type)
    if not model_class:
        raise ValueError(f"Unknown resource type: {resource_type}")

    # Get resource
    stmt = select(model_class).where(model_class.id == resource_id)
    result = await db.execute(stmt)
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type.upper()}_NOT_FOUND"
        )

    # Check ownership
    resource_user_id = getattr(resource, user_id_field, None)
    if resource_user_id != current_user.id and current_user.role != UserRole.ADMIN:
        logger.warning(
            f"Unauthorized {resource_type} access attempt: user {current_user.email} "
            f"tried to access {resource_type} {resource_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FORBIDDEN"
        )

    return resource


class PermissionChecker:
    """
    Dependency class for permission checking.

    Usage:
        @router.get("/projects/{project_id}")
        async def get_project(
            project_id: UUID,
            current_user: User = Depends(get_current_user),
            _: None = Depends(PermissionChecker(require_admin=True))
        ):
            ...
    """

    def __init__(
        self,
        require_admin: bool = False,
        allowed_roles: Optional[List[UserRole]] = None
    ):
        self.require_admin = require_admin
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User):
        """Check permissions."""
        if self.require_admin and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ADMIN_REQUIRED"
            )

        if self.allowed_roles and current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"FORBIDDEN: Requires one of {[r.value for r in self.allowed_roles]}"
            )
