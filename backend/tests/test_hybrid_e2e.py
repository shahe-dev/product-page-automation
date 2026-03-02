"""End-to-end test for hybrid extraction pipeline."""
import pytest
import fitz
from unittest.mock import patch, MagicMock
from app.services.pdf_processor import PDFProcessor
from app.services.vision_extractor import VisionExtractor
from app.services.data_extractor import DataExtractor
from app.services.table_extractor import TableExtractor


def _create_test_pdf() -> bytes:
    """Create a test PDF with known content for validation."""
    doc = fitz.open()

    # Page 1: Cover with project name
    p1 = doc.new_page()
    p1.insert_text((72, 100), "EVELYN on the Park", fontsize=24)
    p1.insert_text((72, 140), "by Nshama", fontsize=14)
    p1.insert_text((72, 180), "Town Square, Dubai", fontsize=12)

    # Page 2: Details
    p2 = doc.new_page()
    p2.insert_text((72, 72), "Starting from AED 820,000")
    p2.insert_text((72, 100), "Bedrooms: Studio, 1BR, 2BR, 3BR")
    p2.insert_text((72, 128), "Handover: Q4 2027")
    p2.insert_text((72, 156), "Payment Plan: 80/20")

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestHybridE2E:
    @pytest.mark.asyncio
    async def test_text_layer_extracted(self):
        """PDFProcessor populates page_text_map with native text."""
        pdf_bytes = _create_test_pdf()
        processor = PDFProcessor()
        result = await processor.extract_all(pdf_bytes)

        assert result.page_text_map, "page_text_map empty"
        all_text = " ".join(result.page_text_map.values())
        assert "EVELYN" in all_text
        assert "820,000" in all_text

    @pytest.mark.asyncio
    async def test_page_char_counts_populated(self):
        """PDFProcessor populates page_char_counts for routing."""
        pdf_bytes = _create_test_pdf()
        processor = PDFProcessor()
        result = await processor.extract_all(pdf_bytes)

        assert result.page_char_counts, "page_char_counts empty"
        assert 1 in result.page_char_counts
        assert 2 in result.page_char_counts

    def test_regex_extracts_from_native_text(self):
        """DataExtractor regex finds fields from native text."""
        pdf_bytes = _create_test_pdf()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_text_map = {}
        for i, page in enumerate(doc, 1):
            page_text_map[i] = page.get_text("text")
        doc.close()

        extractor = DataExtractor()
        result = extractor.extract(page_text_map)

        assert result.location.emirate == "Dubai"
        assert result.prices.min_price is not None

    @pytest.mark.asyncio
    async def test_page_routing_skips_vision_for_text_pages(self):
        """Text-rich pages are not sent to Vision API."""
        page_char_counts = {1: 500, 2: 400}
        page_text_map = {1: "EVELYN text " * 50, 2: "Price text " * 50}
        renders = [MagicMock(), MagicMock()]
        renders[0].metadata.page_number = 1
        renders[1].metadata.page_number = 2

        ve = VisionExtractor()
        with patch.object(ve, "_extract_page") as mock_vision:
            results = await ve.extract_pages(
                renders,
                page_text_map=page_text_map,
                page_char_counts=page_char_counts,
            )

        # No Vision calls -- both pages are text-rich
        assert mock_vision.call_count == 0
        assert len(results) == 2

    def test_table_extractor_on_empty_pdf(self):
        """TableExtractor handles PDFs without tables gracefully."""
        pdf_bytes = _create_test_pdf()
        extractor = TableExtractor()
        result = extractor.extract_tables(pdf_bytes)
        # Test PDF has no tables, should return empty
        assert result.floor_plan_specs == []
        assert result.payment_plan is None

    @pytest.mark.asyncio
    async def test_extraction_method_is_hybrid(self):
        """PDFProcessor sets extraction_method to hybrid."""
        pdf_bytes = _create_test_pdf()
        processor = PDFProcessor()
        result = await processor.extract_all(pdf_bytes)
        assert result.extraction_method == "hybrid"

    def test_cross_validator_no_flags_when_agreement(self):
        """Cross-validator produces no flags when all sources agree."""
        from app.services.cross_validator import CrossValidator
        from app.services.data_structurer import StructuredProject

        structured = StructuredProject(
            project_name="EVELYN on the Park",
            developer="Nshama",
            price_min=820000,
            emirate="Dubai",
            community="Town Square",
        )
        regex_hints = {
            "project_name": "Evelyn On The Park",
            "developer": "Nshama",
            "price_min": 820000,
            "emirate": "Dubai",
            "community": "Town Square",
        }

        validator = CrossValidator()
        reconciled, flags = validator.reconcile_project(
            structured, regex_hints, {}
        )
        assert reconciled.price_min == 820000
        assert reconciled.developer == "Nshama"
        # project_name: "EVELYN on the Park" vs "Evelyn On The Park" -- case insensitive match
        assert len(flags) == 0
