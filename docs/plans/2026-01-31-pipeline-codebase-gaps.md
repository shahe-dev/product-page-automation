# Pipeline & Codebase Gaps -- Post-Prompt Assessment

Date: 2026-01-31
Status: Pending implementation (after all 6 template prompts are finalized)
Prerequisite: All template prompts must be finalized before codebase work begins.
Branch: TBD (create from main after prompt work is complete)

## Context

During the OPR prompt assessment and revision, several gaps were identified between
the finalized prompt structure and the current codebase implementation. These gaps
affect field definitions, content generation, sheet mapping, and data flow between
pipeline stages.

This document captures ALL identified gaps across the pipeline to serve as the
implementation plan for codebase refinement. Gaps are organized by service/file
and prioritized.

---

## 1. template_fields.py -- Field Definition Gaps

File: `backend/app/services/template_fields.py`
Current state: "REWRITE PENDING" warning in file header. 22-58% match rate with
actual standardized Google Sheets.

### OPR_FIELDS changes needed:

| Action | Field Name | Char Limit | Notes |
|--------|-----------|------------|-------|
| ADD | `overview_bullet_points` | 500 | Multi-line extracted bullets |
| ADD | `location_access_h3` | 60 | Section heading |
| ADD | `location_access_bullets` | 500 | Multi-line "Name -- X min" format |
| ADD | `amenities_h3` | 60 | Section heading |
| ADD | `property_types_h3` | 200 | Generated intro sentence |
| ADD | `property_types_table` | 1000 | Multi-line extracted floor plans |
| ADD | `payment_milestones` | 300 | Multi-line extracted milestones |
| ADD | `lifestyle_h3` | 60 | Section heading |
| ADD | `lifestyle_description` | 200 | Generated intro text |
| ADD | `healthcare_h3` | 60 | Section heading |
| ADD | `healthcare_description` | 200 | Generated intro text |
| ADD | `education_h3` | 60 | Section heading |
| ADD | `education_description` | 200 | Generated intro text |
| ADD | `faq_13_question` | 100 | Lifestyle topic |
| ADD | `faq_13_answer` | 200 | Lifestyle topic |
| ADD | `faq_14_question` | 100 | Lifestyle topic |
| ADD | `faq_14_answer` | 200 | Lifestyle topic |
| ADD | `card_starting_price` | 30 | Project details card |
| ADD | `card_handover` | 30 | Project details card |
| ADD | `card_payment_plan` | 10 | Project details card |
| ADD | `card_area` | 40 | Project details card |
| ADD | `card_property_type` | 60 | Project details card |
| ADD | `card_bedrooms` | 60 | Project details card |
| ADD | `card_developer` | 60 | Project details card |
| ADD | `card_location` | 80 | Project details card |
| RENAME | `payment_plan_headline` | 10 | Keep as-is, maps to Payment Plan H3 |
| REMOVE | `location_access_1` thru `_6` | -- | Replace with single bullets field |
| REMOVE | `amenity_bullet_1` thru `_8` | -- | Replace with single bullets field |
| REMOVE | `investment_bullet_1` thru `_4` | -- | Replace with single bullets field |
| REMOVE | `faq_1` thru `faq_12` (individual) | -- | Replace with faq_1 thru faq_14 |

### Pattern: Variable-count fields

The current approach of numbered fields (location_access_1, location_access_2, etc.)
is fundamentally wrong for variable-count data. The actual template uses single cells
with multi-line content (one bullet per line). The field definitions should use single
fields with larger character limits instead of numbered fixed-count fields.

This applies to: location access bullets, amenity bullets, investment bullets,
lifestyle/healthcare/education bullets, overview bullets, property types table,
payment milestones.

### Impact on other templates

The same pattern applies to ALL 6 templates. Each template's field definitions
need the same audit after their prompts are finalized. The OPR changes above are
the reference pattern.

---

## 2. prompt_manager.py -- Prompt Generation Gaps

File: `backend/app/services/prompt_manager.py`

### OPR changes needed:

