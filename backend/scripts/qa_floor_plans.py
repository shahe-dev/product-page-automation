"""
Floor Plan Extraction QA Script

Runs floor plan extraction on a single PDF brochure and produces a
detailed report. Saves floor plan images to disk for visual inspection.

Usage:
    # Table + text only (no API calls, fast)
    python scripts/qa_floor_plans.py "../sample brochures 2/NOVAYAS Brochure.pdf" --no-api

    # Full extraction (API calls, slow -- caches all Vision responses)
    python scripts/qa_floor_plans.py "../sample brochures 2/NOVAYAS Brochure.pdf"

    # Replay: re-run parsing with cached Vision responses (FREE, instant)
    # Uses the cache dir from a previous full run.
    python scripts/qa_floor_plans.py "../sample brochures 2/NOVAYAS Brochure.pdf" \
        --replay scripts/qa_output/novayas_brochure_20260212T120000

    # Generate ground truth draft
    python scripts/qa_floor_plans.py "../sample brochures 2/NOVAYAS Brochure.pdf" --generate-ground-truth

    # Compare against existing ground truth
    python scripts/qa_floor_plans.py "../sample brochures 2/NOVAYAS Brochure.pdf" \
        --ground-truth tests/quality/ground_truth/novayas.json

Run from backend/ directory (needs .env for settings).
"""
import argparse
import asyncio
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("qa_floor_plans")


def _slugify(text: str) -> str:
    """Convert text to filesystem-safe slug."""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:60]


def print_header(brochure_name: str, size_mb: float, page_count: int):
    print("\n" + "=" * 60)
    print("  FLOOR PLAN QA REPORT")
    print("=" * 60)
    print(f"  Brochure : {brochure_name}")
    print(f"  Size     : {size_mb:.1f} MB")
    print(f"  Pages    : {page_count}")
    print("=" * 60)


def print_table_report(table_result):
    specs = table_result.floor_plan_specs
    print("\n--- TABLE EXTRACTION (pdfplumber) ---")
    print(f"  Floor plan tables found: {len(specs)} specs")
    if table_result.errors:
        for e in table_result.errors:
            print(f"  ERROR: {e}")
    if not specs:
        print("  (no floor plan specs found in tables)")
        return
    # Header
    print(f"  {'Unit Type':<35} {'Beds':>4} {'Total':>10} {'Suite':>10} {'Balcony':>10}")
    print(f"  {'-'*35} {'-'*4} {'-'*10} {'-'*10} {'-'*10}")
    for s in specs:
        ut = (s.get("unit_type") or "?")[:35]
        beds = s.get("bedrooms", "?")
        total = f"{s['total_sqft']:>10.2f}" if s.get("total_sqft") else f"{'--':>10}"
        suite = f"{s['suite_sqft']:>10.2f}" if s.get("suite_sqft") else f"{'--':>10}"
        balcony = f"{s['balcony_sqft']:>10.2f}" if s.get("balcony_sqft") else f"{'--':>10}"
        print(f"  {ut:<35} {str(beds):>4} {total} {suite} {balcony}")


def print_text_report(text_results: list[dict]):
    print("\n--- TEXT REGEX EXTRACTION ---")
    if not text_results:
        print("  (no floor plan data found via text regex)")
        return
    for r in text_results:
        fields = []
        if r.get("unit_type"):
            fields.append(f"unit_type={r['unit_type']}")
        if r.get("total_sqft"):
            fields.append(f"total={r['total_sqft']:.2f}")
        if r.get("suite_sqft"):
            fields.append(f"suite={r['suite_sqft']:.2f}")
        if r.get("balcony_sqft"):
            fields.append(f"balcony={r['balcony_sqft']:.2f}")
        if r.get("bathrooms"):
            fields.append(f"baths={r['bathrooms']}")
        if r.get("bedrooms"):
            fields.append(f"beds={r['bedrooms']}")
        print(f"  Page {r['page']}: {', '.join(fields)}")


