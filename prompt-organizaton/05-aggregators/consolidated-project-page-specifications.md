# the company Project Page Sections - Consolidated Specifications

---

## Overview

This specification defines the content generation requirements for all the company project landing pages across multiple regional domains:

| Region | Domains | Currency |
|--------|---------|----------|
| Dubai | sobhacentral.ae, dubaimaritimecity.ae, dubaicreekliving.ae, dubaihillsproperty.ae, dubaislands.ae, rashidyachtsmarina.ae, citywalkproperty.ae | AED (USD) |
| Abu Dhabi | capital-luxury.ae, abu-dhabi.realestate | AED (USD) |
| Ras Al Khaimah | ras-al-khaimah-properties.ae | AED (USD) |
| Saudi Arabia | saudi-estates.ae | SAR (USD) |

**Static Elements (NEVER generate):**
- All forms (consultation, callback, brochure download, floor plan download)
- All CTAs and buttons
- Online consultation / Zoom booking sections
- Developer logos
- Gallery images
- Similar/related projects sections
- the company company sections (stats, awards, testimonials, media mentions)
- "6 Steps to Property Success" process sections
- "After completion, you have 3 options" sections
- Footer sections
- Vision 2030 context blocks (Saudi Arabia)
- Agent/expert cards (photo, name, rating)

---

## SEO

**Title** (generate) 50-60 characters
Format varies by region:
- Dubai: `[Project Name] by [Developer] in [Location], Dubai`
- Abu Dhabi: `[Project Name] by [Developer] | [Location], Abu Dhabi`
- RAK: `[Project Name] at [Location] | Ras Al Khaimah`
- Saudi: `[Project Name] by [Developer] in [City], Saudi Arabia`

**Meta-description** (generate) 155-165 characters
Include: project type, developer, location, starting price, payment plan ratio, handover date, one key differentiator

**URL slug** (generate)
Format: `[project-name]-[location]` (lowercase-hyphens)

---

## Hero Section

**H1 Header** (generate) 50-70 characters
Format options:
- `[Project Name] – [Property Type] at [Location]`
- `[Project Name] by [Developer] in [Location]`
- `Invest in [Project/Location Name]: [Value Proposition]`

**Subtitle** (generate) 80-150 characters
Investment and lifestyle overview. Emphasize:
- ROI potential and capital growth (investment angle)
- Key lifestyle features (waterfront, resort-style, urban, etc.)
- Location benefits

**Key Investment Stats** (generate 3 bullet points):
Extract from brochure and market data. Format examples:
- ROI/Yield: "Average rental yields range from X–X% in [Location]"
- Starting Price: "AED X.XXM (USD XXXK) Starting property price"
- Capital Gains: "≈ +XX% Projected annual capital gains"
- Market Position: "Undersupplied luxury [property type] market in [City]"
- Connectivity: "Prime location with X minutes to [landmark]"

**Quick Info Cards** (EXTRACT from brochure):

| Field | Format |
|-------|--------|
| Starting Price | `AED X.XXM (USD XXXK)` or `SAR X.XM (USD XXXK)` |
| Payment Plan | `XX/XX` or `XX/XX | XX/XX | XX/XX` for multiple options |
| Handover | `QX 20XX` or `QX 20XX – QX 20XX` for phased |

---

## About Section

**Section Label**: `About [Project Name]` or `About [Project Name] by [Developer]`

**H2 Header** (generate) 50-80 characters
Format options:
- `[Project Name] – [Key Value Proposition]`
- `[Project Name] by [Developer] — [Property Type] at [Location]`
- `Discover your [lifestyle benefit] in [Location]`
- `The New Standard in [City] Luxury`

**About Paragraph** (generate) 400-650 characters | ~70-120 words

Write 1 paragraph covering ALL of the following:
- Property types available (apartments, villas, penthouses, duplexes, townhouses, studios)
- Bedroom configurations – list ALL types from brochure using exact naming
- Total unit count (if provided)
- Key features (views, balconies, terraces, staff quarters, etc.)
- Amenity highlights (podium, marina, resort facilities)
- Location positioning
- Starting price and handover (brief mention)
- Target buyer profile (investors, families, end-users)

**CRITICAL:** Unit type breakdown must match floor plan types exactly as provided in brochure. Use "+1" notation for maid's room units.

