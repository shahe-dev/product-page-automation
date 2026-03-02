"""
Update ADOP template Google Sheet to align with prompt v3.

Aligns the ADOP template sheet with the finalized prompt at:
  prompt-organizaton/02-adop/prompt adop.md (54 fields)

Changes applied:
  STRUCTURAL INSERTS (Phase 1 -- bottom to top):
    1. Append FAQ 9-12 unique Q/A slots (12 rows)
    2. Insert Investment Paragraph 4 after Text 3 (3 rows)
    3. Insert LOCATION section between Area Infrastructure and Investment (11 rows)
    4. Insert PROJECT DETAILS (EXTRACTED) between Hero and About (7 rows)
    5. Insert Hero Subtitle after Hero H1 (2 rows)
    Total: 35 new rows (80 -> 115)

  GUIDELINE UPDATES (Phase 2 -- after re-read):
    - EXTRACTED/GENERATED/HYBRID labels on all fields
    - Character range targets on all section guidelines
    - About H2 format: "About [Project Name] by [Developer]"
    - FAQ core reorder: 4=Starting Price, 5=Payment Plan, 6=Completion
    - FAQ 7-8 converted to unique (brochure-triggered) slots
    - FAQ answer length guidance: 40-80 words
    Total: ~40 cell updates

  FIELD MAPPING (prompt field # -> sheet field name):
    SEO:        1=Meta Title, 2=Meta Description, 3=URL Slug, 4=Image Alt Tag
    HERO:       5=Hero H1, 6=Hero Subtitle*, 7=Starting Price, 8=Handover
    DETAILS*:   11=Area From, 12=Location, 16=Property Type
    ABOUT:      19=About H2, 20-22=About Para 1-3
    KEY BENEFITS: 23=KB H2, 24-25=KB Para 1-2
    INFRA:      26=Infra H2, 27-29=Infra Para 1-3
    LOCATION*:  30=Location H2, 31=Drive Times, 32=Overview, 33=Attractions, 34=Destinations
    INVESTMENT: 35=Invest H2, 36-39=Invest Para 1-4*
    DEVELOPER:  40=Dev H2, 41=Dev Description
    FAQ:        42=FAQ H2, 43-48=Core FAQ 1-6, 49-54=Unique FAQ 7-12*
    (* = new fields added by this script)

Usage:
  cd backend
  python scripts/update_adop_template.py --dry-run   # Preview changes
  python scripts/update_adop_template.py              # Execute changes
  python scripts/update_adop_template.py --force      # Skip idempotency check
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
ADOP_SHEET_ID = "YOUR_ADOP_SHEET_ID"

DRY_RUN = "--dry-run" in sys.argv
FORCE = "--force" in sys.argv


def find_row(all_values, col_idx, text, start=0):
    """Find first row with exact text in column. Returns 1-indexed or None."""
    for i in range(start, len(all_values)):
        if len(all_values[i]) > col_idx:
            cell = all_values[i][col_idx].strip()
            if cell == text:
                return i + 1
    return None


def find_row_contains(all_values, col_idx, text, start=0):
    """Find first row containing text (substring). Returns 1-indexed or None."""
    for i in range(start, len(all_values)):
        if len(all_values[i]) > col_idx:
            cell = all_values[i][col_idx].strip()
            if text in cell:
                return i + 1
    return None


# ============================================================
# INSERT DEFINITIONS
# ============================================================

# Each row = [Guidelines/Comments, Fields, EN, AR, RU]

HERO_SUBTITLE_ROWS = [
    ["", "", "", "", ""],  # separator after Hero H1
    [
        "GENERATED. One factual sentence: project's single most "
        "distinctive attribute. 70-80 chars. No adjectives, "
        "no marketing language.",
        "Hero Subtitle",
        "", "", "",
    ],
]

PROJECT_DETAILS_ROWS = [
    [
        "SECTION. Starting Price and Handover populated from HERO "
        "fields above. Developer populated from DEVELOPER section. "
        "These 3 fields below are unique to this section.",
        "PROJECT DETAILS (EXTRACTED)",
        "", "", "",
    ],
    [
        "EXTRACTED from PDF. Smallest floor plan sq.ft.",
        "Area From",
        "", "", "",
    ],
    ["", "", "", "", ""],
    [
        "EXTRACTED from PDF. Area, Location within Emirate.",
        "Location",
        "", "", "",
    ],
    ["", "", "", "", ""],
    [
        "EXTRACTED from PDF floor plans. Options: apartments, "
        "duplexes, villas, townhouses, penthouses.",
        "Property Type",
        "", "", "",
    ],
    ["", "", "", "", ""],
]

LOCATION_ROWS = [
    ["SECTION", "LOCATION", "", "", ""],
    [
        'Format: "Location of [Project Name]". GENERATED.',
        "Location H2",
        "Location of [Project Name]",
        "\u0645\u0648\u0642\u0639 [Project Name]",
        "\u0420\u0430\u0441\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u0435 [Project Name]",
    ],
    ["", "", "", "", ""],
    [
        "GENERATED. Two drive-time tiers: "
        '"5-15 min: [6-10 nearby attractions, comma-separated]" '
        'and "12-25 min: [5-8 further destinations]". '
        "No 'and' before final item.",
        "Location Drive Time Summary",
        "", "", "",
    ],
    ["", "", "", "", ""],
    [
        "GENERATED. 1 paragraph. Project position within "
        "broader district, connectivity vs tranquility, "
        "major road networks. 100-200 chars.",
        "Location Overview",
        "", "", "",
    ],
    ["", "", "", "", ""],
    [
        "GENERATED. 5-7 attractions. Format per line: "
        '"-- [Name] ([X] min) -- [description]". '
        "Google Maps verified. Real Abu Dhabi facilities only.",
        "Location Key Attractions",
        "", "", "",
    ],
    ["", "", "", "", ""],
    [
        "GENERATED. 4-6 destinations. Same format. "
        "Cultural districts, business centers, airport, "
        "other islands/major districts.",
        "Location Major Destinations",
        "", "", "",
    ],
    ["", "", "", "", ""],
]

INVEST_P4_ROWS = [
    ["", "", "", "", ""],  # separator after Text 3
    [
        "HYBRID. Payment plan X/X (EXTRACTED), booking fee "
        "percentage (EXTRACTED), handover date (EXTRACTED). "
        "How this plan supports buyer/investor planning. "
        "150-300 chars. 1-2 sentences.",
        "Investment (Previously Economic Appeal) Text 4",
        "", "", "",
    ],
    ["", "", "", "", ""],  # separator before DEVELOPER section
]

FAQ_APPEND_ROWS = [
    ["", "", "", "", ""],
    [
        "UNIQUE FAQ 9: Generated from brochure triggers "
        "(branded interiors, wellness, smart home, waterfront, "
        "views, signature amenity, community, infrastructure, "
        "ROI, developer). Different trigger than FAQ 7-8. "
        "40-80 words.",
        "FAQ 9 - Question",
        "", "", "",
    ],
    ["", "FAQ 9 - Answer", "", "", ""],
    ["", "", "", "", ""],
    [
        "UNIQUE FAQ 10: MUST be about the area or community "
        "(not just the building). Different trigger than "
        "FAQ 7-9. 40-80 words.",
        "FAQ 10 - Question",
        "", "", "",
    ],
    ["", "FAQ 10 - Answer", "", "", ""],
    ["", "", "", "", ""],
    [
        "UNIQUE FAQ 11: Highlight a different selling point "
        "than FAQ 7-10. 40-80 words.",
        "FAQ 11 - Question",
        "", "", "",
    ],
    ["", "FAQ 11 - Answer", "", "", ""],
    ["", "", "", "", ""],
    [
        "UNIQUE FAQ 12: Different trigger than FAQ 7-11. "
        "If project has multiple property types, include a "
        "comparison FAQ. 40-80 words.",
        "FAQ 12 - Question",
        "", "", "",
    ],
    ["", "FAQ 12 - Answer", "", "", ""],
]


# ============================================================
# CELL UPDATE DEFINITIONS
# ============================================================
# Format: (column_B_label, column_letter, new_value)
# Uses exact match on column B to find the target row after re-read.

CELL_UPDATES = [
    # --- SEO ---
    ("Meta Title", "A",
     "GENERATED. [Project Name] by [Developer] | [Location]. "
     "60-70 chars."),
    ("Meta Description", "A",
     "GENERATED. Property types, starting price, handover, "
     "investment appeal. 155-165 chars."),

    # --- HERO ---
    ("Hero H1", "A",
     "GENERATED. [Project Name] by [Developer]. 50-60 chars."),
    ("Starting Price", "A",
     "EXTRACTED from PDF. Format: AED X,XXX,XXX. "
     "Also populates: Project Info Cards, Project Details, "
     "Meta Description, FAQ 4."),
    ("Handover", "A",
     "EXTRACTED from PDF. Format: QX 20XX. "
     "Also populates: Project Info Cards, Project Details, "
     "Investment Para 4, FAQ 6."),

    # --- ABOUT PROJECT ---
    ("About Project H2", "A",
     'Format: "About [Project Name] by [Developer]". GENERATED.'),
    ("About Project H2", "C",
     "About [Project Name] by [Developer Name]"),
    ("About Project H2", "D",
     "\u062d\u0648\u0644 [Project Name] \u0645\u0646 [Developer Name]"),
    ("About Project H2", "E",
     "\u041e \u043f\u0440\u043e\u0435\u043a\u0442\u0435 [Project Name] \u043e\u0442 [Developer Name]"),
    ("About Paragraph 1", "A",
     "HYBRID. Project identity: project name, floors/buildings "
     "(EXTRACTED), developer (EXTRACTED), location (EXTRACTED), "
     "concept. 250-370 chars. 2-3 sentences."),
    ("About Paragraph 2", "A",
     "HYBRID. Product spec: total unit count (EXTRACTED), "
     "type breakdown matching floor plans exactly (EXTRACTED), "
     "sizes in sq.ft (EXTRACTED), design materials if in PDF. "
     "250-370 chars. 2-3 sentences."),
    ("About Paragraph 3", "A",
     "HYBRID. Value proposition: starting price (EXTRACTED), "
     "location benefit, buyer profile, investment value. "
     "250-370 chars. 2-3 sentences."),

    # --- KEY BENEFITS ---
    ("Key Benefits Paragraph 1", "A",
     "HYBRID. Primary USP. Include metrics from brochure if "
     "available (% open space, park sqm, cycling km). "
     "Data-driven, no generic claims. 250-450 chars."),
    ("Key Benefits Paragraph 2", "A",
     "HYBRID. Amenities in prose (NOT bullets). From PDF only: "
     "Tier 1 (residence: maid room, storage, balcony), "
     "Tier 2 (building: gym, pool, lobby), "
     "Tier 3 (community: marina, parks). "
     "EXCLUDE views, windows, landscaping. 250-500 chars."),

    # --- AREA INFRASTRUCTURE ---
    ("Infrastructure Paragraph 1", "A",
     "GENERATED. Area location, position between "
     "cities/landmarks, immediate environment. "
     "150-250 chars. 1-2 sentences."),
    ("Infrastructure Paragraph 2", "A",
     "GENERATED. Drive times: 'X min to [Place]'. Named "
     "Abu Dhabi facilities: malls, entertainment, healthcare, "
     "schools. Google Maps verified. 200-350 chars. 2-3 sentences."),
    ("Infrastructure Paragraph 3", "A",
     "GENERATED. Walkability, outdoor features, future "
     "development potential, highway/airport connectivity. "
     "150-250 chars. 1-2 sentences."),

    # --- INVESTMENT ---
    ("Investment (Previously Economic Appeal) Text 1", "A",
     "GENERATED. Market context: Abu Dhabi freehold status, "
     "2% transfer fee (not 4%), demand drivers, market stats. "
     "200-320 chars. 2-3 sentences."),
    ("Investment (Previously Economic Appeal) Text 2", "A",
     "HYBRID. Investment metrics: rental yield (verified via "
     "DARI/Bayut -- NOT from PDF), ROI, Golden Visa if "
     "starting price >= AED 2M. 200-320 chars. 2-3 sentences."),
    ("Investment (Previously Economic Appeal) Text 3", "A",
     "GENERATED. Project-specific value: limited inventory, "
     "premium positioning factors, long-term value drivers. "
     "200-320 chars. 2-3 sentences."),

    # --- DEVELOPER ---
    ("Developer Description", "A",
     "GENERATED. Founder/founding year, portfolio regions, "
     "reputation, Abu Dhabi market presence. "
     "300-500 chars. 2-3 sentences."),

    # --- FAQ H2 ---
    ("Faq H2", "A",
     'Format: "Frequently Asked Questions about [Project Name]". '
     "CORE: 6 mandatory (FAQ 1-6). "
     "UNIQUE: 6 brochure-triggered (FAQ 7-12). "
     "Answer length: 40-80 words. Direct answer first, "
     "supporting detail second. No fluff."),

    # --- FAQ 1-3: guideline updates only (keep existing C/D/E) ---
    ("FAQ 1 - Question", "A",
     "CORE FAQ 1: What is [Project]? Include developer "
     "(EXTRACTED), location (EXTRACTED), property types "
     "(EXTRACTED), design concept. 40-80 words."),
    ("FAQ 2 - Question", "A",
     "CORE FAQ 2: Location. Area name (EXTRACTED), road access, "
     "drive times to key Abu Dhabi destinations. 40-80 words."),
    ("FAQ 3 - Question", "A",
     "CORE FAQ 3: Unit types. All property types, bedrooms, "
     "sizes from PDF (EXTRACTED). Must match floor plan "
     "extraction exactly. 40-80 words."),

    # --- FAQ 4: was payment plan -> now starting price ---
    ("FAQ 4 - Question", "A",
     "CORE FAQ 4: Starting price. State 'From AED X.XM' "
     "(EXTRACTED). If unavailable, 'Contact for pricing'. "
     "40-80 words."),
    ("FAQ 4 - Question", "C",
     "What is the starting price of [Project Name]?"),
    ("FAQ 4 - Question", "D",
     "\u0645\u0627 \u0627\u0644\u0633\u0639\u0631 \u0627\u0644\u0645\u0628\u062f\u0626\u064a "
     "\u0641\u064a [Project Name]\u061f"),
    ("FAQ 4 - Question", "E",
     "\u041a\u0430\u043a\u043e\u0432\u0430 \u0441\u0442\u0430\u0440\u0442\u043e\u0432\u0430\u044f "
     "\u0446\u0435\u043d\u0430 \u0432 [Project Name]?"),

    # --- FAQ 5: was foreigners -> now payment plan ---
    ("FAQ 5 - Question", "A",
     "CORE FAQ 5: Payment plan. State X/X structure, "
     "construction vs handover split (EXTRACTED), booking fee. "
     "40-80 words."),
    ("FAQ 5 - Question", "C",
     "What is the payment plan for [Project Name]?"),
    ("FAQ 5 - Question", "D",
     "\u0645\u0627 \u062e\u0637\u0629 \u0627\u0644\u062f\u0641\u0639 "
     "\u0641\u064a [Project Name]\u061f"),
    ("FAQ 5 - Question", "E",
     "\u041a\u0430\u043a\u043e\u0439 \u043f\u043b\u0430\u043d "
     "\u043e\u043f\u043b\u0430\u0442\u044b \u0432 [Project Name]?"),

    # --- FAQ 6: was amenities -> now completion ---
    ("FAQ 6 - Question", "A",
     "CORE FAQ 6: Completion/handover. State quarter + year "
     "(EXTRACTED). Include construction status if known. "
     "40-80 words."),
    ("FAQ 6 - Question", "C",
     "When will [Project Name] be completed?"),
    ("FAQ 6 - Question", "D",
     "\u0645\u062a\u0649 \u0633\u064a\u062a\u0645 \u062a\u0633\u0644\u064a\u0645 "
     "[Project Name]\u061f"),
    ("FAQ 6 - Question", "E",
     "\u041a\u043e\u0433\u0434\u0430 \u0431\u0443\u0434\u0435\u0442 "
     "\u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d [Project Name]?"),

    # --- FAQ 7: was attractions -> now unique ---
    ("FAQ 7 - Question", "A",
     "UNIQUE FAQ 7: Generated from brochure triggers "
     "(branded interiors, wellness, smart home, waterfront, "
     "views, signature amenity). 40-80 words."),
    ("FAQ 7 - Question", "C", ""),
    ("FAQ 7 - Question", "D", ""),
    ("FAQ 7 - Question", "E", ""),

    # --- FAQ 8: was completion -> now unique ---
    ("FAQ 8 - Question", "A",
     "UNIQUE FAQ 8: Generated from brochure triggers. "
     "Different angle than FAQ 7 (community, infrastructure, "
     "ROI, developer track record). 40-80 words."),
    ("FAQ 8 - Question", "C", ""),
    ("FAQ 8 - Question", "D", ""),
    ("FAQ 8 - Question", "E", ""),
]


def main():
    print("=" * 60)
    print("  ADOP Template Update Script")
    print(f"  Mode: {'DRY RUN (no writes)' if DRY_RUN else 'LIVE'}")
    print("=" * 60)

    # --- Auth ---
    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(ADOP_SHEET_ID)
    ws = spreadsheet.sheet1
    all_values = ws.get_all_values()
    print(f"\nSheet: {ws.title} ({len(all_values)} rows x {len(all_values[0])} cols)")

    # --- Idempotency check ---
    if find_row(all_values, 1, "Hero Subtitle"):
        print("\nWARNING: Sheet already has 'Hero Subtitle' -- may have been updated.")
        if not FORCE and not DRY_RUN:
            print("Use --force to run anyway, or --dry-run to preview.")
            sys.exit(1)
        if FORCE:
            print("--force flag set, continuing anyway.")

    # --- Find marker positions ---
    m = {}
    m["hero_h1"] = find_row(all_values, 1, "Hero H1")
    m["about_section"] = find_row(all_values, 1, "ABOUT PROJECT")
    m["invest_section"] = find_row_contains(all_values, 1, "INVESTMENT")
    m["invest_t3"] = find_row_contains(
        all_values, 1, "Investment (Previously Economic Appeal) Text 3"
    )
    m["dev_section"] = find_row(all_values, 1, "DEVELOPER")
    m["faq_h2"] = find_row(all_values, 1, "Faq H2")
    m["faq8_a"] = find_row(all_values, 1, "FAQ 8 - Answer")

    print("\nMarker positions (1-indexed):")
    for name, row in sorted(m.items(), key=lambda x: x[1] or 999):
        print(f"  {name:25s} -> row {row}")

    # Validate
    required = ["hero_h1", "about_section", "invest_section", "invest_t3", "faq_h2"]
    missing_markers = [k for k in required if m[k] is None]
    if missing_markers:
        print(f"\nFATAL: Could not find markers: {missing_markers}")
        sys.exit(1)

    # --- Compute insert positions (using ORIGINAL row numbers) ---
    # Bottom-to-top execution: each position uses original numbers
    # because lower inserts don't affect higher row numbers.
    faq_append_at = len(all_values) + 1  # After last row
    invest_p4_at = m["invest_t3"] + 1    # After Investment Text 3
    location_at = m["invest_section"]     # Before INVESTMENT section header
    project_details_at = m["about_section"]  # Before ABOUT PROJECT header
    hero_subtitle_at = m["hero_h1"] + 1   # After Hero H1

    total_new = (
        len(FAQ_APPEND_ROWS)
        + len(INVEST_P4_ROWS)
        + len(LOCATION_ROWS)
        + len(PROJECT_DETAILS_ROWS)
        + len(HERO_SUBTITLE_ROWS)
    )

    # ================================================
    # EXECUTION PLAN
    # ================================================
    print(f"\n{'=' * 60}")
    print("  EXECUTION PLAN")
    print(f"{'=' * 60}")
    print(f"\n  Phase 1: Structural Inserts (bottom to top)")
    print(f"    1. Insert {len(FAQ_APPEND_ROWS):2d} FAQ 9-12 rows at row {faq_append_at}")
    print(f"    2. Insert {len(INVEST_P4_ROWS):2d} Investment Para 4 rows at row {invest_p4_at}")
    print(f"    3. Insert {len(LOCATION_ROWS):2d} Location section rows at row {location_at}")
    print(f"    4. Insert {len(PROJECT_DETAILS_ROWS):2d} Project Details rows at row {project_details_at}")
    print(f"    5. Insert {len(HERO_SUBTITLE_ROWS):2d} Hero Subtitle rows at row {hero_subtitle_at}")
    print(f"    Total new rows: {total_new}")
    print(f"    Current: {len(all_values)} -> Expected: {len(all_values) + total_new}")
    print(f"\n  Phase 2: Guideline & Content Updates")
    print(f"    {len(CELL_UPDATES)} cell updates across columns A/C/D/E")
    print()

    if DRY_RUN:
        print("** DRY RUN -- no changes will be written **\n")

        print("--- [1] FAQ 9-12 rows (appended) ---")
        for r in FAQ_APPEND_ROWS:
            if r[1]:
                print(f"  B='{r[1]}'  A='{r[0][:70]}'")

        print("\n--- [2] Investment Para 4 rows (at row {}) ---".format(invest_p4_at))
        for r in INVEST_P4_ROWS:
            if r[1]:
                print(f"  B='{r[1]}'  A='{r[0][:70]}'")

        print("\n--- [3] Location section rows (at row {}) ---".format(location_at))
        for r in LOCATION_ROWS:
            if r[1]:
                print(f"  B='{r[1]}'  A='{r[0][:70]}'")

        print("\n--- [4] Project Details rows (at row {}) ---".format(project_details_at))
        for r in PROJECT_DETAILS_ROWS:
            if r[1]:
                print(f"  B='{r[1]}'  A='{r[0][:70]}'")

        print("\n--- [5] Hero Subtitle rows (at row {}) ---".format(hero_subtitle_at))
        for r in HERO_SUBTITLE_ROWS:
            if r[1]:
                print(f"  B='{r[1]}'  A='{r[0][:70]}'")

        print(f"\n--- Cell updates ({len(CELL_UPDATES)} total) ---")
        seen = set()
        for label, col, val in CELL_UPDATES:
            key = f"{label}:{col}"
            if key not in seen:
                # Safely encode for Windows console (cp1252)
                safe_val = val[:75].encode("ascii", "replace").decode("ascii")
                print(f"  [{col}] {label}: {safe_val}...")
                seen.add(key)

        print(f"\n  Current rows: {len(all_values)}")
        print(f"  After update: {len(all_values) + total_new}")
        print("\nRe-run without --dry-run to execute.")
        return

    # ================================================
    # PHASE 1: INSERTS (bottom to top)
    # ================================================

    # Step 1: FAQ 9-12
    print("Step 1: Inserting FAQ 9-12 rows at end...")
    ws.insert_rows(FAQ_APPEND_ROWS, row=faq_append_at)
    print(f"  Inserted {len(FAQ_APPEND_ROWS)} rows at row {faq_append_at}")
    time.sleep(2)

    # Step 2: Investment Paragraph 4
    print(f"Step 2: Inserting Investment Para 4 at row {invest_p4_at}...")
    ws.insert_rows(INVEST_P4_ROWS, row=invest_p4_at)
    print(f"  Inserted {len(INVEST_P4_ROWS)} rows")
    time.sleep(2)

    # Step 3: Location section
    print(f"Step 3: Inserting Location section at row {location_at}...")
    ws.insert_rows(LOCATION_ROWS, row=location_at)
    print(f"  Inserted {len(LOCATION_ROWS)} rows")
    time.sleep(2)

    # Step 4: Project Details
    print(f"Step 4: Inserting Project Details at row {project_details_at}...")
    ws.insert_rows(PROJECT_DETAILS_ROWS, row=project_details_at)
    print(f"  Inserted {len(PROJECT_DETAILS_ROWS)} rows")
    time.sleep(2)

    # Step 5: Hero Subtitle
    print(f"Step 5: Inserting Hero Subtitle at row {hero_subtitle_at}...")
    ws.insert_rows(HERO_SUBTITLE_ROWS, row=hero_subtitle_at)
    print(f"  Inserted {len(HERO_SUBTITLE_ROWS)} rows")
    time.sleep(2)

    # ================================================
    # PHASE 2: RE-READ AND UPDATE CELLS
    # ================================================
    print("\nRe-reading sheet after inserts...")
    time.sleep(2)
    all_values = ws.get_all_values()
    print(f"  New row count: {len(all_values)}")

    # Build batch updates by finding each target row via column B
    batch = []
    update_log = []
    for label, col, val in CELL_UPDATES:
        row_num = find_row(all_values, 1, label)
        if row_num is None:
            row_num = find_row_contains(all_values, 1, label)
        if row_num is None:
            print(f"  WARNING: Could not find '{label}' in column B -- skipping")
            continue
        cell_ref = f"{col}{row_num}"
        batch.append({"range": cell_ref, "values": [[val]]})
        update_log.append(f"  {cell_ref}: {label} [{col}]")

    print(f"\nStep 6: Applying {len(batch)} cell updates...")
    if batch:
        # gspread batch_update has a limit; split if needed
        BATCH_SIZE = 50
        for i in range(0, len(batch), BATCH_SIZE):
            chunk = batch[i:i + BATCH_SIZE]
            ws.batch_update(chunk)
            if i + BATCH_SIZE < len(batch):
                time.sleep(1)
        print(f"  Updated {len(batch)} cells")
    time.sleep(2)

    # ================================================
    # DUMP UPDATED STATE
    # ================================================
    print("\nDumping final state...")
    time.sleep(2)
    updated = ws.get_all_values()

    dump_json = Path(__file__).resolve().parent / "_raw_adop_updated.json"
    with open(dump_json, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2, ensure_ascii=False)

    lines = []
    for i, row in enumerate(updated):
        cells = {}
        for j, v in enumerate(row):
            if v.strip():
                col_letter = chr(65 + j) if j < 26 else f"C{j}"
                cells[col_letter] = v.strip()[:80]
        if cells:
            lines.append(f"Row {i+1:3d}: {json.dumps(cells, ensure_ascii=False)}")
        else:
            lines.append(f"Row {i+1:3d}: (empty)")

    dump_txt = Path(__file__).resolve().parent / "_raw_adop_updated.txt"
    with open(dump_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Dumped to {dump_json.name} and {dump_txt.name}")
    print(f"Final row count: {len(updated)}")

    # ================================================
    # CHANGE LOG
    # ================================================
    print(f"\n{'=' * 60}")
    print("  CHANGE LOG")
    print(f"{'=' * 60}")
    change_log = [
        f"Inserted {len(HERO_SUBTITLE_ROWS)} Hero Subtitle rows (prompt field 6)",
        f"Inserted {len(PROJECT_DETAILS_ROWS)} Project Details rows (prompt fields 11,12,16)",
        f"Inserted {len(LOCATION_ROWS)} Location section rows (prompt fields 30-34)",
        f"Inserted {len(INVEST_P4_ROWS)} Investment Para 4 rows (prompt field 39)",
        f"Inserted {len(FAQ_APPEND_ROWS)} FAQ 9-12 rows (prompt fields 51-54)",
        f"Updated {len(batch)} cells: guidelines, char ranges, EXTRACTED/GENERATED/HYBRID labels",
        "Reordered core FAQs: 4=Starting Price, 5=Payment Plan, 6=Completion",
        "Converted FAQ 7-8 to unique brochure-triggered slots",
        "Added FAQ 9-12 as unique brochure-triggered slots",
        "About H2 updated: 'About [Project Name] by [Developer]' (EN/AR/RU)",
        "All guidelines now include field classification labels and character ranges",
    ]
    for entry in change_log:
        print(f"  - {entry}")

    print(f"\n  Sheet: {len(all_values) - total_new} rows -> {len(updated)} rows")
    print("\nDone.")


if __name__ == "__main__":
    main()
