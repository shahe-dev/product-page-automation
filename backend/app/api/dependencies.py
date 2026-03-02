"""
API Dependencies

Provides common dependencies for FastAPI route handlers including
authentication, database sessions, and service instances.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.database import get_db_session
from app.middleware.auth import (
    get_current_user,
    get_current_user_optional,
    get_current_active_user,
)
from app.models.database import User, Project
from app.models.enums import UserRole


# Re-export database session dependency
get_db = get_db_session


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify current user is an admin.

    Args:
        current_user: Current authenticated user

    Returns:
        User model instance if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FORBIDDEN: Admin access required"
        )
    return current_user


async def get_project_or_404(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Project:
    """
    Get project by ID or raise 404.

    Args:
        project_id: Project UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Project model instance

    Raises:
        HTTPException: If project not found or user doesn't have access
    """
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.is_active == True
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PROJECT_NOT_FOUND: Project {project_id} not found"
        )

    # Check access: owner or admin
    if project.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FORBIDDEN: You don't have access to this project"
        )

    return project


# NOTE: get_job_or_404 is defined in app.api.routes.jobs (route-local dependency).
# PaginationParams is defined in app.models.schemas. Import from there if needed.
# These were removed to eliminate duplicate definitions (audit P3-5, P3-6).
