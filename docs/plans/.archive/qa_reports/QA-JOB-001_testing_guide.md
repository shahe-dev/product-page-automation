# Job Manager Testing Guide

**System:** PDP Automation v.3 - Job Management System
**QA Agent:** QA-JOB-001
**Version:** 1.0
**Date:** 2026-01-26

## Overview

This guide provides comprehensive testing procedures for the Job Manager system, covering unit tests, integration tests, and manual testing scenarios.

## Prerequisites

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx

# Set up test database
psql -U postgres -c "CREATE DATABASE pdp_test;"

# Configure test environment
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/pdp_test"
export GCP_PROJECT_ID="pdp-test-project"
export ENVIRONMENT="test"
```

### Test Database Schema
```bash
# Run migrations
alembic upgrade head
```

## Unit Tests

### 1. JobManager Tests

#### Test File: `tests/unit/test_job_manager.py`

```python
import pytest
from uuid import uuid4
from app.services.job_manager import JobManager
from app.models.enums import JobStatus, JobStepStatus

@pytest.mark.asyncio
async def test_create_job(job_manager, test_user):
    """Test job creation with step initialization."""
    job = await job_manager.create_job(
        user_id=test_user.id,
        template_type="opr"
    )

    assert job.id is not None
    assert job.status == JobStatus.PENDING
    assert job.progress == 0
    assert job.retry_count == 0

    # Check steps initialized
    steps = await job_manager.get_job_steps(job.id)
    assert len(steps) == 10  # All 10 steps
    assert all(step.status == JobStepStatus.PENDING for step in steps)


@pytest.mark.asyncio
async def test_update_job_progress(job_manager, test_job):
    """Test progress updates through steps."""
    await job_manager.update_job_progress(
        job_id=test_job.id,
        step_id="extract_images",
        status=JobStepStatus.IN_PROGRESS
    )

    job = await job_manager.get_job_status(test_job.id)
    assert job.status == JobStatus.PROCESSING
    assert job.progress == 15
    assert job.current_step == "Image Extraction"


@pytest.mark.asyncio
async def test_retry_logic(job_manager, test_job):
    """Test exponential backoff retry logic."""
    # First failure
    await job_manager.fail_job(test_job.id, "Test error 1")
    job = await job_manager.get_job_status(test_job.id)
    assert job.retry_count == 1
    assert job.status == JobStatus.PROCESSING  # Still processing, will retry

    # Second failure
    await job_manager.fail_job(test_job.id, "Test error 2")
    job = await job_manager.get_job_status(test_job.id)
    assert job.retry_count == 2

    # Third failure - max retries reached
    await job_manager.fail_job(test_job.id, "Test error 3")
    job = await job_manager.get_job_status(test_job.id)
    assert job.retry_count == 3
    assert job.status == JobStatus.FAILED  # Permanent failure


@pytest.mark.asyncio
async def test_cancel_pending_job(job_manager, test_job):
    """Test cancelling a pending job."""
    success = await job_manager.cancel_job(test_job.id)

    assert success is True
    job = await job_manager.get_job_status(test_job.id)
    assert job.status == JobStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_completed_job_fails(job_manager, test_job):
    """Test that completed jobs cannot be cancelled."""
    # Complete job first
    await job_manager.complete_job(test_job.id, {"result": "success"})

    # Try to cancel
    success = await job_manager.cancel_job(test_job.id)
    assert success is False
```

### 2. JobRepository Tests

#### Test File: `tests/unit/test_job_repository.py`

```python
import pytest
from datetime import datetime, timedelta
from app.repositories.job_repository import JobRepository
from app.models.enums import JobStatus

@pytest.mark.asyncio
async def test_create_job(job_repo, test_user):
    """Test job creation in database."""
    job = await job_repo.create_job(
        user_id=test_user.id,
        template_type="opr"
    )

    assert job.id is not None
    assert job.created_at is not None
    assert job.updated_at is not None


@pytest.mark.asyncio
async def test_atomic_retry_increment(job_repo, test_job):
    """Test atomic retry count increment."""
    initial_count = test_job.retry_count

    await job_repo.increment_retry_count(test_job.id)

    job = await job_repo.get_job(test_job.id)
    assert job.retry_count == initial_count + 1


