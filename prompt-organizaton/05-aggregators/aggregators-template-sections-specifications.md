# Aggregators Template Sections - Generated vs. Static Specifications

## Overview

This specification defines content generation requirements for the company aggregator project pages across 24+ regional domains:

| Region | Domains | Currency |
|--------|---------|----------|
| Dubai | sobha-central.ae, dubaimaritime-city.ae, dubai-creek-living.ae, dubaihills-property.ae, dubaislands.ae, rashid-yachts-marina.ae, city-walk-property.ae, luxury-villas-dubai.ae, tilalalghaf-maf.ae, the-valley-villas.ae, sharjah-residences.ae, urban-luxury.penthouse.ae, urbanvillas-dubaisouth.ae, difc-residences.ae, dubai-harbour-property.ae, luxury-collection.ae, bloom-living.ae | AED (USD) |
| Abu Dhabi | capital-luxury.ae | AED (USD) |
| Ras Al Khaimah | ras-al-khaimah-properties.ae | AED (USD) |
| Saudi Arabia | saudi-estates.com | SAR (USD) |

---

## Static Elements (NEVER generate)

- All forms (consultation, callback, brochure download, floor plan download)
- All CTAs and buttons ("Book Now", "Register your Interest", "Get Expert Advice", "Learn more")
- Online consultation / Zoom booking sections
- Developer logos
- Gallery images
- "3 options after Handover" / "After completion, you have 3 options" section
- the company company sections (stats, awards, testimonials, media mentions, team photos)
- "6 Steps to Success" / "6 Steps to Property Success" section
- "What Clients Speak about Us" testimonials carousel
- Price statistics cards showing Property Monitor data (666 -> 856 USD/sq.m, etc.)
- Map with facility pins
- Footer sections
- Vision 2030 context blocks (Saudi Arabia sites)
- Agent/expert cards (photo, name, rating)
- "Elite Developer Network" section
- "Featured in Leading Media" section
- "Explore another projects for sale" related projects section

---

## SEO

**Meta Title** (GENERATED) 50-60 characters
Format varies by region:
- Dubai: `[Project Name] by [Developer] in [Location], Dubai`
- Abu Dhabi: `[Project Name] by [Developer] | [Location], Abu Dhabi`
- RAK: `[Project Name] at [Location] | Ras Al Khaimah`
- Saudi: `[Project Name] by [Developer] in [City], Saudi Arabia`

**Meta Description** (GENERATED) 155-165 characters
Include: project type, developer, location, starting price, payment plan ratio, handover date, one key differentiator.

**URL Slug** (GENERATED)
Format: `[project-name]-[location]` (lowercase-hyphens)

**Image Alt Tag** (GENERATED) 80-125 characters
Factual description, no marketing adjectives.

---

## Hero Section

**H1 Header** (GENERATED) 50-70 characters
Format options:
- `[Project Name] at [Location] on SZR, Dubai`
- `[Project Name] -- [Property Type] at [Location]`
- `Invest in [Project Name]: [Value Proposition]`

**Hero Subtitle** (GENERATED) 80-150 characters
Investment and lifestyle overview. Single sentence stating the project's primary value proposition.
Examples:
- "The last tower at Sobha Central -- premium launch with top ROI potential and strong capital growth."
- "Enjoy the exclusive island living in thoughtfully designed residences."
- "The world's first healthy-living island"

**Hero Investment Stats** (HYBRID) 3 bullet points
Extract from brochure and format as investment-focused bullets:
- ROI bullet: "High projected ROI in this high-growth area" or "Projected ROI of X% in this promising area"
- Price bullet: "AED X.XXM (USD XXXK) Starting property price"
- Capital gains bullet: "~ +XX% Projected annual capital gains"

**Quick Info Cards** (EXTRACTED)
| Field | Format |
|-------|--------|
| Starting Price | `AED X.XXM (USD XXXK)` or `SAR X.XM (USD XXXK)` |
| Payment Plan | `XX/XX` (e.g., 60/40, 50/50, 80/20) |
| Handover | `QX 20XX` |

