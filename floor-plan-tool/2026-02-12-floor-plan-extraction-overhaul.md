# Floor Plan Extraction Overhaul

**Date:** 2026-02-12
**Status:** DRAFT -- under active refinement
**Branch:** TBD (will branch from feat/phase4-pipeline-optimization)

---

## Problem Statement

Floor plan extraction is the least reliable stage of the PDP pipeline. Each run produces different numbers, categorizations, and structural outputs. Fixes are applied incrementally but accuracy never reaches an acceptable threshold.

**Root cause:** The pipeline treats all floor plans identically -- same extraction logic, same prompts, same reconciliation -- despite massive format variability across developers and brochure styles.

**Downstream impact:** Content generation receives unreliable room dimensions, bedroom/bathroom counts, and area figures. Wrong data is worse than missing data because content generation will confidently write "spacious master bedroom spanning 45.0 sq.m" when the real value is 12.3.

---

## Observed Format Variability

Analysis of real brochure floor plans reveals at least 6 distinct format categories:

### Format Taxonomy

| Type ID | Name | Characteristics | Extraction Strategy |
|---------|------|----------------|-------------------|
| `SD` | Schematic-Dimensioned | Architectural line drawing, room labels with LxW dimensions, clean text | High-confidence numeric extraction from text layer + Vision |
| `RD` | Rendered-Dimensioned | 3D/rendered floor plan with dimension overlays burned into image | Medium-confidence, prefer text layer, Vision as fallback |
| `RL` | Rendered-Legend | 3D render with numbered legend sidebar, no dimensions in plan | Room names + count only, no dimension extraction |
| `MU` | Multi-Unit | Multiple unit types on a single page, with or without dimensions | Segment into individual units first, then classify each |
| `MF` | Multi-Floor | Villa/townhouse with ground/first/roof floor plans | Process each floor separately, aggregate to unit total |
| `TS` | Table-Summary Only | Area table with unit breakdown but no individual floor plan drawing | Table extraction only, no visual processing |

### Specific Variability Dimensions

**Dimension units (no standard):**
- Meters with 2 decimal places: 3.90 x 3.15
- Millimeters as integers: 3050 X 4500
- Mixed: some rooms in m, area tables in sq.ft
- No dimensions at all (legend-only plans)

**Dimension separators:**
- "X" (uppercase, no spaces): 3.90X3.15
- "x" (lowercase, no spaces): 3.90x3.15
- " X " (uppercase, with spaces): 3050 X 4500
- " x " (lowercase, with spaces): 3.05 x 4.50

**Area presentation:**
- Structured table (rows: Suite, Balcony, Total; columns: Min/Max, Sq.m/Sq.ft)
- Inline text blocks (Area: 71-72 sqm / 769-776 sqft)
- Sq.ft only (Suite = 593.63 SQ.FT.)
- Sq.m only
- Both units in same field
- Floor-by-floor breakdown (villas)
- No area data on page

**Room labeling:**
- Text labels with dimensions inside room boundaries
- Numbered circles with legend sidebar
- Text labels without dimensions
- Abbreviated names (M.BEDROOM, P.ROOM, W.I.C, PWD ROOM)

**Page composition:**
- Single unit, single page
- Two units side-by-side (Type A1 / Type A2)
- Three floors of same villa on one page
- Floor plan + key plan (building location diagram) on same page
- Floor plan + tower level diagrams

---

## Current Pipeline Weaknesses

### 1. No pre-classification
All floor plans enter the same extraction path regardless of type. A rendered 3D plan with no dimensions gets the same "extract room dimensions" prompt as a clean schematic.

### 2. Vision API used for numbers on rendered images
OCR on stylized 3D renders is inherently noisy. Digit transposition (51.57 vs 15.57), decimal misplacement, and font misreading are common. The text layer often has these same numbers losslessly but isn't prioritized.

### 3. Cross-validation assumes sources should agree
The current cross_validator tries to reconcile text layer, regex, table, and Vision sources. But room dimensions intentionally don't sum to stated totals (walls, corridors, circulation space are excluded). The validator treats this mismatch as a conflict to resolve rather than an expected structural property.

### 4. No unit detection
Millimeter dimensions (3050 X 4500) and meter dimensions (3.05 x 4.50) represent the same room but produce wildly different calculations if the unit isn't detected.

