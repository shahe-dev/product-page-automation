# Aggregators Field Registry

Template type: `aggregators`
Target sites: `sobha-central.ae`, `dubaislands.ae`, `dubai-creek-living.ae`, `dubaihills-property.ae`, `dubaimaritime-city.ae`, `rashid-yachts-marina.ae`, `city-walk-property.ae`, `capital-luxury.ae`, `ras-al-khaimah-properties.ae`, `saudi-estates.com`, and 14+ additional regional domains
Total fields: 113
Generated fields: 48
Extracted fields: 41
Hybrid fields: 20
Static fields: 4

## Field Table

| field_name | section | type | char_limit | required | notes |
|------------|---------|------|------------|----------|-------|
| meta_title | SEO | GENERATED | 60 | yes | Format: [Project Name] by [Developer] in [Location], [City] |
| meta_description | SEO | GENERATED | 165 | yes | Include: property types, starting price, payment plan, handover, differentiator |
| url_slug | SEO | GENERATED | - | yes | lowercase-hyphens: [project-name]-[location] |
| image_alt | SEO | GENERATED | 125 | yes | Factual description, no marketing adjectives |
| hero_h1 | Hero | GENERATED | 70 | yes | Format varies: [Project Name] at [Location] or Invest in [Project] |
| hero_subtitle | Hero | GENERATED | 150 | yes | Investment/lifestyle value proposition, single sentence |
| hero_investment_stat_1 | Hero | HYBRID | 80 | yes | ROI bullet: "High projected ROI in this high-growth area" |
| hero_investment_stat_2 | Hero | HYBRID | 80 | yes | Price bullet: "AED X.XXM (USD XXXK) Starting property price" |
| hero_investment_stat_3 | Hero | HYBRID | 80 | yes | Capital gains bullet: "~ +XX% Projected annual capital gains" |
| starting_price | Hero | EXTRACTED | - | yes | AED format from PDF, displayed in Quick Info Cards |
| payment_plan_ratio | Hero | EXTRACTED | - | yes | XX/XX format from PDF (e.g., 60/40, 50/50) |
| handover | Hero | EXTRACTED | - | yes | QX 20XX format from PDF |
| about_h2 | About | GENERATED | 80 | yes | Format: [Project Name] -- [Value Proposition] |
| about_paragraph | About | HYBRID | 650 | yes | Project identity, property types, unit counts, features |
| selling_point_1 | About | HYBRID | 100 | yes | Key selling point from brochure |
| selling_point_2 | About | HYBRID | 100 | yes | Key selling point from brochure |
| selling_point_3 | About | HYBRID | 100 | yes | Key selling point from brochure |
| selling_point_4 | About | HYBRID | 100 | no | Key selling point from brochure |
| selling_point_5 | About | HYBRID | 100 | no | Key selling point from brochure |
| project_details_developer | Project Details | EXTRACTED | - | yes | Developer name from PDF |
| project_details_location | Project Details | EXTRACTED | - | yes | Area, District/Road format |
| project_details_payment_plan | Project Details | EXTRACTED | - | yes | XX/XX format |
| project_details_area | Project Details | EXTRACTED | - | yes | Size range: XXX sq. ft. -- X,XXX sq. ft. |
| project_details_property_type | Project Details | EXTRACTED | - | yes | apartments/villas/penthouses/duplexes |
| project_details_bedrooms | Project Details | EXTRACTED | - | no | Range: X-XBR or Studio, 1-4BR |
| economic_appeal_h2 | Economic Appeal | GENERATED | 60 | yes | Investment-focused header |
| economic_appeal_paragraph | Economic Appeal | GENERATED | 650 | yes | Market drivers, yields, appreciation outlook |
| payment_plan_h2 | Payment Plan | GENERATED | 60 | yes | Format: Easy Installments: XX/XX by [Developer] |
| payment_plan_description | Payment Plan | GENERATED | 200 | yes | Brief explanation of payment structure |
| payment_plan_booking_pct | Payment Plan | EXTRACTED | - | yes | XX% for booking/down payment |
| payment_plan_construction_pct | Payment Plan | EXTRACTED | - | yes | XX% during construction |
| payment_plan_handover_pct | Payment Plan | EXTRACTED | - | yes | XX% on handover |
| milestone_1_name | Payment Plan | EXTRACTED | - | no | Payment milestone name (e.g., On Booking) |
| milestone_1_percentage | Payment Plan | EXTRACTED | - | no | Payment milestone percentage |
| milestone_1_date | Payment Plan | EXTRACTED | - | no | Payment milestone date/timing |
| milestone_2_name | Payment Plan | EXTRACTED | - | no | Payment milestone name |
| milestone_2_percentage | Payment Plan | EXTRACTED | - | no | Payment milestone percentage |
| milestone_2_schedule | Payment Plan | EXTRACTED | - | no | Payment milestone schedule |
| milestone_3_name | Payment Plan | EXTRACTED | - | no | Payment milestone name (e.g., On Handover) |
| milestone_3_percentage | Payment Plan | EXTRACTED | - | no | Payment milestone percentage |
| milestone_3_date | Payment Plan | EXTRACTED | - | no | Payment milestone date |
| key_feature_1_title | Key Features | GENERATED | 50 | yes | Feature card title (e.g., Direct Amenity Connections) |
| key_feature_1_description | Key Features | GENERATED | 180 | yes | Feature card description |
| key_feature_2_title | Key Features | GENERATED | 50 | yes | Feature card title (e.g., Panoramic Views) |
| key_feature_2_description | Key Features | GENERATED | 180 | yes | Feature card description |
| key_feature_3_title | Key Features | GENERATED | 50 | yes | Feature card title (e.g., Sheikh Zayed Road Address) |
| key_feature_3_description | Key Features | GENERATED | 180 | yes | Feature card description |
| amenities_h2 | Amenities | STATIC | - | yes | Section header: Amenities |
| amenity_1_title | Amenities | HYBRID | 40 | yes | Amenity card title from brochure |
| amenity_1_description | Amenities | HYBRID | 100 | yes | Amenity card description |
| amenity_2_title | Amenities | HYBRID | 40 | yes | Amenity card title from brochure |
| amenity_2_description | Amenities | HYBRID | 100 | yes | Amenity card description |
| amenity_3_title | Amenities | HYBRID | 40 | yes | Amenity card title from brochure |
| amenity_3_description | Amenities | HYBRID | 100 | yes | Amenity card description |
| amenity_4_title | Amenities | HYBRID | 40 | yes | Amenity card title from brochure |
| amenity_4_description | Amenities | HYBRID | 100 | yes | Amenity card description |
| amenity_5_title | Amenities | HYBRID | 40 | no | Amenity card title from brochure |
| amenity_5_description | Amenities | HYBRID | 100 | no | Amenity card description |
| amenity_6_title | Amenities | HYBRID | 40 | no | Amenity card title from brochure |
| amenity_6_description | Amenities | HYBRID | 100 | no | Amenity card description |
| developer_h2 | Developer | STATIC | - | yes | Section header: About the Developer |
| developer_description | Developer | GENERATED | 400 | yes | Developer history, portfolio, track record |
| location_h2 | Location | GENERATED | 70 | yes | Location-focused header |
| location_overview_paragraph | Location | GENERATED | 700 | yes | Area character, connectivity, attractions nearby |
| social_facilities_intro | Location | GENERATED | 250 | yes | Brief description of entertainment/dining/leisure |
| social_facility_1 | Location | GENERATED | 80 | yes | Format: [Location Name] -- [X] minutes by car |
| social_facility_2 | Location | GENERATED | 80 | yes | Format: [Location Name] -- [X] minutes by car |
| social_facility_3 | Location | GENERATED | 80 | yes | Format: [Location Name] -- [X] minutes by car |
| education_medicine_intro | Location | GENERATED | 250 | yes | Brief description of schools/healthcare |
| education_facility_1 | Location | GENERATED | 80 | yes | Format: [Institution Name] -- [X] minutes by car |
| education_facility_2 | Location | GENERATED | 80 | yes | Format: [Institution Name] -- [X] minutes by car |
| education_facility_3 | Location | GENERATED | 80 | yes | Format: [Institution Name] -- [X] minutes by car |
| culture_intro | Location | GENERATED | 250 | yes | Brief description of cultural offerings |
| culture_facility_1 | Location | GENERATED | 80 | yes | Format: [Establishment Name] -- [X] minutes by car |
| culture_facility_2 | Location | GENERATED | 80 | yes | Format: [Establishment Name] -- [X] minutes by car |
| culture_facility_3 | Location | GENERATED | 80 | yes | Format: [Establishment Name] -- [X] minutes by car |
| nearby_1_name | Location | EXTRACTED | - | no | Nearby landmark name |
| nearby_1_distance | Location | EXTRACTED | - | no | Distance to landmark |
| nearby_2_name | Location | EXTRACTED | - | no | Nearby landmark name |
| nearby_2_distance | Location | EXTRACTED | - | no | Distance to landmark |
| nearby_3_name | Location | EXTRACTED | - | no | Nearby landmark name |
| nearby_3_distance | Location | EXTRACTED | - | no | Distance to landmark |
| nearby_4_name | Location | EXTRACTED | - | no | Nearby landmark name |
| nearby_4_distance | Location | EXTRACTED | - | no | Distance to landmark |
| floor_plans_h2 | Floor Plans | STATIC | - | yes | Section header: Floor Plans |
| unit_type_1_name | Floor Plans | EXTRACTED | - | no | Floor plan unit type |
| unit_type_1_area | Floor Plans | EXTRACTED | - | no | Floor plan area sq.ft |
| unit_type_1_price | Floor Plans | EXTRACTED | - | no | Floor plan starting price |
| unit_type_2_name | Floor Plans | EXTRACTED | - | no | Floor plan unit type |
| unit_type_2_area | Floor Plans | EXTRACTED | - | no | Floor plan area sq.ft |
| unit_type_2_price | Floor Plans | EXTRACTED | - | no | Floor plan starting price |
| unit_type_3_name | Floor Plans | EXTRACTED | - | no | Floor plan unit type |
| unit_type_3_area | Floor Plans | EXTRACTED | - | no | Floor plan area sq.ft |
| unit_type_3_price | Floor Plans | EXTRACTED | - | no | Floor plan starting price |
| unit_type_4_name | Floor Plans | EXTRACTED | - | no | Floor plan unit type |
| unit_type_4_area | Floor Plans | EXTRACTED | - | no | Floor plan area sq.ft |
| unit_type_4_price | Floor Plans | EXTRACTED | - | no | Floor plan starting price |
| faq_1_question | FAQ | GENERATED | 80 | yes | Core: Where is [Project Name] located? |
| faq_1_answer | FAQ | GENERATED | 200 | yes | Source: Location section |
| faq_2_question | FAQ | GENERATED | 80 | yes | Core: Who is the developer of [Project Name]? |
| faq_2_answer | FAQ | GENERATED | 200 | yes | Source: Developer section |
| faq_3_question | FAQ | GENERATED | 80 | yes | Core: What types of properties are available at [Project Name]? |
| faq_3_answer | FAQ | HYBRID | 200 | yes | Source: Floor plan types from PDF |
| faq_4_question | FAQ | GENERATED | 80 | yes | Core: What is the starting price at [Project Name]? |
| faq_4_answer | FAQ | HYBRID | 200 | yes | Source: Extracted starting price |
| faq_5_question | FAQ | GENERATED | 80 | yes | Core: What payment plans are available for [Project Name]? |
| faq_5_answer | FAQ | HYBRID | 200 | yes | Source: Extracted payment plan breakdown |
| faq_6_question | FAQ | GENERATED | 80 | yes | Core: When will [Project Name] be completed? |
| faq_6_answer | FAQ | HYBRID | 200 | yes | Source: Extracted handover date |
| faq_7_question | FAQ | GENERATED | 80 | yes | Unique: Based on brochure triggers |
| faq_7_answer | FAQ | GENERATED | 200 | yes | 60-120 words, factual |
| faq_8_question | FAQ | GENERATED | 80 | yes | Unique: Different trigger than FAQ 7 |
| faq_8_answer | FAQ | GENERATED | 200 | yes | 60-120 words, factual |
| faq_9_question | FAQ | GENERATED | 80 | yes | Unique: Different trigger than FAQ 7-8 |
| faq_9_answer | FAQ | GENERATED | 200 | yes | 60-120 words, factual |
| faq_10_question | FAQ | GENERATED | 80 | yes | Unique: Must be about area/community |
| faq_10_answer | FAQ | GENERATED | 200 | yes | 60-120 words, factual |

