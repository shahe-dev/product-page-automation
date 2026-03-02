"""
Integration tests for job API routes.

Tests the /api/v1/jobs/* endpoints for job management.
"""

from httpx import AsyncClient
from uuid import uuid4
import pytest


class TestListJobs:
    """Tests for GET /api/v1/jobs endpoint."""

    async def test_list_jobs_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/jobs without auth returns 403."""
        response = await client.get("/api/v1/jobs")
        assert response.status_code == 403

    async def test_list_jobs_with_auth_returns_200(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/jobs with auth returns 200."""
        response = await client.get("/api/v1/jobs", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["jobs"], list)

    async def test_list_jobs_with_status_filter(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/jobs with status filter returns 200."""
        response = await client.get(
            "/api/v1/jobs?status_filter=pending",
            headers=auth_headers
        )
        assert response.status_code == 200

    async def test_list_jobs_with_invalid_status_returns_400(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/jobs with invalid status filter returns 400."""
        response = await client.get(
            "/api/v1/jobs?status_filter=invalid_status",
            headers=auth_headers
        )
        assert response.status_code == 400

    async def test_list_jobs_pagination_params(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/jobs supports pagination parameters."""
        response = await client.get(
            "/api/v1/jobs?limit=10&offset=0",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0


class TestGetJob:
    """Tests for GET /api/v1/jobs/{id} endpoint."""

    async def test_get_job_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/jobs/{id} with nonexistent UUID returns 404."""
        nonexistent_id = uuid4()
        response = await client.get(
            f"/api/v1/jobs/{nonexistent_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_get_job_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/jobs/{id} without auth returns 403."""
        job_id = uuid4()
        response = await client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 403


class TestGetJobStatus:
    """Tests for GET /api/v1/jobs/{id}/status endpoint."""

    async def test_get_job_status_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/jobs/{id}/status with nonexistent UUID returns 404."""
        nonexistent_id = uuid4()
        response = await client.get(
            f"/api/v1/jobs/{nonexistent_id}/status",
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_get_job_status_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/jobs/{id}/status without auth returns 403."""
        job_id = uuid4()
        response = await client.get(f"/api/v1/jobs/{job_id}/status")
        assert response.status_code == 403


class TestGetJobSteps:
    """Tests for GET /api/v1/jobs/{id}/steps endpoint."""

    async def test_get_job_steps_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/jobs/{id}/steps with nonexistent UUID returns 404."""
        nonexistent_id = uuid4()
        response = await client.get(
            f"/api/v1/jobs/{nonexistent_id}/steps",
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_get_job_steps_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/jobs/{id}/steps without auth returns 403."""
        job_id = uuid4()
        response = await client.get(f"/api/v1/jobs/{job_id}/steps")
        assert response.status_code == 403


class TestCreateJob:
    """Tests for POST /api/v1/jobs endpoint."""

    async def test_create_job_without_auth_returns_401(self, client: AsyncClient):
        """POST /api/v1/jobs without auth returns 403."""
        response = await client.post(
            "/api/v1/jobs",
            json={"template_type": "opr"}
        )
        assert response.status_code == 403

    @pytest.mark.skip(reason="Requires PostgreSQL server_default for timestamps; SQLite strips server_default")
    async def test_create_job_with_valid_template_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/jobs with valid template type returns 201."""
        response = await client.post(
            "/api/v1/jobs",
            headers=auth_headers,
            json={"template_type": "opr"}
        )
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["template_type"] == "opr"
        assert data["status"] == "pending"

    async def test_create_job_with_invalid_template_type_returns_400(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/jobs with invalid template type returns 400."""
        response = await client.post(
            "/api/v1/jobs",
            headers=auth_headers,
            json={"template_type": "invalid_template"}
        )
        assert response.status_code == 400


class TestCancelJob:
    """Tests for POST /api/v1/jobs/{id}/cancel endpoint."""

    async def test_cancel_job_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/jobs/{id}/cancel with nonexistent UUID returns 404."""
        nonexistent_id = uuid4()
        response = await client.post(
            f"/api/v1/jobs/{nonexistent_id}/cancel",
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_cancel_job_without_auth_returns_401(self, client: AsyncClient):
        """POST /api/v1/jobs/{id}/cancel without auth returns 403."""
        job_id = uuid4()
        response = await client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert response.status_code == 403
