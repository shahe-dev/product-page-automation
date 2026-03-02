"""
Create standardized copies of template sheets.

Phase 1: MPP, Aggregators, ADOP.
Phase 2: Commercial, ADRE.

For each template:
1. Read all data from the original sheet
2. Rearrange columns to match standard format:
   A=Guidelines | B=Fields | C=EN | D=AR | E=RU | F+=extras
3. Create a new spreadsheet in a 'Standardized Templates' subfolder
4. Write the standardized data

Usage:
    python scripts/standardize_templates.py
    python scripts/standardize_templates.py --dry-run  # Preview without writing
"""

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

CREDS_PATH = Path(__file__).resolve().parent.parent.parent / ".credentials" / "service-account-key.json"
SHARED_DRIVE_ID = "0AOEEIstP54k2Uk9PVA"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Templates to standardize in this phase
TEMPLATES = {
    "mpp": {
        "sheet_id": "YOUR_MPP_SHEET_ID",
        "output_name": "mpp-template-STANDARDIZED",
    },
    "aggregators": {
        "sheet_id": "YOUR_AGGREGATORS_SHEET_ID",
        "output_name": "aggregators-template-STANDARDIZED",
    },
    "adop": {
        "sheet_id": "YOUR_ADOP_SHEET_ID",
        "output_name": "adop-template-STANDARDIZED",
    },
    "commercial": {
        "sheet_id": "YOUR_COMMERCIAL_SHEET_ID",
        "output_name": "commercial-template-STANDARDIZED",
    },
    "adre": {
        "sheet_id": "YOUR_ADRE_SHEET_ID",
        "output_name": "adre-template-STANDARDIZED",
    },
    "opr": {
        "sheet_id": "YOUR_OPR_SHEET_ID",
        "output_name": "opr-template-STANDARDIZED",
    },
}

# Standard header for all templates
STANDARD_HEADER_5COL = ["Guidelines/Comments", "Fields", "EN", "AR", "RU"]
STANDARD_HEADER_8COL = ["Guidelines/Comments", "Fields", "EN", "AR", "RU", "De", "Fr", "Zh"]


def get_clients():
    """Create gspread and Drive API clients."""
    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    return gc, drive


def create_subfolder(drive, folder_name="Standardized Templates"):
    """Create a subfolder in the Shared Drive root. Returns folder ID."""
    # Check if folder already exists
    query = (
        f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' "
        f"and '{SHARED_DRIVE_ID}' in parents and trashed = false"
    )
    results = drive.files().list(
        q=query,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora="drive",
        driveId=SHARED_DRIVE_ID,
        fields="files(id, name)",
    ).execute()

    existing = results.get("files", [])
    if existing:
        folder_id = existing[0]["id"]
        print(f"  Found existing folder: {folder_name} ({folder_id})")
        return folder_id

    # Create new folder
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [SHARED_DRIVE_ID],
    }
    folder = drive.files().create(
        body=metadata,
        supportsAllDrives=True,
        fields="id",
    ).execute()
    folder_id = folder["id"]
    print(f"  Created folder: {folder_name} ({folder_id})")
    return folder_id


def read_template(gc, sheet_id):
    """Read all data from a template sheet."""
    spreadsheet = gc.open_by_key(sheet_id)
    ws = spreadsheet.sheet1
    all_values = ws.get_all_values()
    return {
        "title": spreadsheet.title,
        "tab_name": ws.title,
        "header": all_values[0] if all_values else [],
        "data": all_values,
        "row_count": len(all_values),
    }


def standardize_mpp(data):
    """
    MPP is already close to standard.
    Current: A=Guidelines, B=Fields, C=En, D=Ar, E=Ru, F=De, G=Fr, H=Zh-hans
    Target:  A=Guidelines, B=Fields, C=EN, D=AR, E=RU, F=De, G=Fr, H=Zh

    Changes:
    - Standardize header labels only
    - Verify structure is correct
    """
    rows = data["data"]
    result = []

    for i, row in enumerate(rows):
        # Pad row to 8 columns
        padded = row + [""] * max(0, 8 - len(row))

        if i == 0:
            # Fix header
            result.append(STANDARD_HEADER_8COL)
        else:
            # Data rows: columns are already in correct order
            # A=Guidelines, B=Fields, C=EN, D=AR, E=RU, F=De, G=Fr, H=Zh
            result.append(padded[:8])

    return result, "MPP: Header labels standardized. Column order already correct."


