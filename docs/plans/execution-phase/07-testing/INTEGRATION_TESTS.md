# Integration Tests

**Version:** 1.0
**Last Updated:** 2025-01-15
**Owner:** QA Team

---

## Overview

Integration tests validate the interaction between multiple components of the PDP Automation Platform. Unlike unit tests that test components in isolation, integration tests verify that services, APIs, databases, and external dependencies work correctly together.

### What is an Integration Test?

An integration test:
- Tests interactions between 2+ components
- Uses real database (test instance)
- May mock external APIs (Anthropic, Google)
- Executes in < 5 seconds per test
- Validates API contracts and data flow
- Represents 15% of our test pyramid

### Integration Testing Goals

- **Component Interaction:** Verify services work together correctly
- **API Contract Validation:** Ensure API endpoints return expected data
- **Database Integration:** Test data persistence and retrieval
- **Error Propagation:** Validate error handling across layers
- **Authentication Flow:** Test auth middleware and permissions

---

## Testing Framework Setup

### httpx for API Testing

**Installation:**
```bash
pip install httpx pytest-asyncio
```

**Basic Setup:**
```python
# tests/integration/conftest.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    """Create async HTTP client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### Test Database Configuration

**conftest.py:**
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.database import get_db

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/pdp_test"

@pytest.fixture(scope="function")
async def test_db():
    """Create test database for each test"""
    # Create engine
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    # Cleanup - drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
def override_get_db(test_db):
    """Override database dependency for testing"""
    async def _get_test_db():
        yield test_db

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()
```

---

## API Endpoint Testing

### Upload API Tests

**tests/integration/test_api_upload.py:**
```python
import pytest
from httpx import AsyncClient
from pathlib import Path

class TestUploadAPI:
    """Integration tests for file upload API"""

    @pytest.mark.asyncio
    async def test_upload_pdf_creates_job_and_returns_job_id(
        self, client: AsyncClient, sample_pdf
    ):
        """Should upload PDF, create job, and return job ID"""
        # Arrange
        with open(sample_pdf, "rb") as f:
            files = {"file": ("sample.pdf", f, "application/pdf")}
            data = {
                "website": "opr",
                "template_id": "template1"
            }

            # Act
            response = await client.post("/api/upload", files=files, data=data)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "job_id" in response_data
        assert response_data["status"] == "pending"
        assert response_data["website"] == "opr"

    @pytest.mark.asyncio
    async def test_upload_without_file_returns_400_error(
        self, client: AsyncClient
    ):
        """Should return 400 when no file is provided"""
        # Act
        response = await client.post(
            "/api/upload",
            data={"website": "opr"}
        )

        # Assert
        assert response.status_code == 400
        assert "file is required" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_upload_non_pdf_file_returns_400_error(
        self, client: AsyncClient
    ):
        """Should reject non-PDF files"""
        # Arrange
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}

        # Act
        response = await client.post("/api/upload", files=files)

        # Assert
        assert response.status_code == 400
        assert "invalid file type" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_upload_pdf_exceeding_size_limit_returns_413_error(
        self, client: AsyncClient
    ):
        """Should reject files larger than 50MB"""
        # Arrange - create large file
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        files = {"file": ("large.pdf", large_content, "application/pdf")}

        # Act
        response = await client.post("/api/upload", files=files)

        # Assert
        assert response.status_code == 413
        assert "file too large" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_upload_with_invalid_website_returns_400_error(
        self, client: AsyncClient, sample_pdf
    ):
        """Should validate website parameter"""
        # Arrange
        with open(sample_pdf, "rb") as f:
            files = {"file": ("sample.pdf", f, "application/pdf")}
            data = {"website": "invalid-website"}

            # Act
            response = await client.post("/api/upload", files=files, data=data)

        # Assert
        assert response.status_code == 400
        assert "invalid website" in response.json()["message"].lower()
```

---

## Project API Tests

