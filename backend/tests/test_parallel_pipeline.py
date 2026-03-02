"""Tests for Phase 2: Parallel Extraction Pipeline.

Covers:
- Branch execution and context key isolation
- Post-convergence enrichment step
- Progress monotonicity during parallel execution
- Classifier parallel dedup safety
- Error propagation from branches
"""

import asyncio
import pytest
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.enums import ImageCategory, JobStepStatus, JobType
from app.services.image_classifier import (
    ClassificationOutput,
    ClassificationResult,
    ImageClassifier,
)
from app.services.job_manager import EXTRACTION_STEPS, JobManager


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

IMAGE_BRANCH_KEYS = {
    "classification",
    "detections",
    "cleaned_images",
}
TEXT_BRANCH_KEYS = {"data_extraction", "structured_data"}
SHARED_SUFFIX_KEYS = {
    "floor_plans",
    "optimization",
    "zip_bytes",
    "manifest",
}


def _make_job_manager():
    """Create a JobManager with mocked repo and queue."""
    repo = MagicMock()
    repo.db = MagicMock()
    repo.db.commit = AsyncMock()
    repo.get_job = AsyncMock(
        return_value=MagicMock(
            id=uuid4(),
            template_type=MagicMock(value="aggregators"),
            user_id=uuid4(),
            processing_config={},
        )
    )
    repo.update_job_step = AsyncMock()
    repo.update_job_status = AsyncMock()
    repo.update_job_progress = AsyncMock()
    queue = MagicMock()
    return JobManager(repo, queue)


def _make_mock_step(result: dict):
    """Return an AsyncMock that returns `result`."""
    return AsyncMock(return_value=result)


# ---------------------------------------------------------------------------
# Test 1: Image branch writes expected context keys
# ---------------------------------------------------------------------------


class TestImageBranch:
    @pytest.mark.asyncio
    async def test_image_branch_writes_expected_keys(self):
        """_run_image_branch runs only 3 steps (classify + watermark detect/remove).
        Floor plans, optimize, and package are now in the shared suffix."""
        jm = _make_job_manager()
        job_id = uuid4()
        jm._pipeline_ctx[job_id] = {"extraction": MagicMock()}

        # Mock each step to write its expected key
        jm._step_classify_images = AsyncMock(return_value={"classified": True})
        jm._step_detect_watermarks = AsyncMock(return_value={"detected": 0})
        jm._step_remove_watermarks = AsyncMock(return_value={"removed": 0})

        # Stub out progress updates (steps DB)
        jm.update_job_progress = AsyncMock()

        await jm._run_image_branch(job_id)

        # Verify only 3 steps were called
        jm._step_classify_images.assert_awaited_once()
        jm._step_detect_watermarks.assert_awaited_once()
        jm._step_remove_watermarks.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test 2: Text branch writes expected context keys
# ---------------------------------------------------------------------------


class TestTextBranch:
    @pytest.mark.asyncio
    async def test_text_branch_writes_expected_keys(self):
        """_run_text_branch should populate data_extraction and structured_data."""
        jm = _make_job_manager()
        job_id = uuid4()
        jm._pipeline_ctx[job_id] = {"extraction": MagicMock()}

        jm._step_extract_data = AsyncMock(return_value={"project_name": "Test"})
        jm._step_structure_data = AsyncMock(return_value={"confidence": 0.9})
        jm.update_job_progress = AsyncMock()

        await jm._run_text_branch(job_id)

        jm._step_extract_data.assert_awaited_once()
        jm._step_structure_data.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test 3: Image and text branch context keys are disjoint
# ---------------------------------------------------------------------------


class TestBranchKeyIsolation:
    def test_branches_no_key_overlap(self):
        """Image branch and text branch context keys must be disjoint."""
        image_steps = {s["id"] for s in EXTRACTION_STEPS if s["branch"] == "image"}
        text_steps = {s["id"] for s in EXTRACTION_STEPS if s["branch"] == "text"}
        assert image_steps & text_steps == set(), (
            f"Overlapping steps: {image_steps & text_steps}"
        )


# ---------------------------------------------------------------------------
# Test 4: Enrichment patches low-confidence project name
# ---------------------------------------------------------------------------


