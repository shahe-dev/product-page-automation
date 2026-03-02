"""
Job API Routes

Provides REST API endpoints for job management:
- Create new jobs
- List user's jobs
- Get job details and status
- Get job processing steps
- Cancel jobs
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.models.database import Job, JobStep, User
from app.models.enums import JobStatus, JobStepStatus
from app.services.job_manager import JobManager
from app.repositories.job_repository import JobRepository
from app.background.task_queue import TaskQueue
from app.api.dependencies import get_current_user, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


# =====================================================================
# REQUEST/RESPONSE MODELS
# =====================================================================


class CreateJobRequest(BaseModel):
    """Request to create a new job."""
    template_type: str = Field(
        ...,
        description="Template type (opr, mpp, aggregators, etc.)"
    )
    template_id: Optional[UUID] = Field(
        None,
        description="Optional template UUID"
    )
    processing_config: Optional[dict] = Field(
        None,
        description="Optional processing configuration"
    )


class JobResponse(BaseModel):
    """Job details response."""
    id: UUID
    user_id: UUID
    template_type: str
    template_id: Optional[UUID]
    job_type: Optional[str] = None
    material_package_id: Optional[UUID] = None
    project_id: Optional[str] = None
    status: str
    progress: int
    current_step: Optional[str]
    progress_message: Optional[str]  # Granular substep detail
    result: Optional[dict]
    error_message: Optional[str]
    retry_count: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]

    class Config:
        from_attributes = True

    @classmethod
    def from_job(cls, job: Job) -> "JobResponse":
        """Convert Job model to response."""
        # Extract project_id from JSONB columns (avoids lazy-loading relationships
        # which would crash on async sessions with MissingGreenlet).
        project_id = None
        if job.result and isinstance(job.result, dict):
            project_id = job.result.get("project_id")
        if not project_id and job.processing_config and isinstance(job.processing_config, dict):
            project_id = job.processing_config.get("project_id")

        return cls(
            id=job.id,
            user_id=job.user_id,
            template_type=job.template_type.value,
            template_id=job.template_id,
            job_type=job.job_type.value if job.job_type else None,
            material_package_id=job.material_package_id,
            project_id=project_id,
            status=job.status.value,
            progress=job.progress,
            current_step=job.current_step,
            progress_message=job.progress_message,
            result=job.result,
            error_message=job.error_message,
            retry_count=job.retry_count,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None
        )


class JobStepResponse(BaseModel):
    """Job step response."""
    id: UUID
    step_id: str
    label: str
    status: str
    result: Optional[dict]
    error_message: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_step(cls, step: JobStep) -> "JobStepResponse":
        """Convert JobStep model to response."""
        return cls(
            id=step.id,
            step_id=step.step_id,
            label=step.label,
            status=step.status.value,
            result=step.result,
            error_message=step.error_message,
            started_at=step.started_at.isoformat() if step.started_at else None,
            completed_at=step.completed_at.isoformat() if step.completed_at else None,
            created_at=step.created_at.isoformat()
        )


class JobStatusResponse(BaseModel):
    """Simplified job status response for polling."""
    id: UUID
    status: str
    progress: int
    current_step: Optional[str]
    error_message: Optional[str]

    @classmethod
    def from_job(cls, job: Job) -> "JobStatusResponse":
        """Convert Job model to status response."""
        return cls(
            id=job.id,
            status=job.status.value,
            progress=job.progress,
            current_step=job.current_step,
            error_message=job.error_message
        )


class JobListResponse(BaseModel):
    """Response for job list."""
    jobs: List[JobResponse]
    total: int
    limit: int
    offset: int


# =====================================================================
# DEPENDENCIES
# =====================================================================


async def get_job_manager(db = Depends(get_db)) -> JobManager:
    """
    Dependency to get JobManager instance.

    Args:
        db: Database session

    Returns:
        JobManager instance
    """
    job_repo = JobRepository(db)
    task_queue = TaskQueue()
    return JobManager(job_repo, task_queue)


async def get_job_or_404(
    job_id: UUID,
    job_manager: JobManager = Depends(get_job_manager),
    current_user: User = Depends(get_current_user)
) -> Job:
    """
    Get job by ID or raise 404.

    Args:
        job_id: Job UUID
        job_manager: JobManager instance
        current_user: Current authenticated user

    Returns:
        Job instance

    Raises:
        HTTPException: If job not found or unauthorized
    """
    job = await job_manager.get_job_status(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Check authorization (user can only access their own jobs unless admin)
    if job.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this job"
        )

    return job


# =====================================================================
# ROUTES
# =====================================================================


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new job"
)
async def create_job(
    request: CreateJobRequest,
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
) -> JobResponse:
    """
    Create a new processing job.

    This endpoint creates a job record but does NOT start processing.
    Call the upload endpoint to upload a PDF and start processing.

    Returns:
        Created job details
    """
    try:
        job = await job_manager.create_job(
            user_id=current_user.id,
            template_type=request.template_type,
            template_id=request.template_id,
            processing_config=request.processing_config
        )

        logger.info(
            f"Job {job.id} created by user {current_user.id}",
            extra={"job_id": str(job.id), "user_id": str(current_user.id)}
        )

        return JobResponse.from_job(job)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(
            f"Error creating job for user {current_user.id}",
            extra={"user_id": str(current_user.id), "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )


@router.get(
    "",
    response_model=JobListResponse,
    summary="List user's jobs"
)
async def list_jobs(
    status_filter: Optional[str] = Query(
        None,
        description="Filter by status (pending, processing, completed, failed, cancelled)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
) -> JobListResponse:
    """
    List jobs for the current user.

    Supports filtering by status and pagination.

    Returns:
        List of jobs with pagination metadata
    """
    try:
        # Parse status filter
        job_status = None
        if status_filter:
            try:
                job_status = JobStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}"
                )

        # Get jobs and total count
        jobs = await job_manager.get_user_jobs(
            user_id=current_user.id,
            status=job_status,
            limit=limit,
            offset=offset
        )
        total = await job_manager.count_user_jobs(
            user_id=current_user.id,
            status=job_status
        )

        # Convert to response
        job_responses = [JobResponse.from_job(job) for job in jobs]

        return JobListResponse(
            jobs=job_responses,
            total=total,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Error listing jobs for user {current_user.id}",
            extra={"user_id": str(current_user.id), "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs"
        )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details"
)
async def get_job(
    job: Job = Depends(get_job_or_404)
) -> JobResponse:
    """
    Get detailed information about a specific job.

    Requires:
        - User must own the job or be an admin

    Returns:
        Job details including status, progress, and results
    """
    return JobResponse.from_job(job)


@router.get(
    "/{job_id}/status",
    response_model=JobStatusResponse,
    summary="Get job status"
)
async def get_job_status(
    job: Job = Depends(get_job_or_404)
) -> JobStatusResponse:
    """
    Get simplified job status for polling.

    This endpoint is optimized for frequent polling by returning
    only essential status information.

    Returns:
        Job status and progress
    """
    return JobStatusResponse.from_job(job)


@router.get(
    "/{job_id}/steps",
    response_model=List[JobStepResponse],
    summary="Get job steps"
)
async def get_job_steps(
    job: Job = Depends(get_job_or_404),
    job_manager: JobManager = Depends(get_job_manager)
) -> List[JobStepResponse]:
    """
    Get detailed information about all processing steps for a job.

    Returns timing, status, and error information for each step.

    Returns:
        List of job steps with timing information
    """
    try:
        steps = await job_manager.get_job_steps(job.id)
        return [JobStepResponse.from_step(step) for step in steps]

    except Exception as e:
        logger.exception(
            f"Error getting steps for job {job.id}",
            extra={"job_id": str(job.id), "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job steps"
        )


@router.post(
    "/{job_id}/cancel",
    response_model=JobResponse,
    summary="Cancel job"
)
async def cancel_job(
    job: Job = Depends(get_job_or_404),
    job_manager: JobManager = Depends(get_job_manager)
) -> JobResponse:
    """
    Cancel a pending or processing job.

    Only pending and processing jobs can be cancelled.
    Completed, failed, or already cancelled jobs cannot be cancelled.

    Returns:
        Updated job details

    Raises:
        HTTPException: If job cannot be cancelled
    """
    try:
        success = await job_manager.cancel_job(job.id)

        if not success:
            job_status = job.status.value
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status {job_status}"
            )

        # Refresh job data
        updated_job = await job_manager.get_job_status(job.id)

        logger.info(
            f"Job {job.id} cancelled",
            extra={"job_id": str(job.id)}
        )

        return JobResponse.from_job(updated_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Error cancelling job {job.id}",
            extra={"job_id": str(job.id), "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Delete job (admin only) -- not yet implemented"
)
async def delete_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    Delete a job (admin only).

    WARNING: Not yet implemented. Returns 501 until deletion logic is ready.

    Requires:
        - User must be an admin

    Raises:
        HTTPException: Always returns 501 Not Implemented
    """
    # Check admin permission
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    job = await job_manager.get_job_status(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Job deletion is not yet implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Job deletion is not yet implemented"
    )
