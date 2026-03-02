"""
Analyze scraped page structures to extract:
- Section types per site
- Character limits per section
- Heading patterns
- Comparison to templates
"""

import json
import re
from pathlib import Path
from collections import defaultdict

SCRAPED_PATH = Path(__file__).parent / "scraped_pages" / "page_structures.json"
OUTPUT_DIR = Path(__file__).parent

def extract_section_type(text, classes, heading_texts):
    """Identify section type from content clues."""
    combined = f"{text} {classes} {' '.join(heading_texts)}".lower()

    # Priority order matters
    if any(k in combined for k in ["hero", "banner", "intro", "main-screen"]):
        return "hero"
    if any(k in combined for k in ["floor plan", "floorplan", "unit type", "layout"]):
        return "floor_plans"
    if any(k in combined for k in ["payment", "price", "pricing", "investment"]):
        return "payment_plan"
    if any(k in combined for k in ["amenities", "amenity", "facilities", "feature"]):
        return "amenities"
    if any(k in combined for k in ["location", "map", "area", "neighborhood", "nearby"]):
        return "location"
    if any(k in combined for k in ["developer", "builder", "about the developer"]):
        return "developer"
    if any(k in combined for k in ["faq", "question", "frequently"]):
        return "faq"
    if any(k in combined for k in ["gallery", "photo", "image", "slider"]):
        return "gallery"
    if any(k in combined for k in ["about", "overview", "description", "project"]):
        return "about"
    if any(k in combined for k in ["contact", "form", "register", "inquiry"]):
        return "contact"

    return "other"

def analyze_headings(headings):
    """Analyze heading patterns and lengths."""
    h1s = [h for h in headings if h["tag"] == "h1"]
    h2s = [h for h in headings if h["tag"] == "h2"]
    h3s = [h for h in headings if h["tag"] == "h3"]

    return {
        "h1_count": len(h1s),
        "h2_count": len(h2s),
        "h3_count": len(h3s),
        "h1_lengths": [h["length"] for h in h1s],
        "h2_lengths": [h["length"] for h in h2s],
        "h3_lengths": [h["length"] for h in h3s],
        "h1_texts": [h["text"][:80] for h in h1s],
        "h2_texts": [h["text"][:80] for h in h2s[:10]],  # First 10
    }

