"""Tests for database ORM models."""
import uuid
import pytest
from app.models.database import MaterialPackage, GenerationRun, Job
from app.models.enums import (
    MaterialPackageStatus,
    GenerationRunStatus,
    JobType,
    TemplateType,
)


def test_material_package_model_exists():
    """MaterialPackage model can be instantiated with required fields."""
    pkg = MaterialPackage(
        gcs_base_path="gs://bucket/materials/test-project-id/",
        package_version="1.0",
        status=MaterialPackageStatus.PENDING
    )
    assert pkg.gcs_base_path == "gs://bucket/materials/test-project-id/"
    assert pkg.package_version == "1.0"
    assert pkg.status == MaterialPackageStatus.PENDING


def test_material_package_has_expected_columns():
    """MaterialPackage model has all expected columns."""
    assert hasattr(MaterialPackage, "id")
    assert hasattr(MaterialPackage, "project_id")
    assert hasattr(MaterialPackage, "source_job_id")
    assert hasattr(MaterialPackage, "gcs_base_path")
    assert hasattr(MaterialPackage, "package_version")
    assert hasattr(MaterialPackage, "extraction_summary")
    assert hasattr(MaterialPackage, "structured_data")
    assert hasattr(MaterialPackage, "status")
    assert hasattr(MaterialPackage, "expires_at")


def test_generation_run_model_exists():
    """GenerationRun model can be instantiated with required fields."""
    run = GenerationRun(
        project_id=uuid.uuid4(),
        template_type=TemplateType.OPR,
        status=GenerationRunStatus.PENDING
    )
    assert run.template_type == TemplateType.OPR
    assert run.status == GenerationRunStatus.PENDING


def test_generation_run_has_expected_columns():
    """GenerationRun model has all expected columns."""
    assert hasattr(GenerationRun, "id")
    assert hasattr(GenerationRun, "project_id")
    assert hasattr(GenerationRun, "material_package_id")
    assert hasattr(GenerationRun, "template_type")
    assert hasattr(GenerationRun, "job_id")
    assert hasattr(GenerationRun, "generated_content")
    assert hasattr(GenerationRun, "sheet_url")
    assert hasattr(GenerationRun, "drive_folder_url")
    assert hasattr(GenerationRun, "status")


def test_job_model_has_job_type():
    """Job model has job_type field."""
    job = Job(
        user_id=uuid.uuid4(),
        template_type=TemplateType.OPR,
        job_type=JobType.EXTRACTION
    )
    assert job.job_type == JobType.EXTRACTION


def test_job_model_has_material_package_id():
    """Job model has material_package_id field."""
    assert hasattr(Job, "material_package_id")
    assert hasattr(Job, "job_type")


def test_job_model_accepts_extraction_type():
    """Job model accepts EXTRACTION job type."""
    job = Job(
        user_id=uuid.uuid4(),
        template_type=TemplateType.OPR,
        job_type=JobType.EXTRACTION
    )
    assert job.job_type == JobType.EXTRACTION


def test_job_model_accepts_generation_type():
    """Job model accepts GENERATION job type."""
    job = Job(
        user_id=uuid.uuid4(),
        template_type=TemplateType.OPR,
        job_type=JobType.GENERATION
    )
    assert job.job_type == JobType.GENERATION
