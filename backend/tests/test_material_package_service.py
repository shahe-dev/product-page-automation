"""
Tests for MaterialPackageService.

Tests GCS persistence and loading for material packages.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.enums import MaterialPackageStatus


# =============================================================================
# B.2: MaterialPackageService Tests
# =============================================================================

@pytest.fixture
def mock_storage():
    """Create a mock StorageService."""
    storage = AsyncMock()
    storage.upload_file = AsyncMock(return_value="gs://bucket/test-path")
    storage.download_file = AsyncMock()
    storage.list_blobs = AsyncMock(return_value=[])
    return storage


@pytest.fixture
def mock_repo():
    """Create a mock MaterialPackageRepository."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.mark_ready = AsyncMock(return_value=True)
    repo.mark_error = AsyncMock(return_value=True)
    repo.update_status = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def service(mock_storage, mock_repo):
    """Create MaterialPackageService with mocked dependencies."""
    from app.services.material_package_service import MaterialPackageService

    return MaterialPackageService(mock_storage, mock_repo)


@pytest.fixture
def sample_pipeline_ctx():
    """Create sample pipeline context for testing."""
    return {
        "structured_data": {
            "project_name": "Test Project",
            "developer": "Test Developer",
            "emirate": "Dubai",
            "community": "Test Community",
        },
        "extraction": {
            "text_by_page": {1: "Page 1 text", 2: "Page 2 text"},
            "page_text_map": {1: "Page 1 text", 2: "Page 2 text"},
        },
        "floor_plans": {
            "floor_plans": [],
            "total_extracted": 0,
        },
        "manifest": {
            "entries": [
                {"filename": "img_001.webp", "category": "interior"},
                {"filename": "img_002.webp", "category": "exterior"},
            ],
            "categories": {"interior": 1, "exterior": 1},
        },
        "zip_bytes": b"fake zip data for testing",
        "pdf_path": "file://test.pdf",
    }


@pytest.mark.asyncio
async def test_persist_to_gcs_creates_files(service, mock_storage, sample_pipeline_ctx):
    """Service persists extraction results to GCS."""
    project_id = uuid4()

    gcs_path = await service.persist_to_gcs(project_id, sample_pipeline_ctx)

    # Verify path format
    assert f"materials/{project_id}" in gcs_path

    # Should upload at least 4 files: structured_data.json, extracted_text.json,
    # floor_plans.json, manifest.json
    assert mock_storage.upload_file.call_count >= 4


@pytest.mark.asyncio
async def test_persist_to_gcs_uploads_structured_data(service, mock_storage, sample_pipeline_ctx):
    """Service uploads structured_data.json to GCS."""
    project_id = uuid4()

    await service.persist_to_gcs(project_id, sample_pipeline_ctx)

    # Find the structured_data.json upload call
    calls = mock_storage.upload_file.call_args_list
    structured_data_call = None
    for call in calls:
        args, kwargs = call
        if "structured_data.json" in kwargs.get("destination_blob_path", ""):
            structured_data_call = call
            break

    assert structured_data_call is not None, "structured_data.json should be uploaded"


@pytest.mark.asyncio
async def test_persist_to_gcs_uploads_manifest(service, mock_storage, sample_pipeline_ctx):
    """Service uploads manifest.json to GCS."""
    project_id = uuid4()

    await service.persist_to_gcs(project_id, sample_pipeline_ctx)

    # Find the manifest.json upload call
    calls = mock_storage.upload_file.call_args_list
    manifest_call = None
    for call in calls:
        args, kwargs = call
        if "manifest.json" in kwargs.get("destination_blob_path", ""):
            manifest_call = call
            break

    assert manifest_call is not None, "manifest.json should be uploaded"


@pytest.mark.asyncio
async def test_load_from_gcs_returns_package_data(service, mock_storage):
    """Service loads package data from GCS."""
    package_id = uuid4()
    project_id = uuid4()
    gcs_base_path = f"materials/{project_id}"

    # Mock the downloads
    mock_storage.download_file.side_effect = [
        json.dumps({"project_name": "Test"}).encode(),
        json.dumps({"text_by_page": {1: "text"}}).encode(),
        json.dumps({"floor_plans": []}).encode(),
        json.dumps({"entries": []}).encode(),
    ]

    result = await service.load_from_gcs(gcs_base_path)

    assert result is not None
    assert "structured_data" in result
    assert "extracted_text" in result


