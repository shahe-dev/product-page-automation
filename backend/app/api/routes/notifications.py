"""Notification endpoints for the current user."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.middleware.auth import get_current_user
from app.models.database import Notification, User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    page: int = 1,
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    if unread_only:
        query = query.where(Notification.is_read == False)

    count_query = select(func.count()).select_from(Notification).where(
        Notification.user_id == current_user.id,
    )
    if unread_only:
        count_query = count_query.where(Notification.is_read == False)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.offset((page - 1) * limit).limit(limit))
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": str(n.id),
                "type": n.type.value if hasattr(n.type, "value") else str(n.type),
                "title": n.title,
                "message": n.message,
                "project_id": str(n.project_id) if n.project_id else None,
                "job_id": str(n.job_id) if n.job_id else None,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    count = (await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )).scalar() or 0
    return {"count": count}


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == str(notification_id),
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    notifs = result.scalars().all()
    now = datetime.now(timezone.utc)
    for n in notifs:
        n.is_read = True
        n.read_at = now
    await db.commit()
    return {"ok": True, "count": len(notifs)}
