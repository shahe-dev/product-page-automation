"""
Job Repository

Handles all database operations for jobs and job steps.
Provides atomic operations for status transitions and progress tracking.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import Job, JobStep
from app.models.enums import JobStatus, JobStepStatus, TemplateType, JobType

logger = logging.getLogger(__name__)


class JobRepository:
    """
    Repository for job-related database operations.

    Handles:
    - CRUD operations for jobs and steps
    - Status transitions with atomic updates
    - Query by user/status/date
    - Progress tracking
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_job(
        self,
        user_id: UUID,
        template_type: str,
        job_type: JobType = JobType.EXTRACTION,
        template_id: Optional[UUID] = None,
        material_package_id: Optional[UUID] = None,
        processing_config: Optional[dict] = None
    ) -> Job:
        """
        Create a new job record.

        Args:
            user_id: User creating the job
            template_type: Template type identifier
            job_type: Type of job (EXTRACTION or GENERATION)
            template_id: Optional template UUID
            material_package_id: Required for GENERATION jobs - links to source package
            processing_config: Optional processing configuration

        Returns:
            Created job instance
        """
        job = Job(
            user_id=user_id,
            template_type=TemplateType(template_type),
            job_type=job_type,
            template_id=template_id,
            material_package_id=material_package_id,
            processing_config=processing_config or {},
            status=JobStatus.PENDING,
            progress=0,
            retry_count=0
        )

        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)

        logger.debug(
            f"Created job {job.id}",
            extra={"job_id": str(job.id), "user_id": str(user_id)}
        )

        return job

    async def create_job_step(
        self,
        job_id: UUID,
        step_id: str,
        label: str,
        sequence: int = 0
    ) -> JobStep:
        """
        Create a job step record.

        Args:
            job_id: Parent job ID
            step_id: Step identifier
            label: Human-readable step label
            sequence: Execution order (0-indexed)

        Returns:
            Created job step instance
        """
        step = JobStep(
            job_id=job_id,
            step_id=step_id,
            label=label,
            sequence=sequence,
            status=JobStepStatus.PENDING
        )

        self.db.add(step)
        await self.db.flush()
        await self.db.refresh(step)

        return step

    async def get_job(self, job_id: UUID) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job instance or None if not found
        """
        result = await self.db.execute(
            select(Job).where(Job.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_job_with_steps(self, job_id: UUID) -> Optional[Job]:
        """
        Get job with all steps eagerly loaded.

        Args:
            job_id: Job ID

        Returns:
            Job instance with steps or None if not found
        """
        result = await self.db.execute(
            select(Job)
            .options(selectinload(Job.steps))
            .where(Job.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_job_steps(self, job_id: UUID) -> List[JobStep]:
        """
        Get all steps for a job ordered by execution sequence.

        Args:
            job_id: Job ID

        Returns:
            List of job steps in execution order
        """
        result = await self.db.execute(
            select(JobStep)
            .where(JobStep.job_id == job_id)
            .order_by(JobStep.sequence)
        )
        return list(result.scalars().all())

    async def get_job_step(
        self,
        job_id: UUID,
        step_id: str
    ) -> Optional[JobStep]:
        """
        Get specific job step.

        Args:
            job_id: Job ID
            step_id: Step identifier

        Returns:
            Job step or None if not found
        """
        result = await self.db.execute(
            select(JobStep).where(
                and_(
                    JobStep.job_id == job_id,
                    JobStep.step_id == step_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        result: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update job status with atomic transition.

        Args:
            job_id: Job ID
            status: New job status
            progress: Optional progress percentage
            current_step: Optional current step label
            result: Optional result data
            error_message: Optional error message
        """
        update_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }

        if progress is not None:
            update_data["progress"] = progress

        if current_step is not None:
            update_data["current_step"] = current_step

        if result is not None:
            update_data["result"] = result

        if error_message is not None:
            update_data["error_message"] = error_message

        # Set timestamps based on status
        # Only set started_at if job doesn't already have one (fix: check DB, not update dict)
        if status == JobStatus.PROCESSING:
            existing = await self.db.execute(
                select(Job.started_at).where(Job.id == job_id)
            )
            if not existing.scalar_one_or_none():
                update_data["started_at"] = datetime.now(timezone.utc)

        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            update_data["completed_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(**update_data)
        )
        # Commit immediately so polling requests can see updates
        await self.db.commit()

        logger.debug(
            f"Updated job {job_id} status to {status.value}",
            extra={"job_id": str(job_id), "status": status.value}
        )

    async def update_job_progress(
        self,
        job_id: UUID,
        progress: int,
        current_step: str,
        progress_message: Optional[str] = None
    ) -> None:
        """
        Update job progress without changing status.

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            current_step: Current step label
            progress_message: Optional granular progress detail
        """
        values = {
            "progress": progress,
            "current_step": current_step,
            "updated_at": datetime.now(timezone.utc)
        }
        if progress_message is not None:
            values["progress_message"] = progress_message

        await self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(**values)
        )
        # Commit immediately so polling requests can see updates
        await self.db.commit()

    async def update_progress_message(
        self,
        job_id: UUID,
        message: str
    ) -> None:
        """
        Update only the granular progress message for a job.

        Args:
            job_id: Job ID
            message: Progress detail message (e.g., "Generating: project_name")
        """
        await self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                progress_message=message,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()

    async def update_job_step(
        self,
        job_id: UUID,
        step_id: str,
        status: JobStepStatus,
        result: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update job step status.

        Args:
            job_id: Job ID
            step_id: Step identifier
            status: New step status
            result: Optional step result data
            error_message: Optional error message
        """
        update_data = {
            "status": status
        }

        if status == JobStepStatus.IN_PROGRESS:
            update_data["started_at"] = datetime.now(timezone.utc)

        if status in [JobStepStatus.COMPLETED, JobStepStatus.FAILED, JobStepStatus.SKIPPED]:
            update_data["completed_at"] = datetime.now(timezone.utc)

        if result is not None:
            update_data["result"] = result

        if error_message is not None:
            update_data["error_message"] = error_message

        await self.db.execute(
            update(JobStep)
            .where(
                and_(
                    JobStep.job_id == job_id,
                    JobStep.step_id == step_id
                )
            )
            .values(**update_data)
        )
        # Commit immediately so polling requests can see updates
        await self.db.commit()

        logger.debug(
            f"Updated job {job_id} step {step_id} to {status.value}",
            extra={"job_id": str(job_id), "step_id": step_id, "status": status.value}
        )

    async def increment_retry_count(self, job_id: UUID) -> None:
        """
        Increment job retry count atomically.

        Args:
            job_id: Job ID
        """
        await self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                retry_count=Job.retry_count + 1,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await self.db.flush()

        logger.debug(
            f"Incremented retry count for job {job_id}",
            extra={"job_id": str(job_id)}
        )

    async def update_cloud_task_name(self, job_id: UUID, task_name: str) -> None:
        """
        Store Cloud Tasks task name for potential cancellation.

        Args:
            job_id: Job ID
            task_name: Cloud Tasks task name
        """
        await self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                cloud_task_name=task_name,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await self.db.flush()

        logger.debug(
            f"Stored cloud task name for job {job_id}",
            extra={"job_id": str(job_id), "task_name": task_name}
        )

    async def get_jobs_by_user(
        self,
        user_id: UUID,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Job]:
        """
        Get jobs for a specific user.

        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of jobs ordered by created_at DESC
        """
        query = select(Job).where(Job.user_id == user_id)

        if status:
            query = query.where(Job.status == status)

        query = query.order_by(Job.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_jobs_by_status(
        self,
        status: JobStatus,
        limit: int = 100
    ) -> List[Job]:
        """
        Get jobs by status.

        Args:
            status: Job status to filter by
            limit: Maximum number of jobs to return

        Returns:
            List of jobs
        """
        result = await self.db.execute(
            select(Job)
            .where(Job.status == status)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_stale_jobs(self, hours: int = 24) -> List[Job]:
        """
        Get jobs that have been processing for longer than specified hours.

        Args:
            hours: Number of hours to consider a job stale

        Returns:
            List of stale jobs
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        result = await self.db.execute(
            select(Job).where(
                and_(
                    Job.status == JobStatus.PROCESSING,
                    Job.started_at < cutoff_time
                )
            )
        )
        return list(result.scalars().all())

    async def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Delete completed/failed jobs older than specified days.

        Args:
            days: Number of days to keep jobs

        Returns:
            Number of jobs deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            delete(Job).where(
                and_(
                    Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]),
                    Job.completed_at < cutoff_date
                )
            )
        )
        await self.db.commit()

        deleted_count = result.rowcount
        logger.info(
            f"Cleaned up {deleted_count} jobs older than {days} days",
            extra={"deleted_count": deleted_count, "days": days}
        )

        return deleted_count

    async def get_job_statistics(self, user_id: Optional[UUID] = None) -> dict:
        """
        Get job statistics for monitoring.

        Args:
            user_id: Optional user ID to filter statistics

        Returns:
            Dictionary with job statistics
        """
        query = select(
            Job.status,
            func.count(Job.id).label("count")
        )

        if user_id:
            query = query.where(Job.user_id == user_id)

        query = query.group_by(Job.status)

        result = await self.db.execute(query)
        stats = {row.status.value: row.count for row in result}

        return {
            "total": sum(stats.values()),
            "pending": stats.get(JobStatus.PENDING.value, 0),
            "processing": stats.get(JobStatus.PROCESSING.value, 0),
            "completed": stats.get(JobStatus.COMPLETED.value, 0),
            "failed": stats.get(JobStatus.FAILED.value, 0),
            "cancelled": stats.get(JobStatus.CANCELLED.value, 0)
        }

    async def count_user_jobs(
        self,
        user_id: UUID,
        status: Optional[JobStatus] = None,
        since: Optional[datetime] = None
    ) -> int:
        """
        Count jobs for a user.

        Args:
            user_id: User ID
            status: Optional status filter
            since: Optional datetime to count jobs since

        Returns:
            Number of jobs
        """
        query = select(func.count(Job.id)).where(Job.user_id == user_id)

        if status:
            query = query.where(Job.status == status)

        if since:
            query = query.where(Job.created_at >= since)

        result = await self.db.execute(query)
        return result.scalar_one()
