"""Tests for notification endpoints."""

import pytest

from app.models.database import Notification
from app.models.enums import NotificationType


@pytest.mark.asyncio
async def test_list_notifications_empty(client, auth_headers):
    resp = await client.get("/api/v1/notifications", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_list_notifications(client, auth_headers, test_db, test_user):
    notif = Notification(
        user_id=test_user.id,
        type=NotificationType.INFO,
        title="Hello",
        message="World",
    )
    test_db.add(notif)
    await test_db.commit()

    resp = await client.get("/api/v1/notifications", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Hello"


@pytest.mark.asyncio
async def test_unread_count(client, auth_headers, test_db, test_user):
    for i in range(3):
        test_db.add(Notification(
            user_id=test_user.id,
            type=NotificationType.INFO,
            title=f"N{i}",
            message="msg",
        ))
    await test_db.commit()

    resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 3


@pytest.mark.asyncio
async def test_mark_as_read(client, auth_headers, test_db, test_user):
    notif = Notification(
        user_id=test_user.id,
        type=NotificationType.INFO,
        title="Read me",
        message="msg",
    )
    test_db.add(notif)
    await test_db.commit()
    await test_db.refresh(notif)

    resp = await client.put(
        f"/api/v1/notifications/{notif.id}/read",
        headers=auth_headers,
    )
    assert resp.status_code == 200

    resp2 = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert resp2.json()["count"] == 0


@pytest.mark.asyncio
async def test_mark_all_read(client, auth_headers, test_db, test_user):
    for i in range(3):
        test_db.add(Notification(
            user_id=test_user.id,
            type=NotificationType.INFO,
            title=f"N{i}",
            message="msg",
        ))
    await test_db.commit()

    resp = await client.put("/api/v1/notifications/read-all", headers=auth_headers)
    assert resp.status_code == 200

    resp2 = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert resp2.json()["count"] == 0
