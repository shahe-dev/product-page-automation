# Local Pipeline E2E Test Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a local test script that runs the full 14-step PDF processing pipeline with real APIs, bypassing Cloud Tasks.

**Architecture:** Single Python script that loads `.env` settings, connects to local PostgreSQL, creates a test user/job, then calls `JobManager.execute_processing_pipeline()` directly. Each step prints timing, token usage, and costs. Cloud Tasks is bypassed because the pipeline execution method is already decoupled from the queue.

**Tech Stack:** Python 3.13, asyncio, SQLAlchemy async, pydantic-settings, Anthropic SDK, Google Sheets/Drive APIs, PyMuPDF

---

## Prerequisites

Before running the script, the user must have:
1. `backend/.env` populated with real secrets (not placeholders)
2. Local PostgreSQL running with the `pdp_automation` database created
3. Alembic migrations applied (`alembic upgrade head`)
4. A real estate PDF brochure file for testing
5. Google service account with Sheets/Drive permissions
6. Valid Anthropic API key

---

## Task 1: Create the Local Pipeline Runner Script

**Files:**
- Create: `backend/scripts/test_pipeline_local.py`

**Step 1: Write the script**

The script does the following:
1. Adds `backend/` to `sys.path` so app imports work
2. Loads settings from `.env` via pydantic (validates all required fields)
3. Connects to the local PostgreSQL database
4. Creates a test user (or finds existing one by email)
5. Creates a job record with the specified template type
6. Calls `JobManager.execute_processing_pipeline()` directly
7. Wraps each step with timing and progress output
8. Prints a final summary with:
   - Total time per step
   - Token usage and costs (from Anthropic)
   - Output URLs (Google Sheet, Drive folder)
   - Any errors encountered

**CLI Interface:**
```
python scripts/test_pipeline_local.py <pdf_path> [--template opr] [--email test@your-domain.com]
```

Arguments:
- `pdf_path` (required): Path to the PDF brochure file
- `--template` (optional, default: `opr`): Template type (aggregators/opr/mpp/adop/adre/commercial)
- `--email` (optional, default: `test@your-domain.com`): Test user email for job ownership

**Implementation approach:**

```python
"""
Local Pipeline E2E Test Runner

Runs the full 14-step PDF processing pipeline locally with real APIs.
Bypasses Cloud Tasks by calling JobManager.execute_processing_pipeline() directly.

Usage:
    python scripts/test_pipeline_local.py <pdf_path> [--template opr] [--email test@your-domain.com]

Prerequisites:
    - backend/.env populated with real secrets
    - Local PostgreSQL with alembic migrations applied
    - Google service account with Sheets/Drive access
    - Valid Anthropic API key
"""
```

Key implementation details:

a. **Database setup** - Use `get_db_context()` from `app.config.database`:
```python
from app.config.database import get_db_context, initialize_database
```

b. **Test user creation** - Query by email, create if not found:
```python
from app.models.database import User
from app.models.enums import UserRole
stmt = select(User).where(User.email == email)
user = result.scalar_one_or_none()
if not user:
    user = User(google_id="local-test", email=email, name="Local Test", role=UserRole.USER, is_active=True)
```

c. **Job creation and pipeline execution** - Use JobRepository + JobManager:
```python
from app.repositories.job_repository import JobRepository
from app.services.job_manager import JobManager
from app.background.task_queue import TaskQueue

task_queue = TaskQueue()  # Will fail gracefully in local dev mode
repo = JobRepository(db)
manager = JobManager(repo, task_queue)

job = await manager.create_job(user_id=user.id, template_type=template_type)
result = await manager.execute_processing_pipeline(job.id, pdf_path)
```

d. **Timing wrapper** - Monkey-patch `_execute_step` to add timing:
```python
original_execute = manager._execute_step

async def timed_execute(job_id, step_id, pdf_path):
    start = time.time()
    print(f"\n{'='*60}")
    print(f"  Step: {step_id}")
    print(f"{'='*60}")
    try:
        result = await original_execute(job_id, step_id, pdf_path)
        elapsed = time.time() - start
        print(f"  Completed in {elapsed:.1f}s")
        if result:
            for k, v in result.items():
                print(f"    {k}: {v}")
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"  FAILED after {elapsed:.1f}s: {e}")
        raise

manager._execute_step = timed_execute
```

e. **Final summary** - Print Anthropic usage stats + output URLs:
```python
from app.integrations.anthropic_client import anthropic_service
stats = anthropic_service.get_session_usage()
```

**Step 2: Test the script runs with `--help`**

Run: `cd backend && python scripts/test_pipeline_local.py --help`
Expected: Usage message with arguments listed

**Step 3: Commit**

```bash
git add backend/scripts/test_pipeline_local.py
git commit -m "feat: add local pipeline E2E test runner script"
```

---

## Task 2: Add Prerequisite Validation

**Files:**
- Modify: `backend/scripts/test_pipeline_local.py`

**Step 1: Add preflight checks**

Before running the pipeline, validate:

1. **PDF file exists** and starts with `%PDF` header
2. **Database connection** works (try connecting and running a simple query)
3. **Alembic migrations** are applied (check that `users` table exists)
4. **Anthropic API key** is valid (make a minimal API call or just verify format)
5. **Google service account** credentials file exists (if GOOGLE_APPLICATION_CREDENTIALS is set)
6. **Template type** is valid (one of the 6 allowed values)

Print a checklist:
```
Preflight Checks:
  [OK] PDF file exists (2.4 MB)
  [OK] Database connected (PostgreSQL 15.4)
  [OK] Tables exist (22 tables)
  [OK] Anthropic API key format valid
  [OK] Google credentials file found
  [OK] Template type 'opr' valid
```

If any check fails, print the error and exit with code 1.

**Step 2: Run preflight on a missing PDF**

Run: `cd backend && python scripts/test_pipeline_local.py nonexistent.pdf`
Expected: `[FAIL] PDF file not found: nonexistent.pdf` and exit code 1

**Step 3: Commit**

```bash
git add backend/scripts/test_pipeline_local.py
git commit -m "feat: add preflight validation to pipeline test runner"
```

---

## Task 3: Add .env.local Template for Pipeline Testing

**Files:**
- Create: `backend/.env.pipeline-test.example`

**Step 1: Write the template**

Create a minimal `.env` template specifically for pipeline testing, with comments explaining which values are needed and where to get them. This is separate from `.env.example` because it emphasizes the pipeline-specific secrets.

Only include the secrets actually needed for the pipeline (skip server config, feature flags, etc.):
- DATABASE_URL
- ANTHROPIC_API_KEY
- GOOGLE_APPLICATION_CREDENTIALS
- GCP_PROJECT_ID
- GCS_BUCKET_NAME
- All 6 TEMPLATE_SHEET_IDs
- GOOGLE_DRIVE_ROOT_FOLDER_ID
- JWT_SECRET (needed for settings validation)
- GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET (needed for settings validation)
- INTERNAL_API_KEY (needed for settings validation)

**Step 2: Commit**

```bash
git add backend/.env.pipeline-test.example
git commit -m "docs: add .env template for pipeline E2E testing"
```

---

## Summary

| Task | Description | Dependencies |
|------|-------------|-------------|
| 1 | Local pipeline runner script | None |
| 2 | Preflight validation | Task 1 |
| 3 | .env template for testing | None |

**Total estimated API cost per run:** ~$0.28 (assuming 5 floor plans)
**Expected pipeline duration:** 5-7 minutes for a typical 10-page brochure
