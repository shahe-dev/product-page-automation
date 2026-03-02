# ADRE Field Registry

Template type: `adre`
Target site: `abu-dhabi.realestate`
Total fields: 100
Generated fields: 54
Extracted fields: 35
Hybrid fields: 5
Static fields: 6

## Field Table

| field_name | section | type | char_limit | required | notes |
|------------|---------|------|------------|----------|-------|
| meta_title | SEO | GENERATED | 60 | yes | Format: [Project] by [Developer] \| [Location], Abu Dhabi |
| meta_description | SEO | GENERATED | 165 | yes | Include: types, price, location, handover |
| url_slug | SEO | GENERATED | - | yes | lowercase-hyphens |
| image_alt | SEO | GENERATED | 125 | yes | Factual, no adjectives |
| h1 | Hero | GENERATED | 70 | yes | [Project] by [Developer] in [Location], Abu Dhabi |
| hero_marketing_h2 | Hero | GENERATED | 60 | yes | Marketing tagline |
| property_type_tags | Hero | EXTRACTED | - | yes | Apartments, Penthouses, Villas, Townhouses |
| starting_price | Hero | EXTRACTED | - | yes | AED format from PDF |
| booking_fee | Hero | EXTRACTED | - | no | Percentage from PDF |
| handover_date | Hero | EXTRACTED | - | yes | QX 20XX format |
| project_name | About | EXTRACTED | - | yes | Project name from PDF |
| about_h2 | About | GENERATED | 60 | yes | About [Project Name] |
| about_description | About | HYBRID | 900 | yes | Single paragraph, embeds extracted data |
| project_card_developer | About | EXTRACTED | - | yes | Links to developer page |
| project_card_area_from | About | EXTRACTED | - | yes | Smallest floor plan sq.ft |
| project_card_apartments | About | EXTRACTED | - | no | Bedroom range if applicable |
| project_card_penthouses | About | EXTRACTED | - | no | Bedroom config if applicable |
| project_card_villas | About | EXTRACTED | - | no | Bedroom range if applicable |
| project_card_townhouses | About | EXTRACTED | - | no | Bedroom range if applicable |
| project_card_total_units | About | EXTRACTED | - | no | If provided in brochure |
| project_card_payment_plan | About | EXTRACTED | - | yes | X/X format |
| floor_plans_table | Floor Plans | EXTRACTED | - | yes | Dynamic rows: type \| area \| price |
| floor_plan_1_type | Floor Plans | EXTRACTED | - | no | Unit type name |
| floor_plan_1_area | Floor Plans | EXTRACTED | - | no | Living area sq.ft |
| floor_plan_1_price | Floor Plans | EXTRACTED | - | no | Starting price AED |
| floor_plan_1_suite | Floor Plans | EXTRACTED | - | no | Suite area if provided |
| floor_plan_1_balcony | Floor Plans | EXTRACTED | - | no | Balcony area if provided |
| amenities_h2 | Amenities | GENERATED | 50 | yes | Amenities of [Project Name] |
| amenity_1_h3 | Amenities | GENERATED | 50 | yes | Featured amenity title |
| amenity_1_description | Amenities | GENERATED | 250 | yes | Featured amenity description |
| amenity_2_h3 | Amenities | GENERATED | 50 | yes | Featured amenity title |
| amenity_2_description | Amenities | GENERATED | 250 | yes | Featured amenity description |
| amenity_3_h3 | Amenities | GENERATED | 50 | no | Featured amenity title |
| amenity_3_description | Amenities | GENERATED | 250 | no | Featured amenity description |
| amenity_4_title | Amenities | EXTRACTED | 40 | no | Amenity list item |
| amenity_5_title | Amenities | EXTRACTED | 40 | no | Amenity list item |
| amenity_6_title | Amenities | EXTRACTED | 40 | no | Amenity list item |
| amenity_7_title | Amenities | EXTRACTED | 40 | no | Amenity list item |
| amenity_8_title | Amenities | EXTRACTED | 40 | no | Amenity list item |
| amenities_list | Amenities | HYBRID | - | yes | 8-14 items, <=40 chars each, from PDF |
| developer_h2 | Developer | STATIC | - | yes | "About the developer" |
| developer_description | Developer | GENERATED | 300 | yes | 2-3 factual sentences |
| economic_appeal_h2 | Economic Appeal | GENERATED | 60 | yes | Economic Appeal of [Project Name] |
| economic_appeal_intro | Economic Appeal | GENERATED | 600 | yes | Investment thesis paragraph |
| economic_stats_handover | Economic Appeal | EXTRACTED | - | yes | QX 20XX |
| economic_stats_roi | Economic Appeal | GENERATED | - | no | From market verification, NOT PDF |
| economic_stats_area_from | Economic Appeal | EXTRACTED | - | yes | Size range sq.ft |
| economic_stats_residences | Economic Appeal | EXTRACTED | - | yes | Bedroom types |
| rental_appeal_h3 | Economic Appeal | STATIC | - | yes | Subsection header: For Rent |
| rental_appeal | Economic Appeal | GENERATED | 250 | yes | For Rent subsection |
| resale_appeal_h3 | Economic Appeal | STATIC | - | yes | Subsection header: For Resale |
| resale_appeal | Economic Appeal | GENERATED | 250 | yes | For Resale subsection |
| enduser_appeal_h3 | Economic Appeal | STATIC | - | yes | Subsection header: For Living |
| enduser_appeal | Economic Appeal | GENERATED | 250 | yes | For Living subsection |
| payment_plan_h2 | Payment Plan | GENERATED | 70 | yes | Attractive [X/X] Payment Plan from [Developer] |
| payment_down_payment | Payment Plan | EXTRACTED | - | yes | Percentage |
| payment_on_construction | Payment Plan | EXTRACTED | - | yes | Percentage |
| payment_on_handover | Payment Plan | EXTRACTED | - | yes | Percentage |
| location_h2 | Location | STATIC | - | yes | "Location" |
| location_overview | Location | GENERATED | 700 | yes | 2 paragraphs |
| area_card_style | Location | GENERATED | 30 | yes | Island, Waterfront, Urban |
| area_card_focal_point | Location | GENERATED | 60 | yes | Main landmark/road |
| area_card_accessibility | Location | GENERATED | 80 | yes | Airport with drive time |
| area_card_shopping_1 | Location | GENERATED | 80 | yes | Mall with drive time |
| area_card_shopping_2 | Location | GENERATED | 80 | yes | Mall with drive time |
| area_card_shopping_3 | Location | GENERATED | 80 | no | Mall with drive time |
| area_card_shopping_4 | Location | GENERATED | 80 | no | Mall with drive time |
| entertainment_h3 | Location | STATIC | - | yes | Subsection header: Entertainment |
| area_card_entertainment_1 | Location | GENERATED | 80 | yes | Attraction with drive time |
| area_card_entertainment_2 | Location | GENERATED | 80 | yes | Attraction with drive time |
| area_card_entertainment_3 | Location | GENERATED | 80 | yes | Attraction with drive time |
| area_card_entertainment_4 | Location | GENERATED | 80 | yes | Attraction with drive time |
| area_card_entertainment_5 | Location | GENERATED | 80 | no | Attraction with drive time |
| area_card_entertainment_6 | Location | GENERATED | 80 | no | Attraction with drive time |
| healthcare_h3 | Location | STATIC | - | yes | Subsection header: Healthcare |
| healthcare_facility_1 | Location | GENERATED | 80 | yes | Healthcare facility with drive time |
| healthcare_facility_2 | Location | GENERATED | 80 | no | Healthcare facility with drive time |
| education_h3 | Location | STATIC | - | yes | Subsection header: Education |
| education_nurseries | Location | GENERATED | 80 | yes | Nurseries info |
| education_international_schools | Location | GENERATED | 80 | yes | International schools info |
| education_secondary_schools | Location | GENERATED | 80 | no | Secondary schools info |
| education_universities | Location | GENERATED | 80 | no | Universities info |
| faq_h2 | FAQ | STATIC | - | yes | "FAQ" |
| faq_1_question | FAQ | GENERATED | 80 | yes | Where is [Project] located? |
| faq_1_answer | FAQ | GENERATED | 200 | yes | Location details |
| faq_2_question | FAQ | GENERATED | 80 | yes | Who is the developer? |
| faq_2_answer | FAQ | GENERATED | 200 | yes | Developer details |
| faq_3_question | FAQ | GENERATED | 80 | yes | What types available? |
| faq_3_answer | FAQ | HYBRID | 200 | yes | Uses extracted floor plan data |
| faq_4_question | FAQ | GENERATED | 80 | yes | Starting price? |
| faq_4_answer | FAQ | HYBRID | 200 | yes | Uses extracted price |
| faq_5_question | FAQ | GENERATED | 80 | yes | Payment plans? |
| faq_5_answer | FAQ | HYBRID | 200 | yes | Uses extracted payment data |
| faq_6_question | FAQ | GENERATED | 80 | yes | Completion date? |
| faq_6_answer | FAQ | GENERATED | 200 | yes | Handover details |
| faq_7_question | FAQ | GENERATED | 80 | yes | Unique FAQ 1 |
| faq_7_answer | FAQ | GENERATED | 200 | yes | Project-specific |
| faq_8_question | FAQ | GENERATED | 80 | yes | Unique FAQ 2 |
| faq_8_answer | FAQ | GENERATED | 200 | yes | Project-specific |
| faq_9_question | FAQ | GENERATED | 80 | yes | Unique FAQ 3 |
| faq_9_answer | FAQ | GENERATED | 200 | yes | Project-specific |
| faq_10_question | FAQ | GENERATED | 80 | yes | Unique FAQ 4 (area/community) |
| faq_10_answer | FAQ | GENERATED | 200 | yes | About the area |
| faq_11_question | FAQ | GENERATED | 80 | yes | Unique FAQ 5 |
| faq_11_answer | FAQ | GENERATED | 200 | yes | Project-specific |
| faq_12_question | FAQ | GENERATED | 80 | yes | Unique FAQ 6 |
| faq_12_answer | FAQ | GENERATED | 200 | yes | Project-specific |

