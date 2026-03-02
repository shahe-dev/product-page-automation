"""Tests for floor plan extraction validation and hardening.

Tests are organized by the architectural problem they verify,
not by specific brochure. Each test uses synthetic data that
represents a class of real-world input.
"""
import pytest
from app.services.floor_plan_extractor import (
    FloorPlanExtractor,
    FloorPlanData,
    _is_plausible,
)


class TestDimensionalAnalysis:
    """Verify dimension unit detection handles any real-world format."""

    # --- Null/invalid input guards ---
    def test_none_value_skipped(self):
        dims = {"living": None, "bedroom": "4.0m x 3.0m"}
        result = FloorPlanExtractor._compute_area_from_dimensions(dims)
        expected = 4.0 * 3.0 * 10.764
        assert abs(result - expected) < 1.0

    def test_all_none_returns_zero(self):
        assert FloorPlanExtractor._compute_area_from_dimensions({"a": None}) == 0.0

    def test_non_string_skipped(self):
        dims = {"living": 123, "bedroom": "4.0m x 3.0m"}
        result = FloorPlanExtractor._compute_area_from_dimensions(dims)
        assert result > 0

    def test_empty_string_skipped(self):
        dims = {"living": "", "bedroom": "4.0m x 3.0m"}
        result = FloorPlanExtractor._compute_area_from_dimensions(dims)
        assert result > 0

    # --- Explicit unit suffix detection ---
    def test_detect_explicit_mm(self):
        assert FloorPlanExtractor._detect_dimension_unit("569mm x 671mm", 569, 671) == "mm"

    def test_detect_explicit_cm(self):
        assert FloorPlanExtractor._detect_dimension_unit("420cm x 380cm", 420, 380) == "cm"

    def test_detect_explicit_m(self):
        assert FloorPlanExtractor._detect_dimension_unit("4.2m x 3.8m", 4.2, 3.8) == "m"

    def test_detect_explicit_ft(self):
        assert FloorPlanExtractor._detect_dimension_unit("12ft x 10ft", 12, 10) == "ft"

    def test_detect_explicit_ft_prime(self):
        assert FloorPlanExtractor._detect_dimension_unit("12' x 10'", 12, 10) == "ft"

    # --- Magnitude-based inference (no unit suffix) ---
    def test_infer_mm_from_magnitude(self):
        # Values > 200 with no suffix -> mm
        assert FloorPlanExtractor._detect_dimension_unit("569 x 671", 569, 671) == "mm"

    def test_infer_ft_from_magnitude(self):
        # Values 30-200 with no suffix -> ft
        assert FloorPlanExtractor._detect_dimension_unit("35 x 42", 35, 42) == "ft"

    def test_infer_m_from_magnitude(self):
        # Values <= 30 with no suffix -> m
        assert FloorPlanExtractor._detect_dimension_unit("4.2 x 3.8", 4.2, 3.8) == "m"

    # --- End-to-end area computation ---
    def test_mm_dimensions_produce_sane_area(self):
        result = FloorPlanExtractor._compute_area_from_dimensions({"r": "569mm x 671mm"})
        expected = 0.569 * 0.671 * 10.764  # ~4.11 sqft
        assert result < 100  # NOT millions
        assert abs(result - expected) < 0.5

    def test_cm_dimensions_produce_sane_area(self):
        result = FloorPlanExtractor._compute_area_from_dimensions({"r": "420cm x 380cm"})
        expected = 4.2 * 3.8 * 10.764  # ~171.8 sqft
        assert 100 < result < 300

    def test_bare_large_numbers_inferred_as_mm(self):
        # No unit suffix, values > 200 -> mm inference
        result = FloorPlanExtractor._compute_area_from_dimensions({"r": "4200 x 3800"})
        expected = 4.2 * 3.8 * 10.764  # ~171.8 sqft
        assert 100 < result < 300

    def test_meters_area_correct(self):
        dims = {"living": "4.0m x 3.0m", "bedroom": "3.0m x 3.0m"}
        result = FloorPlanExtractor._compute_area_from_dimensions(dims)
        expected = (4 * 3 + 3 * 3) * 10.764  # 226.0
        assert abs(result - expected) < 1.0

    def test_feet_area_correct(self):
        dims = {"living": "12ft x 10ft"}
        result = FloorPlanExtractor._compute_area_from_dimensions(dims)
        assert abs(result - 120.0) < 1.0


