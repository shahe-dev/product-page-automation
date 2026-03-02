"""
Ground Truth Helper -- extracts readable floor plan data from PDFs
to assist with manual ground truth creation.

Outputs a review-friendly text file per brochure showing:
- Page-by-page text with floor plan signals
- Detected area values (sqft/sqm)
- Detected unit types and bedroom counts
- Pre-filled JSON template for the floor_plans array

Usage:
    cd backend
    python scripts/gt_helper.py                          # All 29 new brochures
    python scripts/gt_helper.py --key avarra_palace       # Single brochure
    python scripts/gt_helper.py --key avarra_palace --json  # Output JSON template only

Output goes to scripts/gt_review/ (one .txt file per brochure).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BROCHURES_DIR = Path(__file__).resolve().parents[2] / "floor-plan-tool" / "sample brochures 2"
GT_DIR = Path(__file__).resolve().parent.parent / "tests" / "quality" / "ground_truth"
REVIEW_DIR = Path(__file__).resolve().parent / "gt_review"

# Load brochure types
TYPES_PATH = GT_DIR.parent / "brochure_types.json"

# Patterns
RE_DIM_M = re.compile(r"(\d+\.?\d*)\s*m?\s*[xX]\s*(\d+\.?\d*)\s*m?", re.I)
RE_SQFT = re.compile(
    r"(\d[\d,]*\.?\d*)\s*(?:sq\.?\s*ft\.?|sqft|SQ\.?\s*FT\.?)", re.I
)
RE_SQM = re.compile(
    r"(\d[\d,]*\.?\d*)\s*(?:sq\.?\s*m\.?|sqm|SQ\.?\s*M\.?)", re.I
)
RE_BEDROOM = re.compile(
    r"(\d)\s*[-]?\s*(?:bedroom|bed\b|BR\b)|studio", re.I
)
RE_UNIT_TYPE = re.compile(
    r"(?:type|layout|unit)\s+([A-Za-z0-9]+)", re.I
)
RE_SUITE_BALCONY = re.compile(
    r"(suite|internal|balcony|terrace|total|built[- ]?up|gross)\s*[:\s]*"
    r"(\d[\d,]*\.?\d*)\s*(?:sq\.?\s*(?:ft|m)\.?|sqft|sqm)?",
    re.I,
)


def parse_num(s: str) -> float | None:
    try:
        return float(s.replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def analyze_page(text: str, page_num: int) -> dict | None:
    """Extract floor plan signals from a page's text."""
    if not text or len(text.strip()) < 20:
        return None

    result = {"page": page_num, "signals": [], "values": {}}

    # Dimensions
    dims = RE_DIM_M.findall(text)
    if dims:
        result["signals"].append(f"dimensions ({len(dims)} found)")
        result["values"]["sample_dimensions"] = [
            f"{d[0]} x {d[1]}" for d in dims[:5]
        ]

    # Area values
    sqft_vals = RE_SQFT.findall(text)
    sqm_vals = RE_SQM.findall(text)
    if sqft_vals:
        result["signals"].append(f"sqft ({len(sqft_vals)} values)")
        result["values"]["sqft_values"] = [parse_num(v) for v in sqft_vals[:10]]
    if sqm_vals:
        result["signals"].append(f"sqm ({len(sqm_vals)} values)")
        result["values"]["sqm_values"] = [parse_num(v) for v in sqm_vals[:10]]

    # Suite/balcony/total labels
    area_labels = RE_SUITE_BALCONY.findall(text)
    if area_labels:
        result["signals"].append("area_labels")
        result["values"]["area_labels"] = [
            {"label": a[0], "value": parse_num(a[1])} for a in area_labels
        ]

    # Bedroom count
    beds = RE_BEDROOM.findall(text)
    if beds:
        result["signals"].append(f"bedrooms: {beds}")

    # Unit type
    unit_types = RE_UNIT_TYPE.findall(text)
    if unit_types:
        result["signals"].append(f"unit_types: {unit_types[:5]}")

    # Room labels
    room_labels = re.findall(
        r"\b(master\s*bedroom|living|kitchen|dining|bathroom|powder|"
        r"balcony|terrace|maid|laundry|dressing|walk[- ]in|utility|"
        r"entrance|corridor|store|study|office|guest|family)\b",
        text,
        re.I,
    )
    if room_labels:
        unique_rooms = sorted(set(r.lower() for r in room_labels))
        result["signals"].append(f"rooms: {unique_rooms}")

    if not result["signals"]:
        return None

    # Include truncated text for context
    result["text_preview"] = text[:500]

    return result


