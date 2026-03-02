# Enum Type Mismatch Audit Report

**Issue Date:** 2026-01-28
**Category:** ORM Type Annotation Mismatch (Enum vs String)
**Severity:** High - Causes runtime crashes

## Root Cause

SQLAlchemy models declare fields with `Mapped[EnumType]` type hints but use `String(50)` column definitions. At runtime, SQLAlchemy returns plain strings instead of enum objects. Code calling `.value` on these fields crashes with `AttributeError: 'str' object has no attribute 'value'`.

## Problem Pattern

```python
# Model definition (database.py)
template_type: Mapped[TemplateType] = mapped_column(String(50), nullable=False)
                      ^^^^^^^^^^^^                  ^^^^^^^^^^
                      Type hint says Enum          Column is String

# Runtime behavior
job.template_type  # Returns: "opr" (string)
job.template_type.value  # CRASH: AttributeError
```

## Affected Enum Fields

From `backend/app/models/database.py`:

1. **UserRole** (line 77)
   - Column: `String(50)`
   - Used in: User model

2. **ImageCategory** (line 408)
   - Column: `String(50)`
   - Used in: ProjectImage model

3. **ApprovalAction** (line 515)
   - Column: `String(50)`
   - Used in: Approval model

4. **TemplateType** (lines 618, 749, 870, 1084, 1390)
   - Column: `String(50)`
   - Used in: Job, Prompt, Template, Publication, ContentGeneration models

5. **JobStatus** (line 626)
   - Column: `String(50)`
   - Used in: Job model

6. **JobStepStatus** (line 700)
   - Column: `String(50)`
   - Used in: JobStep model

7. **ContentVariant** (lines 750, 873, 1391)
   - Column: `String(50)`
   - Used in: Prompt, Template, ContentGeneration models

8. **QACheckpointType** (lines 919, 1178)
   - Column: `String(50)`
   - Used in: QAComparison, QACheckpoint models

9. **QACheckpointStatus** (line 1179)
   - Column: `String(50)`
   - Used in: QACheckpoint model

10. **QAIssueSeverity** (line 1242)
    - Column: `String(20)`
    - Used in: QAIssue model

11. **QAOverrideType** (line 1297)
    - Column: `String(20)`
    - Used in: QAOverride model

12. **ExtractionType** (line 1347)
    - Column: `String(50)`
    - Used in: ContentExtraction model

13. **ContentQACheckType** (line 1456)
    - Column: `String(50)`
    - Used in: ContentQACheck model

14. **NotificationType** (line 981)
    - Column: `String(50)`
    - Used in: Notification model

## Code Locations Calling `.value`

### CRASHES (No hasattr check):

1. **job_manager.py:115** - `job.status.value` ⚠️ ACTIVE CRASH
2. **job_manager.py:161** - `job.status.value` ⚠️ POTENTIAL CRASH
3. **job_manager.py:374** - `job.status.value` ⚠️ POTENTIAL CRASH
4. **job_manager.py:375** - `job.status.value` ⚠️ POTENTIAL CRASH
5. **job_manager.py:747** - `cls_result.category.value` ⚠️ POTENTIAL CRASH
6. **job_manager.py:848** - `job.template_type.value` ⚠️ POTENTIAL CRASH
7. **job_manager.py:877** - `job.template_type.value` ⚠️ POTENTIAL CRASH
8. **job_manager.py:920** - `job.template_type.value` ⚠️ POTENTIAL CRASH
9. **upload.py:261** - `job.status.value` ⚠️ POTENTIAL CRASH
10. **jobs.py:197** - `current_user.role.value` ⚠️ POTENTIAL CRASH
11. **jobs.py:476** - `current_user.role.value` ⚠️ POTENTIAL CRASH
12. **job_repository.py:489** - `row.status.value` ⚠️ POTENTIAL CRASH

### SAFE (Has hasattr check):

