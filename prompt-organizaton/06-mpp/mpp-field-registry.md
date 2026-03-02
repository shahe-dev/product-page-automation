# MPP Field Registry

Template type: `mpp`
Target site: `main-portal.com`
Total fields: 91
Generated fields: 25
Extracted fields: 57
Hybrid fields: 9
Static fields: 2

## Field Table

| field_name | section | type | char_limit | required | notes |
|------------|---------|------|------------|----------|-------|
| meta_title | SEO | GENERATED | 70 | yes | Format: [Project Name] by [Developer] \| [Area], Dubai |
| meta_description | SEO | GENERATED | 165 | yes | Must include property types, starting price, payment plan, handover |
| url_slug | SEO | GENERATED | - | yes | lowercase-hyphens, [project-name]-[area] |
| image_alt_tag | SEO | GENERATED | 125 | yes | Factual, no adjectives, 80-125 chars |
| hero_h1 | Hero | GENERATED | 70 | yes | [Project Name] in [Area] |
| hero_description | Hero | GENERATED | 450 | yes | Project identity paragraph, professional tone |
| starting_price | Hero | EXTRACTED | - | yes | AED format from PDF |
| handover | Hero | EXTRACTED | - | yes | QX 20XX format from PDF |
| down_payment_percentage | Hero | EXTRACTED | - | no | Down payment percentage from PDF |
| number_of_units | Hero | EXTRACTED | - | yes | Total unit count from PDF |
| overview_h2 | Overview | STATIC | - | yes | Fixed: "Project Overview" |
| overview_description | Overview | HYBRID | 800 | yes | Developer, concept, unit types, design, buyer profile |
| project_location | Project Details | EXTRACTED | - | yes | Area, Sub-area from PDF |
| project_developer | Project Details | EXTRACTED | - | yes | Developer name from PDF |
| project_property_type | Project Details | EXTRACTED | - | yes | apartments/villas/townhouses/penthouses/duplexes |
| project_bedrooms | Project Details | EXTRACTED | - | yes | Bedroom range from floor plans (e.g., "1-4 BR") |
| project_area_from | Project Details | EXTRACTED | - | yes | Smallest floor plan sq.ft |
| project_handover | Project Details | EXTRACTED | - | yes | QX 20XX (duplicate display of handover) |
| project_payment_plan | Project Details | EXTRACTED | - | yes | X/X format (e.g., "60/40") |
| floor_plans_table | Floor Plans | EXTRACTED | - | yes | Multi-line: Unit Type \| Area (sq ft) \| Price (AED) |
| floor_plan_1_bedrooms | Floor Plans | EXTRACTED | - | no | Floor plan 1 bedroom config |
| floor_plan_1_starting_price | Floor Plans | EXTRACTED | - | no | Floor plan 1 starting price |
| floor_plan_1_living_area | Floor Plans | EXTRACTED | - | no | Floor plan 1 living area sq.m |
| floor_plan_2_bedrooms | Floor Plans | EXTRACTED | - | no | Floor plan 2 bedroom config |
| floor_plan_2_starting_price | Floor Plans | EXTRACTED | - | no | Floor plan 2 starting price |
| floor_plan_2_living_area | Floor Plans | EXTRACTED | - | no | Floor plan 2 living area sq.m |
| floor_plan_3_bedrooms | Floor Plans | EXTRACTED | - | no | Floor plan 3 bedroom config |
| floor_plan_3_starting_price | Floor Plans | EXTRACTED | - | no | Floor plan 3 starting price |
| floor_plan_3_living_area | Floor Plans | EXTRACTED | - | no | Floor plan 3 living area sq.m |
| floor_plan_4_bedrooms | Floor Plans | EXTRACTED | - | no | Floor plan 4 bedroom config |
| floor_plan_4_starting_price | Floor Plans | EXTRACTED | - | no | Floor plan 4 starting price |
| floor_plan_4_living_area | Floor Plans | EXTRACTED | - | no | Floor plan 4 living area sq.m |
| payment_plan_type_1 | Payment Plan | EXTRACTED | - | no | Payment plan type option 1 |
| payment_plan_type_2 | Payment Plan | EXTRACTED | - | no | Payment plan type option 2 |
| payment_plan_description | Payment Plan | HYBRID | 250 | yes | Standardized sentence with embedded percentages |
| payment_milestones | Payment Plan | EXTRACTED | - | yes | X% On Booking / During Construction / On Handover |
| on_booking_date | Payment Plan | EXTRACTED | - | no | Booking payment date |
| on_booking_percentage | Payment Plan | EXTRACTED | - | no | Booking payment percentage |
| on_construction_period | Payment Plan | EXTRACTED | - | no | Construction payment period |
| on_construction_percentage | Payment Plan | EXTRACTED | - | no | Construction payment percentage |
| on_construction_number_of_payments | Payment Plan | EXTRACTED | - | no | Number of construction payments |
| on_handover_date | Payment Plan | EXTRACTED | - | no | Handover payment date |
| on_handover_percentage | Payment Plan | EXTRACTED | - | no | Handover payment percentage |
| key_point_1_title | Key Points | GENERATED | 60 | yes | First USP title |
| key_point_1_description | Key Points | GENERATED | 350 | yes | First USP expansion |
| key_point_1_image | Key Points | EXTRACTED | - | no | Image reference for key point 1 |
| key_point_2_title | Key Points | GENERATED | 60 | yes | Second USP title |
| key_point_2_description | Key Points | GENERATED | 350 | yes | Second USP expansion |
| key_point_2_image | Key Points | EXTRACTED | - | no | Image reference for key point 2 |
| amenities_h2 | Amenities | STATIC | - | yes | Fixed: "Amenities" |
| amenities_paragraph | Amenities | GENERATED | 450 | yes | Overview using top 3 amenities, 4 sentences max |
| amenity_1 | Amenities | EXTRACTED | - | no | Individual amenity item |
| amenity_2 | Amenities | EXTRACTED | - | no | Individual amenity item |
| amenity_3 | Amenities | EXTRACTED | - | no | Individual amenity item |
| amenity_4 | Amenities | EXTRACTED | - | no | Individual amenity item |
| amenity_5 | Amenities | EXTRACTED | - | no | Individual amenity item |
| amenity_6 | Amenities | EXTRACTED | - | no | Individual amenity item |
| amenity_7 | Amenities | EXTRACTED | - | no | Individual amenity item |
| amenity_8 | Amenities | EXTRACTED | - | no | Individual amenity item |
| amenities_table | Amenities | EXTRACTED | - | yes | All amenities from PDF using 3-tier scope |
| location_name | Location | EXTRACTED | - | no | Location/area name |
| location_title | Location | GENERATED | 50 | yes | Format: [Area Name], Dubai |
| location_description | Location | GENERATED | 600 | yes | Area character, landmarks, connectivity, drive times |
| developer_h2 | Developer | STATIC | - | yes | Section header: About the Developer |
| developer_badge | Developer | EXTRACTED | - | no | Developer badge/certification |
| developer_logo | Developer | EXTRACTED | - | no | Developer logo reference |
| developer_name | Developer | EXTRACTED | - | yes | Developer name from PDF |
| developer_name_title | Developer | GENERATED | 50 | yes | Developer name title |
| developer_description | Developer | GENERATED | 550 | yes | History, portfolio, reputation, Dubai presence |
| developer_stat_1_value | Developer | EXTRACTED | - | no | Developer stat value 1 |
| developer_stat_1_label | Developer | EXTRACTED | - | no | Developer stat label 1 |
| developer_stat_2_value | Developer | EXTRACTED | - | no | Developer stat value 2 |
| developer_stat_2_label | Developer | EXTRACTED | - | no | Developer stat label 2 |
| developer_stat_3_value | Developer | EXTRACTED | - | no | Developer stat value 3 |
| developer_stat_3_label | Developer | EXTRACTED | - | no | Developer stat label 3 |
| faq_h2 | FAQ | GENERATED | - | yes | Format: Frequently Asked Questions about [Project Name] |
| faq_1_question | FAQ | GENERATED | - | yes | Core: What is [Project Name]? |
| faq_1_answer | FAQ | HYBRID | - | yes | Source: Overview section |
| faq_2_question | FAQ | GENERATED | - | yes | Core: Where is [Project Name] located? |
| faq_2_answer | FAQ | GENERATED | - | yes | Source: Location section |
| faq_3_question | FAQ | GENERATED | - | yes | Core: What unit types are available in [Project Name]? |
| faq_3_answer | FAQ | HYBRID | - | yes | Source: Floor plan data (EXTRACTED) |
| faq_4_question | FAQ | GENERATED | - | yes | Core: What is the starting price of [Project Name]? |
| faq_4_answer | FAQ | HYBRID | - | yes | Source: Extracted starting price |
| faq_5_question | FAQ | GENERATED | - | yes | Core: What is the payment plan for [Project Name]? |
| faq_5_answer | FAQ | HYBRID | - | yes | Source: Extracted payment plan |
| faq_6_question | FAQ | GENERATED | - | no | Optional additional FAQ |
| faq_6_answer | FAQ | GENERATED | - | no | Optional additional FAQ answer |

