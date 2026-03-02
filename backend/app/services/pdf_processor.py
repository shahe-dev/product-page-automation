"""
PDF Processor Service (DEV-PDF-001)

Triple-extraction pipeline for PDF processing:
1. Embedded extraction - Extract raster XObjects directly via PyMuPDF
2. Page rendering - Render all pages at adaptive DPI to capture vector content
3. Native text layer - Extract text from the PDF data stream (lossless, no OCR)

The native text layer provides exact numeric values from digital PDFs.
Pages with rich native text skip Vision OCR downstream (hybrid routing).
"""

import logging
from typing import Optional

import fitz  # PyMuPDF
import psutil

from app.utils.pdf_helpers import (
    ExtractedImage,
    ExtractionResult,
    ImageMetadata,
    create_llm_optimized,
    is_valid_embedded_image,
    validate_pdf_bytes,
    RENDER_DPI,
)

logger = logging.getLogger(__name__)

# Memory guard: skip PDFs larger than 500MB
MAX_PDF_SIZE = 500 * 1024 * 1024
MAX_PAGES = 100

# Memory pressure threshold - skip page renders if system memory exceeds this
# Set to 90% to avoid triggering during normal operation while still catching OOM risk
MAX_MEMORY_PERCENT = 90


def _calculate_render_dpi(total_pages: int, pdf_size_mb: float) -> int:
    """
    Calculate adaptive render DPI based on PDF size to prevent OOM.

    Large PDFs get lower DPI to reduce memory usage:
    - >50 pages or >100MB: 150 DPI (half resolution)
    - >20 pages or >50MB: 200 DPI (reduced)
    - Otherwise: 300 DPI (full resolution)

    Args:
        total_pages: Number of pages in the PDF
        pdf_size_mb: PDF file size in megabytes

    Returns:
        DPI value to use for page rendering
    """
    if total_pages > 50 or pdf_size_mb > 100:
        return 150  # Half resolution for large PDFs
    if total_pages > 20 or pdf_size_mb > 50:
        return 200  # Reduced resolution for medium PDFs
    return 300  # Full resolution for small PDFs


def _check_memory_pressure() -> bool:
    """
    Check if system memory usage exceeds threshold.

    Returns:
        True if memory pressure is high and rendering should be skipped
    """
    try:
        return psutil.virtual_memory().percent > MAX_MEMORY_PERCENT
    except Exception:
        return False  # If we can't check, assume OK


