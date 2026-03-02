"""Tests for EmailAllowlist model and auth enforcement."""

import pytest
from sqlalchemy import select

from app.models.database import EmailAllowlist
from app.models.enums import UserRole


@pytest.mark.asyncio
async def test_create_allowlist_entry(test_db):
    """EmailAllowlist record can be created and queried."""
    entry = EmailAllowlist(
        email="newuser@your-domain.com",
        role=UserRole.USER,
        is_active=True,
    )
    test_db.add(entry)
    await test_db.commit()
    await test_db.refresh(entry)

    result = await test_db.execute(
        select(EmailAllowlist).where(EmailAllowlist.email == "newuser@your-domain.com")
    )
    fetched = result.scalar_one()
    assert fetched.email == "newuser@your-domain.com"
    assert fetched.role == UserRole.USER
    assert fetched.is_active is True


@pytest.mark.asyncio
async def test_allowlist_unique_email(test_db):
    """Duplicate emails are rejected."""
    entry1 = EmailAllowlist(email="dup@your-domain.com", role=UserRole.USER)
    test_db.add(entry1)
    await test_db.commit()

    entry2 = EmailAllowlist(email="dup@your-domain.com", role=UserRole.MANAGER)
    test_db.add(entry2)
    with pytest.raises(Exception):  # IntegrityError
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_allowlist_blocks_unlisted_user(test_db):
    """When allowlist has entries, unlisted emails are rejected."""
    from app.services.user_service import UserService

    # Add one entry to allowlist (makes it non-empty)
    entry = EmailAllowlist(email="allowed@your-domain.com", role=UserRole.USER)
    test_db.add(entry)
    await test_db.commit()

    svc = UserService()
    with pytest.raises(PermissionError, match="not authorized"):
        await svc.get_or_create_user(test_db, {
            "email": "blocked@your-domain.com",
            "google_id": "gid_blocked",
            "name": "Blocked User",
        })


@pytest.mark.asyncio
async def test_allowlist_assigns_role_from_list(test_db):
    """New user gets role from allowlist entry."""
    from app.services.user_service import UserService

    entry = EmailAllowlist(email="mgr@your-domain.com", role=UserRole.MANAGER)
    test_db.add(entry)
    await test_db.commit()

    svc = UserService()
    user = await svc.get_or_create_user(test_db, {
        "email": "mgr@your-domain.com",
        "google_id": "gid_mgr",
        "name": "Manager User",
    })
    assert user.role == UserRole.MANAGER


@pytest.mark.asyncio
async def test_allowlist_empty_allows_anyone(test_db):
    """When allowlist is empty (bootstrap), any @your-domain.com user can log in."""
    from app.services.user_service import UserService

    svc = UserService()
    user = await svc.get_or_create_user(test_db, {
        "email": "anyone@your-domain.com",
        "google_id": "gid_anyone",
        "name": "Anyone",
    })
    assert user is not None
    assert user.email == "anyone@your-domain.com"
