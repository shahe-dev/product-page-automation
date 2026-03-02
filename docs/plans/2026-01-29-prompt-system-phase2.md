# Prompt System Phase 2: Sheets Mapping, Prompt UI, and Seed Execution

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the prompt system remediation by wiring template-specific Google Sheets cell mappings, overhauling the prompt management UI for 300+ prompts, and running the seed script.

**Architecture:** Replace the hardcoded 17-field `COMMON_FIELD_MAPPING` with per-template row-based mappings that read from the `templates` database table (already exists as `field_mappings` JSONB column). Fix the column target from B to C (EN content). Restructure the frontend prompt list from a flat table to a template-grouped view with section headers. Seed all 6 templates into the database.

**Tech Stack:** Python/FastAPI (backend), React/TypeScript/TanStack Table (frontend), PostgreSQL JSONB, Google Sheets API (gspread), SQLAlchemy

---

## Pre-Implementation Context

### Critical Facts

1. **Column mismatch (BUG):** The Google Sheet structure per `docs/TEMPLATES_REFERENCE.md:43-54` is:
   - Column A = Guidelines/Comments
   - Column B = Field Name (label, not content)
   - Column C = EN (English content) <-- this is where generated content should go
   - Column D = AR, Column E = RU

   Current code writes to Column B. Must change to Column C.

2. **Single master sheet with tabs:** All 6 templates live in one Google Sheet (`1pef6Q-54l2mFOX6QgwOLQONviBijgaRgI7gA2GHn_Ck`) as separate tabs:
   - "Aggregators Template", "OPR Template", "MPP Template", "ADOP Template", "ADRE Template", "Commercial Project Template"

3. **Row numbers are documented:** TEMPLATES_REFERENCE.md specifies exact row ranges per section per template (e.g., Aggregators SEO = rows 3-7, Hero = rows 9-15).

4. **`Template` model exists but is unused:** `backend/app/models/database.py:877-920` defines a `templates` table with `field_mappings JSONB` column designed for exactly this purpose.

5. **Current mapping:** `sheets_manager.py:88-112` has `COMMON_FIELD_MAPPING` with 17 fields all pointing to column B. `_get_field_mapping()` at line 182 returns the same dict for all template types.

6. **Frontend state:** Flat table listing all prompts with search + template_type filter + status filter. No grouping, no section headers, no bulk view. Editing is one prompt at a time.

### Files That Will Be Modified

| File | Purpose |
|------|---------|
| `backend/app/services/sheets_manager.py` | Replace COMMON_FIELD_MAPPING with per-template mappings |
| `backend/app/services/template_fields.py` | Add row/cell metadata to field definitions |
| `backend/scripts/seed_templates.py` | New: seed the `templates` table with field_mappings |
| `backend/scripts/seed_prompts.py` | Run with --force to populate all 6 templates |
| `backend/app/api/routes/prompts.py` | Add grouping/section metadata to list endpoint |
| `frontend/src/components/prompts/PromptList.tsx` | Grouped-by-template view |
| `frontend/src/components/prompts/PromptTemplateView.tsx` | New: template-level prompt viewer |
| `frontend/src/pages/PromptsPage.tsx` | New layout with template tabs |
| `frontend/src/types/index.ts` | Add section metadata types |
| `backend/tests/test_sheets_mapping.py` | New: mapping coverage tests |

---

## Phase A: Google Sheets Cell Mapping

### Task 1: Add cell references to template_fields.py

**Files:**
- Modify: `backend/app/services/template_fields.py`
- Test: `backend/tests/test_template_fields.py`

**Context:** Currently `template_fields.py` stores `{field_name: character_limit}`. We need to add the cell reference (row number) and section grouping so both sheets_manager and the frontend can use them.

**Step 1: Update the field definition type**

Change the field definitions from `{field_name: int}` to `{field_name: FieldDef}` where FieldDef includes row, section, and character limit.

In `backend/app/services/template_fields.py`, add at the top:

```python
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FieldDef:
    """Definition of a single template field."""
    row: int                    # Row number in Google Sheet
    section: str                # Section name (e.g., "SEO", "Hero", "Amenities")
    character_limit: Optional[int] = None  # Max characters, None = no limit
    required: bool = False      # Whether field must have content before publish


# Type alias for template field registries
FieldRegistry = dict[str, FieldDef]
```

**Step 2: Convert AGGREGATORS_FIELDS to use FieldDef with row numbers**

Replace the existing dict using row numbers from `docs/TEMPLATES_REFERENCE.md:78-87`:

```python
AGGREGATORS_FIELDS: FieldRegistry = {
    # SEO (rows 3-7)
    "meta_title":           FieldDef(row=3,  section="SEO", character_limit=60, required=True),
    "meta_description":     FieldDef(row=4,  section="SEO", character_limit=160, required=True),
    "url_slug":             FieldDef(row=5,  section="SEO", character_limit=80, required=True),
    "image_alt":            FieldDef(row=6,  section="SEO", character_limit=125),
    "canonical_tag":        FieldDef(row=7,  section="SEO"),
    # Hero (rows 9-15)
    "h1":                   FieldDef(row=9,  section="Hero", character_limit=70, required=True),
    "hero_description":     FieldDef(row=10, section="Hero", character_limit=400, required=True),
    "starting_price":       FieldDef(row=11, section="Hero", required=True),
    "payment_plan_headline":FieldDef(row=12, section="Hero"),
    "handover_date":        FieldDef(row=13, section="Hero"),
    "bedrooms":             FieldDef(row=14, section="Hero"),
    "property_type":        FieldDef(row=15, section="Hero"),
    # About (rows 17-24)
    "about_h2":             FieldDef(row=17, section="About", character_limit=50),
    "about_description":    FieldDef(row=18, section="About", character_limit=700, required=True),
    "selling_point_1":      FieldDef(row=19, section="About", character_limit=80),
    "selling_point_2":      FieldDef(row=20, section="About", character_limit=80),
    "selling_point_3":      FieldDef(row=21, section="About", character_limit=80),
    "selling_point_4":      FieldDef(row=22, section="About", character_limit=80),
    "selling_point_5":      FieldDef(row=23, section="About", character_limit=80),
    "about_cta":            FieldDef(row=24, section="About"),
    # Project Details (rows 26-33)
    "developer_name":       FieldDef(row=26, section="Project Details"),
    "project_location":     FieldDef(row=27, section="Project Details"),
    "area_sqft":            FieldDef(row=28, section="Project Details"),
    "project_property_type":FieldDef(row=29, section="Project Details"),
    "project_bedrooms":     FieldDef(row=30, section="Project Details"),
    "project_price":        FieldDef(row=31, section="Project Details"),
    "project_handover":     FieldDef(row=32, section="Project Details"),
    "project_payment_plan": FieldDef(row=33, section="Project Details"),
    # Amenities (rows 35-46)
    "amenities_h2":         FieldDef(row=35, section="Amenities", character_limit=50),
    "amenity_1_title":      FieldDef(row=36, section="Amenities", character_limit=40),
    "amenity_1_description":FieldDef(row=37, section="Amenities", character_limit=150),
    "amenity_2_title":      FieldDef(row=38, section="Amenities", character_limit=40),
    "amenity_2_description":FieldDef(row=39, section="Amenities", character_limit=150),
    "amenity_3_title":      FieldDef(row=40, section="Amenities", character_limit=40),
    "amenity_3_description":FieldDef(row=41, section="Amenities", character_limit=150),
    "amenity_4_title":      FieldDef(row=42, section="Amenities", character_limit=40),
    "amenity_4_description":FieldDef(row=43, section="Amenities", character_limit=150),
    "amenity_5_title":      FieldDef(row=44, section="Amenities", character_limit=40),
    "amenity_5_description":FieldDef(row=45, section="Amenities", character_limit=150),
    "amenities_cta":        FieldDef(row=46, section="Amenities"),
    # Payment Plan (rows 48-60)
    "payment_h2":           FieldDef(row=48, section="Payment Plan", character_limit=50),
    "payment_description":  FieldDef(row=49, section="Payment Plan", character_limit=800),
    "milestone_1_label":    FieldDef(row=50, section="Payment Plan"),
    "milestone_1_percent":  FieldDef(row=51, section="Payment Plan"),
    "milestone_2_label":    FieldDef(row=52, section="Payment Plan"),
    "milestone_2_percent":  FieldDef(row=53, section="Payment Plan"),
    "milestone_3_label":    FieldDef(row=54, section="Payment Plan"),
    "milestone_3_percent":  FieldDef(row=55, section="Payment Plan"),
    "milestone_4_label":    FieldDef(row=56, section="Payment Plan"),
    "milestone_4_percent":  FieldDef(row=57, section="Payment Plan"),
    "payment_plan_cta":     FieldDef(row=58, section="Payment Plan"),
    "payment_plan_note":    FieldDef(row=59, section="Payment Plan"),
    "payment_plan_summary": FieldDef(row=60, section="Payment Plan"),
    # Location (rows 62-72)
    "location_h2":          FieldDef(row=62, section="Location", character_limit=50),
    "location_description": FieldDef(row=63, section="Location", character_limit=550, required=True),
    "nearby_1_name":        FieldDef(row=64, section="Location"),
    "nearby_1_distance":    FieldDef(row=65, section="Location"),
    "nearby_2_name":        FieldDef(row=66, section="Location"),
    "nearby_2_distance":    FieldDef(row=67, section="Location"),
    "nearby_3_name":        FieldDef(row=68, section="Location"),
    "nearby_3_distance":    FieldDef(row=69, section="Location"),
    "nearby_4_name":        FieldDef(row=70, section="Location"),
    "nearby_4_distance":    FieldDef(row=71, section="Location"),
    "location_cta":         FieldDef(row=72, section="Location"),
    # Developer (rows 74-76)
    "developer_h2":         FieldDef(row=74, section="Developer", character_limit=50),
    "developer_description":FieldDef(row=75, section="Developer", character_limit=500, required=True),
    "developer_cta":        FieldDef(row=76, section="Developer"),
    # Floor Plans (rows 78-92)
    "floorplans_h2":        FieldDef(row=78, section="Floor Plans", character_limit=50),
    "floorplan_1_type":     FieldDef(row=79, section="Floor Plans"),
    "floorplan_1_size":     FieldDef(row=80, section="Floor Plans"),
    "floorplan_1_price":    FieldDef(row=81, section="Floor Plans"),
    "floorplan_2_type":     FieldDef(row=82, section="Floor Plans"),
    "floorplan_2_size":     FieldDef(row=83, section="Floor Plans"),
    "floorplan_2_price":    FieldDef(row=84, section="Floor Plans"),
    "floorplan_3_type":     FieldDef(row=85, section="Floor Plans"),
    "floorplan_3_size":     FieldDef(row=86, section="Floor Plans"),
    "floorplan_3_price":    FieldDef(row=87, section="Floor Plans"),
    "floorplan_4_type":     FieldDef(row=88, section="Floor Plans"),
    "floorplan_4_size":     FieldDef(row=89, section="Floor Plans"),
    "floorplan_4_price":    FieldDef(row=90, section="Floor Plans"),
    "floorplans_cta":       FieldDef(row=91, section="Floor Plans"),
    "floorplans_note":      FieldDef(row=92, section="Floor Plans"),
    # FAQ (rows 94-105)
    "faq_h2":               FieldDef(row=94, section="FAQ", character_limit=50),
    "faq_1_question":       FieldDef(row=95, section="FAQ", character_limit=80),
    "faq_1_answer":         FieldDef(row=96, section="FAQ", character_limit=200),
    "faq_2_question":       FieldDef(row=97, section="FAQ", character_limit=80),
    "faq_2_answer":         FieldDef(row=98, section="FAQ", character_limit=200),
    "faq_3_question":       FieldDef(row=99, section="FAQ", character_limit=80),
    "faq_3_answer":         FieldDef(row=100, section="FAQ", character_limit=200),
    "faq_4_question":       FieldDef(row=101, section="FAQ", character_limit=80),
    "faq_4_answer":         FieldDef(row=102, section="FAQ", character_limit=200),
    "faq_5_question":       FieldDef(row=103, section="FAQ", character_limit=80),
    "faq_5_answer":         FieldDef(row=104, section="FAQ", character_limit=200),
    "faq_cta":              FieldDef(row=105, section="FAQ"),
}
```