---

## About Section

**Section Label**: `About [Project Name]` or `About [Project Name] by [Developer]`

**About H2** (GENERATED) 50-80 characters
Format options:
- `[Project Name] -- A Prime Address on [Road/Location]`
- `[Project Name]: Pinnacle of Luxury Living`
- `Holistic living on a private island sanctuary`

**About Paragraph** (HYBRID) 400-650 characters | ~70-120 words

Write 1 paragraph covering:
- Project identity: building type, floor count, number of units
- Property types available (apartments, villas, penthouses, duplexes, townhouses, studios)
- Bedroom configurations -- list ALL types from brochure using exact naming
- Unit count (if provided)
- Key features (views, balconies, terraces, staff quarters)
- Amenity highlights (brief)
- Location positioning

**CRITICAL:** Unit type breakdown must match floor plan types exactly as provided in brochure. Use "+1" notation for maid's room units.

---

## Project Details Card

**All data EXTRACTED from brochure:**

| Field | Format |
|-------|--------|
| Developer | Developer name (links to developer page) |
| Location | `[Area], [District/Road]` or `[City], [Country]` |
| Payment Plan | `XX/XX` |
| Area | `XXX sq. ft. -- X,XXX sq. ft.` or `From X,XXX sq. ft.` |
| Property Type | `Apartments` / `Villas` / `Penthouses` / etc. (comma-separated) |
| Bedrooms | `X-XBR` or `Studio, 1-4BR` |

---

## Economic Appeal Section

**Section Label**: `Economic Appeal` or `Investment Appeal`

**Economic Appeal H2** (GENERATED) 40-60 characters
Format options:
- `Land a Highly Profitable Investment`
- `Investing in the Future`
- `When Health Is Wealth`
- `Tap into [City's] Economic Engines`

**Economic Appeal Paragraph** (GENERATED) 400-650 characters | ~70-120 words

Write 1-2 paragraphs covering:
- Location advantages (address prestige, connectivity, infrastructure)
- Market drivers (tourism, business hubs, population growth)
- Rental returns potential with yield percentage range
- Capital appreciation outlook with percentage if available
- Tenant demand factors
- Service charges per sq.ft (if available)
- Developer reputation and build quality

---

## Payment Plan Section

**Section Label**: `Payment Plan`

**Payment Plan H2** (GENERATED) 40-60 characters
Format: `Easy Installments: [XX/XX] by [Developer]`

**Payment Plan Description** (GENERATED) 100-200 characters
Brief explanation of payment structure.
Example: "Secure your purchase with a 20% up-front payment, then pay 40% during construction, and the final 40% upon transfer."

**Payment Plan Breakdown** (EXTRACTED)
| Stage | Percentage |
|-------|------------|
| For Booking / Down Payment | XX% |
| On Construction | XX% |
| On Handover (QX 20XX) | XX% |

**VALIDATION RULE:** Percentages MUST sum to exactly 100%.

---

## Key Features Section (Highlight Cards)

**Generate 3 feature cards** (GENERATED)

For each card:
- **Title** (GENERATED) 25-50 characters
- **Description** (GENERATED) 80-180 characters

**Feature categories to consider:**
- Location/Address prestige (SZR address, waterfront, downtown)
- Views (panoramic, sea, marina, skyline, garden)
- Amenity access (direct beach, marina berths, retail podium)
- Lifestyle (resort-style, urban convenience, turn-key luxury)
- Design (branded interiors, smart home, private pools)
- Connectivity (metro access, airport proximity)
- Community features (owners club, wellness programs)

