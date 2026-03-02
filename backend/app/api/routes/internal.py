"""
Internal API endpoints.

These endpoints are called by Cloud Tasks and other internal services.
They require internal API key authentication, not user JWT.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.config.settings import get_settings
from app.services.job_manager import JobManager
from app.services.material_package_service import MaterialPackageService
from app.services.storage_service import StorageService
from app.repositories.job_repository import JobRepository
from app.repositories.material_package_repository import MaterialPackageRepository
from app.background.task_queue import TaskQueue
from app.models.enums import JobStatus, JobType

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/internal", tags=["internal"])


class ProcessJobRequest(BaseModel):
    """Request payload from Cloud Tasks."""
    job_id: UUID
    pdf_path: str
    retry_count: Optional[int] = 0


async def verify_internal_auth(
    x_internal_auth: str = Header(..., alias="X-Internal-Auth")
) -> bool:
    """
    Verify internal API authentication.

    Args:
        x_internal_auth: Internal API key from header

    Returns:
        True if valid

    Raises:
        HTTPException: If authentication fails
    """
    expected_key = settings.INTERNAL_API_KEY

    if x_internal_auth != expected_key:
        logger.warning(
            "Invalid internal API key",
            extra={"provided_key_prefix": x_internal_auth[:8] + "..." if len(x_internal_auth) > 8 else "***"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key"
        )

    return True


def get_job_manager(db: AsyncSession = Depends(get_db_session)) -> JobManager:
    """Dependency to get job manager instance."""
    job_repo = JobRepository(db)
    task_queue = TaskQueue()
    job_manager = JobManager(job_repo, task_queue)

    # Inject MaterialPackageService for materialize step
    storage = StorageService()
    material_repo = MaterialPackageRepository(db)
    job_manager._material_package_service = MaterialPackageService(storage, material_repo)

    return job_manager


@router.post("/process-job")
async def process_job(
    request: ProcessJobRequest,
    _auth: bool = Depends(verify_internal_auth),
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    Process a job - callback endpoint for Cloud Tasks.

    This endpoint is called by Cloud Tasks when a job should be processed.
    It triggers the actual job processing pipeline.

    Args:
        request: Job processing request with job_id and pdf_path

    Returns:
        Processing result
    """
    job_id = request.job_id

    logger.info(
        f"Received process-job callback for job {job_id}",
        extra={
            "job_id": str(job_id),
            "pdf_path": request.pdf_path,
            "retry_count": request.retry_count
        }
    )

    try:
        # Get current job status
        job = await job_manager.get_job(job_id)

        if not job:
            logger.error(f"Job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        # Check if job can be processed
        if job.status == JobStatus.CANCELLED:
            logger.info(f"Job {job_id} was cancelled, skipping processing")
            return {"status": "skipped", "reason": "job_cancelled"}

        if job.status == JobStatus.COMPLETED:
            logger.info(f"Job {job_id} already completed")
            return {"status": "skipped", "reason": "already_completed"}

        if job.status == JobStatus.FAILED:
            logger.info(f"Job {job_id} already failed")
            return {"status": "skipped", "reason": "already_failed"}

        # Start processing
        logger.info(f"Starting processing for job {job_id}")

        # Update job status to processing
        await job_manager.update_job_status(
            job_id=job_id,
            status=JobStatus.PROCESSING,
            progress=0,
            current_step="Starting processing"
        )

        # Execute the appropriate pipeline based on job type
        # EXTRACTION jobs run steps 1-10 + materialize, producing a MaterialPackage
        # GENERATION jobs run steps 11-14, consuming a MaterialPackage

        try:
            if job.job_type == JobType.EXTRACTION:
                result = await job_manager.execute_extraction_pipeline(
                    job_id=job_id,
                    pdf_path=request.pdf_path
                )
            elif job.job_type == JobType.GENERATION:
                result = await job_manager.execute_generation_pipeline(job_id=job_id)
            else:
                # Legacy FULL type or unknown - use legacy pipeline
                result = await job_manager.execute_processing_pipeline(
                    job_id=job_id,
                    pdf_path=request.pdf_path
                )

            logger.info(
                f"Job {job_id} completed successfully",
                extra={"job_id": str(job_id), "result": result}
            )

            return {
                "status": "completed",
                "job_id": str(job_id),
                "result": result
            }

        except Exception as processing_error:
            logger.error(
                f"Job {job_id} processing failed: {processing_error}",
                extra={"job_id": str(job_id), "error": str(processing_error)}
            )

            # Update job status to failed
            await job_manager.update_job_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                error_message=str(processing_error)
            )

            # Return 200 to prevent Cloud Tasks retry
            # (retries are handled by our own logic)
            return {
                "status": "failed",
                "job_id": str(job_id),
                "error": str(processing_error)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Unexpected error processing job {job_id}: {e}",
            extra={"job_id": str(job_id), "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.get("/health")
async def internal_health(
    _auth: bool = Depends(verify_internal_auth),
):
    """
    Internal health check endpoint.

    Used by Cloud Tasks to verify the service is reachable.
    Requires internal API key authentication (P3-3).
    """
    return {"status": "ok", "service": "pdp-automation-internal"}