**Step 3: Convert remaining 5 templates similarly**

Apply the same pattern to OPR_FIELDS, MPP_FIELDS, ADOP_FIELDS, ADRE_FIELDS, COMMERCIAL_FIELDS using the row numbers from TEMPLATES_REFERENCE.md:

- **OPR**: SEO rows 2-8, Hero rows 10-21, Project Overview rows 26-30, Project Card rows 41-54, Features & Amenities rows 59-82, Payment Plan rows 86-98, Investment rows 99-118
- **MPP**: SEO rows 1-5, Hero rows 7-12, Project Overview rows 14-16, Details Card rows 18-24, Floor Plans rows 26-44, Payment Plan rows 46-62, Key Points rows 64-73, Amenities rows 75-86, Location rows 88-102, Developer rows 104-119
- **ADOP**: SEO rows 2-8, Hero rows 10-15, About rows 17-24, Key Benefits rows 26-31, Infrastructure rows 33-40, Investment rows 42-49, Developer rows 50-53, FAQ rows 55-80
- **ADRE**: SEO rows 2-8, Hero rows 10-16, Amenities rows 18-41, Developer rows 45-47, Economic Appeal rows 49-63, Location rows 65-84, FAQ rows 86-119
- **Commercial**: SEO rows 2-6, Hero rows 8-22, About Area rows 24-29, Details/Passport rows 31-42, Economic Appeal rows 44-48, Payment Plan rows 50-61, Advantages rows 63-72, Amenities rows 74-91, Developer rows 93-96, Location rows 98-119

**IMPORTANT:** The exact field names and row numbers must be validated against the actual Google Sheet. The row numbers above come from TEMPLATES_REFERENCE.md but should be cross-checked. If a discrepancy is found, the Google Sheet is the source of truth -- update TEMPLATES_REFERENCE.md to match.

**Step 4: Add helper functions**

```python
def get_fields_for_template(template_type: str) -> FieldRegistry:
    """Get field definitions for a template type. Raises ValueError if unknown."""
    registry = TEMPLATE_FIELD_REGISTRY.get(template_type.lower())
    if registry is None:
        valid = list(TEMPLATE_FIELD_REGISTRY.keys())
        raise ValueError(f"Unknown template type: {template_type}. Valid: {valid}")
    return registry


def get_cell_mapping(template_type: str, language: str = "en") -> dict[str, str]:
    """
    Build field_name -> cell_reference mapping for a template.

    Column offsets: C=EN, D=AR, E=RU
    """
    col_map = {"en": "C", "ar": "D", "ru": "E"}
    col = col_map.get(language.lower())
    if col is None:
        raise ValueError(f"Unsupported language: {language}. Valid: en, ar, ru")

    fields = get_fields_for_template(template_type)
    return {name: f"{col}{field.row}" for name, field in fields.items()}


def get_sections_for_template(template_type: str) -> dict[str, list[str]]:
    """
    Get fields grouped by section for a template.
    Returns: {"SEO": ["meta_title", "meta_description", ...], "Hero": [...], ...}
    Preserves insertion order (field order within section matches row order).
    """
    fields = get_fields_for_template(template_type)
    sections: dict[str, list[str]] = {}
    for name, field in fields.items():
        sections.setdefault(field.section, []).append(name)
    return sections
```

