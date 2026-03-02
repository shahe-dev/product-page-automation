"""
Pytest configuration for PDP Automation v.3 backend tests.

Provides fixtures for:
- Async SQLite in-memory test database
- FastAPI test client with dependency overrides
- Test user creation with authentication
- JWT token generation for authenticated requests
"""

from datetime import datetime, timezone
from typing import AsyncGenerator, Dict
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import Depends
from httpx import AsyncClient, ASGITransport
import sqlalchemy as sa
from sqlalchemy import CheckConstraint, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create async SQLite in-memory engine for testing.

    Uses StaticPool to share a single connection across all operations,
    which is required for SQLite in-memory databases (otherwise each
    connection gets a separate empty database).
    """
    # Defer imports to avoid settings validation errors
    from app.models.database import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    def create_tables_sqlite_compat(connection):
        """Create tables with SQLite compatibility by removing PostgreSQL-specific features."""
        from sqlalchemy import Table, Column, Index
        from sqlalchemy.dialects import sqlite

        # Remove PostgreSQL-specific features for each table
        for table_name, table in list(Base.metadata.tables.items()):
            # Remove CHECK constraints (PostgreSQL regex, etc.)
            table.constraints = {c for c in table.constraints if not isinstance(c, CheckConstraint)}

            # Remove PostgreSQL-specific indexes (full-text search, gin, etc.)
            # Keep the indexes list but filter out functional/expression indexes
            filtered_indexes = []
            for idx in list(table.indexes):
                # Skip indexes with expressions (functional indexes using to_tsvector, etc.)
                # Check if any expression contains a function call
                skip_index = False
                for expr in idx.expressions:
                    # If the expression is not a simple column reference, skip it
                    if not hasattr(expr, 'name') or hasattr(expr, 'type'):
                        # This is a functional/expression index, not a simple column index
                        expr_str = str(expr)
                        if 'to_tsvector' in expr_str or 'func.' in expr_str or '(' in expr_str:
                            skip_index = True
                            break
                if not skip_index:
                    filtered_indexes.append(idx)
            table.indexes = set(filtered_indexes)

            # Fix columns for SQLite compatibility
            for column in table.columns:
                if column.server_default is not None:
                    column.server_default = None

                # Replace PostgreSQL types with SQLite equivalents
                if hasattr(column.type, '__visit_name__'):
                    if column.type.__visit_name__ == 'UUID':
                        column.type = sqlite.VARCHAR(36)
                        # Add Python-side default for UUID primary keys
                        if column.primary_key and column.default is None:
                            column.default = sa.ColumnDefault(lambda: str(uuid4()))
                    elif column.type.__visit_name__ == 'JSONB':
                        column.type = sqlite.JSON()
                    elif column.type.__visit_name__ == 'INET':
                        column.type = sqlite.VARCHAR(45)

        # Create all tables
        Base.metadata.create_all(bind=connection)

    # Create all tables with SQLite compatibility
    async with engine.begin() as conn:
        await conn.run_sync(create_tables_sqlite_compat)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create async test database session.

    Each test gets a fresh session with automatic rollback.
    """
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create FastAPI async test client with database override.

    Overrides:
    - get_db_session: uses test database
    - get_current_user: fixes UUID/VARCHAR mismatch in SQLite by
      querying users by email instead of UUID
    """
    from app.main import app
    from app.config.database import get_db_session
    from app.middleware.auth import get_current_user, security
    from app.middleware.rate_limit import RateLimitMiddleware

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    async def override_get_current_user(
        credentials=Depends(security),
    ):
        """
        Test-compatible auth that handles SQLite VARCHAR(36) for UUID columns.
        Decodes JWT, extracts email, queries by email (string comparison works).
        """
        from app.services.auth_service import auth_service, AuthenticationError
        from app.models.database import User
        from sqlalchemy import select
        from fastapi import HTTPException, status

        token = credentials.credentials
        try:
            payload = auth_service.verify_token(token)
        except AuthenticationError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")

        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")

        stmt = select(User).where(User.email == email)
        result = await test_db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER_NOT_FOUND")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ACCOUNT_INACTIVE")
        return user

    # Disable rate limiter for tests
    for middleware in app.user_middleware:
        if middleware.cls is RateLimitMiddleware:
            app.user_middleware.remove(middleware)
            break

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(test_db: AsyncSession):
    """
    Create a test user in the database.

    Returns:
        User model instance with USER role
    """
    # Defer imports
    from app.models.database import User
    from app.models.enums import UserRole

    now = datetime.now(timezone.utc)
    user = User(
        google_id="test_google_id_123",
        email="testuser@your-domain.com",
        name="Test User",
        picture_url="https://example.com/picture.jpg",
        role=UserRole.USER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(test_db: AsyncSession):
    """
    Create an admin test user in the database.

    Returns:
        User model instance with ADMIN role
    """
    # Defer imports
    from app.models.database import User
    from app.models.enums import UserRole

    now = datetime.now(timezone.utc)
    user = User(
        google_id="admin_google_id_456",
        email="admin@your-domain.com",
        name="Admin User",
        picture_url="https://example.com/admin.jpg",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def manager_user(test_db: AsyncSession):
    """
    Create a manager test user in the database.

    Returns:
        User model instance with MANAGER role
    """
    # Defer imports
    from app.models.database import User
    from app.models.enums import UserRole

    now = datetime.now(timezone.utc)
    user = User(
        google_id="manager_google_id_789",
        email="manager@your-domain.com",
        name="Manager User",
        picture_url="https://example.com/manager.jpg",
        role=UserRole.MANAGER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
def auth_headers(test_user) -> Dict[str, str]:
    """
    Generate JWT authentication headers for test user.

    Creates a valid JWT token using the same signing logic as the application.

    Args:
        test_user: Test user to generate token for

    Returns:
        Dict with Authorization header containing Bearer token
    """
    # Defer import
    from app.services.auth_service import auth_service

    token = auth_service.create_access_token(test_user)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
def admin_headers(admin_user) -> Dict[str, str]:
    """
    Generate JWT authentication headers for admin user.

    Args:
        admin_user: Admin user to generate token for

    Returns:
        Dict with Authorization header containing Bearer token
    """
    # Defer import
    from app.services.auth_service import auth_service

    token = auth_service.create_access_token(admin_user)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
def manager_headers(manager_user) -> Dict[str, str]:
    """
    Generate JWT authentication headers for manager user.

    Args:
        manager_user: Manager user to generate token for

    Returns:
        Dict with Authorization header containing Bearer token
    """
    # Defer import
    from app.services.auth_service import auth_service

    token = auth_service.create_access_token(manager_user)
    return {"Authorization": f"Bearer {token}"}
