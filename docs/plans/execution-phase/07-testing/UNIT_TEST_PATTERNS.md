# Unit Test Patterns

**Version:** 1.0
**Last Updated:** 2025-01-15
**Owner:** QA Team

---

## Overview

This document provides comprehensive patterns and best practices for writing unit tests in the PDP Automation Platform. Unit tests form the foundation of our test pyramid (80% of all tests) and focus on testing individual functions, classes, and modules in isolation.

### What is a Unit Test?

A unit test:
- Tests a single function or method in isolation
- Executes in < 100ms
- Has no external dependencies (database, network, file system)
- Uses mocks and stubs for dependencies
- Is deterministic and repeatable

### Unit Testing Goals

- **Fast Feedback:** Run in seconds, not minutes
- **High Coverage:** 85%+ for services, 90%+ for models
- **Clear Intent:** Test name describes what's being tested
- **Isolation:** Each test is independent
- **Maintainability:** Easy to update when code changes

---

## Testing Framework Setup

### pytest Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
asyncio_mode = auto
```

### conftest.py (Shared Fixtures)

```python
# tests/conftest.py
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def sample_pdf():
    """Provide path to sample PDF fixture"""
    return Path(__file__).parent / "fixtures" / "sample.pdf"

@pytest.fixture
def sample_image_bytes():
    """Provide sample image bytes"""
    with open(Path(__file__).parent / "fixtures" / "sample.jpg", "rb") as f:
        return f.read()

@pytest.fixture
def mock_anthropic_client(mocker):
    """Mock Anthropic client for tests"""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(text="interior")
    ]
    mock_client.messages.create.return_value = mock_response

    mocker.patch(
        'app.services.anthropic_service.AsyncAnthropic',
        return_value=mock_client
    )
    return mock_client

@pytest.fixture
def mock_storage_client(mocker):
    """Mock Google Cloud Storage client"""
    mock_client = MagicMock()
    mock_blob = MagicMock()
    mock_blob.public_url = "https://storage.googleapis.com/bucket/file.jpg"
    mock_client.bucket.return_value.blob.return_value = mock_blob

    mocker.patch(
        'app.services.storage_service.storage.Client',
        return_value=mock_client
    )
    return mock_client
```

---

## Testing Services

### PDF Processor Service

**app/services/pdf_processor.py** (actual API):
```python
class PDFProcessor:
    async def extract_all(self, pdf_bytes: bytes) -> ExtractionResult:
        """Triple extraction: embedded images + page renders + per-page text.

        Returns ExtractionResult with:
            embedded: list      -- raster images via doc.extract_image(xref)
            page_renders: list  -- 300 DPI pixmaps via page.get_pixmap()
            page_text_map: dict -- {page_num: markdown_text} via pymupdf4llm
            total_pages: int
            errors: list
        """
```

**tests/test_pdf_processor.py** (actual path):
```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.pdf_processor import PDFProcessor