def standardize_aggregators(data):
    """
    Aggregators needs column swaps and section marker standardization.
    Current: A=Field, B=Guidelines, C=EN, D=RU, E=AR
    Target:  A=Guidelines, B=Field, C=EN, D=AR, E=RU

    Changes:
    - Swap columns A <-> B (Field goes to B, Guidelines to A)
    - Swap columns D <-> E (AR goes to D, RU to E)
    - Detect section header rows and format as SECTION | name
    """
    rows = data["data"]
    result = []

    # Known section header values in the Aggregators template (in column A = Field)
    section_headers = {
        "SEO", "HERO SECTION", "ABOUT SECTION", "PROJECT DETAILS",
        "AMENITIES SECTION", "PAYMENT PLAN SECTION", "LOCATION SECTION",
        "DEVELOPER SECTION", "FLOOR PLANS SECTION", "FAQ SECTION",
    }

    for i, row in enumerate(rows):
        # Pad row to 5 columns
        padded = row + [""] * max(0, 5 - len(row))

        if i == 0:
            # New header
            result.append(STANDARD_HEADER_5COL)
        else:
            # Swap A<->B and D<->E
            old_field = padded[0].strip()
            old_guideline = padded[1].strip()

            # Check if this is a section header row
            if old_field.upper() in section_headers or (
                old_field.upper().endswith("SECTION") and not old_guideline
            ):
                # Format as standard section marker
                section_name = old_field.replace(" SECTION", "").replace("SECTION", "").strip()
                if not section_name:
                    section_name = old_field
                new_row = ["SECTION", section_name, "", "", ""]
            else:
                new_row = [
                    old_guideline,  # A <- old B (Guidelines)
                    old_field,      # B <- old A (Field)
                    padded[2],      # C <- old C (EN) - unchanged
                    padded[4],      # D <- old E (AR) - was in wrong position
                    padded[3],      # E <- old D (RU) - was in wrong position
                ]
            result.append(new_row)

    return result, "Aggregators: Swapped A<->B, D<->E, standardized section markers."


def standardize_adop(data):
    """
    ADOP needs language column swap and field name cleanup.
    Current: A=Guidelines, B=Fields, C=En, D=Ru, E=Ar
    Target:  A=Guidelines, B=Fields, C=EN, D=AR, E=RU

    Changes:
    - Swap columns D <-> E (AR goes to D, RU to E)
    - Rename short field labels to descriptive names
    """
    rows = data["data"]
    result = []

    # Track context for renaming <p> and Q:/A: fields
    current_section = ""
    p_counter = 0  # counter for <p> tags within a section
    faq_counter = 0

    # ADOP field renaming map for short labels
    section_p_names = {
        "ABOUT PROJECT": [
            "About Paragraph 1",
            "About Paragraph 2",
            "About Paragraph 3",
        ],
        "KEY BENEFITS": [
            "Key Benefits Paragraph 1",
            "Key Benefits Paragraph 2",
        ],
        "AREA INFRASTRUCTURE": [
            "Infrastructure Paragraph 1",
            "Infrastructure Paragraph 2",
            "Infrastructure Paragraph 3",
        ],
        "INVESTMENT": [
            "Investment Paragraph 1",
            "Investment Paragraph 2",
            "Investment Paragraph 3",
        ],
        "DEVELOPER": [
            "Developer Description",
        ],
    }

    # Direct field name replacements (strip colons, make descriptive)
    field_renames = {
        "Slug:": "URL Slug",
        "Title:": "Meta Title",
        "Desc:": "Meta Description",
        "Image alt tag:": "Image Alt Tag",
        "H1:": None,  # Will be context-dependent
        "H2:": None,  # Will be context-dependent
        "Starting price": "Starting Price",
        "Handover": "Handover",
    }

    for i, row in enumerate(rows):
        padded = row + [""] * max(0, 5 - len(row))

        if i == 0:
            result.append(STANDARD_HEADER_5COL)
            continue

        # Swap D <-> E (AR/RU)
        new_row = [
            padded[0],  # A = Guidelines (unchanged)
            padded[1],  # B = Fields (unchanged)
            padded[2],  # C = EN (unchanged)
            padded[4],  # D <- old E (AR)
            padded[3],  # E <- old D (RU)
        ]

        # Detect section changes
        col_a = padded[0].strip()
        col_b = padded[1].strip()

        if col_a.startswith("SECTION:") or col_a.startswith("SECTION "):
            section_name = col_a.replace("SECTION:", "").replace("SECTION", "").strip()
            current_section = section_name.upper()
            p_counter = 0
            if "FAQ" in current_section:
                faq_counter = 0
            # Standardize section marker format
            new_row[0] = "SECTION"
            new_row[1] = section_name.strip() if section_name.strip() else col_b
        elif col_b == "<p>" or col_b == "<P>":
            # Rename <p> based on current section context
            p_names = section_p_names.get(current_section, [])
            if p_counter < len(p_names):
                new_row[1] = p_names[p_counter]
            else:
                new_row[1] = f"{current_section.title()} Text {p_counter + 1}"
            p_counter += 1
        elif col_b in ("Q:", "q:"):
            faq_counter += 1
            new_row[1] = f"FAQ {faq_counter} - Question"
        elif col_b in ("A:", "a:"):
            new_row[1] = f"FAQ {faq_counter} - Answer"
        elif col_b in field_renames:
            rename = field_renames[col_b]
            if rename is not None:
                new_row[1] = rename
            else:
                # Context-dependent: H1:/H2: -> use section name
                label = col_b.rstrip(":")
                if current_section:
                    new_row[1] = f"{current_section.title()} {label}"
                else:
                    new_row[1] = label
        elif col_b.endswith(":") and len(col_b) <= 5:
            # Other short labels like "H2:" -- strip colon, add context
            label = col_b.rstrip(":")
            if current_section:
                new_row[1] = f"{current_section.title()} {label}"
            else:
                new_row[1] = label

        result.append(new_row)

    return result, "ADOP: Swapped D<->E (AR/RU), renamed <p>/Q:/A: fields, standardized section markers."


# -- Phase 2 helpers --

_CHAR_LIMIT_RE = re.compile(r'[\u2248~]\s*(.+)$')