def print_classification_report(classification):
    print("\n--- IMAGE CLASSIFICATION ---")
    print(f"  Total images: {classification.total_input}")
    print(f"  Retained: {classification.total_retained}")
    print(f"  Duplicates: {classification.total_duplicates}")
    cats = classification.category_counts
    if cats:
        parts = [f"{k}: {v}" for k, v in sorted(cats.items()) if v > 0]
        print(f"  Categories: {', '.join(parts)}")


def print_classification_report_from_cache(cls_data: dict):
    print("\n--- IMAGE CLASSIFICATION (cached) ---")
    print(f"  Total images: {cls_data.get('total_images', '?')}")
    print(f"  Retained: {cls_data.get('retained', '?')}")
    print(f"  Duplicates: {cls_data.get('duplicates', '?')}")
    cats = cls_data.get("category_counts", {})
    if cats:
        parts = [f"{k}: {v}" for k, v in sorted(cats.items()) if v > 0]
        print(f"  Categories: {', '.join(parts)}")


def print_extraction_report(merged_plans):
    print("\n--- EXTRACTION RESULTS (Vision OCR + table merge) ---")
    print(f"  Total unique floor plans: {len(merged_plans)}")
    if not merged_plans:
        print("  (none)")
        return
    print(
        f"  {'#':>3} {'Unit Type':<30} {'Beds':>4} {'Total':>10} "
        f"{'Suite':>10} {'Balcony':>10} {'Source':>12} {'Conf':>5}"
    )
    print(
        f"  {'-'*3} {'-'*30} {'-'*4} {'-'*10} "
        f"{'-'*10} {'-'*10} {'-'*12} {'-'*5}"
    )
    for i, fp in enumerate(merged_plans):
        ut = (fp.unit_type or "?")[:30]
        beds = fp.bedrooms if fp.bedrooms is not None else "?"
        total = f"{fp.total_sqft:>10.2f}" if fp.total_sqft else f"{'--':>10}"
        suite = f"{fp.suite_sqft:>10.2f}" if fp.suite_sqft else f"{'--':>10}"
        balcony = f"{fp.balcony_sqft:>10.2f}" if fp.balcony_sqft else f"{'--':>10}"
        source = (fp.total_sqft_source or "?")[:12]
        conf = f"{fp.confidence:.2f}" if fp.confidence else "?"
        print(f"  {i+1:>3} {ut:<30} {str(beds):>4} {total} {suite} {balcony} {source:>12} {conf:>5}")

    # Room dimensions summary
    has_dims = sum(1 for fp in merged_plans if fp.room_dimensions)
    print(f"\n  Room dimensions: {has_dims}/{len(merged_plans)} plans have dimensions")

    # Features summary
    has_feats = sum(1 for fp in merged_plans if fp.features)
    print(f"  Features: {has_feats}/{len(merged_plans)} plans have features")


def build_ground_truth_draft(report: dict) -> dict:
    """Build a ground truth draft from extraction results."""
    gt = {
        "brochure": report["brochure"] + ".pdf",
        "last_verified": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "notes": "AUTO-GENERATED DRAFT -- review and correct before use",
    }

    # Table specs
    table_specs = report.get("table_extraction", {}).get("specs", [])
    gt["table_specs"] = table_specs
    gt["table_spec_count"] = len(table_specs)

    # Text assertions
    text_results = report.get("text_extraction", [])
    fp_pages = sorted(set(r["page"] for r in text_results))
    unit_types_in_text = sorted(set(
        r["unit_type"] for r in text_results if r.get("unit_type")
    ))
    gt["text_assertions"] = {
        "pages_with_floor_plan_text": fp_pages,
        "expected_unit_types_in_text": unit_types_in_text,
        "expected_area_labels_present": any(
            r.get("suite_sqft") or r.get("total_sqft") for r in text_results
        ),
    }

    # Floor plans (from full extraction)
    fps = report.get("floor_plans", [])
    gt["floor_plans"] = []
    for fp in fps:
        gt["floor_plans"].append({
            "unit_type": fp.get("unit_type"),
            "bedrooms": fp.get("bedrooms"),
            "bathrooms": fp.get("bathrooms"),
            "total_sqft": fp.get("total_sqft"),
            "suite_sqft": fp.get("suite_sqft"),
            "balcony_sqft": fp.get("balcony_sqft"),
            "builtup_sqft": fp.get("builtup_sqft"),
            "has_room_dimensions": bool(fp.get("room_dimensions")),
            "has_image": bool(fp.get("image_file")),
            "min_confidence": 0.7,
        })
    gt["total_unique_plans"] = len(fps)
    gt["total_unique_plans_tolerance"] = 1

    # Classification
    cls = report.get("classification", {})
    fp_image_count = report.get("floor_plan_image_count", 0)
    gt["classification"] = {
        "min_floor_plan_images": max(1, fp_image_count - 2),
        "total_images_classified": cls.get("total_images", 0),
    }

    # Tolerances
    gt["tolerances"] = {
        "sqft_pct": 2.0,
        "balcony_sqft_pct": 5.0,
        "bedrooms_exact": True,
        "bathrooms_exact": True,
    }

    return gt


