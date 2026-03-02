"""Admin-only endpoints for user and allowlist management."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.config.database import get_db_session
from app.models.database import EmailAllowlist, Job, Project, User
from app.models.enums import JobStatus, UserRole
from app.models.schemas import (
    AllowlistEntryCreate,
    AllowlistEntryResponse,
    AllowlistEntryUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# =====================================================================
# ALLOWLIST CRUD
# =====================================================================


@router.get("/allowlist", response_model=list[AllowlistEntryResponse])
async def list_allowlist(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(EmailAllowlist)
        .where(EmailAllowlist.is_active == True)
        .order_by(EmailAllowlist.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/allowlist",
    response_model=AllowlistEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_allowlist_entry(
    request: AllowlistEntryCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    # Check duplicate
    existing = await db.execute(
        select(EmailAllowlist).where(EmailAllowlist.email == request.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already in allowlist")

    try:
        role = UserRole(request.role)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid role: {request.role}")

    entry = EmailAllowlist(
        email=request.email,
        role=role,
        added_by=current_user.id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.put("/allowlist/{entry_id}", response_model=AllowlistEntryResponse)
async def update_allowlist_entry(
    entry_id: UUID,
    request: AllowlistEntryUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(EmailAllowlist).where(
            EmailAllowlist.id == str(entry_id)
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    try:
        entry.role = UserRole(request.role)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid role: {request.role}")

    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/allowlist/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allowlist_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(EmailAllowlist).where(
            EmailAllowlist.id == str(entry_id)
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry.is_active = False
    await db.commit()


# =====================================================================
# ADMIN STATS & USER MANAGEMENT
# =====================================================================


@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    user_count = (await db.execute(
        select(sa_func.count()).select_from(User).where(User.is_active == True)
    )).scalar() or 0

    active_jobs = (await db.execute(
        select(sa_func.count()).select_from(Job).where(
            Job.status.in_([JobStatus.PENDING.value, JobStatus.PROCESSING.value])
        )
    )).scalar() or 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    failed_jobs_24h = (await db.execute(
        select(sa_func.count()).select_from(Job).where(
            Job.status == JobStatus.FAILED.value,
            Job.updated_at >= cutoff,
        )
    )).scalar() or 0

    total_projects = (await db.execute(
        select(sa_func.count()).select_from(Project).where(Project.is_active == True)
    )).scalar() or 0

    status_rows = (await db.execute(
        select(Project.workflow_status, sa_func.count())
        .where(Project.is_active == True)
        .group_by(Project.workflow_status)
    )).all()
    projects_by_status = {
        row[0].value if hasattr(row[0], "value") else str(row[0]): row[1]
        for row in status_rows
    }

    return {
        "user_count": user_count,
        "active_jobs": active_jobs,
        "failed_jobs_24h": failed_jobs_24h,
        "total_projects": total_projects,
        "projects_by_status": projects_by_status,
    }


@router.get("/users")
async def list_users(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(User).where(User.is_active == True).order_by(User.name)
    )
    users = result.scalars().all()

    user_list = []
    for u in users:
        proj_count = (await db.execute(
            select(sa_func.count()).select_from(Project).where(
                Project.created_by == u.id, Project.is_active == True
            )
        )).scalar() or 0

        user_list.append({
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "project_count": proj_count,
        })
    return user_list


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    request: AllowlistEntryUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).where(User.id == str(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        user.role = UserRole(request.role)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid role: {request.role}")

    await db.commit()
    await db.refresh(user)
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
    }
