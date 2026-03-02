"""
Script to analyze Google Sheets template fields vs prompt requirements
"""

import gspread
from google.oauth2.service_account import Credentials
import json
from pathlib import Path

# Setup credentials
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SERVICE_ACCOUNT_FILE = Path('.credentials/service-account-key.json')

def get_sheet_fields():
    """Extract all fields from the aggregator template sheet"""

    # Authenticate
    creds = Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_FILE),
        scopes=SCOPES
    )
    client = gspread.authorize(creds)

    # Open the sheet by URL
    sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_AGGREGATORS_SHEET_ID/"
    spreadsheet = client.open_by_url(sheet_url)

    # Get all worksheets
    worksheets = spreadsheet.worksheets()

    print(f"Found {len(worksheets)} worksheets:")
    for ws in worksheets:
        print(f"  - {ws.title}")

    # Analyze the first worksheet (assuming it's the template)
    template_sheet = worksheets[0]

    # Get all values
    all_values = template_sheet.get_all_values()

    print(f"\nAnalyzing sheet: {template_sheet.title}")
    print(f"Rows: {len(all_values)}")

    # Extract field names (assuming column A has labels and column B has values)
    fields = []
    for i, row in enumerate(all_values, start=1):
        if len(row) >= 2 and row[0]:  # If column A has content
            field_label = row[0].strip()
            if field_label:  # Skip empty rows
                fields.append({
                    'row': i,
                    'label': field_label,
                    'cell': f'A{i}',
                    'value_cell': f'B{i}'
                })

    return {
        'sheet_title': template_sheet.title,
        'sheet_id': spreadsheet.id,
        'total_rows': len(all_values),
        'fields': fields
    }

def extract_prompt_fields():
    """Extract required fields from the three prompts"""

    prompt_files = [
        'reference/company/prompts/prompt  MJL.md',
        'reference/company/prompts/prompt GRAND POLO.md',
        'reference/company/prompts/prompt Palm Jebel.md'
    ]

    # Parse the prompts to extract all field requirements
    # This is a simplified extraction - focusing on the structural sections

    common_sections = {
        # Meta/SEO
        'meta_title': 'Meta Title',
        'meta_description': 'Meta Description',
        'url_slug': 'URL Slug',
        'image_alt_tag': 'Image Alt Tag',

        # Hero Section
        'h1': 'H1',
        'short_paragraph': 'Short Paragraph / Short Description',
        'hero_paragraph': 'Hero Paragraph',

        # Features/Highlights
        'feature_1_title': 'Feature 1 Title / Highlight 1 Title',
        'feature_1_desc': 'Feature 1 Description',
        'feature_2_title': 'Feature 2 Title',
        'feature_2_desc': 'Feature 2 Description',
        'feature_3_title': 'Feature 3 Title',
        'feature_3_desc': 'Feature 3 Description',

        # Project Details
        'developer': 'Developer',
        'location': 'Location',
        'payment_plan': 'Payment Plan (X/X format)',
        'area_size_range': 'Area / Size Range (sq ft)',
        'property_type': 'Property Type',
        'starting_price': 'Starting Price',
        'bedrooms': 'Bedrooms / Unit Mix',
        'handover': 'Handover Date (QX 20XX)',

        # About Project
        'about_project_h2': 'About [Project Name] H2',
        'about_project_h3': 'About Project H3 Subtitle',
        'about_project_paragraph': 'About Project Paragraph',

        # Economic Appeal / Investment
        'economic_appeal_h2': 'Economic Appeal H2',
        'economic_appeal_h3': 'Economic Appeal H3',
        'economic_appeal_paragraph': 'Economic Appeal Paragraph',
        'roi_potential': 'ROI Potential',
        'rental_yield': 'Average Annual Rent / Rental Yield',
        'golden_visa': 'Golden Visa Eligibility',

        # Payment Plan Section
        'payment_plan_h3': 'Payment Plan H3 Subtitle',
        'payment_plan_paragraph': 'Payment Plan Paragraph',
        'payment_booking': 'On Booking %',
        'payment_construction': 'During Construction %',
        'payment_handover': 'On Handover %',

        # Post-Completion Support
        'post_completion_subtitle': 'Post-Completion Subtitle',
        'post_completion_resell': 'Resell Paragraph',
        'post_completion_rent': 'Rent Out Paragraph',
        'post_completion_movein': 'Move In Paragraph',

        # Investment Advantages
        'investment_adv_1_subtitle': 'Investment Advantage 1 Subtitle',
        'investment_adv_1_paragraph': 'Investment Advantage 1 Paragraph',
        'investment_adv_2_subtitle': 'Investment Advantage 2 Subtitle',
        'investment_adv_2_paragraph': 'Investment Advantage 2 Paragraph',
        'investment_adv_3_subtitle': 'Investment Advantage 3 Subtitle',
        'investment_adv_3_paragraph': 'Investment Advantage 3 Paragraph',

        # Amenities
        'amenity_1_subtitle': 'Amenity 1 Subtitle',
        'amenity_1_paragraph': 'Amenity 1 Paragraph',
        'amenity_2_subtitle': 'Amenity 2 Subtitle',
        'amenity_2_paragraph': 'Amenity 2 Paragraph',
        'amenity_3_subtitle': 'Amenity 3 Subtitle',
        'amenity_3_paragraph': 'Amenity 3 Paragraph',

        # Developer Section
        'developer_h2': 'About the Developer H2',
        'developer_h3': 'Developer H3 Subtitle',
        'developer_paragraph': 'Developer Paragraph',

        # Location & Advantages
        'location_h2': 'Location & Advantages H2',
        'location_h3': 'Location H3 Subtitle',
        'location_paragraph': 'Location Paragraph',

        # Social Facilities
        'social_facilities_paragraph': 'Social Facilities Paragraph',
        'social_location_1': 'Social Location 1',
        'social_location_2': 'Social Location 2',
        'social_location_3': 'Social Location 3',

        # Education & Medicine
        'education_medicine_paragraph': 'Education & Medicine Paragraph',
        'education_location_1': 'Education Location 1',
        'education_location_2': 'Education Location 2',
        'education_location_3': 'Education Location 3',

        # Culture
        'culture_paragraph': 'Culture Paragraph',
        'culture_location_1': 'Culture Location 1',
        'culture_location_2': 'Culture Location 2',
        'culture_location_3': 'Culture Location 3',

        # CTA
        'cta_primary': 'Primary CTA',
        'cta_final_title': 'Final CTA Title',
        'cta_final_paragraph': 'Final CTA Paragraph',
    }

    # GRAND POLO specific additions
    grand_polo_additions = {
        'faq_h2': 'FAQ H2',
        # FAQ 1-18 questions and answers
    }

    # Palm Jebel specific additions
    palm_jebel_additions = {
        'overview_h2': 'Overview H2',
        'overview_paragraph': 'Overview Paragraph',
        'investment_opportunities_h2': 'Investment Opportunities H2',
        'investment_opportunities_paragraph': 'Investment Opportunities Paragraph',
        'property_types_h3': 'Property Types H3',
        'signature_features_heading': 'Signature Features Heading',
        'about_area_h2': 'About the Area H2',
        'about_area_paragraph': 'About the Area Paragraph',
        'location_access': 'Location Access (4 items)',
        'life_on_palm_h2': 'Life on the Palm H2',
        'life_on_palm_1_title': 'Life on Palm 1 Title',
        'life_on_palm_1_text': 'Life on Palm 1 Text',
    }

    return {
        'common_fields': common_sections,
        'grand_polo_specific': grand_polo_additions,
        'palm_jebel_specific': palm_jebel_additions
    }