def _extract_char_limit(text):
    """Extract character-limit guideline from inline text.

    Examples:
        "H1 ~ 50-60 characters"         -> "50-60 characters"
        "Brief description ... ~ 150-200 characters" -> "150-200 characters"
        "H3 (subtitle) ~ 60-80 characters (optional)" -> "60-80 characters (optional)"
    """
    m = _CHAR_LIMIT_RE.search(text)
    if m:
        return m.group(1).strip()
    return ""


def standardize_commercial(data):
    """
    Commercial needs complete restructuring.
    Current: 4 columns (A=Fields, B=EN, C=RU, D=AR) with ALL data in column A.
    Target:  A=Guidelines, B=Fields, C=EN, D=AR, E=RU

    Column A currently mixes field names with character limits and instructions.
    We split into guideline (A) and field name (B), add section markers,
    and set up empty language columns in correct order (EN, AR, RU).
    """
    rows = data["data"]
    result = [STANDARD_HEADER_5COL]

    # -- state --
    current_section = ""
    feature_idx = 0
    advantage_idx = 0
    amenity_idx = 0
    landmark_idx = 0
    in_post_delivery = False
    pd_desc_idx = 0  # post-delivery description counter

    MAIN_SECTIONS = {
        "Home Screen (Hero)": "Hero",
        "About area": "About Area",
        "Project details": "Project Details",
        "Economic attractiveness": "Economic Appeal",
        "Advantages": "Advantages",
        "Amenities (Features, UTP)": "Amenities",
        "About the developer": "Developer",
    }
    LOC_SUBS = {
        "Social Facilities": "Social Facilities",
        "Education & Medicine": "Education & Medicine",
        "Culture": "Culture",
    }
    SKIP_STARTS = [
        "Features (3 theses",
        "3 advantages",
        "3-5 main features",
        "Description for each payment plan",
    ]

    def sep():
        result.append(["", "", "", "", ""])

    def new_section(name):
        nonlocal current_section, feature_idx, advantage_idx, amenity_idx
        nonlocal landmark_idx, in_post_delivery, pd_desc_idx
        sep()
        result.append(["SECTION", name, "", "", ""])
        current_section = name
        in_post_delivery = False
        pd_desc_idx = 0
        if name == "Hero":
            feature_idx = 0
        elif name == "Advantages":
            advantage_idx = 0
        elif name == "Amenities":
            amenity_idx = 0
        if name in LOC_SUBS.values() or name == "Location":
            landmark_idx = 0

    def field(guideline, field_name):
        result.append([guideline, field_name, "", "", ""])

    for i, row in enumerate(rows):
        if i == 0:
            continue
        col_a = row[0].strip() if row else ""
        if not col_a:
            continue

        # -- 1. Main section headers --
        if col_a in MAIN_SECTIONS:
            new_section(MAIN_SECTIONS[col_a])
            continue

        # -- 2. Location subsections --
        if col_a in LOC_SUBS:
            new_section(LOC_SUBS[col_a])
            continue

        # -- 3. Context-dependent: Payment Plan / Location --
        if col_a == "Payment Plan":
            if current_section == "Project Details":
                field("", "Payment Plan")
            else:
                new_section("Payment Plan")
            continue
        if col_a == "Location":
            if current_section == "Project Details":
                field("", "Location")
            else:
                new_section("Location")
            continue

        # -- 4. Skip pure instruction rows --
        if any(col_a.startswith(p) for p in SKIP_STARTS):
            continue

        # -- 5. SEO fields (before first real section, or within SEO) --
        if current_section in ("", "SEO"):
            a_lo = col_a.lower()
            if a_lo.startswith("title") and "seo" in a_lo:
                if current_section == "":
                    new_section("SEO")
                field("SEO page title", "Meta Title")
                continue
            elif a_lo.startswith("desc") and "seo" in a_lo:
                field("SEO meta description. Max 155-160 characters", "Meta Description")
                continue
            elif a_lo == "slug":
                field("URL-friendly identifier. Lowercase, hyphens, no spaces", "URL Slug")
                continue
            if not current_section:
                continue

        # -- 6. Project Details: simple named fields --
        if current_section == "Project Details":
            if "Project Passport" in col_a:
                field("Data table format", "Project Passport")
            else:
                field("", col_a)
            continue

        # -- 7. H1 --
        if col_a.startswith("H1"):
            field(_extract_char_limit(col_a), "H1")
            continue

        # -- 8. H2 --
        if col_a.startswith("H2"):
            rest = col_a[2:].strip()
            gl = rest if '"' in rest else _extract_char_limit(col_a)
            field(gl, f"{current_section} H2")
            continue

        # -- 9. H3 --
        if col_a.startswith("H3"):
            gl = _extract_char_limit(col_a)
            if not gl and "optional" in col_a.lower():
                gl = col_a[2:].strip()  # fallback for unusual format
            field(gl, f"{current_section} H3")
            continue

        # -- 10. Brief description --
        if col_a.startswith("Brief description"):
            gl = _extract_char_limit(col_a)
            if current_section == "Hero":
                field(gl, "Hero Description")
            elif current_section == "About Area":
                field(gl, "About Description")
            elif current_section == "Economic Appeal":
                field(gl, "Economic Appeal Description")
            elif current_section == "Payment Plan":
                if in_post_delivery:
                    pd_desc_idx += 1
                    field(gl, f"Post-Delivery Description {pd_desc_idx}")
                else:
                    field(gl, "Payment Description")
            elif current_section == "Advantages":
                field(gl, f"Advantage {advantage_idx} - Description")
            elif current_section == "Amenities":
                field(gl, f"Amenity {amenity_idx} - Description")
            elif current_section == "Developer":
                field(gl, "Developer Description")
            elif current_section in LOC_SUBS.values():
                field(gl, f"{current_section} Description")
            elif current_section == "Location":
                field(gl, "Location Description")
            else:
                field(gl, "Description")
            continue

        # -- 11. Subtitle --
        if col_a.startswith("Subtitle"):
            gl = _extract_char_limit(col_a)
            if current_section == "Payment Plan":
                in_post_delivery = True
                field(gl, "Post-Delivery Subtitle")
            elif current_section == "Advantages":
                advantage_idx += 1
                field(gl, f"Advantage {advantage_idx} - Title")
            elif current_section == "Amenities":
                amenity_idx += 1
                field(gl, f"Amenity {amenity_idx} - Title")
            else:
                field(gl, f"{current_section} Subtitle")
            continue

        # -- 12. Feature title-N / desc-N --
        if col_a.startswith("title-"):
            feature_idx += 1
            paren_match = re.search(r'\(([^)]+)\)', col_a)
            extra = paren_match.group(1) if paren_match else ""
            gl = f"15-30 characters{'; ' + extra if extra else ''}"
            field(gl, f"Feature {feature_idx} - Title")
            continue
        if col_a.startswith("desc-"):
            field("Up to 60 characters", f"Feature {feature_idx} - Description")
            continue

        # -- 13. CTA --
        if col_a.upper().startswith("CTA"):
            field(_extract_char_limit(col_a), "CTA")
            continue

        # -- 14. Location landmarks --
        if col_a.startswith("Location name"):
            landmark_idx += 1
            if current_section == "Social Facilities":
                field("Name + travel time", f"Social Facility {landmark_idx}")
            elif current_section == "Education & Medicine":
                field("Name + travel time", f"Education Facility {landmark_idx}")
            elif current_section == "Culture":
                field("Name + travel time", f"Culture Venue {landmark_idx}")
            else:
                field("Name + travel time", f"Landmark {landmark_idx}")
            continue

        # -- 15. Static block (post-delivery) --
        if col_a.startswith("Static block"):
            in_post_delivery = True
            field("Static content block", "Post-Delivery Support")
            continue

        # -- 16. Stray "amenities" label inside Advantages --
        if col_a == "amenities" and current_section == "Advantages":
            field("", f"Advantage {advantage_idx} - Description")
            continue

        # -- 17. Fallback --
        field("", col_a)

    return result, (
        "Commercial: Restructured from single-column format. "
        "Split field names from guidelines, added section markers, "
        "set up EN/AR/RU columns."
    )


