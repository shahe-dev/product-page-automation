"""Tests for database enums."""
import pytest


def test_job_type_enum_values():
    """JobType enum has expected values."""
    from app.models.enums import JobType

    assert JobType.EXTRACTION.value == "extraction"
    assert JobType.GENERATION.value == "generation"
    assert len(JobType) == 2


def test_material_package_status_enum_values():
    """MaterialPackageStatus enum has expected values."""
    from app.models.enums import MaterialPackageStatus

    assert MaterialPackageStatus.PENDING.value == "pending"
    assert MaterialPackageStatus.READY.value == "ready"
    assert MaterialPackageStatus.EXPIRED.value == "expired"
    assert MaterialPackageStatus.ERROR.value == "error"
    assert len(MaterialPackageStatus) == 4


def test_generation_run_status_enum_values():
    """GenerationRunStatus enum has expected values."""
    from app.models.enums import GenerationRunStatus

    assert GenerationRunStatus.PENDING.value == "pending"
    assert GenerationRunStatus.PROCESSING.value == "processing"
    assert GenerationRunStatus.COMPLETED.value == "completed"
    assert GenerationRunStatus.FAILED.value == "failed"
    assert len(GenerationRunStatus) == 4
