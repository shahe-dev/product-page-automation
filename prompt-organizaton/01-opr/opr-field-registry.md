# OPR Field Registry

Template type: `opr`
Target site: `opr.ae`
Total fields: 71
Generated fields: 52
Extracted fields: 19

## Field Table

| field_name | section | type | char_limit | required | notes |
|------------|---------|------|------------|----------|-------|
| meta_title | SEO | GENERATED | 60 | yes | Format: [Project Name] by [Developer] \| [Location] |
| meta_description | SEO | GENERATED | 156 | yes | Must include: luxury aspect, location, investment appeal, visa, handover |
| url_slug | SEO | GENERATED | - | yes | lowercase-hyphens |
| image_alt | SEO | GENERATED | 125 | yes | Factual, no adjectives |
| h1 | Hero | GENERATED | 70 | yes | Project Name + Location optional |
| hero_subheading | Hero | GENERATED | 150 | yes | One differentiator, no adjectives |
| starting_price | Hero | EXTRACTED | - | yes | AED X.XM format from PDF |
| payment_plan_display | Hero | EXTRACTED | - | yes | X/X format |
| handover | Hero | EXTRACTED | - | yes | QX 20XX format |
| roi_potential | Hero | EXTRACTED | - | no | From market verification, not PDF. TBA if unverified |
| overview_h2 | Overview | GENERATED | 50 | yes | Format: "Overview of [Project Name]" |
| overview_description | Overview | GENERATED | 500 | yes | One paragraph: what, where, positioning. No amenities/prices |
| overview_bullet_1 | Overview | EXTRACTED | - | yes | Bedroom mix from PDF |
| overview_bullet_2 | Overview | EXTRACTED | - | yes | Property types from PDF |
| overview_bullet_3 | Overview | EXTRACTED | - | yes | Unit size range from PDF |
| overview_bullet_4 | Overview | EXTRACTED | - | yes | Area positioning from PDF |
| overview_bullet_5 | Overview | EXTRACTED | - | no | Key differentiator from PDF |
| overview_bullet_6 | Overview | EXTRACTED | - | no | Additional highlight from PDF |
| location_access_h3 | Location Access | GENERATED | - | yes | Section header |
| location_access_1 | Location Access | GENERATED | 60 | yes | Format: Name -- X minutes |
| location_access_2 | Location Access | GENERATED | 60 | yes | Format: Name -- X minutes |
| location_access_3 | Location Access | GENERATED | 60 | yes | Format: Name -- X minutes |
| location_access_4 | Location Access | GENERATED | 60 | yes | Format: Name -- X minutes |
| location_access_5 | Location Access | GENERATED | 60 | yes | Format: Name -- X minutes |
| location_access_6 | Location Access | GENERATED | 60 | yes | Format: Name -- X minutes |
| location_access_7 | Location Access | GENERATED | 60 | no | Format: Name -- X minutes |
| location_access_8 | Location Access | GENERATED | 60 | no | Format: Name -- X minutes |
| card_starting_price | Project Details Card | EXTRACTED | - | yes | From PDF |
| card_handover | Project Details Card | EXTRACTED | - | yes | From PDF |
| card_payment_plan | Project Details Card | EXTRACTED | - | yes | From PDF |
| card_area | Project Details Card | EXTRACTED | - | yes | [min]-[max] sq ft |
| card_property_type | Project Details Card | EXTRACTED | - | yes | Apartments, Villas, Townhouses |
| card_bedrooms | Project Details Card | EXTRACTED | - | yes | Studio, 1BR, 2BR, 3BR |
| card_developer | Project Details Card | EXTRACTED | - | yes | From PDF |
| card_location | Project Details Card | EXTRACTED | - | yes | From PDF |
| amenities_h3 | Amenities | GENERATED | - | yes | Section header |
| amenities_intro | Amenities | GENERATED | 200 | yes | Simple functional description |
| amenity_bullet_1 | Amenities | GENERATED | 30 | yes | Actual feature, not design feel |
| amenity_bullet_2 | Amenities | GENERATED | 30 | yes | Actual feature, not design feel |
| amenity_bullet_3 | Amenities | GENERATED | 30 | yes | Actual feature, not design feel |
| amenity_bullet_4 | Amenities | GENERATED | 30 | yes | Actual feature, not design feel |
| amenity_bullet_5 | Amenities | GENERATED | 30 | yes | Actual feature, not design feel |
| amenity_bullet_6 | Amenities | GENERATED | 30 | yes | Actual feature, not design feel |
| amenity_bullet_7 | Amenities | GENERATED | 30 | yes | Actual feature, not design feel |
| amenity_bullet_8 | Amenities | GENERATED | 30 | yes | Actual feature, not design feel |
| amenity_bullet_9 | Amenities | GENERATED | 30 | no | Actual feature, not design feel |
| amenity_bullet_10 | Amenities | GENERATED | 30 | no | Actual feature, not design feel |
| amenity_bullet_11 | Amenities | GENERATED | 30 | no | Actual feature, not design feel |
| amenity_bullet_12 | Amenities | GENERATED | 30 | no | Actual feature, not design feel |
| amenity_bullet_13 | Amenities | GENERATED | 30 | no | Actual feature, not design feel |
| amenity_bullet_14 | Amenities | GENERATED | 30 | no | Actual feature, not design feel |
| property_types_h3 | Floor Plans | GENERATED | 200 | yes | Intro sentence describing configurations |
| property_types_table | Floor Plans | EXTRACTED | - | yes | Multi-line: Unit Type \| Size \| Price per line |
| payment_plan_h3 | Payment Plan | GENERATED | - | yes | Format: "[X/X] Payment Plan" |
| payment_plan_description | Payment Plan | GENERATED | 200 | yes | Standardized sentence format |
| payment_milestones | Payment Plan | EXTRACTED | - | yes | X% -- On Booking, X% -- During Construction, X% -- On Handover |
| investment_h2 | Investment | GENERATED | - | yes | Format: "Investment Opportunities at [Project Name]" |
| investment_intro | Investment | GENERATED | 200 | yes | Brief investment thesis |
| investment_bullet_1 | Investment | GENERATED | 100 | yes | ROI or rental data (verified) |
| investment_bullet_2 | Investment | GENERATED | 100 | yes | Investment metric |
| investment_bullet_3 | Investment | GENERATED | 100 | yes | Investment metric |
| investment_bullet_4 | Investment | GENERATED | 100 | yes | Investment metric |
| investment_bullet_5 | Investment | GENERATED | 100 | no | Investment metric |
| investment_bullet_6 | Investment | GENERATED | 100 | no | Investment metric |
| area_h2 | Area | GENERATED | - | yes | Format: "About [Area Name]" |
| area_description | Area | GENERATED | 400 | yes | 1-3 sentences about district, not project location |
| lifestyle_h3 | Area | GENERATED | - | yes | Static: "Lifestyle & Attractions" |
| lifestyle_description | Area | GENERATED | 200 | yes | 1-2 sentences, factual |
| lifestyle_bullet_1 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| lifestyle_bullet_2 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| lifestyle_bullet_3 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| lifestyle_bullet_4 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| healthcare_h3 | Area | GENERATED | - | yes | Static: "Premier Healthcare" |
| healthcare_description | Area | GENERATED | 200 | yes | 1-2 sentences, factual |
| healthcare_bullet_1 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| healthcare_bullet_2 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| healthcare_bullet_3 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| education_h3 | Area | GENERATED | - | yes | Static: "Top-Tier Education" |
| education_description | Area | GENERATED | 200 | yes | 1-2 sentences, factual |
| education_bullet_1 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| education_bullet_2 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| education_bullet_3 | Area | GENERATED | 60 | yes | Format: Name -- X minutes |
| developer_h2 | Developer | GENERATED | - | yes | Format: "About [Developer Name]" |
| developer_description | Developer | GENERATED | 300 | yes | 1-3 factual sentences |
| faq_h2 | FAQ | GENERATED | - | yes | Format: "FAQ About [Project Name]" |
| faq_1_question | FAQ | GENERATED | 100 | yes | Topic: Location. Must mention project name |
| faq_1_answer | FAQ | GENERATED | 200 | yes | Must mention project name |
| faq_2_question | FAQ | GENERATED | 100 | yes | Topic: Developer |
| faq_2_answer | FAQ | GENERATED | 200 | yes | |
| faq_3_question | FAQ | GENERATED | 100 | yes | Topic: Property types |
| faq_3_answer | FAQ | GENERATED | 200 | yes | |
| faq_4_question | FAQ | GENERATED | 100 | yes | Topic: Starting price |
| faq_4_answer | FAQ | GENERATED | 200 | yes | |
| faq_5_question | FAQ | GENERATED | 100 | yes | Topic: Payment plan |
| faq_5_answer | FAQ | GENERATED | 200 | yes | |
| faq_6_question | FAQ | GENERATED | 100 | yes | Topic: Handover |
| faq_6_answer | FAQ | GENERATED | 200 | yes | |
| faq_7_question | FAQ | GENERATED | 100 | yes | Topic: ROI/rental yield |
| faq_7_answer | FAQ | GENERATED | 200 | yes | |
| faq_8_question | FAQ | GENERATED | 100 | yes | Topic: Capital appreciation |
| faq_8_answer | FAQ | GENERATED | 200 | yes | |
| faq_9_question | FAQ | GENERATED | 100 | yes | Topic: Visa eligibility |
| faq_9_answer | FAQ | GENERATED | 200 | yes | |
| faq_10_question | FAQ | GENERATED | 100 | yes | Topic: Key amenities |
| faq_10_answer | FAQ | GENERATED | 200 | yes | |
| faq_11_question | FAQ | GENERATED | 100 | yes | Topic: Transport access |
| faq_11_answer | FAQ | GENERATED | 200 | yes | |
| faq_12_question | FAQ | GENERATED | 100 | yes | Topic: Nearby retail/dining |
| faq_12_answer | FAQ | GENERATED | 200 | yes | |
| faq_13_question | FAQ | GENERATED | 100 | yes | Topic: Lifestyle |
| faq_13_answer | FAQ | GENERATED | 200 | yes | |
| faq_14_question | FAQ | GENERATED | 100 | yes | Topic: Living experience |
| faq_14_answer | FAQ | GENERATED | 200 | yes | |

