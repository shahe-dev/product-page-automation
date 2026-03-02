"""
Tests for VisionExtractor (OCR-only mode).

VisionExtractor extracts raw text from PDF page renders via Vision API.
Structuring is handled downstream by DataStructurer.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.vision_extractor import (
    OCR_PROMPT,
    PageExtractionResult,
    VisionExtractor,
)
from app.utils.pdf_helpers import ExtractedImage, ImageMetadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_render(page_number: int, image_bytes: bytes = b"fake") -> ExtractedImage:
    """Create a minimal ExtractedImage for testing."""
    return ExtractedImage(
        image_bytes=image_bytes,
        metadata=ImageMetadata(
            page_number=page_number,
            source="page_render",
            width=800,
            height=600,
            format="png",
            dpi=300,
        ),
        llm_optimized_bytes=b"optimized",
    )


def _make_page_result(page_number: int, raw_text: str) -> PageExtractionResult:
    return PageExtractionResult(
        page_number=page_number,
        raw_text=raw_text,
        token_usage={"input": 100, "output": 50},
        cost=0.01,
    )


# ---------------------------------------------------------------------------
# PageExtractionResult dataclass
# ---------------------------------------------------------------------------


class TestPageExtractionResult:
    def test_defaults(self):
        pr = PageExtractionResult(page_number=1)
        assert pr.page_number == 1
        assert pr.raw_text == ""
        assert pr.token_usage == {}
        assert pr.cost == 0.0

    def test_with_data(self):
        pr = PageExtractionResult(
            page_number=3,
            raw_text="Grove Ridge\nA golf course community",
            token_usage={"input": 500, "output": 200},
            cost=0.05,
        )
        assert pr.page_number == 3
        assert "Grove Ridge" in pr.raw_text
        assert pr.cost == 0.05


# ---------------------------------------------------------------------------
# concatenate_page_text
# ---------------------------------------------------------------------------


class TestConcatenatePageText:
    def test_empty_results(self):
        assert VisionExtractor.concatenate_page_text([]) == ""

    def test_single_page(self):
        results = [_make_page_result(1, "Hello world")]
        text = VisionExtractor.concatenate_page_text(results)
        assert "--- Page 1 ---" in text
        assert "Hello world" in text

    def test_multi_page_ordered(self):
        results = [
            _make_page_result(3, "Page three"),
            _make_page_result(1, "Page one"),
            _make_page_result(2, "Page two"),
        ]
        text = VisionExtractor.concatenate_page_text(results)
        # Should be in page order regardless of input order
        idx1 = text.index("Page one")
        idx2 = text.index("Page two")
        idx3 = text.index("Page three")
        assert idx1 < idx2 < idx3

    def test_skips_empty_pages(self):
        results = [
            _make_page_result(1, "Content"),
            _make_page_result(2, ""),
            _make_page_result(3, "   "),
            _make_page_result(4, "More content"),
        ]
        text = VisionExtractor.concatenate_page_text(results)
        assert "Page 1" in text
        assert "Page 2" not in text
        assert "Page 3" not in text
        assert "Page 4" in text

    def test_page_separators(self):
        results = [
            _make_page_result(1, "First"),
            _make_page_result(2, "Second"),
        ]
        text = VisionExtractor.concatenate_page_text(results)
        assert "--- Page 1 ---" in text
        assert "--- Page 2 ---" in text


# ---------------------------------------------------------------------------
# extract_pages (mocked API)
# ---------------------------------------------------------------------------


class TestExtractPages:
    @pytest.mark.asyncio
    async def test_extract_pages_parallel(self):
        """Verify parallel extraction collects raw text from all pages."""
        renders = [_make_render(i) for i in range(1, 4)]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Extracted text from page")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        with patch(
            "app.services.vision_extractor.anthropic_service"
        ) as mock_svc, patch(
            "app.services.vision_extractor.create_llm_optimized", return_value=None
        ):
            mock_svc.vision_completion = AsyncMock(return_value=mock_response)
            extractor = VisionExtractor()
            results = await extractor.extract_pages(renders)

        assert len(results) == 3
        for r in results:
            assert r.raw_text == "Extracted text from page"
            assert r.token_usage["input"] == 100

    @pytest.mark.asyncio
    async def test_extract_pages_handles_api_error(self):
        """Failed pages are skipped, successful ones are returned."""
        renders = [_make_render(1), _make_render(2)]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Good text")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        call_count = 0

        async def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("API error")
            return mock_response

        with patch(
            "app.services.vision_extractor.anthropic_service"
        ) as mock_svc, patch(
            "app.services.vision_extractor.create_llm_optimized", return_value=None
        ):
            mock_svc.vision_completion = AsyncMock(side_effect=side_effect)
            extractor = VisionExtractor()
            results = await extractor.extract_pages(renders)

        assert len(results) == 1
        assert results[0].raw_text == "Good text"

    @pytest.mark.asyncio
    async def test_extract_pages_respects_max_pages(self):
        """Only MAX_PAGES renders are processed."""
        renders = [_make_render(i) for i in range(1, 40)]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="text")]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=20)

        with patch(
            "app.services.vision_extractor.anthropic_service"
        ) as mock_svc, patch(
            "app.services.vision_extractor.create_llm_optimized", return_value=None
        ):
            mock_svc.vision_completion = AsyncMock(return_value=mock_response)
            extractor = VisionExtractor()
            results = await extractor.extract_pages(renders)

        assert len(results) == VisionExtractor.MAX_PAGES

    @pytest.mark.asyncio
    async def test_extract_pages_empty_input(self):
        extractor = VisionExtractor()
        results = await extractor.extract_pages([])
        assert results == []

    @pytest.mark.asyncio
    async def test_ocr_prompt_used(self):
        """Verify the OCR prompt is sent to the Vision API."""
        renders = [_make_render(1)]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="text")]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=20)

        with patch(
            "app.services.vision_extractor.anthropic_service"
        ) as mock_svc, patch(
            "app.services.vision_extractor.create_llm_optimized", return_value=None
        ):
            mock_svc.vision_completion = AsyncMock(return_value=mock_response)
            extractor = VisionExtractor()
            await extractor.extract_pages(renders)

            call_kwargs = mock_svc.vision_completion.call_args
            assert call_kwargs.kwargs["prompt"] == OCR_PROMPT

    @pytest.mark.asyncio
    async def test_cost_tracking(self):
        """Verify token usage and cost are recorded."""
        renders = [_make_render(1)]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="text")]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=200)

        with patch(
            "app.services.vision_extractor.anthropic_service"
        ) as mock_svc, patch(
            "app.services.vision_extractor.create_llm_optimized", return_value=None
        ), patch(
            "app.services.vision_extractor.calculate_cost", return_value=0.042
        ):
            mock_svc.vision_completion = AsyncMock(return_value=mock_response)
            extractor = VisionExtractor()
            results = await extractor.extract_pages(renders)

        assert len(results) == 1
        assert results[0].token_usage == {"input": 500, "output": 200}
        assert results[0].cost == 0.042
