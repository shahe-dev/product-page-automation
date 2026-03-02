# MPP Template Section Specifications

**Template type:** `mpp`
**Target site:** `main-portal.com`
**Purpose:** the company main site - comprehensive offplan project pages

---

## SEO

### Meta Title (GENERATED)
**Characters:** 60-70
**Format:** `[Project Name] by [Developer] | [Area], Dubai`

Include: project name, developer name, location area.

### Meta Description (GENERATED)
**Characters:** 155-165
**Format:** `[Property types] by [developer] in [location]. From AED X.XM. [X/X] plan. Handover [QX 20XX].`

Must include: property types, starting price, payment plan structure, handover date.

### URL Slug (GENERATED)
**Format:** `[project-name]-[area]`
Lowercase, hyphen-separated, no special characters.

### Image Alt Tag (GENERATED)
**Characters:** 80-125
**Format:** `[Project Name] [property type] development by [Developer] in [Location], Dubai`
Factual description, no adjectives.

---

## Hero Section

### H1 Header (GENERATED)
**Characters:** 50-70
**Format:** `[Project Name] in [Area]`

Project name combined with area/location for SEO value.

### Hero Description (GENERATED)
**Characters:** 350-450
**Target:** 400

Brief project introduction - one punchy paragraph establishing the project's identity, positioning, and primary appeal. Mention developer name, property types, and key differentiator.

### Project Stats (EXTRACTED from PDF)

| Field | Format | Source |
|-------|--------|--------|
| Starting Price | AED X,XXX,XXX | PDF brochure |
| Handover | QX 20XX | PDF brochure |
| Number of Units | XXX | PDF brochure |

---

## Project Overview Section

### Project Overview H2 (STATIC)
Fixed text: "Project Overview" - do not generate.

### Project Description (GENERATED)
**Characters:** 600-800
**Target:** 700

Detailed project paragraph covering:
- Developer reputation and track record
- Project concept and positioning (waterfront, branded, resort-style, etc.)
- Unit type overview (apartments, villas, penthouses, etc.)
- Design philosophy and architectural highlights
- Target buyer profile (families, investors, end-users)

### Project Details Card (ALL EXTRACTED from PDF)

| Field | Format | Notes |
|-------|--------|-------|
| Location | Area, Sub-area | e.g., "Dubai Marina, Marina Promenade" |
| Developer | Developer Name | Verbatim from PDF |
| Property Type | Type list | apartments, villas, townhouses, penthouses, duplexes |
| Number of Bedrooms | Range | Based on floor plan data, e.g., "1-4 BR" |
| Area From | XXX sq.ft | Smallest unit size from floor plans |
| Handover | QX 20XX | Quarter and year |
| Payment Plan | X/X | e.g., "60/40" or "70/30" |

---

## Gallery Section

**STATIC - do not generate**

Image gallery populated from uploaded project images.

---

## Floor Plans Section

### Floor Plans Table (EXTRACTED - CRITICAL)

This field contains ALL floor plan entries in a SINGLE cell.
Each unique unit configuration goes on its own line.

**Format per line:**
`Unit Type | Living Area (sq ft) | Starting Price (AED)`

**Example output:**
```
Studio | 400-450 sq ft | AED 750,000
1BR Apartment | 650-800 sq ft | AED 1,100,000
2BR Apartment | 1,100-1,300 sq ft | AED 1,800,000
3BR Apartment | 1,500-1,800 sq ft | AED 2,500,000
4BR Penthouse | 2,800-3,200 sq ft | AED 5,000,000
```

**DEDUPLICATION RULES:**
- If the PDF shows multiple sub-variants of the same bedroom count (e.g., "1BR Type A - 650 sq ft" and "1BR Type B - 720 sq ft"), MERGE them into a single line with a size RANGE: `1BR Apartment | 650-720 sq ft | Starting Price`
- Use the LOWEST starting price among variants of the same type.
- If only one variant exists for a bedroom count, use exact size (no range needed): `1BR Apartment | 650 sq ft | AED 1,100,000`

**MISSING DATA RULES (ANTI-HALLUCINATION):**
- If the PDF contains NO floor plan data at all -> write TBA for the entire field.
- If sizes exist but prices do not -> list sizes, write TBA for price: `1BR Apartment | 650-800 sq ft | TBA`
- If prices exist but sizes do not -> list prices, write TBA for size: `1BR Apartment | TBA | AED 1,100,000`
- NEVER fabricate, estimate, or infer sizes or prices.
- If the PDF only lists bedroom counts with no size/price detail: `Studio | TBA | TBA`

Variable count: projects may have 2-8+ distinct floor plans. Output as many lines as the PDF supports.

### View All Floor Plans Button

**STATIC - do not generate**

---

## Payment Plan Section

### Payment Plan Description (GENERATED)
**Characters:** 150-250
**Target:** 200

Use the standardized sentence format:
`"Pay X% during construction and X% on handover in QX 20XX, with a X% booking fee."`

Embed extracted payment percentages and handover date.

### Payment Milestones (EXTRACTED from PDF)

**Format:**
```
X% -- On Booking
X% -- During Construction
X% -- On Handover (QX 20XX)
```

**CRITICAL:** Some projects have multiple payment plan options (e.g., 60/40 AND 70/30). If the PDF shows multiple plans, list each one with its milestone breakdown. Do not merge different plans into one.

**If multiple plans exist:**
```
Plan A (60/40):
10% -- On Booking
50% -- During Construction
40% -- On Handover (QX 20XX)

Plan B (70/30):
10% -- On Booking
60% -- During Construction
30% -- On Handover (QX 20XX)
```

---

## Key Points Section

Two main unique selling points of the project.

### Key Point 1 Title (GENERATED)
**Characters:** 40-60

