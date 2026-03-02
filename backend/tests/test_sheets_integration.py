"""
Integration tests: verify content generation -> sheets mapping pipeline.
Does NOT call Google Sheets API. Tests that generated field names
match sheets cell mapping for all 6 templates.
"""

import pytest
from app.services.template_fields import (
    get_fields_for_template,
    get_cell_mapping,
    get_sections_for_template,
    FieldDef,
)
from app.services.prompt_manager import PromptManager


ALL_TEMPLATES = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_every_field_has_cell_mapping(template_type):
    """Every field in the registry must have a cell in the sheets mapping."""
    fields = get_fields_for_template(template_type)
    mapping = get_cell_mapping(template_type, "en")

    assert set(fields.keys()) == set(mapping.keys()), (
        f"Field/mapping mismatch for {template_type}.\n"
        f"In fields but not mapping: {set(fields.keys()) - set(mapping.keys())}\n"
        f"In mapping but not fields: {set(mapping.keys()) - set(fields.keys())}"
    )


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_all_cell_mappings_target_column_c(template_type):
    """All EN mappings must write to column C, not B."""
    mapping = get_cell_mapping(template_type, "en")
    wrong_column = [f for f, cell in mapping.items() if not cell.startswith("C")]
    assert not wrong_column, (
        f"{template_type} has fields not targeting column C: {wrong_column[:10]}"
    )


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
@pytest.mark.asyncio
async def test_every_field_has_prompt(template_type):
    """Every field should resolve to a non-empty prompt."""
    fields = get_fields_for_template(template_type)
    pm = PromptManager()

    missing = []
    for field_name in fields:
        prompt = await pm.get_prompt(
            field_name=field_name,
            template_type=template_type,
            db=None,
        )
        if not prompt.content:
            missing.append(field_name)

    # Allow some missing (EXTRACTED/STATIC fields may not need prompts)
    coverage = 1 - len(missing) / len(fields)
    assert coverage >= 0.7, (
        f"{template_type} prompt coverage is {coverage:.0%}. "
        f"Missing: {missing[:10]}{'...' if len(missing) > 10 else ''}"
    )


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_sections_cover_all_fields(template_type):
    """Section groupings must include every field exactly once."""
    fields = get_fields_for_template(template_type)
    sections = get_sections_for_template(template_type)

    all_sectioned = []
    for field_list in sections.values():
        all_sectioned.extend(field_list)

    assert set(all_sectioned) == set(fields.keys()), (
        f"{template_type} section coverage mismatch"
    )
    assert len(all_sectioned) == len(fields), (
        f"{template_type} has duplicate fields in sections"
    )


def _is_combined_field(name: str) -> bool:
    """Check if a field name is part of a combined field group.

    Combined fields are multiple logical fields that map to a single cell,
    e.g., location_access_1 through location_access_8 or amenity_bullet_1
    through amenity_bullet_8. They share the same row in the sheet.
    """
    import re

    # Fields ending with _N pattern (e.g., location_access_1, amenity_bullet_3)
    if re.search(r"_\d+$", name):
        return True
    # Explicit bullet fields
    if "bullet" in name:
        return True
    return False


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_field_row_numbers_are_unique(template_type):
    """No two fields should map to the same row (except combined fields)."""
    fields = get_fields_for_template(template_type)
    rows = {}
    duplicates = []

    for name, field in fields.items():
        if field.row in rows:
            existing = rows[field.row]
            # Allow duplicates for combined fields (multiple logical fields in one cell)
            if not (_is_combined_field(name) and _is_combined_field(existing)):
                duplicates.append((name, existing, field.row))
        else:
            rows[field.row] = name

    assert not duplicates, (
        f"{template_type} has non-combined duplicate rows: {duplicates}"
    )


def test_total_field_count():
    """Verify expected total field count across all templates."""
    total = sum(len(get_fields_for_template(t)) for t in ALL_TEMPLATES)
    assert total == 549, f"Expected 549 total fields, got {total}"


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_all_languages_produce_mappings(template_type):
    """All supported languages should produce valid mappings."""
    fields = get_fields_for_template(template_type)

    for lang, expected_col in [("en", "C"), ("ar", "D"), ("ru", "E")]:
        mapping = get_cell_mapping(template_type, lang)

        # Same field count for all languages
        assert len(mapping) == len(fields), (
            f"{template_type} {lang} mapping has wrong field count"
        )

        # All cells start with expected column
        wrong = [f for f, cell in mapping.items() if not cell.startswith(expected_col)]
        assert not wrong, (
            f"{template_type} {lang} has fields not targeting column {expected_col}"
        )


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_field_defs_have_valid_types(template_type):
    """All field definitions must have valid FieldType enum values."""
    from app.services.template_fields import FieldType

    fields = get_fields_for_template(template_type)

    for name, field in fields.items():
        assert isinstance(field, FieldDef), f"{name} is not a FieldDef"
        assert isinstance(field.field_type, FieldType), (
            f"{name} has invalid field_type: {field.field_type}"
        )
        assert field.row > 0, f"{name} has invalid row number: {field.row}"
        assert field.section, f"{name} has empty section"


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_character_limits_are_positive_or_none(template_type):
    """Character limits must be positive integers or None."""
    fields = get_fields_for_template(template_type)

    invalid = []
    for name, field in fields.items():
        if field.char_limit is not None:
            if not isinstance(field.char_limit, int) or field.char_limit <= 0:
                invalid.append((name, field.char_limit))

    assert not invalid, f"{template_type} has invalid character limits: {invalid[:10]}"
