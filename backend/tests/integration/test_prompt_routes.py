"""
Integration tests for prompt API routes.

Tests the /api/v1/prompts/* endpoints for prompt management.
"""

from httpx import AsyncClient
from uuid import uuid4
import pytest


class TestListPrompts:
    """Tests for GET /api/v1/prompts endpoint."""

    async def test_list_prompts_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/prompts without auth returns 403."""
        response = await client.get("/api/v1/prompts")
        assert response.status_code == 403

    async def test_list_prompts_with_auth_returns_200(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/prompts with auth returns 200."""
        response = await client.get("/api/v1/prompts", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["items"], list)

    async def test_list_prompts_with_template_type_filter(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/prompts with template_type filter returns 200."""
        response = await client.get(
            "/api/v1/prompts?template_type=opr",
            headers=auth_headers
        )
        assert response.status_code == 200

    async def test_list_prompts_with_content_variant_filter(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/prompts with content_variant filter returns 200."""
        response = await client.get(
            "/api/v1/prompts?content_variant=standard",
            headers=auth_headers
        )
        assert response.status_code == 200

    async def test_list_prompts_pagination_params(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/prompts supports pagination parameters."""
        response = await client.get(
            "/api/v1/prompts?limit=10&offset=0",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0


class TestGetPrompt:
    """Tests for GET /api/v1/prompts/{id} endpoint."""

    async def test_get_prompt_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/prompts/{id} with nonexistent UUID returns 404."""
        nonexistent_id = uuid4()
        response = await client.get(
            f"/api/v1/prompts/{nonexistent_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_get_prompt_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/prompts/{id} without auth returns 403."""
        prompt_id = uuid4()
        response = await client.get(f"/api/v1/prompts/{prompt_id}")
        assert response.status_code == 403


class TestCreatePrompt:
    """Tests for POST /api/v1/prompts endpoint."""

    async def test_create_prompt_without_auth_returns_401(self, client: AsyncClient):
        """POST /api/v1/prompts without auth returns 403."""
        response = await client.post(
            "/api/v1/prompts",
            json={
                "name": "Test Prompt",
                "template_type": "opr",
                "content_variant": "standard",
                "content": "Test content"
            }
        )
        assert response.status_code == 403

    async def test_create_prompt_with_non_admin_returns_403(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/prompts with non-admin auth returns 403."""
        response = await client.post(
            "/api/v1/prompts",
            headers=auth_headers,
            json={
                "name": "Test Prompt",
                "template_type": "opr",
                "content_variant": "standard",
                "content": "Test content"
            }
        )
        assert response.status_code == 403

    @pytest.mark.skip(reason="Requires PostgreSQL server_default for timestamps; SQLite strips server_default")
    async def test_create_prompt_with_admin_and_valid_data_returns_201(
        self, client: AsyncClient, admin_headers: dict
    ):
        """POST /api/v1/prompts with admin auth and valid data returns 201."""
        response = await client.post(
            "/api/v1/prompts",
            headers=admin_headers,
            json={
                "name": "Test Prompt",
                "template_type": "opr",
                "content_variant": "standard",
                "content": "Test content for prompt"
            }
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Prompt"
        assert data["template_type"] == "opr"
        assert data["content_variant"] == "standard"
        assert data["content"] == "Test content for prompt"
        assert data["version"] == 1
        assert data["is_active"] is True

    async def test_create_prompt_with_invalid_template_type_returns_422(
        self, client: AsyncClient, admin_headers: dict
    ):
        """POST /api/v1/prompts with invalid template_type returns 422."""
        response = await client.post(
            "/api/v1/prompts",
            headers=admin_headers,
            json={
                "name": "Test Prompt",
                "template_type": "invalid_template",
                "content_variant": "standard",
                "content": "Test content"
            }
        )
        assert response.status_code == 422

    async def test_create_prompt_with_invalid_content_variant_returns_422(
        self, client: AsyncClient, admin_headers: dict
    ):
        """POST /api/v1/prompts with invalid content_variant returns 422."""
        response = await client.post(
            "/api/v1/prompts",
            headers=admin_headers,
            json={
                "name": "Test Prompt",
                "template_type": "opr",
                "content_variant": "invalid_variant",
                "content": "Test content"
            }
        )
        assert response.status_code == 422


class TestUpdatePrompt:
    """Tests for PUT /api/v1/prompts/{id} endpoint."""

    async def test_update_prompt_without_auth_returns_401(self, client: AsyncClient):
        """PUT /api/v1/prompts/{id} without auth returns 403."""
        prompt_id = uuid4()
        response = await client.put(
            f"/api/v1/prompts/{prompt_id}",
            json={"content": "Updated content"}
        )
        assert response.status_code == 403

    async def test_update_prompt_with_non_admin_returns_403(
        self, client: AsyncClient, auth_headers: dict
    ):
        """PUT /api/v1/prompts/{id} with non-admin auth returns 403."""
        prompt_id = uuid4()
        response = await client.put(
            f"/api/v1/prompts/{prompt_id}",
            headers=auth_headers,
            json={"content": "Updated content"}
        )
        assert response.status_code == 403

    async def test_update_prompt_nonexistent_returns_404(
        self, client: AsyncClient, admin_headers: dict
    ):
        """PUT /api/v1/prompts/{id} with nonexistent UUID returns 404."""
        nonexistent_id = uuid4()
        response = await client.put(
            f"/api/v1/prompts/{nonexistent_id}",
            headers=admin_headers,
            json={"content": "Updated content"}
        )
        assert response.status_code == 404


class TestGetPromptVersions:
    """Tests for GET /api/v1/prompts/{id}/versions endpoint."""

    async def test_get_prompt_versions_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/prompts/{id}/versions without auth returns 403."""
        prompt_id = uuid4()
        response = await client.get(f"/api/v1/prompts/{prompt_id}/versions")
        assert response.status_code == 403

    async def test_get_prompt_versions_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/prompts/{id}/versions with nonexistent UUID returns 404."""
        nonexistent_id = uuid4()
        response = await client.get(
            f"/api/v1/prompts/{nonexistent_id}/versions",
            headers=auth_headers
        )
        assert response.status_code == 404
