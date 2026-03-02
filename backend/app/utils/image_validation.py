"""Image validation utility for filtering corrupt/invalid images before API calls."""

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def validate_image_bytes(
    image_bytes: bytes,
    min_width: int = 50,
    min_height: int = 50,
) -> bool:
    """Validate that image bytes represent a valid raster image.

    Args:
        image_bytes: Raw image data.
        min_width: Minimum acceptable width in pixels.
        min_height: Minimum acceptable height in pixels.

    Returns:
        True if the image is valid and meets size requirements.
    """
    if not image_bytes or len(image_bytes) < 8:
        return False

    # Reject SVG/XML content
    header = image_bytes[:100]
    if b"<?xml" in header or b"<svg" in header:
        return False

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()  # Checks integrity without decoding full image
        # Re-open after verify (verify closes the file)
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        if w < min_width or h < min_height:
            return False
        return True
    except Exception:
        return False
