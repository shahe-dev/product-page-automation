# Commercial Field Registry

Template type: `commercial`
Target site: `commercial.main-portal.com`
Total fields: 66
Generated fields: 44
Extracted fields: 14
Hybrid fields: 5
Static fields: 3

## Field Table

| field_name | section | type | char_limit | required | notes |
|------------|---------|------|------------|----------|-------|
| meta_title | SEO | GENERATED | 70 | yes | [Project Name] \| Commercial Property in [Location] |
| meta_description | SEO | GENERATED | 165 | yes | Include property types, price, location |
| url_slug | SEO | GENERATED | - | yes | lowercase-hyphens: project-name-location-emirate |
| h1 | Hero | GENERATED | 60 | yes | [Project Name] by [Developer] |
| hero_description | Hero | GENERATED | 80 | yes | Single sentence commercial positioning |
| hero_sale_price | Hero | EXTRACTED | - | yes | Starting price from PDF |
| hero_payment_plan | Hero | EXTRACTED | - | yes | Payment plan ratio from PDF (e.g., 60/40) |
| hero_handover | Hero | EXTRACTED | - | yes | Handover date from PDF |
| hero_feature_1_title | Hero | GENERATED | 30 | yes | Feature highlight |
| hero_feature_1_description | Hero | GENERATED | 60 | yes | Feature detail |
| hero_feature_2_title | Hero | GENERATED | 30 | yes | Feature highlight |
| hero_feature_2_description | Hero | GENERATED | 60 | yes | Feature detail |
| hero_feature_3_title | Hero | GENERATED | 30 | yes | Feature highlight |
| hero_feature_3_description | Hero | GENERATED | 60 | yes | Feature detail |
| about_h2 | About | GENERATED | 50 | yes | About [Project Name] |
| about_h3 | About | GENERATED | 80 | yes | Descriptive subtitle with area mention |
| about_paragraph | About | HYBRID | 200 | yes | Summary embedding extracted data |
| project_passport | Project Passport | STATIC | - | yes | Section header: Project Passport |
| passport_developer | Project Passport | EXTRACTED | - | yes | Verbatim from PDF |
| passport_location | Project Passport | EXTRACTED | - | yes | Area + emirate from PDF |
| passport_payment_plan | Project Passport | EXTRACTED | - | yes | X/X format from PDF |
| passport_area_range | Project Passport | EXTRACTED | - | yes | X-X sq.ft from PDF |
| passport_property_type | Project Passport | EXTRACTED | - | yes | Office/Retail/F&B from PDF |
| payment_plan_title | Payment Plan | GENERATED | 30 | yes | [X/X] Payment Plan |
| payment_plan_headline | Payment Plan | GENERATED | 60 | yes | Headline for payment plan section |
| payment_plan_description | Payment Plan | HYBRID | 150 | yes | Description embedding extracted plan |
| construction_percentage | Payment Plan | EXTRACTED | - | yes | X% during construction |
| handover_date | Payment Plan | EXTRACTED | - | yes | QX 20XX format |
| handover_percentage | Payment Plan | EXTRACTED | - | yes | X% on handover |
| advantage_1_title | Advantages | GENERATED | 80 | yes | Main advantage title |
| advantage_1_description | Advantages | GENERATED | 200 | yes | Advantage detail |
| advantage_2_title | Advantages | GENERATED | 80 | yes | Main advantage title |
| advantage_2_description | Advantages | GENERATED | 200 | yes | Advantage detail |
| advantage_3_title | Advantages | GENERATED | 80 | yes | Main advantage title |
| advantage_3_description | Advantages | GENERATED | 200 | yes | Advantage detail |
| amenity_1_title | Amenities | GENERATED | 80 | yes | Feature/amenity title |
| amenity_1_description | Amenities | GENERATED | 200 | yes | Feature/amenity detail |
| amenity_2_title | Amenities | GENERATED | 80 | yes | Feature/amenity title |
| amenity_2_description | Amenities | GENERATED | 200 | yes | Feature/amenity detail |
| amenity_3_title | Amenities | GENERATED | 80 | yes | Feature/amenity title |
| amenity_3_description | Amenities | GENERATED | 200 | yes | Feature/amenity detail |
| amenity_4_title | Amenities | GENERATED | 80 | yes | Feature/amenity title |
| amenity_4_description | Amenities | GENERATED | 200 | yes | Feature/amenity detail |
| amenity_5_title | Amenities | GENERATED | 80 | yes | Feature/amenity title |
| amenity_5_description | Amenities | GENERATED | 200 | yes | Feature/amenity detail |
| location_h2 | Location | STATIC | - | yes | Section header: Location |
| location_h3 | Location | GENERATED | 80 | yes | Location advantages subtitle |
| location_description | Location | HYBRID | 400 | yes | Strategic positioning, connectivity |
| social_facilities_description | Location | GENERATED | 300 | yes | Nearby social/lifestyle facilities |
| social_facility_1 | Location | GENERATED | 80 | yes | [Name] - [X] min |
| social_facility_2 | Location | GENERATED | 80 | yes | [Name] - [X] min |
| social_facility_3 | Location | GENERATED | 80 | yes | [Name] - [X] min |
| education_medicine_description | Location | GENERATED | 300 | yes | Nearby educational/medical institutions |
| education_nearby_1 | Location | GENERATED | 80 | yes | [Name] - [X] min |
| education_nearby_2 | Location | GENERATED | 80 | yes | [Name] - [X] min |
| education_nearby_3 | Location | GENERATED | 80 | yes | [Name] - [X] min |
| culture_description | Location | GENERATED | 300 | yes | Nearby cultural establishments |
| culture_nearby_1 | Location | GENERATED | 80 | yes | [Name] - [X] min |
| culture_nearby_2 | Location | GENERATED | 80 | yes | [Name] - [X] min |
| culture_nearby_3 | Location | GENERATED | 80 | yes | [Name] - [X] min |
| developer_h2 | Developer | STATIC | - | yes | Section header: About the Developer |
| developer_h3 | Developer | GENERATED | 60 | yes | Developer highlight subtitle |
| developer_name | Developer | EXTRACTED | - | yes | Verbatim from PDF |
| developer_description | Developer | GENERATED | 250 | yes | Track record, notable projects |

