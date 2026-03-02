"""
Image Classifier Service (DEV-IMGCLASS-001)

Claude Vision-based image classification for real estate brochure images.
Classifies images into categories, generates SEO alt-text, applies
category limits, and deduplicates across extraction sources.
"""

import base64
import io
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import anthropic
from PIL import Image

from app.config.settings import get_settings
from app.models.enums import ImageCategory
from app.services.deduplication_service import (
    DeduplicationService,
    should_keep_page_render,
    FLOOR_PLAN_SIMILARITY_THRESHOLD,
)
from app.utils.image_validation import validate_image_bytes
from app.utils.pdf_helpers import (
    ExtractedImage,
    ExtractionResult,
    create_llm_optimized,
)

logger = logging.getLogger(__name__)

# Category limits - disabled per user request to extract all images
# Previously enforced limits (10 interior, 10 exterior, etc.) were dropping good images
# Now all valid categories (non-OTHER) are retained
CATEGORY_LIMITS_DISABLED = True

CLASSIFICATION_PROMPT = """Classify this real estate image into one category:
- interior: Indoor spaces (bedrooms, living rooms, kitchens, bathrooms)
- exterior: Building facade, outdoor views, balconies
- amenity: Pool, gym, playground, common areas
- floor_plan: Architectural floor plans showing individual apartment/unit room layouts with labeled rooms (bedroom, living room, kitchen, bathroom). Must show internal room divisions and walls of a SINGLE unit.
  NOT floor_plan: Building elevation views, tower silhouettes/illustrations, site plans, building cross-sections, 3D building renders, master plan layouts, or aerial views.
- logo: Developer or project logos ONLY if the image IS the logo itself (not a page containing a logo)
- location_map: Maps showing location or nearby landmarks
- master_plan: Site plan or development layout
- other: Text-only, decorative, full document pages, or unclassifiable

IMPORTANT for logos:
- Only classify as "logo" if the image IS a logo graphic (compact, designed element)
- If this is a full page or document that happens to contain a logo, classify as "other"
- Logos are typically small, have transparent/simple backgrounds, aspect ratio close to 1:1 or 2:1

Return ONLY valid JSON (no markdown fences):
{
  "category": "interior",
  "confidence": 0.95,
  "reasoning": "Shows a modern living room with furniture",
  "alt_text": "Describe what is visible in 150 characters or less. Read any text EXACTLY as displayed -- do not paraphrase, correct, or guess unclear text. Keep it concise and SEO-friendly."
}"""

BATCH_SIZE = 5
MAX_RETRIES = 3

# Logo detection prompt for extracting logos from cover pages
LOGO_DETECTION_PROMPT = """Analyze this page image and find any developer or project logos.

If a logo is present, provide its bounding box coordinates as percentages of the image dimensions.
The bounding box should tightly enclose JUST the logo (not surrounding text or decorative elements).

Return ONLY valid JSON (no markdown fences):
{
  "has_logo": true,
  "logo_name": "Project Name",
  "bounding_box": {
    "x_percent": 10,
    "y_percent": 5,
    "width_percent": 25,
    "height_percent": 15
  },
  "confidence": 0.9,
  "alt_text": "Project Name logo"
}

If NO logo is found, return:
{
  "has_logo": false,
  "logo_name": null,
  "bounding_box": null,
  "confidence": 0.0,
  "alt_text": null
}

IMPORTANT:
- Only detect actual logos (brand marks, wordmarks, or combination marks)
- Do NOT include general page headers, titles, or decorative text
- The bounding box should be TIGHT around the logo only
- Coordinates are percentages: x_percent=10 means 10% from left edge
- Read the logo text EXACTLY as it appears -- do not correct spelling or guess unclear letters
- If any character is ambiguous, indicate uncertainty (e.g., "text reads 'Gr[o/a]ve Ridge'")
- Return only text that is clearly visible; use null for logo_name if text is unreadable"""


@dataclass
class ClassificationResult:
    """Result of classifying a single image."""
    category: ImageCategory = ImageCategory.OTHER
    confidence: float = 0.0
    reasoning: str = ""
    alt_text: str = ""
    is_duplicate: bool = False
    duplicate_of_index: Optional[int] = None
    hash_value: str = ""


@dataclass
class ClassificationOutput:
    """Full classification output for a PDF."""
    classified_images: list = field(default_factory=list)
    category_counts: dict = field(default_factory=dict)
    total_input: int = 0
    total_retained: int = 0
    total_duplicates: int = 0
    total_discarded: int = 0