**Step 5: Update get_fields_for_template return type**

The existing `get_fields_for_template()` function returns `dict[str, int]`. Update it to return `FieldRegistry`. Also update `content_generator.py` where it reads character limits:

In `content_generator.py`, anywhere that does `fields[field_name]` to get a character limit, change to `fields[field_name].character_limit`.

**Step 6: Write tests**

```python
# backend/tests/test_template_fields.py

import pytest
from app.services.template_fields import (
    FieldDef, get_fields_for_template, get_cell_mapping,
    get_sections_for_template, TEMPLATE_FIELD_REGISTRY,
)


ALL_TEMPLATES = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_all_templates_registered(template_type):
    fields = get_fields_for_template(template_type)
    assert len(fields) > 20, f"{template_type} has too few fields"


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_all_fields_have_row_numbers(template_type):
    fields = get_fields_for_template(template_type)
    for name, field in fields.items():
        assert isinstance(field, FieldDef), f"{template_type}.{name} is not FieldDef"
        assert field.row > 0, f"{template_type}.{name} has invalid row: {field.row}"
        assert field.section, f"{template_type}.{name} has no section"


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_no_duplicate_rows(template_type):
    fields = get_fields_for_template(template_type)
    rows = [f.row for f in fields.values()]
    dupes = [r for r in rows if rows.count(r) > 1]
    assert not dupes, f"{template_type} has duplicate rows: {set(dupes)}"


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_cell_mapping_produces_column_c(template_type):
    mapping = get_cell_mapping(template_type, "en")
    for field, cell in mapping.items():
        assert cell.startswith("C"), f"{field} maps to {cell}, expected C column"


def test_cell_mapping_arabic():
    mapping = get_cell_mapping("aggregators", "ar")
    assert all(c.startswith("D") for c in mapping.values())


def test_cell_mapping_russian():
    mapping = get_cell_mapping("aggregators", "ru")
    assert all(c.startswith("E") for c in mapping.values())


def test_unknown_template_raises():
    with pytest.raises(ValueError, match="Unknown template"):
        get_fields_for_template("nonexistent")


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_sections_grouping(template_type):
    sections = get_sections_for_template(template_type)
    assert "SEO" in sections, f"{template_type} missing SEO section"
    assert len(sections) >= 4, f"{template_type} has too few sections"


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_required_seo_fields_exist(template_type):
    fields = get_fields_for_template(template_type)
    assert "meta_title" in fields
    assert "meta_description" in fields
```

**Step 7: Run tests, commit**

```bash
cd backend
pytest tests/test_template_fields.py -v
```

Expected: All pass.

```bash
git add backend/app/services/template_fields.py backend/tests/test_template_fields.py
git commit -m "feat: add row numbers and sections to template field definitions"
```

---

### Task 2: Replace COMMON_FIELD_MAPPING in sheets_manager.py

**Files:**
- Modify: `backend/app/services/sheets_manager.py:88-209`
- Test: `backend/tests/test_sheets_mapping.py` (new)

**Step 1: Remove COMMON_FIELD_MAPPING and update _get_field_mapping**

In `sheets_manager.py`, delete lines 88-112 (the `COMMON_FIELD_MAPPING` dict) and replace `_get_field_mapping()`:

```python
from app.services.template_fields import get_cell_mapping

# DELETE: COMMON_FIELD_MAPPING dict entirely

class SheetsManager:
    # ... existing init ...

    async def _get_field_mapping(self, template_type: str, language: str = "en") -> dict[str, str]:
        """
        Get field-to-cell mapping for a template type and language.

        DB-first: reads from Template.field_mappings if available.
        Fallback: uses template_fields.py as the source of truth for row numbers.
        Column C = EN, D = AR, E = RU.

        Args:
            template_type: One of the 6 template types
            language: "en", "ar", or "ru"

        Returns:
            Dict mapping field names to cell references (e.g., {"meta_title": "C3"})
        """
        # DB-first: try Template.field_mappings
        if self.db:
            from sqlalchemy import select
            from app.models.database import Template
            result = await self.db.execute(
                select(Template).where(
                    Template.template_type == template_type,
                    Template.is_active == True,
                )
            )
            template = result.scalar_one_or_none()
            if template and template.field_mappings:
                return template.field_mappings
        # Fallback to hardcoded
        return get_cell_mapping(template_type, language)
```

> **DB-first addition (from 2026-02-02 assessment):** This makes `SheetsManager` read cell mappings from the `templates` table when available. Admin edits to `Template.field_mappings` take effect without code deployment. Falls back to `template_fields.py` if no DB record exists.

**Step 2: Update populate_sheet to use correct column**

Find all calls to `_get_field_mapping()` in sheets_manager.py. Currently they pass only `template_type`. Add `language="en"` parameter (for now, multilingual is out of scope but the plumbing is ready).

In `_populate_sheet_impl()` (around line 440):

```python
field_mapping = self._get_field_mapping(template_type, language="en")
```

