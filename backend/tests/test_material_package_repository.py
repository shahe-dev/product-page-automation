"""Tests for MaterialPackageRepository."""
import pytest
import uuid
from unittest.mock import AsyncMock
from app.repositories.material_package_repository import MaterialPackageRepository
from app.models.database import MaterialPackage
from app.models.enums import MaterialPackageStatus


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def repo(mock_db):
    return MaterialPackageRepository(mock_db)


@pytest.mark.asyncio
async def test_create_material_package(repo, mock_db):
    """Repository creates MaterialPackage record."""
    project_id = uuid.uuid4()
    job_id = uuid.uuid4()
    gcs_path = "gs://bucket/materials/test/"

    result = await repo.create(
        project_id=project_id,
        source_job_id=job_id,
        gcs_base_path=gcs_path,
        extraction_summary={"total_images": 10}
    )

    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


def test_repository_has_expected_methods():
    """Repository class has all expected methods."""
    assert hasattr(MaterialPackageRepository, "create")
    assert hasattr(MaterialPackageRepository, "get_by_id")
    assert hasattr(MaterialPackageRepository, "get_by_project")
    assert hasattr(MaterialPackageRepository, "update_status")
    assert hasattr(MaterialPackageRepository, "mark_ready")
