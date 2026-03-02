# Agent Briefing: Backend Documentation Agent

**Agent ID:** backend-docs-agent
**Batch:** 1 (Foundation)
**Priority:** P0 - Critical Foundation
**Est. Context Usage:** 37,000 tokens

---

## Your Mission

You are a specialized documentation agent responsible for creating **5 backend documentation files** for the PDP Automation v.3 system. These documents describe the FastAPI backend, service layer, and API implementation.

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/04-backend/`

---

## Files You Must Create

1. `SERVICE_LAYER.md` (500-600 lines) - All service classes and their methods
2. `API_ENDPOINTS.md` (600-700 lines) - Complete OpenAPI specification with examples
3. `ERROR_HANDLING.md` (250-300 lines) - Error codes, responses, patterns
4. `BACKGROUND_JOBS.md` (300-350 lines) - Async task processing with Cloud Tasks
5. `CACHING_STRATEGY.md` (250-300 lines) - Redis/memory caching patterns

**Total Output:** ~1,900-2,250 lines across 5 files

---

## Technology Stack

**Core Backend:**
- **Framework:** FastAPI 0.109+
- **Runtime:** Python 3.10+
- **ASGI Server:** Uvicorn with workers
- **ORM:** SQLAlchemy 2.x (async)
- **Migrations:** Alembic 1.x
- **Validation:** Pydantic 2.x

**Processing:**
- **PDF:** PyMuPDF 1.23+ (fitz)
- **Images:** Pillow 10.x
- **Computer Vision:** OpenCV 4.9+
- **Google Cloud:** google-cloud-aiplatform, google-cloud-storage, gspread

**Infrastructure:**
- **Queue:** Cloud Tasks
- **Cache:** Redis (Cloud Memorystore) or in-memory
- **Monitoring:** Sentry for errors
- **Logging:** Python logging + Cloud Logging

---

## Service Layer Architecture

### Core Services

**1. AuthService** (`app/services/auth_service.py`)
```python
class AuthService:
    async def verify_google_token(token: str) -> GoogleUser
    async def check_domain_restriction(email: str) -> bool
    async def get_or_create_user(google_user: GoogleUser) -> User
    async def assign_role(user_id: str, role: str) -> User
```

**2. JobManager** (`app/services/job_manager.py`)
```python
class JobManager:
    async def create_job(user_id: str, module: str, ...) -> str
    async def process_job(job_id: str, file_path: str, ...) -> None
    async def update_job_progress(job_id: str, progress: int, step: str)
    async def get_job_status(job_id: str) -> JobStatus
    async def cancel_job(job_id: str) -> None
```

**3. PDFProcessor** (`app/services/pdf_processor.py`)
```python
class PDFProcessor:
    def __init__(self, render_dpi: int = 300, max_pages: int = 100)
    async def extract_all(self, pdf_bytes: bytes) -> ExtractionResult
        # Triple extraction: embedded images + page renders + per-page text (pymupdf4llm)
        # Returns ExtractionResult with .embedded, .page_renders, .page_text_map
    def get_extraction_summary(self, result: ExtractionResult) -> dict
```

**4. AnthropicService** (`app/services/anthropic_service.py`)
```python
class AnthropicService:
    # Uses Claude Sonnet 4.5 for text extraction and generation
    async def extract_data_from_pdf(
        pdf_pages: List[bytes], prompt: str
    ) -> Dict[str, Any]

    async def generate_content(
        extracted_data: Dict, template: str, prompt: str
    ) -> Dict[str, str]

    # Uses Claude Sonnet 4.5 for vision tasks
    async def classify_image(image_bytes: bytes) -> str

    async def detect_watermark(image_bytes: bytes) -> Optional[BoundingBox]

    async def extract_floor_plan_data(
        image_bytes: bytes
    ) -> Dict[str, Any]
```

**5. ImageClassifier** (`app/services/image_classifier.py`)
```python
class ImageClassifier:
    async def classify_batch(images: List[bytes]) -> List[str]
    async def classify_single(image: bytes) -> str
    def apply_category_limits(
        images: List[Image],
        limits: Dict[str, int]
    ) -> List[Image]
```

**6. WatermarkDetector** (`app/services/watermark_detector.py`)
```python
class WatermarkDetector:
    async def detect(image: bytes) -> Optional[BoundingBox]
    def remove_watermark(
        image: np.ndarray, bbox: BoundingBox
    ) -> np.ndarray  # Uses OpenCV inpainting
```

**7. ImageOptimizer** (`app/services/image_optimizer.py`)
```python
class ImageOptimizer:
    def optimize(
        image_path: str,
        max_dimensions: Tuple[int, int],
        max_size_kb: int
    ) -> str

    def resize(image: Image, max_dim: Tuple[int, int]) -> Image
    def compress(image: Image, target_kb: int) -> bytes
    def convert_format(image: Image, format: str) -> bytes
