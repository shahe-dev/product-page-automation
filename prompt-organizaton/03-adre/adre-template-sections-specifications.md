# ADRE Template Section Specifications

**Template type:** `adre`
**Target site:** abu-dhabi.realestate
**Purpose:** Abu Dhabi ready/secondary market properties
**Last updated:** 2026-02-03

---

## Section Overview

| # | Section | Type | Fields |
|---|---------|------|--------|
| 1 | SEO | GENERATED | 4 |
| 2 | Hero | MIXED | 10 |
| 3 | About | MIXED | 12 |
| 4 | Gallery | STATIC | 0 |
| 5 | Property Types & Floor Plans | EXTRACTED | ~15 (dynamic) |
| 6 | Amenities | MIXED | 12 |
| 7 | Get a Free Consultation | STATIC | 0 |
| 8 | About the Developer | MIXED | 3 |
| 9 | About Company | STATIC | 0 |
| 10 | Economic Appeal | MIXED | 10 |
| 11 | Payment Plan | EXTRACTED | 4 |
| 12 | Download Brochure | STATIC | 0 |
| 13 | Location | MIXED | 14 |
| 14 | Project Materials | STATIC | 0 |
| 15 | FAQ | GENERATED | 24 (12 pairs) |
| 16 | Similar Projects | STATIC | 0 |

---

## 1. SEO Section

All GENERATED fields for search engine optimization.

### 1.1 Meta Title
**Type:** GENERATED
**Characters:** 50-60
**Format:** `[Project Name] by [Developer] | [Location], Abu Dhabi`

### 1.2 Meta Description
**Type:** GENERATED
**Characters:** 155-165
**Content:** project type, developer, location, starting price, payment plan, handover date

### 1.3 URL Slug
**Type:** GENERATED
**Format:** `[project-name-location-abu-dhabi]` (lowercase-hyphens)

### 1.4 Image Alt Tag
**Type:** GENERATED
**Characters:** 80-125
**Content:** Factual description, no adjectives. Include project name, property type, developer, location.

---

## 2. Hero Section

Mix of GENERATED, EXTRACTED, and STATIC fields.

### 2.1 H1 Header
**Type:** GENERATED
**Characters:** 50-70
**Format:** `[Project Name] by [Developer] in [Location], Abu Dhabi`
Alternate: `[Project Name] by [Developer], Abu Dhabi`

### 2.2 Marketing H2 (Tagline)
**Type:** GENERATED
**Characters:** 40-60
**Content:** One marketing tagline for the project. Example: "Modern waterfront living crafted by [Developer] on [Location]"

### 2.3 Property Type Tags
**Type:** EXTRACTED
**Content:** Based on PDF extraction - display as clickable tags (e.g., Apartments, Penthouses, Villas, Townhouses)

### 2.4 Developer Logo
**Type:** STATIC
**Content:** Links to developer page. Do not generate.

### 2.5 Location Link
**Type:** GENERATED
**Content:** Area name text that links to area page.

### 2.6 Starting Price
**Type:** EXTRACTED
**Format:** `AED X.XXM` + optional USD equivalent `(USD XXXK)`

### 2.7 Booking Fee
**Type:** EXTRACTED
**Format:** `X%`

### 2.8 Handover Date
**Type:** EXTRACTED
**Format:** `QX 20XX` or `QX 20XX / QX 20XX` for phased projects

### 2.9 CTA Buttons
**Type:** STATIC
**Content:** Property Inquiry, Download Brochure. Do not generate.

### 2.10 License/Project Number
**Type:** STATIC
**Content:** Do not generate.

---

## 3. About Section

### 3.1 About H2
**Type:** GENERATED
**Characters:** 30-60
**Options:**
- `About [Project Name]`
- `Modern waterfront living crafted by [Developer] on [Location]`
- `First [USP] Residences on [Location]` (for branded/unique projects)

### 3.2 About Description
**Type:** HYBRID
**Characters:** 600-900 | Target: 750 | ~110-165 words

Write exactly 1 paragraph covering:
- Project name and building structure (floors/towers if available)
- Developer name
- Location (island/district/area)
- Unit types and bedroom mix (list ALL floor plan types from brochure)
- Size range in sq.ft (or sqm with sq.ft in parentheses)
- Interior design approach (materials, finishes) if specified in brochure
- Key architectural features
- Core lifestyle/design positioning

