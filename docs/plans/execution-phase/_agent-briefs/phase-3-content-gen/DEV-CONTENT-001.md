# Agent Brief: DEV-CONTENT-001

**Agent ID:** DEV-CONTENT-001
**Agent Name:** Content Generator Agent
**Type:** Development
**Phase:** 3 - Content Generation
**Context Budget:** 65,000 tokens

---

## Mission

Implement AI-powered marketing content generation with brand voice compliance, SEO optimization, and multi-template support.

---

## Documentation to Read

### Primary
1. `docs/02-modules/CONTENT_GENERATION.md` - Content requirements
2. `docs/02-modules/QA_MODULE.md` - QA validation rules
3. `docs/02-modules/PROMPT_LIBRARY.md` - Prompt management

### Secondary
1. `docs/05-integrations/ANTHROPIC_API_INTEGRATION.md` - Claude API integration

### Brand
1. `reference/company/brand-guidelines/brand-context-prompt.md` - Brand voice

---

## Dependencies

**Upstream:** DEV-STRUCT-001
**Downstream:** DEV-SHEETS-001

---

## Outputs

### `backend/app/services/content_generator.py`
### `backend/app/services/content_qa_service.py`
### `backend/app/services/prompt_manager.py`

---

## Acceptance Criteria

1. **Brand Context Integration:**
   - Load brand context from `reference/company/brand-guidelines/`
   - Prepend brand context to all generation prompts
   - Maintain consistent brand voice

2. **Field-by-Field Generation:**
   - Title (max 80 chars)
   - Meta description (max 160 chars)
   - H1 heading (max 60 chars)
   - Short description (50-100 words)
   - Long description (200-300 words)
   - Location description (100-150 words)
   - Amenities description (100-150 words)
   - Payment plan description (50-100 words)

3. **SEO Optimization:**
   - URL slug generation (kebab-case)
   - Keyword integration
   - Meta tag optimization
   - Schema.org compliance

4. **Template Support:**
   - Aggregators template (24+ third-party aggregator domains)
   - OPR template (opr.ae)
   - MPP template (main-portal.com)
   - ADOP template (abudhabioffplan.ae)
   - ADRE template (secondary-market-portal.com)
   - Commercial template (cre.main-portal.com)

5. **QA Validation:**
   - Factual accuracy check against source
   - Brand compliance verification
   - Prohibited terms check
   - Character limit enforcement
   - Consistency scoring

6. **Prompt Management:**
   - Version-controlled prompts
   - A/B testing support
   - Prompt effectiveness tracking

---

## Content Generation Flow

```
1. Load brand context
2. Select template
3. For each field:
   a. Get field-specific prompt
   b. Inject structured data
   c. Generate content
   d. Validate against rules
   e. Score quality
4. Return complete content set with QA scores
```

---

## QA Pair: QA-CONTENT-001

---

**Begin execution.**