### 5. Non-deterministic Vision outputs
Vision API calls likely use non-zero temperature, producing different extractions on repeated runs of the same input.

### 6. Silent correction over honest nulls
When data is unreliable, the pipeline guesses rather than returning null. Downstream consumers (content generation) would handle "N/A" gracefully but can't detect when a number is fabricated.

---

## Proposed Architecture

### Overview

```
PDF Page
  |
  v
[Stage 1] Page Classification --> type: SD|RD|RL|MU|MF|TS
  |
  v
[Stage 2] Text Layer Extraction (PyMuPDF + pdfplumber)
  |         - Area summary tables
  |         - Dimension text objects
  |         - Title/header text
  |
  v
[Stage 3] Type-Specific Visual Extraction (Vision API)
  |         - Prompt selected by Stage 1 classification
  |         - Temperature = 0
  |         - Structured JSON output
  |
  v
[Stage 4] Unit Detection & Normalization
  |         - mm/m/ft detection
  |         - Normalize all to both sq.m and sq.ft
  |
  v
[Stage 5] Validation Gates
  |         - Pass/fail checks (not silent correction)
  |         - Failed fields -> null with reason, not guessed values
  |
  v
[Stage 6] Structured Output
            - Per unit type, per floor
            - Every field tagged with source + confidence
```

### Stage 1: Page Classification

Single Vision API call with classification-only prompt. No number extraction.

**Input:** Floor plan page image
**Output:**
```json
{
  "page_type": "SD|RD|RL|MU|MF|TS",
  "unit_count": 1,
  "unit_types": ["Type A"],
  "bedroom_count": 1,
  "has_area_table": true,
  "has_room_dimensions": true,
  "has_legend": false,
  "dimension_unit_hint": "meters|millimeters|unknown",
  "floor_count": 1
}
```

This classification determines which Stage 3 prompt and which validation rules apply.

### Stage 2: Text Layer Extraction

**Priority source for all numeric data.** Runs before Vision API.

1. **pdfplumber table detection** -- area summary tables (Suite, Balcony, Total rows)
2. **PyMuPDF text block extraction** -- dimension labels that exist as text objects (not burned into image)
3. **Regex patterns** -- applied to extracted text for area values, dimension pairs, bedroom counts

The text layer is lossless. If a number exists here, it's the ground truth. Vision should only fill gaps.

### Stage 3: Type-Specific Visual Extraction

Different prompts per classification type:

**SD (Schematic-Dimensioned):**
- Extract all room names and their LxW dimensions
- High confidence expected -- clean architectural text
- Cross-reference with text layer values

**RD (Rendered-Dimensioned):**
- Extract room names and dimensions, but flag as medium confidence
- Text layer dimensions (from Stage 2) take precedence where available
- Vision fills gaps only

**RL (Rendered-Legend):**
- Extract room name list from legend
- Count bedrooms, bathrooms visually
- Do NOT attempt dimension extraction -- there are none
- Features only (balcony, maid room, walk-in closet presence)

**MU (Multi-Unit):**
- First call: segment page into unit bounding regions
- Then: process each region as its own unit (re-classify as SD/RD/RL)

**MF (Multi-Floor):**
- Process each floor separately
- Tag all extractions with floor identifier (ground, first, roof, etc.)
- Aggregate areas by floor, validate against floor-level totals if present

**TS (Table-Summary Only):**
- Skip Vision entirely
- All data from Stage 2 text layer

**All Vision calls:** temperature = 0, structured JSON output mode.

### Stage 4: Unit Detection & Normalization

Deterministic rules, not heuristics:

```
IF any room dimension value > 100:
    unit = millimeters
    convert: value / 1000 = meters
ELIF any room dimension value between 0.5 and 20:
    unit = meters
ELSE:
    unit = unknown, flag for review

Area unit detection:
    "sq.ft" | "sqft" | "SQ.FT." | "Sq.ft" -> square feet
    "sq.m" | "sqm" | "SQ.M." | "Sq.m" -> square meters
    Both present -> store both, verify conversion
```

All outputs normalized to both sq.m and sq.ft.

