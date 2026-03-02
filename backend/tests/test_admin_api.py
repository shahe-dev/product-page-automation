"""Tests for admin API endpoints (allowlist CRUD, stats, user management)."""

import pytest

from app.models.database import EmailAllowlist, Project
from app.models.enums import UserRole, WorkflowStatus


# =====================================================================
# ALLOWLIST CRUD
# =====================================================================


@pytest.mark.asyncio
async def test_list_allowlist_empty(client, admin_headers):
    """GET /admin/allowlist returns empty list initially."""
    resp = await client.get("/api/v1/admin/allowlist", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_allowlist_requires_admin(client, auth_headers):
    """GET /admin/allowlist returns 403 for non-admin users."""
    resp = await client.get("/api/v1/admin/allowlist", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_add_allowlist_entry(client, admin_headers):
    """POST /admin/allowlist creates a new entry."""
    resp = await client.post(
        "/api/v1/admin/allowlist",
        json={"email": "newuser@your-domain.com", "role": "user"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@your-domain.com"
    assert data["role"] == "user"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_add_allowlist_duplicate(client, admin_headers):
    """POST /admin/allowlist rejects duplicate email."""
    await client.post(
        "/api/v1/admin/allowlist",
        json={"email": "dup@your-domain.com", "role": "user"},
        headers=admin_headers,
    )
    resp = await client.post(
        "/api/v1/admin/allowlist",
        json={"email": "dup@your-domain.com", "role": "manager"},
        headers=admin_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_allowlist_entry(client, admin_headers, test_db):
    """PUT /admin/allowlist/{id} updates role."""
    entry = EmailAllowlist(email="update@your-domain.com", role=UserRole.USER)
    test_db.add(entry)
    await test_db.commit()
    await test_db.refresh(entry)

    resp = await client.put(
        f"/api/v1/admin/allowlist/{entry.id}",
        json={"role": "manager"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "manager"


@pytest.mark.asyncio
async def test_delete_allowlist_entry(client, admin_headers, test_db):
    """DELETE /admin/allowlist/{id} soft-deletes entry."""
    entry = EmailAllowlist(email="delete@your-domain.com", role=UserRole.USER)
    test_db.add(entry)
    await test_db.commit()
    await test_db.refresh(entry)

    resp = await client.delete(
        f"/api/v1/admin/allowlist/{entry.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 204

    await test_db.refresh(entry)
    assert entry.is_active is False


# =====================================================================
# ADMIN STATS
# =====================================================================


@pytest.mark.asyncio
async def test_admin_stats(client, admin_headers):
    """GET /admin/stats returns system stats."""
    resp = await client.get("/api/v1/admin/stats", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "user_count" in data
    assert "active_jobs" in data
    assert "failed_jobs_24h" in data
    assert "total_projects" in data
    assert "projects_by_status" in data


# =====================================================================
# USER MANAGEMENT
# =====================================================================


@pytest.mark.asyncio
async def test_admin_list_users(client, admin_headers, admin_user):
    """GET /admin/users returns list of users."""
    resp = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["email"] == admin_user.email


@pytest.mark.asyncio
async def test_admin_update_user_role(client, admin_headers, test_user):
    """PUT /admin/users/{id}/role changes user role."""
    resp = await client.put(
        f"/api/v1/admin/users/{test_user.id}/role",
        json={"role": "manager"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "manager"


# =====================================================================
# ROLE ENFORCEMENT
# =====================================================================


@pytest.mark.asyncio
async def test_delete_project_requires_admin(client, auth_headers, test_db, test_user):
    """DELETE /projects/{id} returns 403 for non-admin users."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    project = Project(
        name="Test Project",
        workflow_status=WorkflowStatus.DRAFT,
        created_by=test_user.id,
        property_types=[],
        unit_sizes=[],
        amenities=[],
        features=[],
        custom_fields={},
        generated_content={},
        created_at=now,
        updated_at=now,
    )
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)

    resp = await client.delete(
        f"/api/v1/projects/{project.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 403
