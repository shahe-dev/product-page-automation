"""
Task Queue Service

Integrates with Google Cloud Tasks for asynchronous job processing.
Handles task enqueueing, retry policies, and callback handling.
"""

import asyncio
import logging
import json
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from google.api_core import exceptions as gcp_exceptions

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskQueue:
    """
    Manages Cloud Tasks queue for background job processing.

    Responsibilities:
    - Enqueue tasks to Cloud Tasks
    - Configure retry policies
    - Handle task callbacks
    - Manage dead letter queue
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        queue_name: Optional[str] = None,
        api_url: Optional[str] = None,
        internal_api_key: Optional[str] = None
    ):
        """
        Initialize task queue client.

        Args:
            project_id: GCP project ID (defaults to settings)
            location: GCP region (defaults to us-central1)
            queue_name: Cloud Tasks queue name (defaults to pdp-processing-queue)
            api_url: Backend API URL for callbacks
            internal_api_key: Internal API authentication key
        """
        self.project_id = project_id or settings.GCP_PROJECT_ID
        self.location = location or "us-central1"
        self.queue_name = queue_name or "pdp-processing-queue"
        self.api_url = api_url or "http://localhost:8000"
        self.internal_api_key = internal_api_key or settings.INTERNAL_API_KEY

        # Only use Cloud Tasks in production - use local processing for development
        environment = settings.ENVIRONMENT.lower() if settings.ENVIRONMENT else "development"

        if environment == "production":
            try:
                self.client = tasks_v2.CloudTasksClient()
                self.queue_path = self.client.queue_path(
                    self.project_id,
                    self.location,
                    self.queue_name
                )
                logger.info(
                    f"Initialized Cloud Tasks client for queue: {self.queue_path}",
                    extra={"queue_path": self.queue_path}
                )
            except Exception as e:
                logger.warning(
                    f"Cloud Tasks client not available: {str(e)}",
                    extra={"error": str(e)}
                )
                self.client = None
                self.queue_path = None
        else:
            logger.info(
                f"Local dev mode (ENVIRONMENT={environment}): Using local task processing",
                extra={"environment": environment}
            )
            self.client = None
            self.queue_path = None

    async def enqueue_job(
        self,
        job_id: UUID,
        pdf_path: str,
        **kwargs: Any
    ) -> str:
        """
        Enqueue a job processing task to Cloud Tasks.

        Args:
            job_id: Job UUID
            pdf_path: Path to uploaded PDF file (GCS path)
            **kwargs: Additional parameters for processing

        Returns:
            Task name (full resource path)

        Raises:
            Exception: If task creation fails
        """
        # Local dev mode - process directly via HTTP call with error handling
        if self.client is None:
            logger.info(
                f"Local dev mode: Processing job {job_id} directly",
                extra={"job_id": str(job_id), "pdf_path": pdf_path}
            )

            # Wrap in error handler to capture crashes and timeouts
            async def _dev_process_with_error_handling():
                try:
                    await asyncio.wait_for(
                        self._process_local(job_id, pdf_path, **kwargs),
                        timeout=1800  # 30 minute max for job processing
                    )
                except asyncio.TimeoutError:
                    logger.error(
                        f"Job {job_id} timed out after 30 minutes",
                        extra={"job_id": str(job_id)}
                    )
                    await self._mark_job_failed(job_id, "Job timed out after 30 minutes")
                except Exception as e:
                    logger.exception(
                        f"Job {job_id} failed with error: {e}",
                        extra={"job_id": str(job_id), "error": str(e)}
                    )
                    await self._mark_job_failed(job_id, str(e))

            asyncio.create_task(_dev_process_with_error_handling())
            return f"local-dev-task-{job_id}"

        # Prepare task payload
        payload = {
            "job_id": str(job_id),
            "pdf_path": pdf_path,
            **kwargs
        }

        logger.info(
            f"Enqueueing job {job_id} to Cloud Tasks",
            extra={"job_id": str(job_id), "pdf_path": pdf_path}
        )

        # Create HTTP POST task
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{self.api_url}/api/v1/internal/process-job",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Internal-Auth": self.internal_api_key
                },
                "body": json.dumps(payload).encode()
            }
        }

        try:
            # Create task in Cloud Tasks (run sync client in thread pool)
            response = await asyncio.to_thread(
                self.client.create_task,
                request={
                    "parent": self.queue_path,
                    "task": task
                }
            )

            task_name = response.name
            logger.info(
                f"Task created successfully: {task_name}",
                extra={"job_id": str(job_id), "task_name": task_name}
            )

            return task_name

        except gcp_exceptions.GoogleAPIError as e:
            logger.exception(
                f"Google API error enqueueing job {job_id}: {str(e)}",
                extra={"job_id": str(job_id), "error": str(e)}
            )
            raise Exception(f"Failed to enqueue task: {str(e)}")

        except Exception as e:
            logger.exception(
                f"Unexpected error enqueueing job {job_id}: {str(e)}",
                extra={"job_id": str(job_id), "error": str(e)}
            )
            raise

    async def _process_local(
        self,
        job_id: UUID,
        pdf_path: str,
        **kwargs: Any
    ) -> None:
        """
        Process a job locally by calling the internal endpoint directly.
        Used in local dev mode when Cloud Tasks is not available.
        """
        try:
            payload = {
                "job_id": str(job_id),
                "pdf_path": pdf_path,
                **kwargs
            }
            async with httpx.AsyncClient(timeout=1800.0) as client:
                response = await client.post(
                    f"{self.api_url}/api/v1/internal/process-job",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Internal-Auth": self.internal_api_key
                    }
                )
                if response.status_code == 200:
                    logger.info(f"Local dev: Job {job_id} processed successfully")
                else:
                    logger.error(f"Local dev: Job {job_id} failed with status {response.status_code}: {response.text}")
        except Exception as e:
            logger.exception(f"Local dev: Failed to process job {job_id}: {e}")
            raise  # Re-raise so the wrapper can catch and handle

    async def _mark_job_failed(self, job_id: UUID, error_message: str) -> None:
        """
        Mark a job as failed when async processing errors.

        Used by dev mode error handling to record failures that would
        otherwise be silent due to fire-and-forget task creation.
        """
        from app.config.database import async_session_factory
        from app.repositories.job_repository import JobRepository
        from app.models.enums import JobStatus

        try:
            async with async_session_factory() as db:
                job_repo = JobRepository(db)
                await job_repo.update_job_status(
                    job_id=job_id,
                    status=JobStatus.FAILED,
                    error_message=error_message
                )
                logger.info(
                    f"Marked job {job_id} as failed: {error_message}",
                    extra={"job_id": str(job_id)}
                )
        except Exception as e:
            logger.error(
                f"Failed to mark job {job_id} as failed: {e}",
                extra={"job_id": str(job_id), "error": str(e)}
            )

    async def enqueue_delayed_task(
        self,
        job_id: UUID,
        pdf_path: str,
        delay_seconds: int,
        **kwargs: Any
    ) -> str:
        """
        Enqueue a task with a delay (used for retries).

        Args:
            job_id: Job UUID
            pdf_path: Path to uploaded PDF file
            delay_seconds: Delay in seconds before task executes
            **kwargs: Additional parameters

        Returns:
            Task name
        """
        # Local dev mode - skip Cloud Tasks
        if self.client is None:
            logger.info(
                f"Local dev mode: Would enqueue delayed job {job_id} (skipped)",
                extra={"job_id": str(job_id), "delay_seconds": delay_seconds}
            )
            return f"local-dev-delayed-task-{job_id}"

        payload = {
            "job_id": str(job_id),
            "pdf_path": pdf_path,
            **kwargs
        }

        # Calculate schedule time
        import datetime as dt
        schedule_time = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=delay_seconds)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(schedule_time)

        # Create task with schedule time
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{self.api_url}/api/v1/internal/process-job",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Internal-Auth": self.internal_api_key
                },
                "body": json.dumps(payload).encode()
            },
            "schedule_time": timestamp
        }

        try:
            # Create task in Cloud Tasks (run sync client in thread pool)
            response = await asyncio.to_thread(
                self.client.create_task,
                request={
                    "parent": self.queue_path,
                    "task": task
                }
            )

            logger.info(
                f"Delayed task created for job {job_id} (delay: {delay_seconds}s)",
                extra={
                    "job_id": str(job_id),
                    "delay_seconds": delay_seconds,
                    "task_name": response.name
                }
            )

            return response.name

        except Exception as e:
            logger.exception(
                f"Failed to enqueue delayed task for job {job_id}",
                extra={"job_id": str(job_id), "error": str(e)}
            )
            raise

    async def delete_task_async(self, task_name: str) -> bool:
        """
        Delete a task from the queue (async version).

        Args:
            task_name: Full task resource name

        Returns:
            True if deleted, False if task was not found

        Raises:
            Exception: On infrastructure errors (permissions, networking, etc.)
        """
        try:
            await asyncio.to_thread(self.client.delete_task, name=task_name)
            logger.info(
                f"Task deleted: {task_name}",
                extra={"task_name": task_name}
            )
            return True
        except gcp_exceptions.NotFound:
            logger.warning(
                f"Task not found for deletion: {task_name}",
                extra={"task_name": task_name}
            )
            return False
        # Other exceptions (permissions, network, etc.) propagate to caller

    def get_task(self, task_name: str) -> Optional[tasks_v2.Task]:
        """
        Get task details by name.

        Args:
            task_name: Full task resource name

        Returns:
            Task instance or None if not found
        """
        try:
            task = self.client.get_task(name=task_name)
            return task
        except gcp_exceptions.NotFound:
            logger.warning(
                f"Task not found: {task_name}",
                extra={"task_name": task_name}
            )
            return None
        except Exception as e:
            logger.exception(
                f"Error getting task {task_name}: {str(e)}",
                extra={"task_name": task_name, "error": str(e)}
            )
            return None

    def delete_task(self, task_name: str) -> bool:
        """
        Delete a task from the queue.

        Args:
            task_name: Full task resource name

        Returns:
            True if deleted, False otherwise
        """
        try:
            self.client.delete_task(name=task_name)
            logger.info(
                f"Task deleted: {task_name}",
                extra={"task_name": task_name}
            )
            return True
        except gcp_exceptions.NotFound:
            logger.warning(
                f"Task not found for deletion: {task_name}",
                extra={"task_name": task_name}
            )
            return False
        except Exception as e:
            logger.exception(
                f"Error deleting task {task_name}: {str(e)}",
                extra={"task_name": task_name, "error": str(e)}
            )
            return False

    def list_tasks(self, limit: int = 100) -> list:
        """
        List tasks in the queue.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of tasks
        """
        try:
            tasks = self.client.list_tasks(
                request={
                    "parent": self.queue_path,
                    "page_size": limit
                }
            )
            return list(tasks)
        except Exception as e:
            logger.exception(
                f"Error listing tasks: {str(e)}",
                extra={"error": str(e)}
            )
            return []

    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        try:
            queue = self.client.get_queue(name=self.queue_path)

            # Count tasks
            tasks = self.list_tasks(limit=1000)
            task_count = len(tasks)

            return {
                "queue_name": self.queue_name,
                "state": queue.state.name,
                "task_count": task_count,
                "max_dispatches_per_second": queue.rate_limits.max_dispatches_per_second,
                "max_concurrent_dispatches": queue.rate_limits.max_concurrent_dispatches,
                "max_attempts": queue.retry_config.max_attempts,
                "min_backoff": queue.retry_config.min_backoff.seconds,
                "max_backoff": queue.retry_config.max_backoff.seconds
            }
        except Exception as e:
            logger.exception(
                f"Error getting queue stats: {str(e)}",
                extra={"error": str(e)}
            )
            return {}

    def pause_queue(self) -> bool:
        """
        Pause the queue (stop dispatching tasks).

        Returns:
            True if paused successfully
        """
        try:
            self.client.pause_queue(name=self.queue_path)
            logger.info(
                f"Queue paused: {self.queue_name}",
                extra={"queue_name": self.queue_name}
            )
            return True
        except Exception as e:
            logger.exception(
                f"Error pausing queue: {str(e)}",
                extra={"error": str(e)}
            )
            return False

    def resume_queue(self) -> bool:
        """
        Resume the queue (start dispatching tasks).

        Returns:
            True if resumed successfully
        """
        try:
            self.client.resume_queue(name=self.queue_path)
            logger.info(
                f"Queue resumed: {self.queue_name}",
                extra={"queue_name": self.queue_name}
            )
            return True
        except Exception as e:
            logger.exception(
                f"Error resuming queue: {str(e)}",
                extra={"error": str(e)}
            )
            return False

    def purge_queue(self) -> bool:
        """
        Purge all tasks from the queue.

        WARNING: This deletes all pending tasks!

        Returns:
            True if purged successfully
        """
        try:
            self.client.purge_queue(name=self.queue_path)
            logger.warning(
                f"Queue purged: {self.queue_name}",
                extra={"queue_name": self.queue_name}
            )
            return True
        except Exception as e:
            logger.exception(
                f"Error purging queue: {str(e)}",
                extra={"error": str(e)}
            )
            return False


class TaskQueueException(Exception):
    """Base exception for task queue operations."""
    pass


class TaskEnqueueError(TaskQueueException):
    """Raised when task enqueueing fails."""
    pass


class TaskNotFoundError(TaskQueueException):
    """Raised when task is not found."""
    pass