Example cards from live pages:
- "Direct Amenity Connections" -- "Residents have immediate access to cafes, shops, and lifestyle services thanks to the clubhouse, office spaces, and a full retail podium."
- "Panoramic Views" -- "Select apartments grant unhindered views of the Arabian Gulf, Downtown, JLT, and Dubai Marina, promising a refined daily existence."
- "Sheikh Zayed Road Address" -- "Long-term investment strength and daily convenience are delivered by exceptional connection at Dubai's most prominent corridor."
- "Panoramic windows" -- "Enjoy stunning views of the surrounding landscape, enhancing every moment with a deeper sense of immersion."
- "Sky pools" -- "Elevate your experience with sky pools, offering stunning panoramic views of the surrounding cityscape and coastline."
- "Prestigious location" -- "The prime location of Dubai Islands offers quick access to major landmarks and luxury entertainment venues."

---

## Amenities Section ("Why you will love this place")

**Section Label**: `Why you will love this place`

**Generate 4-6 amenity cards** (GENERATED/HYBRID)

For each card:
- **Title** (GENERATED) 20-40 characters
- **Description** (GENERATED) 60-100 characters

**3-TIER SCOPING RULE:**
- **TIER 1 - Inside residences:** maid's room, balcony, terrace, storage, private pool, private cinema
- **TIER 2 - Inside building:** lobby, gym, pool, spa, concierge, parking, co-working, lounges
- **TIER 3 - Within community:** parks, retail, marina, beach club, sports facilities