@pytest.mark.asyncio
async def test_get_stale_jobs(job_repo, test_user):
    """Test stale job detection."""
    # Create job with old started_at
    job = await job_repo.create_job(
        user_id=test_user.id,
        template_type="opr"
    )
    await job_repo.update_job_status(
        job.id,
        JobStatus.PROCESSING,
        started_at=datetime.utcnow() - timedelta(hours=25)
    )

    stale_jobs = await job_repo.get_stale_jobs(hours=24)
    assert len(stale_jobs) == 1
    assert stale_jobs[0].id == job.id


@pytest.mark.asyncio
async def test_cleanup_old_jobs(job_repo, test_user):
    """Test old job cleanup."""
    # Create completed job with old completed_at
    job = await job_repo.create_job(
        user_id=test_user.id,
        template_type="opr"
    )
    await job_repo.update_job_status(
        job.id,
        JobStatus.COMPLETED,
        completed_at=datetime.utcnow() - timedelta(days=31)
    )

    deleted = await job_repo.cleanup_old_jobs(days=30)
    assert deleted == 1
```

### 3. TaskQueue Tests

#### Test File: `tests/unit/test_task_queue.py`

```python
import pytest
from unittest.mock import Mock, patch
from app.background.task_queue import TaskQueue

@pytest.mark.asyncio
async def test_enqueue_job(task_queue, test_job):
    """Test job enqueueing to Cloud Tasks."""
    with patch.object(task_queue.client, 'create_task') as mock_create:
        mock_create.return_value = Mock(name='task-123')

        task_name = await task_queue.enqueue_job(
            job_id=test_job.id,
            pdf_path="gs://bucket/file.pdf"
        )

        assert task_name == 'task-123'
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_enqueue_delayed_task(task_queue, test_job):
    """Test delayed task enqueueing."""
    with patch.object(task_queue.client, 'create_task') as mock_create:
        mock_create.return_value = Mock(name='task-456')

        task_name = await task_queue.enqueue_delayed_task(
            job_id=test_job.id,
            pdf_path="gs://bucket/file.pdf",
            delay_seconds=4  # 2^2 for second retry
        )

        assert task_name == 'task-456'
        # Verify schedule_time was set
        call_args = mock_create.call_args
        assert 'schedule_time' in call_args[0][0]['task']