**Rule:** Unit type breakdown must match the floor plan types exactly as provided in the brochure.

### 3.3 Project Card (All EXTRACTED)

| Field | Type | Format |
|-------|------|--------|
| Developer | EXTRACTED | Links to developer page |
| Area from | EXTRACTED | Smallest floor plan in sq.ft |
| Apartments | EXTRACTED | Bedroom range (e.g., `1-3BR`) |
| Penthouses | EXTRACTED | Bedroom config if applicable |
| Villas | EXTRACTED | Bedroom range if applicable |
| Townhouses | EXTRACTED | Bedroom range if applicable |
| Total Units | EXTRACTED | If provided in brochure |
| Payment Plan | EXTRACTED | Format: `X/X` (e.g., `50/50`, `65/35`) |

### 3.4 Project Materials Link
**Type:** STATIC
**Content:** Do not generate.

---

## 4. Gallery Section

**Type:** STATIC
Do not generate. Images managed by content team.

---

## 5. Property Types & Floor Plans Section

### 5.1 Section Header
**Type:** STATIC
**Content:** "Property Types & Floor Plans"

### 5.2 Floor Plans Table
**Type:** EXTRACTED

| Column | Content | Format |
|--------|---------|--------|
| Property type | Unit description | `X bedroom Apartments` / `X bedroom Penthouse` / `X bedroom Villa` |
| Living area | Size | `from X,XXX sq.ft` |
| Starting price | Price | `AED X,XXX,XXX` or `Ask for Price` |

**DEDUPLICATION RULES:**
- If multiple variants of same bedroom count exist, merge into single line with size range
- Use lowest starting price among variants

**MISSING DATA RULES:**
- If sizes exist but prices do not: list sizes, show "Ask for Price"
- If prices exist but sizes do not: list prices, show "TBA" for size
- NEVER fabricate sizes or prices

### 5.3 Floor Plan Details (Expandable)
**Type:** EXTRACTED
- Suite: `X,XXX sq.ft`
- Balcony: `XXX sq.ft`
- OR for villas:
  - Ground floor: `X,XXX sq.ft`
  - First floor: `X,XXX sq.ft`

### 5.4 Download Floor Plans CTA
**Type:** STATIC
**Content:** Do not generate.

---

## 6. Amenities Section

### 6.1 Amenities H2
**Type:** GENERATED
**Characters:** 30-50
**Format:** `Amenities of [Project Name]`

### 6.2 Featured Amenities (2-3 highlighted)
**Type:** GENERATED

For each featured amenity:
- **H3 Title:** 30-50 characters
- **Description:** 150-250 characters

### 6.3 Amenities List
**Type:** HYBRID
**Count:** 8-14 items
**Format:** Short bullet points (<=40 characters each)

**3-TIER SCOPING RULE:**
- TIER 1: Inside residences (maid room, balcony, terrace, storage)
- TIER 2: Inside the building (lobby, gym, pool, spa, concierge, parking)
- TIER 3: Within community/masterplan (parks, retail, marina, beach club)

**EXCLUDE:** Views, large windows, location descriptions, landscaping, future hotels, marketing adjectives

**Valid examples:**
- Infinity pool with sun deck
- Separate kids' pool and play areas
- Indoor and outdoor fitness studios
- Yoga and meditation zones
- Private indoor and outdoor cinema
- Residents' lounge and conference room
- Landscaped gardens and water features
- BBQ and family picnic areas
- Dedicated parking with valet and EV charging
- 24/7 concierge and security

### 6.4 Download Brochure CTA
**Type:** STATIC
**Content:** Do not generate.

---

## 7. Get a Free Consultation Section

**Type:** STATIC
Form with: Name, Phone, E-Mail, Message fields. CTA: PROPERTY INQUIRY.
Do not generate.

---

## 8. About the Developer Section

### 8.1 Developer H2
**Type:** STATIC
**Content:** "About the developer"

### 8.2 Developer Description
**Type:** GENERATED
**Characters:** 150-300
**Content:** 2-3 factual sentences. Years active, notable projects, development scope. Link to developer page.