def standardize_adre(data):
    """
    ADRE needs field name completion and header fixes.
    Current: 8 cols (A=Guidelines, B=Fields, C=eng, D=Ar, E=Ru, F=de, G=Fr, H=ch)
    Target:  A=Guidelines, B=Fields, C=EN, D=AR, E=RU, F=De, G=Fr, H=Zh

    Main issues:
    - 43+ rows missing field name in column B
    - Header labels inconsistent (eng, de, ch)
    - Corrupted Cyrillic char in Developer H2 row
    - No section markers
    """
    rows = data["data"]
    result = []

    # -- state --
    current_section = ""
    amenity_idx = 0
    faq_idx = 0
    landmark_category = ""
    landmark_idx = 0

    def _row8(a="", b="", lang=None):
        """Build an 8-column output row."""
        if lang is None:
            lang = [""] * 6
        return [a, b] + list(lang)

    def sep():
        result.append(_row8())

    def new_section(name):
        nonlocal current_section, amenity_idx, faq_idx
        nonlocal landmark_category, landmark_idx
        sep()
        result.append(_row8("SECTION", name))
        current_section = name
        if name == "Amenities":
            amenity_idx = 0
        elif name == "FAQ":
            faq_idx = 0
        if name in ("Entertainment", "Healthcare", "Education"):
            landmark_category = name
            landmark_idx = 0

    for i, raw_row in enumerate(rows):
        padded = raw_row + [""] * max(0, 8 - len(raw_row))

        if i == 0:
            result.append(STANDARD_HEADER_8COL)
            continue

        col_a = padded[0].strip()
        col_b = padded[1].strip()
        lang_data = list(padded[2:8])
        a_lower = col_a.lower()

        # Completely empty row -> separator
        if not col_a and not col_b and not any(c.strip() for c in lang_data):
            continue  # collapse multiple empties; sections add their own seps

        # ---- Section detection (insert markers before first field) ----

        # SEO: starts at the very first field (Slug)
        if col_b.rstrip(":") == "Slug" and current_section == "":
            new_section("SEO")

        # About: starts at Project name
        if col_b.rstrip(":") == "Project name" and current_section == "SEO":
            new_section("About")

        # Amenities section header
        if "amenities section header" in a_lower and current_b_is_h2(col_b):
            if current_section != "Amenities":
                new_section("Amenities")

        # Developer section
        if col_b == "\u041d2" or (
            "developer" in a_lower and "title" in a_lower and col_b in ("H2", "\u041d2")
        ):
            if current_section != "Developer":
                new_section("Developer")

        # Economic Appeal
        if "economic appeal section header" in a_lower:
            if current_section != "Economic Appeal":
                new_section("Economic Appeal")

        # Location
        if "location section header" in a_lower:
            if current_section != "Location":
                new_section("Location")

        # FAQ
        if "faq section" in a_lower and current_section != "FAQ":
            new_section("FAQ")
            continue  # row 86 is just the intro guideline, skip it
        if col_b == "FAQ" and current_section == "FAQ":
            continue  # skip the standalone "FAQ" label row

        # ---- Landmark subcategory tracking ----
        if current_section == "Location" and col_b in ("H3", ""):
            if "entertainment" in a_lower and "header" in a_lower:
                landmark_category = "Entertainment"
                landmark_idx = 0
            elif "healthcare" in a_lower and "header" in a_lower:
                landmark_category = "Healthcare"
                landmark_idx = 0
            elif "education" in a_lower and "header" in a_lower:
                landmark_category = "Education"
                landmark_idx = 0

        # ---- Fix corrupted characters ----
        if col_b == "\u041d2":
            col_b = "H2"

        # ---- Determine field name ----
        new_b = col_b

        if not new_b:
            # Row has guideline in A but no field name in B
            if current_section == "About":
                if "description of the project" in a_lower:
                    new_b = "About Description"

            elif current_section == "Amenities":
                if "description of first" in a_lower:
                    new_b = "Amenity 1 - Description"
                elif "description of second" in a_lower:
                    new_b = "Amenity 2 - Description"
                elif "amenity item" in a_lower or "rest of amenities" in a_lower:
                    # Use current amenity_idx (set by the preceding H3 row)
                    new_b = f"Amenity {amenity_idx} - Description"

            elif current_section == "Developer":
                if "description of developer" in a_lower:
                    new_b = "Developer Description"

            elif current_section == "Economic Appeal":
                if "economic appeal overview" in a_lower or (
                    "overview" in a_lower and "economic" in a_lower
                ) or ("3-4 sentences" in a_lower and "starting price" in a_lower):
                    new_b = "Economic Overview"
                elif "rental" in a_lower and ("details" in a_lower or "sentences" in a_lower):
                    new_b = "Rental Appeal Description"
                elif "resale" in a_lower and ("benefit" in a_lower or "sentences" in a_lower):
                    new_b = "Resale Appeal Description"
                elif "living appeal" in a_lower or "end-user" in a_lower or (
                    "resident profile" in a_lower
                ):
                    new_b = "Living Appeal Description"

            elif current_section == "Location":
                if "about the area" in a_lower or "immediate surround" in a_lower:
                    new_b = "Location Description"
                # Specific education patterns (before generic landmark)
                elif "nurseries" in a_lower or "early education" in a_lower:
                    new_b = "Education - Nurseries"
                elif "international school" in a_lower:
                    new_b = "Education - International Schools"
                elif "secondary school" in a_lower:
                    new_b = "Education - Secondary Schools"
                elif "higher education" in a_lower or "universit" in a_lower:
                    new_b = "Education - Universities"
                # Specific healthcare patterns (before generic landmark)
                elif "nearest healthcare" in a_lower:
                    landmark_idx += 1
                    new_b = f"Healthcare Facility {landmark_idx}"
                elif "secondary healthcare" in a_lower or "specialist hospital" in a_lower:
                    landmark_idx += 1
                    new_b = f"Healthcare Facility {landmark_idx}"
                # Generic landmarks (Entertainment, etc.)
                elif "landmark" in a_lower or "travel time" in a_lower:
                    landmark_idx += 1
                    new_b = f"{landmark_category} Landmark {landmark_idx}"

            elif current_section == "FAQ":
                if a_lower.startswith("template q:") or a_lower.startswith("template q "):
                    faq_idx += 1
                    new_b = f"FAQ {faq_idx} - Question"
                elif a_lower.startswith("answer"):
                    new_b = f"FAQ {faq_idx} - Answer"

            # Last resort
            if not new_b and col_a:
                new_b = "[NEEDS FIELD NAME]"

        elif new_b == "H2":
            # Rename generic H2 to descriptive
            if current_section == "Amenities" and "amenities" in a_lower:
                new_b = "Amenities H2"
            elif current_section == "About" and "marketing" in a_lower:
                new_b = "About H2"
            elif current_section == "Developer":
                new_b = "Developer H2"
            elif current_section == "Economic Appeal":
                new_b = "Economic Appeal H2"
            elif current_section == "Location":
                new_b = "Location H2"
            elif current_section:
                new_b = f"{current_section} H2"

        elif new_b == "H3":
            if current_section == "Amenities":
                amenity_idx += 1
                new_b = f"Amenity {amenity_idx} - Title"
            elif current_section == "Economic Appeal":
                if "rental" in a_lower:
                    new_b = "Rental Appeal H3"
                elif "resale" in a_lower:
                    new_b = "Resale Appeal H3"
                elif "end-user" in a_lower or "living" in a_lower:
                    new_b = "Living Appeal H3"
                else:
                    new_b = "Economic Appeal H3"
            elif current_section == "Location":
                if "entertainment" in a_lower:
                    new_b = "Entertainment H3"
                elif "healthcare" in a_lower:
                    new_b = "Healthcare H3"
                elif "education" in a_lower:
                    new_b = "Education H3"
                else:
                    new_b = "Location H3"
            elif current_section:
                new_b = f"{current_section} H3"

        # Strip trailing colons from field names
        if new_b.endswith(":"):
            new_b = new_b[:-1]

        result.append([col_a, new_b] + lang_data)

    return result, (
        "ADRE: Fixed header labels, added section markers, "
        "filled missing field names, fixed corrupted characters, "
        "renamed generic H2/H3 to descriptive names."
    )


