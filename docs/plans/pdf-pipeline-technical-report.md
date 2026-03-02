# PDF Processing Pipeline - Technical Analysis Report

## Executive Summary

The PDP Automation v.3 PDF processing pipeline is a multi-stage async system that extracts images, text, and metadata from real estate brochures, classifies assets via Claude Vision, optimizes them, and outputs a structured package with generated content. The pipeline processes 14 sequential steps triggered via Google Cloud Tasks.

**Key Metrics:**
- **Processing stages**: 14 steps (8 material prep + 4 content gen + 2 finalization)
- **Typical PDF**: 10-50 pages, 50+ images
- **API calls per PDF**: 50+ Anthropic Vision calls (classification + OCR fallback + content generation)
- **Cost estimate**: ~$0.90 per PDF (worst case with Vision OCR)
- **Memory footprint**: 50+ MB per active job in pipeline context

---

## 1. Pipeline Architecture Overview

```
                                    [UPLOAD PHASE]
                                          |
                       POST /api/v1/upload/pdf (multipart/form-data)
                                          |
                        +------------ Validation -------------+
                        |  - Content-Length <= 200MB          |
                        |  - Content-Type = application/pdf   |
                        |  - Magic bytes = %PDF               |
                        |  - Template type validation         |
                        +-------------------------------------+
                                          |
                        +------------ Storage ----------------+
                        |  Stream to temp -> Upload to GCS    |
                        |  Path: gs://bucket/{user_id}/{file} |
                        +-------------------------------------+
                                          |
                        +------------ Job Creation -----------+
                        |  - Create Job + 14 JobStep records  |
                        |  - Commit transaction (critical!)   |
                        |  - Dispatch to Cloud Tasks          |
                        +-------------------------------------+
                                          |
                                    [ASYNC PROCESSING]
                                          |
                       Cloud Tasks -> POST /api/v1/internal/process-job
                                          |
                                 JobManager.execute_processing_pipeline()
                                          |
    +---------------------------------+   |   +----------------------------------+
    |    PHASE 2: MATERIAL PREP       |   |   |    PHASE 3: CONTENT GEN          |
    +---------------------------------+   |   +----------------------------------+
    | 1. upload (3%)                  |   |   | 9. extract_data (60%)            |
    | 2. extract_images (10%)         |   |   | 10. structure_data (68%)         |
    | 3. classify_images (20%)        |   |   | 11. generate_content (78%)       |
    | 4. detect_watermarks (27%)      |   |   | 12. populate_sheet (88%)         |
    | 5. remove_watermarks (34%)      |   |   +----------------------------------+
    | 6. extract_floor_plans (40%)    |   |
    | 7. optimize_images (47%)        |   |   +----------------------------------+
    | 8. package_assets (53%)         |   |   |    FINALIZATION                  |
    +---------------------------------+   |   +----------------------------------+
                                          |   | 13. upload_cloud (95%)           |
                                          |   | 14. finalize (100%)              |
                                          |   +----------------------------------+
```

---

## 2. Step-by-Step Processing Details

