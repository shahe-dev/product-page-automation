"""
Aggregator Template Analysis v2 - Correct field extraction from Column A.
Detect duplicates, compare structures, identify consolidation opportunities.
"""

import json
import hashlib
from pathlib import Path
from collections import defaultdict

# Load the raw data
RAW_PATH = Path(__file__).parent / "aggregator_templates_raw.json"

def normalize_field(field):
    """Normalize field name for comparison - keep only ASCII."""
    if not field:
        return ""
    # Replace non-ASCII with placeholder
    normalized = ''.join(c if ord(c) < 128 else '_' for c in str(field))
    return normalized.lower().strip()

def extract_fields_from_column_a(raw_data):
    """Extract field names from column A (first column)."""
    fields = []
    for row in raw_data:
        if row and len(row) > 0:
            field = str(row[0]).strip()
            if field:
                fields.append(field)
    return fields

def create_structure_hash(fields):
    """Create a hash of the field structure for duplicate detection."""
    normalized = [normalize_field(f) for f in fields if normalize_field(f)]
    structure_str = '|'.join(normalized)
    return hashlib.md5(structure_str.encode()).hexdigest()

def main():
    with open(RAW_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 70)
    print("AGGREGATOR TEMPLATE ANALYSIS v2")
    print("=" * 70)

    # Extract fields and create hashes
    template_info = {}
    hash_groups = defaultdict(list)

    for name, t in data.items():
        if 'error' in t:
            print(f"  ERROR - {name}: {t['error']}")
            continue

        raw_data = t.get('raw_data', [])
        fields = extract_fields_from_column_a(raw_data)

        # Create structure hash
        struct_hash = create_structure_hash(fields)

        template_info[name] = {
            'row_count': t.get('row_count', 0),
            'field_count': len(fields),
            'fields': fields,
            'hash': struct_hash
        }

        hash_groups[struct_hash].append(name)

    # Report duplicates
    print("\n" + "=" * 70)
    print("DUPLICATE DETECTION (identical structures)")
    print("=" * 70)

    unique_templates = []
    duplicate_count = 0

    for struct_hash, templates in hash_groups.items():
        if len(templates) > 1:
            print(f"\nDUPLICATE GROUP (hash: {struct_hash[:8]}...):")
            for t in templates:
                print(f"  - {t} ({template_info[t]['field_count']} fields)")
            unique_templates.append(templates[0])  # Keep one representative
            duplicate_count += len(templates) - 1
        else:
            unique_templates.append(templates[0])
            print(f"\nUNIQUE: {templates[0]} ({template_info[templates[0]]['field_count']} fields)")

    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {len(data)} total, {len(unique_templates)} unique, {duplicate_count} duplicates")
    print("=" * 70)

    # Detailed comparison of unique templates
    print("\n" + "=" * 70)
    print("UNIQUE TEMPLATE COMPARISON")
    print("=" * 70)

    # Extract common fields across unique templates
    all_fields = defaultdict(list)
    for name in unique_templates:
        for field in template_info[name]['fields']:
            norm = normalize_field(field)
            if norm and len(norm) > 1:  # Skip empty/single char
                all_fields[norm].append(name)

    # Core fields (in all or most templates)
    total_unique = len(unique_templates)
    core_fields = []
    common_fields = []
    rare_fields = []

    for field, templates in all_fields.items():
        pct = len(templates) / total_unique * 100
        if pct >= 80:
            core_fields.append((field, len(templates), pct))
        elif pct >= 40:
            common_fields.append((field, len(templates), pct))
        else:
            rare_fields.append((field, len(templates), pct))

    print(f"\nCORE FIELDS (80%+ of templates):")
    for field, count, pct in sorted(core_fields, key=lambda x: -x[1]):
        print(f"  {count}/{total_unique} ({pct:.0f}%): {field}")

    print(f"\nCOMMON FIELDS (40-80% of templates):")
    for field, count, pct in sorted(common_fields, key=lambda x: -x[1]):
        print(f"  {count}/{total_unique} ({pct:.0f}%): {field}")

    print(f"\nRARE/UNIQUE FIELDS (<40% of templates):")
    for field, count, pct in sorted(rare_fields, key=lambda x: -x[1])[:30]:
        templates_using = all_fields[field]
        print(f"  {count}/{total_unique} ({pct:.0f}%): {field} -> {templates_using}")

    # Output detailed structure for each unique template
    print("\n" + "=" * 70)
    print("DETAILED STRUCTURE BY TEMPLATE")
    print("=" * 70)

    for name in sorted(unique_templates):
        info = template_info[name]
        print(f"\n--- {name} ({info['field_count']} fields) ---")
        for i, field in enumerate(info['fields'][:50]):  # First 50 fields
            safe_field = ''.join(c if ord(c) < 128 else '?' for c in field)
            print(f"  {i:2d}. {safe_field[:60]}")
        if len(info['fields']) > 50:
            print(f"  ... and {len(info['fields']) - 50} more")

    # Save analysis
    analysis = {
        'total_templates': len(data),
        'unique_templates': len(unique_templates),
        'duplicates': duplicate_count,
        'hash_groups': {k: v for k, v in hash_groups.items()},
        'core_fields': [f[0] for f in core_fields],
        'common_fields': [f[0] for f in common_fields],
        'rare_fields': [f[0] for f in rare_fields],
        'template_structures': {
            name: {
                'fields': [''.join(c if ord(c) < 128 else '?' for c in f) for f in template_info[name]['fields']],
                'hash': template_info[name]['hash']
            }
            for name in unique_templates
        }
    }

    output_path = Path(__file__).parent / "template_analysis_v2.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"\n\nAnalysis saved to: {output_path}")

if __name__ == "__main__":
    main()
