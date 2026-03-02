"""Tests for table_extractor service."""
from app.services.table_extractor import TableExtractor, TableType


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
        headers = [
            "Unit Type", "Bedrooms", "Bathrooms",
            "Total Area (sqft)", "Balcony (sqft)", "Notes",
        ]
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

    def test_classify_single_area_keyword(self):
        """A single 'area' keyword alone triggers FLOOR_PLAN classification."""
        headers = ["Name", "Area"]
        assert self.extractor._classify_table(headers) == TableType.FLOOR_PLAN

    def test_classify_single_milestone_keyword(self):
        """A single 'milestone' keyword triggers PAYMENT_PLAN classification."""
        headers = ["Milestone", "Date"]
        assert self.extractor._classify_table(headers) == TableType.PAYMENT_PLAN
