"""
Integration tests for authentication API routes.

Tests the /api/v1/auth/* endpoints for authentication and user management.
These tests focus on endpoints that use JWT authentication (not OAuth flow).
"""

from httpx import AsyncClient
import pytest


class TestAuthMe:
    """Tests for GET /api/v1/auth/me endpoint."""

    async def test_get_me_without_auth_returns_403(self, client: AsyncClient):
        """GET /api/v1/auth/me without auth returns 403 (missing credentials)."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403

    async def test_get_me_with_invalid_token_returns_401(self, client: AsyncClient):
        """GET /api/v1/auth/me with invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    async def test_get_me_with_valid_auth_returns_user_info(
        self, client: AsyncClient, auth_headers: dict, test_user
    ):
        """GET /api/v1/auth/me with valid auth returns user info."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["role"] == test_user.role.value
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    async def test_get_me_returns_correct_role_for_admin(
        self, client: AsyncClient, admin_headers: dict, admin_user
    ):
        """GET /api/v1/auth/me returns correct role for admin user."""
        response = await client.get("/api/v1/auth/me", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == admin_user.email
        assert data["role"] == "admin"

    async def test_get_me_returns_correct_role_for_manager(
        self, client: AsyncClient, manager_headers: dict, manager_user
    ):
        """GET /api/v1/auth/me returns correct role for manager user."""
        response = await client.get("/api/v1/auth/me", headers=manager_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == manager_user.email
        assert data["role"] == "manager"


class TestAuthLogout:
    """Tests for POST /api/v1/auth/logout endpoint."""

    async def test_logout_without_auth_returns_403(self, client: AsyncClient):
        """POST /api/v1/auth/logout without auth returns 403 (missing credentials)."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 403

    async def test_logout_with_valid_auth_returns_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/auth/logout with valid auth returns success."""
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "message" in data


class TestAuthLogoutAll:
    """Tests for POST /api/v1/auth/logout/all endpoint."""

    async def test_logout_all_without_auth_returns_403(self, client: AsyncClient):
        """POST /api/v1/auth/logout/all without auth returns 403 (missing credentials)."""
        response = await client.post("/api/v1/auth/logout/all")
        assert response.status_code == 403

    async def test_logout_all_with_valid_auth_returns_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/auth/logout/all with valid auth returns success."""
        response = await client.post("/api/v1/auth/logout/all", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "tokens_revoked" in data