def standardize_opr(data):
    """
    OPR needs comprehensive field name cleanup and structural overhaul.
    Current: A=Guidelines, B=Fields, C=En, D=Ar, E=Ru (correct column order)
    Target:  A=Guidelines, B=Fields, C=EN, D=AR, E=RU (cleaned, with sections)

    Main issues:
    - <p> HTML tags used as field names for multiple unrelated sections
    - H2:/H3: prefixes without specifying which section
    - Notes/instructions scattered in column C instead of column A
    - "flexible" placeholder in content columns
    - No section markers
    - FAQ topic categories need Q/A pair structuring
    - 42 rows with only column B data, 11 with only column A
    """
    rows = data["data"]
    result = [STANDARD_HEADER_5COL]

    # State
    current_section = ""
    faq_counter = 0
    pending_note = ""  # accumulate note-only rows to merge into next field
    last_h3_sub = ""  # track H3 sub-section within About the Area
    _in_financing = False  # flag to skip static Financing Options section

    INSTRUCTION_PHRASES = [
        "If possible, please place each bullet point",
        "Don't use the",
    ]

    def is_instruction(text):
        return any(p in text for p in INSTRUCTION_PHRASES)

    def sep():
        result.append(["", "", "", "", ""])

    def new_section(name):
        nonlocal current_section, faq_counter, last_h3_sub, pending_note
        pending_note = ""  # notes don't cross section boundaries
        sep()
        result.append(["SECTION", name, "", "", ""])
        current_section = name
        if name == "FAQ":
            faq_counter = 0
        last_h3_sub = ""

    def emit(guideline, field_name, en="", ar="", ru=""):
        nonlocal pending_note
        if pending_note:
            guideline = f"{guideline}. {pending_note}" if guideline else pending_note
            pending_note = ""
        result.append([guideline, field_name, en, ar, ru])

    for i, row in enumerate(rows):
        if i == 0:
            continue

        padded = row + [""] * max(0, 5 - len(row))
        col_a = padded[0].strip()
        col_b = padded[1].strip()
        col_c = padded[2].strip()
        col_d = padded[3].strip()
        col_e = padded[4].strip()

        # Skip completely empty rows
        if not col_a and not col_b and not col_c and not col_d and not col_e:
            continue

        # Skip "Fix for all pages" static content (Financing, RERA, Disclaimer)
        # These are hardcoded in the frontend, not LLM-generated.
        if col_b.startswith("H3: Financing"):
            _in_financing = True
            continue
        # End financing section when a new H2/H3 is detected
        if _in_financing and (col_b.startswith("H2:") or col_b.startswith("H3:")):
            _in_financing = False
        if _in_financing:
            continue
        if col_a.startswith("Fix for all pages"):
            continue
        if col_b.startswith("RERA Information") or col_b == "Disclaimer":
            continue

        # --- Pre-process: move misplaced content from C to A ---

        # Move instruction text from C to guidelines
        if is_instruction(col_c):
            col_a = f"{col_a}. {col_c}" if col_a else col_c
            col_c = ""

        # Move "flexible" placeholder from C to guidelines
        if col_c.lower() == "flexible":
            col_a = f"{col_a} [LLM-generated]" if col_a else "[LLM-generated]"
            col_c = ""

        # --- Section detection (order matters: first match wins via elif) ---

        if col_b.rstrip(":").strip().lower() == "meta title" and not current_section:
            new_section("SEO")
        elif col_b == "Hero Section":
            new_section("HERO")
            continue  # label-only row, no content field
        elif col_b.startswith("H2: Project overview"):
            new_section("PROJECT OVERVIEW")
        elif col_b == "Project Card":
            new_section("PROJECT DETAILS CARD")
            continue  # label-only row
        elif col_b == "Project Details" and current_section == "PROJECT DETAILS CARD":
            continue  # sub-label
        elif col_b.startswith("H3: Features and amenities"):
            new_section("FEATURES & AMENITIES")
        elif col_b.startswith("H3: Property types"):
            new_section("PROPERTY TYPES")
        elif col_b.startswith("H3: Payment plan"):
            new_section("PAYMENT PLAN")
        elif col_b.startswith("H2: Investment"):
            new_section("INVESTMENT")
        elif col_b.startswith("H2: About the area"):
            new_section("ABOUT THE AREA")
        elif col_b.startswith("H2: About the developer"):
            new_section("DEVELOPER")
        elif col_b.startswith("H2: FAQ"):
            new_section("FAQ")
        # RERA/Disclaimer/Financing are static ("Fix for all pages") -- skipped above

        # Track H3 sub-sections within About the Area
        if current_section == "ABOUT THE AREA":
            if "Lifestyle" in col_b:
                last_h3_sub = "Lifestyle"
            elif "Healthcare" in col_b:
                last_h3_sub = "Healthcare"
            elif "Education" in col_b:
                last_h3_sub = "Education"

        # --- Determine field name and output values ---

        field_name = ""
        en_out = col_c
        ar_out = col_d
        ru_out = col_e
        guideline = col_a

        # CASE 1: Row has a field name in column B
        if col_b:
            # a) <p> tags -> context-dependent descriptive name
            if col_b == "<p>":
                if current_section == "HERO":
                    field_name = "Hero Subheading"
                elif current_section == "PROJECT OVERVIEW":
                    if "bullet" in guideline.lower():
                        field_name = "Overview Bullet Points"
                    else:
                        field_name = "Overview Description"
                elif current_section == "FEATURES & AMENITIES":
                    # Intro comes first, then bullets
                    recent = [r[1] for r in result[-5:] if len(r) > 1]
                    if "Amenities Intro" in recent:
                        field_name = "Amenity Bullet Points"
                    else:
                        field_name = "Amenities Intro"
                elif current_section == "PROPERTY TYPES":
                    field_name = "Property Types Table"
                else:
                    field_name = f"{current_section.title()} Text"

            # b) H1
            elif col_b.startswith("H1:") or col_b.startswith("H1 "):
                field_name = "H1"

            # c) H2: prefix -> section-specific name
            elif col_b.startswith("H2: "):
                h2_map = {
                    "PROJECT OVERVIEW": "Overview H2",
                    "INVESTMENT": "Investment H2",
                    "ABOUT THE AREA": "Area H2",
                    "DEVELOPER": "Developer H2",
                    "FAQ": "FAQ H2",
                }
                field_name = h2_map.get(current_section, f"{current_section.title()} H2")
                # Move display heading text from C to guideline
                if en_out:
                    guideline = (
                        f"{guideline}. Display: {en_out}" if guideline
                        else f"Display: {en_out}"
                    )
                    en_out = ""

            # d) H3: prefix -> section-specific name
            elif col_b.startswith("H3: "):
                h3_map = {
                    "FEATURES & AMENITIES": "Amenities H3",
                    "PROPERTY TYPES": "Property Types H3",
                    "PAYMENT PLAN": "Payment Plan H3",
                }
                if current_section in h3_map:
                    field_name = h3_map[current_section]
                elif "Lifestyle" in col_b:
                    field_name = "Lifestyle H3"
                elif "Healthcare" in col_b:
                    field_name = "Healthcare H3"
                elif "Education" in col_b:
                    field_name = "Education H3"
                else:
                    field_name = f"{current_section.title()} H3"
                # Move display heading text from C to guideline
                if en_out:
                    guideline = (
                        f"{guideline}. Display: {en_out}" if guideline
                        else f"Display: {en_out}"
                    )
                    en_out = ""

            # e) CTA -> section-specific name
            elif col_b == "CTA":
                cta_map = {
                    "HERO": "Hero CTA",
                    "PROJECT DETAILS CARD": "Card CTA",
                    "PROPERTY TYPES": "Floor Plans CTA",
                    "INVESTMENT": "Investment CTA",
                }
                field_name = cta_map.get(current_section, f"{current_section.title()} CTA")
                # Keep CTA text in C (static per-template content)

            # f) PP short description -> descriptive name
            elif col_b == "PP short description":
                field_name = "Payment Plan Description"

            # g) Meta fields with trailing colons
            elif col_b.rstrip(":").strip().lower() == "meta title":
                field_name = "Meta Title"
            elif col_b.rstrip(":").strip().lower() == "meta description":
                field_name = "Meta Description"

            # h) URL slug normalization
            elif col_b == "Url Slug":
                field_name = "URL Slug"

            # i) Project Details Card fields (disambiguate from Hero)
            elif current_section == "PROJECT DETAILS CARD":
                card_map = {
                    "Starting Price": "Card Starting Price",
                    "Handover": "Card Handover",
                    "Payment Plan": "Card Payment Plan",
                    "Area": "Card Area",
                    "Property Type": "Card Property Type",
                    "Bedrooms": "Card Bedrooms",
                    "Developer": "Card Developer",
                    "Location": "Card Location",
                }
                field_name = card_map.get(col_b.strip(), col_b.strip())

            # j) FAQ topic categories -> Q/A pair fields
            elif current_section == "FAQ" and not col_b.startswith("H2:"):
                faq_counter += 1
                topic = col_b
                emit(f"Topic: {topic}", f"FAQ {faq_counter} - Question", "", "", "")
                emit(f"Answer for: {topic}", f"FAQ {faq_counter} - Answer", "", "", "")
                continue

            # k) Default: use existing name, strip trailing colons/whitespace
            else:
                field_name = col_b.rstrip(":").strip()

        # CASE 2: No B field name, has A guideline (note-only rows needing field names)
        elif col_a and not col_b:
            a_lower = col_a.lower()

            if current_section == "FEATURES & AMENITIES":
                # "bullets below text" note -> merge into next content row
                pending_note = col_a
                continue

            elif current_section == "INVESTMENT":
                if "always check" in a_lower:
                    field_name = "Investment Intro"
                elif "bullets" in a_lower:
                    field_name = "Investment Bullet Points"
                else:
                    pending_note = col_a
                    continue

            elif current_section == "ABOUT THE AREA":
                if "1-3 sentences" in a_lower:
                    if last_h3_sub:
                        sub_map = {
                            "Lifestyle": "Lifestyle Description",
                            "Healthcare": "Healthcare Description",
                            "Education": "Education Description",
                        }
                        field_name = sub_map.get(last_h3_sub, "Area Description")
                    else:
                        field_name = "Area Description"
                elif "text below h3" in a_lower:
                    sub_map = {
                        "Lifestyle": "Lifestyle Description",
                        "Healthcare": "Healthcare Description",
                        "Education": "Education Description",
                    }
                    field_name = sub_map.get(last_h3_sub, "Area Sub-Description")
                elif "bullet" in a_lower:
                    sub_map = {
                        "Lifestyle": "Lifestyle Bullets",
                        "Healthcare": "Healthcare Bullets",
                        "Education": "Education Bullets",
                    }
                    field_name = sub_map.get(last_h3_sub, "Area Bullets")
                else:
                    pending_note = col_a
                    continue

            elif current_section == "DEVELOPER":
                if "sentences about" in a_lower or "developer" in a_lower:
                    field_name = "Developer Description"
                else:
                    pending_note = col_a
                    continue

            else:
                pending_note = col_a
                continue

        # CASE 3: No A, no B, has C only -- skip (no field name possible)
        else:
            continue

        # Emit the row if we have a field name
        if field_name:
            emit(guideline, field_name, en_out, ar_out, ru_out)

    return result, (
        "OPR: Renamed <p>/H2:/H3:/CTA to descriptive names, "
        "added section markers, moved notes from content columns to guidelines, "
        "restructured FAQ into Q/A pairs with topic guidelines."
    )


