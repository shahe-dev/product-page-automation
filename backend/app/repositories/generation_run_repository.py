"""
Repository for GenerationRun database operations.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import GenerationRun
from app.models.enums import GenerationRunStatus, TemplateType

logger = logging.getLogger(__name__)


class GenerationRunRepository:
    """Data access layer for GenerationRun."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        project_id: UUID,
        template_type: TemplateType,
        material_package_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None
    ) -> GenerationRun:
        """Create a new GenerationRun record."""
        run = GenerationRun(
            project_id=project_id,
            material_package_id=material_package_id,
            template_type=template_type,
            job_id=job_id,
            status=GenerationRunStatus.PENDING
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def get_by_id(self, run_id: UUID) -> Optional[GenerationRun]:
        """Get GenerationRun by ID."""
        result = await self.db.execute(
            select(GenerationRun).where(GenerationRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project_and_template(
        self,
        project_id: UUID,
        template_type: TemplateType
    ) -> Optional[GenerationRun]:
        """Get GenerationRun for specific project and template."""
        result = await self.db.execute(
            select(GenerationRun)
            .where(GenerationRun.project_id == project_id)
            .where(GenerationRun.template_type == template_type)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: UUID) -> list[GenerationRun]:
        """List all GenerationRuns for a project."""
        result = await self.db.execute(
            select(GenerationRun)
            .where(GenerationRun.project_id == project_id)
            .order_by(GenerationRun.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        run_id: UUID,
        status: GenerationRunStatus
    ) -> bool:
        """Update run status."""
        result = await self.db.execute(
            update(GenerationRun)
            .where(GenerationRun.id == run_id)
            .values(status=status)
        )
        return result.rowcount > 0

    async def mark_processing(self, run_id: UUID) -> bool:
        """Mark run as processing."""
        return await self.update_status(run_id, GenerationRunStatus.PROCESSING)

    async def mark_completed(
        self,
        run_id: UUID,
        generated_content: dict,
        sheet_url: Optional[str] = None,
        drive_folder_url: Optional[str] = None
    ) -> bool:
        """Mark run as completed with results."""
        result = await self.db.execute(
            update(GenerationRun)
            .where(GenerationRun.id == run_id)
            .values(
                status=GenerationRunStatus.COMPLETED,
                generated_content=generated_content,
                sheet_url=sheet_url,
                drive_folder_url=drive_folder_url,
                completed_at=datetime.now(timezone.utc)
            )
        )
        return result.rowcount > 0

    async def mark_failed(self, run_id: UUID) -> bool:
        """Mark run as failed."""
        result = await self.db.execute(
            update(GenerationRun)
            .where(GenerationRun.id == run_id)
            .values(status=GenerationRunStatus.FAILED)
        )
        return result.rowcount > 0
