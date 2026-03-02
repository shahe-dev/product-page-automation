# Commercial Template v2 -- Gap Analysis & New Specification

## Source Materials

- **Live page spec**: `template-organization/scraped_pages/commercial-project-page-samples/commercial-template-sections-specifications.md`
- **Live page screenshot**: `template-organization/scraped_pages/commercial-project-page-samples/commercial-project-page.png`
- **Current code fields**: `backend/app/services/template_fields.py` (COMMERCIAL_FIELDS, lines 354-415)
- **Current prompts**: `backend/app/services/prompt_manager.py` (_get_commercial_prompts, lines 928-1081)
- **Current raw Google Sheet**: `backend/scripts/_raw_commercial.json`
- **Standardized preview**: `backend/scripts/_preview_commercial.json`

---

## Part 1: Gap Analysis

### Critical Mismatches

| # | Issue | Current Code | Live Page Spec | Severity |
|---|-------|-------------|----------------|----------|
| 1 | **Economic Appeal section** | Generates h2 + description (500 chars) | **FULLY STATIC -- do not generate** | CRITICAL -- wasted API calls, wrong content |
| 2 | **Hero description limit** | 400 characters | 70-80 characters | CRITICAL -- 5x overshoot |
| 3 | **Hero features naming** | `economic_indicator_N_label` (30) / `_value` (20) | Feature N title (15-30) / description (up to 60) | HIGH -- wrong field names, wrong limits, wrong semantics |
| 4 | **About section missing H3** | Only `area_h2` (50) + `area_description` (500) | H2 + H3 (60-80) + description (150-200) | HIGH -- missing heading tier, description 2.5x too long |
| 5 | **Project Passport structure** | Single prose `project_passport_description` (400) | 5 discrete data fields: Developer, Location, Payment Plan, Area, Property Type | CRITICAL -- completely wrong structure |
| 6 | **Payment Plan structure** | `payment_plan_h2` (50) + single `description` (800) | Headline (e.g. "70/30"), description (150), construction %, handover date, handover % | CRITICAL -- wrong structure, 5x too long |
| 7 | **Culture section** | Does not exist | Full section: description (100-300) + 3 venue/time entries | HIGH -- entire section missing |
| 8 | **Location subsection descriptions** | Only `location_description` (550) | 3 separate descriptions: Social (100-300), Education (100-300), Culture (100-300) | HIGH -- flattened into one field |
| 9 | **Developer structure** | `developer_h2` (50) + `description` (500) | Developer name + H2 + H3 (optional, 60-80) + description (150-250) | MEDIUM -- description 2x too long, missing fields |
| 10 | **Amenities limit range** | Title: 40 chars, Description: 150 chars | Title: 40-80 chars, Description: 100-200 chars | MEDIUM -- limits don't match spec |

### Missing Fields (in spec, not in code)

| Field | Section | Char Limit |
|-------|---------|------------|
| `hero_sale_price` | Hero (sidebar) | ~15 |
| `hero_payment_plan` | Hero (sidebar) | ~10 |
| `hero_handover` | Hero (sidebar) | ~10 |
| `about_area_h3` | About Area | 60-80 |
| `passport_developer` | Project Passport | None |
| `passport_location` | Project Passport | None |
| `passport_payment_plan` | Project Passport | None |
| `passport_area` | Project Passport | None |
| `passport_property_type` | Project Passport | None |
| `payment_plan_headline` | Payment Plan | ~20 |
| `payment_plan_description` (short) | Payment Plan | 150 |
| `payment_construction_pct` | Payment Plan | ~5 |
| `payment_handover_date` | Payment Plan | ~20 |
| `payment_handover_pct` | Payment Plan | ~5 |
| `location_h3` | Location | 40-80 |
| `social_facilities_description` | Social Facilities | 100-300 |
| `education_medicine_description` | Education & Medicine | 100-300 |
| `culture_description` | Culture | 100-300 |
| `culture_venue_1` | Culture | 80 |
| `culture_venue_2` | Culture | 80 |
| `culture_venue_3` | Culture | 80 |
| `developer_h3` | Developer | 60-80 (optional) |
| `cta` | Advantages | 15-25 |

### Fields to Remove (in code, not needed per spec)

| Field | Reason |
|-------|--------|
| `image_alt` | Not in page spec |
| `economic_appeal_h2` | Section is fully static |
| `economic_appeal_description` | Section is fully static |
| `amenities_h2` | Section header is static on the page |
| `project_passport_h2` | Section header is static ("Project Passport") |
| `project_passport_description` | Replaced by 5 discrete data fields |
| `economic_indicator_N_label` | Replaced by `feature_N_title` |
| `economic_indicator_N_value` | Replaced by `feature_N_description` |

### Sections That Are Fully Static (DO NOT generate)

Per the spec, these sections have no generated content:

1. **Economic Appeal Section** -- fully static
2. **The Dubai Plan block Section** -- fully static
3. **Gallery Section** -- fully static
4. **"After completion, you have 3 options"** -- static section header

