"""Tests for cross-validation reconciliation."""
from app.services.cross_validator import CrossValidator


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
            llm_value=661.0,
            table_value=555.1,
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
        regex_hints = {
            "price_min": 820000,
            "developer": "Nshama",
            "emirate": "Dubai",
        }
        table_hints = {}

        reconciled, flags = self.validator.reconcile_project(
            structured, regex_hints, table_hints
        )
        assert reconciled.price_min == 820000
        assert len(flags) == 0  # No disagreements

    def test_both_none_returns_none(self):
        """When both sources have None, result is None."""
        result = self.validator.reconcile(
            field="price_min",
            regex_value=None,
            llm_value=None,
        )
        assert result.final_value is None
        assert result.source == "none"
        assert result.confidence == 0.0

    def test_numeric_close_values_match(self):
        """Numeric values within 1.0 tolerance are treated as matching."""
        result = self.validator.reconcile(
            field="price_min",
            regex_value=820000,
            llm_value=820000.5,
        )
        assert result.source == "agreement"
        assert not result.flagged

    def test_string_case_insensitive_match(self):
        """String values match case-insensitively for non-numeric fields."""
        result = self.validator.reconcile(
            field="developer",
            regex_value="NSHAMA",
            llm_value="Nshama",
        )
        assert result.source == "agreement"
        assert not result.flagged
