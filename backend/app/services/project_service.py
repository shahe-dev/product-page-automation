"""
Project service layer for business logic.

Handles:
- Project CRUD operations with validation
- Search and filtering
- Revision tracking
- Custom fields management
- Data export
"""

import csv
import json
import logging
from datetime import datetime, timezone
from io import StringIO
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Project
from app.models.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectFilter,
    PaginationParams,
    ProjectListResponse,
    ProjectRevisionSchema,
    ProjectExportRequest,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db
        self.repository = ProjectRepository(db)

    async def create_project(
        self,
        project_data: ProjectCreate,
        user_id: UUID
    ) -> Project:
        """
        Create a new project.

        Args:
            project_data: Project creation data
            user_id: ID of user creating the project

        Returns:
            Created project instance

        Raises:
            ValueError: If validation fails
        """
        try:
            # Convert Pydantic model to dict
            data_dict = project_data.model_dump(exclude_unset=True)

            # Create project
            project = await self.repository.create(data_dict, user_id)

            # Log the creation
            logger.info(
                f"Project created: {project.id}",
                extra={"project_id": str(project.id), "user_id": str(user_id)}
            )

            await self.db.commit()
            return project

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create project: {e}")
            raise

    async def get_project(
        self,
        project_id: UUID,
        include_inactive: bool = False
    ) -> Optional[Project]:
        """
        Get project by ID.

        Args:
            project_id: Project UUID
            include_inactive: Whether to include soft-deleted projects

        Returns:
            Project instance or None if not found
        """
        return await self.repository.get_by_id(project_id, include_inactive)

    async def update_project(
        self,
        project_id: UUID,
        update_data: ProjectUpdate,
        user_id: UUID
    ) -> Project:
        """
        Update project with revision tracking.

        Args:
            project_id: Project UUID
            update_data: Fields to update
            user_id: ID of user making the update

        Returns:
            Updated project instance

        Raises:
            ValueError: If project not found
        """
        try:
            # Get existing project
            project = await self.repository.get_by_id(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")

            # Track changes for revision history
            changes = []
            update_dict = update_data.model_dump(exclude_unset=True)

            for field, new_value in update_dict.items():
                if hasattr(project, field):
                    old_value = getattr(project, field)

                    # Only track if value actually changed
                    if old_value != new_value:
                        changes.append({
                            "field": field,
                            "old_value": old_value,
                            "new_value": new_value
                        })

            # Update the project
            updated_project = await self.repository.update(
                project,
                update_dict,
                user_id
            )

            # Create revision records for each change
            for change in changes:
                await self.repository.create_revision(
                    project_id=project_id,
                    field=change["field"],
                    old_value=change["old_value"],
                    new_value=change["new_value"],
                    user_id=user_id
                )

            await self.db.commit()

            logger.info(
                f"Project updated: {project_id}",
                extra={
                    "project_id": str(project_id),
                    "user_id": str(user_id),
                    "fields_changed": len(changes)
                }
            )

            return updated_project

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update project {project_id}: {e}")
            raise

    async def delete_project(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Soft delete a project.

        Args:
            project_id: Project UUID
            user_id: ID of user deleting the project

        Raises:
            ValueError: If project not found
        """
        try:
            project = await self.repository.get_by_id(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")

            await self.repository.soft_delete(project)

            # Create revision record for deletion
            await self.repository.create_revision(
                project_id=project_id,
                field="is_active",
                old_value="True",
                new_value="False",
                user_id=user_id,
                change_reason="Project deleted"
            )

            await self.db.commit()

            logger.info(
                f"Project deleted: {project_id}",
                extra={"project_id": str(project_id), "user_id": str(user_id)}
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete project {project_id}: {e}")
            raise

    async def list_projects(
        self,
        filters: ProjectFilter,
        pagination: PaginationParams
    ) -> ProjectListResponse:
        """
        List projects with filtering and pagination.

        Args:
            filters: Filter criteria
            pagination: Pagination parameters

        Returns:
            Paginated list of projects
        """
        projects, total = await self.repository.list_projects(filters, pagination)

        # Calculate pagination metadata
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        has_next = pagination.page < total_pages
        has_prev = pagination.page > 1

        # Convert to response schema
        from app.models.schemas import ProjectListItemSchema

        items = []
        for project in projects:
            # Count related entities
            # Relationships are eagerly loaded via selectinload in the repository.
            # Access directly -- do NOT use hasattr() which can trigger lazy-load
            # errors on async sessions.
            image_count = len(project.images) if project.images else 0
            floor_plan_count = len(project.floor_plans) if project.floor_plans else 0

            # Derive thumbnail from first exterior image, fallback to first image
            thumbnail = None
            if project.images:
                exterior = next(
                    (img for img in project.images if img.category.value == "exterior"),
                    None,
                )
                first_img = exterior or project.images[0]
                thumbnail = first_img.image_url

            item = ProjectListItemSchema(
                id=project.id,
                name=project.name,
                developer=project.developer,
                location=project.location,
                emirate=project.emirate,
                starting_price=project.starting_price,
                template_type=project.template_type,
                workflow_status=project.workflow_status,
                created_at=project.created_at,
                updated_at=project.updated_at,
                created_by=project.creator,
                image_count=image_count,
                floor_plan_count=floor_plan_count,
                thumbnail=thumbnail,
            )
            items.append(item)

        return ProjectListResponse(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )

    async def search_projects(
        self,
        search_query: str,
        limit: int = 50
    ) -> List[Project]:
        """
        Full-text search for projects.

        Args:
            search_query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching projects
        """
        return await self.repository.search_projects(search_query, limit)

    async def get_revision_history(
        self,
        project_id: UUID,
        limit: Optional[int] = None
    ) -> List[ProjectRevisionSchema]:
        """
        Get revision history for a project.

        Args:
            project_id: Project UUID
            limit: Optional limit on number of revisions

        Returns:
            List of project revisions
        """
        revisions = await self.repository.get_revision_history(project_id, limit)

        # Convert to response schema
        return [
            ProjectRevisionSchema(
                id=rev.id,
                field=rev.field,
                old_value=rev.old_value,
                new_value=rev.new_value,
                changed_by=rev.user,
                change_reason=rev.change_reason,
                created_at=rev.created_at
            )
            for rev in revisions
        ]

    async def add_custom_field(
        self,
        project_id: UUID,
        field_name: str,
        field_value: Any,
        user_id: UUID
    ) -> Project:
        """
        Add or update a custom field on a project.

        Args:
            project_id: Project UUID
            field_name: Custom field name
            field_value: Custom field value
            user_id: ID of user adding the field

        Returns:
            Updated project instance

        Raises:
            ValueError: If project not found
        """
        try:
            project = await self.repository.get_by_id(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")

            # Get old value for revision tracking
            old_value = project.custom_fields.get(field_name) if project.custom_fields else None

            # Add/update custom field
            updated_project = await self.repository.add_custom_field(
                project,
                field_name,
                field_value
            )

            # Update last modified metadata
            updated_project.last_modified_by = user_id
            updated_project.updated_at = datetime.now(timezone.utc)

            # Create revision record
            await self.repository.create_revision(
                project_id=project_id,
                field=f"custom_fields.{field_name}",
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(field_value),
                user_id=user_id,
                change_reason=f"Custom field '{field_name}' updated"
            )

            await self.db.commit()

            logger.info(
                f"Custom field added to project {project_id}: {field_name}",
                extra={"project_id": str(project_id), "field_name": field_name}
            )

            return updated_project

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to add custom field: {e}")
            raise

    async def export_projects(
        self,
        export_request: ProjectExportRequest
    ) -> str:
        """
        Export projects to CSV or JSON format.

        Args:
            export_request: Export configuration

        Returns:
            Exported data as string

        Raises:
            ValueError: If export format is invalid
        """
        # Get projects based on IDs or filters
        projects = await self.repository.get_projects_for_export(
            project_ids=export_request.project_ids,
            filters=export_request.filters
        )

        if export_request.format == "csv":
            return self._export_to_csv(projects, export_request.fields)
        elif export_request.format == "json":
            return self._export_to_json(projects, export_request.fields)
        else:
            raise ValueError(f"Unsupported export format: {export_request.format}")

    def _export_to_csv(
        self,
        projects: List[Project],
        fields: Optional[List[str]] = None
    ) -> str:
        """
        Export projects to CSV format.

        Args:
            projects: List of projects to export
            fields: Optional list of fields to include

        Returns:
            CSV data as string
        """
        output = StringIO()

        # Define default fields if not specified
        if not fields:
            fields = [
                "id", "name", "developer", "location", "emirate",
                "starting_price", "handover_date", "workflow_status",
                "created_at"
            ]

        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()

        for project in projects:
            row = {}
            for field in fields:
                value = getattr(project, field, None)
                # Handle special formatting
                if isinstance(value, (datetime, )):
                    value = value.isoformat()
                elif isinstance(value, UUID):
                    value = str(value)
                elif isinstance(value, (list, dict)):
                    value = json.dumps(value)
                row[field] = value

            writer.writerow(row)

        return output.getvalue()

    def _export_to_json(
        self,
        projects: List[Project],
        fields: Optional[List[str]] = None
    ) -> str:
        """
        Export projects to JSON format.

        Args:
            projects: List of projects to export
            fields: Optional list of fields to include

        Returns:
            JSON data as string
        """
        result = []

        for project in projects:
            project_dict = {}

            # Get all fields if not specified
            if not fields:
                fields = [
                    c.name for c in project.__table__.columns
                    if c.name not in ["created_by", "last_modified_by"]
                ]

            for field in fields:
                value = getattr(project, field, None)
                # Handle special types for JSON serialization
                if isinstance(value, (datetime, )):
                    value = value.isoformat()
                elif isinstance(value, UUID):
                    value = str(value)
                project_dict[field] = value

            result.append(project_dict)

        return json.dumps(result, indent=2, default=str)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get project and job statistics for dashboard.

        Returns:
            Dictionary with statistics matching DashboardStats interface:
            - total_projects: Total active project count
            - active_projects: Projects in non-terminal states
            - completed_projects: Projects in published or complete state
            - pending_approvals: Projects awaiting approval
            - failed_jobs: Count of failed jobs
        """
        count_by_status = await self.repository.count_by_status()

        # Get job statistics for failed jobs count
        job_repo = JobRepository(self.db)
        job_stats = await job_repo.get_job_statistics()

        total = sum(count_by_status.values())

        # Active = projects in non-terminal workflow states
        active_statuses = [
            "draft", "pending_approval", "approved",
            "revision_requested", "publishing"
        ]
        active_projects = sum(count_by_status.get(s, 0) for s in active_statuses)

        # Completed = projects in terminal states
        completed_statuses = ["published", "complete"]
        completed_projects = sum(count_by_status.get(s, 0) for s in completed_statuses)

        # Pending approvals
        pending_approvals = count_by_status.get("pending_approval", 0)

        # Failed jobs from job statistics
        failed_jobs = job_stats.get("failed", 0)

        return {
            "total_projects": total,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "pending_approvals": pending_approvals,
            "failed_jobs": failed_jobs
        }
