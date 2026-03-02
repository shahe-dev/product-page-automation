"""
QA comparison API endpoints.

Provides quality assurance functionality:
- POST /api/v1/qa/compare             - Run QA comparison (501)
- GET  /api/v1/qa/{project_id}/results - Get QA results
- POST /api/v1/qa/issues/{id}/resolve - Resolve QA issue
- POST /api/v1/qa/issues/{id}/override - Override QA issue
- GET  /api/v1/qa/history             - Get QA history
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.middleware.auth import get_current_user
from app.models.database import (
    User, Project, QAComparison, QACheckpoint, QAIssue, QAOverride,
)
from app.models.enums import (
    QACheckpointType, QAOverrideType, UserRole,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["qa"])


# Request/Response Models

class QACompareRequest(BaseModel):
    """Request to run QA comparison."""
    project_id: UUID = Field(..., description="Project ID to check")
    checkpoint_type: str = Field(..., description="Checkpoint type: generation, sheets, final")
    input_content: Optional[Dict[str, Any]] = Field(None, description="Input content to compare")
    comparison_target: Optional[Dict[str, Any]] = Field(None, description="Target to compare against")


class QADifference(BaseModel):
    """QA difference detail."""
    field: str
    expected: Optional[str]
    actual: Optional[str]
    severity: str


class QACompareResponse(BaseModel):
    """QA comparison response."""
    id: UUID
    status: str
    matches: int
    differences: int
    missing: int
    extra: int
    result: Dict[str, Any]
    performed_at: str


class QAIssueResolveRequest(BaseModel):
    """Request to resolve QA issue."""
    resolution: str = Field(..., description="Resolution type: fixed, wont_fix, duplicate")
    comments: Optional[str] = Field(None, description="Resolution comments")


class QAIssueOverrideRequest(BaseModel):
    """Request to override QA issue."""
    reason: str = Field(..., description="Override reason")
    approved_by: Optional[str] = Field(None, description="Approver name/email")


@router.post(
    "/compare",
    status_code=status.HTTP_200_OK,
    response_model=QACompareResponse,
    summary="Run QA comparison",
    description="Run quality assurance comparison at checkpoint"
)
async def run_qa_comparison(
    request: QACompareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Run QA comparison at a checkpoint.

    This endpoint requires the QA comparison algorithm which is
    not yet wired into this route.
    """
    # Validate checkpoint type
    valid_checkpoints = [ct.value for ct in QACheckpointType]
    if request.checkpoint_type not in valid_checkpoints:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid checkpoint type",
                "details": {"provided": request.checkpoint_type, "allowed": valid_checkpoints},
            },
        )

    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {request.project_id} not found"},
        )

    # Load source data (MaterialPackage) and generated data (GenerationRun)
    from app.models.database import MaterialPackage, GenerationRun
    from app.models.enums import MaterialPackageStatus, GenerationRunStatus

    pkg_result = await db.execute(
        select(MaterialPackage)
        .where(MaterialPackage.project_id == request.project_id)
        .order_by(MaterialPackage.created_at.desc())
        .limit(1)
    )
    package = pkg_result.scalar_one_or_none()

    gen_result = await db.execute(
        select(GenerationRun)
        .where(GenerationRun.project_id == request.project_id)
        .order_by(GenerationRun.created_at.desc())
        .limit(1)
    )
    gen_run = gen_result.scalar_one_or_none()

    source_data = {}
    generated_data = {}

    if package and package.structured_data:
        source_data = package.structured_data if isinstance(package.structured_data, dict) else {}
    if gen_run and gen_run.generated_content:
        generated_data = gen_run.generated_content if isinstance(gen_run.generated_content, dict) else {}

    # Use provided overrides if given
    if request.input_content:
        source_data = request.input_content
    if request.comparison_target:
        generated_data = request.comparison_target

    # Field-by-field comparison
    all_keys = set(list(source_data.keys()) + list(generated_data.keys()))
    matches = 0
    differences = 0
    missing = 0
    extra = 0
    diff_details = []

    for key in sorted(all_keys):
        src_val = source_data.get(key)
        gen_val = generated_data.get(key)

        if src_val is not None and gen_val is not None:
            src_str = str(src_val).strip().lower()
            gen_str = str(gen_val).strip().lower()
            if src_str == gen_str:
                matches += 1
            else:
                differences += 1
                diff_details.append({
                    "field": key,
                    "expected": str(src_val)[:500],
                    "actual": str(gen_val)[:500],
                    "severity": "minor",
                })
        elif src_val is not None and gen_val is None:
            missing += 1
            diff_details.append({
                "field": key,
                "expected": str(src_val)[:500],
                "actual": None,
                "severity": "major",
            })
        elif src_val is None and gen_val is not None:
            extra += 1

    # Store QA comparison record
    now = datetime.now(timezone.utc)
    comparison = QAComparison(
        project_id=request.project_id,
        checkpoint_type=QACheckpointType(request.checkpoint_type),
        status="completed",
        matches=matches,
        differences=differences,
        missing=missing,
        extra=extra,
        result={"diff_details": diff_details, "source_keys": list(source_data.keys()), "generated_keys": list(generated_data.keys())},
        performed_by=current_user.id,
        performed_at=now,
    )
    db.add(comparison)
    await db.commit()
    await db.refresh(comparison)

    return QACompareResponse(
        id=comparison.id,
        status="completed",
        matches=matches,
        differences=differences,
        missing=missing,
        extra=extra,
        result=comparison.result,
        performed_at=now.isoformat() + "Z",
    )


