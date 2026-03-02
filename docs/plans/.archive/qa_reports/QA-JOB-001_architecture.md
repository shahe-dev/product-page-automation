# Job Manager System Architecture

## System Components Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                              │
├──────────────────────────────────────────────────────────────────┤
│  Web UI / API Client                                             │
│  - Create job                                                     │
│  - Upload PDF                                                     │
│  - Poll job status                                               │
│  - View progress                                                 │
│  - Cancel job                                                    │
└────────────┬─────────────────────────────────────────────────────┘
             │ HTTP/REST
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                         API LAYER                                 │
├──────────────────────────────────────────────────────────────────┤
│  FastAPI Routes (jobs.py)                                        │
│  ├─ POST   /jobs              - Create job                       │
│  ├─ GET    /jobs              - List user jobs                   │
│  ├─ GET    /jobs/{id}         - Get job details                  │
│  ├─ GET    /jobs/{id}/status  - Poll status                      │
│  ├─ GET    /jobs/{id}/steps   - Get step details                 │
│  ├─ POST   /jobs/{id}/cancel  - Cancel job                       │
│  └─ DELETE /jobs/{id}         - Delete job (admin)               │
│                                                                   │
│  Dependencies:                                                    │
│  - get_current_user()   - Authentication                         │
│  - get_job_manager()    - Service injection                      │
│  - get_job_or_404()     - Authorization                          │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                               │
├──────────────────────────────────────────────────────────────────┤
│  JobManager (job_manager.py)                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Business Logic & Orchestration                             │ │
│  │                                                            │ │
│  │ Methods:                                                   │ │
│  │  • create_job()         - Initialize job + steps          │ │
│  │  • start_job()          - Enqueue to Cloud Tasks          │ │
│  │  • update_job_progress()- Track step completion           │ │
│  │  • complete_job()       - Mark success                    │ │
│  │  • fail_job()           - Handle failure + retry          │ │
│  │  • cancel_job()         - User cancellation               │ │
│  │  • get_job_status()     - Query current state             │ │
│  │  • get_job_steps()      - Get detailed progress           │ │
│  │  • cleanup_old_jobs()   - Scheduled cleanup               │ │
│  │                                                            │ │
│  │ Processing Steps (10):                                     │ │
│  │  1. Upload & Validation      (5%)                         │ │
│  │  2. Image Extraction         (15%)                        │ │
│  │  3. Image Classification     (30%)                        │ │
│  │  4. Watermark Detection      (40%)                        │ │
│  │  5. Watermark Removal        (50%)                        │ │
│  │  6. Floor Plan Extraction    (60%)                        │ │
│  │  7. Image Optimization       (70%)                        │ │
│  │  8. Asset Packaging          (85%)                        │ │
│  │  9. Cloud Upload             (95%)                        │ │
│  │  10. Finalization            (100%)                       │ │
│  │                                                            │ │
│  │ Retry Logic:                                               │ │
│  │  • MAX_RETRIES = 3                                        │ │
│  │  • Exponential backoff: 2^retry_count seconds            │ │
│  │  • Permanent failure after max retries                    │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────┬───────────────────────────────┬────────────────────┘
             │                               │
             │ Uses                          │ Uses
             ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│   DATA ACCESS LAYER         │   │   QUEUE LAYER               │