**tests/integration/test_api_projects.py:**
```python
import pytest
from httpx import AsyncClient
from app.models import Project, ProjectStatus

class TestProjectAPI:
    """Integration tests for project management API"""

    @pytest.mark.asyncio
    async def test_list_projects_returns_paginated_results(
        self, client: AsyncClient, override_get_db, auth_token
    ):
        """Should return paginated list of projects"""
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Act
        response = await client.get(
            "/api/projects?page=1&limit=10",
            headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_projects_without_auth_returns_401_error(
        self, client: AsyncClient
    ):
        """Should require authentication"""
        # Act
        response = await client.get("/api/projects")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_project_by_id_returns_project_details(
        self, client: AsyncClient, test_db, auth_token
    ):
        """Should return project details by ID"""
        # Arrange
        project = Project(
            name="Test Project",
            developer="Test Developer",
            website="opr",
            status=ProjectStatus.DRAFT
        )
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)

        headers = {"Authorization": f"Bearer {auth_token}"}

        # Act
        response = await client.get(
            f"/api/projects/{project.id}",
            headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(project.id)
        assert data["name"] == "Test Project"
        assert data["developer"] == "Test Developer"

    @pytest.mark.asyncio
    async def test_get_nonexistent_project_returns_404_error(
        self, client: AsyncClient, auth_token
    ):
        """Should return 404 for non-existent project"""
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Act
        response = await client.get(
            "/api/projects/99999999-9999-9999-9999-999999999999",
            headers=headers
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project_modifies_project_data(
        self, client: AsyncClient, test_db, auth_token
    ):
        """Should update project with new data"""
        # Arrange
        project = Project(
            name="Original Name",
            developer="Original Developer",
            website="opr"
        )
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)

        headers = {"Authorization": f"Bearer {auth_token}"}
        update_data = {
            "name": "Updated Name",
            "location": "Dubai Marina"
        }

        # Act
        response = await client.patch(
            f"/api/projects/{project.id}",
            headers=headers,
            json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["location"] == "Dubai Marina"
        assert data["developer"] == "Original Developer"  # Unchanged

    @pytest.mark.asyncio
    async def test_delete_project_removes_from_database(
        self, client: AsyncClient, test_db, admin_token
    ):
        """Should delete project (admin only)"""
        # Arrange
        project = Project(
            name="To Delete",
            developer="Dev",
            website="opr"
        )
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)

        headers = {"Authorization": f"Bearer {admin_token}"}

        # Act
        response = await client.delete(
            f"/api/projects/{project.id}",
            headers=headers
        )

        # Assert
        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/projects/{project.id}",
            headers=headers
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_as_non_admin_returns_403_error(
        self, client: AsyncClient, test_db, auth_token
    ):
        """Should prevent non-admin users from deleting projects"""
        # Arrange
        project = Project(name="Test", developer="Dev", website="opr")
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)

        headers = {"Authorization": f"Bearer {auth_token}"}

        # Act
        response = await client.delete(
            f"/api/projects/{project.id}",
            headers=headers
        )

        # Assert
        assert response.status_code == 403
```

---

## Job Status and Flow Testing

**tests/integration/test_job_flow.py:**
```python
import pytest
import asyncio
from httpx import AsyncClient

class TestJobFlow:
    """Integration tests for complete job processing flow"""

    @pytest.mark.asyncio
    async def test_full_job_flow_from_upload_to_completion(
        self, client: AsyncClient, sample_pdf, auth_token
    ):
        """Should complete full job flow: upload -> process -> complete"""
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: Upload PDF
        with open(sample_pdf, "rb") as f:
            files = {"file": ("sample.pdf", f, "application/pdf")}
            data = {"website": "opr", "template_id": "template1"}

            upload_response = await client.post(
                "/api/upload",
                files=files,
                data=data,
                headers=headers
            )

        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]

        # Step 2: Poll job status until complete
        max_attempts = 60  # 60 seconds timeout
        for attempt in range(max_attempts):
            status_response = await client.get(
                f"/api/jobs/{job_id}",
                headers=headers
            )
            assert status_response.status_code == 200

            job_data = status_response.json()
            status = job_data["status"]

            if status == "completed":
                break
            elif status == "failed":
                pytest.fail(f"Job failed: {job_data.get('error')}")

            await asyncio.sleep(1)
        else:
            pytest.fail("Job did not complete within timeout")

        # Step 3: Verify job result
        assert job_data["status"] == "completed"
        assert "result" in job_data
        result = job_data["result"]

        assert "sheet_url" in result
        assert "project_id" in result
        assert len(result["extracted_images"]) > 0

        # Step 4: Verify project was created
        project_response = await client.get(
            f"/api/projects/{result['project_id']}",
            headers=headers
        )
        assert project_response.status_code == 200
        project_data = project_response.json()
        assert project_data["name"]
        assert project_data["status"] == "draft"

    @pytest.mark.asyncio
    async def test_job_status_updates_during_processing(
        self, client: AsyncClient, sample_pdf, auth_token
    ):
        """Should update job status through processing stages"""
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Upload file
        with open(sample_pdf, "rb") as f:
            upload_response = await client.post(
                "/api/upload",
                files={"file": ("sample.pdf", f, "application/pdf")},
                data={"website": "opr"},
                headers=headers
            )
        job_id = upload_response.json()["job_id"]

        # Track status changes
        seen_statuses = set()
        for _ in range(30):
            response = await client.get(f"/api/jobs/{job_id}", headers=headers)
            status = response.json()["status"]
            seen_statuses.add(status)

            if status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

        # Verify progression through statuses
        assert "pending" in seen_statuses or "processing" in seen_statuses
        assert "completed" in seen_statuses or "failed" in seen_statuses

    @pytest.mark.asyncio
    async def test_cancel_job_stops_processing(
        self, client: AsyncClient, sample_pdf, auth_token
    ):
        """Should cancel job and stop processing"""
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Upload and start job
        with open(sample_pdf, "rb") as f:
            upload_response = await client.post(
                "/api/upload",
                files={"file": ("sample.pdf", f, "application/pdf")},
                headers=headers
            )
        job_id = upload_response.json()["job_id"]

        # Wait a moment for processing to start
        await asyncio.sleep(2)

        # Act: Cancel job
        cancel_response = await client.post(
            f"/api/jobs/{job_id}/cancel",
            headers=headers
        )

        # Assert
        assert cancel_response.status_code == 200

        # Verify job is cancelled
        status_response = await client.get(
            f"/api/jobs/{job_id}",
            headers=headers
        )
        assert status_response.json()["status"] == "cancelled"
```

