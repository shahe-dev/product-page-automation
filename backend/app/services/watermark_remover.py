"""
Watermark Remover Service (DEV-WATERMARK-001 - Removal)

Uses OpenCV inpainting to remove detected watermark regions.
Validates output quality and falls back to original if
degradation exceeds threshold.
"""

import io
import logging
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from app.services.watermark_detector import DetectionResult, WatermarkRegion
from app.utils.pdf_helpers import pil_to_bytes

logger = logging.getLogger(__name__)

# Quality degradation threshold: reject if quality drops more than 15%
MAX_QUALITY_DEGRADATION = 0.15
INPAINT_RADIUS = 3


@dataclass
class RemovalResult:
    """Result of watermark removal for a single image."""
    cleaned_bytes: bytes = b""
    original_bytes: bytes = b""
    was_modified: bool = False
    quality_score_before: float = 1.0
    quality_score_after: float = 1.0
    quality_degradation: float = 0.0
    fell_back_to_original: bool = False
    regions_processed: int = 0
    error: Optional[str] = None


class WatermarkRemover:
    """
    Removes watermarks from images using OpenCV inpainting.

    Creates a binary mask from detected bounding boxes and applies
    Telea or Navier-Stokes inpainting. Validates output quality
    and reverts to original if quality drops more than 15%.
    """

    def __init__(self, inpaint_radius: int = INPAINT_RADIUS,
                 max_degradation: float = MAX_QUALITY_DEGRADATION,
                 algorithm: int = cv2.INPAINT_TELEA):
        self.inpaint_radius = inpaint_radius
        self.max_degradation = max_degradation
        self.algorithm = algorithm

    async def remove(self, image_bytes: bytes,
                     detection: DetectionResult) -> RemovalResult:
        """
        Remove watermarks from an image based on detection results.

        Args:
            image_bytes: Original image bytes.
            detection: DetectionResult from WatermarkDetector.

        Returns:
            RemovalResult with cleaned image bytes.
        """
        if not detection.has_watermark or not detection.regions:
            return RemovalResult(
                cleaned_bytes=image_bytes,
                original_bytes=image_bytes,
                was_modified=False,
            )

        try:
            # Convert to OpenCV format
            img_array = self._bytes_to_cv2(image_bytes)
            if img_array is None:
                return RemovalResult(
                    cleaned_bytes=image_bytes,
                    original_bytes=image_bytes,
                    error="Failed to decode image",
                )

            # Calculate quality score before removal
            quality_before = self._compute_quality_score(img_array)

            # Create mask from all watermark regions
            mask = self._create_mask(img_array, detection.regions)

            # Apply inpainting
            cleaned = cv2.inpaint(
                img_array, mask, self.inpaint_radius, self.algorithm
            )

            # Calculate quality score after removal
            quality_after = self._compute_quality_score(cleaned)

            # Check quality degradation
            degradation = 0.0
            if quality_before > 0:
                degradation = (quality_before - quality_after) / quality_before

            if degradation > self.max_degradation:
                logger.warning(
                    "Quality degradation %.2f%% exceeds threshold %.2f%%, "
                    "falling back to original",
                    degradation * 100,
                    self.max_degradation * 100,
                )
                return RemovalResult(
                    cleaned_bytes=image_bytes,
                    original_bytes=image_bytes,
                    was_modified=False,
                    quality_score_before=quality_before,
                    quality_score_after=quality_after,
                    quality_degradation=degradation,
                    fell_back_to_original=True,
                    regions_processed=len(detection.regions),
                )

            # Convert back to bytes
            cleaned_bytes = self._cv2_to_bytes(cleaned)

            return RemovalResult(
                cleaned_bytes=cleaned_bytes,
                original_bytes=image_bytes,
                was_modified=True,
                quality_score_before=quality_before,
                quality_score_after=quality_after,
                quality_degradation=degradation,
                regions_processed=len(detection.regions),
            )

        except (cv2.error, ValueError, RuntimeError, OSError) as e:
            logger.error("Watermark removal failed: %s", e)
            return RemovalResult(
                cleaned_bytes=image_bytes,
                original_bytes=image_bytes,
                error=str(e),
            )

    async def remove_batch(
        self, images: list[tuple[bytes, DetectionResult]]
    ) -> list[RemovalResult]:
        """Remove watermarks from a batch of images."""
        results = []
        for img_bytes, detection in images:
            result = await self.remove(img_bytes, detection)
            results.append(result)
        return results

    def _create_mask(self, image: np.ndarray,
                     regions: list[WatermarkRegion]) -> np.ndarray:
        """Create a binary mask from watermark bounding boxes."""
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)

        for region in regions:
            x = max(0, region.x)
            y = max(0, region.y)
            x2 = min(w, x + region.width)
            y2 = min(h, y + region.height)
            mask[y:y2, x:x2] = 255

        return mask

    def _compute_quality_score(self, image: np.ndarray) -> float:
        """
        Compute a quality score for an image using Laplacian variance.

        Higher values indicate sharper, higher-quality images.
        Returns normalized score between 0.0 and 1.0.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Normalize: typical real estate images have variance 50-5000
        normalized = min(laplacian_var / 5000.0, 1.0)
        return normalized

    def _bytes_to_cv2(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Convert image bytes to OpenCV numpy array."""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except (cv2.error, ValueError, RuntimeError) as e:
            logger.warning("Failed to decode image to cv2: %s", e)
            return None

    def _cv2_to_bytes(self, image: np.ndarray, fmt: str = "png") -> bytes:
        """Convert OpenCV numpy array to image bytes."""
        ext_map = {"png": ".png", "jpg": ".jpg", "jpeg": ".jpg", "webp": ".webp"}
        ext = ext_map.get(fmt, ".png")
        success, buffer = cv2.imencode(ext, image)
        if not success:
            raise RuntimeError(f"Failed to encode image to {fmt}")
        return buffer.tobytes()
