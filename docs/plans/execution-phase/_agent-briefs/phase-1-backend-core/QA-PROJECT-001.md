# Agent Brief: QA-PROJECT-001

**Agent ID:** QA-PROJECT-001
**Agent Name:** Project Service QA
**Type:** QA
**Phase:** 1 - Backend Core
**Context Budget:** 45,000 tokens
**Paired Dev Agent:** DEV-PROJECT-001

---

## Mission

Validate the project service implementation for correctness, performance, and adherence to requirements.

---

## Artifacts to Review

1. `backend/app/services/project_service.py`
2. `backend/app/repositories/project_repository.py`
3. `backend/app/api/routes/projects.py`
4. `backend/app/models/schemas.py`

---

## Validation Checklist

### 1. CRUD Operations
- [ ] Create validates required fields
- [ ] Read returns correct project
- [ ] Update handles partial updates
- [ ] Delete is soft (is_active=false)

### 2. Search & Filtering
- [ ] Full-text search works
- [ ] All filters implemented
- [ ] Filters can combine
- [ ] Empty results handled

### 3. Pagination
- [ ] Consistent response format
- [ ] Total count accurate
- [ ] Edge cases handled (page 0, negative)

### 4. Revision Tracking
- [ ] All changes logged
- [ ] old_value/new_value correct
- [ ] User attribution works

### 5. Authorization
- [ ] Owner can edit own projects
- [ ] Admin can edit any project
- [ ] Non-owner cannot edit

### 6. Performance
- [ ] Uses indexes for queries
- [ ] N+1 queries avoided
- [ ] Large result sets handled

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

def test_project_imports():
    errors = []

    modules_to_test = [
        ("app.services.project_service", ["ProjectService"]),
        ("app.repositories.project_repository", ["ProjectRepository"]),
        ("app.api.routes.projects", ["router"]),
        ("app.models.schemas", ["ProjectCreate", "ProjectUpdate", "ProjectResponse"]),
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
- `project_repository.py`: No field named `metadata`, `registry`, `query`, `c`
- `schemas.py`: Pydantic models don't use `model_config`, `model_fields` as field names

### Async Pattern Check

Verify project_service.py and project_repository.py:
- No `time.sleep()` - should use `asyncio.sleep()`
- No sync file operations - should use `aiofiles`
- Database calls use `async with session`

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
  "agent_id": "QA-PROJECT-001",
  "reviewed_agent": "DEV-PROJECT-001",
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

## Review Status

**Status:** COMPLETED (2026-01-26)
**Result:** FAIL (Score: 78/100)
**Output:** `docs/_agent-outputs/QA-PROJECT-001-validation-report.json`
**Summary:** `QA_PROJECT_VALIDATION_SUMMARY.md`

### Key Findings
- CRITICAL: Missing authorization checks on update and custom field operations
- HIGH: Search endpoint unreachable due to route ordering
- Functional implementation is comprehensive and well-structured
- Excellent database indexing and performance patterns
- Requires immediate developer action to fix security vulnerabilities

**Blockers:** Authorization issues must be resolved before production deployment.
