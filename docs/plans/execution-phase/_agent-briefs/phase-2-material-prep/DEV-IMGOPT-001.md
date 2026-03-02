# Agent Brief: DEV-IMGOPT-001

**Agent ID:** DEV-IMGOPT-001
**Agent Name:** Image Optimizer Agent
**Type:** Development
**Phase:** 2 - Material Preparation
**Context Budget:** 50,000 tokens

---

## Mission

Implement image optimization (resize, format conversion, compression) and output packaging with organized ZIP structure for cloud upload.

---

## Documentation to Read

### Primary
1. `docs/02-modules/MATERIAL_PREPARATION.md` - Optimization requirements
2. `docs/05-integrations/CLOUD_STORAGE_PATTERNS.md` - Cloud upload patterns

---

## Dependencies

**Upstream:** DEV-WATERMARK-001, DEV-FLOORPLAN-001
**Downstream:** DEV-GCS-001, DEV-DRIVE-001

---

## Outputs

### `backend/app/services/image_optimizer.py`
### `backend/app/services/output_organizer.py`

---

## Acceptance Criteria

1. **Resize:**
   - Max dimensions: 2450x1400px
   - Maintain aspect ratio
   - Set DPI to 300

2. **Format Conversion:**
   - WebP (85% quality) - primary
   - JPG (90% quality) - fallback
   - Both formats generated

3. **Dual-Tier Output:**
   - Tier 1 (Original): Full quality, no size limit, for archival/delivery
   - Tier 2 (LLM-Optimized): 1568px max, for Claude processing and web

4. **Output Structure:**
   ```
   /interiors/      (10 images x 2 formats)
   /exteriors/      (10 images x 2 formats)
   /amenities/      (5 images x 2 formats)
   /logos/          (3 images x 2 formats)
   /floor_plans/    (N floor plans x 2 formats)
   manifest.json
   ```

5. **Manifest.json:**
   - Complete metadata for all images
   - URLs, categories, quality scores

6. **Performance:**
   - Batch parallel processing
   - Memory efficient

---

## QA Pair: QA-IMGOPT-001

---

**Begin execution.**