Conversion verification: `sq_m * 10.7639 = sq_ft` within 1% tolerance.

### Stage 5: Validation Gates

Hard pass/fail checks. Failures null the field, not correct it.

| Check | Rule | On Failure |
|-------|------|-----------|
| Conversion consistency | sq.m * 10.7639 == sq.ft (+-1%) | Null the less-trusted unit |
| Room sum < suite total | Sum of room areas must be less than stated suite area | Warning only (this is expected) |
| Bedroom count match | Title bedroom count == count of bedroom-labeled rooms | Flag mismatch, prefer title |
| Dimension plausibility | No single room dimension > 15m (apartments) or > 25m (villas) | Null the dimension |
| Area plausibility | No single room > 100 sq.m (apartments) or > 200 sq.m (villas) | Null the area |
| Balcony area check | Balcony area < 30% of suite area | Null balcony area |
| Min <= Max | For ranged values, min must be <= max | Swap if inverted, flag |

### Stage 6: Structured Output

Per unit type:

```json
{
  "unit_type": "Type A",
  "classification": "SD",
  "bedrooms": 1,
  "bathrooms": 1,
  "area": {
    "suite": {"sqm": {"min": 51.57, "max": 51.87}, "sqft": {"min": 555.09, "max": 558.32}},
    "balcony": {"sqm": 5.34, "sqft": 57.48},
    "total": {"sqm": {"min": 56.91, "max": 57.21}, "sqft": {"min": 612.57, "max": 615.80}}
  },
  "rooms": [
    {"name": "Master Bedroom", "dimensions_m": [3.90, 3.15], "area_sqm": 12.29, "source": "text_layer", "confidence": 0.95},
    {"name": "Living Area", "dimensions_m": [3.80, 3.25], "area_sqm": 12.35, "source": "vision", "confidence": 0.75},
    {"name": "Kitchen", "dimensions_m": [3.55, 3.15], "area_sqm": 11.18, "source": "text_layer", "confidence": 0.95}
  ],
  "features": ["balcony", "laundry", "dresser"],
  "validation": {
    "conversion_check": "pass",
    "bedroom_count_match": "pass",
    "plausibility_check": "pass",
    "room_sum_vs_total": {"room_sum_sqm": 46.00, "stated_suite_sqm": 51.57, "gap_pct": 10.8}
  },
  "sources": {
    "area_table": "pdfplumber",
    "room_dimensions": "text_layer + vision_backfill",
    "bedroom_count": "title_text",
    "features": "vision_classification"
  }
}
```

---

## Test Corpus Strategy

### Goal
Build a corpus of 50+ floor plan PDFs spanning all format types, developers, and edge cases. Use this corpus to:
1. Validate classification accuracy (Stage 1)
2. Measure extraction accuracy per format type
3. Establish baseline metrics before and after changes
4. Regression-test every pipeline change

### Corpus Structure

```
backend/tests/quality/ground_truth/floor_plans/
    index.json                          # Manifest of all samples
    SD/                                 # Schematic-Dimensioned
        SD-001-eden-1br-type-d.pdf
        SD-001-eden-1br-type-d.json     # Ground truth
        SD-002-...
    RD/                                 # Rendered-Dimensioned
        RD-001-unit-type-a.pdf
        RD-001-unit-type-a.json
        ...
    RL/                                 # Rendered-Legend
        RL-001-2br-legend.pdf
        RL-001-2br-legend.json
        ...
    MU/                                 # Multi-Unit
        ...
    MF/                                 # Multi-Floor
        ...
    TS/                                 # Table-Summary Only
        ...
```

### Ground Truth JSON Schema

Each PDF gets a hand-verified ground truth file:

```json
{
  "file": "SD-001-eden-1br-type-d.pdf",
  "page": 1,
  "classification": "SD",
  "developer": "Sobha",
  "project": "The Eden",
  "dimension_unit": "millimeters",
  "separator": " X ",
  "units": [
    {
      "unit_type": "Type D",
      "bedrooms": 1,
      "bathrooms": 1,
      "area": {
        "suite_sqft": 593.63,
        "balcony_sqft": 101.40,
        "total_sqft": 695.03
      },
      "rooms": [
        {"name": "Bedroom", "dim1": 3.05, "dim2": 4.50, "area_sqm": 13.73},
        {"name": "Living", "dim1": 3.15, "dim2": 3.55, "area_sqm": 11.18},
        {"name": "Kitchen / Dining", "dim1": 3.05, "dim2": 2.95, "area_sqm": 9.00},
        {"name": "Bathroom", "dim1": 1.60, "dim2": 2.60, "area_sqm": 4.16},
        {"name": "Utility", "dim1": 0.85, "dim2": 1.55, "area_sqm": 1.32}
      ],
      "features": ["balcony"]
    }
  ]
}
```