def score_against_ground_truth(report: dict, gt: dict) -> dict:
    """Compare extraction results against ground truth, return structured metrics."""
    from app.services.floor_plan_extractor import FloorPlanExtractor

    metrics = {
        "plan_count_expected": gt.get("total_unique_plans", 0),
        "plan_count_actual": len(report.get("floor_plans", [])),
        "plan_count_pass": False,
        "table_spec_expected": gt.get("table_spec_count", 0),
        "table_spec_actual": report.get("table_extraction", {}).get("floor_plan_spec_count", 0),
        "unit_type_matched": 0,
        "unit_type_missing": 0,
        "area_checks_pass": 0,
        "area_checks_fail": 0,
        "area_checks_null": 0,
        "bedroom_checks_pass": 0,
        "bedroom_checks_fail": 0,
        "false_data_count": 0,
        "total_fields_checked": 0,
        "details": [],
    }

    tolerance = gt.get("total_unique_plans_tolerance", 1)
    metrics["plan_count_pass"] = (
        abs(metrics["plan_count_actual"] - metrics["plan_count_expected"]) <= tolerance
    )

    gt_plans = gt.get("floor_plans", [])
    actual_plans = report.get("floor_plans", [])
    tol_pct = gt.get("tolerances", {}).get("sqft_pct", 2.0) / 100

    for gt_fp in gt_plans:
        gt_key = FloorPlanExtractor._normalize_unit_key(gt_fp.get("unit_type", ""))
        matched = None
        for ap in actual_plans:
            if FloorPlanExtractor._normalize_unit_key(ap.get("unit_type", "")) == gt_key:
                matched = ap
                break
        if matched is None:
            metrics["unit_type_missing"] += 1
            metrics["details"].append({"unit_type": gt_fp["unit_type"], "status": "MISSING"})
            continue

        metrics["unit_type_matched"] += 1

        for field in ["total_sqft", "suite_sqft", "balcony_sqft"]:
            exp_val = gt_fp.get(field)
            act_val = matched.get(field)
            if exp_val is None:
                continue
            metrics["total_fields_checked"] += 1
            if act_val is None:
                metrics["area_checks_null"] += 1
            else:
                diff_pct = abs(act_val - exp_val) / exp_val if exp_val else 0
                if diff_pct < tol_pct:
                    metrics["area_checks_pass"] += 1
                else:
                    metrics["area_checks_fail"] += 1
                    metrics["false_data_count"] += 1
                    metrics["details"].append({
                        "unit_type": gt_fp["unit_type"],
                        "field": field,
                        "expected": exp_val,
                        "actual": act_val,
                        "diff_pct": round(diff_pct * 100, 1),
                    })

        if gt_fp.get("bedrooms") is not None and matched.get("bedrooms") is not None:
            if matched["bedrooms"] == gt_fp["bedrooms"]:
                metrics["bedroom_checks_pass"] += 1
            else:
                metrics["bedroom_checks_fail"] += 1
                metrics["false_data_count"] += 1

    # Computed rates
    total_checked = metrics["total_fields_checked"]
    if total_checked > 0:
        metrics["area_accuracy_pct"] = round(
            metrics["area_checks_pass"] / total_checked * 100, 1
        )
        metrics["false_data_rate_pct"] = round(
            metrics["false_data_count"] / total_checked * 100, 1
        )
        metrics["null_rate_pct"] = round(
            metrics["area_checks_null"] / total_checked * 100, 1
        )
    else:
        metrics["area_accuracy_pct"] = 0.0
        metrics["false_data_rate_pct"] = 0.0
        metrics["null_rate_pct"] = 0.0

    return metrics