---

## Project Details Card

**All data EXTRACTED from brochure:**

| Field | Format | Notes |
|-------|--------|-------|
| Developer | Developer name | Links to developer page |
| Location | `[Area], [District/Road]` or `[City], [Country]` | |
| Payment Plan | `XX/XX` or `XX/XX, XX/XX, XX/XX` | List all available options |
| Area | `XXX sq. ft. – X,XXX sq. ft.` or `From X,XXX sq. ft.` | Smallest to largest |
| Property Type | `Apartments` / `Villas` / `Penthouses` / etc. | Comma-separated list |
| Bedrooms | `X-XBR` or `Studio, 1-4BR` | Range or list |

---

## Economic Appeal Section

**Section Label**: `Economic Appeal` or `Economic appeal for investors`

**H2 Header** (generate) 40-60 characters
Format options:
- `Land a Highly Profitable Investment`
- `Tap into [City's] [Industry] Economic Engines`
- `Invest in [Location's] Rising [Waterfront/Urban] Economy`
- `Get Your Exclusive Preview`
- `Glamorous [Area] Living`

**Economic Paragraph** (generate) 400-650 characters | ~70-120 words

Write 1-2 paragraphs covering:
- Location advantages (address prestige, connectivity, infrastructure)
- Market drivers (tourism, business hubs, population growth, new developments)
- Rental returns potential with yield percentage range
- Capital appreciation outlook with percentage if available
- Tenant demand factors
- Service charges per sq.ft (if available)
- Developer reputation and build quality
- Limited inventory / exclusivity angle (if applicable)

**Price Statistics Cards** (extract/verify from Property Monitor or equivalent):
- Property Price per sq.m: `XXX → XXX USD/sq.m (20XX)` with `↑ XX.X%` change
- Land Plot Price per sq.m: `XXX → XXX USD/sq.m (20XX)` with `↑ XX.X%` change

**Economic Benefits List** (generate if template requires numbered format):
Format:
```
01. [Benefit Title] – [Brief description or specific data point]
02. [Benefit Title] – [Brief description or specific data point]  
03. [Benefit Title] – Prices start at [Currency] X.XXM (USD XXXK)
```

---

## Payment Plan Section

**Section Label**: `Payment Plan`

**H2 Header** (generate) 40-60 characters
Format: `Easy Installments: [XX/XX] by [Developer]` or `Flexible Payment Plans from [Developer]`

**Payment Description** (generate) 150-250 characters
Brief explanation of payment structure flexibility and investor benefits.

### Payment Plan Extraction Rules

**CRITICAL: Hybrid Extraction Approach**

The automation system must extract ALL payment plan options from the brochure. When multiple payment plans exist, the LLM must:

1. **Identify all payment plan variants** (e.g., 50/50, 60/40, 65/35, 75/25, 80/20)
2. **Extract the breakdown for each plan:**
   - Down Payment / Booking percentage
   - During Construction percentage(s)
   - On Handover percentage
3. **Generate content that accurately represents all options**

**Single Payment Plan Format:**
| Stage | Percentage |
|-------|------------|
| On Booking / Down Payment | XX% |
| On Construction | XX% |
| On Handover | XX% + handover date |

**Multiple Payment Plan Format:**
| Plan | Down Payment | Construction | Handover |
|------|--------------|--------------|----------|
| Plan A (XX/XX) | XX% | XX% | XX% |
| Plan B (XX/XX) | XX% | XX% | XX% |
| Plan C (XX/XX) | XX% | XX% | XX% |

**VALIDATION RULE:** Each plan's percentages MUST sum to exactly 100%.

**Post-Handover Plans:** If a plan includes post-handover payments, format as:
`XX% on booking / XX% during construction / XX% on handover / XX% post-handover over X years`

---

## Key Features Section (Highlight Cards)

**Generate 3 feature cards based on brochure content:**

For each card:
- **Title** (generate) 25-50 characters
- **Description** (generate) 80-180 characters

**Feature categories to consider:**
- Location/Address prestige (SZR address, waterfront, downtown)
- Views (panoramic, sea, marina, skyline, garden)
- Amenity access (direct beach, marina berths, retail podium)
- Lifestyle (resort-style, urban convenience, family-friendly)
- Design (branded interiors, smart home, private pools/cinemas)
- Connectivity (metro access, airport proximity)

