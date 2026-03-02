# ADOP Field Registry

Template type: `adop`
Target site: `abudhabioffplan.ae`
Total fields: 60
Generated fields: 41
Extracted fields: 6
Hybrid fields: 13

## Field Table

| field_name | section | type | char_limit | required | notes |
|------------|---------|------|------------|----------|-------|
| meta_title | SEO | GENERATED | 70 | yes | Format: [Project Name] by [Developer] \| [Location] |
| meta_description | SEO | GENERATED | 165 | yes | Must include property types, starting price, payment plan, handover |
| url_slug | SEO | GENERATED | - | yes | lowercase-hyphens, [project-name]-[location] |
| image_alt_tag | SEO | GENERATED | 125 | yes | Factual, no adjectives, 80-125 chars |
| hero_h1 | Hero | GENERATED | 60 | yes | [Project Name] by [Developer] |
| hero_subtitle | Hero | GENERATED | 80 | yes | Single factual differentiator, no adjectives |
| starting_price | Hero | EXTRACTED | - | yes | AED format from PDF, displayed in Hero/Info Cards/Details |
| handover | Hero | EXTRACTED | - | yes | QX 20XX format from PDF, displayed in Hero/Info Cards/Details |
| area_from | Project Details | EXTRACTED | - | yes | Smallest floor plan sq.ft from PDF |
| location | Project Details | EXTRACTED | - | yes | Area, Location within Emirate |
| property_type | Project Details | EXTRACTED | - | yes | apartments/duplexes/villas/townhouses/penthouses from PDF |
| developer | Project Details | EXTRACTED | - | yes | Developer name from PDF |
| about_h2 | About | GENERATED | - | yes | Format: About [Project Name] by [Developer] |
| about_paragraph_1 | About | HYBRID | 370 | yes | Project identity: floors/buildings, developer, location, concept |
| about_paragraph_2 | About | HYBRID | 370 | yes | Product spec: unit count, types, sizes, design, architecture |
| about_paragraph_3 | About | HYBRID | 370 | yes | Value prop: starting price, location benefit, buyer profile |
| key_benefits_h2 | Key Benefits | GENERATED | - | yes | Format: Key Benefits of [Project Name] |
| key_benefits_paragraph_1 | Key Benefits | HYBRID | 450 | yes | Primary USP and secondary differentiators |
| key_benefits_paragraph_2 | Key Benefits | HYBRID | 500 | yes | Amenities in prose using 3-tier scope rule |
| area_infrastructure_h2 | Area Infrastructure | GENERATED | - | yes | Fixed: Area Infrastructure |
| infrastructure_paragraph_1 | Area Infrastructure | GENERATED | 250 | yes | Location context, position between landmarks |
| infrastructure_paragraph_2 | Area Infrastructure | GENERATED | 350 | yes | Drive times to named facilities |
| infrastructure_paragraph_3 | Area Infrastructure | GENERATED | 250 | yes | Daily conveniences, walkability, connectivity |
| location_h2 | Location | GENERATED | - | yes | Format: Location of [Project Name] |
| location_drive_time_summary | Location | GENERATED | - | yes | Two tiers: 5-15 min and 12-25 min attraction lists |
| location_overview | Location | GENERATED | 200 | yes | Position, tranquility/connectivity balance, road access |
| location_key_attractions | Location | GENERATED | - | yes | 5-7 items with drive times and descriptions |
| location_major_destinations | Location | GENERATED | - | yes | 4-6 destinations (cultural, business, airport) |
| investment_h2 | Investment | GENERATED | - | yes | Format: Investment in [Project Name] |
| investment_paragraph_1 | Investment | GENERATED | 320 | yes | Market context, demand drivers, freehold status, 2% transfer fee |
| investment_paragraph_2 | Investment | HYBRID | 320 | yes | ROI from Step 2 verification, yields, Golden Visa if >=2M |
| investment_paragraph_3 | Investment | GENERATED | 320 | yes | Project-specific value: inventory, positioning, long-term drivers |
| investment_paragraph_4 | Investment | HYBRID | 300 | yes | Payment plan X/X, booking fee, handover date |
| developer_h2 | Developer | GENERATED | - | yes | Format: About [Developer Name] |
| developer_description | Developer | GENERATED | 500 | yes | Founding, portfolio, track record, Abu Dhabi presence |
| faq_h2 | FAQ | GENERATED | - | yes | Format: Frequently Asked Questions about [Project Name] |
| faq_1_question | FAQ | GENERATED | - | yes | Core: What is [Project Name]? |
| faq_1_answer | FAQ | HYBRID | - | yes | Source: About section paragraph 1 |
| faq_2_question | FAQ | GENERATED | - | yes | Core: Where is [Project Name] located? |
| faq_2_answer | FAQ | GENERATED | - | yes | Source: Location section |
| faq_3_question | FAQ | GENERATED | - | yes | Core: What unit types are available in [Project Name]? |
| faq_3_answer | FAQ | HYBRID | - | yes | Source: Floor plan types from PDF |
| faq_4_question | FAQ | GENERATED | - | yes | Core: What is the starting price of [Project Name]? |
| faq_4_answer | FAQ | HYBRID | - | yes | Source: Extracted starting price |
| faq_5_question | FAQ | GENERATED | - | yes | Core: What is the payment plan for [Project Name]? |
| faq_5_answer | FAQ | HYBRID | - | yes | Source: Extracted payment plan |
| faq_6_question | FAQ | GENERATED | - | yes | Core: When will [Project Name] be completed? |
| faq_6_answer | FAQ | HYBRID | - | yes | Source: Extracted handover date |
| faq_7_question | FAQ | GENERATED | - | yes | Unique: Based on brochure trigger table |
| faq_7_answer | FAQ | GENERATED | - | yes | 40-80 words, factual |
| faq_8_question | FAQ | GENERATED | - | yes | Unique: Different trigger than FAQ 7 |
| faq_8_answer | FAQ | GENERATED | - | yes | 40-80 words, factual |
| faq_9_question | FAQ | GENERATED | - | yes | Unique: Different trigger than FAQ 7-8 |
| faq_9_answer | FAQ | GENERATED | - | yes | 40-80 words, factual |
| faq_10_question | FAQ | GENERATED | - | yes | Unique: Must be about area/community |
| faq_10_answer | FAQ | GENERATED | - | yes | 40-80 words, factual |
| faq_11_question | FAQ | GENERATED | - | yes | Unique: Different trigger than FAQ 7-10 |
| faq_11_answer | FAQ | GENERATED | - | yes | 40-80 words, factual |
| faq_12_question | FAQ | GENERATED | - | yes | Unique: Different trigger than FAQ 7-11 |
| faq_12_answer | FAQ | GENERATED | - | yes | 40-80 words, factual |