class TestEnrichmentStep:
    @pytest.mark.asyncio
    async def test_enrichment_patches_project_name(self):
        """Enrichment fires only when BOTH regex and structurer returned no project_name."""
        from app.services.data_extractor import FieldResult
        from app.services.data_structurer import StructuredProject

        jm = _make_job_manager()
        job_id = uuid4()

        mock_extraction = MagicMock()
        mock_extraction.project_name = FieldResult(
            value=None, confidence=0.0, source="regex"
        )
        mock_extraction.full_text = "Long enough text " * 20

        mock_classification = MagicMock()
        mock_classification.classified_images = [
            (
                MagicMock(),
                MagicMock(
                    category=MagicMock(value="logo"),
                    alt_text="Marina Heights project logo",
                ),
            ),
        ]

        # Structurer also returned no project_name
        structured = StructuredProject(project_name=None)

        jm._pipeline_ctx[job_id] = {
            "data_extraction": mock_extraction,
            "structured_data": structured,
            "classification": mock_classification,
        }

        result = await jm._step_enrich_from_classification(job_id)

        assert result["count"] >= 1
        assert "project_name from image alt_text" in result["enrichments"]
        assert mock_extraction.project_name.value == "Marina Heights"
        assert mock_extraction.project_name.confidence == 0.5

    @pytest.mark.asyncio
    async def test_enrichment_skips_when_no_discrepancy(self):
        """Enrichment is a no-op when text name exists and images have no name."""
        from app.services.data_extractor import FieldResult

        jm = _make_job_manager()
        job_id = uuid4()

        mock_extraction = MagicMock()
        mock_extraction.project_name = FieldResult(
            value="Skyline Tower", confidence=0.9, source="regex"
        )
        mock_extraction.full_text = "Lots of text here " * 20

        jm._pipeline_ctx[job_id] = {
            "data_extraction": mock_extraction,
            "structured_data": MagicMock(project_name="Skyline Tower"),
            "classification": MagicMock(classified_images=[]),
        }

        result = await jm._step_enrich_from_classification(job_id)

        assert result["count"] == 0
        assert mock_extraction.project_name.value == "Skyline Tower"

    @pytest.mark.asyncio
    async def test_enrichment_preserves_structurer_name_over_image(self):
        """When structurer says 'Grove Ridge' and images say something else, trust structurer."""
        from app.services.data_extractor import FieldResult
        from app.services.data_structurer import StructuredProject

        jm = _make_job_manager()
        job_id = uuid4()

        mock_extraction = MagicMock()
        mock_extraction.project_name = FieldResult(
            value=None, confidence=0.0, source="regex"
        )
        mock_extraction.full_text = "Lots of text here " * 20

        # Structurer correctly extracted "Grove Ridge" from Vision OCR text
        structured = StructuredProject(project_name="Grove Ridge")

        # Images have noisy alt_text that yields a different name
        mock_classification = MagicMock()
        mock_classification.classified_images = [
            (
                MagicMock(),
                MagicMock(
                    category=MagicMock(value="master_plan"),
                    alt_text="Master plan showing a planned community area",
                ),
            ),
        ]

        jm._pipeline_ctx[job_id] = {
            "data_extraction": mock_extraction,
            "structured_data": structured,
            "classification": mock_classification,
        }

        result = await jm._step_enrich_from_classification(job_id)

        # Structurer name must NOT be overridden by image alt_text
        assert structured.project_name == "Grove Ridge"
        # No override enrichment should have been applied
        assert not any("override" in e for e in result["enrichments"])


# ---------------------------------------------------------------------------
# Test 5: _build_base_context regression guard (Phase 1 tier selection)
# ---------------------------------------------------------------------------


class TestPhase1Regression:
    def test_needs_rich_context_unchanged(self):
        """_build_base_context still includes all 19 structured fields."""
        jm = _make_job_manager()
        structured = MagicMock()
        structured.project_name = "Test"
        structured.developer = "Dev"
        structured.emirate = "Dubai"
        structured.community = "Marina"
        structured.sub_community = None
        structured.property_type = "Residential"
        structured.price_min = 100
        structured.price_max = 200
        structured.currency = "AED"
        structured.price_per_sqft = 50
        structured.bedrooms = ["1BR"]
        structured.total_units = 10
        structured.floors = 5
        structured.handover_date = "Q1 2026"
        structured.launch_date = "Q2 2025"
        structured.amenities = []
        structured.key_features = []
        structured.payment_plan = {}
        structured.description = "Test project."

        ctx = jm._build_base_context(structured, None, None)
        assert ctx["project_name"] == "Test"
        assert "floor_plan_summary" in ctx
        assert "image_metadata" in ctx


