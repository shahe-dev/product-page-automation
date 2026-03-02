# Session Prompt: ADOP Template -- Prompt Creation from Scratch

Copy everything below the line into a new Claude Code session.

---

## Task: Create the ADOP template prompt from scratch

You are working on the PDP Automation v.3 project -- a property documentation
platform that generates content for real estate listings across 6 template types.

The **ADOP** template is used for abudhabioffplan.ae -- Abu Dhabi new development
(off-plan) project pages. This template focuses on Abu Dhabi's real estate market
with emphasis on freehold investment zones, Abu Dhabi visa programs, and
Saadiyat/Yas/Reem Island developments.

### IMPORTANT: No existing prompt file

Unlike OPR and Aggregators, there is NO existing prompt markdown file for ADOP.
You are creating this from scratch by analyzing:
1. Live project page examples (PNGs must be gathered)
2. The ADOP template Google Sheet structure
3. The current hardcoded prompts in the codebase
4. The OPR prompt as the structural reference

### Context

The OPR template prompt has already been finalized as the reference standard.
Read it first -- you will follow the same structure, tone philosophy, and
field classification approach:

```
prompt-organizaton/opr/prompt  opr.md
```

### Available Assets

**ADOP template Google Sheet** (access via service account):
```
Sheet ID: YOUR_ADOP_SHEET_ID
Credentials: .credentials/service-account-key.json
```

**Current field definitions**:
```
backend/app/services/template_fields.py  (ADOP_FIELDS, lines 231-283)
```

**Current hardcoded prompts**:
```
backend/app/services/prompt_manager.py  (_get_adop_prompts method)
```

**No PNGs exist yet**. You will need to gather project page screenshots.
The site is abudhabioffplan.ae. Use the webapp-testing skill with Playwright
to capture full-page screenshots of 4-6 project pages. Save them to:
```
prompt-organizaton/adop/
```

If Playwright is not available or the site blocks automation, document what
pages you attempted and proceed with the template sheet + hardcoded prompts
as primary sources.

### Key Differences from OPR

ADOP has a distinct structure from OPR:
- **3 About paragraphs** instead of 1 overview paragraph + bullets
- **Key Benefits** section (3 items) -- not in OPR
- **Area Infrastructure** section with description + 4 bullets
- **Investment** section with description + 3 bullets
- **Developer** section (same pattern)
- **8 FAQ pairs** (not 14 like OPR)
- **No Location Access section** (no "Name -- X min" bullets)
- **No Amenities section** (different from OPR)
- **No Payment Plan detailed section** (handled differently)
- **No Property Types table / Floor Plans section**
- **Abu Dhabi-specific rules**: different visa thresholds, different market
  verification sources, different regulatory framework

Abu Dhabi visa rules (different from Dubai):
- Verify current Abu Dhabi Golden Visa thresholds (may differ from Dubai's
  AED 2M threshold)
- Abu Dhabi has specific freehold zones for foreign ownership

### Methodology (follow this order exactly)

Use the superpowers skills. Start with /skill brainstorming before implementation.

**Phase 1: Gather project page examples**
1. Use Playwright (webapp-testing skill) to screenshot 4-6 project pages
   from abudhabioffplan.ae
2. Pick diverse projects: different developers, areas, property types
3. Save full-page screenshots to `prompt-organizaton/adop/`
4. If screenshots can't be captured, skip to Phase 2 and note this gap

**Phase 2: Analyze project pages**
1. Read all captured PNGs (or use template + prompts if no PNGs)
2. Identify ALL sections visible on each page
3. Classify each section as STATIC or DYNAMIC
4. Note content style, length, structure of each dynamic section
5. Compare across multiple pages for consistency
6. Pay attention to Abu Dhabi-specific content patterns

**Phase 3: Template analysis**
1. Access the ADOP template Google Sheet via service account
2. Dump the raw structure (use pattern from backend/scripts/_dump_raw_opr.py)
3. Map every template field to a page section
4. Document missing fields or orphaned rows
5. Read the hardcoded prompts in prompt_manager.py for additional context

**Phase 4: Create the ADOP prompt**
1. Write the ADOP template prompt from scratch
2. Follow the EXACT same structural pattern as OPR:
   - System rules at top (adapt for Abu Dhabi market)
   - FIELD CLASSIFICATION section (EXTRACTED vs GENERATED)
   - STEP 1: Developer PDF source rules
   - STEP 2: Market verification (Abu Dhabi sources -- different from Dubai)
   - STEP 3: Healthcare & education lookup (Abu Dhabi facilities)
   - STEP 4: Page output (all fields numbered, matching template)
   - ANTI-HALLUCINATION GUARDRAILS
3. ADOP-specific adaptations:
   - 3 about paragraphs structure (not overview + bullets)
   - Key Benefits section format
   - Area Infrastructure section format
   - Abu Dhabi visa and investment rules
   - Abu Dhabi market verification sources
   - 8 FAQ pairs with Abu Dhabi-specific topics
4. Every field must have EXTRACTED or GENERATED classification
5. Anti-hallucination rules apply equally

**Phase 5: Template sheet updates (if needed)**
1. If gaps found, write update script
2. Follow pattern from backend/scripts/update_opr_template.py
3. Support --dry-run mode

### Output

Save the final prompt to:
```
prompt-organizaton/adop/prompt adop.md
```

Create the directory if it doesn't exist. Save analysis files to
`backend/scripts/` using `_raw_adop.*` naming pattern.

### Rules

- ASCII only, no emojis
- Same neutral, factual, investment-oriented tone as OPR
- Adapted for Abu Dhabi market (not Dubai)
- Do NOT copy OPR sections that don't exist in ADOP
- Do NOT invent sections that aren't in the template
- Every template field must be covered, no more, no less
