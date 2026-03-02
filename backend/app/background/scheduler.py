"""
Background Scheduler for Periodic Tasks

Uses APScheduler to run periodic jobs like stale job recovery.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None

# Configuration
STALE_JOB_CHECK_MINUTES = 5  # Check every 5 minutes
STALE_JOB_THRESHOLD_HOURS = 1  # Mark jobs as failed after 1 hour


async def recover_stale_jobs() -> None:
    """
    Periodic task to mark jobs stuck in PROCESSING for too long as FAILED.

    This catches jobs that weren't recovered at startup (e.g., jobs that
    became stale while the server was running but the processing crashed).
    """
    from app.config.database import async_session_factory
    from app.repositories.job_repository import JobRepository
    from app.models.enums import JobStatus

    try:
        async with async_session_factory() as db:
            job_repo = JobRepository(db)
            stale_jobs = await job_repo.get_stale_jobs(hours=STALE_JOB_THRESHOLD_HOURS)

            for job in stale_jobs:
                await job_repo.update_job_status(
                    job_id=job.id,
                    status=JobStatus.FAILED,
                    error_message=f"Job timed out after {STALE_JOB_THRESHOLD_HOURS} hour(s)"
                )
                logger.warning(
                    f"Marked stale job {job.id} as failed",
                    extra={
                        "job_id": str(job.id),
                        "current_step": job.current_step,
                        "started_at": str(job.started_at)
                    }
                )

            if stale_jobs:
                logger.info(
                    f"Recovered {len(stale_jobs)} stale jobs",
                    extra={"count": len(stale_jobs)}
                )

    except Exception as e:
        logger.exception(
            f"Error in stale job recovery: {e}",
            extra={"error": str(e)}
        )


async def start_scheduler() -> None:
    """
    Start the background scheduler.

    Called during application startup in the lifespan handler.
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return

    _scheduler = AsyncIOScheduler()

    # Add stale job recovery task
    _scheduler.add_job(
        recover_stale_jobs,
        trigger=IntervalTrigger(minutes=STALE_JOB_CHECK_MINUTES),
        id="recover_stale_jobs",
        name="Recover stale jobs",
        replace_existing=True
    )

    _scheduler.start()
    logger.info(
        f"Background scheduler started (stale job check every {STALE_JOB_CHECK_MINUTES} minutes)"
    )


async def stop_scheduler() -> None:
    """
    Stop the background scheduler.

    Called during application shutdown in the lifespan handler.
    """
    global _scheduler

    if _scheduler is None:
        return

    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Background scheduler stopped")
