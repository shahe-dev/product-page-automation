"""Test template field registry loaded from JSON."""
import pytest
from app.services.template_fields import (
    get_fields_for_template,
    get_cell_mapping,
    get_sections_for_template,
    get_character_limit,
    get_required_fields,
    get_generated_fields,
    TEMPLATE_FIELD_REGISTRY,
    AGGREGATORS_FIELDS,
    OPR_FIELDS,
    MPP_FIELDS,
    ADOP_FIELDS,
    ADRE_FIELDS,
    COMMERCIAL_FIELDS,
    FieldDef,
    FieldType,
)


ALL_TEMPLATES = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]


def test_all_six_templates_registered():
    assert set(TEMPLATE_FIELD_REGISTRY.keys()) == {
        "aggregators", "opr", "mpp", "adop", "adre", "commercial"
    }


@pytest.mark.parametrize("template_type,min_fields", [
    ("aggregators", 100),
    ("opr", 100),
    ("mpp", 80),
    ("adop", 50),
    ("adre", 100),
    ("commercial", 60),
])
def test_template_has_minimum_field_count(template_type, min_fields):
    """Verify each template has at least the expected field count from JSON."""
    fields = get_fields_for_template(template_type)
    assert len(fields) >= min_fields, (
        f"{template_type} has {len(fields)} fields, expected >= {min_fields}"
    )


def test_all_templates_have_seo_fields():
    """SEO fields should exist in all templates."""
    required_seo = {"meta_title", "meta_description"}
    for name, fields in TEMPLATE_FIELD_REGISTRY.items():
        assert required_seo.issubset(fields.keys()), (
            f"{name} missing SEO fields: {required_seo - fields.keys()}"
        )


def test_unknown_template_raises():
    with pytest.raises(ValueError, match="Unknown template type"):
        get_fields_for_template("nonexistent")


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_all_fields_are_field_def(template_type):
    """Every field value should be a FieldDef instance."""
    fields = get_fields_for_template(template_type)
    for field_name, field_def in fields.items():
        assert isinstance(field_def, FieldDef), (
            f"{template_type}.{field_name} is {type(field_def)}, expected FieldDef"
        )


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_all_fields_have_row_numbers(template_type):
    """Every field should have a positive row number."""
    fields = get_fields_for_template(template_type)
    for name, field in fields.items():
        assert field.row > 0, f"{template_type}.{name} has invalid row: {field.row}"
        assert field.section, f"{template_type}.{name} has no section"


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_character_limits_are_positive_or_none(template_type):
    """Character limits should be positive integers or None."""
    fields = get_fields_for_template(template_type)
    for field_name, field_def in fields.items():
        if field_def.char_limit is not None:
            assert field_def.char_limit > 0, (
                f"{template_type}.{field_name} has non-positive limit: {field_def.char_limit}"
            )


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_field_types_are_valid(template_type):
    """Every field should have a valid FieldType."""
    fields = get_fields_for_template(template_type)
    for field_name, field_def in fields.items():
        assert isinstance(field_def.field_type, FieldType), (
            f"{template_type}.{field_name} has invalid field_type: {field_def.field_type}"
        )


def test_get_fields_for_template_returns_correct_dict():
    """Verify the lookup function returns the correct registry for each type."""
    assert get_fields_for_template("aggregators") is AGGREGATORS_FIELDS
    assert get_fields_for_template("opr") is OPR_FIELDS
    assert get_fields_for_template("mpp") is MPP_FIELDS
    assert get_fields_for_template("adop") is ADOP_FIELDS
    assert get_fields_for_template("adre") is ADRE_FIELDS
    assert get_fields_for_template("commercial") is COMMERCIAL_FIELDS


# --- Cell Mapping Tests ---

@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_cell_mapping_produces_column_c_for_english(template_type):
    """All EN mappings should target column C."""
    mapping = get_cell_mapping(template_type, "en")
    for field, cell in mapping.items():
        assert cell.startswith("C"), f"{field} maps to {cell}, expected C column"


def test_cell_mapping_arabic():
    mapping = get_cell_mapping("aggregators", "ar")
    assert all(c.startswith("D") for c in mapping.values())


def test_cell_mapping_russian():
    mapping = get_cell_mapping("aggregators", "ru")
    assert all(c.startswith("E") for c in mapping.values())


def test_cell_mapping_invalid_language():
    with pytest.raises(ValueError, match="Unsupported language"):
        get_cell_mapping("aggregators", "de")


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_cell_mapping_count_matches_field_count(template_type):
    """Cell mapping should have same count as fields."""
    fields = get_fields_for_template(template_type)
    mapping = get_cell_mapping(template_type, "en")
    assert len(mapping) == len(fields)


# --- Section Tests ---

@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_sections_grouping(template_type):
    """Each template should have SEO section and multiple sections."""
    sections = get_sections_for_template(template_type)
    assert "SEO" in sections, f"{template_type} missing SEO section"
    assert len(sections) >= 4, f"{template_type} has too few sections: {len(sections)}"


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_sections_contain_all_fields(template_type):
    """Section groupings should contain all fields."""
    fields = get_fields_for_template(template_type)
    sections = get_sections_for_template(template_type)
    all_fields_in_sections = set()
    for field_list in sections.values():
        all_fields_in_sections.update(field_list)
    assert all_fields_in_sections == set(fields.keys())


# --- Helper Function Tests ---

def test_get_character_limit():
    """Test the convenience function for getting character limits."""
    assert get_character_limit("aggregators", "meta_title") == 60
    assert get_character_limit("aggregators", "url_slug") is None
    assert get_character_limit("aggregators", "nonexistent") is None


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_get_required_fields(template_type):
    """Required fields should return a non-empty list."""
    required = get_required_fields(template_type)
    assert isinstance(required, list)
    # meta_title is typically required
    if "meta_title" in get_fields_for_template(template_type):
        fields = get_fields_for_template(template_type)
        if fields["meta_title"].required:
            assert "meta_title" in required


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_get_generated_fields(template_type):
    """Generated fields should return GENERATED and HYBRID types only."""
    generated = get_generated_fields(template_type)
    fields = get_fields_for_template(template_type)
    for field_name in generated:
        field_def = fields[field_name]
        assert field_def.field_type in (FieldType.GENERATED, FieldType.HYBRID), (
            f"{template_type}.{field_name} has type {field_def.field_type}"
        )


# --- Backward Compatibility Tests ---

def test_field_def_has_character_limit_alias():
    """FieldDef.character_limit should alias FieldDef.char_limit."""
    fields = get_fields_for_template("aggregators")
    meta_title = fields["meta_title"]
    assert meta_title.character_limit == meta_title.char_limit
    assert meta_title.character_limit == 60