def current_b_is_h2(col_b):
    """Check if column B value is an H2 marker (including corrupted)."""
    return col_b in ("H2", "\u041d2")


def create_standardized_sheet(gc, drive, folder_id, name, tab_name, data):
    """Create a new spreadsheet directly in the Shared Drive subfolder."""
    # Create spreadsheet directly in the Shared Drive folder
    # (avoids service account personal Drive storage quota)
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [folder_id],
    }
    created = drive.files().create(
        body=file_metadata,
        supportsAllDrives=True,
        fields="id, webViewLink",
    ).execute()

    sheet_id = created["id"]
    url = created.get("webViewLink", f"https://docs.google.com/spreadsheets/d/{sheet_id}")

    # Open with gspread to write data
    spreadsheet = gc.open_by_key(sheet_id)

    # Rename the first tab
    ws = spreadsheet.sheet1
    ws.update_title(tab_name)

    # Resize to fit data
    num_rows = len(data)
    num_cols = max(len(row) for row in data) if data else 5
    ws.resize(rows=max(num_rows, 1), cols=max(num_cols, 5))

    # Write all data in one batch
    if data:
        cell_range = f"A1:{chr(64 + num_cols)}{num_rows}"
        ws.update(cell_range, data, value_input_option="RAW")

    return sheet_id, url


