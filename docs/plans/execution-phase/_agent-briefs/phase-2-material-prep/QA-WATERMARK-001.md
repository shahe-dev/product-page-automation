# Agent Brief: QA-WATERMARK-001

**Agent ID:** QA-WATERMARK-001
**Agent Name:** Watermark QA
**Type:** QA
**Phase:** 2 - Material Preparation
**Paired Dev Agent:** DEV-WATERMARK-001

---

## Validation Checklist

- [ ] Detection identifies watermarks correctly
- [ ] Bounding box coordinates accurate
- [ ] Removal produces clean result
- [ ] Quality validation prevents bad outputs
- [ ] Original preserved when quality drops
- [ ] Works with different watermark types (text, logo)
- [ ] Performance acceptable (<2s per image)

---

## Test Cases

1. Image with text watermark
2. Image with logo watermark
3. Image with no watermark
4. Image with watermark in corner
5. Image with watermark in center
6. Image where removal would degrade quality

---

**Begin review.**
