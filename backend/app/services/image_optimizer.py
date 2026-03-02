"""
Image Optimizer Service (DEV-IMGOPT-001)

Resize, format convert, and compress images for delivery.
Produces dual-tier output:
  Tier 1 (Original): Full quality, no size limit, for archival/delivery
  Tier 2 (LLM-Optimized): 1568px max, for Claude processing and web
"""

import io
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from PIL import Image

from app.utils.pdf_helpers import pil_to_bytes

logger = logging.getLogger(__name__)


def slugify_alt_text(text: str, max_length: int = 60) -> str:
    """
    Convert alt_text to URL-safe slug for filename.

    - Lowercase
    - Replace spaces and special chars with hyphens
    - Remove consecutive hyphens
    - Truncate at word boundary
    """
    if not text:
        return ""

    # Normalize unicode and lowercase
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()

    # Replace non-alphanumeric with hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Remove leading/trailing hyphens
    text = text.strip("-")

    # Truncate at word boundary
    if len(text) > max_length:
        truncated = text[:max_length]
        # Find last hyphen to avoid cutting mid-word
        last_hyphen = truncated.rfind("-")
        if last_hyphen > max_length // 2:
            text = truncated[:last_hyphen]
        else:
            text = truncated

    return text

# Output constraints
MAX_WIDTH = 2450
MAX_HEIGHT = 1400
OUTPUT_DPI = 300
LLM_MAX_DIM = 1568

# Quality settings
WEBP_QUALITY = 85
JPG_QUALITY = 90


@dataclass
class OptimizedImage:
    """A single optimized image in multiple formats and tiers."""
    # Tier 1: Original quality
    original_webp: bytes = b""
    original_jpg: bytes = b""
    # Tier 2: LLM-optimized
    llm_webp: bytes = b""
    llm_jpg: bytes = b""
    # Metadata
    original_width: int = 0
    original_height: int = 0
    optimized_width: int = 0
    optimized_height: int = 0
    llm_width: int = 0
    llm_height: int = 0
    category: str = ""
    alt_text: str = ""
    file_name: str = ""
    quality_score: float = 1.0


@dataclass
class OptimizationResult:
    """Batch optimization result."""
    images: list = field(default_factory=list)
    total_input: int = 0
    total_optimized: int = 0
    total_errors: int = 0
    total_original_bytes: int = 0
    total_optimized_bytes: int = 0


class ImageOptimizer:
    """
    Optimizes images for delivery and LLM processing.

    Applies resize (max 2450x1400), format conversion (WebP + JPG),
    and DPI normalization (300 DPI). Generates dual-tier output.
    """

    def __init__(
        self,
        max_width: int = MAX_WIDTH,
        max_height: int = MAX_HEIGHT,
        output_dpi: int = OUTPUT_DPI,
        llm_max_dim: int = LLM_MAX_DIM,
        webp_quality: int = WEBP_QUALITY,
        jpg_quality: int = JPG_QUALITY,
    ):
        self.max_width = max_width
        self.max_height = max_height
        self.output_dpi = output_dpi
        self.llm_max_dim = llm_max_dim
        self.webp_quality = webp_quality
        self.jpg_quality = jpg_quality

    async def optimize_batch(
        self,
        images: list[tuple[bytes, str, str]],
    ) -> OptimizationResult:
        """
        Optimize a batch of images.

        Args:
            images: List of (image_bytes, category, alt_text) tuples.

        Returns:
            OptimizationResult with all optimized images.
        """
        result = OptimizationResult()
        category_counters: dict[str, int] = {}

        for img_bytes, category, alt_text in images:
            result.total_input += 1
            result.total_original_bytes += len(img_bytes)

            try:
                # Generate semantic filename
                count = category_counters.get(category, 0) + 1
                category_counters[category] = count
                slug = slugify_alt_text(alt_text)
                if slug:
                    file_name = f"{count:03d}-{category}-{slug}"
                else:
                    file_name = f"{count:03d}-{category}"

                # Ensure total filename (without extension) <= 80 chars
                if len(file_name) > 80:
                    file_name = file_name[:80].rstrip("-")

                optimized = self._optimize_single(
                    img_bytes, category, alt_text, file_name
                )

                result.images.append(optimized)
                result.total_optimized += 1

                # Track output size (Tier 1 WebP as primary)
                result.total_optimized_bytes += len(optimized.original_webp)

            except Exception as e:
                logger.error("Failed to optimize image: %s", e)
                result.total_errors += 1

        logger.info(
            "Optimization complete: %d/%d optimized, %d errors",
            result.total_optimized,
            result.total_input,
            result.total_errors,
        )

        return result

    def _optimize_single(
        self,
        image_bytes: bytes,
        category: str,
        alt_text: str,
        file_name: str,
    ) -> OptimizedImage:
        """Optimize a single image into dual-tier, dual-format output."""
        img = Image.open(io.BytesIO(image_bytes))
        original_w, original_h = img.size

        # Ensure RGB mode for JPEG/WebP compatibility
        # Handle all non-RGB modes including CMYK from print brochures
        if img.mode == "CMYK":
            # CMYK to RGB conversion - common in print PDFs
            logger.debug(
                "Converting CMYK image to RGB: %dx%d", original_w, original_h
            )
            img = img.convert("RGB")
        elif img.mode in ("RGBA", "P", "PA", "LA", "L", "1"):
            # Handle transparency, palette, grayscale, and bitmap modes
            img = img.convert("RGB")

        # Tier 1: Resize to max dimensions, maintaining aspect ratio
        tier1_img = self._resize_to_bounds(
            img, self.max_width, self.max_height
        )
        # Set DPI metadata
        tier1_img.info["dpi"] = (self.output_dpi, self.output_dpi)

        tier1_w, tier1_h = tier1_img.size

        # Tier 2: LLM-optimized version
        tier2_img = self._resize_to_bounds(
            img, self.llm_max_dim, self.llm_max_dim
        )
        tier2_w, tier2_h = tier2_img.size

        # Generate both formats for both tiers
        original_webp = pil_to_bytes(tier1_img, "WEBP", self.webp_quality)
        original_jpg = pil_to_bytes(tier1_img, "JPEG", self.jpg_quality)
        llm_webp = pil_to_bytes(tier2_img, "WEBP", self.webp_quality)
        llm_jpg = pil_to_bytes(tier2_img, "JPEG", self.jpg_quality)

        return OptimizedImage(
            original_webp=original_webp,
            original_jpg=original_jpg,
            llm_webp=llm_webp,
            llm_jpg=llm_jpg,
            original_width=original_w,
            original_height=original_h,
            optimized_width=tier1_w,
            optimized_height=tier1_h,
            llm_width=tier2_w,
            llm_height=tier2_h,
            category=category,
            alt_text=alt_text,
            file_name=file_name,
        )

    def _resize_to_bounds(
        self, img: Image.Image, max_w: int, max_h: int
    ) -> Image.Image:
        """
        Resize image to fit within max bounds while maintaining aspect ratio.

        Only downscales; never upscales.
        """
        w, h = img.size
        if w <= max_w and h <= max_h:
            return img.copy()

        ratio = min(max_w / w, max_h / h)
        new_w = int(w * ratio)
        new_h = int(h * ratio)

        return img.resize((new_w, new_h), Image.LANCZOS)
