"""Tests for per-page routing in VisionExtractor."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.vision_extractor import VisionExtractor, PageExtractionResult


class TestPageRouting:
    def setup_method(self):
        self.extractor = VisionExtractor()

    def test_text_rich_page_classified(self):
        """Pages with >= 200 chars are text-rich."""
        page_char_counts = {1: 500, 2: 50, 3: 300}
        text_rich, visual = self.extractor.classify_pages(page_char_counts)
        assert 1 in text_rich
        assert 3 in text_rich
        assert 2 in visual
        assert 2 not in text_rich

    def test_empty_char_counts_all_visual(self):
        """If no char counts provided, classify_pages returns empty text_rich."""
        text_rich, visual = self.extractor.classify_pages({})
        assert text_rich == set()

    def test_threshold_boundary(self):
        """Exactly 200 chars is text-rich. 199 is visual."""
        page_char_counts = {1: 200, 2: 199}
        text_rich, visual = self.extractor.classify_pages(page_char_counts)
        assert 1 in text_rich
        assert 2 in visual

    @pytest.mark.asyncio
    async def test_extract_pages_uses_native_text_for_text_rich(self):
        """extract_pages() returns native text for text-rich pages, Vision for visual."""
        renders = [MagicMock() for _ in range(3)]
        for i, r in enumerate(renders, 1):
            r.metadata.page_number = i

        page_text_map = {1: "A" * 300, 2: "B" * 50, 3: "C" * 400}
        page_char_counts = {1: 300, 2: 50, 3: 400}

        with patch.object(self.extractor, "_extract_page") as mock_vision:
            mock_vision.return_value = PageExtractionResult(
                page_number=2, raw_text="Vision text for page 2"
            )
            results = await self.extractor.extract_pages(
                renders,
                page_text_map=page_text_map,
                page_char_counts=page_char_counts,
            )

        # Only page 2 should have been sent to Vision
        assert mock_vision.call_count == 1
        # Pages 1 and 3 should use native text
        page_texts = {r.page_number: r.raw_text for r in results}
        assert page_texts[1] == "A" * 300
        assert page_texts[3] == "C" * 400

    @pytest.mark.asyncio
    async def test_all_text_rich_no_vision_calls(self):
        """If all pages are text-rich, no Vision API calls happen."""
        renders = [MagicMock(), MagicMock()]
        renders[0].metadata.page_number = 1
        renders[1].metadata.page_number = 2

        page_text_map = {1: "Text " * 100, 2: "More " * 100}
        page_char_counts = {1: 500, 2: 500}

        with patch.object(self.extractor, "_extract_page") as mock_vision:
            results = await self.extractor.extract_pages(
                renders,
                page_text_map=page_text_map,
                page_char_counts=page_char_counts,
            )

        assert mock_vision.call_count == 0
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_no_char_counts_all_go_to_vision(self):
        """Without char counts, all pages go to Vision (backward compat)."""
        renders = [MagicMock()]
        renders[0].metadata.page_number = 1

        with patch.object(self.extractor, "_extract_page") as mock_vision:
            mock_vision.return_value = PageExtractionResult(
                page_number=1, raw_text="Vision text"
            )
            await self.extractor.extract_pages(renders)

        assert mock_vision.call_count == 1

    @pytest.mark.asyncio
    async def test_text_rich_pages_cost_zero(self):
        """Text-rich pages have zero API cost."""
        renders = [MagicMock()]
        renders[0].metadata.page_number = 1

        results = await self.extractor.extract_pages(
            renders,
            page_text_map={1: "Native text " * 50},
            page_char_counts={1: 600},
        )

        assert len(results) == 1
        assert results[0].cost == 0.0