def generate_review(key: str, brochure_file: str, brochure_type: dict) -> str:
    """Generate a review document for manual ground truth creation."""
    import fitz

    pdf_path = BROCHURES_DIR / brochure_file
    if not pdf_path.exists():
        return f"ERROR: PDF not found: {pdf_path}"

    pdf_bytes = pdf_path.read_bytes()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    size_mb = len(pdf_bytes) / (1024 * 1024)

    lines = []
    lines.append("=" * 70)
    lines.append(f"  GROUND TRUTH REVIEW: {key}")
    lines.append("=" * 70)
    lines.append(f"  File: {brochure_file}")
    lines.append(f"  Size: {size_mb:.1f} MB, {len(doc)} pages")
    lines.append(f"  Format: {brochure_type.get('primary_type', '?')} "
                 f"(text quality: {brochure_type.get('text_quality', '?')})")
    lines.append(f"  Notes: {brochure_type.get('notes', '')}")
    lines.append("=" * 70)
    lines.append("")
    lines.append("INSTRUCTIONS:")
    lines.append("  1. Open the PDF in a viewer")
    lines.append("  2. For each floor plan page, verify/fill in the data below")
    lines.append("  3. Copy the JSON template at the bottom into the ground truth file")
    lines.append("")

    # Analyze all pages
    fp_pages = []
    all_sqft = []
    all_unit_types = set()
    all_bedrooms = set()

    for i in range(len(doc)):
        text = doc[i].get_text("text").strip()
        analysis = analyze_page(text, i + 1)
        if analysis:
            fp_pages.append(analysis)
            for v in analysis["values"].get("sqft_values", []):
                if v:
                    all_sqft.append(v)
            for ut in RE_UNIT_TYPE.findall(text):
                all_unit_types.add(ut.upper())
            for b in RE_BEDROOM.findall(text):
                if b:
                    all_bedrooms.add(b)

    doc.close()

    # Print page analysis
    lines.append(f"FLOOR PLAN PAGES DETECTED: {len(fp_pages)}")
    lines.append("-" * 70)

    for page in fp_pages:
        lines.append(f"\n  Page {page['page']}: {', '.join(page['signals'])}")
        for k, v in page["values"].items():
            lines.append(f"    {k}: {v}")
        # Show first 300 chars of text
        preview = page.get("text_preview", "")[:300].replace("\n", " | ")
        lines.append(f"    text: {preview}")

    # Summary
    lines.append("\n" + "-" * 70)
    lines.append("SUMMARY")
    lines.append("-" * 70)
    lines.append(f"  All sqft values found: {sorted(set(all_sqft))}")
    lines.append(f"  Unit types found: {sorted(all_unit_types)}")
    lines.append(f"  Bedroom counts found: {sorted(all_bedrooms)}")

    # Generate JSON template
    lines.append("\n" + "-" * 70)
    lines.append("JSON TEMPLATE (copy into ground truth file)")
    lines.append("-" * 70)

    # Try to infer floor plans from text data
    inferred_plans = []

    # Group by unit type from area labels
    for page in fp_pages:
        area_labels = page["values"].get("area_labels", [])
        sqft_vals = page["values"].get("sqft_values", [])
        beds_found = RE_BEDROOM.findall(page.get("text_preview", ""))
        types_found = RE_UNIT_TYPE.findall(page.get("text_preview", ""))

        if sqft_vals or area_labels:
            plan = {
                "unit_type": None,
                "bedrooms": None,
                "bathrooms": None,
                "total_sqft": None,
                "suite_sqft": None,
                "balcony_sqft": None,
                "_page": page["page"],
                "_needs_review": True,
            }

            # Infer unit type
            if types_found:
                plan["unit_type"] = types_found[0]

            # Infer bedrooms
            if beds_found:
                try:
                    plan["bedrooms"] = int(beds_found[0])
                except (ValueError, TypeError):
                    pass

            # Infer areas from labels
            for al in area_labels:
                label = al["label"].lower()
                val = al["value"]
                if "suite" in label or "internal" in label:
                    plan["suite_sqft"] = val
                elif "balcony" in label or "terrace" in label:
                    plan["balcony_sqft"] = val
                elif "total" in label or "gross" in label or "built" in label:
                    plan["total_sqft"] = val

            # If no labeled areas, use raw sqft values
            if plan["total_sqft"] is None and sqft_vals:
                # Largest value is likely total
                plan["total_sqft"] = max(sqft_vals)

            inferred_plans.append(plan)

    template = {
        "brochure": brochure_file,
        "last_verified": "2026-02-XX",
        "notes": "FILL IN: describe what you found",
        "table_specs": [],
        "table_spec_count": 0,
        "text_assertions": {
            "pages_with_floor_plan_text": [p["page"] for p in fp_pages],
            "expected_unit_types_in_text": sorted(all_unit_types),
            "expected_area_labels_present": bool(all_sqft),
        },
        "floor_plans": [
            {k: v for k, v in p.items() if not k.startswith("_")}
            for p in inferred_plans
        ],
        "total_unique_plans": len(inferred_plans),
        "total_unique_plans_tolerance": 2,
        "tolerances": {
            "sqft_pct": 5.0,
            "balcony_sqft_pct": 10.0,
            "bedrooms_exact": True,
            "bathrooms_exact": True,
        },
    }

    lines.append(json.dumps(template, indent=2, default=str))
    lines.append("")
    lines.append(
        "NOTE: The floor_plans above are INFERRED from text only. "
        "You MUST verify against the actual PDF. "
        "Plans with no text data (RD type) will be empty -- fill in manually."
    )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Ground Truth Helper")
    parser.add_argument("--key", help="Process single brochure by key")
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON template only (no review text)",
    )
    args = parser.parse_args()

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    # Load brochure types
    brochure_types = {}
    if TYPES_PATH.exists():
        raw = json.loads(TYPES_PATH.read_text(encoding="utf-8"))
        brochure_types = {
            k: v for k, v in raw.items() if not k.startswith("_")
        }

    # Load conftest brochure map
    from tests.quality.conftest import BROCHURE_FILES

    # Determine which to process
    if args.key:
        keys = [args.key]
    else:
        # All keys that have AUTO-GENERATED drafts
        keys = []
        for gt_file in sorted(GT_DIR.glob("*.json")):
            gt = json.loads(gt_file.read_text(encoding="utf-8"))
            if "AUTO-GENERATED" in gt.get("notes", ""):
                keys.append(gt_file.stem)

    for key in keys:
        if key not in BROCHURE_FILES:
            print(f"SKIP {key}: not in BROCHURE_FILES")
            continue

        bt = brochure_types.get(key, {})
        review = generate_review(key, BROCHURE_FILES[key], bt)

        out_path = REVIEW_DIR / f"{key}.txt"
        out_path.write_text(review, encoding="utf-8")
        print(f"  {key}: saved to {out_path}")

    print(f"\nDone. Review files in: {REVIEW_DIR}")
    print("Open each .txt file, compare against the PDF, and update the JSON in ground_truth/.")


if __name__ == "__main__":
    main()
