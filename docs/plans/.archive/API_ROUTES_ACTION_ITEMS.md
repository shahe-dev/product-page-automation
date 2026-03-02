# API Routes - Critical Action Items

## BLOCKERS (Must fix to run)

### 1. Database Session Management
**File:** `backend/app/api/dependencies.py`
**Problem:** Line 29 raises NotImplementedError
**Fix:**
```python
from app.config.database import async_session_maker

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
```

### 2. Authentication Dependency
**Files:** Multiple route files import from wrong location
**Problem:** `app.api.dependencies.get_current_user()` raises NotImplementedError
**Fix:**
```python
# Option A: Delete backend/app/api/dependencies.py entirely
# Option B: Make it re-export:
from app.middleware.auth import get_current_user

# Update ALL route imports to use:
from app.middleware.auth import get_current_user
# NOT from app.api.dependencies
```

**Files to update:**
- backend/app/api/routes/jobs.py (line 24)

### 3. Rate Limiting
**File:** Add to `backend/app/main.py`
**Problem:** No rate limiting middleware
**Fix:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Then in each route:
@router.post("/pdf")
@limiter.limit("10/minute")
async def upload_pdf(...):
```

**Routes to limit:**
- upload.py: 10/min for /pdf, 20/min for /images
- auth.py: 5/min for /google, 20/min for /refresh
- content.py: 10/min for /generate, 30/min for GET
- All other endpoints: 100/min default

### 4. File Upload Streaming
**File:** `backend/app/api/routes/upload.py`
**Problem:** Lines 83-84 load entire file into memory
**Fix:**
```python
# BEFORE
content = await file.read()
file_size_mb = len(content) / (1024 * 1024)

# AFTER
# Check size from header first
content_length = request.headers.get('content-length')
if content_length:
    size_bytes = int(content_length)
    if size_bytes > MAX_PDF_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, ...)

# Stream directly to GCS
from google.cloud import storage
storage_client = storage.Client()
bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
blob = bucket.blob(f"uploads/{job_id}/{file.filename}")

# Stream upload
await blob.upload_from_file(
    file.file,  # Don't call .read()
    content_type='application/pdf',
    size=size_bytes
)
```

---

## HIGH PRIORITY (Fix before production)

### 5. Add Pagination to Prompts
**File:** `backend/app/api/routes/prompts.py`
**Problem:** Line 89 - list_prompts has no pagination
**Fix:**
```python
async def list_prompts(
    template_type: Optional[str] = Query(None),
    content_variant: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),          # ADD
    limit: int = Query(50, ge=1, le=100), # ADD
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    offset = (page - 1) * limit
    # Apply offset and limit to query
```

### 6. Centralize Template Types
**Problem:** Template types hardcoded in 5 files
**Fix:**

Create `backend/app/models/enums.py`:
```python
from enum import Enum

class TemplateType(str, Enum):
    AGGREGATORS = "aggregators"
    OPR = "opr"
    MPP = "mpp"
    ADOP = "adop"
    ADRE = "adre"
    COMMERCIAL = "commercial"

class ContentVariant(str, Enum):
    STANDARD = "standard"
    LUXURY = "luxury"

class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class CheckpointType(str, Enum):
    GENERATION = "generation"
    SHEETS = "sheets"
    FINAL = "final"
```

Replace everywhere:
```python
# BEFORE
valid_templates = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]
if template_type not in valid_templates:
    raise HTTPException(...)

# AFTER
from app.models.enums import TemplateType
# Pydantic automatically validates enum
template_type: TemplateType = Field(...)
```

**Files to update:**
- upload.py (line 101)
- content.py (line 98)
- prompts.py (line 255, 270)

### 7. File Type Validation by Content
**File:** `backend/app/api/routes/upload.py`
**Problem:** Line 69 validates Content-Type header (can be spoofed)
**Fix:**
```python
import filetype

# Read first 8KB to detect type
header = await file.read(8192)
await file.seek(0)  # Reset for full read later

kind = filetype.guess(header)
if kind is None or kind.mime != 'application/pdf':
    raise HTTPException(
        status_code=400,
        detail={
            "error_code": "INVALID_FILE_TYPE",
            "message": "File must be a PDF (detected: {})".format(
                kind.mime if kind else "unknown"
            )
        }
    )
```

Add to requirements.txt:
```
filetype==1.2.0
```

---

## MEDIUM PRIORITY (Quality improvements)

### 8. Add Trace IDs
**File:** Create `backend/app/middleware/trace.py`
```python
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response
```

Add to main.py:
```python
from app.middleware.trace import TraceMiddleware
app.add_middleware(TraceMiddleware)
```

Update error responses to include trace_id:
```python
detail={
    "error_code": "...",
    "message": "...",
    "details": {},
    "trace_id": request.state.trace_id  # ADD
}
```

### 9. Request Logging
**File:** Create `backend/app/middleware/logging.py`
```python
import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "trace_id": getattr(request.state, "trace_id", None),
            "user_id": getattr(request.state, "user_id", None)
        }
    )

    return response
```

### 10. OpenAPI Examples
Add to all Pydantic models:
```python
class ContentGenerateRequest(BaseModel):
    project_id: UUID = Field(
        ...,
        description="Project ID to generate content for",
        example="123e4567-e89b-12d3-a456-426614174000"  # ADD
    )
    template_type: str = Field(
        ...,
        description="Template type",
        example="opr"  # ADD
    )