## Section Order

1. SEO
2. Hero
3. About
4. Project Passport
5. Economic Appeal (STATIC - no generated fields)
6. Gallery (STATIC - no generated fields)
7. Payment Plan
8. After Completion Options (STATIC - no generated fields)
9. Advantages
10. Amenities
11. Location
12. Developer

## Static Sections (excluded from field registry)

The following sections are fully static and require no content generation:

- **Economic Appeal**: Fixed investment appeal content
- **Gallery**: Image-only section
- **After Completion Options**: Fixed 3 options content
- **The Dubai Plan Block**: Fixed infographic content

## Discrepancies with template_fields.py

The current `COMMERCIAL_FIELDS` in `template_fields.py` has discrepancies with the live website:

| Issue | Current Code | Should Be |
|-------|--------------|-----------|
| Hero features | Uses `economic_indicator_1-3_label/value` | Should be `hero_feature_1-3_title/description` |
| About section | `area_h2`, `area_description` | Should be `about_h2`, `about_h3`, `about_paragraph` |
| Project Passport | `project_passport_h2`, `project_passport_description` | Should be individual extracted fields |
| Economic Appeal | Has `economic_appeal_h2`, `economic_appeal_description` | Section is STATIC, no generated fields |
| Location subsections | Missing culture, education/medicine descriptions | Needs `education_medicine_description`, `culture_description` |
| Medical fields | Has `medical_nearby_1-3` separate | Should be combined with education in `education_nearby_1-3` |

## Notes

1. **Commercial vs Residential Terminology**: This template uses commercial real estate terminology (tenants, occupiers, Grade A specifications) rather than residential terminology (residents, homeowners).

2. **Project Passport**: All fields in Project Passport are EXTRACTED directly from the developer PDF. These populate a data table, not prose content.

3. **Payment Plan**: The X/X format (e.g., 60/40) must be consistent across all references in the page.

4. **Location Subsections**: The Location section has 4 distinct subsections:
   - Location & Advantages (main description)
   - Social Facilities (lifestyle/retail)
   - Education & Medicine (combined section)
   - Culture (entertainment/attractions)

5. **Amenities**: The "Why You Will Love This Place" section lists 5 features/amenities. These should focus on building specifications and facilities relevant to commercial tenants (lobbies, parking, elevators, fit-out, security).