---

## Authentication and Authorization Tests

**tests/integration/test_auth.py:**
```python
import pytest
from httpx import AsyncClient

class TestAuthentication:
    """Integration tests for authentication and authorization"""

    @pytest.mark.asyncio
    async def test_login_with_valid_google_token_returns_access_token(
        self, client: AsyncClient, mocker
    ):
        """Should authenticate user with valid Google token"""
        # Arrange
        mock_google_verify = mocker.patch(
            'app.services.auth_service.verify_google_token'
        )
        mock_google_verify.return_value = {
            "email": "test@your-domain.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg"
        }

        # Act
        response = await client.post(
            "/api/auth/google",
            json={"token": "valid_google_token"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_invalid_token_returns_401_error(
        self, client: AsyncClient, mocker
    ):
        """Should reject invalid Google token"""
        # Arrange
        mock_google_verify = mocker.patch(
            'app.services.auth_service.verify_google_token'
        )
        mock_google_verify.side_effect = ValueError("Invalid token")

        # Act
        response = await client.post(
            "/api/auth/google",
            json={"token": "invalid_token"}
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_authentication(
        self, client: AsyncClient
    ):
        """Should require authentication for protected endpoints"""
        # Act
        response = await client.get("/api/projects")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_valid_token_succeeds(
        self, client: AsyncClient, auth_token
    ):
        """Should allow access with valid token"""
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Act
        response = await client.get("/api/projects", headers=headers)

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_endpoint_requires_admin_role(
        self, client: AsyncClient, auth_token
    ):
        """Should restrict admin endpoints to admin users"""
        # Arrange - auth_token is for regular user
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Act
        response = await client.get("/api/admin/users", headers=headers)

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_endpoint_with_admin_token_succeeds(
        self, client: AsyncClient, admin_token
    ):
        """Should allow admin access with admin token"""
        # Arrange
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Act
        response = await client.get("/api/admin/users", headers=headers)

        # Assert
        assert response.status_code == 200
```

---

## QA and Approval Flow Tests

**tests/integration/test_api_qa.py:**
```python
import pytest
from httpx import AsyncClient
from app.models import Project, ProjectStatus

class TestQAWorkflow:
    """Integration tests for QA and approval workflow"""

    @pytest.mark.asyncio
    async def test_submit_project_for_approval_updates_status(
        self, client: AsyncClient, test_db, auth_token
    ):
        """Should submit project for approval"""
        # Arrange
        project = Project(
            name="Test Project",
            developer="Dev",
            website="opr",
            status=ProjectStatus.DRAFT
        )
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)

        headers = {"Authorization": f"Bearer {auth_token}"}

        # Act
        response = await client.post(
            f"/api/projects/{project.id}/submit",
            headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_approval"

    @pytest.mark.asyncio
    async def test_approve_project_updates_status_to_approved(
        self, client: AsyncClient, test_db, manager_token
    ):
        """Should approve project (manager only)"""
        # Arrange
        project = Project(
            name="Test",
            developer="Dev",
            website="opr",
            status=ProjectStatus.PENDING_APPROVAL
        )
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)

        headers = {"Authorization": f"Bearer {manager_token}"}

        # Act
        response = await client.post(
            f"/api/projects/{project.id}/approve",
            headers=headers,
            json={"comments": "Looks good!"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    @pytest.mark.asyncio
    async def test_request_revision_adds_feedback(
        self, client: AsyncClient, test_db, manager_token
    ):
        """Should request revision with feedback"""
        # Arrange
        project = Project(
            name="Test",
            developer="Dev",
            website="opr",
            status=ProjectStatus.PENDING_APPROVAL
        )
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)

        headers = {"Authorization": f"Bearer {manager_token}"}

        # Act
        response = await client.post(
            f"/api/projects/{project.id}/request-revision",
            headers=headers,
            json={
                "feedback": "Please update the amenities section",
                "sections": ["amenities"]
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "revision_requested"
        assert len(data["feedback"]) > 0

    @pytest.mark.asyncio
    async def test_non_manager_cannot_approve_project(
        self, client: AsyncClient, test_db, auth_token
    ):
        """Should prevent non-managers from approving"""
        # Arrange
        project = Project(
            name="Test",
            developer="Dev",
            website="opr",
            status=ProjectStatus.PENDING_APPROVAL
        )
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)

        headers = {"Authorization": f"Bearer {auth_token}"}

        # Act
        response = await client.post(
            f"/api/projects/{project.id}/approve",
            headers=headers
        )

        # Assert
        assert response.status_code == 403
```

