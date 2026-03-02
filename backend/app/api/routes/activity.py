"""Activity feed and team stats endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.middleware.auth import get_current_user
from app.models.database import Job, Project, ProjectApproval, User
from app.models.enums import JobStatus

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/feed")
async def get_activity_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    items = []

    # Query approval events
    approvals = await db.execute(
        select(ProjectApproval, Project.name, User.name.label("user_name"))
        .join(Project, ProjectApproval.project_id == Project.id)
        .join(User, ProjectApproval.approver_id == User.id)
        .order_by(ProjectApproval.created_at.desc())
        .limit(limit)
    )

    for row in approvals:
        approval = row[0]
        project_name = row[1]
        user_name = row[2]
        action = approval.action.value if hasattr(approval.action, "value") else str(approval.action)
        items.append({
            "id": str(approval.id),
            "type": f"approval_{action}",
            "title": f"Project {action}",
            "description": f'"{project_name}" was {action}',
            "timestamp": approval.created_at.isoformat() if approval.created_at else None,
            "user_name": user_name,
            "project_id": str(approval.project_id),
        })

    # Query completed/failed jobs
    jobs = await db.execute(
        select(Job, User.name.label("user_name"))
        .outerjoin(User, Job.user_id == User.id)
        .where(Job.status.in_([JobStatus.COMPLETED.value, JobStatus.FAILED.value]))
        .order_by(Job.updated_at.desc())
        .limit(limit)
    )

    for row in jobs:
        job = row[0]
        user_name = row[1] or "System"
        job_status = job.status.value if hasattr(job.status, "value") else str(job.status)
        project_id = None
        if job.result and isinstance(job.result, dict):
            project_id = job.result.get("project_id")
        items.append({
            "id": str(job.id),
            "type": f"job_{job_status}",
            "title": f"Job {job_status}",
            "description": f"Job {str(job.id)[:8]}... {job_status}",
            "timestamp": (job.updated_at or job.created_at).isoformat()
            if job.updated_at or job.created_at
            else None,
            "user_name": user_name,
            "project_id": project_id,
        })

    # Sort combined by timestamp desc, take page slice
    items.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    start = (page - 1) * limit
    items = items[start : start + limit]

    return {"items": items, "page": page, "limit": limit}


@router.get("/team-stats")
async def get_team_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    users = (await db.execute(
        select(User).where(User.is_active == True).order_by(User.name)
    )).scalars().all()

    stats = []
    for u in users:
        projects_week = (await db.execute(
            select(func.count()).select_from(Project).where(
                Project.created_by == u.id,
                Project.created_at >= week_ago,
            )
        )).scalar() or 0

        approvals_week = (await db.execute(
            select(func.count()).select_from(ProjectApproval).where(
                ProjectApproval.approver_id == u.id,
                ProjectApproval.created_at >= week_ago,
            )
        )).scalar() or 0

        stats.append({
            "user_id": str(u.id),
            "name": u.name,
            "email": u.email,
            "projects_this_week": projects_week,
            "approvals_this_week": approvals_week,
            "last_active": u.last_login_at.isoformat() if u.last_login_at else None,
        })

    return stats
