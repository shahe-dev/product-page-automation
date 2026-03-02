"""Tests for hybrid extraction pipeline wiring in job_manager."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestHybridExtractionWiring:
    """Verify that _step_extract_data feeds native text + tables + regex into structuring."""

    @pytest.mark.asyncio
    async def test_step_extract_data_passes_routing_params(self):
        """_step_extract_data passes page_text_map and page_char_counts to VisionExtractor."""
        from app.services.job_manager import JobManager
        from app.services.vision_extractor import PageExtractionResult

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        # Mock extraction result with native text
        extraction = MagicMock()
        extraction.page_renders = [MagicMock()]
        extraction.page_renders[0].metadata.page_number = 1
        extraction.page_text_map = {1: "EVELYN on the Park by Nshama"}
        extraction.page_char_counts = {1: 500}

        jm._pipeline_ctx[job_id] = {"extraction": extraction}

        # Patch at source module -- _step_extract_data uses local import
        with patch("app.services.vision_extractor.VisionExtractor") as MockVE:
            mock_ve = MockVE.return_value
            mock_ve.extract_pages = AsyncMock(return_value=[
                PageExtractionResult(
                    page_number=1,
                    raw_text="EVELYN on the Park by Nshama",
                    cost=0.0,
                )
            ])
            # concatenate_page_text is a staticmethod called on the class
            MockVE.concatenate_page_text = MagicMock(
                return_value="EVELYN on the Park by Nshama"
            )

            result = await jm._step_extract_data(job_id)

        # Verify extract_pages was called with page routing params
        call_kwargs = mock_ve.extract_pages.call_args.kwargs
        assert "page_text_map" in call_kwargs
        assert "page_char_counts" in call_kwargs
        assert call_kwargs["page_text_map"] == {1: "EVELYN on the Park by Nshama"}
        assert call_kwargs["page_char_counts"] == {1: 500}
        assert result["text_rich_pages"] == 1
        assert result["confidence_profile"] == "high"

    @pytest.mark.asyncio
    async def test_step_structure_data_runs_regex_and_structurer(self):
        """_step_structure_data runs regex + DataStructurer + cross-validation."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        mock_job = MagicMock()
        mock_job.template_type.value = "aggregators"
        jm.job_repo.get_job = AsyncMock(return_value=mock_job)

        extraction = MagicMock()
        extraction.page_text_map = {
            1: "EVELYN on the Park by Nshama, Town Square, Dubai. AED 820,000"
        }

        jm._pipeline_ctx[job_id] = {
            "vision_full_text": (
                "--- Page 1 ---\n"
                "EVELYN on the Park by Nshama, Town Square, Dubai. AED 820,000"
            ),
            "page_extraction_results": [],
            "extraction": extraction,
            "pdf_bytes": b"%PDF-fake",
        }

        # Patch at source modules -- _step_structure_data uses local imports
        with patch("app.services.data_structurer.DataStructurer") as MockDS:
            mock_ds = MockDS.return_value
            mock_struct = MagicMock()
            mock_struct.project_name = "EVELYN on the Park"
            mock_struct.developer = "Nshama"
            mock_struct.emirate = "Dubai"
            mock_struct.community = "Town Square"
            mock_struct.price_min = 820000
            mock_struct.price_max = None
            mock_struct.price_per_sqft = None
            mock_ds.structure = AsyncMock(return_value=mock_struct)

            with patch("app.services.table_extractor.TableExtractor") as MockTE:
                mock_te = MockTE.return_value
                mock_table_result = MagicMock()
                mock_table_result.tables = []
                mock_table_result.floor_plan_specs = []
                mock_table_result.payment_plan = None
                mock_te.extract_tables = MagicMock(return_value=mock_table_result)

                result = await jm._step_structure_data(job_id)

        # Verify DataStructurer was called with pre_extracted hints
        struct_call_kwargs = mock_ds.structure.call_args.kwargs
        assert struct_call_kwargs.get("pre_extracted") is not None
        pre_extracted = struct_call_kwargs["pre_extracted"]
        # Regex should have found these from the native text
        assert "developer" in pre_extracted
        assert "emirate" in pre_extracted
        assert "price_min" in pre_extracted

        # Verify result
        assert result["project_name"] == "EVELYN on the Park"
        assert result["pre_extracted_fields"] > 0


