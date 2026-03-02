# Module: Material Preparation

**Module Number:** 1
**Category:** Visual Asset Processing
**Last Updated:** 2026-01-15
**Status:** Core Module

---

## Table of Contents

1. [Overview](#overview)
2. [Purpose & Goals](#purpose--goals)
3. [Key Features](#key-features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [Processing Pipeline](#processing-pipeline)
7. [API Endpoints](#api-endpoints)
8. [Services](#services)
9. [Workflow Diagrams](#workflow-diagrams)
10. [Code Examples](#code-examples)
11. [Configuration](#configuration)
12. [Related Documentation](#related-documentation)

---

## Overview

The **Material Preparation Module** is responsible for extracting, classifying, optimizing, and packaging all visual assets from PDF brochures. It processes images through a multi-stage pipeline that includes AI-powered classification, watermark detection and removal, floor plan extraction, deduplication, and format conversion.

**Position in System:** First parallel processing path that runs alongside text extraction, handling all visual content preparation.

---

## Purpose & Goals

### Primary Purpose

Extract and prepare all visual assets from PDF brochures in web-ready formats with proper categorization, optimization, and organization for publishing workflows.

### Goals

1. **Comprehensive Extraction:** Extract all usable images from PDF brochures
2. **Intelligent Classification:** Categorize images using Claude Sonnet 4.5 vision (interior, exterior, amenity, logo)
3. **Quality Assurance:** Remove watermarks, deduplicate, and optimize for web
4. **Floor Plan Processing:** Extract floor plans with data extraction and deduplication
5. **Web Optimization:** Convert to modern formats (WebP + JPG) with size/quality constraints
6. **Organized Delivery:** Package assets in structured ZIP files with categorized folders

---

## Key Features

### Core Capabilities

- ✅ **PDF Image Extraction** - Extract all images from uploaded PDFs
- ✅ **AI-Powered Classification** - Claude Sonnet 4.5 vision categorizes images automatically
- ✅ **Preset Limits** - Enforce category limits (10 exteriors, 10 interiors, 5 amenities, 3 logos)
- ✅ **Watermark Detection** - Claude Sonnet 4.5 vision identifies watermark locations
- ✅ **Watermark Removal** - OpenCV inpainting removes detected watermarks
- ✅ **Floor Plan Extraction** - Separate floor plans from general images
- ✅ **Floor Plan Data Extraction** - Claude Sonnet 4.5 vision extracts unit data from floor plans
- ✅ **Deduplication** - Remove duplicate floor plans (1 unit type = 1 floor plan)
- ✅ **Image Optimization** - Dual-tier output (original + LLM-optimized), 300 DPI, max 2450x1400px
- ✅ **Multi-Format Output** - Generate both WebP (modern) and JPG (legacy) formats
- ✅ **ZIP Packaging** - Organized folder structure for easy publishing
- ✅ **Cloud Storage** - Upload to Google Cloud Storage and Google Drive

### Image Categories

**Category Limits:**
- **Interior:** 10 images max - Lobby, apartments, living spaces
- **Exterior:** 10 images max - Building facade, surroundings, views
- **Amenity:** 5 images max - Pool, gym, spa, facilities
- **Logo:** 3 images max - Developer logos, project branding
- **Other:** Discarded - Graphs, charts, text-heavy pages

### Image Specifications

**Dual-Tier Image Strategy:**

The system produces TWO versions of each image to optimize for both quality and performance:

**Tier 1: Original/Archive Images**
- **Purpose:** Final output, client delivery, long-term storage
- **Quality:** Maximum fidelity, no compression losses
- **Resolution:** 300 DPI minimum
- **Max Dimensions:** 2450px x 1400px (maintain aspect ratio)
- **File Size:** No limit (quality preserved)
- **Formats:** WebP (primary) + JPG (fallback)
- **Quality Settings:** WebP 85%, JPG 90%
- **Storage:** GCS archive bucket, Google Drive delivery
- **Included in:** Final ZIP package

**Tier 2: LLM-Optimized Images**
- **Purpose:** Claude Sonnet 4.5 processing + web-optimized delivery
- **Quality:** Optimized for vision tasks without sacrificing accuracy
- **Max Dimensions:** Task-specific (see below)
- **Target Size:** ~200-400KB per image
- **Formats:** JPEG (classification, watermark) or PNG (floor plans)
- **Storage:** PERMANENT - included in final package alongside Tier 1
- **Included in:** Final ZIP package (web-ready versions)

**LLM Optimization Settings by Task:**

| Task | Max Dimension | Format | Quality |
|------|---------------|--------|---------|
| Classification | 1024px | JPEG | 80% |
| Watermark detection | 1280px | JPEG | 85% |
| Floor plan OCR | 1568px | PNG | Lossless |
| Alt-text generation | 1024px | JPEG | 80% |

**Why Two Tiers?**
- Claude charges tokens based on image size
- A 2450x1400 image at full quality = more tokens than necessary
- Vision tasks (classification, OCR) work well at reduced resolution
- Original quality preserved for final deliverables
- Estimated token savings: 40-60% per project

### Image Source Types

**Embedded Raster Images (JPEG/PNG)**
- Source: Marketing renders, scanned documents, photographs
- Extraction: `doc.extract_image(xref)` - direct extraction from PDF
- Quality: Depends on embedded resolution

**Vector Graphics (CAD exports, illustrations)**
- Source: Architectural software (AutoCAD, Revit), design tools
- Extraction: `page.get_pixmap()` - render page at high DPI
- Quality: Excellent (vector scales without loss)
- Render DPI: 300 for all pages

**Detection Heuristic:**
- If `page.get_images()` returns empty but page has content
- If extracted image dimensions < 500x500px
- If PDF metadata indicates CAD/vector origin

### Comprehensive Triple-Extraction Strategy

**Problem:** PyMuPDF's `extract_image()` only extracts embedded raster images (XObjects). It does NOT capture:
- Vector graphics composed as images
- CAD-exported floor plans drawn as vector paths
- Composited marketing renders
- Vector logos and illustrations
- Location maps and master plans

**Solution:** Extract BOTH embedded images AND page renders for ALL pages.

```
For each PDF page:
    1. Extract embedded images (doc.extract_image(xref))
       - FREE, instant
       - Captures raster XObjects

    2. Render full page (page.get_pixmap() at 300 DPI)
       - Captures ALL content including vectors
       - Consistent quality across all image types

    3. Classify BOTH sources through Claude Sonnet 4.5
       - Determine if render contains unique content
       - Deduplicate overlap using perceptual hash

    4. Keep both if render has unique content not in embedded
```

**Why ALL Image Types Need This (Not Just Floor Plans):**

| Image Type | Embedded Risk | Page Render Value |
|------------|---------------|-------------------|
| Exterior renders | May be vector-composited CGI | Captures full composition |
| Interior shots | Usually fine as embedded | Backup if quality issues |
| Amenity illustrations | Often vector graphics | Critical for vector amenities |
| Logos | Frequently vector/SVG origin | Essential for clean logos |
| Location maps | Almost always vector | Page render required |
| Master plans | Vector CAD exports | Page render required |
| Floor plans | Often vector CAD | Page render critical |

---

## Architecture

### Components Involved

```
┌─────────────────────────────────────────────────────────┐
│              UPLOAD LAYER                               │
├─────────────────────────────────────────────────────────┤
│ • FileUploadPage.tsx     - PDF upload interface        │
│ • GCS Upload             - Direct PDF to bucket         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           PROCESSING LAYER (Python)                     │
├─────────────────────────────────────────────────────────┤
│ • PDFProcessor           - Extract images from PDF     │
│ • ImageClassifier        - Claude Sonnet 4.5 vision categorization│
│ • WatermarkDetector      - Claude Sonnet 4.5 detect bounding boxes│
│ • WatermarkRemover       - OpenCV inpainting           │
│ • FloorPlanExtractor     - Separate floor plans        │
│ • FloorPlanDataExtractor - Claude Sonnet 4.5 vision data parsing  │
│ • DeduplicationService   - Remove duplicate floor plans│
│ • ImageOptimizer         - Resize, compress, convert   │
│ • OutputOrganizer        - Package into ZIP            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│            STORAGE LAYER                                │
├─────────────────────────────────────────────────────────┤
│ • Google Cloud Storage   - Permanent asset storage     │
│ • Google Drive           - Client-facing downloads     │
│ • PostgreSQL             - Image/floor plan metadata   │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

**Image Processing:**
- `PyMuPDF (fitz)` - PDF image extraction
- `Pillow (PIL)` - Image manipulation, resizing, format conversion
- `OpenCV (cv2)` - Watermark removal via inpainting
- `imagehash` - Perceptual hashing for deduplication

**AI Services:**
- `Anthropic Claude Sonnet 4.5` - Image classification, watermark detection, floor plan data extraction

**Storage:**
- `Google Cloud Storage` - Asset persistence
- `Google Drive API` - Client folder creation
- `Neon PostgreSQL` - Metadata storage

---

## Database Schema

### Table: `project_images`

**Purpose:** Store metadata for all extracted and processed images

```sql
CREATE TABLE project_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Classification
    category VARCHAR(50) NOT NULL,
    -- Categories: 'interior', 'exterior', 'amenity', 'logo', 'other'

    -- File Details
    filename VARCHAR(255),
    file_size_bytes BIGINT,
    format VARCHAR(10),  -- 'webp', 'jpg', 'png'
    width_px INTEGER,
    height_px INTEGER,
    dpi INTEGER DEFAULT 300,

    -- Storage Locations
    gcs_blob_path TEXT NOT NULL,
    google_drive_url TEXT,
    public_url TEXT,

    -- AI Metadata
    classification_confidence DECIMAL(3, 2),  -- 0.00 to 1.00
    classification_reasoning TEXT,
    alt_text TEXT,  -- Generated by Claude Sonnet 4.5

    -- Watermark Processing
    has_watermark BOOLEAN DEFAULT false,
    watermark_bounding_box JSONB,  -- {"x": 100, "y": 50, "width": 200, "height": 30}
    watermark_removed BOOLEAN DEFAULT false,
    watermark_removal_quality DECIMAL(3, 2),

    -- Processing Metadata
    original_pdf_page INTEGER,
    extraction_method VARCHAR(50),  -- 'pymupdf', 'pdfplumber'
    processing_duration_ms INTEGER,

    -- Display Order
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT valid_category CHECK (category IN ('interior', 'exterior', 'amenity', 'logo', 'other')),
    CONSTRAINT valid_confidence CHECK (classification_confidence BETWEEN 0 AND 1)
);

CREATE INDEX idx_images_project ON project_images(project_id);
CREATE INDEX idx_images_category ON project_images(category);
CREATE INDEX idx_images_display_order ON project_images(project_id, display_order);
CREATE INDEX idx_images_watermark ON project_images(has_watermark, watermark_removed);
```

---

### Table: `project_floor_plans`

**Purpose:** Store floor plan metadata and extracted data

```sql
CREATE TABLE project_floor_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Floor Plan Details
    unit_type VARCHAR(100),        -- e.g., "1 Bedroom", "2 Bedroom + Maid"
    unit_size_sqft DECIMAL(10, 2),
    bedrooms INTEGER,
    bathrooms DECIMAL(3, 1),       -- Support 2.5 baths
    has_maid_room BOOLEAN DEFAULT false,
    has_balcony BOOLEAN DEFAULT false,
    has_storage BOOLEAN DEFAULT false,

    -- Extracted Data (from Claude Sonnet 4.5 vision)
    extracted_data JSONB,
    -- Example:
    -- {
    --   "dimensions": {"living": "4.2m x 3.8m", "bedroom1": "3.5m x 3.2m"},
    --   "features": ["Walk-in closet", "En-suite bathroom"],
    --   "total_area": "850 sqft",
    --   "balcony_area": "65 sqft"
    -- }

    extraction_confidence DECIMAL(3, 2),

    -- File References
    image_url TEXT NOT NULL,
    google_drive_url TEXT,
    gcs_blob_path TEXT,

    -- Formats Available
    webp_path TEXT,
    jpg_path TEXT,

    -- Deduplication
    is_duplicate BOOLEAN DEFAULT false,
    duplicate_of_id UUID REFERENCES project_floor_plans(id),
    perceptual_hash VARCHAR(64),  -- For similarity detection

    -- Quality Metrics
    quality_score DECIMAL(3, 2),
    image_clarity VARCHAR(20),  -- 'high', 'medium', 'low'

    -- Processing Metadata
    original_pdf_page INTEGER,
    processing_duration_ms INTEGER,

    -- Display
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT valid_confidence CHECK (extraction_confidence BETWEEN 0 AND 1),
    CONSTRAINT valid_quality CHECK (quality_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_floor_plans_project ON project_floor_plans(project_id);
CREATE INDEX idx_floor_plans_unit_type ON project_floor_plans(unit_type);
CREATE INDEX idx_floor_plans_duplicate ON project_floor_plans(is_duplicate);
CREATE INDEX idx_floor_plans_hash ON project_floor_plans(perceptual_hash);
```

---

### Table: `processing_jobs`

**Purpose:** Track material preparation job status

```sql
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Job Details
    job_type VARCHAR(50) DEFAULT 'material_preparation',
    status VARCHAR(50) DEFAULT 'pending',
    -- Status: pending, processing, completed, failed

    -- Progress Tracking
    total_steps INTEGER DEFAULT 9,
    completed_steps INTEGER DEFAULT 0,
    current_step VARCHAR(100),

    -- Metrics
    images_extracted INTEGER DEFAULT 0,
    images_classified INTEGER DEFAULT 0,
    watermarks_removed INTEGER DEFAULT 0,
    floor_plans_extracted INTEGER DEFAULT 0,
    floor_plans_deduplicated INTEGER DEFAULT 0,

    -- Results
    output_zip_url TEXT,
    google_drive_folder_url TEXT,
    processing_duration_seconds INTEGER,

    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_jobs_project ON processing_jobs(project_id);
CREATE INDEX idx_jobs_status ON processing_jobs(status);
CREATE INDEX idx_jobs_created ON processing_jobs(created_at DESC);
```

---

## Processing Pipeline

### Complete Workflow

```
PDF UPLOAD
    │
    ├──> 1. PDF Image Extraction (PyMuPDF)
    │         ├─> Extract all images from PDF pages
    │         ├─> Preserve resolution and format
    │         └─> Store raw images temporarily
    │
    ├──> 2. Image Classification (Claude Sonnet 4.5 Vision)
    │         ├─> Send each image to Claude Sonnet 4.5
    │         ├─> Classify: interior/exterior/amenity/logo/other
    │         ├─> Extract confidence score
    │         └─> Discard "other" category
    │
    ├──> 3. Apply Category Limits
    │         ├─> Interior: Keep top 10 by confidence
    │         ├─> Exterior: Keep top 10 by confidence
    │         ├─> Amenity: Keep top 5 by confidence
    │         └─> Logo: Keep top 3 by confidence
    │
    ├──> 4. Watermark Detection (Claude Sonnet 4.5 Vision)
    │         ├─> Send each image to Claude Sonnet 4.5
    │         ├─> Detect watermark presence
    │         ├─> Extract bounding box coordinates
    │         └─> Store bounding box in metadata
    │
    ├──> 5. Watermark Removal (OpenCV)
    │         ├─> Apply inpainting algorithm
    │         ├─> Use bounding box from Claude Sonnet 4.5
    │         ├─> Validate removal quality
    │         └─> Fallback: Use original if quality poor
    │
    ├──> 6. Floor Plan Extraction (Claude Sonnet 4.5 Vision)
    │         ├─> Identify floor plan images
    │         ├─> Extract unit type, bedrooms, bathrooms
    │         ├─> Parse room dimensions from image
    │         ├─> Extract features (balcony, maid room, etc.)
    │         └─> Store structured data in JSONB
    │
    ├──> 7. Floor Plan Deduplication
    │         ├─> Generate perceptual hash for each floor plan
    │         ├─> Compare hashes (similarity threshold: 95%)
    │         ├─> Keep highest quality version per unit type
    │         └─> Mark duplicates (is_duplicate = true)
    │
    ├──> 8. Image Optimization
    │         ├─> Create Tier 1: Original quality (max 2450x1400px, 300 DPI)
    │         ├─> Create Tier 2: LLM-optimized (task-specific dimensions)
    │         ├─> Convert to WebP (85% quality) + JPG (90% quality)
    │         └─> Validate output quality
    │
    ├──> 9. ZIP Package Creation
    │         ├─> Organize into folders:
    │         │   ├── /interiors/
    │         │   ├── /exteriors/
    │         │   ├── /amenities/
    │         │   ├── /logos/
    │         │   └── /floor_plans/
    │         ├─> Include both WebP and JPG formats
    │         └─> Generate manifest.json with metadata
    │
    └──> 10. Cloud Upload
              ├─> Upload ZIP to GCS bucket
              ├─> Upload individual files to GCS
              ├─> Create Google Drive folder
              ├─> Upload to Google Drive for client access
              └─> Store URLs in database
```

---

## API Endpoints

### Job Management

#### `POST /api/jobs/material-preparation`

**Description:** Start material preparation job for uploaded PDF

**Request Body:**
```json
{
  "project_id": "uuid",
  "pdf_gcs_path": "gs://bucket/uploads/job-123/original.pdf",
  "options": {
    "skip_watermark_removal": false,
    "enable_deduplication": true,
    "max_images_per_category": {
      "interior": 10,
      "exterior": 10,
      "amenity": 5,
      "logo": 3
    }
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "created_at": "2025-01-15T10:00:00Z",
  "estimated_completion_minutes": 5
}
```

---

#### `GET /api/jobs/{job_id}/status`

**Description:** Get real-time job progress

**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": {
    "total_steps": 9,
    "completed_steps": 5,
    "current_step": "Watermark Removal",
    "percentage": 55
  },
  "metrics": {
    "images_extracted": 45,
    "images_classified": 45,
    "images_kept": 28,
    "watermarks_detected": 12,
    "watermarks_removed": 8,
    "floor_plans_extracted": 6,
    "floor_plans_deduplicated": 4
  },
  "eta_seconds": 120
}
```

---

#### `GET /api/jobs/{job_id}/results`

**Description:** Get completed job results

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "processing_duration_seconds": 287,
  "output": {
    "zip_download_url": "https://storage.googleapis.com/.../assets.zip",
    "google_drive_folder_url": "https://drive.google.com/drive/folders/...",
    "images": {
      "interior": 10,
      "exterior": 10,
      "amenity": 5,
      "logo": 3
    },
    "floor_plans": 4,
    "total_files": 32,
    "total_size_mb": 8.5
  }
}
```

---

### Image Management

#### `GET /api/projects/{project_id}/images`

**Description:** Get all images for a project

**Query Parameters:**
```typescript
{
  category?: 'interior' | 'exterior' | 'amenity' | 'logo';
  has_watermark?: boolean;
  format?: 'webp' | 'jpg';
}
```

**Response:**
```json
{
  "images": [
    {
      "id": "uuid",
      "category": "interior",
      "filename": "interior_01.webp",
      "width_px": 2400,
      "height_px": 1350,
      "file_size_bytes": 456789,
      "public_url": "https://storage.googleapis.com/...",
      "classification_confidence": 0.95,
      "has_watermark": true,
      "watermark_removed": true,
      "alt_text": "Modern luxury apartment living room with floor-to-ceiling windows",
      "display_order": 1
    }
  ]
}
```

---

#### `GET /api/projects/{project_id}/floor-plans`

**Description:** Get all floor plans for a project

**Response:**
```json
{
  "floor_plans": [
    {
      "id": "uuid",
      "unit_type": "2 Bedroom + Maid",
      "unit_size_sqft": 1250,
      "bedrooms": 2,
      "bathrooms": 2.5,
      "has_maid_room": true,
      "extracted_data": {
        "dimensions": {
          "living": "4.5m x 4.2m",
          "master_bedroom": "3.8m x 3.5m",
          "bedroom_2": "3.2m x 3.0m",
          "maid_room": "2.8m x 2.5m"
        },
        "features": ["Walk-in closet", "En-suite bathrooms", "Powder room"]
      },
      "image_url": "https://storage.googleapis.com/.../floor_plan_2br.webp",
      "is_duplicate": false,
      "quality_score": 0.92
    }
  ]
}
```

---

## Services

### PDFProcessor

**Purpose:** Triple extraction from PDF files (embedded images, page renders, per-page text)

**Location:** `backend/app/services/pdf_processor.py`

**Key Methods:**
```python
class PDFProcessor:
    def __init__(self, render_dpi: int = 300, max_pages: int = 100): ...

    async def extract_all(self, pdf_bytes: bytes) -> ExtractionResult:
        """Triple extraction: embedded XObjects + 300 DPI page renders + pymupdf4llm text.
        Returns ExtractionResult with embedded, page_renders, page_text_map, total_pages, errors."""

    def _extract_text(self, pdf_bytes: bytes, total_pages: int) -> dict[int, str]:
        """Per-page markdown text via pymupdf4llm (1-indexed page numbers)."""

    def get_extraction_summary(self, result: ExtractionResult) -> dict:
        """Build summary dict for extraction result."""
```

---

### ImageClassifier

**Purpose:** Classify images using Claude Sonnet 4.5 vision

**Location:** `backend/app/services/image_classifier.py`

**Key Methods:**
```python
class ImageClassifier:
    async def classify_image(self, image_bytes: bytes) -> ClassificationResult:
        """
        Classify image into category using Claude Sonnet 4.5 vision

        Returns:
            ClassificationResult with:
            - category: str ('interior', 'exterior', 'amenity', 'logo', 'other')
            - confidence: float (0.0 to 1.0)
            - reasoning: str (explanation of classification)
        """

    async def classify_batch(self, images: List[bytes]) -> List[ClassificationResult]:
        """Classify multiple images in parallel"""

    async def generate_alt_text(self, image_bytes: bytes) -> str:
        """Generate SEO-optimized alt text for image"""
```

---

### WatermarkDetector

**Purpose:** Detect watermarks using Claude Sonnet 4.5 vision

**Location:** `backend/app/services/watermark_detector.py`

**Key Methods:**
```python
class WatermarkDetector:
    async def detect_watermark(self, image_bytes: bytes) -> WatermarkResult:
        """
        Detect watermark presence and location

        Returns:
            WatermarkResult with:
            - has_watermark: bool
            - bounding_box: dict {"x": int, "y": int, "width": int, "height": int}
            - confidence: float
        """

    async def detect_batch(self, images: List[bytes]) -> List[WatermarkResult]:
        """Detect watermarks in multiple images"""
```

---

### WatermarkRemover

**Purpose:** Remove watermarks using OpenCV inpainting

**Location:** `backend/app/services/watermark_remover.py`

**Key Methods:**
```python
class WatermarkRemover:
    async def remove_watermark(
        self,
        image_bytes: bytes,
        bounding_box: dict
    ) -> RemovalResult:
        """
        Remove watermark using OpenCV inpainting

        Args:
            image_bytes: Original image
            bounding_box: {"x": int, "y": int, "width": int, "height": int}

        Returns:
            RemovalResult with:
            - processed_image: bytes
            - quality_score: float (0.0 to 1.0)
            - success: bool
        """

    def _create_mask(self, image: np.ndarray, bbox: dict) -> np.ndarray:
        """Create binary mask for inpainting"""

    def _apply_inpainting(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Apply cv2.inpaint algorithm"""
```

---

### FloorPlanExtractor

**Purpose:** Extract floor plans and parse data using Claude Sonnet 4.5 vision

**Location:** `backend/app/services/floor_plan_extractor.py`

**Key Methods:**
```python
class FloorPlanExtractor:
    async def extract_floor_plan_data(self, image_bytes: bytes) -> FloorPlanData:
        """
        Extract structured data from floor plan image

        Returns:
            FloorPlanData with:
            - unit_type: str
            - bedrooms: int
            - bathrooms: float
            - unit_size_sqft: float
            - dimensions: dict (room dimensions)
            - features: List[str]
            - confidence: float
        """

    async def is_floor_plan(self, image_bytes: bytes) -> bool:
        """Determine if image is a floor plan"""

    async def extract_batch(self, images: List[bytes]) -> List[FloorPlanData]:
        """Process multiple floor plans"""
```

---

### DeduplicationService

**Purpose:** Remove duplicate floor plans

**Location:** `backend/app/services/deduplication_service.py`

**Key Methods:**
```python
class DeduplicationService:
    def calculate_perceptual_hash(self, image_bytes: bytes) -> str:
        """Calculate perceptual hash using imagehash library"""

    def find_duplicates(
        self,
        floor_plans: List[FloorPlan],
        similarity_threshold: float = 0.95
    ) -> List[DuplicateGroup]:
        """
        Find duplicate floor plans based on perceptual hash

        Returns groups of duplicates with quality scores
        """

    def select_best_version(self, duplicates: List[FloorPlan]) -> FloorPlan:
        """Select highest quality version from duplicate group"""
```

---

### ImageOptimizer

**Purpose:** Resize, compress, and convert image formats

**Location:** `backend/app/services/image_optimizer.py`

**Key Methods:**
```python
class ImageOptimizer:
    async def optimize_image(
        self,
        image_bytes: bytes,
        target_format: str = 'webp',
        tier: str = 'tier1'
    ) -> OptimizedImage:
        """
        Optimize image for delivery (dual-tier output)

        Tier 1 (Original/Archive):
        - Resize to max 2450x1400px (maintain aspect ratio)
        - Set DPI to 300
        - No file size limit (quality preserved)
        - Convert to target format (webp or jpg)

        Tier 2 (LLM-Optimized):
        - Resize to task-specific dimensions (1024-1568px)
        - Optimize for Claude vision processing
        - Target ~200-400KB for token efficiency
        """

    async def optimize_batch(
        self,
        images: List[bytes]
    ) -> List[OptimizedImage]:
        """Optimize multiple images in parallel"""

    def _resize_image(self, img: Image, max_width: int, max_height: int) -> Image:
        """Resize while maintaining aspect ratio"""

    def _compress_to_target_size(
        self,
        img: Image,
        format: str,
        max_size_bytes: int
    ) -> bytes:
        """Iteratively compress until under target size"""
```

---

### OutputOrganizer

**Purpose:** Package processed assets into ZIP file

**Location:** `backend/app/services/output_organizer.py`

**Key Methods:**
```python
class OutputOrganizer:
    async def create_asset_package(
        self,
        project_id: UUID,
        images: List[ProcessedImage],
        floor_plans: List[FloorPlan]
    ) -> PackageResult:
        """
        Create organized ZIP package

        Structure:
        /interiors/
            interior_01.webp
            interior_01.jpg
        /exteriors/
        /amenities/
        /logos/
        /floor_plans/
        manifest.json
        """

    def _generate_manifest(
        self,
        images: List[ProcessedImage],
        floor_plans: List[FloorPlan]
    ) -> dict:
        """Generate JSON manifest with all metadata"""

    async def upload_to_gcs(self, zip_bytes: bytes, project_id: UUID) -> str:
        """Upload ZIP to Google Cloud Storage"""

    async def upload_to_drive(
        self,
        zip_bytes: bytes,
        project_name: str
    ) -> str:
        """Create Google Drive folder and upload assets"""
```

---

## Workflow Diagrams

### Material Preparation Pipeline

```
┌──────────────────────┐
│    PDF UPLOAD        │
│  (via frontend)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  1. IMAGE EXTRACTION (PyMuPDF)           │
│  ─────────────────────────────────────   │
│  • Open PDF with fitz                    │
│  • Iterate through all pages             │
│  • Extract embedded images               │
│  • Save raw images temporarily           │
│                                          │
│  Output: 45 raw images                   │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  2. IMAGE CLASSIFICATION (Claude Sonnet 4.5)        │
│  ─────────────────────────────────────   │
│  • Send each image to Claude Sonnet 4.5 Vision      │
│  • Classify into 5 categories            │
│  • Extract confidence scores             │
│  • Generate alt text                     │
│                                          │
│  Results:                                │
│  - Interior: 15 images (conf: 0.85-0.95) │
│  - Exterior: 12 images (conf: 0.80-0.92) │
│  - Amenity: 8 images (conf: 0.75-0.90)   │
│  - Logo: 4 images (conf: 0.90-0.98)      │
│  - Other: 6 images (DISCARDED)           │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  3. APPLY CATEGORY LIMITS                │
│  ─────────────────────────────────────   │
│  • Interior: Keep top 10 by confidence   │
│  • Exterior: Keep top 10 by confidence   │
│  • Amenity: Keep top 5 by confidence     │
│  • Logo: Keep top 3 by confidence        │
│                                          │
│  Kept: 28 images                         │
│  Discarded: 11 low-confidence images     │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  4. WATERMARK DETECTION (Claude Sonnet 4.5)         │
│  ─────────────────────────────────────   │
│  • Analyze each image for watermarks     │
│  • Extract bounding box coordinates      │
│  • Store coordinates in metadata         │
│                                          │
│  Detected: 12 images with watermarks     │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  5. WATERMARK REMOVAL (OpenCV)           │
│  ─────────────────────────────────────   │
│  • Create binary mask from bounding box  │
│  • Apply cv2.inpaint() algorithm         │
│  • Validate removal quality              │
│  • Fallback to original if poor quality  │
│                                          │
│  Successfully removed: 10 watermarks     │
│  Kept original: 2 (poor removal quality) │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  6. FLOOR PLAN EXTRACTION (Claude Sonnet 4.5)       │
│  ─────────────────────────────────────   │
│  • Identify floor plan images            │
│  • Extract unit type, beds, baths        │
│  • Parse room dimensions                 │
│  • Extract features (balcony, maid, etc) │
│  • Store structured JSONB data           │
│                                          │
│  Extracted: 6 floor plans                │
│  Data completeness: 92%                  │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  7. FLOOR PLAN DEDUPLICATION             │
│  ─────────────────────────────────────   │
│  • Calculate perceptual hash             │
│  • Compare similarity (threshold: 95%)   │
│  • Group duplicates by unit type         │
│  • Keep highest quality version          │
│                                          │
│  Input: 6 floor plans                    │
│  Output: 4 unique floor plans            │
│  Marked as duplicate: 2                  │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  8. IMAGE OPTIMIZATION (Dual-Tier)       │
│  ─────────────────────────────────────   │
│  Tier 1 (Original/Archive):              │
│  • Resize to max 2450x1400px             │
│  • Set DPI to 300                        │
│  • WebP 85% + JPG 90% (no size limit)    │
│                                          │
│  Tier 2 (LLM-Optimized):                 │
│  • Task-specific dimensions (1024-1568px)│
│  • JPEG 80-85% or PNG for floor plans    │
│  • Target ~200-400KB for token savings   │
│                                          │
│  Output:                                 │
│  - 28 images × 2 tiers × 2 formats       │
│  - 4 floor plans × 2 tiers × 2 formats   │
│  Total: Tier 1 + Tier 2 in final package │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  9. ZIP PACKAGE CREATION                 │
│  ─────────────────────────────────────   │
│  • Organize into folders:                │
│    /interiors/ (10 × 2 formats)          │
│    /exteriors/ (10 × 2 formats)          │
│    /amenities/ (5 × 2 formats)           │
│    /logos/ (3 × 2 formats)               │
│    /floor_plans/ (4 × 2 formats)         │
│  • Generate manifest.json                │
│  • Create ZIP archive                    │
│                                          │
│  Package size: 8.5 MB                    │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  10. CLOUD UPLOAD                        │
│  ─────────────────────────────────────   │
│  • Upload ZIP to GCS bucket              │
│  • Upload individual files to GCS        │
│  • Create Google Drive folder            │
│  • Upload to Drive for client access     │
│  • Store URLs in database                │
│                                          │
│  ✅ Complete: All assets ready           │
└──────────────────────────────────────────┘
```

---

## Code Examples

### Backend: Material Preparation Service

```python
# backend/app/services/material_preparation_service.py
from typing import List, Dict
from uuid import UUID
import asyncio
from app.services.pdf_processor import PDFProcessor
from app.services.image_classifier import ImageClassifier
from app.services.watermark_detector import WatermarkDetector
from app.services.watermark_remover import WatermarkRemover
from app.services.floor_plan_extractor import FloorPlanExtractor
from app.services.deduplication_service import DeduplicationService
from app.services.image_optimizer import ImageOptimizer
from app.services.output_organizer import OutputOrganizer
from app.models.processing_job import ProcessingJob

class MaterialPreparationService:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.image_classifier = ImageClassifier()
        self.watermark_detector = WatermarkDetector()
        self.watermark_remover = WatermarkRemover()
        self.floor_plan_extractor = FloorPlanExtractor()
        self.deduplication_service = DeduplicationService()
        self.image_optimizer = ImageOptimizer()
        self.output_organizer = OutputOrganizer()

    async def process_materials(
        self,
        job_id: UUID,
        project_id: UUID,
        pdf_gcs_path: str
    ) -> Dict:
        """
        Complete material preparation pipeline
        """
        job = await self._get_job(job_id)

        try:
            # Step 1: Extract images from PDF
            await self._update_job_progress(job, 1, "Extracting images from PDF")
            raw_images = await self.pdf_processor.extract_images(pdf_gcs_path)
            job.images_extracted = len(raw_images)
            await self._save_job(job)

            # Step 2: Classify images
            await self._update_job_progress(job, 2, "Classifying images")
            classifications = await self.image_classifier.classify_batch(raw_images)
            job.images_classified = len(classifications)
            await self._save_job(job)

            # Step 3: Apply category limits
            await self._update_job_progress(job, 3, "Applying category limits")
            filtered_images = self._apply_category_limits(
                raw_images,
                classifications,
                limits={
                    'interior': 10,
                    'exterior': 10,
                    'amenity': 5,
                    'logo': 3
                }
            )

            # Step 4: Detect watermarks
            await self._update_job_progress(job, 4, "Detecting watermarks")
            watermark_results = await self.watermark_detector.detect_batch(
                [img.bytes for img in filtered_images]
            )

            # Step 5: Remove watermarks
            await self._update_job_progress(job, 5, "Removing watermarks")
            for img, wm_result in zip(filtered_images, watermark_results):
                if wm_result.has_watermark:
                    removal_result = await self.watermark_remover.remove_watermark(
                        img.bytes,
                        wm_result.bounding_box
                    )
                    if removal_result.success:
                        img.bytes = removal_result.processed_image
                        job.watermarks_removed += 1

            await self._save_job(job)

            # Step 6: Extract floor plans
            await self._update_job_progress(job, 6, "Extracting floor plan data")
            floor_plans = []
            for img in filtered_images:
                if await self.floor_plan_extractor.is_floor_plan(img.bytes):
                    fp_data = await self.floor_plan_extractor.extract_floor_plan_data(
                        img.bytes
                    )
                    floor_plans.append(fp_data)
                    # Remove from general images
                    filtered_images.remove(img)

            job.floor_plans_extracted = len(floor_plans)
            await self._save_job(job)

            # Step 7: Deduplicate floor plans
            await self._update_job_progress(job, 7, "Deduplicating floor plans")
            unique_floor_plans = self.deduplication_service.find_duplicates(
                floor_plans,
                similarity_threshold=0.95
            )
            job.floor_plans_deduplicated = len(unique_floor_plans)
            await self._save_job(job)

            # Step 8: Optimize images
            await self._update_job_progress(job, 8, "Optimizing images")
            optimized_images = await self.image_optimizer.optimize_batch(
                [img.bytes for img in filtered_images]
            )
            optimized_floor_plans = await self.image_optimizer.optimize_batch(
                [fp.bytes for fp in unique_floor_plans]
            )

            # Step 9: Create ZIP package
            await self._update_job_progress(job, 9, "Creating asset package")
            package_result = await self.output_organizer.create_asset_package(
                project_id,
                optimized_images,
                optimized_floor_plans
            )

            # Step 10: Upload to cloud
            zip_url = await self.output_organizer.upload_to_gcs(
                package_result.zip_bytes,
                project_id
            )
            drive_url = await self.output_organizer.upload_to_drive(
                package_result.zip_bytes,
                project_id
            )

            # Complete job
            job.status = 'completed'
            job.output_zip_url = zip_url
            job.google_drive_folder_url = drive_url
            job.completed_steps = 9
            await self._save_job(job)

            return {
                'status': 'completed',
                'zip_url': zip_url,
                'drive_url': drive_url,
                'metrics': {
                    'images_extracted': job.images_extracted,
                    'images_kept': len(filtered_images),
                    'watermarks_removed': job.watermarks_removed,
                    'floor_plans_extracted': job.floor_plans_extracted,
                    'floor_plans_unique': job.floor_plans_deduplicated
                }
            }

        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            await self._save_job(job)
            raise

    def _apply_category_limits(
        self,
        images: List,
        classifications: List,
        limits: Dict[str, int]
    ) -> List:
        """Apply category limits, keeping highest confidence images"""
        categorized = {}
        for img, classification in zip(images, classifications):
            category = classification.category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append((img, classification.confidence))

        # Sort by confidence and apply limits
        filtered = []
        for category, limit in limits.items():
            if category in categorized:
                # Sort by confidence descending
                sorted_imgs = sorted(
                    categorized[category],
                    key=lambda x: x[1],
                    reverse=True
                )
                # Keep top N
                filtered.extend([img for img, _ in sorted_imgs[:limit]])

        return filtered

    async def _update_job_progress(
        self,
        job: ProcessingJob,
        step: int,
        description: str
    ):
        """Update job progress"""
        job.completed_steps = step
        job.current_step = description
        await self._save_job(job)
```

---

### Frontend: Material Preparation Monitor

```typescript
// frontend/src/components/MaterialPreparationMonitor.tsx
import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { jobsApi } from '@/lib/api';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, Loader2, XCircle } from 'lucide-react';

interface MaterialPreparationMonitorProps {
  jobId: string;
}

export function MaterialPreparationMonitor({ jobId }: MaterialPreparationMonitorProps) {
  const { data: job, isLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getStatus(jobId),
    refetchInterval: job?.status === 'processing' ? 2000 : false
  });

  if (isLoading) {
    return <div>Loading job status...</div>;
  }

  const progress = (job.completed_steps / job.total_steps) * 100;

  const steps = [
    'Extracting images from PDF',
    'Classifying images',
    'Applying category limits',
    'Detecting watermarks',
    'Removing watermarks',
    'Extracting floor plan data',
    'Deduplicating floor plans',
    'Optimizing images',
    'Creating asset package',
    'Uploading to cloud'
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Material Preparation</h2>
        <p className="text-gray-600">Processing visual assets from PDF</p>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Progress</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <Progress value={progress} />
      </div>

      <div className="space-y-2">
        <h3 className="font-semibold">Processing Steps</h3>
        {steps.map((step, index) => (
          <div key={index} className="flex items-center gap-2">
            {index < job.completed_steps ? (
              <CheckCircle className="text-green-500" size={20} />
            ) : index === job.completed_steps ? (
              <Loader2 className="text-blue-500 animate-spin" size={20} />
            ) : (
              <div className="w-5 h-5 border-2 border-gray-300 rounded-full" />
            )}
            <span className={index <= job.completed_steps ? 'font-medium' : 'text-gray-500'}>
              {step}
            </span>
          </div>
        ))}
      </div>

      {job.status === 'completed' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-2">Processing Complete</h3>
          <div className="space-y-1 text-sm text-green-800">
            <p>Images extracted: {job.metrics.images_extracted}</p>
            <p>Images kept: {job.metrics.images_classified}</p>
            <p>Watermarks removed: {job.metrics.watermarks_removed}</p>
            <p>Floor plans: {job.metrics.floor_plans_extracted}</p>
          </div>
          <div className="mt-4 space-x-2">
            <a
              href={job.output.zip_download_url}
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Download ZIP
            </a>
            <a
              href={job.output.google_drive_folder_url}
              className="inline-block px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Open in Google Drive
            </a>
          </div>
        </div>
      )}

      {job.status === 'failed' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-900 mb-2">
            <XCircle size={20} />
            <h3 className="font-semibold">Processing Failed</h3>
          </div>
          <p className="text-sm text-red-800">{job.error_message}</p>
        </div>
      )}
    </div>
  );
}
```

---

## Configuration

### Environment Variables

```bash
# ============================================
# PDF Processing
# ============================================
ENABLE_PDF_IMAGE_EXTRACTION=true
MAX_PDF_SIZE_MB=50
PDF_DPI=300

# ============================================
# AI/Vision (Anthropic Claude Sonnet 4.5)
# ============================================
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TIMEOUT=120
IMAGE_CLASSIFICATION_TEMPERATURE=0.3

# ============================================
# Category Limits
# ============================================
MAX_INTERIOR_IMAGES=10
MAX_EXTERIOR_IMAGES=10
MAX_AMENITY_IMAGES=5
MAX_LOGO_IMAGES=3

# ============================================
# TIER 1: Original/Archive Images (Output)
# ============================================
MAX_IMAGE_WIDTH_PX=2450
MAX_IMAGE_HEIGHT_PX=1400
OUTPUT_DPI=300
WEBP_QUALITY=85
JPG_QUALITY=90
# NOTE: No file size limit - quality preserved

# ============================================
# TIER 2: LLM-Optimized Images (Processing)
# ============================================
LLM_MAX_DIMENSION=1568                # Anthropic recommended max
LLM_CLASSIFICATION_MAX_DIM=1024       # Lower res sufficient for classification
LLM_WATERMARK_MAX_DIM=1280            # Need detail for bounding boxes
LLM_FLOOR_PLAN_MAX_DIM=1568           # Max for OCR accuracy
LLM_JPEG_QUALITY=85                   # Balance quality vs tokens
LLM_USE_PNG_FOR_FLOOR_PLANS=true      # Lossless for text clarity

# ============================================
# Extraction Strategy
# ============================================
PAGE_RENDER_DPI=300                   # ALL page rendering (consistent quality)
MIN_EMBEDDED_IMAGE_WIDTH=500          # Reject tiny embedded images
ENABLE_TRIPLE_EXTRACTION=true         # Extract embedded + page renders + text (pymupdf4llm)

# ============================================
# Quality Validation
# ============================================
ENABLE_AUTO_ENHANCE=false             # Experimental Pillow enhancement
MIN_CLASSIFICATION_WIDTH=800
MIN_CLASSIFICATION_HEIGHT=600
MIN_FLOOR_PLAN_WIDTH=1200
MIN_FLOOR_PLAN_HEIGHT=900

# ============================================
# Watermark Removal
# ============================================
ENABLE_WATERMARK_REMOVAL=true
WATERMARK_DETECTION_CONFIDENCE_THRESHOLD=0.7
INPAINT_RADIUS=5
INPAINT_METHOD=TELEA  # or NS

# ============================================
# Floor Plan Processing
# ============================================
ENABLE_FLOOR_PLAN_DEDUPLICATION=true
FLOOR_PLAN_SIMILARITY_THRESHOLD=0.95
FLOOR_PLAN_DATA_SOURCE_OF_TRUTH=image  # image or text
FLOOR_PLAN_TEXT_FALLBACK_ENABLED=true
FLOOR_PLAN_TEXT_VERIFICATION_REQUIRED=true

# ============================================
# Storage
# ============================================
GCS_BUCKET_NAME=pdp-automation-assets-dev
GCS_ASSETS_PREFIX=projects/
GOOGLE_DRIVE_ROOT_FOLDER_ID=...

# ============================================
# Performance
# ============================================
ENABLE_PARALLEL_PROCESSING=true
MAX_CONCURRENT_IMAGE_PROCESSING=5
PROCESSING_TIMEOUT_MINUTES=15
```

### Feature Flags

```python
# backend/app/config.py
class MaterialPreparationSettings(BaseSettings):
    # Processing Features
    enable_watermark_removal: bool = True
    enable_floor_plan_deduplication: bool = True
    enable_parallel_processing: bool = True
    enable_triple_extraction: bool = True  # Embedded + page render + text

    # Category Limits
    category_limits: dict = {
        'interior': 10,
        'exterior': 10,
        'amenity': 5,
        'logo': 3
    }

    # Tier 1: Original Image Quality
    output_formats: list = ['webp', 'jpg']
    target_dpi: int = 300
    max_width_px: int = 2450
    max_height_px: int = 1400
    # NOTE: No max_image_size - quality preserved

    # Tier 2: LLM Optimization Settings
    llm_optimization: dict = {
        'classification': {'max_dim': 1024, 'format': 'jpeg', 'quality': 80},
        'watermark_detection': {'max_dim': 1280, 'format': 'jpeg', 'quality': 85},
        'floor_plan_ocr': {'max_dim': 1568, 'format': 'png', 'quality': None},
        'alt_text': {'max_dim': 1024, 'format': 'jpeg', 'quality': 80}
    }

    # AI Configuration
    classification_model: str = 'claude-sonnet-4-5-20250929'
    classification_temperature: float = 0.3
    watermark_confidence_threshold: float = 0.7

    # Floor Plan Data Extraction
    floor_plan_source_of_truth: str = 'image'  # image is primary
    floor_plan_text_fallback: bool = True      # fallback to text if image lacks data
    floor_plan_text_verification: bool = True  # must verify text refers to floor plan

    # Quality Validation
    enable_auto_enhance: bool = False  # Experimental
    min_classification_dims: tuple = (800, 600)
    min_floor_plan_dims: tuple = (1200, 900)

    # Performance
    max_concurrent_jobs: int = 3
    processing_timeout_minutes: int = 15
```

---

## Related Documentation

### Core Documentation
- [Architecture > Processing Pipeline](../01-architecture/PROCESSING_PIPELINE.md) - Overall system flow
- [Architecture > Cloud Storage](../01-architecture/CLOUD_STORAGE.md) - GCS and Drive integration
- [Modules > Project Database](./PROJECT_DATABASE.md) - Image metadata storage

### Integration Points
- [Integrations > Anthropic API](../05-integrations/ANTHROPIC_API_INTEGRATION.md) - Claude Sonnet 4.5 vision API usage
- [Integrations > Google Cloud Storage](../05-integrations/GOOGLE_CLOUD_STORAGE.md) - Asset storage
- [Integrations > Google Drive](../05-integrations/GOOGLE_DRIVE.md) - Client file sharing

### Backend Services
- [Backend > Services](../04-backend/SERVICES.md) - Service implementation details
- [Backend > Image Processing](../04-backend/IMAGE_PROCESSING.md) - OpenCV and PIL usage

### Testing
- [Testing > Integration Tests](../07-testing/INTEGRATION_TESTS.md) - Pipeline testing
- [Testing > AI Testing](../07-testing/AI_TESTING.md) - Claude Sonnet 4.5 vision validation

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Backend Team
**Contact:** backend-team@your-domain.com