class TestPDFProcessor:
    """Test suite for PDF processing service"""

    @pytest.fixture
    def processor(self):
        return PDFProcessor()

    @pytest.fixture
    def simple_pdf_bytes(self):
        """Minimal valid PDF bytes for testing."""
        return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n..."

    # -- Text extraction tests (pymupdf4llm) --

    async def test_extract_all_populates_page_text_map(self, processor, multi_page_pdf):
        """Verify page_text_map is populated after extract_all."""
        result = await processor.extract_all(multi_page_pdf)
        assert isinstance(result.page_text_map, dict)
        assert len(result.page_text_map) > 0

    async def test_extract_text_failure_returns_empty_dict(self, processor, simple_pdf_bytes):
        """Text extraction failure degrades gracefully."""
        with patch("app.services.pdf_processor.pymupdf4llm") as mock_llm:
            mock_llm.to_markdown.side_effect = RuntimeError("fail")
            result = await processor.extract_all(simple_pdf_bytes)
            assert result.page_text_map == {}

    async def test_page_text_map_is_one_indexed(self, processor, simple_pdf_bytes):
        """Page numbers in page_text_map start at 1, not 0."""
        with patch("app.services.pdf_processor.pymupdf4llm") as mock_llm:
            mock_llm.to_markdown.return_value = [
                {"metadata": {"page": 0}, "text": "Page 1 text"}
            ]
            result = await processor.extract_all(simple_pdf_bytes)
            assert 1 in result.page_text_map
            assert 0 not in result.page_text_map

    def test_extract_images_from_valid_pdf_returns_image_list(
        self, processor, valid_pdf, tmp_path
    ):
        """Should extract images from valid PDF and return list of paths"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = processor.extract_images(str(valid_pdf), str(output_dir))

        assert isinstance(result, list)
        assert all(Path(img).exists() for img in result)
        assert all(img.endswith(('.jpg', '.png')) for img in result)

    def test_extract_images_from_nonexistent_pdf_raises_file_not_found_error(
        self, processor, tmp_path
    ):
        """Should raise FileNotFoundError when PDF doesn't exist"""
        fake_path = tmp_path / "nonexistent.pdf"

        with pytest.raises(FileNotFoundError, match="PDF not found"):
            processor.extract_images(str(fake_path), str(tmp_path))

    def test_extract_images_creates_output_directory_if_missing(
        self, processor, valid_pdf, tmp_path
    ):
        """Should create output directory if it doesn't exist"""
        output_dir = tmp_path / "new_output"

        processor.extract_images(str(valid_pdf), str(output_dir))

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_extract_text_from_valid_pdf_returns_string(
        self, processor, valid_pdf
    ):
        """Should extract text content from PDF"""
        result = processor.extract_text(str(valid_pdf))

        assert isinstance(result, str)
        assert len(result) > 0

    def test_extract_text_from_empty_pdf_returns_empty_string(
        self, processor, tmp_path
    ):
        """Should return empty string for PDF with no text"""
        empty_pdf = tmp_path / "empty.pdf"
        # Create PDF with no text content

        result = processor.extract_text(str(empty_pdf))

        assert result == ""
```

---

## Testing Async Functions

### Anthropic Service (Async)

**app/services/anthropic_service.py:**
```python
from anthropic import AsyncAnthropic

class AnthropicService:
    def __init__(self):
        self.client = AsyncAnthropic()

    async def classify_image(self, image_bytes: bytes) -> str:
        """Classify property image using Claude Vision"""
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20241022",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode()}},
                    {"type": "text", "text": "Classify this property image"}
                ]
            }]
        )
        return response.content[0].text
```

**tests/unit/services/test_anthropic_service.py:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.anthropic_service import AnthropicService

class TestAnthropicService:
    """Test suite for Anthropic integration service"""

    @pytest.mark.asyncio
    async def test_classify_image_returns_category(self, mocker, sample_image_bytes):
        """Should classify image and return category"""
        # Arrange
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="interior")]
        mock_client.messages.create.return_value = mock_response

        mocker.patch(
            'app.services.anthropic_service.AsyncAnthropic',
            return_value=mock_client
        )

        service = AnthropicService()

        # Act
        result = await service.classify_image(sample_image_bytes)

        # Assert
        assert result == "interior"
        mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_image_with_api_error_raises_exception(self, mocker):
        """Should raise exception when Anthropic API fails"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = Exception("API Error")

        mocker.patch(
            'app.services.anthropic_service.AsyncAnthropic',
            return_value=mock_client
        )

        service = AnthropicService()

        # Act & Assert
        with pytest.raises(Exception, match="API Error"):
            await service.classify_image(b"invalid")

    @pytest.mark.asyncio
    async def test_classify_image_calls_api_with_correct_parameters(
        self, mocker, sample_image_bytes
    ):
        """Should call Anthropic API with correct parameters"""
        # Arrange
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="exterior")]
        mock_client.messages.create.return_value = mock_response

        mocker.patch(
            'app.services.anthropic_service.AsyncAnthropic',
            return_value=mock_client
        )

        service = AnthropicService()

        # Act
        await service.classify_image(sample_image_bytes)

        # Assert
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs['model'] == "claude-sonnet-4-5-20241022"
        assert len(call_args.kwargs['messages']) == 1
        assert call_args.kwargs['messages'][0]['role'] == "user"
```