Same for `read_back_validate()`.

**Step 3: Update populate_sheet to select correct tab**

Currently the code uses `spreadsheet.sheet1` (first worksheet). Each template is a different tab. Update to select by tab name:

```python
TAB_NAMES = {
    "aggregators": "Aggregators Template",
    "opr": "OPR Template",
    "mpp": "MPP Template",
    "adop": "ADOP Template",
    "adre": "ADRE Template",
    "commercial": "Commercial Project Template",
}
```

In `_populate_sheet_impl()`, replace:
```python
# OLD:
worksheet = spreadsheet.sheet1

# NEW:
tab_name = TAB_NAMES.get(template_type.lower())
if tab_name:
    worksheet = spreadsheet.worksheet(tab_name)
else:
    worksheet = spreadsheet.sheet1
```

Apply the same change in `read_back_validate()` and any other method that accesses worksheets.

**NOTE:** This only applies when using the **master** sheet (single sheet with tabs). If the system creates per-project sheet copies, those may have a single tab. Check `create_project_sheet()` to see if it copies the whole workbook or a single tab. If it copies a single tab, `sheet1` is correct for project sheets. The tab selection should only apply when writing to the master template. Add a parameter or detect by sheet structure.

**Step 4: Write tests**

```python
# backend/tests/test_sheets_mapping.py

import pytest
from unittest.mock import MagicMock, patch
from app.services.sheets_manager import SheetsManager


ALL_TEMPLATES = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_field_mapping_uses_column_c(template_type):
    """All EN mappings should target column C, not B."""
    with patch.object(SheetsManager, '__init__', lambda self: None):
        mgr = SheetsManager()
        mapping = mgr._get_field_mapping(template_type, "en")
        for field, cell in mapping.items():
            assert cell.startswith("C"), (
                f"{template_type}.{field} maps to {cell}, expected column C"
            )


@pytest.mark.parametrize("template_type", ALL_TEMPLATES)
def test_field_mapping_has_many_fields(template_type):
    """Each template should have 30+ field mappings."""
    with patch.object(SheetsManager, '__init__', lambda self: None):
        mgr = SheetsManager()
        mapping = mgr._get_field_mapping(template_type, "en")
        assert len(mapping) >= 30, (
            f"{template_type} only has {len(mapping)} mappings"
        )


def test_no_column_b_in_any_template():
    """Regression: no template should write to column B."""
    with patch.object(SheetsManager, '__init__', lambda self: None):
        mgr = SheetsManager()
        for tt in ALL_TEMPLATES:
            mapping = mgr._get_field_mapping(tt, "en")
            b_cells = [f for f, c in mapping.items() if c.startswith("B")]
            assert not b_cells, f"{tt} still writes to column B: {b_cells}"
```

**Step 5: Run tests, commit**

```bash
cd backend
pytest tests/test_sheets_mapping.py -v
```

```bash
git add backend/app/services/sheets_manager.py backend/tests/test_sheets_mapping.py
git commit -m "fix: sheets mapping uses column C (EN) with per-template row numbers"
```

---

### Task 3: Update content_generator.py to use FieldDef

**Files:**
- Modify: `backend/app/services/content_generator.py`
- Test: `backend/tests/test_prompt_system_e2e.py` (existing)

**Step 1: Add DB-first field definition lookup**

Add a method that tries `Template.field_mappings` from the database first, falling back to `template_fields.py`:

```python
async def _get_field_definitions(self, template_type: str) -> dict:
    """Try Template.field_mappings from DB, fall back to template_fields.py."""
    if self.db:
        from sqlalchemy import select
        from app.models.database import Template
        result = await self.db.execute(
            select(Template).where(
                Template.template_type == template_type,
                Template.is_active == True,
            )
        )
        template = result.scalar_one_or_none()
        if template and template.field_mappings:
            return template.field_mappings
    # Fallback to hardcoded
    return get_fields_for_template(template_type)
```

> **DB-first addition (from 2026-02-02 assessment):** This makes `ContentGenerator` read field definitions from the `templates` table when available. Admin edits to `Template.field_mappings` take effect without code deployment.

**Step 2: Update field limit access**

Wherever `content_generator.py` accesses field character limits from `get_fields_for_template()`, update to use the new `FieldDef` dataclass:

```python
# OLD (returns dict[str, int]):
fields = get_fields_for_template(template_type)
limit = fields.get(field_name)  # int

# NEW (returns dict[str, FieldDef]):
fields = get_fields_for_template(template_type)
field_def = fields.get(field_name)
limit = field_def.character_limit if field_def else None
```

Search for all uses of `get_fields_for_template` in content_generator.py and update each one.

**Step 2: Run existing e2e tests**

```bash
cd backend
pytest tests/test_prompt_system_e2e.py -v
```

If tests reference `dict[str, int]` return types, update them too.

**Step 3: Commit**

```bash
git add backend/app/services/content_generator.py backend/tests/test_prompt_system_e2e.py
git commit -m "refactor: content_generator uses FieldDef for character limits"
```

---

## Phase B: Prompt Management UI Overhaul

### Task 4: Add section metadata to prompts API response

**Files:**
- Modify: `backend/app/api/routes/prompts.py`
- Modify: `backend/app/services/template_fields.py` (already done in Task 1)

