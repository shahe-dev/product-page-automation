"""
Audit script: Extract and compare the column structure of all 6 template sheets.

Reads directly from Google Sheets to establish ground truth about:
- Column headers (what's in row 1)
- Column roles (guidelines vs field names vs content)
- Language column order (EN, AR, RU ordering)
- Row spacing patterns
- Field naming conventions

Usage:
    python scripts/audit_template_structure.py
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gspread
from google.oauth2.service_account import Credentials

# Template sheet IDs from .env
TEMPLATE_SHEETS = {
    "aggregators": "YOUR_AGGREGATORS_SHEET_ID",
    "opr": "YOUR_OPR_SHEET_ID",
    "mpp": "YOUR_MPP_SHEET_ID",
    "adop": "YOUR_ADOP_SHEET_ID",
    "adre": "YOUR_ADRE_SHEET_ID",
    "commercial": "YOUR_COMMERCIAL_SHEET_ID",
}

# Service account credentials
CREDS_PATH = Path(__file__).resolve().parent.parent.parent / ".credentials" / "service-account-key.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_client():
    """Authenticate with Google Sheets API."""
    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    return gspread.authorize(creds)


def audit_sheet(gc, sheet_id, template_name):
    """Extract structure from a single template sheet."""
    try:
        spreadsheet = gc.open_by_key(sheet_id)
    except Exception as e:
        return {"error": str(e), "template": template_name}

    result = {
        "template": template_name,
        "sheet_id": sheet_id,
        "title": spreadsheet.title,
        "tabs": [],
    }

    for ws in spreadsheet.worksheets():
        tab_info = {
            "tab_name": ws.title,
            "row_count": ws.row_count,
            "col_count": ws.col_count,
        }

        # Read all data (to see the full structure)
        all_values = ws.get_all_values()
        if not all_values:
            tab_info["empty"] = True
            result["tabs"].append(tab_info)
            continue

        # Header row
        tab_info["header_row"] = all_values[0] if all_values else []

        # Determine column roles based on header
        header = all_values[0]
        tab_info["num_columns_in_header"] = len(header)

        # Find columns with data
        max_cols_used = 0
        for row in all_values:
            non_empty = len([c for c in row if c.strip()])
            if non_empty > max_cols_used:
                max_cols_used = non_empty
        tab_info["max_columns_used"] = max_cols_used

        # Total rows with any data
        non_empty_rows = [i+1 for i, row in enumerate(all_values) if any(c.strip() for c in row)]
        tab_info["total_data_rows"] = len(non_empty_rows)
        tab_info["last_data_row"] = non_empty_rows[-1] if non_empty_rows else 0

        # Analyze column structure
        # Check if col A has guidelines (long text with instructions)
        # vs field names (short labels)
        col_a_samples = []
        col_b_samples = []
        for i, row in enumerate(all_values[1:31], start=2):  # First 30 data rows
            if len(row) > 0 and row[0].strip():
                col_a_samples.append({"row": i, "value": row[0][:80]})
            if len(row) > 1 and row[1].strip():
                col_b_samples.append({"row": i, "value": row[1][:80]})

        tab_info["col_a_samples"] = col_a_samples[:15]
        tab_info["col_b_samples"] = col_b_samples[:15]

        # Check for rows where content is ONLY in column A (no field name in B)
        rows_only_col_a = 0
        rows_with_both = 0
        rows_only_col_b = 0
        for row in all_values[1:]:  # Skip header
            a = row[0].strip() if len(row) > 0 else ""
            b = row[1].strip() if len(row) > 1 else ""
            if a and not b:
                rows_only_col_a += 1
            elif a and b:
                rows_with_both += 1
            elif b and not a:
                rows_only_col_b += 1

        tab_info["column_usage"] = {
            "only_col_a": rows_only_col_a,
            "both_a_and_b": rows_with_both,
            "only_col_b": rows_only_col_b,
        }

        # Check language column order
        header_lower = [h.strip().lower() for h in header]
        lang_positions = {}
        for i, h in enumerate(header_lower):
            if h in ("en", "eng", "english"):
                lang_positions["en"] = {"col_index": i, "col_letter": chr(65+i), "label": header[i]}
            elif h in ("ar", "arabic"):
                lang_positions["ar"] = {"col_index": i, "col_letter": chr(65+i), "label": header[i]}
            elif h in ("ru", "russian"):
                lang_positions["ru"] = {"col_index": i, "col_letter": chr(65+i), "label": header[i]}
        tab_info["language_columns"] = lang_positions

        # Identify if there's a guidelines column
        has_guidelines_col = any(
            h in ("guidelines", "guidelines/comments", "tag")
            for h in header_lower
        )
        tab_info["has_guidelines_column"] = has_guidelines_col

        # Check if there's a fields column
        has_fields_col = any(
            h in ("fields", "field", "field name")
            for h in header_lower
        )
        tab_info["has_fields_column"] = has_fields_col

        # Look for section markers
        section_markers = []
        for i, row in enumerate(all_values[1:], start=2):
            for cell in row:
                cell_stripped = cell.strip().upper()
                if cell_stripped.startswith("SECTION"):
                    section_markers.append({"row": i, "text": cell.strip()})
        tab_info["section_markers"] = section_markers

        result["tabs"].append(tab_info)

    return result


def main():
    gc = get_client()
    results = {}

    for template_name, sheet_id in TEMPLATE_SHEETS.items():
        print(f"Auditing {template_name} ({sheet_id[:12]}...)...")
        audit = audit_sheet(gc, sheet_id, template_name)
        results[template_name] = audit

    # Output to file
    output_path = Path(__file__).resolve().parent / "template_structure_audit.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nAudit written to: {output_path}")

    # Print summary table
    print("\n" + "=" * 100)
    print("TEMPLATE STRUCTURE AUDIT SUMMARY")
    print("=" * 100)

    for name, audit in results.items():
        if "error" in audit:
            print(f"\n{name.upper()}: ERROR - {audit['error']}")
            continue

        for tab in audit["tabs"]:
            print(f"\n--- {name.upper()} (tab: {tab['tab_name']}) ---")
            print(f"  Title: {audit['title']}")
            print(f"  Header: {tab.get('header_row', 'N/A')}")
            print(f"  Columns in header: {tab.get('num_columns_in_header', 'N/A')}")
            print(f"  Max columns used: {tab.get('max_columns_used', 'N/A')}")
            print(f"  Total data rows: {tab.get('total_data_rows', 'N/A')}")
            print(f"  Has guidelines col: {tab.get('has_guidelines_column', 'N/A')}")
            print(f"  Has fields col: {tab.get('has_fields_column', 'N/A')}")
            print(f"  Language columns: {tab.get('language_columns', 'N/A')}")
            print(f"  Column usage: {tab.get('column_usage', 'N/A')}")
            print(f"  Section markers: {len(tab.get('section_markers', []))}")


if __name__ == "__main__":
    main()