class ImageClassifier:
    """
    Classifies extracted images using Claude Vision API.

    Handles:
    - Dual-source input (embedded + page renders)
    - Cross-source deduplication via perceptual hashing
    - Category classification with confidence scores
    - SEO alt-text generation
    - Category limit enforcement
    """

    def __init__(self, api_key: Optional[str] = None,
                 model: Optional[str] = None):
        settings = get_settings()
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key or settings.ANTHROPIC_API_KEY,
        )
        self._model = model or settings.ANTHROPIC_MODEL
        # Universal dedup at 95% threshold for all image categories
        # This catches near-identical images while preserving distinct variants
        self._dedup_service = DeduplicationService(
            threshold=FLOOR_PLAN_SIMILARITY_THRESHOLD  # 0.95
        )

    async def classify_extraction(
        self, extraction: ExtractionResult
    ) -> ClassificationOutput:
        """
        Classify all images from a PDF extraction result.

        Uses semaphore-bounded asyncio.gather for parallel Vision API calls,
        then applies deduplication sequentially (dedup state is not thread-safe).

        Args:
            extraction: ExtractionResult from PDFProcessor.

        Returns:
            ClassificationOutput with categorized images.
        """
        import asyncio

        MAX_CONCURRENT_VISION = 5

        output = ClassificationOutput()
        self._dedup_service.reset()
        category_counts: dict[ImageCategory, int] = {
            cat: 0 for cat in ImageCategory
        }
        retained: list[tuple[ExtractedImage, ClassificationResult]] = []

        sem = asyncio.Semaphore(MAX_CONCURRENT_VISION)

        async def _bounded_classify(img: ExtractedImage) -> ClassificationResult:
            async with sem:
                return await self._classify_single(img)

        # Phase 0: Filter corrupt images before Vision API calls
        valid_embedded = [
            img for img in extraction.embedded
            if validate_image_bytes(img.image_bytes)
        ]
        skipped = len(extraction.embedded) - len(valid_embedded)
        if skipped:
            logger.warning(
                "Filtered %d corrupt embedded images before classification",
                skipped,
            )

        # Phase 1: Classify embedded images in parallel, then dedup sequentially
        output.total_input += len(valid_embedded) + skipped
        embedded_results = await asyncio.gather(
            *[_bounded_classify(img) for img in valid_embedded]
        )

        for img, classification in zip(valid_embedded, embedded_results):
            if classification.category != ImageCategory.OTHER:
                dedup_result = self._dedup_service.check_and_register(
                    img.image_bytes, len(retained)
                )
                if dedup_result.is_duplicate:
                    output.total_duplicates += 1
                    logger.debug(
                        "Skipping duplicate %s (page %d, %.1f%% similar to idx %d)",
                        classification.category.value,
                        img.metadata.page_number,
                        dedup_result.similarity * 100,
                        dedup_result.matched_index,
                    )
                    continue
                classification.hash_value = dedup_result.hash_value

            if self._should_retain(classification.category, category_counts):
                category_counts[classification.category] += 1
                retained.append((img, classification))
            else:
                output.total_discarded += 1

        # Phase 2: Filter page renders (cross-source dedup), classify in parallel, then dedup
        renders_to_classify: list[ExtractedImage] = []
        for img in extraction.page_renders:
            output.total_input += 1
            page_embedded = [
                e.image_bytes for e in extraction.embedded
                if e.metadata.page_number == img.metadata.page_number
            ]
            if not should_keep_page_render(img.image_bytes, page_embedded):
                output.total_duplicates += 1
                continue
            renders_to_classify.append(img)

        render_results = await asyncio.gather(
            *[_bounded_classify(img) for img in renders_to_classify]
        )

        for img, classification in zip(renders_to_classify, render_results):
            if classification.category != ImageCategory.OTHER:
                dedup_result = self._dedup_service.check_and_register(
                    img.image_bytes, len(retained)
                )
                if dedup_result.is_duplicate:
                    output.total_duplicates += 1
                    logger.debug(
                        "Skipping duplicate %s render (page %d, %.1f%% similar to idx %d)",
                        classification.category.value,
                        img.metadata.page_number,
                        dedup_result.similarity * 100,
                        dedup_result.matched_index,
                    )
                    continue
                classification.hash_value = dedup_result.hash_value

            if self._should_retain(classification.category, category_counts):
                category_counts[classification.category] += 1
                retained.append((img, classification))
            else:
                output.total_discarded += 1

        # Phase 3: Logo extraction from cover pages
        if category_counts.get(ImageCategory.LOGO, 0) == 0:
            logger.info("No logos found, attempting extraction from cover pages")
            cover_pages = [
                img for img in extraction.page_renders
                if img.metadata.page_number <= 2
            ]
            for cover in cover_pages[:2]:
                result = await self.extract_logo_from_page(cover)
                if result:
                    logo_img, logo_class = result
                    category_counts[ImageCategory.LOGO] = (
                        category_counts.get(ImageCategory.LOGO, 0) + 1
                    )
                    retained.append((logo_img, logo_class))
                    output.total_retained += 1
                    logger.info(
                        "Added extracted logo from page %d",
                        cover.metadata.page_number
                    )
                    break

        output.classified_images = retained
        output.category_counts = {
            cat.value: count for cat, count in category_counts.items()
            if count > 0
        }
        output.total_retained = len(retained)

        logger.info(
            "Classification complete: %d input, %d retained, %d duplicates, %d discarded",
            output.total_input,
            output.total_retained,
            output.total_duplicates,
            output.total_discarded,
        )

        return output

    async def _classify_single(
        self, image: ExtractedImage
    ) -> ClassificationResult:
        """Classify a single image via Claude Vision."""
        # Use LLM-optimized version if available
        img_bytes = image.llm_optimized_bytes or image.image_bytes
        if img_bytes is None:
            img_bytes = image.image_bytes

        # Create optimized version if not present
        if image.llm_optimized_bytes is None:
            optimized = create_llm_optimized(img_bytes, max_dim=1024)
            if optimized:
                img_bytes = optimized

        b64_image = base64.b64encode(img_bytes).decode("utf-8")
        media_type = self._detect_media_type(img_bytes)

        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.messages.create(
                    model=self._model,
                    max_tokens=300,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": b64_image,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": CLASSIFICATION_PROMPT,
                                },
                            ],
                        }
                    ],
                )

                classification = self._parse_classification(response)
                classification = self._validate_logo_classification(
                    image.image_bytes, classification
                )
                classification = self._validate_floor_plan_classification(
                    classification
                )
                return classification

            except anthropic.APIError as e:
                logger.warning(
                    "Claude API error (attempt %d/%d): %s",
                    attempt + 1, MAX_RETRIES, e,
                )
                if attempt == MAX_RETRIES - 1:
                    logger.error("Classification failed after %d retries", MAX_RETRIES)
                    return ClassificationResult(
                        category=ImageCategory.OTHER,
                        confidence=0.0,
                        reasoning=f"API error: {e}",
                    )

        return ClassificationResult()

    def _parse_classification(
        self, response: anthropic.types.Message
    ) -> ClassificationResult:
        """Parse Claude's classification response."""
        try:
            text = response.content[0].text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            data = json.loads(text)

            category_str = data.get("category", "other").lower()
            try:
                category = ImageCategory(category_str)
            except ValueError:
                category = ImageCategory.OTHER

            return ClassificationResult(
                category=category,
                confidence=float(data.get("confidence", 0.0)),
                reasoning=data.get("reasoning", ""),
                alt_text=(data.get("alt_text", "") or "")[:150],
            )

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.warning("Failed to parse classification response: %s", e)
            return ClassificationResult(
                category=ImageCategory.OTHER,
                confidence=0.0,
                reasoning=f"Parse error: {e}",
            )

    def _validate_logo_classification(
        self, image_bytes: bytes, classification: ClassificationResult
    ) -> ClassificationResult:
        """
        Post-process logo classifications to filter false positives.

        Rejects logo classification if:
        - Image has page-like aspect ratio (close to A4/Letter: 1:1.4 or taller)
        - Image is very large (> 2000px in either dimension)
        """
        if classification.category != ImageCategory.LOGO:
            return classification

        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            aspect_ratio = w / h if h > 0 else 1.0

            # Page-like: taller than wide (portrait) or very tall landscape
            is_page_like = aspect_ratio < 0.9 or (h > 2000 and w > 1500)

            # Logos are typically small; page renders are large
            is_large = w > 2000 or h > 2000

            if is_page_like or is_large:
                logger.info(
                    "Rejecting logo classification: page-like dimensions %dx%d (ratio=%.2f)",
                    w, h, aspect_ratio
                )
                classification.category = ImageCategory.OTHER
                classification.reasoning = f"Rejected logo: page-like dimensions ({w}x{h})"

        except Exception as e:
            logger.warning("Logo validation failed: %s", e)

        return classification

    @staticmethod
    def _validate_floor_plan_classification(
        classification: ClassificationResult,
    ) -> ClassificationResult:
        """Post-process floor_plan classifications to reject tower/building illustrations.

        If the alt_text contains keywords indicating a building illustration rather
        than a unit-level floor plan, reclassify as exterior.
        """
        if classification.category != ImageCategory.FLOOR_PLAN:
            return classification

        alt_lower = (classification.alt_text or "").lower()
        reject_keywords = [
            "tower", "elevation", "building view", "cross section",
            "site plan", "master plan", "aerial", "bird's eye",
            "3d render", "silhouette", "skyline", "facade",
        ]
        for kw in reject_keywords:
            if kw in alt_lower:
                logger.info(
                    "Reclassifying floor_plan -> exterior: alt_text contains '%s'", kw
                )
                classification.category = ImageCategory.EXTERIOR
                classification.reasoning = (
                    f"Reclassified from floor_plan: alt_text contains '{kw}'"
                )
                break

        return classification

    def _should_retain(self, category: ImageCategory,
                       counts: dict[ImageCategory, int]) -> bool:
        """Check if an image should be retained.

        Category limits are disabled - all valid categories (non-OTHER) are retained.
        Previously, limits were dropping good images from brochures.
        """
        # OTHER category is always discarded (text-only, decorative, etc.)
        return category != ImageCategory.OTHER

    def _detect_media_type(self, image_bytes: bytes) -> str:
        """Detect MIME type from image bytes."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            fmt = (img.format or "jpeg").lower()
            if fmt == "jpg":
                fmt = "jpeg"
            return f"image/{fmt}"
        except Exception:
            return "image/jpeg"

    async def extract_logo_from_page(
        self, page_image: ExtractedImage
    ) -> Optional[tuple[ExtractedImage, ClassificationResult]]:
        """
        Extract a logo from a full page image using bounding box detection.

        Uses Claude Vision to detect logo location, then crops the logo
        region from the page. This handles cases where logos appear on
        cover pages but aren't embedded as separate images.

        Args:
            page_image: A page render ExtractedImage.

        Returns:
            Tuple of (cropped logo ExtractedImage, ClassificationResult) if
            a logo is found, None otherwise.
        """
        img_bytes = page_image.llm_optimized_bytes or page_image.image_bytes
        if img_bytes is None:
            return None

        # Optimize for API call
        optimized = create_llm_optimized(img_bytes, max_dim=1568)
        if optimized:
            img_bytes = optimized

        b64_image = base64.b64encode(img_bytes).decode("utf-8")
        media_type = self._detect_media_type(img_bytes)

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=400,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": b64_image,
                                },
                            },
                            {
                                "type": "text",
                                "text": LOGO_DETECTION_PROMPT,
                            },
                        ],
                    }
                ],
            )

            # Parse response
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            data = json.loads(text)

            if not data.get("has_logo", False):
                logger.debug(
                    "No logo detected on page %d",
                    page_image.metadata.page_number
                )
                return None

            bbox = data.get("bounding_box")
            if not bbox:
                return None

            # Crop the logo from original image
            original_img = Image.open(io.BytesIO(page_image.image_bytes))
            w, h = original_img.size

            # Convert percentages to pixels with padding
            padding = 0.02  # 2% padding around detected box
            x1 = max(0, int((bbox["x_percent"] / 100 - padding) * w))
            y1 = max(0, int((bbox["y_percent"] / 100 - padding) * h))
            x2 = min(w, int(((bbox["x_percent"] + bbox["width_percent"]) / 100 + padding) * w))
            y2 = min(h, int(((bbox["y_percent"] + bbox["height_percent"]) / 100 + padding) * h))

            # Validate crop dimensions
            crop_w = x2 - x1
            crop_h = y2 - y1
            if crop_w < 50 or crop_h < 30:
                logger.debug(
                    "Logo crop too small (%dx%d), skipping",
                    crop_w, crop_h
                )
                return None

            # Crop and save
            cropped = original_img.crop((x1, y1, x2, y2))
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            logo_bytes = buf.getvalue()

            # Create LLM-optimized version
            llm_bytes = create_llm_optimized(logo_bytes)

            # Build metadata
            from app.utils.pdf_helpers import ImageMetadata
            metadata = ImageMetadata(
                page_number=page_image.metadata.page_number,
                source="logo_extraction",
                width=crop_w,
                height=crop_h,
                format="png",
                dpi=page_image.metadata.dpi,
                file_size=len(logo_bytes),
            )

            extracted = ExtractedImage(
                image_bytes=logo_bytes,
                metadata=metadata,
                llm_optimized_bytes=llm_bytes,
            )

            classification = ClassificationResult(
                category=ImageCategory.LOGO,
                confidence=data.get("confidence", 0.8),
                reasoning="Extracted from cover page via bounding box detection",
                alt_text=(data.get("alt_text", data.get("logo_name", "Project logo")) or "")[:150],
            )

            logger.info(
                "Extracted logo from page %d: %dx%d at (%d,%d)",
                page_image.metadata.page_number,
                crop_w, crop_h, x1, y1
            )

            return (extracted, classification)

        except (json.JSONDecodeError, KeyError, anthropic.APIError) as e:
            logger.warning(
                "Logo extraction failed for page %d: %s",
                page_image.metadata.page_number, e
            )
            return None