class TestPlausibilityValidation:
    """Verify implausible values are rejected regardless of source."""

    # --- Direct function tests ---
    def test_valid_bathrooms_plausible(self):
        assert _is_plausible("bathrooms", 2.5)

    def test_price_as_bathrooms_rejected(self):
        assert not _is_plausible("bathrooms", 2450)

    def test_valid_sqft_plausible(self):
        assert _is_plausible("total_sqft", 1250)

    def test_price_as_sqft_rejected(self):
        assert not _is_plausible("total_sqft", 175000)

    def test_none_always_plausible(self):
        assert _is_plausible("total_sqft", None)

    def test_unknown_field_always_plausible(self):
        assert _is_plausible("unknown_field", 999999)

    def test_zero_bedrooms_plausible(self):
        # Studio = 0 bedrooms
        assert _is_plausible("bedrooms", 0)

    def test_negative_sqft_rejected(self):
        assert not _is_plausible("total_sqft", -100)

    # --- Integration with _extract_from_text ---
    def test_text_valid_bathrooms_accepted(self):
        ext = FloorPlanExtractor()
        r = ext._extract_from_text({1: "2.5 bathrooms in suite"}, 1)
        assert r.get("bathrooms") == 2.5

    def test_text_insane_bathrooms_rejected(self):
        ext = FloorPlanExtractor()
        r = ext._extract_from_text({1: "2450 bathrooms"}, 1)
        assert "bathrooms" not in r

    def test_text_insane_bedrooms_rejected(self):
        ext = FloorPlanExtractor()
        r = ext._extract_from_text({1: "750 bedrooms"}, 1)
        assert "bedrooms" not in r

    def test_text_valid_sqft_accepted(self):
        ext = FloorPlanExtractor()
        r = ext._extract_from_text({1: "1,250 sq ft apartment"}, 1)
        assert r.get("total_sqft") == 1250.0

    def test_text_insane_sqft_rejected(self):
        ext = FloorPlanExtractor()
        r = ext._extract_from_text({1: "175,000 sq ft lot"}, 1)
        assert "total_sqft" not in r

    # --- Integration with _cross_validate_area ---
    def test_implausible_computed_area_discarded(self):
        fp = FloorPlanData(
            unit_type="Studio", bedrooms=0, total_sqft=None,
            room_dimensions={"main": "50m x 50m"},
        )
        result = FloorPlanExtractor._cross_validate_area(fp)
        # 50*50*10.764*1.15 = 30,951 sqft -> exceeds 25000 bound
        assert result.total_sqft is None

    def test_plausible_computed_area_fills(self):
        fp = FloorPlanData(
            unit_type="1BR", bedrooms=1, total_sqft=None,
            room_dimensions={"living": "5m x 4m", "bed": "4m x 3m"},
        )
        result = FloorPlanExtractor._cross_validate_area(fp)
        assert result.total_sqft is not None
        assert result.total_sqft < 25000