def compare_against_ground_truth(report: dict, gt_path: str):
    """Compare extraction results against ground truth and print diff."""
    gt = json.loads(Path(gt_path).read_text(encoding="utf-8"))
    metrics = score_against_ground_truth(report, gt)

    print(f"\n--- COMPARISON vs GROUND TRUTH ({Path(gt_path).name}) ---")

    status = "PASS" if metrics["plan_count_pass"] else "FAIL"
    print(
        f"  [{status}] Plan count: expected {metrics['plan_count_expected']}, "
        f"got {metrics['plan_count_actual']}"
    )

    status = "PASS" if metrics["table_spec_expected"] == metrics["table_spec_actual"] else "FAIL"
    print(
        f"  [{status}] Table specs: expected {metrics['table_spec_expected']}, "
        f"got {metrics['table_spec_actual']}"
    )

    print(
        f"  Unit types: {metrics['unit_type_matched']} matched, "
        f"{metrics['unit_type_missing']} missing"
    )
    print(
        f"  Area accuracy: {metrics['area_accuracy_pct']}% "
        f"({metrics['area_checks_pass']}/{metrics['total_fields_checked']} pass)"
    )
    print(f"  False data rate: {metrics['false_data_rate_pct']}%")
    print(f"  Null rate: {metrics['null_rate_pct']}%")

    for d in metrics["details"]:
        if d.get("status") == "MISSING":
            print(f"  [FAIL] Missing: {d['unit_type']}")
        elif "field" in d:
            print(
                f"  [FAIL] {d['unit_type']} {d['field']}: "
                f"expected {d['expected']}, got {d['actual']} "
                f"(diff {d['diff_pct']}%)"
            )


def save_report(report: dict, output_dir: Path):
    """Save report JSON and print summary."""
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\n  Report saved to: {report_path}")


