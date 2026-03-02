"""
Patch: Add Hero sidebar data fields (Sale Price, Payment Plan, Handover)
to the existing Commercial Template v2 Google Sheet.

Inserts 3 new rows after "Hero Description" (row 9) in the sheet.

Usage:
    cd backend
    python scripts/_patch_commercial_v2_hero_sidebar.py
"""

import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv(backend_dir / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ID = "1MQZvI-YVY5d5Cgf5jUmoVO6DVZ1YTlQTSiZzzOmGXuA"


def get_client() -> gspread.Client:
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set")
    creds_path = Path(creds_path)
    if not creds_path.is_absolute():
        creds_path = backend_dir / creds_path
    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    client = gspread.authorize(creds)
    client.http_client.session.timeout = 30
    return client


def patch():
    client = get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    worksheet = spreadsheet.sheet1

    # Find "Hero Description" row to insert after it
    all_values = worksheet.get_all_values()
    insert_after_row = None
    for i, row in enumerate(all_values):
        if len(row) > 1 and row[1] == "Hero Description":
            insert_after_row = i + 1  # 1-indexed
            break

    if insert_after_row is None:
        print("ERROR: Could not find 'Hero Description' row in sheet")
        sys.exit(1)

    print(f"Found 'Hero Description' at row {insert_after_row}")
    print(f"Inserting 3 new rows after row {insert_after_row}...")

    # New rows to insert (Guidelines/Comments, Fields, EN, AR, RU)
    new_rows = [
        [
            'Starting sale price. Label "Sale price from:" is static. '
            'Value extracted from PDF (e.g. "AED 3.5M"). ~15 characters',
            "Hero - Sale Price",
            "",
            "",
            "",
        ],
        [
            'Payment plan ratio. Label "Payment Plan:" is static. '
            'Value extracted from PDF (e.g. "50/50"). ~10 characters',
            "Hero - Payment Plan",
            "",
            "",
            "",
        ],
        [
            'Handover quarter/year. Label "Handover:" is static. '
            'Value extracted from PDF (e.g. "Q4 2028"). ~10 characters',
            "Hero - Handover",
            "",
            "",
            "",
        ],
    ]

    # Insert rows using gspread (inserts AFTER the specified row)
    worksheet.insert_rows(new_rows, row=insert_after_row + 1)

    print("Done. 3 hero sidebar fields inserted:")
    print("  - Hero - Sale Price")
    print("  - Hero - Payment Plan")
    print("  - Hero - Handover")
    print(f"  URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == "__main__":
    try:
        patch()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