```

---

## LOW PRIORITY (Nice to have)

### 11. Fix Route Path Conflict
**File:** `backend/app/api/routes/projects.py`
**Problem:** Line 395 - `/search` conflicts with `/{project_id}`
**Fix:**
```python
# Move search to list endpoint as query param
# OR use different prefix:
@router.get("/search/all")  # Instead of /search
async def search_projects(...):
```

### 12. Admin Role Checks
**Files:** prompts.py, workflow.py
**Problem:** Admin checks commented as TODO
**Fix:**
```python
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=403,
            detail="ADMIN_REQUIRED"
        )
    return current_user

# Then use:
@router.post("/prompts")
async def create_prompt(
    current_user: User = Depends(require_admin),  # Changed
    ...
):
```

---

## Testing Requirements

Create `backend/tests/test_api_routes.py`:
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_upload_pdf_valid():
    async with AsyncClient(app=app, base_url="http://test") as client:
        files = {"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
        data = {"template_type": "opr"}
        response = await client.post(
            "/api/v1/upload/pdf",
            files=files,
            data=data,
            headers={"Authorization": "Bearer fake_token"}
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_upload_pdf_invalid_type():
    async with AsyncClient(app=app, base_url="http://test") as client:
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}
        data = {"template_type": "opr"}
        response = await client.post(
            "/api/v1/upload/pdf",
            files=files,
            data=data,
            headers={"Authorization": "Bearer fake_token"}
        )
        assert response.status_code == 400
        assert "INVALID_FILE_TYPE" in response.json()["detail"]["error_code"]

@pytest.mark.asyncio
async def test_rate_limiting():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make 11 requests (limit is 10/min)
        for i in range(11):
            response = await client.post("/api/v1/upload/pdf", ...)
        assert response.status_code == 429

# Add tests for:
# - Authentication (valid/invalid/expired tokens)
# - Pagination edge cases
# - Concurrent uploads
# - File size limits
# - Input validation
```

---

## Estimated Time to Fix

| Priority | Item | Time | Blocker? |
|----------|------|------|----------|
| CRITICAL | Database sessions | 2h | YES |
| CRITICAL | Auth dependency | 1h | YES |
| CRITICAL | Rate limiting | 4h | YES |
| CRITICAL | File streaming | 6h | YES |
| HIGH | Pagination | 1h | NO |
| HIGH | Centralize enums | 3h | NO |
| HIGH | File type validation | 2h | NO |
| MEDIUM | Trace IDs | 2h | NO |
| MEDIUM | Request logging | 4h | NO |
| MEDIUM | OpenAPI examples | 4h | NO |
| LOW | Route conflict | 0.5h | NO |
| LOW | Admin checks | 1h | NO |

**Total blockers:** 13 hours (2 days)
**Total high priority:** 6 hours (1 day)
**Total recommended:** 30.5 hours (4 days)

---

## Quick Wins (Do These First)

1. Fix auth dependency import (1 hour) - Unblocks everything
2. Add pagination to prompts (1 hour) - Prevents future issues
3. Fix route path conflict (30 min) - Avoids confusion

**Total:** 2.5 hours to resolve 3 issues

---

## Files to Create

- `backend/app/models/enums.py` (centralized enums)
- `backend/app/middleware/trace.py` (trace ID middleware)
- `backend/app/middleware/logging.py` (request logging)
- `backend/tests/test_api_routes.py` (integration tests)

## Files to Modify

- `backend/app/api/dependencies.py` (implement or delete)
- `backend/app/api/routes/upload.py` (streaming, validation)
- `backend/app/api/routes/prompts.py` (pagination)
- `backend/app/api/routes/content.py` (use enums)
- `backend/app/api/routes/qa.py` (use enums)
- `backend/app/api/routes/workflow.py` (use enums, admin checks)
- `backend/app/api/routes/projects.py` (fix route conflict)
- `backend/app/main.py` (add rate limiting, middleware)

## Dependencies to Add

```txt
# requirements.txt additions
slowapi==0.1.9           # Rate limiting
filetype==1.2.0          # File type detection
google-cloud-storage     # Already have but ensure streaming support
```

---

## Priority Order

**Day 1 Morning:**
1. Fix auth dependency (BLOCKER)
2. Fix database sessions (BLOCKER)

**Day 1 Afternoon:**
3. Implement rate limiting (SECURITY)

**Day 2:**
4. Fix file upload streaming (SECURITY + PERFORMANCE)

**Day 3:**
5. Create enums file and update all routes
6. Add pagination to prompts

**Day 4:**
7. Add trace IDs and logging
8. Write integration tests

**Ready for deployment after Day 4**

---

## Questions for Developer

1. Why is `app.api.dependencies.py` separate from `app.middleware.auth.py`?
2. Is there a database session factory already implemented in `app.config.database`?
3. What's the plan for prompt/template caching?
4. Should rate limits be per-user or per-IP?
5. Is there a staging environment for testing these fixes?

---

**QA Agent:** QA-API-001
**Priority:** CRITICAL
**Action Required:** Address blockers before next code review
