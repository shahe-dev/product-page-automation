"""
Fetch and analyze all aggregator templates from Drive.
Extract fields, compare structures, identify clusters.
"""

import json
from pathlib import Path
from collections import defaultdict

from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDENTIALS_PATH = Path(__file__).parent.parent / ".credentials" / "service-account-key.json"
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

AGGREGATOR_IDS = {
    "capital.luxury": "1rkymdZERDJSuWJj1FP0cP-WPlrWx8HMHG-1UnnJnh4I",
    "luxury-villas-dubai.ae": "1fXylQbpSEYTd8ELZHKv3z2QNjGg2W-K6s5RP70MR9O4",
    "bloom.living": "1tBzXEc8lrsrFFtwWNoRhIpGx2X6uVubQ0NALaDOnrkw",
    "sharjah.residences.ae": "15RlmEA6Lp_9uq6zMOmunkn9fobLE0HiPrTG7Skwu3jg",
    "luxury-collection.ae": "1L_lgRAc83DZI5SI-AK1sCtKrkVjPXqr1oNAxw74f9eU",
    "the-valley-villas": "1Zp_H6ZS42l4WDGWoWn7W-dNkZJ9_miU1B0CiQSCBKcs",
    "dubai-harbour-property.ae": "13rPGKTzHbdVIjc5IMd0ezhxNn0LK7BmeSQ4vff7bGiM",
    "sobha-hartland": "1P1KmHuMvPP9hq6GGe7heFowF9fDddaWj0__uo20q7yM",
    "luxury-villas-dubai.ae-2": "1KHYxx7I8Bw0_MyW-wkle5UevsoRC9XOvTfp3D3dQQII",
    "tilal-al-ghaf": "1soLSusEkewiYlroIu2J-Hk5_TtIdAJQYtpCWk5OOK_0",
    "urban-luxury.penthouse.ae": "10fWBwjaoLBwy63Jq1ffnpv9TTeJVvtlNRQlH8E4yIKM",
    "ras-al-khaimah-properties.ae": "1wK1hrxVAwPsuHYUlcP0btYqh5F1VsDWv3IEwbyV-lks",
    "saudi-estates.com": "1UbtPAuYScuvnw-jP_A3IsFu2QCm8bUClQ-zqgOaOGQc",
    "dubai-creek-living.ae": "1f9sBDW3zcW5hS5LDJvp0868Hr-1xOxT3izFTuyjwxLs",
    "urbanvillas-dubaisouth.ae": "1ciZRJCXE5f2aTDR5EU0W-YJ4om0wHQoLXk37KxNKFsM",
    "dubaihills-property.ae": "1clQOW6w53S4b9vQ-1TaUm3VsPw2fbYTQHpFzR69Lti0",
    "dubaislands.ae": "1mRSyQNZz5PAAqnJs9DXo75VkrcvoJlH74LaOaWFde30",
    "city-walk-property.ae": "1-PKBkSIV4N6PZqdW94E3pgQja3dTJd1BnwKlxOPnmso",
    "rashid-yachts-marina.ae": "10xsSOy8HGqpsF8RFabGryFhA0n3bxC4bSm1HeDAwrXw",
    "dubaimaritime-city.ae": "10KMdz8YKqEsx-GDbM63vnx9Tv9sL6ashlOzlhgSHZXc",
    "sobha-central.ae": "16Q67eQ4qldByrM5Nfl6866N4__KgsKY5-hyTJc5Dyq8",
    "difc-residences.ae": "15rVhm6LAd8n9j_Iej7ns7HWBTpO99srbXeeFTKxOXlc",
}

def get_credentials():
    return service_account.Credentials.from_service_account_file(
        str(CREDENTIALS_PATH), scopes=SCOPES
    )

def read_sheet_fields(sheet_id, name):
    """Read a sheet and extract the field names (column B typically)."""
    creds = get_credentials()
    sheets = build('sheets', 'v4', credentials=creds)

    try:
        # Get sheet metadata first
        metadata = sheets.spreadsheets().get(
            spreadsheetId=sheet_id,
            includeGridData=False
        ).execute()

        sheet_name = metadata['sheets'][0]['properties']['title']

        # Read the data
        result = sheets.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{sheet_name}'!A1:E200"
        ).execute()

        values = result.get('values', [])

        # Extract fields (typically in column B)
        fields = []
        sections = []
        current_section = None

        for i, row in enumerate(values):
            if len(row) >= 2:
                col_a = row[0].strip() if row[0] else ""
                col_b = row[1].strip() if len(row) > 1 and row[1] else ""

                # Check if it's a section header (usually col_a says "SECTION" or col_b has H2/H3)
                if col_a.upper() == "SECTION" or "H2:" in col_b or "H3:" in col_b:
                    current_section = col_b
                    sections.append(col_b)

                # Check if col_b contains a field name
                if col_b and col_b not in ['', 'Fields', 'HERO SECTION', 'PROJECT OVERVIEW']:
                    # Skip if it's clearly a guideline not a field
                    if not col_b.startswith("Includes") and not col_b.startswith("Focus on"):
                        fields.append({
                            'row': i + 1,
                            'field': col_b,
                            'section': current_section,
                            'guideline': col_a
                        })

        return {
            'name': name,
            'sheet_title': sheet_name,
            'row_count': len(values),
            'field_count': len(fields),
            'sections': sections,
            'fields': fields,
            'raw_data': values  # Keep raw for detailed analysis
        }

    except Exception as e:
        return {
            'name': name,
            'error': str(e)
        }

