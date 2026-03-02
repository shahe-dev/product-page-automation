"""Layer 2: Full floor plan extraction quality tests.

Runs the complete extraction pipeline (PDF processing, classification,
Vision OCR, table merge) on real brochures and validates against ground truth.

Requires Anthropic API key. Marked with @pytest.mark.live.

Run: pytest tests/quality/test_layer2_extraction.py -v -m live --no-cov
Run single brochure: pytest tests/quality/test_layer2_extraction.py -v -m live -k novayas --no-cov
"""
import io
import logging

import pytest
from PIL import Image

from app.models.enums import ImageCategory
from app.services.floor_plan_extractor import FloorPlanExtractor
from app.services.image_classifier import ImageClassifier
from app.services.pdf_processor import PDFProcessor
from app.services.table_extractor import TableExtractor
from app.utils.image_validation import validate_image_bytes

logger = logging.getLogger(__name__)

# Exclude Hilton from default parametrized runs (117 MB, very slow)
FAST_KEYS = ["evelyn", "expo_valley", "novayas", "sobha_eden"]


async def _run_full_extraction(pdf_bytes: bytes) -> dict:
    """Run the complete floor plan extraction pipeline on raw PDF bytes.

    Replicates the job_manager pipeline steps:
      extract_all -> classify -> preserve fp images -> extract_floor_plans -> merge
    """
    processor = PDFProcessor()
    extraction = await processor.extract_all(pdf_bytes)
    logger.info(
        "PDF processed: %d embedded, %d renders, %d pages with text",
        len(extraction.embedded),
        len(extraction.page_renders),
        len(extraction.page_text_map),
    )

    classifier = ImageClassifier()
    classification = await classifier.classify_extraction(extraction)
    logger.info(
        "Classified: %d input, %d retained, categories: %s",
        classification.total_input,
        classification.total_retained,
        classification.category_counts,
    )

    # Preserve floor plan images (replicates job_manager lines 1788-1820)
    fp_images = []
    for image, cls_result in classification.classified_images:
        if cls_result.category == ImageCategory.FLOOR_PLAN:
            eff = image.image_bytes or image.llm_optimized_bytes
            if eff and validate_image_bytes(eff):
                fp_images.append(image)

    # Fallback to page renders if embedded images are corrupt
    if not fp_images:
        fp_pages = {
            img.metadata.page_number
            for img, cr in classification.classified_images
            if cr.category == ImageCategory.FLOOR_PLAN
        }
        if fp_pages and hasattr(extraction, "page_renders"):
            for render in extraction.page_renders:
                if render.metadata.page_number in fp_pages:
                    eff = render.image_bytes or render.llm_optimized_bytes
                    if eff and validate_image_bytes(eff):
                        fp_images.append(render)
            if fp_images:
                logger.info(
                    "Floor plan fallback: %d page renders for pages %s",
                    len(fp_images), sorted(fp_pages),
                )

    logger.info("Floor plan images: %d", len(fp_images))

    extractor = FloorPlanExtractor()
    fp_result = await extractor.extract_floor_plans(
        fp_images, extraction.page_text_map
    )
    logger.info(
        "Extracted: %d plans, %d duplicates, %d errors",
        fp_result.total_extracted,
        fp_result.total_duplicates,
        len(fp_result.errors),
    )

    table_result = TableExtractor().extract_tables(pdf_bytes)
    if table_result.floor_plan_specs:
        merged = extractor.merge_with_table_data(
            fp_result.floor_plans, table_result.floor_plan_specs
        )
        logger.info(
            "Merged with %d table specs -> %d final plans",
            len(table_result.floor_plan_specs), len(merged),
        )
    else:
        merged = fp_result.floor_plans

    return {
        "classification": classification,
        "fp_images": fp_images,
        "fp_result": fp_result,
        "table_result": table_result,
        "merged": merged,
    }


# Session-scoped extraction cache to avoid re-running expensive API calls
# when multiple test methods run for the same brochure.
_extraction_cache: dict[str, dict] = {}


@pytest.fixture(scope="session")
def extraction_cache(pdf_bytes_cache):
    """Cache full extraction results per brochure across the test session."""

    async def _get(key: str) -> dict:
        if key not in _extraction_cache:
            logger.info("Running full extraction for %s (not cached)", key)
            pdf_bytes = pdf_bytes_cache(key)
            _extraction_cache[key] = await _run_full_extraction(pdf_bytes)
        return _extraction_cache[key]

    return _get


