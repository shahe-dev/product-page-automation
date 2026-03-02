"""
Build field name mapping: Sheet column B -> template_fields.py keys.

For each standardized template, extracts field names from column B
and compares them to the programmatic keys in template_fields.py.

Outputs a mapping table showing:
- Sheet field name (human-readable from column B)
- Code field key (snake_case from template_fields.py)
- Row number
- Match status (exact, fuzzy, unmatched)

Usage:
    python scripts/build_field_mapping.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gspread
from google.oauth2.service_account import Credentials
from app.services.template_fields import TEMPLATE_FIELD_REGISTRY

CREDS_PATH = Path(__file__).resolve().parent.parent.parent / ".credentials" / "service-account-key.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

IDS_PATH = Path(__file__).resolve().parent / "standardized_template_ids.json"


def sheet_name_to_snake(name):
    """Convert a sheet field name to snake_case for matching."""
    # Remove trailing colons
    name = name.rstrip(":")
    # Replace common patterns
    name = name.replace(" - ", "_")
    name = name.replace(" ", "_")
    name = name.replace("-", "_")
    # Lowercase
    name = name.lower()
    # Remove non-alphanumeric except underscore
    name = re.sub(r"[^a-z0-9_]", "", name)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def build_mapping(gc, template_name, sheet_id):
    """Build mapping between sheet field names and code field keys."""
    spreadsheet = gc.open_by_key(sheet_id)
    ws = spreadsheet.sheet1
    all_values = ws.get_all_values()

    # Get code field keys for this template
    code_fields = TEMPLATE_FIELD_REGISTRY.get(template_name, {})
    code_keys = set(code_fields.keys())
    matched_code_keys = set()

    mapping = []
    for i, row in enumerate(all_values[1:], start=2):
        if len(row) < 2:
            continue
        a = row[0].strip()
        b = row[1].strip()

        # Skip empty rows and section markers
        if not b:
            continue
        if a.upper() == "SECTION":
            mapping.append({
                "row": i,
                "sheet_name": f"--- {b} ---",
                "type": "section",
            })
            continue

        # Try to match to code field key
        snake = sheet_name_to_snake(b)

        if snake in code_keys:
            status = "MATCH"
            matched_code_keys.add(snake)
        else:
            # Try partial/fuzzy matching
            partial_matches = [k for k in code_keys if snake in k or k in snake]
            if partial_matches:
                status = f"PARTIAL: {partial_matches[0]}"
            else:
                status = "UNMATCHED"

        mapping.append({
            "row": i,
            "sheet_name": b,
            "snake_case": snake,
            "status": status,
            "type": "field",
        })

    # Find code keys with no sheet field
    unmatched_code = code_keys - matched_code_keys
    return mapping, unmatched_code, code_keys


def main():
    if not IDS_PATH.exists():
        print(f"Error: {IDS_PATH} not found.")
        sys.exit(1)

    with open(IDS_PATH) as f:
        templates = json.load(f)

    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)

    all_mappings = {}

    for name, info in templates.items():
        print(f"\n{'='*70}")
        print(f"{name.upper()} FIELD MAPPING")
        print(f"{'='*70}")

        mapping, unmatched_code, total_code = build_mapping(gc, name, info["sheet_id"])
        all_mappings[name] = mapping

        # Print mapping table
        matched = 0
        partial = 0
        unmatched_sheet = 0

        for entry in mapping:
            if entry["type"] == "section":
                print(f"\n  {entry['sheet_name']}")
                continue

            status = entry["status"]
            marker = " " if status == "MATCH" else "?" if "PARTIAL" in status else "X"
            print(f"  [{marker}] Row {entry['row']:3d}: {entry['sheet_name']:<40s} -> {entry['snake_case']:<35s} {status}")

            if status == "MATCH":
                matched += 1
            elif "PARTIAL" in status:
                partial += 1
            else:
                unmatched_sheet += 1

        sheet_fields = sum(1 for e in mapping if e["type"] == "field")
        print(f"\n  Summary:")
        print(f"    Sheet fields:     {sheet_fields}")
        print(f"    Code fields:      {len(total_code)}")
        print(f"    Exact matches:    {matched}")
        print(f"    Partial matches:  {partial}")
        print(f"    Unmatched (sheet): {unmatched_sheet}")
        print(f"    Unmatched (code):  {len(unmatched_code)}")

        if unmatched_code:
            print(f"\n    Code keys with no sheet field:")
            for key in sorted(unmatched_code):
                print(f"      - {key}")

    # Save full mapping
    output_path = Path(__file__).resolve().parent / "field_mapping_report.json"
    with open(output_path, "w") as f:
        json.dump(all_mappings, f, indent=2)
    print(f"\n\nFull mapping saved to: {output_path}")


if __name__ == "__main__":
    main()
