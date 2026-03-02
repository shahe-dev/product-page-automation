"""
Update OPR template Google Sheet with structural changes.

Changes applied:
  P0: Insert Location Access section (between Overview and Project Details)
  P1a: Clarify overview bullet guidelines
  P1b: Expand Property Types section guidelines
  P1c: Insert payment plan milestone rows
  P2a: Verify and report FAQ structure
  P2b: Check section heading alignment with prompt

Usage:
  cd backend
  python scripts/update_opr_template.py
  python scripts/update_opr_template.py --dry-run   # Preview only, no writes
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gspread
from google.oauth2.service_account import Credentials

CREDS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / ".credentials"
    / "service-account-key.json"
)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
OPR_SHEET_ID = "YOUR_OPR_SHEET_ID"

DRY_RUN = "--dry-run" in sys.argv


def find_row(all_values, col_idx, text, start=0):
    """Find first row containing exact text in specified column.

    Returns 1-indexed row number, or None if not found.
    """
    for i in range(start, len(all_values)):
        if len(all_values[i]) > col_idx:
            cell = all_values[i][col_idx].strip()
            if cell == text or text in cell:
                return i + 1
    return None


def main():
    print("=" * 60)
    print("  OPR Template Update Script")
    print(f"  Mode: {'DRY RUN (no writes)' if DRY_RUN else 'LIVE'}")
    print("=" * 60)

    # --- Auth ---
    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(OPR_SHEET_ID)
    ws = spreadsheet.sheet1
    all_values = ws.get_all_values()
    print(f"\nSheet: {ws.title} ({len(all_values)} rows x {len(all_values[0])} cols)")

    # --- Find key positions using actual column B labels ---
    m = {}
    m["overview_bullets"] = find_row(all_values, 1, "Overview Bullet Points")
    m["project_details_section"] = find_row(all_values, 1, "PROJECT DETAILS CARD")
    m["features_section"] = find_row(all_values, 1, "FEATURES & AMENITIES")
    m["amenities_h3"] = find_row(all_values, 1, "Amenities H3")
    m["prop_types_section"] = find_row(all_values, 1, "PROPERTY TYPES")
    m["prop_types_h3"] = find_row(all_values, 1, "Property Types H3")
    m["prop_types_table"] = find_row(all_values, 1, "Property Types Table")
    m["payment_section"] = find_row(all_values, 1, "PAYMENT PLAN")
    m["payment_h3"] = find_row(all_values, 1, "Payment Plan H3")
    m["payment_desc"] = find_row(all_values, 1, "Payment Plan Description")
    m["investment_section"] = find_row(all_values, 1, "INVESTMENT")
    m["investment_h2"] = find_row(all_values, 1, "Investment H2")
    m["area_section"] = find_row(all_values, 1, "ABOUT THE AREA")
    m["developer_section"] = find_row(all_values, 1, "DEVELOPER")
    m["faq_section"] = find_row(all_values, 1, "FAQ")
    m["faq_h2"] = find_row(all_values, 1, "FAQ H2")

    print("\nSection positions (1-indexed):")
    for name, row in sorted(m.items(), key=lambda x: x[1] or 999):
        print(f"  {name:30s} -> row {row}")

    # Validate critical markers
    required = [
        "overview_bullets", "project_details_section",
        "prop_types_h3", "prop_types_table",
        "payment_desc", "investment_section", "faq_h2",
    ]
    missing = [k for k in required if m[k] is None]
    if missing:
        print(f"\nFATAL: Could not find: {missing}")
        sys.exit(1)

    change_log = []

    # ==========================================================
    # Strategy: Insert rows bottom-to-top to avoid offset issues.
    # 1. Insert Payment Plan milestones (after payment_desc)
    # 2. Insert Location Access (after overview_bullets)
    # 3. Cell updates (P1a, P1b) use post-insert row numbers
    # ==========================================================

    # --- P1c: PAYMENT PLAN MILESTONES ---
    # Insert 5 rows after Payment Plan Description (row m["payment_desc"])
    # New rows: section label + 3 milestone fields + empty separator
    pp_insert_at = m["payment_desc"] + 1  # Insert AFTER the description row
    pp_rows = [
        # [Guidelines, Fields, EN, AR, RU]
        [
            "Payment milestones extracted from developer PDF. "
            "Variable count per project.",
            "Payment Milestones",
            "", "", "",
        ],
        [
            "Booking fee percentage",
            "Milestone: On Booking",
            "", "", "",
        ],
        [
            "Sum of all pre-handover installments",
            "Milestone: During Construction",
            "", "", "",
        ],
        [
            "Final installment at handover. Include quarter and year (QX YYYY).",
            "Milestone: On Handover",
            "", "", "",
        ],
        ["", "", "", "", ""],  # Separator row
    ]
    pp_insert_count = len(pp_rows)

    print(f"\n[P1c] Inserting {pp_insert_count} payment milestone rows at row {pp_insert_at}")
    change_log.append(
        f"P1c: Inserted {pp_insert_count} payment milestone rows after row {m['payment_desc']}"
    )

    # --- P0: LOCATION ACCESS SECTION ---
    # Insert after Overview Bullet Points, before PROJECT DETAILS CARD
    loc_insert_at = m["overview_bullets"] + 1  # Insert AFTER overview bullets
    loc_rows = [
        ["", "", "", "", ""],  # Separator
        [
            "SECTION",
            "LOCATION ACCESS",
            "", "", "",
        ],
        [
            "6-8 key destinations near the project. "
            "Format: 'Destination Name - X minutes'. "
            "Round driving times to nearest 5 min.",
            "Location Access H3",
            "", "", "",
        ],
        [
            "Location access bullets. Each on a separate line. "
            "Format: 'Name - X minutes'. "
            "Sources: Google Maps verified.",
            "Location Access Bullets",
            "", "", "",
        ],
        ["", "", "", "", ""],  # Separator
    ]
    loc_insert_count = len(loc_rows)

    print(f"[P0] Inserting {loc_insert_count} Location Access rows at row {loc_insert_at}")
    change_log.append(
        f"P0: Inserted {loc_insert_count} Location Access rows after row {m['overview_bullets']}"
    )

    # --- Calculate post-insert row positions for cell updates ---
    # After P1c insert (bottom), rows >= pp_insert_at shift by pp_insert_count
    # After P0 insert (top), rows >= loc_insert_at shift by loc_insert_count
    #
    # P1a target: overview_bullets row (row 20) -- BEFORE loc_insert_at, no shift
    # P1b target: prop_types_table row -- AFTER both insert points
    p1a_row = m["overview_bullets"]  # Not shifted (insert happens AFTER this row)
    p1b_row = m["prop_types_table"]
    # Shift for P0 insert (loc_insert_at = 21, so rows >= 21 shift by 5)
    if p1b_row >= loc_insert_at:
        p1b_row += loc_insert_count
    # Shift for P1c insert -- but P1c inserts at pp_insert_at (originally 44)
    # After P0 shift, the original pp_insert_at moves too
    # pp_insert_at was calculated from original positions, and P0 insert affects it
    # Since we insert bottom-first in execution, let's recalculate:
    # Execution order: P1c first (bottom), then P0 (top)
    # P1c insert at original row 44 -- rows below shift
    # P0 insert at original row 21 -- rows below (including P1c's new rows) shift
    # So p1b (originally row 39):
    #   After P1c: 39 < 44, no shift -> still 39
    #   After P0: 39 >= 21, shift +5 -> 44
    # Let me recalculate properly:
    p1b_row_orig = m["prop_types_table"]  # Original row
    # After P1c insert at row 44: 39 < 44, no shift
    p1b_after_p1c = p1b_row_orig
    # After P0 insert at row 21: 39 >= 21, shift by loc_insert_count
    p1b_final = p1b_after_p1c + loc_insert_count

    p1b_h3_orig = m["prop_types_h3"]
    p1b_h3_after_p1c = p1b_h3_orig  # 38 < 44, no shift
    p1b_h3_final = p1b_h3_after_p1c + loc_insert_count

    print(f"\n[P1a] Overview bullets guideline: row {p1a_row} (unchanged)")
    print(f"[P1b] Property Types guideline: row {p1b_h3_final} (orig {m['prop_types_h3']})")

    # --- Build cell updates (applied AFTER all inserts) ---
    cell_updates = []

    # P1a: Overview bullet guidelines
    cell_updates.append((
        f"A{p1a_row}",
        "4-6 project highlight bullets: bedroom mix, property types, "
        "unit sizes, area positioning, key differentiator. "
        "Each bullet on a separate line. Data from developer PDF."
    ))
    change_log.append(f"P1a: Updated overview bullet guideline at row {p1a_row}")

    # P1b: Property Types guidelines
    cell_updates.extend([
        (
            f"A{p1b_h3_final}",
            "Property type entries from developer PDF. "
            "Format per line: Property Type | Living Area (sq ft) | "
            "Starting Price (AED). Variable count (3-8 types per project).",
        ),
        (
            f"A{p1b_final}",
            "Intro sentence (<=200 chars) then list each property type. "
            "One line per type. Data extracted from developer brochure.",
        ),
    ])
    change_log.append(
        f"P1b: Updated Property Types guidelines at rows {p1b_h3_final}-{p1b_final}"
    )

    # ==========================================================
    # P2a: FAQ VERIFICATION
    # ==========================================================
    faq_start = m["faq_h2"]
    print(f"\n[P2a] FAQ structure starting at row {faq_start}:")

    faq_questions = []
    faq_answers = []
    for i in range(faq_start - 1, len(all_values)):
        col_b = all_values[i][1].strip() if len(all_values[i]) > 1 else ""
        if "Question" in col_b:
            topic = all_values[i][0].strip() if all_values[i][0].strip() else ""
            faq_questions.append((i + 1, col_b, topic))
        elif "Answer" in col_b:
            faq_answers.append((i + 1, col_b))

    print(f"  Questions: {len(faq_questions)}, Answers: {len(faq_answers)}")
    if len(faq_questions) != len(faq_answers):
        print(f"  WARNING: Q/A count mismatch!")
    for row_num, label, topic in faq_questions:
        print(f"    Row {row_num}: {label} -- {topic}")

    faq_count = len(faq_questions)
    if 12 <= faq_count <= 18:
        print(f"  OK: {faq_count} FAQ pairs within 12-18 range.")
    else:
        print(f"  WARNING: {faq_count} FAQ pairs outside 12-18 range.")

    change_log.append(f"P2a: Verified FAQ -- {faq_count} Q&A pairs")

    # ==========================================================
    # P2b: SECTION HEADING CHECK
    # ==========================================================
    if m["amenities_h3"]:
        feat_guideline = all_values[m["amenities_h3"] - 1][0].strip()
        print(f"\n[P2b] Amenities H3 guideline: '{feat_guideline[:60]}...'")
        print("  Original prompt heading: 'Signature Features & Private Amenities'")
        print("  Live site heading: 'Signature Features & Resort-Style Amenities'")
        print("  -> Prompt should be updated to match live site, not the other way.")
        change_log.append(
            "P2b: Prompt uses 'Private Amenities', live site uses "
            "'Resort-Style Amenities'. Prompt needs updating."
        )

    # ==========================================================
    # EXECUTE
    # ==========================================================
    print(f"\n{'=' * 60}")
    print("  EXECUTION PLAN")
    print(f"{'=' * 60}")
    print(f"  1. Insert {pp_insert_count} rows at row {pp_insert_at} (payment milestones)")
    print(f"  2. Insert {loc_insert_count} rows at row {loc_insert_at} (location access)")
    print(f"  3. Update {len(cell_updates)} cells (guideline text)")
    print()

    if DRY_RUN:
        print("** DRY RUN -- no changes written **")
        print("\nRows to insert for Location Access:")
        for r in loc_rows:
            print(f"  {r}")
        print("\nRows to insert for Payment Milestones:")
        for r in pp_rows:
            print(f"  {r}")
        print("\nCell updates:")
        for ref, val in cell_updates:
            print(f"  {ref}: {val[:70]}...")
    else:
        # Step 1: Insert payment milestones (bottom-first)
        print("Step 1: Inserting payment milestone rows...")
        ws.insert_rows(pp_rows, row=pp_insert_at)
        print(f"  Inserted {pp_insert_count} rows at row {pp_insert_at}")
        time.sleep(2)  # API rate limit

        # Step 2: Insert Location Access
        print("Step 2: Inserting Location Access rows...")
        ws.insert_rows(loc_rows, row=loc_insert_at)
        print(f"  Inserted {loc_insert_count} rows at row {loc_insert_at}")
        time.sleep(2)

        # Step 3: Cell updates
        print("Step 3: Applying cell updates...")
        batch_data = [
            {"range": ref, "values": [[val]]}
            for ref, val in cell_updates
        ]
        ws.batch_update(batch_data)
        print(f"  Updated {len(cell_updates)} cells")
        time.sleep(1)

        print("\nAll changes applied.")

        # Dump updated state
        print("Re-reading sheet...")
        time.sleep(2)
        updated = ws.get_all_values()
        dump_path = Path(__file__).resolve().parent / "_raw_opr_updated.json"
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2, ensure_ascii=False)

        # Also dump human-readable version
        lines = []
        for i, row in enumerate(updated):
            cells = {}
            for j, v in enumerate(row):
                if v.strip():
                    col = chr(65 + j) if j < 26 else f"C{j}"
                    cells[col] = v.strip()[:80]
            if cells:
                lines.append(f"Row {i+1:3d}: {json.dumps(cells, ensure_ascii=True)}")
        dump_txt = Path(__file__).resolve().parent / "_raw_opr_updated.txt"
        with open(dump_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"Dumped to {dump_path.name} and {dump_txt.name}")
        print(f"New row count: {len(updated)}")

    # ==========================================================
    # CHANGE LOG
    # ==========================================================
    print(f"\n{'=' * 60}")
    print("  CHANGE LOG")
    print(f"{'=' * 60}")
    for entry in change_log:
        print(f"  - {entry}")

    print("\nDone.")


if __name__ == "__main__":
    main()
