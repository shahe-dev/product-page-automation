"""
Workflow/Kanban API endpoints.

Provides workflow management functionality:
- GET /api/v1/workflow/board          - Get Kanban board
- PUT /api/v1/workflow/items/{id}/move  - Move item between columns
- PUT /api/v1/workflow/items/{id}/assign - Assign item to user
- GET /api/v1/workflow/stats          - Get workflow statistics
- GET /api/v1/workflow/items          - Get workflow items (paginated)
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.config.database import get_db_session
from app.middleware.auth import get_current_user
from app.models.database import User, Project, ProjectApproval
from app.models.enums import WorkflowStatus, ApprovalAction, NotificationType
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])

# Valid workflow transitions based on the WorkflowStatus enum flow
VALID_TRANSITIONS: Dict[str, list[str]] = {
    "draft": ["pending_approval"],
    "pending_approval": ["approved", "revision_requested", "draft"],
    "approved": ["publishing", "revision_requested"],
    "revision_requested": ["draft", "pending_approval"],
    "publishing": ["published"],
    "published": ["qa_verified"],
    "qa_verified": ["complete", "revision_requested"],
    "complete": [],
}


# Request/Response Models

class WorkflowItemMove(BaseModel):
    """Request to move workflow item."""
    workflow_status: str = Field(..., description="New workflow status")
    published_url: Optional[str] = Field(None, description="URL of published page (for publishing->published)")


class WorkflowItemAssign(BaseModel):
    """Request to assign workflow item."""
    assigned_to: UUID = Field(..., description="User ID to assign to")


class WorkflowItem(BaseModel):
    """Workflow item (project)."""
    id: UUID
    name: str
    developer: Optional[str] = None
    workflow_status: str
    assigned_to: Optional[Dict[str, str]] = None
    created_at: str
    updated_at: str
    priority: Optional[str] = None


class WorkflowBoard(BaseModel):
    """Kanban board with columns."""
    columns: Dict[str, list[WorkflowItem]]
    total_items: int


class WorkflowStats(BaseModel):
    """Workflow statistics."""
    total_projects: int
    by_status: Dict[str, int]
    by_assignee: Dict[str, int]
    avg_processing_time_hours: float


class ApprovalSubmitRequest(BaseModel):
    """Request to submit project for approval."""
    project_id: UUID = Field(..., description="Project ID to submit")


class ApprovalRejectRequest(BaseModel):
    """Request to reject approval."""
    reason: str = Field(..., min_length=1, description="Rejection reason")


class ApprovalItem(BaseModel):
    """Approval queue item."""
    id: str
    project_id: str
    project_name: str
    submitted_by: str
    submitted_at: str
    status: str


def _project_to_item(project: Project, user_lookup: Optional[Dict[UUID, str]] = None) -> WorkflowItem:
    """Convert a Project model instance to a WorkflowItem response."""
    assigned_to = None
    if project.last_modified_by:
        name = "Unknown"
        if user_lookup and project.last_modified_by in user_lookup:
            name = user_lookup[project.last_modified_by]
        assigned_to = {"id": str(project.last_modified_by), "name": name}

    return WorkflowItem(
        id=project.id,
        name=project.name,
        developer=project.developer,
        workflow_status=project.workflow_status.value,
        assigned_to=assigned_to,
        created_at=project.created_at.isoformat() + "Z",
        updated_at=project.updated_at.isoformat() + "Z",
        priority=None,
    )


@router.get(
    "/board",
    status_code=status.HTTP_200_OK,
    response_model=WorkflowBoard,
    summary="Get Kanban board",
    description="Get workflow board with all items organized by status",
)
async def get_workflow_board(
    assigned_to: Optional[UUID] = Query(None, description="Filter by assigned user"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get Kanban board with projects grouped by workflow status."""
    query = select(Project).where(Project.is_active.is_(True))

    if assigned_to is not None:
        query = query.where(Project.last_modified_by == assigned_to)

    query = query.order_by(Project.updated_at.desc())
    result = await db.execute(query)
    projects = result.scalars().all()

    # Group by status
    columns: Dict[str, list[WorkflowItem]] = {
        ws.value: [] for ws in WorkflowStatus
    }
    for project in projects:
        item = _project_to_item(project)
        columns[project.workflow_status.value].append(item)

    return WorkflowBoard(
        columns=columns,
        total_items=len(projects),
    )


