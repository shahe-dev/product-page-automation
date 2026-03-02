"""
Floor Plan Extractor Service (DEV-FLOORPLAN-001)

Extracts structured data from floor plan images using Claude Vision OCR.
Supports triple extraction input (embedded + page renders + text), text cross-referencing
as fallback, and perceptual hash deduplication at 95% threshold.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import anthropic

from app.config.settings import get_settings
from app.integrations.anthropic_client import anthropic_service
from app.services.deduplication_service import (
    DeduplicationService,
    FLOOR_PLAN_SIMILARITY_THRESHOLD,
)
from app.utils.image_validation import validate_image_bytes
from app.utils.pdf_helpers import ExtractedImage, create_llm_optimized

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

FLOOR_PLAN_OCR_PROMPT = """Extract ALL floor plan data visible on this page/image.

This may be a full brochure page containing one or more floor plan diagrams,
or a cropped floor plan image. Extract data for EACH distinct unit type visible.

Return ONLY valid JSON (no markdown fences):
{
  "floor_plans": [
    {
      "unit_type": "2BR Type A",
      "bedrooms": 2,
      "bathrooms": 2.5,
      "suite_sqft": 1100.0,
      "balcony_sqft": 150.0,
      "total_sqft": 1250.0,
      "builtup_sqft": null,
      "room_dimensions": {
        "living_dining": "4.2m x 3.8m",
        "bedroom_1": "3.5m x 3.2m",
        "bedroom_2": "3.0m x 2.8m",
        "kitchen": "2.5m x 2.0m",
        "bathroom_1": "2.0m x 1.8m",
        "balcony": "3.0m x 1.5m"
      },
      "features": ["maid_room", "walk_in_closet"],
      "confidence": 0.92
    }
  ]
}

AREA FIELD DEFINITIONS (read carefully):
- suite_sqft: Internal/suite area ONLY (excludes balcony). Labels: "Suite", "Internal", "Suite Area".
- balcony_sqft: Balcony/terrace area only.
- total_sqft: The LARGEST area number = suite + balcony. Labels: "Total", "Total Built-up", "Total Area", "Gross Area".
- builtup_sqft: Only use if explicitly labeled "Built-up" and is DIFFERENT from total.

CRITICAL RULES:
1. Read numbers EXACTLY as printed. Do NOT round, estimate, or modify digits.
2. If area is labeled "sqm" or "m2", convert to sqft by multiplying by 10.764.
3. If area is labeled "sqft" or "sq.ft." or "sq ft", use the value as-is.
4. Only extract data VISIBLE in the image. Do not guess or infer.
5. For unit_type, include the full label (e.g., "2BR Type A", not just "2BR").
6. Double-check all digits: common OCR errors include 1<->7, 5<->6, 0<->8.
7. For room_dimensions, use the room label as shown, converted to snake_case.
8. Record dimensions EXACTLY as displayed (e.g., "4.2m x 3.8m").
9. If multiple unit types appear on one page, return ALL in the array.
10. Return null for any field NOT visible. Do not invent values.
11. A single area labeled "Suite" or "Internal" goes in suite_sqft, NOT total_sqft.
12. Bedroom count must come from the unit_type LABEL (e.g. "1BR" = 1, "Studio" = 0), NOT from counting rooms visually.
13. If areas are shown as ranges (e.g., "541.64 - 541.75 SQ.FT"), extract the LARGER value.
14. When a page shows Suite Range, Balcony Range, and Total Range separately, extract all three: suite_sqft = Suite/Internal area, balcony_sqft = Balcony area, total_sqft = Total/Built-up area (always the LARGEST number).
15. For bathrooms: count rooms labeled "Bath", "Bathroom", "WC", "Toilet", "Ensuite", "En-suite", "Shower" in room_dimensions. Each full bathroom = 1.0, powder room/half bath/WC = 0.5. Always return a numeric count, not null, unless truly no bathrooms are visible."""

FLOOR_PLAN_CROP_PROMPT = """Locate the floor plan diagram on this page. The floor plan is the architectural
drawing showing room layouts with walls, doors, and labeled rooms.

Ignore: page headers, footers, marketing text, project logos, decorative borders,
legends that are separate from the plan, and surrounding whitespace.

Return ONLY valid JSON (no markdown fences):
{
  "has_floor_plan": true,
  "bounding_box": {
    "x_percent": 5,
    "y_percent": 10,
    "width_percent": 80,
    "height_percent": 75
  },
  "confidence": 0.9
}

All values are percentages of image width/height.
x_percent and y_percent are the top-left corner of the bounding box.
width_percent and height_percent are the size of the bounding box.

If the image IS the floor plan with no surrounding page elements, return:
{"has_floor_plan": true, "bounding_box": {"x_percent": 0, "y_percent": 0, "width_percent": 100, "height_percent": 100}, "confidence": 1.0}

If no floor plan is found, return:
{"has_floor_plan": false, "bounding_box": null, "confidence": 0.0}"""

FLOOR_PLAN_MULTI_CROP_PROMPT = """This page contains MULTIPLE floor plan diagrams ({count} plans). Locate EACH
individual floor plan diagram separately. Each floor plan is a self-contained
architectural drawing showing room layouts with walls, doors, and labeled rooms.

The floor plans on this page are:
{unit_types}

Return a SEPARATE bounding box for EACH floor plan. Do NOT return one large box
covering all plans -- each box must tightly contain exactly ONE floor plan diagram.

Return ONLY valid JSON (no markdown fences):
{{
  "floor_plans": [
    {{
      "label": "unit type label as shown on page",
      "bounding_box": {{
        "x_percent": 5,
        "y_percent": 10,
        "width_percent": 45,
        "height_percent": 75
      }}
    }}
  ]
}}

All values are percentages of image width/height.
x_percent and y_percent are the top-left corner.
width_percent and height_percent are the size.

