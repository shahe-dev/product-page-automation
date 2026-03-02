"""
Project repository for database operations.

Provides data access layer for projects with:
- CRUD operations
- Full-text search
- Multi-field filtering
- Pagination
- Soft delete support
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, or_, and_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import Project, ProjectRevision, ProjectImage, ProjectFloorPlan, User, MaterialPackage, GenerationRun
from app.models.schemas import ProjectFilter, PaginationParams


def _escape_like(value: str) -> str:
    """Escape LIKE special characters to prevent SQL injection via wildcards."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ProjectRepository:
    """Repository for project database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create(self, project_data: Dict[str, Any], user_id: UUID) -> Project:
        """
        Create a new project.

        Args:
            project_data: Project data dictionary
            user_id: ID of user creating the project

        Returns:
            Created project instance
        """
        project = Project(
            **project_data,
            created_by=user_id,
            last_modified_by=user_id,
            is_active=True
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get_by_id(
        self,
        project_id: UUID,
        include_inactive: bool = False
    ) -> Optional[Project]:
        """
        Get project by ID with related data.

        Args:
            project_id: Project UUID
            include_inactive: Whether to include soft-deleted projects

        Returns:
            Project instance or None if not found
        """
        query = (
            select(Project)
            .options(
                selectinload(Project.creator),
                selectinload(Project.modifier),
                selectinload(Project.images),
                selectinload(Project.floor_plans),
                selectinload(Project.material_packages),
                selectinload(Project.generation_runs)
            )
            .where(Project.id == project_id)
        )

        if not include_inactive:
            query = query.where(Project.is_active == True)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self,
        project: Project,
        update_data: Dict[str, Any],
        user_id: UUID
    ) -> Project:
        """
        Update project fields.

        Args:
            project: Project instance to update
            update_data: Dictionary of fields to update
            user_id: ID of user making the update

        Returns:
            Updated project instance
        """
        for field, value in update_data.items():
            if hasattr(project, field):
                setattr(project, field, value)

        project.last_modified_by = user_id
        project.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def soft_delete(self, project: Project) -> None:
        """
        Soft delete a project (set is_active to False).

        Args:
            project: Project instance to soft delete
        """
        project.is_active = False
        project.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def list_projects(
        self,
        filters: ProjectFilter,
        pagination: PaginationParams
    ) -> Tuple[List[Project], int]:
        """
        List projects with filtering and pagination.

        Args:
            filters: Filter criteria
            pagination: Pagination parameters

        Returns:
            Tuple of (list of projects, total count)
        """
        # Base query - eager load relationships to avoid async lazy loading issues
        query = select(Project).options(
            selectinload(Project.creator),
            selectinload(Project.images),
            selectinload(Project.floor_plans)
        )

        # Apply filters
        conditions = []

        # Active status filter
        if filters.is_active:
            conditions.append(Project.is_active == True)

        # Full-text search
        if filters.search:
            search_term = filters.search.strip()
            # Use PostgreSQL full-text search
            search_vector = func.to_tsvector(
                'english',
                func.coalesce(Project.name, '') + ' ' +
                func.coalesce(Project.developer, '') + ' ' +
                func.coalesce(Project.location, '') + ' ' +
                func.coalesce(Project.description, '')
            )
            search_query = func.plainto_tsquery('english', search_term)
            conditions.append(search_vector.op('@@')(search_query))

        # Developer filter
        if filters.developer:
            escaped = _escape_like(filters.developer)
            conditions.append(Project.developer.ilike(f"%{escaped}%", escape="\\"))

        # Emirate filter
        if filters.emirate:
            conditions.append(Project.emirate == filters.emirate)

        # Location filter
        if filters.location:
            escaped = _escape_like(filters.location)
            conditions.append(Project.location.ilike(f"%{escaped}%", escape="\\"))

        # Workflow status filter
        if filters.workflow_status:
            conditions.append(Project.workflow_status == filters.workflow_status)

        # Price range filters
        if filters.min_price is not None:
            conditions.append(Project.starting_price >= filters.min_price)

        if filters.max_price is not None:
            conditions.append(Project.starting_price <= filters.max_price)

        # Date range filters
        if filters.created_after:
            conditions.append(Project.created_at >= filters.created_after)

        if filters.created_before:
            conditions.append(Project.created_at <= filters.created_before)

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        if pagination.sort_by:
            sort_column = getattr(Project, pagination.sort_by, Project.created_at)
            if pagination.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)

        # Execute query
        result = await self.db.execute(query)
        projects = result.scalars().all()

        return list(projects), total

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
        search_term = search_query.strip()

        # Use PostgreSQL full-text search with ranking
        search_vector = func.to_tsvector(
            'english',
            func.coalesce(Project.name, '') + ' ' +
            func.coalesce(Project.developer, '') + ' ' +
            func.coalesce(Project.location, '') + ' ' +
            func.coalesce(Project.description, '')
        )
        search_query_ts = func.plainto_tsquery('english', search_term)
        rank = func.ts_rank(search_vector, search_query_ts)

        query = (
            select(Project)
            .where(
                and_(
                    Project.is_active == True,
                    search_vector.op('@@')(search_query_ts)
                )
            )
            .order_by(desc(rank))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_revision_history(
        self,
        project_id: UUID,
        limit: Optional[int] = None
    ) -> List[ProjectRevision]:
        """
        Get revision history for a project.

        Args:
            project_id: Project UUID
            limit: Optional limit on number of revisions

        Returns:
            List of project revisions
        """
        query = (
            select(ProjectRevision)
            .options(selectinload(ProjectRevision.user))
            .where(ProjectRevision.project_id == project_id)
            .order_by(desc(ProjectRevision.created_at))
        )

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_revision(
        self,
        project_id: UUID,
        field: str,
        old_value: Optional[str],
        new_value: Optional[str],
        user_id: UUID,
        change_reason: Optional[str] = None
    ) -> ProjectRevision:
        """
        Create a revision record for a field change.

        Args:
            project_id: Project UUID
            field: Field name that changed
            old_value: Previous value
            new_value: New value
            user_id: ID of user making the change
            change_reason: Optional reason for change

        Returns:
            Created revision instance
        """
        revision = ProjectRevision(
            project_id=project_id,
            field=field,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            changed_by=user_id,
            change_reason=change_reason
        )
        self.db.add(revision)
        await self.db.flush()
        await self.db.refresh(revision)
        return revision

    async def add_custom_field(
        self,
        project: Project,
        field_name: str,
        field_value: Any
    ) -> Project:
        """
        Add or update a custom field on a project.

        Args:
            project: Project instance
            field_name: Custom field name
            field_value: Custom field value

        Returns:
            Updated project instance
        """
        if project.custom_fields is None:
            project.custom_fields = {}

        project.custom_fields[field_name] = field_value
        project.updated_at = datetime.now(timezone.utc)

        # Mark the JSONB field as modified for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "custom_fields")

        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get_by_developer(
        self,
        developer: str,
        limit: int = 50
    ) -> List[Project]:
        """
        Get projects by developer name.

        Args:
            developer: Developer name
            limit: Maximum number of results

        Returns:
            List of projects
        """
        query = (
            select(Project)
            .where(
                and_(
                    Project.developer.ilike(f"%{_escape_like(developer)}%", escape="\\"),
                    Project.is_active == True
                )
            )
            .order_by(desc(Project.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_emirate(
        self,
        emirate: str,
        limit: int = 50
    ) -> List[Project]:
        """
        Get projects by emirate.

        Args:
            emirate: Emirate name
            limit: Maximum number of results

        Returns:
            List of projects
        """
        query = (
            select(Project)
            .where(
                and_(
                    Project.emirate == emirate,
                    Project.is_active == True
                )
            )
            .order_by(desc(Project.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_workflow_status(
        self,
        workflow_status: str,
        limit: int = 50
    ) -> List[Project]:
        """
        Get projects by workflow status.

        Args:
            workflow_status: Workflow status value
            limit: Maximum number of results

        Returns:
            List of projects
        """
        query = (
            select(Project)
            .where(
                and_(
                    Project.workflow_status == workflow_status,
                    Project.is_active == True
                )
            )
            .order_by(desc(Project.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self) -> Dict[str, int]:
        """
        Get count of projects grouped by workflow status.

        Returns:
            Dictionary mapping status to count
        """
        query = (
            select(
                Project.workflow_status,
                func.count(Project.id).label('count')
            )
            .where(Project.is_active == True)
            .group_by(Project.workflow_status)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return {row.workflow_status: row.count for row in rows}

    async def get_projects_for_export(
        self,
        project_ids: Optional[List[UUID]] = None,
        filters: Optional[ProjectFilter] = None
    ) -> List[Project]:
        """
        Get projects for export (CSV/JSON).

        Args:
            project_ids: Optional list of specific project IDs
            filters: Optional filters to apply

        Returns:
            List of projects
        """
        query = select(Project).options(
            selectinload(Project.creator),
            selectinload(Project.images),
            selectinload(Project.floor_plans)
        )

        conditions = [Project.is_active == True]

        if project_ids:
            conditions.append(Project.id.in_(project_ids))

        if filters:
            if filters.developer:
                conditions.append(Project.developer.ilike(f"%{_escape_like(filters.developer)}%", escape="\\"))
            if filters.emirate:
                conditions.append(Project.emirate == filters.emirate)
            if filters.workflow_status:
                conditions.append(Project.workflow_status == filters.workflow_status)

        query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return list(result.scalars().all())
