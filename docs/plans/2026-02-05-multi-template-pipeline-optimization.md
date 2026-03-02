# Multi-Template Pipeline Optimization — Extract Once, Generate Many

**Problem:** Every project template requires a full pipeline run (~$0.85–0.92, 2–7 min), even though 80% of the work (image extraction, classification, optimization, data extraction, structuring) is identical across templates. Running 3 templates for one project costs ~$2.76 and takes 6–21 minutes instead of ~$1.00 and 3–8 minutes.

**Solution:** Split the pipeline into a reusable **Extraction Phase** (runs once per PDF) and a lightweight **Generation Phase** (runs once per template). Store extraction results as a durable **MaterialPackage** in GCS that any template can consume on-demand.

---

## Architecture: Before vs After

### Current (v.3) — Full Pipeline Per Template

```
Template A:  PDF → [Steps 1–14] → Sheet A    ~$0.92, 2–7 min
Template B:  PDF → [Steps 1–14] → Sheet B    ~$0.92, 2–7 min  (redundant extraction)
Template C:  PDF → [Steps 1–14] → Sheet C    ~$0.92, 2–7 min  (redundant extraction)
                                              ─────────────────
                                              ~$2.76, 6–21 min total
```

### Proposed — Extract Once, Generate Many

```
PDF → [Extraction Phase: Steps 1–10] → MaterialPackage (GCS)    ~$0.85, 1.5–5 min (once)
          │
          ├→ [Generation Phase: Steps 11–14] → Sheet A           ~$0.04, 30–60s
          ├→ [Generation Phase: Steps 11–14] → Sheet B           ~$0.04, 30–60s
          └→ [Generation Phase: Steps 11–14] → Sheet C           ~$0.04, 30–60s
                                                                 ─────────────────
                                                                 ~$0.97, 2.5–6.5 min total
```

**Savings for 3 templates:** 65% cost reduction, 60% time reduction. The savings increase with each additional template.

---

## Where to Split the Pipeline

The natural split point is **after step 10 (structure_data)**. Everything before this step is template-agnostic — the extracted images, classified categories, floor plan data, optimized assets, project metadata (name, developer, location, prices, bedrooms, amenities) are the same regardless of which website template the content is for.

| Steps 1–10 (Extraction Phase) | Steps 11–14 (Generation Phase) |
|-------------------------------|-------------------------------|
| Template-agnostic | Template-specific |
| Runs once per PDF | Runs once per template |
| ~$0.85 cost, 1.5–5 min | ~$0.04 cost, 30–60s per template |
| Produces MaterialPackage | Consumes MaterialPackage |
| Expensive: Vision API, OCR, image processing | Cheap: 1 content generation call + Sheets API |

What changes per template in the Generation Phase:

- **Content generation prompts** — different tone, style, and emphasis per website (luxury portal vs general listing)
- **Field definitions** — different fields, different character limits (website A allows 80-char titles, website B allows 120)
- **Sheet template ID** — different Google Sheet source template to copy
- **Cell mapping** — field X goes to cell B3 on template A, cell C5 on template B
- **Drive folder** — each template output may go to a different destination folder

---

## The MaterialPackage

After step 10 completes, all reusable data is persisted to GCS as a structured package. This is the contract between the Extraction Phase and any number of Generation Phase runs.

### Storage Layout

```
gs://bucket/materials/{project_id}/
  metadata.json            # MaterialPackage manifest
  structured_data.json     # Project metadata from steps 9–10
  extracted_text.json      # Per-page markdown from pymupdf4llm
  floor_plan_data.json     # Consolidated floor plan information
  image_manifest.json      # All classified/optimized images with categories
  assets.zip               # Packaged images from step 8 (or individual refs)
  pages/                   # Page renders for fallback use
    page_001.jpg
    page_002.jpg
    ...
```

### metadata.json Schema

