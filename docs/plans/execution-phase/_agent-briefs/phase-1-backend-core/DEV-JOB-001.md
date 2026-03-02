# Agent Brief: DEV-JOB-001

**Agent ID:** DEV-JOB-001
**Agent Name:** Job Manager Agent
**Type:** Development
**Phase:** 1 - Backend Core
**Context Budget:** 55,000 tokens

---

## Mission

Implement the asynchronous job processing system with lifecycle management, progress tracking, error handling with retry logic, and Cloud Tasks integration.

---

## Documentation to Read

### Primary (MUST READ)
1. `docs/04-backend/BACKGROUND_JOBS.md` - Job processing requirements
2. `docs/01-architecture/DATA_FLOW.md` - Processing pipeline flow

### Secondary (SHOULD READ)
3. `docs/05-integrations/GOOGLE_CLOUD_SETUP.md` - Cloud Tasks setup
4. `docs/04-backend/ERROR_HANDLING.md` - Error patterns

---

## Dependencies

**Upstream:**
- DEV-DB-001: Job, JobStep models
- DEV-CONFIG-001: GCP configuration

**Downstream:**
- DEV-PDF-001: Needs job manager for processing
- All processing agents: Use job steps

---

## Outputs to Produce

### File 1: `backend/app/services/job_manager.py`
Job orchestration service

### File 2: `backend/app/repositories/job_repository.py`
Job database operations

### File 3: `backend/app/background/task_queue.py`
Cloud Tasks integration

### File 4: `backend/app/api/routes/jobs.py`
Job API endpoints

---

## Acceptance Criteria

1. **Job Lifecycle:**
   - pending → processing → completed/failed/cancelled
   - Atomic state transitions
   - Timestamps for each state

2. **Progress Tracking:**
   - Total steps count
   - Completed steps count
   - Current step name
   - Percentage calculation

3. **Error Handling:**
   - 3 retry attempts
   - Exponential backoff
   - Error details stored
   - Failed state after retries exhausted

4. **Cloud Tasks Integration:**
   - Enqueue tasks for processing
   - Handle task callbacks
   - Retry policy configuration

5. **Job Cancellation:**
   - Cancel pending/processing jobs
   - Clean up resources
   - Mark as cancelled

6. **Step Tracking:**
   - 9+ processing steps
   - Step timing
   - Step-level errors

---

## Job Steps (9 minimum)

1. PDF Upload & Validation
2. Image Extraction
3. Image Classification
4. Watermark Detection
5. Watermark Removal
6. Floor Plan Extraction
7. Image Optimization
8. Asset Packaging
9. Cloud Upload

---

## QA Pair

Your outputs will be reviewed by: **QA-JOB-001**

---

**Begin execution.**
