"""
Download endpoints for PDP Automation v.3

Provides ZIP download for project assets (images, floor plans, source PDF).
"""

import asyncio
import io
import logging
import zipfile
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.database import Project, ProjectFloorPlan, ProjectImage, User
from app.models.enums import ImageCategory
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/downloads", tags=["downloads"])

# Maximum total download size: 200 MB
MAX_DOWNLOAD_SIZE_BYTES = 200 * 1024 * 1024


def _sanitize_filename(name: str) -> str:
    """Strip path separators, null bytes, and spaces from a filename for safe ZIP entry."""
    return name.replace("/", "_").replace("\\", "_").replace("\0", "").replace(" ", "_")


@router.get("/projects/{project_id}/assets")
async def download_project_assets(
    project_id: UUID,
    category: Optional[str] = Query(
        None,
        description="Image category filter: exterior, interior, amenity, logo, floor_plan, or all",
    ),
    ids: Optional[str] = Query(
        None,
        description="Comma-separated ProjectImage/ProjectFloorPlan UUIDs for selective download",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download project assets as a ZIP archive.

    Streams a ZIP containing images, floor plans, and optionally the source PDF.
    Supports filtering by category or specific asset IDs.
    """
    # 1. Look up project (str() cast for SQLite test compat -- VARCHAR(36) vs UUID)
    result = await db.execute(
        select(Project).where(Project.id == str(project_id), Project.is_active == True)  # noqa: E712
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Parse IDs if provided
    selected_ids: set[str] = set()
    if ids:
        selected_ids = {s.strip() for s in ids.split(",") if s.strip()}

    # 2. Query images and floor plans
    include_all = not category or category == "all"

    images: list[ProjectImage] = []
    floor_plans: list[ProjectFloorPlan] = []

    if selected_ids:
        # When IDs provided, fetch only those specific records (ignore category)
        img_result = await db.execute(
            select(ProjectImage).where(
                ProjectImage.project_id == str(project_id),
                ProjectImage.id.in_(list(selected_ids)),
            )
        )
        images = list(img_result.scalars().all())

        fp_result = await db.execute(
            select(ProjectFloorPlan).where(
                ProjectFloorPlan.project_id == str(project_id),
                ProjectFloorPlan.id.in_(list(selected_ids)),
            )
        )
        floor_plans = list(fp_result.scalars().all())
    else:
        # Filter by category
        if include_all or category != "floor_plan":
            img_query = select(ProjectImage).where(
                ProjectImage.project_id == str(project_id)
            )
            if not include_all and category:
                try:
                    cat_enum = ImageCategory(category)
                except ValueError:
                    cat_enum = category
                img_query = img_query.where(ProjectImage.category == cat_enum)
            img_result = await db.execute(img_query)
            images = list(img_result.scalars().all())

        if include_all or category == "floor_plan":
            fp_result = await db.execute(
                select(ProjectFloorPlan).where(
                    ProjectFloorPlan.project_id == str(project_id)
                )
            )
            floor_plans = list(fp_result.scalars().all())

    # 3. Collect GCS blob paths
    download_tasks: list[dict] = []

    for img in images:
        blob_path = img.image_url
        cat = str(img.category.value if hasattr(img.category, "value") else img.category)
        ext = img.format or "webp"
        zip_path = f"images/{cat}/{cat}_{img.display_order + 1}.{ext}"
        download_tasks.append(
            {"blob_path": blob_path, "zip_path": zip_path, "file_size": img.file_size or 0}
        )

    for fp in floor_plans:
        blob_path = fp.image_url
        zip_path = f"floor_plans/{_sanitize_filename(fp.unit_type)}_{fp.display_order + 1}.webp"
        download_tasks.append({"blob_path": blob_path, "zip_path": zip_path, "file_size": 0})

    # 4. Include source PDF when downloading all (no IDs, no specific category)
    source_pdf_blobs: list[str] = []
    if include_all and not selected_ids:
        try:
            source_prefix = f"materials/{project_id}/source/"
            source_files = await storage_service.list_files(prefix=source_prefix)
            for sf in source_files:
                filename = sf.rsplit("/", 1)[-1] if "/" in sf else sf
                download_tasks.append(
                    {"blob_path": sf, "zip_path": f"source/{filename}", "file_size": 0}
                )
                source_pdf_blobs.append(sf)
        except Exception:
            logger.warning("Could not list source files for project %s", project_id)

    # 5. Check we have files
    if not download_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No downloadable assets found for this project",
        )

    # 6. Size guard (from known file_size in DB)
    known_total = sum(t["file_size"] for t in download_tasks)
    if known_total > MAX_DOWNLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Total download size ({known_total // (1024*1024)} MB) exceeds 200 MB limit",
        )

    # 7. Download all files from GCS concurrently
    semaphore = asyncio.Semaphore(10)
    skipped: list[str] = []

    async def _download_blob(task: dict) -> tuple[str, bytes | None]:
        async with semaphore:
            try:
                data = await storage_service.download_file(task["blob_path"])
                return task["zip_path"], data
            except Exception as e:
                logger.warning(
                    "Skipping file %s: %s", task["blob_path"], str(e)
                )
                skipped.append(task["blob_path"])
                return task["zip_path"], None

    results = await asyncio.gather(*[_download_blob(t) for t in download_tasks])

    # 8. Build ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for zip_path, data in results:
            if data is not None:
                zf.writestr(zip_path, data)

        if skipped:
            skipped_content = "\n".join(skipped)
            zf.writestr("_skipped.txt", skipped_content)

    zip_buffer.seek(0)

    # 9. Check actual ZIP isn't empty (all files skipped)
    if zip_buffer.getbuffer().nbytes <= 22:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not download any files from storage",
        )

    project_name = _sanitize_filename(project.name or str(project_id))
    filename = f"{project_name}_assets.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(zip_buffer.getbuffer().nbytes),
        },
    )
