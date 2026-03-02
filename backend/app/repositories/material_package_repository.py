"""
Repository for MaterialPackage database operations.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import MaterialPackage
from app.models.enums import MaterialPackageStatus

logger = logging.getLogger(__name__)


class MaterialPackageRepository:
    """Data access layer for MaterialPackage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        project_id: Optional[UUID],
        source_job_id: Optional[UUID],
        gcs_base_path: str,
        extraction_summary: Optional[dict] = None,
        structured_data: Optional[dict] = None,
        expires_in_days: int = 30
    ) -> MaterialPackage:
        """Create a new MaterialPackage record."""
        package = MaterialPackage(
            project_id=project_id,
            source_job_id=source_job_id,
            gcs_base_path=gcs_base_path,
            extraction_summary=extraction_summary or {},
            structured_data=structured_data or {},
            status=MaterialPackageStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        )
        self.db.add(package)
        await self.db.flush()
        await self.db.refresh(package)
        return package

    async def get_by_id(self, package_id: UUID) -> Optional[MaterialPackage]:
        """Get MaterialPackage by ID."""
        result = await self.db.execute(
            select(MaterialPackage).where(MaterialPackage.id == package_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: UUID) -> Optional[MaterialPackage]:
        """Get the latest READY MaterialPackage for a project."""
        result = await self.db.execute(
            select(MaterialPackage)
            .where(MaterialPackage.project_id == project_id)
            .where(MaterialPackage.status == MaterialPackageStatus.READY)
            .order_by(MaterialPackage.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        package_id: UUID,
        status: MaterialPackageStatus,
        structured_data: Optional[dict] = None
    ) -> bool:
        """Update package status and optionally structured data."""
        values: dict = {"status": status, "updated_at": datetime.now(timezone.utc)}
        if structured_data is not None:
            values["structured_data"] = structured_data

        result = await self.db.execute(
            update(MaterialPackage)
            .where(MaterialPackage.id == package_id)
            .values(**values)
        )
        return result.rowcount > 0

    async def mark_ready(
        self,
        package_id: UUID,
        extraction_summary: dict,
        structured_data: dict
    ) -> bool:
        """Mark package as ready with final data."""
        result = await self.db.execute(
            update(MaterialPackage)
            .where(MaterialPackage.id == package_id)
            .values(
                status=MaterialPackageStatus.READY,
                extraction_summary=extraction_summary,
                structured_data=structured_data,
                updated_at=datetime.now(timezone.utc)
            )
        )
        return result.rowcount > 0

    async def mark_error(self, package_id: UUID) -> bool:
        """Mark package as errored."""
        result = await self.db.execute(
            update(MaterialPackage)
            .where(MaterialPackage.id == package_id)
            .values(
                status=MaterialPackageStatus.ERROR,
                updated_at=datetime.now(timezone.utc)
            )
        )
        return result.rowcount > 0
