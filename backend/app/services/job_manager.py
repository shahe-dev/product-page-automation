"""
Job Manager Service

Orchestrates job lifecycle management with progress tracking, error handling,
and retry logic. Manages the complete processing pipeline from PDF upload
to final output generation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from app.models.database import Job, JobStep, ProjectImage, ProjectFloorPlan
from app.models.enums import JobStatus, JobStepStatus, JobType, ImageCategory
from app.repositories.job_repository import JobRepository
from app.background.task_queue import TaskQueue
from app.utils.image_validation import validate_image_bytes

logger = logging.getLogger(__name__)


# =============================================================================
# Step Configurations for Different Job Types
# =============================================================================

# Extraction pipeline: 12 steps, split into shared prefix, parallel branches, shared suffix.
# Image branch (classify, watermark detect/remove) and text branch (extract, structure) run
# concurrently via asyncio.gather. Floor plans, optimize, and package run in the shared suffix
# AFTER both branches complete -- this guarantees table data exists when floor plans merge.
# Drive upload happens as a background task after ALL generation jobs complete.
EXTRACTION_STEPS = [
    {"id": "upload", "label": "PDF Upload & Validation", "branch": "shared"},
    {"id": "extract_images", "label": "Image Extraction", "branch": "shared", "timeout": 300},
    {"id": "classify_images", "label": "Image Classification", "branch": "image", "timeout": 600},
    {"id": "detect_watermarks", "label": "Watermark Detection", "branch": "image", "timeout": 300},
    {"id": "remove_watermarks", "label": "Watermark Removal", "branch": "image", "timeout": 600},
    {"id": "extract_data", "label": "Data Extraction", "branch": "text", "timeout": 600},
    {"id": "structure_data", "label": "Data Structuring", "branch": "text", "timeout": 300},
    {"id": "extract_floor_plans", "label": "Floor Plan Extraction", "branch": "shared", "timeout": 600},
    {"id": "optimize_images", "label": "Image Optimization", "branch": "shared", "timeout": 300},
    {"id": "package_assets", "label": "Asset Packaging", "branch": "shared", "timeout": 120},
    {"id": "enrich_data", "label": "Cross-Source Enrichment", "branch": "shared", "timeout": 120},
    {"id": "materialize", "label": "Package Materialization", "branch": "shared", "timeout": 900},
]

# Generation pipeline: 5 steps that consume a MaterialPackage
# Each generation job targets one template type.
# Drive upload is handled by background sync after ALL generation jobs complete.
GENERATION_STEPS = [
    {"id": "load_package", "label": "Load Material Package", "progress": 10},
    {"id": "generate_content", "label": "Content Generation", "progress": 50},
    {"id": "populate_sheet", "label": "Sheet Population", "progress": 75},
    {"id": "export_sheet", "label": "Export Sheet to Archive", "progress": 90},
    {"id": "finalize_generation", "label": "Finalization", "progress": 100},
]


def get_steps_for_job_type(job_type: JobType) -> list[dict]:
    """
    Return step configuration for the given job type.

    Args:
        job_type: The type of job (EXTRACTION or GENERATION)

    Returns:
        List of step configuration dictionaries
    """
    if job_type == JobType.GENERATION:
        return GENERATION_STEPS
    # Default to extraction steps
    return EXTRACTION_STEPS


class JobManager:
    """
    Manages job lifecycle, progress tracking, and error handling.

    Responsibilities:
    - Create and initialize jobs
    - Track job progress through processing steps
    - Handle errors with automatic retry logic
    - Cancel jobs and clean up resources
    - Coordinate with task queue for async processing
    """

    # Define the processing steps (Phase 2 + Phase 3)
    JOB_STEPS = [
        # Phase 2: Material Preparation
        {"id": "upload", "label": "PDF Upload & Validation", "progress": 3},
        {"id": "extract_images", "label": "Image Extraction", "progress": 10},
        {"id": "classify_images", "label": "Image Classification", "progress": 20},
        {"id": "detect_watermarks", "label": "Watermark Detection", "progress": 27},
        {"id": "remove_watermarks", "label": "Watermark Removal", "progress": 34},
        {"id": "extract_floor_plans", "label": "Floor Plan Extraction", "progress": 40},
        {"id": "optimize_images", "label": "Image Optimization", "progress": 47},
        {"id": "package_assets", "label": "Asset Packaging", "progress": 53},
        # Phase 3: Content Generation
        {"id": "extract_data", "label": "Data Extraction", "progress": 60},
        {"id": "structure_data", "label": "Data Structuring", "progress": 68},
        {"id": "generate_content", "label": "Content Generation", "progress": 78},
        {"id": "populate_sheet", "label": "Sheet Population", "progress": 88},
        # Finalization
        {"id": "upload_cloud", "label": "Cloud Upload", "progress": 95},
        {"id": "finalize", "label": "Finalization", "progress": 100},
    ]

    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # Exponential backoff base (2^retry_count seconds)

    def __init__(self, job_repository: JobRepository, task_queue: TaskQueue):
        """
        Initialize job manager.

        Args:
            job_repository: Repository for job database operations
            task_queue: Task queue for enqueueing background tasks
        """
        self.job_repo = job_repository
        self.task_queue = task_queue
        # Per-job pipeline context for passing data between steps
        self._pipeline_ctx: Dict[UUID, Dict[str, Any]] = {}
        # Material package service (set via property for DI/testing)
        self._material_package_service: Optional[Any] = None

    async def _branch_clone(self):
        """Create a new JobManager with its own DB session for parallel branches.

        Returns an async context manager that yields a session-isolated clone.
        The clone shares _pipeline_ctx dict (safe: asyncio is single-threaded).
        """
        from contextlib import asynccontextmanager
        from app.config.database import async_session_factory

        @asynccontextmanager
        async def _ctx():
            async with async_session_factory() as session:
                repo = JobRepository(session)
                clone = JobManager(repo, self.task_queue)
                clone._pipeline_ctx = self._pipeline_ctx
                clone._material_package_service = self._material_package_service
                try:
                    yield clone
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        return _ctx()

    async def create_job(
        self,
        user_id: UUID,
        template_type: str,
        job_type: JobType = JobType.EXTRACTION,
        template_id: Optional[UUID] = None,
        material_package_id: Optional[UUID] = None,
        processing_config: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """
        Create a new job and initialize processing steps.

        Args:
            user_id: User creating the job
            template_type: Template type (opr, mpp, etc.)
            job_type: Type of job (EXTRACTION or GENERATION)
            template_id: Optional template ID
            material_package_id: Required for GENERATION jobs
            processing_config: Optional processing configuration

        Returns:
            Created job instance

        Raises:
            ValueError: If template_type is invalid
        """
        logger.info(
            f"Creating {job_type.value} job for user {user_id} with template {template_type}",
            extra={
                "user_id": str(user_id),
                "template_type": template_type,
                "job_type": job_type.value,
            },
        )

        # Create job record
        job = await self.job_repo.create_job(
            user_id=user_id,
            template_type=template_type,
            job_type=job_type,
            template_id=template_id,
            material_package_id=material_package_id,
            processing_config=processing_config or {},
        )

        # Initialize job steps based on job type
        await self._initialize_job_steps(job.id, job_type)

        logger.info(
            f"Job {job.id} created successfully",
            extra={
                "job_id": str(job.id),
                "status": job.status.value,
                "job_type": job_type.value,
            },
        )

        return job

    async def create_and_dispatch_job(
        self,
        user_id: UUID,
        template_type: str,
        pdf_path: str,
        job_type: JobType = JobType.EXTRACTION,
        template_id: Optional[UUID] = None,
        material_package_id: Optional[UUID] = None,
        processing_config: Optional[Dict[str, Any]] = None,
    ) -> tuple[Job, Optional[str]]:
        """
        Create a job and dispatch it to the task queue atomically.

        This method ensures proper transaction boundaries: the job is committed
        to the database before dispatching to the task queue. This is critical
        because the task queue callback (whether Cloud Tasks in production or
        local HTTP call in development) uses a separate database connection
        and must be able to read the job.

        Args:
            user_id: User creating the job
            template_type: Template type (opr, mpp, etc.)
            pdf_path: Path to uploaded PDF (GCS URL or local path)
            job_type: Type of job (EXTRACTION or GENERATION)
            template_id: Optional template ID
            material_package_id: Required for GENERATION jobs
            processing_config: Optional processing configuration

        Returns:
            Tuple of (created job, task name or None)

        Raises:
            ValueError: If template_type is invalid
            Exception: If job creation or dispatch fails
        """
        # Step 1: Create job and steps (flushed but not committed)
        job = await self.create_job(
            user_id=user_id,
            template_type=template_type,
            job_type=job_type,
            template_id=template_id,
            material_package_id=material_package_id,
            processing_config=processing_config,
        )

        # Step 2: Commit transaction before dispatch
        # This ensures the job is visible to the task queue callback,
        # which uses a separate database connection. This matches production
        # behavior where Cloud Tasks calls back asynchronously.
        await self.job_repo.db.commit()

        # Step 3: Dispatch to task queue (job is now guaranteed visible)
        try:
            task_name = await self.task_queue.enqueue_job(
                job_id=job.id, pdf_path=pdf_path, template_type=template_type
            )

            if task_name:
                await self.job_repo.update_cloud_task_name(job.id, task_name)

            logger.info(
                f"Job {job.id} created and dispatched successfully",
                extra={"job_id": str(job.id), "task_name": task_name},
            )

            return job, task_name

        except Exception as e:
            # Job exists but dispatch failed - mark as failed
            logger.exception(
                f"Failed to dispatch job {job.id}",
                extra={"job_id": str(job.id), "error": str(e)},
            )
            await self.fail_job(job.id, f"Failed to dispatch: {str(e)}")
            raise

    async def _initialize_job_steps(
        self, job_id: UUID, job_type: JobType = JobType.EXTRACTION
    ) -> None:
        """
        Initialize job steps with PENDING status based on job type.

        Args:
            job_id: Job ID to initialize steps for
            job_type: Type of job (EXTRACTION or GENERATION) determines steps
        """
        steps = get_steps_for_job_type(job_type)

        for index, step_config in enumerate(steps):
            await self.job_repo.create_job_step(
                job_id=job_id,
                step_id=step_config["id"],
                label=step_config["label"],
                sequence=index,
            )

        logger.debug(
            f"Initialized {len(steps)} steps for {job_type.value} job {job_id}",
            extra={
                "job_id": str(job_id),
                "step_count": len(steps),
                "job_type": job_type.value,
            },
        )

    async def start_job(self, job_id: UUID, pdf_path: str, **kwargs: Any) -> None:
        """
        Start job processing by enqueueing it to the task queue.

        Args:
            job_id: Job ID to start
            pdf_path: Path to uploaded PDF file
            **kwargs: Additional parameters for processing

        Raises:
            ValueError: If job not found or already started
        """
        job = await self.job_repo.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status != JobStatus.PENDING:
            raise ValueError(
                f"Job {job_id} already started with status {job.status.value}"
            )

        logger.info(
            f"Starting job {job_id}",
            extra={"job_id": str(job_id), "pdf_path": pdf_path},
        )

        # Enqueue task to Cloud Tasks
        try:
            task_name = await self.task_queue.enqueue_job(
                job_id=job_id, pdf_path=pdf_path, **kwargs
            )

            # Store task name for potential cancellation
            if task_name:
                await self.job_repo.update_cloud_task_name(job_id, task_name)

            logger.info(
                f"Job {job_id} enqueued successfully: {task_name}",
                extra={"job_id": str(job_id), "task_name": task_name},
            )

        except Exception as e:
            logger.exception(
                f"Failed to enqueue job {job_id}",
                extra={"job_id": str(job_id), "error": str(e)},
            )
            await self.fail_job(job_id, f"Failed to enqueue: {str(e)}")
            raise

    async def update_job_progress(
        self,
        job_id: UUID,
        step_id: str,
        status: JobStepStatus,
        step_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update progress for a specific job step.

        Progress is computed dynamically from the ratio of completed steps
        to total steps. This avoids non-monotonic progress jumps when the
        image and text branches run in parallel.

        Args:
            job_id: Job ID
            step_id: Step identifier
            status: New step status
            step_data: Optional step result data
            error_message: Optional error message if step failed
        """
        logger.info(
            f"Updating job {job_id} step {step_id} to {status.value}",
            extra={"job_id": str(job_id), "step_id": step_id, "status": status.value},
        )

        # Find step configuration from both pipeline types
        all_steps = EXTRACTION_STEPS + GENERATION_STEPS
        step_config = next((s for s in all_steps if s["id"] == step_id), None)

        if not step_config:
            logger.warning(
                f"Unknown step_id '{step_id}' for job {job_id}",
                extra={"job_id": str(job_id), "step_id": step_id},
            )
            return

        # Update step status
        await self.job_repo.update_job_step(
            job_id=job_id,
            step_id=step_id,
            status=status,
            result=step_data,
            error_message=error_message,
        )

        # Compute progress from completed step count (parallel-safe)
        steps = await self.job_repo.get_job_steps(job_id)
        total = len(steps) or 1
        completed = sum(
            1 for s in steps if s.status in (JobStepStatus.COMPLETED.value, "completed")
        )

        if status == JobStepStatus.IN_PROGRESS:
            # Conservative: count completed + partial credit for this step
            progress_pct = min(int((completed / total) * 100) + 1, 99)
            await self.job_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.PROCESSING,
                progress=progress_pct,
                current_step=step_config["label"],
            )
        elif status == JobStepStatus.COMPLETED:
            # Re-count after this step was marked completed above
            progress_pct = min(int(((completed + 1) / total) * 100), 100)
            await self.job_repo.update_job_progress(
                job_id=job_id, progress=progress_pct, current_step=step_config["label"]
            )

    async def complete_job(self, job_id: UUID, result: Dict[str, Any]) -> None:
        """
        Mark job as completed with final results.

        Args:
            job_id: Job ID
            result: Job result data (project_id, sheet_url, zip_url, etc.)
        """
        logger.info(
            f"Completing job {job_id}", extra={"job_id": str(job_id), "result": result}
        )

        await self.job_repo.update_job_status(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            current_step="Complete",
            result=result,
        )

        logger.info(
            f"Job {job_id} completed successfully", extra={"job_id": str(job_id)}
        )

    async def update_progress_message(self, job_id: UUID, message: str) -> None:
        """
        Update the granular progress message for a job.
        Used to show detailed substep info like "Generating: project_name".

        Args:
            job_id: Job ID
            message: Progress detail message
        """
        await self.job_repo.update_progress_message(job_id, message)

    async def fail_job(
        self, job_id: UUID, error_message: str, retry: bool = True
    ) -> None:
        """
        Mark job as failed and optionally retry.

        Args:
            job_id: Job ID
            error_message: Error message describing failure
            retry: Whether to attempt retry (default: True)
        """
        job = await self.job_repo.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found for failure handling")
            return

        retry_count = job.retry_count

        logger.error(
            f"Job {job_id} failed (attempt {retry_count + 1}/{self.MAX_RETRIES}): {error_message}",
            extra={
                "job_id": str(job_id),
                "retry_count": retry_count,
                "error_message": error_message,
            },
        )

        # Increment retry count
        new_retry_count = retry_count + 1

        # Check if we should retry
        if retry and new_retry_count < self.MAX_RETRIES:
            # Calculate backoff time
            backoff_seconds = self.RETRY_BACKOFF_BASE**new_retry_count

            logger.info(
                f"Will retry job {job_id} in {backoff_seconds} seconds",
                extra={
                    "job_id": str(job_id),
                    "backoff_seconds": backoff_seconds,
                    "retry_count": new_retry_count,
                },
            )

            # Update retry count but keep status as PROCESSING
            await self.job_repo.increment_retry_count(job_id)

            # Note: The actual retry scheduling is handled by Cloud Tasks
            # based on the retry policy configured in the queue

        else:
            # Max retries exhausted or retry disabled
            logger.error(
                f"Job {job_id} permanently failed after {new_retry_count} attempts",
                extra={
                    "job_id": str(job_id),
                    "retry_count": new_retry_count,
                    "error_message": error_message,
                },
            )

            await self.job_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                error_message=f"Failed after {new_retry_count} attempts: {error_message}",
            )

    async def cancel_job(self, job_id: UUID) -> bool:
        """
        Cancel a pending or processing job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled successfully, False otherwise
        """
        job = await self.job_repo.get_job(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found for cancellation")
            return False

        if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
            logger.warning(
                f"Cannot cancel job {job_id} with status {job.status.value}",
                extra={"job_id": str(job_id), "status": job.status.value},
            )
            return False

        logger.info(f"Cancelling job {job_id}", extra={"job_id": str(job_id)})

        await self.job_repo.update_job_status(
            job_id=job_id,
            status=JobStatus.CANCELLED,
            error_message="Job cancelled by user",
        )

        # Cancel task in Cloud Tasks queue if task name is stored
        cloud_task_cancelled = False
        if job.cloud_task_name:
            try:
                deleted = await self.task_queue.delete_task_async(job.cloud_task_name)
                if deleted:
                    cloud_task_cancelled = True
                    logger.info(
                        f"Cloud Task deleted for job {job_id}: {job.cloud_task_name}",
                        extra={"job_id": str(job_id), "task_name": job.cloud_task_name},
                    )
                else:
                    logger.warning(
                        f"Cloud Task not found or already completed for job {job_id}",
                        extra={"job_id": str(job_id), "task_name": job.cloud_task_name},
                    )
            except Exception as e:
                # Log but don't fail - the job is already cancelled in our DB
                logger.warning(
                    f"Failed to delete Cloud Task for job {job_id}: {e}",
                    extra={
                        "job_id": str(job_id),
                        "task_name": job.cloud_task_name,
                        "error": str(e),
                    },
                )

        logger.info(
            f"Job {job_id} cancelled successfully (Cloud Task deleted: {cloud_task_cancelled})",
            extra={"job_id": str(job_id), "cloud_task_cancelled": cloud_task_cancelled},
        )

        return True

    async def execute_processing_pipeline(
        self, job_id: UUID, pdf_path: str
    ) -> Dict[str, Any]:
        """
        Execute the full job processing pipeline.

        This is called by the Cloud Tasks callback endpoint. It processes
        the job through all steps in sequence.

        Args:
            job_id: Job ID to process
            pdf_path: Path to the uploaded PDF file

        Returns:
            Processing result dictionary

        Raises:
            Exception: If processing fails
        """
        logger.info(
            f"Starting processing pipeline for job {job_id}",
            extra={"job_id": str(job_id), "pdf_path": pdf_path},
        )

        result = {}
        current_step = None

        try:
            # Get job steps
            steps = await self.job_repo.get_job_steps(job_id)

            if not steps:
                # Initialize steps if not already done
                await self._initialize_job_steps(job_id)
                steps = await self.job_repo.get_job_steps(job_id)

            total_steps = len(steps)

            # Process each step
            for index, step in enumerate(steps):
                current_step = step.step_id

                # Check if job was cancelled
                job = await self.job_repo.get_job(job_id)
                if job.status == JobStatus.CANCELLED:
                    logger.info(f"Job {job_id} cancelled, stopping pipeline")
                    raise Exception("Job cancelled")

                # Update step to in progress
                await self.update_job_progress(
                    job_id=job_id,
                    step_id=step.step_id,
                    status=JobStepStatus.IN_PROGRESS,
                )

                # Calculate overall progress
                progress = int((index / total_steps) * 100)
                await self.job_repo.update_job_progress(
                    job_id=job_id, progress=progress, current_step=step.label
                )

                logger.info(
                    f"Processing step {step.step_id} ({index + 1}/{total_steps}) for job {job_id}",
                    extra={
                        "job_id": str(job_id),
                        "step_id": step.step_id,
                        "progress": progress,
                    },
                )

                # Execute step (routes by step_id via _make_step_fn)
                step_fn = self._make_step_fn(step.step_id, job_id, pdf_path)
                step_result = await step_fn()

                # Update step as completed
                await self.update_job_progress(
                    job_id=job_id,
                    step_id=step.step_id,
                    status=JobStepStatus.COMPLETED,
                    step_data=step_result,
                )

                # Store step result
                result[step.step_id] = step_result

            # All steps completed - mark job as complete
            await self.complete_job(job_id, result)

            logger.info(
                f"Processing pipeline completed for job {job_id}",
                extra={"job_id": str(job_id)},
            )

            return result

        except Exception as e:
            logger.exception(
                f"Processing pipeline failed for job {job_id} at step {current_step}",
                extra={
                    "job_id": str(job_id),
                    "current_step": current_step,
                    "error": str(e),
                },
            )

            # Mark current step as failed
            if current_step:
                await self.update_job_progress(
                    job_id=job_id,
                    step_id=current_step,
                    status=JobStepStatus.FAILED,
                    error_message=str(e),
                )

            # Mark the overall job as failed (prevents zombie jobs stuck in PROCESSING)
            await self.fail_job(job_id, str(e))

            raise

        finally:
            # Always clean up pipeline context to prevent memory leaks.
            # Each job's context can hold 50+ MB of image/ZIP data.
            self._pipeline_ctx.pop(job_id, None)

    async def execute_extraction_pipeline(
        self, job_id: UUID, pdf_path: str
    ) -> Optional[Any]:
        """
        Execute extraction pipeline with parallel image/text branches.

        Three phases:
          A. Shared prefix (upload, extract_images) -- sequential
          B. Parallel branches via asyncio.gather:
             - Image branch: classify -> watermark detect/remove
             - Text branch:  extract_data -> structure_data
          C. Shared suffix -- sequential:
             extract_floor_plans -> optimize_images -> package_assets ->
             enrich_data -> materialize

        Floor plans run in the suffix (not image branch) so table data from
        the text branch is guaranteed to exist for the merge step.

        After completion, auto-dispatches generation jobs for any template_ids
        specified in job.processing_config["template_ids"].
        Drive upload is handled as a background task after ALL generation jobs complete.

        Args:
            job_id: Job UUID
            pdf_path: Path to PDF file (GCS or local)

        Returns:
            The created MaterialPackage or None if failed
        """
        logger.info(f"Starting extraction pipeline for job {job_id}")
        current_step = None

        try:
            # Initialize pipeline context
            self._pipeline_ctx[job_id] = {}

            # Get job for template info
            job = await self.job_repo.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Validate required services before starting
            if not self._material_package_service:
                raise RuntimeError(
                    "MaterialPackageService not configured on JobManager. "
                    "Cannot run extraction pipeline without it."
                )

            # ----------------------------------------------------------
            # Phase A: Shared prefix (sequential)
            # ----------------------------------------------------------
            current_step = "upload"
            await self._execute_step(
                job_id, "upload", lambda: self._step_upload(pdf_path)
            )

            current_step = "extract_images"
            await self._execute_step(
                job_id,
                "extract_images",
                lambda: self._step_extract_images(job_id, pdf_path),
            )

            # ----------------------------------------------------------
            # Phase B: Parallel branches (each gets its own DB session)
            # ----------------------------------------------------------
            logger.info(f"Job {job_id}: launching parallel image + text branches")

            async def _image_branch():
                async with await self._branch_clone() as mgr:
                    await mgr._run_image_branch(job_id)

            async def _text_branch():
                async with await self._branch_clone() as mgr:
                    await mgr._run_text_branch(job_id)

            await asyncio.gather(
                _image_branch(),
                _text_branch(),
            )

            # ----------------------------------------------------------
            # Phase C: Shared suffix (sequential)
            # Floor plans run here (not in image branch) so table data
            # from text branch is guaranteed to exist for merging.
            # ----------------------------------------------------------
            current_step = "extract_floor_plans"
            await self._execute_step(
                job_id,
                "extract_floor_plans",
                lambda: self._step_extract_floor_plans(job_id),
            )

            current_step = "optimize_images"
            await self._execute_step(
                job_id,
                "optimize_images",
                lambda: self._step_optimize_images(job_id),
            )

            current_step = "package_assets"
            await self._execute_step(
                job_id,
                "package_assets",
                lambda: self._step_package_assets(job_id),
            )

            current_step = "enrich_data"
            await self._execute_step(
                job_id,
                "enrich_data",
                lambda: self._step_enrich_from_classification(job_id),
            )

            current_step = "materialize"
            project = await self._create_project_from_extraction(job_id)
            self._pipeline_ctx[job_id]["project_id"] = project.id
            await self._execute_step(
                job_id,
                "materialize",
                lambda: self._step_materialize_package(job_id, project.id),
            )

            # Get package info from context (available after materialize)
            ctx = self._pipeline_ctx.get(job_id, {})
            package_id = ctx.get("material_package_id")
            project_id = ctx.get("project_id")

            # Dispatch generation jobs immediately after materialize.
            # No Drive upload during extraction -- Drive sync happens as a
            # background task after ALL generation jobs complete.
            if package_id and project_id:
                await self._dispatch_generation_jobs(job_id, project_id, package_id)

            # Mark extraction job as completed
            await self.complete_job(
                job_id,
                {
                    "project_id": str(project_id) if project_id else None,
                    "material_package_id": str(package_id) if package_id else None,
                    "extraction_complete": True,
                },
            )

            # Return the MaterialPackage
            if package_id and self._material_package_service:
                return await self._material_package_service.get_by_id(package_id)

            return None

        except Exception as e:
            logger.exception(
                f"Extraction pipeline failed for job {job_id} at step {current_step}"
            )

            if current_step:
                await self.update_job_progress(
                    job_id=job_id,
                    step_id=current_step,
                    status=JobStepStatus.FAILED,
                    error_message=str(e),
                )

            await self.fail_job(job_id, str(e))
            raise

        finally:
            # Always cleanup pipeline context
            self._pipeline_ctx.pop(job_id, None)

    # Lookup table: step_id -> timeout (seconds) from step configs
    _STEP_TIMEOUTS: Dict[str, int] = {
        s["id"]: s["timeout"]
        for s in EXTRACTION_STEPS + GENERATION_STEPS
        if "timeout" in s
    }

    async def _execute_step(
        self,
        job_id: UUID,
        step_id: str,
        step_fn,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run a single pipeline step with progress bookkeeping.

        Commits after each progress update so frontend sees real-time progress,
        even when running inside a branch clone session.

        If a ``timeout`` (seconds) is configured for the step in
        EXTRACTION_STEPS / GENERATION_STEPS, the step is wrapped in
        ``asyncio.wait_for`` so a single hung operation cannot block the
        entire pipeline indefinitely.

        Args:
            job_id: Job UUID
            step_id: Step identifier (e.g., "materialize")
            step_fn: Async callable that executes the step
            timeout: Explicit override; falls back to step config
        """
        await self.update_job_progress(
            job_id=job_id, step_id=step_id, status=JobStepStatus.IN_PROGRESS
        )
        await self.job_repo.db.commit()

        effective_timeout = timeout or self._STEP_TIMEOUTS.get(step_id)
        if effective_timeout:
            try:
                result = await asyncio.wait_for(
                    step_fn(), timeout=effective_timeout
                )
            except asyncio.TimeoutError:
                raise RuntimeError(
                    f"Step '{step_id}' timed out after {effective_timeout}s"
                )
        else:
            result = await step_fn()

        await self.update_job_progress(
            job_id=job_id,
            step_id=step_id,
            status=JobStepStatus.COMPLETED,
            step_data=result,
        )
        await self.job_repo.db.commit()
        return result

    @staticmethod
    async def _step_upload(pdf_path: str) -> Dict[str, Any]:
        """Validate the PDF upload path."""
        return {"status": "validated", "pdf_path": pdf_path}

    async def _run_image_branch(self, job_id: UUID) -> None:
        """
        Image processing branch: classify -> watermark detect -> watermark remove.
        Floor plans, optimize, and package moved to shared suffix (Phase C) so
        table data from the text branch is available for floor plan merging.
        """
        image_steps = [
            ("classify_images", lambda: self._step_classify_images(job_id)),
            ("detect_watermarks", lambda: self._step_detect_watermarks(job_id)),
            ("remove_watermarks", lambda: self._step_remove_watermarks(job_id)),
        ]
        for step_id, step_fn in image_steps:
            await self._execute_step(job_id, step_id, step_fn)

    async def _run_text_branch(self, job_id: UUID) -> None:
        """
        Text processing branch (steps 9-10): data extraction, data structuring.
        Steps run sequentially within the branch.
        """
        text_steps = [
            ("extract_data", lambda: self._step_extract_data(job_id)),
            ("structure_data", lambda: self._step_structure_data(job_id)),
        ]
        for step_id, step_fn in text_steps:
            await self._execute_step(job_id, step_id, step_fn)

    async def _dispatch_generation_jobs(
        self, extraction_job_id: UUID, project_id: UUID, material_package_id: UUID
    ) -> list[tuple]:
        """
        Auto-dispatch generation jobs for templates specified in extraction job config.

        Called at the end of execute_extraction_pipeline. Creates one generation
        job per template_id in processing_config["template_ids"].

        Args:
            extraction_job_id: Source extraction job UUID
            project_id: Project UUID
            material_package_id: MaterialPackage UUID

        Returns:
            List of (job, task_name) tuples for dispatched jobs
        """
        job = await self.job_repo.get_job(extraction_job_id)
        if not job:
            return []

        template_ids = job.processing_config.get("template_ids", [])

        if not template_ids:
            logger.info(
                f"No template_ids in extraction job {extraction_job_id}, "
                "skipping generation dispatch"
            )
            return []

        dispatched = []
        for template_id in template_ids:
            try:
                gen_job, task_name = await self.create_and_dispatch_job(
                    user_id=job.user_id,
                    template_type=template_id,
                    pdf_path="",  # Not needed for generation
                    job_type=JobType.GENERATION,
                    material_package_id=material_package_id,
                    processing_config={
                        "project_id": str(project_id),
                        "source_extraction_job_id": str(extraction_job_id),
                    },
                )
                dispatched.append((gen_job, task_name))
                logger.info(
                    f"Dispatched generation job {gen_job.id} for template {template_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to dispatch generation job for template {template_id}: {e}"
                )

        return dispatched

    async def execute_generation_pipeline(self, job_id: UUID) -> Dict[str, Any]:
        """
        Execute generation-only pipeline (steps 11-14).

        Loads data from existing MaterialPackage and generates content
        for a specific template.

        Args:
            job_id: Job UUID

        Returns:
            Generation results including sheet_url and drive_folder_url
        """
        logger.info(f"Starting generation pipeline for job {job_id}")
        current_step = None

        try:
            # Initialize pipeline context
            self._pipeline_ctx[job_id] = {}

            # Get job for template info
            job = await self.job_repo.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Get steps for generation job type
            steps = GENERATION_STEPS

            result = {}

            # Execute each step
            for step_config in steps:
                current_step = step_config["id"]

                # Update progress
                await self.update_job_progress(
                    job_id=job_id,
                    step_id=current_step,
                    status=JobStepStatus.IN_PROGRESS,
                )

                # Execute step based on ID
                if current_step == "load_package":
                    result = await self._step_load_material_package(job_id)
                elif current_step == "generate_content":
                    result = await self._step_generate_content(job_id)
                elif current_step == "populate_sheet":
                    result = await self._step_populate_sheet(job_id)
                elif current_step == "export_sheet":
                    result = await self._step_export_sheet(job_id)
                elif current_step == "finalize_generation":
                    result = await self._step_finalize_generation(job_id)
                else:
                    result = {"status": "completed", "step_id": current_step}

                # Mark step complete
                await self.update_job_progress(
                    job_id=job_id,
                    step_id=current_step,
                    status=JobStepStatus.COMPLETED,
                    step_data=result,
                )

            # Mark generation job as completed
            await self.complete_job(job_id, result)

            return result

        except Exception as e:
            logger.exception(
                f"Generation pipeline failed for job {job_id} at step {current_step}"
            )

            if current_step:
                await self.update_job_progress(
                    job_id=job_id,
                    step_id=current_step,
                    status=JobStepStatus.FAILED,
                    error_message=str(e),
                )

            await self.fail_job(job_id, str(e))
            raise

        finally:
            # Always cleanup pipeline context
            self._pipeline_ctx.pop(job_id, None)

    async def _step_export_sheet(self, job_id: UUID) -> Dict[str, Any]:
        """Export populated Google Sheet as .xlsx to GCS for archival.

        The sheet remains a live Google Sheet in Drive. This step creates
        a static .xlsx snapshot in GCS alongside the extraction data.
        Drive folder creation and sheet move happen during background sync
        after all generation jobs complete.

        Args:
            job_id: Job UUID

        Returns:
            Dict with sheet_id, gcs_xlsx_path, and xlsx_size_bytes
        """
        from app.integrations.drive_client import drive_client

        ctx = self._pipeline_ctx.get(job_id, {})
        sheet_result = ctx.get("sheet_result")
        sheet_id = getattr(sheet_result, "sheet_id", None) if sheet_result else None

        if not sheet_id:
            logger.info("No sheet for job %s, skipping export", job_id)
            return {"status": "skipped"}

        job = await self.job_repo.get_job(job_id)
        template_type = job.template_type.value if job and job.template_type else "unknown"
        gcs_base = ctx.get("material_package_gcs_path", "")

        # Export Google Sheet to .xlsx bytes
        try:
            xlsx_bytes = await drive_client.export_google_sheet_to_excel(sheet_id)
        except Exception as e:
            logger.warning("Sheet export failed for job %s: %s", job_id, e)
            return {"status": "export_failed", "error": str(e)}

        # Upload .xlsx to GCS
        gcs_xlsx_path = f"{gcs_base}/sheets/{template_type}.xlsx"
        await self._material_package_service.storage.upload_file(
            source_file=xlsx_bytes,
            destination_blob_path=gcs_xlsx_path,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Store in context for finalize step
        ctx["gcs_xlsx_path"] = gcs_xlsx_path

        logger.info(
            "Exported sheet %s as .xlsx to GCS: %s (%d bytes)",
            sheet_id, gcs_xlsx_path, len(xlsx_bytes),
        )

        return {
            "sheet_id": sheet_id,
            "gcs_xlsx_path": gcs_xlsx_path,
            "xlsx_size_bytes": len(xlsx_bytes),
        }

    async def _step_finalize_generation(self, job_id: UUID) -> Dict[str, Any]:
        """
        Finalize generation run and create GenerationRun record.

        Creates a GenerationRun record linking the job to the template
        and MaterialPackage. This allows tracking which templates have
        been generated from a given package.

        Args:
            job_id: Job UUID

        Returns:
            Dict with generation_run_id and summary
        """
        from datetime import datetime as _dt, timezone as _tz

        from app.models.database import GenerationRun
        from app.models.enums import GenerationRunStatus

        ctx = self._pipeline_ctx.get(job_id, {})
        job = await self.job_repo.get_job(job_id)

        if not job:
            raise ValueError(f"Job {job_id} not found")

        material_package_id = job.material_package_id or ctx.get("material_package_id")
        sheet_result = ctx.get("sheet_result")
        content = ctx.get("generated_content")

        # Build output summary (sheet_result is a SheetResult object, not a dict)
        output_summary = {
            "sheet_id": getattr(sheet_result, "sheet_id", None)
            if sheet_result
            else None,
            "sheet_url": (
                getattr(sheet_result, "sheet_url", None) if sheet_result else None
            ),
            "fields_generated": len(content.fields) if content else 0,
            "total_cost": content.total_cost if content else 0,
        }

        # Create GenerationRun record
        db = self.job_repo.db

        # Resolve project_id from job config or context
        config = job.processing_config or {}
        project_id = config.get("project_id") or str(ctx.get("project_id", ""))
        if not project_id:
            raise RuntimeError("Cannot finalize generation: no project_id available")

        # Drive folder URL set to None during generation.
        # Updated by background Drive sync after all generation jobs complete.
        drive_folder_url = None

        generation_run = GenerationRun(
            project_id=UUID(project_id) if isinstance(project_id, str) else project_id,
            material_package_id=material_package_id,
            job_id=job_id,
            template_type=job.template_type,
            status=GenerationRunStatus.COMPLETED,
            generated_content=output_summary,
            sheet_url=output_summary.get("sheet_url"),
            drive_folder_url=drive_folder_url,
            completed_at=_dt.now(_tz.utc),
        )

        db.add(generation_run)
        await db.flush()
        await db.refresh(generation_run)

        # Update the Project record so the detail page shows generated content
        from app.models.database import Project
        from sqlalchemy.orm.attributes import flag_modified

        pid = UUID(project_id) if isinstance(project_id, str) else project_id
        project = await db.get(Project, pid)
        if project:
            # Build per-field content dict from ContentOutput
            content_dict = {}
            if content:
                for name, field in content.fields.items():
                    content_dict[name] = {
                        "content": field.content,
                        "character_count": field.character_count,
                        "within_limit": field.within_limit,
                    }

            # Merge with existing generated_content (multiple generation runs)
            merged = dict(project.generated_content or {})
            merged.update(content_dict)
            project.generated_content = merged
            flag_modified(project, "generated_content")

            resolved_sheet_url = output_summary.get("sheet_url")
            if resolved_sheet_url:
                project.sheet_url = resolved_sheet_url

            logger.info(
                "Updated Project %s: %d generated fields, sheet_url=%s",
                pid, len(content_dict), resolved_sheet_url,
            )

        logger.info(
            f"Created GenerationRun {generation_run.id} for job {job_id} "
            f"(template={job.template_type.value})"
        )

        # Check if all generation jobs for this package are complete.
        # If so, trigger background Drive sync to copy everything from GCS.
        # Pass current job_id so it's excluded from the "incomplete" count --
        # this job is still in_progress in the DB until the pipeline wrapper commits.
        if material_package_id:
            await self._check_and_trigger_drive_sync(material_package_id, current_job_id=job_id)

        return {
            "generation_run_id": str(generation_run.id),
            "template_type": job.template_type.value,
            "sheet_url": output_summary.get("sheet_url"),
            "fields_generated": output_summary.get("fields_generated"),
        }

    async def _check_and_trigger_drive_sync(
        self, material_package_id: UUID, current_job_id: UUID | None = None
    ) -> None:
        """Check if all generation jobs for a package are complete; trigger Drive sync.

        Uses atomic check-and-set on extraction_summary to prevent
        duplicate sync triggers when multiple jobs finalize concurrently.

        ``current_job_id`` is excluded from the "incomplete" query because the
        calling job hasn't been committed as COMPLETED yet (it's still
        in_progress in the DB at this point in the pipeline).
        """
        import asyncio
        from sqlalchemy import select, update, and_
        from app.models.database import MaterialPackage

        db = self.job_repo.db

        # Count incomplete generation jobs for this package
        conditions = [
            Job.material_package_id == material_package_id,
            Job.job_type == JobType.GENERATION.value,
            Job.status != JobStatus.COMPLETED.value,
            Job.status != JobStatus.FAILED.value,
        ]
        if current_job_id:
            conditions.append(Job.id != current_job_id)

        result = await db.execute(
            select(Job.id, Job.status).where(and_(*conditions))
        )
        incomplete = result.all()

        if incomplete:
            logger.info(
                "Package %s has %d incomplete generation jobs, skipping Drive sync",
                material_package_id, len(incomplete),
            )
            return

        # Atomic check-and-set: only trigger sync if not already triggered
        pkg_result = await db.execute(
            select(MaterialPackage.extraction_summary).where(
                MaterialPackage.id == material_package_id
            )
        )
        summary = pkg_result.scalar_one_or_none() or {}
        if not isinstance(summary, dict):
            summary = {}

        if summary.get("drive_sync_triggered"):
            # Full sync already ran. Check if there's an existing folder
            # for incremental sync (new template generated after initial sync).
            drive_folder_id = summary.get("drive_folder_id")
            if drive_folder_id:
                logger.info(
                    "Drive sync already triggered for package %s, "
                    "running incremental sync for new sheets",
                    material_package_id,
                )
                asyncio.create_task(
                    self._incremental_drive_sync(
                        material_package_id, drive_folder_id
                    )
                )
            else:
                logger.info(
                    "Drive sync already triggered for package %s but "
                    "no folder ID stored, skipping",
                    material_package_id,
                )
            return

        # Set flag atomically
        new_summary = {**summary, "drive_sync_triggered": True}
        await db.execute(
            update(MaterialPackage)
            .where(MaterialPackage.id == material_package_id)
            .values(extraction_summary=new_summary)
        )
        await db.commit()

        logger.info(
            "All generation jobs complete for package %s, triggering Drive sync",
            material_package_id,
        )

        # Fire-and-forget background sync
        asyncio.create_task(
            self._background_drive_sync(material_package_id)
        )

    async def _background_drive_sync(self, material_package_id: UUID) -> None:
        """Sync MaterialPackage from GCS to Google Drive (background task).

        Creates Drive project folder, uploads extraction assets from GCS,
        moves all generated Google Sheets into the folder, and uploads
        .xlsx snapshots.

        Uses its own DB session since this runs after pipeline completion.
        """
        import time
        from app.config.database import async_session_factory
        from app.integrations.drive_client import drive_client
        from app.models.database import MaterialPackage, GenerationRun
        from app.models.enums import GenerationRunStatus
        from app.services.storage_service import StorageService
        from sqlalchemy import select
        from sqlalchemy.orm.attributes import flag_modified

        start = time.monotonic()

        try:
            async with async_session_factory() as db:
                # Load package record
                pkg = await db.get(MaterialPackage, material_package_id)
                if not pkg:
                    logger.error("Drive sync: package %s not found", material_package_id)
                    return

                gcs_base = pkg.gcs_base_path
                structured = pkg.structured_data or {}
                project_name = (
                    structured.get("project_name", "Untitled Project")
                    if isinstance(structured, dict)
                    else getattr(structured, "project_name", "Untitled Project")
                )

                # 1. Create Drive folder structure
                folder_structure = await drive_client.create_project_structure(
                    project_name=project_name
                )
                folder_id = folder_structure["project"]
                logger.info(
                    "Drive sync: created folder for '%s': %s",
                    project_name, folder_id,
                )

                # 2. Download from GCS and upload to Drive
                storage = StorageService()
                gcs_files = await storage.list_files(prefix=gcs_base + "/")

                images_uploaded = 0
                data_uploaded = 0

                for blob_path in gcs_files:
                    relative = blob_path[len(gcs_base) + 1:]  # Strip base path
                    file_bytes = await storage.download_file(blob_path)
                    if file_bytes is None:
                        continue

                    # Route to correct Drive subfolder
                    if relative.startswith("images/"):
                        target_folder = folder_structure.get("images", folder_id)
                        parts = relative.replace("images/", "").split("/")
                        filename = parts[-1]
                        if len(parts) > 1:
                            # Create subfolder hierarchy under Images/
                            parent_id = target_folder
                            for subfolder_name in parts[:-1]:
                                parent_id = await drive_client.get_folder_by_path(
                                    subfolder_name, parent_id,
                                    create_if_missing=True,
                                )
                            target_folder = parent_id

                        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
                        mime = {
                            "webp": "image/webp", "jpg": "image/jpeg",
                            "jpeg": "image/jpeg", "png": "image/png",
                        }.get(ext, "application/octet-stream")
                        await drive_client.upload_file_bytes(
                            file_bytes, filename,
                            folder_id=target_folder, mime_type=mime,
                        )
                        images_uploaded += 1

                    elif relative.startswith("source/"):
                        filename = relative.split("/")[-1]
                        await drive_client.upload_file_bytes(
                            file_bytes, filename,
                            folder_id=folder_structure.get("source", folder_id),
                            mime_type="application/pdf",
                        )

                    elif relative.endswith(".json"):
                        filename = relative.split("/")[-1]
                        await drive_client.upload_file_bytes(
                            file_bytes, filename,
                            folder_id=folder_structure.get("raw_data", folder_id),
                            mime_type="application/json",
                        )
                        data_uploaded += 1

                    elif relative.startswith("sheets/") and relative.endswith(".xlsx"):
                        filename = relative.split("/")[-1]
                        await drive_client.upload_file_bytes(
                            file_bytes, filename,
                            folder_id=folder_structure.get("raw_data", folder_id),
                            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )

                # 3. Move all generated Google Sheets to project folder
                gen_runs = (await db.execute(
                    select(GenerationRun).where(
                        GenerationRun.material_package_id == material_package_id,
                        GenerationRun.status == GenerationRunStatus.COMPLETED.value,
                    )
                )).scalars().all()

                sheets_moved = 0
                for run in gen_runs:
                    sheet_id = (run.generated_content or {}).get("sheet_id")
                    if sheet_id:
                        try:
                            await drive_client.move_file(
                                file_id=sheet_id,
                                destination_folder_id=folder_id,
                            )
                            sheets_moved += 1
                        except Exception as e:
                            logger.warning("Failed to move sheet %s: %s", sheet_id, e)

                    # Update GenerationRun with drive folder URL
                    run.drive_folder_url = (
                        f"https://drive.google.com/drive/folders/{folder_id}"
                    )

                # 4. Update MaterialPackage with Drive info
                elapsed = time.monotonic() - start
                summary = dict(pkg.extraction_summary or {})
                summary.update({
                    "drive_folder_id": folder_id,
                    "drive_folder_url": f"https://drive.google.com/drive/folders/{folder_id}",
                    "drive_sync_status": "completed",
                    "drive_images_uploaded": images_uploaded,
                    "drive_data_uploaded": data_uploaded,
                    "drive_sheets_moved": sheets_moved,
                    "drive_sync_time_seconds": round(elapsed, 1),
                })
                pkg.extraction_summary = summary
                flag_modified(pkg, "extraction_summary")
                await db.commit()

                logger.info(
                    "Drive sync complete for package %s: "
                    "%d images, %d data files, %d sheets in %.1fs",
                    material_package_id, images_uploaded, data_uploaded,
                    sheets_moved, elapsed,
                )

        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error(
                "Drive sync failed for package %s after %.1fs: %s. "
                "All data is safe in GCS.",
                material_package_id, elapsed, e, exc_info=True,
            )
            try:
                async with async_session_factory() as db:
                    pkg = await db.get(MaterialPackage, material_package_id)
                    if pkg:
                        summary = dict(pkg.extraction_summary or {})
                        summary["drive_sync_status"] = "failed"
                        summary["drive_sync_error"] = str(e)
                        pkg.extraction_summary = summary
                        flag_modified(pkg, "extraction_summary")
                        await db.commit()
            except Exception:
                pass

    async def _incremental_drive_sync(
        self, material_package_id: UUID, drive_folder_id: str
    ) -> None:
        """Move newly generated sheets into an existing Drive project folder.

        Called when a new template is generated after the initial full sync
        has already run. Only handles sheets and xlsx -- images/JSON are
        unchanged (they come from the extraction, not generation).

        Uses its own DB session since this runs as a background task.
        """
        import time
        from app.config.database import async_session_factory
        from app.integrations.drive_client import drive_client
        from app.models.database import MaterialPackage, GenerationRun
        from app.models.enums import GenerationRunStatus
        from app.services.storage_service import StorageService
        from sqlalchemy import select
        from sqlalchemy.orm.attributes import flag_modified

        start = time.monotonic()
        drive_url = f"https://drive.google.com/drive/folders/{drive_folder_id}"

        try:
            async with async_session_factory() as db:
                pkg = await db.get(MaterialPackage, material_package_id)
                if not pkg:
                    logger.error(
                        "Incremental Drive sync: package %s not found",
                        material_package_id,
                    )
                    return

                gcs_base = pkg.gcs_base_path

                # Find generation runs that haven't been synced to Drive yet
                gen_runs = (await db.execute(
                    select(GenerationRun).where(
                        GenerationRun.material_package_id == material_package_id,
                        GenerationRun.status == GenerationRunStatus.COMPLETED.value,
                        GenerationRun.drive_folder_url.is_(None),
                    )
                )).scalars().all()

                if not gen_runs:
                    logger.info(
                        "Incremental Drive sync: no un-synced runs for package %s",
                        material_package_id,
                    )
                    return

                # Resolve Raw Data subfolder for xlsx uploads
                raw_data_folder_id = await drive_client.get_folder_by_path(
                    "Raw Data", drive_folder_id, create_if_missing=True
                )

                sheets_moved = 0
                xlsx_uploaded = 0
                storage = StorageService()

                for run in gen_runs:
                    sheet_id = (run.generated_content or {}).get("sheet_id")
                    if sheet_id:
                        try:
                            await drive_client.move_file(
                                file_id=sheet_id,
                                destination_folder_id=drive_folder_id,
                            )
                            sheets_moved += 1
                        except Exception as e:
                            logger.warning(
                                "Incremental sync: failed to move sheet %s: %s",
                                sheet_id, e,
                            )

                    # Upload the .xlsx snapshot if it exists in GCS
                    template = run.template_type.value if run.template_type else ""
                    if template and gcs_base:
                        xlsx_path = f"{gcs_base}/sheets/{template}.xlsx"
                        try:
                            xlsx_bytes = await storage.download_file(xlsx_path)
                            if xlsx_bytes:
                                await drive_client.upload_file_bytes(
                                    xlsx_bytes,
                                    f"{template}.xlsx",
                                    folder_id=raw_data_folder_id,
                                    mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                )
                                xlsx_uploaded += 1
                        except Exception as e:
                            logger.warning(
                                "Incremental sync: failed to upload xlsx for %s: %s",
                                template, e,
                            )

                    run.drive_folder_url = drive_url

                # Update package summary with incremental sync info
                elapsed = time.monotonic() - start
                summary = dict(pkg.extraction_summary or {})
                prev_sheets = summary.get("drive_sheets_moved", 0)
                summary["drive_sheets_moved"] = prev_sheets + sheets_moved
                summary["drive_last_incremental_sync"] = round(elapsed, 1)
                pkg.extraction_summary = summary
                flag_modified(pkg, "extraction_summary")
                await db.commit()

                logger.info(
                    "Incremental Drive sync complete for package %s: "
                    "%d sheets moved, %d xlsx uploaded in %.1fs",
                    material_package_id, sheets_moved, xlsx_uploaded, elapsed,
                )

        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error(
                "Incremental Drive sync failed for package %s after %.1fs: %s",
                material_package_id, elapsed, e, exc_info=True,
            )

    def _make_step_fn(self, step_id: str, job_id: UUID, pdf_path: str):
        """Build a callable for a step by ID (used by legacy pipeline)."""
        step_map = {
            "extract_images": lambda: self._step_extract_images(job_id, pdf_path),
            "classify_images": lambda: self._step_classify_images(job_id),
            "detect_watermarks": lambda: self._step_detect_watermarks(job_id),
            "remove_watermarks": lambda: self._step_remove_watermarks(job_id),
            "extract_floor_plans": lambda: self._step_extract_floor_plans(job_id),
            "optimize_images": lambda: self._step_optimize_images(job_id),
            "package_assets": lambda: self._step_package_assets(job_id),
            "extract_data": lambda: self._step_extract_data(job_id),
            "structure_data": lambda: self._step_structure_data(job_id),
            "generate_content": lambda: self._step_generate_content(job_id),
            "populate_sheet": lambda: self._step_populate_sheet(job_id),
            "upload_cloud": lambda: self._step_upload_cloud(job_id),
            "finalize": lambda: self._step_finalize(job_id),
        }
        return step_map.get(step_id, lambda: self._step_stub(step_id, job_id))

    @staticmethod
    async def _step_stub(step_id: str, job_id: UUID) -> Dict[str, Any]:
        return {
            "status": "completed",
            "step_id": step_id,
            "job_id": str(job_id),
            "message": f"Step {step_id} completed (stub)",
        }

    # ------------------------------------------------------------------
    # Phase 2: Material Preparation step implementations
    # ------------------------------------------------------------------

    async def _step_extract_images(self, job_id: UUID, pdf_path: str) -> Dict[str, Any]:
        """Extract images from PDF using dual extraction."""
        import asyncio
        from app.services.pdf_processor import PDFProcessor

        # Handle file:// URLs (local dev) vs GCS blob paths (production)
        if pdf_path.startswith("file://"):
            # Local filesystem path - strip file:// prefix
            local_path = pdf_path[7:]  # Remove "file://" prefix

            def _read_pdf():
                with open(local_path, "rb") as f:
                    return f.read()

            pdf_bytes = await asyncio.to_thread(_read_pdf)
        else:
            # GCS blob path - download from storage
            from app.services.storage_service import StorageService

            storage = StorageService()
            pdf_bytes = await storage.download_file(pdf_path)
            if pdf_bytes is None:
                raise RuntimeError(f"Failed to download PDF from storage: {pdf_path}")

        processor = PDFProcessor()
        result = await processor.extract_all(pdf_bytes)

        # Store extraction result and PDF bytes in pipeline context
        self._pipeline_ctx[job_id].update(
            {
                "extraction": result,
                "pdf_bytes": pdf_bytes,
                "pdf_path": pdf_path,
            }
        )

        return processor.get_extraction_summary(result)

    async def _step_classify_images(self, job_id: UUID) -> Dict[str, Any]:
        """Classify extracted images via Claude Vision."""
        from app.services.image_classifier import ImageClassifier

        ctx = self._pipeline_ctx.get(job_id, {})
        extraction = ctx.get("extraction")
        if extraction is None:
            raise RuntimeError("No extraction result available")

        classifier = ImageClassifier()
        output = await classifier.classify_extraction(extraction)

        ctx["classification"] = output

        # Preserve floor plan image bytes BEFORE _release_extraction_originals
        # runs in step 5 (remove_watermarks). After release, image_bytes = b"".
        fp_images = []
        for image, cls_result in output.classified_images:
            if cls_result.category == ImageCategory.FLOOR_PLAN:
                effective = image.image_bytes or image.llm_optimized_bytes
                if effective and validate_image_bytes(effective):
                    fp_images.append(image)

        # Fallback: if ALL embedded floor plan images are corrupt/empty,
        # use page renders for the same pages as fallback.
        if not fp_images:
            fp_pages = {
                image.metadata.page_number
                for image, cls_result in output.classified_images
                if cls_result.category == ImageCategory.FLOOR_PLAN
            }
            if fp_pages:
                extraction = ctx.get("extraction")
                if extraction and hasattr(extraction, "page_renders"):
                    for render in extraction.page_renders:
                        if render.metadata.page_number in fp_pages:
                            eff = render.image_bytes or render.llm_optimized_bytes
                            if eff and validate_image_bytes(eff):
                                fp_images.append(render)
                if fp_images:
                    logger.info(
                        "Floor plan fallback: preserved %d page renders for pages %s",
                        len(fp_images),
                        sorted(fp_pages),
                    )

        ctx["floor_plan_images"] = fp_images

        return {
            "total_input": output.total_input,
            "total_retained": output.total_retained,
            "total_duplicates": output.total_duplicates,
            "category_counts": output.category_counts,
        }

    async def _step_detect_watermarks(self, job_id: UUID) -> Dict[str, Any]:
        """Detect watermarks in classified images."""
        from app.models.enums import ImageCategory
        from app.services.watermark_detector import WatermarkDetector

        ctx = self._pipeline_ctx.get(job_id, {})
        classification = ctx.get("classification")
        if classification is None:
            raise RuntimeError("No classification result available")

        import asyncio

        detector = WatermarkDetector()
        sem = asyncio.Semaphore(5)

        async def _bounded_detect(img_bytes: bytes):
            async with sem:
                return await detector.detect(img_bytes)

        # Separate images that need detection from those that don't
        to_detect = []
        skip_indices = set()
        for i, (image, cls_result) in enumerate(classification.classified_images):
            if cls_result.category in (ImageCategory.FLOOR_PLAN, ImageCategory.LOGO):
                skip_indices.add(i)
            else:
                to_detect.append((i, image))

        # Run detections in parallel
        detect_results = await asyncio.gather(
            *[_bounded_detect(img.image_bytes) for _, img in to_detect]
        )

        # Reassemble results in original order
        detect_map = {
            idx: result for (idx, _), result in zip(to_detect, detect_results)
        }
        detections = []
        for i, (image, cls_result) in enumerate(classification.classified_images):
            detection = detect_map.get(i)
            detections.append((image, cls_result, detection))

        ctx["detections"] = detections
        watermark_count = sum(1 for _, _, d in detections if d and d.has_watermark)
        return {
            "watermarks_detected": watermark_count,
            "images_scanned": len(to_detect),
        }

    async def _step_remove_watermarks(self, job_id: UUID) -> Dict[str, Any]:
        """Remove detected watermarks using OpenCV inpainting."""
        from app.services.watermark_detector import DetectionResult
        from app.services.watermark_remover import WatermarkRemover

        ctx = self._pipeline_ctx.get(job_id, {})
        detections = ctx.get("detections")
        if detections is None:
            raise RuntimeError("No detection results available")

        remover = WatermarkRemover()
        cleaned = []
        removed_count = 0
        for image, cls_result, detection in detections:
            if detection and detection.has_watermark:
                removal = await remover.remove(image.image_bytes, detection)
                cleaned.append((removal.cleaned_bytes, cls_result))
                if removal.was_modified:
                    removed_count += 1
            else:
                cleaned.append((image.image_bytes, cls_result))

        ctx["cleaned_images"] = cleaned

        # Memory optimization: Release original bytes from extracted images
        # since cleaned_images now holds the processed bytes we need.
        # This can free ~50% of image memory.
        self._release_extraction_originals(job_id)

        return {"watermarks_removed": removed_count}

    async def _step_extract_floor_plans(self, job_id: UUID) -> Dict[str, Any]:
        """Extract structured data from floor plan images."""
        from app.models.enums import ImageCategory
        from app.services.floor_plan_extractor import FloorPlanExtractor

        ctx = self._pipeline_ctx.get(job_id, {})
        classification = ctx.get("classification")
        if classification is None:
            raise RuntimeError("No classification result available")

        # Use preserved floor plan images (saved before memory release in
        # _step_classify_images), falling back to classification list.
        floor_plan_images = ctx.get("floor_plan_images")
        if not floor_plan_images:
            floor_plan_images = [
                image
                for image, cls_result in classification.classified_images
                if cls_result.category == ImageCategory.FLOOR_PLAN
            ]

        extraction = ctx.get("extraction")
        page_text_map = (
            getattr(extraction, "page_text_map", None) if extraction else None
        )

        extractor = FloorPlanExtractor()
        result = await extractor.extract_floor_plans(
            floor_plan_images, page_text_map=page_text_map
        )

        # Merge with pdfplumber table data (if available from _step_structure_data)
        table_result = ctx.get("table_extraction")
        table_floor_plans = (
            table_result.floor_plan_specs if table_result else []
        )
        if table_floor_plans:
            result.floor_plans = extractor.merge_with_table_data(
                result.floor_plans, table_floor_plans
            )

        ctx["floor_plans"] = result
        return {
            "total_extracted": result.total_extracted,
            "total_duplicates": result.total_duplicates,
            "table_merged": len(table_floor_plans),
        }

    async def _step_optimize_images(self, job_id: UUID) -> Dict[str, Any]:
        """Optimize all images for delivery."""
        from app.services.image_optimizer import ImageOptimizer

        ctx = self._pipeline_ctx.get(job_id, {})
        cleaned = ctx.get("cleaned_images", [])
        floor_plans = ctx.get("floor_plans")

        images_to_optimize = []
        for img_bytes, cls_result in cleaned:
            images_to_optimize.append(
                (
                    img_bytes,
                    cls_result.category.value,
                    cls_result.alt_text,
                )
            )

        if floor_plans:
            for fp in floor_plans.floor_plans:
                images_to_optimize.append(
                    (
                        fp.image_bytes,
                        "floor_plan",
                        f"Floor plan - {fp.unit_type or 'unit'}",
                    )
                )

        optimizer = ImageOptimizer()
        result = await optimizer.optimize_batch(images_to_optimize)

        ctx["optimization"] = result
        return {
            "total_optimized": result.total_optimized,
            "total_errors": result.total_errors,
        }

    async def _step_package_assets(self, job_id: UUID) -> Dict[str, Any]:
        """Package optimized images into ZIP with manifest."""
        from app.services.output_organizer import OutputOrganizer

        ctx = self._pipeline_ctx.get(job_id, {})
        optimization = ctx.get("optimization")
        if optimization is None:
            raise RuntimeError("No optimization result available")

        # Get page text from extraction for extracted_text.json
        extraction = ctx.get("extraction")
        page_text_map = (
            getattr(extraction, "page_text_map", None) if extraction else None
        )

        floor_plans = ctx.get("floor_plans")
        fp_data = None
        if (
            floor_plans
            and hasattr(floor_plans, "floor_plans")
            and floor_plans.floor_plans
        ):
            fp_data = [
                {
                    "unit_type": getattr(fp, "unit_type", None),
                    "bedrooms": getattr(fp, "bedrooms", None),
                    "bathrooms": getattr(fp, "bathrooms", None),
                    "total_sqft": getattr(fp, "total_sqft", None),
                    "suite_sqft": getattr(fp, "suite_sqft", None),
                    "balcony_sqft": getattr(fp, "balcony_sqft", None),
                    "builtup_sqft": getattr(fp, "builtup_sqft", None),
                    "features": getattr(fp, "features", []),
                }
                for fp in floor_plans.floor_plans
            ]

        organizer = OutputOrganizer()
        zip_bytes, manifest = organizer.create_package(
            optimization,
            project_name="",
            floor_plan_data=fp_data,
            page_text_map=page_text_map,
        )

        ctx["zip_bytes"] = zip_bytes
        ctx["manifest"] = manifest

        return {
            "zip_size_bytes": len(zip_bytes),
            "total_files": len(manifest.entries),
            "categories": manifest.categories,
        }

    async def _step_materialize_package(
        self, job_id: UUID, project_id: UUID
    ) -> Dict[str, Any]:
        """
        Create MaterialPackage from pipeline context and persist to GCS.

        This step runs after structure_data (step 10) for EXTRACTION jobs.
        It persists all extraction data to GCS and creates a MaterialPackage
        DB record that can be consumed by multiple generation jobs.

        Args:
            job_id: Job UUID
            project_id: Project UUID (from _create_project_from_extraction)

        Returns:
            Dict with material_package_id and gcs_path
        """
        ctx = self._pipeline_ctx.get(job_id, {})

        # Persist to GCS
        gcs_path = await self._material_package_service.persist_to_gcs(
            project_id=project_id,
            pipeline_ctx=ctx,
        )

        # Build extraction summary from classification data
        classification = ctx.get("classification", {})
        extraction = ctx.get("extraction", {})

        extraction_summary = {
            "total_images": getattr(classification, "total_input", 0)
            if hasattr(classification, "total_input")
            else classification.get("total_images", 0),
            "classified_images": getattr(classification, "category_counts", {})
            if hasattr(classification, "category_counts")
            else classification.get("by_category", {}),
            "total_pages": len(extraction.get("page_text_map", {}))
            if isinstance(extraction, dict)
            else getattr(extraction, "total_pages", 0),
            "confidence_profile": ctx.get("pdf_confidence_profile", "high"),
        }

        # Serialize structured_data for DB storage (must be JSON-safe for JSONB)
        import dataclasses as _dc

        structured = ctx.get("structured_data", {})
        if _dc.is_dataclass(structured) and not isinstance(structured, type):
            structured_dict = _dc.asdict(structured)
        elif hasattr(structured, "model_dump"):
            structured_dict = structured.model_dump()
        elif hasattr(structured, "__dict__"):
            structured_dict = {
                k: v for k, v in structured.__dict__.items() if not k.startswith("_")
            }
        else:
            structured_dict = structured

        # Create DB record
        package = await self._material_package_service.create_package_record(
            project_id=project_id,
            source_job_id=job_id,
            gcs_base_path=gcs_path,
            extraction_summary=extraction_summary,
            structured_data=structured_dict,
        )

        # Mark package as ready
        await self._material_package_service.mark_ready(
            package.id, extraction_summary, structured_dict
        )

        # Store in context for potential generation dispatch
        ctx["material_package_id"] = package.id
        ctx["material_package_gcs_path"] = gcs_path

        # Create ProjectImage and ProjectFloorPlan DB records
        await self._create_image_records(project_id, gcs_path, ctx)

        logger.info(f"Materialized package {package.id} at {gcs_path}")

        return {
            "material_package_id": str(package.id),
            "gcs_path": gcs_path,
        }

    async def _create_image_records(
        self, project_id: UUID, gcs_path: str, ctx: Dict[str, Any]
    ) -> None:
        """
        Create ProjectImage and ProjectFloorPlan DB records from pipeline context.

        Reads the manifest to find optimized webp images uploaded to GCS,
        then creates corresponding DB records so the project detail API can
        serve them with signed URLs.

        Args:
            project_id: Project UUID
            gcs_path: GCS base path (e.g. "materials/{project_id}")
            ctx: Pipeline context with manifest and floor_plans data
        """
        db = self.job_repo.db

        manifest_obj = ctx.get("manifest")
        if not manifest_obj:
            return

        # Get entries (handle both OutputManifest object and dict)
        if hasattr(manifest_obj, "entries"):
            entries = manifest_obj.entries
        elif isinstance(manifest_obj, dict):
            entries = manifest_obj.get("entries", [])
        else:
            return

        # Helper to read fields from ManifestEntry dataclass or dict
        def _e(entry, key, default=""):
            if hasattr(entry, key):
                return getattr(entry, key)
            if isinstance(entry, dict):
                return entry.get(key, default)
            return default

        # Create ProjectImage records from manifest
        seen_images = set()
        image_order = 0
        for entry in entries:
            e_tier = _e(entry, "tier")
            e_fmt = _e(entry, "format")
            e_cat = _e(entry, "category")
            e_fname = _e(entry, "file_name")

            # Only process llm_optimized webp (matches what persist_to_gcs uploads)
            if e_tier != "llm_optimized" or e_fmt != "webp":
                continue

            # De-duplicate by base filename
            base_name = e_fname.rsplit(".", 1)[0] if "." in e_fname else e_fname
            if base_name in seen_images:
                continue
            seen_images.add(base_name)

            # Map category string to ImageCategory enum
            try:
                cat_enum = ImageCategory(e_cat)
            except ValueError:
                continue

            # Floor plans are handled separately below
            if cat_enum == ImageCategory.FLOOR_PLAN:
                continue

            gcs_image_path = f"{gcs_path}/images/{e_fname}"

            raw_alt = _e(entry, "alt_text", None) or None
            img_record = ProjectImage(
                project_id=project_id,
                category=cat_enum,
                image_url=gcs_image_path,
                thumbnail_url=gcs_image_path,
                alt_text=raw_alt[:500] if raw_alt else None,
                filename=e_fname[:255] if e_fname else None,
                width=_e(entry, "width", None),
                height=_e(entry, "height", None),
                file_size=_e(entry, "file_size", None),
                format="webp",
                display_order=image_order,
            )
            db.add(img_record)
            image_order += 1

        # Create ProjectFloorPlan records
        floor_plans_data = ctx.get("floor_plans")
        fp_list = []
        if hasattr(floor_plans_data, "floor_plans"):
            fp_list = floor_plans_data.floor_plans
        elif isinstance(floor_plans_data, dict):
            fp_list = floor_plans_data.get("floor_plans", [])

        # Get floor plan image entries from manifest (optimized webp only)
        fp_image_entries = [
            e
            for e in entries
            if _e(e, "category") == "floor_plan"
            and _e(e, "tier") == "llm_optimized"
            and _e(e, "format") == "webp"
        ]

        for i, fp_data in enumerate(fp_list):
            unit_type = _e(fp_data, "unit_type", f"Unit {i + 1}")
            bedrooms = _e(fp_data, "bedrooms", None)
            bathrooms = _e(fp_data, "bathrooms", None)
            total_sqft = _e(fp_data, "total_sqft", None)
            balcony_sqft = _e(fp_data, "balcony_sqft", None)
            builtup_sqft = _e(fp_data, "builtup_sqft", None)

            # Match with image by index position
            if i < len(fp_image_entries):
                fname = _e(fp_image_entries[i], "file_name")
                fp_image_url = f"{gcs_path}/images/{fname}"
            else:
                continue  # Skip floor plans without images

            fp_record = ProjectFloorPlan(
                project_id=project_id,
                unit_type=unit_type or f"Unit {i + 1}",
                bedrooms=int(bedrooms) if bedrooms is not None else None,
                bathrooms=int(bathrooms) if bathrooms is not None else None,
                total_sqft=total_sqft,
                balcony_sqft=balcony_sqft,
                builtup_sqft=builtup_sqft,
                image_url=fp_image_url,
                display_order=i,
                parsed_data={
                    "room_dimensions": _e(fp_data, "room_dimensions", None),
                    "features": _e(fp_data, "features", []),
                    "confidence": _e(fp_data, "confidence", 0.0),
                    "sources": {
                        "unit_type": _e(fp_data, "unit_type_source", ""),
                        "total_sqft": _e(fp_data, "total_sqft_source", ""),
                    },
                },
            )
            db.add(fp_record)

        await db.flush()
        logger.info(
            f"Created {image_order} ProjectImage and {min(len(fp_list), len(fp_image_entries))} "
            f"ProjectFloorPlan records for project {project_id}"
        )

    async def _step_load_material_package(self, job_id: UUID) -> Dict[str, Any]:
        """
        Load MaterialPackage from GCS into pipeline context.

        This is the first step for GENERATION jobs. Populates the context
        with structured_data, extracted_text, etc. from the source package.

        Args:
            job_id: Job UUID

        Returns:
            Dict with material_package_id and structured_data_keys

        Raises:
            ValueError: If job has no material_package_id or package is not ready
        """
        from app.models.enums import MaterialPackageStatus

        job = await self.job_repo.get_job(job_id)

        if not job or not job.material_package_id:
            raise ValueError(f"Generation job {job_id} has no material_package_id")

        # Get package record
        package = await self._material_package_service.get_by_id(
            job.material_package_id
        )
        if not package:
            raise ValueError(f"MaterialPackage {job.material_package_id} not found")

        if package.status != MaterialPackageStatus.READY:
            raise ValueError(
                f"MaterialPackage {package.id} is not ready (status={package.status})"
            )

        # Load from GCS
        package_data = await self._material_package_service.load_from_gcs(
            package.gcs_base_path
        )

        # Populate pipeline context
        ctx = self._pipeline_ctx.setdefault(job_id, {})
        ctx["structured_data"] = package_data.get("structured_data", {})
        ctx["extraction"] = {
            "pages": package_data.get("extracted_text", {}).get("pages", {})
        }
        ctx["floor_plans"] = package_data.get("floor_plans", {})
        ctx["manifest"] = package_data.get("manifest", {})
        ctx["material_package_id"] = package.id
        ctx["material_package_gcs_path"] = package.gcs_base_path

        logger.info(
            f"Loaded MaterialPackage {package.id} into context for job {job_id}"
        )

        return {
            "material_package_id": str(package.id),
            "structured_data_keys": list(ctx["structured_data"].keys()),
        }

    def _release_extraction_originals(self, job_id: UUID) -> None:
        """
        Release original image bytes from extraction to free memory.

        Called after watermark removal when cleaned_images holds all the
        processed bytes we need. The original high-resolution bytes in
        extraction.embedded and extraction.page_renders are no longer needed.

        This can free ~50% of image memory for large PDFs.
        """
        ctx = self._pipeline_ctx.get(job_id, {})
        extraction = ctx.get("extraction")
        if extraction is None:
            return

        released_count = 0

        # Release originals from embedded images
        for image in extraction.embedded:
            if hasattr(image, "release_original"):
                image.release_original()
                released_count += 1

        # Release originals from page renders
        for image in extraction.page_renders:
            if hasattr(image, "release_original"):
                image.release_original()
                released_count += 1

        if released_count > 0:
            logger.info(
                f"Released original bytes from {released_count} images for job {job_id}",
                extra={"job_id": str(job_id), "released_count": released_count},
            )

    # ------------------------------------------------------------------
    # Phase 3: Content Generation step implementations
    # ------------------------------------------------------------------

    async def _step_extract_data(self, job_id: UUID) -> Dict[str, Any]:
        """Extract text from PDF pages using hybrid approach.

        1. Native text layer from PDFProcessor (lossless, free)
        2. Vision OCR only for visual/graphic-heavy pages
        3. Per-page routing based on native text char count
        """
        from app.services.vision_extractor import VisionExtractor

        ctx = self._pipeline_ctx.get(job_id, {})
        extraction = ctx.get("extraction")
        if extraction is None:
            raise RuntimeError("No extraction result available")

        page_renders = extraction.page_renders
        if not page_renders:
            raise RuntimeError("No page renders available for extraction")

        # Native text from PDFProcessor (already populated in triple extraction)
        page_text_map = getattr(extraction, "page_text_map", {}) or {}
        page_char_counts = getattr(extraction, "page_char_counts", {}) or {}

        extractor = VisionExtractor()
        page_results = await extractor.extract_pages(
            page_renders,
            page_text_map=page_text_map,
            page_char_counts=page_char_counts,
        )

        ctx["page_extraction_results"] = page_results

        # Merge: native text for text-rich pages, Vision text for visual pages
        merged_text_map = dict(page_text_map)
        for r in page_results:
            if r.page_number not in merged_text_map and r.raw_text:
                merged_text_map[r.page_number] = r.raw_text
        extraction.page_text_map = merged_text_map

        # Concatenate all page text for downstream structuring
        full_text = VisionExtractor.concatenate_page_text(page_results)
        ctx["vision_full_text"] = full_text

        total_cost = sum(r.cost for r in page_results)
        total_pages = len(page_results)
        text_rich_count = sum(
            1 for pn in page_char_counts if page_char_counts[pn] >= 200
        )

        # Confidence profile: flag when PDF has no native text layer
        # (flattened/scanned) -- cross-validation cannot independently verify numbers
        if total_pages > 0 and text_rich_count == 0:
            ctx["pdf_confidence_profile"] = "low"
            logger.warning(
                "All-visual PDF detected for job %s: 0/%d pages have native text. "
                "Cross-validation will rely solely on Vision OCR -- "
                "numeric accuracy cannot be independently verified.",
                job_id,
                total_pages,
            )
        elif total_pages > 0 and text_rich_count < total_pages * 0.5:
            ctx["pdf_confidence_profile"] = "mixed"
            logger.info(
                "Partially-visual PDF for job %s: %d/%d pages have native text.",
                job_id,
                text_rich_count,
                total_pages,
            )
        else:
            ctx["pdf_confidence_profile"] = "high"

        return {
            "pages_extracted": total_pages,
            "text_rich_pages": text_rich_count,
            "vision_pages": total_pages - text_rich_count,
            "total_chars": len(full_text),
            "total_cost": total_cost,
            "confidence_profile": ctx["pdf_confidence_profile"],
        }

    def _extract_project_name_from_images(
        self, classified_images: list
    ) -> Optional[str]:
        """
        Extract project name from classified image alt_text.

        Looks for project name mentions in logo and master plan alt_text.
        Returns the most frequently mentioned candidate name.
        """
        import re
        from collections import Counter

        candidates: list[str] = []

        for img, cls_result in classified_images:
            alt = cls_result.alt_text or ""
            cat = cls_result.category.value

            if cat == "logo" and alt:
                # "ProjectName logo" or "ProjectName project logo"
                match = re.search(
                    r"^([A-Z][A-Za-z\s]+?)(?:\s+(?:project\s+)?logo)",
                    alt,
                    re.IGNORECASE,
                )
                if match:
                    candidates.append(match.group(1).strip())

            if cat == "master_plan" and alt:
                # "view of X development"
                match = re.search(
                    r"(?:view of|aerial view of)\s+([A-Z][A-Za-z\s]+?)(?:\s+development)",
                    alt,
                    re.IGNORECASE,
                )
                if match:
                    candidates.append(match.group(1).strip())

                # "showing ProjectName area" -- common in master plan descriptions
                match = re.search(
                    r"showing\s+([A-Z][A-Za-z\s]+?)\s+(?:area|zone|phase|section|district)\b",
                    alt,
                    re.IGNORECASE,
                )
                if match:
                    candidates.append(match.group(1).strip())

        if not candidates:
            return None

        # Return the most common candidate
        counts = Counter(candidates)
        best, _ = counts.most_common(1)[0]
        logger.debug(
            "Image-derived project name candidates: %s -> best=%r",
            dict(counts),
            best,
        )
        return best

    async def _step_structure_data(self, job_id: UUID) -> Dict[str, Any]:
        """Structure extracted text into StructuredProject using hybrid approach.

        1. Run DataExtractor regex pass on native text (free, high-confidence anchors)
        2. Run TableExtractor on PDF bytes (exact table values)
        3. Feed pre_extracted hints to DataStructurer for LLM structuring
        4. Cross-validate numeric fields between sources
        """
        from app.services.data_extractor import DataExtractor
        from app.services.data_structurer import DataStructurer
        from app.services.table_extractor import TableExtractor

        ctx = self._pipeline_ctx.get(job_id, {})
        full_text = ctx.get("vision_full_text", "")
        extraction = ctx.get("extraction")

        if not full_text:
            raise RuntimeError("No extracted text available for structuring")

        job = await self.job_repo.get_job(job_id)
        template_type = job.template_type.value if job else "aggregators"

        # Layer 1: Regex pre-extraction on native text (free, no API calls)
        page_text_map = getattr(extraction, "page_text_map", {}) or {}
        regex_extractor = DataExtractor()
        regex_result = regex_extractor.extract(page_text_map)
        ctx["data_extraction"] = regex_result  # for enrichment step backward compat

        # Build pre_extracted dict from high-confidence regex results
        pre_extracted: Dict[str, Any] = {}
        if regex_result.developer.value and regex_result.developer.confidence >= 0.6:
            pre_extracted["developer"] = regex_result.developer.value
        if (
            regex_result.project_name.value
            and regex_result.project_name.confidence >= 0.6
        ):
            pre_extracted["project_name"] = regex_result.project_name.value
        if regex_result.location.emirate:
            pre_extracted["emirate"] = regex_result.location.emirate
        if regex_result.location.community:
            pre_extracted["community"] = regex_result.location.community
        if regex_result.prices.min_price:
            pre_extracted["price_min"] = regex_result.prices.min_price
        if regex_result.prices.max_price:
            pre_extracted["price_max"] = regex_result.prices.max_price
        if regex_result.bedrooms:
            pre_extracted["bedrooms"] = regex_result.bedrooms
        if regex_result.completion_date.value:
            pre_extracted["handover_date"] = regex_result.completion_date.value
        if regex_result.payment_plan.down_payment_pct is not None:
            pp: Dict[str, str] = {
                "down_payment": f"{regex_result.payment_plan.down_payment_pct}%",
            }
            if regex_result.payment_plan.during_construction_pct is not None:
                pp["during_construction"] = (
                    f"{regex_result.payment_plan.during_construction_pct}%"
                )
            if regex_result.payment_plan.on_handover_pct is not None:
                pp["on_handover"] = (
                    f"{regex_result.payment_plan.on_handover_pct}%"
                )
            pre_extracted["payment_plan"] = pp

        # Layer 2: Table extraction on original PDF bytes (free, exact values)
        pdf_bytes = ctx.get("pdf_bytes")
        table_result = None
        if pdf_bytes:
            table_extractor = TableExtractor()
            table_result = table_extractor.extract_tables(pdf_bytes)
            ctx["table_extraction"] = table_result

            # Merge floor plan specs into pre_extracted
            if table_result.floor_plan_specs:
                pre_extracted["_floor_plan_specs"] = table_result.floor_plan_specs
                areas = [
                    fp["total_sqft"]
                    for fp in table_result.floor_plan_specs
                    if fp.get("total_sqft")
                ]
                if areas:
                    pre_extracted["_area_range_sqft"] = {
                        "min": min(areas),
                        "max": max(areas),
                    }

            # Merge payment plan from tables
            if table_result.payment_plan and not pre_extracted.get("payment_plan"):
                pre_extracted["payment_plan"] = table_result.payment_plan

        logger.info(
            "Pre-extraction: %d regex hints, tables=%s",
            len(pre_extracted),
            "yes" if table_result and table_result.tables else "no",
        )

        # Layer 3: LLM structuring with pre_extracted hints
        structurer = DataStructurer()
        structured = await structurer.structure(
            markdown_text=full_text,
            template_type=template_type,
            pre_extracted=pre_extracted,
        )

        # Layer 4: Cross-validation reconciliation
        from app.services.cross_validator import CrossValidator

        validator = CrossValidator()
        table_hints: Dict[str, Any] = {}
        structured, flags = validator.reconcile_project(
            structured, pre_extracted, table_hints
        )
        if flags:
            logger.warning(
                "Cross-validation flags for job %s: %s",
                job_id,
                [(f.field, f.details) for f in flags],
            )
        ctx["cross_validation_flags"] = flags
        ctx["structured_data"] = structured

        # Update regex_result extraction_method to hybrid
        regex_result.extraction_method = "hybrid"

        # Warn when cross-validation has no independent verification
        confidence_profile = ctx.get("pdf_confidence_profile", "high")
        if confidence_profile == "low":
            logger.warning(
                "Low-confidence extraction for job %s: flattened/scanned PDF. "
                "All numeric values come from Vision OCR with no native text "
                "cross-check. Manual review recommended for: %s",
                job_id,
                ", ".join(
                    f
                    for f in ("price_min", "price_max", "price_per_sqft")
                    if getattr(structured, f, None) is not None
                )
                or "no numeric fields found",
            )

        return {
            "project_name": structured.project_name,
            "developer": structured.developer,
            "pre_extracted_fields": len(pre_extracted),
            "confidence_profile": confidence_profile,
        }

    async def _step_enrich_from_classification(self, job_id: UUID) -> Dict[str, Any]:
        """
        Post-convergence enrichment: enrich text-branch outputs with image-branch data.

        Runs after both the image branch and text branch have completed.

        1. If BOTH regex and structurer returned no project_name, try to
           extract it from classification alt_text (logo/master_plan images).
        2. If structured_data has low confidence AND the source text was
           very sparse (< 100 chars), re-run structuring with image
           alt_text appended -- but clearly labeled as AI-generated descriptions
           so the structurer does not treat them as document content.
        """
        from app.services.data_extractor import FieldResult

        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        ctx = self._pipeline_ctx.get(job_id, {})
        classification = ctx.get("classification")
        data_extraction = ctx.get("data_extraction")
        structured_data = ctx.get("structured_data")
        enrichments = []

        # Enrichment 1: project name from image alt_text (fallback only)
        # Only fires when BOTH regex and structurer returned no project_name.
        # Never overrides a name the structurer already found.
        regex_name = (
            data_extraction.project_name.value
            if data_extraction and data_extraction.project_name
            else None
        )
        structured_name = (
            _get(structured_data, "project_name") if structured_data else None
        )
        image_name = None
        if classification and hasattr(classification, "classified_images"):
            image_name = self._extract_project_name_from_images(
                classification.classified_images
            )

        if not regex_name and not structured_name:
            # Case (a): no name from text at all -- use image name
            if image_name:
                logger.info(
                    "Enrichment: project_name from image alt_text (no text source): %s",
                    image_name,
                )
                data_extraction.project_name = FieldResult(
                    value=image_name, confidence=0.5, source="image_alt_text", page=1
                )
                enrichments.append("project_name from image alt_text")

        # Enrichment 2: re-structure if text was too sparse
        # Skip if extraction was Vision-based (Vision already saw the full page content)
        extraction_method = (
            getattr(data_extraction, "extraction_method", "") if data_extraction else ""
        )
        if extraction_method != "vision":
            full_text = data_extraction.full_text if data_extraction else ""
            if len((full_text or "").strip()) < 100:
                if classification and hasattr(classification, "classified_images"):
                    alt_texts = [
                        f"[{c.category.value}] {c.alt_text}"
                        for _, c in classification.classified_images
                        if c.alt_text
                    ]
                    if alt_texts:
                        from app.services.data_structurer import DataStructurer

                        enriched_text = (
                            (full_text or "")
                            + "\n\nNOTE: The following are AI-generated image descriptions, NOT text from the document. "
                            + "Use them only to identify the project/developer name if not found above. "
                            + "Do NOT treat amenities, features, or locations from these descriptions as factual:\n"
                            + "\n".join(alt_texts)
                        )
                        job = await self.job_repo.get_job(job_id)
                        template_type = (
                            job.template_type.value if job else "aggregators"
                        )
                        structurer = DataStructurer()
                        ctx["structured_data"] = await structurer.structure(
                            enriched_text, template_type=template_type
                        )
                        enrichments.append("re-structured with image alt_text")
                        logger.info(
                            "Enrichment: re-structured sparse text with %d image alt_texts",
                            len(alt_texts),
                        )

        return {"enrichments": enrichments, "count": len(enrichments)}

    # ------------------------------------------------------------------
    # Tiered context builders for generation
    # ------------------------------------------------------------------

    def _build_base_context(
        self,
        structured,
        floor_plans: Any = None,
        manifest: Any = None,
    ) -> Dict[str, Any]:
        """
        Build Tier 1 (base) context from StructuredProject + floor plans + manifest.

        Includes all 19 StructuredProject fields, a floor plan summary, and
        image manifest metadata. Used for short-form fields (meta_title, h1_tag, etc.).
        """
        import dataclasses

        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        ctx = {
            # Core fields
            "project_name": _get(structured, "project_name"),
            "developer": _get(structured, "developer"),
            "emirate": _get(structured, "emirate"),
            "community": _get(structured, "community"),
            "sub_community": _get(structured, "sub_community"),
            "property_type": _get(structured, "property_type"),
            # Pricing
            "price_min": _get(structured, "price_min"),
            "price_max": _get(structured, "price_max"),
            "currency": _get(structured, "currency"),
            "price_per_sqft": _get(structured, "price_per_sqft"),
            # Specs
            "bedrooms": _get(structured, "bedrooms"),
            "total_units": _get(structured, "total_units"),
            "floors": _get(structured, "floors"),
            # Dates
            "handover_date": _get(structured, "handover_date"),
            "launch_date": _get(structured, "launch_date"),
            # Features
            "amenities": _get(structured, "amenities"),
            "key_features": _get(structured, "key_features"),
            # Payment
            "payment_plan": _get(structured, "payment_plan"),
            # Meta
            "description": _get(structured, "description"),
        }

        # Floor plan summary
        fp_summary = {
            "count": 0,
            "unit_types": [],
            "sqft_range": "N/A",
            "bedroom_counts": [],
        }
        if floor_plans:
            fp_list = []
            if isinstance(floor_plans, dict):
                fp_list = floor_plans.get("floor_plans", [])
            elif isinstance(floor_plans, list):
                fp_list = floor_plans
            elif hasattr(floor_plans, "floor_plans"):
                fp_list = floor_plans.floor_plans
                # Convert dataclass items to dicts if needed
                if fp_list and hasattr(fp_list[0], "__dataclass_fields__"):
                    fp_list = [dataclasses.asdict(fp) for fp in fp_list]

            unit_types = set()
            sqfts = []
            bedroom_counts = set()
            for fp in fp_list:
                if isinstance(fp, dict):
                    ut = fp.get("unit_type")
                    if ut:
                        unit_types.add(ut)
                    sqft = fp.get("total_sqft")
                    if sqft:
                        sqfts.append(float(sqft))
                    br = fp.get("bedrooms")
                    if br is not None:
                        if isinstance(br, list):
                            bedroom_counts.update(br)
                        else:
                            bedroom_counts.add(br)

            sqft_range = "N/A"
            if sqfts:
                if len(sqfts) == 1:
                    sqft_range = f"{sqfts[0]:,.0f} sqft"
                else:
                    sqft_range = f"{min(sqfts):,.0f} - {max(sqfts):,.0f} sqft"

            fp_summary = {
                "count": len(fp_list),
                "unit_types": sorted(unit_types),
                "sqft_range": sqft_range,
                "bedroom_counts": sorted(bedroom_counts),
            }

        ctx["floor_plan_summary"] = fp_summary

        # Image manifest metadata
        image_metadata = {"total_images": 0, "categories": {}}
        if manifest:
            entries = []
            if isinstance(manifest, dict):
                entries = manifest.get("entries", [])
            elif isinstance(manifest, list):
                entries = manifest

            categories: Dict[str, int] = {}
            alt_texts_by_cat: Dict[str, list[str]] = {}
            for entry in entries:
                if isinstance(entry, dict):
                    cat = entry.get("category", "unknown")
                    categories[cat] = categories.get(cat, 0) + 1
                    alt = entry.get("alt_text", "")
                    if alt and cat != "other":
                        alt_texts_by_cat.setdefault(cat, []).append(alt)

            image_metadata = {
                "total_images": len(entries),
                "categories": categories,
            }

        ctx["image_metadata"] = image_metadata
        ctx["image_descriptions"] = self._format_image_descriptions(
            alt_texts_by_cat if manifest else {}
        )

        non_null = sum(
            1
            for k, v in ctx.items()
            if v is not None and k not in ("floor_plan_summary", "image_metadata")
        )
        logger.info(
            "Generation base context built: %d keys (%d non-null structured fields)",
            len(ctx),
            non_null,
        )

        return ctx

    def _build_rich_context(
        self,
        base_ctx: Dict[str, Any],
        extraction_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build Tier 2 (rich) context by adding full extracted text to base context.

        Used for paragraph/description fields that benefit from source PDF text.
        """
        rich = dict(base_ctx)

        extracted_text = ""
        if isinstance(extraction_data, dict):
            pages = (
                extraction_data.get("pages")
                or extraction_data.get("text_by_page")
                or {}
            )
            if isinstance(pages, dict):
                for page_num in sorted(
                    pages.keys(), key=lambda x: int(x) if str(x).isdigit() else 0
                ):
                    extracted_text += pages[page_num] + "\n\n"
            elif isinstance(pages, list):
                extracted_text = "\n\n".join(str(p) for p in pages)
            # Fallback: extraction_data might have a "full_text" or "text" key
            if not extracted_text.strip():
                extracted_text = extraction_data.get(
                    "full_text", ""
                ) or extraction_data.get("text", "")

        rich["extracted_text"] = extracted_text.strip()

        logger.info(
            "Generation rich context built: base + %d chars of extracted text",
            len(rich["extracted_text"]),
        )

        return rich

    @staticmethod
    def _needs_rich_context(field_name: str, char_limit: int | None) -> bool:
        """Return True if the field should receive Tier 2 (rich) context."""
        if char_limit and char_limit > 300:
            return True
        rich_keywords = ("paragraph", "description", "about", "overview")
        return any(kw in field_name for kw in rich_keywords)

    @staticmethod
    def _format_image_descriptions(alt_texts_by_cat: Dict[str, list[str]]) -> str:
        """Format image alt_text strings into a compact visual context block.

        Groups by category in display order, deduplicates exact matches,
        and caps at 5 descriptions per category to limit token usage.

        Returns empty string if no alt_text data is available.
        """
        if not alt_texts_by_cat:
            return ""

        display_order = [
            ("interior", "Interior spaces"),
            ("exterior", "Exterior / facade"),
            ("amenity", "Amenities"),
            ("master_plan", "Master plan"),
            ("location_map", "Location"),
            ("floor_plan", "Floor plans"),
            ("logo", "Branding"),
        ]
        max_per_cat = 5
        lines: list[str] = []

        for cat_key, cat_label in display_order:
            texts = alt_texts_by_cat.get(cat_key, [])
            if not texts:
                continue
            # Deduplicate exact matches while preserving order
            seen: set[str] = set()
            unique: list[str] = []
            for t in texts:
                if t not in seen:
                    seen.add(t)
                    unique.append(t)
            unique = unique[:max_per_cat]
            lines.append(f"- {cat_label}: {'; '.join(unique)}")

        # Include any categories not in display_order
        known_keys = {k for k, _ in display_order}
        for cat_key in sorted(alt_texts_by_cat.keys()):
            if cat_key in known_keys or cat_key == "other":
                continue
            texts = alt_texts_by_cat[cat_key]
            seen_extra: set[str] = set()
            unique_extra: list[str] = []
            for t in texts:
                if t not in seen_extra:
                    seen_extra.add(t)
                    unique_extra.append(t)
            unique_extra = unique_extra[:max_per_cat]
            label = cat_key.replace("_", " ").title()
            lines.append(f"- {label}: {'; '.join(unique_extra)}")

        return "\n".join(lines)

    async def _step_generate_content(self, job_id: UUID) -> Dict[str, Any]:
        """Generate AI content for all fields."""
        from app.services.content_generator import get_content_generator

        ctx = self._pipeline_ctx.get(job_id, {})
        structured = ctx.get("structured_data")
        if structured is None:
            raise RuntimeError("No structured data available")

        job = await self.job_repo.get_job(job_id)
        template_type = job.template_type.value if job else "aggregators"

        # Build tiered context dicts from all available pipeline data
        base_ctx = self._build_base_context(
            structured,
            ctx.get("floor_plans"),
            ctx.get("manifest"),
        )
        rich_ctx = self._build_rich_context(
            base_ctx,
            ctx.get("extraction", {}),
        )

        generator = get_content_generator(db=self.job_repo.db)

        # Progress callback that updates both message AND numeric progress.
        # generate_content is step 2 of 5 in the generation pipeline,
        # so progress interpolates from 21% (step 1 done) to 40% (step 2 done).
        async def progress_callback(message: str, fraction: float = 0.0):
            step_progress = 21 + int(fraction * 19)
            await self.job_repo.update_job_progress(
                job_id=job_id,
                progress=step_progress,
                current_step="Content Generation",
                progress_message=message,
            )

        content = await generator.generate_all(
            base_context=base_ctx,
            rich_context=rich_ctx,
            template_type=template_type,
            progress_callback=progress_callback,
        )

        ctx["generated_content"] = content
        return {
            "fields_generated": len(content.fields),
            "total_cost": content.total_cost,
            "total_tokens": content.total_token_usage,
            "errors": content.errors,
        }

    async def _step_populate_sheet(self, job_id: UUID) -> Dict[str, Any]:
        """Populate Google Sheet with generated content."""
        from app.services.sheets_manager import SheetsManager

        ctx = self._pipeline_ctx.get(job_id, {})
        content = ctx.get("generated_content")
        structured = ctx.get("structured_data")
        if content is None:
            raise RuntimeError("No generated content available")

        job = await self.job_repo.get_job(job_id)
        template_type = job.template_type.value if job else "aggregators"

        def _get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        project_name = (
            _get(structured, "project_name", "Untitled") if structured else "Untitled"
        )

        manager = SheetsManager()

        # Create project sheet from template
        sheet_result = await manager.create_project_sheet(
            project_name=project_name,
            template_type=template_type,
        )

        # Build content dict from generated fields
        content_dict = {name: field.content for name, field in content.fields.items()}

        # Add structured data fields
        if structured:
            content_dict["project_name"] = _get(structured, "project_name") or ""
            content_dict["developer"] = _get(structured, "developer") or ""
            location_parts = [
                _get(structured, "community"),
                _get(structured, "emirate"),
            ]
            content_dict["location"] = ", ".join(p for p in location_parts if p)
            price_min = _get(structured, "price_min")
            if price_min:
                try:
                    price_val = (
                        float(price_min) if isinstance(price_min, str) else price_min
                    )
                    content_dict["starting_price"] = f"AED {price_val:,.0f}"
                except (ValueError, TypeError):
                    content_dict["starting_price"] = str(price_min)
            else:
                content_dict["starting_price"] = ""
            bedrooms = _get(structured, "bedrooms")
            if bedrooms:
                if isinstance(bedrooms, (list, tuple)):
                    content_dict["bedrooms"] = ", ".join(str(b) for b in bedrooms)
                else:
                    content_dict["bedrooms"] = str(bedrooms)
            else:
                content_dict["bedrooms"] = ""
            content_dict["completion_date"] = _get(structured, "handover_date") or ""
            content_dict["property_type"] = _get(structured, "property_type") or ""

        # Populate sheet
        populate_result = await manager.populate_sheet(
            sheet_id=sheet_result.sheet_id,
            content=content_dict,
            template_type=template_type,
        )

        ctx["sheet_result"] = sheet_result
        ctx["populate_result"] = populate_result

        return {
            "sheet_id": sheet_result.sheet_id,
            "sheet_url": sheet_result.sheet_url,
            "fields_written": populate_result.fields_written,
            "fields_failed": populate_result.fields_failed,
        }

    async def _step_upload_cloud(self, job_id: UUID) -> Dict[str, Any]:
        """Upload images and raw data to Google Drive project structure.

        Uploads directly to Images/ and Raw Data/ folders without creating a ZIP.
        This eliminates redundant uploads (previously both ZIP and extracted images
        were uploaded).
        """
        import io
        import os
        import zipfile

        from app.integrations.drive_client import drive_client

        ctx = self._pipeline_ctx.get(job_id, {})

        # Get required data from context
        zip_bytes = ctx.get("zip_bytes")
        if zip_bytes is None:
            raise RuntimeError("No ZIP bytes available in pipeline context")

        sheet_result = ctx.get("sheet_result")
        if sheet_result is None:
            raise RuntimeError("No sheet result available in pipeline context")

        structured = ctx.get("structured_data")
        if isinstance(structured, dict):
            project_name = structured.get("project_name", "Untitled Project")
        elif structured is not None:
            project_name = getattr(structured, "project_name", "Untitled Project")
        else:
            project_name = "Untitled Project"

        # Get original PDF bytes and path for Source folder upload
        pdf_bytes = ctx.get("pdf_bytes")
        pdf_path = ctx.get("pdf_path", "")
        source_filename = (
            os.path.basename(pdf_path.replace("file://", ""))
            if pdf_path
            else "brochure.pdf"
        )

        logger.info(f"Uploading assets for project '{project_name}' (job_id={job_id})")

        # 1. Create project folder structure in Shared Drive
        folder_structure = await drive_client.create_project_structure(
            project_name=project_name
        )

        logger.info(
            f"Created folder structure for '{project_name}': {folder_structure}"
        )

        # 2. Extract images and raw data files from ZIP
        organized_images: list[tuple[str, bytes]] = []
        raw_data_files: list[tuple[str, bytes]] = []
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
                for name in zf.namelist():
                    # Image files go to Images/
                    if name.startswith(
                        ("original/", "optimized/")
                    ) and name.lower().endswith((".webp", ".jpg", ".jpeg", ".png")):
                        organized_images.append((name, zf.read(name)))
                    # Non-image files go to Raw Data/
                    elif name.lower().endswith((".json",)):
                        raw_data_files.append((name, zf.read(name)))
            logger.info(
                f"Extracted {len(organized_images)} images and {len(raw_data_files)} "
                f"raw data files from package"
            )
        except zipfile.BadZipFile as e:
            logger.warning(f"Failed to extract from package: {e}")

        # 3. Upload to project folders (no ZIP upload - direct files only)
        upload_result = await drive_client.upload_to_project(
            project_structure=folder_structure,
            source_pdf=pdf_bytes,
            source_filename=source_filename,
            organized_images=organized_images,
            raw_data_files=raw_data_files,
        )

        images_uploaded = upload_result.get("images_uploaded", 0)
        raw_data_uploaded = upload_result.get("raw_data_uploaded", 0)

        logger.info(
            f"Uploaded source PDF, {images_uploaded} images, and {raw_data_uploaded} "
            f"raw data files to project folders"
        )

        # 4. Move Google Sheet to project folder
        await drive_client.move_file(
            file_id=sheet_result.sheet_id,
            destination_folder_id=folder_structure["project"],
        )

        logger.info(
            f"Moved Google Sheet (ID: {sheet_result.sheet_id}) to project folder"
        )

        # 5. Get file metadata for URLs
        sheet_metadata = await drive_client.get_file_metadata(sheet_result.sheet_id)

        # 6. Store results in context for job completion
        ctx["drive_upload"] = {
            "folder_structure": folder_structure,
            "sheet_url": sheet_metadata.get("webViewLink"),
            "images_uploaded": images_uploaded,
            "raw_data_uploaded": raw_data_uploaded,
        }

        return {
            "project_folder_id": folder_structure["project"],
            "sheet_url": sheet_metadata.get("webViewLink"),
            "source_pdf_uploaded": pdf_bytes is not None,
            "images_uploaded": images_uploaded,
            "raw_data_uploaded": raw_data_uploaded,
        }

    async def _create_project_from_extraction(self, job_id: UUID):
        """
        Create Project record from extraction pipeline context.

        Extracts project metadata from structured_data and creates a Project
        in DRAFT status. Used by extraction pipeline before materialization
        so it can be linked to the MaterialPackage.

        Args:
            job_id: Job UUID

        Returns:
            Created Project instance

        Note: This is similar to the project creation in _step_finalize but
        without the content generation results. The project is created early
        so it can be linked to the MaterialPackage.
        """
        from app.models.database import Project
        from app.models.enums import WorkflowStatus

        ctx = self._pipeline_ctx.get(job_id, {})
        job = await self.job_repo.get_job(job_id)
        structured = ctx.get("structured_data")

        # Handle both dataclass/object and dict formats
        if structured is None:
            structured = {}

        def get_field(name: str, default=None):
            """Get field from structured data (handles both obj and dict)."""
            if hasattr(structured, name):
                return getattr(structured, name, default)
            elif isinstance(structured, dict):
                return structured.get(name, default)
            return default

        # Extract fields
        project_name = get_field("project_name", "Untitled Project")
        developer = get_field("developer")
        emirate = get_field("emirate")
        community = get_field("community")
        property_type = get_field("property_type")
        price_min = get_field("price_min")
        price_max = get_field("price_max")
        price_per_sqft = get_field("price_per_sqft")
        bedrooms = get_field("bedrooms", [])
        amenities = get_field("amenities", [])
        handover_date = get_field("handover_date")
        payment_plan = get_field("payment_plan")
        key_features = get_field("key_features", [])
        description = get_field("description")
        total_units = get_field("total_units")
        floors = get_field("floors")

        # Build location string
        location_parts = [community, emirate]
        location = ", ".join(p for p in location_parts if p) or None

        # Build property types list
        property_types = [property_type] if property_type else []

        # Create project record
        project = Project(
            name=project_name,
            developer=developer,
            location=location,
            emirate=emirate,
            starting_price=price_min,
            price_per_sqft=price_per_sqft,
            payment_plan=str(payment_plan) if payment_plan else None,
            description=description,
            property_types=property_types,
            unit_sizes=bedrooms or [],
            amenities=amenities or [],
            features=key_features or [],
            total_units=total_units,
            floors=floors,
            workflow_status=WorkflowStatus.DRAFT,
            created_by=job.user_id if job else None,
            last_modified_by=job.user_id if job else None,
            processing_job_id=job_id,
        )

        db = self.job_repo.db
        db.add(project)
        await db.flush()
        await db.refresh(project)

        logger.info(
            f"Created project '{project_name}' (id={project.id}) from extraction job {job_id}"
        )

        return project

    async def _step_finalize(self, job_id: UUID) -> Dict[str, Any]:
        """Create Project record from pipeline context and link to job."""
        from app.models.database import Project
        from app.models.enums import WorkflowStatus

        ctx = self._pipeline_ctx.get(job_id, {})
        structured = ctx.get("structured_data")
        content = ctx.get("generated_content")
        drive_upload = ctx.get("drive_upload", {})
        sheet_result = ctx.get("sheet_result")

        job = await self.job_repo.get_job(job_id)
        if job is None:
            raise RuntimeError(f"Job {job_id} not found")

        # Build project fields from structured data
        project_name = "Untitled Project"
        developer = None
        location = None
        emirate = None
        starting_price = None
        price_per_sqft = None
        payment_plan = None
        description = None
        property_types = []
        unit_sizes = []
        amenities = []
        features = []
        total_units = None
        floors = None

        if structured:

            def _get(obj, key, default=None):
                if isinstance(obj, dict):
                    return obj.get(key, default)
                return getattr(obj, key, default)

            project_name = _get(structured, "project_name") or project_name
            developer = _get(structured, "developer")
            emirate = _get(structured, "emirate")
            location_parts = [
                _get(structured, "community"),
                _get(structured, "emirate"),
            ]
            location = ", ".join(p for p in location_parts if p) or None
            starting_price = _get(structured, "price_min")
            price_per_sqft = _get(structured, "price_per_sqft")
            pp = _get(structured, "payment_plan")
            payment_plan = str(pp) if pp else None
            description = _get(structured, "description")
            pt = _get(structured, "property_type")
            property_types = [pt] if pt else []
            unit_sizes = _get(structured, "bedrooms") or []
            amenities = _get(structured, "amenities") or []
            features = _get(structured, "key_features") or []
            total_units = _get(structured, "total_units")
            floors = _get(structured, "floors")

        # Build generated content dict
        generated_content = {}
        if content:
            for name, field in content.fields.items():
                generated_content[name] = {
                    "content": field.content,
                    "character_count": field.character_count,
                    "within_limit": field.within_limit,
                }

        # Resolve URLs
        sheet_url = None
        if sheet_result:
            sheet_url = drive_upload.get("sheet_url") or sheet_result.sheet_url

        # Create project record
        db = self.job_repo.db
        project = Project(
            name=project_name,
            developer=developer,
            location=location,
            emirate=emirate,
            starting_price=starting_price,
            price_per_sqft=price_per_sqft,
            payment_plan=payment_plan,
            description=description,
            property_types=property_types,
            unit_sizes=unit_sizes,
            amenities=amenities,
            features=features,
            total_units=total_units,
            floors=floors,
            processed_zip_url=None,  # ZIP no longer uploaded
            sheet_url=sheet_url,
            generated_content=generated_content,
            workflow_status=WorkflowStatus.DRAFT,
            created_by=job.user_id,
            last_modified_by=job.user_id,
            processing_job_id=job_id,
        )
        db.add(project)
        await db.flush()
        await db.refresh(project)

        logger.info(
            f"Created project '{project_name}' (id={project.id}) for job {job_id}"
        )

        return {
            "project_id": str(project.id),
            "project_name": project_name,
            "developer": developer,
            "sheet_url": sheet_url,
            "images_uploaded": drive_upload.get("images_uploaded", 0),
            "raw_data_uploaded": drive_upload.get("raw_data_uploaded", 0),
            "fields_in_content": len(generated_content),
        }

    async def get_job(self, job_id: UUID) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job instance or None if not found
        """
        return await self.job_repo.get_job(job_id)

    async def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update job status.

        Args:
            job_id: Job ID
            status: New status
            progress: Optional progress percentage
            current_step: Optional current step label
            error_message: Optional error message
        """
        await self.job_repo.update_job_status(
            job_id=job_id,
            status=status,
            progress=progress,
            current_step=current_step,
            error_message=error_message,
        )

    async def get_job_status(self, job_id: UUID) -> Optional[Job]:
        """
        Get current job status with progress details.

        Args:
            job_id: Job ID

        Returns:
            Job instance or None if not found
        """
        return await self.job_repo.get_job(job_id)

    async def get_job_steps(self, job_id: UUID) -> list[JobStep]:
        """
        Get all steps for a job with timing and status.

        Args:
            job_id: Job ID

        Returns:
            List of job steps
        """
        return await self.job_repo.get_job_steps(job_id)

    async def get_user_jobs(
        self,
        user_id: UUID,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """
        Get jobs for a specific user.

        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of jobs
        """
        return await self.job_repo.get_jobs_by_user(
            user_id=user_id, status=status, limit=limit, offset=offset
        )

    async def count_user_jobs(
        self, user_id: UUID, status: Optional[JobStatus] = None
    ) -> int:
        """
        Count jobs for a specific user.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            Total count of matching jobs
        """
        return await self.job_repo.count_user_jobs(user_id=user_id, status=status)

    async def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Clean up jobs older than specified days.

        Args:
            days: Number of days to keep jobs

        Returns:
            Number of jobs cleaned up
        """
        count = await self.job_repo.cleanup_old_jobs(days)
        logger.info(
            f"Cleaned up {count} jobs older than {days} days",
            extra={"count": count, "days": days},
        )
        return count