---

## Amenities Section (Why You Will Love This Place)

**Section Label**: `Why you will love this place`

**Generate 4-6 amenity cards:**

For each card:
- **Title** (generate) 20-40 characters
- **Description** (generate) 60-100 characters

**3-TIER SCOPING RULE:**
- **TIER 1 - Inside residences:** maid's room, balcony, terrace, storage, private pool, private cinema
- **TIER 2 - Inside building:** lobby, gym, pool, spa, concierge, parking, co-working, lounges
- **TIER 3 - Within community:** parks, retail, marina, beach club, sports facilities

**EXTRACT from brochure. Common amenities include:**
- Swimming pools (infinity, lap, kids', leisure)
- Fitness facilities (gym, yoga studio, sports courts)
- Wellness (spa, sauna, meditation zones)
- Social spaces (residents' lounge, BBQ areas, picnic areas)
- Children's facilities (play areas, kids' pool)
- Business (co-working, meeting rooms)
- Convenience (retail podium, concierge, valet, EV charging)
- Outdoor (landscaped gardens, jogging tracks, cycling paths)
- Waterfront (beach access, marina, water sports)

**EXCLUDE:** Views, large windows, location descriptions, landscaping aesthetics, future hotels, marketing adjectives

---

## Floor Plans Section

**H2 Header**: `Floor Plans` or `Explore [Project Name] Floor Plans`

**Floor Plan Table** (EXTRACT from brochure):

| Property Type | Living Area | Starting Price |
|---------------|-------------|----------------|
| Studio | from XXX sq. ft. | AED XXX,XXX or Upon request |
| 1BR Apartment | from XXX sq. ft. | AED X,XXX,XXX or Upon request |
| 2BR Apartment | from X,XXX sq. ft. | AED X,XXX,XXX or Upon request |
| 3BR Duplex | from X,XXX sq. ft. | AED X,XXX,XXX or Upon request |
| 4BR Penthouse | from X,XXX sq. ft. | AED X,XXX,XXX or Upon request |
| XBR Villa | from X,XXX sq. ft. | AED X,XXX,XXX or Upon request |

**DEDUPLICATION RULES:**
- If multiple variants of same bedroom count exist (e.g., 2BR Type A, 2BR Type B), merge into single row
- Use smallest size for "from" value
- Use lowest starting price among variants

**MISSING DATA RULES:**
- If sizes exist but prices do not → show sizes, display "Upon request" for price
- If prices exist but sizes do not → show prices, display "TBA" for size
- NEVER fabricate sizes or prices

---

## Gallery Section

**H2 Header**: `Gallery` or `View photos of [Project Name]`

**Tabs**: Exteriors | Interiors

**Static** - Images managed by content team

---

## About Developer Section

**Section Label**: `About developer` or `About the developer`

**Developer Description** (generate) 200-400 characters | ~35-70 words

Write 2-3 factual sentences covering:
- Years active / establishment date
- Total delivered square footage or unit count
- Market positioning (luxury, master developer, etc.)
- Design/construction philosophy
- Notable projects in portfolio
- Geographic presence

---

## Location & Advantages Section

**Section Label**: `Location & Advantages`

**H2 Header** (generate) 50-70 characters
Format options:
- `One of the most prestigious areas in [region]`
- `Prime [Area] Living, Unmatched Convenience`
- `[Location] – A Sophisticated Urban Hub in [City Region]`
- `[Location] – [Region's] Premier [Waterfront/Urban] Destination`

**Location Overview** (generate) 400-700 characters | ~70-130 words

Write 2 paragraphs:

**Paragraph 1:**
- Project's position within broader district/masterplan
- Total area/waterfront length (if applicable)
- General area character (urban, resort, waterfront)
- Connection to main roads/highways/bridges

**Paragraph 2:**
- Key attractions and lifestyle features nearby
- Beaches, parks, entertainment
- Retail and dining options
- Walkability features

---

## Nearby Facilities Section

**Generate content for 3 categories:**

### Social Facilities
**Introduction** (generate) 150-250 characters
Brief description of entertainment, dining, and leisure options.

**Nearby Locations** (generate 3-4 items):
Format: `[Location Name] — [X] minutes by car`

Examples: malls, beaches, theme parks, water parks, golf courses, marinas, entertainment venues

### Education & Medicine
**Introduction** (generate) 150-250 characters
Brief description of educational and healthcare accessibility.

**Nearby Institutions** (generate 3-4 items):
Format: `[Institution Name] — [X] minutes by car`

Examples: nurseries, schools, universities, hospitals, clinics, medical centers

### Culture
**Introduction** (generate) 150-250 characters
Brief description of cultural and lifestyle offerings.

**Nearby Establishments** (generate 3-4 items):
Format: `[Establishment Name] — [X] minutes by car`

Examples: museums, galleries, opera houses, heritage sites, cultural centers

**CRITICAL:** All drive times must be Google Maps verified. Do NOT estimate or fabricate.

---

## FAQ Section

**H2 Header**: `FAQ` or `FAQ: Frequently Asked Questions`

**Total: 10-12 FAQs | Core: 6 mandatory | Unique: 4-6 project-specific**

### TIER 1: CORE FAQs (Always include these 6)

| # | Question Template | Answer Source |
|---|-------------------|---------------|
| 1 | Where is [Project Name] located? | Location section, area details |
| 2 | Who is the developer of [Project Name]? | Developer name + 1-2 notable projects |
| 3 | What types of properties are available at [Project Name]? | Floor plan types from brochure |
| 4 | What is the starting price at [Project Name]? | Starting price or "Contact for pricing" |
| 5 | What payment plans are available for [Project Name]? | All payment plan options with breakdowns |
| 6 | When will [Project Name] be completed? | Handover date(s) |

### TIER 2: UNIQUE FAQs (Generate 4-6 based on brochure content)

**Scan brochure for these triggers:**

| If brochure mentions... | Generate FAQ like... |
|-------------------------|----------------------|
| Freehold ownership | "Can foreigners buy property at [Project]?" |
| Golden Visa / Premium Residency eligibility | "What visa benefits are available for [Project] buyers?" |
| Investment positioning | "Is [Project] a good investment?" |
| Area/lifestyle benefits | "Is [Location] a good place to live?" |
| Branded/designer interiors | "What is the [Designer Name] design concept at [Project]?" |
| Specific wellness features | "What wellness facilities are included at [Project]?" |
| Smart home / technology | "What smart home features come with [Project] units?" |
| Waterfront/beach/marina access | "Does [Project] have direct beach/marina access?" |
| Unique architectural feature | "What is the [specific feature] at [Project]?" |
| Multiple property categories | "What is the difference between [Type A] and [Type B] at [Project]?" |
| Specific view types | "What views can residents expect from [Project]?" |
| Upcoming infrastructure | "How will [new development] benefit [Project] residents?" |
| Rental/ROI data | "What are the expected rental yields at [Project]?" |
| Service charges | "What are the service charges at [Project]?" |

### FAQ ANSWER GUIDELINES

| Guideline | Description |
|-----------|-------------|
| Length | 60-120 words per answer |
| Tone | Informative, factual – not salesy |
| Structure | Direct answer first, then supporting detail |
| Data | Include specific numbers (sizes, prices, distances, dates) |
| No fluff | Avoid "absolutely" / "definitely" / "perfect for" |
| Project name | Each question AND answer must mention the project name |

### FAQs TO AVOID

| Bad FAQ | Why it's bad |
|---------|--------------|
| "Is [Project] a good investment?" without data | Too generic if not backed by yield/appreciation figures |
| "What amenities does [Project] offer?" | Too broad – split into specific amenity questions |
| "Why should I buy in [Project]?" | Salesy framing |
| "Is [Project] family-friendly?" | Yes/no question, not informative |
| "What are the benefits of living in [Project]?" | Vague, no specific angle |
| "How accessible is [Project]?" | Too vague – use specific distance/transport FAQs |

---

## Total Character Count

**All generated sections combined: 4,000-7,000 characters | Target: 5,500 | ~725-1,270 words**

---

## Regional Rules

### Dubai
- Transfer fee: **4%** to DLD (Dubai Land Department)
- Golden Visa: Reference if starting price ≥ AED 2,000,000
- Service charges: Quote per sq.ft per year if available
- Metro connectivity: Always mention nearest metro station if applicable
- Currency: AED with USD equivalent

### Abu Dhabi
- Transfer fee: **2%** (NOT 4%)
- Golden Visa: Reference if starting price ≥ AED 2,000,000
- Freehold zones: Yas Island, Saadiyat Island, Al Reem Island, Al Raha Beach, Al Maryah Island, Hudayriyat Island, Masdar City
- Currency: AED with USD equivalent

### Ras Al Khaimah
- Transfer fee: **2%**
- Highlight Dubai proximity (45-60 min drive)
- Reference Wynn Casino development (demand driver)
- Note lower price per sq.ft vs. Dubai
- Reference RAK tourism growth
- Currency: AED with USD equivalent

### Saudi Arabia
- Currency: **SAR** (Saudi Riyal) with USD equivalent
- Reference Premium Residency eligibility for qualifying investments
- Note freehold ownership zones
- Do NOT generate Vision 2030 content (static section)
- Currency: SAR with USD equivalent

---

## Style Guidelines

### Tone
Professional, confident, informative. Balance investment appeal with lifestyle benefits. Not salesy or hyperbolic.

### Formatting Rules
- No bullet points within paragraphs (convert to flowing prose)
- Use en-dash (–) for Location section attraction lists
- Include specific numbers: unit counts, sizes, prices, drive times, yields
- Avoid superlatives without substantiation
- No exclamation marks
- Write "sq. ft." (not "square feet" or "sqft")
- Write "sqm" for square meters

### Terminology
- Use "residents" when describing lifestyle
- Use "investors and end-users" when addressing target audience
- Reference "capital appreciation" and "rental yields" for investment content
- Use "handover" not "completion" for delivery dates
- Use "freehold" when describing ownership in designated zones

### Currency Formatting
- Primary currency first, USD equivalent in parentheses
- Millions: `AED X.XXM (USD X.XM)` or `SAR X.XM (USD XXXK)`
- Thousands: `AED XXX,XXX` or `AED XXXK`
- Always include both AED/SAR and USD for prices

### Data Handling
- If brochure lacks specific data (price, yield, payment plan), **omit rather than fabricating**
- Location drive times must be **Google Maps verified**
- ROI/yield figures should reference authoritative sources (Property Monitor, etc.)
- Cross-reference amenities from both marketing copy and floor plans/site plans
- When data conflicts between sources, use the brochure as primary source

---

## Input Data Requirements

For the automation system to generate content, the following must be extracted from the brochure:

### Required Data
- [ ] Project name
- [ ] Developer name
- [ ] Location (area, district, emirate/city)
- [ ] Property types (apartments, villas, penthouses, etc.)
- [ ] Bedroom configurations (all types)
- [ ] Size range (smallest and largest in sq. ft.)
- [ ] Starting price
- [ ] Payment plan(s) – ALL options with full breakdown
- [ ] Handover date(s)
- [ ] Amenities list

### Optional Data (include if available)
- [ ] Total unit count
- [ ] Number of floors/buildings
- [ ] Interior designer/brand name
- [ ] Service charges per sq. ft.
- [ ] Expected rental yield
- [ ] ROI projections
- [ ] Nearby landmarks with distances
- [ ] Unique features or selling points

---

## Output Format

Generated content should be delivered in structured format with clear section labels:

```
## SEO
Title: [generated title]
Meta-description: [generated meta-description]
URL slug: [generated slug]

## Hero Section
H1: [generated header]
Subtitle: [generated subtitle]
Investment Stats:
- [stat 1]
- [stat 2]
- [stat 3]

## About Section
H2: [generated header]
Content: [generated paragraph]

[... continue for all sections ...]
```

---

## Validation Checklist

Before finalizing generated content, verify:

- [ ] All character counts within specified ranges
- [ ] Payment plan percentages sum to 100% (each plan)
- [ ] No fabricated data (prices, sizes, distances)
- [ ] Project name mentioned in all FAQ questions AND answers
- [ ] Currency formatted correctly for region
- [ ] Regional rules applied (transfer fees, visa eligibility)
- [ ] No bullet points in prose paragraphs
- [ ] No exclamation marks
- [ ] All drive times are realistic/verified
- [ ] Unit types match brochure exactly