## Section Order

1. SEO
2. Hero
3. Overview
4. Location Access
5. Project Details Card
6. Amenities
7. Floor Plans
8. Payment Plan
9. Investment
10. Area
11. Developer
12. FAQ

## Discrepancies with template_fields.py

The current `OPR_FIELDS` in `template_fields.py` is incomplete:

| Issue | Current | Required |
|-------|---------|----------|
| FAQ pairs | 12 | 14 |
| Hero EXTRACTED fields | Missing | starting_price, payment_plan_display, handover, roi_potential |
| Project Details Card | Missing | 8 fields (card_*) |
| Overview bullets | Missing | 6 EXTRACTED fields |
| Floor Plans table | Missing | property_types_table |
| Payment milestones | Missing | payment_milestones |
| Section headers (H2/H3) | Missing most | 12 header fields |
| Area sub-descriptions | Missing | lifestyle_description, healthcare_description, education_description |
| Amenity bullets | 8 max | 14 max |
| Investment bullets | 4 max | 6 max |
| Location access | 6 max | 8 max |

## Dynamic Fields Note

Several fields are variable-count based on PDF content:
- `overview_bullet_*`: 4-6 bullets
- `location_access_*`: 6-8 bullets
- `amenity_bullet_*`: 8-14 bullets
- `investment_bullet_*`: 4-6 bullets
- `lifestyle_bullet_*`: 4+ bullets
- `healthcare_bullet_*`: 3+ bullets
- `education_bullet_*`: 3+ bullets
- `property_types_table`: 2-8+ lines (multi-line single field)

The registry lists maximum slots. Implementation should handle variable counts without requiring all slots.
