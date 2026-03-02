"""Layer 1: Text + regex extraction quality tests.

Tests PyMuPDF text extraction and FloorPlanExtractor regex parsing
against ground truth. No API calls -- fast, deterministic.

Run: pytest tests/quality/test_layer1_text.py -v
"""
import pytest

from app.services.floor_plan_extractor import FloorPlanExtractor

BROCHURE_KEYS = ["evelyn", "expo_valley", "hilton", "novayas", "sobha_eden"]


@pytest.mark.quality
@pytest.mark.parametrize("brochure_key", BROCHURE_KEYS)
class TestTextExtraction:
    """Validate text-based floor plan extraction against ground truth."""

    def test_floor_plan_pages_have_text(
        self, brochure_key, page_text_cache, ground_truth_cache
    ):
        """Pages identified as floor plan pages contain extractable text."""
        gt = ground_truth_cache(brochure_key)
        text_map = page_text_cache(brochure_key)
        fp_pages = gt.get("text_assertions", {}).get("pages_with_floor_plan_text", [])
        if not fp_pages:
            pytest.skip("No floor plan pages defined in ground truth")
        errors = []
        for page_num in fp_pages:
            if page_num not in text_map:
                errors.append(f"Page {page_num}: no extractable text")
            elif len(text_map[page_num]) < 20:
                errors.append(
                    f"Page {page_num}: text too short ({len(text_map[page_num])} chars)"
                )
        assert not errors, "\n".join(errors)

    def test_area_breakdown_parsing(
        self, brochure_key, page_text_cache, ground_truth_cache
    ):
        """_parse_area_breakdown finds suite/balcony/total from real page text."""
        gt = ground_truth_cache(brochure_key)
        if not gt.get("text_assertions", {}).get("expected_area_labels_present", False):
            pytest.skip("No area labels expected in text for this brochure")
        text_map = page_text_cache(brochure_key)
        fp_pages = gt.get("text_assertions", {}).get("pages_with_floor_plan_text", [])
        found_any = False
        errors = []
        for page_num in fp_pages:
            if page_num not in text_map:
                continue
            # Combine adjacent pages (same logic as _extract_from_text)
            combined = ""
            for p in [page_num - 1, page_num, page_num + 1]:
                if p in text_map:
                    combined += text_map[p] + "\n"
            breakdown = FloorPlanExtractor._parse_area_breakdown(combined)
            if breakdown:
                found_any = True
                total = breakdown.get("total_sqft", 0)
                suite = breakdown.get("suite_sqft", 0)
                if total and total > 0:
                    # Sanity: total should be a plausible sqft (100 - 50,000)
                    if total < 100 or total > 50000:
                        errors.append(
                            f"Page {page_num}: total_sqft={total} outside plausible range"
                        )
                if suite and total and suite > total:
                    errors.append(
                        f"Page {page_num}: suite_sqft ({suite}) > total_sqft ({total})"
                    )
        assert found_any, "No area breakdown found on any floor plan page"
        assert not errors, "\n".join(errors)

    def test_unit_type_regex(self, brochure_key, page_text_cache, ground_truth_cache):
        """_extract_from_text finds expected unit type patterns in real PDF text."""
        gt = ground_truth_cache(brochure_key)
        expected_types = (
            gt.get("text_assertions", {}).get("expected_unit_types_in_text", [])
        )
        if not expected_types:
            pytest.skip("No expected text unit types defined in ground truth")
        text_map = page_text_cache(brochure_key)
        extractor = FloorPlanExtractor()
        found_types = set()
        for page_num in text_map:
            result = extractor._extract_from_text(text_map, page_num)
            if result.get("unit_type"):
                found_types.add(result["unit_type"].upper())
        errors = []
        for expected in expected_types:
            normalized = expected.upper()
            if not any(
                normalized in ft or ft in normalized for ft in found_types
            ):
                errors.append(
                    f"Expected '{expected}' not found. Found types: {sorted(found_types)}"
                )
        assert not errors, "\n".join(errors)

    def test_no_phantom_prices_as_sqft(
        self, brochure_key, page_text_cache, ground_truth_cache
    ):
        """Text regex should not parse prices (>10000) as sqft values."""
        gt = ground_truth_cache(brochure_key)
        text_map = page_text_cache(brochure_key)
        fp_pages = gt.get("text_assertions", {}).get("pages_with_floor_plan_text", [])
        if not fp_pages:
            pytest.skip("No floor plan pages defined")
        extractor = FloorPlanExtractor()
        warnings = []
        for page_num in fp_pages:
            if page_num not in text_map:
                continue
            result = extractor._extract_from_text(text_map, page_num)
            total = result.get("total_sqft")
            # Floor plans are typically 200-10,000 sqft. Anything above 10,000
            # is likely a price (AED) being parsed as area.
            if total and total > 10000:
                warnings.append(
                    f"Page {page_num}: total_sqft={total} looks like a price, not area"
                )
            baths = result.get("bathrooms")
            if baths and baths > 20:
                warnings.append(
                    f"Page {page_num}: bathrooms={baths} looks like a price, not bath count"
                )
        # Plausibility validation should prevent all suspicious values.
        assert not warnings, (
            f"{len(warnings)} suspicious values found:\n"
            + "\n".join(warnings[:5])
        )
