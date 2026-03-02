"""
PDF Helper Utilities

Low-level helpers for PDF operations: format detection, image validation,
DPI calculation, and byte-level format conversions.
"""

import io
import logging
from dataclasses import dataclass, field
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

# Minimum dimensions for embedded images
# Lowered from 500x500 to capture logos (typically 100-400px)
# Still filters tiny decorative elements and tracking pixels
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 50

# Page render DPI
RENDER_DPI = 300
DPI_SCALE = RENDER_DPI / 72  # PDF base is 72 DPI

# Supported output formats
SUPPORTED_FORMATS = {"jpeg", "jpg", "png", "webp"}


@dataclass
class ImageMetadata:
    """Metadata for an extracted image."""
    page_number: int
    source: str  # "embedded" or "page_render"
    width: int = 0
    height: int = 0
    format: str = "png"
    dpi: int = 72
    xref: Optional[int] = None
    file_size: int = 0
    color_space: str = ""
    bits_per_component: int = 8


@dataclass
class ExtractedImage:
    """Container for an extracted image with its metadata and bytes."""
    image_bytes: bytes
    metadata: ImageMetadata
    llm_optimized_bytes: Optional[bytes] = None

    def release_original(self) -> None:
        """
        Release original image bytes after LLM-optimized version is created.

        This saves ~50% memory by freeing the high-resolution original bytes
        while keeping the LLM-optimized version for AI processing.
        Should be called after classification when original bytes are no longer needed.
        """
        if self.llm_optimized_bytes:
            # Keep structure but free the large original bytes
            object.__setattr__(self, "image_bytes", b"")


@dataclass
class ExtractionResult:
    """Result of triple PDF extraction (embedded + page render + text)."""
    embedded: list = field(default_factory=list)
    page_renders: list = field(default_factory=list)
    page_text_map: dict = field(default_factory=dict)  # {page_num: text}
    page_char_counts: dict = field(default_factory=dict)  # {page_num: char_count}
    total_pages: int = 0
    errors: list = field(default_factory=list)
    extraction_method: str = "pymupdf"  # "pymupdf", "vision", or "hybrid"


def is_valid_embedded_image(width: int, height: int) -> bool:
    """Check if embedded image meets minimum dimension requirements."""
    return width >= MIN_IMAGE_WIDTH and height >= MIN_IMAGE_HEIGHT


def image_bytes_to_pil(image_bytes: bytes) -> Optional[Image.Image]:
    """Convert raw image bytes to a PIL Image. Returns None on failure."""
    try:
        return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        logger.warning("Failed to open image from bytes: %s", e)
        return None


def pil_to_bytes(image: Image.Image, fmt: str = "PNG", quality: int = 95) -> bytes:
    """Convert a PIL Image to bytes in the specified format."""
    buf = io.BytesIO()
    save_kwargs = {"format": fmt}
    if fmt.upper() in ("JPEG", "JPG", "WEBP"):
        save_kwargs["quality"] = quality
    # Convert non-RGB modes to RGB for JPEG/WebP compatibility
    if fmt.upper() in ("JPEG", "JPG", "WEBP"):
        if image.mode == "CMYK":
            # CMYK from print PDFs - common in brochures
            image = image.convert("RGB")
        elif image.mode in ("RGBA", "LA", "PA", "P", "L", "1"):
            # Transparency, palette, grayscale, bitmap modes
            image = image.convert("RGB")
    image.save(buf, **save_kwargs)
    return buf.getvalue()


def create_llm_optimized(image_bytes: bytes, max_dim: int = 1024,
                         fmt: str = "JPEG", quality: int = 80) -> Optional[bytes]:
    """
    Create an LLM-optimized version of an image.

    Resizes to max_dim on the longest side and compresses for
    reduced token consumption during Claude Vision calls.
    """
    img = image_bytes_to_pil(image_bytes)
    if img is None:
        return None

    try:
        w, h = img.size
        if max(w, h) > max_dim:
            ratio = max_dim / max(w, h)
            new_w = int(w * ratio)
            new_h = int(h * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)

        return pil_to_bytes(img, fmt=fmt, quality=quality)
    finally:
        img.close()


def get_image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    """Return (width, height) of an image from its bytes."""
    img = image_bytes_to_pil(image_bytes)
    if img is None:
        return (0, 0)
    try:
        return img.size
    finally:
        img.close()


def detect_format(image_bytes: bytes) -> str:
    """Detect image format from bytes. Returns lowercase format string."""
    img = image_bytes_to_pil(image_bytes)
    if img is None:
        return "unknown"
    try:
        fmt = img.format
        if fmt is None:
            return "unknown"
        return fmt.lower()
    finally:
        img.close()


def validate_pdf_bytes(pdf_bytes: bytes) -> bool:
    """Quick validation that bytes start with PDF magic number."""
    return pdf_bytes[:5] == b"%PDF-"
