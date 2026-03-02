"""
Service for managing MaterialPackage persistence to GCS.

Handles the lifecycle of MaterialPackages:
- Creation of package records in the database
- Persistence of extraction results to GCS
- Loading packages from GCS for generation jobs
"""

import asyncio
import dataclasses
import json
import logging
import os
from io import BytesIO
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified
import zipfile

from app.models.database import MaterialPackage
from app.repositories.material_package_repository import MaterialPackageRepository
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class MaterialPackageService:
    """
    Manages MaterialPackage lifecycle: creation, GCS persistence, and loading.

    A MaterialPackage represents the extracted data from a PDF that can be
    reused across multiple generation jobs (one per template type).
    """

    def __init__(
        self,
        storage_service: StorageService,
        repo: MaterialPackageRepository
    ):
        """
        Initialize service with dependencies.

        Args:
            storage_service: Service for GCS operations
            repo: Repository for MaterialPackage DB operations
        """
        self.storage = storage_service
        self.repo = repo

    async def persist_to_gcs(
        self,
        project_id: UUID,
        pipeline_ctx: dict[str, Any],
    ) -> str:
        """
        Persist extraction results to GCS.

        Uploads:
        - structured_data.json: AI-structured project data
        - extracted_text.json: Raw text extraction by page
        - floor_plans.json: Floor plan extraction data
        - manifest.json: Package manifest with file metadata
        - images/: Optimized images extracted from PDF

        Args:
            project_id: Project UUID for folder structure
            pipeline_ctx: Pipeline context with extraction results

        Returns:
            GCS base path for the package (e.g., "materials/{project_id}")

        Raises:
            RuntimeError: If required data is missing from context
        """
        base_path = f"materials/{project_id}"

        logger.info(f"Persisting MaterialPackage to GCS: {base_path}")

        # Upload structured_data.json
        structured_data = pipeline_ctx.get("structured_data")
        if structured_data:
            structured_json = self._serialize_structured_data(structured_data)
            await self.storage.upload_file(
                source_file=structured_json,
                destination_blob_path=f"{base_path}/structured_data.json",
                content_type="application/json",
            )
            logger.debug(f"Uploaded structured_data.json to {base_path}")

        # Upload extracted_text.json
        extraction = pipeline_ctx.get("extraction")
        if extraction and hasattr(extraction, "page_text_map"):
            text_by_page = extraction.page_text_map or {}
        elif isinstance(extraction, dict):
            text_by_page = extraction.get("text_by_page") or extraction.get("page_text_map", {})
        else:
            text_by_page = {}
        extracted_text = {
            "pages": text_by_page,
            "total_pages": len(text_by_page),
        }
        await self.storage.upload_file(
            source_file=json.dumps(extracted_text).encode("utf-8"),
            destination_blob_path=f"{base_path}/extracted_text.json",
            content_type="application/json",
        )
        logger.debug(f"Uploaded extracted_text.json to {base_path}")

        # Upload floor_plans.json
        floor_plans = pipeline_ctx.get("floor_plans", {})
        floor_plans_data = self._serialize_floor_plans(floor_plans)
        await self.storage.upload_file(
            source_file=json.dumps(floor_plans_data).encode("utf-8"),
            destination_blob_path=f"{base_path}/floor_plans.json",
            content_type="application/json",
        )
        logger.debug(f"Uploaded floor_plans.json to {base_path}")

        # Upload manifest.json
        manifest = pipeline_ctx.get("manifest", {})
        manifest_data = self._serialize_manifest(manifest)
        await self.storage.upload_file(
            source_file=json.dumps(manifest_data).encode("utf-8"),
            destination_blob_path=f"{base_path}/manifest.json",
            content_type="application/json",
        )
        logger.debug(f"Uploaded manifest.json to {base_path}")

        # Upload source PDF (needed for Drive sync later)
        pdf_bytes = pipeline_ctx.get("pdf_bytes")
        pdf_path = pipeline_ctx.get("pdf_path", "")
        source_filename = (
            os.path.basename(pdf_path.replace("file://", ""))
            if pdf_path
            else "brochure.pdf"
        )
        if pdf_bytes:
            await self.storage.upload_file(
                source_file=pdf_bytes,
                destination_blob_path=f"{base_path}/source/{source_filename}",
                content_type="application/pdf",
            )
            logger.debug(f"Uploaded source PDF to {base_path}/source/{source_filename}")

        # Extract and upload images from ZIP
        zip_bytes = pipeline_ctx.get("zip_bytes")
        if zip_bytes:
            await self._upload_images_from_zip(base_path, zip_bytes)

        logger.info(f"MaterialPackage persisted to GCS: {base_path}")
        return base_path

    # Max concurrent GCS uploads to avoid socket/thread exhaustion
    _UPLOAD_CONCURRENCY = 10
    # Per-image upload timeout (seconds) -- safety net for hung connections
    _UPLOAD_TIMEOUT = 120

    async def _upload_images_from_zip(
        self,
        base_path: str,
        zip_bytes: bytes,
    ) -> int:
        """
        Extract images from ZIP and upload to GCS images/ folder.

        Uploads run concurrently (up to _UPLOAD_CONCURRENCY) with a per-image
        timeout so a single stalled upload cannot block the pipeline.

        Args:
            base_path: GCS base path for the package
            zip_bytes: ZIP file bytes containing images

        Returns:
            Number of images successfully uploaded
        """
        sem = asyncio.Semaphore(self._UPLOAD_CONCURRENCY)
        uploaded = 0
        failed = 0

        try:
            with zipfile.ZipFile(BytesIO(zip_bytes), "r") as zf:
                # Collect image entries first (ZIP reads are synchronous)
                entries: list[tuple[str, bytes]] = []
                for name in zf.namelist():
                    if name.startswith("optimized/") and name.lower().endswith(
                        (".webp", ".jpg", ".jpeg", ".png")
                    ):
                        entries.append((name.split("/")[-1], zf.read(name)))

            if not entries:
                logger.info("No images found in ZIP for %s", base_path)
                return 0

            logger.info(
                "Uploading %d images to %s/images/ (concurrency=%d)",
                len(entries), base_path, self._UPLOAD_CONCURRENCY,
            )

            async def _upload_one(filename: str, data: bytes) -> bool:
                async with sem:
                    try:
                        await asyncio.wait_for(
                            self.storage.upload_file(
                                source_file=data,
                                destination_blob_path=f"{base_path}/images/{filename}",
                                content_type=self._get_image_content_type(filename),
                            ),
                            timeout=self._UPLOAD_TIMEOUT,
                        )
                        return True
                    except asyncio.TimeoutError:
                        logger.error(
                            "Image upload timed out after %ds: %s",
                            self._UPLOAD_TIMEOUT, filename,
                        )
                        return False
                    except Exception as exc:
                        logger.error(
                            "Image upload failed: %s -- %s", filename, exc,
                        )
                        return False

            results = await asyncio.gather(
                *[_upload_one(fn, data) for fn, data in entries]
            )
            uploaded = sum(1 for ok in results if ok)
            failed = len(results) - uploaded

            logger.info(
                "Image upload complete for %s: %d succeeded, %d failed out of %d",
                base_path, uploaded, failed, len(entries),
            )

        except zipfile.BadZipFile as e:
            logger.warning(f"Failed to extract images from ZIP: {e}")

        return uploaded

    def _get_image_content_type(self, filename: str) -> str:
        """Get content type for image file."""
        ext = filename.lower().split(".")[-1]
        content_types = {
            "webp": "image/webp",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
        }
        return content_types.get(ext, "application/octet-stream")

    def _serialize_structured_data(self, data: Any) -> bytes:
        """Serialize structured data to JSON bytes."""
        if hasattr(data, "model_dump"):
            # Pydantic model
            return json.dumps(data.model_dump()).encode("utf-8")
        elif dataclasses.is_dataclass(data) and not isinstance(data, type):
            # Dataclass instance -- use asdict() for recursive conversion
            return json.dumps(dataclasses.asdict(data)).encode("utf-8")
        elif hasattr(data, "__dict__"):
            # Other object with __dict__
            return json.dumps(data.__dict__).encode("utf-8")
        else:
            # Already a dict
            return json.dumps(data).encode("utf-8")

    def _serialize_floor_plans(self, floor_plans: Any) -> dict:
        """Serialize floor plans to dict."""
        if hasattr(floor_plans, "floor_plans"):
            # FloorPlanResult object
            return {
                "floor_plans": [
                    {
                        "unit_type": fp.unit_type if hasattr(fp, "unit_type") else None,
                        "bedrooms": fp.bedrooms if hasattr(fp, "bedrooms") else None,
                        "bathrooms": fp.bathrooms if hasattr(fp, "bathrooms") else None,
                        "total_sqft": fp.total_sqft if hasattr(fp, "total_sqft") else None,
                        "suite_sqft": fp.suite_sqft if hasattr(fp, "suite_sqft") else None,
                        "balcony_sqft": fp.balcony_sqft if hasattr(fp, "balcony_sqft") else None,
                        "builtup_sqft": fp.builtup_sqft if hasattr(fp, "builtup_sqft") else None,
                        "features": fp.features if hasattr(fp, "features") else [],
                    }
                    for fp in floor_plans.floor_plans
                ],
                "total_extracted": getattr(floor_plans, "total_extracted", 0),
                "total_duplicates": getattr(floor_plans, "total_duplicates", 0),
            }
        elif isinstance(floor_plans, dict):
            return floor_plans
        else:
            return {"floor_plans": [], "total_extracted": 0}

    def _serialize_manifest(self, manifest: Any) -> dict:
        """Serialize manifest to dict."""
        if hasattr(manifest, "entries"):
            entries = []
            for e in manifest.entries:
                if isinstance(e, dict):
                    entries.append(e)
                else:
                    cat = getattr(e, "category", None)
                    entries.append({
                        "filename": getattr(e, "filename", None),
                        "category": cat.value if hasattr(cat, "value") else cat,
                        "alt_text": getattr(e, "alt_text", None),
                    })
            return {
                "entries": entries,
                "categories": getattr(manifest, "categories", {}),
            }
        elif isinstance(manifest, dict):
            return manifest
        else:
            return {"entries": [], "categories": {}}

    async def load_from_gcs(self, gcs_base_path: str) -> dict[str, Any]:
        """
        Load MaterialPackage data from GCS.

        Args:
            gcs_base_path: GCS path to the package (e.g., "materials/{project_id}")

        Returns:
            Dict containing loaded package data:
            - structured_data: AI-structured project data
            - extracted_text: Raw text extraction by page
            - floor_plans: Floor plan extraction data
            - manifest: Package manifest

        Raises:
            RuntimeError: If package data cannot be loaded
        """
        logger.info(f"Loading MaterialPackage from GCS: {gcs_base_path}")

        result = {}

        # Load structured_data.json
        try:
            structured_bytes = await self.storage.download_file(
                f"{gcs_base_path}/structured_data.json"
            )
            if structured_bytes:
                result["structured_data"] = json.loads(structured_bytes.decode("utf-8"))
                logger.info(
                    "Loaded structured_data: %d keys",
                    len(result["structured_data"]) if isinstance(result["structured_data"], dict) else 0,
                )
        except Exception as e:
            logger.warning(f"Could not load structured_data.json: {e}")
            result["structured_data"] = {}

        # Load extracted_text.json
        try:
            text_bytes = await self.storage.download_file(
                f"{gcs_base_path}/extracted_text.json"
            )
            if text_bytes:
                result["extracted_text"] = json.loads(text_bytes.decode("utf-8"))
                pages = result["extracted_text"].get("pages", {})
                page_count = len(pages) if isinstance(pages, (dict, list)) else 0
                logger.info("Loaded extracted_text: %d pages", page_count)
        except Exception as e:
            logger.warning(f"Could not load extracted_text.json: {e}")
            result["extracted_text"] = {"pages": {}}

        # Load floor_plans.json
        try:
            fp_bytes = await self.storage.download_file(
                f"{gcs_base_path}/floor_plans.json"
            )
            if fp_bytes:
                result["floor_plans"] = json.loads(fp_bytes.decode("utf-8"))
                fp_list = result["floor_plans"].get("floor_plans", [])
                logger.info("Loaded floor_plans: %d plans", len(fp_list) if isinstance(fp_list, list) else 0)
        except Exception as e:
            logger.warning(f"Could not load floor_plans.json: {e}")
            result["floor_plans"] = {"floor_plans": []}

        # Load manifest.json
        try:
            manifest_bytes = await self.storage.download_file(
                f"{gcs_base_path}/manifest.json"
            )
            if manifest_bytes:
                result["manifest"] = json.loads(manifest_bytes.decode("utf-8"))
                entries = result["manifest"].get("entries", [])
                logger.info("Loaded manifest: %d entries", len(entries) if isinstance(entries, list) else 0)
        except Exception as e:
            logger.warning(f"Could not load manifest.json: {e}")
            result["manifest"] = {"entries": []}

        logger.info(f"MaterialPackage loaded from GCS: {gcs_base_path}")
        return result

    async def create_package_record(
        self,
        project_id: Optional[UUID],
        source_job_id: Optional[UUID],
        gcs_base_path: str,
        extraction_summary: Optional[dict] = None,
        structured_data: Optional[dict] = None,
        expires_in_days: int = 30,
    ) -> MaterialPackage:
        """
        Create a MaterialPackage database record.

        Args:
            project_id: Associated project ID (can be None if project not yet created)
            source_job_id: ID of the extraction job that created this package
            gcs_base_path: GCS path where package data is stored
            extraction_summary: Summary of extraction results
            structured_data: Structured project data
            expires_in_days: Number of days before package expires

        Returns:
            Created MaterialPackage instance
        """
        logger.info(
            f"Creating MaterialPackage record: project_id={project_id}, "
            f"job_id={source_job_id}, gcs_path={gcs_base_path}"
        )

        package = await self.repo.create(
            project_id=project_id,
            source_job_id=source_job_id,
            gcs_base_path=gcs_base_path,
            extraction_summary=extraction_summary,
            structured_data=structured_data,
            expires_in_days=expires_in_days,
        )

        return package

    async def mark_ready(
        self,
        package_id: UUID,
        extraction_summary: dict,
        structured_data: dict,
    ) -> bool:
        """
        Mark package as ready with final data.

        Args:
            package_id: Package UUID
            extraction_summary: Final extraction summary
            structured_data: Final structured data

        Returns:
            True if update succeeded
        """
        return await self.repo.mark_ready(package_id, extraction_summary, structured_data)

    async def mark_error(self, package_id: UUID) -> bool:
        """
        Mark package as errored.

        Args:
            package_id: Package UUID

        Returns:
            True if update succeeded
        """
        return await self.repo.mark_error(package_id)

    async def get_by_id(self, package_id: UUID) -> Optional[MaterialPackage]:
        """
        Get MaterialPackage by ID.

        Args:
            package_id: Package UUID

        Returns:
            MaterialPackage or None if not found
        """
        return await self.repo.get_by_id(package_id)

    async def update_extraction_summary(
        self, package_id: UUID, updates: dict
    ) -> None:
        """
        Merge new keys into a MaterialPackage's extraction_summary JSONB.

        Used to add metadata (e.g., drive_sync_status) after pipeline steps.

        Args:
            package_id: Package UUID
            updates: Dict of keys to merge into extraction_summary
        """
        package = await self.repo.get_by_id(package_id)
        if package:
            summary = dict(package.extraction_summary or {})
            summary.update(updates)
            package.extraction_summary = summary
            flag_modified(package, "extraction_summary")
            await self.repo.db.flush()
            logger.info(
                "Updated extraction_summary for package %s: added keys %s",
                package_id, list(updates.keys()),
            )

    async def get_by_project(self, project_id: UUID) -> Optional[MaterialPackage]:
        """
        Get the latest ready MaterialPackage for a project.

        Args:
            project_id: Project UUID

        Returns:
            Latest ready MaterialPackage or None
        """
        return await self.repo.get_by_project(project_id)
