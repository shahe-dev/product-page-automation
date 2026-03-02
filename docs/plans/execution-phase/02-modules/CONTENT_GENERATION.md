# Module: Content Generation

**Module Number:** 2
**Category:** AI Content Creation
**Last Updated:** 2026-01-15
**Status:** Core Module

---

## Table of Contents

1. [Overview](#overview)
2. [Purpose & Goals](#purpose--goals)
3. [Key Features](#key-features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [Content Pipeline](#content-pipeline)
7. [API Endpoints](#api-endpoints)
8. [Services](#services)
9. [Workflow Diagrams](#workflow-diagrams)
10. [Code Examples](#code-examples)
11. [Configuration](#configuration)
12. [Related Documentation](#related-documentation)

---

## Overview

The **Content Generation Module** orchestrates the complete text extraction and AI-powered content creation pipeline. It extracts structured data from PDF brochures using pymupdf4llm (cost-free), structures it with Claude Sonnet 4.5, generates SEO-optimized content for multiple website templates, validates quality through QA checkpoints, and pushes final content directly to Google Sheets via API.

**Position in System:** Second parallel processing path running alongside material preparation, handling all text-based content creation.

---

## Purpose & Goals

### Primary Purpose

Transform unstructured PDF brochures into structured, SEO-optimized website content tailored to specific templates (Aggregators, OPR, MPP, ADOP, ADRE, Commercial) with automated quality validation and direct Google Sheets population.

### Goals

1. **Cost Optimization:** Use pymupdf4llm for text extraction (90% cost savings vs Claude Sonnet 4.5 vision)
2. **Accuracy:** Structure extracted data with Claude Sonnet 4.5 according to predefined schemas
3. **SEO Excellence:** Generate template-specific content optimized for search engines
4. **Quality Assurance:** Validate factual accuracy and prompt compliance before publishing
5. **Automation:** Eliminate manual copy-paste by pushing content directly to Google Sheets
6. **Flexibility:** Support multiple website templates with customizable prompts

---

## Key Features

### Core Capabilities

- ✅ **Cost-Free Text Extraction** - pymupdf4llm extracts markdown from PDFs locally
- ✅ **AI Structuring** - Claude Sonnet 4.5 organizes text into JSON schema
- ✅ **Multi-Template Support** - Aggregators, OPR, MPP, ADOP, ADRE, Commercial templates
- ✅ **Field-Level Prompts** - Individual prompts with character limits per field
- ✅ **SEO Optimization** - Meta tags, URL slugs, H1 headings, alt tags
- ✅ **Pre-Generation Review** - Customize prompts before generation
- ✅ **QA Validation** - Automated fact-checking against source PDF
- ✅ **Version Comparison** - Compare with previous versions before regenerating
- ✅ **Direct Sheets Push** - Google Sheets API integration (no manual work)
- ✅ **Content Reuse** - Save and reuse successful content patterns

### Template Types

**Aggregators:**
- 24+ third-party aggregator domains
- Focus: Quick comparisons, key stats, pricing
- Character limits: Concise summaries

**OPR (opr.ae):**
- Off-plan residential projects
- Focus: Developer reputation, location benefits, investment potential
- Character limits: Strict (60 char titles, 160 char descriptions)

**MPP (main-portal.com):**
- the company main site
- Focus: Luxury positioning, developer highlights
- Character limits: Standard

**ADOP (abudhabioffplan.ae):**
- Abu Dhabi off-plan projects
- Focus: Abu Dhabi market specifics, investment potential
- Character limits: Standard

**ADRE (secondary-market-portal.com):**
- Abu Dhabi ready properties
- Focus: Ready-to-move properties, immediate availability
- Character limits: Standard

**Commercial (cre.main-portal.com):**
- Commercial and mixed-use projects
- Focus: Business advantages, ROI, commercial amenities
- Character limits: Moderate

---

## Architecture

### Components Involved

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND LAYER                             │
├─────────────────────────────────────────────────────────┤
│ • ContentGenerationPage.tsx - Template selection       │
│ • PromptCustomizer.tsx      - Pre-gen prompt editing   │
│ • ContentPreview.tsx        - Review before push       │
│ • VersionComparison.tsx     - Compare with previous    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           API LAYER (FastAPI)                           │
├─────────────────────────────────────────────────────────┤
│ • /api/content/extract      - Extract text from PDF    │
│ • /api/content/structure    - Structure to JSON        │
│ • /api/content/generate     - Generate content         │
│ • /api/content/validate     - QA validation            │
│ • /api/content/push-sheets  - Push to Google Sheets    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│            SERVICE LAYER (Python)                       │
├─────────────────────────────────────────────────────────┤
│ • PDFExtractor          - pymupdf4llm text extraction  │
│ • DataStructurer        - Claude Sonnet 4.5 JSON formatting  │
│ • ContentGenerator      - Claude Sonnet 4.5 content creation │
│ • ContentQAService      - Fact-checking validation     │
│ • SheetsManager         - Google Sheets API integration│
│ • PromptManager         - Prompt version management    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│         EXTERNAL INTEGRATIONS                           │
├─────────────────────────────────────────────────────────┤
│ • Anthropic API            - Claude Sonnet 4.5                  │
│ • Google Sheets API     - Direct content push          │
│ • PostgreSQL            - Content storage & versions   │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: `extracted_data`

**Purpose:** Store structured data extracted from PDFs

```sql
CREATE TABLE extracted_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Source Information
    source_pdf_url TEXT NOT NULL,
    extraction_method VARCHAR(50) DEFAULT 'pymupdf4llm',

    -- Raw Extraction
    raw_markdown TEXT,  -- Full markdown from pymupdf4llm
    raw_text TEXT,      -- Plain text fallback

    -- Structured Data (Claude Sonnet 4.5 output)
    structured_data JSONB NOT NULL,
    -- Example structure:
    -- {
    --   "project_name": "Downtown Elite Residence",
    --   "developer": "Emaar Properties",
    --   "location": "Downtown Dubai",
    --   "starting_price": "1,200,000 AED",
    --   "payment_plan": "60/40",
    --   "handover_date": "Q2 2026",
    --   "property_types": ["1BR", "2BR", "3BR", "Penthouse"],
    --   "amenities": ["Infinity Pool", "Gym", "Spa", ...],
    --   "description": "Full project description from PDF..."
    -- }

    -- Quality Metrics
    extraction_quality_score DECIMAL(3, 2),  -- 0.00 to 1.00
    completeness_score DECIMAL(3, 2),        -- % of required fields filled
    confidence_score DECIMAL(3, 2),

    -- Processing Metadata
    extraction_duration_ms INTEGER,
    structuring_duration_ms INTEGER,
    total_tokens_used INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT valid_quality CHECK (extraction_quality_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_extracted_data_project ON extracted_data(project_id);
CREATE INDEX idx_extracted_data_quality ON extracted_data(extraction_quality_score);
```

---

### Table: `generated_content`

**Purpose:** Store AI-generated content for each website template

```sql
CREATE TABLE generated_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    extracted_data_id UUID REFERENCES extracted_data(id),

    -- Template Information
    template_type VARCHAR(50) NOT NULL,  -- 'aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial'
    template_version VARCHAR(20) DEFAULT 'v1',

    -- Generated Content (structured by field)
    content JSONB NOT NULL,
    -- Example:
    -- {
    --   "meta_title": "Downtown Elite Residence | Off-Plan Dubai",
    --   "meta_description": "Luxury residential tower by Emaar...",
    --   "url_slug": "downtown-elite-residence-emaar",
    --   "h1_heading": "Downtown Elite Residence by Emaar Properties",
    --   "overview_paragraph_1": "Discover luxury living...",
    --   "overview_paragraph_2": "Situated in the heart...",
    --   "amenities_intro": "Residents enjoy world-class...",
    --   "location_description": "Downtown Dubai offers...",
    --   "investment_highlights": "This project represents...",
    --   "image_alt_tags": ["Modern lobby", "Infinity pool", ...]
    -- }

    -- Prompt References
    prompts_used JSONB,  -- {"field_name": "prompt_id", ...}

    -- Quality Validation
    qa_status VARCHAR(50) DEFAULT 'pending',
    -- Status: pending, passed, failed, approved_override
    qa_result JSONB,
    -- {
    --   "factual_accuracy": "passed",
    --   "prompt_compliance": "passed",
    --   "character_limits": "passed",
    --   "issues": []
    -- }

    -- Generation Metadata
    generation_duration_ms INTEGER,
    total_tokens_used INTEGER,
    total_cost_usd DECIMAL(10, 4),

    -- Version Control
    version INTEGER DEFAULT 1,
    previous_version_id UUID REFERENCES generated_content(id),
    is_latest BOOLEAN DEFAULT true,

    -- Status
    status VARCHAR(50) DEFAULT 'draft',
    -- Status: draft, validated, approved, published

    -- Google Sheets
    sheet_url TEXT,
    pushed_to_sheet_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT valid_template_type CHECK (template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial'))
);

CREATE INDEX idx_generated_content_project ON generated_content(project_id);
CREATE INDEX idx_generated_content_template_type ON generated_content(template_type);
CREATE INDEX idx_generated_content_status ON generated_content(status);
CREATE INDEX idx_generated_content_latest ON generated_content(is_latest) WHERE is_latest = true;
```

---

### Table: `content_qa_results`

**Purpose:** Store detailed QA validation results

```sql
CREATE TABLE content_qa_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_content_id UUID REFERENCES generated_content(id) ON DELETE CASCADE,

    -- Validation Type
    qa_checkpoint VARCHAR(50) NOT NULL,
    -- Checkpoints: 'factual_accuracy', 'prompt_compliance', 'consistency'

    -- Results
    status VARCHAR(50) NOT NULL,  -- 'passed', 'failed', 'warning'
    issues JSONB DEFAULT '[]',
    -- [
    --   {
    --     "type": "factual_error",
    --     "field": "starting_price",
    --     "message": "Price in content (1.5M) doesn't match PDF (1.2M)",
    --     "severity": "high"
    --   }
    -- ]

    -- Details
    validation_details JSONB,
    -- Full comparison data, LLM reasoning, etc.

    -- Metadata
    validated_by_model VARCHAR(50) DEFAULT 'claude-sonnet-4-5-20241022',
    validation_duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_generated_content FOREIGN KEY (generated_content_id)
        REFERENCES generated_content(id)
);

CREATE INDEX idx_qa_results_content ON content_qa_results(generated_content_id);
CREATE INDEX idx_qa_results_status ON content_qa_results(status);
```

---

## Content Pipeline

### Complete Workflow

```
PDF UPLOAD
    │
    ▼
┌─────────────────────────────────────────────┐
│  1. TEXT EXTRACTION (pymupdf4llm)           │
│  ────────────────────────────────────────   │
│  • Extract text in markdown format         │
│  • Preserve headings, lists, tables        │
│  • Local processing (no API cost)          │
│  • Duration: ~2-5 seconds                   │
│                                             │
│  Output: Markdown-formatted text            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  2. DATA STRUCTURING (Claude Sonnet 4.5)         │
│  ────────────────────────────────────────   │
│  • Send markdown to Claude Sonnet 4.5             │
│  • Provide JSON schema for structure        │
│  • Extract all project fields               │
│  • Parse pricing, dates, amenities          │
│  • Cost: ~$0.01-0.03 per PDF               │
│                                             │
│  Output: Structured JSON data               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  3. QA CHECKPOINT #1: Extraction Quality   │
│  ────────────────────────────────────────   │
│  • Validate completeness (all fields?)      │
│  • Check confidence scores                  │
│  • Flag missing critical fields             │
│                                             │
│  Decision: PASS → Continue                  │
│            FAIL → User review required      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  4. SAVE TO DATABASE                        │
│  ────────────────────────────────────────   │
│  • Insert into extracted_data table         │
│  • Link to project_id                       │
│  • Store quality metrics                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  5. TEMPLATE SELECTION                      │
│  ────────────────────────────────────────   │
│  • User selects template type               │
│  • Load template-specific prompts           │
│  • Display pre-generation prompt editor     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  6. PRE-GENERATION PROMPT CUSTOMIZATION     │
│  ────────────────────────────────────────   │
│  • Show all field prompts to user           │
│  • Allow inline editing                     │
│  • Highlight character limits               │
│  • Save custom prompts (optional)           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  6b. BRAND CONTEXT INJECTION                │
│  ────────────────────────────────────────   │
│  • Load brand-context-prompt.md             │
│  • Prepend to each field prompt             │
│  • Enforces: voice, terminology, language   │
│  • No user intervention required            │
│                                             │
│  Source: reference/company/brand-guidelines/│
│          brand-context-prompt.md            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  7. CONTENT GENERATION (Claude Sonnet 4.5)       │
│  ────────────────────────────────────────   │
│  • Generate content field-by-field          │
│  • Apply character limits                   │
│  • Ensure SEO optimization                  │
│  • Generate URL slug, meta tags, alt tags   │
│  • Brand voice automatically enforced       │
│  • Cost: ~$0.05-0.15 per project           │
│                                             │
│  Output: Complete content package           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  8. QA CHECKPOINT #2: Content Validation   │
│  ────────────────────────────────────────   │
│  • Factual Accuracy Check:                  │
│    - Compare generated vs extracted data    │
│    - Flag contradictions                    │
│    - Verify pricing, dates, developer       │
│                                             │
│  • Prompt Compliance Check:                 │
│    - Character limits met?                  │
│    - Required fields present?               │
│    - Tone and style consistent?             │
│                                             │
│  • Consistency Check:                       │
│    - No internal contradictions?            │
│    - Terminology consistent?                │
│                                             │
│  Decision: PASS → Push to Sheets            │
│            FAIL → Show issues, regenerate   │
│            OVERRIDE → User approves anyway  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  9. CONTENT PREVIEW & APPROVAL              │
│  ────────────────────────────────────────   │
│  • Display generated content to user        │
│  • Show QA results                          │
│  • Allow manual edits                       │
│  • Compare with previous versions           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  10. PUSH TO GOOGLE SHEETS (API)            │
│  ────────────────────────────────────────   │
│  • Authenticate with service account        │
│  • Map content fields to sheet cells        │
│  • Populate all fields via API              │
│  • Validate population success              │
│                                             │
│  Output: Google Sheet URL                   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  11. QA CHECKPOINT #3: Sheet Validation     │
│  ────────────────────────────────────────   │
│  • Read back sheet contents via API         │
│  • Compare with generated content           │
│  • Flag mapping errors                      │
│                                             │
│  ✅ Complete: Content ready for approval    │
└─────────────────────────────────────────────┘
```

---

## API Endpoints

### Extraction & Structuring

#### `POST /api/content/extract`

**Description:** Extract and structure text from PDF

**Request Body:**
```json
{
  "project_id": "uuid",
  "pdf_gcs_path": "gs://bucket/uploads/job-123/original.pdf"
}
```

**Response:**
```json
{
  "extraction_id": "uuid",
  "structured_data": {
    "project_name": "Downtown Elite Residence",
    "developer": "Emaar Properties",
    "location": "Downtown Dubai",
    "starting_price": "1,200,000 AED",
    "payment_plan": "60/40",
    "handover_date": "Q2 2026",
    "property_types": ["1BR", "2BR", "3BR"],
    "amenities": ["Infinity Pool", "Gym", "Spa"],
    "description": "Full description..."
  },
  "quality_metrics": {
    "completeness_score": 0.92,
    "confidence_score": 0.88,
    "missing_fields": ["total_units"]
  },
  "processing_time_ms": 3450,
  "tokens_used": 4500
}
```

---

#### `POST /api/content/generate`

**Description:** Generate SEO content for selected template

**Request Body:**
```json
{
  "extraction_id": "uuid",
  "template_type": "opr",
  "custom_prompts": {
    "meta_title": "Custom prompt for meta title...",
    "overview": "Custom prompt for overview..."
  }
}
```

**Response:**
```json
{
  "content_id": "uuid",
  "template_type": "opr",
  "content": {
    "meta_title": "Downtown Elite Residence | Off-Plan Dubai",
    "meta_description": "Luxury residential tower by Emaar Properties in Downtown Dubai...",
    "url_slug": "downtown-elite-residence-emaar",
    "h1_heading": "Downtown Elite Residence by Emaar Properties",
    "overview_paragraph_1": "Discover luxury living at its finest...",
    "overview_paragraph_2": "Situated in the heart of Downtown Dubai...",
    "amenities_intro": "Residents enjoy world-class amenities...",
    "location_description": "Downtown Dubai offers unparalleled connectivity...",
    "investment_highlights": "This project represents an exceptional investment...",
    "image_alt_tags": [
      "Modern luxury apartment lobby with marble finishes",
      "Infinity pool overlooking Dubai skyline",
      "State-of-the-art fitness center"
    ]
  },
  "qa_status": "pending",
  "generation_time_ms": 8750,
  "tokens_used": 6200,
  "estimated_cost_usd": 0.093
}
```

---

#### `POST /api/content/validate`

**Description:** Run QA validation on generated content

**Request Body:**
```json
{
  "content_id": "uuid"
}
```

**Response:**
```json
{
  "qa_status": "passed",
  "validation_results": {
    "factual_accuracy": {
      "status": "passed",
      "checks": 15,
      "issues": []
    },
    "prompt_compliance": {
      "status": "passed",
      "checks": 10,
      "issues": []
    },
    "character_limits": {
      "status": "passed",
      "violations": []
    },
    "consistency": {
      "status": "passed",
      "issues": []
    }
  },
  "overall_score": 0.98,
  "recommendation": "approved_for_publishing"
}
```

---

#### `POST /api/content/push-sheets`

**Description:** Push content to Google Sheets

**Request Body:**
```json
{
  "content_id": "uuid",
  "sheet_template": "opr_template_v2",
  "create_new_sheet": true
}
```

**Response:**
```json
{
  "success": true,
  "sheet_url": "https://docs.google.com/spreadsheets/d/...",
  "cells_populated": 45,
  "validation": {
    "all_fields_mapped": true,
    "errors": []
  },
  "pushed_at": "2025-01-15T10:30:00Z"
}
```

---

### Version Management

#### `GET /api/content/{content_id}/versions`

**Description:** Get version history

**Response:**
```json
{
  "versions": [
    {
      "version": 2,
      "created_at": "2025-01-15T10:30:00Z",
      "created_by": "user@your-domain.com",
      "changes": ["Updated overview", "Regenerated meta description"],
      "is_latest": true
    },
    {
      "version": 1,
      "created_at": "2025-01-15T09:00:00Z",
      "created_by": "user@your-domain.com",
      "is_latest": false
    }
  ]
}
```

---

#### `POST /api/content/{content_id}/compare`

**Description:** Compare two versions

**Request Body:**
```json
{
  "version_a": 1,
  "version_b": 2
}
```

**Response:**
```json
{
  "differences": [
    {
      "field": "overview_paragraph_1",
      "version_a": "Discover luxury living...",
      "version_b": "Experience unparalleled luxury...",
      "change_type": "modified"
    },
    {
      "field": "investment_highlights",
      "version_a": null,
      "version_b": "This project represents...",
      "change_type": "added"
    }
  ]
}
```

---

## Services

### PDFExtractor

**Purpose:** Extract text from PDFs using pymupdf4llm

**Location:** `backend/app/services/pdf_extractor.py`

**Key Methods:**
```python
class PDFExtractor:
    async def extract_text_markdown(self, pdf_path: str) -> str:
        """
        Extract text in markdown format using pymupdf4llm

        Returns formatted markdown preserving:
        - Headings hierarchy
        - Lists (bulleted and numbered)
        - Tables
        - Paragraph structure
        """

    async def extract_text_plain(self, pdf_path: str) -> str:
        """Fallback: plain text extraction"""
```

---

### DataStructurer

**Purpose:** Structure extracted text using Claude Sonnet 4.5

**Location:** `backend/app/services/data_structurer.py`

**Key Methods:**
```python
class DataStructurer:
    async def structure_to_json(
        self,
        markdown_text: str,
        schema: dict
    ) -> StructuredData:
        """
        Convert markdown to structured JSON using Claude Sonnet 4.5

        Args:
            markdown_text: Extracted markdown from PDF
            schema: Target JSON schema

        Returns:
            StructuredData with extracted fields and confidence scores
        """
```

---

### ContentGenerator

**Purpose:** Generate SEO content using Claude Sonnet 4.5 with brand context enforcement

**Location:** `backend/app/services/content_generator.py`

**Key Methods:**
```python
class ContentGenerator:
    def __init__(self):
        # Load brand context on initialization
        self.brand_context = self._load_brand_context()

    def _load_brand_context(self) -> str:
        """
        Load brand context from file for prepending to prompts.
        Source: reference/company/brand-guidelines/brand-context-prompt.md
        """

    async def generate_content(
        self,
        structured_data: dict,
        template_type: str,
        prompts: dict
    ) -> GeneratedContent:
        """
        Generate SEO-optimized content for website template.

        Brand context is automatically prepended to enforce:
        - Advisor voice (not salesperson)
        - Terminology standards (apartment not flat, specific amenity terms)
        - Language prohibitions (no "world-class", "prime location", etc.)
        - Content structure rules

        Generates:
        - Meta title (60 char limit)
        - Meta description (160 char limit)
        - URL slug
        - H1 heading
        - Multiple paragraphs
        - SEO keywords
        - Image alt tags
        """

    async def generate_field(
        self,
        field_name: str,
        prompt: str,
        context: dict,
        char_limit: int = None
    ) -> str:
        """
        Generate single content field with brand context.

        The full prompt sent to Anthropic follows this structure:
        1. Brand context (voice, terminology, prohibitions)
        2. Field-specific prompt (format, char limit, requirements)
        3. Project data context
        """
```

**Brand Context Integration:**

The ContentGenerator automatically prepends brand guidelines to every prompt:

```
[Brand Context - ~400 tokens]
├── Brand voice directive
├── Audience calibration rules
├── Terminology standards
├── Language prohibitions
└── Quality checklist

[Field Prompt - Variable]
├── Specific instructions
├── Character limits
└── Required elements

[Project Data - Variable]
└── Extracted structured data
```

See [Prompt Library > Brand Context Integration](./PROMPT_LIBRARY.md#brand-context-integration) for full details.

---

### ContentQAService

**Purpose:** Validate generated content quality

**Location:** `backend/app/services/content_qa_service.py`

**Key Methods:**
```python
class ContentQAService:
    async def validate_before_push(
        self,
        extracted_data: dict,
        generated_content: dict,
        prompt_spec: dict
    ) -> QAResult:
        """
        Comprehensive QA validation

        Checks:
        1. Factual accuracy (content matches source)
        2. Prompt compliance (character limits, required fields)
        3. Consistency (no contradictions)

        Returns QAResult with pass/fail and detailed issues
        """

    async def check_factual_accuracy(
        self,
        source: dict,
        generated: dict
    ) -> ValidationResult:
        """Compare generated content against source data"""

    async def check_prompt_compliance(
        self,
        content: dict,
        spec: dict
    ) -> ValidationResult:
        """Verify character limits and required fields"""
```

---

### SheetsManager

**Purpose:** Google Sheets API integration

**Location:** `backend/app/services/sheets_manager.py`

**Key Methods:**
```python
class SheetsManager:
    async def push_content_to_sheet(
        self,
        content: dict,
        template: str
    ) -> PushResult:
        """
        Push content to Google Sheet via API

        Steps:
        1. Create new sheet from template (or use existing)
        2. Map content fields to cell addresses
        3. Batch update all cells
        4. Validate population
        5. Return sheet URL
        """

    async def validate_sheet_population(
        self,
        sheet_url: str,
        expected_content: dict
    ) -> ValidationResult:
        """Read back and compare sheet contents"""
```

---

## Code Examples

### Backend: Content Generation Service

```python
# backend/app/services/content_generation_service.py
from typing import Dict
from uuid import UUID
from app.services.pdf_extractor import PDFExtractor
from app.services.data_structurer import DataStructurer
from app.services.content_generator import ContentGenerator
from app.services.content_qa_service import ContentQAService
from app.services.sheets_manager import SheetsManager

class ContentGenerationService:
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.data_structurer = DataStructurer()
        self.content_generator = ContentGenerator()
        self.qa_service = ContentQAService()
        self.sheets_manager = SheetsManager()

    async def process_content(
        self,
        project_id: UUID,
        pdf_path: str,
        website: str,
        custom_prompts: dict = None
    ) -> Dict:
        """Complete content generation pipeline"""

        # Step 1: Extract text (pymupdf4llm - cost-free)
        markdown_text = await self.pdf_extractor.extract_text_markdown(pdf_path)

        # Step 2: Structure to JSON (Claude Sonnet 4.5)
        schema = self._get_extraction_schema()
        structured_data = await self.data_structurer.structure_to_json(
            markdown_text,
            schema
        )

        # Step 3: QA Checkpoint #1 - Extraction quality
        if structured_data.completeness_score < 0.7:
            return {
                'status': 'extraction_failed',
                'message': 'Insufficient data extracted from PDF',
                'missing_fields': structured_data.missing_fields
            }

        # Step 4: Save extracted data
        extraction_id = await self._save_extracted_data(
            project_id,
            structured_data
        )

        # Step 5: Load prompts (custom or default)
        prompts = custom_prompts or await self._get_default_prompts(website)

        # Step 6: Generate content (Claude Sonnet 4.5)
        generated_content = await self.content_generator.generate_content(
            structured_data.data,
            website,
            prompts
        )

        # Step 7: QA Checkpoint #2 - Content validation
        qa_result = await self.qa_service.validate_before_push(
            structured_data.data,
            generated_content.content,
            prompts
        )

        if qa_result.status == 'failed':
            return {
                'status': 'qa_failed',
                'content': generated_content.content,
                'qa_issues': qa_result.issues,
                'recommendation': 'review_and_regenerate'
            }

        # Step 8: Save generated content
        content_id = await self._save_generated_content(
            project_id,
            extraction_id,
            generated_content,
            qa_result
        )

        return {
            'status': 'ready_for_sheets',
            'content_id': content_id,
            'content': generated_content.content,
            'qa_status': qa_result.status,
            'metrics': {
                'extraction_time_ms': structured_data.duration_ms,
                'generation_time_ms': generated_content.duration_ms,
                'total_tokens': structured_data.tokens + generated_content.tokens,
                'total_cost_usd': self._calculate_cost(
                    structured_data.tokens,
                    generated_content.tokens
                )
            }
        }

    async def push_to_sheets(
        self,
        content_id: UUID,
        template: str
    ) -> Dict:
        """Push content to Google Sheets"""

        # Fetch content
        content = await self._get_content(content_id)

        # Push to sheet
        push_result = await self.sheets_manager.push_content_to_sheet(
            content.content,
            template
        )

        # QA Checkpoint #3 - Validate sheet population
        validation = await self.sheets_manager.validate_sheet_population(
            push_result.sheet_url,
            content.content
        )

        # Update content record
        await self._update_content_sheet_info(
            content_id,
            push_result.sheet_url
        )

        return {
            'success': True,
            'sheet_url': push_result.sheet_url,
            'cells_populated': push_result.cells_populated,
            'validation': validation
        }
```

---

## Configuration

### Environment Variables

```bash
# Text Extraction
ENABLE_PYMUPDF4LLM=true
EXTRACTION_TIMEOUT_SECONDS=30

# Anthropic
ANTHROPIC_API_KEY=sk-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20241022
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_MAX_TOKENS=4000

# Templates
DEFAULT_TEMPLATE_TYPE=opr
AVAILABLE_TEMPLATE_TYPES=aggregators,opr,mpp,adop,adre,commercial

# Character Limits (OPR)
OPR_META_TITLE_MAX=60
OPR_META_DESCRIPTION_MAX=160
OPR_H1_MAX=70
OPR_OVERVIEW_MIN=300
OPR_OVERVIEW_MAX=500

# Google Sheets (6 Template IDs)
TEMPLATE_SHEET_ID_AGGREGATORS=YOUR_AGGREGATORS_SHEET_ID
TEMPLATE_SHEET_ID_OPR=YOUR_OPR_SHEET_ID
TEMPLATE_SHEET_ID_MPP=YOUR_MPP_SHEET_ID
TEMPLATE_SHEET_ID_ADOP=YOUR_ADOP_SHEET_ID
TEMPLATE_SHEET_ID_ADRE=YOUR_ADRE_SHEET_ID
TEMPLATE_SHEET_ID_COMMERCIAL=YOUR_COMMERCIAL_SHEET_ID

# QA Thresholds
QA_FACTUAL_ACCURACY_THRESHOLD=0.85
QA_MIN_COMPLETENESS_SCORE=0.70
ENABLE_AUTO_REGENERATE_ON_FAIL=false
```

---

## Related Documentation

### Core Documentation
- [Architecture > AI Pipeline](../01-architecture/AI_PIPELINE.md) - LLM orchestration
- [Modules > Project Database](./PROJECT_DATABASE.md) - Content storage
- [Modules > Prompt Library](./PROMPT_LIBRARY.md) - Prompt management and brand context integration

### Brand Guidelines
- [Brand Content Guidelines](../../reference/company/brand-guidelines/Brand-Content-Guidelines.md) - Full reference document
- [Brand Context Prompt](../../reference/company/brand-guidelines/brand-context-prompt.md) - Condensed version for AI injection

### Integration Points
- [Integrations > Anthropic](../05-integrations/ANTHROPIC_API_INTEGRATION.md) - Claude Sonnet 4.5 API with brand context
- [Integrations > Google Sheets](../05-integrations/GOOGLE_SHEETS_INTEGRATION.md) - Sheets API
- [Modules > QA Module](./QA_MODULE.md) - Quality validation

### Backend Services
- [Backend > Services](../04-backend/SERVICE_LAYER.md) - Service implementation
- [Backend > AI Services](../04-backend/AI_SERVICES.md) - LLM integration

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Backend Team
**Contact:** backend-team@your-domain.com
