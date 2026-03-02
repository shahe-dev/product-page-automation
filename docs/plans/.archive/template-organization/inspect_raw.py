"""Inspect raw template data to understand structure."""
import json

with open('c:/Users/shahe/PDP Automation v.3/template-organization/aggregator_templates_raw.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

output = []

# Pick a few templates to examine
templates_to_check = ['difc-residences.ae', 'urban-luxury.penthouse.ae', 'sobha-central.ae']

for name in templates_to_check:
    if name not in data:
        output.append(f"{name}: NOT FOUND")
        continue

    t = data[name]
    output.append(f"\n{'='*60}")
    output.append(f"TEMPLATE: {name}")
    output.append(f"{'='*60}")

    if 'error' in t:
        output.append(f"ERROR: {t['error']}")
        continue

    output.append(f"Sheet title: {t.get('sheet_title', 'N/A')}")
    output.append(f"Row count: {t.get('row_count', 0)}")

    raw = t.get('raw_data', [])
    output.append(f"\nFirst 60 rows:")
    for i, row in enumerate(raw[:60]):
        # Truncate long values, ASCII only
        safe_row = []
        for c in row:
            s = str(c)[:60]
            # Replace non-ASCII
            s = ''.join(ch if ord(ch) < 128 else '?' for ch in s)
            safe_row.append(s)
        output.append(f"  {i:2d}: {safe_row}")

# Write to file
with open('c:/Users/shahe/PDP Automation v.3/template-organization/raw_inspection.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("Output written to raw_inspection.txt")