**EXTRACT from brochure. Common amenities include:**
- Swimming pools (infinity, lap, kids', leisure, sky pools)
- Fitness facilities (gym, yoga studio, sports courts, fitness centre)
- Wellness (spa, sauna, meditation zones, mind & body pavilion)
- Social spaces (residents' lounge, BBQ areas, picnic areas)
- Children's facilities (play areas, kids' pool)
- Business (co-working, meeting rooms)
- Convenience (retail podium, concierge, valet, EV charging)
- Outdoor (landscaped gardens, jogging tracks, cycling paths)
- Waterfront (beach access, marina, water sports)

**EXCLUDE:** Views, large windows, location descriptions, landscaping aesthetics, future hotels, marketing adjectives

Example amenity cards from live pages:
- "Swimming Pools" -- "A family-friendly pool, lap pool, Jacuzzi, and leisure pool."
- "Fitness centre" -- "Achieve your fitness goals in a state-of-the-art space."
- "Mind & Body Pavilion" -- "Yoga, meditation, mindfulness, Pilates -- discover a path to mental and spiritual well-being with the guidance of experienced instructors."

---

## Floor Plans Section

**H2**: `Floor Plans`

**Floor Plan Table** (EXTRACTED from brochure)

| Property Type | Living Area | Starting Price |
|---------------|-------------|----------------|
| Studio | from XXX sq. ft. | AED XXX,XXX or Upon request |
| 1BR Apartment | from XXX sq. ft. | AED X,XXX,XXX or Upon request |
| 2BR Apartment | from X,XXX sq. ft. | AED X,XXX,XXX or Upon request |
| 3BR Apartment | from X,XXX sq. ft. | AED X,XXX,XXX or Upon request |
| XBR Duplex | from X,XXX sq. ft. | AED X,XXX,XXX or Upon request |
| XBR Villa | from X,XXX sq. ft. | AED X,XXX,XXX or Upon request |

**DEDUPLICATION RULES:**
- If multiple variants of same bedroom count exist (e.g., 2BR Type A, 2BR Type B), merge into single row
- Use smallest size for "from" value
- Use lowest starting price among variants

**MISSING DATA RULES:**
- If sizes exist but prices do not -> show sizes, display "Upon request" for price
- If prices exist but sizes do not -> show prices, display "TBA" for size
- NEVER fabricate sizes or prices

---

## Gallery Section

**H2**: `Gallery`

**Tabs**: Exteriors | Interiors

**Static** - Images managed by content team, do not generate.

---

## Developer Section

**Section Label**: `About developer` or Developer logo display

**Developer Description** (GENERATED) 200-400 characters | ~35-70 words

Write 2-3 factual sentences covering:
- Years active / establishment date
- Total delivered square footage or unit count
- Market positioning (luxury, master developer, etc.)
- Design/construction philosophy (e.g., "Backward Integration" concept)
- Notable projects in portfolio
- Geographic presence

Example from live page:
"With more than 13 million square feet of delivered luxury real estate worldwide, Sobha Realty is a well-known developer. Sobha handles all design, construction, and quality control in-house using their groundbreaking 'Backward Integration' concept. This promises unwavering quality in all high-rise buildings and master-planned communities."

---

## Location & Advantages Section

**Section Label**: `Location & Advantages`

**Location H2** (GENERATED) 50-70 characters
Format options:
- `Prime SZR Living, Unmatched Convenience`
- `Designed for Elevated Living`
- `The Rise of a Premier Luxury Destination`
- `One of the most prestigious areas in [region]`

**Location Overview** (GENERATED) 400-700 characters | ~70-130 words

Write 1-2 paragraphs:

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
**Introduction** (GENERATED) 150-250 characters
Brief description of entertainment, dining, and leisure options.

**Nearby Locations** (GENERATED) 3-4 items
Format: `[Location Name] -- [X] minutes by car`

Examples: malls, beaches, theme parks, water parks, golf courses, marinas, entertainment venues

### Education & Medicine
**Introduction** (GENERATED) 150-250 characters
Brief description of educational and healthcare accessibility.

**Nearby Institutions** (GENERATED) 3-4 items
Format: `[Institution Name] -- [X] minutes by car`

Examples: nurseries, schools, universities, hospitals, clinics, medical centers

### Culture
**Introduction** (GENERATED) 150-250 characters
Brief description of cultural and lifestyle offerings.

**Nearby Establishments** (GENERATED) 3-4 items
Format: `[Establishment Name] -- [X] minutes by car`

Examples: museums, galleries, souks, heritage sites, cultural centers, landmarks

**CRITICAL:** All drive times must be Google Maps verified. Do NOT estimate or fabricate.

---

## FAQ Section

**H2**: `FAQ` or `FAQ: Frequently Asked Questions`

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
| Tone | Informative, factual -- not salesy |
| Structure | Direct answer first, then supporting detail |
| Data | Include specific numbers (sizes, prices, distances, dates) |
| No fluff | Avoid "absolutely" / "definitely" / "perfect for" |
| Project name | Each question AND answer must mention the project name |

### FAQs TO AVOID

| Bad FAQ | Why it's bad |
|---------|--------------|
| "Is [Project] a good investment?" without data | Too generic if not backed by yield/appreciation figures |
| "What amenities does [Project] offer?" | Too broad -- split into specific amenity questions |
| "Why should I buy in [Project]?" | Salesy framing |
| "Is [Project] family-friendly?" | Yes/no question, not informative |
| "What are the benefits of living in [Project]?" | Vague, no specific angle |
| "How accessible is [Project]?" | Too vague -- use specific distance/transport FAQs |

---

## Total Character Count

**All generated sections combined: 4,000-7,000 characters | Target: 5,500 | ~725-1,270 words**

---

## Regional Rules

### Dubai
- Transfer fee: **4%** to DLD (Dubai Land Department)
- Golden Visa: Reference if starting price >= AED 2,000,000
- Service charges: Quote per sq.ft per year if available
- Metro connectivity: Always mention nearest metro station if applicable
- Currency: AED with USD equivalent

### Abu Dhabi
- Transfer fee: **2%** (NOT 4%)
- Golden Visa: Reference if starting price >= AED 2,000,000
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

---

## Style Guidelines

### Tone
Professional, confident, informative. Balance investment appeal with lifestyle benefits. Not salesy or hyperbolic.

### Formatting Rules
- No bullet points within paragraphs (convert to flowing prose)
- Use en-dash (--) for Location section attraction lists
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
