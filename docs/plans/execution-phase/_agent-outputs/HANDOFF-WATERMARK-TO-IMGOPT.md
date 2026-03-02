# Handoff Record: DEV-WATERMARK-001 + DEV-FLOORPLAN-001 -> DEV-IMGOPT-001

**Date:** 2026-01-27
**From:** DEV-WATERMARK-001 (Watermark Agent), DEV-FLOORPLAN-001 (Floor Plan Agent)
**To:** DEV-IMGOPT-001 (Image Optimizer Agent)
**Phase:** 2 - Material Preparation (Wave 3 -> Wave 4)

---

## Deliverables from DEV-WATERMARK-001

### Files Created
- `backend/app/services/watermark_detector.py` - Claude Vision watermark detection
- `backend/app/services/watermark_remover.py` - OpenCV inpainting removal

### Key Interface
```python
# RemovalResult contains cleaned or original bytes
result = await remover.remove(image_bytes, detection_result)
cleaned_bytes = result.cleaned_bytes  # Use this for optimization
```

## Deliverables from DEV-FLOORPLAN-001

### Files Created
- `backend/app/services/floor_plan_extractor.py` - Floor plan OCR extraction

### Key Interface
```python
# FloorPlanData contains structured data + original image bytes
for fp in extraction_result.floor_plans:
    image_bytes = fp.image_bytes
    structured_data = fp  # unit_type, bedrooms, area, etc.
```

## Combined Input for Image Optimizer
```python
# Collect all images for optimization
images_to_optimize = []

# Non-floor-plan images (watermark cleaned)
for image, classification in classified_images:
    if classification.category != ImageCategory.FLOOR_PLAN:
        removal = await remover.remove(image.image_bytes, detection)
        images_to_optimize.append((
            removal.cleaned_bytes,
            classification.category.value,
            classification.alt_text,
        ))

# Floor plan images
for fp in floor_plan_result.floor_plans:
    images_to_optimize.append((
        fp.image_bytes,
        "floor_plan",
        f"Floor plan - {fp.unit_type or 'Unknown'} unit",
    ))

# Optimize all
optimizer = ImageOptimizer()
result = await optimizer.optimize_batch(images_to_optimize)
```

## Validation Status
- QA-WATERMARK-001: PASSED (Score: 88/100)
- QA-FLOORPLAN-001: PASSED (Score: 89/100)

## Notes for Downstream
- cleaned_bytes may be identical to original if no watermark was found or removal was rejected
- Floor plan structured data should be included in ZIP manifest
- Both watermark and floor plan processing are complete; optimizer receives final image bytes