1. **Update `_get_opr_prompts()` method** to match the revised prompt structure:
   - Add FIELD CLASSIFICATION context to system message
   - Add EXTRACTED vs GENERATED tagging per field
   - Add anti-hallucination guardrails to system message
   - Add floor plan deduplication rules
   - Update amenities heading: "Private" -> "Resort-Style"

2. **Expand `_faq_topic_opr()` from 12 to 14 topics**:
   - Add topic 13: Lifestyle and living experience
   - Add topic 14: Lifestyle and living experience

3. **Add new field prompts**:
   - `overview_bullet_points`: extracted data, 4-6 bullets
   - `property_types_table`: extracted data with dedup rules
   - `payment_milestones`: extracted data with format rules
   - `lifestyle_description`, `healthcare_description`, `education_description`
   - All `card_*` fields (8 total)

4. **Mark EXTRACTED fields differently from GENERATED fields**:
   The current prompt system treats all fields as GENERATED (composing prose).
   Extracted fields need different prompts: "Copy this value exactly from the
   structured data input. If not available, write TBA."

### Architecture consideration

The current per-field prompt approach generates individual prompts for each field,
each requiring a separate LLM call (or batch). For extracted fields, this is wasteful.
Consider:
- Extracted fields could be populated directly from `data_structurer.py` output
  without an LLM call
- Only GENERATED fields need LLM prompts
- This reduces API calls and cost significantly

Priority: HIGH (cost reduction + accuracy improvement)

---

## 3. sheets_manager.py -- Field Mapping Gaps

File: `backend/app/services/sheets_manager.py`
Status: User confirmed this is already in the pipeline for remediation.

### Key issues:

1. **COMMON_FIELD_MAPPING uses column B for content** but actual sheets use column C
   (column B = field labels, column C = EN content, column D = AR, column E = RU)

2. **Fixed sequential mapping (B2, B3, B4...)** doesn't match actual sheet structure
   where rows have section separators, empty rows, and non-sequential field positions

3. **No template-specific mappings**: All 6 templates share one mapping dict, but each
   template has different row structures

### Required approach:

Each template needs its own mapping dict that maps field names to actual cell
references (e.g., `"meta_title": "C4"` for OPR). These mappings should be derived
from the standardized template sheets after all prompt/template work is complete.

Recommended: Build a script that reads each template sheet and auto-generates
the mapping by finding field labels in column B and mapping to column C for the
corresponding row.

---

## 4. content_generator.py -- Data Flow Gaps

File: `backend/app/services/content_generator.py`

### Floor plan data not injected into content generation

The `floor_plan_extractor.py` produces per-unit structured data:
- unit_type, bedrooms, total_sqft, balcony_sqft, builtup_sqft, features, confidence
- Deduplication at 95% pHash threshold (image-level only)

This data is NOT currently passed to `content_generator.py` when generating the
"Property Types Table" field. The content generator would need to compose the
table from floor plan extractor results.

### Required change:

When generating the `property_types_table` field, inject `floor_plan_extractor`
results as structured context into the prompt. Format:

```
FLOOR PLAN DATA (extracted from developer PDF via OCR):
- Studio: 400 sq ft (confidence: 0.92)
- 1BR: 650 sq ft (confidence: 0.88)
- 2BR: 1100 sq ft (confidence: 0.95)

Use ONLY this data for the Property Types Table.
If confidence < 0.7, mark as TBA.
```

Alternatively (preferred): skip the LLM call entirely for this field and compose
the table directly from structured floor plan data in Python.

---

## 5. data_structurer.py -- Missing Fields

File: `backend/app/services/data_structurer.py`

### StructuredProject dataclass gaps:

| Missing field | Type | Source |
|--------------|------|--------|
| `unit_configurations` | `list[dict]` | Per-unit: type, size_min, size_max, price |
| `payment_milestones` | `list[dict]` | milestone_name, percentage, timing |
| `location` | `str` | Community/area name |
| `sub_community` | Already exists | Needs validation |