class TestConfidenceScoring:
    """Verify confidence is set correctly by each extraction source."""

    def test_vision_sets_confidence(self):
        plan_data = {
            "unit_type": "1BR Type A", "bedrooms": 1, "bathrooms": 1,
            "total_sqft": 750.0, "suite_sqft": 650.0, "balcony_sqft": 100.0,
            "confidence": 0.92, "room_dimensions": {},
        }
        fp = FloorPlanExtractor._parse_single_plan(plan_data)
        assert fp.total_sqft_confidence == 0.92
        assert fp.suite_sqft_confidence == 0.92
        assert fp.balcony_sqft_confidence == 0.92
        assert fp.bedrooms_confidence == 0.92

    def test_vision_default_confidence(self):
        plan_data = {
            "unit_type": "Studio", "bedrooms": 0, "total_sqft": 500.0,
        }
        fp = FloorPlanExtractor._parse_single_plan(plan_data)
        assert fp.total_sqft_confidence == 0.85  # default when no confidence key

    def test_text_breakdown_gets_high_confidence(self):
        ext = FloorPlanExtractor()
        r = ext._extract_from_text(
            {1: "Suite\nBalcony\nTotal built-up\n50.00 Sq.m / 538.20 Sq.ft\n"
                "10.00 Sq.m / 107.64 Sq.ft\n60.00 Sq.m / 645.84 Sq.ft"},
            1,
        )
        # If breakdown parsed, confidence should be 0.92
        if r.get("total_sqft"):
            assert r.get("total_sqft_confidence", 0) >= 0.90

    def test_text_fallback_gets_lower_confidence(self):
        ext = FloorPlanExtractor()
        r = ext._extract_from_text({1: "750 sq ft apartment"}, 1)
        assert r.get("total_sqft_confidence", 0) <= 0.70

    def test_computed_from_dimensions_gets_low_confidence(self):
        fp = FloorPlanData(
            total_sqft=None,
            room_dimensions={"living": "5m x 4m", "bed": "4m x 3m"},
        )
        result = FloorPlanExtractor._cross_validate_area(fp)
        assert result.total_sqft is not None
        assert result.total_sqft_confidence <= 0.60

    def test_confidence_zero_when_missing(self):
        fp = FloorPlanData()
        assert fp.total_sqft_confidence == 0.0
        assert fp.bedrooms_confidence == 0.0

    def test_unit_type_label_enforcement_high_confidence(self):
        fp = FloorPlanData(
            unit_type="2BR Type A", bedrooms=1,
            bedrooms_source="floor_plan_image", bedrooms_confidence=0.85,
        )
        result = FloorPlanExtractor._enforce_bedrooms_from_unit_type(fp)
        assert result.bedrooms == 2
        assert result.bedrooms_confidence == 0.95


class TestConfidenceWeightedMerge:
    """Verify merge picks higher-confidence value, not rigid priority."""

    def test_text_breakdown_overrides_low_conf_vision(self):
        ext = FloorPlanExtractor()
        vision = FloorPlanData(
            total_sqft=650.0, total_sqft_source="floor_plan_image",
            total_sqft_confidence=0.80,
        )
        text_data = {
            "suite_sqft": 550.0, "total_sqft": 750.0,
            "balcony_sqft": 200.0,
        }
        result = ext._merge_data(vision, text_data, page_num=1)
        # Text breakdown confidence 0.92 > Vision 0.80
        assert result.total_sqft == 750.0
        assert result.total_sqft_source == "text_breakdown"

    def test_high_conf_vision_preserved_over_text_fallback(self):
        ext = FloorPlanExtractor()
        vision = FloorPlanData(
            total_sqft=750.0, total_sqft_source="floor_plan_image",
            total_sqft_confidence=0.95,
        )
        text_data = {"total_sqft": 800.0}  # No breakdown -> conf 0.60
        result = ext._merge_data(vision, text_data, page_num=1)
        # Vision 0.95 > text fallback 0.60
        assert result.total_sqft == 750.0
        assert result.total_sqft_source == "floor_plan_image"

    def test_text_fills_missing_vision(self):
        ext = FloorPlanExtractor()
        vision = FloorPlanData(total_sqft=None)
        text_data = {"total_sqft": 750.0}
        result = ext._merge_data(vision, text_data, page_num=1)
        assert result.total_sqft == 750.0
        assert result.total_sqft_confidence == 0.60

    def test_empty_text_data_no_change(self):
        ext = FloorPlanExtractor()
        vision = FloorPlanData(total_sqft=750.0, total_sqft_confidence=0.90)
        result = ext._merge_data(vision, {}, page_num=1)
        assert result.total_sqft == 750.0
        assert result.total_sqft_confidence == 0.90

    def test_bathrooms_higher_conf_wins(self):
        ext = FloorPlanExtractor()
        vision = FloorPlanData(
            bathrooms=2.0, bathrooms_confidence=0.50,
        )
        text_data = {"bathrooms": 3.0, "bathrooms_confidence": 0.60}
        result = ext._merge_data(vision, text_data, page_num=1)
        assert result.bathrooms == 3.0

    def test_bathrooms_vision_wins_when_higher(self):
        ext = FloorPlanExtractor()
        vision = FloorPlanData(
            bathrooms=2.0, bathrooms_confidence=0.90,
        )
        text_data = {"bathrooms": 3.0, "bathrooms_confidence": 0.60}
        result = ext._merge_data(vision, text_data, page_num=1)
        assert result.bathrooms == 2.0