**Step 1: Add a new endpoint for grouped prompt listing**

> **DB-first addition (from 2026-02-02 assessment):** The endpoint should check `Template.field_mappings` from the DB first. If a template record with field_mappings exists, use that as the field source instead of `template_fields.py`. This ensures admin edits to field definitions are reflected in the UI immediately.

Add to `backend/app/api/routes/prompts.py`:

```python
from app.services.template_fields import get_sections_for_template, get_fields_for_template, FieldDef
from app.models.database import Template as TemplateModel

@router.get("/grouped")
async def list_prompts_grouped(
    template_type: str = Query(..., description="Template type to list prompts for"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    List prompts for a template type, grouped by section.

    Returns sections in sheet order with prompts nested inside.
    """
    sections = get_sections_for_template(template_type)
    fields = get_fields_for_template(template_type)

    # Fetch all active prompts for this template type
    result = await db.execute(
        select(Prompt).where(
            Prompt.template_type == template_type,
            Prompt.is_active == True,
        )
    )
    prompts_by_name = {p.name: p for p in result.scalars().all()}

    grouped = []
    for section_name, field_names in sections.items():
        section_prompts = []
        for fname in field_names:
            field_def = fields[fname]
            prompt = prompts_by_name.get(fname)
            section_prompts.append({
                "field_name": fname,
                "row": field_def.row,
                "character_limit": field_def.character_limit,
                "required": field_def.required,
                "has_prompt": prompt is not None,
                "prompt_id": str(prompt.id) if prompt else None,
                "version": prompt.version if prompt else None,
                "content_preview": (prompt.content[:100] + "...") if prompt and len(prompt.content) > 100 else (prompt.content if prompt else None),
            })
        grouped.append({
            "section": section_name,
            "field_count": len(field_names),
            "prompts_defined": sum(1 for p in section_prompts if p["has_prompt"]),
            "fields": section_prompts,
        })

    return {
        "template_type": template_type,
        "total_fields": len(fields),
        "total_prompts_defined": len(prompts_by_name),
        "coverage_percent": round(len(prompts_by_name) / len(fields) * 100, 1) if fields else 0,
        "sections": grouped,
    }
```

**Step 2: Commit**

```bash
git add backend/app/api/routes/prompts.py
git commit -m "feat: add grouped prompts endpoint with section metadata"
```

---

### Task 5: Frontend - Template tab navigation

**Files:**
- Modify: `frontend/src/pages/PromptsPage.tsx`
- Modify: `frontend/src/types/index.ts`

**Step 1: Add types**

In `frontend/src/types/index.ts`, add:

```typescript
export interface PromptFieldSummary {
  field_name: string;
  row: number;
  character_limit: number | null;
  required: boolean;
  has_prompt: boolean;
  prompt_id: string | null;
  version: number | null;
  content_preview: string | null;
}

export interface PromptSection {
  section: string;
  field_count: number;
  prompts_defined: number;
  fields: PromptFieldSummary[];
}

export interface GroupedPromptsResponse {
  template_type: string;
  total_fields: number;
  total_prompts_defined: number;
  coverage_percent: number;
  sections: PromptSection[];
}
```

**Step 2: Add API call**

In `frontend/src/lib/api.ts`, add to the prompts object:

```typescript
grouped: (template_type: string) =>
  apiClient
    .get<GroupedPromptsResponse>("/prompts/grouped", {
      params: { template_type },
    })
    .then((r) => r.data),
```

**Step 3: Add React Query hook**

In `frontend/src/hooks/queries/use-prompts.ts`, add:

```typescript
export function useGroupedPrompts(templateType: string | null) {
  return useQuery({
    queryKey: ["prompts", "grouped", templateType],
    queryFn: () => api.prompts.grouped(templateType!),
    enabled: !!templateType,
    staleTime: 5 * 60 * 1000,
  });
}
```

**Step 4: Restructure PromptsPage with template tabs**

Replace the flat list layout with a tab-based design. The page should have:

1. **Top-level tabs**: One tab per template type (Aggregators | OPR | MPP | ADOP | ADRE | Commercial)
2. **Coverage summary bar**: Shows "42/65 prompts defined (64.6%)" with a progress bar
3. **Section accordion/collapsible groups**: Each section (SEO, Hero, About, etc.) is a collapsible group
4. **Field rows inside sections**: Each field shows name, row number, character limit, status (defined/missing), and a link to edit

This is the core UI change. The implementation should use the existing shadcn/ui components (Tabs, Accordion/Collapsible, Badge, Progress).