def extract_field_names(template_data):
    """Extract just the field names for comparison."""
    if 'error' in template_data:
        return []
    return [f['field'] for f in template_data.get('fields', [])]

def normalize_field_name(field):
    """Normalize field names for comparison."""
    # Remove common variations
    normalized = field.lower().strip()
    normalized = normalized.replace(':', '').replace('-', ' ')
    normalized = normalized.replace('h1', '').replace('h2', '').replace('h3', '')
    normalized = normalized.replace('<p>', '').replace('</p>', '')
    return normalized.strip()

def calculate_similarity(fields1, fields2):
    """Calculate Jaccard similarity between two field sets."""
    set1 = set(normalize_field_name(f) for f in fields1)
    set2 = set(normalize_field_name(f) for f in fields2)

    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union

def main():
    print("=" * 70)
    print("AGGREGATOR TEMPLATE ANALYSIS")
    print("=" * 70)

    all_templates = {}
    all_fields = defaultdict(list)  # field -> list of templates using it

    # Fetch all templates
    for name, sheet_id in AGGREGATOR_IDS.items():
        print(f"Reading: {name}...")
        data = read_sheet_fields(sheet_id, name)
        all_templates[name] = data

        if 'error' not in data:
            for field in data.get('fields', []):
                normalized = normalize_field_name(field['field'])
                all_fields[normalized].append(name)

    # Save raw data
    output_path = Path(__file__).parent / "aggregator_templates_raw.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_templates, f, indent=2, ensure_ascii=False)
    print(f"\nRaw data saved to: {output_path}")

    # Analysis
    print("\n" + "=" * 70)
    print("FIELD FREQUENCY ANALYSIS")
    print("=" * 70)

    # Sort fields by frequency
    field_freq = [(field, len(templates)) for field, templates in all_fields.items()]
    field_freq.sort(key=lambda x: -x[1])

    print("\nMost Common Fields (appearing in 10+ templates):")
    common_fields = []
    for field, count in field_freq:
        if count >= 10:
            print(f"  {count:2d} templates: {field}")
            common_fields.append(field)

    print(f"\nUnique Fields (appearing in only 1 template):")
    unique_fields = [(f, t) for f, t in all_fields.items() if len(t) == 1]
    for field, templates in unique_fields[:20]:
        print(f"  {field} -> {templates[0]}")
    if len(unique_fields) > 20:
        print(f"  ... and {len(unique_fields) - 20} more")

    # Similarity matrix
    print("\n" + "=" * 70)
    print("TEMPLATE SIMILARITY ANALYSIS")
    print("=" * 70)

    template_names = list(all_templates.keys())
    similarity_matrix = {}

    for i, name1 in enumerate(template_names):
        fields1 = extract_field_names(all_templates[name1])
        similarities = []
        for name2 in template_names:
            fields2 = extract_field_names(all_templates[name2])
            sim = calculate_similarity(fields1, fields2)
            similarities.append((name2, sim))
        similarity_matrix[name1] = similarities

    # Find clusters (templates with >80% similarity)
    clusters = []
    clustered = set()

    for name1 in template_names:
        if name1 in clustered:
            continue
        cluster = [name1]
        for name2, sim in similarity_matrix[name1]:
            if name2 != name1 and sim > 0.8 and name2 not in clustered:
                cluster.append(name2)
                clustered.add(name2)
        if len(cluster) > 1:
            clusters.append(cluster)
            clustered.add(name1)

    # Also add singletons (unique templates)
    for name in template_names:
        if name not in clustered:
            clusters.append([name])

    print(f"\nIdentified {len(clusters)} potential template groups:")
    for i, cluster in enumerate(clusters, 1):
        if len(cluster) > 1:
            print(f"\n  Group {i} ({len(cluster)} templates - POTENTIAL CONSOLIDATION):")
            for name in cluster:
                fc = all_templates[name].get('field_count', 0)
                print(f"    - {name} ({fc} fields)")
        else:
            fc = all_templates[cluster[0]].get('field_count', 0)
            print(f"\n  Group {i} (unique): {cluster[0]} ({fc} fields)")

    # Save analysis
    analysis = {
        'total_templates': len(all_templates),
        'total_unique_fields': len(all_fields),
        'common_fields': common_fields,
        'unique_fields_count': len(unique_fields),
        'field_frequency': dict(field_freq),
        'clusters': clusters,
        'similarity_matrix': {k: [(n, round(s, 2)) for n, s in v] for k, v in similarity_matrix.items()}
    }

    analysis_path = Path(__file__).parent / "template_analysis.json"
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"\nAnalysis saved to: {analysis_path}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total templates analyzed: {len(all_templates)}")
    print(f"  Total unique fields found: {len(all_fields)}")
    print(f"  Fields appearing in 10+ templates: {len(common_fields)}")
    print(f"  Unique/one-off fields: {len(unique_fields)}")
    print(f"  Potential consolidation groups: {len([c for c in clusters if len(c) > 1])}")

if __name__ == "__main__":
    main()
