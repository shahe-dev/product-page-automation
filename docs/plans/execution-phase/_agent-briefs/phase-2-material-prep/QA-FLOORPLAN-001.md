# Agent Brief: QA-FLOORPLAN-001

**Agent ID:** QA-FLOORPLAN-001
**Agent Name:** Floor Plan QA
**Type:** QA
**Phase:** 2 - Material Preparation
**Paired Dev Agent:** DEV-FLOORPLAN-001

---

## Validation Checklist

- [ ] Floor plan detection accurate
- [ ] Unit type extraction correct
- [ ] Bedroom/bathroom counts accurate
- [ ] Area calculations reasonable
- [ ] Features extracted correctly
- [ ] Deduplication identifies duplicates
- [ ] Highest quality selected
- [ ] Perceptual hash consistent
- [ ] JSONB storage format correct
- [ ] `page_text_map` received from job manager pipeline
- [ ] Text fallback used only when image OCR lacks data
- [ ] Text fallback limited to same page or adjacent (+/- 1 page)

---

## Test Cases

1. Clear floor plan with labeled rooms
2. Floor plan without labels
3. Multiple floor plans (different units)
4. Duplicate floor plans (same unit, different quality)
5. Near-duplicate floor plans (95% similar)
6. Non-floor-plan architectural drawing
7. Floor plan with text fallback (page_text_map provides unit type when image OCR returns null)

---

**Begin review.**
