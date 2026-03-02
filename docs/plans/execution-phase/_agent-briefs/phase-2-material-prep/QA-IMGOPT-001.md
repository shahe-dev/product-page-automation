# Agent Brief: QA-IMGOPT-001

**Agent ID:** QA-IMGOPT-001
**Agent Name:** Image Optimizer QA
**Type:** QA
**Phase:** 2 - Material Preparation
**Paired Dev Agent:** DEV-IMGOPT-001

---

## Validation Checklist

- [ ] Resize maintains aspect ratio
- [ ] Max dimensions enforced (2450x1400)
- [ ] DPI set to 300
- [ ] WebP output valid and viewable
- [ ] JPG output valid and viewable
- [ ] Dual-tier output: Tier 1 (original quality) and Tier 2 (LLM-optimized 1568px max)
- [ ] ZIP structure correct
- [ ] Manifest.json complete and valid
- [ ] All images categorized correctly
- [ ] Batch processing works
- [ ] Memory usage acceptable

---

## Quality Tests

1. Large image resize quality
2. Small image upscale handling
3. Transparent PNG handling
4. ZIP integrity verification
5. Manifest schema validation

---

**Begin review.**
