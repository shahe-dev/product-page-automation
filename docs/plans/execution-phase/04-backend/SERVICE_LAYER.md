# Service Layer

**Last Updated:** 2026-01-15
**Related Documents:**
- [System Architecture](../01-architecture/SYSTEM_ARCHITECTURE.md)
- [API Endpoints](./API_ENDPOINTS.md)
- [Background Jobs](./BACKGROUND_JOBS.md)
- [Error Handling](./ERROR_HANDLING.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Service Architecture](#service-architecture)
3. [Core Services](#core-services)
4. [Processing Services](#processing-services)
5. [AI Services](#ai-services)
6. [Integration Services](#integration-services)
7. [Utility Services](#utility-services)
8. [Service Dependencies](#service-dependencies)
9. [Related Documentation](#related-documentation)

---

## Overview

The service layer encapsulates all business logic and external service interactions. Services are stateless, dependency-injected, and follow the Single Responsibility Principle. Each service focuses on a specific domain or integration point.

**Design Principles:**
1. **Single Responsibility** - Each service has one clear purpose
2. **Dependency Injection** - Services receive dependencies via constructor
3. **Async/Await** - All I/O operations are asynchronous
4. **Error Handling** - Services raise specific exceptions caught by API layer
5. **Testability** - Services are easily mockable for unit tests

**Service Location:**
```
backend/
└── app/
    └── services/
        ├── auth_service.py
        ├── job_manager.py
        ├── pdf_processor.py
        ├── anthropic_service.py
        ├── image_classifier.py
        ├── watermark_detector.py
        ├── image_optimizer.py
        ├── floor_plan_extractor.py
        ├── output_organizer.py
        ├── content_generator.py
        ├── content_qa_service.py
        ├── sheets_manager.py
        ├── qa_service.py
        ├── web_scraper.py
        ├── project_service.py
        ├── prompt_service.py
        ├── notification_service.py
        └── storage_service.py
```

---

## Service Architecture

```
┌─────────────────────────────────────────────────────┐
│              API LAYER (FastAPI Routes)             │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 SERVICE LAYER                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Core Services│  │  Processing  │  │   AI     │ │
│  │              │  │   Services   │  │ Services │ │
│  │ - Auth       │  │ - PDF        │  │ - Anthropic │ │
│  │ - Job Mgmt   │  │ - Image      │  │          │ │
│  │ - Project    │  │ - Floor Plan │  │          │ │
│  │ - Prompt     │  │ - Watermark  │  │          │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Integration  │  │   Utility    │  │   QA     │ │
│  │   Services   │  │   Services   │  │ Services │ │
│  │              │  │              │  │          │ │
│  │ - Sheets     │  │ - Storage    │  │ - QA     │ │
│  │ - Drive      │  │ - Cache      │  │ - WebScr │ │
│  │ - Notif      │  │ - Audit      │  │          │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│         EXTERNAL DEPENDENCIES                        │
├─────────────────────────────────────────────────────┤
│  Database  │  Storage  │  Anthropic  │  Google APIs   │
└─────────────────────────────────────────────────────┘
```

---

## Core Services

### 1. AuthService

**Purpose:** Handle user authentication and authorization.

**Location:** `app/services/auth_service.py`

**Methods:**

```python
class AuthService:
    def __init__(self, db: Database):
        self.db = db

    async def verify_google_token(self, token: str) -> GoogleUser:
        """
        Verify Google OAuth token and extract user info.

        Args:
            token: Google OAuth token

        Returns:
            GoogleUser object with user details

        Raises:
            ValueError: If token is invalid
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            return GoogleUser(
                google_id=idinfo['sub'],
                email=idinfo['email'],
                name=idinfo.get('name'),
                picture_url=idinfo.get('picture')
            )
        except ValueError:
            raise ValueError("Invalid Google token")

    async def check_domain_restriction(self, email: str) -> bool:
        """
        Check if email belongs to allowed domain (@your-domain.com).

        Args:
            email: Email address to check

        Returns:
            True if domain is allowed, False otherwise
        """
        return email.endswith('@your-domain.com')

    async def get_or_create_user(self, google_user: GoogleUser) -> User:
        """
        Get existing user or create new one.

        Args:
            google_user: GoogleUser object from OAuth

        Returns:
            User database record

        Raises:
            ValueError: If email domain not allowed
        """
        if not await self.check_domain_restriction(google_user.email):
            raise ValueError("Email domain not allowed")

        user = await self.db.users.find_one({"google_id": google_user.google_id})

        if not user:
            user = await self.db.users.insert_one({
                "google_id": google_user.google_id,
                "email": google_user.email,
                "name": google_user.name,
                "picture_url": google_user.picture_url,
                "role": "user",
                "is_active": True,
                "created_at": datetime.utcnow()
            })

        # Update last login
        await self.db.users.update_one(
            {"id": user.id},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )

        return user

    async def assign_role(self, user_id: str, role: str) -> User:
        """
        Assign role to user (admin only).

        Args:
            user_id: User UUID
            role: Role to assign ("user" or "admin")

        Returns:
            Updated user record

        Raises:
            ValueError: If role is invalid
        """
        if role not in ["user", "admin"]:
            raise ValueError("Invalid role")

        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"role": role}}
        )

        return await self.db.users.find_one({"id": user_id})

    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token (1 hour expiry).

        Args:
            user: User object

        Returns:
            JWT token string
        """
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    def create_refresh_token(self, user: User) -> str:
        """
        Create refresh token (7 days expiry).

        Args:
            user: User object

        Returns:
            Refresh token string
        """
        payload = {
            "sub": str(user.id),
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm="HS256")
```

---

### 2. JobManager

**Purpose:** Manage background processing job lifecycle.

**Location:** `app/services/job_manager.py`

**Methods:**

```python
class JobManager:
    def __init__(
        self,
        db: Database,
        queue: QueueService,
        pdf_processor: PDFProcessor,
        image_classifier: ImageClassifier,
        content_generator: ContentGenerator,
        project_service: ProjectService,
        storage_manager: StorageManager,
        sheets_manager: SheetsManager
    ):
        self.db = db
        self.queue = queue
        self.pdf_processor = pdf_processor
        self.image_classifier = image_classifier
        self.content_generator = content_generator
        self.project_service = project_service
        self.storage_manager = storage_manager
        self.sheets_manager = sheets_manager

    async def create_job(
        self,
        user_id: str,
        website: str,
        template_id: str,
        **kwargs
    ) -> str:
        """
        Create new processing job.

        Args:
            user_id: User UUID
            template_type: Template type ("aggregators", "opr", "mpp", "adop", "adre", "commercial")
            template_id: Template UUID
            **kwargs: Additional job parameters

        Returns:
            Job UUID

        Raises:
            ValueError: If parameters are invalid
        """
        job_id = str(uuid.uuid4())

        await self.db.jobs.insert_one({
            "id": job_id,
            "user_id": user_id,
            "website": website,
            "template_id": template_id,
            "status": "pending",
            "progress": 0,
            "current_step": "Upload PDF",
            "result": None,
            "error_message": None,
            "retry_count": 0,
            "created_at": datetime.utcnow()
        })

        return job_id

    async def process_job(
        self,
        job_id: str,
        pdf_path: str,
        **kwargs
    ) -> None:
        """
        Process job (extract, classify, generate, push to sheets).

        This is the main orchestrator that coordinates all processing steps.

        Args:
            job_id: Job UUID
            pdf_path: GCS path to PDF file
            **kwargs: Additional processing parameters

        Raises:
            Exception: Any processing error (logged and stored in job)
        """
        try:
            await self.update_job_status(job_id, "processing")

            # Step 1: Extract text
            await self.update_job_progress(job_id, 10, "Extracting text")
            extracted_data = await self.pdf_processor.extract_text(pdf_path)

            # Step 2: Extract images
            await self.update_job_progress(job_id, 30, "Extracting images")
            images = await self.pdf_processor.extract_images(pdf_path)

            # Step 3: Classify images
            await self.update_job_progress(job_id, 50, "Classifying images")
            classified_images = await self.image_classifier.classify_batch(images)

            # Step 4: Generate content
            await self.update_job_progress(job_id, 70, "Generating content")
            generated_content = await self.content_generator.generate(extracted_data)

            # Step 5: Create project record
            await self.update_job_progress(job_id, 80, "Creating project record")
            project_id = await self.project_service.create_project(
                extracted_data=extracted_data,
                generated_content=generated_content,
                images=classified_images
            )

            # Step 6: Upload images and create ZIP
            await self.update_job_progress(job_id, 85, "Uploading assets to GCS")
            zip_url = await self.storage_manager.upload_image_zip(
                project_id=project_id,
                images=classified_images
            )

            # Step 7: Push to sheets
            await self.update_job_progress(job_id, 90, "Pushing to Google Sheets")
            sheet_url = await self.sheets_manager.populate_sheet(generated_content)

            # Mark complete
            await self.update_job_result(job_id, {
                "project_id": project_id,
                "sheet_url": sheet_url,
                "zip_url": zip_url
            })

        except Exception as e:
            logger.exception(f"Job {job_id} failed")
            await self.update_job_error(job_id, str(e))
            raise

    async def update_job_status(self, job_id: str, status: str):
        """Update job status."""
        await self.db.jobs.update_one(
            {"id": job_id},
            {"$set": {"status": status}}
        )

    async def update_job_progress(
        self,
        job_id: str,
        progress: int,
        step: str
    ):
        """Update job progress and current step."""
        await self.db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "progress": progress,
                "current_step": step
            }}
        )

    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get job status and result."""
        job = await self.db.jobs.find_one({"id": job_id})

        if not job:
            raise ValueError(f"Job {job_id} not found")

        return JobStatus(
            id=job.id,
            status=job.status,
            progress=job.progress,
            current_step=job.current_step,
            result=job.result,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at
        )

    async def cancel_job(self, job_id: str) -> None:
        """Cancel running job."""
        await self.db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "cancelled",
                "completed_at": datetime.utcnow()
            }}
        )
```

---

### 3. ProjectService

**Purpose:** Manage project CRUD operations and search.

**Location:** `app/services/project_service.py`

**Methods:**

```python
class ProjectService:
    def __init__(self, db: Database):
        self.db = db

    async def create_from_extraction(
        self,
        extracted_data: Dict,
        job_id: str,
        user_id: str
    ) -> Project:
        """
        Create project from extracted data.

        Args:
            extracted_data: Extracted data from PDF
            job_id: Job UUID
            user_id: User UUID

        Returns:
            Created project
        """
        project_id = str(uuid.uuid4())

        await self.db.projects.insert_one({
            "id": project_id,
            "name": extracted_data.get("name"),
            "developer": extracted_data.get("developer"),
            "location": extracted_data.get("location"),
            "emirate": extracted_data.get("emirate"),
            "starting_price": extracted_data.get("starting_price"),
            "property_types": extracted_data.get("property_types", []),
            "amenities": extracted_data.get("amenities", []),
            "workflow_status": "draft",
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "processing_job_id": job_id
        })

        return await self.get_project(project_id)

    async def update_project(
        self,
        project_id: str,
        updates: Dict,
        user: User
    ) -> Project:
        """
        Update project fields.

        Args:
            project_id: Project UUID
            updates: Dictionary of field updates
            user: Current user

        Returns:
            Updated project

        Raises:
            ValueError: If project not found
            PermissionError: If user not authorized
        """
        project = await self.get_project(project_id)

        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Check permissions
        if project.created_by != user.id and user.role != "admin":
            raise PermissionError("Not authorized to update this project")

        # Track revisions
        for field, new_value in updates.items():
            old_value = getattr(project, field, None)

            if old_value != new_value:
                await self.track_revision(
                    project_id, field, old_value, new_value, user
                )

        # Update project
        await self.db.projects.update_one(
            {"id": project_id},
            {"$set": {
                **updates,
                "last_modified_by": user.id,
                "last_modified_at": datetime.utcnow()
            }}
        )

        return await self.get_project(project_id)

    async def search_projects(
        self,
        filters: ProjectFilters,
        pagination: Pagination
    ) -> List[Project]:
        """
        Search projects with filters and pagination.

        Args:
            filters: Filter criteria
            pagination: Pagination parameters

        Returns:
            List of projects matching criteria
        """
        query = {}

        # Full-text search
        if filters.search:
            query["$text"] = {"$search": filters.search}

        # Developer filter
        if filters.developer:
            query["developer"] = filters.developer

        # Emirate filter
        if filters.emirate:
            query["emirate"] = filters.emirate

        # Status filter
        if filters.status:
            query["workflow_status"] = filters.status

        # Price range
        if filters.price_min or filters.price_max:
            query["starting_price"] = {}
            if filters.price_min:
                query["starting_price"]["$gte"] = filters.price_min
            if filters.price_max:
                query["starting_price"]["$lte"] = filters.price_max

        # Date range
        if filters.date_from or filters.date_to:
            query["created_at"] = {}
            if filters.date_from:
                query["created_at"]["$gte"] = filters.date_from
            if filters.date_to:
                query["created_at"]["$lte"] = filters.date_to

        # Pagination
        skip = (pagination.page - 1) * pagination.limit
        sort_field = pagination.sort.lstrip("-")
        sort_order = -1 if pagination.sort.startswith("-") else 1

        projects = await self.db.projects.find(query)\
            .sort(sort_field, sort_order)\
            .skip(skip)\
            .limit(pagination.limit)\
            .to_list()

        return projects

    async def track_revision(
        self,
        project_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
        user: User
    ):
        """Track field revision for audit trail."""
        await self.db.project_revisions.insert_one({
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "field": field,
            "old_value": str(old_value) if old_value is not None else None,
            "new_value": str(new_value) if new_value is not None else None,
            "changed_by": user.id,
            "created_at": datetime.utcnow()
        })
```

---

### 4. PromptService

**Purpose:** Manage version-controlled prompt library.

**Location:** `app/services/prompt_service.py`

**Methods:**

```python
class PromptService:
    def __init__(self, db: Database):
        self.db = db

    async def create_prompt(
        self,
        prompt_data: PromptCreate,
        user: User
    ) -> Prompt:
        """
        Create new prompt.

        Args:
            prompt_data: Prompt creation data
            user: Current user

        Returns:
            Created prompt
        """
        prompt_id = str(uuid.uuid4())

        await self.db.prompts.insert_one({
            "id": prompt_id,
            "name": prompt_data.name,
            "website": prompt_data.website,
            "template_type": prompt_data.template_type,
            "content": prompt_data.content,
            "character_limit": prompt_data.character_limit,
            "version": 1,
            "is_active": True,
            "created_by": user.id,
            "created_at": datetime.utcnow()
        })

        # Create version record
        await self._create_version(prompt_id, 1, prompt_data.content, user)

        return await self.get_prompt(prompt_id)

    async def update_prompt(
        self,
        prompt_id: str,
        updates: Dict,
        user: User
    ) -> Prompt:
        """
        Update prompt (creates new version).

        Args:
            prompt_id: Prompt UUID
            updates: Update data (must include change_reason)
            user: Current user

        Returns:
            Updated prompt with incremented version

        Raises:
            ValueError: If prompt not found
        """
        prompt = await self.get_prompt(prompt_id)

        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        new_version = prompt.version + 1

        # Update prompt
        await self.db.prompts.update_one(
            {"id": prompt_id},
            {"$set": {
                "content": updates["content"],
                "version": new_version,
                "updated_by": user.id,
                "updated_at": datetime.utcnow()
            }}
        )

        # Create version record
        await self._create_version(
            prompt_id,
            new_version,
            updates["content"],
            user,
            updates.get("change_reason")
        )

        return await self.get_prompt(prompt_id)

    async def get_active_prompt(
        self,
        website: str,
        template_type: str,
        name: str
    ) -> Prompt:
        """
        Get active prompt for website/template/name.

        Args:
            website: Website identifier
            template_type: Template type
            name: Prompt name

        Returns:
            Active prompt

        Raises:
            ValueError: If no active prompt found
        """
        prompt = await self.db.prompts.find_one({
            "website": website,
            "template_type": template_type,
            "name": name,
            "is_active": True
        })

        if not prompt:
            raise ValueError(
                f"No active prompt found for {website}/{template_type}/{name}"
            )

        return prompt

    async def _create_version(
        self,
        prompt_id: str,
        version: int,
        content: str,
        user: User,
        change_reason: str = None
    ):
        """Create version record."""
        await self.db.prompt_versions.insert_one({
            "id": str(uuid.uuid4()),
            "prompt_id": prompt_id,
            "version": version,
            "content": content,
            "change_reason": change_reason,
            "created_by": user.id,
            "created_at": datetime.utcnow()
        })
```

---

## Processing Services

### 5. PDFProcessor

**Purpose:** Triple extraction from PDF documents -- embedded images, page renders, and per-page text.

**Location:** `app/services/pdf_processor.py`

**Methods:**

```python
import fitz  # PyMuPDF
import pymupdf4llm
from app.utils.pdf_helpers import ExtractionResult, ExtractedImage

class PDFProcessor:
    def __init__(self, render_dpi: int = 300, max_pages: int = 100):
        self.render_dpi = render_dpi
        self.dpi_scale = render_dpi / 72
        self.max_pages = max_pages

    async def extract_all(self, pdf_bytes: bytes) -> ExtractionResult:
        """
        Run triple extraction on a PDF document.

        1. Embedded extraction -- raster XObjects via doc.extract_image(xref)
        2. Page rendering -- full page at 300 DPI via page.get_pixmap()
        3. Text extraction -- per-page markdown via pymupdf4llm.to_markdown()

        Args:
            pdf_bytes: Raw PDF file content

        Returns:
            ExtractionResult with embedded, page_renders, page_text_map,
            total_pages, and errors

        Raises:
            ValueError: If PDF is invalid, corrupted, or exceeds size limit
        """

    def _extract_embedded(self, doc, page, page_num) -> list[ExtractedImage]:
        """Extract all embedded raster images from a page."""

    def _render_page(self, page, page_num) -> ExtractedImage | None:
        """Render a full page at configured DPI."""

    def _extract_text(self, pdf_bytes: bytes, total_pages: int) -> dict[int, str]:
        """Extract per-page text as markdown using pymupdf4llm.
        Returns dict mapping 1-indexed page numbers to markdown text.
        Failures are caught and logged (returns empty dict)."""

    def get_extraction_summary(self, result: ExtractionResult) -> dict:
        """Build a summary dict for the extraction result."""
```

---

## AI Services

### 6. AnthropicService

**Purpose:** Interact with Anthropic API for text and vision tasks.

**Location:** `app/services/anthropic_service.py`

**Methods:**

```python
class AnthropicService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def extract_data_from_pdf(
        self,
        pdf_pages: List[bytes],
        prompt: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from PDF using Claude Sonnet 4.5.

        Args:
            pdf_pages: List of PDF page text
            prompt: Extraction prompt

        Returns:
            Structured data dictionary

        Raises:
            AnthropicError: If API call fails
        """
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            system=prompt,
            messages=[
                {"role": "user", "content": "\n\n".join(pdf_pages)}
            ]
        )

        return json.loads(response.content[0].text)

    async def generate_content(
        self,
        extracted_data: Dict,
        template: str,
        prompt: str
    ) -> Dict[str, str]:
        """
        Generate SEO content from extracted data using Claude Sonnet 4.5.

        Args:
            extracted_data: Extracted project data
            template: Content template
            prompt: Generation prompt

        Returns:
            Generated content dictionary

        Raises:
            AnthropicError: If API call fails
        """
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            system=prompt,
            messages=[
                {"role": "user", "content": json.dumps(extracted_data)}
            ]
        )

        return json.loads(response.content[0].text)

    async def classify_image(self, image_bytes: bytes) -> str:
        """
        Classify image category using Claude Sonnet 4.5 vision.

        Args:
            image_bytes: Image binary data

        Returns:
            Category: "interior", "exterior", "amenity", "logo", "floor_plan"

        Raises:
            AnthropicError: If API call fails
        """
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Classify this real estate image into one category: interior, exterior, amenity, logo, or floor_plan. Respond with only the category name."
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        )

        return response.content[0].text.strip().lower()

    async def detect_watermark(self, image_bytes: bytes) -> Optional[BoundingBox]:
        """
        Detect watermark in image using Claude Sonnet 4.5 vision.

        Args:
            image_bytes: Image binary data

        Returns:
            BoundingBox if watermark found, None otherwise

        Raises:
            AnthropicError: If API call fails
        """
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Detect if there's a watermark in this image. If found, provide the bounding box coordinates as JSON: {\"x\": int, \"y\": int, \"width\": int, \"height\": int}. If no watermark, respond with null."
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        )

        result = json.loads(response.content[0].text)

        if result:
            return BoundingBox(**result)

        return None

    async def extract_floor_plan_data(
        self,
        image_bytes: bytes
    ) -> Dict[str, Any]:
        """
        Extract data from floor plan image using Claude Sonnet 4.5 vision.

        Args:
            image_bytes: Floor plan image data

        Returns:
            Extracted floor plan data

        Raises:
            AnthropicError: If API call fails
        """
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the following data from this floor plan: unit_type (e.g., 1BR, 2BR), bedrooms (int), bathrooms (int), total_sqft (float), balcony_sqft (float), builtup_sqft (float). Return as JSON."
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        )

        return json.loads(response.content[0].text)
```

---

## Integration Services

### 7. SheetsManager

**Purpose:** Google Sheets integration for content output.

**Location:** `app/services/sheets_manager.py`

```python
import asyncio

class SheetsManager:
    def __init__(self):
        self.client = gspread.authorize(credentials)

    async def create_from_template(self, template_id: str) -> str:
        """
        Create new sheet from template.

        Args:
            template_id: Template sheet ID

        Returns:
            New sheet URL

        Raises:
            Exception: If creation fails
        """
        def _create():
            template_sheet = self.client.open_by_key(template_id)
            new_sheet = template_sheet.copy(title=f"PDP_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            # Share with @your-domain.com organization
            new_sheet.share('your-domain.com', perm_type='domain', role='writer', with_link=True)
            return new_sheet.url

        return await asyncio.to_thread(_create)

    async def populate_sheet(
        self,
        sheet_id: str,
        content: Dict,
        field_mapping: Dict
    ) -> None:
        """
        Populate sheet with content.

        Args:
            sheet_id: Sheet ID
            content: Content dictionary
            field_mapping: Field to cell mapping

        Raises:
            Exception: If population fails
        """
        def _populate():
            sheet = self.client.open_by_key(sheet_id).sheet1

            # Prepare batch update
            updates = []

            for field, cell in field_mapping.items():
                value = content.get(field)
                if value is not None:
                    updates.append({
                        "range": cell,
                        "values": [[value]]
                    })

            # Batch update
            sheet.batch_update(updates)

        await asyncio.to_thread(_populate)
```

---

## Utility Services

### 8. StorageService

**Purpose:** Google Cloud Storage operations.

**Location:** `app/services/storage_service.py`

```python
class StorageService:
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = settings.GCS_BUCKET

    async def upload_file(
        self,
        file_bytes: bytes,
        blob_path: str,
        content_type: str
    ) -> str:
        """
        Upload file to GCS.

        Args:
            file_bytes: File binary data
            blob_path: Destination path in bucket
            content_type: MIME type

        Returns:
            Public URL

        Raises:
            Exception: If upload fails
        """
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_path)

        blob.upload_from_string(
            file_bytes,
            content_type=content_type
        )

        return blob.public_url

    async def download_file(self, blob_path: str) -> bytes:
        """Download file from GCS."""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_path)

        return blob.download_as_bytes()

    async def delete_file(self, blob_path: str) -> None:
        """Delete file from GCS."""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_path)
        blob.delete()

    async def generate_signed_url(
        self,
        blob_path: str,
        expiration_minutes: int
    ) -> str:
        """Generate signed URL for temporary access."""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=expiration_minutes),
            method="GET"
        )

        return url
```

---

## Service Dependencies

```
AuthService
  └─ Database

JobManager
  ├─ Database
  ├─ QueueService
  ├─ PDFProcessor
  ├─ ImageClassifier
  ├─ ContentGenerator
  └─ SheetsManager

ProjectService
  └─ Database

PromptService
  └─ Database

PDFProcessor
  (no dependencies)

AnthropicService
  (no dependencies)

SheetsManager
  (no dependencies)

StorageService
  (no dependencies)
```

---

## Related Documentation

- [API Endpoints](./API_ENDPOINTS.md) - REST API implementation
- [Background Jobs](./BACKGROUND_JOBS.md) - Async job processing
- [Error Handling](./ERROR_HANDLING.md) - Error patterns
- [System Architecture](../01-architecture/SYSTEM_ARCHITECTURE.md) - Overall design

---

**Last Updated:** 2026-01-15