```json
{
  "package_version": "1.0",
  "project_id": "uuid",
  "source_job_id": "uuid",
  "created_at": "2025-02-05T12:00:00Z",
  "source_pdf": {
    "filename": "brochure.pdf",
    "gcs_path": "gs://bucket/uploads/{user_id}/brochure.pdf",
    "page_count": 32,
    "file_size_bytes": 45000000
  },
  "extraction_summary": {
    "total_images": 47,
    "classified_images": {
      "interior": 12,
      "exterior": 8,
      "amenity": 6,
      "floor_plan": 15,
      "logo": 2,
      "location_map": 1,
      "master_plan": 1,
      "other": 2
    },
    "text_extraction_method": "pymupdf4llm",
    "ocr_used": false
  },
  "available_for_generation": true,
  "generation_runs": [
    {
      "template_id": "template_property_finder",
      "job_id": "uuid",
      "status": "completed",
      "sheet_url": "https://docs.google.com/spreadsheets/d/...",
      "completed_at": "2025-02-05T12:03:00Z"
    }
  ]
}
```

### structured_data.json — What Steps 9–10 Produce

This is the template-agnostic project data that every generation run consumes:

```json
{
  "project_name": "Azure Residences",
  "developer": "Nakheel",
  "location": {
    "emirate": "Dubai",
    "community": "Palm Jumeirah",
    "sub_community": null
  },
  "prices": {
    "starting_from": 2500000,
    "currency": "AED",
    "price_range": "2.5M - 8.2M AED"
  },
  "bedrooms": ["1BR", "2BR", "3BR", "4BR"],
  "amenities": ["infinity pool", "gym", "spa", "concierge", "valet parking"],
  "payment_plan": {
    "down_payment": "20%",
    "during_construction": "50%",
    "on_handover": "30%"
  },
  "completion_date": "Q4 2027",
  "property_types": ["apartment", "penthouse"],
  "floor_plans": [
    {
      "unit_type": "1BR Type A",
      "total_area_sqft": 850,
      "image_ref": "floor_plans/fp_001.jpg",
      "rooms": {"bedroom": 1, "bathroom": 1, "balcony": 1}
    }
  ],
  "key_features": ["beachfront", "branded residences", "panoramic sea views"],
  "confidence_scores": {
    "project_name": 0.9,
    "developer": 0.85,
    "location": 0.9,
    "prices": 0.7
  }
}
```

---

## Template Configuration Model

Each template defines what content to generate and where to put it. Templates are stored in the database (or a config file) and referenced by ID.

### TemplateConfig Schema

```python
class TemplateFieldDef(BaseModel):
    field_name: str                    # e.g., "title", "description", "seo_title"
    max_length: Optional[int]          # Character limit for this template
    cell_reference: str                # Where in the sheet, e.g., "B3"
    prompt_override: Optional[str]     # Template-specific prompt tweak
    source: str                        # "generated" or "extracted"
    extraction_path: Optional[str]     # JSONPath into structured_data, e.g., "$.project_name"

class TemplateConfig(BaseModel):
    template_id: str                   # e.g., "property_finder_v2"
    template_name: str                 # Human-readable: "Property Finder"
    website: str                       # "propertyfinder.ae", "bayut.com"
    spreadsheet_template_id: str       # Google Sheets template to copy
    target_drive_folder_id: str        # Where to put the output
    system_prompt: str                 # Base prompt for content generation
    tone: str                          # "luxury", "professional", "casual"
    language: str                      # "en", "ar", "en+ar"
    fields: list[TemplateFieldDef]     # All fields for this template

    # Pydantic output schema is built dynamically from fields
    def build_output_schema(self) -> type[BaseModel]:
        """Generate a Pydantic model matching this template's generated fields."""
        field_defs = {}
        for f in self.fields:
            if f.source == "generated":
                if f.max_length:
                    field_defs[f.field_name] = (str, Field(max_length=f.max_length))
                else:
                    field_defs[f.field_name] = (str, ...)
        return create_model(f"Generated_{self.template_id}", **field_defs)
```

