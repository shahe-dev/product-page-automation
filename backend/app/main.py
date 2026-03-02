"""
FastAPI application entry point for PDP Automation v.3

Initializes the application with configuration, database, and middleware.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import (
    get_settings,
    setup_logging,
    check_database_connection,
    close_database,
)

# Initialize settings
settings = get_settings()

# Setup logging
setup_logging(
    level=settings.LOG_LEVEL,
    environment=settings.ENVIRONMENT,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info(f"Starting PDP Automation v.3 in {settings.ENVIRONMENT} mode")

    # Check database connection
    db_connected = await check_database_connection()
    if not db_connected:
        logger.error("Database connection failed at startup")
        raise RuntimeError("Database connection failed")

    # Recover zombie jobs from previous crash
    await _recover_zombie_jobs()

    logger.info("Application startup complete")

    # Start background rate limit cleanup task
    from app.middleware.rate_limit import cleanup_rate_limits
    cleanup_task = asyncio.create_task(cleanup_rate_limits())

    # Start periodic stale job recovery scheduler
    from app.background.scheduler import start_scheduler, stop_scheduler
    await start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down application")
    cleanup_task.cancel()
    await stop_scheduler()
    await close_database()
    logger.info("Application shutdown complete")


async def _recover_zombie_jobs():
    """
    Mark any jobs stuck in PROCESSING state as FAILED on startup.

    This handles jobs that were interrupted by server crashes/restarts.
    """
    from app.config.database import async_session_factory
    from app.repositories.job_repository import JobRepository
    from app.models.enums import JobStatus

    try:
        async with async_session_factory() as db:
            job_repo = JobRepository(db)
            # Get all jobs in PROCESSING state (hours=0 means no time filter)
            stale_jobs = await job_repo.get_stale_jobs(hours=0)

            for job in stale_jobs:
                await job_repo.update_job_status(
                    job_id=job.id,
                    status=JobStatus.FAILED,
                    error_message="Job interrupted by server restart"
                )
                logger.warning(
                    f"Recovered zombie job {job.id}",
                    extra={"job_id": str(job.id), "previous_step": job.current_step}
                )

            if stale_jobs:
                logger.warning(
                    f"Recovered {len(stale_jobs)} zombie jobs from previous crash"
                )
    except Exception as e:
        logger.error(f"Failed to recover zombie jobs: {e}")


# Create FastAPI application
app = FastAPI(
    title="PDP Automation API",
    description="Production Documentation Platform Automation System",
    version="3.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)


# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Rate limiting middleware
from app.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)


# Global exception handler -- prevent stack traces from leaking in production
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch unhandled exceptions and return a safe error response."""
    if settings.DEBUG:
        # In development, re-raise so FastAPI's default handler shows the traceback
        raise exc
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred"},
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PDP Automation API v3",
        "environment": settings.ENVIRONMENT,
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Returns:
        JSON with health status
    """
    db_status = await check_database_connection()

    if db_status:
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "database": "connected",
                "environment": settings.ENVIRONMENT,
            }
        )
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "environment": settings.ENVIRONMENT,
            }
        )


@app.get("/config/info")
async def config_info():
    """
    Return non-sensitive configuration information.

    Only available in development/debug mode (P3-2).
    In production, this endpoint is unconditionally disabled.
    """
    if not settings.DEBUG:
        return JSONResponse(
            status_code=404,
            content={"detail": "Not found"}
        )

    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "api_prefix": settings.API_V1_PREFIX,
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "anthropic_model": settings.ANTHROPIC_MODEL,
        "features": {
            "registration": settings.ENABLE_REGISTRATION,
            "metrics": settings.ENABLE_METRICS,
            "audit_log": settings.ENABLE_AUDIT_LOG,
        },
    }


# Import and include routers
from app.api.routes import (
    activity,
    admin,
    auth,
    downloads,
    projects,
    jobs,
    notifications as notifications_routes,
    upload,
    content,
    qa,
    prompts,
    templates,
    workflow,
    internal,
    process,
)

# Include all API routers
app.include_router(activity.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(notifications_routes.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")
app.include_router(qa.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1")
app.include_router(internal.router, prefix="/api/v1")
app.include_router(process.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )
