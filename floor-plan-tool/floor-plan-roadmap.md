Phase 1 — Foundation (Weeks 1–2)

Audit your current pipeline failures. Pull 50–100 brochures that caused extraction errors and categorize each failure by type: misattribution, multi-plan page, villa cross-page, position diagram confusion, or variant detection. This tells you which stages to prioritize.
Build the golden test suite. From that same set, select 50–100 brochures stratified by developer (Emaar, DAMAC, Sobha, Nakheel, etc.), unit type (apartment/villa/townhouse), and complexity level. Manually create verified ground truth JSON for each — unit type, bedroom count, sqft, floor range, and crop coordinates per floor plan. This becomes your regression gate for every future change.
Set up the dual extraction baseline. For every page: render to 300 DPI image (PyMuPDF) AND extract text with bounding box coordinates (pdfplumber or Docling). Store both outputs per page. This replaces the current approach of treating text and image extraction as a single pass.


Phase 2 — Layout Detection Model (Weeks 3–5)

Set up annotation tooling. Install CVAT or Label Studio. Define your custom classes: floor_plan, position_diagram, data_table, building_render, lifestyle_photo, site_plan.
Annotate 300–500 brochure pages. Prioritize diversity — cover at least 15–20 different developers and include pages with multiple floor plans, villa multi-floor spreads, and position diagrams. This is the most time-consuming step but the highest-leverage investment in the entire pipeline.
Fine-tune DocLayout-YOLO or YOLOv11 on your annotated dataset. Use the Ultralytics training pipeline. Start with a pretrained DocLayout-YOLO checkpoint (already understands document structure), fine-tune on your labeled data. Validate against a held-out 20% split.
Test detection accuracy on your golden test suite. Measure per-class precision/recall. You need >90% on floor_plan detection and >85% on position_diagram vs. floor_plan discrimination before proceeding.


Phase 3 — Spatial Attribution (Weeks 5–7)

Build the per-region text association logic. For each detected floor plan bounding box, gather all text elements (from Step 3’s pdfplumber output) whose coordinates fall within or adjacent to that box. Use proximity scoring — closer text gets higher association confidence.
Implement table extraction for specification pages. Integrate Docling’s TableFormer or a similar table recognition model. Many brochures have a specifications table that maps unit types to areas and floor ranges — this is often the most reliable data source when it exists.
Build the cross-page villa grouping module. Logic: scan consecutive pages for floor plan detections sharing the same unit identifier text (e.g., “Villa Type A”). Detect level indicators (“Ground Floor,” “First Floor,” “Roof Terrace”) via OCR. Group them into a single multi-level unit record.
Implement unit variant detection. After associating text with each floor plan, parse variant labels (“Type A,” “Type B,” “Layout 1,” “Layout 2”) from nearby text. Generate composite identifiers like 2BR-TypeA, 2BR-TypeB. When multiple floor plans on the same page share a bedroom count, flag them as potential variants.


Phase 4 — Template Matching Layer (Weeks 7–9)

Build developer identification. Detect developer from logo (YOLO class or CLIP matching), header text patterns, or PDF metadata. Map each brochure to a developer ID.
Create extraction templates for your top 10–15 developers by volume. For each developer, define deterministic extraction rules based on their typical brochure layout — where unit types appear, where the spec table lives, how floor plans are arranged. These templates produce near-100% accuracy for known formats.
Implement the template-first routing logic. When a brochure arrives: attempt developer ID → template match → if match confidence is high, use template extraction. If low or unknown developer, route to the AI pipeline (YOLO → spatial attribution → VLM).


Phase 5 — VLM Verification Layer (Weeks 9–10)

Add targeted VLM verification for low-confidence extractions. Send only cropped regions (not full pages) with a structured prompt asking for specific fields. Use Gemini Flash for cost efficiency on bulk verification, Claude for numerical accuracy on flagged cases.
Design the VLM prompts for each specific task: “Extract the unit type, bedroom count, and total area in sqft from this floor plan image” with strict JSON output schema. Test and iterate prompts against your golden test suite.


Phase 6 — QA and Production Hardening (Weeks 10–12)

Implement automated field validation rules. Area range checks by bedroom count, floor number bounds, required field completeness, unit count reconciliation against brochure totals.
Build the human review queue and UI. Show source PDF page with highlighted bounding boxes alongside extracted data. Route anything below 0.85 confidence to review. Track reviewer override rates per pipeline stage — this is your most actionable improvement metric.
Set up CI/CD regression testing. Every pipeline change runs against the golden test suite with automated precision/recall/F1 scoring per field, per developer. Block deployments that degrade accuracy.
Build the feedback loop. Every human-corrected extraction becomes training data — corrections feed back into YOLO fine-tuning, template refinement, and VLM prompt improvement. This is the flywheel that makes the system improve with volume rather than break with variety.


The critical path is Steps 4–7 (YOLO fine-tuning). That single intervention solves page segmentation, multi-plan cropping, and position diagram confusion — which account for most of your current failures. Everything else builds on having reliable region detection as the foundation.​​​​​​​​​​​​​​​​