### Distinguishing Extracted vs Generated Fields

This directly addresses the note about prompt coverage percentages. Each template field is tagged as either `"extracted"` (populated directly from structured_data.json via a JSONPath) or `"generated"` (requires an LLM call). Prompt coverage should only measure completion of **generated** fields, not extracted ones.

| Field | Source | Template A Cell | Template B Cell |
|-------|--------|----------------|----------------|
| Project Name | extracted (`$.project_name`) | B2 | C3 |
| Developer | extracted (`$.developer`) | B3 | C4 |
| Location | extracted (`$.location.community`) | B4 | C5 |
| Title | **generated** (80 chars) | B5 | C6 |
| Description | **generated** (300 words) | B6 | C7 |
| SEO Title | **generated** (60 chars) | B7 | — (not used) |

Prompt coverage = generated fields with valid prompts / total generated fields. Extracted fields are excluded from this metric entirely.

---

## Generation Phase Flow (Steps 11–14, Per Template)

When a generation job runs, it receives a `material_package_ref` (GCS path) and a `template_id`. It does not touch any image processing or text extraction code.

```
Generation Job Input:
  - material_package_ref: gs://bucket/materials/{project_id}/
  - template_id: "property_finder_v2"
  - project_id: UUID (to link output)

Step 11: Generate Content
  1. Load structured_data.json from MaterialPackage
  2. Load TemplateConfig for the target template
  3. Build dynamic Pydantic schema from template's generated fields
  4. Populate extracted fields directly from structured_data (no LLM needed)
  5. Call Claude once with structured outputs for all generated fields
  6. Validate output against field constraints
  → Output: complete field map {field_name: value} for all fields

Step 12: Populate Sheet
  1. Copy the template's spreadsheet_template_id
  2. Map fields to cells using TemplateConfig.fields[].cell_reference
  3. Batch update all cells
  4. Read-back validation
  → Output: new Google Sheet URL

Step 13: Upload to Cloud
  1. Upload sheet + assets to template's target_drive_folder_id
  2. Reuse image assets from MaterialPackage (already optimized)
  3. No need to re-upload images if they're already in a shared project folder
  → Output: Drive folder URL

Step 14: Finalize
  1. Link generation job to Project via project_jobs table
  2. Store generated_content as JSONB with template attribution
  3. Update MaterialPackage metadata.json with new generation_run entry
  → Output: completed project record
```

### Cost Per Generation Run

| Component | Cost | Time |
|-----------|------|------|
| Load MaterialPackage from GCS | Free | ~50ms |
| Extract fields (no LLM) | Free | <1ms |
| Generate content (1 Claude call) | ~$0.04 | 5–8s |
| Populate sheet (Sheets API) | Free | 5–10s |
| Upload to Drive | Free | 10–30s |
| **Total per template** | **~$0.04** | **20–50s** |

---

## Database Changes

### New Tables and Fields