---

## Error Handling Tests

**tests/integration/test_error_handling.py:**
```python
import pytest
from httpx import AsyncClient

class TestErrorHandling:
    """Integration tests for error handling"""

    @pytest.mark.asyncio
    async def test_validation_error_returns_422_with_details(
        self, client: AsyncClient, auth_token
    ):
        """Should return validation error details"""
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}
        invalid_data = {
            "name": "",  # Empty name
            "website": "invalid"  # Invalid website
        }

        # Act
        response = await client.post(
            "/api/projects",
            headers=headers,
            json=invalid_data
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0

    @pytest.mark.asyncio
    async def test_server_error_returns_500_with_message(
        self, client: AsyncClient, mocker
    ):
        """Should handle server errors gracefully"""
        # Arrange - mock service to raise error
        mocker.patch(
            'app.services.project_service.ProjectService.list',
            side_effect=Exception("Database connection error")
        )

        # Act
        response = await client.get("/api/projects")

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_rate_limiting_returns_429_error(
        self, client: AsyncClient, auth_token
    ):
        """Should enforce rate limiting"""
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Act - make many requests
        for _ in range(100):
            response = await client.get("/api/projects", headers=headers)

        # Assert - eventually hit rate limit
        assert response.status_code == 429
```

---

## Testing Fixtures

**tests/integration/conftest.py:**
```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_pdf():
    """Provide sample PDF file path"""
    return Path(__file__).parent.parent / "fixtures" / "sample.pdf"

@pytest.fixture
def auth_token(mocker):
    """Generate test authentication token for regular user"""
    from app.services.auth_service import create_access_token

    return create_access_token(
        data={"sub": "test@your-domain.com", "role": "user"}
    )

@pytest.fixture
def manager_token(mocker):
    """Generate test authentication token for manager"""
    from app.services.auth_service import create_access_token

    return create_access_token(
        data={"sub": "manager@your-domain.com", "role": "manager"}
    )

@pytest.fixture
def admin_token(mocker):
    """Generate test authentication token for admin"""
    from app.services.auth_service import create_access_token

    return create_access_token(
        data={"sub": "admin@your-domain.com", "role": "admin"}
    )
```

---

## Running Integration Tests

### Basic Commands

```bash
# Run all integration tests
pytest tests/integration -v

# Run specific test file
pytest tests/integration/test_api_projects.py -v

# Run with database setup
pytest tests/integration -v --setup-show

# Run with coverage
pytest tests/integration --cov=app --cov-report=html

# Run in parallel
pytest tests/integration -n auto
```

### CI/CD Integration

**GitHub Actions:**
```yaml
integration-tests:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:16
      env:
        POSTGRES_USER: test
        POSTGRES_PASSWORD: test
        POSTGRES_DB: pdp_test
      ports:
        - 5432:5432
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5

  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run integration tests
      env:
        DATABASE_URL: postgresql+asyncpg://test:test@localhost/pdp_test
      run: pytest tests/integration -v
```

---

## Best Practices

### Do's

1. **Test Real Integrations**
   - Use test database, not mocks
   - Test actual API endpoints
   - Verify data persistence

2. **Clean Up After Tests**
   - Use transactions and rollback
   - Delete created test data
   - Reset database state

3. **Test Error Scenarios**
   - Invalid input
   - Missing authentication
   - Permission errors

### Don'ts

1. **Don't Use Production Data**
2. **Don't Skip Cleanup**
3. **Don't Test External APIs** (mock them)
4. **Don't Make Tests Dependent** on each other

---

## Resources

- [httpx Documentation](https://www.python-httpx.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

**Next:** Review `E2E_TEST_SCENARIOS.md` for end-to-end testing patterns.
