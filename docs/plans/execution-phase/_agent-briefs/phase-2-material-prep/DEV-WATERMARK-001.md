# Agent Brief: DEV-WATERMARK-001

**Agent ID:** DEV-WATERMARK-001
**Agent Name:** Watermark Agent
**Type:** Development
**Phase:** 2 - Material Preparation
**Context Budget:** 55,000 tokens

---

## Mission

Implement watermark detection using Claude Sonnet 4.5 vision and removal using OpenCV inpainting, with quality validation.

---

## Documentation to Read

### Primary
1. `docs/02-modules/MATERIAL_PREPARATION.md` - Watermark processing requirements
2. `docs/05-integrations/ANTHROPIC_API_INTEGRATION.md` - Claude Vision API usage

---

## Dependencies

**Upstream:** DEV-IMGCLASS-001
**Downstream:** DEV-IMGOPT-001

---

## Outputs

### `backend/app/services/watermark_detector.py`
### `backend/app/services/watermark_remover.py`

---

## Acceptance Criteria

1. **Detection with Claude Sonnet 4.5:**
   - Identify watermark presence (yes/no)
   - Extract bounding box (x, y, width, height)
   - Confidence score

2. **Removal with OpenCV:**
   - Create binary mask from bounding box
   - Apply inpainting (TELEA or NS algorithm)
   - Preserve surrounding image quality

3. **Quality Validation:**
   - Compare before/after quality score
   - Fallback to original if quality drops >15%
   - Store quality metrics

---

## Technical Implementation

```python
import cv2
import numpy as np

def remove_watermark(image: np.ndarray, bbox: dict) -> np.ndarray:
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
    mask[y:y+h, x:x+w] = 255
    result = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    return result
```

---

## QA Pair: QA-WATERMARK-001

---

**Begin execution.**
