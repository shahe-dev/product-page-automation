"""
Deduplication Service

Perceptual hash-based image deduplication using pHash algorithm.
Supports configurable similarity thresholds for different use cases:
- General images: 90% threshold
- Floor plans: 95% threshold (tighter matching)
"""

import io
import logging
from dataclasses import dataclass
from typing import Optional

import imagehash
from PIL import Image

logger = logging.getLogger(__name__)

# pHash produces 64-bit hash; max Hamming distance = 64
HASH_SIZE = 64

DEFAULT_SIMILARITY_THRESHOLD = 0.90
FLOOR_PLAN_SIMILARITY_THRESHOLD = 0.95


@dataclass
class DeduplicationResult:
    """Result of deduplication comparison."""
    is_duplicate: bool
    similarity: float
    matched_index: Optional[int] = None
    hash_value: str = ""


def compute_phash(image_bytes: bytes) -> Optional[imagehash.ImageHash]:
    """Compute perceptual hash for an image."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return imagehash.phash(img)
    except Exception as e:
        logger.warning("Failed to compute phash: %s", e)
        return None


def compute_similarity(hash_a: imagehash.ImageHash,
                       hash_b: imagehash.ImageHash) -> float:
    """
    Compute similarity between two perceptual hashes.

    Returns a float between 0.0 (completely different) and 1.0 (identical).
    """
    distance = hash_a - hash_b  # Hamming distance
    return 1.0 - (distance / HASH_SIZE)


class DeduplicationService:
    """
    Manages deduplication of images using perceptual hashing.

    Maintains a registry of seen hashes and checks new images
    against the registry to detect duplicates.
    """

    def __init__(self, threshold: float = DEFAULT_SIMILARITY_THRESHOLD):
        self.threshold = threshold
        self._hash_registry: list[tuple[imagehash.ImageHash, int]] = []

    def reset(self) -> None:
        """Clear the hash registry."""
        self._hash_registry.clear()

    def check_duplicate(self, image_bytes: bytes) -> DeduplicationResult:
        """
        Check if an image is a duplicate of any previously seen image.

        Args:
            image_bytes: Raw image bytes to check.

        Returns:
            DeduplicationResult indicating whether it is a duplicate.
        """
        img_hash = compute_phash(image_bytes)
        if img_hash is None:
            return DeduplicationResult(
                is_duplicate=False, similarity=0.0, hash_value=""
            )

        for idx, (existing_hash, original_idx) in enumerate(self._hash_registry):
            sim = compute_similarity(img_hash, existing_hash)
            if sim >= self.threshold:
                return DeduplicationResult(
                    is_duplicate=True,
                    similarity=sim,
                    matched_index=original_idx,
                    hash_value=str(img_hash),
                )

        return DeduplicationResult(
            is_duplicate=False,
            similarity=0.0,
            hash_value=str(img_hash),
        )

    def register(self, image_bytes: bytes, index: int) -> Optional[str]:
        """
        Register an image in the hash registry.

        Args:
            image_bytes: Raw image bytes.
            index: Logical index to associate with this image.

        Returns:
            Hash string if successful, None on failure.
        """
        img_hash = compute_phash(image_bytes)
        if img_hash is None:
            return None
        self._hash_registry.append((img_hash, index))
        return str(img_hash)

    def check_and_register(self, image_bytes: bytes,
                           index: int) -> DeduplicationResult:
        """
        Check for duplicate and register if unique.

        Args:
            image_bytes: Raw image bytes.
            index: Logical index for this image.

        Returns:
            DeduplicationResult.
        """
        result = self.check_duplicate(image_bytes)
        if not result.is_duplicate:
            hash_str = self.register(image_bytes, index)
            if hash_str:
                result.hash_value = hash_str
        return result


def should_keep_page_render(
    render_bytes: bytes,
    embedded_list: list[bytes],
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    coverage_threshold: float = 0.70,
) -> bool:
    """
    Determine if a page render should be kept based on similarity to embedded images.

    Skip page render if:
    1. Any embedded image covers >coverage_threshold of the page render's area
    2. It's perceptually similar to any embedded image (hash match)

    Args:
        render_bytes: Page render image bytes.
        embedded_list: List of embedded image bytes from the same page.
        threshold: Hash similarity threshold (default 0.90).
        coverage_threshold: Minimum area coverage ratio to skip render (default 0.70).

    Returns:
        True if the render should be kept (unique content), False if duplicate.
    """
    if not embedded_list:
        return True

    try:
        render_img = Image.open(io.BytesIO(render_bytes))
        render_w, render_h = render_img.size
        render_area = render_w * render_h
    except Exception as e:
        logger.warning("Failed to open page render: %s", e)
        return True

    render_hash = compute_phash(render_bytes)

    for emb_bytes in embedded_list:
        try:
            emb_img = Image.open(io.BytesIO(emb_bytes))
            emb_w, emb_h = emb_img.size
            emb_area = emb_w * emb_h

            # Check 1: Size-based coverage (only when render is larger)
            # In real PDFs, page renders are always larger than embedded images
            if render_area > emb_area:
                coverage = emb_area / render_area
                if coverage >= coverage_threshold:
                    logger.debug(
                        "Skipping page render: embedded covers %.1f%% of page",
                        coverage * 100
                    )
                    return False

        except Exception as e:
            logger.warning("Failed to check embedded image coverage: %s", e)

        # Check 2: Perceptual hash similarity
        if render_hash is not None:
            emb_hash = compute_phash(emb_bytes)
            if emb_hash is not None:
                similarity = compute_similarity(render_hash, emb_hash)
                if similarity >= threshold:
                    logger.debug(
                        "Skipping page render: %.1f%% similar to embedded",
                        similarity * 100
                    )
                    return False

    return True
