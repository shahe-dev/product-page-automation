"""Tests for restored text layer extraction in PDFProcessor."""
import io
import pytest

import fitz
from PIL import Image

from app.services.pdf_processor import PDFProcessor


class TestTextLayerExtraction:
    """Test that PDFProcessor extracts native text layer."""

    def setup_method(self):
        self.processor = PDFProcessor()

    @pytest.mark.asyncio
    async def test_page_text_map_populated(self):
        """extract_all() populates page_text_map from native text layer."""
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "EVELYN on the Park\nBy NSHAMA\nDubai")
        pdf_bytes = doc.tobytes()
        doc.close()

        result = await self.processor.extract_all(pdf_bytes)
        assert result.page_text_map, "page_text_map should not be empty"
        assert 1 in result.page_text_map
        assert "EVELYN" in result.page_text_map[1]

    @pytest.mark.asyncio
    async def test_page_char_counts_populated(self):
        """extract_all() sets page_char_counts for routing decisions."""
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello World " * 50)
        pdf_bytes = doc.tobytes()
        doc.close()

        result = await self.processor.extract_all(pdf_bytes)
        assert hasattr(result, "page_char_counts")
        assert result.page_char_counts.get(1, 0) > 100

    @pytest.mark.asyncio
    async def test_visual_page_has_low_char_count(self):
        """Pages with only images have near-zero char count."""
        doc = fitz.open()
        page = doc.new_page()
        # Insert a small image, no text
        img = Image.new("RGB", (100, 100), "red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        page.insert_image(page.rect, stream=buf.getvalue())
        pdf_bytes = doc.tobytes()
        doc.close()

        result = await self.processor.extract_all(pdf_bytes)
        # Image-only page should have very low char count
        assert result.page_char_counts.get(1, 0) < 50

    @pytest.mark.asyncio
    async def test_extraction_method_is_hybrid(self):
        """extract_all() sets extraction_method to 'hybrid'."""
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test text")
        pdf_bytes = doc.tobytes()
        doc.close()

        result = await self.processor.extract_all(pdf_bytes)
        assert result.extraction_method == "hybrid"

    @pytest.mark.asyncio
    async def test_multi_page_text_extraction(self):
        """Text from multiple pages is extracted into separate entries."""
        doc = fitz.open()
        p1 = doc.new_page()
        p1.insert_text((72, 72), "Page one content")
        p2 = doc.new_page()
        p2.insert_text((72, 72), "Page two content")
        pdf_bytes = doc.tobytes()
        doc.close()

        result = await self.processor.extract_all(pdf_bytes)
        assert 1 in result.page_text_map
        assert 2 in result.page_text_map
        assert "one" in result.page_text_map[1]
        assert "two" in result.page_text_map[2]