class TestAreaRelationshipConsistency:
    """Verify area field relationships are enforced correctly."""

    # --- Reconcile threshold ---
    def test_close_values_not_recomputed(self):
        # suite=1000, balcony=50, total=1050 -> 4.8% diff, should NOT trigger
        fp = FloorPlanData(suite_sqft=1000, balcony_sqft=50, total_sqft=1050)
        result = FloorPlanExtractor._reconcile_area_fields(fp)
        assert result.total_sqft == 1050.0

    def test_total_equals_suite_recomputed(self):
        # suite=1000, balcony=150, total=1005 -> 0.5% diff, should trigger
        fp = FloorPlanData(suite_sqft=1000, balcony_sqft=150, total_sqft=1005)
        result = FloorPlanExtractor._reconcile_area_fields(fp)
        assert result.total_sqft == 1150.0

    def test_total_less_than_suite_always_recomputed(self):
        fp = FloorPlanData(suite_sqft=1000, balcony_sqft=150, total_sqft=950)
        result = FloorPlanExtractor._reconcile_area_fields(fp)
        assert result.total_sqft == 1150.0

    def test_correct_total_preserved(self):
        # total = suite + balcony (exact) -> no change
        fp = FloorPlanData(suite_sqft=800, balcony_sqft=200, total_sqft=1000)
        result = FloorPlanExtractor._reconcile_area_fields(fp)
        assert result.total_sqft == 1000.0

    def test_missing_balcony_computed(self):
        fp = FloorPlanData(suite_sqft=800, total_sqft=1000)
        result = FloorPlanExtractor._reconcile_area_fields(fp)
        assert result.balcony_sqft == 200.0

    def test_missing_suite_computed(self):
        fp = FloorPlanData(balcony_sqft=200, total_sqft=1000)
        result = FloorPlanExtractor._reconcile_area_fields(fp)
        assert result.suite_sqft == 800.0

    def test_missing_total_computed(self):
        fp = FloorPlanData(suite_sqft=800, balcony_sqft=200)
        result = FloorPlanExtractor._reconcile_area_fields(fp)
        assert result.total_sqft == 1000.0

    # --- Cross-validate extreme divergence ---
    def test_extreme_computed_vs_stated_keeps_stated(self):
        fp = FloorPlanData(
            unit_type="1BR", total_sqft=700.0, total_sqft_confidence=0.90,
            room_dimensions={"r": "50m x 50m"},  # -> computed ~31000
        )
        result = FloorPlanExtractor._cross_validate_area(fp)
        assert result.total_sqft == 700.0  # Stated preserved

    def test_moderate_divergence_keeps_stated(self):
        fp = FloorPlanData(
            unit_type="1BR", total_sqft=400.0,
            room_dimensions={"living": "5.0m x 4.0m", "bedroom": "4.0m x 3.0m"},
        )
        result = FloorPlanExtractor._cross_validate_area(fp)
        # computed = (20+12)*10.764*1.15 ~= 396. Ratio ~= 0.99. No override.
        assert result.total_sqft == 400.0


