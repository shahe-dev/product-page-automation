# Ironclad Hybrid Extraction Pipeline - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the Vision-only PDF extraction pipeline with a hybrid multi-layer system that cross-validates text extraction, regex patterns, table parsing, and Vision OCR to guarantee data fidelity.

**Architecture:** Four extraction layers run in parallel -- (1) PyMuPDF native text layer, (2) pdfplumber table extraction, (3) DataExtractor regex pre-extraction, (4) Vision OCR (visual pages only). A reconciliation layer cross-validates numeric fields between methods, preferring text-layer values for numbers and LLM values for semantic fields. Floor plans use pdfplumber tables as primary source with Vision as secondary.

**Tech Stack:** PyMuPDF (text layer), pdfplumber (tables), DataExtractor (regex), Claude Vision (visual OCR), DataStructurer (LLM structuring with pre_extracted hints)

---

## Context: Why This Change Is Needed

The Vision-only pipeline (shipped 2026-02-09) introduced catastrophic regression:

1. **Digit transposition**: Vision OCR misread floor plan areas (51.57 sqm -> 61.37, 78.50 -> 78.05, 11.78 -> 1.78)
2. **Map label contamination**: Location proximity page had 40+ hotel/landmark labels read from map illustration, wrong proximity values
3. **Sparse structuring**: 993 bytes of structured data from a 24-page brochure -- missed floor plan specs, payment plan, most numeric fields
4. **Floor plan nulls**: 7/7 floor plans had mostly null fields (Vision failed on corrupt images + misread numbers on valid ones)
5. **No regex pre-extraction**: DataExtractor regex pass was removed when Vision was added, losing free high-confidence anchors

The old pipeline (pymupdf text + regex + Claude structuring) was 100% accurate on numbers from digital PDFs because it read the text data stream directly. The new pipeline renders pages as images and asks an LLM to OCR them -- fundamentally inferior for text-native content.

**Root cause**: We replaced a lossless text extraction path with a lossy image->OCR path for ALL pages, including pages where the text layer is perfectly readable.

**Fix**: Hybrid approach. Use text layer as ground truth for digital content. Use Vision only where the text layer is insufficient (graphic-heavy pages, embedded text in images). Cross-validate everything.

---

## Task 1: Add pdfplumber Dependency and Table Extraction Service

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/services/table_extractor.py`
- Create: `backend/tests/test_table_extractor.py`

pdfplumber extracts tables from digital PDFs with 96% accuracy, no OCR needed. It reads the PDF data stream directly (like pymupdf text extraction) so numbers are exact. This is critical for floor plan specification tables and payment plan tables.

**Step 1: Add pdfplumber to requirements.txt**

Add after `PyMuPDF>=1.26.6` line in `backend/requirements.txt`:
```
pdfplumber>=0.11.0
```

**Step 2: Write failing tests for TableExtractor**

Create `backend/tests/test_table_extractor.py`:
```python
"""Tests for table_extractor service."""
import pytest
from unittest.mock import patch, MagicMock
from app.services.table_extractor import TableExtractor, ExtractedTable, TableType


class TestTableExtractor:
    """Tests for TableExtractor."""

    def setup_method(self):
        self.extractor = TableExtractor()

    def test_classify_floor_plan_table(self):
        """Tables with sqft/sqm/bedroom headers are floor plan tables."""
        headers = ["Type", "Bedrooms", "Area (sqft)", "Balcony (sqft)"]
        assert self.extractor._classify_table(headers) == TableType.FLOOR_PLAN

    def test_classify_payment_plan_table(self):
        """Tables with percentage/milestone headers are payment plan tables."""
        headers = ["Milestone", "Percentage", "Due Date"]
        assert self.extractor._classify_table(headers) == TableType.PAYMENT_PLAN

    def test_classify_unknown_table(self):
        """Tables with no recognized headers are UNKNOWN."""
        headers = ["Column A", "Column B"]
        assert self.extractor._classify_table(headers) == TableType.UNKNOWN

    def test_parse_floor_plan_rows(self):
        """Floor plan rows are parsed into structured dicts with numeric conversion."""
        rows = [
            ["1BR Type A", "1", "1", "554", "63", ""],
            ["2BR Type A", "2", "2", "991", "127", ""],
        ]
        headers = ["Unit Type", "Bedrooms", "Bathrooms", "Total Area (sqft)", "Balcony (sqft)", "Notes"]
        result = self.extractor._parse_floor_plan_table(headers, rows)
        assert len(result) == 2
        assert result[0]["unit_type"] == "1BR Type A"
        assert result[0]["total_sqft"] == 554.0
        assert result[1]["bedrooms"] == 2

    def test_parse_payment_plan_rows(self):
        """Payment plan rows are parsed with percentage extraction."""
        rows = [
            ["On Booking", "20%"],
            ["During Construction", "50%"],
            ["On Handover", "30%"],
        ]
        headers = ["Milestone", "Percentage"]
        result = self.extractor._parse_payment_plan_table(headers, rows)
        assert result["down_payment"] == "20%"

    def test_sqm_to_sqft_conversion(self):
        """Values labeled sqm are auto-converted to sqft."""
        headers = ["Unit Type", "Area (sqm)"]
        rows = [["1BR", "51.57"]]
        result = self.extractor._parse_floor_plan_table(headers, rows)
        # 51.57 * 10.764 = 555.1
        assert abs(result[0]["total_sqft"] - 555.1) < 1.0

    def test_empty_pdf_returns_empty(self):
        """Empty/invalid PDF bytes return empty result."""
        result = self.extractor.extract_tables(b"not a pdf")
        assert result.tables == []

    def test_percentage_parsing(self):
        """Percentages are extracted from various formats."""
        assert self.extractor._parse_percentage("20%") == 20.0
        assert self.extractor._parse_percentage("20 %") == 20.0
        assert self.extractor._parse_percentage("20") == 20.0
        assert self.extractor._parse_percentage("N/A") is None
```

**Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_table_extractor.py -v
```
Expected: FAIL (module not found)

**Step 4: Implement TableExtractor**

