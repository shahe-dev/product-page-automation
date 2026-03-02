"""
Database configuration and connection management.

Provides async SQLAlchemy engine, session factory, and FastAPI dependencies.
"""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


# NOTE: The canonical Base is defined in app.models.database.
# Import it lazily in initialize_database() to avoid circular imports.
# Do NOT define a separate Base here -- it would have no models registered.


def create_database_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with connection pooling.

    Returns:
        AsyncEngine: Configured async database engine
    """
    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
    }

    # Use NullPool for testing/development with SQLite
    # For async engines, don't specify poolclass - SQLAlchemy will use AsyncAdaptedQueuePool
    if settings.DATABASE_URL.startswith("sqlite"):
        engine_kwargs["poolclass"] = NullPool
        logger.warning("Using SQLite with NullPool - not recommended for production")
    else:
        engine_kwargs.update({
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
            "pool_recycle": settings.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": True,  # Verify connections before using
            # Don't specify poolclass for async engine - it auto-selects AsyncAdaptedQueuePool
        })

    engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

    logger.info(
        "Database engine created",
        extra={
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
        }
    )

    return engine


# Global engine and session factory
engine: AsyncEngine = create_database_engine()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.

    NOTE: This auto-commits on success. Read-only operations will trigger an
    empty commit. Route handlers that need multi-step transactions should use
    session.begin_nested() for savepoints.

    Yields:
        AsyncSession: Database session for the request

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session outside of FastAPI routes.

    Yields:
        AsyncSession: Database session

    Example:
        async with get_db_context() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """
    Health check for database connection.

    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            logger.info("Database connection check: OK")
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def initialize_database() -> None:
    """
    Initialize database schema.

    Creates all tables defined in Base metadata.
    Use Alembic migrations in production instead.
    """
    try:
        # Import from models to get the Base with all registered models
        from app.models.database import Base as ModelsBase
        async with engine.begin() as conn:
            await conn.run_sync(ModelsBase.metadata.create_all)
            logger.info("Database schema initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_database() -> None:
    """
    Close database connections and dispose of the engine.

    Call this during application shutdown.
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


async def get_connection_pool_status() -> dict:
    """
    Get current connection pool status for monitoring.

    Returns:
        dict: Pool statistics including size, checked out connections, etc.
    """
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_size": settings.DATABASE_POOL_SIZE,
    }
