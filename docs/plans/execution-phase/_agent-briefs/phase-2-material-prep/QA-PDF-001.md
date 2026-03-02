# Agent Brief: QA-PDF-001

**Agent ID:** QA-PDF-001
**Agent Name:** PDF Processor QA
**Type:** QA
**Phase:** 2 - Material Preparation
**Paired Dev Agent:** DEV-PDF-001

---

## Validation Checklist

### Image Extraction
- [ ] All images extracted from test PDFs
- [ ] Resolution preserved (compare original vs extracted)
- [ ] Memory usage acceptable (<500MB for 50MB PDF)
- [ ] Corrupted PDF handling (graceful error)
- [ ] Multi-page extraction works
- [ ] Metadata accurate (page, dimensions, format)
- [ ] Performance acceptable (<5s for 20-page PDF)
- [ ] No image quality loss

### Text Extraction (pymupdf4llm)
- [ ] `page_text_map` populated for all pages in ExtractionResult
- [ ] Page numbers in `page_text_map` are 1-indexed (matching image metadata)
- [ ] Text extraction failure returns empty dict (does not break image pipeline)
- [ ] pymupdf4llm called with `page_chunks=True` and `ignore_images=True`
- [ ] Markdown formatting preserved (headers, tables, reading order)

---

## Test Cases

### Image Tests
1. Single-page PDF with 5 images
2. Multi-page PDF (50+ pages)
3. Large PDF (>30MB)
4. Corrupted PDF (partial)
5. PDF with no images
6. PDF with embedded vector graphics

### Text Extraction Tests
7. Multi-page PDF produces correct page_text_map entries
8. pymupdf4llm crash returns empty dict (graceful fallback)
9. Page numbering is 1-indexed in page_text_map
10. pymupdf4llm receives correct arguments (page_chunks, ignore_images)

---

**Begin review.**