### 8.3 Developer Logo
**Type:** STATIC
**Content:** Do not generate.

### 8.4 Interest-free Installments Link
**Type:** STATIC
**Content:** Do not generate.

---

## 9. About Company Section

**Type:** STATIC
Contains company information. Do not generate.

---

## 10. Economic Appeal Section

### 10.1 Economic Appeal H2
**Type:** GENERATED
**Characters:** 40-60
**Format:** `Economic Appeal of [Project Name]`

### 10.2 Intro Paragraph
**Type:** GENERATED
**Characters:** 400-600

Write 1 paragraph covering:
- Market positioning and investment thesis
- Location advantages for investors
- Limited inventory/exclusivity if applicable
- Long-term value drivers

### 10.3 Key Stats Cards
**Type:** EXTRACTED (where available)

| Stat | Source |
|------|--------|
| Handover | EXTRACTED: `QX 20XX` |
| ROI | VERIFIED: `X-X%` (from market verification, NOT PDF) |
| Area from | EXTRACTED: `X,XXX-X,XXX sq.ft` |
| Residences | EXTRACTED: Bedroom types |

### 10.4 For Rent / To Rent Subsection
**Type:** GENERATED
**Characters:** 150-250
**Content:** Rental returns potential, target tenant demographics, demand drivers

### 10.5 For Resale Subsection
**Type:** GENERATED
**Characters:** 150-250
**Content:** Capital appreciation potential, exclusivity factors, market positioning

### 10.6 For Living Subsection
**Type:** GENERATED
**Characters:** 150-250
**Content:** Target resident profile (families, professionals, executives), lifestyle benefits, proximity to key amenities (schools, healthcare, business hubs), services included (concierge, housekeeping if applicable)

### 10.7 CTA
**Type:** STATIC
**Content:** "Get a free consultation from sales team" - do not generate.

---

## 11. Payment Plan Section

### 11.1 Payment Plan H2
**Type:** GENERATED
**Characters:** 40-70
**Format:** `Attractive [X/X] Payment Plan from [Developer]`

### 11.2 Payment Plan Breakdown
**Type:** EXTRACTED

| Field | Format |
|-------|--------|
| Down Payment | `X%` |
| On Construction | `X%` |
| On Handover | `X%` |

**CRITICAL RULE:** Percentages MUST sum to 100%

---

## 12. Download Brochure Section

**Type:** STATIC
Form section. Do not generate.

---

## 13. Location Section

### 13.1 Location H2
**Type:** STATIC
**Content:** "Location"

### 13.2 Location Overview
**Type:** GENERATED
**Characters:** 400-700

Write 2 paragraphs:

**Paragraph 1:**
- Project's position within broader district
- General area character
- Connection to main roads/bridges

**Paragraph 2:**
- Key attractions and lifestyle features
- Beaches, parks, sports facilities
- Dining, entertainment options

### 13.3 Area Card

#### Style
**Type:** GENERATED
**Examples:** `Island`, `Waterfront`, `Urban`

#### Focal Point
**Type:** GENERATED
**Examples:** `Hudayriyat Bridge`, `Sheikh Khalifa Bin Zayed St`

#### Accessibility
**Type:** GENERATED
**Format:** `[X]min` + destination name
**Required:** Zayed International Airport

#### Shopping (2-4 items)
**Type:** GENERATED
**Format:** `[X]min` + mall/shopping destination name
Round times to nearest 5 minutes.

#### Entertainment (4-6 items)
**Type:** GENERATED
**Format:** `[X]min` + attraction name
Round times to nearest 5 minutes.

**Sources:** Google Maps verified. Do NOT estimate or fabricate drive times.

---

## 14. Project Materials Section

**Type:** STATIC
- Brochure cover image + download link
- Floor Plans cover image + download link
Do not generate.

---

## 15. FAQ Section

### 15.1 FAQ H2
**Type:** STATIC
**Content:** "FAQ"

### 15.2 FAQ Pairs
**Type:** GENERATED
**Total:** 10-12 FAQs | Core: 6 mandatory | Unique: 4-6 project-specific

---

### TIER 1: CORE FAQs (Always include these 6)

