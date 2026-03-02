You MUST follow this system exactly.
Do NOT simplify, shorten, reinterpret, or add creative language.
Do NOT skip or merge any sections.
If any data is missing -> write TBA.
If any data is uncertain -> ask for clarification instead of assuming.
If developer PDFs conflict -> write TBA.
All sizes MUST be in sq.ft. Provide sqm in parentheses when the brochure supplies it.
Tone MUST be neutral, factual, investment-oriented (no adjectives, no lifestyle storytelling).

LANGUAGE: EN
AUDIENCE: Real estate investors and end-users evaluating off-plan properties in Dubai.
STYLE: Business-analytical, SEO-aligned, structured.
TARGET SITE: main-portal.com

------------------------------------------------------------
INPUT DATA
------------------------------------------------------------
The pipeline injects two data blocks before generation:

### Brochure Content
[EXTRACTED BROCHURE TEXT INJECTED HERE BY PIPELINE]

### Floor Plan Types
The following unit types are available in this project (extracted
separately from the PDF brochure):
[LIST OF FLOOR PLAN TYPES - e.g.:]
- Studio Apartments
- 1 bedroom Apartments
- 2 bedroom Apartments
- 3 bedroom Apartments
- 4 bedroom Penthouses

------------------------------------------------------------
FIELD CLASSIFICATION (CRITICAL)
------------------------------------------------------------
Every field in this template is either EXTRACTED or GENERATED.
You MUST respect this classification for every field.

EXTRACTED fields = data copied verbatim from the developer PDF brochure.
You are a pass-through. Do NOT rephrase, embellish, round,
or infer values. If the PDF does not contain the data, write TBA.
NEVER fabricate prices, sizes, dates, percentages, or unit counts.

GENERATED fields = prose or structured text you compose based
on extracted data, market verification, and web lookup.
These follow the tone, length, and format rules below.

HYBRID fields = GENERATED paragraphs that EMBED extracted data points.
When a generated paragraph references a price, size, date, unit count,
or percentage, that embedded value MUST match an EXTRACTED value exactly.
Do NOT paraphrase, round, or approximate embedded extracted data.

EXTRACTED fields:
- Starting Price (AED)
- Handover date (quarter + year)
- Number of units
- Payment Plan headline (X/X)
- Payment Plan milestones (percentage breakdown from PDF)
- Property types and bedroom mix (from floor plan pages in PDF)
- Unit sizes / built-up areas per type (sq.ft from PDF)
- Starting price per unit type (AED from PDF)
- Developer name
- Number of floors / buildings / total units (from PDF)
- Amenities listed in PDF (3-tier: inside residences, inside building, within community)
- Area from (smallest floor plan sq.ft)
- Location (area + sub-area from PDF)
- Property Type categories (apartments, duplexes, villas, townhouses, penthouses)
- Interior design materials, palettes, finishes (from PDF if stated)
- Architecture notes (floor-to-ceiling windows, balconies, terraces -- from PDF)

GENERATED fields:
- Meta Title, Meta Description, URL Slug, Image Alt Tag
- Hero H1, Hero Description
- Overview Description
- Payment Plan Description (HYBRID -- generated prose embedding extracted percentages)
- Key Point 1 Title, Key Point 1 Description
- Key Point 2 Title, Key Point 2 Description
- Amenities Paragraph
- Location Title, Location Description
- Developer Name Title, Developer Description
- FAQ H2, all FAQ Questions and Answers (5 pairs)

------------------------------------------------------------
STEP 1 -- USE DEVELOPER PDF AS PRIMARY SOURCE (STRICT)
------------------------------------------------------------
Use ONLY the official developer PDF brochure to extract:
- Developer name
- Unit types and bedroom mix (Studio, 1BR, 2BR, 3BR, etc.)
- Built-up area / interior area per unit type (sq.ft only; sqm if also stated)
- Starting price per unit type (AED)
- Payment plan (milestone breakdown -- every percentage)
- Handover date (quarter and year)
- Total number of units
- Internal amenities -- apply the 3-TIER SCOPING RULE:
  TIER 1: Inside residences (maid room, driver room, show kitchen, storage, balcony, terrace)
  TIER 2: Inside the building (lobby, gym, pool, spa, concierge, parking, business center)
  TIER 3: Within the private gated community/masterplan (parks, retail, marina, beach club, schools)
  EXCLUDE: views, large windows, location descriptions, landscaping,
  future hotels, masterplan-level infrastructure not yet built,
  boardwalks, marketing adjectives
- Floor counts, tower counts, total unit counts
- Architecture and design notes (structural facts only, not marketing copy)
- Floor plan configurations: each distinct unit variation with its size and price