Create `backend/app/services/table_extractor.py`:
```python
"""
Table Extractor Service

Extracts structured tables from PDF documents using pdfplumber.
Classifies tables as floor plan specs, payment plans, or unknown.
Returns exact numeric values from the PDF data stream (no OCR).
"""

import enum
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)

SQM_TO_SQFT = 10.764


class TableType(enum.Enum):
    FLOOR_PLAN = "floor_plan"
    PAYMENT_PLAN = "payment_plan"
    UNKNOWN = "unknown"


@dataclass
class ExtractedTable:
    """A single extracted and classified table."""
    table_type: TableType
    page_number: int
    headers: list[str]
    rows: list[list[str]]
    parsed_data: list[dict] | dict | None = None


@dataclass
class TableExtractionResult:
    """All tables extracted from a PDF."""
    tables: list[ExtractedTable] = field(default_factory=list)
    floor_plan_specs: list[dict] = field(default_factory=list)
    payment_plan: Optional[dict] = None
    errors: list[str] = field(default_factory=list)


# Header keywords for table classification
FLOOR_PLAN_KEYWORDS = {
    "sqft", "sq ft", "sq.ft", "sqm", "sq m", "sq.m",
    "area", "bedroom", "bathroom", "unit type", "type",
    "balcony", "built-up", "builtup", "built up", "terrace",
}
PAYMENT_PLAN_KEYWORDS = {
    "milestone", "percentage", "payment", "installment",
    "booking", "construction", "handover", "completion",
    "down payment", "post-handover", "post handover",
}


class TableExtractor:
    """
    Extracts tables from PDF using pdfplumber.

    Tables are classified as floor_plan, payment_plan, or unknown.
    Floor plan tables have numeric values auto-parsed and sqm->sqft converted.
    Payment plan tables have percentages extracted.
    """

    def extract_tables(self, pdf_bytes: bytes) -> TableExtractionResult:
        """Extract all tables from PDF bytes."""
        result = TableExtractionResult()

        try:
            import io
            pdf = pdfplumber.open(io.BytesIO(pdf_bytes))
        except Exception as e:
            logger.warning("pdfplumber failed to open PDF: %s", e)
            result.errors.append(str(e))
            return result

        try:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                if not tables:
                    continue

                for raw_table in tables:
                    if not raw_table or len(raw_table) < 2:
                        continue

                    # First row is headers
                    headers = [str(c or "").strip() for c in raw_table[0]]
                    rows = [
                        [str(c or "").strip() for c in row]
                        for row in raw_table[1:]
                        if any(str(c or "").strip() for c in row)
                    ]

                    if not headers or not rows:
                        continue

                    table_type = self._classify_table(headers)
                    table = ExtractedTable(
                        table_type=table_type,
                        page_number=page_num,
                        headers=headers,
                        rows=rows,
                    )

                    if table_type == TableType.FLOOR_PLAN:
                        parsed = self._parse_floor_plan_table(headers, rows)
                        table.parsed_data = parsed
                        result.floor_plan_specs.extend(parsed)
                    elif table_type == TableType.PAYMENT_PLAN:
                        parsed = self._parse_payment_plan_table(headers, rows)
                        table.parsed_data = parsed
                        if not result.payment_plan:
                            result.payment_plan = parsed

                    result.tables.append(table)
        except Exception as e:
            logger.error("Table extraction failed: %s", e)
            result.errors.append(str(e))
        finally:
            pdf.close()

        logger.info(
            "Table extraction: %d tables (%d floor plan, %d payment plan)",
            len(result.tables),
            sum(1 for t in result.tables if t.table_type == TableType.FLOOR_PLAN),
            sum(1 for t in result.tables if t.table_type == TableType.PAYMENT_PLAN),
        )
        return result

    def _classify_table(self, headers: list[str]) -> TableType:
        """Classify a table based on its header content."""
        header_text = " ".join(h.lower() for h in headers)

        fp_score = sum(1 for kw in FLOOR_PLAN_KEYWORDS if kw in header_text)
        pp_score = sum(1 for kw in PAYMENT_PLAN_KEYWORDS if kw in header_text)

        if fp_score >= 2:
            return TableType.FLOOR_PLAN
        if pp_score >= 2:
            return TableType.PAYMENT_PLAN
        # Single keyword match with heuristics
        if fp_score == 1 and any(kw in header_text for kw in ("sqft", "sqm", "area")):
            return TableType.FLOOR_PLAN
        if pp_score == 1 and any(kw in header_text for kw in ("milestone", "payment")):
            return TableType.PAYMENT_PLAN
        return TableType.UNKNOWN

    def _parse_floor_plan_table(
        self, headers: list[str], rows: list[list[str]]
    ) -> list[dict]:
        """Parse floor plan table rows into structured dicts."""
        # Map header positions to semantic fields
        col_map = self._map_floor_plan_columns(headers)
        is_sqm = any("sqm" in h.lower() or "sq m" in h.lower() or "sq.m" in h.lower() for h in headers)

        parsed = []
        for row in rows:
            entry: dict = {}
            for col_idx, cell in enumerate(row):
                field_name = col_map.get(col_idx)
                if not field_name or not cell.strip():
                    continue

                if field_name == "unit_type":
                    entry["unit_type"] = cell.strip()
                elif field_name in ("bedrooms", "bathrooms"):
                    val = self._parse_number(cell)
                    if val is not None:
                        entry[field_name] = int(val) if field_name == "bedrooms" else val
                elif field_name in ("total_sqft", "balcony_sqft", "builtup_sqft", "terrace_sqft"):
                    val = self._parse_number(cell)
                    if val is not None:
                        if is_sqm:
                            val = round(val * SQM_TO_SQFT, 1)
                        entry[field_name] = val

            if entry:
                parsed.append(entry)

        return parsed

    def _map_floor_plan_columns(self, headers: list[str]) -> dict[int, str]:
        """Map column indices to semantic field names."""
        col_map: dict[int, str] = {}
        for idx, header in enumerate(headers):
            h = header.lower().strip()
            if any(kw in h for kw in ("unit type", "type", "unit")):
                col_map[idx] = "unit_type"
            elif any(kw in h for kw in ("bedroom", "bed", "br")):
                col_map[idx] = "bedrooms"
            elif any(kw in h for kw in ("bathroom", "bath")):
                col_map[idx] = "bathrooms"
            elif any(kw in h for kw in ("total area", "total sqft", "total sq", "area")):
                # "area" alone maps to total only if no other area column already mapped
                if "total_sqft" not in col_map.values():
                    col_map[idx] = "total_sqft"
            elif any(kw in h for kw in ("balcony",)):
                col_map[idx] = "balcony_sqft"
            elif any(kw in h for kw in ("built-up", "builtup", "built up")):
                col_map[idx] = "builtup_sqft"
            elif any(kw in h for kw in ("terrace",)):
                col_map[idx] = "terrace_sqft"
        return col_map

    def _parse_payment_plan_table(
        self, headers: list[str], rows: list[list[str]]
    ) -> dict:
        """Parse payment plan table into structured dict."""
        result: dict = {}

        # Find milestone and percentage columns
        milestone_col = None
        pct_col = None
        for idx, h in enumerate(headers):
            hl = h.lower()
            if any(kw in hl for kw in ("milestone", "stage", "event", "description")):
                milestone_col = idx
            if any(kw in hl for kw in ("percentage", "%", "amount", "payment")):
                pct_col = idx

        if milestone_col is None:
            milestone_col = 0
        if pct_col is None:
            pct_col = 1 if len(headers) > 1 else 0

        for row in rows:
            if len(row) <= max(milestone_col, pct_col):
                continue
            milestone = row[milestone_col].lower().strip()
            pct_str = row[pct_col].strip()

            if any(kw in milestone for kw in ("booking", "down payment", "reservation")):
                result["down_payment"] = pct_str
            elif any(kw in milestone for kw in ("construction", "during")):
                result["during_construction"] = pct_str
            elif "post" in milestone and "handover" in milestone:
                result["post_handover"] = pct_str
            elif any(kw in milestone for kw in ("handover", "completion", "delivery")):
                result["on_handover"] = pct_str

        return result

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse a numeric value from text, handling commas and whitespace."""
        cleaned = text.replace(",", "").replace(" ", "").strip()
        match = re.search(r"[\d.]+", cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    def _parse_percentage(self, text: str) -> Optional[float]:
        """Parse a percentage value from text."""
        if not text or text.strip().upper() in ("N/A", "-", ""):
            return None
        cleaned = text.replace("%", "").replace(" ", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
```

**Step 5: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_table_extractor.py -v
```
Expected: all 9 tests PASS

**Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/services/table_extractor.py backend/tests/test_table_extractor.py
git commit -m "feat: add pdfplumber table extraction service for floor plans and payment plans"
```

---

## Task 2: Restore PyMuPDF Text Layer Extraction in PDFProcessor

**Files:**
- Modify: `backend/app/services/pdf_processor.py` (lines 93-172)
- Modify: `backend/app/utils/pdf_helpers.py` (ExtractionResult dataclass)
- Create: `backend/tests/test_pdf_text_extraction.py`

The PDFProcessor currently skips text extraction entirely (comment at line 161: "Text extraction is now handled by VisionExtractor"). We restore native text extraction using `page.get_text("text")` which reads the PDF data stream directly -- zero OCR errors.

**Step 1: Write failing test**

Create `backend/tests/test_pdf_text_extraction.py`:
```python
"""Tests for restored text layer extraction in PDFProcessor."""
import pytest
from unittest.mock import patch, MagicMock
from app.services.pdf_processor import PDFProcessor


class TestTextLayerExtraction:
    """Test that PDFProcessor extracts native text layer."""

    def setup_method(self):
        self.processor = PDFProcessor()

    @pytest.mark.asyncio
    async def test_page_text_map_populated(self):
        """extract_all() populates page_text_map from native text layer."""
        # Create a minimal valid PDF with text
        import fitz
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
        import fitz
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
        import fitz
        from PIL import Image
        import io

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
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_pdf_text_extraction.py -v
```
Expected: FAIL (page_text_map empty, page_char_counts missing)

**Step 3: Modify PDFProcessor to restore text extraction**

In `backend/app/services/pdf_processor.py`, inside the `for page_num` loop (around line 143-159):

Add text extraction after embedded extraction and page rendering. Also add `page_char_counts` dict to ExtractionResult.

