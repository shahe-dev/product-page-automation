# Agent Brief: QA-JOB-001

**Agent ID:** QA-JOB-001
**Agent Name:** Job Manager QA
**Type:** QA
**Phase:** 1 - Backend Core
**Context Budget:** 45,000 tokens
**Paired Dev Agent:** DEV-JOB-001

---

## Mission

Validate the job management system for reliability, correct state handling, and proper error recovery.

---

## Artifacts to Review

1. `backend/app/services/job_manager.py`
2. `backend/app/repositories/job_repository.py`
3. `backend/app/background/task_queue.py`
4. `backend/app/api/routes/jobs.py`

---

## Validation Checklist

### 1. State Transitions
- [ ] All valid transitions work
- [ ] Invalid transitions rejected
- [ ] Transitions are atomic
- [ ] Timestamps recorded

### 2. Progress Tracking
- [ ] Progress updates correctly
- [ ] Percentage accurate
- [ ] Step names meaningful

### 3. Error Handling
- [ ] Retries work correctly
- [ ] Backoff is exponential
- [ ] Errors stored with details
- [ ] Max retries enforced

### 4. Cloud Tasks
- [ ] Tasks enqueued correctly
- [ ] Callbacks handled
- [ ] Dead letter handling

### 5. Concurrency
- [ ] Race conditions handled
- [ ] Concurrent updates safe
- [ ] No lost updates

### 6. Cancellation
- [ ] Pending jobs cancellable
- [ ] Processing jobs cancellable
- [ ] Resources cleaned up

---

## Runtime Validation (REQUIRED)

In addition to the domain-specific checklist above, perform these runtime checks:

- [ ] **Import Test:** All modules import without errors
- [ ] **Reserved Names:** No SQLAlchemy/Pydantic reserved name conflicts
- [ ] **Async Patterns:** No sync-blocking calls in async functions
- [ ] **Type Hints:** mypy passes with --ignore-missing-imports

### Import Validation Script

```python
import sys
sys.path.insert(0, "backend")

def test_job_imports():
    errors = []

    modules_to_test = [
        ("app.services.job_manager", ["JobManager"]),
        ("app.repositories.job_repository", ["JobRepository"]),
        ("app.background.task_queue", ["TaskQueue", "enqueue_task"]),
        ("app.api.routes.jobs", ["router"]),
    ]

    for module_path, exports in modules_to_test:
        try:
            module = __import__(module_path, fromlist=exports)
            for export in exports:
                if not hasattr(module, export):
                    errors.append(f"FAIL: {module_path}.{export} not found")
        except ImportError as e:
            errors.append(f"FAIL: Cannot import {module_path} - {e}")
        except Exception as e:
            errors.append(f"FAIL: Error loading {module_path} - {e}")

    return errors if errors else ["PASS: All imports successful"]
```

### Reserved Name Check

Verify these don't use reserved names:
- `job_repository.py`: No field named `metadata`, `registry`, `query`, `c`
- `job_manager.py`: No variable shadowing built-in `type`

### Async Pattern Check

Verify job_manager.py and task_queue.py:
- No `time.sleep()` - should use `asyncio.sleep()`
- No blocking I/O in async functions
- Database calls use `async with session`
- Background task execution properly awaited

### Runtime Validation Results

```
Import Test:      PASS / FAIL (details)
Reserved Names:   PASS / FAIL (details)
Async Patterns:   PASS / FAIL (details)
Type Hints:       PASS / FAIL (details)
```

**Runtime Validation Status:** PASS / FAIL

Note: If Runtime Validation fails, the overall QA review FAILS regardless of checklist score.

---

## Output Format

```json
{
  "agent_id": "QA-JOB-001",
  "reviewed_agent": "DEV-JOB-001",
  "review_timestamp": "2026-01-15T12:00:00Z",
  "passed": true,
  "score": 90,
  "checklist_results": {...},
  "runtime_validation": {
    "import_test": "PASS",
    "reserved_names": "PASS",
    "async_patterns": "PASS",
    "type_hints": "PASS"
  },
  "issues": [],
  "recommendations": []
}
```

---

**Begin review.**