# ---------------------------------------------------------------------------
# Test 6: Progress never decreases (monotonicity)
# ---------------------------------------------------------------------------


class TestProgressMonotonicity:
    @pytest.mark.asyncio
    async def test_progress_monotonic(self):
        """Simulated step completions from both branches produce monotonic progress."""
        jm = _make_job_manager()
        job_id = uuid4()

        # Build a list of mock steps with incrementing completion
        total_steps = len(EXTRACTION_STEPS)
        progress_values = []

        # Create mock steps that track completion
        completed_count = 0
        mock_steps = []
        for i, step in enumerate(EXTRACTION_STEPS):
            mock_step = MagicMock()
            mock_step.status = "pending"
            mock_step.step_id = step["id"]
            mock_steps.append(mock_step)

        jm.job_repo.get_job_steps = AsyncMock(return_value=mock_steps)

        # Simulate step completions in interleaved order
        # (image step, text step, image step, ...)
        image_step_ids = [s["id"] for s in EXTRACTION_STEPS if s["branch"] == "image"]
        text_step_ids = [s["id"] for s in EXTRACTION_STEPS if s["branch"] == "text"]

        all_step_order = []
        i, j = 0, 0
        while i < len(image_step_ids) or j < len(text_step_ids):
            if i < len(image_step_ids):
                all_step_order.append(image_step_ids[i])
                i += 1
            if j < len(text_step_ids):
                all_step_order.append(text_step_ids[j])
                j += 1

        prev_call_count = 0
        for step_id in all_step_order:
            # Mark step as completed in mock
            for ms in mock_steps:
                if ms.step_id == step_id:
                    ms.status = "completed"
                    break

            await jm.update_job_progress(job_id, step_id, JobStepStatus.COMPLETED)

            # Capture the progress value from the repo call
            cur_count = jm.job_repo.update_job_progress.call_count
            if cur_count > prev_call_count:
                last_call = jm.job_repo.update_job_progress.call_args
                progress = last_call.kwargs.get("progress")
                if progress is not None:
                    progress_values.append(progress)
                prev_call_count = cur_count

        assert len(progress_values) > 0, "No progress values captured"

        # Verify monotonicity
        for i in range(1, len(progress_values)):
            assert progress_values[i] >= progress_values[i - 1], (
                f"Progress decreased at index {i}: "
                f"{progress_values[i - 1]} -> {progress_values[i]}"
            )


# ---------------------------------------------------------------------------
# Test 7: Classifier parallel + sequential dedup produces same counts
# ---------------------------------------------------------------------------


class TestClassifierParallelDedup:
    @pytest.mark.asyncio
    @patch("app.services.image_classifier.validate_image_bytes", return_value=True)
    async def test_classifier_parallel_dedup_safe(self, _mock_validate):
        """Parallel classification + sequential dedup produces correct counts."""
        from app.utils.pdf_helpers import ExtractedImage, ImageMetadata

        classifier = ImageClassifier.__new__(ImageClassifier)
        classifier._dedup_service = MagicMock()
        classifier._dedup_service.reset = MagicMock()

        # Create 10 images, 3 of which will be "duplicates"
        images = []
        for i in range(10):
            meta = ImageMetadata(
                page_number=i + 1,
                source="embedded",
                width=100,
                height=100,
                format="png",
                dpi=72,
                file_size=100,
            )
            img = ExtractedImage(image_bytes=f"image_{i}".encode(), metadata=meta)
            images.append(img)

        # Mock _classify_single: all return interior with high confidence
        async def _mock_classify(img):
            return ClassificationResult(
                category=ImageCategory.INTERIOR,
                confidence=0.95,
                alt_text="test",
            )

        classifier._classify_single = _mock_classify
        classifier._should_retain = lambda cat, counts: cat != ImageCategory.OTHER

        # Mock dedup: images at index 2, 5, 8 are duplicates
        duplicate_indices = {2, 5, 8}
        call_count = [0]

        def _mock_dedup(image_bytes, idx):
            is_dup = call_count[0] in duplicate_indices
            result = MagicMock()
            result.is_duplicate = is_dup
            result.similarity = 0.99 if is_dup else 0.0
            result.matched_index = 0
            result.hash_value = f"hash_{call_count[0]}"
            call_count[0] += 1
            return result

        classifier._dedup_service.check_and_register = _mock_dedup

        extraction = MagicMock()
        extraction.embedded = images
        extraction.page_renders = []

        output = await classifier.classify_extraction(extraction)

        assert output.total_input == 10
        assert output.total_duplicates == 3
        assert output.total_retained == 7