```

**8. FloorPlanExtractor** (`app/services/floor_plan_extractor.py`)
```python
class FloorPlanExtractor:
    async def extract_data(floor_plan_image: bytes) -> FloorPlanData
    def deduplicate(
        floor_plans: List[FloorPlanData]
    ) -> List[FloorPlanData]
```

**9. OutputOrganizer** (`app/services/output_organizer.py`)
```python
class OutputOrganizer:
    def create_zip_package(
        images: List[str],
        floor_plans: List[str],
        output_path: str
    ) -> str

    def organize_by_category(images: List[Image]) -> Dict[str, List[Image]]
```

**10. ContentGenerator** (`app/services/content_generator.py`)
```python
class ContentGenerator:
    async def generate(
        extracted_data: Dict,
        template_id: str,
        website: str
    ) -> Dict[str, str]

    def apply_character_limits(content: Dict, limits: Dict) -> Dict
    def generate_seo_tags(content: Dict) -> Dict[str, str]
    def generate_url_slug(project_name: str) -> str
```

**11. ContentQAService** (`app/services/content_qa_service.py`)
```python
class ContentQAService:
    async def validate_before_push(
        extracted_data: Dict,
        generated_content: Dict,
        prompt_spec: Prompt
    ) -> QAResult

    def check_factual_accuracy(
        extracted: Dict, generated: Dict
    ) -> List[Issue]

    def check_prompt_compliance(
        content: Dict, spec: Prompt
    ) -> List[Issue]
```

**12. SheetsManager** (`app/services/sheets_manager.py`)
```python
class SheetsManager:
    async def create_from_template(template_id: str) -> str
    async def populate_sheet(
        sheet_id: str,
        content: Dict,
        field_mapping: Dict
    ) -> None
    async def batch_update(
        sheet_id: str,
        updates: List[CellUpdate]
    ) -> None
```

**13. QAService** (`app/services/qa_service.py`)
```python
class QAService:
    async def validate_extraction(
        extracted: Dict, pdf_path: str
    ) -> QAResult

    async def validate_generation(
        generated: Dict, extracted: Dict
    ) -> QAResult

    async def validate_sheet(
        sheet_url: str, generated: Dict
    ) -> QAResult

    async def compare_published(
        approved: Dict, page_url: str
    ) -> QAResult
```

**14. WebScraper** (`app/services/web_scraper.py`)
```python
class WebScraper:
    async def scrape_page(url: str) -> Dict[str, str]
    def extract_meta_tags(html: str) -> Dict[str, str]
    def extract_content(html: str, selectors: Dict) -> Dict
```

**15. ProjectService** (`app/services/project_service.py`)
```python
class ProjectService:
    async def create_from_extraction(
        extracted_data: Dict, job_id: str
    ) -> Project

    async def update_project(
        project_id: str, updates: Dict, user: User
    ) -> Project

    async def add_custom_field(
        project_id: str, key: str, value: Any
    ) -> Project

    async def search_projects(
        filters: ProjectFilters, pagination: Pagination
    ) -> List[Project]

    async def get_project_with_media(
        project_id: str
    ) -> ProjectDetail

    async def track_revision(
        project_id: str, field: str, old: Any, new: Any, user: User
    )
```

**16. PromptService** (`app/services/prompt_service.py`)
```python
class PromptService:
    async def create_prompt(prompt_data: PromptCreate, user: User) -> Prompt
    async def update_prompt(
        prompt_id: str, updates: Dict, user: User
    ) -> Prompt  # Creates new version
    async def get_prompt_versions(prompt_id: str) -> List[PromptVersion]
    async def get_active_prompt(
        website: str, template_type: str, name: str
    ) -> Prompt
```

**17. NotificationService** (`app/services/notification_service.py`)
```python
class NotificationService:
    async def create_notification(
        user_id: str, event_type: str, data: Dict
    ) -> Notification

    async def mark_as_read(notification_id: str, user_id: str) -> None
    async def mark_all_as_read(user_id: str) -> None
    async def get_unread_count(user_id: str) -> int
```

**18. StorageService** (`app/services/storage_service.py`)
```python
class StorageService:
    async def upload_file(
        file_bytes: bytes, blob_path: str, content_type: str
    ) -> str  # Returns public URL

    async def download_file(blob_path: str) -> bytes
    async def delete_file(blob_path: str) -> None
    async def generate_signed_url(
        blob_path: str, expiration_minutes: int
    ) -> str