IMPORTANT: Each bounding box must contain exactly ONE floor plan. If two plans are
side-by-side, each box should cover roughly half the page width."""

# Minimum crop dimension in pixels -- below this, keep the original image
MIN_CROP_DIMENSION = 200

# Conversion factor
SQM_TO_SQFT = 10.764

# Physical plausibility bounds for residential floor plans.
# These are generous maximums that accommodate ultra-luxury properties worldwide.
# They exist to catch parsing errors (prices as bath counts, mm as meters),
# NOT to enforce market-specific constraints.
PLAUSIBILITY_BOUNDS: dict[str, tuple[float, float]] = {
    "bedrooms": (0, 10),
    "bathrooms": (0, 15),
    "total_sqft": (50, 25000),
    "suite_sqft": (50, 25000),
    "balcony_sqft": (5, 10000),
    "builtup_sqft": (50, 30000),
}


def _is_plausible(field: str, value: float | int | None) -> bool:
    """Check if extracted value falls within physical plausibility bounds.

    Returns True if value is plausible, False if it's almost certainly
    a parsing error (price read as bathroom count, mm read as meters, etc).
    """
    if value is None:
        return True  # None is not implausible, it's missing
    bounds = PLAUSIBILITY_BOUNDS.get(field)
    if bounds is None:
        return True  # No bounds defined for this field
    lo, hi = bounds
    return lo <= float(value) <= hi


@dataclass
class FloorPlanData:
    """Structured data extracted from a floor plan."""
    unit_type: Optional[str] = None
    unit_type_source: str = ""
    unit_type_confidence: float = 0.0
    bedrooms: Optional[int] = None
    bedrooms_source: str = ""
    bedrooms_confidence: float = 0.0
    bathrooms: Optional[float] = None
    bathrooms_source: str = ""
    bathrooms_confidence: float = 0.0
    total_sqft: Optional[float] = None
    total_sqft_source: str = ""
    total_sqft_confidence: float = 0.0
    suite_sqft: Optional[float] = None
    suite_sqft_source: str = ""
    suite_sqft_confidence: float = 0.0
    balcony_sqft: Optional[float] = None
    balcony_sqft_source: str = ""
    balcony_sqft_confidence: float = 0.0
    builtup_sqft: Optional[float] = None
    builtup_sqft_source: str = ""
    builtup_sqft_confidence: float = 0.0
    room_dimensions: Optional[dict] = None
    dimensions_source: str = ""
    features: list = field(default_factory=list)
    features_source: str = ""
    confidence: float = 0.0
    is_duplicate: bool = False
    duplicate_of_index: Optional[int] = None
    hash_value: str = ""
    image_bytes: bytes = b""


@dataclass
class FloorPlanExtractionResult:
    """Collection of all extracted floor plan data."""
    floor_plans: list = field(default_factory=list)
    total_input: int = 0
    total_extracted: int = 0
    total_duplicates: int = 0
    errors: list = field(default_factory=list)


class FloorPlanExtractor:
    """
    Extracts structured data from floor plan images.

    Uses Claude Vision OCR as primary data source with optional
    text fallback from surrounding PDF text. Applies perceptual
    hash deduplication at 95% similarity threshold.
    """

    def __init__(self, api_key: Optional[str] = None,
                 model: Optional[str] = None):
        settings = get_settings()
        self._service = anthropic_service
        self._model = model or settings.ANTHROPIC_MODEL
        self._dedup = DeduplicationService(
            threshold=FLOOR_PLAN_SIMILARITY_THRESHOLD
        )

    async def extract_floor_plans(
        self,
        floor_plan_images: list[ExtractedImage],
        page_text_map: Optional[dict[int, str]] = None,
    ) -> FloorPlanExtractionResult:
        """
        Extract structured data from all floor plan images.

        Deduplication runs first (sequential, CPU-only), then Vision OCR
        calls run in parallel with a semaphore to respect API rate limits.

        Args:
            floor_plan_images: Images classified as floor_plan.
            page_text_map: Optional mapping of page number to extracted text
                           for fallback data enrichment.

        Returns:
            FloorPlanExtractionResult with all extracted data.
        """
        import asyncio

        MAX_CONCURRENT_FP = 5

        result = FloorPlanExtractionResult()
        self._dedup.reset()

        # Phase 0: Filter corrupt images before dedup and Vision API calls.
        # Try image_bytes first, fall back to llm_optimized_bytes.
        valid_images = []
        for image in floor_plan_images:
            if validate_image_bytes(image.image_bytes):
                valid_images.append(image)
            elif (
                image.llm_optimized_bytes
                and validate_image_bytes(image.llm_optimized_bytes)
            ):
                logger.info(
                    "Floor plan page %d: using llm_optimized_bytes fallback",
                    image.metadata.page_number,
                )
                valid_images.append(image)
            else:
                logger.warning(
                    "Skipping corrupt floor plan image on page %d",
                    image.metadata.page_number,
                )
                result.errors.append({
                    "page": image.metadata.page_number,
                    "error": "corrupt or invalid image bytes",
                })
        floor_plan_images = valid_images

        # Phase 1: Dedup sequentially (CPU-only, fast)
        # Use effective bytes (image_bytes or llm_optimized_bytes) for hashing
        unique_images: list[tuple[ExtractedImage, str]] = []
        for idx, image in enumerate(floor_plan_images):
            result.total_input += 1
            effective_bytes = image.image_bytes or image.llm_optimized_bytes or b""
            dedup_result = self._dedup.check_and_register(
                effective_bytes, idx
            )
            if dedup_result.is_duplicate:
                result.total_duplicates += 1
                continue
            unique_images.append((image, dedup_result.hash_value))

        # Phase 2: Vision extraction in parallel (API-bound)
        sem = asyncio.Semaphore(MAX_CONCURRENT_FP)

        async def _extract_one(
            image: ExtractedImage, hash_value: str
        ) -> list[FloorPlanData]:
            async with sem:
                try:
                    vision_plans = await self._extract_from_image(image)
                    effective_bytes = image.image_bytes or image.llm_optimized_bytes or b""
                    for vp in vision_plans:
                        vp = self._enforce_bedrooms_from_unit_type(vp)
                        if page_text_map:
                            page_num = image.metadata.page_number
                            text_data = self._extract_from_text(
                                page_text_map, page_num,
                                unit_type_hint=vp.unit_type,
                            )
                            vp = self._merge_data(vp, text_data, page_num)
                        vp = self._cross_validate_area(vp)
                        vp.hash_value = hash_value
                        vp.image_bytes = effective_bytes
                    return vision_plans
                except Exception as e:
                    logger.error(
                        "Floor plan extraction failed for page %d: %s",
                        image.metadata.page_number, e,
                    )
                    result.errors.append({
                        "page": image.metadata.page_number, "error": str(e)
                    })
                    return []

        extracted_nested = await asyncio.gather(
            *[_extract_one(img, h) for img, h in unique_images]
        )

        for fp_list in extracted_nested:
            for fp in fp_list:
                if fp is not None and fp.confidence > 0:
                    result.floor_plans.append(fp)
                    result.total_extracted += 1

        # Deduplicate by unit_type: when multiple images produce floor
        # plans with the same normalized unit key (e.g., diagram page and
        # specs page both yield "1BR Type A"), keep the one with the most
        # complete area data and merge missing fields from the other.
        result.floor_plans = self._deduplicate_by_unit_type(result.floor_plans)

        logger.info(
            "Floor plan extraction complete: %d input, %d unique, %d duplicates",
            result.total_input,
            len(result.floor_plans),
            result.total_duplicates,
        )

        return result

    @classmethod
    def _deduplicate_by_unit_type(
        cls, floor_plans: list[FloorPlanData],
    ) -> list[FloorPlanData]:
        """Merge floor plans that share the same normalized unit key.

        When Vision OCR runs on both diagram pages and specs pages, the same
        unit type may appear twice: once with room dimensions (from diagram)
        and once with correct area breakdown (from specs table).  This method
        merges them, keeping the most complete data from each.

        The entry with MORE non-null area fields (suite/balcony/total) is the
        primary. Missing fields are filled from the secondary. Image bytes
        are taken from whichever entry has them (diagram page typically does).

        Generic entries (no sub-type, e.g. "1BR") are merged into specific
        entries (e.g. "1BR Type A") when there is exactly one specific entry
        with that bed count to merge into.
        """
        if len(floor_plans) <= 1:
            return floor_plans

        groups: dict[str, list[FloorPlanData]] = {}
        no_type: list[FloorPlanData] = []

        for fp in floor_plans:
            if not fp.unit_type:
                no_type.append(fp)
                continue
            key = "|".join(cls._normalize_unit_key(fp.unit_type))
            groups.setdefault(key, []).append(fp)

        # Merge generic entries (empty sub-type) into specific entries.
        # e.g., "1br|" entries merge into "1br|a" if that's the only
        # specific 1br group. If multiple specific groups exist (a, b, c),
        # generics are dropped (ambiguous -- can't determine which).
        generic_keys = [k for k in groups if k.endswith("|")]
        for gk in generic_keys:
            bed_key = gk.rstrip("|")
            # Find all specific groups with same bed count
            specific = [
                k for k in groups
                if k.startswith(bed_key + "|") and not k.endswith("|")
            ]
            if len(specific) == 1:
                # Unambiguous: merge generics into the single specific group
                groups[specific[0]].extend(groups.pop(gk))
            elif len(specific) > 1:
                # Ambiguous: drop generics (they have less data anyway)
                dropped = groups.pop(gk)
                logger.info(
                    "Dropping %d generic '%s' floor plans (ambiguous: %d specific groups)",
                    len(dropped), bed_key, len(specific),
                )

        merged: list[FloorPlanData] = []
        for key, group in groups.items():
            if len(group) == 1:
                merged.append(group[0])
                continue

            # Score each entry by data completeness
            def _area_score(fp: FloorPlanData) -> int:
                return sum(1 for v in (
                    fp.suite_sqft, fp.balcony_sqft, fp.total_sqft,
                    fp.builtup_sqft,
                ) if v is not None and v > 0)

            group.sort(key=lambda fp: (_area_score(fp), fp.confidence), reverse=True)
            primary = group[0]

            # Merge missing fields from secondary entries
            for secondary in group[1:]:
                if primary.suite_sqft is None and secondary.suite_sqft:
                    primary.suite_sqft = secondary.suite_sqft
                    primary.suite_sqft_source = secondary.suite_sqft_source
                if primary.balcony_sqft is None and secondary.balcony_sqft:
                    primary.balcony_sqft = secondary.balcony_sqft
                    primary.balcony_sqft_source = secondary.balcony_sqft_source
                if primary.total_sqft is None and secondary.total_sqft:
                    primary.total_sqft = secondary.total_sqft
                    primary.total_sqft_source = secondary.total_sqft_source
                if primary.builtup_sqft is None and secondary.builtup_sqft:
                    primary.builtup_sqft = secondary.builtup_sqft
                    primary.builtup_sqft_source = secondary.builtup_sqft_source
                if not primary.room_dimensions and secondary.room_dimensions:
                    primary.room_dimensions = secondary.room_dimensions
                    primary.dimensions_source = secondary.dimensions_source
                if not primary.features and secondary.features:
                    primary.features = secondary.features
                if not primary.image_bytes and secondary.image_bytes:
                    primary.image_bytes = secondary.image_bytes
                if primary.bathrooms is None and secondary.bathrooms is not None:
                    primary.bathrooms = secondary.bathrooms
                    primary.bathrooms_source = secondary.bathrooms_source

            # Reconcile area fields after merge
            primary = cls._reconcile_area_fields(primary)

            logger.info(
                "Deduplicated floor plan '%s': merged %d entries",
                primary.unit_type, len(group),
            )
            merged.append(primary)

        merged.extend(no_type)
        return merged

    async def _extract_from_image(
        self, image: ExtractedImage
    ) -> list[FloorPlanData]:
        """Extract floor plan data from image using Claude Vision.

        Falls back to llm_optimized_bytes when image_bytes is empty (released).
        Returns a list to support multi-plan pages.
        """
        # Determine effective source bytes
        source_bytes = image.image_bytes if image.image_bytes else None
        if not source_bytes and image.llm_optimized_bytes:
            source_bytes = image.llm_optimized_bytes
        if not source_bytes:
            logger.warning(
                "No usable bytes for floor plan on page %d",
                image.metadata.page_number,
            )
            return [FloorPlanData(confidence=0.0)]

        # Use PNG for floor plans (lossless, better for text)
        optimized = create_llm_optimized(
            source_bytes, max_dim=1568, fmt="PNG", quality=100
        )
        img_bytes = optimized if optimized else source_bytes

        media_type = self._detect_media_type(img_bytes)

        try:
            response = await self._service.vision_completion(
                image_bytes=img_bytes,
                prompt=FLOOR_PLAN_OCR_PROMPT,
                media_type=media_type,
                max_tokens=2000,
            )

            return self._parse_vision_response(response)

        except Exception as e:
            logger.error(
                "Floor plan OCR failed: %s", e,
            )
            return [FloorPlanData(confidence=0.0)]

    def _parse_vision_response(
        self, response: anthropic.types.Message
    ) -> list[FloorPlanData]:
        """Parse Claude's floor plan OCR response.

        Supports both the new multi-plan format ({"floor_plans": [...]})
        and the legacy single-plan format ({"unit_type": ...}).
        """
        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            data = json.loads(text)

            # Multi-plan format: {"floor_plans": [...]}
            if "floor_plans" in data and isinstance(data["floor_plans"], list):
                plans = []
                for item in data["floor_plans"]:
                    plans.append(self._parse_single_plan(item))
                return plans if plans else [FloorPlanData(confidence=0.0)]

            # Legacy single-plan format: {"unit_type": ..., ...}
            return [self._parse_single_plan(data)]

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.warning("Failed to parse floor plan OCR response: %s", e)
            return [FloorPlanData(confidence=0.0)]

    @staticmethod
    def _parse_range_value(val) -> float | None:
        """Parse a potentially range-formatted area value, returning the max.

        Handles:
            "541.64 - 541.75"  -> 541.75
            "541.64 to 541.75" -> 541.75
            "541.64"           -> 541.64
            541.64             -> 541.64
            None               -> None
        """
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        if not s:
            return None
        for sep in [" - ", " to ", "-"]:
            if sep in s:
                parts = s.split(sep)
                try:
                    return max(float(p.strip()) for p in parts if p.strip())
                except ValueError:
                    continue
        try:
            return float(s)
        except ValueError:
            return None

    @classmethod
    def _parse_single_plan(cls, data: dict) -> FloorPlanData:
        """Parse a single floor plan dict into FloorPlanData."""
        fp = FloorPlanData()

        plan_conf = float(data.get("confidence", 0.85))

        if data.get("unit_type"):
            fp.unit_type = data["unit_type"]
            fp.unit_type_source = "floor_plan_image"
            fp.unit_type_confidence = plan_conf

        if data.get("bedrooms") is not None:
            bed_val = int(data["bedrooms"])
            if _is_plausible("bedrooms", bed_val):
                fp.bedrooms = bed_val
                fp.bedrooms_source = "floor_plan_image"
                fp.bedrooms_confidence = plan_conf

        if data.get("bathrooms") is not None:
            bath_val = float(data["bathrooms"])
            if _is_plausible("bathrooms", bath_val):
                fp.bathrooms = bath_val
                fp.bathrooms_source = "floor_plan_image"
                fp.bathrooms_confidence = plan_conf

        parsed_total = cls._parse_range_value(data.get("total_sqft"))
        if parsed_total is not None and _is_plausible("total_sqft", parsed_total):
            fp.total_sqft = parsed_total
            fp.total_sqft_source = "floor_plan_image"
            fp.total_sqft_confidence = plan_conf

        parsed_suite = cls._parse_range_value(data.get("suite_sqft"))
        if parsed_suite is not None and _is_plausible("suite_sqft", parsed_suite):
            fp.suite_sqft = parsed_suite
            fp.suite_sqft_source = "floor_plan_image"
            fp.suite_sqft_confidence = plan_conf

        parsed_balcony = cls._parse_range_value(data.get("balcony_sqft"))
        if parsed_balcony is not None and _is_plausible("balcony_sqft", parsed_balcony):
            fp.balcony_sqft = parsed_balcony
            fp.balcony_sqft_source = "floor_plan_image"
            fp.balcony_sqft_confidence = plan_conf

        parsed_builtup = cls._parse_range_value(data.get("builtup_sqft"))
        if parsed_builtup is not None and _is_plausible("builtup_sqft", parsed_builtup):
            fp.builtup_sqft = parsed_builtup
            fp.builtup_sqft_source = "floor_plan_image"
            fp.builtup_sqft_confidence = plan_conf

        # Room dimensions ONLY from image (never text)
        if data.get("room_dimensions"):
            fp.room_dimensions = data["room_dimensions"]
            fp.dimensions_source = "floor_plan_image"

        if data.get("features"):
            fp.features = data["features"]
            fp.features_source = "floor_plan_image"

        fp.confidence = plan_conf

        # Infer bathrooms from room_dimensions if Vision didn't return a count
        if fp.bathrooms is None and fp.room_dimensions:
            inferred = cls._infer_bathrooms_from_rooms(fp.room_dimensions)
            if inferred > 0:
                fp.bathrooms = inferred
                fp.bathrooms_source = "inferred_from_rooms"
                fp.bathrooms_confidence = 0.70
                logger.info(
                    "Inferred bathrooms=%.1f from room dims for %s",
                    inferred, fp.unit_type or "unknown",
                )

        return fp

    @staticmethod
    @staticmethod
    def _infer_bathrooms_from_rooms(room_dimensions: dict) -> float:
        """Count bathrooms from room dimension keys.

        Full bathrooms (1.0 each): bath, bathroom, ensuite, en-suite, shower_room
        Half bathrooms (0.5 each): wc, powder_room, toilet, half_bath, guest_wc

        Handles numbered variants: bath_1, bath_2, bathroom_2, etc.
        """
        full_bath_patterns = re.compile(
            r"^(?:bath(?:room)?|en_?suite|shower_?room)(?:_?\d+)?$", re.IGNORECASE
        )
        half_bath_patterns = re.compile(
            r"^(?:wc|powder_?room|toilet|half_?bath|guest_?wc|p_room)(?:_?\d+)?$",
            re.IGNORECASE,
        )

        count = 0.0
        for key in room_dimensions:
            normalized = key.strip().lower().replace(" ", "_")
            if full_bath_patterns.match(normalized):
                count += 1.0
            elif half_bath_patterns.match(normalized):
                count += 0.5
        return count

    @staticmethod
    def _enforce_bedrooms_from_unit_type(fp: FloorPlanData) -> FloorPlanData:
        """Override bedroom count when unit_type label contradicts Vision's count.

        Parsing rules:
        - "Studio" / "STD" -> 0
        - "1BR", "1 BR", "1 Bed", "1 Bedroom", "1BR Type A" -> 1
        - "2BR Type B" -> 2, etc.
        """
        if not fp.unit_type:
            return fp

        label = fp.unit_type.strip().lower()

        if label.startswith("studio") or label.startswith("std"):
            label_beds = 0
        else:
            m = re.match(r"(\d+)\s*(?:br|bed|bedroom)", label)
            if m:
                label_beds = int(m.group(1))
            else:
                return fp  # cannot parse -- leave as-is

        if fp.bedrooms != label_beds:
            logger.info(
                "Bedroom override for %s: Vision said %s, label says %d",
                fp.unit_type, fp.bedrooms, label_beds,
            )
            fp.bedrooms = label_beds
            fp.bedrooms_source = "unit_type_label"
            fp.bedrooms_confidence = 0.95

        return fp

    @staticmethod
    def _parse_dimension(dim_str: str) -> tuple[float, float] | None:
        """Parse a dimension string like '4.2m x 3.8m' into (length, width).

        Supports mm, cm, meters (m, M), feet (ft, '), and bare numbers.
        Returns None if the string cannot be parsed.
        """
        pattern = r"([\d.]+)\s*(?:mm|cm|m|M|ft|'|)?\s*[xX]\s*([\d.]+)\s*(?:mm|cm|m|M|ft|'|)?"
        match = re.search(pattern, dim_str)
        if not match:
            return None
        try:
            return (float(match.group(1)), float(match.group(2)))
        except ValueError:
            return None

    @staticmethod
    def _is_feet_dimension(dim_str: str) -> bool:
        """Check if dimension string uses feet units."""
        return bool(re.search(r"(?:ft|')\s*$", dim_str.split("x")[0], re.IGNORECASE))

    @staticmethod
    def _detect_dimension_unit(dim_str: str, length: float, width: float) -> str:
        """Infer measurement unit from explicit suffix OR magnitude.

        Priority: explicit suffix > magnitude inference.
        Returns: 'mm', 'cm', 'm', or 'ft'.

        Magnitude heuristics (when no suffix is present):
        - avg > 200: millimeters (room dimensions in mm are 3000-8000 range)
        - avg > 30: feet (room dimensions in ft are 8-40 range)
        - avg <= 30: meters (room dimensions in m are 2-15 range)
        """
        s = dim_str.lower()
        # Explicit suffix detection (order matters: check mm before m)
        first_half = s.split("x")[0]
        if "mm" in first_half:
            return "mm"
        if "cm" in first_half:
            return "cm"
        if re.search(r"(?:ft|')\s*$", first_half):
            return "ft"
        if re.search(r"(?<![mcf])m(?:\s|$)", first_half):
            return "m"

        # No explicit unit: infer from magnitude
        avg = (length + width) / 2
        if avg > 200:
            return "mm"
        if avg > 30:
            return "ft"
        return "m"

    @classmethod
    def _compute_area_from_dimensions(
        cls, room_dimensions: dict[str, str]
    ) -> float:
        """Compute total area in sqft from room dimension strings.

        For meter dimensions, converts to sqft (sqm * 10.764).
        For feet dimensions, area is already in sqft.
        """
        total_area = 0.0
        for label, dim_str in room_dimensions.items():
            if not isinstance(dim_str, str) or not dim_str.strip():
                continue
            parsed = cls._parse_dimension(dim_str)
            if parsed is None:
                continue
            length, width = parsed
            unit = cls._detect_dimension_unit(dim_str, length, width)
            if unit == "mm":
                room_area = (length / 1000) * (width / 1000) * SQM_TO_SQFT
            elif unit == "cm":
                room_area = (length / 100) * (width / 100) * SQM_TO_SQFT
            elif unit == "ft":
                room_area = length * width
            else:  # meters (default)
                room_area = length * width * SQM_TO_SQFT
            total_area += room_area
        return total_area

    @classmethod
    def _cross_validate_area(cls, fp: FloorPlanData) -> FloorPlanData:
        """Cross-validate stated total_sqft against room dimensions.

        - If total_sqft is missing but dimensions exist: compute and fill.
        - If both exist and differ by >40%: log warning, keep stated value.
        - The computed area is a lower bound (rooms don't include walls,
          corridors, etc.), so we apply a 15% gross-up factor.
        """
        if not fp.room_dimensions:
            return fp

        computed_net = cls._compute_area_from_dimensions(fp.room_dimensions)
        if computed_net <= 0:
            return fp

        # Gross-up: rooms are net area, total_sqft includes walls/corridors
        GROSS_UP = 1.15
        computed_gross = round(computed_net * GROSS_UP, 1)

        if fp.total_sqft is None:
            if _is_plausible("total_sqft", computed_gross):
                fp.total_sqft = computed_gross
                fp.total_sqft_source = "computed_from_dimensions"
                fp.total_sqft_confidence = 0.55
            else:
                logger.warning(
                    "Discarding implausible computed area %.0f sqft for %s",
                    computed_gross, fp.unit_type or "unknown",
                )
            return fp

        # Both exist: check consistency
        if fp.total_sqft > 0:
            ratio = computed_gross / fp.total_sqft
            if ratio < 0.3 or ratio > 3.0:
                # Extreme divergence: computed is wildly wrong, ignore it
                logger.warning(
                    "Floor plan %s: computed=%.0f vs stated=%.0f (ratio=%.2f) "
                    "-- extreme divergence, ignoring computed",
                    fp.unit_type or "unknown",
                    computed_gross,
                    fp.total_sqft,
                    ratio,
                )
                return fp
            elif ratio < 0.6 or ratio > 1.4:
                logger.info(
                    "Floor plan %s: computed=%.0f vs stated=%.0f (ratio=%.2f) "
                    "-- moderate divergence",
                    fp.unit_type or "unknown",
                    computed_gross,
                    fp.total_sqft,
                    ratio,
                )

        return fp

    @staticmethod
    def _reconcile_area_fields(fp: FloorPlanData) -> FloorPlanData:
        """Compute missing area field when 2 of 3 (suite, balcony, total) are known.

        Relationship: total = suite + balcony.
        If two values are present, derive the third.

        Also detects when total_sqft ~= suite_sqft (Vision read suite as total)
        and recomputes total = suite + balcony. Uses relationship checks:
        - total < suite is always wrong
        - total within 2% of suite means total IS suite (balcony missing)
        """
        s = fp.suite_sqft
        b = fp.balcony_sqft
        t = fp.total_sqft

        known = sum(1 for v in (s, b, t) if v is not None and v > 0)

        # All three known: sanity check total ~= suite + balcony
        if known == 3 and s and b and t:
            expected = s + b
            if t > 0 and (t < s or abs(t - s) / t < 0.02) and abs(expected - t) / t > 0.02:
                logger.info(
                    "Recomputing total_sqft for %s: was %.2f (=suite), now %.2f (suite+balcony)",
                    fp.unit_type or "unknown", t, expected,
                )
                fp.total_sqft = round(expected, 2)
                fp.total_sqft_source = "computed"
            return fp

        if known < 2:
            return fp

        if t is not None and s is not None and b is None:
            fp.balcony_sqft = round(t - s, 2)
            fp.balcony_sqft_source = "computed"
        elif t is not None and b is not None and s is None:
            fp.suite_sqft = round(t - b, 2)
            fp.suite_sqft_source = "computed"
        elif s is not None and b is not None and t is None:
            fp.total_sqft = round(s + b, 2)
            fp.total_sqft_source = "computed"

        return fp

    def _extract_from_text(
        self, page_text_map: dict[int, str], page_num: int,
        unit_type_hint: str | None = None,
    ) -> dict[str, Any]:
        """
        Extract floor plan data from surrounding PDF text.

        Only uses text from the same page or adjacent pages (+/- 1).
        Extracts unit type, area breakdown (suite/balcony/total), bathroom
        count, and price via regex.

        Args:
            page_text_map: Mapping of page number to extracted text.
            page_num: Current floor plan page number.
            unit_type_hint: Optional unit_type from Vision OCR to match
                the correct area breakdown when multiple units are on one page.
        """
        relevant_text = ""
        for p in [page_num - 1, page_num, page_num + 1]:
            if p in page_text_map:
                relevant_text += page_text_map[p] + "\n"

        if not relevant_text.strip():
            return {}

        extracted: dict[str, Any] = {}

        text_lower = relevant_text.lower()

        # Unit type patterns
        for pattern in ["studio", "1br", "2br", "3br", "4br", "5br",
                        "1 bed", "2 bed", "3 bed", "4 bed", "5 bed",
                        "penthouse", "duplex", "townhouse"]:
            if pattern in text_lower:
                extracted["unit_type"] = pattern.upper().replace(" BED", "BR")
                break

        # -----------------------------------------------------------------
        # Area breakdown parsing: Suite / Balcony / Total built-up
        # Handles Dubai brochure format where areas are listed as:
        #   Suite\nBalcony\nTotal built-up\n[Min\n]VAL\nVAL\nVAL\n[Max\n]...
        # Values are "XX.XX Sq.m / YYY.YY Sq.ft" or just "YYY.YY Sq.ft".
        # For min/max ranges, we take the MAX values.
        # -----------------------------------------------------------------
        breakdown = self._parse_area_breakdown(relevant_text, unit_type_hint)
        if breakdown:
            if breakdown.get("suite_sqft"):
                extracted["suite_sqft"] = breakdown["suite_sqft"]
                extracted["suite_sqft_confidence"] = 0.92
            if breakdown.get("balcony_sqft"):
                extracted["balcony_sqft"] = breakdown["balcony_sqft"]
                extracted["balcony_sqft_confidence"] = 0.92
            if breakdown.get("total_sqft"):
                extracted["total_sqft"] = breakdown["total_sqft"]
                extracted["total_sqft_confidence"] = 0.92

        # Fallback: generic sqft if breakdown parsing found nothing
        if "total_sqft" not in extracted:
            sqft_match = re.search(
                r'([\d,]+(?:\.\d+)?)\s*(?:sq\.?\s*ft|sqft|square\s*feet)',
                relevant_text,
                re.IGNORECASE,
            )
            if sqft_match:
                sqft_str = sqft_match.group(1).replace(",", "")
                try:
                    sqft_val = float(sqft_str)
                    if _is_plausible("total_sqft", sqft_val):
                        extracted["total_sqft"] = sqft_val
                        extracted["total_sqft_confidence"] = 0.60
                except ValueError:
                    pass

        # Sqm patterns (convert to sqft): "1,234 sqm", "1234 sq.m"
        if "total_sqft" not in extracted:
            sqm_match = re.search(
                r'([\d,]+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|square\s*met)',
                relevant_text,
                re.IGNORECASE,
            )
            if sqm_match:
                sqm_str = sqm_match.group(1).replace(",", "")
                try:
                    sqft_val = float(sqm_str) * SQM_TO_SQFT
                    if _is_plausible("total_sqft", sqft_val):
                        extracted["total_sqft"] = sqft_val
                        extracted["total_sqft_confidence"] = 0.60
                except ValueError:
                    pass

        # Bathroom patterns: "2.5 bath", "2 bathrooms", "3 baths"
        bath_match = re.search(
            r'(\d+(?:\.\d)?)\s*(?:bath(?:room)?s?|baths?)\b',
            relevant_text,
            re.IGNORECASE,
        )
        if bath_match:
            try:
                bath_val = float(bath_match.group(1))
                if _is_plausible("bathrooms", bath_val):
                    extracted["bathrooms"] = bath_val
                    extracted["bathrooms_confidence"] = 0.60
            except ValueError:
                pass

        # Bedroom count from text (numeric, not already captured via unit_type)
        if "unit_type" not in extracted:
            bed_match = re.search(
                r'(\d+)\s*(?:bed(?:room)?s?|BR)\b',
                relevant_text,
                re.IGNORECASE,
            )
            if bed_match:
                try:
                    bed_val = int(bed_match.group(1))
                    if _is_plausible("bedrooms", bed_val):
                        extracted["bedrooms"] = bed_val
                        extracted["bedrooms_confidence"] = 0.60
                except ValueError:
                    pass

        # Price patterns: "AED 1,500,000", "AED 1.5M", "AED 850K"
        price_match = re.search(
            r'AED\s*([\d,]+(?:\.\d+)?)\s*([MmKk])?',
            relevant_text,
        )
        if price_match:
            try:
                price_val = float(price_match.group(1).replace(",", ""))
                suffix = (price_match.group(2) or "").upper()
                if suffix == "M":
                    price_val *= 1_000_000
                elif suffix == "K":
                    price_val *= 1_000
                extracted["price"] = price_val
            except ValueError:
                pass

        return extracted

    @classmethod
    def _parse_area_breakdown(
        cls, text: str, unit_type_hint: str | None = None,
    ) -> dict[str, float] | None:
        """Parse labeled Suite / Balcony / Total area breakdown from text.

        Handles common Dubai brochure formats:
        1. Column-header format:
             Suite\\nBalcony\\nTotal built-up\\n[Min\\n]VAL\\nVAL\\nVAL
        2. Labeled-row format:
             Suite  XX.XX Sq.m / YYY.YY Sq.ft
             Balcony  XX.XX Sq.m / YYY.YY Sq.ft
             Total built-up  XX.XX Sq.m / YYY.YY Sq.ft

        For min/max ranges, returns the MAX values.

        If multiple unit types appear in the text, uses unit_type_hint to
        pick the closest matching section.

        Returns:
            Dict with suite_sqft, balcony_sqft, total_sqft or None.
        """
        # Sqft value pattern: captures "YYY.YY" from "XX Sq.m / YYY.YY Sq.ft"
        # or standalone "YYY.YY Sq.ft"
        _SQFT_VAL = r'([\d,]+(?:\.\d+)?)\s*(?:sq\.?\s*ft|sqft)'

        # ---------------------------------------------------------------
        # Strategy 1: Column-header format
        # Find "Suite\nBalcony\nTotal" header block, then extract sqft
        # values that follow.
        # ---------------------------------------------------------------
        sections = cls._split_text_by_unit_type(text)

        if unit_type_hint and len(sections) > 1:
            sections = cls._pick_matching_section(sections, unit_type_hint)

        for _label, section_text in sections:
            header_match = re.search(
                r'suite\s*\n\s*balcony\s*\n\s*total(?:\s+built[\s-]*up)?',
                section_text,
                re.IGNORECASE,
            )
            if not header_match:
                continue

            after_header = section_text[header_match.end():]
            sqft_values = re.findall(_SQFT_VAL, after_header, re.IGNORECASE)
            floats = []
            for v in sqft_values[:6]:
                try:
                    floats.append(float(v.replace(",", "")))
                except ValueError:
                    continue

            if len(floats) >= 3:
                # If 6+ values => min/max; take last triplet (max)
                idx = 3 if len(floats) >= 6 else 0
                result = {
                    "suite_sqft": floats[idx],
                    "balcony_sqft": floats[idx + 1],
                    "total_sqft": floats[idx + 2],
                }
                # Sanity: total should be >= suite
                if result["total_sqft"] >= result["suite_sqft"]:
                    return result

        # ---------------------------------------------------------------
        # Strategy 2: Labeled-row format
        # "Suite ... NNN Sq.ft", "Balcony ... NNN Sq.ft", "Total ... NNN Sq.ft"
        # Each on its own line or nearby.
        # ---------------------------------------------------------------
        suite_val = None
        balcony_val = None
        total_val = None

        suite_m = re.search(
            r'(?:suite|internal)(?:\s+area)?\s*[:\s].*?' + _SQFT_VAL,
            text, re.IGNORECASE,
        )
        if suite_m:
            try:
                suite_val = float(suite_m.group(1).replace(",", ""))
            except ValueError:
                pass

        balcony_m = re.search(
            r'(?:balcony|terrace)(?:\s+area)?\s*[:\s].*?' + _SQFT_VAL,
            text, re.IGNORECASE,
        )
        if balcony_m:
            try:
                balcony_val = float(balcony_m.group(1).replace(",", ""))
            except ValueError:
                pass

        total_m = re.search(
            r'(?:total|gross)(?:\s+(?:built[\s-]*up|area))?\s*[:\s].*?' + _SQFT_VAL,
            text, re.IGNORECASE,
        )
        if total_m:
            try:
                total_val = float(total_m.group(1).replace(",", ""))
            except ValueError:
                pass

        if total_val and suite_val and total_val >= suite_val:
            return {
                "suite_sqft": suite_val,
                "balcony_sqft": balcony_val,
                "total_sqft": total_val,
            }

        return None

    @staticmethod
    def _split_text_by_unit_type(text: str) -> list[tuple[str, str]]:
        """Split text into sections by unit type labels.

        Returns list of (unit_type_label, section_text) tuples.
        If no unit type labels found, returns [("", full_text)].
        """
        # Match labels like "1 bedroom - Unit type A", "2BR Type B", etc.
        pattern = re.compile(
            r'(\d+\s*(?:bed(?:room)?s?|br)\s*[-]?\s*(?:(?:apartment|unit)\s*)?'
            r'(?:type\s+[a-z]\d*)?|studio|penthouse|duplex|townhouse)',
            re.IGNORECASE,
        )
        matches = list(pattern.finditer(text))
        if not matches:
            return [("", text)]

        sections = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append((m.group(0).strip(), text[start:end]))
        return sections

    @classmethod
    def _pick_matching_section(
        cls, sections: list[tuple[str, str]], unit_type_hint: str,
    ) -> list[tuple[str, str]]:
        """Pick the section whose label best matches the unit_type_hint.

        Falls back to returning all sections if no match found.
        """
        hint_bed, hint_sub = cls._normalize_unit_key(unit_type_hint)
        hint_letter = cls._extract_type_letter(unit_type_hint)

        for label, section_text in sections:
            s_bed, s_sub = cls._normalize_unit_key(label)
            s_letter = cls._extract_type_letter(label)
            # Exact match: bed key + sub type
            if s_bed == hint_bed and s_sub and s_sub == hint_sub:
                return [(label, section_text)]
            # Type letter match
            if s_bed == hint_bed and s_letter and s_letter == hint_letter:
                return [(label, section_text)]

        # Fallback: bed count only
        for label, section_text in sections:
            s_bed, _ = cls._normalize_unit_key(label)
            if s_bed == hint_bed:
                return [(label, section_text)]

        return sections

    def _merge_data(
        self, vision: FloorPlanData, text_data: dict,
        page_num: int
    ) -> FloorPlanData:
        """
        Merge vision-extracted data with text-extracted data.

        For area fields (suite/balcony/total): if text has a LABELED
        breakdown (suite + total both present, total > suite), text values
        are preferred because labeled text is more reliable than Vision OCR
        which often confuses suite area with total area.

        For other fields: Vision is source of truth, text is fallback only.
        Room dimensions are ONLY sourced from image OCR (never text).
        """
        if not text_data:
            return vision

        # Unit type: image first, text fallback
        # Unit type: image first, text fallback
        if not vision.unit_type and text_data.get("unit_type"):
            vision.unit_type = text_data["unit_type"]
            vision.unit_type_source = "text_fallback"
            vision.unit_type_confidence = text_data.get(
                "unit_type_confidence", 0.60
            )

        # -----------------------------------------------------------------
        # Area fields: confidence-weighted merge.
        # Text labeled breakdown (suite + total present) gets 0.92 confidence.
        # Text fallback (single regex match) gets 0.60. Higher confidence wins.
        # -----------------------------------------------------------------
        text_has_breakdown = (
            text_data.get("suite_sqft") is not None
            and text_data.get("total_sqft") is not None
            and text_data["total_sqft"] > text_data["suite_sqft"]
        )
        text_area_confidence = 0.92 if text_has_breakdown else 0.60

        for area_field in ("total_sqft", "suite_sqft", "balcony_sqft"):
            text_val = text_data.get(area_field)
            text_conf = text_data.get(
                f"{area_field}_confidence", text_area_confidence
            )
            vision_val = getattr(vision, area_field)
            vision_conf = getattr(vision, f"{area_field}_confidence", 0.0)

            if text_val is None:
                continue  # Nothing from text, keep Vision value

            if vision_val is None:
                # Vision has nothing, take text
                setattr(vision, area_field, text_val)
                setattr(
                    vision, f"{area_field}_source",
                    "text_breakdown" if text_has_breakdown else "text_fallback",
                )
                setattr(vision, f"{area_field}_confidence", text_conf)
            elif text_conf > vision_conf:
                # Text is more confident -- log if values differ significantly
                if vision_val > 0 and abs(text_val - vision_val) / vision_val > 0.02:
                    logger.info(
                        "Page %d %s: text %.1f (conf=%.2f) overrides "
                        "vision %.1f (conf=%.2f)",
                        page_num, area_field, text_val, text_conf,
                        vision_val, vision_conf,
                    )
                setattr(vision, area_field, text_val)
                setattr(
                    vision, f"{area_field}_source",
                    "text_breakdown" if text_has_breakdown else "text_fallback",
                )
                setattr(vision, f"{area_field}_confidence", text_conf)
            # else: Vision confidence >= text confidence, keep Vision value

        # Bathrooms: higher confidence wins
        if text_data.get("bathrooms") is not None:
            text_conf = text_data.get("bathrooms_confidence", 0.60)
            if vision.bathrooms is None or text_conf > vision.bathrooms_confidence:
                vision.bathrooms = text_data["bathrooms"]
                vision.bathrooms_source = "text_fallback"
                vision.bathrooms_confidence = text_conf

        # Bedrooms: higher confidence wins
        if text_data.get("bedrooms") is not None:
            text_conf = text_data.get("bedrooms_confidence", 0.60)
            if vision.bedrooms is None or text_conf > vision.bedrooms_confidence:
                vision.bedrooms = text_data["bedrooms"]
                vision.bedrooms_source = "text_fallback"
                vision.bedrooms_confidence = text_conf

        return vision

    def merge_with_table_data(
        self,
        vision_plans: list[FloorPlanData],
        table_specs: list[dict],
    ) -> list[FloorPlanData]:
        """Merge Vision-extracted floor plans with pdfplumber table data.

        Table data is ground truth for numeric fields (sqft, bedrooms, bathrooms).
        Vision data supplements with room dimensions and visual features.

        Strategy:
        - Match table rows to Vision plans by unit_type string similarity
        - For matched pairs: numeric fields from table, dimensions from Vision
        - Unmatched table rows: create FloorPlanData from table alone
        - Unmatched Vision plans: keep as-is (low confidence warning)
        """
        if not table_specs:
            return vision_plans

        merged = []
        used_table_indices: set[int] = set()

        for vp in vision_plans:
            best_match = self._find_matching_table_row(
                vp, table_specs, used_table_indices
            )
            if best_match is not None:
                idx, table_row = best_match
                used_table_indices.add(idx)
                # Override numeric fields with table values (highest confidence)
                if table_row.get("total_sqft"):
                    vp.total_sqft = table_row["total_sqft"]
                    vp.total_sqft_source = "table"
                    vp.total_sqft_confidence = 0.99
                if table_row.get("balcony_sqft"):
                    vp.balcony_sqft = table_row["balcony_sqft"]
                    vp.balcony_sqft_source = "table"
                    vp.balcony_sqft_confidence = 0.99
                if table_row.get("builtup_sqft"):
                    vp.builtup_sqft = table_row["builtup_sqft"]
                    vp.builtup_sqft_source = "table"
                    vp.builtup_sqft_confidence = 0.99
                if table_row.get("bedrooms") is not None:
                    vp.bedrooms = int(table_row["bedrooms"])
                    vp.bedrooms_source = "table"
                    vp.bedrooms_confidence = 0.99
                if table_row.get("bathrooms") is not None:
                    vp.bathrooms = float(table_row["bathrooms"])
                    vp.bathrooms_source = "table"
                    vp.bathrooms_confidence = 0.99
                if table_row.get("suite_sqft"):
                    vp.suite_sqft = table_row["suite_sqft"]
                    vp.suite_sqft_source = "table"
                    vp.suite_sqft_confidence = 0.99
                if table_row.get("unit_type") and not vp.unit_type:
                    vp.unit_type = table_row["unit_type"]
                    vp.unit_type_source = "table"
                    vp.unit_type_confidence = 0.99
                vp = self._reconcile_area_fields(vp)
            merged.append(vp)

        # Add table rows that had no Vision match
        for idx, row in enumerate(table_specs):
            if idx not in used_table_indices:
                fp = FloorPlanData(
                    unit_type=row.get("unit_type"),
                    unit_type_source="table" if row.get("unit_type") else "",
                    bedrooms=(
                        int(row["bedrooms"])
                        if row.get("bedrooms") is not None
                        else None
                    ),
                    bedrooms_source=(
                        "table" if row.get("bedrooms") is not None else ""
                    ),
                    bathrooms=(
                        float(row["bathrooms"])
                        if row.get("bathrooms") is not None
                        else None
                    ),
                    bathrooms_source=(
                        "table" if row.get("bathrooms") is not None else ""
                    ),
                    total_sqft=row.get("total_sqft"),
                    total_sqft_source="table" if row.get("total_sqft") else "",
                    suite_sqft=row.get("suite_sqft"),
                    suite_sqft_source="table" if row.get("suite_sqft") else "",
                    balcony_sqft=row.get("balcony_sqft"),
                    balcony_sqft_source=(
                        "table" if row.get("balcony_sqft") else ""
                    ),
                    confidence=0.95,
                )
                fp = self._reconcile_area_fields(fp)
                merged.append(fp)

        return merged

    @staticmethod
    def _normalize_unit_key(raw: str) -> tuple[str, str]:
        """Normalize a unit type label into (bed_key, sub_type).

        Examples:
            "1 Bedroom - Unit Type A" -> ("1br", "a")
            "1 Bedroom Apartment Type E" -> ("1br", "e")
            "2BR Type B"              -> ("2br", "b")
            "Studio"                  -> ("studio", "")
            "3 BR - Type A1"          -> ("3br", "a1")
        """
        s = raw.lower().strip()
        # Extract sub-type: "type a", "type a1", "type e", "unit a1", "- a"
        sub = ""
        sub_match = re.search(r"(?:type|unit)\s+([a-z]\d*)\b", s)
        if not sub_match:
            sub_match = re.search(r"[-]\s*([a-z]\d*)\b", s)
        if sub_match:
            sub = sub_match.group(1)

        # Extract bedroom key
        if "studio" in s or "std" in s:
            return ("studio", sub)
        bed_match = re.match(r"(\d+)\s*(?:br|bed(?:room)?(?:\s+apartment)?)", s)
        if bed_match:
            return (f"{bed_match.group(1)}br", sub)
        # Fallback: try to find any digit
        digit_match = re.search(r"(\d+)", s)
        if digit_match:
            return (f"{digit_match.group(1)}br", sub)
        return (s, sub)

    @staticmethod
    def _extract_type_letter(raw: str) -> str | None:
        """Extract just the type letter/number suffix from a unit type label.

        Examples:
            "1 Bedroom Apartment Type E" -> "e"
            "1BR - Type E"               -> "e"
            "Type E"                     -> "e"
            "Unit A1"                    -> "a1"
            "Studio"                     -> None
        """
        s = raw.lower().strip()
        m = re.search(r"(?:type|unit)\s+([a-z]\d*)\b", s)
        if m:
            return m.group(1)
        m = re.search(r"[-]\s*([a-z]\d*)\s*$", s)
        if m:
            return m.group(1)
        return None

    @classmethod
    def _find_matching_table_row(
        cls, vp: FloorPlanData, table_specs: list[dict], used: set[int]
    ) -> tuple[int, dict] | None:
        """Find matching table row using 4-pass matching.

        Pass 1: Exact (bed_key, sub_type) match.
        Pass 2: Type letter match (same bed count + same type letter).
        Pass 3: bed_key only (first unused row with same bed count).
        Pass 4: Numeric bedroom count fallback.
        """
        if not vp.unit_type:
            return None

        vp_bed, vp_sub = cls._normalize_unit_key(vp.unit_type)
        vp_letter = cls._extract_type_letter(vp.unit_type)

        # Pass 1: exact (bed_key, sub_type)
        for idx, row in enumerate(table_specs):
            if idx in used:
                continue
            row_type = row.get("unit_type") or ""
            if not row_type:
                continue
            r_bed, r_sub = cls._normalize_unit_key(row_type)
            if vp_bed == r_bed and vp_sub == r_sub and vp_sub:
                return (idx, row)

        # Pass 2: type letter match (bed_key + type letter)
        if vp_letter:
            for idx, row in enumerate(table_specs):
                if idx in used:
                    continue
                row_type = row.get("unit_type") or ""
                if not row_type:
                    continue
                r_bed, _ = cls._normalize_unit_key(row_type)
                r_letter = cls._extract_type_letter(row_type)
                if vp_bed == r_bed and r_letter and vp_letter == r_letter:
                    return (idx, row)

        # Pass 3: bed_key only (first unused)
        for idx, row in enumerate(table_specs):
            if idx in used:
                continue
            row_type = row.get("unit_type") or ""
            if not row_type:
                continue
            r_bed, _ = cls._normalize_unit_key(row_type)
            if vp_bed == r_bed:
                return (idx, row)

        # Pass 4: numeric bedroom count fallback
        if vp.bedrooms is not None:
            for idx, row in enumerate(table_specs):
                if idx in used:
                    continue
                row_beds = row.get("bedrooms")
                if row_beds is not None and int(row_beds) == vp.bedrooms:
                    return (idx, row)

        return None

    # -----------------------------------------------------------------
    # Floor plan cropping (runs AFTER data extraction from full page)
    # -----------------------------------------------------------------

    async def crop_floor_plans(
        self, floor_plan_result: FloorPlanExtractionResult
    ) -> FloorPlanExtractionResult:
        """Crop floor plan diagrams from full-page images for website display.

        Groups floor plans by source image hash. When multiple plans share the
        same source (e.g. two floor plans on one page), uses a multi-bbox
        prompt to locate each individual plan. Single-plan pages use the
        standard single-bbox prompt.

        Fallbacks (image kept unchanged):
        - Confidence < 0.7
        - Bounding box covers >90% of image area (single-plan only)
        - Cropped result < MIN_CROP_DIMENSION px in either dimension
        - Vision API call fails
        """
        import asyncio
        from collections import defaultdict

        MAX_CONCURRENT = 5
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        cropped_count = 0
        skipped_count = 0

        # Group floor plans by source image hash.
        # Plans from the same PDF page share the same hash_value + image_bytes.
        groups: dict[str, list[FloorPlanData]] = defaultdict(list)
        skip_fps: list[FloorPlanData] = []
        for fp in floor_plan_result.floor_plans:
            if not fp.image_bytes or fp.is_duplicate:
                skip_fps.append(fp)
                continue
            groups[fp.hash_value].append(fp)

        skipped_count += len(skip_fps)

        async def _crop_single(fp: FloorPlanData) -> None:
            """Crop a single floor plan from its page image."""
            nonlocal cropped_count, skipped_count
            async with sem:
                try:
                    bbox_result = await self._detect_floor_plan_bbox(
                        fp.image_bytes
                    )
                except Exception as e:
                    logger.warning("Floor plan bbox detection failed: %s", e)
                    skipped_count += 1
                    return

                if not bbox_result or bbox_result.get("confidence", 0) < 0.7:
                    logger.info(
                        "Low confidence bbox (%.2f), keeping original for %s",
                        bbox_result.get("confidence", 0) if bbox_result else 0,
                        fp.unit_type or "unknown",
                    )
                    skipped_count += 1
                    return

                if not bbox_result.get("has_floor_plan", False):
                    skipped_count += 1
                    return

                bbox = bbox_result.get("bounding_box")
                if not bbox:
                    skipped_count += 1
                    return

                area_pct = (
                    bbox.get("width_percent", 0) * bbox.get("height_percent", 0)
                ) / 10000
                if area_pct > 0.90:
                    logger.info(
                        "Bbox covers %.0f%% of image for %s, skipping crop",
                        area_pct * 100, fp.unit_type or "unknown",
                    )
                    skipped_count += 1
                    return

                cropped_bytes = self._crop_region(fp.image_bytes, bbox)
                if cropped_bytes:
                    fp.image_bytes = cropped_bytes
                    cropped_count += 1
                else:
                    skipped_count += 1

        async def _crop_multi(fps: list[FloorPlanData]) -> None:
            """Crop multiple floor plans that share the same source page."""
            nonlocal cropped_count, skipped_count
            async with sem:
                unit_types = [fp.unit_type or f"Plan {i+1}" for i, fp in enumerate(fps)]
                try:
                    bboxes = await self._detect_multi_floor_plan_bboxes(
                        fps[0].image_bytes, unit_types
                    )
                except Exception as e:
                    logger.warning(
                        "Multi-plan bbox detection failed for %d plans: %s",
                        len(fps), e,
                    )
                    # Fallback: split image evenly
                    bboxes = self._generate_even_split_bboxes(len(fps))

                if not bboxes or len(bboxes) < len(fps):
                    logger.info(
                        "Multi-bbox returned %d boxes for %d plans, using even split",
                        len(bboxes) if bboxes else 0, len(fps),
                    )
                    bboxes = self._generate_even_split_bboxes(len(fps))

                # Match bboxes to floor plans by unit type label or position
                matched = self._match_bboxes_to_plans(fps, bboxes, unit_types)

                for fp, bbox in matched:
                    if not bbox:
                        skipped_count += 1
                        continue
                    cropped_bytes = self._crop_region(
                        fp.image_bytes, bbox, padding_pct=0.02
                    )
                    if cropped_bytes:
                        fp.image_bytes = cropped_bytes
                        cropped_count += 1
                    else:
                        skipped_count += 1

        tasks = []
        for hash_val, fps in groups.items():
            if len(fps) == 1:
                tasks.append(_crop_single(fps[0]))
            else:
                tasks.append(_crop_multi(fps))

        await asyncio.gather(*tasks)

        logger.info(
            "Floor plan cropping complete: %d cropped, %d skipped (of %d total)",
            cropped_count,
            skipped_count,
            len(floor_plan_result.floor_plans),
        )

        return floor_plan_result

    @staticmethod
    def _generate_even_split_bboxes(count: int) -> list[dict]:
        """Generate evenly split bounding boxes as fallback.

        Assumes floor plans are arranged left-to-right for 2 plans,
        or in a grid for more. Uses conservative margins.
        """
        if count == 2:
            return [
                {"label": "", "bounding_box": {
                    "x_percent": 2, "y_percent": 10,
                    "width_percent": 46, "height_percent": 80,
                }},
                {"label": "", "bounding_box": {
                    "x_percent": 52, "y_percent": 10,
                    "width_percent": 46, "height_percent": 80,
                }},
            ]
        if count == 3:
            return [
                {"label": "", "bounding_box": {
                    "x_percent": 1, "y_percent": 10,
                    "width_percent": 31, "height_percent": 80,
                }},
                {"label": "", "bounding_box": {
                    "x_percent": 34, "y_percent": 10,
                    "width_percent": 31, "height_percent": 80,
                }},
                {"label": "", "bounding_box": {
                    "x_percent": 67, "y_percent": 10,
                    "width_percent": 31, "height_percent": 80,
                }},
            ]
        # 4+: 2x2 grid
        bboxes = []
        cols = 2
        rows = (count + 1) // 2
        w = 46
        h = max(35, 80 // rows)
        for i in range(count):
            col = i % cols
            row = i // cols
            bboxes.append({"label": "", "bounding_box": {
                "x_percent": 2 + col * 50,
                "y_percent": 5 + row * (h + 5),
                "width_percent": w,
                "height_percent": h,
            }})
        return bboxes

    @staticmethod
    def _match_bboxes_to_plans(
        fps: list[FloorPlanData],
        bboxes: list[dict],
        unit_types: list[str],
    ) -> list[tuple[FloorPlanData, Optional[dict]]]:
        """Match detected bounding boxes to FloorPlanData instances.

        Strategy:
        1. Try exact label match (case-insensitive)
        2. Try substring match
        3. Fall back to spatial ordering (sort by x_percent)
        """
        result: list[tuple[FloorPlanData, Optional[dict]]] = []
        used_bbox_indices: set[int] = set()

        # Build normalized lookup
        bbox_labels = []
        for b in bboxes:
            label = (b.get("label") or "").strip().lower()
            bbox_labels.append(label)

        # Pass 1: exact match
        for fp in fps:
            fp_label = (fp.unit_type or "").strip().lower()
            matched_idx = None
            for i, bl in enumerate(bbox_labels):
                if i in used_bbox_indices:
                    continue
                if bl and fp_label and bl == fp_label:
                    matched_idx = i
                    break
            if matched_idx is not None:
                used_bbox_indices.add(matched_idx)
                result.append((fp, bboxes[matched_idx].get("bounding_box")))
            else:
                result.append((fp, None))  # placeholder

        # Pass 2: substring match for unmatched
        for idx, (fp, bbox) in enumerate(result):
            if bbox is not None:
                continue
            fp_label = (fp.unit_type or "").strip().lower()
            for i, bl in enumerate(bbox_labels):
                if i in used_bbox_indices:
                    continue
                if bl and fp_label and (bl in fp_label or fp_label in bl):
                    used_bbox_indices.add(i)
                    result[idx] = (fp, bboxes[i].get("bounding_box"))
                    break

        # Pass 3: spatial fallback -- sort remaining bboxes by x, assign in order
        unmatched_fp_indices = [i for i, (_, b) in enumerate(result) if b is None]
        unused_bbox_indices = sorted(
            [i for i in range(len(bboxes)) if i not in used_bbox_indices],
            key=lambda i: bboxes[i].get("bounding_box", {}).get("x_percent", 0),
        )

        for fp_idx, bbox_idx in zip(unmatched_fp_indices, unused_bbox_indices):
            fp = result[fp_idx][0]
            result[fp_idx] = (fp, bboxes[bbox_idx].get("bounding_box"))
            logger.info(
                "Matched '%s' to bbox at x=%.0f%% by spatial position",
                fp.unit_type or "unknown",
                bboxes[bbox_idx].get("bounding_box", {}).get("x_percent", 0),
            )

        return result

    async def _detect_floor_plan_bbox(
        self, image_bytes: bytes
    ) -> Optional[dict]:
        """Detect floor plan bounding box via Vision API.

        Returns dict with has_floor_plan, bounding_box, confidence keys,
        or None if detection fails.
        """
        optimized = create_llm_optimized(
            image_bytes, max_dim=1568, fmt="PNG", quality=100
        )
        img_bytes = optimized if optimized else image_bytes
        media_type = self._detect_media_type(img_bytes)

        try:
            response = await self._service.vision_completion(
                image_bytes=img_bytes,
                prompt=FLOOR_PLAN_CROP_PROMPT,
                media_type=media_type,
                max_tokens=400,
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)
            bbox = result.get("bounding_box") or {}
            logger.info(
                "Floor plan bbox: has=%s conf=%.2f x=%.0f%% y=%.0f%% w=%.0f%% h=%.0f%%",
                result.get("has_floor_plan"),
                result.get("confidence", 0),
                bbox.get("x_percent", 0),
                bbox.get("y_percent", 0),
                bbox.get("width_percent", 0),
                bbox.get("height_percent", 0),
            )
            return result

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.warning("Failed to parse floor plan bbox response: %s", e)
            return None
        except Exception as e:
            logger.warning("Floor plan bbox Vision API call failed: %s", e)
            return None

    async def _detect_multi_floor_plan_bboxes(
        self, image_bytes: bytes, unit_types: list[str]
    ) -> list[dict]:
        """Detect bounding boxes for multiple floor plans on the same page.

        Returns list of dicts, each with 'label' and 'bounding_box' keys.
        """
        optimized = create_llm_optimized(
            image_bytes, max_dim=1568, fmt="PNG", quality=100
        )
        img_bytes = optimized if optimized else image_bytes
        media_type = self._detect_media_type(img_bytes)

        unit_list = "\n".join(f"- {ut}" for ut in unit_types)
        prompt = FLOOR_PLAN_MULTI_CROP_PROMPT.format(
            count=len(unit_types), unit_types=unit_list
        )

        try:
            response = await self._service.vision_completion(
                image_bytes=img_bytes,
                prompt=prompt,
                media_type=media_type,
                max_tokens=800,
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)
            plans = result.get("floor_plans", [])

            for p in plans:
                bbox = p.get("bounding_box", {})
                logger.info(
                    "Multi-bbox: '%s' x=%.0f%% y=%.0f%% w=%.0f%% h=%.0f%%",
                    p.get("label", "?"),
                    bbox.get("x_percent", 0),
                    bbox.get("y_percent", 0),
                    bbox.get("width_percent", 0),
                    bbox.get("height_percent", 0),
                )

            return plans

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.warning(
                "Failed to parse multi-bbox response: %s", e
            )
            return []
        except Exception as e:
            logger.warning(
                "Multi-plan bbox Vision API call failed: %s", e
            )
            return []

    @staticmethod
    def _crop_region(
        image_bytes: bytes, bbox: dict, padding_pct: float = 0.04
    ) -> Optional[bytes]:
        """Crop a region from image bytes using percentage-based bounding box.

        Args:
            image_bytes: Source image bytes.
            bbox: Dict with x_percent, y_percent, width_percent, height_percent.
            padding_pct: Extra padding around the box (0.04 = 4%).

        Returns:
            Cropped image as PNG bytes, or None if crop is too small.
        """
        import io

        try:
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size

            x_pct = bbox.get("x_percent", 0) / 100
            y_pct = bbox.get("y_percent", 0) / 100
            w_pct = bbox.get("width_percent", 100) / 100
            h_pct = bbox.get("height_percent", 100) / 100

            # Apply padding
            x1 = max(0, int((x_pct - padding_pct) * w))
            y1 = max(0, int((y_pct - padding_pct) * h))
            x2 = min(w, int((x_pct + w_pct + padding_pct) * w))
            y2 = min(h, int((y_pct + h_pct + padding_pct) * h))

            crop_w = x2 - x1
            crop_h = y2 - y1

            if crop_w < MIN_CROP_DIMENSION or crop_h < MIN_CROP_DIMENSION:
                logger.info(
                    "Crop too small (%dx%d), keeping original", crop_w, crop_h
                )
                return None

            cropped = img.crop((x1, y1, x2, y2))
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            result = buf.getvalue()

            logger.info(
                "Cropped floor plan: %dx%d -> %dx%d (bbox %.0f%%,%.0f%% %.0f%%x%.0f%%) %d->%d bytes",
                w, h, crop_w, crop_h,
                x_pct * 100, y_pct * 100, w_pct * 100, h_pct * 100,
                len(image_bytes), len(result),
            )
            return result

        except Exception as e:
            logger.warning("Floor plan crop failed: %s", e)
            return None

    @staticmethod
    def _detect_media_type(image_bytes: bytes) -> str:
        """Detect MIME type from image bytes using magic-byte signatures."""
        # Check magic bytes instead of opening the full image with PIL (P3-12)
        if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        if image_bytes[:4] in (b"GIF8",):
            return "image/gif"
        if image_bytes[:4] == b"II\x2a\x00" or image_bytes[:4] == b"MM\x00\x2a":
            return "image/tiff"
        # Fallback
        return "image/png"