---

## Part 2: New Commercial Template v2

### Section-by-Section Field Definitions

All fields marked **(generate)** require AI content generation.
All fields marked **(static)** are hardcoded in the frontend and do not appear in the template.
Character limits shown as recommended ranges from the spec.

---

#### 1. SEO

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 1 | Meta Title | SEO page title | 60-70 | Yes |
| 2 | Meta Description | SEO meta description | 155-165 | Yes |
| 3 | URL Slug | URL-friendly identifier. Format: [project-name-location]. Lowercase, hyphens, no spaces | None | Yes |

#### 2. Hero Section

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 4 | H1 | Main page heading | 50-60 | Yes |
| 5 | Hero Description | Brief promotional description under H1 | 70-80 | Yes |
| 6 | Hero - Sale Price | Starting sale price. Label "Sale price from:" is static. Value extracted from PDF (e.g. "AED 3.5M") | ~15 | Yes |
| 7 | Hero - Payment Plan | Payment plan ratio. Label "Payment Plan:" is static. Value extracted from PDF (e.g. "50/50") | ~10 | Yes |
| 8 | Hero - Handover | Handover quarter/year. Label "Handover:" is static. Value extracted from PDF (e.g. "Q4 2028") | ~10 | Yes |
| 9 | Feature 1 - Title | Economic indicator or key feature title | 15-30 | Yes |
| 10 | Feature 1 - Description | Supporting detail for feature 1 | up to 60 | Yes |
| 11 | Feature 2 - Title | Key feature title | 15-30 | Yes |
| 12 | Feature 2 - Description | Supporting detail for feature 2 | up to 60 | Yes |
| 13 | Feature 3 - Title | Key feature title | 15-30 | Yes |
| 14 | Feature 3 - Description | Supporting detail for feature 3 | up to 60 | Yes |

#### 3. About [Project Name]

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 15 | About Area H2 | "About ... [project name]" | ~40 | Yes |
| 16 | About Area H3 | Brief descriptive promotional subtitle with mention of area | 60-80 | Yes |
| 17 | About Description | Paragraph summary about the project | 150-200 | Yes |

#### 4. Project Passport (Data Table)

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 15 | Passport - Developer | Developer name | None | Yes |
| 16 | Passport - Location | Project location | None | Yes |
| 20 | Passport - Payment Plan | Payment plan summary (e.g. "70/30") | None | Yes |
| 21 | Passport - Area | Area range in sq ft | None | Yes |
| 22 | Passport - Property Type | Property type(s) | None | Yes |

#### 5. Economic Appeal Section

**FULLY STATIC -- no fields to generate.**

#### 6. The Dubai Plan Block

**FULLY STATIC -- no fields to generate.**

#### 7. Gallery

**FULLY STATIC -- no fields to generate.**

#### 8. Payment Plan

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 23 | Payment Plan Headline | Format: "[number/number] Payment Plan" (e.g. "70/30 Payment Plan") | ~30 | Yes |
| 24 | Payment Plan Description | Description of the payment plan structure | ~150 | Yes |
| 25 | Construction Percentage | First number percentage (e.g. "70%"). "On Construction" label is static | ~5 | Yes |
| 26 | Handover Date | Expected handover date | ~20 | Yes |
| 27 | Handover Percentage | Second number percentage (e.g. "30%"). "On Handover" label is static | ~5 | Yes |

#### 9. After Completion (3 Options)

**STATIC section header. No fields to generate.**

#### 10. Advantages (3 items)

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 28 | Advantage 1 - Title | Key advantage heading | 40-80 | Yes |
| 29 | Advantage 1 - Description | Brief supporting description | 100-200 | Yes |
| 30 | Advantage 2 - Title | Key advantage heading | 40-80 | Yes |
| 31 | Advantage 2 - Description | Brief supporting description | 100-200 | Yes |
| 32 | Advantage 3 - Title | Key advantage heading | 40-80 | Yes |
| 33 | Advantage 3 - Description | Brief supporting description | 100-200 | Yes |

#### 11. Amenities ("Why you will love this place") -- 3 to 5 items

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 34 | Amenity 1 - Title | Feature or amenity name | 40-80 | Yes |
| 35 | Amenity 1 - Description | Brief description | 100-200 | Yes |
| 36 | Amenity 2 - Title | Feature or amenity name | 40-80 | Yes |
| 37 | Amenity 2 - Description | Brief description | 100-200 | Yes |
| 38 | Amenity 3 - Title | Feature or amenity name | 40-80 | Yes |
| 39 | Amenity 3 - Description | Brief description | 100-200 | Yes |
| 40 | Amenity 4 - Title | Feature or amenity name (optional) | 40-80 | Yes |
| 41 | Amenity 4 - Description | Brief description (optional) | 100-200 | Yes |
| 42 | Amenity 5 - Title | Feature or amenity name (optional) | 40-80 | Yes |
| 43 | Amenity 5 - Description | Brief description (optional) | 100-200 | Yes |