class TestConfidenceProfile:
    """Verify PDF confidence profile detection for flattened/scanned PDFs."""

    @pytest.mark.asyncio
    async def test_all_visual_pdf_gets_low_confidence(self):
        """PDF with zero text-rich pages is flagged as low confidence."""
        from app.services.job_manager import JobManager
        from app.services.vision_extractor import PageExtractionResult

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        extraction = MagicMock()
        extraction.page_renders = [MagicMock(), MagicMock()]
        extraction.page_renders[0].metadata.page_number = 1
        extraction.page_renders[1].metadata.page_number = 2
        # Flattened PDF: zero native text on all pages
        extraction.page_text_map = {}
        extraction.page_char_counts = {1: 0, 2: 15}

        jm._pipeline_ctx[job_id] = {"extraction": extraction}

        with patch("app.services.vision_extractor.VisionExtractor") as MockVE:
            mock_ve = MockVE.return_value
            mock_ve.extract_pages = AsyncMock(return_value=[
                PageExtractionResult(page_number=1, raw_text="Vision text p1", cost=0.01),
                PageExtractionResult(page_number=2, raw_text="Vision text p2", cost=0.01),
            ])
            MockVE.concatenate_page_text = MagicMock(
                return_value="Vision text p1\nVision text p2"
            )

            result = await jm._step_extract_data(job_id)

        assert result["confidence_profile"] == "low"
        assert result["text_rich_pages"] == 0
        assert result["vision_pages"] == 2
        assert jm._pipeline_ctx[job_id]["pdf_confidence_profile"] == "low"

    @pytest.mark.asyncio
    async def test_mixed_pdf_gets_mixed_confidence(self):
        """PDF with some text-rich and some visual pages gets mixed confidence."""
        from app.services.job_manager import JobManager
        from app.services.vision_extractor import PageExtractionResult

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        extraction = MagicMock()
        extraction.page_renders = [MagicMock() for _ in range(4)]
        for i, r in enumerate(extraction.page_renders, 1):
            r.metadata.page_number = i
        # 1 text-rich out of 4 = 25% < 50% threshold
        extraction.page_text_map = {1: "A" * 300}
        extraction.page_char_counts = {1: 300, 2: 10, 3: 5, 4: 0}

        jm._pipeline_ctx[job_id] = {"extraction": extraction}

        with patch("app.services.vision_extractor.VisionExtractor") as MockVE:
            mock_ve = MockVE.return_value
            mock_ve.extract_pages = AsyncMock(return_value=[
                PageExtractionResult(page_number=i, raw_text=f"text {i}", cost=0.0)
                for i in range(1, 5)
            ])
            MockVE.concatenate_page_text = MagicMock(return_value="all text")

            result = await jm._step_extract_data(job_id)

        assert result["confidence_profile"] == "mixed"

    @pytest.mark.asyncio
    async def test_digital_pdf_gets_high_confidence(self):
        """PDF with all text-rich pages gets high confidence."""
        from app.services.job_manager import JobManager
        from app.services.vision_extractor import PageExtractionResult

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        extraction = MagicMock()
        extraction.page_renders = [MagicMock(), MagicMock()]
        extraction.page_renders[0].metadata.page_number = 1
        extraction.page_renders[1].metadata.page_number = 2
        extraction.page_text_map = {1: "A" * 500, 2: "B" * 400}
        extraction.page_char_counts = {1: 500, 2: 400}

        jm._pipeline_ctx[job_id] = {"extraction": extraction}

        with patch("app.services.vision_extractor.VisionExtractor") as MockVE:
            mock_ve = MockVE.return_value
            mock_ve.extract_pages = AsyncMock(return_value=[
                PageExtractionResult(page_number=1, raw_text="A" * 500, cost=0.0),
                PageExtractionResult(page_number=2, raw_text="B" * 400, cost=0.0),
            ])
            MockVE.concatenate_page_text = MagicMock(return_value="all text")

            result = await jm._step_extract_data(job_id)

        assert result["confidence_profile"] == "high"
        assert result["text_rich_pages"] == 2

    @pytest.mark.asyncio
    async def test_low_confidence_propagates_to_structure_result(self):
        """Structure step includes confidence_profile from extract step."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        mock_job = MagicMock()
        mock_job.template_type.value = "aggregators"
        jm.job_repo.get_job = AsyncMock(return_value=mock_job)

        extraction = MagicMock()
        extraction.page_text_map = {1: "AED 820,000 Dubai"}

        jm._pipeline_ctx[job_id] = {
            "vision_full_text": "AED 820,000 Dubai",
            "page_extraction_results": [],
            "extraction": extraction,
            "pdf_bytes": b"%PDF-fake",
            "pdf_confidence_profile": "low",  # set by extract step
        }

        with patch("app.services.data_structurer.DataStructurer") as MockDS:
            mock_ds = MockDS.return_value
            mock_struct = MagicMock()
            mock_struct.project_name = "Test"
            mock_struct.developer = None
            mock_struct.emirate = "Dubai"
            mock_struct.community = None
            mock_struct.price_min = 820000
            mock_struct.price_max = None
            mock_struct.price_per_sqft = None
            mock_ds.structure = AsyncMock(return_value=mock_struct)

            with patch("app.services.table_extractor.TableExtractor") as MockTE:
                mock_te = MockTE.return_value
                mock_table_result = MagicMock()
                mock_table_result.tables = []
                mock_table_result.floor_plan_specs = []
                mock_table_result.payment_plan = None
                mock_te.extract_tables = MagicMock(return_value=mock_table_result)

                result = await jm._step_structure_data(job_id)

        assert result["confidence_profile"] == "low"
