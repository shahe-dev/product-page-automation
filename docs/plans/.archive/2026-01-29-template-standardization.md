# Template Standardization -- Status & Next Steps

**Date:** 2026-01-29
**Status:** Phase 1 complete (MPP, Aggregators, ADOP)

---

## What Was Done

### 1. Audited all 6 template sheets

Ran audit against the live Google Sheets via service account. Found major inconsistencies:

| Template | Guidelines Col | Fields Col | EN | AR | RU | Extra |
|----------|---------------|-----------|-----|-----|-----|-------|
| Aggregators | B (wrong) | A (wrong) | C | E (wrong) | D (wrong) | -- |
| OPR | A | B | C | D | E | -- |
| MPP | A | B | C | D | E | De, Fr, Zh |
| ADOP | A | B | C | E (wrong) | D (wrong) | -- |
| ADRE | A | B | C | D | E | de, Fr, ch |
| Commercial | NONE | A | B | D (wrong) | C (wrong) | -- |

### 2. Created standardized copies (Phase 1: 3 templates)

All copies are in the **Standardized Templates** subfolder in the Shared Drive (folder ID: `1_T-x_8MXCneMEO2WlfhEAlVdw29N46Qv`).

| Template | Standardized Sheet | Sheet ID |
|----------|-------------------|----------|
| MPP | mpp-template-STANDARDIZED | `1YLfVIY6YVFFDGdMNsJ7lB_OGDFnHpBEvpp0Q4kKXJYY` |
| Aggregators | aggregators-template-STANDARDIZED | `1Od1pqJUC7f6kZic_qf7SVA2PGtUB4r_DQhDtR7zmZgU` |
| ADOP | adop-template-STANDARDIZED | `1sopQ7jgIvlU2Y96bqTR8TsyHJDMJ6zCdYS2N1gy2bQE` |

Standard format applied:
- Column A = Guidelines/Comments (human reference, NOT fed to LLM)
- Column B = Field Names (human-readable labels)
- Column C = EN, Column D = AR, Column E = RU
- Additional language columns (F+) preserved for MPP
- Section markers: A="SECTION", B=section name
- Empty separator rows between sections

### 3. Ran field mapping analysis

Compared sheet field names against `template_fields.py` code keys. Results saved to:
- `backend/scripts/field_mapping_report.json` -- full mapping
- `backend/scripts/standardized_template_ids.json` -- new sheet IDs

---

## Key Finding: template_fields.py is out of sync

The code's field definitions were written based on assumptions that don't match the actual templates.

**Gap summary:**

| Template | Sheet Fields | Code Fields | Exact Match |
|----------|-------------|-------------|-------------|
| MPP | 95 | 50 | 22 (23%) |
| Aggregators | 84 | 42 | 35 (42%) |
| ADOP | 41 | 43 | 25 (58%) |

Major categories of mismatch:
1. **Fields in sheets not in code:** Floor plans, payment milestones, CTAs, map coords, developer logos/badges, project detail card fields
2. **Fields in code not in sheets:** The code assumed bullet-point structures where sheets use paragraphs (e.g., ADOP infrastructure_bullet_1-4 vs paragraphs)
3. **Naming mismatches:** `image_alt` vs `Image Alt Tag`, `nearby_1` vs `Nearby 1 - Name` + `Nearby 1 - Distance`

---

## Phase 2: Deferred (Separate Session)

### Templates still needing standardization
- **ADRE** -- 43 rows missing field names in column B; extra languages need label fixes
- **Commercial** -- No guidelines column; field names mixed with guidelines in column A; 4-column layout needs restructuring
- **OPR** -- Most disorganized; notes scattered everywhere; `<p>` used as field names; requires reference to page screenshots in `template-organization/scraped_pages/opr-project-page-screenshots/`

### Code updates needed (after all sheets standardized)
1. **Rewrite `template_fields.py`** -- Must match actual standardized sheet fields, not assumptions
2. **Update `sheets_manager.py`** -- Column C for EN content (currently writes to B)
3. **Add row numbers** to field definitions (for Phase 2 cell mapping)
4. **Update prompts** to match the real field names

### Design notes for template_fields.py rewrite

**Dynamic/conditional fields (ALL templates):**

Many template fields are not fixed -- they have variable counts or are conditional on the source material. The field mapping rewrite MUST treat these as dynamic/repeatable field groups, not hardcoded fixed entries. Any example values in templates are illustrative only, not defaults.

Known dynamic field patterns across templates:

| Pattern | Templates | Example |
|---------|-----------|---------|
| Payment Plan Types | MPP, Aggregators, ADOP | Type 1 always present; Type 2+ conditional on source PDF. Count is variable (usually 1-2, can be more). |
| FAQ Q&A Pairs | All | Variable number of question/answer pairs per template. |
| Amenity Items | Aggregators, MPP, OPR | Variable number of amenities extracted from source. |
| Floor Plan Entries | Aggregators, MPP | Variable number of floor plan types/sizes. |
| Nearby Landmarks | MPP | Nearby 1-5 with Name + Distance pairs; count depends on project. |
| Property Types | OPR | Variable number of property type tabs/entries. |

Key rules:
- The LLM deduces all dynamic field values from the source PDF during content generation.
- "IF" statements in column A guidelines are conditional instructions for the LLM, not static fields.
- Example values (e.g., 50/50, 70/30 payment plans) have been removed from templates to avoid confusion.
- Field definitions must support a variable number of entries per group (not a hardcoded max).

---

## Scripts Created

| Script | Purpose |
|--------|---------|
| `backend/scripts/audit_template_structure.py` | Audit column structure of any template sheet |
| `backend/scripts/standardize_templates.py` | Create standardized copies (Phase 1) |
| `backend/scripts/verify_standardized.py` | Verify standardized copies match expected format |
| `backend/scripts/build_field_mapping.py` | Compare sheet field names to template_fields.py |

---

## Manual Steps Required

After reviewing the standardized copies in the Shared Drive:
1. Review each standardized sheet for accuracy
2. Copy the standardized content back to the original template sheets (preserving original sheet IDs)
3. Run `audit_template_structure.py` against the originals to confirm
4. Proceed with `template_fields.py` rewrite in Phase 2