class PDFProcessor:
    """
    Extracts images and text from PDF documents using triple extraction.

    Embedded extraction captures raster XObjects directly.
    Page rendering at 300 DPI captures vector graphics, composited
    marketing renders, and other content missed by embedded extraction.
    Native text layer provides exact text from the PDF data stream.
    """

    def __init__(self, render_dpi: int = RENDER_DPI, max_pages: int = MAX_PAGES):
        self.render_dpi = render_dpi
        self.dpi_scale = render_dpi / 72
        self.max_pages = max_pages

    async def extract_all(
        self,
        pdf_bytes: bytes,
    ) -> ExtractionResult:
        """
        Run dual extraction on a PDF document.

        Args:
            pdf_bytes: Raw PDF file content.

        Returns:
            ExtractionResult with embedded images and page renders.
        """
        if not validate_pdf_bytes(pdf_bytes):
            raise ValueError("Invalid PDF: missing PDF header")

        if len(pdf_bytes) > MAX_PDF_SIZE:
            raise ValueError(f"PDF exceeds {MAX_PDF_SIZE // (1024 * 1024)}MB limit")

        result = ExtractionResult()
        page_num = 0

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Failed to open PDF: %s", e)
            raise ValueError(f"Corrupted or unreadable PDF: {e}") from e

        # Document-level xref tracking to prevent extracting same image from multiple pages
        seen_xrefs: set[int] = set()

        try:
            result.total_pages = min(len(doc), self.max_pages)

            # Calculate adaptive DPI based on PDF size to prevent OOM
            # Only downgrade DPI for large PDFs; never upgrade beyond user-specified value
            pdf_size_mb = len(pdf_bytes) / (1024 * 1024)
            adaptive_dpi = _calculate_render_dpi(result.total_pages, pdf_size_mb)
            effective_dpi = min(self.render_dpi, adaptive_dpi)
            if effective_dpi != self.render_dpi:
                logger.info(
                    "Reducing DPI from %d to %d for %d pages, %.1fMB PDF",
                    self.render_dpi,
                    effective_dpi,
                    result.total_pages,
                    pdf_size_mb,
                )
                self.dpi_scale = effective_dpi / 72
                self.render_dpi = effective_dpi

            for page_num in range(result.total_pages):
                page = doc[page_num]

                # Extraction 1: Embedded raster images (with cross-page dedup)
                embedded = self._extract_embedded(doc, page, page_num, seen_xrefs)
                result.embedded.extend(embedded)

                # Extraction 2: Full page render at 300 DPI
                rendered = self._render_page(page, page_num)
                if rendered is not None:
                    result.page_renders.append(rendered)

                # Extraction 3: Native text layer (lossless, no OCR)
                try:
                    page_text = page.get_text("text").strip()
                    page_1indexed = page_num + 1
                    result.page_char_counts[page_1indexed] = len(page_text)
                    if page_text:
                        result.page_text_map[page_1indexed] = page_text
                except Exception as e:
                    logger.warning(
                        "Text extraction failed for page %d: %s",
                        page_num + 1, e,
                    )

        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Error during extraction at page %d: %s", page_num + 1, e)
            result.errors.append({"page": page_num + 1, "error": str(e)})
        finally:
            doc.close()

        result.extraction_method = "hybrid"

        logger.info(
            "PDF extraction complete: %d embedded, %d page renders, %d pages, %d errors",
            len(result.embedded),
            len(result.page_renders),
            result.total_pages,
            len(result.errors),
        )

        return result

    def _extract_embedded(
        self, doc: fitz.Document, page: fitz.Page, page_num: int, seen_xrefs: set[int]
    ) -> list[ExtractedImage]:
        """Extract all embedded raster images from a page.

        Args:
            doc: The PDF document.
            page: The current page.
            page_num: Zero-indexed page number.
            seen_xrefs: Document-level set of already extracted xrefs for cross-page dedup.

        Returns:
            List of ExtractedImage objects for images not yet seen.
        """
        images = []

        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in seen_xrefs:
                logger.debug(
                    "Skipping duplicate xref=%d on page %d (already extracted)",
                    xref,
                    page_num + 1,
                )
                continue
            seen_xrefs.add(xref)

            try:
                base_image = doc.extract_image(xref)
                if base_image is None:
                    continue

                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                if not is_valid_embedded_image(width, height):
                    logger.debug(
                        "Skipping small embedded image xref=%d (%dx%d) on page %d",
                        xref,
                        width,
                        height,
                        page_num + 1,
                    )
                    continue

                raw_bytes = base_image["image"]
                ext = base_image.get("ext", "png")

                metadata = ImageMetadata(
                    page_number=page_num + 1,
                    source="embedded",
                    width=width,
                    height=height,
                    format=ext,
                    dpi=72,
                    xref=xref,
                    file_size=len(raw_bytes),
                    color_space=base_image.get("colorspace_name", ""),
                    bits_per_component=base_image.get("bpc", 8),
                )

                llm_bytes = create_llm_optimized(raw_bytes)

                images.append(
                    ExtractedImage(
                        image_bytes=raw_bytes,
                        metadata=metadata,
                        llm_optimized_bytes=llm_bytes,
                    )
                )

            except Exception as e:
                logger.warning(
                    "Failed to extract embedded image xref=%d on page %d: %s",
                    xref,
                    page_num + 1,
                    e,
                )

        return images

    def _render_page(self, page: fitz.Page, page_num: int) -> Optional[ExtractedImage]:
        """Render a full page at configured DPI."""
        # Memory guard: skip rendering if system memory is under pressure
        if _check_memory_pressure():
            logger.warning(
                "Skipping page %d render due to memory pressure (>%d%% used)",
                page_num + 1,
                MAX_MEMORY_PERCENT,
            )
            return None

        try:
            mat = fitz.Matrix(self.dpi_scale, self.dpi_scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            raw_bytes = pix.tobytes("png")

            width = pix.width
            height = pix.height

            metadata = ImageMetadata(
                page_number=page_num + 1,
                source="page_render",
                width=width,
                height=height,
                format="png",
                dpi=self.render_dpi,
                file_size=len(raw_bytes),
            )

            llm_bytes = create_llm_optimized(raw_bytes)

            return ExtractedImage(
                image_bytes=raw_bytes,
                metadata=metadata,
                llm_optimized_bytes=llm_bytes,
            )

        except Exception as e:
            logger.warning("Failed to render page %d: %s", page_num + 1, e)
            return None

    def get_extraction_summary(self, result: ExtractionResult) -> dict:
        """Build a summary dict for the extraction result."""
        return {
            "total_embedded": len(result.embedded),
            "total_page_renders": len(result.page_renders),
            "total_pages": result.total_pages,
            "extraction_method": result.extraction_method,
            "render_dpi": self.render_dpi,
            "errors": result.errors,
        }
