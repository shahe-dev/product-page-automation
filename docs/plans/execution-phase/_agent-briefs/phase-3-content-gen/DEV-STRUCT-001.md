# Agent Brief: DEV-STRUCT-001

**Agent ID:** DEV-STRUCT-001
**Agent Name:** Data Structurer Agent
**Type:** Development
**Phase:** 3 - Content Generation
**Context Budget:** 55,000 tokens

---

## Mission

Implement Claude Sonnet 4.5-based extraction of structured property data from markdown text with confidence scoring and field validation.

---

## Documentation to Read

### Primary
1. `docs/02-modules/CONTENT_GENERATION.md` - Structuring requirements
2. `docs/02-modules/PROJECT_DATABASE.md` - Required field schema

### Secondary
1. `docs/05-integrations/ANTHROPIC_API_INTEGRATION.md` - Claude API usage patterns

---

## Dependencies

**Upstream:** DEV-EXTRACT-001
**Downstream:** DEV-CONTENT-001

---

## Outputs

### `backend/app/services/data_structurer.py`

---

## Acceptance Criteria

1. **Field Extraction:**
   - Project name
   - Developer name
   - Location (emirate, community, sub-community)
   - Property type
   - Price range (min, max, currency)
   - Handover date
   - Payment plan details
   - Amenities list
   - Key features

2. **Confidence Scoring:**
   - Per-field confidence (0.0-1.0)
   - Overall extraction confidence
   - Flag fields with <0.7 confidence for review

3. **Validation:**
   - Required fields present
   - Data type validation
   - Range validation (e.g., prices positive)
   - Date format validation

4. **Missing Field Tracking:**
   - List missing required fields
   - List incomplete fields
   - Suggest manual review items

5. **Cost Efficiency:**
   - Target: $0.01-0.03 per PDF
   - Efficient prompt design
   - Token usage tracking

---

## Claude Sonnet 4.5 Structuring Prompt Template

```
Extract structured real estate data from this brochure text:

{markdown_content}

Return JSON with:
{
  "project_name": "",
  "developer": "",
  "emirate": "",
  "community": "",
  "property_type": "",
  "price_min": 0,
  "price_max": 0,
  "handover_date": "",
  "payment_plan": {},
  "amenities": [],
  "confidence_scores": {}
}
```

---

## QA Pair: QA-STRUCT-001

---

**Begin execution.**
