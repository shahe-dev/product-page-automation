# Phase 1: Google Sheet Alignment - Complete Fix Plan

**Created:** 2026-02-03
**Completed:** 2026-02-03
**Status:** COMPLETE
**Prerequisite for:** Phase 2 Engineering (field_row_mappings.json generation)

## Problem Statement

The `field_row_mappings.json` was generated but has gaps - GENERATED and HYBRID fields from the field registries are missing row mappings because they don't exist in the Google Sheets. We cannot proceed to Phase 2 Engineering until 100% of GENERATED/HYBRID fields have sheet rows.

## Source of Truth

**Field Registries** in `prompt-organizaton/XX-<template>/<template>-field-registry.md` are the single source of truth.

## Gap Summary by Template

Based on analysis of `backend/scripts/field_row_mappings.json` vs field registries:

### OPR - READY (0 blocking gaps)
- All GENERATED/HYBRID fields mapped
- Uses combined bullet fields pattern (handled at runtime)

### ADOP - 1 blocking gap
Missing GENERATED field:
- `area_infrastructure_h2` (Area Infrastructure section header)

### Commercial - 2 blocking gaps
Missing GENERATED fields:
- `h1` (Hero H1)
- `payment_plan_title` (Payment Plan section)

### MPP - 5 blocking gaps
Missing GENERATED/HYBRID fields:
- `amenities_paragraph` (GENERATED, Amenities section)
- `developer_name_title` (GENERATED, Developer section)
- `faq_h2` (GENERATED, FAQ section header)
- `location_title` (GENERATED, Location section)
- `payment_plan_description` (HYBRID, Payment Plan section)

### ADRE - 16 blocking gaps
Missing GENERATED fields:
- `h1` (Hero section)
- `hero_marketing_h2` (Hero section)
- `area_card_style` (Location section)
- `area_card_focal_point` (Location section)
- `area_card_accessibility` (Location section)
- `area_card_shopping_1` through `area_card_shopping_4` (Location section)
- `area_card_entertainment_5`, `area_card_entertainment_6` (Location section)
- `economic_stats_roi` (Economic Appeal section)
- `payment_plan_h2` (Payment Plan section)
- `faq_12_question`, `faq_12_answer` (FAQ section)

### Aggregators - 36 blocking gaps
Missing GENERATED/HYBRID fields:
- `hero_h1` (Hero section)
- `hero_investment_stat_1`, `hero_investment_stat_2`, `hero_investment_stat_3` (Hero, HYBRID)
- `economic_appeal_h2`, `economic_appeal_paragraph` (Economic Appeal section)
- `key_feature_1_title`, `key_feature_1_description` (Key Features)
- `key_feature_2_title`, `key_feature_2_description` (Key Features)
- `key_feature_3_title`, `key_feature_3_description` (Key Features)
- `amenity_6_title`, `amenity_6_description` (Amenities, HYBRID)
- `social_facilities_intro`, `social_facility_1/2/3` (Location)
- `education_medicine_intro`, `education_facility_1/2/3` (Location)
- `culture_intro`, `culture_facility_1/2/3` (Location)
- `faq_6_question` through `faq_10_answer` (FAQ section)

## Resolution Strategy

### Option A: Use sync_sheet_to_registry.py (RECOMMENDED)

The `backend/scripts/sync_sheet_to_registry.py` script already exists and can:
1. Read field registries
2. Compare against Google Sheets
3. Insert missing fields with proper labels and guidelines

**Command:**
```bash
cd backend
python scripts/sync_sheet_to_registry.py --template <template_name>
# Or for all templates:
python scripts/sync_sheet_to_registry.py
```

**Note:** The script has `FIELD_LABEL_MAPPINGS` in `sync_sheet_to_registry.py` that map registry field names to sheet labels. These mappings are already comprehensive for all 6 templates.

### Option B: Manual Sheet Updates

For each missing field:
1. Open the Google Sheet for the template
2. Add a row with:
   - Column B (Fields): The field label from `FIELD_LABEL_MAPPINGS` or converted from snake_case
   - Column C (Guidelines): Character limit and notes from registry

## Execution Steps

### Step 1: Run sync script in dry-run mode
```bash
cd backend
python scripts/sync_sheet_to_registry.py --dry-run
```
Review the output to see what changes will be made.

### Step 2: Run sync script to apply changes
```bash
python scripts/sync_sheet_to_registry.py
```

### Step 3: Regenerate field_row_mappings.json
```bash
python scripts/generate_field_row_mapping.py
```

