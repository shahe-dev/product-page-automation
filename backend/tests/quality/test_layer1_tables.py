"""Layer 1: Table extraction quality tests.

Tests pdfplumber table extraction against ground truth.
No API calls -- fast, deterministic, runs in seconds.

Run: pytest tests/quality/test_layer1_tables.py -v
"""
import pytest

from app.services.floor_plan_extractor import FloorPlanExtractor
from app.services.table_extractor import TableExtractor

BROCHURE_KEYS = ["evelyn", "expo_valley", "hilton", "novayas", "sobha_eden"]


def _find_spec_by_key(specs: list[dict], target_key: tuple) -> dict | None:
    """Find a table spec matching the normalized unit key."""
    for s in specs:
        if FloorPlanExtractor._normalize_unit_key(s.get("unit_type", "")) == target_key:
            return s
    return None


@pytest.mark.quality
@pytest.mark.parametrize("brochure_key", BROCHURE_KEYS)
class TestTableExtraction:
    """Validate pdfplumber floor plan table extraction against ground truth."""

    def test_spec_count(self, brochure_key, pdf_bytes_cache, ground_truth_cache):
        """pdfplumber finds the expected number of floor plan specs."""
        gt = ground_truth_cache(brochure_key)
        result = TableExtractor().extract_tables(pdf_bytes_cache(brochure_key))
        expected = gt["table_spec_count"]
        tolerance = gt.get("table_spec_count_tolerance", 0)
        actual = len(result.floor_plan_specs)
        assert abs(actual - expected) <= tolerance, (
            f"Expected {expected} +/- {tolerance} table specs, got {actual}"
        )

    def test_unit_types_found(self, brochure_key, pdf_bytes_cache, ground_truth_cache):
        """All expected unit types appear in table specs (normalized match)."""
        gt = ground_truth_cache(brochure_key)
        gt_specs = gt.get("table_specs", [])
        if not gt_specs:
            pytest.skip("No table specs in ground truth")
        result = TableExtractor().extract_tables(pdf_bytes_cache(brochure_key))
        extracted_keys = {
            FloorPlanExtractor._normalize_unit_key(s.get("unit_type", ""))
            for s in result.floor_plan_specs
            if s.get("unit_type")
        }
        for gt_spec in gt_specs:
            gt_key = FloorPlanExtractor._normalize_unit_key(gt_spec["unit_type"])
            assert gt_key in extracted_keys, (
                f"Missing: {gt_spec['unit_type']} (key: {gt_key}). "
                f"Found: {extracted_keys}"
            )

    def test_area_values_within_tolerance(self, brochure_key, pdf_bytes_cache, ground_truth_cache):
        """Numeric area values from tables match ground truth within tolerance."""
        gt = ground_truth_cache(brochure_key)
        gt_specs = gt.get("table_specs", [])
        if not gt_specs:
            pytest.skip("No table specs in ground truth")
        result = TableExtractor().extract_tables(pdf_bytes_cache(brochure_key))
        tol = gt.get("tolerances", {}).get("sqft_pct", 2.0) / 100
        errors = []
        for gt_spec in gt_specs:
            gt_key = FloorPlanExtractor._normalize_unit_key(gt_spec["unit_type"])
            matched = _find_spec_by_key(result.floor_plan_specs, gt_key)
            if matched is None:
                continue  # covered by test_unit_types_found
            for field in ["total_sqft", "suite_sqft", "balcony_sqft"]:
                expected = gt_spec.get(field)
                actual = matched.get(field)
                if expected is not None and actual is not None and expected > 0:
                    diff_pct = abs(actual - expected) / expected
                    if diff_pct >= tol:
                        errors.append(
                            f"{field} for {gt_spec['unit_type']}: "
                            f"expected {expected}, got {actual} "
                            f"(diff {diff_pct*100:.1f}%, tol {tol*100:.1f}%)"
                        )
        assert not errors, "\n".join(errors)

    def test_bedroom_counts_exact(self, brochure_key, pdf_bytes_cache, ground_truth_cache):
        """Bedroom counts from tables match exactly."""
        gt = ground_truth_cache(brochure_key)
        gt_specs = gt.get("table_specs", [])
        if not gt_specs:
            pytest.skip("No table specs in ground truth")
        result = TableExtractor().extract_tables(pdf_bytes_cache(brochure_key))
        errors = []
        for gt_spec in gt_specs:
            gt_key = FloorPlanExtractor._normalize_unit_key(gt_spec["unit_type"])
            matched = _find_spec_by_key(result.floor_plan_specs, gt_key)
            if matched is None:
                continue
            expected_beds = gt_spec.get("bedrooms")
            actual_beds = matched.get("bedrooms")
            if expected_beds is not None and actual_beds is not None:
                if actual_beds != expected_beds:
                    errors.append(
                        f"{gt_spec['unit_type']}: "
                        f"expected {expected_beds} bedrooms, got {actual_beds}"
                    )
        assert not errors, "\n".join(errors)

    def test_no_extraction_errors(self, brochure_key, pdf_bytes_cache, ground_truth_cache):
        """Table extraction produces no errors."""
        ground_truth_cache(brochure_key)  # ensure GT exists (triggers skip if not)
        result = TableExtractor().extract_tables(pdf_bytes_cache(brochure_key))
        assert len(result.errors) == 0, f"Errors: {result.errors}"
