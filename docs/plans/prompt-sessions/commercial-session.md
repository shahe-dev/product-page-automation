# Session Prompt: Commercial Template -- Prompt Assessment & Creation

Copy everything below the line into a new Claude Code session.

---

## Task: Assess and create the Commercial template prompt

You are working on the PDP Automation v.3 project -- a property documentation
platform that generates content for real estate listings across 6 template types.

The **commercial** template is used for cre.main-portal.com -- office,
retail, and commercial real estate project pages. This is a B2B-focused template
targeting business investors and commercial tenants.

### Context

The OPR template prompt has already been finalized as the reference standard.
Read it first to understand the tone, structure, field classification
(EXTRACTED vs GENERATED), anti-hallucination guardrails, and formatting approach:

```
prompt-organizaton/opr/prompt  opr.md
```

The commercial template has existing specification documents:

```
template-organization/commercial-template-v2-specification.md
template-organization/scraped_pages/commercial-project-page-samples/commercial-template-sections-specifications.md
```

### Available Assets

**Example project page PNG** (commercial site):
```
template-organization/scraped_pages/commercial-project-page-samples/commercial-project-page.png
```
NOTE: Only 1 commercial PNG exists. You may need to supplement analysis with
the specification documents and the current hardcoded prompts.

**Commercial template Google Sheet** (access via service account):
```
Sheet ID: YOUR_COMMERCIAL_SHEET_ID
Credentials: .credentials/service-account-key.json
```

**Current field definitions** (likely out of sync):
```
backend/app/services/template_fields.py  (COMMERCIAL_FIELDS)
```

**Current hardcoded prompts** (reference only, will be replaced):
```
backend/app/services/prompt_manager.py  (_get_commercial_prompts method)
```

**Existing project-specific prompts** (may have commercial-relevant patterns):
```
reference/company/prompts/prompt  MJL.md
reference/company/prompts/prompt GRAND POLO.md
reference/company/prompts/prompt Palm Jebel.md
```

### Key Differences from OPR

The commercial template has UNIQUE sections not found in OPR:
- **Economic Indicators** (3 label/value pairs in hero -- e.g., GDP growth, market yield)
- **Project Passport** (structured project data card)
- **Economic Appeal** (B2B investment thesis)
- **Advantages** (3 title/description pairs)
- **Location with categories**: Social, Education, Medical (not Lifestyle/Healthcare/Education)
- **No FAQ section** in the current template

The tone should be more corporate/professional than OPR's investor-focused tone.
Think institutional investors, corporate tenants, fund managers.

### Methodology (follow this order exactly)

Use the superpowers skills. Start with /skill brainstorming before implementation.

**Phase 1: Analyze specifications and existing assets**
1. Read both commercial specification documents thoroughly
2. Read the commercial project page PNG
3. Read the current COMMERCIAL_FIELDS in template_fields.py
4. Read the _get_commercial_prompts() method in prompt_manager.py
5. Document the complete section structure of commercial pages

**Phase 2: Analyze live project page**
1. From the PNG, identify ALL sections visible on the page
2. Classify each section as STATIC or DYNAMIC
3. Note the content style -- commercial pages use a different register
   than residential (more data-driven, corporate language)
4. Pay special attention to the Economic Indicators and Project Passport
   sections -- these are structured data displays

**Phase 3: Template gap analysis**
1. Access the commercial template Google Sheet via service account
2. Dump the raw structure (use pattern from backend/scripts/_dump_raw_opr.py)
3. Cross-reference: PNG sections <-> template fields <-> spec documents
4. Document any missing fields or misalignments
5. Compare the v2 specification against the current template

**Phase 4: Create the commercial prompt**
1. Write the commercial template prompt from scratch
2. Follow the EXACT same structural pattern as OPR:
   - System rules at top
   - FIELD CLASSIFICATION section (EXTRACTED vs GENERATED)
   - STEP 1: Developer PDF source rules (adapted for commercial PDFs)
   - STEP 2: Market verification (commercial metrics: yield, occupancy, cap rate)
   - STEP 3: Nearby facilities lookup (Social, Education, Medical -- not
     Lifestyle/Healthcare/Education)
   - STEP 4: Page output (all fields numbered)
   - ANTI-HALLUCINATION GUARDRAILS
3. Adapt for commercial real estate:
   - B2B professional tone (not residential investor tone)
   - Economic indicators require verified market data sources
   - Project Passport is fully EXTRACTED structured data
   - Advantages section is GENERATED with specific format
   - Location categories differ from OPR
4. Floor plans / unit types: commercial has offices, retail, etc. -- different
   terminology but same dedup and anti-hallucination rules apply
5. Every field must have EXTRACTED or GENERATED classification

**Phase 5: Template sheet updates (if needed)**
1. If gaps found, write update script following backend/scripts/update_opr_template.py
2. Support --dry-run mode
3. Insert rows bottom-to-top

### Output

Save the final prompt to:
```
prompt-organizaton/commercial/prompt commercial.md
```

Create the directory if it doesn't exist. Save analysis files to
`backend/scripts/` using `_raw_commercial.*` naming pattern.

### Rules

- ASCII only, no emojis
- Corporate professional tone, data-driven, institutional
- Do NOT duplicate OPR content -- this is a fundamentally different page type
- Commercial sites target a different audience (B2B vs B2C)
- Every template field must be covered, no more, no less