## Section Order

1. SEO
2. Hero
3. Overview
4. Project Details
5. Floor Plans
6. Payment Plan
7. Key Points
8. Amenities
9. Location
10. Developer
11. FAQ

## Notes

### Field Deduplication

The following extracted fields appear in multiple UI sections but are stored once:
- `starting_price` - Hero stats
- `handover` - Hero stats, Project Details Card
- `number_of_units` - Hero stats
- `project_area_from` / `project_bedrooms` - Project Details Card (derived from floor_plans_table)

### Character Limit Sources

- SEO limits from standard SEO best practices (60-70 title, 155-165 description)
- Hero Description: 350-450 chars
- Overview Description: 600-800 chars
- Payment Plan Description: 150-250 chars
- Key Points: 40-60 title, 250-350 description each
- Amenities Paragraph: 300-450 chars
- Location Description: 450-600 chars
- Developer Description: 400-550 chars
- FAQ answers: 40-80 words each (~200-400 chars)

### HYBRID Field Rules

HYBRID fields generate prose that embeds extracted data. When embedding:
- Prices, sizes, dates, percentages MUST match EXTRACTED values exactly
- No paraphrasing, rounding, or approximating embedded extracted data
- If extracted value is TBA, paragraph must omit or explicitly state TBA

### Floor Plans Table Format