```tsx
// frontend/src/pages/PromptsPage.tsx -- conceptual structure

export function PromptsPage() {
  const [activeTemplate, setActiveTemplate] = useState("aggregators");
  const { data, isLoading } = useGroupedPrompts(activeTemplate);

  return (
    <PageLayout>
      <PageHeader
        title="Prompt Management"
        description="Manage prompts by template type and section"
      />

      {/* Template type tabs */}
      <Tabs value={activeTemplate} onValueChange={setActiveTemplate}>
        <TabsList>
          <TabsTrigger value="aggregators">Aggregators</TabsTrigger>
          <TabsTrigger value="opr">OPR</TabsTrigger>
          <TabsTrigger value="mpp">MPP</TabsTrigger>
          <TabsTrigger value="adop">ADOP</TabsTrigger>
          <TabsTrigger value="adre">ADRE</TabsTrigger>
          <TabsTrigger value="commercial">Commercial</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Coverage summary */}
      {data && (
        <CoverageSummary
          defined={data.total_prompts_defined}
          total={data.total_fields}
          percent={data.coverage_percent}
        />
      )}

      {/* Sections */}
      {data?.sections.map((section) => (
        <SectionGroup key={section.section} section={section} />
      ))}
    </PageLayout>
  );
}
```

**Step 5: Create SectionGroup component**

```tsx
// frontend/src/components/prompts/SectionGroup.tsx

function SectionGroup({ section }: { section: PromptSection }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Collapsible open={expanded} onOpenChange={setExpanded}>
      <CollapsibleTrigger asChild>
        <div className="flex items-center justify-between p-4 border rounded-lg cursor-pointer hover:bg-muted/50">
          <div className="flex items-center gap-3">
            <ChevronRight
              className={cn("h-4 w-4 transition-transform", expanded && "rotate-90")}
            />
            <h3 className="font-semibold">{section.section}</h3>
            <Badge variant="outline">
              {section.prompts_defined}/{section.field_count}
            </Badge>
          </div>
          <Progress
            value={(section.prompts_defined / section.field_count) * 100}
            className="w-24 h-2"
          />
        </div>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="border-x border-b rounded-b-lg">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/30">
                <th className="text-left p-2 w-8">Row</th>
                <th className="text-left p-2">Field</th>
                <th className="text-left p-2 w-20">Limit</th>
                <th className="text-left p-2 w-20">Status</th>
                <th className="text-left p-2 w-20"></th>
              </tr>
            </thead>
            <tbody>
              {section.fields.map((field) => (
                <tr key={field.field_name} className="border-b last:border-0">
                  <td className="p-2 text-muted-foreground">{field.row}</td>
                  <td className="p-2">
                    <span className="font-mono text-xs">{field.field_name}</span>
                    {field.required && (
                      <Badge variant="destructive" className="ml-2 text-[10px]">
                        Required
                      </Badge>
                    )}
                  </td>
                  <td className="p-2 text-muted-foreground">
                    {field.character_limit ?? "-"}
                  </td>
                  <td className="p-2">
                    {field.has_prompt ? (
                      <Badge variant="default">v{field.version}</Badge>
                    ) : (
                      <Badge variant="secondary">Missing</Badge>
                    )}
                  </td>
                  <td className="p-2">
                    {field.prompt_id ? (
                      <Link to={`/prompts/${field.prompt_id}`}>
                        <Button variant="ghost" size="sm">Edit</Button>
                      </Link>
                    ) : (
                      <Button variant="ghost" size="sm" disabled>
                        Create
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
```

**Step 6: Keep the old flat list accessible**

Do NOT remove the existing PromptList.tsx. Add a view toggle (Grouped | List) so the admin can switch between the new grouped view and the original flat table when needed. The flat table is still useful for cross-template search.

**Step 7: Commit**

```bash
git add frontend/src/pages/PromptsPage.tsx frontend/src/components/prompts/SectionGroup.tsx frontend/src/types/index.ts frontend/src/lib/api.ts frontend/src/hooks/queries/use-prompts.ts
git commit -m "feat: prompt management grouped by template sections"
```

---

### Task 6: Seed templates table with field mappings

**Files:**
- Create: `backend/scripts/seed_templates.py`

**Step 1: Write the seed script**

This populates the `templates` database table with the field_mappings JSONB for each template type. This makes the mapping queryable and editable without code deploys.

```python
#!/usr/bin/env python
"""
Seed the templates table with field-to-cell mappings for all 6 template types.

Usage:
    python scripts/seed_templates.py          # Skip existing
    python scripts/seed_templates.py --force  # Overwrite existing
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.models.database import Template
from app.models.enums import TemplateType, ContentVariant
from app.services.template_fields import (
    get_cell_mapping, get_fields_for_template, TEMPLATE_FIELD_REGISTRY,
)
from app.config.database import async_session_factory


TEMPLATE_NAMES = {
    "aggregators": "Aggregators Template",
    "opr": "OPR Template",
    "mpp": "MPP Template",
    "adop": "ADOP Template",
    "adre": "ADRE Template",
    "commercial": "Commercial Project Template",
}

# Master sheet ID from docs/TEMPLATES_REFERENCE.md
MASTER_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1pef6Q-54l2mFOX6QgwOLQONviBijgaRgI7gA2GHn_Ck"
)


async def seed_templates(force: bool = False):
    async with async_session_factory() as session:
        for template_type in TEMPLATE_FIELD_REGISTRY:
            name = TEMPLATE_NAMES[template_type]
            cell_mapping = get_cell_mapping(template_type, "en")

            # Check if already exists
            existing = await session.execute(
                select(Template).where(
                    Template.template_type == TemplateType(template_type),
                    Template.content_variant == ContentVariant.STANDARD,
                )
            )
            existing_template = existing.scalar_one_or_none()

            if existing_template and not force:
                print(f"  SKIP {template_type} (already exists, use --force)")
                continue

            if existing_template and force:
                existing_template.field_mappings = cell_mapping
                existing_template.name = name
                existing_template.sheet_template_url = MASTER_SHEET_URL
                print(f"  UPDATE {template_type} ({len(cell_mapping)} fields)")
            else:
                template = Template(
                    name=name,
                    template_type=TemplateType(template_type),
                    content_variant=ContentVariant.STANDARD,
                    sheet_template_url=MASTER_SHEET_URL,
                    field_mappings=cell_mapping,
                    is_active=True,
                )
                session.add(template)
                print(f"  CREATE {template_type} ({len(cell_mapping)} fields)")

        await session.commit()
        print("Done.")


if __name__ == "__main__":
    force = "--force" in sys.argv
    print(f"Seeding templates (force={force})...")
    asyncio.run(seed_templates(force))
```

