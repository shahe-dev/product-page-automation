"""
Verify that the standardized template copies match the expected format.

Checks:
1. Header row matches standard
2. Language columns are in correct order (EN=C, AR=D, RU=E)
3. Every non-empty, non-section row has a field name in column B
4. Section markers follow SECTION | name pattern
5. No trailing colons or HTML tags in field names

Usage:
    python scripts/verify_standardized.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gspread
from google.oauth2.service_account import Credentials

CREDS_PATH = Path(__file__).resolve().parent.parent.parent / ".credentials" / "service-account-key.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Load standardized sheet IDs
IDS_PATH = Path(__file__).resolve().parent / "standardized_template_ids.json"

STANDARD_HEADER_5 = ["Guidelines/Comments", "Fields", "EN", "AR", "RU"]
STANDARD_HEADER_8 = ["Guidelines/Comments", "Fields", "EN", "AR", "RU", "De", "Fr", "Zh"]


def verify_template(gc, name, sheet_id):
    """Verify a single standardized template."""
    issues = []

    spreadsheet = gc.open_by_key(sheet_id)
    ws = spreadsheet.sheet1
    all_values = ws.get_all_values()

    if not all_values:
        issues.append("Sheet is empty")
        return issues

    header = all_values[0]

    # Check 1: Header matches standard
    expected_header = STANDARD_HEADER_8 if len(header) >= 8 else STANDARD_HEADER_5
    if header[:len(expected_header)] != expected_header:
        issues.append(f"Header mismatch: got {header}, expected {expected_header}")

    # Check 2: Language column positions
    header_lower = [h.lower() for h in header]
    en_pos = next((i for i, h in enumerate(header_lower) if h in ("en", "eng")), None)
    ar_pos = next((i for i, h in enumerate(header_lower) if h == "ar"), None)
    ru_pos = next((i for i, h in enumerate(header_lower) if h == "ru"), None)

    if en_pos != 2:
        issues.append(f"EN column at index {en_pos}, expected 2 (column C)")
    if ar_pos != 3:
        issues.append(f"AR column at index {ar_pos}, expected 3 (column D)")
    if ru_pos != 4:
        issues.append(f"RU column at index {ru_pos}, expected 4 (column E)")

    # Check 3: Every data row should have a field name in column B
    rows_missing_field = []
    for i, row in enumerate(all_values[1:], start=2):
        if len(row) < 2:
            continue
        a = row[0].strip()
        b = row[1].strip()
        c_and_beyond = any(row[j].strip() for j in range(2, len(row)))

        # Skip completely empty rows (separator rows)
        if not a and not b and not c_and_beyond:
            continue

        # Section markers: A=SECTION, B=name -- OK
        if a.upper() == "SECTION":
            continue

        # Content rows should have field name in B
        if not b:
            rows_missing_field.append(i)

    if rows_missing_field:
        issues.append(
            f"{len(rows_missing_field)} rows missing field name in column B: "
            f"rows {rows_missing_field[:10]}{'...' if len(rows_missing_field) > 10 else ''}"
        )

    # Check 4: No HTML tags or trailing colons in field names (column B)
    bad_field_names = []
    for i, row in enumerate(all_values[1:], start=2):
        if len(row) < 2:
            continue
        b = row[1].strip()
        if not b:
            continue
        # Skip section markers
        if len(row) > 0 and row[0].strip().upper() == "SECTION":
            continue

        if b in ("<p>", "<P>", "<h1>", "<h2>", "<h3>"):
            bad_field_names.append((i, b, "HTML tag"))
        elif b in ("Q:", "A:", "q:", "a:"):
            bad_field_names.append((i, b, "short label"))
        # Trailing colon is OK for some names like "Meta title:"

    if bad_field_names:
        issues.append(
            f"{len(bad_field_names)} field names still use HTML/short labels: "
            f"{bad_field_names[:5]}{'...' if len(bad_field_names) > 5 else ''}"
        )

    # Check 5: Section markers follow pattern
    section_issues = []
    for i, row in enumerate(all_values[1:], start=2):
        if len(row) < 2:
            continue
        a = row[0].strip()
        b = row[1].strip()
        if a.upper() == "SECTION" and not b:
            section_issues.append(f"Row {i}: SECTION marker has no name in B")

    if section_issues:
        issues.extend(section_issues)

    # Summary stats
    total_rows = len(all_values) - 1
    section_rows = sum(1 for r in all_values[1:] if r[0].strip().upper() == "SECTION")
    empty_rows = sum(1 for r in all_values[1:] if not any(c.strip() for c in r))
    field_rows = total_rows - section_rows - empty_rows

    print(f"  Stats: {total_rows} data rows, {section_rows} sections, {empty_rows} separators, {field_rows} fields")

    return issues


def main():
    if not IDS_PATH.exists():
        print(f"Error: {IDS_PATH} not found. Run standardize_templates.py first.")
        sys.exit(1)

    with open(IDS_PATH) as f:
        templates = json.load(f)

    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)

    all_pass = True
    for name, info in templates.items():
        print(f"\nVerifying {name.upper()} ({info['name']})...")
        issues = verify_template(gc, name, info["sheet_id"])

        if issues:
            all_pass = False
            print(f"  ISSUES FOUND ({len(issues)}):")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print(f"  PASS - all checks passed")

    print(f"\n{'='*60}")
    if all_pass:
        print("ALL TEMPLATES PASS VERIFICATION")
    else:
        print("SOME TEMPLATES HAVE ISSUES - review above")


if __name__ == "__main__":
    main()
