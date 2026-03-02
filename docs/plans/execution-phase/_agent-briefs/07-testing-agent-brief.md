# Agent Briefing: Testing Documentation Agent

**Agent ID:** testing-docs-agent
**Batch:** 3 (Operations)
**Priority:** P2 - Quality Assurance
**Est. Context Usage:** 34,000 tokens

---

## Your Mission

Create **5 testing documentation files** covering test strategy, unit tests, integration tests, E2E tests, and performance testing.

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/07-testing/`

---

## Files You Must Create

1. `TEST_STRATEGY.md` (300-350 lines) - Overall testing approach and standards
2. `UNIT_TEST_PATTERNS.md` (400-500 lines) - How to write unit tests (pytest)
3. `INTEGRATION_TESTS.md` (350-400 lines) - API testing patterns (httpx)
4. `E2E_TEST_SCENARIOS.md` (400-500 lines) - End-to-end test cases (Playwright)
5. `PERFORMANCE_TESTING.md` (300-350 lines) - Load testing approach (Locust)

**Total Output:** ~1,750-2,100 lines across 5 files

---

## Testing Stack

**Backend Testing:**
- **Framework:** pytest 8.x
- **Async:** pytest-asyncio
- **HTTP Client:** httpx (for integration tests)
- **Mocking:** pytest-mock, unittest.mock
- **Coverage:** pytest-cov
- **Fixtures:** pytest fixtures

**Frontend Testing:**
- **Framework:** Vitest
- **Component Testing:** React Testing Library
- **E2E:** Playwright
- **Mocking:** MSW (Mock Service Worker)

**Performance Testing:**
- **Load Testing:** Locust
- **Monitoring:** Cloud Monitoring metrics

**Security Testing:**
- **OWASP:** OWASP ZAP
- **Dependency Scanning:** Safety, Snyk

---

## 1. Test Strategy

**Coverage Targets:**
| Component | Target | Critical Areas |
|-----------|--------|----------------|
| Services | 90%+ | All business logic paths |
| API Routes | 80%+ | Happy path + error cases |
| Models | 95%+ | Validation logic |
| Utils | 85%+ | Edge cases |
| Frontend | 70%+ | User interactions |

**Test Pyramid:**
```
        E2E (5%)
      ┌─────────┐
     Integration (15%)
    ┌───────────────┐
   Unit Tests (80%)
  ┌─────────────────────┐
```

**Testing Phases:**
1. **Unit Tests** - Run on every commit
2. **Integration Tests** - Run on PR creation
3. **E2E Tests** - Run before merge to main
4. **Performance Tests** - Run weekly on staging
5. **Security Tests** - Run monthly

**Naming Conventions:**
```python
# Unit tests
test_<function_name>_<scenario>_<expected_result>

