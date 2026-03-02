"""Test sheets_manager field mapping integration.

Verifies that sheets_manager uses the correct column mappings:
- Column A = Guidelines/Comments
- Column B = Field Name (label)
- Column C = EN (English content) <-- target for EN writes
- Column D = AR (Arabic content)
- Column E = RU (Russian content)
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.sheets_manager import SheetsManager, TAB_NAMES
from app.services.template_fields import get_fields_for_template, get_cell_mapping


ALL_TEMPLATES = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]


class TestTabNames:
    """Tests for TAB_NAMES dict."""

    def test_all_templates_have_tab_names(self):
        """All 6 templates should have a tab name mapping."""
        for template_type in ALL_TEMPLATES:
            assert template_type in TAB_NAMES, f"Missing tab name for {template_type}"

    def test_tab_names_are_nonempty_strings(self):
        """Tab names should be non-empty strings."""
        for template_type, tab_name in TAB_NAMES.items():
            assert isinstance(tab_name, str), f"{template_type} tab name is not a string"
            assert len(tab_name) > 0, f"{template_type} has empty tab name"

    def test_tab_names_contain_template_keyword(self):
        """Each tab name should contain 'Template' (per convention)."""
        for template_type, tab_name in TAB_NAMES.items():
            assert "Template" in tab_name, (
                f"{template_type} tab name '{tab_name}' missing 'Template' keyword"
            )


class TestFieldMappingIntegration:
    """Tests for SheetsManager._get_field_mapping integration."""

    @pytest.fixture
    def sheets_manager(self):
        """Create SheetsManager with mocked gspread client."""
        with patch.object(SheetsManager, "_init_gspread_client") as mock_init:
            mock_init.return_value = MagicMock()
            manager = SheetsManager()
            return manager

    @pytest.mark.parametrize("template_type", ALL_TEMPLATES)
    def test_english_mapping_uses_column_c(self, sheets_manager, template_type):
        """All EN field mappings should target column C, not B."""
        mapping = sheets_manager._get_field_mapping(template_type, language="en")
        for field_name, cell_ref in mapping.items():
            assert cell_ref.startswith("C"), (
                f"{template_type}.{field_name} maps to {cell_ref}, expected column C"
            )
            assert not cell_ref.startswith("B"), (
                f"{template_type}.{field_name} incorrectly writes to column B"
            )

    @pytest.mark.parametrize("template_type", ALL_TEMPLATES)
    def test_no_mapping_writes_to_column_b(self, sheets_manager, template_type):
        """No field should ever write to column B (label column)."""
        for lang in ["en", "ar", "ru"]:
            mapping = sheets_manager._get_field_mapping(template_type, language=lang)
            for field_name, cell_ref in mapping.items():
                assert not cell_ref.startswith("B"), (
                    f"{template_type}.{field_name} ({lang}) writes to column B: {cell_ref}"
                )

    @pytest.mark.parametrize("template_type", ALL_TEMPLATES)
    def test_arabic_mapping_uses_column_d(self, sheets_manager, template_type):
        """All AR field mappings should target column D."""
        mapping = sheets_manager._get_field_mapping(template_type, language="ar")
        for field_name, cell_ref in mapping.items():
            assert cell_ref.startswith("D"), (
                f"{template_type}.{field_name} (AR) maps to {cell_ref}, expected column D"
            )

    @pytest.mark.parametrize("template_type", ALL_TEMPLATES)
    def test_russian_mapping_uses_column_e(self, sheets_manager, template_type):
        """All RU field mappings should target column E."""
        mapping = sheets_manager._get_field_mapping(template_type, language="ru")
        for field_name, cell_ref in mapping.items():
            assert cell_ref.startswith("E"), (
                f"{template_type}.{field_name} (RU) maps to {cell_ref}, expected column E"
            )

    @pytest.mark.parametrize("template_type", ALL_TEMPLATES)
    def test_field_count_matches_template_fields(self, sheets_manager, template_type):
        """Mapping field count should match template_fields registry."""
        mapping = sheets_manager._get_field_mapping(template_type, language="en")
        expected_fields = get_fields_for_template(template_type)
        assert len(mapping) == len(expected_fields), (
            f"{template_type}: mapping has {len(mapping)} fields, "
            f"registry has {len(expected_fields)}"
        )

    @pytest.mark.parametrize("template_type", ALL_TEMPLATES)
    def test_mapping_matches_template_fields_cell_mapping(self, sheets_manager, template_type):
        """Manager._get_field_mapping should match template_fields.get_cell_mapping."""
        manager_mapping = sheets_manager._get_field_mapping(template_type, language="en")
        direct_mapping = get_cell_mapping(template_type, "en")
        assert manager_mapping == direct_mapping, (
            f"{template_type}: SheetsManager mapping differs from template_fields"
        )

    def test_invalid_template_raises_value_error(self, sheets_manager):
        """Invalid template type should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid template type"):
            sheets_manager._get_field_mapping("nonexistent")

    def test_invalid_language_raises_value_error(self, sheets_manager):
        """Invalid language should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported language"):
            sheets_manager._get_field_mapping("aggregators", language="de")

    def test_default_language_is_english(self, sheets_manager):
        """Calling without language parameter should default to EN (column C)."""
        mapping = sheets_manager._get_field_mapping("aggregators")
        for field_name, cell_ref in mapping.items():
            assert cell_ref.startswith("C"), (
                f"Default language should be EN (column C), got {cell_ref}"
            )


class TestMinimumFieldCounts:
    """Verify minimum expected field counts per template."""

    @pytest.fixture
    def sheets_manager(self):
        with patch.object(SheetsManager, "_init_gspread_client") as mock_init:
            mock_init.return_value = MagicMock()
            return SheetsManager()

    @pytest.mark.parametrize("template_type,min_count", [
        ("aggregators", 100),
        ("opr", 100),
        ("mpp", 80),
        ("adop", 50),
        ("adre", 100),
        ("commercial", 60),
    ])
    def test_template_has_minimum_fields(self, sheets_manager, template_type, min_count):
        """Each template should have at least the minimum expected fields."""
        mapping = sheets_manager._get_field_mapping(template_type)
        assert len(mapping) >= min_count, (
            f"{template_type} has {len(mapping)} fields, expected >= {min_count}"
        )


class TestCellReferencesAreValid:
    """Verify cell references follow expected format."""

    @pytest.fixture
    def sheets_manager(self):
        with patch.object(SheetsManager, "_init_gspread_client") as mock_init:
            mock_init.return_value = MagicMock()
            return SheetsManager()

    @pytest.mark.parametrize("template_type", ALL_TEMPLATES)
    def test_cell_references_have_valid_format(self, sheets_manager, template_type):
        """Cell references should match pattern like 'C4', 'D123', etc."""
        import re
        pattern = re.compile(r"^[A-Z]+\d+$")
        mapping = sheets_manager._get_field_mapping(template_type)
        for field_name, cell_ref in mapping.items():
            assert pattern.match(cell_ref), (
                f"{template_type}.{field_name} has invalid cell ref: {cell_ref}"
            )

    @pytest.mark.parametrize("template_type", ALL_TEMPLATES)
    def test_row_numbers_are_positive(self, sheets_manager, template_type):
        """Row numbers in cell references should be > 0."""
        import re
        mapping = sheets_manager._get_field_mapping(template_type)
        for field_name, cell_ref in mapping.items():
            row_match = re.search(r"\d+", cell_ref)
            assert row_match, f"{template_type}.{field_name} missing row number: {cell_ref}"
            row_num = int(row_match.group())
            assert row_num > 0, (
                f"{template_type}.{field_name} has non-positive row: {row_num}"
            )