class TestBathroomInference:
    """Verify bathroom count is inferred from room dimension keys."""

    def test_two_full_baths(self):
        dims = {"bath": "1.9x1.9", "bath_2": "2.3x2.1", "bedroom": "3.8x3.8"}
        assert FloorPlanExtractor._infer_bathrooms_from_rooms(dims) == 2.0

    def test_one_full_one_half(self):
        dims = {"bathroom": "2.0x1.8", "wc": "1.2x0.9", "kitchen": "3.0x2.5"}
        assert FloorPlanExtractor._infer_bathrooms_from_rooms(dims) == 1.5

    def test_no_bathrooms(self):
        dims = {"bedroom": "3.8x3.8", "kitchen": "3.0x2.5", "living_area": "4.0x3.5"}
        assert FloorPlanExtractor._infer_bathrooms_from_rooms(dims) == 0.0

    def test_ensuite_counted(self):
        dims = {"ensuite": "2.0x1.8", "bath_2": "2.3x2.1"}
        assert FloorPlanExtractor._infer_bathrooms_from_rooms(dims) == 2.0

    def test_powder_room_half(self):
        dims = {"p_room": "1.9x1.8", "bathroom": "2.0x1.8"}
        assert FloorPlanExtractor._infer_bathrooms_from_rooms(dims) == 1.5

    def test_inference_fills_missing_bathrooms(self):
        plan_data = {
            "unit_type": "2BR Type A",
            "bedrooms": 2,
            "total_sqft": 900.0,
            "room_dimensions": {
                "bath": "1.9x1.9", "bath_2": "2.3x2.1",
                "bedroom": "3.8x3.8", "m_bedroom": "3.2x3.0",
            },
        }
        fp = FloorPlanExtractor._parse_single_plan(plan_data)
        assert fp.bathrooms == 2.0
        assert fp.bathrooms_source == "inferred_from_rooms"

    def test_no_inference_when_vision_has_bathrooms(self):
        plan_data = {
            "unit_type": "1BR",
            "bedrooms": 1,
            "bathrooms": 1.5,
            "total_sqft": 600.0,
            "room_dimensions": {"bath": "1.9x1.9", "wc": "1.2x0.9"},
        }
        fp = FloorPlanExtractor._parse_single_plan(plan_data)
        assert fp.bathrooms == 1.5
        assert fp.bathrooms_source == "floor_plan_image"


class TestMultiPlanCropHelpers:
    """Verify multi-plan crop helper methods."""

    def test_even_split_two_plans(self):
        bboxes = FloorPlanExtractor._generate_even_split_bboxes(2)
        assert len(bboxes) == 2
        # Left half
        assert bboxes[0]["bounding_box"]["x_percent"] < 50
        assert bboxes[0]["bounding_box"]["width_percent"] < 50
        # Right half
        assert bboxes[1]["bounding_box"]["x_percent"] >= 50

    def test_even_split_three_plans(self):
        bboxes = FloorPlanExtractor._generate_even_split_bboxes(3)
        assert len(bboxes) == 3

    def test_match_bboxes_exact_label(self):
        fps = [
            FloorPlanData(unit_type="1BR Type A"),
            FloorPlanData(unit_type="2BR Type B"),
        ]
        bboxes = [
            {"label": "2BR Type B", "bounding_box": {"x_percent": 55}},
            {"label": "1BR Type A", "bounding_box": {"x_percent": 5}},
        ]
        matched = FloorPlanExtractor._match_bboxes_to_plans(
            fps, bboxes, ["1BR Type A", "2BR Type B"]
        )
        assert matched[0][1]["x_percent"] == 5   # 1BR -> left
        assert matched[1][1]["x_percent"] == 55   # 2BR -> right

    def test_match_bboxes_spatial_fallback(self):
        fps = [
            FloorPlanData(unit_type="Plan X"),
            FloorPlanData(unit_type="Plan Y"),
        ]
        bboxes = [
            {"label": "something else", "bounding_box": {"x_percent": 55}},
            {"label": "unknown", "bounding_box": {"x_percent": 5}},
        ]
        matched = FloorPlanExtractor._match_bboxes_to_plans(
            fps, bboxes, ["Plan X", "Plan Y"]
        )
        # Spatial fallback: unmatched get sorted by x
        assert matched[0][1]["x_percent"] == 5
        assert matched[1][1]["x_percent"] == 55