```sql
-- Template configurations
CREATE TABLE template_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id VARCHAR(100) UNIQUE NOT NULL,      -- "property_finder_v2"
    template_name VARCHAR(255) NOT NULL,            -- "Property Finder"
    website VARCHAR(255),                           -- "propertyfinder.ae"
    spreadsheet_template_id VARCHAR(255) NOT NULL,  -- Google Sheets template
    target_drive_folder_id VARCHAR(255),
    system_prompt TEXT,
    tone VARCHAR(50) DEFAULT 'professional',
    language VARCHAR(10) DEFAULT 'en',
    field_definitions JSONB NOT NULL,               -- Array of TemplateFieldDef
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Material packages (extraction results)
CREATE TABLE material_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    source_job_id UUID REFERENCES jobs(id),
    gcs_base_path VARCHAR(500) NOT NULL,            -- gs://bucket/materials/{project_id}/
    package_version VARCHAR(10) DEFAULT '1.0',
    extraction_summary JSONB,                        -- Image counts, methods used
    structured_data JSONB,                           -- Cached copy for quick access
    status VARCHAR(50) DEFAULT 'ready',              -- ready, expired, error
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ                           -- Optional TTL
);

-- Generation runs (one per template per project)
CREATE TABLE generation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    material_package_id UUID REFERENCES material_packages(id),
    template_id VARCHAR(100) REFERENCES template_configs(template_id),
    job_id UUID REFERENCES jobs(id),                 -- The generation job
    generated_content JSONB,                         -- All field values
    sheet_url VARCHAR(500),
    drive_folder_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending',            -- pending, processing, completed, failed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    UNIQUE(project_id, template_id)                  -- One run per template per project
);

-- Indexes
CREATE INDEX idx_material_packages_project ON material_packages(project_id);
CREATE INDEX idx_generation_runs_project ON generation_runs(project_id);
CREATE INDEX idx_generation_runs_template ON generation_runs(template_id);
```

### Modifications to Existing Tables

```sql
-- Add material_package_id to jobs (for generation jobs to reference their source)
ALTER TABLE jobs ADD COLUMN material_package_id UUID REFERENCES material_packages(id);
ALTER TABLE jobs ADD COLUMN job_type VARCHAR(50) DEFAULT 'full';  -- 'full', 'extraction', 'generation'
```

---

## API Changes

### New Endpoints

```
POST /api/v1/process/extract
  - file: File (multipart) OR pdf_url: string
  - template_ids: string[] (optional — if provided, generation starts automatically after extraction)
  - Returns: { extraction_job_id: UUID, project_id: UUID, generation_job_ids?: UUID[] }
  - Runs extraction phase only. If template_ids provided, queues generation jobs to start on completion.

POST /api/v1/process/generate
  - project_id: UUID
  - template_ids: string[]
  - Returns: { generation_job_ids: UUID[] }
  - Requires existing MaterialPackage for the project. Fails if extraction hasn't completed.
  - Can be called multiple times to add templates to an existing project.

GET /api/v1/projects/{project_id}/materials
  - Returns: MaterialPackage metadata + list of generation runs with status
  - Shows what's been extracted and which templates have been generated.

GET /api/v1/templates
  - Returns: list of available TemplateConfig (id, name, website, field count)
  - Used by frontend to populate template selector.

POST /api/v1/projects/{project_id}/regenerate/{template_id}
  - Re-runs content generation for a specific template using existing MaterialPackage
  - Useful when prompts are updated or user wants to refresh content
  - Returns: { generation_job_id: UUID }
```

### Modified Endpoints

```
POST /api/v1/upload/pdf (existing)
  - Add optional: template_ids: string[] (defaults to primary template for backward compat)
  - If template_ids provided: extraction + parallel generation
  - If not provided: behaves exactly as v.3 (full pipeline, single template)
```

---

## Job Manager Changes

### New Job Types

The JobManager needs to handle three job types:

```python
class JobType(str, Enum):
    FULL = "full"              # Legacy v.3 behavior (steps 1–14)
    EXTRACTION = "extraction"  # Steps 1–10 only, produces MaterialPackage
    GENERATION = "generation"  # Steps 11–14 only, consumes MaterialPackage
```

### Extraction Job Flow