def compare_fields(sheet_data, prompt_data):
    """Compare sheet fields with prompt requirements"""

    sheet_field_labels = [f['label'].lower() for f in sheet_data['fields']]

    prompt_fields = list(prompt_data['common_fields'].keys())

    print("\n" + "="*80)
    print("COMPARISON ANALYSIS")
    print("="*80)

    print(f"\nSheet has {len(sheet_data['fields'])} fields")
    print(f"Prompts require ~{len(prompt_fields)} common fields")

    # Check which prompt fields are missing from sheet
    print("\n--- FIELDS IN PROMPTS BUT NOT IN SHEET ---")
    missing_count = 0
    for field_key, field_desc in prompt_data['common_fields'].items():
        # Simple fuzzy matching
        found = any(field_key.replace('_', ' ').lower() in label or
                   label in field_key.replace('_', ' ').lower()
                   for label in sheet_field_labels)
        if not found:
            print(f"  - {field_desc} ({field_key})")
            missing_count += 1

    if missing_count == 0:
        print("  (All prompt fields appear to be covered)")

    # Check which sheet fields might not be in prompts
    print("\n--- FIELDS IN SHEET BUT POSSIBLY NOT IN PROMPTS ---")
    extra_count = 0
    for field in sheet_data['fields']:
        label = field['label'].lower()
        # Check if it matches any prompt field
        found = any(key.replace('_', ' ').lower() in label or
                   label in key.replace('_', ' ').lower()
                   for key in prompt_fields)
        if not found and len(label) > 3:  # Skip very short labels
            print(f"  - {field['label']} (Row {field['row']})")
            extra_count += 1

    if extra_count == 0:
        print("  (All sheet fields appear to be in prompts)")

    print("\n" + "="*80)
    print(f"Summary: {missing_count} fields potentially missing from sheet")
    print(f"         {extra_count} fields in sheet possibly not in prompts")
    print("="*80)

    return {
        'missing_from_sheet': missing_count,
        'extra_in_sheet': extra_count
    }

if __name__ == '__main__':
    print("Analyzing Google Sheets Template vs Prompt Requirements...")
    print("="*80)

    try:
        # Get sheet structure
        sheet_data = get_sheet_fields()

        print(f"\nSheet Fields ({len(sheet_data['fields'])} total):")
        print("-" * 80)
        for i, field in enumerate(sheet_data['fields'][:20], 1):  # Show first 20
            print(f"{i:3}. {field['label']:<40} [{field['value_cell']}]")
        if len(sheet_data['fields']) > 20:
            print(f"... and {len(sheet_data['fields']) - 20} more fields")

        # Get prompt requirements
        prompt_data = extract_prompt_fields()

        # Compare
        comparison = compare_fields(sheet_data, prompt_data)

        # Save detailed output
        output = {
            'sheet_data': sheet_data,
            'prompt_data': prompt_data,
            'comparison': comparison,
            'timestamp': str(Path(__file__).stat().st_mtime)
        }

        with open('template_vs_prompt_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print("\nDetailed analysis saved to: template_vs_prompt_analysis.json")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