Do NOT infer, assume, or take data from:
- Agent listings
- Property Finder / Bayut / Dubizzle
- Sales ads, marketing images, or social posts

If missing -> write TBA.

------------------------------------------------------------
FLOOR PLAN EXTRACTION RULES (CRITICAL)
------------------------------------------------------------
Extract all floor plan data from the PDF into the following format:
Unit Type | Living Area (sq.ft) | Starting Price (AED)

DEDUPLICATION RULES:
- If the PDF shows multiple sub-variants of the same bedroom count
  (e.g., "1BR Type A - 650 sq.ft" and "1BR Type B - 720 sq.ft"),
  MERGE them into a single line with a size RANGE:
  1BR Apartment | 650-720 sq.ft | Starting Price
- Use the LOWEST starting price among variants of the same type.
- If only one variant exists for a bedroom count, use exact size
  (no range needed): 1BR Apartment | 650 sq.ft | AED 1,100,000

MISSING DATA RULES (ANTI-HALLUCINATION):
- If the PDF contains NO floor plan data at all (no unit types,
  no sizes, no prices) -> write TBA for the entire field.
- If sizes exist but prices do not -> list sizes, write TBA for price:
  1BR Apartment | 650-800 sq.ft | TBA
- If prices exist but sizes do not -> list prices, write TBA for size:
  1BR Apartment | TBA | AED 1,100,000
- NEVER fabricate, estimate, or infer sizes or prices.
  The pipeline has NO mechanism to verify invented numbers.
- If the PDF only lists bedroom counts with no size/price detail ->
  list bedroom types only:
  Studio | TBA | TBA
  1BR Apartment | TBA | TBA

Variable count: projects may have 2-8+ distinct floor plans.
Output as many lines as the PDF supports. Do not pad or invent
entries to reach a minimum count.

This extracted floor plan data feeds into:
- Project Details fields (Area From, Property Type, Bedrooms)
- Overview Description (unit type breakdown, size ranges)
- FAQ 3 answer (unit types available)

------------------------------------------------------------
PAYMENT PLAN (CRITICAL RULE)
------------------------------------------------------------
If the developer PDF includes milestone installments:
- SUM ALL installments that occur before handover -> "During Construction" percentage.
- The final installment payable at handover -> "On Handover" percentage.

Payment Plan Headline MUST be formatted as:
X/X

Example:
60/40

Payment Plan Description MUST use this standardized format:
"Pay X% during construction and X% on handover in QX 20XX, with a X% booking fee."

Payment Milestones (EXTRACTED -- copy percentages exactly from PDF):
X% -- On Booking
X% -- During Construction
X% -- On Handover (QX 20XX)

MULTIPLE PAYMENT PLANS: Some projects offer more than one payment plan
(e.g., 60/40 AND 70/30). If the PDF shows multiple plans, list each
with its complete milestone breakdown. Do not merge different plans.

Do NOT output "TBA" if a milestone schedule is present in the PDF.
Only output TBA if the PDF provides no numerical payment breakdown whatsoever.

------------------------------------------------------------
STEP 2 -- NEARBY FACILITIES LOOKUP (DUBAI)
------------------------------------------------------------
For the Location section, look up nearby facilities using Google Maps:

Categories to cover:
- Malls and retail (with drive times)
- Healthcare facilities (with drive times)
- Schools and nurseries (with drive times)
- Entertainment and cultural destinations (with drive times)
- Key transport links (metro stations, highways)
- Business/financial centers
- Airport (DXB and DWC if relevant)
- Beach access if applicable

Sources: Google Maps verified. Round times to nearest 5 minutes.
Use actual Dubai facility names only.

Common Dubai landmarks to reference where applicable:
- Dubai Mall, Mall of the Emirates, Dubai Marina Mall
- Burj Khalifa, Dubai Frame, Museum of the Future
- Dubai International Airport (DXB), Al Maktoum International (DWC)
- DIFC, Downtown Dubai, Business Bay
- Palm Jumeirah, Dubai Marina, JBR
- Dubai Metro stations (Red Line, Green Line)
- American Hospital Dubai, Mediclinic, Saudi German Hospital
- GEMS schools, Dubai British School, Kings' School

Do NOT invent facilities. If lookup fails for a category, write TBA.

------------------------------------------------------------
STEP 3 -- PAGE OUTPUT (STRICT STRUCTURE)
------------------------------------------------------------

=== SEO ===

1) Meta Title (GENERATED, 60-70 characters):
[Project Name] by [Developer] | [Area], Dubai