├─────────────────────────────┤   ├─────────────────────────────┤
│ JobRepository               │   │ TaskQueue                   │
│ (job_repository.py)         │   │ (task_queue.py)             │
│                             │   │                             │
│ CRUD Operations:            │   │ Cloud Tasks Integration:    │
│  • create_job()             │   │  • enqueue_job()            │
│  • create_job_step()        │   │  • enqueue_delayed_task()   │
│  • get_job()                │   │  • get_task()               │
│  • get_job_with_steps()     │   │  • delete_task()            │
│  • update_job_status()      │   │  • list_tasks()             │
│  • update_job_step()        │   │  • get_queue_stats()        │
│  • increment_retry_count()  │   │  • pause_queue()            │
│  • get_jobs_by_user()       │   │  • resume_queue()           │
│  • get_jobs_by_status()     │   │  • purge_queue()            │
│  • get_stale_jobs()         │   │                             │
│  • cleanup_old_jobs()       │   │ Task Payload:               │
│  • get_job_statistics()     │   │  {                          │
│  • count_user_jobs()        │   │    job_id: UUID             │
│                             │   │    pdf_path: GCS path       │
│ Atomic Operations:          │   │    ...kwargs                │
│  • All updates use          │   │  }                          │
│    SQLAlchemy update()      │   │                             │
│  • Immediate commit         │   │ Retry Policy:               │
│  • No race conditions       │   │  • Configured in queue      │
│                             │   │  • Automatic retries        │
└────────────┬────────────────┘   └─────────────┬───────────────┘
             │                                   │
             │ Async                             │ HTTP POST
             ▼                                   ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│   DATABASE LAYER             │   │   BACKGROUND PROCESSING      │
├──────────────────────────────┤   ├──────────────────────────────┤
│ PostgreSQL 16+               │   │ Google Cloud Tasks           │
│                              │   │                              │
│ Tables:                      │   │ Queue: pdp-processing-queue  │
│  • jobs                      │   │ Location: us-central1        │
│  • job_steps                 │   │                              │
│                              │   │ Task Configuration:          │
│ jobs table:                  │   │  • HTTP POST to internal API │
│  - id (UUID, PK)             │   │  • X-Internal-Auth header    │
│  - user_id (FK → users)      │   │  • Max attempts: 3           │
│  - template_type (enum)      │   │  • Min backoff: 2s           │
│  - status (enum)             │   │  • Max backoff: 60s          │
│  - progress (0-100)          │   │                              │
│  - current_step              │   │ Dead Letter Queue:           │
│  - result (JSONB)            │   │  • Not yet configured        │
│  - error_message             │   └──────────────┬───────────────┘
│  - retry_count               │                  │
│  - started_at                │                  │ HTTP POST
│  - completed_at              │                  ▼
│  - created_at                │   ┌──────────────────────────────┐
│  - updated_at                │   │ Internal Processing Endpoint │
│                              │   ├──────────────────────────────┤
│ job_steps table:             │   │ POST /api/v1/internal/       │
│  - id (UUID, PK)             │   │      process-job             │
│  - job_id (FK → jobs)        │   │                              │
│  - step_id (string)          │   │ Authenticated with           │
│  - label (string)            │   │ X-Internal-Auth header       │
│  - status (enum)             │   │                              │
│  - result (JSONB)            │   │ Calls JobManager methods:    │
│  - error_message             │   │  • update_job_progress()     │
│  - started_at                │   │  • complete_job()            │
│  - completed_at              │   │  • fail_job()                │
│                              │   └──────────────────────────────┘
│ Indexes:                     │
│  • idx_jobs_user_id          │
│  • idx_jobs_status           │
│  • idx_jobs_created_at       │
│  • idx_job_steps_job_id      │
│                              │
│ Constraints:                 │
│  • progress >= 0 AND <= 100  │
│  • status IN (enum values)   │
│  • CASCADE delete steps      │
└──────────────────────────────┘
```

## State Transition Diagram

```
                     create_job()
                          │
                          ▼
                    ┌──────────┐
                    │ PENDING  │────────────┐
                    └──────────┘            │
                          │                 │ cancel_job()
                  start_job()               │
                          │                 │
                          ▼                 │
                    ┌──────────┐            │
              ┌─────│PROCESSING│────┐       │
              │     └──────────┘    │       │
              │           │         │       │
              │  complete_job()     │       ▼
              │           │    fail_job() ┌───────────┐
              │           ▼         │     │ CANCELLED │
              │     ┌──────────┐    │     └───────────┘
              │     │COMPLETED │    │
              │     └──────────┘    │
              │                     │
              │ fail_job()          │
              │ (retry_count < 3)   │
              └─────────────────────┘
                          │
                  fail_job()
                  (retry_count >= 3)
                          │
                          ▼
                    ┌──────────┐
                    │  FAILED  │
                    └──────────┘
