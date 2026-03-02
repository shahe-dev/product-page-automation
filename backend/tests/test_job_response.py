"""Tests for JobResponse serialization of pipeline fields."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from app.api.routes.jobs import JobResponse
from app.models.enums import JobStatus, JobType, TemplateType


def _make_mock_job(**overrides):
    """Create a mock Job ORM object."""
    job = MagicMock()
    job.id = overrides.get("id", uuid4())
    job.user_id = overrides.get("user_id", uuid4())
    job.template_type = overrides.get("template_type", TemplateType.OPR)
    job.template_id = overrides.get("template_id", None)
    job.job_type = overrides.get("job_type", JobType.EXTRACTION)
    job.material_package_id = overrides.get("material_package_id", None)
    job.material_package = overrides.get("material_package", None)
    job.status = overrides.get("status", JobStatus.PENDING)
    job.progress = overrides.get("progress", 0)
    job.current_step = overrides.get("current_step", None)
    job.progress_message = overrides.get("progress_message", None)
    job.result = overrides.get("result", None)
    job.processing_config = overrides.get("processing_config", None)
    job.error_message = overrides.get("error_message", None)
    job.retry_count = overrides.get("retry_count", 0)
    job.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    job.started_at = overrides.get("started_at", None)
    job.completed_at = overrides.get("completed_at", None)
    return job


def test_job_response_includes_job_type():
    """JobResponse.from_job() includes job_type field."""
    job = _make_mock_job(job_type=JobType.EXTRACTION)
    resp = JobResponse.from_job(job)
    assert resp.job_type == "extraction"


def test_job_response_includes_generation_job_type():
    """JobResponse.from_job() serializes generation job_type."""
    pkg_id = uuid4()
    job = _make_mock_job(job_type=JobType.GENERATION, material_package_id=pkg_id)
    resp = JobResponse.from_job(job)
    assert resp.job_type == "generation"
    assert resp.material_package_id == pkg_id


def test_job_response_includes_material_package_id():
    """JobResponse.from_job() includes material_package_id when set."""
    pkg_id = uuid4()
    job = _make_mock_job(material_package_id=pkg_id)
    resp = JobResponse.from_job(job)
    assert resp.material_package_id == pkg_id


def test_job_response_material_package_id_none():
    """JobResponse.from_job() returns None when no material_package_id."""
    job = _make_mock_job(material_package_id=None)
    resp = JobResponse.from_job(job)
    assert resp.material_package_id is None


def test_job_response_project_id_from_result():
    """JobResponse.from_job() extracts project_id from result dict."""
    project_id = str(uuid4())
    job = _make_mock_job(result={"project_id": project_id, "sheet_url": "https://..."})
    resp = JobResponse.from_job(job)
    assert resp.project_id == project_id


def test_job_response_project_id_none_when_no_result():
    """JobResponse.from_job() returns None project_id when result is None."""
    job = _make_mock_job(result=None, processing_config=None)
    resp = JobResponse.from_job(job)
    assert resp.project_id is None


def test_job_response_project_id_from_processing_config():
    """JobResponse.from_job() falls back to processing_config for project_id (generation jobs)."""
    project_id = str(uuid4())
    job = _make_mock_job(
        job_type=JobType.GENERATION,
        result=None,
        processing_config={"project_id": project_id},
    )
    resp = JobResponse.from_job(job)
    assert resp.project_id == project_id


def test_job_response_project_id_result_takes_precedence():
    """JobResponse.from_job() prefers result.project_id over processing_config."""
    result_pid = str(uuid4())
    config_pid = str(uuid4())
    job = _make_mock_job(
        result={"project_id": result_pid},
        processing_config={"project_id": config_pid},
    )
    resp = JobResponse.from_job(job)
    assert resp.project_id == result_pid