## Section Order

1. SEO
2. Hero
3. About
4. Project Details
5. Economic Appeal
6. Payment Plan
7. Key Features
8. Amenities
9. Floor Plans (EXTRACTED - variable count)
10. Gallery (STATIC)
11. Developer
12. Location
13. FAQ

## Notes

### Field Deduplication

The following extracted fields appear in multiple UI locations but are stored once:
- `starting_price` - Hero Quick Info Cards, Project Details
- `payment_plan_ratio` - Hero Quick Info Cards, Project Details, Payment Plan section
- `handover` - Hero Quick Info Cards, Project Details, Payment Plan breakdown

### Dynamic Field Counts

These sections have variable field counts based on brochure content:

**Floor Plans** (EXTRACTED)
- Variable count: projects may have 2-8+ distinct floor plan types
- Each floor plan: `floor_plan_N_type`, `floor_plan_N_area`, `floor_plan_N_price`
- Output as many entries as the PDF supports

**Amenities** (HYBRID)
- Minimum 4, maximum 6 amenity cards
- Source from brochure using 3-tier scope rule

**FAQs**
- 6 core (mandatory) + 4-6 unique (project-specific)
- Total: 10-12 FAQ pairs

### Regional Variations

**Abu Dhabi (capital-luxury.ae)**
- Section labeled "Investment Appeal" instead of "Economic Appeal"
- Transfer fee: 2% (not 4%)
- Golden Visa threshold: AED 2,000,000+
- Freehold zones only

