# Agent Brief: DEV-FLOORPLAN-001

**Agent ID:** DEV-FLOORPLAN-001
**Agent Name:** Floor Plan Agent
**Type:** Development
**Phase:** 2 - Material Preparation
**Context Budget:** 60,000 tokens

---

## Mission

Implement floor plan processing with:
1. **Vector handling** - Accept both embedded rasters AND page renders (vector CAD content)
2. **Data extraction** - Claude Sonnet 4.5 vision OCR with PNG format (lossless for text)
3. **Text cross-referencing** - Fall back to surrounding PDF text when image lacks data
4. **Deduplication** - Perceptual hashing across all floor plan sources

---

## Documentation to Read

### Primary
1. `docs/02-modules/MATERIAL_PREPARATION.md` - Floor plan requirements
2. `docs/05-integrations/ANTHROPIC_API_INTEGRATION.md` - Claude Vision API

---

## Dependencies

**Upstream:** DEV-IMGCLASS-001
**Downstream:** DEV-IMGOPT-001

---

## Outputs

### `backend/app/services/floor_plan_extractor.py`
### `backend/app/services/deduplication_service.py`

---

## Acceptance Criteria

### Vector Floor Plan Handling
1. **Accept triple extraction input:** Embedded images, page renders, and per-page text from DEV-PDF-001
2. **Prefer page renders for floor plans:** CAD exports are often vector, not embedded raster
3. **LLM optimization:** Use `task="floor_plan_ocr"` (1568px max, PNG lossless)

### Data Extraction - Image as Source of Truth
4. **PRIMARY source:** Floor plan image via Claude Sonnet 4.5 vision OCR
5. **FALLBACK only:** Surrounding PDF text (from pymupdf4llm) when image lacks data
6. **Verification required:** Text fallback must be on same page or adjacent (+/- 1 page)
7. **Never associate:** Unverified text with any floor plan

### Structured Data Fields
8. **Unit type:** (1BR, 2BR, Studio, etc.)
9. **Bedroom count:** Integer
10. **Bathroom count:** Support .5 for half-bath
11. **Total area:** sqft (convert sqm if needed)
12. **Balcony area:** sqft
13. **Built-up area:** sqft
14. **Features:** (maid room, storage, walk-in closet)
15. **Room dimensions:** From image only (never text)
16. **Per-field source tracking:** "floor_plan_image" or "text_fallback"
17. **Confidence scores:** Per field

### Deduplication
18. **Perceptual hash (pHash):** Calculate for all floor plans
19. **95% similarity threshold:** Group duplicates
20. **Cross-source deduplication:** Compare embedded vs page renders
21. **Select highest quality:** Keep best version per unit type
22. **Mark duplicates:** `is_duplicate=true`

---

## Implementation Notes

### Data Source Priority
```python
# CRITICAL: Image is source of truth
def merge_floor_plan_data(vision_result, text_result, page_num):
    merged = FloorPlanData()

    # Unit type: image first, text fallback
    if vision_result.get("unit_type"):
        merged.unit_type = vision_result["unit_type"]
        merged.unit_type_source = "floor_plan_image"
    elif verified_text := find_verified_text(text_result, page_num, "unit_type"):
        merged.unit_type = verified_text["value"]
        merged.unit_type_source = "text_fallback"

    # Room dimensions: ONLY from image (never in text)
    if vision_result.get("room_dimensions"):
        merged.room_dimensions = vision_result["room_dimensions"]
        merged.dimensions_source = "floor_plan_image"

    return merged
```

### Vector Floor Plan Detection
```python
def is_likely_vector_floor_plan(page_render: dict, embedded: list) -> bool:
    # If no embedded images but page render classified as floor_plan
    if not embedded and page_render["classification"] == "floor_plan":
        return True

    # If embedded is low-res but render is detailed
    if embedded and embedded["width"] < 800:
        return True

    return False
```

## Claude Sonnet 4.5 Floor Plan Prompt

```
Extract all visible data from this floor plan image.
Return null for fields NOT visible in the image.

{
  "unit_type": "2BR or null",
  "bedrooms": 2,
  "bathrooms": 2.5,
  "total_sqft": 1250,
  "balcony_sqft": 150,
  "room_dimensions": {"living": "4.2m x 3.8m", "bedroom1": "3.5m x 3.2m"},
  "features": ["maid_room", "walk_in_closet"],
  "confidence": 0.92
}

IMPORTANT: Only extract data that is VISIBLE in the image.
Do not guess or infer values not shown.
```

### LLM Optimization
- Use `task="floor_plan_ocr"` (1568px max, PNG format)
- PNG preserves text clarity for dimension extraction
- Expected token usage: ~900 per floor plan

---

## QA Pair: QA-FLOORPLAN-001

---

**Begin execution.**