```python
async def execute_extraction_pipeline(self, job_id: UUID):
    """Steps 1–10: Extract, classify, optimize, structure. Store as MaterialPackage."""
    try:
        await self._step_upload(job_id)           # 1
        await self._step_extract_images(job_id)   # 2
        await self._step_classify_images(job_id)  # 3
        await self._step_detect_watermarks(job_id)# 4
        await self._step_remove_watermarks(job_id)# 5
        await self._step_extract_floor_plans(job_id)# 6
        await self._step_optimize_images(job_id)  # 7
        await self._step_package_assets(job_id)   # 8
        await self._step_extract_data(job_id)     # 9
        await self._step_structure_data(job_id)   # 10
        
        # NEW: Persist MaterialPackage to GCS
        material_package = await self._persist_material_package(job_id)
        
        # Dispatch generation jobs for requested templates
        template_ids = job.processing_config.get("template_ids", [])
        for template_id in template_ids:
            await self._dispatch_generation_job(
                project_id=job.project_id,
                material_package_id=material_package.id,
                template_id=template_id
            )
    finally:
        self._cleanup_pipeline_ctx(job_id)
```

### Generation Job Flow

```python
async def execute_generation_pipeline(self, job_id: UUID):
    """Steps 11–14: Generate content for a specific template using MaterialPackage."""
    job = await self._get_job(job_id)
    material_package = await self._load_material_package(job.material_package_id)
    template_config = await self._load_template_config(job.processing_config["template_id"])
    
    # Load structured data from MaterialPackage (not from pipeline context)
    structured_data = await self._load_from_gcs(material_package.gcs_base_path + "/structured_data.json")
    
    # Step 11: Generate content with template-specific prompts
    generated = await self._step_generate_content_for_template(
        structured_data=structured_data,
        template_config=template_config,
    )
    
    # Step 12: Populate the template's specific sheet
    sheet_url = await self._step_populate_template_sheet(
        generated_content=generated,
        template_config=template_config,
    )
    
    # Step 13: Upload to template-specific Drive folder
    drive_url = await self._step_upload_template_outputs(
        material_package=material_package,
        template_config=template_config,
        sheet_url=sheet_url,
    )
    
    # Step 14: Finalize generation run
    await self._finalize_generation_run(
        job_id=job_id,
        project_id=material_package.project_id,
        template_id=template_config.template_id,
        generated_content=generated,
        sheet_url=sheet_url,
        drive_url=drive_url,
    )
```

---

## Integration With Existing Optimization Plan

This multi-template architecture is designed to layer cleanly on top of the phased optimization plan. Here's how each phase interacts:

| Optimization Plan Phase | Interaction | Notes |
|------------------------|-------------|-------|
| **Phase 1** (Quick wins: DPI, JPG-only, Drive concurrency) | No conflict | All apply to the Extraction Phase unchanged |
| **Phase 2.1** (Batch classification) | No conflict | Part of Extraction Phase |
| **Phase 2.2** (Concurrent API calls) | No conflict | Part of Extraction Phase |
| **Phase 2.3** (Consolidated content gen) | **Template-aware** | The single-call Pydantic schema must be built dynamically from TemplateConfig.fields instead of hardcoded |
| **Phase 2.4** (pyvips) | No conflict | Part of Extraction Phase |
| **Phase 3.1** (Hybrid OCR) | No conflict | Part of Extraction Phase |
| **Phase 3.2** (GCS-backed context) | **Prerequisite** | MaterialPackage IS the GCS-backed storage. This phase directly enables multi-template reuse |
| **Phase 3.3** (Parallel pipeline split) | **Synergistic** | Image pipe + text pipe parallelize the Extraction Phase. After convergence, generation jobs fan out in parallel per template |
| **Phase 3.4** (Local pre-filtering) | No conflict | Part of Extraction Phase |
| **v4** (Multi-document) | **Composable** | Multiple documents → shared MaterialPackage → multiple templates. M docs × N templates |

### Combined Architecture (Optimization Plan Phase 3.3 + Multi-Template)

```
Steps 1–2: Upload + Extract
        │
    extracted text + images
        │
   ┌────┴────┐
   │         │
IMAGE PIPE  TEXT PIPE
(steps 3–8) (steps 9–10)
   │         │
   └────┬────┘
        │
   CONVERGENCE → Persist MaterialPackage to GCS
        │
   ┌────┼────┐
   │    │    │
 GEN A  GEN B  GEN C     ← Parallel Cloud Tasks, one per template
(11–14)(11–14)(11–14)
   │    │    │
   └────┴────┘
        │
   All generation_runs linked to Project
```

