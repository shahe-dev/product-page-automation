"""
Table Extractor Service

Extracts structured tables from PDF documents using pdfplumber.
Classifies tables as floor plan specs, payment plans, or unknown.
Returns exact numeric values from the PDF data stream (no OCR).
"""

import enum
import io
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
        col_map = self._map_floor_plan_columns(headers)
        is_sqm = any(
            "sqm" in h.lower() or "sq m" in h.lower() or "sq.m" in h.lower()
            for h in headers
        )

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
                        entry[field_name] = (
                            int(val) if field_name == "bedrooms" else val
                        )
                elif field_name in (
                    "total_sqft", "suite_sqft", "balcony_sqft",
                    "builtup_sqft", "terrace_sqft",
                ):
                    val = self._parse_number(cell)
                    if val is not None:
                        if is_sqm:
                            val = round(val * SQM_TO_SQFT, 1)
                        entry[field_name] = val

            if entry:
                parsed.append(entry)

        return parsed

    def _map_floor_plan_columns(self, headers: list[str]) -> dict[int, str]:
        """Map column indices to semantic field names.

        Order matters: check compound phrases before single keywords to avoid
        mis-mapping (e.g. "Total built-up" must map to total_sqft, not builtup).
        Bare "area" is a last-resort fallback for total_sqft.
        """
        col_map: dict[int, str] = {}
        # Track bare "area" columns for deferred fallback assignment
        bare_area_idx: int | None = None

        for idx, header in enumerate(headers):
            h = header.lower().strip()

            if any(kw in h for kw in ("unit type", "type", "unit")):
                col_map[idx] = "unit_type"
            elif any(kw in h for kw in ("bedroom", "bed", "br")):
                col_map[idx] = "bedrooms"
            elif any(kw in h for kw in ("bathroom", "bath")):
                col_map[idx] = "bathrooms"
            # -- compound "total built" BEFORE bare "built-up" --
            elif "total built" in h or "total area" in h or "total sqft" in h or "total sq" in h:
                col_map[idx] = "total_sqft"
            elif any(kw in h for kw in ("suite", "internal")):
                col_map[idx] = "suite_sqft"
            elif any(kw in h for kw in ("balcony",)):
                col_map[idx] = "balcony_sqft"
            elif any(kw in h for kw in ("built-up", "builtup", "built up")):
                col_map[idx] = "builtup_sqft"
            elif any(kw in h for kw in ("terrace",)):
                col_map[idx] = "terrace_sqft"
            elif "area" in h:
                # Bare "area" -- defer to fallback
                bare_area_idx = idx

        # If no total_sqft was mapped yet, use bare "area" column
        if "total_sqft" not in col_map.values() and bare_area_idx is not None:
            col_map[bare_area_idx] = "total_sqft"

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

            if any(
                kw in milestone
                for kw in ("booking", "down payment", "reservation")
            ):
                result["down_payment"] = pct_str
            elif any(kw in milestone for kw in ("construction", "during")):
                result["during_construction"] = pct_str
            elif "post" in milestone and "handover" in milestone:
                result["post_handover"] = pct_str
            elif any(
                kw in milestone
                for kw in ("handover", "completion", "delivery")
            ):
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
