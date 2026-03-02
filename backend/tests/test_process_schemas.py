"""Tests for process route response schemas."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from app.api.routes.process import MaterialPackageResponse, GenerationRunResponse
from app.models.enums import MaterialPackageStatus, GenerationRunStatus, TemplateType


def _make_mock_package(**overrides):
    """Create a mock MaterialPackage ORM object."""
    pkg = MagicMock()
    pkg.id = overrides.get("id", uuid4())
    pkg.project_id = overrides.get("project_id", uuid4())
    pkg.source_job_id = overrides.get("source_job_id", uuid4())
    pkg.gcs_base_path = overrides.get("gcs_base_path", "materials/test/")
    pkg.package_version = overrides.get("package_version", "1.0")
    pkg.extraction_summary = overrides.get("extraction_summary", {"pages": 5})
    pkg.structured_data = overrides.get("structured_data", {"name": "Test"})
    pkg.status = overrides.get("status", MaterialPackageStatus.READY)
    pkg.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    pkg.updated_at = overrides.get("updated_at", datetime.now(timezone.utc))
    pkg.expires_at = overrides.get("expires_at", None)
    return pkg


def _make_mock_generation_run(**overrides):
    """Create a mock GenerationRun ORM object."""
    run = MagicMock()
    run.id = overrides.get("id", uuid4())
    run.project_id = overrides.get("project_id", uuid4())
    run.material_package_id = overrides.get("material_package_id", uuid4())
    run.template_type = overrides.get("template_type", TemplateType.OPR)
    run.job_id = overrides.get("job_id", uuid4())
    run.generated_content = overrides.get("generated_content", None)
    run.sheet_url = overrides.get("sheet_url", None)
    run.drive_folder_url = overrides.get("drive_folder_url", None)
    run.status = overrides.get("status", GenerationRunStatus.PENDING)
    run.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    run.completed_at = overrides.get("completed_at", None)
    return run


# -- MaterialPackageResponse tests --

def test_material_package_response_from_orm():
    """MaterialPackageResponse serializes ORM object correctly."""
    pkg = _make_mock_package()
    resp = MaterialPackageResponse.from_package(pkg)
    assert resp.id == pkg.id
    assert resp.status == "ready"
    assert resp.gcs_base_path == "materials/test/"


def test_material_package_response_nullable_fields():
    """MaterialPackageResponse handles None fields."""
    pkg = _make_mock_package(
        project_id=None,
        source_job_id=None,
        extraction_summary=None,
        structured_data=None,
        expires_at=None
    )
    resp = MaterialPackageResponse.from_package(pkg)
    assert resp.project_id is None
    assert resp.source_job_id is None
    assert resp.expires_at is None


def test_material_package_response_round_trip():
    """MaterialPackageResponse produces JSON matching frontend MaterialPackage type."""
    pkg = _make_mock_package(status=MaterialPackageStatus.READY)
    resp = MaterialPackageResponse.from_package(pkg)
    data = resp.model_dump()
    expected_keys = {
        "id", "project_id", "source_job_id", "gcs_base_path",
        "package_version", "extraction_summary", "structured_data",
        "status", "created_at", "updated_at", "expires_at",
    }
    assert expected_keys == set(data.keys())


# -- GenerationRunResponse tests --

def test_generation_run_response_from_orm():
    """GenerationRunResponse serializes ORM object correctly."""
    run = _make_mock_generation_run(status=GenerationRunStatus.COMPLETED)
    resp = GenerationRunResponse.from_run(run)
    assert resp.status == "completed"
    assert resp.template_type == "opr"


def test_generation_run_response_nullable_fields():
    """GenerationRunResponse handles None fields."""
    run = _make_mock_generation_run(
        material_package_id=None,
        job_id=None,
        generated_content=None,
        completed_at=None
    )
    resp = GenerationRunResponse.from_run(run)
    assert resp.material_package_id is None
    assert resp.job_id is None
    assert resp.completed_at is None


def test_generation_run_response_round_trip():
    """GenerationRunResponse produces JSON matching frontend GenerationRun type."""
    run = _make_mock_generation_run()
    resp = GenerationRunResponse.from_run(run)
    data = resp.model_dump()
    expected_keys = {
        "id", "project_id", "material_package_id", "template_type",
        "job_id", "generated_content", "sheet_url", "drive_folder_url",
        "status", "created_at", "completed_at",
    }
    assert expected_keys == set(data.keys())