### Step 4: Verify 100% coverage
```bash
python -c "
import json
from pathlib import Path

# Load mappings
with open('scripts/field_row_mappings.json') as f:
    mappings = json.load(f)

# Load registries and check coverage
templates = ['opr', 'adop', 'adre', 'commercial', 'aggregators', 'mpp']
registry_paths = {
    'opr': '../prompt-organizaton/01-opr/opr-field-registry.md',
    'adop': '../prompt-organizaton/02-adop/adop-field-registry.md',
    'adre': '../prompt-organizaton/03-adre/adre-field-registry.md',
    'commercial': '../prompt-organizaton/04-commercial/commercial-field-registry.md',
    'aggregators': '../prompt-organizaton/05-aggregators/aggregators-field-registry.md',
    'mpp': '../prompt-organizaton/06-mpp/mpp-field-registry.md',
}

import re
for template in templates:
    # Parse registry for GENERATED/HYBRID fields
    content = Path(registry_paths[template]).read_text()
    table_match = re.search(r'\| field_name.*?\n\|[-|]+\|\n(.*?)(?=\n\n|\n##|\Z)', content, re.DOTALL)
    if not table_match:
        print(f'{template}: Could not parse registry')
        continue

    required_fields = []
    for line in table_match.group(1).strip().split('\n'):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4:
            field_name = parts[1]
            field_type = parts[3]
            if field_type in ('GENERATED', 'HYBRID'):
                required_fields.append(field_name)

    # Check coverage
    mapped = set(mappings.get(template, {}).keys())
    missing = [f for f in required_fields if f not in mapped]

    if missing:
        print(f'{template}: MISSING {len(missing)} fields')
        for f in missing[:5]:
            print(f'  - {f}')
        if len(missing) > 5:
            print(f'  ... and {len(missing) - 5} more')
    else:
        print(f'{template}: 100% coverage ({len(required_fields)} fields)')
"
```

### Step 5: If gaps remain, check FIELD_LABEL_MAPPINGS

If fields are still missing after sync, the issue is likely:
1. The sheet label doesn't match what `title_to_snake()` expects
2. Add explicit mapping to `FIELD_LABEL_MAPPINGS` in `sync_sheet_to_registry.py`

## Key Files

| File | Purpose |
|------|---------|
| `prompt-organizaton/XX-*/XX-field-registry.md` | Source of truth for fields |
| `backend/scripts/sync_sheet_to_registry.py` | Syncs sheets to match registries |
| `backend/scripts/generate_field_row_mapping.py` | Generates field_row_mappings.json |
| `backend/scripts/field_row_mappings.json` | Output: field-to-row mappings |

## Success Criteria

Before proceeding to Phase 2 Engineering:
- [x] All 6 templates have 0 missing GENERATED/HYBRID fields
- [x] `field_row_mappings.json` contains all required fields
- [x] Verification script shows "100% coverage" for all templates

## Completion Summary (2026-02-03)

### GENERATED/HYBRID Coverage (Phase 1 Goal)

| Template | GENERATED/HYBRID | Coverage |
|----------|------------------|----------|
| OPR | 93/93 | 100% |
| ADOP | 54/54 | 100% |
| ADRE | 68/68 | 100% |
| COMMERCIAL | 49/49 | 100% |
| AGGREGATORS | 73/73 | 100% |
| MPP | 30/30 | 100% |
| **Total** | **367/367** | **100%** |

### COMPLETE Field Coverage (ALL types for content managers)

| Template | Total Fields | Coverage |
|----------|--------------|----------|
| OPR | 113/113 | 100% |
| ADOP | 60/60 | 100% |
| ADRE | 107/107 | 100% |
| COMMERCIAL | 64/64 | 100% |
| AGGREGATORS | 117/117 | 100% |
| MPP | 88/88 | 100% |
| **Total** | **549/549** | **100%** |

Key changes:
1. 94 new field rows inserted into Google Sheets (89 initial + 5 EXTRACTED)
2. 140 guideline rows updated with char limits and field type metadata
3. `generate_field_row_mapping.py` updated to correctly handle "H1", "H2", "FAQ H2" labels
4. FIELD_LABEL_MAPPINGS updated for ADOP and ADRE EXTRACTED fields

## Next Steps After Completion

Once 100% alignment is achieved:
1. Proceed to Phase 2 Engineering Task 1: Rewrite `template_fields.py`
2. Follow `docs/plans/2026-01-29-prompt-system-phase2.md`
