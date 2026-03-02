"""
Process API endpoints for multi-template pipeline.

Provides endpoints for extraction and generation workflows:
- POST /api/v1/process/extract - Start extraction-only job
- POST /api/v1/process/generate - Start generation job for template(s)
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.middleware.auth import get_current_user
from app.models.database import User
from app.models.enums import JobType
from app.repositories.job_repository import JobRepository
from app.repositories.material_package_repository import MaterialPackageRepository
from app.services.job_manager import JobManager
from app.services.material_package_service import MaterialPackageService
from app.services.storage_service import StorageService
from app.background.task_queue import TaskQueue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/process", tags=["process"])


# =============================================================================
# Request/Response Schemas
# =============================================================================

class ExtractRequest(BaseModel):
    """Request body for extraction job."""
    pdf_url: str = Field(..., description="GCS URL or local path to the PDF file")
    template_ids: list[str] = Field(
        default_factory=list,
        description="Template types to auto-generate after extraction (e.g., ['opr', 'mpp'])"
    )


class ExtractResponse(BaseModel):
    """Response for extraction job creation."""
    extraction_job_id: str
    status: str
    template_ids: list[str]
    message: str


class GenerateRequest(BaseModel):
    """Request body for generation job(s)."""
    material_package_id: str = Field(..., description="UUID of the MaterialPackage to use")
    template_types: list[str] = Field(
        ...,
        description="Template types to generate (e.g., ['opr', 'mpp'])"
    )


class GenerateResponse(BaseModel):
    """Response for generation job(s) creation."""
    generation_job_ids: list[str]
    status: str
    message: str



# MaterialPackageResponse and GenerationRunResponse imported from schemas
from app.models.schemas import MaterialPackageResponse, GenerationRunResponse


# =============================================================================
# Dependencies (per addendum: use Depends() pattern from upload.py)
# =============================================================================

def get_job_manager(db: AsyncSession = Depends(get_db_session)) -> JobManager:
    """Create JobManager with dependencies."""
    job_repo = JobRepository(db)
    task_queue = TaskQueue()
    return JobManager(job_repo, task_queue)


def get_material_package_service(
    db: AsyncSession = Depends(get_db_session)
) -> MaterialPackageService:
    """Create MaterialPackageService with dependencies."""
    storage = StorageService()
    repo = MaterialPackageRepository(db)
    return MaterialPackageService(storage, repo)


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/extract",
    status_code=status.HTTP_201_CREATED,
    response_model=ExtractResponse,
    summary="Start extraction job",
    description="Start an extraction-only job that creates a MaterialPackage"
)
async def start_extraction(
    request: ExtractRequest,
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
    material_package_service: MaterialPackageService = Depends(get_material_package_service),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Start an extraction-only job.

    This creates a job that runs steps 1-12 (extraction + materialization)
    and produces a MaterialPackage in GCS. After extraction completes,
    generation jobs are auto-dispatched for any templates specified in
    template_ids.

    Args:
        request: Extraction request with PDF URL and optional template IDs
        current_user: Authenticated user
        job_manager: JobManager instance
        material_package_service: MaterialPackageService instance
        db: Database session

    Returns:
        ExtractResponse with job ID and status
    """
    try:
        # Inject material package service into job manager
        job_manager._material_package_service = material_package_service

        # Create and dispatch extraction job
        job, task_name = await job_manager.create_and_dispatch_job(
            user_id=current_user.id,
            template_type="aggregators",  # Default template for extraction
            pdf_path=request.pdf_url,
            job_type=JobType.EXTRACTION,
            processing_config={
                "pdf_url": request.pdf_url,
                "template_ids": request.template_ids,  # For auto-dispatch after extraction
            }
        )

        logger.info(
            f"Extraction job {job.id} created for user {current_user.email}, "
            f"template_ids={request.template_ids}, task={task_name}"
        )

        return ExtractResponse(
            extraction_job_id=str(job.id),
            status=job.status.value,
            template_ids=request.template_ids,
            message=f"Extraction job created. "
                    f"Generation jobs will be auto-dispatched for: {', '.join(request.template_ids) or 'none'}"
        )

    except Exception as e:
        logger.exception(f"Failed to create extraction job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "EXTRACTION_JOB_FAILED",
                "message": str(e),
            }
        )


@router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=GenerateResponse,
    summary="Start generation job(s)",
    description="Start generation jobs for specified templates using an existing MaterialPackage"
)
async def start_generation(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
    material_package_service: MaterialPackageService = Depends(get_material_package_service),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Start generation jobs for specified templates.

    This creates one job per template type, each running steps 11-14
    (load package -> generate -> populate sheet -> upload -> finalize).
    All jobs use the same MaterialPackage.

    Args:
        request: Generation request with package ID and template types
        current_user: Authenticated user
        job_manager: JobManager instance
        material_package_service: MaterialPackageService instance
        db: Database session

    Returns:
        GenerateResponse with job IDs and status
    """
    try:
        # Inject material package service into job manager
        job_manager._material_package_service = material_package_service

        # Validate material package exists and is ready
        package_id = UUID(request.material_package_id)
        package = await material_package_service.get_by_id(package_id)

        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "PACKAGE_NOT_FOUND",
                    "message": f"MaterialPackage {package_id} not found"
                }
            )

        from app.models.enums import MaterialPackageStatus
        if package.status != MaterialPackageStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "PACKAGE_NOT_READY",
                    "message": f"MaterialPackage {package_id} is not ready (status={package.status.value})"
                }
            )

        # Create generation jobs for each template
        job_ids = []
        for template_type in request.template_types:
            job, task_name = await job_manager.create_and_dispatch_job(
                user_id=current_user.id,
                template_type=template_type,
                pdf_path="",  # Not needed for generation
                job_type=JobType.GENERATION,
                material_package_id=package_id,
                processing_config={
                    "project_id": str(package.project_id) if package.project_id else None,
                }
            )
            job_ids.append(str(job.id))

            logger.info(
                f"Generation job {job.id} created for template {template_type}, "
                f"package={package_id}, user={current_user.email}"
            )

        return GenerateResponse(
            generation_job_ids=job_ids,
            status="dispatched",
            message=f"Created {len(job_ids)} generation job(s) for templates: {', '.join(request.template_types)}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create generation jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GENERATION_JOB_FAILED",
                "message": str(e),
            }
        )


@router.get(
    "/material-packages/{package_id}",
    response_model=MaterialPackageResponse,
    summary="Get MaterialPackage details"
)
async def get_material_package(
    package_id: UUID,
    current_user: User = Depends(get_current_user),
    material_package_service: MaterialPackageService = Depends(get_material_package_service)
):
    """Get details of a MaterialPackage by ID."""
    package = await material_package_service.get_by_id(package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialPackage {package_id} not found"
        )
    return MaterialPackageResponse.from_package(package)


@router.get(
    "/projects/{project_id}/generations",
    response_model=list[GenerationRunResponse],
    summary="List GenerationRuns for a project"
)
async def list_project_generations(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """List all generation runs for a project."""
    from app.repositories.generation_run_repository import GenerationRunRepository
    repo = GenerationRunRepository(db)
    runs = await repo.list_by_project(project_id)
    return [GenerationRunResponse.from_run(run) for run in runs]