### Target Distribution (50+ samples)

| Type | Target Count | Notes |
|------|-------------|-------|
| SD | 15 | Most common in Dubai brochures |
| RD | 15 | Second most common |
| RL | 5 | Less common but tricky |
| MU | 5 | Side-by-side units |
| MF | 5 | Villas/townhouses |
| TS | 5 | Table-only pages |

### Accuracy Metrics

Per format type and overall:

```
Classification accuracy:  correct_type / total_samples
Bedroom count accuracy:   correct_count / total_samples
Bathroom count accuracy:  correct_count / total_samples
Area accuracy (suite):    within 2% of ground truth / total_with_area
Area accuracy (total):    within 2% of ground truth / total_with_area
Room dimension accuracy:  within 5% of ground truth / total_with_dimensions
Feature detection F1:     precision * recall for feature list
Null rate:                fields returned as null / total_fields
False data rate:          wrong non-null values / total_non_null_values
```

**Key metric: false data rate must be < 2%.** It's better to return null than wrong data.

### QA Test Runner

```
pytest backend/tests/quality/test_floor_plan_accuracy.py -v

Runs each PDF through the extraction pipeline, compares output against
ground truth, reports per-type and aggregate accuracy metrics.
```

---

## Implementation Phases

### Phase A: Test Corpus & Baseline (no code changes)
1. Collect 50+ floor plan PDFs from brochure archive
2. Hand-annotate ground truth JSON for each
3. Build QA test runner that measures current pipeline accuracy
4. Establish baseline metrics per format type
5. Identify which format types have worst accuracy

### Phase B: Page Classification (Stage 1)
1. Implement classification prompt and parser
2. Validate classification accuracy against corpus (target: >95%)
3. Route to type-specific extraction paths

### Phase C: Text Layer Priority (Stage 2)
1. Enhance pdfplumber table extraction for area summaries
2. Extract dimension text objects from PyMuPDF (not just page text)
3. Implement text-layer-first priority for all numeric fields

### Phase D: Type-Specific Prompts (Stage 3)
1. Write and test prompts for each format type
2. Set temperature = 0 for all extraction Vision calls
3. Enforce structured JSON output
4. Measure accuracy improvement per type

### Phase E: Validation & Normalization (Stages 4-5)
1. Implement unit detection (mm vs m)
2. Implement validation gates
3. Replace silent correction with null + reason
4. Measure false data rate reduction

### Phase F: Integration & Regression
1. Integrate into main pipeline (job_manager.py)
2. Update structured output schema
3. Update content generation to handle new floor plan data shape
4. Full regression against corpus
5. Compare final metrics against Phase A baseline

---

## Open Questions

- [ ] What is the minimum acceptable accuracy for room dimensions before they're included in content generation?
- [ ] Should we extract room dimensions at all for rendered-legend (RL) plans, or just bedroom/bathroom count + features?
- [ ] How should multi-unit pages (MU) be handled when unit types share a single area table?
- [ ] Is there value in extracting balcony dimensions separately when "balcony sizes vary" disclaimers are common?
- [ ] Should the QA test runner be part of CI, or a separate manual validation step?
- [ ] For villas (MF), should we report per-floor area breakdowns or just the total?
- [ ] What confidence threshold should trigger null instead of returning a value?

---

## References

- Previous hybrid extraction plan: `docs/plans/2026-02-10-hybrid-extraction-pipeline.md`
- Current floor plan extractor: `backend/app/services/floor_plan_extractor.py`
- Current cross validator: `backend/app/services/cross_validator.py`
- Current table extractor: `backend/app/services/table_extractor.py`
- QA ground truth (existing): `backend/tests/quality/ground_truth/`