### Step 1: Upload (3%) - `_step_upload`
**Location:** [job_manager.py:650-705](backend/app/services/job_manager.py#L650)

| Action | Details |
|--------|---------|
| Input | GCS path or `file://` path |
| Validation | PDF magic bytes check |
| Storage | Already uploaded in upload route |
| Output | `{pdf_path, file_size_bytes}` |

---

### Step 2: Extract Images (10%) - `_step_extract_images`
**Location:** [job_manager.py:707-744](backend/app/services/job_manager.py#L707)

**Core Service:** [PDFProcessor.extract_all()](backend/app/services/pdf_processor.py#L71)

| Stage | Technology | Config | Output |
|-------|------------|--------|--------|
| **Embedded Extraction** | PyMuPDF `page.get_images(full=True)` | Min 100x50px | ExtractedImage objects with xref dedup |
| **Page Rendering** | PyMuPDF `page.get_pixmap()` | 300 DPI | PNG rasters of each page |
| **Text Extraction** | pymupdf4llm `to_markdown()` | `page_chunks=True` | Per-page markdown |
| **Vision OCR Fallback** | Claude Vision API | Triggers if <100 chars/page avg | 4000 tokens/page |

**Configuration Thresholds:**
```python
MAX_PDF_SIZE = 500_000_000      # 500MB - pdf_processor.py:36
MAX_PAGES = 100                 # pdf_processor.py:37
MIN_CHARS_PER_PAGE = 100        # OCR fallback trigger - pdf_processor.py:40
RENDER_DPI = 300                # Page render quality - pdf_helpers.py:24
MIN_IMAGE_WIDTH = 100           # Embedded filter - pdf_helpers.py:20
MIN_IMAGE_HEIGHT = 50           # Embedded filter - pdf_helpers.py:21
```

**Cross-Page Deduplication:**
- XRef tracking in `seen_xrefs` set prevents duplicate embedded images across pages
- Location: [pdf_processor.py:104](backend/app/services/pdf_processor.py#L104)

---

### Step 3: Classify Images (20%) - `_step_classify_images`
**Location:** [job_manager.py:746-766](backend/app/services/job_manager.py#L746)

**Core Service:** [ImageClassifier.classify_extraction()](backend/app/services/image_classifier.py#L149)

**Processing Pipeline (3 Phases):**

| Phase | Input | Processing | Output |
|-------|-------|------------|--------|
| **1. Embedded** | Embedded images | Claude Vision per image -> pHash dedup @ 95% | Classified, deduped |
| **2. Page Renders** | Page rasters | Cross-source dedup (>70% coverage?) -> Claude Vision -> pHash @ 95% | Remaining unique |
| **3. Logo Extraction** | Cover pages (1-2) | Bounding box detection via Claude Vision -> crop | Extracted logos |

**Classification Categories:**
```python
CATEGORIES = [
    "interior",       # Indoor spaces
    "exterior",       # Building facade, outdoor
    "amenity",        # Pool, gym, common areas
    "floor_plan",     # Architectural layouts
    "logo",           # Developer/project logos
    "location_map",   # Maps
    "master_plan",    # Site plans
    "other"           # Discarded (text-only, decorative)
]
```

**Claude Vision Call (per image):**
- Location: [image_classifier.py:282-345](backend/app/services/image_classifier.py#L282)
- Max tokens: 300
- Retries: 3
- Returns: `{category, confidence, reasoning, alt_text}`

**Deduplication Thresholds:**
```python
FLOOR_PLAN_SIMILARITY_THRESHOLD = 0.95  # 95% perceptual hash match
CROSS_SOURCE_COVERAGE = 0.70            # Skip render if embedded covers 70%+ area
```

---

### Step 4-5: Watermark Detection/Removal (27%, 34%)
**Location:** [job_manager.py:768-822](backend/app/services/job_manager.py#L768)

| Action | Technology | Notes |
|--------|------------|-------|
| Detection | WatermarkDetector | Scans non-floor-plan, non-logo images |
| Removal | OpenCV inpainting | Cleans detected regions |

---

### Step 6: Floor Plan Extraction (40%)
**Location:** [job_manager.py:824-853](backend/app/services/job_manager.py#L824)

- Filters to `floor_plan` category images
- Uses `FloorPlanExtractor` with page text context
- Outputs structured floor plan data with sidecar JSON

---

### Step 7: Optimize Images (47%) - `_step_optimize_images`
**Location:** [job_manager.py:855-888](backend/app/services/job_manager.py#L855)

**Core Service:** [ImageOptimizer.optimize_batch()](backend/app/services/image_optimizer.py#L126)

**Dual-Tier Output Strategy:**

| Tier | Max Dimensions | Use Case | Formats |
|------|----------------|----------|---------|
| **Tier 1 (Original)** | 2450 x 1400 px | Website delivery | WebP@85, JPG@90 |
| **Tier 2 (LLM)** | 1568 px (longest) | Claude Vision input | WebP@85, JPG@90 |

**Processing Steps:**
1. Color space conversion (CMYK -> RGB)
2. Mode conversion (RGBA, palette, grayscale -> RGB)
3. Resize to bounds (LANCZOS resampling)
4. DPI metadata: 300
5. Dual format encoding

**No upscaling** - only downscales to specified dimensions

---

### Step 8: Package Assets (53%) - `_step_package_assets`
**Location:** [job_manager.py:890-936](backend/app/services/job_manager.py#L890)

**Core Service:** [OutputOrganizer.create_package()](backend/app/services/output_organizer.py)

**ZIP Structure:**
```
archive.zip/
  original/
    interiors/        *.webp, *.jpg
    exteriors/        *.webp, *.jpg
    amenities/        *.webp, *.jpg
    logos/            *.webp, *.jpg
    floor_plans/      *.webp, *.jpg
    location_maps/    *.webp, *.jpg
    master_plans/     *.webp, *.jpg
  optimized/
    [same structure - LLM-optimized versions]
  floor_plans/
    floor_plan_data.json      (consolidated)
    {image-name}.json         (per-image sidecar)
  extracted_text.json         (page text map)
  manifest.json               (metadata + entries)
```

---

### Step 9: Extract Data (60%) - `_step_extract_data`
**Location:** [job_manager.py:942-983](backend/app/services/job_manager.py#L942)

**Core Service:** [DataExtractor.extract()](backend/app/services/data_extractor.py#L111)

**No external API calls** - Pure regex/text analysis:

| Field | Method | Confidence Range |
|-------|--------|-----------------|
| Project Name | H1 headers, all-caps, bold markdown | 0.7-0.9 |
| Developer | "by Developer" patterns, known vendor list | 0.5-0.9 |
| Location | Emirates/communities list matching | 0.9 |
| Prices | AED pattern matching with K/M suffixes | 0.6-0.8 |
| Bedrooms | Pattern: "1BR", "2 Bedroom", "3 B/R" | List return |
| Amenities | Known amenities list matching | Set dedup |
| Payment Plan | Percentage extraction | 0-0.9 |

---

### Step 10: Structure Data (68%) - `_step_structure_data`
**Location:** [job_manager.py:1022-1073](backend/app/services/job_manager.py#L1022)

- Uses Claude to structure extracted data
- Fallback: Uses image alt_texts if PDF text is empty
- Outputs validated project metadata

---

### Step 11: Generate Content (78%) - `_step_generate_content`
**Location:** [job_manager.py:1075-1124](backend/app/services/job_manager.py#L1075)

**Core Service:** [ContentGenerator.generate_all()](backend/app/services/content_generator.py#L58)

**Per-Field API Calls:**
- Model: `claude-sonnet-4-5-20250514`
- Max tokens: ~200-1000 per field
- Retries: 3 (for character limit enforcement)
- Inter-field delay: 0.5s (rate limit prevention)

**Progress Callback:** Updates `job.progress_message` for UI visibility

---

### Step 12: Populate Sheet (88%) - `_step_populate_sheet`
**Location:** [job_manager.py:1126-1185](backend/app/services/job_manager.py#L1126)

**Core Service:** [SheetsManager](backend/app/services/sheets_manager.py)

| Operation | API Call |
|-----------|----------|
| Copy template | `sheets.copy()` |
| Batch update cells | `values.batchUpdate()` |
| Read-back validation | `values.get()` |

---

### Step 13: Upload to Cloud (95%) - `_step_upload_cloud`
**Location:** [job_manager.py:1187-1298](backend/app/services/job_manager.py#L1187)

**Core Service:** [DriveClient](backend/app/integrations/drive_client.py)

**Folder Structure Created:**
```
Project Folder/
  Source/         -> Original PDF
  Images/         -> Optimized images by category
  Raw Data/       -> JSON files (manifest, floor plans, text)
```

**Concurrency:** Max 5 parallel uploads (semaphore)
**Retry:** 3 attempts with exponential backoff (1-32s)

---

### Step 14: Finalize (100%) - `_step_finalize`
**Location:** [job_manager.py:1300-1406](backend/app/services/job_manager.py#L1300)

- Creates `Project` database record
- Links to job via `processing_job_id`
- Stores `generated_content` as JSONB
- Sets `workflow_status = DRAFT`

---

## 3. External API Summary

### Anthropic (Claude) API

| Stage | Calls Per PDF | Tokens/Call | Total Tokens | Est. Cost |
|-------|---------------|-------------|--------------|-----------|
| Image Classification | 50 images | 300 | 15,000 | $0.23 |
| Vision OCR (if needed) | 10 pages | 4,000 | 40,000 | $0.60 |
| Logo Detection | 2 pages | 400 | 800 | $0.01 |
| Content Generation | 10 fields | 500 | 5,000 | $0.08 |
| **Total (worst case)** | | | **60,800** | **~$0.92** |

**Retry Config:**
```python
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0s
RETRY_DELAY_MAX = 15.0s
JITTER_MAX = 0.5s
```

### Google Drive API

| Operation | When | Rate Limit Handling |
|-----------|------|-------------------|
| Create folder | Step 13 | 3 retries, 1-32s backoff |
| Upload file | Step 13 | 5 concurrent max, resumable for large |
| Move sheet | Step 13 | Same |

### Google Cloud Storage

| Operation | When | Threshold |
|-----------|------|-----------|
| Upload PDF | Step 1 | Resumable if >5MB |
| Download PDF | Step 2 | Streaming |
| Signed URLs | On-demand | 60-min default expiry |

### Google Sheets API

| Operation | When | Rate Limit |
|-----------|------|-----------|
| Copy template | Step 12 | Standard quota |
| Batch update | Step 12 | Standard quota |
| Permission grant | Step 12 | Shared Drive quota |

---

## 4. Memory & Resource Usage

### Pipeline Context (per job)
```python
_pipeline_ctx[job_id] = {
    "extraction": ExtractionResult,     # Images + text
    "pdf_bytes": bytes,                 # Original PDF
    "pdf_path": str,
    "classification": ClassificationOutput,
    "detections": list,                 # Watermark masks
    "cleaned_images": list,             # Post-removal
    "floor_plans": FloorPlanResult,
    "optimization": OptimizationResult,
    "zip_bytes": bytes,                 # Full package
}
```

**Estimated per-job memory:** 50-100MB (depending on PDF size and image count)
**Cleanup:** Always in `finally` block after pipeline completes

---

## 5. Timing Analysis (Estimated)

| Step | Typical Duration | Bottleneck |
|------|-----------------|------------|
| Upload validation | 1-2s | File streaming |
| Extract images | 5-30s | PyMuPDF extraction, 300 DPI renders |
| Classify images | 30-120s | 50+ Claude Vision API calls |
| Detect watermarks | 5-15s | Image analysis |
| Remove watermarks | 5-20s | OpenCV inpainting |
| Extract floor plans | 10-30s | Structured extraction |
| Optimize images | 10-30s | PIL resize + encode |
| Package assets | 5-10s | ZIP compression |
| Extract data | 2-5s | Regex parsing |
| Structure data | 10-30s | Claude API |
| Generate content | 30-60s | 10+ Claude API calls |
| Populate sheet | 5-10s | Sheets API |
| Upload cloud | 20-60s | Drive uploads |
| Finalize | 1-2s | DB write |
| **Total** | **2-7 minutes** | |

---

## 6. Error Handling Summary

| Layer | Strategy | Recovery |
|-------|----------|----------|
| Upload | 413/400 status codes | Immediate rejection |
| Job dispatch | Mark FAILED if queue fails | User retry |
| Processing steps | 3 retries with exponential backoff | Auto-retry |
| Claude API | 3 retries, respects `retry_after` | Auto-retry |
| Drive API | 3 retries, 1-32s backoff | Auto-retry |
| Max retries exceeded | Job status = FAILED | Manual retry |

---

## 7. Key Files Reference

| Component | File Path |
|-----------|-----------|
| Upload endpoint | [backend/app/api/routes/upload.py](backend/app/api/routes/upload.py) |
| Job routes | [backend/app/api/routes/jobs.py](backend/app/api/routes/jobs.py) |
| Internal processor | [backend/app/api/routes/internal.py](backend/app/api/routes/internal.py) |
| Job manager | [backend/app/services/job_manager.py](backend/app/services/job_manager.py) |
| PDF processor | [backend/app/services/pdf_processor.py](backend/app/services/pdf_processor.py) |
| Image classifier | [backend/app/services/image_classifier.py](backend/app/services/image_classifier.py) |
| Image optimizer | [backend/app/services/image_optimizer.py](backend/app/services/image_optimizer.py) |
| Output organizer | [backend/app/services/output_organizer.py](backend/app/services/output_organizer.py) |
| Deduplication | [backend/app/services/deduplication_service.py](backend/app/services/deduplication_service.py) |
| Data extractor | [backend/app/services/data_extractor.py](backend/app/services/data_extractor.py) |
| Content generator | [backend/app/services/content_generator.py](backend/app/services/content_generator.py) |
| Sheets manager | [backend/app/services/sheets_manager.py](backend/app/services/sheets_manager.py) |
| Drive client | [backend/app/integrations/drive_client.py](backend/app/integrations/drive_client.py) |
| Storage service | [backend/app/services/storage_service.py](backend/app/services/storage_service.py) |
| Anthropic client | [backend/app/integrations/anthropic_client.py](backend/app/integrations/anthropic_client.py) |
| Task queue | [backend/app/background/task_queue.py](backend/app/background/task_queue.py) |
| PDF helpers | [backend/app/utils/pdf_helpers.py](backend/app/utils/pdf_helpers.py) |
| Database models | [backend/app/models/database.py](backend/app/models/database.py) |

---

## 8. Configuration Reference

```python
# PDF Processing
MAX_PDF_SIZE = 500_000_000      # 500MB
MAX_PAGES = 100
RENDER_DPI = 300
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 50
MIN_CHARS_PER_PAGE = 100        # OCR fallback trigger

# Image Optimization
MAX_WIDTH = 2450                # Tier 1
MAX_HEIGHT = 1400               # Tier 1
LLM_MAX_DIM = 1568             # Tier 2
WEBP_QUALITY = 85
JPG_QUALITY = 90
OUTPUT_DPI = 300

# Deduplication
FLOOR_PLAN_SIMILARITY_THRESHOLD = 0.95
CROSS_SOURCE_COVERAGE = 0.70

# Retry Logic
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2s
RETRY_DELAY_MAX = 32s (Drive), 15s (Anthropic), 16s (Sheets)

# Rate Limiting
DRIVE_MAX_CONCURRENT = 5
CONTENT_GEN_INTER_FIELD_DELAY = 0.5s
```
