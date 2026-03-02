# Agent Brief: QA-EXTRACT-001

**Agent ID:** QA-EXTRACT-001
**Agent Name:** Text Extractor QA
**Type:** QA
**Phase:** 3 - Content Generation
**Paired Dev Agent:** DEV-EXTRACT-001

---

## Validation Checklist

- [ ] pymupdf4llm correctly integrated
- [ ] Markdown formatting preserved
- [ ] Headers extracted correctly
- [ ] Lists converted properly
- [ ] Tables preserved
- [ ] Large PDFs handled without memory issues
- [ ] Corrupted PDFs handled gracefully
- [ ] Empty pages handled
- [ ] Progress callbacks work
- [ ] Page boundaries marked in output

---

## Test Cases

1. Standard PDF with text and images
2. Large PDF (50MB+) - memory test
3. PDF with complex tables
4. PDF with multiple columns
5. Corrupted/malformed PDF
6. Password-protected PDF
7. PDF with only images (no text)
8. Multi-language PDF

---

## Quality Metrics

- Extraction accuracy: >95%
- Memory usage: <500MB for 50MB PDF
- Processing time: <30s per 10-page PDF

---

**Begin review.**