---

## Testing with Database

### Project Service (Database Operations)

**tests/unit/services/test_project_service.py:**
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base, Project
from app.services.project_service import ProjectService

@pytest.fixture
async def test_db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/test_db",
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def test_db_session(test_db_engine):
    """Create test database session"""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session

class TestProjectService:
    """Test suite for project service"""

    @pytest.mark.asyncio
    async def test_create_project_stores_in_database(self, test_db_session):
        """Should create project and store in database"""
        # Arrange
        service = ProjectService(test_db_session)
        project_data = {
            "name": "Test Project",
            "developer": "Test Developer",
            "website": "opr",
            "location": "Dubai"
        }

        # Act
        project = await service.create_from_extraction(
            project_data,
            job_id="test-job-123"
        )

        # Assert
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.developer == "Test Developer"
        assert project.status == "draft"

        # Verify in database
        retrieved = await service.get_by_id(project.id)
        assert retrieved is not None
        assert retrieved.name == project.name

    @pytest.mark.asyncio
    async def test_create_project_with_invalid_data_raises_validation_error(
        self, test_db_session
    ):
        """Should raise ValidationError for invalid project data"""
        # Arrange
        service = ProjectService(test_db_session)
        invalid_data = {
            "name": "",  # Empty name
            "developer": "Test"
        }

        # Act & Assert
        with pytest.raises(ValueError, match="name is required"):
            await service.create_from_extraction(invalid_data, job_id="test")

    @pytest.mark.asyncio
    async def test_update_project_modifies_existing_record(self, test_db_session):
        """Should update existing project in database"""
        # Arrange
        service = ProjectService(test_db_session)
        project = await service.create_from_extraction(
            {"name": "Original", "developer": "Dev", "website": "opr"},
            job_id="test"
        )

        # Act
        updated = await service.update(
            project.id,
            {"name": "Updated Name"}
        )

        # Assert
        assert updated.name == "Updated Name"
        assert updated.developer == "Dev"  # Unchanged

        # Verify in database
        retrieved = await service.get_by_id(project.id)
        assert retrieved.name == "Updated Name"
```

---

## Mocking External Services

### Google Drive Service

**tests/unit/services/test_google_drive_service.py:**
```python
import pytest
from unittest.mock import MagicMock, patch
from app.services.google_drive_service import GoogleDriveService

class TestGoogleDriveService:
    """Test suite for Google Drive integration"""

    @pytest.fixture
    def mock_drive_client(self, mocker):
        """Mock Google Drive API client"""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.get.return_value.execute.return_value = {
            'id': 'file123',
            'name': 'test.jpg',
            'webViewLink': 'https://drive.google.com/file/d/file123'
        }
        mock_client.files.return_value = mock_file

        mocker.patch(
            'app.services.google_drive_service.build',
            return_value=mock_client
        )
        return mock_client

    def test_upload_file_creates_file_in_drive(self, mock_drive_client, tmp_path):
        """Should upload file to Google Drive"""
        # Arrange
        service = GoogleDriveService()
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"image data")

        # Act
        file_id = service.upload_file(str(test_file), folder_id="folder123")

        # Assert
        assert file_id == "file123"
        mock_drive_client.files.return_value.create.assert_called_once()

    def test_create_folder_returns_folder_id(self, mock_drive_client):
        """Should create folder in Google Drive"""
        # Arrange
        service = GoogleDriveService()
        mock_drive_client.files.return_value.create.return_value.execute.return_value = {
            'id': 'folder123'
        }

        # Act
        folder_id = service.create_folder("Test Folder", parent_id="parent")

        # Assert
        assert folder_id == "folder123"

        # Verify API call
        call_args = mock_drive_client.files.return_value.create.call_args
        assert call_args.kwargs['body']['name'] == "Test Folder"
        assert call_args.kwargs['body']['mimeType'] == "application/vnd.google-apps.folder"
