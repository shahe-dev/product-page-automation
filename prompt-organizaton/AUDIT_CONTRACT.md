# Prompt Audit Contract

> **Purpose:** This document defines the exact output format that every prompt audit session must produce. It bridges the audit (domain expert work) and Phase 2 implementation (engineering work in `template_fields.py`, `prompt_manager.py`, `sheets_manager.py`).
>
> **Rule:** Every audit session MUST reference this file. Every completed audit MUST produce artifacts in this exact format.

---

## Context for Audit Sessions

You are auditing the prompt system for PDP Automation v.3 -- a property documentation platform that generates content for 6 website template types using Claude AI.

### How the pipeline works

1. User uploads a developer PDF brochure
2. Pipeline extracts data from the PDF
3. For each field in a template, `ContentGenerator` calls `PromptManager.get_prompt()` to get the prompt for that field
4. The prompt + extracted PDF data are sent to Claude API
5. Claude generates content for that field
6. Generated content is written to a Google Sheet at a specific cell (row + column)

### What the audit produces

Each audit session reviews a template type against live website screenshots and produces:
- A **section specifications file** (prose, for domain understanding)
- A **system prompt file** (the actual prompt sent to Claude API)
- A **field registry file** (structured data that maps directly to code)

The **field registry file** is the critical bridge to Phase 2. Without it, engineers must manually parse prose specs into code.

---

## Required Artifacts Per Template

Each completed audit in `prompt-organizaton/XX-<template>/` MUST contain:

### 1. Screenshots (reference material)
- `*.png` files showing live project pages from the actual website

### 2. Section Specifications (`<template>-template-sections-specifications.md`)
- Free-form markdown describing each section of the page
- Documents which sections are static vs generated
- Character limits, tone guidelines, content rules
- This is the domain expert's detailed spec

### 3. System Prompt (`prompt <template>.md`)
- The actual system message sent to Claude API for this template type
- Includes field classification (EXTRACTED/GENERATED/HYBRID)
- Includes input data format, style guidelines, formatting rules
- This maps to what `PromptManager._build_system_message()` returns

### 4. Field Registry (`<template>-field-registry.md`) -- CRITICAL FOR PHASE 2
- Structured table that maps directly to `template_fields.py`
- Must use the exact format below

---

## Field Registry Format

Each template's field registry MUST be a markdown file with this exact structure:

```markdown
# <Template Name> Field Registry

Template type: `<template_type>`
Target site: `<website URL>`
Total fields: <N>
Generated fields: <N>
Extracted fields: <N>

## Field Table

| field_name | section | type | char_limit | required | notes |
|------------|---------|------|------------|----------|-------|
| meta_title | SEO | GENERATED | 60 | yes | |
| meta_description | SEO | GENERATED | 160 | yes | |
| starting_price | Hero | EXTRACTED | - | yes | AED format from PDF |
| about_paragraph_1 | About | HYBRID | 500 | yes | Generated prose embedding extracted data |
| ... | ... | ... | ... | ... | ... |

## Section Order

1. SEO
2. Hero
3. About
...
```

### Field naming convention

- All `snake_case`, lowercase
- Numbered items: `amenity_1_title`, `amenity_2_title` (not `amenity_title_1`)
- Pairs: `faq_1_question` / `faq_1_answer`
- Descriptions: `amenity_1_description` (not `amenity_1_desc` or `amenity_1_text`)
- Section headers: `<section>_h2` (e.g., `about_h2`, `amenities_h2`)
- Sub-headers: `<section>_h3` or `<item>_h3`
- No spaces, no hyphens in field names

### Field type classification

| Type | Meaning | Needs prompt? | Written to sheet? |
|------|---------|--------------|-------------------|
| GENERATED | AI composes content from context | YES | YES - Column C |
| EXTRACTED | Verbatim from PDF brochure | NO | YES - Column C |
| HYBRID | AI prose that embeds extracted data | YES | YES - Column C |
| STATIC | Fixed UI element, not generated | NO | NO |

**Key rule:** EXTRACTED fields appear in the field registry (they need sheet cells) but do NOT get seeded into the `prompts` database table. They are pass-through from PDF extraction.

### Section naming convention

Use these standardized section names where applicable. Template-specific sections are allowed but should be clearly named:

| Standard name | Used in |
|--------------|---------|
| SEO | All 6 templates |
| Hero | All 6 templates |
| About | aggregators, adop, commercial |
| Overview | opr, mpp |
| Project Details | aggregators, commercial |
| Amenities | aggregators, mpp, adre, commercial |
| Payment Plan | aggregators, opr, mpp, commercial |
| Location | aggregators, adop, adre, commercial |
| Developer | All 6 templates |
| FAQ | All 6 templates |
| Investment | opr, adop |
| Economic Appeal | adre, commercial |
| Key Benefits | adop |
| Key Points | mpp |
| Floor Plans | aggregators, mpp |
| Area Infrastructure | adop |
| Advantages | commercial |

---

## How Phase 2 Consumes This

Phase 2 Task 1 rewrites `backend/app/services/template_fields.py`:

```python
# Current format (Phase 1):
ADOP_FIELDS: FieldDefs = {
    "meta_title": 60,        # just field_name: char_limit
    "meta_description": 160,
}

# Target format (Phase 2):
from dataclasses import dataclass

@dataclass(frozen=True)
class FieldDef:
    row: int              # <-- from Google Sheet row number
    section: str          # <-- from field registry "section" column
    character_limit: int | None  # <-- from field registry "char_limit" column
    required: bool = False       # <-- from field registry "required" column
    field_type: str = "GENERATED"  # <-- from field registry "type" column

ADOP_FIELDS: dict[str, FieldDef] = {
    "meta_title": FieldDef(row=3, section="SEO", character_limit=60, required=True, field_type="GENERATED"),
    "starting_price": FieldDef(row=11, section="Hero", character_limit=None, required=True, field_type="EXTRACTED"),
}
```

The field registry table maps 1:1 to FieldDef entries. The only additional data needed is `row` (Google Sheet row number), which comes from cross-referencing with the actual sheet.

---

## Session Prompt Template

Use this prompt when starting an audit session for a template that hasn't been audited yet:

```
I'm conducting a prompt copywriting audit for the [TEMPLATE_TYPE] template
([TARGET_SITE]).

Context files to read first:
- prompt-organizaton/AUDIT_CONTRACT.md (output format contract)
- backend/app/services/template_fields.py (current field definitions)
- backend/app/services/prompt_manager.py (current prompt defaults)
- docs/TEMPLATES_REFERENCE.md (template specifications)
- [Any existing screenshots in prompt-organizaton/XX-<template>/]

The audit must produce these 3 artifacts in prompt-organizaton/XX-<template>/:
1. <template>-template-sections-specifications.md (section-by-section spec)
2. prompt <template>.md (system prompt for Claude API)
3. <template>-field-registry.md (structured field table per AUDIT_CONTRACT.md)

The field registry is the most important output -- it feeds directly into
backend code. Use exact field naming convention from AUDIT_CONTRACT.md.

For each field, classify as GENERATED, EXTRACTED, HYBRID, or STATIC based on
the actual website behavior visible in the screenshots.

Cross-reference character limits against:
- The live website content (approximate from screenshots)
- The current template_fields.py definitions
- The docs/TEMPLATES_REFERENCE.md specifications
Flag any discrepancies.
```

---

## Validation Checklist (run after each audit session)

Before marking a template audit as complete, verify:

- [ ] All 3 artifact files exist
- [ ] Field registry uses exact naming convention (snake_case, no hyphens)
- [ ] Every field has a type classification (GENERATED/EXTRACTED/HYBRID/STATIC)
- [ ] Section names match the standardized list (or are clearly documented as template-specific)
- [ ] Character limits are specified for all GENERATED and HYBRID fields
- [ ] EXTRACTED fields have no character limits (use `-`)
- [ ] STATIC fields are listed for documentation but marked as STATIC
- [ ] Field count matches between registry and section spec
- [ ] System prompt references all GENERATED/HYBRID fields
- [ ] No duplicate field names within a template

---

## Current Audit Status

| # | Template | Screenshots | Section Spec | System Prompt | Field Registry | Status |
|---|----------|------------|-------------|---------------|----------------|--------|
| 01 | opr | Done | -- | Done | Done | Needs section spec |
| 02 | adop | Done | Done | Done | Done | COMPLETE |
| 03 | adre | Done | Done | Done | Done | COMPLETE |
| 04 | commercial | Done | Done | Done | Done | COMPLETE |
| 05 | aggregators | Done | Done | Done | Done | COMPLETE |
| 06 | mpp | Done | Done | Done | Done | COMPLETE |

**Update this table as audits complete.**