```

---

## API Endpoints Specification

### Authentication & Users

**POST /api/auth/google**
```python
Request Body:
{
  "token": "google_oauth_token_here"
}

Response (200):
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "user": {
    "id": "uuid",
    "email": "user@your-domain.com",
    "name": "John Doe",
    "picture_url": "https://...",
    "role": "user"
  }
}

Errors:
401: Invalid token
403: Email domain not allowed (@your-domain.com only)
```

**GET /api/auth/me**
```python
Headers: Authorization: Bearer <token>

Response (200):
{
  "id": "uuid",
  "email": "user@your-domain.com",
  "name": "John Doe",
  "role": "user",
  "last_login_at": "2026-01-14T10:30:00Z"
}

Errors:
401: Unauthorized
```

### File Upload & Jobs

**POST /api/upload**
```python
Headers:
  Authorization: Bearer <token>
  Content-Type: multipart/form-data

Form Data:
  file: <pdf_file>
  template_type: "aggregators" | "opr" | "mpp" | "adop" | "adre" | "commercial"
  template_id: "uuid"

Response (200):
{
  "job_id": "uuid",
  "status": "pending",
  "created_at": "2026-01-14T10:30:00Z"
}

Errors:
400: Invalid file type
400: File too large (max 50MB)
413: Payload too large
429: Rate limit exceeded
```

**GET /api/jobs/{job_id}**
```python
Headers: Authorization: Bearer <token>

Response (200):
{
  "id": "uuid",
  "status": "processing" | "completed" | "failed",
  "progress": 75,
  "current_step": "Extracting images",
  "steps": [
    {"id": "upload", "label": "Upload PDF", "status": "completed"},
    {"id": "extract", "label": "Extract text", "status": "completed"},
    {"id": "classify", "label": "Classify images", "status": "in_progress"}
  ],
  "result": {
    "sheet_url": "https://docs.google.com/spreadsheets/...",
    "zip_url": "https://storage.googleapis.com/...",
    "project_id": "uuid"
  },
  "error_message": null
}

Errors:
404: Job not found
403: Not authorized to view this job
```

### Projects

**GET /api/projects**
```python
Headers: Authorization: Bearer <token>

Query Params:
  page: int (default: 1)
  limit: int (default: 50, max: 100)
  search: str (full-text search)
  developer: str
  emirate: str
  status: str
  price_min: float
  price_max: float
  date_from: date
  date_to: date
  sort: str (e.g., "-created_at", "name")