def main():
    dry_run = "--dry-run" in sys.argv

    # --only=<name> to process a single template
    only = None
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            only = arg.split("=", 1)[1]

    gc, drive = get_clients()

    if dry_run:
        print("=== DRY RUN MODE (no sheets will be created) ===\n")
    else:
        print("Creating 'Standardized Templates' subfolder...")
        folder_id = create_subfolder(drive)
        print()

    templates_to_process = TEMPLATES
    if only:
        if only not in TEMPLATES:
            print(f"Error: unknown template '{only}'. Valid: {list(TEMPLATES.keys())}")
            sys.exit(1)
        templates_to_process = {only: TEMPLATES[only]}
        print(f"Processing only: {only.upper()}\n")

    results = {}

    for template_name, config in templates_to_process.items():
        print(f"Processing {template_name.upper()}...")
        print(f"  Reading from: {config['sheet_id'][:20]}...")

        # Read original
        original = read_template(gc, config["sheet_id"])
        print(f"  Original: {original['row_count']} rows, header: {original['header']}")

        # Apply standardization
        if template_name == "mpp":
            standardized, description = standardize_mpp(original)
        elif template_name == "aggregators":
            standardized, description = standardize_aggregators(original)
        elif template_name == "adop":
            standardized, description = standardize_adop(original)
        elif template_name == "commercial":
            standardized, description = standardize_commercial(original)
        elif template_name == "adre":
            standardized, description = standardize_adre(original)
        elif template_name == "opr":
            standardized, description = standardize_opr(original)
        else:
            print(f"  SKIPPED: no standardization function for {template_name}")
            continue

        print(f"  Transform: {description}")
        print(f"  Output: {len(standardized)} rows, header: {standardized[0]}")

        if dry_run:
            # Preview first 10 rows
            print(f"  Preview (first 10 data rows):")
            for j, row in enumerate(standardized[1:11], start=2):
                non_empty = {chr(65+k): v for k, v in enumerate(row) if v.strip()}
                if non_empty:
                    print(f"    Row {j}: {non_empty}")
            print()
        else:
            # Create the standardized copy
            print(f"  Creating: {config['output_name']}...")
            sheet_id, url = create_standardized_sheet(
                gc, drive, folder_id,
                config["output_name"],
                original["tab_name"],
                standardized,
            )
            print(f"  Created: {url}")
            results[template_name] = {
                "sheet_id": sheet_id,
                "url": url,
                "name": config["output_name"],
                "rows": len(standardized),
            }

            # Rate limit: wait between API calls
            time.sleep(2)

        print()

    if not dry_run and results:
        # Save results (merge with existing to preserve previous standardizations)
        output_path = Path(__file__).resolve().parent / "standardized_template_ids.json"
        existing = {}
        if output_path.exists():
            with open(output_path) as f:
                existing = json.load(f)
        existing.update(results)
        with open(output_path, "w") as f:
            json.dump(existing, f, indent=2)
        print(f"Results saved to: {output_path}")

        print("\n=== SUMMARY ===")
        for name, info in results.items():
            print(f"  {name.upper()}: {info['url']}")


if __name__ == "__main__":
    main()