#### 12. Location & Advantages

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 44 | Location H3 | Subtitle for location section. "Location & Advantages" H2 is static | 40-80 | Yes |
| 45 | Location Description | Description of location advantages, transport, infrastructure | 250-400 | Yes |

#### 13. Social Facilities

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 46 | Social Facilities Description | Brief description of nearby social/lifestyle facilities. Section header is static | 100-300 | Yes |
| 47 | Social Facility 1 | Location name + time in minutes | ~80 | Yes |
| 48 | Social Facility 2 | Location name + time in minutes | ~80 | Yes |
| 49 | Social Facility 3 | Location name + time in minutes | ~80 | Yes |

#### 14. Education & Medicine

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 50 | Education & Medicine Description | Brief description of nearby educational and medical institutions. Section header is static | 100-300 | Yes |
| 51 | Education Facility 1 | Institution name + time in minutes | ~80 | Yes |
| 52 | Education Facility 2 | Institution name + time in minutes | ~80 | Yes |
| 53 | Education Facility 3 | Institution name + time in minutes | ~80 | Yes |

#### 15. Culture

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 54 | Culture Description | Brief description of nearby cultural establishments. Section header is static | 100-300 | Yes |
| 55 | Culture Venue 1 | Venue name + time in minutes | ~80 | Yes |
| 56 | Culture Venue 2 | Venue name + time in minutes | ~80 | Yes |
| 57 | Culture Venue 3 | Venue name + time in minutes | ~80 | Yes |

#### 16. About the Developer

| # | Field Name | Guidelines/Comments | Char Limit | Generate? |
|---|-----------|-------------------|-----------|----------|
| 58 | Developer Name | Developer company name | None | Yes |
| 59 | Developer Description | Brief description about the developer | 150-250 | Yes |

---

### Summary: v1 vs v2

| Metric | Current v1 | New v2 |
|--------|-----------|--------|
| Total generated fields | 42 | 59 |
| Static sections wrongly generated | 2 (Economic Appeal h2 + desc) | 0 |
| Missing sections | Culture (entire), Hero sidebar data | None |
| Structural mismatches | 3 critical (Passport, Payment, Hero desc) | 0 |
| Wrong character limits | 8+ fields | 0 |
| Wrong field names | 6 (economic_indicator_*) | 0 |

---

## Part 3: Prompt Implications (For Future Phase)

The following prompt changes will be required when the template is finalized. These are documented here for planning but should NOT be implemented until the template and field mapping are locked.

### Prompts to Remove
- `economic_appeal_h2` -- section is static
- `economic_appeal_description` -- section is static
- `economic_indicator_N_label` (x3) -- replaced by feature fields
- `economic_indicator_N_value` (x3) -- replaced by feature fields
- `project_passport_h2` -- section header is static
- `project_passport_description` -- replaced by discrete passport fields

### Prompts to Add
- `feature_N_title` (x3) -- hero features with 15-30 char limit
- `feature_N_description` (x3) -- hero feature descriptions, up to 60 chars
- `about_area_h3` -- about section subtitle, 60-80 chars
- `passport_developer` -- discrete data field
- `passport_location` -- discrete data field
- `passport_payment_plan` -- discrete data field
- `passport_area` -- discrete data field
- `passport_property_type` -- discrete data field
- `payment_plan_headline` -- e.g. "70/30 Payment Plan"
- `payment_construction_pct` -- percentage value
- `payment_handover_date` -- date value
- `payment_handover_pct` -- percentage value
- `location_h3` -- location subtitle, 40-80 chars
- `social_facilities_description` -- 100-300 chars
- `education_medicine_description` -- 100-300 chars
- `culture_description` -- 100-300 chars
- `culture_venue_N` (x3) -- venue name + time
- `developer_h3` -- optional subtitle, 60-80 chars
- `developer_name` -- developer company name

### Prompts to Modify (character limits)
- `hero_description`: 400 -> 80 (70-80 range)
- `area_description` -> `about_description`: 500 -> 200 (150-200 range)
- `payment_plan_description`: 800 -> 150
- `developer_description`: 500 -> 250 (150-250 range)
- `amenity_N_title`: 40 -> 80 (40-80 range)
- `amenity_N_description`: 150 -> 200 (100-200 range)
- `advantage_N_title`: 60 -> 80 (40-80 range)

### Cross-Template Inconsistency Note

The user identified that Guidelines/Comments columns differ significantly across the 6 templates. The current raw templates have:
- **Aggregators, OPR, MPP, ADOP, ADRE**: Various column structures, some with Guidelines/Comments, some without
- **Commercial (raw)**: 4-column format (Fields, EN, RU, AR) with char limits embedded in field names

The standardized preview format (5 columns: Guidelines/Comments, Fields, EN, AR, RU) should be adopted uniformly across ALL templates. This is a prerequisite for reliable field mapping.
