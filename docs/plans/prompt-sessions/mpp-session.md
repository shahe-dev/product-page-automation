# Session Prompt: MPP Template -- Prompt Creation (New Design Migration)

Copy everything below the line into a new Claude Code session.

---

## Task: Create the MPP template prompt for the NEW page design

You are working on the PDP Automation v.3 project -- a property documentation
platform that generates content for real estate listings across 6 template types.

The **MPP** template is used for main-portal.com -- the company's flagship website. This is the most complex template because:

1. The site is migrating from an OLD project page design to a NEW design
2. The new design exists only as Figma mockups (exported as WEBP/JPG)
3. The old design has live examples you can screenshot
4. The prompt must target the NEW design, not the old one
5. The tone must align with OPR's approach but adapt for MPP's
   balanced buyer/investor audience (not purely investment-focused)

### Context

Read the OPR prompt first as the structural reference:
```
prompt-organizaton/opr/prompt  opr.md
```

### Available Assets

**NEW design mockups** (Figma exports -- CRITICAL, these define the target):
```
reference/company/sheet-templates/1-MPP - New Offplan Design - HERO.webp
reference/company/sheet-templates/2-MPP - New Offplan Design - Gallery and Floor plans.webp
reference/company/sheet-templates/3-MPP - New Offplan Design - PaymentPlan and Amenities.webp
reference/company/sheet-templates/4-MPP - New Offplan Design - Location and Developer.webp
reference/company/sheet-templates/5-MPP - New Offplan Design - FAQ section.webp
reference/company/sheet-templates/MPP - New Offplan Design.jpg  (full page)
reference/company/sheet-templates/MPP - New Offplan Design - reduced.jpg
```

Read ALL of these mockups. They define the new page structure, sections,
and visual hierarchy. The prompt must produce content that fills these designs.

**MPP template Google Sheet** (access via service account):
```
Sheet ID: YOUR_MPP_SHEET_ID
Credentials: .credentials/service-account-key.json
```

**Current field definitions**:
```
backend/app/services/template_fields.py  (MPP_FIELDS, lines 165-225)
```

**Current hardcoded prompts**:
```
backend/app/services/prompt_manager.py  (_get_mpp_prompts method)
```

**Old design live pages**: The current main-portal.com site has project
pages in the OLD design format. Use Playwright (webapp-testing skill) to capture
4-6 screenshots of existing project pages for tone/content reference.
Save to `prompt-organizaton/mpp/old-design/`

### Key Characteristics of MPP

MPP sits between OPR (pure investor focus) and a general audience site:
- **Balanced audience**: Both end-user buyers AND investors
- **More visual**: Key points with images, 8 amenity cards, developer stats
- **Richer location content**: location_description + area_description + future_dev
- **Developer emphasis**: 3 stat highlights + description (not just description)
- **Key Points**: 2 image-backed key selling points (unique to MPP)
- **8 amenity items** (not bullets -- title + description pairs)
- **5 FAQ pairs** (fewer than OPR's 14)
- **No Investment section** (investment angle woven into other sections)
- **No Location Access bullets** (different location treatment)

### The Migration Challenge

You must analyze BOTH:
1. **Old design pages** (live site) -- for tone, content quality, and what works
2. **New design mockups** (Figma exports) -- for section structure and field mapping

The prompt must target the NEW design. But the content tone and quality from
the old design should be preserved and improved, not discarded.

Specifically:
- Old design content that maps to a new design section: adapt the approach
- New design sections not in old design: create new prompt instructions
- Old design sections removed in new design: drop from prompt
- Where old design content is good: maintain the quality bar
- Where old design content is weak: improve using OPR patterns

### Methodology (follow this order exactly)

Use the superpowers skills. Start with /skill brainstorming before implementation.

**Phase 1: Analyze new design mockups**
1. Read ALL 5 section mockups + the full-page JPG
2. For each mockup section, identify:
   - Section name and visual hierarchy (H1, H2, H3)
   - Content fields visible (text blocks, bullet lists, cards, stats)
   - Character length estimates from the mockup placeholder text
   - Whether the content is structured data or editorial prose
3. Create a complete section map of the new design
4. Note which sections have images/visual elements that need alt text

**Phase 2: Analyze old design live pages**
1. Use Playwright to screenshot 4-6 project pages from main-portal.com
2. Save to `prompt-organizaton/mpp/old-design/`
3. For each page, identify sections and note the content approach
4. Compare old design sections to new design sections
5. Document what's preserved, what's new, what's removed
6. Note the tone -- MPP should feel premium but accessible, not purely
   analytical like OPR

**Phase 3: Template analysis**
1. Access the MPP template Google Sheet via service account
2. Dump the raw structure
3. Cross-reference: new design mockup sections <-> template fields
4. Identify gaps: sections in mockup without template fields
5. Identify orphans: template fields without mockup sections
6. Read the current MPP_FIELDS and hardcoded prompts

**Phase 4: Create section mapping document**
Before writing the prompt, create a clear mapping:

```
New Design Section -> Template Field(s) -> Content Type -> Old Design Equivalent
```

This ensures nothing is missed when writing the prompt.

**Phase 5: Create the MPP prompt**
1. Write the MPP template prompt
2. Follow the EXACT same structural pattern as OPR:
   - System rules (adapted for MPP audience)
   - FIELD CLASSIFICATION (EXTRACTED vs GENERATED)
   - STEP 1: Developer PDF source rules
   - STEP 2: Market verification
   - STEP 3: Nearby facilities lookup
   - STEP 4: Page output (all fields numbered, matching template)
   - ANTI-HALLUCINATION GUARDRAILS
3. MPP-specific adaptations:
   - Balanced buyer/investor tone (not pure investor like OPR)
   - Key Points section (2 items with image context)
   - 8 amenity cards (title + description, not bullets)
   - Rich location content (3 sub-sections: description, area, future dev)
   - Developer stats (3 highlights)
   - Shorter FAQ (5 pairs)
   - Gallery and Floor Plans section handling
   - Payment Plan with visual milestone display
4. Every field must have EXTRACTED or GENERATED classification
5. Floor plans / property types: same dedup and anti-hallucination rules as OPR
   but adapted for MPP's visual card-based display

**Phase 6: Template sheet updates (if needed)**
1. If the new design introduces sections not in the current template,
   write update script
2. Follow pattern from backend/scripts/update_opr_template.py
3. This is likely -- the template was built for the old design

### Output

Save the final prompt to:
```
prompt-organizaton/mpp/prompt mpp.md
```

Save the section mapping to:
```
prompt-organizaton/mpp/section-mapping.md
```

Save old design screenshots to:
```
prompt-organizaton/mpp/old-design/
```

Create directories if they don't exist. Save analysis files to
`backend/scripts/` using `_raw_mpp.*` naming pattern.

### Rules

- ASCII only, no emojis
- Premium but accessible tone -- not coldly analytical like OPR,
  not marketing-fluffy either. Think "confident expert advisor"
- The prompt targets the NEW design, not the old one
- Content quality from old design should be preserved where applicable
- Do NOT invent sections not visible in the new design mockups
- Do NOT carry over old design sections that were removed
- Every template field must be covered, no more, no less
- Document any template changes needed for the new design separately