```

## Job Step Status Flow

```
Each step follows this flow:

┌─────────┐  update_job_progress()  ┌────────────┐
│ PENDING │───────status: IN_PROGRESS─────▶│IN_PROGRESS │
└─────────┘                          └────────────┘
                                           │
                                           │ update_job_progress()
                                           │ status: COMPLETED/FAILED
                                           │
                         ┌─────────────────┴────────────┐
                         │                              │
                         ▼                              ▼
                   ┌──────────┐                  ┌────────┐
                   │COMPLETED │                  │ FAILED │
                   └──────────┘                  └────────┘
```

## Sequence Diagram: Job Creation and Processing

```
Client      API Route    JobManager   JobRepository   TaskQueue   Cloud Tasks   Worker
  │             │            │              │             │            │           │
  │ POST /jobs  │            │              │             │            │           │
  ├────────────▶│            │              │             │            │           │
  │             │ create_job()              │             │            │           │
  │             ├────────────▶│              │             │            │           │
  │             │             │create_job()  │             │            │           │
  │             │             ├─────────────▶│             │            │           │
  │             │             │              │INSERT jobs  │            │           │
  │             │             │              ├────────────▶DB           │           │
  │             │             │◀─────────────┤             │            │           │
  │             │             │_initialize_  │             │            │           │
  │             │             │  job_steps() │             │            │           │
  │             │             ├─────────────▶│             │            │           │
  │             │             │              │INSERT steps │            │           │
  │             │             │              ├────────────▶DB           │           │
  │             │             │◀─────────────┤             │            │           │
  │             │◀────────────┤              │             │            │           │
  │◀────────────┤ Job created │              │             │            │           │
  │             │              │             │             │            │           │
  │ POST /upload│              │             │             │            │           │
  ├────────────▶│              │             │             │            │           │
  │             │ start_job()  │             │             │            │           │
  │             ├─────────────▶│             │             │            │           │
  │             │              │enqueue_job()│             │            │           │
  │             │              ├────────────▶│             │            │           │
  │             │              │             │create_task()│            │           │
  │             │              │             ├────────────▶│            │           │
  │             │              │             │             │ Enqueue    │           │
  │             │              │             │             ├───────────▶│           │
  │             │              │             │◀────────────┤            │           │
  │             │              │◀────────────┤ task_name   │            │           │
  │             │◀─────────────┤             │             │            │           │
  │◀────────────┤              │             │             │            │           │
  │             │              │             │             │            │           │
  │             │              │             │             │            │ Dispatch  │
  │             │              │             │             │            ├──────────▶│
  │             │              │             │             │            │           │
  │             │              │             │             │   POST /internal/      │
  │             │              │             │             │   process-job          │
  │             │              │             │             │◀──────────────────────┤
  │             │              │             │             │           │           │
  │             │              │◀───────────────update_job_progress()──────────────┤
  │             │              ├────────────▶│             │           │           │
  │             │              │             │UPDATE jobs  │           │           │
  │             │              │             ├────────────▶DB          │           │
  │             │              │             │             │           │           │
  │ GET /jobs/  │              │             │             │           │           │
  │   {id}/status              │             │             │           │           │
  ├────────────▶│              │             │             │           │           │
  │             │get_job_status()            │             │           │           │
  │             ├─────────────▶│             │             │           │           │
  │             │              │get_job()    │             │           │           │
  │             │              ├────────────▶│             │           │           │
  │             │              │             │SELECT jobs  │           │           │
  │             │              │             ├────────────▶DB          │           │
  │             │              │◀────────────┤             │           │           │
  │             │◀─────────────┤             │             │           │           │
  │◀────────────┤ Status       │             │             │           │           │
  │             │ + Progress   │             │             │           │           │
  │             │              │             │             │           │           │
  │             │              │◀───────────────complete_job()─────────────────────┤
  │             │              ├────────────▶│             │           │           │
  │             │              │             │UPDATE jobs  │           │           │
  │             │              │             │SET status=  │           │           │
  │             │              │             │  COMPLETED  │           │           │
  │             │              │             ├────────────▶DB          │           │
  │             │              │             │             │           │           │