# ------------------------------------------------------------------
# Cache helpers: save/load intermediate state for --replay
# ------------------------------------------------------------------
def save_cache(cache_dir: Path, page_text_map: dict, classification: dict,
               fp_image_entries: list[dict]):
    """Save intermediate data so --replay can skip API calls."""
    cache_dir.mkdir(parents=True, exist_ok=True)

    # page_text_map: {page_num_str: text}
    (cache_dir / "page_text_map.json").write_text(
        json.dumps(page_text_map, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # classification summary
    (cache_dir / "classification.json").write_text(
        json.dumps(classification, indent=2), encoding="utf-8"
    )

    # floor plan images: [{page: N, filename: "fp_NNN.png"}]
    img_dir = cache_dir / "fp_images"
    img_dir.mkdir(exist_ok=True)
    manifest = []
    for entry in fp_image_entries:
        fname = f"fp_{entry['page']:03d}.png"
        (img_dir / fname).write_bytes(entry["image_bytes"])
        manifest.append({"page": entry["page"], "filename": fname})

    (cache_dir / "fp_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    logger.info("Cache saved to %s (%d floor plan images)", cache_dir, len(manifest))


def load_cache(cache_dir: Path):
    """Load cached intermediate data for replay."""
    ptm_raw = json.loads(
        (cache_dir / "page_text_map.json").read_text(encoding="utf-8")
    )
    # JSON keys are strings, convert back to int
    page_text_map = {int(k): v for k, v in ptm_raw.items()}

    classification = json.loads(
        (cache_dir / "classification.json").read_text(encoding="utf-8")
    )

    manifest = json.loads(
        (cache_dir / "fp_manifest.json").read_text(encoding="utf-8")
    )

    img_dir = cache_dir / "fp_images"
    fp_entries = []
    for entry in manifest:
        img_bytes = (img_dir / entry["filename"]).read_bytes()
        fp_entries.append({"page": entry["page"], "image_bytes": img_bytes})

    return page_text_map, classification, fp_entries


async def run_qa(pdf_path: str, output_dir: Path, no_api: bool,
                 generate_gt: bool, gt_path: str | None,
                 replay_dir: str | None):
    pdf_bytes = Path(pdf_path).read_bytes()
    brochure_name = Path(pdf_path).stem
    size_mb = len(pdf_bytes) / (1024 * 1024)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out = output_dir / f"{_slugify(brochure_name)}_{timestamp}"
    out.mkdir(parents=True, exist_ok=True)

    # Vision cache lives in a stable location per brochure (not per run)
    # so subsequent runs + replays all share the same cache.
    vision_cache = output_dir / f"{_slugify(brochure_name)}_vision_cache"

    report = {
        "brochure": brochure_name,
        "timestamp": timestamp,
        "size_mb": round(size_mb, 1),
    }

    # --- Phase 1: Text extraction via PyMuPDF (no API) ---
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_text_map = {}
    for i in range(len(doc)):
        t = doc[i].get_text("text").strip()
        if t:
            page_text_map[i + 1] = t
    page_count = len(doc)
    doc.close()
    report["page_count"] = page_count

    print_header(brochure_name, size_mb, page_count)

    # --- Phase 2: Table extraction (pdfplumber, no API) ---
    from app.services.table_extractor import TableExtractor

    te = TableExtractor()
    table_result = te.extract_tables(pdf_bytes)
    report["table_extraction"] = {
        "floor_plan_spec_count": len(table_result.floor_plan_specs),
        "specs": table_result.floor_plan_specs,
        "errors": table_result.errors,
    }
    print_table_report(table_result)

    # --- Phase 3: Text regex extraction (no API) ---
    from app.services.floor_plan_extractor import FloorPlanExtractor

    extractor = FloorPlanExtractor(vision_cache_dir=vision_cache)
    text_results = []
    for page_num in sorted(page_text_map.keys()):
        text_data = extractor._extract_from_text(page_text_map, page_num)
        if text_data.get("unit_type") or text_data.get("total_sqft"):
            text_results.append({"page": page_num, **text_data})
    report["text_extraction"] = text_results
    print_text_report(text_results)

    if no_api:
        save_report(report, out)
        if generate_gt:
            gt_draft = build_ground_truth_draft(report)
            gt_path_out = out / "ground_truth_draft.json"
            gt_path_out.write_text(
                json.dumps(gt_draft, indent=2, default=str), encoding="utf-8"
            )
            print(f"  Ground truth draft saved to: {gt_path_out}")
            print("  NOTE: --no-api mode. Draft has table/text data only, no Vision extraction.")
        if gt_path:
            compare_against_ground_truth(report, gt_path)
        return

    # ------------------------------------------------------------------
    # REPLAY MODE: load cached classification + floor plan images
    # ------------------------------------------------------------------
    if replay_dir:
        replay_path = Path(replay_dir)
        cache_subdir = replay_path / "cache"
        if not cache_subdir.exists():
            print(f"ERROR: No cache dir found at {cache_subdir}")
            print("  Run a full extraction first (without --replay) to build the cache.")
            sys.exit(1)

        print(f"\n  REPLAY MODE: loading from {cache_subdir}")
        cached_ptm, cls_data, fp_entries = load_cache(cache_subdir)

        # Use cached page_text_map (it's the same PDF, but just in case)
        # Override with fresh text extraction since we always have the PDF
        report["classification"] = cls_data
        print_classification_report_from_cache(cls_data)

        # Reconstruct ExtractedImage objects from cached image bytes
        from app.utils.pdf_helpers import ExtractedImage, ImageMetadata

        fp_images = []
        for entry in fp_entries:
            img = ExtractedImage(
                image_bytes=entry["image_bytes"],
                metadata=ImageMetadata(
                    page_number=entry["page"],
                    source="cached",
                    dpi=300,
                ),
            )
            fp_images.append(img)

        report["floor_plan_image_count"] = len(fp_images)
        print(f"  Floor plan images (cached): {len(fp_images)}")

    # ------------------------------------------------------------------
    # FULL MODE: extract images + classify (expensive)
    # ------------------------------------------------------------------
    else:
        from app.models.enums import ImageCategory
        from app.services.image_classifier import ImageClassifier
        from app.services.pdf_processor import PDFProcessor
        from app.utils.image_validation import validate_image_bytes

        print("\n  Processing PDF (extracting images + rendering pages)...")
        processor = PDFProcessor()
        extraction = await processor.extract_all(pdf_bytes)

        print("  Classifying images via Vision API...")
        classifier = ImageClassifier()
        classification = await classifier.classify_extraction(extraction)
        cls_data = {
            "total_images": classification.total_input,
            "retained": classification.total_retained,
            "duplicates": classification.total_duplicates,
            "category_counts": classification.category_counts,
        }
        report["classification"] = cls_data
        print_classification_report(classification)

        # Preserve floor plan images (replicates job_manager lines 1788-1820)
        fp_images = []
        for image, cls_result in classification.classified_images:
            if cls_result.category == ImageCategory.FLOOR_PLAN:
                eff = image.image_bytes or image.llm_optimized_bytes
                if eff and validate_image_bytes(eff):
                    fp_images.append(image)

        if not fp_images:
            fp_pages = {
                img.metadata.page_number
                for img, cr in classification.classified_images
                if cr.category == ImageCategory.FLOOR_PLAN
            }
            if fp_pages and hasattr(extraction, "page_renders"):
                for render in extraction.page_renders:
                    if render.metadata.page_number in fp_pages:
                        eff = render.image_bytes or render.llm_optimized_bytes
                        if eff and validate_image_bytes(eff):
                            fp_images.append(render)
                if fp_images:
                    print(f"  Floor plan fallback: using {len(fp_images)} page renders")

        report["floor_plan_image_count"] = len(fp_images)
        print(f"  Floor plan images: {len(fp_images)}")

        # Save cache for future --replay runs
        cache_subdir = out / "cache"
        fp_cache_entries = []
        for img in fp_images:
            eff = img.image_bytes or img.llm_optimized_bytes or b""
            fp_cache_entries.append({
                "page": img.metadata.page_number,
                "image_bytes": eff,
            })
        save_cache(cache_subdir, page_text_map, cls_data, fp_cache_entries)

    # --- Phase 5: Floor plan Vision OCR extraction ---
    # In replay mode, all Vision calls hit the cache (no API cost).
    # In full mode, responses are cached for future replays.
    print("  Extracting floor plan data via Vision OCR...")
    fp_result = await extractor.extract_floor_plans(fp_images, page_text_map)

    # --- Phase 6: Merge with table data ---
    if table_result.floor_plan_specs:
        merged = extractor.merge_with_table_data(
            fp_result.floor_plans, table_result.floor_plan_specs
        )
        print(f"  Merged {len(fp_result.floor_plans)} Vision plans with {len(table_result.floor_plan_specs)} table specs")
    else:
        merged = fp_result.floor_plans

    # Save floor plan images
    img_dir = out / "floor_plans"
    img_dir.mkdir(exist_ok=True)
    report["floor_plans"] = []
    for i, fp in enumerate(merged):
        fname = None
        if fp.image_bytes:
            fname = f"{i+1:02d}_{_slugify(fp.unit_type or 'unknown')}.png"
            (img_dir / fname).write_bytes(fp.image_bytes)
        report["floor_plans"].append({
            "unit_type": fp.unit_type,
            "bedrooms": fp.bedrooms,
            "bathrooms": fp.bathrooms,
            "total_sqft": fp.total_sqft,
            "total_sqft_source": fp.total_sqft_source,
            "suite_sqft": fp.suite_sqft,
            "suite_sqft_source": fp.suite_sqft_source,
            "balcony_sqft": fp.balcony_sqft,
            "balcony_sqft_source": fp.balcony_sqft_source,
            "builtup_sqft": fp.builtup_sqft,
            "builtup_sqft_source": fp.builtup_sqft_source,
            "room_dimensions": fp.room_dimensions,
            "features": fp.features,
            "confidence": fp.confidence,
            "is_duplicate": fp.is_duplicate,
            "image_file": fname,
        })

    report["extraction_summary"] = {
        "total_input": fp_result.total_input,
        "total_extracted": len(merged),
        "total_duplicates": fp_result.total_duplicates,
        "errors": fp_result.errors,
    }
    print_extraction_report(merged)

    save_report(report, out)

    if generate_gt:
        gt_draft = build_ground_truth_draft(report)
        gt_path_out = out / "ground_truth_draft.json"
        gt_path_out.write_text(
            json.dumps(gt_draft, indent=2, default=str), encoding="utf-8"
        )
        print(f"\n  Ground truth draft saved to: {gt_path_out}")
        print("  IMPORTANT: Review and correct this file against the actual PDF before using as ground truth.")

    if gt_path:
        compare_against_ground_truth(report, gt_path)


async def run_batch(output_dir: Path, no_api: bool):
    """Run QA on all brochures that have ground truth files. Print scorecard."""
    gt_dir = Path(__file__).resolve().parent.parent / "tests" / "quality" / "ground_truth"
    brochures_dir = Path(__file__).resolve().parents[2] / "floor-plan-tool" / "sample brochures 2"

    if not gt_dir.exists():
        print(f"ERROR: Ground truth directory not found: {gt_dir}")
        sys.exit(1)

    # Load brochure types for format classification display
    types_path = gt_dir.parent / "brochure_types.json"
    brochure_types = {}
    if types_path.exists():
        brochure_types = json.loads(types_path.read_text(encoding="utf-8"))

    gt_files = sorted(gt_dir.glob("*.json"))
    if not gt_files:
        print("ERROR: No ground truth JSON files found.")
        sys.exit(1)

    print(f"\n{'='*100}")
    print("  BATCH SCORECARD")
    print(f"{'='*100}")
    print(f"  Ground truth files: {len(gt_files)}")
    print(f"  Mode: {'no-api (tables+text only)' if no_api else 'full (with Vision API)'}")
    print(f"{'='*100}\n")

    all_metrics = {}
    errors = {}

    for gt_file in gt_files:
        key = gt_file.stem
        gt = json.loads(gt_file.read_text(encoding="utf-8"))
        brochure_filename = gt.get("brochure", "")
        if not brochure_filename:
            errors[key] = "No 'brochure' field in ground truth JSON"
            continue

        pdf_path = brochures_dir / brochure_filename
        if not pdf_path.exists():
            errors[key] = f"PDF not found: {pdf_path.name}"
            continue

        # Check for existing vision cache (for replay)
        vision_cache = output_dir / f"{_slugify(pdf_path.stem)}_vision_cache"

        # Check for any existing run dir with cache (for replay)
        replay_dir = None
        if not no_api:
            # Find most recent run dir with cache for this brochure
            slug = _slugify(pdf_path.stem)
            candidates = sorted(
                output_dir.glob(f"{slug}_*/cache"),
                key=lambda p: p.parent.name,
                reverse=True,
            )
            if candidates:
                replay_dir = str(candidates[0].parent)

        print(f"  Processing: {key} ({brochure_filename})...", end=" ", flush=True)

        try:
            # Run the QA extraction (suppress normal output)
            import io
            import contextlib

            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                await run_qa(
                    str(pdf_path),
                    output_dir,
                    no_api=no_api,
                    generate_gt=False,
                    gt_path=None,
                    replay_dir=replay_dir,
                )

            # Find the most recent report for this brochure
            slug = _slugify(pdf_path.stem)
            report_dirs = sorted(
                output_dir.glob(f"{slug}_*/report.json"),
                key=lambda p: p.parent.name,
                reverse=True,
            )
            if not report_dirs:
                errors[key] = "No report.json generated"
                print("ERROR (no report)")
                continue

            report = json.loads(report_dirs[0].read_text(encoding="utf-8"))
            metrics = score_against_ground_truth(report, gt)
            all_metrics[key] = metrics
            status = "OK" if metrics["plan_count_pass"] else "FAIL"
            print(
                f"{status} (plans: {metrics['plan_count_actual']}/{metrics['plan_count_expected']}, "
                f"area: {metrics['area_accuracy_pct']}%)"
            )

        except Exception as e:
            errors[key] = str(e)
            print(f"ERROR ({e})")

    # Print scorecard
    print(f"\n{'='*100}")
    print("  SCORECARD SUMMARY")
    print(f"{'='*100}")
    print(
        f"  {'Key':<25} {'Type':>4} {'Plans':>10} {'UT Match':>10} "
        f"{'Area Acc':>10} {'False %':>10} {'Null %':>10}"
    )
    print(f"  {'-'*25} {'-'*4} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

    total_plans_expected = 0
    total_plans_actual = 0
    total_area_pass = 0
    total_area_fail = 0
    total_area_null = 0
    total_fields = 0

    for key in sorted(all_metrics.keys()):
        m = all_metrics[key]
        bt = brochure_types.get(key, {})
        fmt = bt.get("primary_type", "?")
        plans = f"{m['plan_count_actual']}/{m['plan_count_expected']}"
        ut = f"{m['unit_type_matched']}/{m['unit_type_matched'] + m['unit_type_missing']}"
        area = f"{m['area_accuracy_pct']}%"
        false_d = f"{m['false_data_rate_pct']}%"
        null_r = f"{m['null_rate_pct']}%"
        print(f"  {key:<25} {fmt:>4} {plans:>10} {ut:>10} {area:>10} {false_d:>10} {null_r:>10}")

        total_plans_expected += m["plan_count_expected"]
        total_plans_actual += m["plan_count_actual"]
        total_area_pass += m["area_checks_pass"]
        total_area_fail += m["area_checks_fail"]
        total_area_null += m["area_checks_null"]
        total_fields += m["total_fields_checked"]

    # Totals row
    print(f"  {'-'*25} {'-'*4} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    agg_area = round(total_area_pass / total_fields * 100, 1) if total_fields else 0
    agg_false = round(total_area_fail / total_fields * 100, 1) if total_fields else 0
    agg_null = round(total_area_null / total_fields * 100, 1) if total_fields else 0
    plans_agg = f"{total_plans_actual}/{total_plans_expected}"
    print(
        f"  {'TOTAL':<25} {'':>4} {plans_agg:>10} {'':>10} "
        f"{agg_area}%{'':<5} {agg_false}%{'':<5} {agg_null}%"
    )

    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for key, err in sorted(errors.items()):
            print(f"    {key}: {err}")

    # Save scorecard as JSON
    scorecard = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "no-api" if no_api else "full",
        "brochure_count": len(all_metrics),
        "errors": errors,
        "aggregate": {
            "plans_expected": total_plans_expected,
            "plans_actual": total_plans_actual,
            "area_accuracy_pct": agg_area,
            "false_data_rate_pct": agg_false,
            "null_rate_pct": agg_null,
            "total_fields_checked": total_fields,
        },
        "per_brochure": all_metrics,
    }
    sc_path = output_dir / f"scorecard_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    sc_path.write_text(json.dumps(scorecard, indent=2, default=str), encoding="utf-8")
    print(f"\n  Scorecard saved to: {sc_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Floor Plan Extraction QA Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default=None,
        help="Path to the PDF brochure (not required for --batch)",
    )
    parser.add_argument(
        "--output-dir",
        default="scripts/qa_output",
        help="Output directory for reports and images (default: scripts/qa_output)",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Skip Vision API calls (table + text extraction only)",
    )
    parser.add_argument(
        "--replay",
        metavar="DIR",
        help="Replay from a previous run dir (uses cached Vision responses, no API cost)",
    )
    parser.add_argument(
        "--generate-ground-truth",
        action="store_true",
        help="Generate a ground truth draft JSON from extraction results",
    )
    parser.add_argument(
        "--ground-truth",
        metavar="PATH",
        help="Path to ground truth JSON file for comparison",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run QA on ALL brochures with ground truth files and print scorecard",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    if args.batch:
        asyncio.run(run_batch(output_dir, args.no_api))
        return

    if args.pdf_path is None:
        parser.error("pdf_path is required (unless using --batch)")

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    asyncio.run(
        run_qa(
            str(pdf_path),
            output_dir,
            args.no_api,
            args.generate_ground_truth,
            args.ground_truth,
            args.replay,
        )
    )


if __name__ == "__main__":
    main()
