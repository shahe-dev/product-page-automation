"""
Output Organizer Service (DEV-IMGOPT-001 - Packaging)

Organizes optimized images into a structured ZIP archive with
manifest.json for cloud upload.
"""

import io
import json
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.services.image_optimizer import OptimizedImage, OptimizationResult

logger = logging.getLogger(__name__)

# Directory mapping for categories
CATEGORY_DIRS = {
    "interior": "interiors",
    "exterior": "exteriors",
    "amenity": "amenities",
    "logo": "logos",
    "floor_plan": "floor_plans",
    "location_map": "location_maps",
    "master_plan": "master_plans",
}


@dataclass
class ManifestEntry:
    """Single entry in the output manifest."""
    file_name: str
    category: str
    directory: str
    format: str
    tier: str
    width: int
    height: int
    file_size: int
    alt_text: str = ""
    quality_score: float = 1.0


@dataclass
class OutputManifest:
    """Complete manifest for the output package."""
    project_name: str = ""
    created_at: str = ""
    total_images: int = 0
    categories: dict = field(default_factory=dict)
    entries: list = field(default_factory=list)
    tier1_count: int = 0
    tier2_count: int = 0

    def to_dict(self) -> dict:
        """Serialize manifest to dictionary."""
        return {
            "project_name": self.project_name,
            "created_at": self.created_at,
            "total_images": self.total_images,
            "categories": self.categories,
            "tier1_count": self.tier1_count,
            "tier2_count": self.tier2_count,
            "entries": [
                {
                    "file_name": e.file_name,
                    "category": e.category,
                    "directory": e.directory,
                    "format": e.format,
                    "tier": e.tier,
                    "width": e.width,
                    "height": e.height,
                    "file_size": e.file_size,
                    "alt_text": e.alt_text,
                    "quality_score": e.quality_score,
                }
                for e in self.entries
            ],
        }


class OutputOrganizer:
    """
    Packages optimized images into structured ZIP archives.

    Creates organized directory structure:
      /interiors/    (WebP + JPG)
      /exteriors/    (WebP + JPG)
      /amenities/    (WebP + JPG)
      /logos/        (WebP + JPG)
      /floor_plans/  (WebP + JPG)
      /llm/          (LLM-optimized versions)
      manifest.json
    """

    def create_package(
        self,
        optimization_result: OptimizationResult,
        project_name: str = "",
        floor_plan_data: Optional[list] = None,
        page_text_map: Optional[dict[int, str]] = None,
    ) -> tuple[bytes, OutputManifest]:
        """
        Create a ZIP package from optimization results.

        Args:
            optimization_result: Result from ImageOptimizer.
            project_name: Project name for manifest.
            floor_plan_data: Optional structured floor plan data.

        Returns:
            Tuple of (zip_bytes, manifest).
        """
        manifest = OutputManifest(
            project_name=project_name,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        zip_buffer = io.BytesIO()
        category_counts: dict[str, int] = {}

        with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED
        ) as zf:
            for img in optimization_result.images:
                cat_dir = CATEGORY_DIRS.get(img.category, "other")
                count = category_counts.get(img.category, 0)
                category_counts[img.category] = count + 1

                # Tier 1 (Original): /original/{category}/
                t1_webp_path = f"original/{cat_dir}/{img.file_name}.webp"
                zf.writestr(t1_webp_path, img.original_webp)
                manifest.entries.append(ManifestEntry(
                    file_name=f"{img.file_name}.webp",
                    category=img.category,
                    directory=f"original/{cat_dir}",
                    format="webp",
                    tier="original",
                    width=img.optimized_width,
                    height=img.optimized_height,
                    file_size=len(img.original_webp),
                    alt_text=img.alt_text,
                    quality_score=img.quality_score,
                ))
                manifest.tier1_count += 1

                t1_jpg_path = f"original/{cat_dir}/{img.file_name}.jpg"
                zf.writestr(t1_jpg_path, img.original_jpg)
                manifest.entries.append(ManifestEntry(
                    file_name=f"{img.file_name}.jpg",
                    category=img.category,
                    directory=f"original/{cat_dir}",
                    format="jpg",
                    tier="original",
                    width=img.optimized_width,
                    height=img.optimized_height,
                    file_size=len(img.original_jpg),
                    alt_text=img.alt_text,
                    quality_score=img.quality_score,
                ))
                manifest.tier1_count += 1

                # Tier 2 (LLM-Optimized): /optimized/{category}/
                t2_webp_path = f"optimized/{cat_dir}/{img.file_name}.webp"
                zf.writestr(t2_webp_path, img.llm_webp)
                manifest.entries.append(ManifestEntry(
                    file_name=f"{img.file_name}.webp",
                    category=img.category,
                    directory=f"optimized/{cat_dir}",
                    format="webp",
                    tier="llm_optimized",
                    width=img.llm_width,
                    height=img.llm_height,
                    file_size=len(img.llm_webp),
                    alt_text=img.alt_text,
                ))
                manifest.tier2_count += 1

                t2_jpg_path = f"optimized/{cat_dir}/{img.file_name}.jpg"
                zf.writestr(t2_jpg_path, img.llm_jpg)
                manifest.entries.append(ManifestEntry(
                    file_name=f"{img.file_name}.jpg",
                    category=img.category,
                    directory=f"optimized/{cat_dir}",
                    format="jpg",
                    tier="llm_optimized",
                    width=img.llm_width,
                    height=img.llm_height,
                    file_size=len(img.llm_jpg),
                    alt_text=img.alt_text,
                ))
                manifest.tier2_count += 1

            # Add floor plan structured data if available
            if floor_plan_data:
                # Consolidated JSON
                fp_json = json.dumps(floor_plan_data, indent=2, default=str)
                zf.writestr("floor_plans/floor_plan_data.json", fp_json)

                # Per-floor-plan sidecar JSON files
                for fp_entry in floor_plan_data:
                    if "image_filename" in fp_entry:
                        # Extract base name without extension
                        img_name = fp_entry["image_filename"]
                        base_name = img_name.rsplit(".", 1)[0] if "." in img_name else img_name
                        sidecar_path = f"floor_plans/{base_name}.json"
                        sidecar_json = json.dumps(fp_entry, indent=2, default=str)
                        zf.writestr(sidecar_path, sidecar_json)

            # Add extracted text from PDF if available
            if page_text_map:
                text_json = json.dumps(
                    {
                        "pages": [
                            {"page": k, "text": v}
                            for k, v in sorted(page_text_map.items())
                        ]
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                zf.writestr("extracted_text.json", text_json)

            # Summary
            manifest.total_images = len(optimization_result.images)
            manifest.categories = {
                cat: cnt for cat, cnt in category_counts.items()
            }

            # Write manifest
            manifest_json = json.dumps(
                manifest.to_dict(), indent=2, default=str
            )
            zf.writestr("manifest.json", manifest_json)

        zip_bytes = zip_buffer.getvalue()
        logger.info(
            "Output package created: %d images, %d files, %.2f MB",
            manifest.total_images,
            len(manifest.entries),
            len(zip_bytes) / (1024 * 1024),
        )

        return zip_bytes, manifest