Response (200):
{
  "items": [
    {
      "id": "uuid",
      "name": "Marina Bay Residences",
      "developer": "Emaar",
      "location": "Dubai Marina",
      "starting_price": 1500000,
      "workflow_status": "published",
      "created_at": "2026-01-14T10:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "pages": 3
}
```

**GET /api/projects/{id}**
```python
Response (200):
{
  "id": "uuid",
  "name": "Marina Bay Residences",
  "developer": "Emaar",
  "location": "Dubai Marina",
  "emirate": "Dubai",
  "starting_price": 1500000,
  "property_types": ["apartment", "penthouse"],
  "amenities": ["Pool", "Gym"],
  "images": [
    {
      "id": "uuid",
      "category": "exterior",
      "image_url": "https://...",
      "thumbnail_url": "https://..."
    }
  ],
  "floor_plans": [
    {
      "id": "uuid",
      "unit_type": "1BR",
      "bedrooms": 1,
      "total_sqft": 750,
      "image_url": "https://..."
    }
  ],
  "custom_fields": {
    "sales_contact": "John Smith"
  },
  "created_by": {...},
  "created_at": "2026-01-14T10:30:00Z"
}
```

**PUT /api/projects/{id}**
```python
Request Body:
{
  "name": "Updated Name",
  "starting_price": 1600000,
  "custom_fields": {
    "priority": "high"
  }
}

Response (200):
{
  "id": "uuid",
  "name": "Updated Name",
  ...
}

Errors:
404: Project not found
403: Not authorized to edit
```

### Prompts

**GET /api/prompts**
```python
Query Params:
  website: str
  template_type: str
  search: str

Response (200):
{
  "items": [
    {
      "id": "uuid",
      "name": "Meta Description",
      "website": "opr",
      "template_type": "standard",
      "version": 3,
      "is_active": true,
      "updated_at": "2026-01-14T10:30:00Z"
    }
  ]
}
```

**PUT /api/prompts/{id}**
```python
Request Body:
{
  "content": "Updated prompt content...",
  "change_reason": "Improved clarity"
}

Response (200):
{
  "id": "uuid",
  "version": 4,  // Incremented
  "content": "Updated prompt content...",
  "updated_at": "2026-01-14T10:35:00Z"
}
```

### QA

**POST /api/qa/compare**
```python
Request Body:
{
  "project_id": "uuid",
  "checkpoint_type": "generation",
  "input_content": {...},
  "comparison_target": {...}
}

Response (200):
{
  "id": "uuid",
  "status": "passed" | "failed",
  "matches": 45,
  "differences": 2,
  "missing": 1,
  "extra": 0,
  "result": {
    "differences": [
      {
        "field": "starting_price",
        "expected": "1500000",
        "actual": "1600000"
      }
    ]
  }
}
```

---

## Error Handling

### Error Response Format

```python
{
  "error_code": "UPLOAD_FILE_TOO_LARGE",
  "message": "File exceeds maximum size of 50MB",
  "details": {
    "file_size": 52428800,
    "max_size": 52428800
  },
  "retry_after": null,
  "trace_id": "abc123-def456"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UPLOAD_FILE_TOO_LARGE` | 400 | File exceeds 50MB |
| `UPLOAD_INVALID_FILE_TYPE` | 400 | Not a PDF file |
| `UPLOAD_MALFORMED_PDF` | 400 | PDF corrupted or encrypted |
| `GEMINI_QUOTA_EXCEEDED` | 429 | AI service quota exceeded |
| `PROJECT_NOT_FOUND` | 404 | Project ID doesn't exist |
| `UNAUTHORIZED` | 401 | Invalid or expired token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

### Exception Handling Pattern

```python
# app/api/routes/upload.py
try:
    result = await job_manager.process_job(job_id, ...)
    return result
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except VertexAIQuotaExceeded:
    raise HTTPException(
        status_code=429,
        detail={
            "error_code": "GEMINI_QUOTA_EXCEEDED",
            "message": "AI service quota exceeded",
            "retry_after": 60
        }
    )
except Exception as e:
    logger.exception(f"Unexpected error in job {job_id}")
    sentry_sdk.capture_exception(e)
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Background Jobs (Cloud Tasks)

### Job Processing Flow

```
User uploads PDF → API creates job record → Enqueue to Cloud Tasks →
Worker picks up task → Process job → Update DB → Send notification
```

### Cloud Tasks Setup

```python
# app/services/queue_service.py
from google.cloud import tasks_v2

class JobQueue:
    def __init__(self):
        self.client = tasks_v2.CloudTasksClient()
        self.queue_path = self.client.queue_path(
            "pdp-automation-prod",
            "us-central1",
            "pdp-processing-queue"
        )

    async def enqueue_job(self, job_id: str, file_path: str, ...):
        task = {
            "http_request": {
                "http_method": "POST",
                "url": f"{settings.API_URL}/internal/process-job",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Internal-Auth": settings.INTERNAL_API_KEY
                },
                "body": json.dumps({
                    "job_id": job_id,
                    "file_path": file_path,
                    ...
                }).encode()
            }
        }

        response = self.client.create_task(
            request={"parent": self.queue_path, "task": task}
        )
        return response.name
```

### Retry Configuration

```yaml
# queue.yaml
queue:
- name: pdp-processing-queue
  rate: 10/s
  retry_parameters:
    task_retry_limit: 3
    min_backoff_seconds: 10
    max_backoff_seconds: 300
```

---

## Caching Strategy

### Cache Layers

1. **Gemini Response Cache** (Redis, 30 days)
   - Cache key: `gemini:{prompt_hash}`
   - 70-90% cost savings

2. **Prompt Cache** (Redis, 1 hour)
   - Cache key: `prompt:{id}`
   - Fast retrieval

3. **Project Metadata Cache** (Redis, 5 min)
   - Cache key: `project:{id}:meta`
   - Reduce DB hits

4. **Template Cache** (Redis, 24 hours)
   - Cache key: `templates:list`
   - Rarely changes

### Implementation

```python
# app/services/cache_service.py
from redis import asyncio as aioredis

class CacheService:
    def __init__(self):
        self.redis = aioredis.from_url(settings.REDIS_URL)

    async def get_or_fetch(
        self, key: str, fetch_fn, ttl: int = 300
    ):
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        data = await fetch_fn()
        await self.redis.setex(key, ttl, json.dumps(data))
        return data
```

---

## Document Standards

Each backend document must include:
1. Service/API overview
2. Method signatures with type hints
3. Request/response examples
4. Error handling patterns
5. Code examples in Python
6. Integration points
7. Performance considerations

---

## Quality Checklist

- ✅ All 5 files created
- ✅ All services documented
- ✅ All API endpoints specified
- ✅ Error codes defined
- ✅ Code examples in Python
- ✅ Type hints included
- ✅ Background job patterns clear
- ✅ Caching strategy explained

Begin with `SERVICE_LAYER.md`.