Changes to `backend/app/utils/pdf_helpers.py` -- add `page_char_counts` field to `ExtractionResult`:
```python
# In ExtractionResult dataclass, add:
page_char_counts: dict[int, int] = field(default_factory=dict)
```

Changes to `backend/app/services/pdf_processor.py`:

After the page rendering block (after line 153 `result.page_renders.append(rendered)`), add:
```python
# Extraction 3: Native text layer (lossless, no OCR)
try:
    page_text = page.get_text("text").strip()
    page_1indexed = page_num + 1
    result.page_char_counts[page_1indexed] = len(page_text)
    if page_text:
        result.page_text_map[page_1indexed] = page_text
except Exception as e:
    logger.warning("Text extraction failed for page %d: %s", page_num + 1, e)
```

Change the `extraction_method` assignment (line 162) from:
```python
result.extraction_method = "vision"
```
to:
```python
result.extraction_method = "hybrid"
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_pdf_text_extraction.py -v
```
Expected: all 3 tests PASS

**Step 5: Run existing PDF processor tests**

```bash
cd backend && python -m pytest tests/test_pdf_processor.py -v
```
Expected: existing tests still pass (text extraction is additive, not breaking)

**Step 6: Commit**

```bash
git add backend/app/services/pdf_processor.py backend/app/utils/pdf_helpers.py backend/tests/test_pdf_text_extraction.py
git commit -m "feat: restore native text layer extraction in PDFProcessor for hybrid pipeline"
```

---

## Task 3: Image Validation Guard

**Files:**
- Create: `backend/app/utils/image_validation.py`
- Create: `backend/tests/test_image_validation.py`
- Modify: `backend/app/services/floor_plan_extractor.py` (line 139, in extract_floor_plans)
- Modify: `backend/app/services/image_classifier.py` (before Vision API calls)