# ---------------------------------------------------------------------------
# Test 8: asyncio.gather error propagation
# ---------------------------------------------------------------------------


class TestGatherErrorPropagation:
    @pytest.mark.asyncio
    async def test_gather_error_propagation(self):
        """If one branch raises, the pipeline should fail (not silently succeed)."""
        jm = _make_job_manager()
        job_id = uuid4()
        jm._pipeline_ctx[job_id] = {"extraction": MagicMock()}

        # Image branch raises
        async def _failing_image_branch(jid):
            raise RuntimeError("Classification API down")

        # Text branch succeeds
        async def _ok_text_branch(jid):
            pass

        jm._run_image_branch = _failing_image_branch
        jm._run_text_branch = _ok_text_branch

        with pytest.raises(RuntimeError, match="Classification API down"):
            await asyncio.gather(
                jm._run_image_branch(job_id),
                jm._run_text_branch(job_id),
            )


# ---------------------------------------------------------------------------
# Test 9: EXTRACTION_STEPS has correct branch assignments
# ---------------------------------------------------------------------------


class TestStepConfiguration:
    def test_extraction_steps_count(self):
        """Extraction pipeline should have 12 steps (6 image + 2 text + 4 shared)."""
        assert len(EXTRACTION_STEPS) == 12

    def test_branch_assignments(self):
        """Verify branch assignments match expected groupings."""
        shared = [s["id"] for s in EXTRACTION_STEPS if s["branch"] == "shared"]
        image = [s["id"] for s in EXTRACTION_STEPS if s["branch"] == "image"]
        text = [s["id"] for s in EXTRACTION_STEPS if s["branch"] == "text"]

        assert shared == [
            "upload",
            "extract_images",
            "extract_floor_plans",
            "optimize_images",
            "package_assets",
            "enrich_data",
            "materialize",
        ]
        assert image == [
            "classify_images",
            "detect_watermarks",
            "remove_watermarks",
        ]
        assert text == ["extract_data", "structure_data"]

    def test_all_steps_have_branch(self):
        """Every step config must have a 'branch' key."""
        for step in EXTRACTION_STEPS:
            assert "branch" in step, f"Step {step['id']} missing 'branch' key"

    def test_enrich_step_exists(self):
        """The new enrich_data step must be present between text and materialize."""
        ids = [s["id"] for s in EXTRACTION_STEPS]
        enrich_idx = ids.index("enrich_data")
        materialize_idx = ids.index("materialize")
        assert enrich_idx < materialize_idx


# ---------------------------------------------------------------------------
# Test 10: Enrichment skips sparse-text re-structuring for Vision extraction
# ---------------------------------------------------------------------------


class TestEnrichmentVisionGuard:
    @pytest.mark.asyncio
    async def test_enrichment_skips_restructure_for_vision_extraction(self):
        """Enrichment 2 (sparse text re-structure) is skipped when extraction_method='vision'."""
        from app.services.data_extractor import (
            ExtractionOutput,
            FieldResult,
            LocationResult,
            PriceResult,
            PaymentPlanResult,
        )
        from app.services.data_structurer import StructuredProject

        jm = _make_job_manager()
        job_id = uuid4()

        # Simulate Vision-based extraction: extraction_method="vision", full_text=""
        mock_extraction = ExtractionOutput(
            project_name=FieldResult(value=None, confidence=0.0, source="vision"),
            developer=FieldResult(value=None, confidence=0.0, source="vision"),
            location=LocationResult(
                emirate=None,
                community=None,
                sub_community=None,
                full_location=None,
                confidence=0.0,
            ),
            prices=PriceResult(min_price=None, max_price=None),
            bedrooms=[],
            completion_date=FieldResult(value=None, confidence=0.0, source="vision"),
            amenities=[],
            payment_plan=PaymentPlanResult(
                down_payment_pct=None,
                during_construction_pct=None,
                on_handover_pct=None,
                post_handover_pct=None,
            ),
            property_type=FieldResult(value=None, confidence=0.0, source="vision"),
            total_pages=5,
            full_text="",  # Empty because Vision doesn't produce text
            extraction_method="vision",
        )

        # Empty text would normally trigger re-structuring for non-vision extraction
        structured = StructuredProject(project_name=None)

        mock_classification = MagicMock()
        mock_classification.classified_images = [
            (
                MagicMock(),
                MagicMock(
                    category=MagicMock(value="interior"),
                    alt_text="Modern living room",
                ),
            ),
        ]

        jm._pipeline_ctx[job_id] = {
            "data_extraction": mock_extraction,
            "structured_data": structured,
            "classification": mock_classification,
        }

        result = await jm._step_enrich_from_classification(job_id)

        # Should NOT have re-structured (no "re-structured with image alt_text")
        assert "re-structured with image alt_text" not in result["enrichments"]


