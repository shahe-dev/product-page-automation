# Session Prompt: ADRE Template -- Prompt Creation from Scratch

Copy everything below the line into a new Claude Code session.

---

## Task: Create the ADRE template prompt from scratch

You are working on the PDP Automation v.3 project -- a property documentation
platform that generates content for real estate listings across 6 template types.

The **ADRE** template is used for secondary-market-portal.com -- Abu Dhabi ready and
secondary market property pages. Unlike ADOP (off-plan/new development), ADRE
covers EXISTING properties available for resale or rental. This is a different
content angle: not "what's being built" but "what exists and what it returns."

### IMPORTANT: No existing prompt file

There is NO existing prompt markdown file for ADRE. You are creating this from
scratch by analyzing live pages, the template sheet, and codebase references.

### Context

Read the OPR prompt first as the structural reference:
```
prompt-organizaton/opr/prompt  opr.md
```

Also read the ADOP prompt if it has been created (check if it exists):
```
prompt-organizaton/adop/prompt adop.md
```
ADRE shares the Abu Dhabi market context with ADOP but targets a completely
different property lifecycle stage (ready/secondary vs off-plan).

### Available Assets

**ADRE template Google Sheet** (access via service account):
```
Sheet ID: YOUR_ADRE_SHEET_ID
Credentials: .credentials/service-account-key.json
```

**Current field definitions**:
```
backend/app/services/template_fields.py  (ADRE_FIELDS, lines 289-348)
```

**Current hardcoded prompts**:
```
backend/app/services/prompt_manager.py  (_get_adre_prompts method)
```

**No PNGs exist yet**. You will need to gather project page screenshots.
The site is secondary-market-portal.com. Use the webapp-testing skill with Playwright
to capture full-page screenshots of 4-6 project pages. Save them to:
```
prompt-organizaton/adre/
```

### Key Differences from OPR and ADOP

ADRE has a unique structure that differs from both OPR and ADOP:

- **Hero with marketing H2**: Additional marketing subheading in hero
- **Amenities with H3 subheadings**: 5 amenity items, each with its own H3
  and description paragraph (not bullet-style like OPR)
- **Economic Appeal section**: 3 distinct appeals:
  - Rental appeal (for landlords/investors)
  - Resale appeal (for flippers/capital gain seekers)
  - End-user appeal (for owner-occupiers)
  This is unique to ADRE -- neither OPR nor ADOP has this structure.
- **Location with categories**: Entertainment (3), Healthcare (3), Education (3)
  -- similar to commercial but different from OPR's Lifestyle/Healthcare/Education
- **No Payment Plan section** (ready properties, already built)
- **No Investment Opportunities section** (replaced by Economic Appeal)
- **No Property Types table / Floor Plans**
- **No Location Access bullets**
- **No Overview section** (hero description covers this)
- **8 FAQ pairs**

CRITICAL DIFFERENCE: ADRE is for READY properties. Content must NOT reference:
- Handover dates
- Construction progress
- Off-plan payment plans
- Under-construction status
Content SHOULD reference:
- Current rental yields
- Resale market trends
- Community maturity and established infrastructure
- Service charges and maintenance
- Immediate occupancy / move-in ready status

### Methodology (follow this order exactly)

Use the superpowers skills. Start with /skill brainstorming before implementation.

**Phase 1: Gather project page examples**
1. Use Playwright (webapp-testing skill) to screenshot 4-6 project pages
   from secondary-market-portal.com
2. Pick diverse projects: different communities, property types, price ranges
3. Save full-page screenshots to `prompt-organizaton/adre/`
4. If screenshots can't be captured, skip to Phase 2

**Phase 2: Analyze project pages**
1. Read all captured PNGs (or use template + prompts if no PNGs)
2. Identify ALL sections visible on each page
3. Classify each section as STATIC or DYNAMIC
4. Note content style -- ADRE pages should emphasize existing value,
   not future promise
5. Pay special attention to the Economic Appeal section (3 distinct angles)
6. Note how amenities are presented (H3 + paragraph, not bullets)

**Phase 3: Template analysis**
1. Access the ADRE template Google Sheet via service account
2. Dump the raw structure
3. Map every template field to a page section
4. Document gaps
5. Read the hardcoded prompts in prompt_manager.py

**Phase 4: Create the ADRE prompt**
1. Write the ADRE template prompt from scratch
2. Follow the same structural pattern as OPR:
   - System rules (adapted for ready/secondary market)
   - FIELD CLASSIFICATION (EXTRACTED vs GENERATED)
   - STEP 1: Source data rules (NOT "developer PDF" -- instead
     "project documentation" or "property listing data")
   - STEP 2: Market verification (Abu Dhabi rental yields, resale trends,
     DLD/RERA data, service charge benchmarks)
   - STEP 3: Nearby facilities lookup (Entertainment, Healthcare, Education)
   - STEP 4: Page output (all fields numbered)
   - ANTI-HALLUCINATION GUARDRAILS
3. ADRE-specific adaptations:
   - Hero marketing H2 format
   - Amenities as 5 H3+description blocks (not bullets)
   - Economic Appeal with 3 distinct angles (rental/resale/enduser)
   - Location with Entertainment/Healthcare/Education categories
   - Ready-property language (no construction, no handover)
   - Abu Dhabi-specific market data sources
   - 8 FAQ pairs with ready-market topics
4. Every field must have EXTRACTED or GENERATED classification

**Phase 5: Template sheet updates (if needed)**
1. If gaps found, write update script
2. Follow pattern from backend/scripts/update_opr_template.py

### Output

Save the final prompt to:
```
prompt-organizaton/adre/prompt adre.md
```

Create the directory if it doesn't exist. Save analysis files to
`backend/scripts/` using `_raw_adre.*` naming pattern.

### Rules

- ASCII only, no emojis
- Neutral, factual tone -- but oriented toward existing property value
  rather than future investment potential
- Abu Dhabi market context (not Dubai)
- Ready/secondary market language -- NEVER reference off-plan concepts
- Do NOT copy OPR sections that don't apply to ready properties
- Every template field must be covered, no more, no less