# Examples
test_extract_images_from_valid_pdf_returns_image_list()
test_extract_images_from_encrypted_pdf_raises_value_error()
test_classify_image_with_interior_returns_interior_category()
```

**Test Organization:**
```
backend/tests/
├── unit/
│   ├── test_pdf_processor.py
│   ├── test_image_classifier.py
│   └── test_content_generator.py
├── integration/
│   ├── test_api_upload.py
│   ├── test_api_projects.py
│   └── test_api_qa.py
├── e2e/
│   ├── test_upload_flow.py
│   └── test_approval_flow.py
├── performance/
│   └── locustfile.py
├── fixtures/
│   ├── sample.pdf
│   └── test_data.json
└── conftest.py  # Shared fixtures
```

---

## 2. Unit Test Patterns

**Testing Services:**
```python
# tests/unit/test_pdf_processor.py
import pytest
from app.services.pdf_processor import PDFProcessor

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a valid test PDF"""
    pdf_path = tmp_path / "test.pdf"
    # Create minimal PDF
    return str(pdf_path)

def test_extract_images_from_valid_pdf_returns_list(sample_pdf):
    processor = PDFProcessor()
    images = processor.extract_images(sample_pdf, "/tmp/out")

    assert isinstance(images, list)
    assert len(images) > 0
    assert all(Path(img).exists() for img in images)

def test_extract_images_from_nonexistent_pdf_raises_error():
    processor = PDFProcessor()

    with pytest.raises(FileNotFoundError):
        processor.extract_images("/fake/path.pdf", "/tmp/out")

def test_extract_images_from_encrypted_pdf_raises_value_error(encrypted_pdf):
    processor = PDFProcessor()

    with pytest.raises(ValueError, match="encrypted"):
        processor.extract_images(encrypted_pdf, "/tmp/out")
```

**Mocking External Services:**
```python
# tests/unit/test_anthropic_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.anthropic_service import AnthropicService

@pytest.mark.asyncio
async def test_classify_image_returns_category(mocker):
    # Mock Anthropic client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="interior"))]
    mock_client.chat.completions.create.return_value = mock_response

    mocker.patch(
        'app.services.anthropic_service.AsyncAnthropic',
        return_value=mock_client
    )

    service = AnthropicService()
    category = await service.classify_image(b"image_bytes")

    assert category == "interior"
    mock_client.chat.completions.create.assert_called_once()
```

**Testing Async Functions:**
```python
@pytest.mark.asyncio
async def test_process_job_updates_progress():
    job_manager = JobManager()

    job_id = await job_manager.create_job(...)

    await job_manager.process_job(job_id, ...)

    status = await job_manager.get_job_status(job_id)
    assert status["progress"] == 100
    assert status["status"] == "completed"
```

**Database Testing (with Test DB):**
```python
# conftest.py
@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# test_project_service.py
@pytest.mark.asyncio
async def test_create_project_stores_in_database(test_db):
    service = ProjectService(test_db)

    project = await service.create_from_extraction({
        "name": "Test Project",
        "developer": "Test Dev"
    }, job_id="test-job")

    assert project.id is not None
    assert project.name == "Test Project"
```

---

## 3. Integration Tests

**API Testing Pattern:**
```python
# tests/integration/test_api_upload.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_upload_pdf_creates_job():
    async with AsyncClient(app=app, base_url="http://test") as client:
        with open("tests/fixtures/sample.pdf", "rb") as f:
            response = await client.post(
                "/api/upload",
                files={"file": ("sample.pdf", f, "application/pdf")},
                data={"website": "opr", "template_id": "template1"}
            )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_upload_non_pdf_returns_400():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"not a pdf", "text/plain")}
        )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["message"]
```

**Authentication Testing:**
```python
@pytest.mark.asyncio
async def test_protected_route_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/projects")

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_route_requires_admin_role(user_token):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            "/api/projects/123",
            headers={"Authorization": f"Bearer {user_token}"}
        )

    assert response.status_code == 403
```

**Full Job Flow Test:**
```python
@pytest.mark.asyncio
async def test_full_job_flow_completes_successfully():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Upload PDF
        with open("tests/fixtures/sample.pdf", "rb") as f:
            response = await client.post("/api/upload", files={"file": f})
        job_id = response.json()["job_id"]

        # 2. Poll status until complete
        for _ in range(30):
            response = await client.get(f"/api/jobs/{job_id}")
            status = response.json()["status"]
            if status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

        # 3. Verify result
        assert status == "completed"
        result = response.json()["result"]
        assert result["sheet_url"]
        assert len(result["extracted_images"]) > 0
```

---

## 4. E2E Test Scenarios

**Using Playwright:**
```python
# tests/e2e/test_upload_flow.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
async def test_user_uploads_brochure_and_views_result():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # 1. Login
        await page.goto("http://localhost:5174/login")
        await page.click("button:text('Login with Google')")
        # Mock OAuth flow
        await page.fill("#email", "test@your-domain.com")
        await page.fill("#password", "password")
        await page.click("button:text('Sign in')")

        # 2. Navigate to processing page
        await page.goto("http://localhost:5174/processing")

        # 3. Upload file
        await page.set_input_files(
            "#file-upload",
            "tests/fixtures/sample.pdf"
        )
        await page.select_option("#website", "opr")
        await page.click("button:text('Generate Content')")

        # 4. Wait for processing
        await page.wait_for_selector(
            "text=Complete",
            timeout=120000
        )

        # 5. Verify results page
        assert await page.is_visible("text=Google Sheet:")
        assert await page.is_visible("text=Download ZIP")

        # 6. Check project created
        await page.goto("http://localhost:5174/projects")
        await page.wait_for_selector("text=Test Project")

        await browser.close()
```

**Critical User Journeys:**
1. **Content Creator:** Upload → Review → Submit for Approval
2. **Marketing Manager:** Approve → Request Revision → Approve
3. **Publisher:** Download Assets → Create Page → Mark Published
4. **Admin:** Manage Users → View Audit Log → Export Data

---

## 5. Performance Testing

**Locust Load Test:**
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class PDPAutomationUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        # Login once
        response = self.client.post("/api/auth/google", json={
            "token": "test_token"
        })
        self.token = response.json()["access_token"]

    @task(10)
    def list_projects(self):
        self.client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(5)
    def get_project_detail(self):
        self.client.get(
            "/api/projects/test-id",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def upload_pdf(self):
        with open("tests/fixtures/sample.pdf", "rb") as f:
            self.client.post(
                "/api/upload",
                files={"file": ("sample.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {self.token}"}
            )
```

**Performance Targets:**
- **Upload endpoint:** < 2s response time (p95)
- **List projects:** < 500ms (p95)
- **Project detail:** < 300ms (p95)
- **Concurrent users:** 100 without errors
- **Job processing:** < 5 min for average brochure

**Running Tests:**
```bash
# Run load test
locust -f tests/performance/locustfile.py \
  --host http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m

# Results in web UI: http://localhost:8089
```

---

## Test Commands

```bash
# Backend unit tests
cd backend
pytest tests/unit -v --cov=app --cov-report=html

# Backend integration tests
pytest tests/integration -v

# Backend E2E tests
pytest tests/e2e -v -m e2e

# Frontend unit tests
cd frontend
npm test

# Frontend E2E tests
npx playwright test

# Run all tests
pytest tests/ -v --cov=app

# Coverage report
open htmlcov/index.html
```

---

## Quality Checklist

- ✅ All 5 files created
- ✅ Test strategy defined
- ✅ Unit test patterns with examples
- ✅ Integration test patterns
- ✅ E2E scenarios documented
- ✅ Performance testing approach
- ✅ Code examples in Python/TypeScript
- ✅ Commands for running tests

Begin with `TEST_STRATEGY.md`.