---

## Integration With v4 Multi-Document Pipeline

The multi-template optimization composes naturally with v4's multi-document support. They're orthogonal concerns:

- **v4 Multi-Document:** Multiple PDFs contribute to a single MaterialPackage (via ProjectAggregator merge logic)
- **Multi-Template:** A single MaterialPackage produces content for multiple Google Sheet templates

Combined flow for a real-world scenario (main brochure + floor plans PDF, 3 website templates):

```
PDF 1 (brochure) → Extraction Job A ─┐
                                      ├→ ProjectAggregator → Merged MaterialPackage
PDF 2 (floor plans) → Extraction Job B┘
                                              │
                                     ┌────────┼────────┐
                                     │        │        │
                                   Gen PF   Gen BY   Gen DB
                                  (PropertyFinder) (Bayut) (Dubizzle)
```

The MaterialPackage schema already supports this — `structured_data.json` can be merged from multiple extraction jobs, and `image_manifest.json` tracks source document attribution.

---

## Floor Plan Data Consolidation

This architecture directly solves the floor plan fragmentation issue from the notes. Currently, floor plan images sit in one folder while their data sits in a separate JSON, forcing manual reconciliation.

In the MaterialPackage, floor plan data is stored with **direct image references**:

```json
// floor_plan_data.json in MaterialPackage
{
  "floor_plans": [
    {
      "unit_type": "1BR Type A",
      "total_area_sqft": 850,
      "image_ref": "gs://bucket/materials/{project_id}/assets/floor_plans/fp_001.jpg",
      "image_filename": "fp_001.jpg",
      "page_source": 12,
      "rooms": {
        "bedroom": {"count": 1, "area_sqft": 280},
        "bathroom": {"count": 1, "area_sqft": 65},
        "living_dining": {"area_sqft": 350},
        "balcony": {"count": 1, "area_sqft": 90}
      },
      "extraction_confidence": 0.85
    }
  ]
}
```

Each generation template can then map floor plan data to its own cell structure without any manual consolidation.

---

## Extracted Text Verification Step

Adding an LLM quality check between steps 9 and 10 (as noted in my-notes.md) fits naturally into the Extraction Phase. This becomes step 9.5:

```
Step 9:   extract_data (regex/text analysis)
Step 9.5: verify_extraction (NEW — LLM compares extracted JSON against page renders)
Step 10:  structure_data (Claude structures and fills gaps)
```

The verification step:
1. Takes the extracted_text.json and structured_data draft from step 9
2. Sends 2–3 key pages (cover, pricing page, specs page) as images to Claude
3. Asks Claude to verify: "Does the extracted data match what's visible in these pages?"
4. Flags discrepancies with confidence scores
5. Stores verification results in MaterialPackage for transparency

Cost: ~$0.03–0.05 per PDF (2–3 image + text verification calls). Worth it for data quality assurance, especially on flattened PDFs where text extraction fails silently.

---

## Implementation Plan

### Phase A: MaterialPackage Foundation (3–4 days)

This can be implemented **independently** of the optimization plan phases, as an overlay on the current v.3 pipeline.

```
[ ] A.1  Create material_packages, generation_runs, template_configs tables + migration
[ ] A.2  Create MaterialPackageService (persist/load/validate MaterialPackage to/from GCS)
[ ] A.3  Add _persist_material_package() to JobManager after step 10
[ ] A.4  Create TemplateConfig model and seed with primary template definition
[ ] A.5  Verify: existing full pipeline still works (extraction + materialization + single template gen)
```

### Phase B: Generation Job Separation (3–4 days)