@router.get(
    "/{project_id}/results",
    status_code=status.HTTP_200_OK,
    summary="Get QA results",
    description="Get QA comparison results for a project"
)
async def get_qa_results(
    project_id: UUID,
    checkpoint_type: Optional[str] = Query(None, description="Filter by checkpoint type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get QA results for a project from the database."""
    # Verify project exists
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    if proj_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {project_id} not found"},
        )

    query = (
        select(QAComparison)
        .where(QAComparison.project_id == project_id)
        .order_by(QAComparison.performed_at.desc())
    )

    if checkpoint_type:
        try:
            ct = QACheckpointType(checkpoint_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid checkpoint type",
                    "details": {"provided": checkpoint_type, "allowed": [c.value for c in QACheckpointType]},
                },
            )
        query = query.where(QAComparison.checkpoint_type == ct)

    result = await db.execute(query)
    comparisons = result.scalars().all()

    items = []
    for c in comparisons:
        items.append({
            "id": str(c.id),
            "checkpoint_type": c.checkpoint_type.value,
            "status": c.status,
            "matches": c.matches or 0,
            "differences": c.differences or 0,
            "missing": c.missing or 0,
            "extra": c.extra or 0,
            "performed_at": c.performed_at.isoformat() + "Z",
            "performed_by": str(c.performed_by),
        })

    return {
        "project_id": str(project_id),
        "results": items,
        "total": len(items),
    }


@router.post(
    "/issues/{issue_id}/resolve",
    status_code=status.HTTP_200_OK,
    summary="Resolve QA issue",
    description="Mark a QA issue as resolved"
)
async def resolve_qa_issue(
    issue_id: UUID,
    request: QAIssueResolveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Resolve a QA issue."""
    # Validate resolution type
    valid_resolutions = ["fixed", "wont_fix", "duplicate"]
    if request.resolution not in valid_resolutions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid resolution type",
                "details": {"provided": request.resolution, "allowed": valid_resolutions},
            },
        )

    # Fetch issue
    result = await db.execute(select(QAIssue).where(QAIssue.id == issue_id))
    issue = result.scalar_one_or_none()
    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"QA issue {issue_id} not found"},
        )

    issue.is_resolved = True
    issue.resolved_by = current_user.id
    issue.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(issue)

    logger.info("QA issue %s resolved as '%s' by %s", issue_id, request.resolution, current_user.email)

    return {
        "id": str(issue.id),
        "status": "resolved",
        "resolution": request.resolution,
        "resolved_by": {"id": str(current_user.id), "name": current_user.name},
        "resolved_at": issue.resolved_at.isoformat() + "Z",
        "comments": request.comments,
    }


@router.post(
    "/issues/{issue_id}/override",
    status_code=status.HTTP_200_OK,
    summary="Override QA issue",
    description="Override a QA issue (admin approval)"
)
async def override_qa_issue(
    issue_id: UUID,
    request: QAIssueOverrideRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Override a QA issue with admin approval."""
    # Check admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "FORBIDDEN", "message": "Only admins can override QA issues"},
        )

    # Fetch issue
    result = await db.execute(select(QAIssue).where(QAIssue.id == issue_id))
    issue = result.scalar_one_or_none()
    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"QA issue {issue_id} not found"},
        )

    # Create override record
    override = QAOverride(
        issue_id=issue.id,
        override_type=QAOverrideType.ACCEPT,
        reason=request.reason,
        overridden_by=current_user.id,
    )
    db.add(override)

    # Mark issue as resolved
    issue.is_resolved = True
    issue.resolved_by = current_user.id
    issue.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(override)

    logger.info("QA issue %s overridden by admin %s", issue_id, current_user.email)

    return {
        "id": str(issue.id),
        "status": "overridden",
        "overridden_by": {"id": str(current_user.id), "name": current_user.name},
        "overridden_at": override.created_at.isoformat() + "Z",
        "reason": request.reason,
        "approved_by": request.approved_by,
    }


@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Get QA history",
    description="Get QA comparison history for user or project"
)
async def get_qa_history(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    checkpoint_type: Optional[str] = Query(None, description="Filter by checkpoint type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get QA comparison history with pagination."""
    query = select(QAComparison)

    if project_id:
        query = query.where(QAComparison.project_id == project_id)

    if checkpoint_type:
        try:
            ct = QACheckpointType(checkpoint_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid checkpoint type",
                    "details": {"provided": checkpoint_type, "allowed": [c.value for c in QACheckpointType]},
                },
            )
        query = query.where(QAComparison.checkpoint_type == ct)

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Paginate
    offset = (page - 1) * limit
    query = query.order_by(QAComparison.performed_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    comparisons = result.scalars().all()

    items = []
    for c in comparisons:
        items.append({
            "id": str(c.id),
            "project_id": str(c.project_id),
            "checkpoint_type": c.checkpoint_type.value,
            "status": c.status,
            "performed_at": c.performed_at.isoformat() + "Z",
            "performed_by": str(c.performed_by),
        })

    pages = max(1, (total + limit - 1) // limit)

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
    }