1. **auth_service.py:267** - `user.role.value` ✓ SAFE
2. **dependencies_temp.py:79** - `current_user.role.value` ✓ SAFE
3. **dependencies_temp.py:224** - `current_user.role.value` ✓ SAFE
4. **dependencies_temp.py:266** - `current_user.role.value` ✓ SAFE
5. **auth.py:222** - `user.role.value` ✓ SAFE
6. **auth.py:350** - `current_user.role.value` ✓ SAFE
7. **jobs.py:76** - `job.template_type.value` ✓ SAFE
8. **jobs.py:78** - `job.status.value` ✓ SAFE
9. **jobs.py:112** - `step.status.value` ✓ SAFE
10. **jobs.py:134** - `job.status.value` ✓ SAFE
11. **jobs.py:425** - `job.status.value` ✓ SAFE

## Test Coverage Gap

**No tests exist for:**
- Job upload flow (upload.py)
- Job creation (job_manager.py)
- Job API routes (jobs.py)
- Job repository
- Background task queue

**Tests only cover:**
- Individual service functions (PDF, images, content generation)
- NOT end-to-end flows through the database

## Fix Strategy

### Option 1: Use Enum Column Type (Recommended)

Change database columns to proper enum types:

```python
from sqlalchemy import Enum as SQLAlchemyEnum

status: Mapped[JobStatus] = mapped_column(
    SQLAlchemyEnum(JobStatus, name='job_status', native_enum=False),
    nullable=False
)
```

**Pros:**
- Type safety
- Database constraints
- No `.value` needed

**Cons:**
- Requires migration
- More complex enum definition

### Option 2: Always Use hasattr Check (Current Workaround)

```python
status = job.status.value if hasattr(job.status, 'value') else job.status
```

**Pros:**
- No migration needed
- Works with current schema

**Cons:**
- Boilerplate everywhere
- Easy to forget
- Masks the real problem

### Option 3: Remove Enum Type Hints

Change all `Mapped[EnumType]` to `Mapped[str]`:

```python
status: Mapped[str] = mapped_column(String(50), nullable=False)
```

**Pros:**
- Type hints match runtime
- No `.value` calls needed

**Cons:**
- Loses type safety
- No IDE autocomplete for valid values

## Recommended Actions

### Immediate (Stop the bleeding):

1. ✅ Fix crash at job_manager.py:115 (hasattr check)
2. ⚠️ Add hasattr checks to all 12 CRASH locations
3. ⚠️ Add integration test for PDF upload flow

### Short-term (Next sprint):

4. ⚠️ Migrate all enum columns to proper SQLAlchemy Enum types
5. ⚠️ Remove all hasattr workarounds
6. ⚠️ Add MyPy strict mode to catch type mismatches

### Long-term (Technical debt):

7. ⚠️ Write integration tests for all API routes
8. ⚠️ Add pre-commit hook running MyPy
9. ⚠️ Add database schema validation tests

## Prevention

### 1. Add Integration Tests

```python
# tests/test_upload_integration.py
async def test_upload_pdf_creates_job():
    """Test full upload flow creates job without crashes"""
    response = await client.post(
        "/api/v1/upload/pdf",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"template_type": "opr"}
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify job was created
    job_response = await client.get(f"/api/v1/jobs/{job_id}")
    assert job_response.status_code == 200
```

### 2. Enable MyPy Strict Mode

```ini
# pyproject.toml
[tool.mypy]
strict = True
plugins = ["sqlalchemy.ext.mypy.plugin"]
```

### 3. Add Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: mypy
        language: system
        types: [python]
        args: ["--strict"]
```

## Impact Assessment

**Current state:**
- ❌ Upload flow completely broken
- ❌ Job creation fails 100% of the time
- ❌ Cannot process PDFs
- ✅ Other flows work (auth already has hasattr checks)

**User impact:**
- **Critical:** Cannot upload any PDFs
- **Critical:** All jobs fail immediately after creation
- **Moderate:** Rate limiting makes debugging difficult (retries hit limit)

## Related Issues

- Rate limiting too aggressive for dev (20/min causes cascading failures)
- Frontend retries on 500 error without exponential backoff
- No proper error handling/display for upload failures
- No test coverage for critical paths

---

**Generated:** 2026-01-28 19:35 UTC
**Last Updated:** 2026-01-28 19:35 UTC