**Dubai (majority of sites)**
- Transfer fee: 4% to DLD
- Golden Visa threshold: AED 2,000,000+
- Metro connectivity relevant

**RAK (ras-al-khaimah-properties.ae)**
- Transfer fee: 2%
- Reference Dubai proximity and Wynn Casino development

**Saudi Arabia (saudi-estates.com)**
- Currency: SAR (not AED)
- Premium Residency instead of Golden Visa
- No Vision 2030 content (static section)

### Character Limit Sources

- SEO: Standard best practices (50-60 title, 155-165 description)
- Hero subtitle: 80-150 characters (investment value proposition)
- About paragraph: 400-650 characters (~70-120 words)
- Economic Appeal: 400-650 characters (~70-120 words)
- Location overview: 400-700 characters (~70-130 words)
- Developer: 200-400 characters (~35-70 words)
- FAQ answers: 60-120 words each

### HYBRID Field Rules

HYBRID fields generate prose that embeds extracted data. When embedding:
- Prices, sizes, dates, percentages MUST match EXTRACTED values exactly
- No paraphrasing, rounding, or approximating embedded extracted data
- If extracted value is TBA, paragraph must omit or explicitly state TBA

### Amenity 3-Tier Scope Rule

Amenity cards must follow:
- TIER 1: Inside residences (maid room, balcony, terrace, storage, private pool)
- TIER 2: Inside building (lobby, gym, pool, spa, concierge, parking, co-working)
- TIER 3: Within community (marina, beach club, parks, retail, sports facilities)

Exclude: views, windows, landscaping, future infrastructure, marketing adjectives

### Static Elements (Not in Field Table)

These UI elements exist on the page but are NOT generated:
- Lead capture forms
- CTAs and buttons
- Developer logo images
- Gallery images
- the company company section
- "3 options after Handover" section
- "6 Steps to Success" section
- Client testimonials
- Price statistics cards (Property Monitor data)
- Map with facility pins
- Footer

### Cross-Reference with template_fields.py

Current `AGGREGATORS_FIELDS` in `template_fields.py` defines 40 fields with character limits. This registry expands to 75 fields to match the actual page structure observed in live screenshots. Key additions:
- Hero investment stats (3 fields)
- Project details card fields (6 fields)
- Payment plan breakdown fields (3 fields)
- Key feature cards (6 fields)
- Location facility categories (12 fields)
- Additional FAQs (4 fields beyond current 5 pairs)

Reconciliation needed in Phase 2 Task 1.