```

## Error Handling Flow

```
Worker encounters error
        │
        ▼
fail_job(job_id, error_msg)
        │
        ├──▶ Get current job
        │
        ├──▶ Check retry_count
        │
        ├─────────┬──────────────┐
        │         │              │
        │   retry_count < 3      │   retry_count >= 3
        │         │              │
        │         ▼              ▼
        │   Increment retry   Set status = FAILED
        │   Keep PROCESSING   Set error_message
        │         │              │
        │         │              ▼
        │         │         Permanent failure
        │         │         No more retries
        │         │
        │         ▼
        │   Calculate backoff:
        │   2^retry_count seconds
        │   (2s, 4s, 8s)
        │         │
        │         ▼
        │   Cloud Tasks automatic retry
        │   (configured in queue)
        │         │
        │         ▼
        │   Task re-dispatched after delay
        │         │
        │         ▼
        │   Worker tries again
```

## Scaling Considerations

### Horizontal Scaling
- Multiple API instances behind load balancer
- Multiple background workers consuming Cloud Tasks queue
- Database connection pooling (asyncpg)
- Stateless services enable easy scaling

### Bottlenecks
1. **Database writes** - Job status updates on every step
   - Mitigation: Batch progress updates, use read replicas for queries
2. **Cloud Tasks queue throughput** - Max dispatches per second
   - Mitigation: Multiple queues for different priorities
3. **Processing workers** - Limited by compute resources
   - Mitigation: Auto-scaling based on queue depth

### Reliability
- Cloud Tasks provides at-least-once delivery
- Idempotent processing steps prevent duplicate work
- Database constraints prevent invalid states
- Automatic retries with exponential backoff

## Security Architecture

```
┌────────────────────────────────────────┐
│ External Traffic                       │
│ (OAuth 2.0 authenticated)              │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│ API Gateway / Load Balancer            │
│ - Rate limiting                        │
│ - SSL/TLS termination                  │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│ API Layer                              │
│ - JWT validation                       │
│ - User authorization (get_current_user)│
│ - Job ownership check                  │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│ Internal Network                       │
│ (Not exposed to internet)              │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Internal Processing Endpoint       │ │
│ │ - X-Internal-Auth header check     │ │
│ │ - Only callable from Cloud Tasks   │ │
│ └────────────────────────────────────┘ │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Database                           │ │
│ │ - Private subnet                   │ │
│ │ - SSL required                     │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

## Monitoring & Observability

### Key Metrics to Track
1. **Job Metrics**
   - Jobs created per hour
   - Average job duration by template type
   - Job success/failure rate
   - Retry rate by step

2. **Queue Metrics**
   - Queue depth
   - Task age (time in queue)
   - Dispatch rate
   - Dead letter queue size

3. **Performance Metrics**
   - Step duration by type
   - Database query latency
   - API response time
   - Worker CPU/memory usage

### Logging Strategy
- Structured logging with JSON format
- Correlation IDs (job_id) across all logs
- Log levels: DEBUG (development), INFO (production), ERROR (always)
- Centralized log aggregation (Cloud Logging)

### Alerting
- Job failure rate > 10%
- Queue depth > 1000 tasks
- Stale jobs > 24 hours
- Dead letter queue not empty
- Database connection pool exhausted

---

**Document Version:** 1.0
**Last Updated:** 2026-01-26
**Reviewed by:** QA-JOB-001