@router.put(
    "/items/{item_id}/move",
    status_code=status.HTTP_200_OK,
    summary="Move workflow item",
    description="Move item to a different workflow status",
)
async def move_workflow_item(
    item_id: UUID,
    request: WorkflowItemMove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Move workflow item to a different status with transition validation."""
    # Validate target status is a real enum value
    valid_statuses = [ws.value for ws in WorkflowStatus]
    if request.workflow_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid workflow status",
                "details": {"provided": request.workflow_status, "allowed": valid_statuses},
            },
        )

    # Fetch project
    result = await db.execute(select(Project).where(Project.id == item_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {item_id} not found"},
        )

    # Validate transition
    current_status = project.workflow_status.value
    allowed = VALID_TRANSITIONS.get(current_status, [])
    if request.workflow_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_TRANSITION",
                "message": f"Cannot move from '{current_status}' to '{request.workflow_status}'",
                "details": {"current": current_status, "allowed": allowed},
            },
        )

    # Update
    project.workflow_status = WorkflowStatus(request.workflow_status)
    project.last_modified_by = current_user.id

    # If transitioning to "published", save the URL
    if request.workflow_status == WorkflowStatus.PUBLISHED.value and request.published_url:
        project.published_url = request.published_url
        project.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(project)

    logger.info(
        "Workflow item %s moved from %s to %s by %s",
        item_id, current_status, request.workflow_status, current_user.email,
    )

    return {
        "id": str(project.id),
        "workflow_status": project.workflow_status.value,
        "updated_at": project.updated_at.isoformat() + "Z",
        "updated_by": {"id": str(current_user.id), "name": current_user.name},
    }


@router.put(
    "/items/{item_id}/assign",
    status_code=status.HTTP_200_OK,
    summary="Assign workflow item",
    description="Assign item to a user",
)
async def assign_workflow_item(
    item_id: UUID,
    request: WorkflowItemAssign,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Assign workflow item to a user."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == item_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {item_id} not found"},
        )

    # Verify assignee exists
    user_result = await db.execute(select(User).where(User.id == request.assigned_to))
    assignee = user_result.scalar_one_or_none()
    if assignee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"User {request.assigned_to} not found"},
        )

    # Update assignment
    project.last_modified_by = assignee.id
    await db.commit()
    await db.refresh(project)

    logger.info(
        "Workflow item %s assigned to %s by %s",
        item_id, assignee.email, current_user.email,
    )

    return {
        "id": str(project.id),
        "assigned_to": {"id": str(assignee.id), "name": assignee.name},
        "assigned_at": project.updated_at.isoformat() + "Z",
        "assigned_by": {"id": str(current_user.id), "name": current_user.name},
    }


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    response_model=WorkflowStats,
    summary="Get workflow statistics",
    description="Get workflow statistics and metrics",
)
async def get_workflow_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get workflow statistics aggregated from the database."""
    # Total active projects
    total_result = await db.execute(
        select(func.count(Project.id)).where(Project.is_active.is_(True))
    )
    total_projects = total_result.scalar() or 0

    # Count by status
    status_result = await db.execute(
        select(Project.workflow_status, func.count(Project.id))
        .where(Project.is_active.is_(True))
        .group_by(Project.workflow_status)
    )
    by_status: Dict[str, int] = {ws.value: 0 for ws in WorkflowStatus}
    for ws_val, count in status_result.all():
        by_status[ws_val.value if hasattr(ws_val, "value") else str(ws_val)] = count

    # Count by assignee (last_modified_by)
    assignee_result = await db.execute(
        select(User.name, func.count(Project.id))
        .join(User, User.id == Project.last_modified_by)
        .where(Project.is_active.is_(True))
        .where(Project.last_modified_by.isnot(None))
        .group_by(User.name)
    )
    by_assignee: Dict[str, int] = {row[0]: row[1] for row in assignee_result.all()}

    # Average processing time (draft -> complete) in hours
    # Use time between created_at and updated_at for completed projects as proxy
    avg_result = await db.execute(
        select(
            func.avg(
                func.extract("epoch", Project.updated_at - Project.created_at) / 3600.0
            )
        )
        .where(Project.is_active.is_(True))
        .where(Project.workflow_status == WorkflowStatus.COMPLETE)
    )
    avg_hours = avg_result.scalar() or 0.0

    return WorkflowStats(
        total_projects=total_projects,
        by_status=by_status,
        by_assignee=by_assignee,
        avg_processing_time_hours=round(float(avg_hours), 1),
    )


@router.get(
    "/items",
    status_code=status.HTTP_200_OK,
    summary="Get workflow items",
    description="Get workflow items with filtering",
)
async def get_workflow_items(
    workflow_status: Optional[str] = Query(None, alias="status", description="Filter by workflow status"),
    assigned_to: Optional[UUID] = Query(None, description="Filter by assigned user"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get paginated workflow items with optional filters."""
    query = select(Project).where(Project.is_active.is_(True))
    count_query = select(func.count(Project.id)).where(Project.is_active.is_(True))

    if workflow_status:
        try:
            ws = WorkflowStatus(workflow_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid workflow status",
                    "details": {
                        "provided": workflow_status,
                        "allowed": [s.value for s in WorkflowStatus],
                    },
                },
            )
        query = query.where(Project.workflow_status == ws)
        count_query = count_query.where(Project.workflow_status == ws)

    if assigned_to is not None:
        query = query.where(Project.last_modified_by == assigned_to)
        count_query = count_query.where(Project.last_modified_by == assigned_to)

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    query = query.order_by(Project.updated_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()

    items = [_project_to_item(p) for p in projects]
    pages = max(1, (total + limit - 1) // limit)

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }


# =============================================================================
# Approval Endpoints
# =============================================================================

@router.get(
    "/approvals",
    status_code=status.HTTP_200_OK,
    summary="Get approval queue",
    description="Get list of projects pending approval or with approval history",
)
async def get_approval_queue(
    approval_status: Optional[str] = Query(None, alias="status", description="Filter by status: pending, approved, rejected"),
    project_id: Optional[UUID] = Query(None, description="Filter by specific project"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get approval queue with pending, approved, and rejected items."""
    # Get projects in pending_approval status or with approval records
    query = (
        select(Project)
        .options(selectinload(Project.creator))
        .where(Project.is_active.is_(True))
    )

    if project_id:
        query = query.where(Project.id == project_id)

    # Filter by approval status
    if approval_status == "pending":
        query = query.where(Project.workflow_status == WorkflowStatus.PENDING_APPROVAL)
    elif approval_status == "approved":
        query = query.where(Project.workflow_status == WorkflowStatus.APPROVED)
    elif approval_status == "rejected":
        query = query.where(Project.workflow_status == WorkflowStatus.REVISION_REQUESTED)
    else:
        # Default: show all projects in approval-related statuses
        query = query.where(
            Project.workflow_status.in_([
                WorkflowStatus.PENDING_APPROVAL,
                WorkflowStatus.APPROVED,
                WorkflowStatus.REVISION_REQUESTED
            ])
        )

    query = query.order_by(Project.updated_at.desc())
    result = await db.execute(query)
    projects = result.scalars().all()

    # Transform to approval items
    items = []
    for project in projects:
        # Map workflow status to approval status
        if project.workflow_status == WorkflowStatus.PENDING_APPROVAL:
            status_str = "pending"
        elif project.workflow_status == WorkflowStatus.APPROVED:
            status_str = "approved"
        elif project.workflow_status == WorkflowStatus.REVISION_REQUESTED:
            status_str = "rejected"
        else:
            status_str = "pending"

        submitted_by = "Unknown"
        if project.creator:
            submitted_by = project.creator.name

        items.append({
            "id": str(project.id),
            "project_id": str(project.id),
            "project_name": project.name,
            "submitted_by": submitted_by,
            "submitted_at": project.updated_at.isoformat(),
            "status": status_str
        })

    return items


@router.post(
    "/approvals",
    status_code=status.HTTP_201_CREATED,
    summary="Submit project for approval",
    description="Submit a project for approval review",
)
async def submit_for_approval(
    request: ApprovalSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Submit a project for approval."""
    # Fetch project
    result = await db.execute(
        select(Project).where(Project.id == request.project_id)
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {request.project_id} not found"},
        )

    # Validate transition (only draft can be submitted)
    if project.workflow_status != WorkflowStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_TRANSITION",
                "message": f"Cannot submit project in '{project.workflow_status.value}' status. Must be 'draft'.",
            },
        )

    # Update project status
    project.workflow_status = WorkflowStatus.PENDING_APPROVAL
    project.last_modified_by = current_user.id

    # Create approval record
    approval = ProjectApproval(
        project_id=project.id,
        action=ApprovalAction.SUBMITTED,
        approver_id=current_user.id,
        comments="Submitted for approval"
    )
    db.add(approval)

    await db.commit()
    await db.refresh(project)

    # Notify all users about new submission
    try:
        await notification_service.notify_all_users(
            db=db,
            type=NotificationType.APPROVAL,
            title="Approval Needed",
            message=f'"{project.name}" has been submitted for approval',
            project_id=project.id,
            exclude_user_id=current_user.id,
        )
        await db.commit()
    except Exception:
        logger.warning("Failed to send submission notifications for project %s", project.id)

    logger.info(
        "Project %s submitted for approval by %s",
        project.id, current_user.email,
    )

    return {
        "id": str(project.id),
        "project_id": str(project.id),
        "status": "pending",
        "submitted_at": project.updated_at.isoformat(),
    }


@router.post(
    "/approvals/{project_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve project",
    description="Approve a project that is pending approval",
)
async def approve_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Approve a project."""
    # Fetch project
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {project_id} not found"},
        )

    # Validate project is pending approval
    if project.workflow_status != WorkflowStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_TRANSITION",
                "message": f"Cannot approve project in '{project.workflow_status.value}' status. Must be 'pending_approval'.",
            },
        )

    # Update project status
    project.workflow_status = WorkflowStatus.APPROVED
    project.last_modified_by = current_user.id

    # Create approval record
    approval = ProjectApproval(
        project_id=project.id,
        action=ApprovalAction.APPROVED,
        approver_id=current_user.id,
        comments="Approved"
    )
    db.add(approval)

    await db.commit()
    await db.refresh(project)

    # Notify the project creator
    if project.created_by:
        try:
            await notification_service.create(
                db=db,
                user_id=project.created_by,
                type=NotificationType.SUCCESS,
                title="Project Approved",
                message=f'"{project.name}" has been approved',
                project_id=project.id,
            )
            await db.commit()
        except Exception:
            logger.warning("Failed to send approval notification for project %s", project.id)

    logger.info(
        "Project %s approved by %s",
        project.id, current_user.email,
    )

    return {
        "id": str(project.id),
        "project_id": str(project.id),
        "status": "approved",
        "approved_at": project.updated_at.isoformat(),
        "approved_by": {"id": str(current_user.id), "name": current_user.name},
    }


@router.post(
    "/approvals/{project_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Reject project",
    description="Reject a project with a reason",
)
async def reject_project(
    project_id: UUID,
    request: ApprovalRejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Reject a project with a reason."""
    # Fetch project
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {project_id} not found"},
        )

    # Validate project is pending approval
    if project.workflow_status != WorkflowStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_TRANSITION",
                "message": f"Cannot reject project in '{project.workflow_status.value}' status. Must be 'pending_approval'.",
            },
        )

    # Update project status
    project.workflow_status = WorkflowStatus.REVISION_REQUESTED
    project.last_modified_by = current_user.id

    # Create approval record with rejection reason
    approval = ProjectApproval(
        project_id=project.id,
        action=ApprovalAction.REJECTED,
        approver_id=current_user.id,
        comments=request.reason
    )
    db.add(approval)

    await db.commit()
    await db.refresh(project)

    # Notify the project creator about rejection
    if project.created_by:
        try:
            await notification_service.create(
                db=db,
                user_id=project.created_by,
                type=NotificationType.WARNING,
                title="Revision Requested",
                message=f'"{project.name}" needs revision: {request.reason[:200]}',
                project_id=project.id,
            )
            await db.commit()
        except Exception:
            logger.warning("Failed to send rejection notification for project %s", project.id)

    logger.info(
        "Project %s rejected by %s. Reason: %s",
        project.id, current_user.email, request.reason,
    )

    return {
        "id": str(project.id),
        "project_id": str(project.id),
        "status": "rejected",
        "rejected_at": project.updated_at.isoformat(),
        "rejected_by": {"id": str(current_user.id), "name": current_user.name},
        "reason": request.reason,
    }