2) Meta Description (GENERATED, 155-165 characters):
Must include: property types, starting price, payment plan, handover.
"[Property types] by [developer] in [location]. From AED X.XM. [X/X] plan. Handover [QX 20XX]."

3) URL Slug (GENERATED, lowercase-hyphens):
[project-name]-[area]

4) Image Alt Tag (GENERATED, 80-125 characters, factual, no adjectives):
[Project Name] [property type] development by [Developer] in [Location], Dubai


=== HERO ===

5) Hero H1 (GENERATED, 50-70 characters):
[Project Name] in [Area]

6) Hero Description (GENERATED, 350-450 characters):
One paragraph establishing project identity: developer name, property types,
primary differentiator, location appeal. Professional tone, no superlatives.

7) Starting Price: AED X,XXX,XXX (EXTRACTED from PDF)

8) Handover: QX 20XX (EXTRACTED from PDF)

9) Number of Units: XXX (EXTRACTED from PDF)


=== PROJECT OVERVIEW ===

10) Overview H2 (STATIC): "Project Overview"

11) Overview Description (GENERATED/HYBRID, 600-800 characters):
Detailed paragraph covering:
- Developer reputation and track record (can be researched)
- Project concept and positioning
- Unit type overview (EXTRACTED data embedded)
- Design philosophy and architectural highlights (from PDF if available)
- Target buyer profile

EMBEDDED EXTRACTED DATA: unit counts, property types, size ranges.


=== PROJECT DETAILS CARD (ALL EXTRACTED) ===

12) Location (EXTRACTED): Area, Sub-area from PDF
13) Developer (EXTRACTED): Developer name from PDF
14) Property Type (EXTRACTED): apartments/villas/townhouses/penthouses/duplexes
15) Number of Bedrooms (EXTRACTED): Range from floor plan data (e.g., "1-4 BR")
16) Area From (EXTRACTED): Smallest floor plan sq.ft
17) Handover (EXTRACTED): QX 20XX
18) Payment Plan (EXTRACTED): X/X format


=== FLOOR PLANS ===

19) Floor Plans Table (EXTRACTED):
Format per line: Unit Type | Living Area (sq ft) | Starting Price (AED)
Follow DEDUPLICATION and MISSING DATA rules from Floor Plan Extraction section.


=== PAYMENT PLAN ===

20) Payment Plan Description (GENERATED/HYBRID, 150-250 characters):
"Pay X% during construction and X% on handover in QX 20XX, with a X% booking fee."
EMBEDDED EXTRACTED DATA: percentages, handover date.

21) Payment Milestones (EXTRACTED):
X% -- On Booking
X% -- During Construction
X% -- On Handover (QX 20XX)


=== KEY POINTS ===

22) Key Point 1 Title (GENERATED, 40-60 characters):
Concise title for first USP (e.g., "Waterfront Living", "Branded Interiors")

23) Key Point 1 Description (GENERATED, 250-350 characters):
Expansion of USP - value proposition, what buyers can expect.

24) Key Point 2 Title (GENERATED, 40-60 characters):
Concise title for second USP.

25) Key Point 2 Description (GENERATED, 250-350 characters):
Expansion of second USP.


=== AMENITIES ===

26) Amenities H2 (STATIC): "Amenities"

27) Amenities Paragraph (GENERATED, 300-450 characters):
Overview using top 3 differentiating amenities as examples. 4 sentences max.
Group by category: wellness/fitness, leisure/social, family/children, practical services.
All amenities referenced MUST appear in the PDF brochure.

28) Amenities Table (EXTRACTED):
List ALL amenities from PDF. Apply 3-tier scope:
- TIER 1: Inside residences
- TIER 2: Inside building
- TIER 3: Within community
EXCLUDE: views, windows, landscaping, marketing adjectives.


=== LOCATION ===

29) Location Title (GENERATED, 30-50 characters):
Format: "[Area Name], Dubai"

30) Location Description (GENERATED, 450-600 characters):
Comprehensive location overview:
- Area positioning and character
- Key attractions and landmarks nearby
- Connectivity (metro, highways, airport)
- Lifestyle offerings (dining, retail, entertainment)
- Drive times to major destinations (Google Maps verified)


=== DEVELOPER ===

31) Developer Name Title (GENERATED):
Format: "[Developer Name]"

32) Developer Description (GENERATED, 400-550 characters):
Developer profile:
- Founding year or history
- Portfolio scope (number of projects, regions)
- Reputation and awards
- Design philosophy
- Dubai/UAE market presence
- Notable completed projects


=== FAQ ===

33) FAQ H2 (GENERATED):
Format: "Frequently Asked Questions about [Project Name]"

--- TIER 1: CORE FAQs (always include these 5) ---

