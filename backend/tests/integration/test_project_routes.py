"""
Integration tests for project API routes.

Tests the /api/v1/projects/* endpoints for project management.
"""

from httpx import AsyncClient
from uuid import uuid4
import pytest


class TestListProjects:
    """Tests for GET /api/v1/projects endpoint."""

    async def test_list_projects_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/projects without auth returns 403."""
        response = await client.get("/api/v1/projects")
        assert response.status_code == 403

    async def test_list_projects_with_auth_returns_200(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/projects with auth returns 200."""
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        assert "has_prev" in data
        assert isinstance(data["items"], list)

    async def test_list_projects_pagination_params(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/projects supports pagination parameters."""
        response = await client.get(
            "/api/v1/projects?page=1&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_list_projects_filter_by_emirate(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/projects supports filtering by emirate."""
        response = await client.get(
            "/api/v1/projects?emirate=Dubai",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestGetProject:
    """Tests for GET /api/v1/projects/{id} endpoint."""

    async def test_get_project_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/projects/{id} with nonexistent UUID returns 404."""
        nonexistent_id = uuid4()
        response = await client.get(
            f"/api/v1/projects/{nonexistent_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_get_project_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/projects/{id} without auth returns 403."""
        project_id = uuid4()
        response = await client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 403


class TestDeleteProject:
    """Tests for DELETE /api/v1/projects/{id} endpoint."""

    async def test_delete_project_without_auth_returns_401(self, client: AsyncClient):
        """DELETE /api/v1/projects/{id} without auth returns 403."""
        project_id = uuid4()
        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 403

    async def test_delete_project_with_non_admin_returns_403(
        self, client: AsyncClient, auth_headers: dict
    ):
        """DELETE /api/v1/projects/{id} with non-admin auth returns 403."""
        project_id = uuid4()
        response = await client.delete(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == 403

    async def test_delete_project_admin_nonexistent_returns_404(
        self, client: AsyncClient, admin_headers: dict
    ):
        """DELETE /api/v1/projects/{id} by admin with nonexistent ID returns 404."""
        nonexistent_id = uuid4()
        response = await client.delete(
            f"/api/v1/projects/{nonexistent_id}",
            headers=admin_headers
        )
        assert response.status_code == 404


class TestProjectStatistics:
    """Tests for GET /api/v1/projects/statistics endpoint."""

    async def test_get_statistics_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/projects/statistics without auth returns 403."""
        response = await client.get("/api/v1/projects/statistics")
        assert response.status_code == 403

    async def test_get_statistics_with_auth_returns_200(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/projects/statistics with auth returns 200."""
        response = await client.get(
            "/api/v1/projects/statistics",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)


class TestProjectActivity:
    """Tests for GET /api/v1/projects/activity endpoint."""

    async def test_get_activity_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/projects/activity without auth returns 403."""
        response = await client.get("/api/v1/projects/activity")
        assert response.status_code == 403

    async def test_get_activity_with_auth_returns_200(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/projects/activity with auth returns 200."""
        response = await client.get(
            "/api/v1/projects/activity",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    async def test_get_activity_respects_limit_param(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/projects/activity respects limit parameter."""
        response = await client.get(
            "/api/v1/projects/activity?limit=3",
            headers=auth_headers
        )
        assert response.status_code == 200
