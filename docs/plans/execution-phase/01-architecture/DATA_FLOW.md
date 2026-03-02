# Data Flow Architecture

**Last Updated:** 2026-01-15
**Related Documents:**
- [System Architecture](./SYSTEM_ARCHITECTURE.md)
- [API Design](./API_DESIGN.md)
- [Database Schema](./DATABASE_SCHEMA.md)
- [Service Layer](../04-backend/SERVICE_LAYER.md)

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level Data Flow](#high-level-data-flow)
3. [Upload and Initialization Flow](#upload-and-initialization-flow)
4. [Text Processing Flow](#text-processing-flow)
5. [Visual Processing Flow](#visual-processing-flow)
6. [QA Validation Flow](#qa-validation-flow)
7. [Approval Workflow Flow](#approval-workflow-flow)
8. [Publication Flow](#publication-flow)
9. [Data Transformations](#data-transformations)
10. [Error Handling Flow](#error-handling-flow)
11. [Related Documentation](#related-documentation)

---

## Overview

This document describes how data flows through the PDP Automation v.3 system from initial PDF upload to final publication. The system uses a **parallel processing architecture** where text extraction and image processing occur concurrently, optimizing for speed and efficiency.

---

## High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React 19 + Vite)                   │
│  HomePage │ ProcessingPage │ QAPage │ PromptsPage │ Workflow   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API (JSON over HTTPS)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 BACKEND (FastAPI + Python 3.10+)                │
│  /api/upload │ /api/projects │ /api/qa │ /api/prompts │ /auth  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Text Pipeline │  │Visual Pipeline│  │  QA Service   │
│ - Extract     │  │ - Extract Imgs│  │ - Compare     │
│ - Generate    │  │ - Classify    │  │ - Validate    │
│ - Push Sheets │  │ - Floor Plans │  │ - History     │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│                   Anthropic API (Claude Sonnet 4.5 + Claude Sonnet 4.5)           │
│  Claude Sonnet 4.5: Vision (classification, extraction, watermark)       │
│  Claude Sonnet 4.5: Text (content generation, comparison, QA)       │
└──────────────────────────┬────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│     Neon      │  │ Cloud Storage │  │ Google Sheets │
│  PostgreSQL   │  │     (GCS)     │  │      API      │
│               │  │               │  │               │
│  - Users      │  │  - PDFs       │  │  - Templates  │
│  - Projects   │  │  - Images     │  │  - Content    │
│  - Jobs       │  │  - ZIPs       │  │  - Sharing    │
│  - Prompts    │  │  - FloorPlans │  │               │
│  - QA         │  │               │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Upload and Initialization Flow

### Step 1: User Uploads PDF

```
User (Browser)
  │
  │ POST /api/upload
  │ - file: <pdf_file>
  │ - website: "opr"
  │ - template_id: "uuid"
  │
  ▼
FastAPI Backend
  │
  │ 1. Authenticate user (JWT token)
  │ 2. Validate file (extension, MIME type, size, magic bytes)
  │ 3. Generate unique job_id
  │
  ▼
Database (Neon PostgreSQL)
  │
  │ INSERT INTO jobs (
  │   id, user_id, website, template_id, status="pending"
  │ )
  │
  ▼
Cloud Storage (GCS)
  │
  │ Upload to: gs://pdp-automation-assets-dev/pdfs/{job_id}/original.pdf
  │
  ▼
Cloud Tasks Queue
  │
  │ Enqueue processing task
  │ {
  │   "job_id": "uuid",
  │   "pdf_path": "gs://...",
  │   "website": "opr",
  │   "template_id": "uuid"
  │ }
  │
  ▼
Response to User
  │
  │ {
  │   "job_id": "uuid",
  │   "status": "pending",
  │   "created_at": "2026-01-15T10:00:00Z"
  │ }
  │
  ▼
User receives job_id
(polls GET /api/jobs/{job_id} for status)
```

### Data Format at Each Stage

**Upload Request:**
```json
{
  "file": "<binary PDF data>",
  "website": "opr",
  "template_id": "12345678-1234-1234-1234-123456789abc"
}
```

**Job Record (Database):**
```json
{
  "id": "98765432-9876-9876-9876-987654321098",
  "user_id": "user-uuid",
  "website": "opr",
  "template_id": "template-uuid",
  "status": "pending",
  "progress": 0,
  "current_step": "Upload PDF",
  "created_at": "2026-01-15T10:00:00Z"
}
```

**Cloud Tasks Payload:**
```json
{
  "job_id": "98765432-9876-9876-9876-987654321098",
  "pdf_path": "gs://pdp-automation-assets-dev/pdfs/98765432.../original.pdf",
  "website": "opr",
  "template_id": "template-uuid",
  "user_id": "user-uuid"
}
```

---

## Text Processing Flow

### Step 2: Triple Extraction from PDF

```
Cloud Tasks Worker
  │
  │ Receives task from queue
  │
  ▼
JobManager.process_job()
  │
  │ Update status: "processing", step: "Extracting images and text"
  │
  ▼
PDFProcessor.extract_all(pdf_bytes)
  │
  │ 1. Embedded extraction: doc.extract_image(xref) for raster XObjects
  │ 2. Page rendering: page.get_pixmap() at 300 DPI for vector content
  │ 3. Text extraction: pymupdf4llm.to_markdown() for per-page markdown
  │
  ▼
ExtractionResult
  │
  │ {
  │   embedded: [ExtractedImage, ...],
  │   page_renders: [ExtractedImage, ...],
  │   page_text_map: {1: "# Marina Bay Residences\n...", 2: "...", ...},
  │   total_pages: N
  │ }
  │
  ▼
Anthropic Service (Claude Sonnet 4.5)
  │
  │ POST https://api.anthropic.com/v1/messages
  │ {
  │   "model": "claude-sonnet-4-5-20241022",
  │   "max_tokens": 4096,
  │   "system": "<extraction_prompt>",
  │   "messages": [
  │     {"role": "user", "content": "<pdf_text>"}
  │   ]
  │ }
  │
  ▼
Structured Data Extracted
  │
  │ {
  │   "name": "Marina Bay Residences",
  │   "developer": "Emaar Properties",
  │   "location": "Dubai Marina",
  │   "emirate": "Dubai",
  │   "starting_price": 1500000,
  │   "property_types": ["apartment", "penthouse"],
  │   "amenities": ["Pool", "Gym", "Parking"],
  │   "handover_date": "2027-Q4",
  │   "payment_plan": "60/40",
  │   "unit_sizes": [
  │     {"type": "1BR", "sqft_min": 650, "sqft_max": 750},
  │     {"type": "2BR", "sqft_min": 1100, "sqft_max": 1300}
  │   ]
  │ }
  │
  ▼
QA Checkpoint 1: Extraction Validation
  │
  │ QAService.validate_extraction()
  │ - Check all required fields present
  │ - Verify data types
  │ - Cross-reference with PDF
  │
  ▼
Database (Neon PostgreSQL)
  │
  │ INSERT INTO projects (...extracted_data...)
  │ INSERT INTO qa_comparisons (checkpoint="extraction", status="passed")
  │
  ▼
Extracted data stored
```

### Step 3: Generate Content

```
ContentGenerator.generate()
  │
  │ 1. Load active prompt for website/template
  │ 2. Apply character limits
  │ 3. Generate SEO tags
  │
  ▼
Anthropic Service (Claude Sonnet 4.5)
  │
  │ POST https://api.anthropic.com/v1/messages
  │ {
  │   "model": "claude-sonnet-4-5-20241022",
  │   "max_tokens": 4096,
  │   "system": "<generation_prompt>",
  │   "messages": [
  │     {"role": "user", "content": "<structured_data>"}
  │   ]
  │ }
  │
  ▼
Generated Content
  │
  │ {
  │   "meta_title": "Marina Bay Residences by Emaar | Dubai Marina",
  │   "meta_description": "Luxury apartments in Dubai Marina...",
  │   "h1": "Marina Bay Residences",
  │   "intro_paragraph": "Discover waterfront living...",
  │   "amenities_text": "World-class amenities include...",
  │   "payment_plan_text": "Flexible 60/40 payment plan...",
  │   "location_text": "Prime location in Dubai Marina...",
  │   "url_slug": "marina-bay-residences-dubai-marina"
  │ }
  │
  ▼
QA Checkpoint 2: Generation Validation
  │
  │ ContentQAService.validate_before_push()
  │ - Compare generated content to extracted data
  │ - Check factual accuracy
  │ - Verify prompt compliance
  │
  ▼
Validation Result
  │
  │ {
  │   "status": "passed",
  │   "matches": 45,
  │   "differences": 0,
  │   "issues": []
  │ }
  │
  ▼
Database Update
  │
  │ UPDATE projects SET
  │   generated_content = {...},
  │   workflow_status = "pending_approval"
  │
  │ INSERT INTO qa_comparisons (checkpoint="generation", status="passed")
  │
  ▼
SheetsManager.populate_sheet()
  │
  │ 1. Create new Google Sheet from template
  │ 2. Batch update cells with generated content
  │ 3. Share with @your-domain.com organization
  │
  ▼
Google Sheets API
  │
  │ POST https://sheets.googleapis.com/v4/spreadsheets
  │ POST https://sheets.googleapis.com/v4/spreadsheets/{id}/values:batchUpdate
  │
  ▼
Sheet URL Returned
  │
  │ https://docs.google.com/spreadsheets/d/ABC123.../edit
  │
  ▼
Database Update
  │
  │ UPDATE projects SET
  │   sheet_url = "https://docs.google.com/..."
  │
  ▼
Text processing complete
```

---

## Visual Processing Flow

### Step 4: Extract and Classify Images

```
PDFProcessor.extract_all() (images from ExtractionResult)
  │
  │ Embedded raster XObjects + 300 DPI page renders
  │ (text extraction also runs here; page_text_map stored in ExtractionResult)
  │
  ▼
Extracted Images (from ExtractionResult.embedded + .page_renders)
  │
  │ [ExtractedImage, ExtractedImage, ..., ExtractedImage]
  │
  ▼
Upload to GCS
  │
  │ gs://pdp-automation-assets-dev/images/{job_id}/original/
  │
  ▼
ImageClassifier.classify_batch()
  │
  │ Process in batches of 10-20 images
  │
  ▼
Anthropic Service (Claude Sonnet 4.5 Vision)
  │
  │ For each image:
  │ POST https://api.anthropic.com/v1/messages
  │ {
  │   "model": "claude-sonnet-4-5-20241022",
  │   "max_tokens": 1024,
  │   "messages": [
  │     {
  │       "role": "user",
  │       "content": [
  │         {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": "<base64_image>"}},
  │         {"type": "text", "text": "<classification_prompt>"}
  │       ]
  │     }
  │   ]
  │ }
  │
  ▼
Classification Results
  │
  │ [
  │   {"image": "image_001.jpg", "category": "exterior"},
  │   {"image": "image_002.jpg", "category": "interior"},
  │   {"image": "003.jpg", "category": "amenity"},
  │   {"image": "004.jpg", "category": "floor_plan"},
  │   {"image": "005.jpg", "category": "logo"}
  │ ]
  │
  ▼
Separate Floor Plans
  │
  │ floor_plans = [images with category="floor_plan"]
  │ standard_images = [all other images]
  │
  ▼
FloorPlanExtractor.extract_data()
  │
  │ For each floor plan image:
  │ Anthropic Claude Sonnet 4.5 Vision extracts:
  │ - Unit type (1BR, 2BR, etc.)
  │ - Bedrooms count
  │ - Bathrooms count
  │ - Total area (sqft)
  │ - Balcony area (sqft)
  │ - Built-up area (sqft)
  │
  ▼
Floor Plan Data
  │
  │ [
  │   {
  │     "image_url": "gs://.../floor_plan_1.jpg",
  │     "unit_type": "1BR",
  │     "bedrooms": 1,
  │     "bathrooms": 1,
  │     "total_sqft": 750,
  │     "balcony_sqft": 100,
  │     "builtup_sqft": 650
  │   }
  │ ]
  │
  ▼
Database Insert
  │
  │ INSERT INTO project_floor_plans (
  │   project_id, unit_type, bedrooms, total_sqft, image_url
  │ )
```

### Step 5: Watermark Detection and Removal

```
WatermarkDetector.detect()
  │
  │ For each standard image (not floor plans):
  │
  ▼
Anthropic Service (Claude Sonnet 4.5 Vision)
  │
  │ POST https://api.anthropic.com/v1/messages
  │ {
  │   "model": "claude-sonnet-4-5-20241022",
  │   "max_tokens": 1024,
  │   "messages": [
  │     {
  │       "role": "user",
  │       "content": [
  │         {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": "<base64>"}},
  │         {"type": "text", "text": "Detect watermark location"}
  │       ]
  │     }
  │   ]
  │ }
  │
  ▼
Watermark Bounding Box
  │
  │ {
  │   "x": 50,
  │   "y": 50,
  │   "width": 200,
  │   "height": 100
  │ }
  │
  ▼
WatermarkDetector.remove_watermark()
  │
  │ Use OpenCV inpainting to remove watermark
  │ cv2.inpaint(image, mask, radius, method)
  │
  ▼
Cleaned Image
```

### Step 6: Image Optimization

```
ImageOptimizer.optimize()
  │
  │ For each image:
  │ 1. Resize to max 1920x1080 (maintain aspect ratio)
  │ 2. Compress to target size (200KB for standard, 150KB for thumbs)
  │ 3. Convert to WebP format (better compression)
  │
  ▼
Optimized Images
  │
  │ [
  │   "exterior_001.webp",
  │   "interior_001.webp",
  │   "amenity_001.webp"
  │ ]
  │
  ▼
Upload to GCS
  │
  │ gs://pdp-automation-assets-dev/images/{job_id}/optimized/
  │
  ▼
Database Insert
  │
  │ INSERT INTO project_images (
  │   project_id, category, image_url, thumbnail_url
  │ )
```

### Step 7: Package ZIP

```
OutputOrganizer.create_zip_package()
  │
  │ Create directory structure:
  │ /interior/
  │ /exterior/
  │ /amenity/
  │ /floor_plans/
  │ /logo/
  │
  ▼
Add Images to ZIP
  │
  │ Organize images by category
  │ Include floor plans with extracted data
  │
  ▼
Upload to GCS
  │
  │ gs://pdp-automation-assets-dev/outputs/{job_id}/images.zip
  │
  ▼
Share with Google Drive
  │
  │ Share ZIP with @your-domain.com organization
  │
  ▼
Database Update
  │
  │ UPDATE projects SET
  │   processed_zip_url = "gs://.../images.zip"
  │
  ▼
Visual processing complete
```

---

## QA Validation Flow

### Three-Checkpoint QA System

```
┌──────────────────────────────────────────────┐
│         Checkpoint 1: Extraction             │
├──────────────────────────────────────────────┤
│ Validates: PDF parsing accuracy              │
│ Compares: Extracted data vs. PDF text        │
│ Checks:                                      │
│ - All required fields present                │
│ - Data types correct                         │
│ - Values plausible                           │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│         Checkpoint 2: Generation             │
├──────────────────────────────────────────────┤
│ Validates: Generated content accuracy        │
│ Compares: Generated content vs. extracted    │
│ Checks:                                      │
│ - Factual consistency                        │
│ - Prompt compliance                          │
│ - Character limits respected                 │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│         Checkpoint 3: Publication            │
├──────────────────────────────────────────────┤
│ Validates: Published page matches approved   │
│ Compares: Published page vs. sheet content   │
│ Checks:                                      │
│ - All fields published correctly             │
│ - Images displayed properly                  │
│ - SEO tags match                             │
└──────────────────────────────────────────────┘
```

### QA Comparison Data Flow

```
User initiates QA check
  │
  │ POST /api/qa/compare
  │ {
  │   "project_id": "uuid",
  │   "checkpoint_type": "generation",
  │   "input_content": {...},
  │   "comparison_target": {...}
  │ }
  │
  ▼
QAService.validate_generation()
  │
  │ 1. Load extracted data from database
  │ 2. Load generated content from database
  │ 3. Compare field by field
  │
  ▼
Anthropic Service (Claude Sonnet 4.5)
  │
  │ POST https://api.anthropic.com/v1/messages
  │ {
  │   "model": "claude-sonnet-4-5-20241022",
  │   "max_tokens": 2048,
  │   "system": "Compare these two documents for factual consistency...",
  │   "messages": [
  │     {
  │       "role": "user",
  │       "content": "Extracted: {...}\nGenerated: {...}"
  │     }
  │   ]
  │ }
  │
  ▼
QA Result
  │
  │ {
  │   "status": "passed" | "failed",
  │   "matches": 45,
  │   "differences": 2,
  │   "missing": 1,
  │   "extra": 0,
  │   "result": {
  │     "differences": [
  │       {
  │         "field": "starting_price",
  │         "expected": "1500000",
  │         "actual": "1600000",
  │         "severity": "high"
  │       }
  │     ],
  │     "missing": ["property_tax"],
  │     "extra": []
  │   }
  │ }
  │
  ▼
Database Insert
  │
  │ INSERT INTO qa_comparisons (
  │   project_id,
  │   checkpoint_type,
  │   status,
  │   result,
  │   performed_by,
  │   performed_at
  │ )
  │
  ▼
Response to User
  │
  │ QA results displayed in UI with diff visualization
```

---

## Approval Workflow Flow

### Approval State Machine

```
┌─────────────┐
│   DRAFT     │ (Initial state)
└──────┬──────┘
       │ User clicks "Submit for Approval"
       │
       ▼
┌──────────────────┐
│ PENDING_APPROVAL │
└──────┬───────────┘
       │
       ├──────────────────┐
       │                  │
       │ Approve          │ Request Revision
       │                  │
       ▼                  ▼
┌─────────────┐   ┌───────────────────┐
│  APPROVED   │   │ REVISION_REQUESTED│
└──────┬──────┘   └─────────┬─────────┘
       │                    │
       │                    │ User updates and resubmits
       │                    │
       │                    ▼
       │           ┌──────────────────┐
       │           │ PENDING_APPROVAL │
       │           └──────────────────┘
       │
       │ Publishing team downloads assets
       │
       ▼
┌─────────────┐
│ PUBLISHING  │
└──────┬──────┘
       │ Mark as published
       │
       ▼
┌─────────────┐
│  PUBLISHED  │
└──────┬──────┘
       │ QA verifies published page
       │
       ▼
┌─────────────┐
│ QA_VERIFIED │
└──────┬──────┘
       │ All steps complete
       │
       ▼
┌─────────────┐
│  COMPLETE   │
└─────────────┘
```

### Approval Action Data Flow

```
Reviewer approves project
  │
  │ POST /api/projects/{id}/approve
  │ {
  │   "comments": "Looks good, approved for publication"
  │ }
  │
  ▼
ProjectService.approve_project()
  │
  │ 1. Check user has "admin" or "reviewer" role
  │ 2. Verify current status is "pending_approval"
  │ 3. Update workflow status
  │
  ▼
Database Transaction
  │
  │ BEGIN TRANSACTION;
  │
  │ UPDATE projects
  │ SET workflow_status = "approved",
  │     last_modified_by = <reviewer_id>,
  │     last_modified_at = NOW()
  │ WHERE id = <project_id>;
  │
  │ INSERT INTO project_approvals (
  │   project_id,
  │   approver_id,
  │   action,
  │   comments,
  │   created_at
  │ ) VALUES (
  │   <project_id>,
  │   <reviewer_id>,
  │   'approved',
  │   'Looks good...',
  │   NOW()
  │ );
  │
  │ INSERT INTO notifications (
  │   user_id,
  │   type,
  │   message,
  │   project_id
  │ ) VALUES (
  │   <creator_id>,
  │   'approval',
  │   'Your project has been approved',
  │   <project_id>
  │ );
  │
  │ COMMIT;
  │
  ▼
NotificationService.send_notification()
  │
  │ Create in-app notification for project creator
  │
  ▼
Response to Reviewer
  │
  │ {
  │   "id": "project-uuid",
  │   "workflow_status": "approved",
  │   "approval": {
  │     "approver": {...},
  │     "comments": "Looks good...",
  │     "approved_at": "2026-01-15T10:30:00Z"
  │   }
  │ }
```

---

## Publication Flow

### Publishing Process

```
Publishing team downloads assets
  │
  │ GET /api/projects/{id}
  │
  ▼
Retrieve project data with assets
  │
  │ {
  │   "sheet_url": "https://docs.google.com/spreadsheets/...",
  │   "processed_zip_url": "https://storage.googleapis.com/...",
  │   "floor_plans": [...]
  │ }
  │
  ▼
Publishing team creates page on website
  │
  │ (Manual or automated process)
  │
  ▼
Publishing team marks as published
  │
  │ POST /api/projects/{id}/publish
  │ {
  │   "published_url": "https://opr.com/properties/marina-bay-residences"
  │ }
  │
  ▼
ProjectService.mark_published()
  │
  │ UPDATE projects SET
  │   workflow_status = "published",
  │   published_url = "...",
  │   published_at = NOW()
  │
  ▼
QA team verifies published page
  │
  │ POST /api/qa/compare
  │ {
  │   "project_id": "uuid",
  │   "checkpoint_type": "publication",
  │   "comparison_target": "https://opr.com/properties/..."
  │ }
  │
  ▼
WebScraper.scrape_page()
  │
  │ 1. Fetch published page HTML
  │ 2. Extract meta tags
  │ 3. Extract content using CSS selectors
  │
  ▼
Scraped Data
  │
  │ {
  │   "meta_title": "Marina Bay Residences...",
  │   "meta_description": "...",
  │   "h1": "Marina Bay Residences",
  │   "content": {...}
  │ }
  │
  ▼
QAService.compare_published()
  │
  │ Compare scraped data to approved sheet content
  │
  ▼
QA Result
  │
  │ {
  │   "status": "passed",
  │   "differences": []
  │ }
  │
  ▼
Database Update
  │
  │ UPDATE projects SET
  │   workflow_status = "qa_verified"
  │
  │ INSERT INTO qa_comparisons (
  │   checkpoint_type = "publication",
  │   status = "passed"
  │ )
  │
  ▼
Project marked as complete
  │
  │ UPDATE projects SET
  │   workflow_status = "complete"
```

---

## Data Transformations

### PDF → Extracted Data

**Input (PDF):**
```
Raw PDF with mixed formatting, images, text blocks
```

**Output (Structured JSON):**
```json
{
  "name": "Marina Bay Residences",
  "developer": "Emaar Properties",
  "location": "Dubai Marina",
  "emirate": "Dubai",
  "starting_price": 1500000,
  "price_per_sqft": 2000,
  "handover_date": "2027-12-31",
  "payment_plan": "60/40",
  "property_types": ["apartment", "penthouse"],
  "unit_sizes": [
    {"type": "1BR", "sqft_min": 650, "sqft_max": 750},
    {"type": "2BR", "sqft_min": 1100, "sqft_max": 1300}
  ],
  "amenities": ["Swimming Pool", "Gym", "Parking"],
  "total_units": 250,
  "floors": 30,
  "buildings": 2
}
```

### Extracted Data → Generated Content

**Input (Structured JSON):**
```json
{
  "name": "Marina Bay Residences",
  "developer": "Emaar Properties",
  "location": "Dubai Marina",
  "starting_price": 1500000,
  "property_types": ["apartment", "penthouse"],
  "amenities": ["Pool", "Gym", "Parking"]
}
```

**Output (SEO-Optimized Content):**
```json
{
  "meta_title": "Marina Bay Residences by Emaar | Apartments in Dubai Marina",
  "meta_description": "Discover luxury apartments & penthouses at Marina Bay Residences by Emaar Properties. Starting from AED 1.5M. Premium amenities & prime location.",
  "h1": "Marina Bay Residences - Dubai Marina",
  "intro_paragraph": "Experience waterfront living at its finest at Marina Bay Residences, an exclusive development by Emaar Properties in the heart of Dubai Marina. This prestigious community offers a perfect blend of modern luxury and convenience, with stunning views of the marina and easy access to world-class dining, shopping, and entertainment.",
  "amenities_text": "Residents enjoy a comprehensive range of premium amenities including a state-of-the-art swimming pool, fully-equipped gymnasium, and secure underground parking. The development is designed to provide a resort-style living experience with 24/7 security and concierge services.",
  "location_text": "Strategically located in Dubai Marina, residents are just minutes away from JBR Beach, Dubai Marina Mall, and the Dubai Metro. The community offers unparalleled connectivity to Sheikh Zayed Road and easy access to key business districts.",
  "payment_plan_text": "Flexible 60/40 payment plan available. Pay 60% during construction and 40% upon handover. Competitive pricing starting from AED 1.5 million.",
  "url_slug": "marina-bay-residences-dubai-marina"
}
```

### Images → Categorized & Optimized

**Input (Raw Images):**
```
image_001.jpg (3MB, 4096x3072, uncategorized)
image_002.jpg (2.5MB, 3840x2160, uncategorized)
image_003.jpg (1.8MB, 3000x2000, uncategorized)
```

**Output (Categorized & Optimized):**
```
exterior_001.webp (200KB, 1920x1080, "exterior")
interior_001.webp (180KB, 1920x1080, "interior")
amenity_001.webp (195KB, 1920x1080, "amenity")
floor_plan_1br.webp (150KB, 1200x900, "floor_plan")
  └─ Extracted data: {unit_type: "1BR", sqft: 750}
```

---

## Error Handling Flow

### Error Detection and Recovery

```
Error Occurs
  │
  ▼
┌─────────────────────────────────────┐
│ Error Type Classification           │
├─────────────────────────────────────┤
│ - Upload Error                      │
│ - Processing Error                  │
│ - AI Service Error                  │
│ - Database Error                    │
│ - External Service Error            │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ Retry Strategy                      │
├─────────────────────────────────────┤
│ Transient errors: Exponential       │
│ backoff (3 retries)                 │
│                                     │
│ Rate limit: Wait and retry          │
│                                     │
│ Fatal errors: Fail immediately      │
└──────────┬──────────────────────────┘
           │
           │ Max retries exceeded
           │
           ▼
┌─────────────────────────────────────┐
│ Error Logging                       │
├─────────────────────────────────────┤
│ 1. Log to Cloud Logging             │
│ 2. Send to Sentry (with context)    │
│ 3. Update job status to "failed"    │
│ 4. Store error details in DB        │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ User Notification                   │
├─────────────────────────────────────┤
│ - In-app notification               │
│ - Error message in UI               │
│ - Option to retry or cancel         │
└─────────────────────────────────────┘
```

### Error Data Flow

```
Processing Error Occurs
  │
  │ Exception: AnthropicRateLimitError
  │
  ▼
JobManager catches exception
  │
  │ 1. Log error details
  │ 2. Determine retry strategy
  │
  ▼
Database Update
  │
  │ UPDATE jobs SET
  │   status = "failed",
  │   error_message = "Anthropic rate limit exceeded. Retrying in 60s...",
  │   retry_count = retry_count + 1
  │
  ▼
Exponential Backoff
  │
  │ Wait: 2^retry_count * 10 seconds
  │ (10s, 20s, 40s for retries 1, 2, 3)
  │
  ▼
Retry Job
  │
  │ Enqueue task back to Cloud Tasks
  │
  ▼
If max retries exceeded (3)
  │
  │ UPDATE jobs SET status = "failed"
  │
  │ INSERT INTO notifications (
  │   user_id,
  │   type = "error",
  │   message = "Processing failed after 3 retries"
  │ )
  │
  ▼
User receives notification in UI
```

---

## Related Documentation

- [System Architecture](./SYSTEM_ARCHITECTURE.md) - Overall system design
- [API Design](./API_DESIGN.md) - RESTful API specification
- [Database Schema](./DATABASE_SCHEMA.md) - Database structure
- [Service Layer](../04-backend/SERVICE_LAYER.md) - Service implementations
- [Background Jobs](../04-backend/BACKGROUND_JOBS.md) - Async processing patterns

---

**Last Updated:** 2026-01-15
