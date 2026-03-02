# Agent Brief: DEV-PDF-001

**Agent ID:** DEV-PDF-001
**Agent Name:** PDF Processor Agent
**Type:** Development
**Phase:** 2 - Material Preparation
**Context Budget:** 55,000 tokens

---

## Mission

Implement comprehensive triple-extraction PDF pipeline using PyMuPDF (fitz) and pymupdf4llm:
1. **Embedded extraction** - Extract raster XObjects directly
2. **Page rendering** - Render all pages at 300 DPI to capture vector content
3. **Text extraction** - Per-page markdown text via pymupdf4llm for downstream text cross-referencing

All extraction methods run for every page. Text extraction enables floor plan data fallback when image OCR lacks data.

---

## Documentation to Read

### Primary
1. `docs/02-modules/MATERIAL_PREPARATION.md` - Complete extraction requirements

### Secondary
2. `docs/04-backend/SERVICE_LAYER.md` - Service patterns
3. `docs/01-architecture/DATA_FLOW.md` - Processing pipeline

---

## Dependencies

**Upstream:** DEV-JOB-001 (job manager)
**Downstream:** DEV-IMGCLASS-001, DEV-EXTRACT-001

---

## Outputs

### `backend/app/services/pdf_processor.py`
### `backend/app/utils/pdf_helpers.py`

---

## Acceptance Criteria

### Triple Extraction Strategy
1. **Embedded Extraction:** Extract ALL embedded XObjects using `doc.extract_image(xref)`
2. **Page Rendering:** Render EVERY page at 300 DPI using `page.get_pixmap()`
3. **Text Extraction:** Extract per-page markdown using `pymupdf4llm.to_markdown(doc, page_chunks=True, ignore_images=True)`
4. All methods run for all pages (not fallback-only)
5. Skip embedded images smaller than 500x500px (decorative)
6. Text extraction failures are caught and logged; image pipeline unaffected

### Quality Preservation
5. Preserve original resolution (no downscaling) for embedded images
6. Page renders at 300 DPI for consistent quality across all image types
7. No file size limits during extraction - quality is primary

### Dual-Tier Output
8. **Tier 1 (Original):** Full quality, no compression, for final delivery
9. **Tier 2 (LLM-Optimized):** Task-specific dimensions for Claude processing
10. BOTH tiers included in output (not just originals)

### Robustness
11. Handle multi-page PDFs (up to 100 pages)
12. Memory-efficient streaming for files >20MB
13. Handle corrupted PDFs gracefully
14. Return metadata: page number, extraction source, format, dimensions, DPI

### Format Support
15. Input: PDF
16. Output: JPEG, PNG, WebP for both tiers

---

## Technical Notes

### Why Triple Extraction?
PyMuPDF's `extract_image()` only extracts embedded raster XObjects. It MISSES:
- Vector graphics (CAD floor plans, illustrations)
- Composited marketing renders
- Vector logos and location maps

Page rendering via `get_pixmap()` captures ALL visual content.

**Text extraction** via `pymupdf4llm` provides per-page markdown with reading order detection,
table extraction, and header identification. This text flows to `FloorPlanExtractor` via
`page_text_map` for unit type cross-referencing when image OCR returns null.

### Implementation Pattern

```python
import fitz  # PyMuPDF
from typing import Dict, List

import fitz
import pymupdf4llm

class PDFProcessor:
    async def extract_all(self, pdf_bytes: bytes) -> ExtractionResult:
        """Triple extraction: embedded + page renders + text"""
        # EXTRACTION 1: Embedded raster images (doc.extract_image(xref))
        # EXTRACTION 2: Full page render at 300 DPI (page.get_pixmap())
        # EXTRACTION 3: Per-page markdown text (pymupdf4llm.to_markdown())
        ...

    def _extract_text(self, pdf_bytes, total_pages) -> dict[int, str]:
        """Uses pymupdf4llm with page_chunks=True, ignore_images=True."""
        ...
```

### Output Structure (ExtractionResult dataclass)
```
{
    "embedded": [...],          # Direct XObject extraction
    "page_renders": [...],      # Full page renders (captures vectors)
    "page_text_map": {          # Per-page markdown text (1-indexed)
        1: "# Project Name\n...",
        2: "## Unit Types\n...",
    },
    "total_pages": int,
    "errors": [...]
}
```

---

## QA Pair: QA-PDF-001

---

**Begin execution.**