```

## Integration Tests

### 4. API Integration Tests

#### Test File: `tests/integration/test_job_api.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_job_endpoint(client: AsyncClient, auth_headers):
    """Test POST /jobs endpoint."""
    response = await client.post(
        "/api/v1/jobs",
        json={
            "template_type": "opr",
            "processing_config": {"test": True}
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["progress"] == 0
    assert "id" in data


@pytest.mark.asyncio
async def test_list_jobs_endpoint(client: AsyncClient, auth_headers, test_jobs):
    """Test GET /jobs endpoint with filtering."""
    response = await client.get(
        "/api/v1/jobs?status=pending&limit=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert data["limit"] == 10


@pytest.mark.asyncio
async def test_get_job_status(client: AsyncClient, auth_headers, test_job):
    """Test GET /jobs/{id}/status endpoint."""
    response = await client.get(
        f"/api/v1/jobs/{test_job.id}/status",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_job.id)
    assert "status" in data
    assert "progress" in data


@pytest.mark.asyncio
async def test_cancel_job_endpoint(client: AsyncClient, auth_headers, test_job):
    """Test POST /jobs/{id}/cancel endpoint."""
    response = await client.post(
        f"/api/v1/jobs/{test_job.id}/cancel",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient, test_job, other_user_headers):
    """Test that users cannot access other users' jobs."""
    response = await client.get(
        f"/api/v1/jobs/{test_job.id}",
        headers=other_user_headers
    )

    assert response.status_code == 403
```

### 5. End-to-End Tests

#### Test File: `tests/e2e/test_job_lifecycle.py`

```python
import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_job_lifecycle(client: AsyncClient, auth_headers):
    """Test complete job lifecycle from creation to completion."""

    # 1. Create job
    create_response = await client.post(
        "/api/v1/jobs",
        json={"template_type": "opr"},
        headers=auth_headers
    )
    assert create_response.status_code == 201
    job_id = create_response.json()["id"]

    # 2. Start job (upload PDF)
    # This would trigger Cloud Tasks in production
    # For testing, we'll simulate the processing

    # 3. Poll status
    for i in range(10):
        status_response = await client.get(
            f"/api/v1/jobs/{job_id}/status",
            headers=auth_headers
        )
        status_data = status_response.json()

        if status_data["status"] in ["completed", "failed"]:
            break

        await asyncio.sleep(1)

    # 4. Get detailed steps
    steps_response = await client.get(
        f"/api/v1/jobs/{job_id}/steps",
        headers=auth_headers
    )
    assert steps_response.status_code == 200
    steps = steps_response.json()
    assert len(steps) == 10


@pytest.mark.asyncio
async def test_retry_on_failure(client: AsyncClient, auth_headers, mock_processor):
    """Test job retry on failure."""
    # Configure mock to fail first 2 times, succeed on 3rd
    mock_processor.configure_mock(
        side_effect=[Exception("Fail 1"), Exception("Fail 2"), {"success": True}]
    )

    create_response = await client.post(
        "/api/v1/jobs",
        json={"template_type": "opr"},
        headers=auth_headers
    )
    job_id = create_response.json()["id"]

    # Wait for retries and completion
    await asyncio.sleep(15)  # Allow for exponential backoff

    status_response = await client.get(
        f"/api/v1/jobs/{job_id}/status",
        headers=auth_headers
    )
    status_data = status_response.json()

    assert status_data["status"] == "completed"
```

## Manual Testing Scenarios

### Scenario 1: Happy Path

**Objective:** Test successful job completion

**Steps:**
1. Log in to the application
2. Navigate to "Create New Job"
3. Select template type "OPR"
4. Upload a valid PDF file
5. Click "Start Processing"
6. Monitor progress bar
7. Verify all 10 steps complete successfully
8. Check final result contains project_id and URLs

**Expected Result:**
- Job status transitions: PENDING → PROCESSING → COMPLETED
- Progress increases: 0% → 5% → 15% → ... → 100%
- All steps show green checkmarks
- Final result available in job details

### Scenario 2: Job Cancellation

**Objective:** Test user cancellation during processing

**Steps:**
1. Create and start a job
2. Wait until progress reaches ~30% (Image Classification)
3. Click "Cancel Job" button
4. Confirm cancellation dialog

**Expected Result:**
- Job status changes to CANCELLED
- Progress stops increasing
- Error message: "Job cancelled by user"
- Cannot restart cancelled job

### Scenario 3: Retry on Failure

**Objective:** Test automatic retry with exponential backoff

**Steps:**
1. Configure test to simulate transient failure (network timeout)
2. Create and start a job
3. Monitor job status and retry_count

**Expected Result:**
- Job fails initially
- retry_count increments: 0 → 1 → 2
- Backoff delays: 2s, 4s, 8s
- Job eventually completes on 3rd attempt (if transient)
- Or fails permanently after 3 attempts (if persistent)

### Scenario 4: Concurrent Job Processing

**Objective:** Test multiple jobs processing simultaneously

**Steps:**
1. Create 5 jobs with different PDFs
2. Start all jobs simultaneously
3. Monitor Cloud Tasks queue
4. Verify all jobs complete

**Expected Result:**
- All 5 jobs process in parallel
- No database deadlocks
- No lost updates
- All jobs reach terminal state (COMPLETED/FAILED)

### Scenario 5: Authorization

**Objective:** Test job access control

**Steps:**
1. User A creates a job
2. User B attempts to view User A's job
3. Admin user attempts to view User A's job

**Expected Result:**
- User A can view their job
- User B receives 403 Forbidden
- Admin can view any user's job

### Scenario 6: Stale Job Detection

**Objective:** Test cleanup of jobs stuck in PROCESSING

**Steps:**
1. Create a job and mark as PROCESSING
2. Manually set started_at to 25 hours ago
3. Run stale job detection query
4. Verify job is flagged as stale

**Expected Result:**
- Job appears in stale jobs list
- Admin notification sent
- Can manually intervene to fail or retry

## Performance Testing

### Load Test: Job Creation

**Objective:** Test system under high job creation load

**Tool:** Locust or Apache JMeter

```python
# locustfile.py
from locust import HttpUser, task, between

class JobUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def create_job(self):
        self.client.post("/api/v1/jobs", json={
            "template_type": "opr"
        })

    @task(2)
    def list_jobs(self):
        self.client.get("/api/v1/jobs")
```

**Test Criteria:**
- 100 concurrent users
- 10 requests per second per user
- Duration: 5 minutes

**Acceptance Criteria:**
- 95th percentile response time < 500ms
- Error rate < 1%
- No database connection pool exhaustion
- No memory leaks

### Stress Test: Queue Processing

**Objective:** Test Cloud Tasks queue under heavy load

**Steps:**
1. Enqueue 1000 jobs simultaneously
2. Monitor queue depth
3. Monitor worker CPU/memory
4. Verify all jobs eventually complete

**Acceptance Criteria:**
- Queue depth decreases steadily
- No tasks stuck in queue > 1 hour
- Worker auto-scaling triggers
- All jobs complete within 2 hours

## Test Fixtures

### Pytest Fixtures

```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.models.database import Base
from app.services.job_manager import JobManager
from app.repositories.job_repository import JobRepository
from app.background.task_queue import TaskQueue

@pytest.fixture
async def db_session():
    """Create test database session."""
    engine = create_async_engine(
        "postgresql+asyncpg://localhost/pdp_test",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def job_repo(db_session):
    """Create JobRepository instance."""
    return JobRepository(db_session)


@pytest.fixture
def task_queue():
    """Create mock TaskQueue."""
    return TaskQueue(
        project_id="test-project",
        queue_name="test-queue"
    )


@pytest.fixture
def job_manager(job_repo, task_queue):
    """Create JobManager instance."""
    return JobManager(job_repo, task_queue)


@pytest.fixture
async def test_user(db_session):
    """Create test user."""
    from app.models.database import User
    user = User(
        google_id="test-123",
        email="test@your-domain.com",
        name="Test User"
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def test_job(job_manager, test_user):
    """Create test job."""
    return await job_manager.create_job(
        user_id=test_user.id,
        template_type="opr"
    )
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Job Manager Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: pdp_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: |
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Data

### Sample Job Configurations

```json
{
  "opr_job": {
    "template_type": "opr",
    "processing_config": {
      "extract_floor_plans": true,
      "optimize_images": true,
      "max_image_size": 1920
    }
  },
  "mpp_job": {
    "template_type": "mpp",
    "processing_config": {
      "luxury_variant": true,
      "watermark_removal": true
    }
  }
}
```

### Sample Test PDFs

- `tests/fixtures/sample_opr.pdf` - 10 pages, mixed content
- `tests/fixtures/sample_mpp.pdf` - 15 pages, floor plans
- `tests/fixtures/invalid.pdf` - Corrupted PDF for error testing
- `tests/fixtures/large.pdf` - 100 pages for performance testing

## Test Coverage Goals

| Component | Target Coverage | Current Coverage |
|-----------|----------------|------------------|
| JobManager | 95% | - |
| JobRepository | 95% | - |
| TaskQueue | 90% | - |
| API Routes | 90% | - |
| Overall | 90% | - |

## Known Issues / Limitations

1. **Cloud Tasks Cancellation** - Not implemented; jobs marked CANCELLED may still execute
2. **Dead Letter Queue** - Processing not implemented
3. **Mock Limitations** - Cloud Tasks client difficult to fully mock
4. **Async Testing** - Requires careful fixture management

## Next Steps

1. Implement unit tests for all components
2. Add integration tests for API endpoints
3. Set up CI/CD pipeline
4. Configure test coverage reporting
5. Add performance/load testing
6. Document test results

---

**Document Owner:** QA-JOB-001
**Last Updated:** 2026-01-26
**Review Cycle:** After each sprint