| # | Question Template | Answer Source |
|---|-------------------|---------------|
| 1 | Where is [Project Name] located? | Location section, area details |
| 2 | Who is the developer of [Project Name]? | Developer name + notable projects |
| 3 | What types of properties are available at [Project Name]? | Floor plan types from brochure |
| 4 | How much do residences in [Project Name] cost? | Starting prices from brochure |
| 5 | What payment plans are available for [Project Name]? | Payment plan details |
| 6 | When will [Project Name] be completed? | Handover date |

---

### TIER 2: UNIQUE FAQs (Generate 4-6 based on brochure content)

**Question triggers -- scan brochure for:**

| If brochure mentions... | Generate FAQ like... |
|-------------------------|----------------------|
| Freehold ownership | "Can a foreigner buy property in [Project]?" |
| Residency eligibility | "Can I obtain residency status if I buy a property in [Project]?" |
| Golden Visa eligibility | "What visa can I get if I buy property at [Project]?" |
| Investment positioning | "Is [Project] a good investment?" |
| Area/lifestyle benefits | "Is [Area Name] a good place to live?" |
| Branded/designer interiors | "What is the [Designer Name] design concept in [Project]?" |
| Specific wellness features | "What wellness facilities are included in [Project]?" |
| Smart home / technology | "What smart home features come with [Project] apartments?" |
| Waterfront/beach access | "Does [Project] have direct beach/waterfront access?" |
| Unique architectural feature | "What is the [specific feature] at [Project]?" |
| Multiple property categories | "What is the difference between [Type A] and [Type B] at [Project]?" |
| Specific view types | "What views can residents expect from [Project]?" |
| Upcoming infrastructure | "How will [new facility] benefit [Project] residents?" |

---

### FAQ Answer Guidelines

| Guideline | Description |
|-----------|-------------|
| Length | 60-120 words per answer |
| Tone | Informative, factual -- not salesy |
| Structure | Direct answer first, then supporting detail |
| Data | Include specific numbers (sizes, prices, distances, dates) |
| No fluff | Avoid "absolutely" / "definitely" / "perfect for" |
| Project name | Each question AND answer MUST mention the project name |

---

### FAQs to Avoid

| Bad FAQ | Why |
|---------|-----|
| "Is [Project] a good investment?" without substance | Too generic if not backed by data |
| "What amenities does [Project] offer?" | Too broad -- split into specific questions |
| "Why should I buy in [Project]?" | Salesy framing |
| "Is [Project] family-friendly?" | Yes/no question, not informative |
| "What are the benefits of living in [Project]?" | Vague, no specific angle |

---

## 16. Similar Projects Section

**Type:** STATIC
Auto-populated based on area/property type. Do not generate.

---

## Total Character Count

**All generated sections combined:** 3,500-6,500 | Target: 5,000 | ~630-1,180 words

---

## Style Guidelines

**Tone:** Professional, confident, informative. Not salesy or hyperbolic.

**Formatting Rules:**
- No bullet points within paragraphs (convert to flowing prose)
- Include specific numbers: unit counts, sizes, prices, drive times, yields
- Avoid superlatives without substantiation
- No exclamation marks
- Write "sq.ft" and "sqm" (not "square feet" or "square meters")

**Terminology:**
- Use "residents" not "homeowners" or "buyers" when describing lifestyle
- Use "investors and end-users" when addressing target audience
- Reference "capital appreciation" and "rental yields" for investment content
- Use "handover" not "completion" for delivery dates
- Use "freehold" when describing ownership in designated investment zones

**Abu Dhabi-Specific Rules:**
- Transfer fee: Abu Dhabi charges **2%** (NOT 4% -- that is Dubai)
- Golden Visa: Only reference if starting price >= AED 2,000,000
- Freehold zones: Yas Island, Saadiyat Island, Al Reem Island, Al Raha Beach, Al Maryah Island, Hudayriyat Island, Masdar City, and others per Law No. 19 of 2005

**Data Handling:**
- If brochure lacks specific data (price, yield, payment plan), omit that detail rather than fabricating
- Location drive times must be Google Maps verified
- Cross-reference amenities from both marketing copy and floor plans/site plans in brochure