7/51 embedded images from EVELYN were corrupt (vector/SVG objects from PyMuPDF that Pillow can't open). These caused cascading failures: pHash dedup errors, 400 errors from Anthropic ("image cannot be empty"), and image optimizer errors. A validation guard filters these before any downstream processing.

**Step 1: Write failing tests**

Create `backend/tests/test_image_validation.py`:
```python
"""Tests for image validation utility."""
import io
import pytest
from PIL import Image
from app.utils.image_validation import validate_image_bytes


class TestImageValidation:
    def test_valid_jpeg(self):
        """Valid JPEG passes validation."""
        img = Image.new("RGB", (200, 200), "blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        assert validate_image_bytes(buf.getvalue()) is True

    def test_valid_png(self):
        """Valid PNG passes validation."""
        img = Image.new("RGB", (200, 200), "green")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        assert validate_image_bytes(buf.getvalue()) is True

    def test_corrupt_bytes(self):
        """Random bytes fail validation."""
        assert validate_image_bytes(b"not an image at all") is False

    def test_empty_bytes(self):
        """Empty bytes fail validation."""
        assert validate_image_bytes(b"") is False

    def test_too_small(self):
        """Images smaller than 50x50 fail validation."""
        img = Image.new("RGB", (10, 10), "red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        assert validate_image_bytes(buf.getvalue(), min_width=50, min_height=50) is False

    def test_svg_xml_fails(self):
        """SVG/XML content fails validation."""
        svg = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'
        assert validate_image_bytes(svg) is False
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_image_validation.py -v
```

**Step 3: Implement image validation**

Create `backend/app/utils/image_validation.py`:
```python
"""Image validation utility for filtering corrupt/invalid images before API calls."""

import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def validate_image_bytes(
    image_bytes: bytes,
    min_width: int = 50,
    min_height: int = 50,
) -> bool:
    """Validate that image bytes represent a valid raster image.

    Args:
        image_bytes: Raw image data.
        min_width: Minimum acceptable width in pixels.
        min_height: Minimum acceptable height in pixels.

    Returns:
        True if the image is valid and meets size requirements.
    """
    if not image_bytes or len(image_bytes) < 8:
        return False

    # Reject SVG/XML content
    header = image_bytes[:100]
    if b"<?xml" in header or b"<svg" in header:
        return False

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()  # Checks integrity without decoding full image
        # Re-open after verify (verify closes the file)
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        if w < min_width or h < min_height:
            return False
        return True
    except Exception:
        return False
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_image_validation.py -v
```
Expected: all 6 PASS

**Step 5: Wire validation into floor_plan_extractor.py and image_classifier.py**

In `backend/app/services/floor_plan_extractor.py`, at the top of `extract_floor_plans()` (around line 139), add a pre-filter:
```python
from app.utils.image_validation import validate_image_bytes

# Pre-filter corrupt images before dedup and Vision API calls
valid_images = []
for image in floor_plan_images:
    if validate_image_bytes(image.image_bytes):
        valid_images.append(image)
    else:
        logger.warning(
            "Skipping corrupt floor plan image on page %d",
            image.metadata.page_number,
        )
        result.errors.append({
            "page": image.metadata.page_number,
            "error": "corrupt or invalid image bytes",
        })
floor_plan_images = valid_images
```

Similarly in `backend/app/services/image_classifier.py`, add validation before Vision API calls in `classify_extraction()` (filter out invalid images before the classification loop).

**Step 6: Commit**

```bash
git add backend/app/utils/image_validation.py backend/tests/test_image_validation.py \
      backend/app/services/floor_plan_extractor.py backend/app/services/image_classifier.py
git commit -m "feat: add image validation guard to prevent corrupt images reaching Vision API"
```

---

## Task 4: Expand DataExtractor Known Entities and Restore Regex Pass

**Files:**
- Modify: `backend/app/services/data_extractor.py` (lines 24-50: DUBAI_COMMUNITIES, KNOWN_DEVELOPERS)
- Create: `backend/tests/test_data_extractor_expanded.py`

The existing DataExtractor is missing many UAE developers and communities. NSHAMA (EVELYN's developer) is not in KNOWN_DEVELOPERS. Town Square (EVELYN's community) is not in DUBAI_COMMUNITIES. This means regex extraction returns low/zero confidence for these fields.

**Step 1: Write failing tests**

Create `backend/tests/test_data_extractor_expanded.py`:
```python
"""Tests for expanded DataExtractor patterns."""
import pytest
from app.services.data_extractor import DataExtractor, KNOWN_DEVELOPERS, DUBAI_COMMUNITIES


class TestExpandedPatterns:
    def setup_method(self):
        self.extractor = DataExtractor()

    def test_nshama_in_known_developers(self):
        assert any("NSHAMA" in d.upper() or "Nshama" in d for d in KNOWN_DEVELOPERS)

    def test_town_square_in_communities(self):
        assert any("Town Square" in c for c in DUBAI_COMMUNITIES)

    def test_extract_nshama_developer(self):
        text = "EVELYN on the Park by Nshama in Town Square, Dubai"
        result = self.extractor.extract_developer(text)
        assert result.value is not None
        assert "nshama" in result.value.lower()
        assert result.confidence >= 0.7

    def test_extract_town_square_community(self):
        text = "Located in Town Square, Dubai"
        result = self.extractor.extract_location(text)
        assert result.community is not None
        assert "Town Square" in result.community

    def test_extract_aed_price_with_comma(self):
        text = "Starting from AED 820,000"
        result = self.extractor.extract_prices(text)
        assert result.min_price == 820000 or 820000 in [result.min_price, result.max_price]

    def test_extract_sqft_from_text(self):
        """Regex extracts area in sqft format."""
        text = "Total area: 554 sq.ft. Balcony: 63 sq.ft."
        result = self.extractor.extract_floor_plan_specs(text)
        assert result is not None  # Method may need to be added

    def test_handover_date_extraction(self):
        text = "Expected handover: Q4 2027"
        result = self.extractor.extract_completion_date(text)
        assert result.value is not None
        assert "2027" in result.value

    def test_payment_plan_extraction(self):
        text = "Payment Plan: 80/20. 80% during construction, 20% on handover."
        result = self.extractor.extract_payment_plan(text)
        assert result.confidence > 0
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_data_extractor_expanded.py -v
```
Expected: at least the NSHAMA and Town Square tests FAIL

**Step 3: Expand entity lists in data_extractor.py**

Add to `KNOWN_DEVELOPERS` (line 39-44):
```python
KNOWN_DEVELOPERS = [
    "Emaar", "DAMAC", "Nakheel", "Meraas", "Dubai Properties",
    "Sobha", "Azizi", "Omniyat", "Select Group", "Ellington",
    "Binghatti", "Danube", "Samana", "Vincitore", "MAG",
    "Deyaar", "Union Properties", "Tiger", "Gemini", "Mag Lifestyle",
    # Added Phase 5
    "Nshama", "Reportage", "Aldar", "Eagle Hills", "Bloom",
    "Arada", "Majid Al Futtaim", "Al Habtoor", "IRTH", "Wasl",
    "Dubai Holding", "Meydan", "Tilal Al Ghaf", "RAK Properties",
    "Palma Holding", "Prestige One", "Object 1", "Imtiaz",
]
```

Add to `DUBAI_COMMUNITIES` (line 24-36):
```python
# After existing entries, add:
    "Town Square", "Expo City", "Dubai Islands", "Rashid Yachts & Marina",
    "City Walk", "La Mer", "Port de La Mer", "Bluewaters",
    "Dubai Harbour", "Emaar South", "Dubai Hills", "Villanova",
    "Mudon", "Remraam", "Al Reef", "Saadiyat Island",
    "Yas Island", "Al Reem Island", "MBR City",
    "Jumeirah Golf Estates", "Dubai Creek Residences",
    "Sobha Hartland", "The Valley", "Tilal Al Ghaf",
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_data_extractor_expanded.py -v
```

**Step 5: Commit**

```bash
git add backend/app/services/data_extractor.py backend/tests/test_data_extractor_expanded.py
git commit -m "feat: expand known developers and communities in DataExtractor regex patterns"
```

---

## Task 5: Per-Page Routing and Selective Vision OCR

**Files:**
- Modify: `backend/app/services/vision_extractor.py` (extract_pages method)
- Create: `backend/tests/test_page_routing.py`

Currently ALL pages are sent to Vision OCR. With text layer extraction restored, we only need Vision for pages where the native text is insufficient (graphic-heavy pages, text embedded in images). This saves 50-80% of Vision API cost and eliminates OCR errors on text-rich pages.

**Routing rule**: A page is "text-rich" if its native text layer has >= 200 characters. Text-rich pages use the native text directly. Visual pages (< 200 chars) get Vision OCR.

**Step 1: Write failing tests**

Create `backend/tests/test_page_routing.py`:
```python
"""Tests for per-page routing in VisionExtractor."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.vision_extractor import VisionExtractor, PageExtractionResult


class TestPageRouting:
    def setup_method(self):
        self.extractor = VisionExtractor()

    def test_text_rich_page_skips_vision(self):
        """Pages with >= 200 chars of native text skip Vision OCR."""
        page_char_counts = {1: 500, 2: 50, 3: 300}
        text_rich, visual = self.extractor.classify_pages(page_char_counts)
        assert 1 in text_rich
        assert 3 in text_rich
        assert 2 in visual
        assert 2 not in text_rich

    def test_empty_char_counts_all_visual(self):
        """If no char counts provided, all pages are treated as visual."""
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
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_page_routing.py -v
```

**Step 3: Modify VisionExtractor to support per-page routing**

In `backend/app/services/vision_extractor.py`:

Add `classify_pages` method and modify `extract_pages` signature to accept `page_text_map` and `page_char_counts`:

```python
TEXT_RICH_THRESHOLD = 200  # chars -- pages above this use native text

class VisionExtractor:
    MAX_CONCURRENT = 5
    MAX_PAGES = 30

    @staticmethod
    def classify_pages(
        page_char_counts: dict[int, int],
        threshold: int = TEXT_RICH_THRESHOLD,
    ) -> tuple[set[int], set[int]]:
        """Classify pages as text-rich or visual based on native text char count.

        Args:
            page_char_counts: {page_number: char_count} from PDFProcessor.
            threshold: Minimum chars for text-rich classification.

        Returns:
            (text_rich_pages, visual_pages) as sets of page numbers.
        """
        text_rich = set()
        visual = set()
        for page_num, count in page_char_counts.items():
            if count >= threshold:
                text_rich.add(page_num)
            else:
                visual.add(page_num)
        return text_rich, visual

    async def extract_pages(
        self,
        page_renders: list[ExtractedImage],
        template_type: str = "aggregators",
        page_text_map: dict[int, str] | None = None,
        page_char_counts: dict[int, int] | None = None,
    ) -> list[PageExtractionResult]:
        """Send page renders to Vision API with per-page routing.

        Text-rich pages use native text directly (no Vision API call).
        Visual pages get Vision OCR.
        """
        renders = page_renders[: self.MAX_PAGES]
        if not renders:
            return []

        # Classify pages
        text_rich_pages = set()
        if page_char_counts:
            text_rich_pages, _ = self.classify_pages(page_char_counts)

        results: list[PageExtractionResult] = []

        # Text-rich pages: use native text directly (free, lossless)
        visual_renders: list[ExtractedImage] = []
        for render in renders:
            pn = render.metadata.page_number
            if pn in text_rich_pages and page_text_map and pn in page_text_map:
                results.append(PageExtractionResult(
                    page_number=pn,
                    raw_text=page_text_map[pn],
                    token_usage={"input": 0, "output": 0},
                    cost=0.0,
                ))
            else:
                visual_renders.append(render)

        # Visual pages: Vision OCR (parallel with semaphore)
        if visual_renders:
            sem = asyncio.Semaphore(self.MAX_CONCURRENT)

            async def _extract_one(render: ExtractedImage) -> PageExtractionResult:
                async with sem:
                    return await self._extract_page(render)

            vision_results = await asyncio.gather(
                *[_extract_one(r) for r in visual_renders],
                return_exceptions=True,
            )

            for i, r in enumerate(vision_results):
                if isinstance(r, BaseException):
                    logger.error(
                        "Vision OCR failed for page %d: %s",
                        visual_renders[i].metadata.page_number, r,
                    )
                else:
                    results.append(r)

        text_rich_count = len(renders) - len(visual_renders)
        logger.info(
            "Page routing: %d text-rich (native), %d visual (Vision OCR), %d/%d succeeded",
            text_rich_count,
            len(visual_renders),
            len(results),
            len(renders),
        )
        return results
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_page_routing.py -v
```
Expected: all 4 PASS

**Step 5: Run existing vision extractor tests**

```bash
cd backend && python -m pytest tests/test_vision_extractor.py -v
```

**Step 6: Commit**

```bash
git add backend/app/services/vision_extractor.py backend/tests/test_page_routing.py
git commit -m "feat: add per-page routing -- text-rich pages skip Vision, visual pages get OCR"
```

---

## Task 6: Wire Regex Pre-Extraction and Table Data into DataStructurer

**Files:**
- Modify: `backend/app/services/job_manager.py` (lines 2063-2244: _step_extract_data, _step_structure_data)
- Create: `backend/tests/test_hybrid_extraction.py`

This is the core integration task. The extraction pipeline steps are rewired:

1. `_step_extract_data`: Now runs VisionExtractor with per-page routing (using native text + Vision)
2. **NEW**: Between extract and structure, run DataExtractor regex pass on native text to get pre_extracted hints
3. **NEW**: Between extract and structure, run TableExtractor on original PDF bytes
4. `_step_structure_data`: Passes pre_extracted hints (regex + table data) to DataStructurer

**Step 1: Write failing integration test**

Create `backend/tests/test_hybrid_extraction.py`:
```python
"""Tests for hybrid extraction pipeline wiring in job_manager."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestHybridExtractionWiring:
    """Verify that _step_extract_data feeds native text + tables + regex into structuring."""

    @pytest.mark.asyncio
    async def test_step_extract_data_populates_page_text_map(self):
        """_step_extract_data uses native text from PDFProcessor, not just Vision."""
        from app.services.job_manager import JobManager

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

        with patch("app.services.vision_extractor.VisionExtractor") as MockVE:
            mock_ve = MockVE.return_value
            mock_ve.extract_pages = AsyncMock(return_value=[
                MagicMock(page_number=1, raw_text="EVELYN on the Park by Nshama", cost=0.0)
            ])
            mock_ve.concatenate_page_text = MagicMock(return_value="EVELYN on the Park by Nshama")

            result = await jm._step_extract_data(job_id)

        # Verify extract_pages was called with page routing params
        call_kwargs = mock_ve.extract_pages.call_args
        assert "page_text_map" in (call_kwargs.kwargs if call_kwargs.kwargs else {})

    @pytest.mark.asyncio
    async def test_step_structure_data_passes_pre_extracted(self):
        """_step_structure_data passes regex pre_extracted hints to DataStructurer."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        mock_job = MagicMock()
        mock_job.template_type.value = "aggregators"
        jm.job_repo.get_job = AsyncMock(return_value=mock_job)

        jm._pipeline_ctx[job_id] = {
            "vision_full_text": "EVELYN on the Park by Nshama, Town Square, Dubai. AED 820,000",
            "page_extraction_results": [],
            "extraction": MagicMock(
                page_text_map={1: "EVELYN on the Park by Nshama, Town Square, Dubai. AED 820,000"},
                pdf_bytes=b"",
            ),
        }

        with patch("app.services.data_structurer.DataStructurer") as MockDS:
            mock_ds = MockDS.return_value
            mock_struct = MagicMock()
            mock_struct.project_name = "EVELYN on the Park"
            mock_struct.developer = "Nshama"
            mock_ds.structure = AsyncMock(return_value=mock_struct)

            with patch("app.services.data_extractor.DataExtractor") as MockDE:
                mock_de = MockDE.return_value
                mock_extraction = MagicMock()
                mock_extraction.prices.min_price = 820000
                mock_extraction.location.emirate = "Dubai"
                mock_extraction.location.community = "Town Square"
                mock_extraction.developer.value = "Nshama"
                mock_extraction.developer.confidence = 0.9
                mock_de.extract = MagicMock(return_value=mock_extraction)

                await jm._step_structure_data(job_id)

        # Verify DataStructurer.structure() was called with pre_extracted
        struct_call = mock_ds.structure.call_args
        assert struct_call.kwargs.get("pre_extracted") is not None
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_hybrid_extraction.py -v
```

**Step 3: Modify _step_extract_data in job_manager.py**

At `backend/app/services/job_manager.py` line 2063, rewrite `_step_extract_data`:

```python
async def _step_extract_data(self, job_id: UUID) -> Dict[str, Any]:
    """Extract text from PDF pages using hybrid approach.

    1. Native text layer from PDFProcessor (lossless, free)
    2. Vision OCR only for visual/graphic-heavy pages
    3. Per-page routing based on native text char count
    """
    from app.services.vision_extractor import VisionExtractor

    ctx = self._pipeline_ctx.get(job_id, {})
    extraction = ctx.get("extraction")
    if extraction is None:
        raise RuntimeError("No extraction result available")

    page_renders = extraction.page_renders
    if not page_renders:
        raise RuntimeError("No page renders available for extraction")

    # Native text from PDFProcessor (already populated in Task 2)
    page_text_map = getattr(extraction, "page_text_map", {}) or {}
    page_char_counts = getattr(extraction, "page_char_counts", {}) or {}

    extractor = VisionExtractor()
    page_results = await extractor.extract_pages(
        page_renders,
        page_text_map=page_text_map,
        page_char_counts=page_char_counts,
    )

    ctx["page_extraction_results"] = page_results

    # Merge: use native text for text-rich pages, Vision text for visual pages
    merged_text_map = dict(page_text_map)  # start with native text
    for r in page_results:
        if r.page_number not in merged_text_map and r.raw_text:
            merged_text_map[r.page_number] = r.raw_text
    extraction.page_text_map = merged_text_map

    full_text = VisionExtractor.concatenate_page_text(page_results)
    ctx["vision_full_text"] = full_text

    total_cost = sum(r.cost for r in page_results)
    text_rich_count = sum(1 for pn in page_char_counts if page_char_counts[pn] >= 200)
    return {
        "pages_extracted": len(page_results),
        "text_rich_pages": text_rich_count,
        "vision_pages": len(page_results) - text_rich_count,
        "total_chars": len(full_text),
        "total_cost": total_cost,
    }
```

**Step 4: Modify _step_structure_data to add regex + table pre-extraction**

At `backend/app/services/job_manager.py` line 2161, rewrite `_step_structure_data`:

```python
async def _step_structure_data(self, job_id: UUID) -> Dict[str, Any]:
    """Structure extracted text into StructuredProject using hybrid approach.

    1. Run DataExtractor regex pass on native text (free, high-confidence anchors)
    2. Run TableExtractor on PDF bytes (exact table values)
    3. Feed pre_extracted hints to DataStructurer for LLM structuring
    """
    from app.services.data_extractor import DataExtractor
    from app.services.data_structurer import DataStructurer
    from app.services.table_extractor import TableExtractor

    ctx = self._pipeline_ctx.get(job_id, {})
    full_text = ctx.get("vision_full_text", "")
    page_results = ctx.get("page_extraction_results", [])
    extraction = ctx.get("extraction")

    if not full_text:
        raise RuntimeError("No extracted text available for structuring")

    job = await self.job_repo.get_job(job_id)
    template_type = job.template_type.value if job else "aggregators"

    # Layer 1: Regex pre-extraction (free, no API calls)
    page_text_map = getattr(extraction, "page_text_map", {}) or {}
    regex_extractor = DataExtractor()
    regex_result = regex_extractor.extract(page_text_map)
    ctx["data_extraction"] = regex_result  # for enrichment step backward compat

    # Build pre_extracted dict from high-confidence regex results
    pre_extracted = {}
    if regex_result.developer.value and regex_result.developer.confidence >= 0.6:
        pre_extracted["developer"] = regex_result.developer.value
    if regex_result.project_name.value and regex_result.project_name.confidence >= 0.6:
        pre_extracted["project_name"] = regex_result.project_name.value
    if regex_result.location.emirate:
        pre_extracted["emirate"] = regex_result.location.emirate
    if regex_result.location.community:
        pre_extracted["community"] = regex_result.location.community
    if regex_result.prices.min_price:
        pre_extracted["price_min"] = regex_result.prices.min_price
    if regex_result.prices.max_price:
        pre_extracted["price_max"] = regex_result.prices.max_price
    if regex_result.bedrooms:
        pre_extracted["bedrooms"] = regex_result.bedrooms
    if regex_result.completion_date.value:
        pre_extracted["handover_date"] = regex_result.completion_date.value
    if regex_result.payment_plan.down_payment_pct is not None:
        pre_extracted["payment_plan"] = {
            "down_payment": f"{regex_result.payment_plan.down_payment_pct}%",
        }
        if regex_result.payment_plan.during_construction_pct is not None:
            pre_extracted["payment_plan"]["during_construction"] = (
                f"{regex_result.payment_plan.during_construction_pct}%"
            )
        if regex_result.payment_plan.on_handover_pct is not None:
            pre_extracted["payment_plan"]["on_handover"] = (
                f"{regex_result.payment_plan.on_handover_pct}%"
            )

    # Layer 2: Table extraction (free, exact values from PDF data stream)
    pdf_bytes = getattr(extraction, "pdf_bytes", None) or ctx.get("pdf_bytes")
    if pdf_bytes:
        table_extractor = TableExtractor()
        table_result = table_extractor.extract_tables(pdf_bytes)
        ctx["table_extraction"] = table_result

        # Merge floor plan specs into pre_extracted
        if table_result.floor_plan_specs:
            pre_extracted["_floor_plan_specs"] = table_result.floor_plan_specs
            # Extract min/max area from table specs for validation
            areas = [
                fp["total_sqft"] for fp in table_result.floor_plan_specs
                if fp.get("total_sqft")
            ]
            if areas:
                pre_extracted["_area_range_sqft"] = {
                    "min": min(areas), "max": max(areas)
                }

        # Merge payment plan from tables
        if table_result.payment_plan and not pre_extracted.get("payment_plan"):
            pre_extracted["payment_plan"] = table_result.payment_plan

    logger.info(
        "Pre-extraction: %d regex hints, tables=%s",
        len(pre_extracted),
        "yes" if pdf_bytes and table_result.tables else "no",
    )

    # Layer 3: LLM structuring with pre_extracted hints
    structurer = DataStructurer()
    structured = await structurer.structure(
        markdown_text=full_text,
        template_type=template_type,
        pre_extracted=pre_extracted,
    )
    ctx["structured_data"] = structured

    # Update regex_result extraction_method
    regex_result.extraction_method = "hybrid"

    return {
        "project_name": structured.project_name,
        "developer": structured.developer,
        "pre_extracted_fields": len(pre_extracted),
    }
```

**Step 5: Store pdf_bytes in pipeline context**

The pipeline needs access to the original PDF bytes for table extraction. In the pipeline initialization (where PDFProcessor.extract_all() is called), store `pdf_bytes` in ctx:

Find the line where `extract_all()` is called and add after it:
```python
ctx["pdf_bytes"] = pdf_bytes  # Needed for table extraction
```

**Step 6: Run tests**

```bash
cd backend && python -m pytest tests/test_hybrid_extraction.py tests/test_parallel_pipeline.py -v
```

**Step 7: Commit**

```bash
git add backend/app/services/job_manager.py
git commit -m "feat: wire hybrid extraction -- regex pre-extraction + table parsing + Vision routing into structuring"
```

---

## Task 7: Cross-Validation and Numeric Reconciliation

**Files:**
- Create: `backend/app/services/cross_validator.py`
- Create: `backend/tests/test_cross_validator.py`

After structuring, cross-validate numeric fields between the text-layer regex extraction and the LLM structuring output. If the LLM disagrees with regex on a number, flag it and prefer the regex value (since regex reads text directly, no OCR errors).

**Step 1: Write failing tests**

Create `backend/tests/test_cross_validator.py`:
```python
"""Tests for cross-validation reconciliation."""
import pytest
from app.services.cross_validator import CrossValidator, ReconciliationResult


class TestCrossValidator:
    def setup_method(self):
        self.validator = CrossValidator()

    def test_matching_values_accepted(self):
        """When regex and LLM agree, value is accepted with high confidence."""
        result = self.validator.reconcile(
            field="price_min",
            regex_value=820000,
            llm_value=820000,
        )
        assert result.final_value == 820000
        assert result.confidence >= 0.95
        assert not result.flagged

    def test_regex_preferred_for_numeric_disagreement(self):
        """When regex and LLM disagree on a number, regex wins."""
        result = self.validator.reconcile(
            field="price_min",
            regex_value=820000,
            llm_value=850000,
        )
        assert result.final_value == 820000
        assert result.source == "regex"
        assert result.flagged

    def test_llm_used_when_regex_null(self):
        """When regex returns None but LLM has a value, LLM value is used."""
        result = self.validator.reconcile(
            field="price_min",
            regex_value=None,
            llm_value=820000,
        )
        assert result.final_value == 820000
        assert result.source == "llm"

    def test_semantic_fields_prefer_llm(self):
        """For non-numeric fields (description, amenities), LLM is preferred."""
        result = self.validator.reconcile(
            field="description",
            regex_value=None,
            llm_value="A luxury residential community by Nshama",
        )
        assert result.final_value == "A luxury residential community by Nshama"
        assert result.source == "llm"

    def test_table_value_overrides_both(self):
        """pdfplumber table values override both regex and LLM."""
        result = self.validator.reconcile(
            field="price_min",
            regex_value=820000,
            llm_value=850000,
            table_value=820000,
        )
        assert result.final_value == 820000
        assert result.source == "table"

    def test_floor_plan_area_table_overrides_vision(self):
        """Floor plan area from table overrides Vision-extracted value."""
        result = self.validator.reconcile(
            field="total_sqft",
            regex_value=None,
            llm_value=661.0,  # Vision misread 51.57 sqm as 61.37
            table_value=555.1,  # pdfplumber exact: 51.57 * 10.764
        )
        assert result.final_value == 555.1
        assert result.source == "table"

    def test_reconcile_structured_project(self):
        """Full reconciliation of a StructuredProject against regex + table data."""
        from app.services.data_structurer import StructuredProject

        structured = StructuredProject(
            project_name="EVELYN on the Park",
            developer="Nshama",
            price_min=820000,
            emirate="Dubai",
        )
        regex_hints = {"price_min": 820000, "developer": "Nshama", "emirate": "Dubai"}
        table_hints = {}

        reconciled, flags = self.validator.reconcile_project(
            structured, regex_hints, table_hints
        )
        assert reconciled.price_min == 820000
        assert len(flags) == 0  # No disagreements
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_cross_validator.py -v
```

**Step 3: Implement CrossValidator**

Create `backend/app/services/cross_validator.py`:
```python
"""
Cross-Validation Reconciliation Service

Compares extraction results from multiple sources (regex, LLM, table)
and produces a reconciled value with confidence scoring.

Priority order for numeric fields: table > regex > LLM
Priority order for semantic fields: LLM > regex
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Fields where regex/table values should override LLM
NUMERIC_FIELDS = {
    "price_min", "price_max", "price_per_sqft",
    "total_units", "floors",
    "total_sqft", "balcony_sqft", "builtup_sqft",
    "bedrooms_count", "bathrooms_count",
}

# Fields where LLM is preferred (semantic understanding needed)
SEMANTIC_FIELDS = {
    "description", "amenities", "key_features",
    "property_type", "community", "sub_community",
}


@dataclass
class ReconciliationResult:
    """Result of reconciling a single field."""
    field: str
    final_value: Any
    source: str  # "regex", "llm", "table", "agreement"
    confidence: float
    flagged: bool = False
    details: str = ""


class CrossValidator:
    """Reconciles extraction results from multiple sources."""

    def reconcile(
        self,
        field: str,
        regex_value: Any = None,
        llm_value: Any = None,
        table_value: Any = None,
    ) -> ReconciliationResult:
        """Reconcile a single field from multiple sources."""

        # Table values are highest priority (exact from PDF data stream)
        if table_value is not None:
            flagged = (
                llm_value is not None
                and llm_value != table_value
                and field in NUMERIC_FIELDS
            )
            return ReconciliationResult(
                field=field,
                final_value=table_value,
                source="table",
                confidence=0.99,
                flagged=flagged,
                details=f"table={table_value}, llm={llm_value}" if flagged else "",
            )

        is_numeric = field in NUMERIC_FIELDS

        # Both sources agree
        if regex_value is not None and llm_value is not None:
            if self._values_match(regex_value, llm_value, is_numeric):
                return ReconciliationResult(
                    field=field,
                    final_value=regex_value,
                    source="agreement",
                    confidence=0.98,
                )

            # Disagreement
            if is_numeric:
                # For numbers, prefer regex (reads text stream directly, no OCR)
                return ReconciliationResult(
                    field=field,
                    final_value=regex_value,
                    source="regex",
                    confidence=0.85,
                    flagged=True,
                    details=f"regex={regex_value}, llm={llm_value}",
                )
            else:
                # For semantic fields, prefer LLM
                return ReconciliationResult(
                    field=field,
                    final_value=llm_value,
                    source="llm",
                    confidence=0.80,
                    flagged=True,
                    details=f"regex={regex_value}, llm={llm_value}",
                )

        # Only one source has a value
        if regex_value is not None:
            return ReconciliationResult(
                field=field,
                final_value=regex_value,
                source="regex",
                confidence=0.80,
            )
        if llm_value is not None:
            return ReconciliationResult(
                field=field,
                final_value=llm_value,
                source="llm",
                confidence=0.70,
            )

        # Neither source has a value
        return ReconciliationResult(
            field=field,
            final_value=None,
            source="none",
            confidence=0.0,
        )

    def reconcile_project(
        self,
        structured,  # StructuredProject
        regex_hints: dict,
        table_hints: dict,
    ) -> tuple:
        """Reconcile all fields of a StructuredProject.

        Returns (reconciled_project, list_of_flags).
        """
        flags = []

        field_mapping = {
            "price_min": "price_min",
            "price_max": "price_max",
            "price_per_sqft": "price_per_sqft",
            "developer": "developer",
            "emirate": "emirate",
            "community": "community",
            "project_name": "project_name",
        }

        for field_name, attr_name in field_mapping.items():
            llm_value = getattr(structured, attr_name, None)
            regex_value = regex_hints.get(field_name)
            table_value = table_hints.get(field_name)

            result = self.reconcile(
                field=field_name,
                regex_value=regex_value,
                llm_value=llm_value,
                table_value=table_value,
            )

            if result.final_value is not None:
                setattr(structured, attr_name, result.final_value)
            if result.flagged:
                flags.append(result)

        return structured, flags

    @staticmethod
    def _values_match(a: Any, b: Any, is_numeric: bool) -> bool:
        """Check if two values match (with tolerance for numbers)."""
        if a == b:
            return True
        if is_numeric:
            try:
                return abs(float(a) - float(b)) < 1.0
            except (ValueError, TypeError):
                return False
        if isinstance(a, str) and isinstance(b, str):
            return a.strip().lower() == b.strip().lower()
        return False
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_cross_validator.py -v
```
Expected: all 8 PASS

**Step 5: Wire into _step_structure_data**

After `structurer.structure()` call in `_step_structure_data` (added in Task 6), add:
```python
# Layer 4: Cross-validation reconciliation
from app.services.cross_validator import CrossValidator
validator = CrossValidator()
structured, flags = validator.reconcile_project(
    structured, pre_extracted, table_hints={}
)
if flags:
    logger.warning(
        "Cross-validation flags for job %s: %s",
        job_id,
        [(f.field, f.details) for f in flags],
    )
ctx["cross_validation_flags"] = flags
```

**Step 6: Commit**

```bash
git add backend/app/services/cross_validator.py backend/tests/test_cross_validator.py backend/app/services/job_manager.py
git commit -m "feat: add cross-validation reconciliation -- regex/table override LLM for numbers"
```

---

## Task 8: Floor Plan Extraction Hardening

**Files:**
- Modify: `backend/app/services/floor_plan_extractor.py`
- Modify: `backend/app/services/job_manager.py` (floor plan step)

Floor plan extraction had catastrophic failures on EVELYN: 7/7 plans had mostly null fields, duplicate entries for same unit types, and Vision-misread numbers. The fix:

1. Use pdfplumber table specs as PRIMARY source for floor plan data (exact numbers)
2. Vision OCR as SECONDARY source only for room dimensions and features
3. Filter corrupt images before processing (from Task 3)
4. Merge pdfplumber table row with Vision OCR for same unit type

**Step 1: Modify floor plan step in job_manager.py to pass table_extraction**

In the floor plan extraction step (find `_step_extract_floor_plans` or equivalent), add:
```python
# Get table-extracted floor plan specs (exact from pdfplumber)
table_result = ctx.get("table_extraction")
table_floor_plans = table_result.floor_plan_specs if table_result else []
```

**Step 2: Add table-Vision merge logic to FloorPlanExtractor**

Add method to `FloorPlanExtractor`:
```python
def merge_with_table_data(
    self,
    vision_plans: list[FloorPlanData],
    table_specs: list[dict],
) -> list[FloorPlanData]:
    """Merge Vision-extracted floor plans with pdfplumber table data.

    Table data is ground truth for numeric fields (sqft, bedrooms, bathrooms).
    Vision data supplements with room dimensions and visual features.

    Strategy:
    - Match table rows to Vision plans by unit_type string similarity
    - For matched pairs: numeric fields from table, dimensions from Vision
    - Unmatched table rows: create FloorPlanData from table alone
    - Unmatched Vision plans: keep as-is (low confidence warning)
    """
    if not table_specs:
        return vision_plans

    merged = []
    used_table_indices = set()

    for vp in vision_plans:
        best_match = self._find_matching_table_row(vp, table_specs, used_table_indices)
        if best_match is not None:
            idx, table_row = best_match
            used_table_indices.add(idx)
            # Override numeric fields with table values
            if table_row.get("total_sqft"):
                vp.total_sqft = table_row["total_sqft"]
                vp.total_sqft_source = "table"
            if table_row.get("balcony_sqft"):
                vp.balcony_sqft = table_row["balcony_sqft"]
                vp.balcony_sqft_source = "table"
            if table_row.get("builtup_sqft"):
                vp.builtup_sqft = table_row["builtup_sqft"]
                vp.builtup_sqft_source = "table"
            if table_row.get("bedrooms") is not None:
                vp.bedrooms = int(table_row["bedrooms"])
                vp.bedrooms_source = "table"
            if table_row.get("bathrooms") is not None:
                vp.bathrooms = float(table_row["bathrooms"])
                vp.bathrooms_source = "table"
            if table_row.get("unit_type") and not vp.unit_type:
                vp.unit_type = table_row["unit_type"]
                vp.unit_type_source = "table"
        merged.append(vp)

    # Add table rows that had no Vision match
    for idx, row in enumerate(table_specs):
        if idx not in used_table_indices:
            fp = FloorPlanData(
                unit_type=row.get("unit_type"),
                unit_type_source="table",
                bedrooms=int(row["bedrooms"]) if row.get("bedrooms") is not None else None,
                bedrooms_source="table" if row.get("bedrooms") is not None else "",
                bathrooms=float(row["bathrooms"]) if row.get("bathrooms") is not None else None,
                bathrooms_source="table" if row.get("bathrooms") is not None else "",
                total_sqft=row.get("total_sqft"),
                total_sqft_source="table" if row.get("total_sqft") else "",
                balcony_sqft=row.get("balcony_sqft"),
                balcony_sqft_source="table" if row.get("balcony_sqft") else "",
                confidence=0.95,  # high confidence -- exact from PDF
            )
            merged.append(fp)

    return merged

def _find_matching_table_row(
    self, vp: FloorPlanData, table_specs: list[dict], used: set[int]
) -> tuple[int, dict] | None:
    """Find matching table row for a Vision-extracted floor plan."""
    if not vp.unit_type:
        return None
    vp_type = vp.unit_type.lower().strip()
    for idx, row in enumerate(table_specs):
        if idx in used:
            continue
        row_type = (row.get("unit_type") or "").lower().strip()
        if not row_type:
            continue
        # Exact or substring match
        if vp_type == row_type or vp_type in row_type or row_type in vp_type:
            return (idx, row)
    return None
```

**Step 3: Wire into pipeline**

In `_step_extract_floor_plans` or wherever floor plans are extracted:
```python
# After Vision extraction
table_result = ctx.get("table_extraction")
table_floor_plans = table_result.floor_plan_specs if table_result else []
if table_floor_plans:
    fp_result.floor_plans = self._floor_plan_extractor.merge_with_table_data(
        fp_result.floor_plans, table_floor_plans
    )
```

**Step 4: Tests and commit**

```bash
cd backend && python -m pytest tests/ -k "floor_plan" -v
git add backend/app/services/floor_plan_extractor.py backend/app/services/job_manager.py
git commit -m "feat: harden floor plan extraction -- pdfplumber tables as primary, Vision as secondary"
```

---

## Task 9: Refined Vision OCR Prompts

**Files:**
- Modify: `backend/app/services/vision_extractor.py` (OCR_PROMPT)
- Modify: `backend/app/services/floor_plan_extractor.py` (FLOOR_PLAN_OCR_PROMPT)

The current OCR prompt says "Read ALL text visible" which causes map label contamination on location/proximity pages. Refine prompts with negative instructions.

**Step 1: Update OCR_PROMPT in vision_extractor.py**

```python
OCR_PROMPT = """Read all TEXT CONTENT from this page of a real estate property brochure.

Include:
- Body text, headings, subheadings, and paragraphs
- Stylized/decorative text rendered as graphics
- Text overlaid on images (but NOT labels on maps or diagrams)
- Small print, footnotes, disclaimers, legal text
- Numbers in structured data (prices, areas, unit counts)
- Contact information, website URLs

IMPORTANT exclusions:
- Do NOT read labels from maps, satellite imagery, or cartographic illustrations
- Do NOT read hotel names, landmark names, or road names from map overlays
- Do NOT read navigation UI elements (zoom controls, compass, etc.)
- If a page is primarily a map/aerial view, extract ONLY the text labels that are
  part of the brochure design (e.g. proximity callouts like "5 min to X"), not
  every label visible on the map itself.

Output the text in reading order (top to bottom, left to right).
Preserve the original formatting where possible (line breaks between sections).
Read text EXACTLY as displayed -- do not paraphrase, correct spelling, or interpret.
If a section has no readable text, skip it.

Return ONLY the extracted text, nothing else."""
```

**Step 2: Update FLOOR_PLAN_OCR_PROMPT in floor_plan_extractor.py**

```python
FLOOR_PLAN_OCR_PROMPT = """Extract all visible data from this floor plan image.
Return null for fields NOT visible in the image.

Return ONLY valid JSON (no markdown fences):
{
  "unit_type": "2BR Type A or null",
  "bedrooms": 2,
  "bathrooms": 2.5,
  "total_sqft": 1250.0,
  "balcony_sqft": 150.0,
  "builtup_sqft": 1100.0,
  "room_dimensions": {"living": "4.2m x 3.8m", "bedroom1": "3.5m x 3.2m"},
  "features": ["maid_room", "walk_in_closet"],
  "confidence": 0.92
}

CRITICAL RULES:
1. Read numbers EXACTLY as printed. Do NOT round, estimate, or modify digits.
2. If area is labeled "sqm" or "m2", convert to sqft by multiplying by 10.764.
3. If area is labeled "sqft" or "sq.ft." or "sq ft", use the value as-is.
4. Only extract data VISIBLE in the image. Do not guess or infer.
5. For unit_type, include the full label (e.g., "2BR Type A", not just "2BR").
6. Double-check all digits: common OCR errors include 1<->7, 5<->6, 0<->8."""
```

**Step 3: Commit**

```bash
git add backend/app/services/vision_extractor.py backend/app/services/floor_plan_extractor.py
git commit -m "fix: refine Vision OCR prompts -- exclude map labels, add digit-check instruction"
```

---

## Task 10: Integration Wiring and End-to-End Test

**Files:**
- Modify: `backend/app/services/job_manager.py` (pipeline initialization)
- Create: `backend/tests/test_hybrid_e2e.py`

Final integration: ensure the full extraction pipeline flows correctly from PDFProcessor through hybrid extraction to structured output.

**Step 1: Ensure pdf_bytes is available in pipeline context**

Find where `PDFProcessor.extract_all()` is called in job_manager.py. Add `pdf_bytes` storage:

```python
# After: extraction = await processor.extract_all(pdf_bytes)
ctx["pdf_bytes"] = pdf_bytes
```

Also ensure `extraction.page_char_counts` is available (set by PDFProcessor from Task 2).

**Step 2: Write end-to-end integration test**

Create `backend/tests/test_hybrid_e2e.py`:
```python
"""End-to-end test for hybrid extraction pipeline."""
import pytest
import fitz
from unittest.mock import AsyncMock, patch, MagicMock
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

    def test_regex_extracts_from_native_text(self):
        """DataExtractor regex finds fields from native text."""
        pdf_bytes = _create_test_pdf()
        import fitz as f
        doc = f.open(stream=pdf_bytes, filetype="pdf")
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
        page_text_map = {1: "EVELYN text", 2: "Price text"}
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
```

**Step 3: Run all tests**

```bash
cd backend && python -m pytest tests/test_hybrid_e2e.py -v
cd backend && python -m pytest tests/ -v --tb=short
```

**Step 4: Commit**

```bash
git add backend/tests/test_hybrid_e2e.py backend/app/services/job_manager.py
git commit -m "feat: complete hybrid extraction pipeline integration with end-to-end tests"
```

---

## Task 11: Manual Pipeline Test with EVELYN Brochure

**No code changes -- validation only.**

Re-run the EVELYN PDF through the pipeline and validate:

**Step 1: Upload EVELYN brochure through the UI or API**

```bash
# If using API directly:
curl -X POST http://localhost:8000/api/process/start-extraction \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@evelyn-brochure.pdf" \
  -F "template_type=opr"
```

**Step 2: Monitor Docker logs**

```bash
docker logs -f pdp-backend 2>&1 | grep -E "(Page routing|Pre-extraction|Cross-validation|Table extraction|floor plan)"
```

**Expected log output:**
```
Page routing: N text-rich (native), M visual (Vision OCR)
Table extraction: X tables (Y floor plan, Z payment plan)
Pre-extraction: N regex hints, tables=yes
```

**Step 3: Validate structured_data.json**

Download from GCS and verify:
- project_name: "EVELYN on the Park" (exact)
- developer: "Nshama" (exact)
- emirate: "Dubai" (exact)
- community: "Town Square" (exact)
- price_min: 820000 (from regex/table, NOT Vision)
- bedrooms: ["Studio", "1BR", "2BR", "3BR"]
- handover_date: "Q4 2027"

**Step 4: Validate floor_plans.json**

- Each unit type present: Studio, 1BR Type A, 2BR Type A, 2BR Type B, 3BR Type A
- Areas match brochure exactly (e.g., 1BR Type A = 554 sqft = 51.47 sqm)
- No duplicate entries for same unit type
- Source fields show "table" for numeric values

**Step 5: Validate Google Sheet output**

- Check OPR sheet: all fields populated with correct data
- Check for zero "TBA" values where brochure has data
- Check Property Types Table: correct unit types, correct areas

---

## Summary of All New/Modified Files

### New files:
| File | Purpose |
|------|---------|
| `backend/app/services/table_extractor.py` | pdfplumber table extraction (floor plans, payment plans) |
| `backend/app/services/cross_validator.py` | Cross-validation reconciliation between extraction layers |
| `backend/app/utils/image_validation.py` | Corrupt image filter before Vision API calls |
| `backend/tests/test_table_extractor.py` | Table extractor tests |
| `backend/tests/test_pdf_text_extraction.py` | Text layer restoration tests |
| `backend/tests/test_image_validation.py` | Image validation tests |
| `backend/tests/test_page_routing.py` | Per-page routing tests |
| `backend/tests/test_hybrid_extraction.py` | Integration wiring tests |
| `backend/tests/test_cross_validator.py` | Cross-validation tests |
| `backend/tests/test_data_extractor_expanded.py` | Expanded regex pattern tests |
| `backend/tests/test_hybrid_e2e.py` | End-to-end pipeline test |

### Modified files:
| File | Change |
|------|--------|
| `backend/requirements.txt` | Add pdfplumber dependency |
| `backend/app/services/pdf_processor.py` | Restore native text extraction, add page_char_counts |
| `backend/app/utils/pdf_helpers.py` | Add page_char_counts to ExtractionResult |
| `backend/app/services/vision_extractor.py` | Per-page routing, refined OCR prompt |
| `backend/app/services/data_extractor.py` | Expand KNOWN_DEVELOPERS + DUBAI_COMMUNITIES |
| `backend/app/services/data_structurer.py` | No changes (pre_extracted already supported) |
| `backend/app/services/job_manager.py` | Rewire _step_extract_data + _step_structure_data for hybrid |
| `backend/app/services/floor_plan_extractor.py` | Image validation, table merge, refined prompt |
| `backend/app/services/image_classifier.py` | Image validation guard |

### Unchanged (already support what we need):
| File | Why unchanged |
|------|---------------|
| `backend/app/services/data_structurer.py` | Already accepts `pre_extracted` param |
| `backend/app/services/content_generator.py` | Consumes StructuredProject -- no changes needed |
| `backend/app/services/sheets_manager.py` | Consumes content dict -- no changes needed |

---

## Verification Checklist

After all tasks are complete:

1. **Unit tests**: `cd backend && python -m pytest tests/ -v --tb=short` -- all pass
2. **Coverage**: `cd backend && python -m pytest tests/ --cov=app --cov-report=term-missing` -- >= 75%
3. **Lint**: `cd backend && ruff check . && ruff format --check .`
4. **Docker build**: `docker compose -f docker-compose.dev.yml build backend`
5. **Pipeline test**: Upload EVELYN brochure, verify structured_data.json matches brochure exactly
6. **Floor plan validation**: All unit types present with correct areas from pdfplumber
7. **Log inspection**: Confirm "Page routing: N text-rich, M visual" appears in logs
8. **Cost check**: Vision API calls reduced (only visual pages, not all pages)
