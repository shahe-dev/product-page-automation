# System Architecture

**Last Updated:** 2026-01-15
**Related Documents:**
- [Data Flow](./DATA_FLOW.md)
- [API Design](./API_DESIGN.md)
- [Database Schema](./DATABASE_SCHEMA.md)
- [Security Architecture](./SECURITY_ARCHITECTURE.md)
- [Infrastructure](./INFRASTRUCTURE.md)

---

## Table of Contents

1. [Overview](#overview)
2. [System Purpose](#system-purpose)
3. [Target Users](#target-users)
4. [Core Workflow](#core-workflow)
5. [Technology Stack](#technology-stack)
6. [High-Level Architecture](#high-level-architecture)
7. [Key Components](#key-components)
8. [Processing Pipelines](#processing-pipelines)
9. [Design Principles](#design-principles)
10. [Scalability Considerations](#scalability-considerations)
11. [Related Documentation](#related-documentation)

---

## Overview

**PDP Automation v.3** is a Real Estate PDF Automation System that transforms PDF brochures into structured, SEO-optimized content and processed images for property detail pages. The system automates the manual workflow of extracting data from real estate PDF brochures, generating content, and publishing to websites.

This document provides a comprehensive overview of the system architecture, including component interactions, technology choices, and design decisions.

---

## System Purpose

The PDP Automation system serves multiple critical functions:

1. **Automated Data Extraction** - Extracts structured data from unstructured PDF brochures using AI
2. **Content Generation** - Creates SEO-optimized, brand-compliant content for multiple websites
3. **Image Processing** - Classifies, optimizes, and packages images for web publication
4. **Quality Assurance** - Validates accuracy at three critical checkpoints in the workflow
5. **Approval Workflow** - Manages multi-stage review and approval process
6. **Asset Distribution** - Delivers processed content and images to publishing teams

---

## Target Users

The system serves four distinct user departments with different roles and permissions:

### 1. Content Creation Team
**Role:** Initiate processing workflows
**Responsibilities:**
- Upload PDF brochures
- Configure processing parameters (website, template)
- Submit content for approval
- Monitor processing jobs

### 2. Marketing Team
**Role:** Content review and approval
**Responsibilities:**
- Review generated content and images
- Approve or request revisions
- Provide feedback on quality
- Ensure brand compliance

### 3. Publishing Team
**Role:** Publication and asset management
**Responsibilities:**
- Download processed assets (images, content sheets)
- Create property detail pages on websites
- Mark projects as published
- Verify published pages against approved content

### 4. Web Development Team
**Role:** API integration and automation
**Responsibilities:**
- Access project data via REST API
- Integrate assets programmatically
- Build automated publishing workflows
- Monitor API health and performance

---

## Core Workflow

The system follows a parallel processing workflow optimized for speed and efficiency:

```
┌──────────────┐
│  PDF Upload  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│         Parallel Processing Initiated         │
└──────┬───────────────────────┬────────────────┘
       │                       │
       ▼                       ▼
┌──────────────┐      ┌──────────────────┐
│  TEXT PATH   │      │   VISUAL PATH    │
├──────────────┤      ├──────────────────┤
│ 1. Extract   │      │ 1. Extract Images│
│ 2. Organize  │      │ 2. Classify      │
│ 3. Generate  │      │ 3. Floor Plans   │
│ 4. QA Check  │      │ 4. Optimize      │
│ 5. Push Sheet│      │ 5. Package ZIP   │
└──────┬───────┘      └──────┬───────────┘
       │                     │
       └──────────┬──────────┘
                  ▼
       ┌────────────────────┐
       │   QA Validation    │
       │  (3 Checkpoints)   │
       └──────────┬─────────┘
                  ▼
       ┌────────────────────┐
       │  Approval Workflow │
       └──────────┬─────────┘
                  ▼
       ┌────────────────────┐
       │    Publishing      │
       └────────────────────┘
```

### Processing Steps

**Text Path (Sequential):**
1. **Extract** - Use pymupdf4llm to extract text from PDF (FREE)
2. **Organize** - Structure extracted data according to template schema
3. **Generate** - Create SEO-optimized content using Claude Sonnet 4.5
4. **QA Check** - Validate generated content against extracted data
5. **Push to Sheet** - Populate Google Sheet with approved content

**Visual Path (Parallel):**
1. **Extract Images** - Extract all images from PDF using PyMuPDF (FREE)
2. **Classify** - Use Claude Sonnet 4.5 vision to categorize images (interior, exterior, amenity, logo)
3. **Floor Plans** - Detect and extract data from floor plan images using Claude Sonnet 4.5
4. **Optimize** - Compress, resize, and optimize images for web
5. **Package ZIP** - Create organized ZIP archive for download

**QA Checkpoints:**
1. **Extraction QA** - Verify PDF parsing accuracy before content generation
2. **Generation QA** - Ensure generated content matches extracted data
3. **Publication QA** - Compare published page to approved content

---

## Technology Stack

### Frontend

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Framework | React | 19.x | UI component library |
| Build Tool | Vite | 5.x | Fast development server and bundler |
| Language | TypeScript | 5.x | Type-safe JavaScript |
| Styling | Tailwind CSS | 4.x | Utility-first CSS framework |
| UI Components | shadcn/ui | Latest | Pre-built accessible components |
| Server State | React Query | 5.x | Data fetching and caching |
| Client State | Zustand | 4.x | Lightweight state management |
| Routing | React Router | 7.x | Client-side routing |
| Icons | Lucide React | Latest | Modern icon library |

### Backend

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Framework | FastAPI | 0.109+ | High-performance async API |
| Runtime | Python | 3.10+ | Programming language |
| ORM | SQLAlchemy | 2.x | Async database toolkit |
| Migrations | Alembic | 1.x | Database schema migrations |
| Validation | Pydantic | 2.x | Data validation and serialization |
| PDF Processing | PyMuPDF | 1.23+ | PDF text and image extraction |
| Image Processing | Pillow | 10.x | Image manipulation |
| Computer Vision | OpenCV | 4.9+ | Advanced image processing |
| Google APIs | gspread | 6.x | Google Sheets integration |
| | google-cloud-storage | 2.x | Cloud Storage operations |

### Infrastructure

| Category | Service | Configuration | Purpose |
|----------|---------|---------------|---------|
| Compute | Cloud Run | 2GB RAM, 2 CPU (backend) | Serverless container hosting |
| | | 512MB RAM, 1 CPU (frontend) | Auto-scaling web serving |
| Database | Neon PostgreSQL | Serverless, 10GB free tier | Relational data storage |
| Storage | Google Cloud Storage | Standard class, us-central1 | PDF and image storage |
| AI/ML | Anthropic API + pymupdf4llm | Claude Sonnet 4.5 | Vision tasks (text via pymupdf4llm) |
| Auth | Google OAuth | Workspace domain-restricted | User authentication |
| CI/CD | Cloud Build | Automated builds | Deployment pipeline |
| Monitoring | Cloud Monitoring + Sentry | Logs, metrics, errors | Observability |

---

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                       │
│                     React 19 + Vite + TypeScript                │
├────────────────────────────────────────────────────────────────┤
│  HomePage  │  ProcessingPage  │  QAPage  │  PromptsPage  │     │
│  UploadForm │ JobMonitor       │ Compare  │ Editor        │ ... │
└──────────────────────────┬─────────────────────────────────────┘
                           │ HTTPS/REST (JSON)
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                          │
│                   FastAPI + Python 3.10+                        │
├────────────────────────────────────────────────────────────────┤
│                      API ROUTES                                 │
│  /api/auth  │  /api/upload  │  /api/projects  │  /api/qa  │    │
└──────────────────────────┬─────────────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────────────┐
│                       SERVICE LAYER                             │
├────────────────────────────────────────────────────────────────┤
│  AuthService      │  JobManager       │  ProjectService        │
│  PDFProcessor     │  ImageClassifier  │  ContentGenerator      │
│  AnthropicService │  FloorPlanExtract │  ContentQAService      │
│  SheetsManager    │  QAService        │  NotificationService   │
└──────────────────────────┬─────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬─────────────────┐
        │                  │                  │                 │
        ▼                  ▼                  ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐
│     Neon     │  │ Cloud Storage│  │ Anthropic API│  │  Google    │
│  PostgreSQL  │  │     (GCS)    │  │Claude Sonnet │  │  Sheets    │
│              │  │              │  │     4.5      │  │    API     │
└──────────────┘  └──────────────┘  └──────────────┘  └────────────┘
```

---

## Key Components

### 1. Frontend Application (React 19)

**Location:** Cloud Run - `pdp-automation-web`
**Purpose:** User interface for all workflow interactions

**Core Pages:**
- **HomePage** - Project dashboard with search, filters, and Kanban board
- **ProcessingPage** - Upload PDF and configure processing parameters
- **ProjectDetailPage** - View/edit project data with revision history
- **QAPage** - Compare extracted vs. generated content with diff visualization
- **PromptsPage** - Manage version-controlled prompt library
- **WorkflowPage** - Kanban board for approval workflow management

**State Management:**
- **React Query** - Server state (API calls, caching, background refetching)
- **Zustand** - Client state (UI preferences, selected items, filters)

### 2. Backend API (FastAPI)

**Location:** Cloud Run - `pdp-automation-api`
**Purpose:** Core business logic and external service orchestration

**Responsibilities:**
- Handle all HTTP requests from frontend
- Validate and sanitize inputs using Pydantic
- Orchestrate processing workflows via service layer
- Manage authentication and authorization
- Queue background jobs to Cloud Tasks
- Emit notifications and audit logs

**Key Features:**
- **Async/Await** - Non-blocking I/O for high performance
- **OpenAPI Spec** - Auto-generated API documentation
- **CORS Middleware** - Cross-origin request handling
- **Rate Limiting** - Per-user request quotas
- **Request Logging** - Comprehensive audit trail

### 3. Service Layer

**Purpose:** Encapsulate business logic and external service interactions

**Core Services:**

| Service | Responsibility |
|---------|----------------|
| `AuthService` | Google OAuth, JWT tokens, role management |
| `JobManager` | Job lifecycle, progress tracking, error handling |
| `PDFProcessor` | Triple extraction: embedded images + page renders (PyMuPDF), text as markdown (pymupdf4llm) |
| `AnthropicService` | Claude Sonnet 4.5 (text and vision) interactions |
| `ImageClassifier` | Image categorization using Claude Sonnet 4.5 |
| `WatermarkDetector` | Watermark detection using Claude Sonnet 4.5 + OpenCV removal |
| `FloorPlanExtractor` | Floor plan data extraction using Claude Sonnet 4.5 |
| `ImageOptimizer` | Image compression, resizing, format conversion |
| `ContentGenerator` | SEO content generation using Claude Sonnet 4.5 |
| `ContentQAService` | Pre-publish content validation |
| `SheetsManager` | Google Sheets template creation and population |
| `QAService` | Three-checkpoint quality assurance |
| `ProjectService` | CRUD operations, search, revision tracking |
| `PromptService` | Version-controlled prompt management |
| `StorageService` | GCS upload/download/delete operations |
| `NotificationService` | In-app notification creation and delivery |

### 4. Database Layer (Neon PostgreSQL)

**Connection:** Serverless PostgreSQL with connection pooling
**Purpose:** Persistent storage for all application data

**Core Tables:**
- `users` - User accounts (Google OAuth profiles)
- `projects` - Central repository for all project data
- `project_images` - Categorized image references
- `project_floor_plans` - Floor plan data and images
- `project_approvals` - Approval workflow state
- `project_revisions` - Audit trail of field changes
- `jobs` + `job_steps` - Background processing tracking
- `prompts` + `prompt_versions` - Version-controlled prompts
- `qa_comparisons` - QA checkpoint results
- `notifications` - User notifications
- `execution_history` - Complete audit log

### 5. Storage Layer (Google Cloud Storage)

**Bucket:** `gs://pdp-automation-assets-dev`
**Purpose:** Durable storage for binary assets

**Directory Structure:**
```
pdfs/
  {job_id}/original.pdf
images/
  {job_id}/
    original/
      image_001.jpg
    optimized/
      interior_001.jpg
      exterior_001.jpg
floor_plans/
  {job_id}/
    floor_plan_1br.jpg
outputs/
  {job_id}/
    images.zip
```

**Lifecycle Policies:**
- **PDFs:** Delete after 365 days (originals no longer needed)
- **Outputs:** Keep forever (processed assets for publication)

### 6. AI/ML Services (Anthropic API + pymupdf4llm)

**API Endpoint:** `https://api.anthropic.com/v1/messages`

**Models and Tools Used:**

| Model/Tool | Use Cases | Context Window | Cost |
|------------|-----------|----------------|------|
| pymupdf4llm | Text extraction from PDFs | N/A | FREE |
| Claude Sonnet 4.5 | Vision: classification, watermark, floor plans, content gen | 200K tokens | $3/$15 per MTok |

**Why Anthropic + pymupdf4llm Hybrid?**
- 90% cost savings using pymupdf4llm for text extraction (FREE vs API costs)
- Claude Sonnet 4.5 excels at vision tasks and structured output
- Multimodal capabilities (single model for all vision tasks)
- Simple REST API integration
- Extended context window (200K tokens)

### 7. Integration Services

**Google Sheets API:**
- Template-based sheet creation
- Batch content population
- Organization-wide sharing (@your-domain.com)

**Google Drive API:**
- Automatic file sharing with @your-domain.com organization
- ZIP package delivery

**Google OAuth:**
- Workspace domain-restricted authentication
- MFA handled by Google
- Profile photos and names auto-populated

---

## Processing Pipelines

### Text Processing Pipeline

```
┌─────────────┐
│  PDF Upload │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  Extract Text        │
│  (pymupdf4llm)       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Structure Data      │
│  (Claude Sonnet 4.5) │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  QA: Extraction      │
│  (Checkpoint 1)      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Generate Content    │
│  (Claude Sonnet 4.5) │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  QA: Generation      │
│  (Checkpoint 2)      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Push to Sheet       │
│  (Google Sheets API) │
└──────────────────────┘
```

### Visual Processing Pipeline

```
┌─────────────┐
│  PDF Upload │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  Extract Images      │
│  (PyMuPDF)           │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Classify Images     │
│ (Claude Sonnet 4.5)  │
│  Categories:         │
│  - Interior          │
│  - Exterior          │
│  - Amenity           │
│  - Logo              │
│  - Floor Plan        │
└──────┬───────────────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────────┐
│  Standard    │   │  Floor Plans     │
│  Images      │   │                  │
└──────┬───────┘   └──────┬───────────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────────┐
│  Detect      │   │  Extract Data    │
│  Watermarks  │   │ (Claude Sonnet)  │
│ (Claude 4.5) │   │  - Unit type     │
└──────┬───────┘   │  - Bedrooms      │
       │           │  - Area (sqft)   │
       ▼           └──────┬───────────┘
┌──────────────┐          │
│  Remove      │          │
│  Watermarks  │          │
│  (OpenCV)    │          │
└──────┬───────┘          │
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────────┐
│  Optimize    │   │  Optimize        │
│  - Resize    │   │  - Resize        │
│  - Compress  │   │  - Compress      │
│  - Format    │   │  - Format        │
└──────┬───────┘   └──────┬───────────┘
       │                  │
       └────────┬─────────┘
                ▼
     ┌────────────────────┐
     │  Package ZIP       │
     │  - /interior/      │
     │  - /exterior/      │
     │  - /amenity/       │
     │  - /floor_plans/   │
     │  - /logo/          │
     └────────────────────┘
```

---

## Design Principles

### 1. Serverless-First Architecture

**Principle:** Minimize infrastructure management and maximize cost efficiency.

**Implementation:**
- **Cloud Run** for compute (auto-scaling, pay-per-request)
- **Neon PostgreSQL** for database (serverless, scales to zero)
- **Cloud Storage** for object storage (fully managed)
- **Cloud Tasks** for background jobs (managed queue)

**Benefits:**
- No server provisioning or patching
- Automatic scaling based on demand
- Pay only for actual usage
- Built-in redundancy and failover

### 2. Parallel Processing

**Principle:** Maximize throughput by processing text and images concurrently.

**Implementation:**
- Text extraction and image processing run in parallel
- Anthropic API calls batched where possible
- Images classified in batches of 10-20

**Benefits:**
- Reduced processing time (50-70% faster than sequential)
- Better resource utilization
- Improved user experience

### 3. Quality-First with Triple QA

**Principle:** Catch errors early and validate at critical checkpoints.

**Implementation:**
- **Checkpoint 1 (Extraction):** Validate PDF parsing before content generation
- **Checkpoint 2 (Generation):** Compare generated content to extracted data
- **Checkpoint 3 (Publication):** Verify published page matches approved content

**Benefits:**
- Early error detection reduces wasted processing
- Higher accuracy and content quality
- Confidence in published content

### 4. Version-Controlled Prompts

**Principle:** Track prompt changes and enable rollback for consistency.

**Implementation:**
- Prompts stored in database with version history
- Each update creates a new version
- Active version selectable per website/template
- Change reason required for audit trail

**Benefits:**
- Reproducible results
- Easy rollback if quality degrades
- Clear audit trail for compliance

### 5. Domain-Driven Design

**Principle:** Organize code around business domains, not technical layers.

**Implementation:**
- **Auth Domain** - User authentication and authorization
- **Jobs Domain** - Background processing lifecycle
- **Projects Domain** - Project data management
- **Processing Domain** - PDF and image processing
- **QA Domain** - Quality assurance workflows
- **Prompts Domain** - Prompt library management

**Benefits:**
- Clear separation of concerns
- Easier to test and maintain
- Scalable codebase structure

### 6. API-First Development

**Principle:** Design APIs before implementation for consistency.

**Implementation:**
- OpenAPI specification auto-generated by FastAPI
- Frontend and backend developed independently
- API versioning strategy for backwards compatibility
- Comprehensive API documentation

**Benefits:**
- Parallel frontend/backend development
- Clear contracts between layers
- Easy third-party integration

---

## Scalability Considerations

### Current Design Limits

| Resource | Limit | Scaling Strategy |
|----------|-------|------------------|
| PDF size | 50MB | Process in chunks if needed |
| Images per PDF | 500 | Batch processing (groups of 20) |
| Concurrent jobs | 10 per instance | Auto-scale Cloud Run instances |
| Anthropic API rate limit | Tier-dependent | Queue + exponential backoff |
| Google Sheets API | 100 req/100s | Batch operations, use caching |
| Database connections | 100 (pooled) | Connection pooling enabled |

### Growth Path

| Phase | Timeline | Users | Projects/Month | Infrastructure Changes |
|-------|----------|-------|----------------|------------------------|
| **Launch** | Month 1-3 | 10 | 50 | 1 Cloud Run instance (min) |
| **Early Growth** | Month 4-6 | 25 | 150 | 2-3 instances, consider Redis cache |
| **Established** | Month 7-12 | 50 | 300 | Add read replicas, CDN for assets |
| **Scale** | Year 2+ | 100+ | 500+ | Consider GKE, horizontal sharding |

### Horizontal Scaling Strategies

**Compute:**
- Cloud Run auto-scales based on CPU and memory
- Max 10 instances initially (increase as needed)
- Min 1 instance for backend (avoid cold starts)

**Database:**
- Neon PostgreSQL auto-scales storage
- Add read replicas for read-heavy operations
- Consider caching layer (Redis) for hot data

**Storage:**
- GCS scales automatically (no limits)
- Consider CDN (Cloud CDN) for image delivery
- Multi-region replication for disaster recovery

**AI/ML:**
- Anthropic API rate limits scale with usage tier
- Implement request queuing with exponential backoff
- Consider response caching (70-90% savings)

---

## Related Documentation

- [Data Flow](./DATA_FLOW.md) - Detailed data flow through the system
- [API Design](./API_DESIGN.md) - RESTful API specification
- [Database Schema](./DATABASE_SCHEMA.md) - Complete PostgreSQL schema
- [Security Architecture](./SECURITY_ARCHITECTURE.md) - Auth, permissions, data protection
- [Infrastructure](./INFRASTRUCTURE.md) - Google Cloud components and configuration
- [Service Layer](../04-backend/SERVICE_LAYER.md) - Backend service implementation
- [Module Documentation](../02-modules/) - Individual module details

---

**Last Updated:** 2026-01-15
