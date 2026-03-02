# Background Jobs

**Last Updated:** 2026-01-15
**Related Documents:**
- [Service Layer](./SERVICE_LAYER.md)
- [Error Handling](./ERROR_HANDLING.md)
- [Data Flow](../01-architecture/DATA_FLOW.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Cloud Tasks Setup](#cloud-tasks-setup)
3. [Job Lifecycle](#job-lifecycle)
4. [Job Processing Flow](#job-processing-flow)
5. [Retry Configuration](#retry-configuration)
6. [Job Monitoring](#job-monitoring)
7. [Related Documentation](#related-documentation)

---

## Overview

The PDP Automation v.3 system uses **Google Cloud Tasks** for background job processing. PDF processing is CPU and memory intensive, taking 3-5 minutes per file, so it runs asynchronously to provide a better user experience.

**Why Cloud Tasks?**
- **Managed queue** - No infrastructure to maintain
- **Automatic retries** - Built-in exponential backoff
- **Rate limiting** - Control throughput
- **Dead letter queue** - Handle failed jobs
- **Monitoring** - Built-in metrics and logging

**Job Processing Architecture:**
```
User uploads PDF
  │
  ▼
API creates job record (status: pending)
  │
  ▼
API enqueues task to Cloud Tasks
  │
  ▼
API returns job_id to user
  │
  ▼
Cloud Tasks worker picks up task
  │
  ▼
Worker processes job (extract, classify, generate)
  │
  ▼
Worker updates job status to completed
  │
  ▼
User polls GET /api/jobs/{job_id} for status
```

---

## Cloud Tasks Setup

### Queue Configuration

**Queue Name:** `pdp-processing-queue`
**Region:** `us-central1`
**Project:** `YOUR-GCP-PROJECT-ID`

**Create Queue:**
```bash
gcloud tasks queues create pdp-processing-queue \
  --location=us-central1 \
  --max-dispatches-per-second=10 \
  --max-concurrent-dispatches=5 \
  --max-attempts=3 \
  --min-backoff=10s \
  --max-backoff=300s \
  --max-doublings=3
```

**Queue Configuration Explained:**
- `max-dispatches-per-second: 10` - Max 10 new tasks dispatched per second
- `max-concurrent-dispatches: 5` - Max 5 tasks running concurrently
- `max-attempts: 3` - Retry failed tasks up to 3 times
- `min-backoff: 10s` - Wait at least 10 seconds before first retry
- `max-backoff: 300s` - Wait at most 5 minutes between retries
- `max-doublings: 3` - Double backoff up to 3 times (10s, 20s, 40s, then cap at 300s)

---

## Job Lifecycle

### Job States

```
pending → processing → completed
                    → failed
                    → cancelled
```

**State Transitions:**
- `pending` - Job created, waiting in queue
- `processing` - Worker picked up job and started processing
- `completed` - Job finished successfully
- `failed` - Job failed after all retries exhausted
- `cancelled` - User cancelled job

### Job Database Schema

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    website VARCHAR(50) NOT NULL,
    template_id UUID REFERENCES templates(id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    current_step VARCHAR(100),
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

---

## Job Processing Flow

### 1. Enqueue Job

**API Endpoint:** `POST /api/upload`

```python
# app/api/routes/upload.py

@router.post("/upload")
async def upload_pdf(
    file: UploadFile,
    website: str,
    template_id: str,
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    # Validate PDF
    file_content = await file.read()
    await validate_pdf(file_content)

    # Upload to GCS
    job_id = str(uuid.uuid4())
    pdf_path = f"pdfs/{job_id}/original.pdf"
    await storage_service.upload_file(file_content, pdf_path, "application/pdf")

    # Create job record
    await job_manager.create_job(
        job_id=job_id,
        user_id=current_user.id,
        website=website,
        template_id=template_id
    )

    # Enqueue task
    await job_manager.enqueue_task(
        job_id=job_id,
        pdf_path=f"gs://pdp-automation-assets-dev/{pdf_path}",
        website=website,
        template_id=template_id
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
```

### 2. Create Cloud Task

```python
# app/services/queue_service.py

from google.cloud import tasks_v2
import json

class QueueService:
    def __init__(self):
        self.client = tasks_v2.CloudTasksClient()
        self.queue_path = self.client.queue_path(
            "YOUR-GCP-PROJECT-ID",
            "us-central1",
            "pdp-processing-queue"
        )

    async def enqueue_job(
        self,
        job_id: str,
        pdf_path: str,
        website: str,
        template_id: str
    ) -> str:
        """
        Enqueue job to Cloud Tasks.

        Args:
            job_id: Job UUID
            pdf_path: GCS path to PDF
            website: Website identifier
            template_id: Template UUID

        Returns:
            Task name

        Raises:
            Exception: If task creation fails
        """
        # Task payload
        payload = {
            "job_id": job_id,
            "pdf_path": pdf_path,
            "website": website,
            "template_id": template_id
        }

        # Create HTTP POST task
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{settings.API_URL}/internal/process-job",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Internal-Auth": settings.INTERNAL_API_KEY
                },
                "body": json.dumps(payload).encode()
            }
        }

        # Create task
        response = self.client.create_task(
            request={"parent": self.queue_path, "task": task}
        )

        logger.info(f"Enqueued job {job_id}, task name: {response.name}")

        return response.name
```

### 3. Process Job

**Internal Endpoint:** `POST /internal/process-job`

```python
# app/api/routes/internal.py

@router.post("/process-job")
async def process_job(
    request: Request,
    payload: ProcessJobPayload,
    job_manager: JobManager = Depends(get_job_manager)
):
    # Verify internal auth
    auth_header = request.headers.get("X-Internal-Auth")
    if auth_header != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Process job
    try:
        await job_manager.process_job(
            job_id=payload.job_id,
            pdf_path=payload.pdf_path,
            website=payload.website,
            template_id=payload.template_id
        )

        return {"status": "success"}

    except Exception as e:
        logger.exception(f"Job {payload.job_id} failed")

        # Update job status
        await job_manager.update_job_status(
            payload.job_id,
            "failed",
            error_message=str(e)
        )

        # Re-raise for Cloud Tasks retry
        raise
```

### 4. Job Processing Steps

```python
# app/services/job_manager.py

class JobManager:
    async def process_job(
        self,
        job_id: str,
        pdf_path: str,
        website: str,
        template_id: str
    ):
        """
        Process job through all steps.

        Steps:
        1. Update status to processing
        2. Extract text from PDF
        3. Extract images from PDF
        4. Classify images
        5. Extract floor plan data
        6. Detect and remove watermarks
        7. Optimize images
        8. Generate content
        9. Run QA validation
        10. Push to Google Sheets
        11. Package ZIP
        12. Mark complete
        """
        try:
            # Step 1: Update status
            await self.update_job_status(job_id, "processing")
            await self.update_job_progress(job_id, 0, "Starting processing")

            # Step 2: Triple extraction (images + text)
            await self.update_job_progress(job_id, 10, "Extracting images and text from PDF")
            extraction = await self.pdf_processor.extract_all(pdf_bytes)
            # extraction.embedded -> embedded raster images
            # extraction.page_renders -> 300 DPI page renders
            # extraction.page_text_map -> {page_num: markdown_text} via pymupdf4llm

            # Step 3: Classify images
            await self.update_job_progress(job_id, 30, "Classifying images")
            classified_images = await self.image_classifier.classify_batch(
                extraction.embedded + extraction.page_renders
            )

            # Step 4: Extract floor plans (with text cross-referencing)
            await self.update_job_progress(job_id, 50, "Extracting floor plan data")
            floor_plans = await self.floor_plan_extractor.extract_floor_plans(
                floor_plan_images, page_text_map=extraction.page_text_map
            )

            # Step 6: Detect watermarks
            await self.update_job_progress(job_id, 55, "Detecting watermarks")
            watermarked_images = await self.watermark_detector.detect_batch(classified_images)

            # Step 7: Optimize images
            await self.update_job_progress(job_id, 65, "Optimizing images")
            optimized_images = await self.image_optimizer.optimize_batch(classified_images)

            # Step 8: Generate content
            await self.update_job_progress(job_id, 75, "Generating SEO content")
            generated_content = await self.content_generator.generate(
                extracted_text, website, template_id
            )

            # Step 9: QA validation
            await self.update_job_progress(job_id, 85, "Running QA validation")
            qa_result = await self.qa_service.validate_generation(
                extracted_text, generated_content
            )

            if qa_result.status == "failed":
                raise Exception(f"QA validation failed: {qa_result.result}")

            # Step 10: Push to Google Sheets
            await self.update_job_progress(job_id, 90, "Pushing to Google Sheets")
            sheet_url = await self.sheets_manager.populate_sheet(
                generated_content, template_id
            )

            # Step 11: Package ZIP
            await self.update_job_progress(job_id, 95, "Packaging images")
            zip_url = await self.output_organizer.create_zip_package(
                optimized_images, floor_plans, job_id
            )

            # Step 12: Create project record
            project = await self.project_service.create_from_extraction(
                extracted_text, job_id, user_id
            )

            # Step 13: Mark complete
            await self.update_job_result(job_id, {
                "project_id": project.id,
                "sheet_url": sheet_url,
                "zip_url": zip_url,
                "image_count": len(optimized_images),
                "floor_plan_count": len(floor_plans)
            })

            await self.update_job_progress(job_id, 100, "Complete")

            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.exception(f"Job {job_id} failed")
            await self.update_job_error(job_id, str(e))
            raise

    async def update_job_status(self, job_id: str, status: str):
        """Update job status."""
        await self.db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": status,
                "started_at": datetime.utcnow() if status == "processing" else None,
                "completed_at": datetime.utcnow() if status in ["completed", "failed", "cancelled"] else None
            }}
        )

    async def update_job_progress(self, job_id: str, progress: int, step: str):
        """Update job progress."""
        await self.db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "progress": progress,
                "current_step": step
            }}
        )

    async def update_job_result(self, job_id: str, result: dict):
        """Update job result."""
        await self.db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "result": result,
                "completed_at": datetime.utcnow()
            }}
        )

    async def update_job_error(self, job_id: str, error_message: str):
        """Update job error."""
        await self.db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "failed",
                "error_message": error_message,
                "completed_at": datetime.utcnow()
            }}
        )
```

---

## Retry Configuration

### Automatic Retries

Cloud Tasks automatically retries failed tasks with exponential backoff:

**Retry Schedule:**
- Attempt 1: Immediate
- Attempt 2: After 10 seconds (min_backoff)
- Attempt 3: After 20 seconds (10s * 2)
- Attempt 4: After 40 seconds (20s * 2)
- Further attempts: After 300 seconds (max_backoff)

**Maximum Attempts:** 3

**When to Retry:**
- HTTP 500-599 (Server errors)
- Task timeout
- Network errors

**When NOT to Retry:**
- HTTP 400-499 (Client errors)
- Invalid PDF
- File not found

### Custom Retry Logic

```python
# app/services/job_manager.py

class JobManager:
    async def process_job_with_retry(
        self,
        job_id: str,
        pdf_path: str,
        website: str,
        template_id: str
    ):
        """Process job with custom retry logic."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                await self.process_job(job_id, pdf_path, website, template_id)
                return  # Success

            except (anthropic.RateLimitError, anthropic.APIError) as e:
                # Transient error - retry
                retry_count += 1
                wait_time = 2 ** retry_count * 10  # Exponential backoff

                logger.warning(
                    f"Job {job_id} failed (attempt {retry_count}/{max_retries}), "
                    f"retrying in {wait_time}s. Error: {str(e)}"
                )

                if retry_count < max_retries:
                    await asyncio.sleep(wait_time)
                else:
                    # Max retries exhausted
                    await self.update_job_error(
                        job_id,
                        f"Failed after {max_retries} retries: {str(e)}"
                    )
                    raise

            except (ValueError, FileNotFoundError) as e:
                # Fatal error - don't retry
                logger.error(f"Job {job_id} failed with fatal error: {str(e)}")
                await self.update_job_error(job_id, str(e))
                raise

            except Exception as e:
                # Unknown error - log and retry
                logger.exception(f"Job {job_id} failed with unexpected error")
                retry_count += 1

                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count * 10)
                else:
                    await self.update_job_error(
                        job_id,
                        f"Failed after {max_retries} retries: {str(e)}"
                    )
                    raise
```

---

## Job Monitoring

### Job Status Endpoint

**GET /api/jobs/{job_id}**

```python
@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    job = await job_manager.get_job_status(job_id)

    # Check authorization
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
        "result": job.result,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at
    }
```

### Metrics and Logging

**Cloud Monitoring Metrics:**
- Job queue depth
- Job processing time
- Job success rate
- Job failure rate by error type

**Custom Metrics:**
```python
# app/utils/metrics.py

from google.cloud import monitoring_v3

metrics_client = monitoring_v3.MetricServiceClient()
project_name = f"projects/YOUR-GCP-PROJECT-ID"

def record_job_metric(metric_type: str, value: float, labels: dict = None):
    """Record custom metric to Cloud Monitoring."""
    series = monitoring_v3.TimeSeries()
    series.metric.type = f"custom.googleapis.com/{metric_type}"

    if labels:
        for key, val in labels.items():
            series.metric.labels[key] = val

    point = monitoring_v3.Point()
    point.value.double_value = value
    point.interval.end_time.seconds = int(time.time())

    series.points = [point]

    metrics_client.create_time_series(
        name=project_name,
        time_series=[series]
    )

# Usage
record_job_metric(
    "job_processing_time",
    duration_seconds,
    labels={"status": "completed", "website": "opr"}
)
```

### Job Alerts

**Alert Policies:**
1. **High failure rate** - Alert if >10% of jobs fail in 1 hour
2. **Long queue depth** - Alert if >50 jobs waiting for >5 minutes
3. **Slow processing** - Alert if average processing time >10 minutes

**Alert Configuration:**
```yaml
displayName: "High Job Failure Rate"
conditions:
  - displayName: "Job failure rate > 10%"
    conditionThreshold:
      filter: 'metric.type="custom.googleapis.com/job_status" AND metric.label.status="failed"'
      comparison: COMPARISON_GT
      thresholdValue: 0.1
      duration: 3600s
notificationChannels:
  - "projects/YOUR-GCP-PROJECT-ID/notificationChannels/email"
```

---

## Related Documentation

- [Service Layer](./SERVICE_LAYER.md) - Job processing services
- [Error Handling](./ERROR_HANDLING.md) - Error retry patterns
- [Data Flow](../01-architecture/DATA_FLOW.md) - End-to-end processing flow

---

**Last Updated:** 2026-01-15
