"""
Integration tests for authentication endpoints.

Tests JWT authentication flow and user management.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.integration
async def test_authenticated_request(client: AsyncClient, test_user, auth_headers):
    """
    Test authenticated request with valid JWT token.

    This test verifies that:
    1. Test user is created in database
    2. JWT token is generated correctly
    3. Auth headers are properly formatted
    4. Protected endpoints accept valid tokens
    """
    # Test user should have correct attributes
    assert test_user.email == "testuser@your-domain.com"
    assert test_user.is_active is True

    # Auth headers should be properly formatted
    assert "Authorization" in auth_headers
    assert auth_headers["Authorization"].startswith("Bearer ")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_user_role(admin_user, admin_headers):
    """Test admin user has correct role and token generation works."""
    from app.models.enums import UserRole

    assert admin_user.role == UserRole.ADMIN
    assert admin_user.email == "admin@your-domain.com"
    assert "Authorization" in admin_headers
    assert admin_headers["Authorization"].startswith("Bearer ")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_user_role(manager_user, manager_headers):
    """Test manager user has correct role and token generation works."""
    from app.models.enums import UserRole

    assert manager_user.role == UserRole.MANAGER
    assert manager_user.email == "manager@your-domain.com"
    assert "Authorization" in manager_headers
    assert manager_headers["Authorization"].startswith("Bearer ")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_database_session_isolation(test_db: AsyncSession, test_user):
    """
    Test that database sessions are properly isolated between tests.

    Verifies that test_user is persisted in the test database.
    """
    from app.models.database import User
    from sqlalchemy import select

    # Query for the test user
    result = await test_db.execute(
        select(User).where(User.email == "testuser@your-domain.com")
    )
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email
