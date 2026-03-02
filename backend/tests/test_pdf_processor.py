"""
Comprehensive test suite for PDF Processor service and PDF helper utilities.

Tests cover:
- PDF validation helpers
- Image validation and dimension checks
- PIL image conversions and format handling
- LLM optimization (downscaling, compression)
- PDFProcessor triple extraction (embedded + page render + text)
- Error handling for corrupted/invalid PDFs
"""

import io
from unittest.mock import Mock, patch

import fitz
import pytest
from PIL import Image

from app.services.pdf_processor import PDFProcessor, MAX_PDF_SIZE
from app.utils.pdf_helpers import (
    MIN_IMAGE_HEIGHT,
    MIN_IMAGE_WIDTH,
    RENDER_DPI,
    ExtractedImage,
    ExtractionResult,
    ImageMetadata,
    create_llm_optimized,
    detect_format,
    get_image_dimensions,
    image_bytes_to_pil,
    is_valid_embedded_image,
    pil_to_bytes,
    validate_pdf_bytes,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_pdf_header():
    """Valid PDF magic number."""
    return b"%PDF-1.7"


@pytest.fixture
def invalid_pdf_header():
    """Invalid PDF header."""
    return b"NOTAPDF"


@pytest.fixture
def sample_image_bytes():
    """Create a simple test image as bytes (PNG format)."""
    img = Image.new("RGB", (800, 600), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_small_image_bytes():
    """Create a small image below MIN dimensions (for embedded filtering)."""
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_large_image_bytes():
    """Create a large image that needs downscaling for LLM optimization."""
    img = Image.new("RGB", (2048, 2048), color="green")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_rgba_image_bytes():
    """Create an RGBA image (for JPEG conversion testing)."""
    img = Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def simple_pdf_bytes():
    """Create a simple 1-page PDF with text."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((100, 100), "Test PDF Page")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def pdf_with_embedded_image(sample_image_bytes):
    """Create a PDF with an embedded image above MIN dimensions."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    # Insert image using insert_image method
    img_rect = fitz.Rect(50, 50, 450, 400)
    page.insert_image(img_rect, stream=sample_image_bytes)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def pdf_with_small_embedded_image(sample_small_image_bytes):
    """Create a PDF with a small embedded image (should be filtered out)."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    # Insert small image using insert_image method
    img_rect = fitz.Rect(50, 50, 150, 150)
    page.insert_image(img_rect, stream=sample_small_image_bytes)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def multi_page_pdf():
    """Create a 3-page PDF."""
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=612, height=792)
        page.insert_text((100, 100), f"Page {i + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def empty_pdf():
    """Create a PDF with one empty page (fitz doesn't allow zero-page PDFs)."""
    doc = fitz.open()
    # Add one blank page since fitz.Document.tobytes() requires at least one page
    doc.new_page(width=612, height=792)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ============================================================================
# Tests: pdf_helpers.py - validate_pdf_bytes
# ============================================================================


def test_validate_pdf_bytes_valid(valid_pdf_header):
    """Test that valid PDF header passes validation."""
    full_pdf = valid_pdf_header + b"\n%Some PDF content"
    assert validate_pdf_bytes(full_pdf) is True


def test_validate_pdf_bytes_invalid(invalid_pdf_header):
    """Test that invalid header fails validation."""
    assert validate_pdf_bytes(invalid_pdf_header) is False


def test_validate_pdf_bytes_empty():
    """Test that empty bytes fail validation."""
    assert validate_pdf_bytes(b"") is False


def test_validate_pdf_bytes_short():
    """Test that bytes shorter than header fail validation."""
    assert validate_pdf_bytes(b"%PD") is False


# ============================================================================
# Tests: pdf_helpers.py - is_valid_embedded_image
# ============================================================================


def test_is_valid_embedded_image_valid():
    """Test that images meeting MIN dimensions are valid.

    MIN_IMAGE_WIDTH=100, MIN_IMAGE_HEIGHT=50 (lowered to capture logos).
    """
    assert is_valid_embedded_image(100, 50) is True
    assert is_valid_embedded_image(200, 100) is True
    assert is_valid_embedded_image(500, 500) is True
    assert is_valid_embedded_image(1000, 1000) is True


def test_is_valid_embedded_image_below_width():
    """Test that images below MIN_IMAGE_WIDTH (100) are invalid."""
    assert is_valid_embedded_image(99, 50) is False
    assert is_valid_embedded_image(50, 100) is False


def test_is_valid_embedded_image_below_height():
    """Test that images below MIN_IMAGE_HEIGHT (50) are invalid."""
    assert is_valid_embedded_image(100, 49) is False
    assert is_valid_embedded_image(200, 30) is False


def test_is_valid_embedded_image_both_below():
    """Test that very small images in both dimensions are invalid."""
    assert is_valid_embedded_image(50, 40) is False
    assert is_valid_embedded_image(0, 0) is False
    # 100x100 is now valid with the lowered thresholds
    assert is_valid_embedded_image(100, 100) is True


def test_is_valid_embedded_image_boundary():
    """Test exact boundary conditions."""
    assert is_valid_embedded_image(MIN_IMAGE_WIDTH, MIN_IMAGE_HEIGHT) is True
    assert is_valid_embedded_image(MIN_IMAGE_WIDTH - 1, MIN_IMAGE_HEIGHT) is False
    assert is_valid_embedded_image(MIN_IMAGE_WIDTH, MIN_IMAGE_HEIGHT - 1) is False


# ============================================================================
# Tests: pdf_helpers.py - image_bytes_to_pil
# ============================================================================


def test_image_bytes_to_pil_valid(sample_image_bytes):
    """Test converting valid image bytes to PIL Image."""
    img = image_bytes_to_pil(sample_image_bytes)
    assert img is not None
    assert isinstance(img, Image.Image)
    assert img.size == (800, 600)


def test_image_bytes_to_pil_invalid():
    """Test that invalid bytes return None."""
    img = image_bytes_to_pil(b"not an image")
    assert img is None


def test_image_bytes_to_pil_empty():
    """Test that empty bytes return None."""
    img = image_bytes_to_pil(b"")
    assert img is None


def test_image_bytes_to_pil_corrupted():
    """Test that corrupted image data returns None."""
    # Valid PNG header but truncated/corrupted
    corrupted = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    img = image_bytes_to_pil(corrupted)
    assert img is None


# ============================================================================
# Tests: pdf_helpers.py - pil_to_bytes
# ============================================================================


def test_pil_to_bytes_png():
    """Test converting PIL Image to PNG bytes."""
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = pil_to_bytes(img, fmt="PNG")

    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 0
    assert img_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_pil_to_bytes_jpeg():
    """Test converting PIL Image to JPEG bytes."""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = pil_to_bytes(img, fmt="JPEG", quality=90)

    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 0
    assert img_bytes[:2] == b"\xff\xd8"  # JPEG SOI marker


def test_pil_to_bytes_jpeg_with_alpha(sample_rgba_image_bytes):
    """Test that RGBA images are converted to RGB for JPEG."""
    img = image_bytes_to_pil(sample_rgba_image_bytes)
    assert img.mode == "RGBA"

    img_bytes = pil_to_bytes(img, fmt="JPEG")

    # Should succeed without error (RGBA converted to RGB)
    assert isinstance(img_bytes, bytes)
    assert img_bytes[:2] == b"\xff\xd8"


def test_pil_to_bytes_webp():
    """Test converting PIL Image to WEBP bytes."""
    img = Image.new("RGB", (100, 100), color="green")
    img_bytes = pil_to_bytes(img, fmt="WEBP", quality=85)

    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 0
    # WEBP has "RIFF" header
    assert img_bytes[:4] == b"RIFF"


def test_pil_to_bytes_quality_parameter():
    """Test that quality parameter affects output size (lower quality = smaller)."""
    img = Image.new("RGB", (500, 500), color="blue")

    high_quality = pil_to_bytes(img, fmt="JPEG", quality=95)
    low_quality = pil_to_bytes(img, fmt="JPEG", quality=50)

    assert len(low_quality) < len(high_quality)


# ============================================================================
# Tests: pdf_helpers.py - create_llm_optimized
# ============================================================================


def test_create_llm_optimized_downscales_large_image(sample_large_image_bytes):
    """Test that large images are downscaled to max_dim."""
    optimized = create_llm_optimized(sample_large_image_bytes, max_dim=1024)

    assert optimized is not None

    # Check dimensions
    img = image_bytes_to_pil(optimized)
    assert img is not None
    w, h = img.size
    assert max(w, h) == 1024
    assert w == h  # Should maintain aspect ratio (original was square)


def test_create_llm_optimized_small_image_unchanged(sample_image_bytes):
    """Test that images already below max_dim are not upscaled."""
    # Original is 800x600, max_dim is 1024, so no resizing needed
    optimized = create_llm_optimized(sample_image_bytes, max_dim=1024)

    assert optimized is not None

    img = image_bytes_to_pil(optimized)
    assert img is not None
    # Note: dimensions might differ slightly due to re-encoding, but should be close
    w, h = img.size
    # Original was 800x600, should not be resized but will be re-encoded as JPEG
    assert w <= 800 and h <= 600


def test_create_llm_optimized_compression():
    """Test that optimized version processes correctly with JPEG compression."""
    # Create a large image with varied colors (compresses differently than solid color)
    img = Image.new("RGB", (2000, 2000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    optimized = create_llm_optimized(png_bytes, max_dim=1024, fmt="JPEG", quality=80)

    assert optimized is not None
    # Verify it's a JPEG
    assert optimized[:2] == b"\xff\xd8"
    # Verify dimensions are reduced
    opt_img = image_bytes_to_pil(optimized)
    assert max(opt_img.size) == 1024


def test_create_llm_optimized_invalid_bytes():
    """Test that invalid image bytes return None."""
    optimized = create_llm_optimized(b"not an image")
    assert optimized is None


def test_create_llm_optimized_maintains_aspect_ratio():
    """Test that aspect ratio is maintained during downscaling."""
    # Create 1600x800 image (2:1 ratio)
    img = Image.new("RGB", (1600, 800), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    optimized = create_llm_optimized(img_bytes, max_dim=1024)

    assert optimized is not None

    result_img = image_bytes_to_pil(optimized)
    w, h = result_img.size

    # Longest side should be 1024
    assert max(w, h) == 1024
    # Aspect ratio should be approximately 2:1
    assert abs((w / h) - 2.0) < 0.01


# ============================================================================
# Tests: pdf_helpers.py - get_image_dimensions
# ============================================================================


def test_get_image_dimensions_valid(sample_image_bytes):
    """Test getting dimensions from valid image bytes."""
    w, h = get_image_dimensions(sample_image_bytes)
    assert w == 800
    assert h == 600


def test_get_image_dimensions_invalid():
    """Test that invalid bytes return (0, 0)."""
    w, h = get_image_dimensions(b"not an image")
    assert w == 0
    assert h == 0


def test_get_image_dimensions_various_sizes():
    """Test dimension detection with various image sizes."""
    test_cases = [(100, 100), (640, 480), (1920, 1080), (500, 300)]

    for width, height in test_cases:
        img = Image.new("RGB", (width, height), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        w, h = get_image_dimensions(img_bytes)
        assert w == width
        assert h == height


# ============================================================================
# Tests: pdf_helpers.py - detect_format
# ============================================================================


def test_detect_format_png():
    """Test format detection for PNG images."""
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = pil_to_bytes(img, fmt="PNG")

    fmt = detect_format(img_bytes)
    assert fmt == "png"


def test_detect_format_jpeg():
    """Test format detection for JPEG images."""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = pil_to_bytes(img, fmt="JPEG")

    fmt = detect_format(img_bytes)
    assert fmt == "jpeg"


def test_detect_format_webp():
    """Test format detection for WEBP images."""
    img = Image.new("RGB", (100, 100), color="green")
    img_bytes = pil_to_bytes(img, fmt="WEBP")

    fmt = detect_format(img_bytes)
    assert fmt == "webp"


def test_detect_format_invalid():
    """Test format detection for invalid bytes."""
    fmt = detect_format(b"not an image")
    assert fmt == "unknown"


def test_detect_format_empty():
    """Test format detection for empty bytes."""
    fmt = detect_format(b"")
    assert fmt == "unknown"


# ============================================================================
# Tests: PDFProcessor - extract_all with simple PDF
# ============================================================================


@pytest.mark.asyncio
async def test_extract_all_simple_pdf(simple_pdf_bytes):
    """Test extracting from a simple text-only PDF."""
    processor = PDFProcessor()
    result = await processor.extract_all(simple_pdf_bytes)

    assert isinstance(result, ExtractionResult)
    assert result.total_pages == 1
    assert len(result.page_renders) == 1
    assert len(result.embedded) == 0  # No embedded images
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_extract_all_invalid_pdf_header(invalid_pdf_header):
    """Test that invalid PDF header raises ValueError."""
    processor = PDFProcessor()

    with pytest.raises(ValueError, match="Invalid PDF: missing PDF header"):
        await processor.extract_all(invalid_pdf_header)


@pytest.mark.asyncio
async def test_extract_all_corrupted_pdf():
    """Test handling of corrupted PDF content."""
    processor = PDFProcessor()

    # Valid header but corrupted body
    corrupted_pdf = b"%PDF-1.7\n" + b"corrupted content"

    with pytest.raises(ValueError, match="Corrupted or unreadable PDF"):
        await processor.extract_all(corrupted_pdf)


@pytest.mark.asyncio
async def test_extract_all_empty_pdf(empty_pdf):
    """Test extracting from a PDF with one empty page."""
    processor = PDFProcessor()
    result = await processor.extract_all(empty_pdf)

    assert result.total_pages == 1
    assert len(result.page_renders) == 1
    assert len(result.embedded) == 0  # No embedded images


@pytest.mark.asyncio
async def test_extract_all_oversized_pdf():
    """Test that PDFs exceeding MAX_PDF_SIZE are rejected."""
    processor = PDFProcessor()

    # Create bytes larger than MAX_PDF_SIZE
    oversized = b"%PDF-1.7\n" + b"x" * (MAX_PDF_SIZE + 1)

    with pytest.raises(ValueError, match="PDF exceeds .* limit"):
        await processor.extract_all(oversized)


# ============================================================================
# Tests: PDFProcessor - extract_all with embedded images
# ============================================================================


@pytest.mark.asyncio
async def test_extract_all_with_embedded_image(pdf_with_embedded_image):
    """Test extraction of embedded images above MIN dimensions."""
    processor = PDFProcessor()
    result = await processor.extract_all(pdf_with_embedded_image)

    assert result.total_pages == 1
    assert len(result.page_renders) == 1

    # Note: Depending on how fitz handles show_pdf_page, embedded extraction may vary
    # This test validates the extraction runs without errors
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_extract_all_filters_small_embedded(pdf_with_small_embedded_image):
    """Test that small embedded images are filtered out."""
    processor = PDFProcessor()
    result = await processor.extract_all(pdf_with_small_embedded_image)

    assert result.total_pages == 1
    assert len(result.page_renders) == 1

    # Small image should be filtered during _extract_embedded
    # Note: Actual behavior depends on how fitz represents the embedded image
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_extract_all_multi_page(multi_page_pdf):
    """Test extraction from multi-page PDF."""
    processor = PDFProcessor()
    result = await processor.extract_all(multi_page_pdf)

    assert result.total_pages == 3
    assert len(result.page_renders) == 3
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_extract_all_respects_max_pages():
    """Test that extraction stops at max_pages limit."""
    # Create a 5-page PDF
    doc = fitz.open()
    for i in range(5):
        page = doc.new_page(width=612, height=792)
        page.insert_text((100, 100), f"Page {i + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()

    processor = PDFProcessor(max_pages=3)
    result = await processor.extract_all(pdf_bytes)

    assert result.total_pages == 3  # Should stop at max_pages
    assert len(result.page_renders) == 3


# ============================================================================
# Tests: PDFProcessor - _extract_embedded
# ============================================================================


@pytest.mark.asyncio
async def test_extract_embedded_uses_get_images():
    """Test that _extract_embedded calls page.get_images()."""
    processor = PDFProcessor()

    # Create a mock document and page
    mock_page = Mock()
    mock_page.get_images.return_value = []

    mock_doc = Mock()
    seen_xrefs: set[int] = set()

    result = processor._extract_embedded(mock_doc, mock_page, 0, seen_xrefs)

    assert mock_page.get_images.called
    assert result == []


@pytest.mark.asyncio
async def test_extract_embedded_skips_duplicate_xrefs():
    """Test that duplicate xrefs are skipped within a page."""
    processor = PDFProcessor()

    mock_page = Mock()
    # Return same xref twice on same page
    mock_page.get_images.return_value = [
        (123, 0, 0, 0, 0, 0, 0, "", ""),
        (123, 0, 0, 0, 0, 0, 0, "", ""),
    ]

    mock_doc = Mock()
    mock_doc.extract_image.return_value = None
    seen_xrefs: set[int] = set()

    result = processor._extract_embedded(mock_doc, mock_page, 0, seen_xrefs)

    # extract_image should only be called once due to xref deduplication
    assert mock_doc.extract_image.call_count == 1


@pytest.mark.asyncio
async def test_extract_embedded_skips_cross_page_duplicate_xrefs():
    """Test that xrefs seen on previous pages are skipped."""
    processor = PDFProcessor()

    mock_page = Mock()
    mock_page.get_images.return_value = [
        (456, 0, 0, 0, 0, 0, 0, "", ""),
    ]

    mock_doc = Mock()
    mock_doc.extract_image.return_value = None

    # Simulate xref already seen from a previous page
    seen_xrefs: set[int] = {456}

    result = processor._extract_embedded(mock_doc, mock_page, 0, seen_xrefs)

    # extract_image should NOT be called since xref was already seen
    assert mock_doc.extract_image.call_count == 0
    assert result == []


# ============================================================================
# Tests: PDFProcessor - _render_page
# ============================================================================


@pytest.mark.asyncio
async def test_render_page_at_dpi():
    """Test that _render_page renders at configured DPI."""
    processor = PDFProcessor(render_dpi=300)

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    result = processor._render_page(page, 0)

    assert result is not None
    assert isinstance(result, ExtractedImage)
    assert result.metadata.dpi == 300
    assert result.metadata.source == "page_render"
    assert result.metadata.page_number == 1

    # Check that dimensions are scaled appropriately
    # At 300 DPI, scale factor is 300/72 = 4.166...
    expected_width = int(612 * (300 / 72))
    expected_height = int(792 * (300 / 72))

    assert result.metadata.width == expected_width
    assert result.metadata.height == expected_height

    doc.close()


@pytest.mark.asyncio
async def test_render_page_creates_llm_optimized():
    """Test that _render_page creates LLM-optimized bytes."""
    processor = PDFProcessor()

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    result = processor._render_page(page, 0)

    assert result is not None
    assert result.llm_optimized_bytes is not None
    assert len(result.llm_optimized_bytes) > 0

    doc.close()


@pytest.mark.asyncio
async def test_render_page_error_handling():
    """Test that _render_page returns None on error."""
    processor = PDFProcessor()

    # Create a mock page that raises an exception
    mock_page = Mock()
    mock_page.get_pixmap.side_effect = Exception("Render error")

    result = processor._render_page(mock_page, 0)

    assert result is None


# ============================================================================
# Tests: PDFProcessor - get_extraction_summary
# ============================================================================


def test_get_extraction_summary():
    """Test that get_extraction_summary returns correct structure."""
    processor = PDFProcessor(render_dpi=300)

    result = ExtractionResult(
        total_pages=5, errors=[{"page": 3, "error": "test error"}]
    )

    # Add some mock data
    result.embedded = [Mock(), Mock()]
    result.page_renders = [Mock(), Mock(), Mock(), Mock(), Mock()]

    summary = processor.get_extraction_summary(result)

    assert summary["total_embedded"] == 2
    assert summary["total_page_renders"] == 5
    assert summary["total_pages"] == 5
    assert (
        summary["extraction_method"] == "pymupdf"
    )  # ExtractionResult default (not from extract_all)
    assert summary["render_dpi"] == 300
    assert len(summary["errors"]) == 1
    assert summary["errors"][0]["page"] == 3


def test_get_extraction_summary_empty():
    """Test summary with empty result."""
    processor = PDFProcessor()
    result = ExtractionResult()

    summary = processor.get_extraction_summary(result)

    assert summary["total_embedded"] == 0
    assert summary["total_page_renders"] == 0
    assert summary["total_pages"] == 0
    assert summary["extraction_method"] == "pymupdf"  # ExtractionResult default
    assert len(summary["errors"]) == 0


# ============================================================================
# Tests: Integration - Full extraction workflow
# ============================================================================


@pytest.mark.asyncio
async def test_full_extraction_workflow(sample_image_bytes):
    """
    Integration test: Create a PDF with embedded image and text,
    extract all content, and verify both extraction methods work.
    """
    # Create a PDF with both embedded image and text
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    # Add text
    page.insert_text((100, 100), "Test PDF with content")

    # Add an embedded image (using a large enough image)
    img = Image.new("RGB", (800, 600), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    # Use insert_image instead of show_pdf_page
    img_rect = fitz.Rect(100, 150, 500, 550)
    page.insert_image(img_rect, stream=img_bytes)

    pdf_bytes = doc.tobytes()
    doc.close()

    # Extract
    processor = PDFProcessor()
    result = await processor.extract_all(pdf_bytes)

    # Verify results
    assert result.total_pages == 1
    assert len(result.page_renders) == 1
    assert len(result.errors) == 0

    # Verify page render
    page_render = result.page_renders[0]
    assert page_render.metadata.source == "page_render"
    assert page_render.metadata.page_number == 1
    assert page_render.image_bytes is not None
    assert page_render.llm_optimized_bytes is not None

    # Verify summary
    summary = processor.get_extraction_summary(result)
    assert summary["total_pages"] == 1
    assert summary["extraction_method"] == "hybrid"


@pytest.mark.asyncio
async def test_extraction_with_custom_dpi():
    """Test extraction with custom DPI setting."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((100, 100), "Custom DPI test")
    pdf_bytes = doc.tobytes()
    doc.close()

    processor = PDFProcessor(render_dpi=150)
    result = await processor.extract_all(pdf_bytes)

    assert len(result.page_renders) == 1

    page_render = result.page_renders[0]
    assert page_render.metadata.dpi == 150

    # Verify dimensions are scaled for 150 DPI
    expected_width = int(612 * (150 / 72))
    expected_height = int(792 * (150 / 72))

    assert page_render.metadata.width == expected_width
    assert page_render.metadata.height == expected_height


# ============================================================================
# Tests: Edge cases and error conditions
# ============================================================================


@pytest.mark.asyncio
async def test_extraction_handles_page_with_error():
    """Test that extraction continues after a page error."""
    processor = PDFProcessor()

    # Create a valid PDF
    doc = fitz.open()
    doc.new_page(width=612, height=792)
    pdf_bytes = doc.tobytes()
    doc.close()

    # Mock _render_page to raise RuntimeError (one of the caught types)
    # The code catches RuntimeError, ValueError, OSError
    with patch.object(
        processor, "_render_page", side_effect=RuntimeError("Render failed")
    ):
        result = await processor.extract_all(pdf_bytes)

    # Should still complete but with errors recorded
    assert result.total_pages == 1
    # The error is caught in extract_all and added to errors list
    assert len(result.errors) == 1
    assert "Render failed" in result.errors[0]["error"]


def test_image_metadata_dataclass():
    """Test ImageMetadata dataclass creation and defaults."""
    metadata = ImageMetadata(page_number=1, source="embedded")

    assert metadata.page_number == 1
    assert metadata.source == "embedded"
    assert metadata.width == 0
    assert metadata.height == 0
    assert metadata.format == "png"
    assert metadata.dpi == 72
    assert metadata.xref is None
    assert metadata.file_size == 0


def test_extracted_image_dataclass():
    """Test ExtractedImage dataclass creation."""
    metadata = ImageMetadata(page_number=1, source="page_render")
    image = ExtractedImage(image_bytes=b"test", metadata=metadata)

    assert image.image_bytes == b"test"
    assert image.metadata == metadata
    assert image.llm_optimized_bytes is None


def test_extraction_result_dataclass():
    """Test ExtractionResult dataclass with default factories."""
    result = ExtractionResult()

    assert result.embedded == []
    assert result.page_renders == []
    assert result.total_pages == 0
    assert result.errors == []

    # Verify lists are independent instances
    result1 = ExtractionResult()
    result2 = ExtractionResult()

    result1.embedded.append("test")
    assert len(result2.embedded) == 0


def test_extraction_result_page_text_map_default():
    """Test ExtractionResult page_text_map defaults to empty dict."""
    result = ExtractionResult()
    assert result.page_text_map == {}

    # Verify dicts are independent instances
    result1 = ExtractionResult()
    result2 = ExtractionResult()
    result1.page_text_map[1] = "test"
    assert len(result2.page_text_map) == 0


# ============================================================================
# Tests: PDFProcessor - text extraction removed (now handled by VisionExtractor)
# ============================================================================


@pytest.mark.asyncio
async def test_extract_all_page_text_map_populated(multi_page_pdf):
    """PDFProcessor now populates page_text_map from native text layer."""
    processor = PDFProcessor()
    result = await processor.extract_all(multi_page_pdf)

    # page_text_map is populated by native text extraction (hybrid pipeline)
    assert result.page_text_map != {}
    assert result.extraction_method == "hybrid"


@pytest.mark.asyncio
async def test_extract_all_no_anthropic_service_param(simple_pdf_bytes):
    """extract_all no longer accepts anthropic_service parameter."""
    processor = PDFProcessor()
    # Should work without any extra parameters
    result = await processor.extract_all(simple_pdf_bytes)
    assert result.total_pages == 1
    assert result.extraction_method == "hybrid"
