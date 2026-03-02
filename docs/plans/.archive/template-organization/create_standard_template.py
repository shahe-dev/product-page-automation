"""
Create the STANDARD archetype template in Shared Drive.
Uses centralized config for credentials and Shared Drive ID.
"""

from config import (
    get_sheets_service,
    get_drive_service,
    SHARED_DRIVE_ID,
    create_file_in_shared_drive
)

TEMPLATE_DATA = [
    ["Field", "Guidelines / Character Limits", "EN", "RU", "AR"],
    ["", "", "", "", ""],
    ["SEO", "", "", "", ""],
    ["Meta Title", "50-60 chars. Include: project name, developer, location", "", "", ""],
    ["Meta Description", "150-160 chars. Include: property type, location, investment appeal, key amenity", "", "", ""],
    ["URL Slug", "Lowercase, hyphens only. e.g., project-name-location", "", "", ""],
    ["Image Alt Tag", "Descriptive, include project name and location", "", "", ""],
    ["", "", "", "", ""],
    ["HERO SECTION", "", "", "", ""],
    ["H1", "30-60 chars. Project name + developer OR project name + area", "", "", ""],
    ["Hero Description", "250-400 chars. One punchy paragraph: unique selling point, location advantage, property type", "", "", ""],
    ["Starting Price", "Format: AED X,XXX,XXX / USD X,XXX,XXX", "", "", ""],
    ["Payment Plan", "Summary format: e.g., 60/40, 80/20", "", "", ""],
    ["Handover", "Format: Q1 2026, Q4 2027", "", "", ""],
    ["CTA Button", "10-20 chars. e.g., Get Expert Advice, Register Interest", "", "", ""],
    ["", "", "", "", ""],
    ["ABOUT SECTION", "", "", "", ""],
    ["About H2", "20-50 chars. e.g., About [Project Name]", "", "", ""],
    ["About Description", "400-700 chars. Cover: location context, unit count, architecture style, target buyer, unique features", "", "", ""],
    ["Selling Point 1", "50-80 chars. Key differentiator bullet", "", "", ""],
    ["Selling Point 2", "50-80 chars. Key differentiator bullet", "", "", ""],
    ["Selling Point 3", "50-80 chars. Key differentiator bullet", "", "", ""],
    ["Selling Point 4", "50-80 chars. Optional bullet", "", "", ""],
    ["Selling Point 5", "50-80 chars. Optional bullet", "", "", ""],
    ["", "", "", "", ""],
    ["PROJECT DETAILS", "", "", "", ""],
    ["Developer", "Developer name (linked to developer page)", "", "", ""],
    ["Location", "Area/district name (linked to area page)", "", "", ""],
    ["Property Types", "e.g., Apartments, Penthouses, Townhouses", "", "", ""],
    ["Bedrooms", "e.g., 1-5, Studio-4BR", "", "", ""],
    ["Starting Price", "AED format", "", "", ""],
    ["Handover", "Quarter + Year", "", "", ""],
    ["Payment Plan", "Summary percentage", "", "", ""],
    ["", "", "", "", ""],
    ["AMENITIES SECTION", "", "", "", ""],
    ["Amenities H2", "20-50 chars. e.g., World-Class Amenities, Signature Features", "", "", ""],
    ["Amenity 1 Title", "20-40 chars. Feature name", "", "", ""],
    ["Amenity 1 Description", "100-150 chars. Brief explanation of the amenity", "", "", ""],
    ["Amenity 2 Title", "20-40 chars. Feature name", "", "", ""],
    ["Amenity 2 Description", "100-150 chars. Brief explanation of the amenity", "", "", ""],
    ["Amenity 3 Title", "20-40 chars. Feature name", "", "", ""],
    ["Amenity 3 Description", "100-150 chars. Brief explanation of the amenity", "", "", ""],
    ["Amenity 4 Title", "20-40 chars. Feature name", "", "", ""],
    ["Amenity 4 Description", "100-150 chars. Brief explanation of the amenity", "", "", ""],
    ["Amenity 5 Title", "20-40 chars. Feature name", "", "", ""],
    ["Amenity 5 Description", "100-150 chars. Brief explanation of the amenity", "", "", ""],
    ["", "", "", "", ""],
    ["PAYMENT PLAN SECTION", "", "", "", ""],
    ["Payment H2", "20-50 chars. e.g., Flexible Payment Plan", "", "", ""],
    ["Payment Description", "400-800 chars. Explain ROE benefits, investor appeal", "", "", ""],
    ["Milestone 1 - Name", "e.g., On Booking, Down Payment", "", "", ""],
    ["Milestone 1 - Percentage", "e.g., 20%", "", "", ""],
    ["Milestone 1 - Date", "e.g., On signing, Immediate", "", "", ""],
    ["Milestone 2 - Name", "e.g., During Construction", "", "", ""],
    ["Milestone 2 - Percentage", "e.g., 40%", "", "", ""],
    ["Milestone 2 - Schedule", "e.g., Monthly installments, Quarterly", "", "", ""],
    ["Milestone 3 - Name", "e.g., On Handover", "", "", ""],
    ["Milestone 3 - Percentage", "e.g., 40%", "", "", ""],
    ["Milestone 3 - Date", "e.g., Q4 2027", "", "", ""],
    ["CTA Button", "15-25 chars. e.g., Discuss Payment Options", "", "", ""],
    ["", "", "", "", ""],
    ["LOCATION SECTION", "", "", "", ""],
    ["Location H2", "20-50 chars. e.g., Prime Location, Strategic Location", "", "", ""],
    ["Location Description", "300-550 chars. Cover: neighborhood character, connectivity, lifestyle appeal", "", "", ""],
    ["Nearby 1 - Name", "Landmark/attraction name", "", "", ""],
    ["Nearby 1 - Distance", "e.g., 5 min drive, 2 km", "", "", ""],
    ["Nearby 2 - Name", "Landmark/attraction name", "", "", ""],
    ["Nearby 2 - Distance", "e.g., 10 min drive, 5 km", "", "", ""],
    ["Nearby 3 - Name", "Landmark/attraction name", "", "", ""],
    ["Nearby 3 - Distance", "e.g., 15 min drive, 8 km", "", "", ""],
    ["Nearby 4 - Name", "Optional landmark", "", "", ""],
    ["Nearby 4 - Distance", "Optional distance", "", "", ""],
    ["", "", "", "", ""],
    ["DEVELOPER SECTION", "", "", "", ""],
    ["Developer H2", "20-50 chars. e.g., About [Developer Name]", "", "", ""],
    ["Developer Description", "250-500 chars. Cover: track record, notable projects, reputation, years in market", "", "", ""],
    ["", "", "", "", ""],
    ["FLOOR PLANS SECTION", "", "", "", ""],
    ["Floor Plans H2", "20-50 chars. e.g., Floor Plans & Pricing", "", "", ""],
    ["Unit Type 1 - Name", "e.g., 1 Bedroom Apartment", "", "", ""],
    ["Unit Type 1 - Area", "e.g., 750 sq.ft / 70 m2", "", "", ""],
    ["Unit Type 1 - Price", "e.g., From AED 1,200,000", "", "", ""],
    ["Unit Type 2 - Name", "e.g., 2 Bedroom Apartment", "", "", ""],
    ["Unit Type 2 - Area", "e.g., 1,100 sq.ft / 102 m2", "", "", ""],
    ["Unit Type 2 - Price", "e.g., From AED 1,800,000", "", "", ""],
    ["Unit Type 3 - Name", "e.g., 3 Bedroom Apartment", "", "", ""],
    ["Unit Type 3 - Area", "e.g., 1,500 sq.ft / 139 m2", "", "", ""],
    ["Unit Type 3 - Price", "e.g., From AED 2,500,000", "", "", ""],
    ["Unit Type 4 - Name", "Optional: e.g., Penthouse", "", "", ""],
    ["Unit Type 4 - Area", "Optional", "", "", ""],
    ["Unit Type 4 - Price", "Optional", "", "", ""],
    ["CTA Button", "15-25 chars. e.g., Download All Floor Plans", "", "", ""],
    ["", "", "", "", ""],
    ["FAQ SECTION", "", "", "", ""],
    ["FAQ H2", "20-50 chars. e.g., Frequently Asked Questions", "", "", ""],
    ["FAQ 1 - Question", "Common buyer question about the project", "", "", ""],
    ["FAQ 1 - Answer", "100-200 chars. Clear, helpful answer", "", "", ""],
    ["FAQ 2 - Question", "Common buyer question about the project", "", "", ""],
    ["FAQ 2 - Answer", "100-200 chars. Clear, helpful answer", "", "", ""],
    ["FAQ 3 - Question", "Common buyer question about the project", "", "", ""],
    ["FAQ 3 - Answer", "100-200 chars. Clear, helpful answer", "", "", ""],
    ["FAQ 4 - Question", "Optional question", "", "", ""],
    ["FAQ 4 - Answer", "Optional answer", "", "", ""],
    ["FAQ 5 - Question", "Optional question", "", "", ""],
    ["FAQ 5 - Answer", "Optional answer", "", "", ""],
]

