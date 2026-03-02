"""
Integration tests for health and basic endpoints.

Tests basic application setup and health checks.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns success."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "PDP Automation API" in data["message"]
    assert "status" in data
    assert data["status"] == "operational"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint returns service unavailable with SQLite test DB."""
    response = await client.get("/health")

    # Health check requires real PostgreSQL connection
    # SQLite test DB returns 503 (service unavailable)
    assert response.status_code == 503