A concise title for the first USP (e.g., "Waterfront Living", "Branded Interiors by Elie Saab", "Resort-Style Amenities").

### Key Point 1 Description (GENERATED)
**Characters:** 250-350
**Target:** 300

Expansion of the USP - what makes this feature valuable, what buyers can expect.

### Key Point 2 Title (GENERATED)
**Characters:** 40-60

A concise title for the second USP.

### Key Point 2 Description (GENERATED)
**Characters:** 250-350
**Target:** 300

Expansion of the second USP.

---

## Amenities Section

### Amenities H2 (STATIC)
Fixed text: "Amenities" - do not generate.

### Amenities Paragraph (GENERATED)
**Characters:** 300-450
**Target:** 380

Overview of the amenities using the top 3 differentiating amenities as examples. Describe what makes the project unique from an amenities perspective. 4 sentences maximum.

Focus on:
- Wellness/fitness (gym, pool, spa, yoga)
- Leisure/social (lounges, BBQ areas, rooftop terraces)
- Family/children (kids play areas, parks, splash pads)
- Practical services (concierge, parking, security)

### Amenities Table (EXTRACTED from PDF)

Extract ALL amenities from the PDF brochure. This section has a "Show all amenities" button indicating it must cover every amenity the project offers.

**Format:** List each amenity on its own line or in a structured format suitable for the UI.

**3-TIER SCOPING RULE:**
- TIER 1 (inside residences): maid room, driver room, show kitchen, storage, private balcony, private terrace, private pool
- TIER 2 (inside building): lobby, gym, swimming pool, spa, sauna, yoga studio, kids' play area, business center, concierge, co-working, lounge, parking
- TIER 3 (within community): marina, beach club, parks, retail, cycling tracks, jogging paths, sports courts, schools, healthcare

**EXCLUDE:** views, large windows, location descriptions, landscaping, future hotels, masterplan-level infrastructure not yet built, boardwalks, marketing adjectives.

---

## Get Professional Property Guidance Section

**STATIC - do not generate**

Contact form and agent information block.

---

## Location Section

### Location Title (GENERATED)
**Format:** `[Area Name], [Emirate]`
**Characters:** 30-50

Example: "Dubai Marina, Dubai"

### Location Description (GENERATED)
**Characters:** 450-600
**Target:** 550

Comprehensive location overview including:
- Area positioning and character
- Key attractions and landmarks nearby
- Connectivity (metro, highways, airport proximity)
- Lifestyle offerings (dining, retail, entertainment)
- Drive times to major destinations (use Google Maps verified times)

---

## Explore Future Developments Section

**STATIC - do not generate**

Dynamic block showing nearby upcoming projects.

---

## Other Projects in [Area Name] Section

**STATIC - do not generate**

Dynamic block showing other projects in the same area.

---

## Developer Section

### Developer Name Title (GENERATED)
**Format:** `[Developer Name]`
**Characters:** 20-50

### Developer Description (GENERATED)
**Characters:** 400-550
**Target:** 500

Developer profile covering:
- Founding year or history
- Portfolio scope (number of projects, regions)
- Reputation and awards
- Design philosophy or USPs
- Dubai/UAE market presence
- Notable completed projects

---

## Other Projects by Developer Section

**STATIC - do not generate**

Dynamic block showing other projects by the same developer.

---

## FAQ Section

### FAQ Structure

Generate 5 Q&A pairs that are relevant to this specific project.

**TIER 1: CORE FAQs (Always include these 5)**

| # | Question Template | Answer Source |
|---|-------------------|---------------|
| 1 | What is [Project Name]? | Overview section |
| 2 | Where is [Project Name] located? | Location section |
| 3 | What unit types are available in [Project Name]? | Floor plan data (EXTRACTED) |
| 4 | What is the starting price of [Project Name]? | Starting price (EXTRACTED) |
| 5 | What is the payment plan for [Project Name]? | Payment plan (EXTRACTED) |

**Answer Guidelines:**
- Length: 40-80 words per answer
- Tone: Informative, factual - not salesy
- Structure: Direct answer first, then supporting detail
- Data: Include specific numbers (sizes, prices, dates) where available
- No fluff: Avoid "absolutely" / "definitely" / "perfect for"

**FAQ OUTPUT FORMAT:**
```
Q: [Question text]
A: [Answer text - 40-80 words]
```

---

## Static Sections Summary

The following sections are STATIC and should NOT be generated:

1. Gallery Section
2. View All Floor Plans Button
3. Get Professional Property Guidance Section
4. Explore Future Developments Section
5. Other Projects in [Area Name] Section
6. Other Projects by [Developer Name] Section
7. Footer/Contact sections
8. All CTAs and form elements

---

## Total Character Count

**All generated sections combined:**
- Minimum: ~3,200 characters
- Maximum: ~4,800 characters
- Target: ~4,000 characters (~600-900 words)

---

## Style Guidelines

**Tone:** Professional, confident, informative. Not salesy or hyperbolic.

**Formatting Rules:**
- No bullet points within paragraphs (convert to flowing prose)
- Include specific numbers: unit counts, sizes, prices, drive times
- Avoid superlatives without substantiation
- No exclamation marks
- Write "sq.ft" and "sqm" (not "square feet" or "square meters")

**Terminology:**
- Use "residents" not "homeowners" or "buyers" when describing lifestyle
- Use "investors and end-users" when addressing target audience
- Reference "capital appreciation" and "rental yields" for investment content
- Use "handover" not "completion" for delivery dates

**Data Handling:**
- If brochure lacks specific data (price, size, payment plan), write TBA - do NOT fabricate
- If location drive times are not provided, use reasonable estimates based on Google Maps
- Cross-reference amenities from both marketing copy and floor plans in brochure