```

### Google Sheets Service

**tests/unit/services/test_google_sheets_service.py:**
```python
import pytest
from unittest.mock import MagicMock
from app.services.google_sheets_service import GoogleSheetsService

class TestGoogleSheetsService:
    """Test suite for Google Sheets integration"""

    @pytest.fixture
    def mock_sheets_client(self, mocker):
        """Mock Google Sheets API client"""
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.values.return_value.update.return_value.execute.return_value = {
            'updatedCells': 10
        }
        mock_client.spreadsheets.return_value = mock_sheet

        mocker.patch(
            'app.services.google_sheets_service.build',
            return_value=mock_client
        )
        return mock_client

    def test_write_data_updates_sheet(self, mock_sheets_client):
        """Should write data to Google Sheet"""
        # Arrange
        service = GoogleSheetsService()
        data = [
            ["Name", "Developer", "Location"],
            ["Project 1", "Dev A", "Dubai"],
            ["Project 2", "Dev B", "Abu Dhabi"]
        ]

        # Act
        service.write_data("sheet123", "Sheet1!A1", data)

        # Assert
        mock_sheets_client.spreadsheets.return_value.values.return_value.update.assert_called_once()
        call_args = mock_sheets_client.spreadsheets.return_value.values.return_value.update.call_args
        assert call_args.kwargs['spreadsheetId'] == "sheet123"
        assert call_args.kwargs['range'] == "Sheet1!A1"
        assert call_args.kwargs['body']['values'] == data

    def test_create_spreadsheet_returns_sheet_id(self, mock_sheets_client):
        """Should create new Google Sheet and return ID"""
        # Arrange
        service = GoogleSheetsService()
        mock_sheets_client.spreadsheets.return_value.create.return_value.execute.return_value = {
            'spreadsheetId': 'new-sheet-123',
            'spreadsheetUrl': 'https://docs.google.com/spreadsheets/d/new-sheet-123'
        }

        # Act
        sheet_id = service.create_spreadsheet("Test Sheet")

        # Assert
        assert sheet_id == "new-sheet-123"
```

---

## Testing Models and Validators

### Project Model Validation

**tests/unit/models/test_project_model.py:**
```python
import pytest
from datetime import datetime
from app.models.project import Project, ProjectStatus

class TestProjectModel:
    """Test suite for Project model"""

    def test_create_project_with_valid_data_succeeds(self):
        """Should create project with valid data"""
        # Arrange & Act
        project = Project(
            name="Test Project",
            developer="Test Developer",
            website="opr",
            location="Dubai",
            status=ProjectStatus.DRAFT
        )

        # Assert
        assert project.name == "Test Project"
        assert project.developer == "Test Developer"
        assert project.status == ProjectStatus.DRAFT

    def test_create_project_without_name_raises_validation_error(self):
        """Should raise ValidationError when name is missing"""
        with pytest.raises(ValueError, match="name"):
            Project(
                name="",
                developer="Test",
                website="opr"
            )

    def test_project_status_defaults_to_draft(self):
        """Should default status to DRAFT"""
        project = Project(
            name="Test",
            developer="Dev",
            website="opr"
        )

        assert project.status == ProjectStatus.DRAFT

    def test_project_created_at_auto_set(self):
        """Should automatically set created_at timestamp"""
        project = Project(
            name="Test",
            developer="Dev",
            website="opr"
        )

        assert project.created_at is not None
        assert isinstance(project.created_at, datetime)

    def test_project_slug_generated_from_name(self):
        """Should generate URL-friendly slug from name"""
        project = Project(
            name="Test Project With Spaces",
            developer="Dev",
            website="opr"
        )

        assert project.slug == "test-project-with-spaces"

    def test_project_to_dict_returns_serializable_data(self):
        """Should convert project to dictionary"""
        project = Project(
            name="Test",
            developer="Dev",
            website="opr",
            status=ProjectStatus.APPROVED
        )

        data = project.to_dict()

        assert isinstance(data, dict)
        assert data['name'] == "Test"
        assert data['status'] == "approved"
        assert 'created_at' in data
