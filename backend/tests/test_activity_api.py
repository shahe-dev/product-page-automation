"""Tests for activity feed endpoints."""

import pytest


@pytest.mark.asyncio
async def test_activity_feed_empty(client, auth_headers):
    resp = await client.get("/api/v1/activity/feed", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["items"] == []


@pytest.mark.asyncio
async def test_activity_feed_includes_approvals(client, auth_headers, test_db, test_user):
    from datetime import datetime, timezone

    from app.models.database import Project, ProjectApproval
    from app.models.enums import ApprovalAction, WorkflowStatus

    now = datetime.now(timezone.utc)
    project = Project(
        name="Feed Test",
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

    approval = ProjectApproval(
        project_id=project.id,
        action=ApprovalAction.SUBMITTED,
        approver_id=test_user.id,
        comments=None,
        created_at=now,
    )
    test_db.add(approval)
    await test_db.commit()

    resp = await client.get("/api/v1/activity/feed", headers=auth_headers)
    data = resp.json()
    assert len(data["items"]) >= 1
    assert data["items"][0]["type"] == "approval_submitted"


@pytest.mark.asyncio
async def test_team_stats(client, auth_headers):
    resp = await client.get("/api/v1/activity/team-stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