SECTION_KEYWORDS = [
    "SEO", "HERO SECTION", "ABOUT SECTION", "PROJECT DETAILS",
    "AMENITIES SECTION", "PAYMENT PLAN SECTION", "LOCATION SECTION",
    "DEVELOPER SECTION", "FLOOR PLANS SECTION", "FAQ SECTION"
]


def create_template(name="STANDARD Archetype Template"):
    """Create template spreadsheet in Shared Drive."""
    sheets = get_sheets_service()
    drive = get_drive_service()

    print(f"Creating '{name}' in Shared Drive: {SHARED_DRIVE_ID}")

    # Create spreadsheet
    spreadsheet_id = create_file_in_shared_drive(name)
    print(f"Created spreadsheet: {spreadsheet_id}")

    # Get sheet ID
    spreadsheet = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = spreadsheet['sheets'][0]['properties']['sheetId']

    # Write data
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body={"values": TEMPLATE_DATA}
    ).execute()
    print("Written template data")

    # Build formatting requests
    requests = [
        # Rename sheet
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "title": "STANDARD Template"},
                "fields": "title"
            }
        },
        # Header row styling
        {
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        },
        # Column widths
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 180}, "fields": "pixelSize"
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
            "properties": {"pixelSize": 450}, "fields": "pixelSize"
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 5},
            "properties": {"pixelSize": 280}, "fields": "pixelSize"
        }},
        # Freeze header and field column
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 1}
                },
                "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"
            }
        }
    ]

    # Section header formatting
    for i, row in enumerate(TEMPLATE_DATA):
        if row[0] in SECTION_KEYWORDS:
            requests.append({
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": i, "endRowIndex": i + 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.85, "green": 0.92, "blue": 1.0},
                            "textFormat": {"bold": True}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            })

    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()
    print("Applied formatting")

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    return spreadsheet_id, url


if __name__ == "__main__":
    print("=" * 60)
    print("CREATING STANDARD TEMPLATE IN SHARED DRIVE")
    print("=" * 60)
    sheet_id, url = create_template()
    print("=" * 60)
    print(f"SUCCESS! Access at: {url}")
