"""Service for creating and managing in-app notifications."""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Notification, User
from app.models.enums import NotificationType

logger = logging.getLogger(__name__)


class NotificationService:
    async def create(
        self,
        db: AsyncSession,
        user_id: UUID,
        type: NotificationType,
        title: str,
        message: str,
        project_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            project_id=project_id,
            job_id=job_id,
        )
        db.add(notif)
        return notif

    async def notify_all_users(
        self,
        db: AsyncSession,
        type: NotificationType,
        title: str,
        message: str,
        project_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
        exclude_user_id: Optional[UUID] = None,
    ) -> int:
        result = await db.execute(
            select(User.id).where(User.is_active == True)
        )
        user_ids = result.scalars().all()

        count = 0
        for uid in user_ids:
            if exclude_user_id and str(uid) == str(exclude_user_id):
                continue
            await self.create(db, uid, type, title, message, project_id, job_id)
            count += 1
        return count


notification_service = NotificationService()
