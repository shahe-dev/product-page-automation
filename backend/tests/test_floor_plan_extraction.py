"""Tests for robust floor plan extraction with page render fallback."""

import io
import json

import pytest
from PIL import Image
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.enums import ImageCategory
from app.utils.image_validation import validate_image_bytes


def _make_valid_png(width=200, height=200, color="blue"):
    """Create valid PNG bytes for testing."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestFloorPlanPreservation:
    """Verify floor plan image bytes are preserved before memory release."""

    @pytest.mark.asyncio
    async def test_classify_step_preserves_floor_plan_images(self):
        """_step_classify_images stores floor plan images in ctx before release."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        valid_png = _make_valid_png()

        extraction = MagicMock()
        extraction.page_renders = [MagicMock() for _ in range(3)]
        for i, r in enumerate(extraction.page_renders):
            r.metadata.page_number = i + 21
            r.image_bytes = valid_png
            r.llm_optimized_bytes = b"optimized_" + str(i).encode()

        jm._pipeline_ctx[job_id] = {"extraction": extraction}

        mock_cls_result_fp = MagicMock()
        mock_cls_result_fp.category = ImageCategory.FLOOR_PLAN

        mock_cls_result_other = MagicMock()
        mock_cls_result_other.category = ImageCategory.EXTERIOR

        mock_output = MagicMock()
        mock_output.classified_images = [
            (extraction.page_renders[0], mock_cls_result_fp),
            (extraction.page_renders[1], mock_cls_result_fp),
            (extraction.page_renders[2], mock_cls_result_other),
        ]
        mock_output.total_input = 3
        mock_output.total_retained = 3
        mock_output.total_duplicates = 0
        mock_output.category_counts = {"floor_plan": 2, "exterior": 1}

        with patch("app.services.image_classifier.ImageClassifier") as MockIC:
            MockIC.return_value.classify_extraction = AsyncMock(
                return_value=mock_output
            )
            await jm._step_classify_images(job_id)

        assert "floor_plan_images" in jm._pipeline_ctx[job_id]
        preserved = jm._pipeline_ctx[job_id]["floor_plan_images"]
        assert len(preserved) == 2

    @pytest.mark.asyncio
    async def test_page_render_fallback_when_embedded_corrupt(self):
        """When embedded floor plan images are corrupt, page renders are used."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        valid_png = _make_valid_png()

        corrupt_image = MagicMock()
        corrupt_image.metadata.page_number = 21
        corrupt_image.metadata.source = "embedded"
        corrupt_image.image_bytes = b""
        corrupt_image.llm_optimized_bytes = None

        page_render = MagicMock()
        page_render.metadata.page_number = 21
        page_render.metadata.source = "page_render"
        page_render.image_bytes = valid_png
        page_render.llm_optimized_bytes = b"optimized_render"

        mock_cls_result = MagicMock()
        mock_cls_result.category = ImageCategory.FLOOR_PLAN

        extraction = MagicMock()
        extraction.page_renders = [page_render]

        mock_output = MagicMock()
        mock_output.classified_images = [(corrupt_image, mock_cls_result)]
        mock_output.total_input = 1
        mock_output.total_retained = 1
        mock_output.total_duplicates = 0
        mock_output.category_counts = {"floor_plan": 1}

        jm._pipeline_ctx[job_id] = {"extraction": extraction}

        with patch("app.services.image_classifier.ImageClassifier") as MockIC:
            MockIC.return_value.classify_extraction = AsyncMock(
                return_value=mock_output
            )
            with patch(
                "app.services.job_manager.validate_image_bytes",
                side_effect=lambda b: len(b) > 10,
            ):
                await jm._step_classify_images(job_id)

        preserved = jm._pipeline_ctx[job_id]["floor_plan_images"]
        assert len(preserved) == 1
        assert preserved[0].image_bytes == valid_png

    @pytest.mark.asyncio
    async def test_extract_floor_plans_uses_preserved_images(self):
        """_step_extract_floor_plans reads from ctx['floor_plan_images']."""
        from app.services.job_manager import JobManager
        from app.services.floor_plan_extractor import (
            FloorPlanExtractionResult,
            FloorPlanData,
        )

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        valid_png = _make_valid_png()

        preserved_img = MagicMock()
        preserved_img.metadata.page_number = 21
        preserved_img.image_bytes = valid_png
        preserved_img.llm_optimized_bytes = valid_png

        mock_result = FloorPlanExtractionResult(
            floor_plans=[FloorPlanData(unit_type="1BR", confidence=0.9)],
            total_input=1,
            total_extracted=1,
        )

        extraction = MagicMock()
        extraction.page_text_map = {}

        classification = MagicMock()
        classification.classified_images = []

        jm._pipeline_ctx[job_id] = {
            "extraction": extraction,
            "classification": classification,
            "floor_plan_images": [preserved_img],
        }

        with patch(
            "app.services.floor_plan_extractor.FloorPlanExtractor"
        ) as MockFPE:
            MockFPE.return_value.extract_floor_plans = AsyncMock(
                return_value=mock_result
            )
            MockFPE.return_value.merge_with_table_data = MagicMock(
                return_value=mock_result.floor_plans
            )
            result = await jm._step_extract_floor_plans(job_id)

        assert result["total_extracted"] == 1
        # Verify preserved images were passed to extractor
        call_args = MockFPE.return_value.extract_floor_plans.call_args
        passed_images = call_args[0][0]
        assert len(passed_images) == 1
        assert passed_images[0] is preserved_img


class TestFloorPlanByteFallback:
    """Verify FloorPlanExtractor handles released/corrupt bytes."""

    def test_phase0_rejects_empty_bytes(self):
        """Phase 0 rejects images with empty image_bytes."""
        assert not validate_image_bytes(b"")

    def test_phase0_accepts_valid_png(self):
        """Phase 0 accepts valid PNG bytes."""
        valid_png = _make_valid_png()
        assert validate_image_bytes(valid_png)

    @pytest.mark.asyncio
    async def test_extract_from_image_uses_llm_bytes_fallback(self):
        """_extract_from_image falls back to llm_optimized_bytes."""
        from app.services.floor_plan_extractor import FloorPlanExtractor

        valid_png = _make_valid_png()

        image = MagicMock()
        image.image_bytes = b""
        image.llm_optimized_bytes = valid_png
        image.metadata.page_number = 21

        extractor = FloorPlanExtractor.__new__(FloorPlanExtractor)
        extractor._service = MagicMock()
        extractor._model = "test-model"

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "floor_plans": [
                            {
                                "unit_type": "1BR",
                                "bedrooms": 1,
                                "total_sqft": 700,
                                "confidence": 0.9,
                            }
                        ]
                    }
                )
            )
        ]
        extractor._service.vision_completion = AsyncMock(
            return_value=mock_response
        )

        results = await extractor._extract_from_image(image)
        assert len(results) >= 1
        assert results[0].unit_type == "1BR"

    @pytest.mark.asyncio
    async def test_phase0_fallback_to_llm_optimized(self):
        """Phase 0 in extract_floor_plans accepts llm_optimized_bytes when image_bytes empty."""
        from app.services.floor_plan_extractor import FloorPlanExtractor

        valid_png = _make_valid_png()

        image = MagicMock()
        image.image_bytes = b""
        image.llm_optimized_bytes = valid_png
        image.metadata.page_number = 21

        extractor = FloorPlanExtractor.__new__(FloorPlanExtractor)
        extractor._service = MagicMock()
        extractor._model = "test-model"
        extractor._dedup = MagicMock()
        dedup_result = MagicMock()
        dedup_result.is_duplicate = False
        dedup_result.hash_value = "abc123"
        extractor._dedup.check_and_register = MagicMock(return_value=dedup_result)
        extractor._dedup.reset = MagicMock()

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "floor_plans": [
                            {"unit_type": "Studio", "confidence": 0.85}
                        ]
                    }
                )
            )
        ]
        extractor._service.vision_completion = AsyncMock(
            return_value=mock_response
        )

        result = await extractor.extract_floor_plans([image])
        assert result.total_extracted >= 1
        assert result.floor_plans[0].unit_type == "Studio"


class TestMultiPlanParsing:
    """Verify multi-plan response parsing."""

    def test_multi_plan_response_parsed(self):
        """Vision response with multiple floor plans is parsed correctly."""
        from app.services.floor_plan_extractor import FloorPlanExtractor

        extractor = FloorPlanExtractor.__new__(FloorPlanExtractor)
        extractor._service = MagicMock()

        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "floor_plans": [
                            {
                                "unit_type": "Studio",
                                "bedrooms": 0,
                                "total_sqft": 400,
                                "confidence": 0.9,
                            },
                            {
                                "unit_type": "1BR Type A",
                                "bedrooms": 1,
                                "total_sqft": 700,
                                "confidence": 0.85,
                            },
                            {
                                "unit_type": "2BR Type A",
                                "bedrooms": 2,
                                "total_sqft": 1100,
                                "confidence": 0.88,
                            },
                        ]
                    }
                )
            )
        ]

        results = extractor._parse_vision_response(response)
        assert len(results) == 3
        assert results[0].unit_type == "Studio"
        assert results[1].unit_type == "1BR Type A"
        assert results[2].bedrooms == 2

    def test_legacy_single_plan_backward_compat(self):
        """Old single-plan format still works."""
        from app.services.floor_plan_extractor import FloorPlanExtractor

        extractor = FloorPlanExtractor.__new__(FloorPlanExtractor)
        extractor._service = MagicMock()

        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "unit_type": "1BR",
                        "bedrooms": 1,
                        "total_sqft": 700,
                        "confidence": 0.9,
                    }
                )
            )
        ]

        results = extractor._parse_vision_response(response)
        assert len(results) == 1
        assert results[0].unit_type == "1BR"


class TestDimensionCrossValidation:
    """Verify dimension parsing and area cross-validation."""

    def test_parse_dimension_meters(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor

        assert FloorPlanExtractor._parse_dimension("4.2m x 3.8m") == (4.2, 3.8)
        assert FloorPlanExtractor._parse_dimension("4.2 x 3.8") == (4.2, 3.8)
        assert FloorPlanExtractor._parse_dimension("4.2M X 3.8M") == (4.2, 3.8)
        assert FloorPlanExtractor._parse_dimension("invalid") is None

    def test_parse_dimension_feet(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor

        assert FloorPlanExtractor._parse_dimension("12ft x 10ft") == (12.0, 10.0)
        assert FloorPlanExtractor._parse_dimension("12' x 10'") == (12.0, 10.0)

    def test_compute_area_from_dimensions(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor

        dims = {"living": "4.0m x 3.0m", "bedroom": "3.0m x 3.0m"}
        # (4*3 + 3*3) = 21 sqm * 10.764 = 226.0 sqft
        result = FloorPlanExtractor._compute_area_from_dimensions(dims)
        assert abs(result - 226.0) < 1.0

    def test_compute_area_feet_dimensions(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor

        dims = {"living": "12ft x 10ft"}
        # 12*10 = 120 sqft (already in feet)
        result = FloorPlanExtractor._compute_area_from_dimensions(dims)
        assert abs(result - 120.0) < 1.0

    def test_cross_validate_fills_missing_total(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(
            unit_type="1BR",
            total_sqft=None,
            room_dimensions={"living": "5.0m x 4.0m", "bedroom": "4.0m x 3.0m"},
        )
        result = FloorPlanExtractor._cross_validate_area(fp)
        assert result.total_sqft is not None
        assert result.total_sqft_source == "computed_from_dimensions"

    def test_cross_validate_passes_when_matching(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(
            unit_type="1BR",
            total_sqft=400.0,
            total_sqft_source="floor_plan_image",
            room_dimensions={"living": "5.0m x 4.0m", "bedroom": "4.0m x 3.0m"},
        )
        result = FloorPlanExtractor._cross_validate_area(fp)
        # Stated value kept when within reasonable range
        assert result.total_sqft == 400.0

    def test_cross_validate_no_dimensions(self):
        from app.services.floor_plan_extractor import FloorPlanExtractor, FloorPlanData

        fp = FloorPlanData(unit_type="1BR", total_sqft=500.0)
        result = FloorPlanExtractor._cross_validate_area(fp)
        assert result.total_sqft == 500.0


class TestStoreRoomDimensions:
    """Verify room dimensions stored in parsed_data JSONB."""

    @pytest.mark.asyncio
    async def test_create_image_records_populates_parsed_data(self):
        """_create_image_records populates parsed_data with room dimensions."""
        from app.services.job_manager import JobManager
        from app.services.floor_plan_extractor import (
            FloorPlanData,
            FloorPlanExtractionResult,
        )

        jm = JobManager.__new__(JobManager)
        jm.job_repo = MagicMock()
        jm.job_repo.db = MagicMock()

        added_records = []
        jm.job_repo.db.add = lambda r: added_records.append(r)
        jm.job_repo.db.flush = AsyncMock()

        project_id = uuid4()
        gcs_path = f"materials/{project_id}"

        fp_data = FloorPlanData(
            unit_type="2BR Type A",
            bedrooms=2,
            bathrooms=2,
            total_sqft=1250.0,
            balcony_sqft=150.0,
            builtup_sqft=1100.0,
            room_dimensions={"living": "4.2m x 3.8m", "bedroom_1": "3.5m x 3.2m"},
            features=["maid_room", "walk_in_closet"],
            confidence=0.92,
            total_sqft_source="floor_plan_image",
            unit_type_source="floor_plan_image",
        )

        manifest_entry = {
            "file_name": "fp_001.webp",
            "tier": "llm_optimized",
            "format": "webp",
            "category": "floor_plan",
            "width": 800,
            "height": 600,
            "file_size": 50000,
        }

        ctx = {
            "manifest": {"entries": [manifest_entry]},
            "floor_plans": FloorPlanExtractionResult(
                floor_plans=[fp_data],
                total_input=1,
                total_extracted=1,
            ),
        }

        await jm._create_image_records(project_id, gcs_path, ctx)

        fp_records = [
            r
            for r in added_records
            if hasattr(r, "unit_type")  # ProjectFloorPlan
        ]
        assert len(fp_records) == 1
        rec = fp_records[0]
        assert rec.balcony_sqft == 150.0
        assert rec.builtup_sqft == 1100.0
        assert rec.parsed_data is not None
        assert rec.parsed_data["room_dimensions"] == {
            "living": "4.2m x 3.8m",
            "bedroom_1": "3.5m x 3.2m",
        }
        assert rec.parsed_data["features"] == ["maid_room", "walk_in_closet"]
        assert rec.parsed_data["confidence"] == 0.92