Multi-line field containing all floor plan entries:
```
Unit Type | Living Area (sq ft) | Starting Price (AED)
Studio | 400-450 sq ft | AED 750,000
1BR Apartment | 650-800 sq ft | AED 1,100,000
```

DEDUPLICATION: Merge same-bedroom variants into size ranges, use lowest price.
MISSING DATA: Use TBA for missing sizes or prices, never fabricate.

### Amenity 3-Tier Scope Rule

Amenities paragraph and table must follow:
- TIER 1: Inside residences (maid room, driver room, show kitchen, storage, balcony, terrace)
- TIER 2: Inside building (lobby, gym, pool, spa, concierge, parking, business center)
- TIER 3: Within community (marina, beach club, parks, retail, schools)

Exclude: views, windows, landscaping, future infrastructure, marketing adjectives.

### Multiple Payment Plans

Some projects offer multiple payment plan options. If PDF shows multiple plans:
- `project_payment_plan` should list primary plan (e.g., "60/40")
- `payment_milestones` should include all plan variants with breakdowns

### Dubai-Specific Context

- Transfer fee: 4% (DLD)
- Golden Visa: Reference only if starting_price >= AED 2,000,000
- Use Dubai facility names only (not Abu Dhabi)
- Drive times verified via Google Maps

### Static Sections (Not in Field Registry)

The following UI sections are static and do not require content generation:
- Gallery Section
- View All Floor Plans Button
- Get Professional Property Guidance Section
- Explore Future Developments Section
- Other Projects in [Area Name] Section
- Other Projects by [Developer Name] Section
- Footer/Contact sections

## Cross-Reference: template_fields.py

Current MPP_FIELDS in template_fields.py (75 fields) includes fields not reflected in the actual website layout. This registry documents the fields actually needed based on the live page structure:

| template_fields.py field | Registry status | Notes |
|--------------------------|-----------------|-------|
| meta_title | Mapped | SEO |
| meta_description | Mapped | SEO |
| url_slug | Mapped | SEO |
| image_alt | Mapped as image_alt_tag | SEO |
| h1 | Mapped as hero_h1 | Hero |
| hero_description | Mapped | Hero |
| overview_h2 | Mapped (STATIC) | Overview |
| overview_description | Mapped | Overview |
| payment_plan_h2 | Not needed | Section has no H2 on live site |
| payment_plan_description | Mapped | Payment Plan |
| key_point_1_title | Mapped | Key Points |
| key_point_1_description | Mapped | Key Points |
| key_point_2_title | Mapped | Key Points |
| key_point_2_description | Mapped | Key Points |
| amenities_h2 | Mapped (STATIC) | Amenities |
| amenity_X_title/description | Replaced by amenities_table | EXTRACTED from PDF |
| location_h2 | Not needed | Location uses location_title |
| location_description | Mapped | Location |
| location_area_description | Merged into location_description | Simplification |
| location_future_dev | Not needed | Static section |
| developer_h2 | Mapped as developer_name_title | Developer |
| developer_description | Mapped | Developer |
| developer_stat_X | Not visible on live page | May be removed |
| faq_X_question/answer | Mapped (5 pairs) | FAQ |