@pytest.mark.asyncio
async def test_create_package_record(service, mock_repo, sample_pipeline_ctx):
    """Service creates MaterialPackage DB record."""
    from app.models.database import MaterialPackage

    project_id = uuid4()
    source_job_id = uuid4()
    gcs_path = f"materials/{project_id}"

    # Set up mock return
    mock_package = MagicMock(spec=MaterialPackage)
    mock_package.id = uuid4()
    mock_package.status = MaterialPackageStatus.PENDING
    mock_repo.create.return_value = mock_package

    package = await service.create_package_record(
        project_id=project_id,
        source_job_id=source_job_id,
        gcs_base_path=gcs_path,
        extraction_summary={"images": 10},
        structured_data=sample_pipeline_ctx["structured_data"],
    )

    assert package is not None
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_mark_package_ready(service, mock_repo):
    """Service marks package as ready with final data."""
    package_id = uuid4()

    result = await service.mark_ready(
        package_id=package_id,
        extraction_summary={"images": 10},
        structured_data={"project_name": "Test"},
    )

    assert result is True
    mock_repo.mark_ready.assert_called_once_with(
        package_id,
        {"images": 10},
        {"project_name": "Test"},
    )


@pytest.mark.asyncio
async def test_mark_package_error(service, mock_repo):
    """Service marks package as errored."""
    package_id = uuid4()

    result = await service.mark_error(package_id)

    assert result is True
    mock_repo.mark_error.assert_called_once_with(package_id)


@pytest.mark.asyncio
async def test_persist_to_gcs_with_dataclass_structured_data(service, mock_storage):
    """Service serializes StructuredProject dataclass without error."""
    from app.services.data_structurer import StructuredProject

    project_id = uuid4()
    structured = StructuredProject(
        project_name="Test Project",
        developer="Test Dev",
        emirate="Dubai",
    )

    ctx = {
        "structured_data": structured,
        "extraction": {"page_text_map": {1: "text"}},
        "floor_plans": {},
        "manifest": {},
    }

    gcs_path = await service.persist_to_gcs(project_id, ctx)
    assert f"materials/{project_id}" in gcs_path

    # Verify structured_data.json was uploaded with valid JSON bytes
    calls = mock_storage.upload_file.call_args_list
    for call in calls:
        _, kwargs = call
        if "structured_data.json" in kwargs.get("destination_blob_path", ""):
            raw = kwargs.get("source_file") or call[0][0]
            parsed = json.loads(raw)
            assert parsed["project_name"] == "Test Project"
            assert parsed["developer"] == "Test Dev"
            break
    else:
        pytest.fail("structured_data.json upload not found")


@pytest.mark.asyncio
async def test_persist_to_gcs_uploads_source_pdf(service, mock_storage, sample_pipeline_ctx):
    """persist_to_gcs uploads source PDF when present in pipeline_ctx."""
    sample_pipeline_ctx["pdf_bytes"] = b"%PDF-1.4 fake pdf content"
    sample_pipeline_ctx["pdf_path"] = "file://C:/uploads/brochure_test.pdf"
    project_id = uuid4()

    await service.persist_to_gcs(project_id, sample_pipeline_ctx)

    # Find the source PDF upload call
    calls = mock_storage.upload_file.call_args_list
    source_pdf_call = None
    for call in calls:
        _, kwargs = call
        dest = kwargs.get("destination_blob_path", "")
        if "/source/" in dest and dest.endswith(".pdf"):
            source_pdf_call = call
            break

    assert source_pdf_call is not None, "source PDF should be uploaded to GCS"
    _, kwargs = source_pdf_call
    assert kwargs["destination_blob_path"].endswith("source/brochure_test.pdf")
    assert kwargs["content_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_persist_to_gcs_skips_source_pdf_when_absent(service, mock_storage, sample_pipeline_ctx):
    """persist_to_gcs does not upload source PDF when pdf_bytes is missing."""
    sample_pipeline_ctx.pop("pdf_bytes", None)
    sample_pipeline_ctx.pop("pdf_path", None)
    project_id = uuid4()

    await service.persist_to_gcs(project_id, sample_pipeline_ctx)

    # No call should contain /source/
    calls = mock_storage.upload_file.call_args_list
    for call in calls:
        _, kwargs = call
        dest = kwargs.get("destination_blob_path", "")
        assert "/source/" not in dest, f"Unexpected source PDF upload: {dest}"