## Section Order

1. SEO
2. Hero
3. About
4. Floor Plans
5. Amenities
6. Developer
7. Economic Appeal
8. Payment Plan
9. Location
10. FAQ

## Notes

### Dynamic Fields

The following fields are variable-count based on brochure content:

- **Floor Plans:** 2-8+ unit types. Each has: type, area, price, suite, balcony
- **Amenities List:** 8-14 bullet items
- **Shopping:** 2-4 items
- **Entertainment:** 4-6 items

### Static Sections (Not in Registry)

These sections appear on the page but are NOT generated:

- Gallery (images managed by content team)
- Get a Free Consultation (form)
- About Company (company info)
- Download Brochure (form)
- Project Materials (brochure/floor plan links)
- Similar Projects (auto-populated)

### Field Type Clarification

| Type | Count | Needs Prompt | Written to Sheet |
|------|-------|--------------|------------------|
| GENERATED | 48 | YES | YES |
| EXTRACTED | 29 | NO | YES |
| HYBRID | 5 | YES | YES |
| STATIC | 3 | NO | NO |

### Discrepancies with Current template_fields.py

The current `backend/app/services/template_fields.py` ADRE section (lines 286-348) has significant gaps:

**Missing entirely:**
- About section (about_h2, about_description)
- Project Card fields (developer, area_from, apartments, penthouses, villas, townhouses, total_units, payment_plan)
- Floor Plans section
- Payment Plan section (payment_h2, down_payment, on_construction, on_handover)
- Economic Appeal intro paragraph
- Economic stats cards (handover, roi, area_from, residences)
- Location area card (style, focal_point, accessibility, shopping items)