def main():
    with open(SCRAPED_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 70)
    print("PAGE STRUCTURE ANALYSIS")
    print("=" * 70)

    # Aggregate analysis
    all_sections = defaultdict(list)  # section_type -> list of (site, length)
    all_headings = defaultdict(list)  # heading_tag -> list of lengths
    site_structures = {}

    for site, page_data in data.items():
        if page_data["status"] != "success":
            print(f"\n{site}: FAILED - {page_data.get('errors', [])}")
            continue

        print(f"\n{'=' * 50}")
        print(f"SITE: {site}")
        print(f"{'=' * 50}")

        # Meta analysis
        meta = page_data.get("meta", {})
        print(f"Meta Title: {meta.get('title_length', 0)} chars")
        print(f"Meta Desc: {meta.get('description_length', 0)} chars")

        # Heading analysis
        headings = page_data.get("headings", [])
        h_analysis = analyze_headings(headings)
        print(f"H1: {h_analysis['h1_count']} (lengths: {h_analysis['h1_lengths']})")
        print(f"H2: {h_analysis['h2_count']} (avg length: {sum(h_analysis['h2_lengths'])/max(len(h_analysis['h2_lengths']),1):.0f})")
        print(f"H3: {h_analysis['h3_count']}")

        # Collect heading lengths
        for h in headings:
            all_headings[h["tag"]].append(h["length"])

        # Section analysis
        sections = page_data.get("sections", [])
        detected = page_data.get("detected_patterns", [])

        print(f"Detected patterns: {detected}")

        # Classify sections
        site_sections = defaultdict(list)
        for sec in sections:
            heading_texts = [h["text"] for h in sec.get("headings", [])]
            sec_type = extract_section_type(
                sec.get("text_preview", ""),
                sec.get("classes", ""),
                heading_texts
            )
            text_len = sec.get("text_length", 0)
            if text_len > 0:
                site_sections[sec_type].append(text_len)
                all_sections[sec_type].append((site, text_len))

        print(f"\nSection content lengths:")
        for sec_type in ["hero", "about", "amenities", "payment_plan", "location", "developer", "faq", "floor_plans"]:
            if sec_type in site_sections:
                lengths = site_sections[sec_type]
                print(f"  {sec_type}: {len(lengths)} sections, total {sum(lengths)} chars, avg {sum(lengths)/len(lengths):.0f}")

        site_structures[site] = {
            "meta": meta,
            "heading_analysis": h_analysis,
            "sections_detected": detected,
            "section_lengths": {k: {"count": len(v), "total": sum(v), "avg": sum(v)/len(v) if v else 0}
                               for k, v in site_sections.items()}
        }

    # Aggregate statistics
    print("\n" + "=" * 70)
    print("AGGREGATE STATISTICS")
    print("=" * 70)

    print("\n--- HEADING LENGTH STATISTICS ---")
    for tag in ["h1", "h2", "h3"]:
        lengths = all_headings[tag]
        if lengths:
            print(f"{tag.upper()}:")
            print(f"  Count: {len(lengths)}")
            print(f"  Min: {min(lengths)} chars")
            print(f"  Max: {max(lengths)} chars")
            print(f"  Avg: {sum(lengths)/len(lengths):.0f} chars")
            print(f"  Median: {sorted(lengths)[len(lengths)//2]} chars")

    print("\n--- SECTION CONTENT LENGTH STATISTICS ---")
    section_stats = {}
    for sec_type in ["hero", "about", "amenities", "payment_plan", "location", "developer", "faq", "floor_plans", "gallery", "contact"]:
        entries = all_sections[sec_type]
        if entries:
            lengths = [e[1] for e in entries]
            stats = {
                "sites_with_section": len(set(e[0] for e in entries)),
                "total_instances": len(entries),
                "min_chars": min(lengths),
                "max_chars": max(lengths),
                "avg_chars": sum(lengths) / len(lengths),
                "median_chars": sorted(lengths)[len(lengths)//2]
            }
            section_stats[sec_type] = stats
            print(f"\n{sec_type.upper()}:")
            print(f"  Sites with this section: {stats['sites_with_section']}/22")
            print(f"  Char range: {stats['min_chars']} - {stats['max_chars']}")
            print(f"  Average: {stats['avg_chars']:.0f} chars")
            print(f"  Median: {stats['median_chars']} chars")

    # Section presence matrix
    print("\n" + "=" * 70)
    print("SECTION PRESENCE MATRIX")
    print("=" * 70)

    section_types = ["hero", "about", "amenities", "payment_plan", "location", "developer", "faq", "floor_plans", "gallery"]
    print(f"\n{'Site':<30} | " + " | ".join(f"{s[:6]:^6}" for s in section_types))
    print("-" * 100)

    for site, structure in site_structures.items():
        detected = structure.get("sections_detected", [])
        # Map detected patterns to our section types
        mapping = {
            "hero": "hero", "about": "about", "amenities": "amenities",
            "payment": "payment_plan", "location": "location",
            "developer": "developer", "faq": "faq", "floor_plans": "floor_plans",
            "gallery": "gallery"
        }
        has_sections = []
        for sec in section_types:
            # Check if any of the detected patterns match
            found = False
            for pattern, sec_name in mapping.items():
                if pattern in detected and sec_name == sec:
                    found = True
                    break
            has_sections.append("Y" if found else "-")

        print(f"{site[:30]:<30} | " + " | ".join(f"{s:^6}" for s in has_sections))

    # Save analysis
    analysis = {
        "heading_statistics": {
            tag: {
                "count": len(lengths),
                "min": min(lengths) if lengths else 0,
                "max": max(lengths) if lengths else 0,
                "avg": sum(lengths)/len(lengths) if lengths else 0,
            }
            for tag, lengths in all_headings.items()
        },
        "section_statistics": section_stats,
        "site_structures": site_structures
    }

    output_path = OUTPUT_DIR / "page_structure_analysis.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"\n\nAnalysis saved to: {output_path}")

    # Recommended character limits
    print("\n" + "=" * 70)
    print("RECOMMENDED CHARACTER LIMITS (based on actual content)")
    print("=" * 70)

    recommendations = {
        "meta_title": "50-60 chars (SEO optimal)",
        "meta_description": "150-160 chars (SEO optimal)",
        "h1": f"{all_headings['h1'] and min(all_headings['h1']) or 20}-{all_headings['h1'] and max(all_headings['h1']) or 80} chars (observed range)",
        "h2": f"30-80 chars (observed avg: {sum(all_headings['h2'])/max(len(all_headings['h2']),1):.0f})",
        "h3": f"20-60 chars (observed avg: {sum(all_headings['h3'])/max(len(all_headings['h3']),1):.0f})",
    }

    for field, limit in recommendations.items():
        print(f"  {field}: {limit}")

    print("\nSection content recommendations:")
    for sec_type, stats in section_stats.items():
        if stats["sites_with_section"] >= 10:  # Common sections
            print(f"  {sec_type}: {int(stats['avg_chars']*0.8)}-{int(stats['avg_chars']*1.2)} chars (based on {stats['avg_chars']:.0f} avg)")

if __name__ == "__main__":
    main()
