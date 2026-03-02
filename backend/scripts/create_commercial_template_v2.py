"""
Create Commercial Template v2 Google Sheet in the shared drive.

This script creates a new Google Sheet with the corrected commercial template
structure based on the live page specification analysis. It replaces the
existing commercial template which had critical mismatches with the actual
published page layout.

Usage:
    cd backend
    python scripts/create_commercial_template_v2.py

Requires:
    - GOOGLE_APPLICATION_CREDENTIALS env var pointing to service account key
    - Service account must have Editor access to the shared drive
"""

import os
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv(backend_dir / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHARED_DRIVE_ID = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID", "0AOEEIstP54k2Uk9PVA")
SHEET_TITLE = "Commercial Project Template v2"
TAB_NAME = "Commercial Project Template"


def get_gspread_client() -> gspread.Client:
    """Initialize gspread client with service account credentials."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set")

    # Resolve relative path from backend dir
    creds_path = Path(creds_path)
    if not creds_path.is_absolute():
        creds_path = backend_dir / creds_path

    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials file not found: {creds_path}")

    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    client = gspread.authorize(creds)
    client.http_client.session.timeout = 30
    return client


def build_template_rows() -> list[list[str]]:
    """
    Build the full row data for the Commercial Template v2.

    Structure: 5 columns [Guidelines/Comments, Fields, EN, AR, RU]
    Based on: template-organization/commercial-template-v2-specification.md
    """
    rows = []

    def section(name: str):
        rows.append(["SECTION", name, "", "", ""])

    def field(guideline: str, field_name: str):
        rows.append([guideline, field_name, "", "", ""])

    def blank():
        rows.append(["", "", "", "", ""])

    # Header row
    rows.append(["Guidelines/Comments", "Fields", "EN", "AR", "RU"])
    blank()

    # --- SEO ---
    section("SEO")
    field("SEO page title. 60-70 characters", "Meta Title")
    field("SEO meta description. 155-165 characters", "Meta Description")
    field(
        "URL-friendly identifier. Format: [project-name-location]. Lowercase, hyphens, no spaces",
        "URL Slug",
    )
    blank()

    # --- Hero ---
    section("Hero")
    field("50-60 characters", "H1")
    field("70-80 characters", "Hero Description")
    field(
        'Starting sale price. Label "Sale price from:" is static. '
        'Value extracted from PDF (e.g. "AED 3.5M"). ~15 characters',
        "Hero - Sale Price",
    )
    field(
        'Payment plan ratio. Label "Payment Plan:" is static. '
        'Value extracted from PDF (e.g. "50/50"). ~10 characters',
        "Hero - Payment Plan",
    )
    field(
        'Handover quarter/year. Label "Handover:" is static. '
        'Value extracted from PDF (e.g. "Q4 2028"). ~10 characters',
        "Hero - Handover",
    )
    field("15-30 characters; economic indicator or key feature", "Feature 1 - Title")
    field("Up to 60 characters", "Feature 1 - Description")
    field("15-30 characters", "Feature 2 - Title")
    field("Up to 60 characters", "Feature 2 - Description")
    field("15-30 characters", "Feature 3 - Title")
    field("Up to 60 characters", "Feature 3 - Description")
    blank()

    # --- About Area ---
    section("About Area")
    field('"About ... [project name]"', "About Area H2")
    field(
        "Descriptive promotional subtitle with mention of area. 60-80 characters",
        "About Area H3",
    )
    field("Paragraph summary about the project. 150-200 characters", "About Description")
    blank()

    # --- Project Passport ---
    section("Project Passport")
    field("Data table format. 5 discrete data fields", "Project Passport")
    field("Developer company name", "Passport - Developer")
    field("Project location", "Passport - Location")
    field('Payment plan summary (e.g. "70/30")', "Passport - Payment Plan")
    field("Area range in sq ft", "Passport - Area")
    field("Property type(s)", "Passport - Property Type")
    blank()

    # --- Economic Appeal (STATIC) ---
    section("Economic Appeal")
    field("FULLY STATIC SECTION. Do not generate any content", "(static - no fields)")
    blank()

    # --- Dubai Plan Block (STATIC) ---
    section("Dubai Plan Block")
    field("FULLY STATIC SECTION. Do not generate any content", "(static - no fields)")
    blank()

    # --- Gallery (STATIC) ---
    section("Gallery")
    field("FULLY STATIC SECTION. Do not generate any content", "(static - no fields)")
    blank()

    # --- Payment Plan ---
    section("Payment Plan")
    field(
        'Format: "[N/N] Payment Plan" (e.g. "70/30 Payment Plan"). ~30 characters',
        "Payment Plan Headline",
    )
    field("Description of payment plan structure. ~150 characters", "Payment Plan Description")
    field(
        'First percentage (e.g. "70%"). "On Construction" label is static. ~5 characters',
        "Construction Percentage",
    )
    field("Expected handover date. ~20 characters", "Handover Date")
    field(
        'Second percentage (e.g. "30%"). "On Handover" label is static. ~5 characters',
        "Handover Percentage",
    )
    blank()

    # --- After Completion (STATIC) ---
    section("After Completion (3 Options)")
    field("STATIC section header. Do not generate any content", "(static - no fields)")
    blank()

    # --- Advantages ---
    section("Advantages")
    field("40-80 characters", "Advantage 1 - Title")
    field("100-200 characters", "Advantage 1 - Description")
    field("40-80 characters", "Advantage 2 - Title")
    field("100-200 characters", "Advantage 2 - Description")
    field("40-80 characters", "Advantage 3 - Title")
    field("100-200 characters", "Advantage 3 - Description")
    blank()

    # --- Amenities ---
    section("Amenities")
    field("40-80 characters", "Amenity 1 - Title")
    field("100-200 characters", "Amenity 1 - Description")
    field("40-80 characters", "Amenity 2 - Title")
    field("100-200 characters", "Amenity 2 - Description")
    field("40-80 characters", "Amenity 3 - Title")
    field("100-200 characters", "Amenity 3 - Description")
    field("40-80 characters (optional)", "Amenity 4 - Title")
    field("100-200 characters (optional)", "Amenity 4 - Description")
    field("40-80 characters (optional)", "Amenity 5 - Title")
    field("100-200 characters (optional)", "Amenity 5 - Description")
    blank()

    # --- Developer ---
    section("Developer")
    field('"About ... [developer name]"', "Developer H2")
    field("60-80 characters (optional subtitle)", "Developer H3")
    field("Developer company name", "Developer Name")
    field("150-250 characters", "Developer Description")
    blank()

    # --- Location ---
    section("Location")
    field('"Location & Advantages" (static SEO H2)', "Location H2")
    field("40-80 characters", "Location H3")
    field("250-400 characters", "Location Description")
    blank()

    # --- Social Facilities ---
    section("Social Facilities")
    field(
        "100-300 characters. Section header is static",
        "Social Facilities Description",
    )
    field("Name + travel time in minutes", "Social Facility 1")
    field("Name + travel time in minutes", "Social Facility 2")
    field("Name + travel time in minutes", "Social Facility 3")
    blank()

    # --- Education & Medicine ---
    section("Education & Medicine")
    field(
        "100-300 characters. Section header is static",
        "Education & Medicine Description",
    )
    field("Name + travel time in minutes", "Education Facility 1")
    field("Name + travel time in minutes", "Education Facility 2")
    field("Name + travel time in minutes", "Education Facility 3")
    blank()

    # --- Culture ---
    section("Culture")
    field(
        "100-300 characters. Section header is static",
        "Culture Description",
    )
    field("Name + travel time in minutes", "Culture Venue 1")
    field("Name + travel time in minutes", "Culture Venue 2")
    field("Name + travel time in minutes", "Culture Venue 3")

    return rows


def format_sheet(worksheet: gspread.Worksheet, row_count: int):
    """Apply formatting to make the sheet readable and professional."""
    requests = []

    sheet_id = worksheet.id

    # -- Column widths --
    col_widths = {0: 400, 1: 250, 2: 300, 3: 300, 4: 300}  # A-E
    for col_idx, width in col_widths.items():
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": col_idx,
                    "endIndex": col_idx + 1,
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })

    # -- Header row formatting (row 0) --
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 5,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                    "textFormat": {
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                        "bold": True,
                        "fontSize": 11,
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP",
                }
            },
            "fields": "userEnteredFormat",
        }
    })

    # -- SECTION row formatting --
    # Find all SECTION rows and format them
    rows = build_template_rows()
    for i, row in enumerate(rows):
        if row[0] == "SECTION":
            bg_color = {"red": 0.85, "green": 0.92, "blue": 0.97}
            # Check if it's a static section
            if "STATIC" in row[0] or (
                len(rows) > i + 1
                and "STATIC" in rows[i + 1][0].upper()
                and "static" in rows[i + 1][0].lower()
            ):
                bg_color = {"red": 0.95, "green": 0.95, "blue": 0.95}

            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": i,
                        "endRowIndex": i + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 5,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": bg_color,
                            "textFormat": {"bold": True, "fontSize": 11},
                        }
                    },
                    "fields": "userEnteredFormat",
                }
            })

    # -- Static section indicator rows --
    for i, row in enumerate(rows):
        if "FULLY STATIC" in row[0] or "STATIC section" in row[0]:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": i,
                        "endRowIndex": i + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 5,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.95, "green": 0.90, "blue": 0.90},
                            "textFormat": {"italic": True, "fontSize": 10},
                        }
                    },
                    "fields": "userEnteredFormat",
                }
            })

    # -- Freeze header row --
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenRowCount": 1},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    })

    # -- All cells wrap text --
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": row_count,
                "startColumnIndex": 0,
                "endColumnIndex": 5,
            },
            "cell": {
                "userEnteredFormat": {
                    "wrapStrategy": "WRAP",
                    "verticalAlignment": "TOP",
                }
            },
            "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)",
        }
    })

    return requests


def create_sheet():
    """Create the Commercial Template v2 Google Sheet."""
    print(f"Initializing gspread client...")
    client = get_gspread_client()

    print(f"Building template data ({TAB_NAME})...")
    rows = build_template_rows()
    print(f"  Total rows: {len(rows)}")

    # Count generated fields (non-section, non-blank, non-static rows)
    generated = [
        r for r in rows
        if r[1]
        and r[0] != "SECTION"
        and r[1] != "(static - no fields)"
        and r != rows[0]  # skip header
    ]
    print(f"  Generated content fields: {len(generated)}")

    # Create new spreadsheet in the shared drive
    print(f"Creating spreadsheet '{SHEET_TITLE}' in shared drive...")
    spreadsheet = client.create(
        title=SHEET_TITLE,
        folder_id=SHARED_DRIVE_ID,
    )
    sheet_id = spreadsheet.id
    print(f"  Spreadsheet ID: {sheet_id}")
    print(f"  URL: https://docs.google.com/spreadsheets/d/{sheet_id}")

    # Rename default sheet tab
    worksheet = spreadsheet.sheet1
    worksheet.update_title(TAB_NAME)

    # Resize to fit data
    worksheet.resize(rows=len(rows), cols=5)

    # Write all data in one batch
    print(f"Writing {len(rows)} rows...")
    worksheet.update(
        range_name=f"A1:E{len(rows)}",
        values=rows,
    )

    # Apply formatting
    print("Applying formatting...")
    format_requests = format_sheet(worksheet, len(rows))
    if format_requests:
        spreadsheet.batch_update({"requests": format_requests})

    print("")
    print("=" * 60)
    print("DONE")
    print(f"  Sheet: {SHEET_TITLE}")
    print(f"  Tab:   {TAB_NAME}")
    print(f"  ID:    {sheet_id}")
    print(f"  URL:   https://docs.google.com/spreadsheets/d/{sheet_id}")
    print(f"  Rows:  {len(rows)}")
    print(f"  Fields: {len(generated)} (generated content)")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("  1. Review the sheet in Google Drive")
    print("  2. Update TEMPLATE_SHEET_ID_COMMERCIAL in .env to point to new sheet")
    print("  3. Update template_fields.py COMMERCIAL_FIELDS to match v2 structure")
    print("  4. Update prompt_manager.py commercial prompts")

    return sheet_id


if __name__ == "__main__":
    try:
        sheet_id = create_sheet()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