```

---

## Testing Utilities and Helpers

### Validation Utils

**tests/unit/utils/test_validators.py:**
```python
import pytest
from app.utils.validators import (
    validate_website,
    validate_email,
    validate_phone,
    validate_image_format,
    ValidationError
)

class TestValidators:
    """Test suite for validation utilities"""

    # Website validation
    def test_validate_website_with_valid_opr_returns_true(self):
        """Should validate 'opr' as valid website"""
        assert validate_website("opr") is True

    def test_validate_website_with_valid_dxb_returns_true(self):
        """Should validate 'dxb' as valid website"""
        assert validate_website("dxb") is True

    def test_validate_website_with_invalid_value_raises_error(self):
        """Should raise ValidationError for invalid website"""
        with pytest.raises(ValidationError, match="Invalid website"):
            validate_website("invalid")

    # Email validation
    @pytest.mark.parametrize("email", [
        "test@your-domain.com",
        "user.name@your-domain.com",
        "test+tag@your-domain.com"
    ])
    def test_validate_email_with_valid_emails_returns_true(self, email):
        """Should validate correct email formats"""
        assert validate_email(email) is True

    @pytest.mark.parametrize("email", [
        "invalid",
        "@your-domain.com",
        "test@",
        "test @your-domain.com"
    ])
    def test_validate_email_with_invalid_emails_raises_error(self, email):
        """Should raise ValidationError for invalid emails"""
        with pytest.raises(ValidationError):
            validate_email(email)

    # Image format validation
    @pytest.mark.parametrize("filename", [
        "image.jpg",
        "photo.jpeg",
        "picture.png",
        "graphic.webp"
    ])
    def test_validate_image_format_with_valid_formats_returns_true(self, filename):
        """Should validate supported image formats"""
        assert validate_image_format(filename) is True

    def test_validate_image_format_with_invalid_format_raises_error(self):
        """Should raise ValidationError for unsupported formats"""
        with pytest.raises(ValidationError, match="Unsupported image format"):
            validate_image_format("document.pdf")
```

### File Utils

**tests/unit/utils/test_file_utils.py:**
```python
import pytest
from pathlib import Path
from app.utils.file_utils import (
    get_file_extension,
    sanitize_filename,
    create_temp_directory,
    cleanup_temp_files
)

class TestFileUtils:
    """Test suite for file utility functions"""

    def test_get_file_extension_returns_lowercase_extension(self):
        """Should return lowercase file extension"""
        assert get_file_extension("document.PDF") == ".pdf"
        assert get_file_extension("image.JPG") == ".jpg"

    def test_sanitize_filename_removes_invalid_characters(self):
        """Should remove invalid characters from filename"""
        result = sanitize_filename("file/name:with*invalid?chars.txt")
        assert "/" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result

    def test_sanitize_filename_preserves_extension(self):
        """Should keep file extension intact"""
        result = sanitize_filename("test file.pdf")
        assert result.endswith(".pdf")

    def test_create_temp_directory_creates_directory(self, tmp_path):
        """Should create temporary directory"""
        temp_dir = create_temp_directory(prefix="test_")

        assert Path(temp_dir).exists()
        assert Path(temp_dir).is_dir()
        assert "test_" in str(temp_dir)

    def test_cleanup_temp_files_removes_files(self, tmp_path):
        """Should remove temporary files"""
        # Create test files
        test_file1 = tmp_path / "temp1.txt"
        test_file2 = tmp_path / "temp2.txt"
        test_file1.write_text("content")
        test_file2.write_text("content")

        # Cleanup
        cleanup_temp_files([str(test_file1), str(test_file2)])

        assert not test_file1.exists()
        assert not test_file2.exists()