**Incorrect structure:**
- Current has entertainment_1/2/3, healthcare_1/2/3, education_1/2/3
- Live site shows shopping and entertainment categories in area card, not healthcare/education
- FAQ count is 8, should be 12

### Row Mapping (Google Sheet)

Based on TEMPLATES_REFERENCE.md, ADRE Template rows:
- SEO: rows 2-8
- Hero: rows 10-16
- About: rows 17-24 (estimated)
- Floor Plans: rows 26-44 (estimated, dynamic)
- Amenities: rows 18-41 (per TEMPLATES_REFERENCE)
- Developer: rows 45-47
- Economic Appeal: rows 49-63
- Payment Plan: rows 64-70 (estimated)
- Location: rows 65-84
- FAQ: rows 86-119

**Note:** Exact row numbers need verification against the actual ADRE Template tab in the PDP Master Google Sheet.

### Character Limits Summary

| Section | Min | Max | Target |
|---------|-----|-----|--------|
| SEO (all fields) | - | 410 | 350 |
| Hero H1 | 50 | 70 | 60 |
| Hero Marketing H2 | 40 | 60 | 50 |
| About Description | 600 | 900 | 750 |
| Developer Description | 150 | 300 | 225 |
| Economic Appeal Intro | 400 | 600 | 500 |
| Rental/Resale/Enduser | 150 | 250 | 200 |
| Location Overview | 400 | 700 | 550 |
| FAQ Answer | 100 | 200 | 150 |
| Total Generated | 3,500 | 6,500 | 5,000 |