```
[ ] B.1  Add job_type field to Job model (full/extraction/generation)
[ ] B.2  Create execute_generation_pipeline() in JobManager
[ ] B.3  Create _step_generate_content_for_template() using dynamic Pydantic schema
[ ] B.4  Create _step_populate_template_sheet() with template-specific cell mapping
[ ] B.5  Add POST /api/v1/process/generate endpoint
[ ] B.6  Add POST /api/v1/process/extract endpoint
[ ] B.7  Wire extraction completion → dispatch generation jobs for requested templates
```

### Phase C: Multi-Template UX (2–3 days)

```
[ ] C.1  GET /api/v1/templates endpoint
[ ] C.2  Template selector in upload UI (checkboxes for available templates)
[ ] C.3  Project detail view showing generation runs per template with status
[ ] C.4  "Generate for another template" action on completed projects
[ ] C.5  Regenerate action (re-run generation with updated prompts)
```

### Phase D: Quality & Polish (2–3 days)

```
[ ] D.1  Add extraction verification step (9.5) — LLM cross-checks extracted data against page renders
[ ] D.2  Fix prompt coverage metrics to exclude extracted fields
[ ] D.3  Add MaterialPackage expiry/cleanup (TTL on GCS temp prefix)
[ ] D.4  Backward compatibility: existing /upload/pdf with no template_ids runs full pipeline as before
```

### Timeline Integration

This work slots between Phase 2 and Phase 3 of the optimization plan, or can run in parallel:

```
Week 1:    Optimization Phase 1 (quick wins)
Week 2–3:  Optimization Phase 2 (batch classification, consolidated content gen)
Week 3–4:  Multi-Template Phases A + B (MaterialPackage + generation separation)  ← THIS
Week 4–5:  Multi-Template Phases C + D (UX + quality)
Week 5–7:  Optimization Phase 3 (hybrid OCR, streaming, parallel split)
Week 7+:   v4 Multi-Document
```

---

## Cost Summary

| Scenario | Current Cost | With Multi-Template | Savings |
|----------|-------------|--------------------|---------| 
| 1 PDF, 1 template | $0.92 | $0.89 (~$0.85 extraction + $0.04 generation) | 3% |
| 1 PDF, 2 templates | $1.84 | $0.93 | **49%** |
| 1 PDF, 3 templates | $2.76 | $0.97 | **65%** |
| 1 PDF, 5 templates | $4.60 | $1.05 | **77%** |

With optimization plan Phase 2 applied (batch classification + consolidated content gen):

| Scenario | Optimized Cost | With Multi-Template | Savings vs Baseline |
|----------|---------------|--------------------|--------------------|
| 1 PDF, 3 templates | $1.38 ($0.46 × 3) | ~$0.54 ($0.42 extraction + $0.04 × 3) | **80%** |

---

## Key Design Decisions

1. **Split after step 10, not step 8.** Steps 9–10 (data extraction + structuring) are template-agnostic and relatively cheap. Including them in the Extraction Phase means generation jobs only need to run content generation + sheet population — the cheapest and fastest part of the pipeline.

2. **GCS over Redis for MaterialPackage storage.** MaterialPackages are large (structured data + image refs + text), need to persist across requests (not just within a pipeline run), and may be consumed hours or days later when a user adds a new template. GCS is the right choice. Redis is for in-flight pipeline context.

3. **Dynamic Pydantic schemas per template.** Rather than a hardcoded PropertyListing model, the generation phase builds a Pydantic model from the template's field definitions at runtime. This means adding a new template is a config change, not a code change.

4. **Extracted fields bypass the LLM entirely.** Fields like project_name, developer, location, and prices are populated directly from structured_data.json into the sheet. Only creative/marketing fields (title, description, SEO content) go through content generation. This is faster, cheaper, and more reliable.

5. **Backward compatibility is mandatory.** The existing single-template `/upload/pdf` endpoint continues to work exactly as before. Multi-template is opt-in via the new endpoints or by passing `template_ids` to the existing endpoint.