```

---

## Parametrized Tests

### Using pytest.mark.parametrize

```python
import pytest
from app.utils.text_processor import extract_amenities

class TestTextProcessor:
    """Test suite for text processing utilities"""

    @pytest.mark.parametrize("text,expected", [
        ("Gym and Swimming Pool", ["gym", "swimming_pool"]),
        ("24/7 Security, Parking", ["security", "parking"]),
        ("Kids Play Area, BBQ", ["play_area", "bbq"]),
        ("No amenities mentioned", []),
    ])
    def test_extract_amenities_from_text(self, text, expected):
        """Should extract amenities from text"""
        result = extract_amenities(text)
        assert result == expected

    @pytest.mark.parametrize("price,currency,expected", [
        (1500000, "AED", "AED 1,500,000"),
        (2750000, "AED", "AED 2,750,000"),
        (500000, "USD", "USD 500,000"),
    ])
    def test_format_price_with_currency(self, price, currency, expected):
        """Should format price with currency"""
        from app.utils.formatters import format_price

        result = format_price(price, currency)
        assert result == expected
```

---

## Testing Error Handling

### Exception Testing

```python
import pytest
from app.services.job_manager import JobManager, JobNotFoundError, JobProcessingError

class TestJobManagerErrors:
    """Test error handling in job manager"""

    @pytest.mark.asyncio
    async def test_get_job_with_invalid_id_raises_not_found_error(self):
        """Should raise JobNotFoundError for invalid job ID"""
        manager = JobManager()

        with pytest.raises(JobNotFoundError, match="Job not found: invalid-id"):
            await manager.get_job("invalid-id")

    @pytest.mark.asyncio
    async def test_process_job_with_corrupt_pdf_raises_processing_error(
        self, mock_storage
    ):
        """Should raise JobProcessingError for corrupt PDF"""
        manager = JobManager()
        job_id = await manager.create_job("corrupt.pdf", "opr")

        with pytest.raises(JobProcessingError, match="Failed to process PDF"):
            await manager.process_job(job_id)

    @pytest.mark.asyncio
    async def test_cancel_completed_job_raises_value_error(self):
        """Should not allow cancelling completed job"""
        manager = JobManager()
        job_id = await manager.create_job("test.pdf", "opr")
        await manager.complete_job(job_id)

        with pytest.raises(ValueError, match="Cannot cancel completed job"):
            await manager.cancel_job(job_id)
```

---

## Testing with Fixtures

### Fixture Scopes

```python
import pytest

# Function scope (default) - runs for each test
@pytest.fixture
def temp_file(tmp_path):
    """Create temporary file for each test"""
    file_path = tmp_path / "temp.txt"
    file_path.write_text("test content")
    return file_path

# Class scope - runs once per test class
@pytest.fixture(scope="class")
def database_connection():
    """Create database connection for test class"""
    conn = create_connection()
    yield conn
    conn.close()

# Module scope - runs once per module
@pytest.fixture(scope="module")
def api_client():
    """Create API client for entire module"""
    client = APIClient()
    yield client
    client.cleanup()

# Session scope - runs once for entire test session
@pytest.fixture(scope="session")
def test_config():
    """Load test configuration once"""
    return load_config("test")
```

### Fixture Factories

```python
@pytest.fixture
def project_factory():
    """Factory for creating test projects"""
    def _create_project(**kwargs):
        defaults = {
            "name": "Test Project",
            "developer": "Test Developer",
            "website": "opr",
            "status": "draft"
        }
        return Project(**{**defaults, **kwargs})
    return _create_project

