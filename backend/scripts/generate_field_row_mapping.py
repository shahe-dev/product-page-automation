#!/usr/bin/env python
"""
Generate field_row_mappings.json for Phase 2 Engineering.

Reads:
- Google Sheets (for actual row numbers)
- Field registries (for section, type, char_limit, required)
- FIELD_LABEL_MAPPINGS (for label -> field_name conversion)

Output format:
{
  "adop": {
    "meta_title": {"row": 3, "section": "SEO", "char_limit": 70, "required": true, "field_type": "GENERATED"},
    ...
  },
  ...
}

Usage:
    python scripts/generate_field_row_mapping.py
    python scripts/generate_field_row_mapping.py --template adop
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from sync script - uses the same sheet IDs and mappings
from sync_sheet_to_registry import (
    SHEET_IDS, FIELD_LABEL_MAPPINGS, COMBINED_BULLET_FIELDS, title_to_snake, read_sheet
)

# Auth configuration (matches sync_sheet_to_registry.py)
CREDS_PATH = Path(__file__).resolve().parent.parent.parent / ".credentials" / "service-account-key.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_gspread_client() -> gspread.Client:
    """Initialize gspread client with service account credentials."""
    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    return gspread.authorize(creds)

REGISTRY_PATHS = {
    "opr": "prompt-organizaton/01-opr",
    "adop": "prompt-organizaton/02-adop",
    "adre": "prompt-organizaton/03-adre",
    "commercial": "prompt-organizaton/04-commercial",
    "aggregators": "prompt-organizaton/05-aggregators",
    "mpp": "prompt-organizaton/06-mpp",
}


@dataclass
class FieldMapping:
    """A field mapping with all metadata."""
    row: int
    section: str
    char_limit: Optional[int]
    required: bool
    field_type: str  # GENERATED, EXTRACTED, HYBRID, STATIC
    sheet_label: str  # Original label from sheet


def parse_registry(template: str) -> dict[str, dict]:
    """Parse field registry markdown file, return field metadata."""
    project_root = Path(__file__).parent.parent.parent
    registry_path = project_root / REGISTRY_PATHS[template] / f"{template}-field-registry.md"

    if not registry_path.exists():
        print(f"  WARNING: Registry not found: {registry_path}")
        return {}

    content = registry_path.read_text(encoding="utf-8")

    # Find the Field Table section
    table_match = re.search(
        r'\| field_name \| section \| type \| char_limit \| required \| notes \|.*?\n\|[-|]+\|\n(.*?)(?=\n\n|\n##|\Z)',
        content,
        re.DOTALL
    )

    if not table_match:
        print(f"  WARNING: Could not find field table in {registry_path}")
        return {}

    fields = {}
    for line in table_match.group(1).strip().split('\n'):
        if not line.strip() or line.startswith('|--'):
            continue

        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7:
            continue

        # parts[0] is empty (before first |), parts[1] is field_name, etc.
        field_name = parts[1]
        section = parts[2]
        field_type = parts[3]
        char_limit_str = parts[4]
        required_str = parts[5]

        # Parse char_limit
        char_limit = None
        if char_limit_str and char_limit_str != '-':
            try:
                char_limit = int(char_limit_str)
            except ValueError:
                pass

        # Parse required
        required = required_str.lower() == 'yes'

        fields[field_name] = {
            'section': section,
            'field_type': field_type,
            'char_limit': char_limit,
            'required': required,
        }

    return fields


def generate_mapping_for_template(gc: gspread.Client, template: str) -> dict[str, dict]:
    """Generate field-to-row mapping for a single template."""
    print(f"\n{'='*60}")
    print(f"Processing: {template}")
    print(f"{'='*60}")

    # Step 1: Read sheet rows using sync script's read_sheet
    print(f"\n1. Reading Google Sheet...")
    raw_rows = read_sheet(gc, template)
    # Keep full SheetRow objects for access to guidelines
    sheet_rows = [r for r in raw_rows if r.field_label.strip()]
    print(f"   Found {len(sheet_rows)} non-empty rows")

    # Step 2: Parse registry
    print(f"\n2. Parsing field registry...")
    registry_fields = parse_registry(template)
    print(f"   Found {len(registry_fields)} fields in registry")

    # Step 3: Build mapping
    print(f"\n3. Building field-to-row mapping...")

    # Get explicit mappings for this template
    explicit_mappings = FIELD_LABEL_MAPPINGS.get(template, {})

    result = {}
    unmapped_labels = []
    unmapped_fields = set(registry_fields.keys())

    for row in sheet_rows:
        row_num = row.row_number
        label = row.field_label
        guidelines = row.guidelines

        # Skip header row
        if row_num == 1 or label.lower() in ('fields', 'field', 'guidelines'):
            continue
        # Skip section headers (guidelines column says "SECTION")
        if guidelines.upper() == 'SECTION':
            continue
        # Skip generic labels like <p>, CTA, etc.
        if label.startswith('<') and label.endswith('>'):
            continue

        # Convert label to field name
        if label in explicit_mappings:
            field_name = explicit_mappings[label]
        else:
            field_name = title_to_snake(label, template)

        if not field_name:
            continue

        # Look up in registry
        if field_name in registry_fields:
            reg = registry_fields[field_name]
            result[field_name] = {
                'row': row_num,
                'section': reg['section'],
                'char_limit': reg['char_limit'],
                'required': reg['required'],
                'field_type': reg['field_type'],
                'sheet_label': label,
            }
            unmapped_fields.discard(field_name)
        else:
            unmapped_labels.append((row_num, label, field_name))

    # Step 4: Handle combined bullet fields
    # Some templates have aggregated sheet rows (e.g., "Amenity Bullet Points")
    # that correspond to multiple registry fields (amenity_bullet_1, amenity_bullet_2, etc.)
    combined_fields = COMBINED_BULLET_FIELDS.get(template, {})
    if combined_fields:
        print(f"\n4. Processing combined bullet fields...")

        for combined_name, individual_fields in combined_fields.items():
            # Find the row for this combined field
            # The combined field name (e.g., "overview_bullet_points") comes from title_to_snake()
            # We need to find the original sheet label
            combined_row = None
            combined_label = None
            for row in sheet_rows:
                snake = title_to_snake(row.field_label, template)
                if snake == combined_name:
                    combined_row = row.row_number
                    combined_label = row.field_label
                    break

            if combined_row is None:
                print(f"      WARNING: Combined field '{combined_name}' not found in sheet")
                continue

            # Map all individual fields to this row
            mapped_count = 0
            for ind_field in individual_fields:
                if ind_field in registry_fields and ind_field not in result:
                    reg = registry_fields[ind_field]
                    result[ind_field] = {
                        'row': combined_row,
                        'section': reg['section'],
                        'char_limit': reg['char_limit'],
                        'required': reg['required'],
                        'field_type': reg['field_type'],
                        'sheet_label': combined_label,
                        'combined_field': combined_name,  # Track that this is part of a combined field
                    }
                    unmapped_fields.discard(ind_field)
                    mapped_count += 1

            if mapped_count > 0:
                print(f"      {combined_name} (row {combined_row}): mapped {mapped_count} individual fields")

    # Report
    print(f"\n5. Results:")
    print(f"   Mapped: {len(result)} fields")

    if unmapped_labels:
        print(f"\n   Sheet labels not in registry ({len(unmapped_labels)}):")
        for row, label, fname in unmapped_labels[:10]:
            print(f"      Row {row}: '{label}' -> '{fname}'")
        if len(unmapped_labels) > 10:
            print(f"      ... and {len(unmapped_labels) - 10} more")

    if unmapped_fields:
        print(f"\n   Registry fields not in sheet ({len(unmapped_fields)}):")
        for fname in sorted(unmapped_fields)[:10]:
            print(f"      {fname}")
        if len(unmapped_fields) > 10:
            print(f"      ... and {len(unmapped_fields) - 10} more")

    return result


def main():
    parser = argparse.ArgumentParser(description="Generate field_row_mappings.json")
    parser.add_argument("--template", "-t", help="Single template to process")
    parser.add_argument("--output", "-o", default="backend/scripts/field_row_mappings.json",
                        help="Output file path")
    args = parser.parse_args()

    # Authenticate
    print("Authenticating with Google Sheets API...")
    gc = get_gspread_client()
    print("Authenticated.")

    # Determine templates to process
    if args.template:
        templates = [args.template]
    else:
        templates = list(SHEET_IDS.keys())

    # Generate mappings
    all_mappings = {}
    for template in templates:
        try:
            mapping = generate_mapping_for_template(gc, template)
            # Remove internal tracking fields from output
            cleaned = {
                field_name: {k: v for k, v in data.items() if k not in ('sheet_label', 'combined_field')}
                for field_name, data in mapping.items()
            }
            all_mappings[template] = cleaned
        except Exception as e:
            print(f"\n  ERROR processing {template}: {e}")
            all_mappings[template] = {"error": str(e)}

    # Write output
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / args.output

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_mappings, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"OUTPUT: {output_path}")
    print(f"{'='*60}")

    # Summary
    print("\nSUMMARY:")
    total_fields = 0
    for template, mapping in all_mappings.items():
        if "error" in mapping:
            print(f"  {template}: ERROR - {mapping['error']}")
        else:
            count = len(mapping)
            total_fields += count
            print(f"  {template}: {count} fields mapped")

    print(f"\nTotal: {total_fields} fields across {len(templates)} templates")


if __name__ == "__main__":
    main()
