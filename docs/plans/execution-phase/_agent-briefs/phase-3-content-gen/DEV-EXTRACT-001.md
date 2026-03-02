# Agent Brief: DEV-EXTRACT-001

**Agent ID:** DEV-EXTRACT-001
**Agent Name:** Text Extractor Agent
**Type:** Development
**Phase:** 3 - Content Generation
**Context Budget:** 50,000 tokens

---

## Mission

Implement PDF text extraction using pymupdf4llm for:
1. **Cost-efficient markdown conversion** - FREE text extraction (no API costs)
2. **Format preservation** - Headers, lists, tables, styling
3. **Floor plan cross-reference support** - Structure output for DEV-FLOORPLAN-001 to use as fallback data source

---

## Documentation to Read

### Primary
1. `docs/02-modules/CONTENT_GENERATION.md` - Text extraction requirements

### Secondary
1. `docs/04-backend/SERVICE_LAYER.md` - Service architecture patterns
2. `docs/05-integrations/ANTHROPIC_API_INTEGRATION.md` - Claude vision fallback for scanned PDFs

---

## Dependencies

**Upstream:** DEV-JOB-001
**Downstream:** DEV-STRUCT-001

---

## Outputs

### `backend/app/services/pdf_extractor.py`

---

## Acceptance Criteria

### pymupdf4llm Integration
1. Use pymupdf4llm for text extraction (90% cost savings vs OCR)
2. Handle PDFs up to 50MB

### Markdown Preservation
3. Preserve headers (H1-H6)
4. Preserve lists (bulleted, numbered)
5. Preserve tables
6. Preserve bold/italic formatting

### Floor Plan Cross-Reference Support
7. **Page boundaries:** Clear page markers (`--- Page N ---`) for context lookup
8. **Unit specifications extraction:** Identify and structure:
   - Unit type labels (1BR, 2BR, Studio, etc.)
   - Area measurements (sqft, sqm)
   - Bedroom/bathroom counts in text
   - Feature lists per unit
9. **Page-indexed output:** Associate extracted specs with page numbers
10. **Context window support:** Enable +/- 2 page lookups for floor plan verification

### Performance
11. Stream processing for large files
12. Memory-efficient extraction
13. Progress callbacks for job tracking

### Error Handling
14. Handle corrupted PDFs gracefully
15. Handle password-protected PDFs (skip or prompt)
16. Handle empty pages
17. Return meaningful error messages

### Output Format
18. Clean markdown output
19. Page boundaries clearly marked
20. Metadata extraction (page count, file size)
21. Structured unit specs (for floor plan fallback)

---

## Implementation Notes

### Page Context Extraction for Floor Plans
```python
def extract_page_context(markdown_text: str, page_num: int, window: int = 2) -> str:
    """
    Extract text from pages surrounding a floor plan.
    Used by DEV-FLOORPLAN-001 for text fallback data.

    Args:
        markdown_text: Full markdown from pymupdf4llm
        page_num: Page where floor plan was found
        window: Number of pages before/after to include

    Returns:
        Concatenated text from surrounding pages
    """
    pages = markdown_text.split("--- Page ")
    start = max(0, page_num - window - 1)
    end = min(len(pages), page_num + window)
    return "\n".join(pages[start:end])
```

### Unit Specification Detection
```python
def extract_unit_specs_from_text(markdown_text: str) -> List[Dict]:
    """
    Parse unit specifications from text for floor plan fallback.

    Looks for patterns like:
    - "2 Bedroom | 1,250 sqft"
    - "Unit Type: Studio"
    - "Area: 850 sq.ft."
    """
    import re

    specs = []
    # Unit type patterns
    unit_pattern = r'(\d)\s*(?:BR|Bed(?:room)?s?|B/R)'
    # Area patterns
    area_pattern = r'(\d{3,5})\s*(?:sq\.?\s*ft|sqft|sqm)'
    # ...
    return specs
```

---

## QA Pair: QA-EXTRACT-001

---

**Begin execution.**