The current `StructuredProject` has `property_type` (single string like "Residential")
and `bedrooms` (list like ["Studio", "1BR", "2BR"]). It does NOT have per-unit-type
size and price data, which is needed for the Property Types Table.

### Required change:

Add `unit_configurations` field:
```python
@dataclass
class UnitConfiguration:
    unit_type: str          # "Studio", "1BR Apartment", "2BR Apartment"
    bedrooms: int           # 0, 1, 2, 3
    size_min_sqft: Optional[float]
    size_max_sqft: Optional[float]
    starting_price: Optional[int]
    confidence: float

# In StructuredProject:
unit_configurations: list[UnitConfiguration] = field(default_factory=list)
```

---

## 6. job_manager.py -- Deduplication Gap

File: `backend/app/services/job_manager.py`

### Bedroom list not deduplicated (line 963):

```python
content_dict["bedrooms"] = ", ".join(structured.bedrooms) if structured.bedrooms else ""
```

If `structured.bedrooms = ["1BR", "2BR", "1BR", "2BR", "3BR"]`, the output is
`"1BR, 2BR, 1BR, 2BR, 3BR"` with duplicates.

### Fix:

```python
content_dict["bedrooms"] = ", ".join(dict.fromkeys(structured.bedrooms)) if structured.bedrooms else ""
```

Priority: LOW (quick fix, minimal impact)

---

## 7. deduplication_service.py -- Content-Level Gap

File: `backend/app/services/deduplication_service.py`

Current deduplication is IMAGE-ONLY (pHash at 90% general, 95% floor plans).
There is no content-level deduplication for:
- Duplicate unit type entries in floor plan data
- Duplicate amenity entries
- Duplicate bedroom entries

### Required:

Content-level dedup should happen in `data_structurer.py` or `job_manager.py`
before sheet population. The prompt-level dedup rules (merge variants into ranges)
handle the LLM output, but if we bypass the LLM for extracted fields, we need
Python-level dedup.

Priority: MEDIUM (after extracted field pipeline is built)

---

## Implementation Order

Phase 1 (after ALL template prompts are finalized):
1. template_fields.py -- Rewrite all 6 template field definitions
2. prompt_manager.py -- Update all 6 template prompt methods

Phase 2 (field mapping):
3. sheets_manager.py -- Build per-template field mappings
4. Write auto-mapping script to generate mappings from live sheets

Phase 3 (data flow optimization):
5. data_structurer.py -- Add unit_configurations to StructuredProject
6. content_generator.py -- Inject floor plan data, skip LLM for extracted fields
7. job_manager.py -- Dedup fixes, use new structured fields

Phase 4 (validation):
8. deduplication_service.py -- Add content-level dedup
9. End-to-end pipeline test with new prompt + field + mapping stack

---

## Dependencies

```
Prompt finalization (all 6 templates)
    |
    v
template_fields.py + prompt_manager.py (Phase 1)
    |
    v
sheets_manager.py mapping (Phase 2)
    |
    v
data_structurer.py + content_generator.py + job_manager.py (Phase 3)
    |
    v
deduplication + E2E testing (Phase 4)
```

Each phase depends on the previous. Do not start Phase 2 until Phase 1 is validated.

---

## Reference: Template Sheet IDs

| Template | Sheet ID |
|----------|----------|
| Aggregators | `YOUR_AGGREGATORS_SHEET_ID` |
| OPR | `YOUR_OPR_SHEET_ID` |
| MPP | `YOUR_MPP_SHEET_ID` |
| ADOP | `YOUR_ADOP_SHEET_ID` |
| ADRE | `YOUR_ADRE_SHEET_ID` |
| Commercial | `YOUR_COMMERCIAL_SHEET_ID` |

## Reference: Finalized Prompts

| Template | Prompt File | Status |
|----------|------------|--------|
| OPR | `prompt-organizaton/opr/prompt  opr.md` | DONE |
| Aggregators | TBD | Pending |
| Commercial | TBD | Pending |
| ADOP | TBD | Pending |
| ADRE | TBD | Pending |
| MPP | TBD | Pending |