def _find_merged_by_key(merged_list, target_key):
    """Find a FloorPlanData in merged list matching the normalized unit key."""
    for fp in merged_list:
        if FloorPlanExtractor._normalize_unit_key(fp.unit_type or "") == target_key:
            return fp
    return None


@pytest.mark.quality
@pytest.mark.live
@pytest.mark.parametrize("brochure_key", FAST_KEYS)
class TestFullExtraction:
    """Full floor plan extraction with Vision API -- validates against ground truth."""

    @pytest.mark.timeout(300)
    async def test_plan_count(self, brochure_key, extraction_cache, ground_truth_cache):
        """Extraction produces expected number of unique floor plans."""
        gt = ground_truth_cache(brochure_key)
        expected = gt.get("total_unique_plans", 0)
        if expected == 0:
            pytest.skip("No floor plans defined in ground truth yet (needs full API run)")
        result = await extraction_cache(brochure_key)
        tolerance = gt.get("total_unique_plans_tolerance", 1)
        actual = len(result["merged"])
        assert abs(actual - expected) <= tolerance, (
            f"Expected {expected} +/- {tolerance} plans, got {actual}. "
            f"Types found: {[fp.unit_type for fp in result['merged']]}"
        )

    @pytest.mark.timeout(300)
    async def test_unit_types_match(self, brochure_key, extraction_cache, ground_truth_cache):
        """All expected unit types are found in merged results."""
        gt = ground_truth_cache(brochure_key)
        gt_fps = gt.get("floor_plans", [])
        if not gt_fps:
            pytest.skip("No floor plans defined in ground truth yet")
        result = await extraction_cache(brochure_key)
        extracted_keys = {
            FloorPlanExtractor._normalize_unit_key(fp.unit_type or "")
            for fp in result["merged"]
            if fp.unit_type
        }
        errors = []
        for gt_fp in gt_fps:
            gt_key = FloorPlanExtractor._normalize_unit_key(gt_fp["unit_type"])
            if gt_key not in extracted_keys:
                errors.append(f"Missing: {gt_fp['unit_type']} (key: {gt_key})")
        assert not errors, (
            "\n".join(errors) + f"\nFound: {sorted(extracted_keys)}"
        )

    @pytest.mark.timeout(300)
    async def test_area_accuracy(self, brochure_key, extraction_cache, ground_truth_cache):
        """Area values match ground truth within tolerance."""
        gt = ground_truth_cache(brochure_key)
        gt_fps = gt.get("floor_plans", [])
        if not gt_fps:
            pytest.skip("No floor plans defined in ground truth yet")
        result = await extraction_cache(brochure_key)
        tol_pct = gt.get("tolerances", {}).get("sqft_pct", 2.0) / 100
        bal_tol = gt.get("tolerances", {}).get("balcony_sqft_pct", 5.0) / 100
        errors = []
        for gt_fp in gt_fps:
            gt_key = FloorPlanExtractor._normalize_unit_key(gt_fp["unit_type"])
            matched = _find_merged_by_key(result["merged"], gt_key)
            if matched is None:
                continue  # covered by test_unit_types_match
            for field, tolerance in [
                ("total_sqft", tol_pct),
                ("suite_sqft", tol_pct),
                ("balcony_sqft", bal_tol),
            ]:
                expected = gt_fp.get(field)
                actual = getattr(matched, field, None)
                if expected and actual and expected > 0:
                    diff_pct = abs(actual - expected) / expected
                    if diff_pct >= tolerance:
                        source = getattr(matched, field + "_source", "?")
                        errors.append(
                            f"{field} for {gt_fp['unit_type']}: "
                            f"expected {expected}, got {actual} "
                            f"(diff {diff_pct*100:.1f}%, source: {source})"
                        )
        assert not errors, "\n".join(errors)

    @pytest.mark.timeout(300)
    async def test_bedroom_counts(self, brochure_key, extraction_cache, ground_truth_cache):
        """Bedroom counts are exact matches."""
        gt = ground_truth_cache(brochure_key)
        gt_fps = gt.get("floor_plans", [])
        if not gt_fps:
            pytest.skip("No floor plans defined in ground truth yet")
        result = await extraction_cache(brochure_key)
        errors = []
        for gt_fp in gt_fps:
            gt_key = FloorPlanExtractor._normalize_unit_key(gt_fp["unit_type"])
            matched = _find_merged_by_key(result["merged"], gt_key)
            if matched is None:
                continue
            exp_beds = gt_fp.get("bedrooms")
            act_beds = matched.bedrooms
            if exp_beds is not None and act_beds is not None and exp_beds != act_beds:
                errors.append(
                    f"{gt_fp['unit_type']}: expected {exp_beds} bedrooms, got {act_beds}"
                )
        assert not errors, "\n".join(errors)

    @pytest.mark.timeout(300)
    async def test_images_valid(self, brochure_key, extraction_cache, ground_truth_cache):
        """All extracted floor plan images are valid with reasonable dimensions."""
        gt = ground_truth_cache(brochure_key)
        # This test runs even without full ground truth
        result = await extraction_cache(brochure_key)
        if not result["merged"]:
            pytest.skip("No floor plans extracted")
        errors = []
        for i, fp in enumerate(result["merged"]):
            label = f"Plan {i+1} ({fp.unit_type or '?'})"
            if not fp.image_bytes:
                errors.append(f"{label}: no image bytes")
                continue
            if not validate_image_bytes(fp.image_bytes):
                errors.append(f"{label}: invalid image data")
                continue
            img = Image.open(io.BytesIO(fp.image_bytes))
            w, h = img.size
            if w < 200 or h < 200:
                errors.append(f"{label}: too small ({w}x{h})")
            if w > 10000 or h > 10000:
                errors.append(f"{label}: suspiciously large ({w}x{h})")
        assert not errors, "\n".join(errors)

    @pytest.mark.timeout(300)
    async def test_confidence_above_threshold(
        self, brochure_key, extraction_cache, ground_truth_cache
    ):
        """All floor plans have confidence above minimum threshold."""
        gt = ground_truth_cache(brochure_key)
        result = await extraction_cache(brochure_key)
        if not result["merged"]:
            pytest.skip("No floor plans extracted")
        min_conf = 0.5
        low_conf = [
            f"{fp.unit_type}: {fp.confidence:.2f}"
            for fp in result["merged"]
            if fp.confidence < min_conf
        ]
        assert not low_conf, (
            f"Floor plans below {min_conf} confidence:\n" + "\n".join(low_conf)
        )

    @pytest.mark.timeout(300)
    async def test_classification_floor_plan_count(
        self, brochure_key, extraction_cache, ground_truth_cache
    ):
        """Classifier identifies at least the minimum expected floor plan images."""
        gt = ground_truth_cache(brochure_key)
        min_expected = gt.get("classification", {}).get("min_floor_plan_images", 1)
        result = await extraction_cache(brochure_key)
        actual = len(result["fp_images"])
        assert actual >= min_expected, (
            f"Expected >= {min_expected} floor plan images, got {actual}"
        )

    @pytest.mark.timeout(300)
    async def test_no_phantom_plans(self, brochure_key, extraction_cache, ground_truth_cache):
        """No hallucinated floor plans beyond ground truth + tolerance."""
        gt = ground_truth_cache(brochure_key)
        expected = gt.get("total_unique_plans", 0)
        if expected == 0:
            pytest.skip("No floor plans defined in ground truth yet")
        result = await extraction_cache(brochure_key)
        tolerance = gt.get("total_unique_plans_tolerance", 1)
        actual = len(result["merged"])
        assert actual <= expected + tolerance, (
            f"Too many plans: expected at most {expected + tolerance}, got {actual}. "
            f"Possible phantoms: {[fp.unit_type for fp in result['merged']]}"
        )


@pytest.mark.quality
@pytest.mark.live
@pytest.mark.slow
class TestHiltonExtraction:
    """Separate tests for Hilton (117 MB, requires extra time)."""

    @pytest.mark.timeout(600)
    async def test_hilton_extraction_completes(self, extraction_cache, ground_truth_cache):
        """Hilton extraction completes without errors."""
        ground_truth_cache("hilton")  # ensure GT exists
        result = await extraction_cache("hilton")
        assert len(result["merged"]) > 0, "No floor plans extracted from Hilton"
        assert len(result["fp_result"].errors) == 0, (
            f"Errors: {result['fp_result'].errors}"
        )

    @pytest.mark.timeout(600)
    async def test_hilton_images_valid(self, extraction_cache, ground_truth_cache):
        """All Hilton floor plan images are valid."""
        ground_truth_cache("hilton")
        result = await extraction_cache("hilton")
        for i, fp in enumerate(result["merged"]):
            label = f"Plan {i+1} ({fp.unit_type or '?'})"
            assert fp.image_bytes, f"{label}: no image bytes"
            assert validate_image_bytes(fp.image_bytes), f"{label}: invalid image"
