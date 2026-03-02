"""
Tests for JobManager service.

Tests step configurations for different job types and pipeline execution.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.models.enums import JobType, TemplateType, WorkflowStatus


# =============================================================================
# B.1: Step Configuration Tests
# =============================================================================

def test_extraction_steps_defined():
    """Extraction steps cover steps 1-10 plus materialize plus upload_shared_assets (12 total)."""
    from app.services.job_manager import EXTRACTION_STEPS

    step_ids = [s["id"] for s in EXTRACTION_STEPS]

    # Verify core extraction steps are present
    assert "upload" in step_ids
    assert "extract_images" in step_ids
    assert "classify_images" in step_ids
    assert "detect_watermarks" in step_ids
    assert "remove_watermarks" in step_ids
    assert "extract_floor_plans" in step_ids
    assert "optimize_images" in step_ids
    assert "package_assets" in step_ids
    assert "extract_data" in step_ids
    assert "structure_data" in step_ids
    assert "materialize" in step_ids
    assert "upload_shared_assets" in step_ids  # Per addendum: Drive upload step

    # Verify generation steps are NOT in extraction
    assert "generate_content" not in step_ids
    assert "populate_sheet" not in step_ids

    # Must be exactly 12 steps (addendum fix: 1-10 + materialize + upload_shared_assets)
    assert len(step_ids) == 12


def test_generation_steps_defined():
    """Generation steps cover steps 11-14 (load package through finalize)."""
    from app.services.job_manager import GENERATION_STEPS

    step_ids = [s["id"] for s in GENERATION_STEPS]

    # Verify generation-specific steps
    assert "load_package" in step_ids
    assert "generate_content" in step_ids
    assert "populate_sheet" in step_ids
    assert "upload_cloud_generation" in step_ids  # Generation-specific upload
    assert "finalize_generation" in step_ids

    # Verify extraction steps are NOT in generation
    assert "extract_images" not in step_ids
    assert "classify_images" not in step_ids
    assert "materialize" not in step_ids

    assert len(step_ids) == 5


def test_get_steps_for_job_type_extraction():
    """get_steps_for_job_type returns EXTRACTION_STEPS for extraction jobs."""
    from app.services.job_manager import get_steps_for_job_type, EXTRACTION_STEPS

    steps = get_steps_for_job_type(JobType.EXTRACTION)
    assert steps == EXTRACTION_STEPS


def test_get_steps_for_job_type_generation():
    """get_steps_for_job_type returns GENERATION_STEPS for generation jobs."""
    from app.services.job_manager import get_steps_for_job_type, GENERATION_STEPS

    steps = get_steps_for_job_type(JobType.GENERATION)
    assert steps == GENERATION_STEPS


def test_get_steps_for_job_type_default_is_extraction():
    """get_steps_for_job_type returns EXTRACTION_STEPS by default."""
    from app.services.job_manager import get_steps_for_job_type, EXTRACTION_STEPS

    steps = get_steps_for_job_type(JobType.EXTRACTION)
    assert steps == EXTRACTION_STEPS


def test_extraction_steps_have_required_fields():
    """All extraction steps have id, label, and progress fields."""
    from app.services.job_manager import EXTRACTION_STEPS

    for step in EXTRACTION_STEPS:
        assert "id" in step, f"Step missing 'id' field"
        assert "label" in step, f"Step {step.get('id')} missing 'label' field"
        assert "progress" in step, f"Step {step.get('id')} missing 'progress' field"
        assert isinstance(step["progress"], int), f"Step {step['id']} progress must be int"


def test_generation_steps_have_required_fields():
    """All generation steps have id, label, and progress fields."""
    from app.services.job_manager import GENERATION_STEPS

    for step in GENERATION_STEPS:
        assert "id" in step, f"Step missing 'id' field"
        assert "label" in step, f"Step {step.get('id')} missing 'label' field"
        assert "progress" in step, f"Step {step.get('id')} missing 'progress' field"
        assert isinstance(step["progress"], int), f"Step {step['id']} progress must be int"


def test_extraction_steps_progress_ends_at_100():
    """Extraction steps progress ends at 100."""
    from app.services.job_manager import EXTRACTION_STEPS

    last_step = EXTRACTION_STEPS[-1]
    assert last_step["progress"] == 100, "Last extraction step must have progress=100"


def test_generation_steps_progress_ends_at_100():
    """Generation steps progress ends at 100."""
    from app.services.job_manager import GENERATION_STEPS

    last_step = GENERATION_STEPS[-1]
    assert last_step["progress"] == 100, "Last generation step must have progress=100"


# =============================================================================
# B.2b: _create_project_from_extraction Tests
# =============================================================================

@pytest.fixture
def mock_job_repo():
    """Create mock JobRepository."""
    repo = AsyncMock()
    repo.db = AsyncMock()
    repo.get_job = AsyncMock()
    return repo


@pytest.fixture
def mock_task_queue():
    """Create mock TaskQueue."""
    return AsyncMock()


@pytest.fixture
def job_manager(mock_job_repo, mock_task_queue):
    """Create JobManager with mocked dependencies."""
    from app.services.job_manager import JobManager

    return JobManager(mock_job_repo, mock_task_queue)


@pytest.mark.asyncio
async def test_create_project_from_extraction_creates_project(job_manager, mock_job_repo):
    """Creates Project record from pipeline context structured_data."""
    import uuid
    from app.models.enums import TemplateType, WorkflowStatus

    job_id = uuid.uuid4()

    # Set up pipeline context with structured data
    job_manager._pipeline_ctx[job_id] = {
        "structured_data": MagicMock(
            project_name="Azure Residences",
            developer="Nakheel",
            emirate="Dubai",
            community="Palm Jumeirah",
            property_type="Apartment",
            price_min=2500000,
            price_max=5000000,
            price_per_sqft=None,
            bedrooms=["1BR", "2BR", "3BR"],
            amenities=["Pool", "Gym"],
            handover_date="Q4 2025",
            payment_plan="60/40",
            key_features=["Sea view", "Beach access"],
            description="Luxury apartments",
            total_units=None,
            floors=None,
        )
    }

    # Mock job
    mock_job = MagicMock()
    mock_job.user_id = uuid.uuid4()
    mock_job.template_type = TemplateType.OPR
    mock_job_repo.get_job.return_value = mock_job

    # Mock database operations
    mock_db = mock_job_repo.db
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    project = await job_manager._create_project_from_extraction(job_id)

    # Verify project was created
    assert project is not None
    assert project.name == "Azure Residences"
    assert project.developer == "Nakheel"
    assert project.emirate == "Dubai"
    assert project.workflow_status == WorkflowStatus.DRAFT


@pytest.mark.asyncio
async def test_create_project_from_extraction_with_dict_data(job_manager, mock_job_repo):
    """Creates Project from dict-based structured_data."""
    import uuid
    from app.models.enums import TemplateType, WorkflowStatus

    job_id = uuid.uuid4()

    # Set up pipeline context with dict (not dataclass)
    job_manager._pipeline_ctx[job_id] = {
        "structured_data": {
            "project_name": "Test Project",
            "developer": "Test Developer",
            "emirate": "Abu Dhabi",
            "community": "Saadiyat",
            "property_type": "Villa",
        }
    }

    mock_job = MagicMock()
    mock_job.user_id = uuid.uuid4()
    mock_job.template_type = TemplateType.AGGREGATORS
    mock_job_repo.get_job.return_value = mock_job

    mock_db = mock_job_repo.db
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    project = await job_manager._create_project_from_extraction(job_id)

    assert project.name == "Test Project"
    assert project.workflow_status == WorkflowStatus.DRAFT


# =============================================================================
# B.3: _step_materialize_package Tests
# =============================================================================

@pytest.mark.asyncio
async def test_step_materialize_package_creates_package(job_manager, mock_job_repo):
    """Materialize step creates MaterialPackage from pipeline context."""
    job_id = uuid.uuid4()
    project_id = uuid.uuid4()

    # Setup pipeline context
    job_manager._pipeline_ctx[job_id] = {
        "structured_data": {"project_name": "Test"},
        "extraction": {"page_text_map": {1: "text"}},
        "floor_plans": {},
        "manifest": {"entries": [], "categories": {}},
        "classification": {"total_images": 5, "by_category": {"interior": 3}},
    }

    # Mock the service
    mock_package = MagicMock()
    mock_package.id = uuid.uuid4()
    mock_package_service = AsyncMock()
    mock_package_service.persist_to_gcs.return_value = f"materials/{project_id}"
    mock_package_service.create_package_record.return_value = mock_package
    mock_package_service.mark_ready.return_value = True
    job_manager._material_package_service = mock_package_service

    result = await job_manager._step_materialize_package(job_id, project_id)

    assert "material_package_id" in result
    assert "gcs_path" in result
    assert result["gcs_path"] == f"materials/{project_id}"
    mock_package_service.persist_to_gcs.assert_called_once()
    mock_package_service.create_package_record.assert_called_once()


@pytest.mark.asyncio
async def test_step_materialize_package_stores_in_context(job_manager, mock_job_repo):
    """Materialize step stores package ID in pipeline context."""
    job_id = uuid.uuid4()
    project_id = uuid.uuid4()
    package_id = uuid.uuid4()

    job_manager._pipeline_ctx[job_id] = {
        "structured_data": {},
        "extraction": {},
        "floor_plans": {},
        "manifest": {},
    }

    mock_package = MagicMock()
    mock_package.id = package_id
    mock_package_service = AsyncMock()
    mock_package_service.persist_to_gcs.return_value = f"materials/{project_id}"
    mock_package_service.create_package_record.return_value = mock_package
    mock_package_service.mark_ready.return_value = True
    job_manager._material_package_service = mock_package_service

    await job_manager._step_materialize_package(job_id, project_id)

    ctx = job_manager._pipeline_ctx[job_id]
    assert ctx["material_package_id"] == package_id
    assert ctx["material_package_gcs_path"] == f"materials/{project_id}"


# =============================================================================
# B.4: _step_load_material_package Tests
# =============================================================================

@pytest.mark.asyncio
async def test_step_load_material_package_populates_context(job_manager, mock_job_repo):
    """Load package step populates pipeline context from GCS."""
    from app.models.enums import MaterialPackageStatus

    job_id = uuid.uuid4()
    package_id = uuid.uuid4()

    # Mock job with material_package_id
    mock_job = MagicMock()
    mock_job.material_package_id = package_id
    mock_job_repo.get_job.return_value = mock_job

    # Mock package
    mock_package = MagicMock()
    mock_package.id = package_id
    mock_package.gcs_base_path = "materials/test-project"
    mock_package.status = MaterialPackageStatus.READY

    # Mock service
    mock_package_service = AsyncMock()
    mock_package_service.get_by_id.return_value = mock_package
    mock_package_service.load_from_gcs.return_value = {
        "structured_data": {"project_name": "Loaded Project"},
        "extracted_text": {"pages": {1: "Page 1 text"}},
        "floor_plans": {"floor_plans": []},
        "manifest": {"entries": []},
    }
    job_manager._material_package_service = mock_package_service

    job_manager._pipeline_ctx[job_id] = {}

    result = await job_manager._step_load_material_package(job_id)

    ctx = job_manager._pipeline_ctx[job_id]
    assert ctx["structured_data"]["project_name"] == "Loaded Project"
    assert "material_package_id" in result
    mock_package_service.load_from_gcs.assert_called_once_with("materials/test-project")


@pytest.mark.asyncio
async def test_step_load_material_package_raises_if_no_package_id(job_manager, mock_job_repo):
    """Load package raises error if job has no material_package_id."""
    job_id = uuid.uuid4()

    mock_job = MagicMock()
    mock_job.material_package_id = None
    mock_job_repo.get_job.return_value = mock_job

    job_manager._pipeline_ctx[job_id] = {}
    job_manager._material_package_service = AsyncMock()

    with pytest.raises(ValueError, match="has no material_package_id"):
        await job_manager._step_load_material_package(job_id)


@pytest.mark.asyncio
async def test_step_load_material_package_raises_if_not_ready(job_manager, mock_job_repo):
    """Load package raises error if package is not in READY status."""
    from app.models.enums import MaterialPackageStatus

    job_id = uuid.uuid4()
    package_id = uuid.uuid4()

    mock_job = MagicMock()
    mock_job.material_package_id = package_id
    mock_job_repo.get_job.return_value = mock_job

    mock_package = MagicMock()
    mock_package.id = package_id
    mock_package.status = MaterialPackageStatus.PENDING  # Not READY

    mock_package_service = AsyncMock()
    mock_package_service.get_by_id.return_value = mock_package
    job_manager._material_package_service = mock_package_service

    job_manager._pipeline_ctx[job_id] = {}

    with pytest.raises(ValueError, match="not ready"):
        await job_manager._step_load_material_package(job_id)


# =============================================================================
# B.5: JobRepository.create_job + JobManager.create_and_dispatch_job Tests
# =============================================================================

def test_job_repo_create_job_with_job_type():
    """Repository creates job with specified job_type."""
    from app.repositories.job_repository import JobRepository
    from app.models.database import Job
    from app.models.enums import JobType

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    repo = JobRepository(mock_db)

    # Run the coroutine
    import asyncio
    job = asyncio.get_event_loop().run_until_complete(
        repo.create_job(
            user_id=uuid.uuid4(),
            template_type="opr",
            job_type=JobType.EXTRACTION
        )
    )

    # Verify job was added with correct job_type
    mock_db.add.assert_called_once()
    added_job = mock_db.add.call_args[0][0]
    assert isinstance(added_job, Job)
    assert added_job.job_type == JobType.EXTRACTION


def test_job_repo_create_job_with_material_package_id():
    """Repository creates job with material_package_id."""
    from app.repositories.job_repository import JobRepository
    from app.models.database import Job
    from app.models.enums import JobType

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    repo = JobRepository(mock_db)
    package_id = uuid.uuid4()

    import asyncio
    job = asyncio.get_event_loop().run_until_complete(
        repo.create_job(
            user_id=uuid.uuid4(),
            template_type="opr",
            job_type=JobType.GENERATION,
            material_package_id=package_id
        )
    )

    mock_db.add.assert_called_once()
    added_job = mock_db.add.call_args[0][0]
    assert added_job.job_type == JobType.GENERATION
    assert added_job.material_package_id == package_id


def test_job_repo_create_job_defaults_to_extraction():
    """Repository defaults job_type to EXTRACTION when not specified."""
    from app.repositories.job_repository import JobRepository
    from app.models.database import Job
    from app.models.enums import JobType

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    repo = JobRepository(mock_db)

    import asyncio
    job = asyncio.get_event_loop().run_until_complete(
        repo.create_job(
            user_id=uuid.uuid4(),
            template_type="aggregators"
        )
    )

    mock_db.add.assert_called_once()
    added_job = mock_db.add.call_args[0][0]
    assert added_job.job_type == JobType.EXTRACTION


@pytest.mark.asyncio
async def test_job_manager_create_and_dispatch_job_with_job_type(job_manager, mock_job_repo, mock_task_queue):
    """JobManager.create_and_dispatch_job accepts job_type and material_package_id."""
    user_id = uuid.uuid4()
    package_id = uuid.uuid4()

    mock_job = MagicMock()
    mock_job.id = uuid.uuid4()
    mock_job.status = MagicMock()
    mock_job.status.value = "pending"
    mock_job.job_type = JobType.GENERATION

    mock_job_repo.create_job.return_value = mock_job
    mock_job_repo.db.commit = AsyncMock()
    mock_task_queue.enqueue_job.return_value = "task-123"

    job, task_name = await job_manager.create_and_dispatch_job(
        user_id=user_id,
        template_type="opr",
        pdf_path="file://test.pdf",
        job_type=JobType.GENERATION,
        material_package_id=package_id
    )

    # Verify create_job was called with job_type and material_package_id
    mock_job_repo.create_job.assert_called_once()
    call_kwargs = mock_job_repo.create_job.call_args.kwargs
    assert call_kwargs.get("job_type") == JobType.GENERATION
    assert call_kwargs.get("material_package_id") == package_id


# =============================================================================
# B.6: execute_extraction_pipeline Tests
# =============================================================================

@pytest.mark.asyncio
async def test_execute_extraction_pipeline_exists(job_manager):
    """JobManager has execute_extraction_pipeline method."""
    assert hasattr(job_manager, "execute_extraction_pipeline")
    assert callable(job_manager.execute_extraction_pipeline)


@pytest.mark.asyncio
async def test_dispatch_generation_jobs_dispatches_for_template_ids(job_manager, mock_job_repo):
    """_dispatch_generation_jobs creates generation jobs for each template_id."""
    extraction_job_id = uuid.uuid4()
    project_id = uuid.uuid4()
    package_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_job = MagicMock()
    mock_job.user_id = user_id
    mock_job.processing_config = {"template_ids": ["opr", "mpp", "aggregators"]}
    mock_job_repo.get_job.return_value = mock_job

    # Track dispatched jobs
    dispatched_templates = []

    async def mock_create_dispatch(
        user_id, template_type, pdf_path, job_type, material_package_id, processing_config
    ):
        dispatched_templates.append(template_type)
        mock_gen_job = MagicMock()
        mock_gen_job.id = uuid.uuid4()
        return mock_gen_job, "task-name"

    job_manager.create_and_dispatch_job = mock_create_dispatch

    result = await job_manager._dispatch_generation_jobs(
        extraction_job_id, project_id, package_id
    )

    assert len(result) == 3
    assert "opr" in dispatched_templates
    assert "mpp" in dispatched_templates
    assert "aggregators" in dispatched_templates


@pytest.mark.asyncio
async def test_dispatch_generation_jobs_skips_if_no_templates(job_manager, mock_job_repo):
    """_dispatch_generation_jobs returns empty if no template_ids."""
    extraction_job_id = uuid.uuid4()

    mock_job = MagicMock()
    mock_job.user_id = uuid.uuid4()
    mock_job.processing_config = {}  # No template_ids
    mock_job_repo.get_job.return_value = mock_job

    result = await job_manager._dispatch_generation_jobs(
        extraction_job_id, uuid.uuid4(), uuid.uuid4()
    )

    assert result == []


# =============================================================================
# B.6b: _step_upload_cloud_generation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_step_upload_cloud_generation_exists(job_manager):
    """JobManager has _step_upload_cloud_generation method."""
    assert hasattr(job_manager, "_step_upload_cloud_generation")
    assert callable(job_manager._step_upload_cloud_generation)


# =============================================================================
# B.7: execute_generation_pipeline Tests
# =============================================================================

@pytest.mark.asyncio
async def test_execute_generation_pipeline_exists(job_manager):
    """JobManager has execute_generation_pipeline method."""
    assert hasattr(job_manager, "execute_generation_pipeline")
    assert callable(job_manager.execute_generation_pipeline)


# =============================================================================
# B.8: _step_finalize_generation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_step_finalize_generation_exists(job_manager):
    """JobManager has _step_finalize_generation method."""
    assert hasattr(job_manager, "_step_finalize_generation")
    assert callable(job_manager._step_finalize_generation)
