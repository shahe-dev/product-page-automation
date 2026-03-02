"""Tests for NotificationService."""

import pytest
from sqlalchemy import select

from app.models.database import Notification
from app.models.enums import NotificationType


@pytest.mark.asyncio
async def test_create_notification(test_db, test_user):
    """NotificationService.create() inserts a Notification record."""
    from app.services.notification_service import NotificationService

    svc = NotificationService()
    await svc.create(
        db=test_db,
        user_id=test_user.id,
        type=NotificationType.INFO,
        title="Test Title",
        message="Test message body",
    )
    await test_db.commit()

    result = await test_db.execute(
        select(Notification).where(Notification.user_id == test_user.id)
    )
    notif = result.scalar_one()
    assert notif.title == "Test Title"
    assert notif.is_read is False


@pytest.mark.asyncio
async def test_notify_all_users(test_db, test_user, admin_user):
    """notify_all_users creates one notification per active user."""
    from app.services.notification_service import NotificationService

    svc = NotificationService()
    await svc.notify_all_users(
        db=test_db,
        type=NotificationType.APPROVAL,
        title="Approval Needed",
        message="Project X submitted",
    )
    await test_db.commit()

    result = await test_db.execute(select(Notification))
    notifs = result.scalars().all()
    assert len(notifs) == 2  # test_user + admin_user