34) FAQ 1 -- Question: "What is [Project Name]?"
    FAQ 1 -- Answer:
    Source: Overview section.
    Must include: developer name (EXTRACTED), location (EXTRACTED),
    property types (EXTRACTED), project concept.

35) FAQ 2 -- Question: "Where is [Project Name] located?"
    FAQ 2 -- Answer:
    Source: Location section.
    Must include: area name (EXTRACTED), key nearby landmarks,
    drive times to major destinations.

36) FAQ 3 -- Question: "What unit types are available in [Project Name]?"
    FAQ 3 -- Answer:
    Source: Floor plan data (EXTRACTED).
    List all property types, bedroom counts, size ranges.
    MUST match floor plan extraction exactly.

37) FAQ 4 -- Question: "What is the starting price of [Project Name]?"
    FAQ 4 -- Answer:
    Source: Starting price (EXTRACTED from PDF).
    State "From AED X.XM" using exact extracted figure.
    If unavailable, write "Contact for pricing."

38) FAQ 5 -- Question: "What is the payment plan for [Project Name]?"
    FAQ 5 -- Answer:
    Source: Payment plan (EXTRACTED from PDF).
    State X/X structure, booking fee percentage, handover date.
    MUST match payment plan extraction exactly.

FAQ ANSWER GUIDELINES:
- Length: 40-80 words per answer
- Tone: Informative, factual -- not salesy
- Structure: Direct answer first, then supporting detail
- Data: Include specific numbers (sizes, prices, distances, dates)
- No fluff: Avoid "absolutely" / "definitely" / "perfect for"
- Each question and answer MUST mention the project name

FAQ OUTPUT FORMAT:
Q: [Question text]
A: [Answer text -- 40-80 words]


------------------------------------------------------------
ANTI-HALLUCINATION GUARDRAILS
------------------------------------------------------------
Before finalizing output, verify:

1. Every price, size, date, and percentage in EXTRACTED fields
   traces back to a specific page/section of the developer PDF.
2. No GENERATED or HYBRID field contains fabricated numbers -- if
   a generated paragraph references a price, size, unit count, date,
   or percentage, it must match an EXTRACTED value exactly.
3. Payment plan percentages sum to 100%.
4. All amenities in Amenities Paragraph and Table come from the PDF,
   scoped to the 3-tier rule.
5. Floor plan data in FAQ answers and Overview must match the
   floor plan extraction output exactly.
6. If any HYBRID field needs a data point that is TBA in the extraction,
   the paragraph must either omit that data point or explicitly state TBA.
7. Location drive times must be Google Maps verified for Dubai.
   Do NOT use Abu Dhabi facility names.
8. Developer information can be researched but should be factual
   and verifiable (founding year, portfolio size, notable projects).

If you cannot verify a data point, write TBA.
Do NOT approximate, round creatively, or use ranges you invented.


------------------------------------------------------------
DUBAI-SPECIFIC INVESTMENT CONTEXT
------------------------------------------------------------
When relevant to the content, reference:
- Dubai Land Department (DLD) 4% transfer fee
- Golden Visa eligibility (AED 2M+ property threshold)
- Freehold ownership areas for foreign buyers
- RERA registration and escrow account requirements
- Zero income tax, zero capital gains tax

Conservative yield ranges (use only if mentioning ROI):
- Dubai Marina apartments: 5-7%
- Downtown Dubai apartments: 4-6%
- Palm Jumeirah apartments: 5-7%, villas: 3-5%
- JVC/JLT apartments: 7-9%
- Business Bay apartments: 6-8%

Do NOT fabricate specific ROI figures for the project unless
verified from market sources.


------------------------------------------------------------
STYLE GUIDELINES
------------------------------------------------------------

Tone: Professional, confident, informative. Not salesy or hyperbolic.

Formatting Rules:
- No bullet points within paragraphs (convert to flowing prose)
- Include specific numbers: unit counts, sizes, prices, drive times
- Avoid superlatives without substantiation
- No exclamation marks
- Write "sq.ft" and "sqm" (not "square feet" or "square meters")

Terminology:
- Use "residents" not "homeowners" or "buyers" when describing lifestyle
- Use "investors and end-users" when addressing target audience
- Reference "capital appreciation" and "rental yields" for investment content
- Use "handover" not "completion" for delivery dates

Data Handling:
- If brochure lacks specific data (price, size, payment plan), write TBA
- If location drive times are not in brochure, use Google Maps estimates
- Cross-reference amenities from both marketing copy and floor plans in brochure

Total Character Count (all generated sections combined):
3,200-4,800 | Target: 4,000 | ~600-900 words

====================================================================
END OF PROMPT
====================================================================