## Section Order

1. SEO
2. Hero
3. Project Details
4. About
5. Key Benefits
6. Area Infrastructure
7. Location
8. Investment
9. Developer
10. FAQ

## Notes

### Field Deduplication

The following extracted fields appear in multiple UI sections but are stored once:
- `starting_price` - Hero, Project Info Cards, Project Details
- `handover` - Hero, Project Info Cards, Project Details
- `area_from` - Project Info Cards, Project Details
- `location` - Project Info Cards, Project Details

### Character Limit Sources

- SEO limits from standard SEO best practices (60-70 title, 155-165 description)
- About section: 740-1,100 total (~250-370 per paragraph)
- Key Benefits: 540-950 total (250-450 para 1, 250-500 para 2)
- Area Infrastructure: 225-770 total (150-250, 200-350, 150-250 per paragraph)
- Location: 620-1,860 total (variable based on area maturity)
- Investment: 770-1,270 total (200-320, 200-320, 200-320, 150-300 per paragraph)
- Developer: 300-500 chars
- FAQ answers: 40-80 words each

### HYBRID Field Rules

HYBRID fields generate prose that embeds extracted data. When embedding:
- Prices, sizes, dates, percentages MUST match EXTRACTED values exactly
- No paraphrasing, rounding, or approximating embedded extracted data
- If extracted value is TBA, paragraph must omit or explicitly state TBA

### Abu Dhabi-Specific Rules

- ROI data from Step 2 verification (DARI, ADREC, Bayut, Property Finder) - NOT from PDF
- Transfer fee: 2% (not 4%)
- Golden Visa: Only reference if starting_price >= AED 2,000,000
- Freehold only in 9 designated investment zones
- Use Abu Dhabi facility names only (not Dubai)

### Amenity 3-Tier Scope Rule

Key Benefits paragraph 2 must follow:
- TIER 1: Inside residences (maid room, driver room, show kitchen, storage, balcony, terrace)
- TIER 2: Inside building (lobby, gym, pool, spa, concierge, parking, business center)
- TIER 3: Within community (marina, beach club, parks, retail, schools)

Exclude: views, windows, landscaping, future infrastructure, marketing adjectives