def test_create_multiple_projects(project_factory):
    """Should create multiple projects with different data"""
    project1 = project_factory(name="Project A")
    project2 = project_factory(name="Project B", website="dxb")

    assert project1.name == "Project A"
    assert project2.name == "Project B"
    assert project2.website == "dxb"
```

---

## Best Practices

### Do's

1. **Test Behavior, Not Implementation**
   ```python
   # Good - tests behavior
   def test_calculate_total_price_applies_discount():
       result = calculate_total([100, 200], discount=0.1)
       assert result == 270

   # Bad - tests implementation
   def test_calculate_total_price_multiplies_by_point_nine():
       # Too specific to implementation
       pass
   ```

2. **Use Descriptive Test Names**
   ```python
   # Good
   def test_upload_file_with_invalid_extension_returns_400_error():
       pass

   # Bad
   def test_upload():
       pass
   ```

3. **Arrange-Act-Assert Pattern**
   ```python
   def test_create_project():
       # Arrange
       service = ProjectService()
       data = {"name": "Test", "developer": "Dev"}

       # Act
       result = service.create(data)

       # Assert
       assert result.id is not None
   ```

### Don'ts

1. **Don't Test Multiple Things**
   ```python
   # Bad - testing too much
   def test_project_service():
       # Creates, updates, deletes all in one test
       pass

   # Good - separate tests
   def test_create_project():
       pass

   def test_update_project():
       pass
   ```

2. **Don't Use Sleep in Tests**
   ```python
   # Bad
   async def test_async_operation():
       start_operation()
       await asyncio.sleep(5)  # Don't wait arbitrarily
       assert operation_complete()

   # Good
   async def test_async_operation():
       result = await perform_operation()  # Wait for actual completion
       assert result.status == "complete"
   ```

3. **Don't Depend on Test Order**
   ```python
   # Bad - tests depend on each other
   def test_1_create_user():
       global user_id
       user_id = create_user()

   def test_2_update_user():
       update_user(user_id)  # Depends on test_1

   # Good - tests are independent
   def test_create_user():
       user_id = create_user()
       assert user_id

   def test_update_user(user_factory):
       user = user_factory()
       update_user(user.id)
   ```

---

## Running Tests

### Basic Commands

```bash
# Run all unit tests
pytest tests/unit -v

# Run specific test file
pytest tests/unit/test_pdf_processor.py -v

# Run specific test
pytest tests/unit/test_pdf_processor.py::test_extract_images -v

# Run tests matching pattern
pytest tests/unit -k "image" -v

# Run with coverage
pytest tests/unit --cov=app --cov-report=html

# Stop on first failure
pytest tests/unit -x

# Show local variables on failure
pytest tests/unit -l

# Run in parallel
pytest tests/unit -n auto
```

### Advanced Options

```bash
# Run only failed tests from last run
pytest tests/unit --lf

# Run failed tests first
pytest tests/unit --ff

# Show slowest tests
pytest tests/unit --durations=10

# Verbose output with print statements
pytest tests/unit -v -s

# Generate JUnit XML report
pytest tests/unit --junitxml=report.xml
```

---

## Coverage Analysis

### Generating Reports

```bash
# HTML coverage report
pytest tests/unit --cov=app --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/unit --cov=app --cov-report=term-missing

# Fail if coverage below threshold
pytest tests/unit --cov=app --cov-fail-under=85
```

### Coverage Configuration

**.coveragerc:**
```ini
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

---

## Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

### Next Steps
- Review `INTEGRATION_TESTS.md` for API testing patterns
- Review `E2E_TEST_SCENARIOS.md` for end-to-end testing
- Review `TEST_STRATEGY.md` for overall testing approach

---

**Last Updated:** 2025-01-15
