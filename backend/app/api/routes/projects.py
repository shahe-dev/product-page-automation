"""
Project API endpoints.

Provides RESTful API for project management:
- GET    /api/v1/projects              List with filters
- POST   /api/v1/projects              Create new
- GET    /api/v1/projects/{id}         Get single
- PUT    /api/v1/projects/{id}         Update
- DELETE /api/v1/projects/{id}         Soft delete
- GET    /api/v1/projects/{id}/history Revision history
- POST   /api/v1/projects/{id}/fields  Add custom field
- POST   /api/v1/projects/export       Export to CSV
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.models.database import User
from app.models.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectDetailSchema,
    ProjectListResponse,
    ProjectRevisionSchema,
    ProjectFilter,
    PaginationParams,
    CustomFieldCreate,
    ProjectExportRequest,
    GenerationRunSummary
)
from app.services.project_service import ProjectService
from app.services.storage_service import StorageService
from app.api.dependencies import get_current_user, get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


async def _resolve_image_urls(
    images: list,
    storage: StorageService,
    expiry_minutes: int = 60,
) -> None:
    """Replace GCS blob paths with signed URLs in-place on schema objects."""
    async def _resolve_one(img):
        if img.image_url and not img.image_url.startswith("http"):
            try:
                img.image_url = await storage.generate_signed_url(
                    img.image_url, expiry_minutes
                )
            except Exception:
                img.image_url = ""
        if getattr(img, "thumbnail_url", None) and not img.thumbnail_url.startswith("http"):
            try:
                img.thumbnail_url = await storage.generate_signed_url(
                    img.thumbnail_url, expiry_minutes
                )
            except Exception:
                img.thumbnail_url = ""

    if images:
        await asyncio.gather(*[_resolve_one(img) for img in images])


async def _backfill_generated_content(project, db: AsyncSession) -> None:
    """Backfill Project.generated_content/sheet_url from GenerationRun if empty.

    Older generation runs wrote to GenerationRun but never updated the Project
    record. This one-time backfill copies the data so the frontend sees it.
    """
    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified
    from app.models.database import GenerationRun

    stmt = (
        select(GenerationRun)
        .where(GenerationRun.project_id == project.id)
        .where(GenerationRun.status == "completed")
        .order_by(GenerationRun.completed_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        return

    if run.generated_content:
        project.generated_content = dict(run.generated_content)
        flag_modified(project, "generated_content")
    if run.sheet_url:
        project.sheet_url = run.sheet_url
    await db.commit()
    logger.info("Backfilled generated_content on Project %s from GenerationRun %s", project.id, run.id)


def get_project_service(db: AsyncSession = Depends(get_db_session)) -> ProjectService:
    """Dependency to get project service instance."""
    return ProjectService(db)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    # Search and filters
    search: str | None = Query(None, description="Full-text search query"),
    developer: str | None = Query(None, description="Filter by developer"),
    emirate: str | None = Query(None, description="Filter by emirate"),
    location: str | None = Query(None, description="Filter by location"),
    workflow_status: str | None = Query(None, description="Filter by workflow status"),
    min_price: float | None = Query(None, ge=0, description="Minimum starting price"),
    max_price: float | None = Query(None, ge=0, description="Maximum starting price"),
    is_active: bool = Query(True, description="Filter by active status"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    # Dependencies
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    List projects with filtering, search, and pagination.

    Supports:
    - Full-text search across name, developer, location, description
    - Filter by developer, emirate, location, workflow status
    - Price range filtering
    - Active/inactive filtering
    - Pagination with configurable page size
    - Sorting by any field
    """
    try:
        # Build filter object
        filters = ProjectFilter(
            search=search,
            developer=developer,
            emirate=emirate,
            location=location,
            workflow_status=workflow_status,
            min_price=min_price,
            max_price=max_price,
            is_active=is_active
        )

        # Build pagination params
        pagination = PaginationParams(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Get projects
        result = await service.list_projects(filters, pagination)

        # Resolve thumbnail GCS paths to signed URLs (parallel)
        storage = StorageService()

        async def _resolve_thumbnail(item):
            if item.thumbnail and not item.thumbnail.startswith("http"):
                try:
                    item.thumbnail = await storage.generate_signed_url(
                        item.thumbnail
                    )
                except Exception:
                    item.thumbnail = None

        items_needing_resolve = [
            item for item in result.items
            if item.thumbnail and not item.thumbnail.startswith("http")
        ]
        if items_needing_resolve:
            await asyncio.gather(*[_resolve_thumbnail(item) for item in items_needing_resolve])

        logger.info(
            f"Listed {len(result.items)} projects (page {page}, total {result.total})"
        )

        return result

    except Exception as e:
        logger.exception(f"Failed to list projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.post("", response_model=ProjectDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    Create a new project.

    Requires authentication. The authenticated user will be set as the creator.
    """
    try:
        project = await service.create_project(project_data, current_user.id)

        logger.info(f"Project created: {project.id}")

        return ProjectDetailSchema.model_validate(project)

    except ValueError as e:
        logger.warning(f"Validation error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Failed to create project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


# Static routes must be defined BEFORE parameterized routes
# to prevent FastAPI from matching "/search" as "/{project_id}"

@router.get("/search")
async def search_projects(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    Full-text search for projects.

    Searches across:
    - Project name
    - Developer name
    - Location
    - Description

    Results are ranked by relevance.
    """
    try:
        projects = await service.search_projects(q, limit)

        logger.info(f"Search for '{q}' returned {len(projects)} results")

        return [ProjectDetailSchema.model_validate(p) for p in projects]

    except Exception as e:
        logger.exception(f"Search failed for query '{q}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.get("/statistics")
async def get_statistics(
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    Get project statistics.

    Returns:
    - Total project count
    - Count by workflow status
    - Generation timestamp
    """
    try:
        stats = await service.get_statistics()

        logger.info("Retrieved project statistics")

        return stats

    except Exception as e:
        logger.exception(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.get("/activity")
async def get_recent_activity(
    limit: int = Query(5, ge=1, le=100, description="Number of recent activities"),
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    Get recent project activity.

    Returns recently updated projects as ActivityItem format for dashboard display.
    """
    try:
        # Build filter for active projects only
        filters = ProjectFilter(is_active=True)

        # Get most recent projects by updated_at
        pagination = PaginationParams(
            page=1,
            page_size=limit,
            sort_by="updated_at",
            sort_order="desc"
        )

        result = await service.list_projects(filters, pagination)

        # Transform to ActivityItem format expected by frontend
        activities = []
        for project in result.items:
            # Determine activity type based on workflow status
            if project.workflow_status == "draft":
                activity_type = "project_created"
                description = "New project created"
            elif project.workflow_status == "pending_approval":
                activity_type = "approval_submitted"
                description = "Submitted for approval"
            elif project.workflow_status in ["published", "complete"]:
                activity_type = "job_completed"
                description = f"Project completed - {project.workflow_status}"
            else:
                activity_type = "project_updated"
                description = f"Project updated - {project.workflow_status}"

            user_name = "System"
            if project.created_by:
                if hasattr(project.created_by, 'name'):
                    user_name = project.created_by.name
                else:
                    user_name = str(project.created_by)

            activities.append({
                "id": str(project.id),
                "type": activity_type,
                "title": project.name,
                "description": description,
                "timestamp": project.updated_at.isoformat(),
                "user_name": user_name,
                "project_id": str(project.id)
            })

        logger.info(f"Retrieved {len(activities)} recent activities")

        return activities

    except Exception as e:
        logger.exception(f"Failed to get recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.post("/export")
async def export_projects(
    export_request: ProjectExportRequest,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    Export projects to CSV or JSON format.

    Can export:
    - Specific project IDs
    - All projects matching filters
    - Selected fields only

    Returns the exported data as a downloadable file.
    """
    try:
        # Export projects
        export_data = await service.export_projects(export_request)

        # Determine content type and filename
        if export_request.format == "csv":
            media_type = "text/csv"
            filename = f"projects_export_{int(datetime.now(timezone.utc).timestamp())}.csv"
        else:
            media_type = "application/json"
            filename = f"projects_export_{int(datetime.now(timezone.utc).timestamp())}.json"

        # Return as downloadable response
        from fastapi.responses import Response
        return Response(
            content=export_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error in export: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Failed to export projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


# Parameterized routes below - these must come AFTER static routes

@router.get("/{project_id}", response_model=ProjectDetailSchema)
async def get_project(
    project_id: UUID,
    include_inactive: bool = Query(False, description="Include soft-deleted projects"),
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    Get detailed project information by ID.

    Returns complete project data including:
    - All project fields
    - Related images
    - Related floor plans
    - Creator information
    """
    try:
        project = await service.get_project(project_id, include_inactive)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        # Backfill from GenerationRun if Project fields are empty
        if not project.generated_content and not project.sheet_url:
            await _backfill_generated_content(project, service.db)

        response = ProjectDetailSchema.model_validate(project)

        # Populate material_package_id from the latest READY package
        ready_packages = [
            p for p in project.material_packages
            if (p.status.value if hasattr(p.status, "value") else str(p.status)) == "ready"
        ]
        if ready_packages:
            latest_pkg = max(ready_packages, key=lambda p: p.created_at)
            response.material_package_id = latest_pkg.id

        # Populate generation_runs summaries
        response.generation_runs = [
            GenerationRunSummary(
                template_type=r.template_type.value if hasattr(r.template_type, "value") else str(r.template_type),
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
                sheet_url=r.sheet_url,
                completed_at=r.completed_at,
            )
            for r in project.generation_runs
        ]

        # Resolve GCS paths to signed URLs for images and floor plans
        storage = StorageService()
        await _resolve_image_urls(response.images, storage)
        await _resolve_image_urls(response.floor_plans, storage)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.put("/{project_id}", response_model=ProjectDetailSchema)
async def update_project(
    project_id: UUID,
    update_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    Update project fields.

    Supports partial updates - only provided fields will be updated.
    All changes are tracked in revision history.
    """
    try:
        project = await service.update_project(project_id, update_data, current_user.id)

        logger.info(f"Project updated: {project_id}")

        return ProjectDetailSchema.model_validate(project)

    except ValueError as e:
        logger.warning(f"Validation error updating project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Failed to update project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_admin),
    service: ProjectService = Depends(get_project_service)
):
    """
    Soft delete a project.

    Sets is_active to False. The project will be excluded from normal queries
    but can still be retrieved with include_inactive=True.

    Requires authenticated user (admin or project owner).
    """
    try:
        await service.delete_project(project_id, current_user.id)

        logger.info(f"Project deleted: {project_id}")

        return None

    except ValueError as e:
        logger.warning(f"Project not found for deletion: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.get("/{project_id}/history", response_model=List[ProjectRevisionSchema])
async def get_project_history(
    project_id: UUID,
    limit: int | None = Query(None, ge=1, le=1000, description="Limit number of revisions"),
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    Get revision history for a project.

    Returns all field changes with:
    - Field name
    - Old and new values
    - User who made the change
    - Timestamp
    - Optional change reason
    """
    try:
        revisions = await service.get_revision_history(project_id, limit)

        logger.info(f"Retrieved {len(revisions)} revisions for project {project_id}")

        return revisions

    except Exception as e:
        logger.exception(f"Failed to get revision history for {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.post("/{project_id}/fields", response_model=ProjectDetailSchema)
async def add_custom_field(
    project_id: UUID,
    field_data: CustomFieldCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    """
    Add or update a custom field on a project.

    Custom fields are stored in a JSONB column and can hold any JSON-serializable value.
    Changes to custom fields are tracked in revision history.
    """
    try:
        project = await service.add_custom_field(
            project_id,
            field_data.field_name,
            field_data.field_value,
            current_user.id
        )

        logger.info(
            f"Custom field added to project {project_id}: {field_data.field_name}"
        )

        return ProjectDetailSchema.model_validate(project)

    except ValueError as e:
        logger.warning(f"Validation error adding custom field: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Failed to add custom field to {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred"
        )


@router.get("/{project_id}/data-files")
async def get_data_files(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """
    Get parsed JSON data files from GCS for a project.

    Returns manifest.json, extracted_text.json, floor_plans.json,
    and structured_data.json as parsed JSON objects.
    """
    import json as json_mod

    storage = StorageService()
    file_names = [
        "manifest.json",
        "extracted_text.json",
        "floor_plans.json",
        "structured_data.json",
    ]
    gcs_base = f"materials/{project_id}"
    files: dict = {}

    for name in file_names:
        blob_path = f"{gcs_base}/{name}"
        try:
            data_bytes = await storage.download_file(blob_path)
            if data_bytes:
                files[name] = json_mod.loads(data_bytes.decode("utf-8"))
        except Exception:
            continue

    return {"files": files}