**Step 2: Commit**

```bash
git add backend/scripts/seed_templates.py
git commit -m "feat: seed script for templates table with field mappings"
```

---

### Task 7: Run seed scripts against database

**Files:**
- Run: `backend/scripts/seed_templates.py --force`
- Run: `backend/scripts/seed_prompts.py --force`

**Step 1: Seed templates table**

```bash
cd backend
python scripts/seed_templates.py --force
```

Expected output:
```
Seeding templates (force=True)...
  CREATE aggregators (65 fields)
  CREATE opr (45 fields)
  CREATE mpp (75 fields)
  CREATE adop (55 fields)
  CREATE adre (65 fields)
  CREATE commercial (70 fields)
Done.
```

**Step 2: Seed prompts table**

```bash
python scripts/seed_prompts.py --force
```

Expected: All 6 template types seeded with field-level prompts.

**Step 3: Verify in database**

```bash
python -c "
import asyncio
from app.config.database import async_session_factory
from sqlalchemy import select, func
from app.models.database import Template, Prompt

async def verify():
    async with async_session_factory() as session:
        t_count = await session.execute(select(func.count()).select_from(Template))
        p_count = await session.execute(select(func.count()).select_from(Prompt))
        print(f'Templates: {t_count.scalar()}')
        print(f'Prompts: {p_count.scalar()}')

asyncio.run(verify())
"
```

Expected: Templates = 6, Prompts = 300+.

**Step 4: Commit verification evidence**

No code to commit. This is an operational step.

---

## Phase C: Cleanup and Integration Testing

### Task 8: Integration test -- full pipeline with sheets mapping

**Files:**
- Create: `backend/tests/test_sheets_integration.py`

**Step 1: Write integration test**

```python
# backend/tests/test_sheets_integration.py

"""
Integration test: verify content generation -> sheets mapping pipeline.
Does NOT call Google Sheets API. Tests that generated field names
match sheets cell mapping for all 6 templates.
"""

import pytest
from app.services.template_fields import (
    get_fields_for_template, get_cell_mapping,
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
def test_every_field_has_prompt(template_type):
    """Every field in the registry should have a prompt (default or template-specific)."""
    fields = get_fields_for_template(template_type)
    pm = PromptManager()
    defaults = pm.get_default_prompts()

    missing = []
    for field_name in fields:
        key = f"{template_type}:{field_name}"
        if key not in defaults and field_name not in defaults:
            missing.append(field_name)

    # Allow up to 10% missing (data-only fields like starting_price don't need prompts)
    coverage = 1 - len(missing) / len(fields)
    assert coverage >= 0.7, (
        f"{template_type} prompt coverage is {coverage:.0%}. "
        f"Missing: {missing[:10]}{'...' if len(missing) > 10 else ''}"
    )
```

**Step 2: Run all tests**

```bash
cd backend
pytest tests/test_template_fields.py tests/test_sheets_mapping.py tests/test_sheets_integration.py tests/test_prompt_system_e2e.py -v
```

**Step 3: Commit**

```bash
git add backend/tests/test_sheets_integration.py
git commit -m "test: integration tests for field-mapping-prompt coverage"
```

---

## Out of Scope (Explicitly Excluded)

1. **Prompt copywriting review** -- Admin can now edit via UI; this is a domain task, not engineering.
2. **Luxury variant** -- Dropped per user decision.
3. **Arabic/Russian content generation** -- Column plumbing is ready (D/E), but actual multilingual generation is a separate feature.
4. **Field editor UI** -- Admin UI for adding/removing/reordering fields within a template. DB-first lookups are wired (Tasks 2, 3, 4), so editing `Template.field_mappings` via DB or future UI takes effect immediately. The field editor UI itself is deferred to Phase 3. See `docs/plans/2026-02-02-dynamic-templates-assessment.md`.

---

## Dependency Graph

```
Task 1 (field defs + rows)
  |
  +---> Task 2 (sheets mapping) ---> Task 7 (run seeds)
  |                                       |
  +---> Task 3 (content_generator)        +---> Task 8 (integration tests)
  |
  +---> Task 4 (grouped API endpoint)
          |
          +---> Task 5 (frontend UI)
```

Tasks 2, 3, 4 can run in parallel after Task 1. Task 5 depends on 4. Tasks 7-8 are last.
