# Session Prompt: Aggregators Template -- Prompt Assessment & Creation

Copy everything below the line into a new Claude Code session.

---

## Task: Assess and create the Aggregators template prompt

You are working on the PDP Automation v.3 project -- a property documentation
platform that generates content for real estate listings across 6 template types.

The **aggregators** template is used for 24+ third-party aggregator websites
(single-page property domains like dubaislands.ae, sobha-central.ae, etc.).

### Context

The OPR template prompt has already been finalized as the reference standard.
Read it first to understand the tone, structure, field classification
(EXTRACTED vs GENERATED), anti-hallucination guardrails, and formatting approach:

```
prompt-organizaton/opr/prompt  opr.md
```

There are existing project-specific prompts that were used manually before the
automation pipeline. These need to be analyzed and consolidated into a single
aggregator template prompt:

```
reference/company/prompts/prompt  MJL.md
reference/company/prompts/prompt GRAND POLO.md
reference/company/prompts/prompt Palm Jebel.md
```

### Available Assets

**Example project page PNGs** (aggregator sites -- 23 screenshots):
```
template-organization/scraped_pages/*.png
```
These are full-page screenshots of live aggregator project pages.

**Aggregator template Google Sheet** (access via service account):
```
Sheet ID: YOUR_AGGREGATORS_SHEET_ID
Credentials: .credentials/service-account-key.json
```

**Current field definitions** (likely out of sync):
```
backend/app/services/template_fields.py  (AGGREGATORS_FIELDS)
```

**Current hardcoded prompts** (reference only, will be replaced):
```
backend/app/services/prompt_manager.py  (_get_aggregators_prompts method)
```

**Previous analysis documents**:
```
template-organization/CONSOLIDATION_ANALYSIS.md
template-organization/LIVE_PAGE_ANALYSIS.md
template-organization/page_structure_analysis.json
```

### Methodology (follow this order exactly)

Use the superpowers skills. Start with /skill brainstorming before implementation.

**Phase 1: Analyze existing prompts**
1. Read all 3 project-specific prompts (MJL, Grand Polo, Palm Jebel)
2. Compare their structure, sections, and tone
3. Identify what is common vs what is project-specific
4. Identify differences from the OPR prompt approach
5. Document which elements are aggregator-specific vs OPR-specific

**Phase 2: Analyze live project pages**
1. Read 6-8 of the aggregator PNGs (pick diverse examples)
2. Identify ALL sections visible on each page
3. Classify each section as STATIC (constant across all pages) or
   DYNAMIC (unique per project, requires content generation)
4. Note the content style, length, and structure of each dynamic section
5. Compare across multiple PNGs to confirm consistency

**Phase 3: Template gap analysis**
1. Access the aggregator template Google Sheet via service account
2. Dump the raw structure (use the pattern from backend/scripts/_dump_raw_opr.py)
3. Cross-reference: for every DYNAMIC section found in PNGs, verify
   it has a corresponding field in the template
4. For every template field, verify it maps to a visible section in the PNGs
5. Document any missing fields or orphaned template rows

**Phase 4: Prompt-to-template alignment**
1. Cross-reference the existing prompts against the template fields
2. Identify fields that the prompts cover vs fields they miss
3. Identify prompt instructions that don't map to any template field

**Phase 5: Create the aggregator prompt**
1. Write a single consolidated aggregator template prompt
2. Follow the EXACT same structure as the OPR prompt:
   - System rules at top
   - FIELD CLASSIFICATION section (EXTRACTED vs GENERATED)
   - STEP 1: Developer PDF source rules
   - PAYMENT PLAN rules
   - STEP 2: Market verification
   - STEP 3: Healthcare & education lookup
   - STEP 4: Page output (all fields numbered)
   - ANTI-HALLUCINATION GUARDRAILS at bottom
3. Adapt the tone and sections for aggregator sites (simpler structure,
   fewer sections than OPR, more SEO-focused)
4. Every field must have EXTRACTED or GENERATED classification
5. Floor plans / property types section must include dedup rules
   and missing data handling (same as OPR)

**Phase 6: Template sheet updates (if needed)**
1. If gaps were found in Phase 3, write a script to update the template
2. Follow the pattern from backend/scripts/update_opr_template.py
3. Support --dry-run mode
4. Insert rows bottom-to-top to avoid offset issues

### Output

Save the final prompt to:
```
prompt-organizaton/aggregators/prompt aggregators.md
```

Create the directory if it doesn't exist. Also save any analysis/dump files
to `backend/scripts/` using the `_raw_aggregators.*` naming pattern.

### Rules

- ASCII only, no emojis
- Neutral, factual, investment-oriented tone
- Do NOT duplicate OPR content -- adapt it for the aggregator page structure
- Aggregator pages are typically simpler than OPR (fewer sections, shorter content)
- The prompt must cover ALL fields in the template sheet, no more, no less
