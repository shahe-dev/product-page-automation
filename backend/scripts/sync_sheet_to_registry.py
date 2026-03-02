"""
Sync Google Sheet template to field registry (source of truth).

This script:
1. Parses the field registry markdown for a template
2. Reads the current Google Sheet state
3. Computes the diff (missing fields, wrong char limits, etc.)
4. Applies changes via Sheets API
5. Re-validates to confirm zero gaps

Usage:
    python sync_sheet_to_registry.py <template>  # e.g., opr, adop, aggregators
    python sync_sheet_to_registry.py --all       # sync all 6 templates
    python sync_sheet_to_registry.py <template> --dry-run  # preview changes only
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gspread
from google.oauth2.service_account import Credentials

# Paths
CREDS_PATH = Path(__file__).resolve().parent.parent.parent / ".credentials" / "service-account-key.json"
REGISTRY_BASE = Path(__file__).resolve().parent.parent.parent / "prompt-organizaton"

# Scopes (read/write for sync)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Template sheet IDs (from docs/plans/2026-01-31-pipeline-codebase-gaps.md)
SHEET_IDS = {
    "aggregators": "YOUR_AGGREGATORS_SHEET_ID",
    "opr": "YOUR_OPR_SHEET_ID",
    "mpp": "YOUR_MPP_SHEET_ID",
    "adop": "YOUR_ADOP_SHEET_ID",
    "adre": "YOUR_ADRE_SHEET_ID",
    "commercial": "YOUR_COMMERCIAL_SHEET_ID",
}

# Template folder mapping
TEMPLATE_FOLDERS = {
    "opr": "01-opr",
    "adop": "02-adop",
    "adre": "03-adre",
    "commercial": "04-commercial",
    "aggregators": "05-aggregators",
    "mpp": "06-mpp",
}

# Explicit field label to registry field name mappings per template
# These override automatic title_to_snake() conversion for non-standard labels
FIELD_LABEL_MAPPINGS = {
    "opr": {
        # SEO
        "Meta title:": "meta_title",
        "Meta description:": "meta_description",
        "Url Slug": "url_slug",
        "Image Alt Tag": "image_alt",
        # Hero
        "H1: Project + developer (or area)": "h1",
        # Overview
        "H2: Project overview": "overview_h2",
        # Amenities
        "H3: Features and amenities": "amenities_h3",
        # Floor Plans
        "H3: Property types & pricing": "property_types_h3",
        # Payment Plan
        "H3: Payment plan": "payment_plan_h3",
        "PP short description": "payment_plan_description",
        # Investment
        "H2: Investment opportunities": "investment_h2",
        # Area
        "H2: About the area": "area_h2",
        "H3: Lifestyle & attractions": "lifestyle_h3",
        "H3: Healthcare": "healthcare_h3",
        "H3: Education": "education_h3",
        # Developer
        "H2: About the developer": "developer_h2",
        # FAQ
        "H2: FAQ about the project": "faq_h2",
        "General: Location": "faq_1_question",
        "General: Developer": "faq_2_question",
        "General: Type": "faq_3_question",
        "Pricing & Investment: Starting Price": "faq_4_question",
        "Pricing & Investment: Payment Plan": "faq_5_question",
        "Pricing & Investment: Handover": "faq_6_question",
        "Pricing & Investment": "faq_7_question",  # ROI
        # Note: Row 183 and 189 also have "Pricing & Investment" - need context
        "Pricing & Investment (Visa)": "faq_9_question",
        "Amenities & Connectivity": "faq_10_question",  # First one
        "Lifestyle and living experience": "faq_13_question",  # First one
        # Card fields
        "Starting Price": "starting_price",  # Hero
        "Payment Plan": "payment_plan_display",  # Hero
        "Handover": "handover",  # Hero
        "ROI Potential": "roi_potential",  # Hero
        # Payment section - multiple milestone rows map to single payment_milestones field
        "Milestone: On Handover": "payment_milestones",
        "Milestone: During Construction": "payment_milestones",
        "Milestone: On Booking": "payment_milestones",
    },
    "adop": {
        # SEO
        "URL Slug": "url_slug",
        "Meta Title": "meta_title",
        "Meta Description": "meta_description",
        "Image Alt Tag": "image_alt_tag",
        # Hero
        "Hero H1": "hero_h1",
        "Hero Sub Title": "hero_subtitle",
        "Starting Price": "starting_price",
        "Handover": "handover",
        # About
        "About Project H2": "about_h2",
        "About Paragraph 1": "about_paragraph_1",
        "About Paragraph 2": "about_paragraph_2",
        "About Paragraph 3": "about_paragraph_3",
        # Key Benefits
        "Key Benefits H2": "key_benefits_h2",
        "Key Benefits Paragraph 1": "key_benefits_paragraph_1",
        "Key Benefits Paragraph 2": "key_benefits_paragraph_2",
        # Area Infrastructure
        "H2": "area_infrastructure_h2",
        "Infrastructure Paragraph 1": "infrastructure_paragraph_1",
        "Infrastructure Paragraph 2": "infrastructure_paragraph_2",
        "Infrastructure Paragraph 3": "infrastructure_paragraph_3",
        # Location
        "Location H2": "location_h2",
        "Location Overview": "location_overview",
        "Location Key Attractions": "location_key_attractions",
        "Location Major Destinations": "location_major_destinations",
        "Location Drive Time Summary": "location_drive_time_summary",
        # Investment
        "Investment (Previously Economic Appeal) H2": "investment_h2",
        "Investment (Previously Economic Appeal) Text 1": "investment_paragraph_1",
        "Investment (Previously Economic Appeal) Text 2": "investment_paragraph_2",
        "Investment (Previously Economic Appeal) Text 3": "investment_paragraph_3",
        "Investment (Previously Economic Appeal) Text 4": "investment_paragraph_4",
        # Developer
        "Developer": "developer",
        "Developer H2": "developer_h2",
        "Developer Description": "developer_description",
        # FAQ
        "Faq H2": "faq_h2",
        "FAQ 1 - Question": "faq_1_question",
        "FAQ 1 - Answer": "faq_1_answer",
        "FAQ 2 - Question": "faq_2_question",
        "FAQ 2 - Answer": "faq_2_answer",
        "FAQ 3 - Question": "faq_3_question",
        "FAQ 3 - Answer": "faq_3_answer",
        "FAQ 4 - Question": "faq_4_question",
        "FAQ 4 - Answer": "faq_4_answer",
        "FAQ 5 - Question": "faq_5_question",
        "FAQ 5 - Answer": "faq_5_answer",
        "FAQ 6 - Question": "faq_6_question",
        "FAQ 6 - Answer": "faq_6_answer",
        "FAQ 7 - Question": "faq_7_question",
        "FAQ 7 - Answer": "faq_7_answer",
        "FAQ 8 - Question": "faq_8_question",
        "FAQ 8 - Answer": "faq_8_answer",
        "FAQ 9 - Question": "faq_9_question",
        "FAQ 9 - Answer": "faq_9_answer",
        "FAQ 10 - Question": "faq_10_question",
        "FAQ 10 - Answer": "faq_10_answer",
        "FAQ 11 - Question": "faq_11_question",
        "FAQ 11 - Answer": "faq_11_answer",
        "FAQ 12 - Question": "faq_12_question",
        "FAQ 12 - Answer": "faq_12_answer",
    },
    "adre": {
        # SEO (no colons in current sheet)
        "Slug": "url_slug",
        "Title": "meta_title",
        "Desc": "meta_description",
        "Image alt tag": "image_alt",
        # About
        "Project name": "project_name",
        "H1": "h1",
        "About H2": "about_h2",
        "About Description": "about_description",
        "Project Card - Townhouses": "project_card_townhouses",
        "Project Card - Total Units": "project_card_total_units",
        "Project Card - Payment Plan": "project_card_payment_plan",
        # Floor Plans
        "Floor Plans Table": "floor_plans_table",
        # Amenities
        "Amenities H2": "amenities_h2",
        "Amenity 1 - Title": "amenity_1_h3",
        "Amenity 1 - Description": "amenity_1_description",
        "Amenity 2 - Title": "amenity_2_h3",
        "Amenity 2 - Description": "amenity_2_description",
        "Amenity 3 - Title": "amenity_3_h3",
        "Amenity 3 - Description": "amenity_3_description",
        "Amenity 4 - Title": "amenity_4_title",
        "Amenity 5 - Title": "amenity_5_title",
        "Amenity 6 - Title": "amenity_6_title",
        "Amenity 7 - Title": "amenity_7_title",
        "Amenity 8 - Title": "amenity_8_title",
        # Developer
        "Developer H2": "developer_h2",
        "Developer Description": "developer_description",
        # Economic Appeal
        "Economic Appeal H2": "economic_appeal_h2",
        "Economic Overview": "economic_appeal_intro",
        "Rental Appeal H3": "rental_appeal_h3",
        "Rental Appeal Description": "rental_appeal",
        "Resale Appeal H3": "resale_appeal_h3",
        "Resale Appeal Description": "resale_appeal",
        "Living Appeal H3": "enduser_appeal_h3",
        "Living Appeal Description": "enduser_appeal",
        # Payment Plan
        "Payment Plan H2": "payment_plan_h2",
        # Location
        "Location H2": "location_h2",
        "Location Description": "location_overview",
        "Entertainment H3": "entertainment_h3",
        "Entertainment Landmark 1": "area_card_entertainment_1",
        "Entertainment Landmark 2": "area_card_entertainment_2",
        "Entertainment Landmark 3": "area_card_entertainment_3",
        "Entertainment Landmark 4": "area_card_entertainment_4",
        "Healthcare H3": "healthcare_h3",
        "Healthcare Facility 1": "healthcare_facility_1",
        "Healthcare Facility 2": "healthcare_facility_2",
        "Education H3": "education_h3",
        "Education - Nurseries": "education_nurseries",
        "Education - International Schools": "education_international_schools",
        "Education - Secondary Schools": "education_secondary_schools",
        "Education - Universities": "education_universities",
        # FAQ
        "FAQ H2": "faq_h2",
        "FAQ 1 - Question": "faq_1_question",
        "FAQ 1 - Answer": "faq_1_answer",
        "FAQ 2 - Question": "faq_2_question",
        "FAQ 2 - Answer": "faq_2_answer",
        "FAQ 3 - Question": "faq_3_question",
        "FAQ 3 - Answer": "faq_3_answer",
        "FAQ 4 - Question": "faq_4_question",
        "FAQ 4 - Answer": "faq_4_answer",
        "FAQ 5 - Question": "faq_5_question",
        "FAQ 5 - Answer": "faq_5_answer",
        "FAQ 6 - Question": "faq_6_question",
        "FAQ 6 - Answer": "faq_6_answer",
        "FAQ 7 - Question": "faq_7_question",
        "FAQ 7 - Answer": "faq_7_answer",
        "FAQ 8 - Question": "faq_8_question",
        "FAQ 8 - Answer": "faq_8_answer",
        "FAQ 9 - Question": "faq_9_question",
        "FAQ 9 - Answer": "faq_9_answer",
        "FAQ 10 - Question": "faq_10_question",
        "FAQ 10 - Answer": "faq_10_answer",
        "FAQ 11 - Question": "faq_11_question",
        "FAQ 11 - Answer": "faq_11_answer",
        "FAQ 12 - Question": "faq_12_question",
        "FAQ 12 - Answer": "faq_12_answer",
    },
    "commercial": {
        # SEO (new labels without special chars)
        "Meta Title": "meta_title",
        "Meta Description": "meta_description",
        "URL Slug": "url_slug",
        # Hero
        "H1": "h1",
        "Hero Description": "hero_description",
        "Hero - Sale Price": "hero_sale_price",
        "Hero - Payment Plan": "hero_payment_plan",
        "Hero - Handover": "hero_handover",
        # Hero Features
        "Feature 1 - Title": "hero_feature_1_title",
        "Feature 1 - Description": "hero_feature_1_description",
        "Feature 2 - Title": "hero_feature_2_title",
        "Feature 2 - Description": "hero_feature_2_description",
        "Feature 3 - Title": "hero_feature_3_title",
        "Feature 3 - Description": "hero_feature_3_description",
        # About Area
        "About Area H2": "about_h2",
        "About Area H3": "about_h3",
        "About Description": "about_paragraph",
        # Project Passport (section header)
        "Project Passport": "project_passport",
        "Passport - Developer": "passport_developer",
        "Passport - Location": "passport_location",
        "Passport - Payment Plan": "passport_payment_plan",
        "Passport - Area": "passport_area_range",
        "Passport - Property Type": "passport_property_type",
        # Payment Plan
        "Payment Plan H3": "payment_plan_title",
        "Payment Plan Headline": "payment_plan_headline",
        "Payment Plan Description": "payment_plan_description",
        # Advantages
        "Advantage 1 - Title": "advantage_1_title",
        "Advantage 1 - Description": "advantage_1_description",
        "Advantage 2 - Title": "advantage_2_title",
        "Advantage 2 - Description": "advantage_2_description",
        "Advantage 3 - Title": "advantage_3_title",
        "Advantage 3 - Description": "advantage_3_description",
        # Amenities
        "Amenity 1 - Title": "amenity_1_title",
        "Amenity 1 - Description": "amenity_1_description",
        "Amenity 2 - Title": "amenity_2_title",
        "Amenity 2 - Description": "amenity_2_description",
        "Amenity 3 - Title": "amenity_3_title",
        "Amenity 3 - Description": "amenity_3_description",
        "Amenity 4 - Title": "amenity_4_title",
        "Amenity 4 - Description": "amenity_4_description",
        "Amenity 5 - Title": "amenity_5_title",
        "Amenity 5 - Description": "amenity_5_description",
        # Developer
        "Developer H2": "developer_h2",
        "Developer H3": "developer_h3",
        "Developer Name": "developer_name",
        "Developer Description": "developer_description",
        # Location
        "Location H2": "location_h2",
        "Location H3": "location_h3",
        "Location Description": "location_description",
        # Social Facilities
        "Social Facilities Description": "social_facilities_description",
        "Social Facility 1": "social_facility_1",
        "Social Facility 2": "social_facility_2",
        "Social Facility 3": "social_facility_3",
        # Education & Medicine
        "Education & Medicine Description": "education_medicine_description",
        "Education Facility 1": "education_nearby_1",
        "Education Facility 2": "education_nearby_2",
        "Education Facility 3": "education_nearby_3",
        # Culture
        "Culture Description": "culture_description",
        "Culture Venue 1": "culture_nearby_1",
        "Culture Venue 2": "culture_nearby_2",
        "Culture Venue 3": "culture_nearby_3",
    },
    "aggregators": {
        # SEO
        "Meta Title": "meta_title",
        "Meta Description": "meta_description",
        "URL Slug": "url_slug",
        "Image Alt Tag": "image_alt",
        # Hero
        "H1": "hero_h1",
        "Hero Description": "hero_subtitle",
        "Hero Investment Stat 1": "hero_investment_stat_1",
        "Hero Investment Stat 2": "hero_investment_stat_2",
        "Hero Investment Stat 3": "hero_investment_stat_3",
        "Starting Price": "starting_price",
        "Payment Plan": "payment_plan_ratio",
        "Handover": "handover",
        # About
        "About H2": "about_h2",
        "About Description": "about_paragraph",
        # Selling Points (new HYBRID fields)
        "Selling Point 1": "selling_point_1",
        "Selling Point 2": "selling_point_2",
        "Selling Point 3": "selling_point_3",
        "Selling Point 4": "selling_point_4",
        "Selling Point 5": "selling_point_5",
        # Project Details
        "Developer": "project_details_developer",
        "Location": "project_details_location",
        "Property Types": "project_details_property_type",
        "Bedrooms": "project_details_bedrooms",
        "Area": "project_details_area",
        "Payment Plan Display": "project_details_payment_plan",
        # Economic Appeal
        "Economic Appeal H2": "economic_appeal_h2",
        "Economic Appeal Description": "economic_appeal_paragraph",
        # Payment Plan Section
        "Payment H2": "payment_plan_h2",
        "Payment Description": "payment_plan_description",
        "Booking Percentage": "payment_plan_booking_pct",
        "Construction Percentage": "payment_plan_construction_pct",
        "Handover Percentage": "payment_plan_handover_pct",
        # Milestones (EXTRACTED)
        "Milestone 1 - Name": "milestone_1_name",
        "Milestone 1 - Percentage": "milestone_1_percentage",
        "Milestone 1 - Date": "milestone_1_date",
        "Milestone 2 - Name": "milestone_2_name",
        "Milestone 2 - Percentage": "milestone_2_percentage",
        "Milestone 2 - Schedule": "milestone_2_schedule",
        "Milestone 3 - Name": "milestone_3_name",
        "Milestone 3 - Percentage": "milestone_3_percentage",
        "Milestone 3 - Date": "milestone_3_date",
        # Key Features
        "Key Feature 1 Title": "key_feature_1_title",
        "Key Feature 1 Description": "key_feature_1_description",
        "Key Feature 2 Title": "key_feature_2_title",
        "Key Feature 2 Description": "key_feature_2_description",
        "Key Feature 3 Title": "key_feature_3_title",
        "Key Feature 3 Description": "key_feature_3_description",
        # Amenities
        "Amenities H2": "amenities_h2",
        "Amenity 1 Title": "amenity_1_title",
        "Amenity 1 Description": "amenity_1_description",
        "Amenity 2 Title": "amenity_2_title",
        "Amenity 2 Description": "amenity_2_description",
        "Amenity 3 Title": "amenity_3_title",
        "Amenity 3 Description": "amenity_3_description",
        "Amenity 4 Title": "amenity_4_title",
        "Amenity 4 Description": "amenity_4_description",
        "Amenity 5 Title": "amenity_5_title",
        "Amenity 5 Description": "amenity_5_description",
        "Amenity 6 Title": "amenity_6_title",
        "Amenity 6 Description": "amenity_6_description",
        # Developer
        "Developer H2": "developer_h2",
        "Developer Description": "developer_description",
        # Location
        "Location H2": "location_h2",
        "Location Description": "location_overview_paragraph",
        # Nearby (EXTRACTED)
        "Nearby 1 - Name": "nearby_1_name",
        "Nearby 1 - Distance": "nearby_1_distance",
        "Nearby 2 - Name": "nearby_2_name",
        "Nearby 2 - Distance": "nearby_2_distance",
        "Nearby 3 - Name": "nearby_3_name",
        "Nearby 3 - Distance": "nearby_3_distance",
        "Nearby 4 - Name": "nearby_4_name",
        "Nearby 4 - Distance": "nearby_4_distance",
        # Floor Plans (STATIC header + EXTRACTED data)
        "Floor Plans H2": "floor_plans_h2",
        "Unit Type 1 - Name": "unit_type_1_name",
        "Unit Type 1 - Area": "unit_type_1_area",
        "Unit Type 1 - Price": "unit_type_1_price",
        "Unit Type 2 - Name": "unit_type_2_name",
        "Unit Type 2 - Area": "unit_type_2_area",
        "Unit Type 2 - Price": "unit_type_2_price",
        "Unit Type 3 - Name": "unit_type_3_name",
        "Unit Type 3 - Area": "unit_type_3_area",
        "Unit Type 3 - Price": "unit_type_3_price",
        "Unit Type 4 - Name": "unit_type_4_name",
        "Unit Type 4 - Area": "unit_type_4_area",
        "Unit Type 4 - Price": "unit_type_4_price",
        # Social Facilities
        "Social Facilities Intro": "social_facilities_intro",
        "Social Facility 1": "social_facility_1",
        "Social Facility 2": "social_facility_2",
        "Social Facility 3": "social_facility_3",
        # Education/Medicine
        "Education Medicine Intro": "education_medicine_intro",
        "Education Facility 1": "education_facility_1",
        "Education Facility 2": "education_facility_2",
        "Education Facility 3": "education_facility_3",
        # Culture
        "Culture Intro": "culture_intro",
        "Culture Facility 1": "culture_facility_1",
        "Culture Facility 2": "culture_facility_2",
        "Culture Facility 3": "culture_facility_3",
        # FAQ
        "FAQ H2": "faq_h2",
        "FAQ 1 - Question": "faq_1_question",
        "FAQ 1 - Answer": "faq_1_answer",
        "FAQ 2 - Question": "faq_2_question",
        "FAQ 2 - Answer": "faq_2_answer",
        "FAQ 3 - Question": "faq_3_question",
        "FAQ 3 - Answer": "faq_3_answer",
        "FAQ 4 - Question": "faq_4_question",
        "FAQ 4 - Answer": "faq_4_answer",
        "FAQ 5 - Question": "faq_5_question",
        "FAQ 5 - Answer": "faq_5_answer",
        "FAQ 6 - Question": "faq_6_question",
        "FAQ 6 - Answer": "faq_6_answer",
        "FAQ 7 - Question": "faq_7_question",
        "FAQ 7 - Answer": "faq_7_answer",
        "FAQ 8 - Question": "faq_8_question",
        "FAQ 8 - Answer": "faq_8_answer",
        "FAQ 9 - Question": "faq_9_question",
        "FAQ 9 - Answer": "faq_9_answer",
        "FAQ 10 - Question": "faq_10_question",
        "FAQ 10 - Answer": "faq_10_answer",
    },
    "mpp": {
        # SEO
        "Meta title": "meta_title",
        "Meta description": "meta_description",
        "Url Slug": "url_slug",
        "Image Alt Tag": "image_alt_tag",
        # Hero
        "H1: Project + Developer": "hero_h1",
        "Hero Description": "hero_description",
        "Starting Price": "starting_price",
        "Handover": "handover",
        "Down Payment %": "down_payment_percentage",
        # Overview
        "H2: Project Overview": "overview_h2",
        "Overview Description": "overview_description",
        # Project Details
        "Location": "project_location",
        "Developer": "project_developer",
        "Property Types": "project_property_type",
        "Bedrooms": "project_bedrooms",
        # Floor Plans (EXTRACTED)
        "Floor Plan 1 - Bedrooms": "floor_plan_1_bedrooms",
        "Floor Plan 1 - Starting Price": "floor_plan_1_starting_price",
        "Floor Plan 1 - Living Area (m2)": "floor_plan_1_living_area",
        "Floor Plan 2 - Bedrooms": "floor_plan_2_bedrooms",
        "Floor Plan 2 - Starting Price": "floor_plan_2_starting_price",
        "Floor Plan 2 - Living Area (m2)": "floor_plan_2_living_area",
        "Floor Plan 3 - Bedrooms": "floor_plan_3_bedrooms",
        "Floor Plan 3 - Starting Price": "floor_plan_3_starting_price",
        "Floor Plan 3 - Living Area (m2)": "floor_plan_3_living_area",
        "Floor Plan 4 - Bedrooms": "floor_plan_4_bedrooms",
        "Floor Plan 4 - Starting Price": "floor_plan_4_starting_price",
        "Floor Plan 4 - Living Area (m2)": "floor_plan_4_living_area",
        # Payment Plan (EXTRACTED)
        "Payment Plan Type 1": "payment_plan_type_1",
        "Payment Plan Type 2": "payment_plan_type_2",
        "On Booking - Date": "on_booking_date",
        "On Booking - Percentage": "on_booking_percentage",
        "On Construction - Period": "on_construction_period",
        "On Construction - Percentage": "on_construction_percentage",
        "On Construction - Number of Payments": "on_construction_number_of_payments",
        "On Handover - Date": "on_handover_date",
        "On Handover - Percentage": "on_handover_percentage",
        # Key Points
        "Key Point 1 - Title": "key_point_1_title",
        "Key Point 1 - Description": "key_point_1_description",
        "Key Point 1 - Image": "key_point_1_image",
        "Key Point 2 - Title": "key_point_2_title",
        "Key Point 2 - Description": "key_point_2_description",
        "Key Point 2 - Image": "key_point_2_image",
        # Amenities
        "Amenity 1": "amenity_1",
        "Amenity 2": "amenity_2",
        "Amenity 3": "amenity_3",
        "Amenity 4": "amenity_4",
        "Amenity 5": "amenity_5",
        "Amenity 6": "amenity_6",
        "Amenity 7": "amenity_7",
        "Amenity 8": "amenity_8",
        # Location
        "Location Name": "location_name",
        "Location Description": "location_description",
        # Developer
        "H2: About the Developer": "developer_h2",
        "Developer Badge": "developer_badge",
        "Developer Logo": "developer_logo",
        "Developer Name": "developer_name",
        "Developer Description": "developer_description",
        "Developer Stat 1 - Value": "developer_stat_1_value",
        "Developer Stat 1 - Label": "developer_stat_1_label",
        "Developer Stat 2 - Value": "developer_stat_2_value",
        "Developer Stat 2 - Label": "developer_stat_2_label",
        "Developer Stat 3 - Value": "developer_stat_3_value",
        "Developer Stat 3 - Label": "developer_stat_3_label",
        # FAQ
        "H2: FAQ": "faq_h2",
        "FAQ 1 - Question": "faq_1_question",
        "FAQ 1 - Answer": "faq_1_answer",
        "FAQ 2 - Question": "faq_2_question",
        "FAQ 2 - Answer": "faq_2_answer",
        "FAQ 3 - Question": "faq_3_question",
        "FAQ 3 - Answer": "faq_3_answer",
        "FAQ 4 - Question": "faq_4_question",
        "FAQ 4 - Answer": "faq_4_answer",
        "FAQ 5 - Question": "faq_5_question",
        "FAQ 5 - Answer": "faq_5_answer",
        "FAQ 6 - Question": "faq_6_question",
        "FAQ 6 - Answer": "faq_6_answer",
    },
}

# Fields that use <p> or generic labels and need context-based mapping
# Maps (template, section_context) -> field_name
CONTEXTUAL_MAPPINGS = {
    "opr": {
        # Hero subheading
        ("hero", "<p>"): "hero_subheading",
        # Overview
        ("overview", "<p>", 0): "overview_description",
        ("overview", "<p>", 1): "overview_bullets",  # Combined bullets
        # Amenities
        ("amenities", "<p>", 0): "amenities_intro",
        ("amenities", "<p>", 1): "amenity_bullets",  # Combined bullets
        # Investment
        ("investment", None): "investment_intro",
        # Area descriptions
        ("lifestyle", None): "lifestyle_description",
        ("healthcare", None): "healthcare_description",
        ("education", None): "education_description",
        # Developer
        ("developer", None): "developer_description",
    },
}

# Combined bullet fields in sheets that map to multiple individual fields in registry
# Keys match what title_to_snake() produces from sheet labels
# Values are the individual field names from the registry
COMBINED_BULLET_FIELDS = {
    "opr": {
        # Sheet label "Overview Bullet Points" -> title_to_snake() -> "overview_bullet_points"
        "overview_bullet_points": ["overview_bullet_1", "overview_bullet_2", "overview_bullet_3",
                                   "overview_bullet_4", "overview_bullet_5", "overview_bullet_6"],
        # Sheet label "Amenity Bullet Points" -> "amenity_bullet_points"
        "amenity_bullet_points": [f"amenity_bullet_{i}" for i in range(1, 15)],
        # Sheet label "Investment Bullet Points" -> "investment_bullet_points"
        "investment_bullet_points": [f"investment_bullet_{i}" for i in range(1, 7)],
        # Sheet label "Lifestyle Bullets" -> "lifestyle_bullets"
        "lifestyle_bullets": [f"lifestyle_bullet_{i}" for i in range(1, 5)],
        # Sheet label "Healthcare Bullets" -> "healthcare_bullets"
        "healthcare_bullets": [f"healthcare_bullet_{i}" for i in range(1, 4)],
        # Sheet label "Education Bullets" -> "education_bullets"
        "education_bullets": [f"education_bullet_{i}" for i in range(1, 4)],
        # Sheet label "Location Access Bullets" -> "location_access_bullets"
        "location_access_bullets": [f"location_access_{i}" for i in range(1, 9)],
    },
}


@dataclass
class RegistryField:
    """A field from the registry."""
    field_name: str
    section: str
    field_type: str  # GENERATED, EXTRACTED, HYBRID, STATIC
    char_limit: Optional[int]
    required: bool
    notes: str


@dataclass
class SheetRow:
    """A row from the Google Sheet."""
    row_number: int
    guidelines: str
    field_label: str
    en_content: str
    ar_content: str
    ru_content: str


@dataclass
class SyncAction:
    """An action to perform on the sheet."""
    action_type: str  # INSERT, UPDATE_GUIDELINES, DELETE, REORDER
    row_number: Optional[int]
    field_name: str
    details: dict


def parse_registry(template: str) -> list[RegistryField]:
    """Parse field registry markdown and extract fields."""
    folder = TEMPLATE_FOLDERS.get(template)
    if not folder:
        raise ValueError(f"Unknown template: {template}")

    registry_path = REGISTRY_BASE / folder / f"{template}-field-registry.md"
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry not found: {registry_path}")

    content = registry_path.read_text(encoding="utf-8")
    fields = []

    # Find the markdown table (starts with | field_name |)
    in_table = False
    for line in content.split("\n"):
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Detect table start
        if line.startswith("| field_name |"):
            in_table = True
            continue

        # Skip separator line
        if in_table and line.startswith("|--"):
            continue

        # Parse table row
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            # Filter empty parts from leading/trailing pipes
            parts = [p for p in parts if p]

            if len(parts) >= 5:
                field_name = parts[0]
                section = parts[1]
                field_type = parts[2]
                char_limit_str = parts[3]
                required_str = parts[4]
                notes = parts[5] if len(parts) > 5 else ""

                # Parse char_limit
                char_limit = None
                if char_limit_str and char_limit_str != "-":
                    try:
                        char_limit = int(char_limit_str)
                    except ValueError:
                        pass

                # Parse required
                required = required_str.lower() in ("yes", "true", "1")

                fields.append(RegistryField(
                    field_name=field_name,
                    section=section,
                    field_type=field_type,
                    char_limit=char_limit,
                    required=required,
                    notes=notes,
                ))

        # End of table (next section starts)
        if in_table and line.startswith("##"):
            break

    return fields


def read_sheet(gc: gspread.Client, template: str) -> list[SheetRow]:
    """Read current state of Google Sheet."""
    sheet_id = SHEET_IDS.get(template)
    if not sheet_id:
        raise ValueError(f"No sheet ID for template: {template}")

    spreadsheet = gc.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1
    all_values = worksheet.get_all_values()

    rows = []
    for i, row in enumerate(all_values):
        # Pad row to ensure 5 columns
        while len(row) < 5:
            row.append("")

        rows.append(SheetRow(
            row_number=i + 1,  # 1-indexed
            guidelines=row[0].strip(),
            field_label=row[1].strip(),
            en_content=row[2].strip() if len(row) > 2 else "",
            ar_content=row[3].strip() if len(row) > 3 else "",
            ru_content=row[4].strip() if len(row) > 4 else "",
        ))

    return rows


def snake_to_title(field_name: str) -> str:
    """Convert snake_case field_name to Title Case field label.

    Examples:
        meta_title -> Meta Title
        hero_h1 -> Hero H1
        faq_1_question -> FAQ 1 Question
    """
    # Handle special cases
    special = {
        "h1": "H1",
        "h2": "H2",
        "h3": "H3",
        "faq": "FAQ",
        "seo": "SEO",
        "roi": "ROI",
        "url": "URL",
    }

    words = field_name.split("_")
    result = []
    for word in words:
        if word.lower() in special:
            result.append(special[word.lower()])
        elif word.isdigit():
            result.append(word)
        else:
            result.append(word.capitalize())

    return " ".join(result)


def title_to_snake(field_label: str, template: str = None) -> str:
    """Convert Title Case field label to snake_case field_name.

    Uses explicit mappings first, then falls back to automatic conversion.

    Examples:
        Meta Title -> meta_title
        Hero H1 -> hero_h1
        FAQ 1 Question -> faq_1_question
        FAQ 1 - Question -> faq_1_question
    """
    # Normalize
    label = field_label.strip()

    # Check explicit mapping first
    if template and template in FIELD_LABEL_MAPPINGS:
        if label in FIELD_LABEL_MAPPINGS[template]:
            return FIELD_LABEL_MAPPINGS[template][label]

    # Handle special abbreviations
    label = re.sub(r'\bH1\b', 'h1', label)
    label = re.sub(r'\bH2\b', 'h2', label)
    label = re.sub(r'\bH3\b', 'h3', label)
    label = re.sub(r'\bFAQ\b', 'faq', label, flags=re.IGNORECASE)
    label = re.sub(r'\bSEO\b', 'seo', label, flags=re.IGNORECASE)
    label = re.sub(r'\bROI\b', 'roi', label, flags=re.IGNORECASE)
    label = re.sub(r'\bURL\b', 'url', label, flags=re.IGNORECASE)
    label = re.sub(r'\bPP\b', 'pp', label, flags=re.IGNORECASE)
    label = re.sub(r'\bCTA\b', 'cta', label, flags=re.IGNORECASE)

    # Remove dashes/hyphens surrounded by spaces (FAQ 1 - Question -> FAQ 1 Question)
    label = re.sub(r'\s+-\s+', ' ', label)

    # Remove colons and what follows (for OPR labels like "Meta title:" or "H1: Project...")
    if ':' in label:
        label = label.split(':')[0].strip()

    # Remove content in angle brackets (for <p> labels)
    label = re.sub(r'<[^>]+>', '', label).strip()

    # Remove parenthetical content
    label = re.sub(r'\([^)]*\)', '', label).strip()

    # Convert to snake_case
    words = label.split()
    return "_".join(w.lower() for w in words if w)


def build_guidelines(field: RegistryField) -> str:
    """Build Guidelines column value from registry field."""
    parts = []

    if field.char_limit:
        parts.append(f"{field.char_limit} chars")

    if field.field_type in ("EXTRACTED", "HYBRID"):
        parts.append(field.field_type)

    if field.required:
        parts.append("Required")

    if field.notes and len(field.notes) < 100:
        parts.append(field.notes)

    return ". ".join(parts) if parts else ""


def compute_diff(
    registry_fields: list[RegistryField],
    sheet_rows: list[SheetRow],
    template: str,
) -> list[SyncAction]:
    """Compute diff between registry and sheet."""
    actions = []

    # Build lookup of existing sheet fields (by snake_case name)
    sheet_field_map: dict[str, SheetRow] = {}
    for row in sheet_rows:
        if row.field_label:
            snake_name = title_to_snake(row.field_label, template)
            if snake_name:
                sheet_field_map[snake_name] = row

    # Track which registry fields are in the sheet
    registry_names = {f.field_name for f in registry_fields}

    # Get combined bullet field mappings for this template
    combined_fields = COMBINED_BULLET_FIELDS.get(template, {})

    # Build reverse mapping: individual field -> combined field
    individual_to_combined = {}
    for combined_name, individuals in combined_fields.items():
        for ind in individuals:
            individual_to_combined[ind] = combined_name

    # Find fields in registry but not in sheet -> INSERT
    for field in registry_fields:
        # Check if this is an individual bullet field that's covered by a combined field
        if field.field_name in individual_to_combined:
            combined_name = individual_to_combined[field.field_name]
            # If the combined field exists in sheet, skip the individual fields
            # They're handled together at runtime
            if combined_name in sheet_field_map:
                continue
            # If first of the group and combined doesn't exist, we need the section header
            # (location_access_h3, etc.) but not individual bullets

        if field.field_name not in sheet_field_map:
            # Check if this field is part of a missing section
            section_key = f"{field.section.lower().replace(' ', '_')}_bullets"
            if section_key in combined_fields:
                # This is a bullet field for a section that uses combined bullets
                # Skip individual bullets, but keep section headers
                if not field.field_name.endswith("_h3") and not field.field_name.endswith("_h2"):
                    continue

            actions.append(SyncAction(
                action_type="INSERT",
                row_number=None,  # Will be computed based on section
                field_name=field.field_name,
                details={
                    "section": field.section,
                    "field_label": snake_to_title(field.field_name),
                    "guidelines": build_guidelines(field),
                    "field_type": field.field_type,
                    "char_limit": field.char_limit,
                },
            ))

    # Find char limit mismatches -> UPDATE_GUIDELINES
    for field in registry_fields:
        if field.field_name in sheet_field_map:
            sheet_row = sheet_field_map[field.field_name]
            expected_guidelines = build_guidelines(field)

            # Check if char limit is mentioned in guidelines
            if field.char_limit:
                limit_pattern = rf"\b{field.char_limit}\b"
                if not re.search(limit_pattern, sheet_row.guidelines):
                    actions.append(SyncAction(
                        action_type="UPDATE_GUIDELINES",
                        row_number=sheet_row.row_number,
                        field_name=field.field_name,
                        details={
                            "current": sheet_row.guidelines,
                            "expected": expected_guidelines,
                            "char_limit": field.char_limit,
                        },
                    ))

    # Find fields in sheet but not in registry -> FLAG for review (don't auto-delete)
    for snake_name, row in sheet_field_map.items():
        # Skip section headers and special rows
        if not snake_name or row.field_label.upper() == row.field_label:
            continue
        if row.guidelines.upper() == "SECTION":
            continue
        # Skip generic labels like <p>, CTA, etc.
        if row.field_label.startswith("<") or row.field_label == "CTA":
            continue
        # Skip combined bullet fields - they're valid
        if snake_name in combined_fields:
            continue
        # Skip header rows (row 1 typically has "Fields" or "Guidelines")
        if row.row_number == 1 or row.field_label.lower() in ("fields", "field", "guidelines"):
            continue

        if snake_name not in registry_names:
            actions.append(SyncAction(
                action_type="REVIEW",
                row_number=row.row_number,
                field_name=snake_name,
                details={
                    "field_label": row.field_label,
                    "reason": "Field exists in sheet but not in registry",
                },
            ))

    return actions


def apply_actions(
    gc: gspread.Client,
    template: str,
    actions: list[SyncAction],
    dry_run: bool = True,
) -> dict:
    """Apply sync actions to the sheet."""
    sheet_id = SHEET_IDS.get(template)
    spreadsheet = gc.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    results = {
        "inserts": 0,
        "updates": 0,
        "reviews": 0,
        "errors": [],
    }

    if dry_run:
        print("\n[DRY RUN] No changes will be made.\n")

    # Group actions by type
    inserts = [a for a in actions if a.action_type == "INSERT"]
    updates = [a for a in actions if a.action_type == "UPDATE_GUIDELINES"]
    reviews = [a for a in actions if a.action_type == "REVIEW"]

    # Process INSERTS (add at end of sheet for now - manual reorder may be needed)
    if inserts:
        print(f"\nINSERTS ({len(inserts)} fields to add):")
        for action in inserts:
            details = action.details
            print(f"  + {details['field_label']} ({action.field_name})")
            print(f"    Section: {details['section']}")
            print(f"    Guidelines: {details['guidelines']}")

            if not dry_run:
                try:
                    # Append row: [Guidelines, Field Label, EN, AR, RU]
                    worksheet.append_row([
                        details["guidelines"],
                        details["field_label"],
                        "",  # EN content (empty)
                        "",  # AR content (empty)
                        "",  # RU content (empty)
                    ])
                    results["inserts"] += 1
                except Exception as e:
                    results["errors"].append(f"Failed to insert {action.field_name}: {e}")

    # Process UPDATES (batch update guidelines column)
    if updates:
        print(f"\nUPDATES ({len(updates)} guidelines to update):")
        batch_updates = []
        for action in updates:
            details = action.details
            print(f"  ~ Row {action.row_number}: {action.field_name}")
            print(f"    Current: {details['current'][:50]}...")
            print(f"    Expected: {details['expected'][:50]}...")

            if not dry_run:
                batch_updates.append({
                    "range": f"A{action.row_number}",
                    "values": [[details["expected"]]],
                })

        if batch_updates and not dry_run:
            try:
                worksheet.batch_update(batch_updates)
                results["updates"] = len(batch_updates)
            except Exception as e:
                results["errors"].append(f"Failed to batch update guidelines: {e}")

    # Report REVIEWS (fields in sheet not in registry)
    if reviews:
        print(f"\nREVIEW NEEDED ({len(reviews)} fields not in registry):")
        for action in reviews:
            details = action.details
            print(f"  ? Row {action.row_number}: {details['field_label']} ({action.field_name})")
            print(f"    {details['reason']}")
            results["reviews"] += 1

    return results


def sync_template(template: str, dry_run: bool = True) -> dict:
    """Sync a single template."""
    print(f"\n{'='*60}")
    print(f"  SYNCING: {template.upper()}")
    print(f"{'='*60}")

    # Initialize gspread client
    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)

    # Parse registry
    print(f"\n1. Parsing field registry...")
    registry_fields = parse_registry(template)
    print(f"   Found {len(registry_fields)} fields in registry")

    # Read current sheet
    print(f"\n2. Reading Google Sheet...")
    sheet_rows = read_sheet(gc, template)
    print(f"   Found {len(sheet_rows)} rows in sheet")

    # Compute diff
    print(f"\n3. Computing diff...")
    actions = compute_diff(registry_fields, sheet_rows, template)
    print(f"   Found {len(actions)} actions needed")

    # Apply actions
    print(f"\n4. Applying actions...")
    results = apply_actions(gc, template, actions, dry_run=dry_run)

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY: {template.upper()}")
    print(f"{'='*60}")
    print(f"  Registry fields: {len(registry_fields)}")
    print(f"  Sheet rows: {len(sheet_rows)}")
    print(f"  Inserts: {results['inserts']}")
    print(f"  Updates: {results['updates']}")
    print(f"  Reviews needed: {results['reviews']}")
    if results["errors"]:
        print(f"  Errors: {len(results['errors'])}")
        for err in results["errors"]:
            print(f"    - {err}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Sync Google Sheet to field registry")
    parser.add_argument(
        "template",
        nargs="?",
        help="Template to sync (opr, adop, adre, commercial, aggregators, mpp) or --all",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Sync all 6 templates",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without applying (default: True)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply changes (overrides --dry-run)",
    )

    args = parser.parse_args()

    # Determine dry_run mode
    dry_run = not args.apply

    if args.all:
        templates = list(SHEET_IDS.keys())
    elif args.template:
        if args.template not in SHEET_IDS:
            print(f"Error: Unknown template '{args.template}'")
            print(f"Valid templates: {', '.join(SHEET_IDS.keys())}")
            sys.exit(1)
        templates = [args.template]
    else:
        parser.print_help()
        sys.exit(1)

    all_results = {}
    for template in templates:
        try:
            results = sync_template(template, dry_run=dry_run)
            all_results[template] = results
        except Exception as e:
            print(f"\nError syncing {template}: {e}")
            all_results[template] = {"error": str(e)}

    # Final summary
    if len(templates) > 1:
        print(f"\n{'='*60}")
        print(f"  FINAL SUMMARY (ALL TEMPLATES)")
        print(f"{'='*60}")
        for template, results in all_results.items():
            if "error" in results:
                print(f"  {template}: ERROR - {results['error']}")
            else:
                print(f"  {template}: {results['inserts']} inserts, {results['updates']} updates, {results['reviews']} reviews")


if __name__ == "__main__":
    main()