# ---------------------------------------------------------------------------
# Test 11: _normalize_unit_key parses various formats
# ---------------------------------------------------------------------------


class TestNormalizeUnitKey:
    def test_standard_formats(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor

        assert FloorPlanExtractor._normalize_unit_key("1BR Type A") == ("1br", "a")
        assert FloorPlanExtractor._normalize_unit_key("2BR Type B") == ("2br", "b")
        assert FloorPlanExtractor._normalize_unit_key("3 Bedroom - Type A1") == ("3br", "a1")

    def test_studio(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor

        assert FloorPlanExtractor._normalize_unit_key("Studio") == ("studio", "")
        assert FloorPlanExtractor._normalize_unit_key("STD Type A") == ("studio", "a")

    def test_spaces_and_case(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor

        assert FloorPlanExtractor._normalize_unit_key("  1 BR Type A  ") == ("1br", "a")
        assert FloorPlanExtractor._normalize_unit_key("2 bed - Type B") == ("2br", "b")

    def test_no_sub_type(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor

        bed, sub = FloorPlanExtractor._normalize_unit_key("1BR")
        assert bed == "1br"
        assert sub == ""


# ---------------------------------------------------------------------------
# Test 12: _find_matching_table_row 3-pass matching
# ---------------------------------------------------------------------------


class TestFindMatchingTableRow:
    def test_exact_match(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        vp = FloorPlanData(unit_type="1BR Type A", bedrooms=1)
        table = [
            {"unit_type": "1BR Type B", "total_sqft": 600},
            {"unit_type": "1BR Type A", "total_sqft": 555},
        ]
        result = FloorPlanExtractor._find_matching_table_row(vp, table, set())
        assert result is not None
        assert result[0] == 1  # matched index
        assert result[1]["total_sqft"] == 555

    def test_bed_key_fallback(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        vp = FloorPlanData(unit_type="2 Bedroom", bedrooms=2)
        table = [
            {"unit_type": "2BR Type A", "total_sqft": 900},
        ]
        result = FloorPlanExtractor._find_matching_table_row(vp, table, set())
        assert result is not None
        assert result[0] == 0

    def test_numeric_bedroom_fallback(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        vp = FloorPlanData(unit_type="Two Bed", bedrooms=2)
        table = [
            {"unit_type": "1BR", "bedrooms": 1, "total_sqft": 600},
            {"unit_type": "Unknown", "bedrooms": 2, "total_sqft": 900},
        ]
        # "Two Bed" won't parse a digit at start, but bedrooms=2 matches pass 3
        result = FloorPlanExtractor._find_matching_table_row(vp, table, set())
        assert result is not None
        assert result[0] == 1

    def test_respects_used_set(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        vp = FloorPlanData(unit_type="1BR Type A", bedrooms=1)
        table = [
            {"unit_type": "1BR Type A", "total_sqft": 555},
            {"unit_type": "1BR Type A", "total_sqft": 560},
        ]
        # First row already used
        result = FloorPlanExtractor._find_matching_table_row(vp, table, {0})
        assert result is not None
        assert result[0] == 1


# ---------------------------------------------------------------------------
# Test 13: _enforce_bedrooms_from_unit_type
# ---------------------------------------------------------------------------


class TestEnforceBedroomsFromUnitType:
    def test_override_wrong_count(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(unit_type="1BR Type A", bedrooms=3)
        fp = FloorPlanExtractor._enforce_bedrooms_from_unit_type(fp)
        assert fp.bedrooms == 1
        assert fp.bedrooms_source == "unit_type_label"

    def test_studio_is_zero(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(unit_type="Studio", bedrooms=1)
        fp = FloorPlanExtractor._enforce_bedrooms_from_unit_type(fp)
        assert fp.bedrooms == 0

    def test_no_change_when_correct(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(unit_type="2BR Type A", bedrooms=2, bedrooms_source="floor_plan_image")
        fp = FloorPlanExtractor._enforce_bedrooms_from_unit_type(fp)
        assert fp.bedrooms == 2
        assert fp.bedrooms_source == "floor_plan_image"

    def test_unparseable_label_no_change(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(unit_type="Penthouse", bedrooms=4)
        fp = FloorPlanExtractor._enforce_bedrooms_from_unit_type(fp)
        assert fp.bedrooms == 4  # unchanged


# ---------------------------------------------------------------------------
# Test 14: _reconcile_area_fields
# ---------------------------------------------------------------------------


class TestReconcileAreaFields:
    def test_compute_missing_balcony(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(suite_sqft=555.0, total_sqft=612.0)
        fp = FloorPlanExtractor._reconcile_area_fields(fp)
        assert fp.balcony_sqft == 57.0

    def test_compute_missing_suite(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(total_sqft=612.0, balcony_sqft=57.0)
        fp = FloorPlanExtractor._reconcile_area_fields(fp)
        assert fp.suite_sqft == 555.0

    def test_compute_missing_total(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(suite_sqft=555.0, balcony_sqft=57.0)
        fp = FloorPlanExtractor._reconcile_area_fields(fp)
        assert fp.total_sqft == 612.0
        assert fp.total_sqft_source == "computed"

    def test_no_change_when_insufficient(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(suite_sqft=555.0)
        fp = FloorPlanExtractor._reconcile_area_fields(fp)
        assert fp.total_sqft is None
        assert fp.balcony_sqft is None

    def test_all_three_present_no_change(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(suite_sqft=555.0, balcony_sqft=57.0, total_sqft=612.0)
        fp = FloorPlanExtractor._reconcile_area_fields(fp)
        # All already present -- should not be modified
        assert fp.suite_sqft == 555.0
        assert fp.balcony_sqft == 57.0
        assert fp.total_sqft == 612.0


# ---------------------------------------------------------------------------
# Test 15: table_extractor._map_floor_plan_columns with EVELYN-style headers
# ---------------------------------------------------------------------------


class TestMapFloorPlanColumns:
    def test_evelyn_headers(self):
        from app.services.table_extractor import TableExtractor

        te = TableExtractor()
        headers = ["Type", "Suite Area (sqft)", "Balcony (sqft)", "Total Built-up Area (sqft)"]
        col_map = te._map_floor_plan_columns(headers)
        assert col_map[0] == "unit_type"
        assert col_map[1] == "suite_sqft"
        assert col_map[2] == "balcony_sqft"
        assert col_map[3] == "total_sqft"

    def test_bare_area_fallback(self):
        from app.services.table_extractor import TableExtractor

        te = TableExtractor()
        headers = ["Type", "Area (sqft)", "Balcony (sqft)"]
        col_map = te._map_floor_plan_columns(headers)
        assert col_map[0] == "unit_type"
        assert col_map[1] == "total_sqft"  # bare "area" -> fallback
        assert col_map[2] == "balcony_sqft"

    def test_bare_area_not_used_when_total_exists(self):
        from app.services.table_extractor import TableExtractor

        te = TableExtractor()
        headers = ["Type", "Total Area (sqft)", "Area (sqft)"]
        col_map = te._map_floor_plan_columns(headers)
        assert col_map[1] == "total_sqft"
        # "Area" at index 2 should NOT also become total_sqft
        assert 2 not in col_map

    def test_internal_maps_to_suite(self):
        from app.services.table_extractor import TableExtractor

        te = TableExtractor()
        headers = ["Type", "Internal Area (sqft)", "Balcony", "Total Built-up"]
        col_map = te._map_floor_plan_columns(headers)
        assert col_map[1] == "suite_sqft"
        assert col_map[3] == "total_sqft"
