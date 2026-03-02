PART 1: DOCUMENTATION REPOSITORY STRUCTURE
Documentation Categories
A. DOCUMENTS I WILL CREATE FOR YOU
These will be generated and placed in the new project folder:


docs/
├── 01-architecture/
│   ├── SYSTEM_ARCHITECTURE.md      # Overall system design
│   ├── DATA_FLOW.md                # How data moves through the system
│   ├── API_DESIGN.md               # RESTful API specification
│   ├── DATABASE_SCHEMA.md          # Complete PostgreSQL schema
│   ├── SECURITY_ARCHITECTURE.md    # Auth, permissions, data protection
│   └── INFRASTRUCTURE.md           # Google Cloud components
│
├── 02-modules/
│   ├── PROJECT_DATABASE.md         # Central repository module
│   ├── MATERIAL_PREPARATION.md     # PDF → Images pipeline
│   ├── CONTENT_GENERATION.md       # LLM content creation
│   ├── APPROVAL_WORKFLOW.md        # Marketing approval process
│   ├── PUBLISHING_WORKFLOW.md      # Publisher checklist system
│   ├── QA_MODULE.md                # Quality assurance checkpoints
│   ├── PROMPT_LIBRARY.md           # Version-controlled prompts
│   ├── NOTIFICATIONS.md            # Alert system
│   └── JIRA_INTEGRATION.md         # JIRA webhook handling
│
├── 03-frontend/
│   ├── COMPONENT_LIBRARY.md        # UI component specifications
│   ├── PAGE_SPECIFICATIONS.md      # Every page with wireframes
│   ├── STATE_MANAGEMENT.md         # React Query + Zustand patterns
│   ├── ROUTING.md                  # All routes and guards
│   └── ACCESSIBILITY.md            # WCAG 2.1 AA compliance
│
├── 04-backend/
│   ├── SERVICE_LAYER.md            # All service classes
│   ├── API_ENDPOINTS.md            # OpenAPI specification
│   ├── ERROR_HANDLING.md           # Error codes and responses
│   ├── BACKGROUND_JOBS.md          # Async task processing
│   └── CACHING_STRATEGY.md         # Redis/memory caching
│
├── 05-integrations/
│   ├── GOOGLE_CLOUD_SETUP.md       # Step-by-step GCP configuration
│   ├── VERTEX_AI_INTEGRATION.md    # Gemini API usage patterns
│   ├── GOOGLE_SHEETS_INTEGRATION.md # Sheets API patterns
│   ├── GOOGLE_OAUTH_SETUP.md       # Workspace auth setup
│   ├── JIRA_WEBHOOK_SETUP.md       # JIRA app configuration
│   └── CLOUD_STORAGE_PATTERNS.md   # GCS upload/download patterns
│
├── 06-devops/
│   ├── LOCAL_DEVELOPMENT.md        # Dev environment setup
│   ├── CICD_PIPELINE.md            # Cloud Build configuration
│   ├── DEPLOYMENT_GUIDE.md         # Step-by-step deployment
│   ├── MONITORING_SETUP.md         # Sentry, Cloud Monitoring
│   └── BACKUP_RECOVERY.md          # Disaster recovery plan
│
├── 07-testing/
│   ├── TEST_STRATEGY.md            # Overall testing approach
│   ├── UNIT_TEST_PATTERNS.md       # How to write unit tests
│   ├── INTEGRATION_TESTS.md        # API testing patterns
│   ├── E2E_TEST_SCENARIOS.md       # Playwright test cases
│   └── PERFORMANCE_TESTING.md      # Load testing approach
│
├── 08-user-guides/
│   ├── CONTENT_CREATOR_GUIDE.md    # How to use as content creator
│   ├── MARKETING_MANAGER_GUIDE.md  # Approval workflow guide
│   ├── PUBLISHER_GUIDE.md          # Publishing checklist guide
│   ├── ADMIN_GUIDE.md              # System administration
│   └── DEVELOPER_GUIDE.md          # API integration guide
│
└── 09-reference/
    ├── GLOSSARY.md                 # Terms and definitions
    ├── CHANGELOG.md                # Version history
    ├── TROUBLESHOOTING.md          # Common issues and solutions
    └── FAQ.md                      # Frequently asked questions
B. DOCUMENTS YOU MUST COLLECT
These are external resources I cannot access - you need to gather them:

B.1 GOOGLE CLOUD DOCUMENTATION (Required)
Document	URL	Why Needed
Vertex AI Quickstart	https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform	Understand Gemini API patterns
Gemini API Reference	https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini	Model IDs, parameters, limits
Gemini Vision Guide	https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview	Image understanding specifics
Gemini Pricing	https://cloud.google.com/vertex-ai/generative-ai/pricing	Accurate cost calculations
Cloud Run Docs	https://cloud.google.com/run/docs	Deployment configuration
Cloud SQL Docs	https://cloud.google.com/sql/docs/postgres	PostgreSQL managed service
Cloud Storage Docs	https://cloud.google.com/storage/docs	File storage patterns
Google Sheets API	https://developers.google.com/sheets/api/guides/concepts	Spreadsheet automation
Google OAuth 2.0	https://developers.google.com/identity/protocols/oauth2	Workspace authentication
B.2 JIRA INTEGRATION (Required for Phase 9)
Document	URL	Why Needed
JIRA REST API	https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/	API integration
JIRA Webhooks	https://developer.atlassian.com/cloud/jira/platform/webhooks/	Attachment event handling
JIRA App Development	https://developer.atlassian.com/cloud/jira/platform/getting-started/	OAuth for JIRA
B.3 YOUR COMPANY-SPECIFIC DOCUMENTS (Critical)
Document	Description	Why Needed
Google Sheet Template	Actual template used for OPR/MJL/Palm Jebel Ali	Cell mapping, structure
Brand Guidelines	Tone, voice, terminology for content generation	Prompt engineering
Website Templates	Existing page structures on your websites	Content field mapping
Sample Brochures	3-5 actual PDF brochures from past projects	Testing, extraction patterns
Approval Workflow Doc	Current manual approval process description	Digitize existing workflow
JIRA Project Structure	How JIRA projects/tickets are organized	Webhook filtering logic
User List	Who will use this, their roles, email domains	Permission configuration
MPD Domain Info	@your-domain.com Google Workspace admin access	OAuth domain restriction
B.4 TECHNICAL REFERENCE (Nice to Have)
Document	URL	Why Needed
FastAPI Best Practices	https://fastapi.tiangolo.com/tutorial/	Backend patterns
React Query Docs	https://tanstack.com/query/latest	Data fetching patterns
Tailwind CSS Docs	https://tailwindcss.com/docs	Styling reference
PyMuPDF Docs	https://pymupdf.readthedocs.io/	PDF extraction
OpenCV Python Docs	https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html	Image processing
YOUR DOCUMENT COLLECTION CHECKLIST
Priority 1: Must Have Before Development Starts
 Google Cloud Project created with billing enabled
 Service Account JSON downloaded for Vertex AI + Sheets + Storage
 Google Workspace Admin Access to configure OAuth domain restriction
 At least 1 Google Sheet Template (OPR, MJL, or Palm Jebel Ali)
 3-5 Sample PDF Brochures from actual past projects
 User list with emails and their roles (content, marketing, publishing, admin)
Priority 2: Needed for Module Development
 All Google Sheet Templates (OPR, MJL, Palm Jebel Ali)
 Brand/Tone Guidelines for content generation
 Website page structures showing where content goes
 Current approval workflow documentation (even informal)
 JIRA project/board structure for integration planning
Priority 3: Nice to Have for Polish
 Company logo for the web app branding
 Existing prompts from current Telegram bots (if accessible)
 Sample QA reports from current manual QA process
 Competitor/inspiration web apps you like the UX of
NEXT STEPS
Step 1: Create New Project Folder

mkdir "PDP Automation v.3"
cd "PDP Automation v.3"
Step 2: Create Documentation Structure
I will create all the documentation files in the new folder once you approve this plan.

Step 3: Collect Required Documents
Use the checklist above. Place company-specific documents in:


PDP Automation v.3/
├── reference/
│   ├── google-cloud/           # API docs, pricing PDFs
│   ├── jira/                   # JIRA API docs
│   ├── company/                # Your templates, brochures, guidelines
│   │   ├── sheet-templates/    # Google Sheet templates (exported)
│   │   ├── sample-brochures/   # PDF files for testing
│   │   ├── brand-guidelines/   # Tone, voice, style
│   │   └── workflows/          # Current process descriptions
│   └── technical/              # FastAPI, React, PyMuPDF docs
Step 4: Review & Finalize Documentation
Once I create the docs, we'll review each one for completeness.

Step 5: Begin Implementation
Only after documentation is complete and reviewed.

WHAT I WILL DELIVER
Phase 0: Documentation (Before Any Code)
Deliverables:

40+ documentation files covering every aspect of the system
Complete database schema with all tables, relationships, indexes
API specification with every endpoint documented
Page specifications with UI wireframes in text format
Step-by-step setup guides for all integrations
Test case documents for every module
Format:

All docs in Markdown (GitHub-compatible)
Code examples in every technical doc
Diagrams using ASCII art (portable, no external tools)
Cross-references between related docs
Quality Standards:

Every decision documented with rationale
Every API endpoint with request/response examples
Every database table with sample data
Every UI page with user journey description
PART 2: IMPLEMENTATION PLAN
Executive Summary
Goal: Build a complete 5-module Real Estate PDF Automation System that transforms the current manual workflow into an automated, quality-assured pipeline serving 4 departments.

Current State: ~20-25% implemented (UI scaffolding + partial backend)
Target State: Full production system with all modules + integrations

Estimated Timeline: 100-110 days (~22 weeks) - Revised based on technical review
Estimated Monthly Cost: $273-650/month (Gemini API + Cloud Run + Cloud SQL)

Review Findings (PM + Engineering Audit)
Critical Issues Addressed in This Revision
Issue	Severity	Resolution
Auth too late (was Phase 8)	Critical	Moved to Phase 0.5
Missing Publishing workflow	Critical	Added PublishingModule
Missing Approval UI	Critical	Added ApprovalWorkflow
No observability	Critical	Added monitoring stack
Cost underestimated	High	Corrected budget ($273-650/mo)
Timeline unrealistic	High	Extended to 100+ days
No content preview	High	Added ContentPreviewPage
No notifications	High	Added NotificationService
No testing strategy	High	Added testing phases
No CI/CD	Medium	Added Cloud Build config
Multi-Department Support
Department	Primary Features	Pages Added
Content Creation	Upload, Generate, Preview, Submit	ContentPreviewPage
Marketing Management	Review, Approve/Reject, Dashboard	ApprovalQueuePage, ManagerDashboard
Content Publishing	Download, Checklist, Mark Complete	PublishQueuePage, PublishChecklist
Web Development	API access, Webhooks, Asset CDN	API Docs, Webhook config
User Requirements Summary
From Workflow Document (Mariya's Description)
Old Workflow (Current Pain Points)
Brochure uploaded manually
Images/floor plans/logos extracted via Telegram bot
Text generated by Gemini but must be manually copied to Google Sheets
Image processing in separate workflow with specifications
Manual review by Marketing Manager
Manual page creation in websites (OPR, Aggregators)
Post-publication QA via Telegram bot
New Desired Workflow

PARALLEL PROCESSING:

TEXT PATH:                              VISUAL PATH:
─────────────────────                   ─────────────────────
Brochure Upload                         Brochure Upload
      ↓                                       ↓
Gemini Vision Text Extraction           Image Extraction (specs)
      ↓                                       ↓
QA Checkpoint #1                        Gemini Vision Classification
(extraction accuracy)                         ↓
      ↓                                 Watermark Detection → Removal
Organize into JSON                            ↓
      ↓                                 Floor Plan Extraction
Save to Database                              ↓
      ↓                                 Gemini Vision Data Extraction
Pre-generation Prompts                        ↓
      ↓                                 Deduplication
LLM Text Generation                           ↓
      ↓                                 ZIP Package Output
┌─────────────────────┐
│ QA Checkpoint #2    │  ← CRITICAL GATE
│ - Factual accuracy  │
│ - Prompt compliance │
│ - Character limits  │
│ - Consistency       │
└─────────────────────┘
      ↓
  PASS? ──No──→ User Review → Regenerate
      │
     Yes
      ↓
Google Sheets API Push
      ↓
QA Checkpoint #3
(sheet populated correctly)
      ↓
Marketing Manager Approval
Additional Integration Requirements
Integration	Purpose	Priority
Google Cloud Hosting	Deploy on Cloud Run (serverless, auto-scaling)	Phase 7
Google Workspace Auth	OAuth login restricted to @your-domain.com domain	Phase 7
JIRA	Auto-detect brochures in tickets, create follow-ups	Phase 8
Slack	Marketplace app for notifications	Future
User & Permissions Requirements
Requirement	Implementation
Google OAuth	Login with Google Workspace accounts only
Domain restriction	Only @your-domain.com (or configured domain) can access
Shared visibility	All processed PDFs/projects visible to all users
Persistent history	All uploads, images, outputs saved permanently
Admin-only delete	Only admin role can delete files/projects
User roles	admin (full access), user (view/create only)
5 Core Modules
Module 0: Project Database (Central Hub)
Purpose: Central repository of all processed projects with full CRUD and export

This is the foundation - every processed PDF creates a project record that persists.

Features:

All extracted data stored: Project name, developer, location, pricing, floor plans, property types, amenities, handover dates, payment plans, etc.
Custom fields: Users can add unlimited custom fields per project
Full editing: Any user can correct/update extracted data
Search & filter: Find projects by any field (name, developer, date range, price range, etc.)
Project timeline: Track when processed, who processed, revision history
Export formats: Excel, CSV, PDF reports, JSON (API)
Project Record Schema:


Project:
├── Core Fields (auto-extracted)
│   ├── name, developer, location, emirate
│   ├── starting_price, price_per_sqft
│   ├── handover_date, payment_plan
│   ├── property_types[], unit_sizes[]
│   ├── amenities[], features[]
│   └── total_units, floors, buildings
│
├── Floor Plans (linked)
│   ├── unit_type, bedrooms, sqft
│   ├── living_sqft, balcony_sqft
│   └── image_url, floorplan_pdf_page
│
├── Media (linked)
│   ├── interior_images[], exterior_images[]
│   ├── amenity_images[], logos[]
│   └── original_pdf_url, zip_url
│
├── Generated Content (linked)
│   ├── sheet_url, content_version
│   └── qa_results[], approval_status
│
├── Custom Fields (user-added)
│   └── {key: value} pairs - unlimited
│
└── Metadata
    ├── created_by, created_at
    ├── last_modified_by, last_modified_at
    └── processing_job_id, revision_history[]
UI Components:

ProjectsListPage.tsx - Browse all projects with filters
ProjectDetailPage.tsx - View/edit single project
ProjectExportPage.tsx - Export wizard
CustomFieldsEditor.tsx - Add/edit custom fields
Module 1: Approval & Publishing Workflow (NEW - from PM Review)
Purpose: Formal handoff between Content Creation → Marketing → Publishing

Workflow Stages:


DRAFT → PENDING_APPROVAL → APPROVED → PUBLISHING → PUBLISHED → QA_VERIFIED → COMPLETE
                ↓
           REVISION_REQUESTED (back to Content Creator)
Approval Workflow Features:

Submit for Approval button (Content Creator)
ApprovalQueuePage (Marketing Manager view)
Approve / Request Revision / Reject buttons
Required comments for rejections
Bulk approval for multiple projects
Publishing Workflow Features:

PublishQueuePage (Publisher view)
Per-site checklists (OPR, MJL, Palm Jebel Ali)
Asset download tracking
Mark as published with URL input
Handoff notifications at each stage
Database Additions:


project_approvals (
    id, project_id, status, reviewer_id,
    submitted_at, reviewed_at, comments
)

publication_checklists (
    id, project_id, site_name,
    is_page_created, is_images_uploaded, is_seo_verified,
    published_url, published_by, published_at
)
Module 2: Notifications System (NEW - from PM Review)
Purpose: Keep all departments informed of status changes

Events:

project.created - New project added
project.pending_approval - Ready for marketing review
project.approved - Ready for publishing
project.rejected - Needs revision
qa.failed - QA issues found
deadline.approaching - 24h before deadline
deadline.missed - Overdue projects
Channels:

In-app notifications (required)
Email notifications (optional per user)
Future: Slack integration
Frontend:

Notification bell icon in header
NotificationsPage with history
Mark as read / mark all as read
Module 3: QA Module
Purpose: Multi-stage quality assurance throughout the pipeline

Three QA Checkpoints:

After Text Extraction - Verify extraction accuracy
After Text Generation - Validate generated content quality
After Sheet Population - Confirm correct template filling
Post-Publication QA:

Compare approved Google Sheet against published page URL
Output: Matches, differences, missing info, extra info
Store history for auditing
Module 2: Material Preparation
Purpose: Extract and process all visual assets from PDFs

Features:

Image extraction with category classification (Interior/Exterior/Amenity)
Preset limits: 10 exteriors, 10 interiors, 5 amenities
Logo extraction from first page
Watermark detection and removal (OpenCV inpainting)
Floor plan extraction with Vision LLM data extraction
Floor plan deduplication (1 unit type = 1 floor plan)
Image specs: 300 DPI, max 2450x1400 (Real-ESRGAN deferred to future)
File size: max 500KB per image
Output: WebP + JPG formats, ZIP package
Module 3: Text Generation
Purpose: Generate SEO-optimized content for project pages

Features:

Website selection (OPR, Aggregators - MJL, Palm Jebel Ali)
Template-specific content generation
Field-by-field prompts with character limits
URL slug, SEO metas, image ALT tags, all template fields
Version comparison and reuse
Direct Google Sheets API population (no manual copy/paste)
Templates:

MJL template (for commercial pages)
Palm Jebel Ali template (for others)
Module 4: Prompt Library
Purpose: Centralized, version-controlled prompt management

Features:

Prompts grouped by website and template type
Description and intended use per prompt
Full version control
Change history (who changed what, when)
Pre-generation prompt customization
Technical Architecture
Technology Stack
Layer	Technology
Frontend	React 19 + Vite + TypeScript + Tailwind CSS
Backend	FastAPI + Python 3.10+
Database	PostgreSQL + SQLAlchemy (async)
AI/LLM	Google Vertex AI (Gemini 2.5 Flash) - ALL vision + text tasks
Storage	Google Cloud Storage
Sheets	Google Sheets API + gspread
Image Processing	PyMuPDF (extraction), Pillow (resize/compress), OpenCV (inpainting)
Gemini Model Selection in Vertex AI
Yes, you can select the model in Vertex AI configuration. Available models:

Model ID	Best For	Speed	Cost
gemini-2.5-flash	Most tasks, high-throughput	Fastest	Lower
gemini-2.5-pro	Complex reasoning, highest accuracy	Slower	Higher
gemini-2.5-flash-lite	Simple classification, cost-sensitive	Very Fast	Lowest
Recommended Configuration:


# backend/app/config.py
class Settings:
    # Use the latest, most capable model for each task type
    GEMINI_VISION_MODEL: str = "gemini-2.5-pro"  # For image analysis, extraction
    GEMINI_TEXT_MODEL: str = "gemini-2.5-pro"    # For content generation
    VERTEX_AI_LOCATION: str = "us-central1"       # Check regional availability
Task-to-Model Mapping:

Task	Recommended Model	Why
Image Classification	gemini-2.5-pro	Higher accuracy for categories
Floor Plan Data Extraction	gemini-2.5-pro	Complex data extraction needs best reasoning
Watermark/Logo Detection	gemini-2.5-pro	Precise bounding box detection
Text Extraction from PDF	gemini-2.5-pro	90%+ accuracy on complex documents
Content Generation	gemini-2.5-pro	Best SEO-quality output
QA Comparisons	gemini-2.5-pro	Nuanced difference detection
Non-AI image processing (Pillow/OpenCV):

Watermark removal via OpenCV inpainting (after Gemini detects bbox)
Image resizing/compression to meet 500KB limit
Format conversion (WebP + JPG)
Aspect ratio calculations
Model Updates: Vertex AI automatically provides access to the latest model versions. When Google releases newer models, you simply update the model ID in config.

Sources:

Gemini 2.5 Flash Documentation
Gemini 2.5 Pro Documentation
Image Understanding API
Data Flow Architecture

┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  HomePage │ ProcessingPage │ QAPage │ PromptsPage │ Workflow   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                            │
│  /api/upload │ /api/qa │ /api/prompts │ /api/workflow │ /auth  │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌────────▼───────┐   ┌───────▼───────┐
│ Text Pipeline │   │ Visual Pipeline│   │  QA Service   │
│ - Extraction  │   │ - Image Extract│   │ - Compare     │
│ - Generation  │   │ - Classify     │   │ - Validate    │
│ - Sheets Push │   │ - Floor Plans  │   │ - History     │
└───────┬───────┘   └────────┬───────┘   └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Vertex AI (Gemini)                          │
│     Vision API (classification, extraction, watermark detect)   │
│     Text API (content generation, comparison, QA analysis)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Google Cloud                                │
│         Cloud Storage (PDFs, images) │ Sheets API (output)      │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     PostgreSQL Database                         │
│  Jobs │ Prompts │ Templates │ QA History │ Users │ Workflow    │
└─────────────────────────────────────────────────────────────────┘
Database Schema
Core Tables

-- Users (Google Workspace OAuth)
users (id, google_id, email, name, picture_url, role,
       is_active, created_at, last_login_at)
  -- roles: 'admin' (can delete), 'user' (view/create only)
  -- email must be @your-domain.com domain

-- PROJECTS (Central Database - NEW)
projects (
    id UUID PRIMARY KEY,
    -- Core extracted fields
    name VARCHAR(255) NOT NULL,
    developer VARCHAR(255),
    location VARCHAR(255),
    emirate VARCHAR(100),
    starting_price DECIMAL,
    price_per_sqft DECIMAL,
    handover_date DATE,
    payment_plan TEXT,
    property_types JSONB DEFAULT '[]',  -- ["apartment", "villa", "townhouse"]
    unit_sizes JSONB DEFAULT '[]',       -- [{"type": "1BR", "sqft_min": 500, "sqft_max": 700}]
    amenities JSONB DEFAULT '[]',
    features JSONB DEFAULT '[]',
    total_units INTEGER,
    floors INTEGER,
    buildings INTEGER,
    description TEXT,

    -- Custom fields (user-added, flexible)
    custom_fields JSONB DEFAULT '{}',

    -- Media references
    original_pdf_url VARCHAR(500),
    processed_zip_url VARCHAR(500),

    -- Generated content
    sheet_url VARCHAR(500),
    approval_status VARCHAR(50) DEFAULT 'pending',

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    last_modified_by UUID REFERENCES users(id),
    last_modified_at TIMESTAMP DEFAULT NOW(),
    processing_job_id UUID REFERENCES jobs(id)
)

-- Project floor plans
project_floor_plans (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    unit_type VARCHAR(50),  -- "1BR", "2BR", "Studio", etc.
    bedrooms INTEGER,
    total_sqft DECIMAL,
    living_sqft DECIMAL,
    balcony_sqft DECIMAL,
    image_url VARCHAR(500),
    pdf_page_number INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
)

-- Project images
project_images (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    category VARCHAR(50),  -- "interior", "exterior", "amenity", "logo"
    image_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    alt_text VARCHAR(255),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
)

-- Project revision history (audit trail)
project_revisions (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    change_reason VARCHAR(255)
)

-- Processing jobs
jobs (id, user_id, project_id, status, module, website, template_id,
      input_file_path, output_sheet_url, output_zip_path,
      progress, current_step, extracted_data_json, error_message,
      created_at, completed_at)
  -- Now linked to project_id

-- Job processing steps
job_steps (id, job_id, step_id, label, status, started_at, completed_at)

-- Prompts library with versioning
prompts (id, name, website, template_type, description, content,
         version, is_active, created_by, created_at, updated_at)

prompt_versions (id, prompt_id, version, content, changed_by,
                 change_reason, created_at)

-- Website templates
templates (id, name, website, sheet_template_id, field_mapping_json,
           is_active, created_at)

-- QA comparisons
qa_comparisons (id, job_id, checkpoint_type, input_content,
                comparison_target, result_json, status, created_at)
  -- checkpoint_type: 'extraction', 'generation', 'sheet', 'published'

-- Workflow board
workflow_items (id, job_id, project_name, status, priority,
                assigned_to, notes, created_at, updated_at)
  -- status: 'backlog', 'in_progress', 'qa', 'done'

-- Execution history (audit)
execution_history (id, job_id, user_id, action, details_json, created_at)
Implementation Phases
Phase 0: Prerequisites (Days 1-2)
Goal: Set up Google Cloud infrastructure

Tasks:

Create Google Cloud Project (pdp-automation-prod)
Enable APIs:
Vertex AI API
Google Sheets API
Google Drive API
Cloud Storage API
Create Service Account with roles:
Vertex AI User
Storage Object Admin
Sheets Editor
Download credentials JSON
Create Cloud Storage bucket
Create/configure Google Sheets template
Deliverable: Working credentials, ready to integrate

Phase 1: Core Infrastructure (Days 3-7)
Goal: Fix critical issues, add database, restructure backend

Tasks:

Add missing dependencies to requirements.txt:


sqlalchemy[asyncio], asyncpg, alembic
google-cloud-aiplatform, gspread, google-auth
playwright, beautifulsoup4 (for QA scraping)
Create database models (backend/app/models/db_models.py)

Set up Alembic migrations

Update config.py with comprehensive settings

Fix file upload to actually save files

Fix API response schema (add steps array, fix field names)

Create new route structure:


backend/app/api/routes/
├── upload.py
├── jobs.py
├── qa.py
├── prompts.py
├── templates.py
├── workflow.py
└── auth.py
Deliverable: Working upload + database persistence

Phase 2: Vertex AI Integration (Days 8-12)
Goal: Connect Gemini 2.5 Flash for ALL vision and text processing

Tasks:

Create vertex_ai.py service:


class VertexAIService:
    # Text generation
    async def generate_text(prompt: str) -> str

    # Vision - single image analysis
    async def analyze_image(image_bytes: bytes, prompt: str) -> str

    # Vision - multi-image (PDF pages)
    async def generate_with_images(prompt: str, images: List[bytes]) -> str

    # Vision - bounding box detection (for watermarks)
    async def detect_objects(image_bytes: bytes, target: str) -> List[BBox]
Create image_classifier.py (ALL using Gemini Vision):

Classification: interior/exterior/amenity/floorplan/logo/other
Watermark Detection: Get bounding boxes for removal
Floor Plan Analysis: Extract type, sqft, living sqft, bedrooms
Quality Assessment: Identify blurry/low-res images
Create content_generator.py:

Extract all project info from PDF pages (Vision LLM)
Generate SEO content per template (Text LLM)
Validate against character limits
Deliverable: Working Gemini integration for all AI tasks

Phase 3: Material Preparation Module (Days 13-17)
Goal: Complete image processing pipeline with Gemini Vision

Tasks:

Enhance pdf_processor.py:

Gemini Vision: Classify each extracted image
Gemini Vision: Detect watermark bounding boxes
OpenCV: Remove watermarks via inpainting (non-AI)
Gemini Vision: Extract floor plan data (type, sqft)
Python: Deduplicate floor plans by unit type
Image optimization pipeline (Pillow only, no Real-ESRGAN):

Resize to max dimensions (2450x1400)
Compress iteratively to meet 500KB limit
Export WebP + JPG formats
Gemini can flag low-quality images for manual review
Connect storage_service.py for GCS uploads

Fix output_organizer.py:

Enforce category limits (10 ext, 10 int, 5 amenity)
Proper ZIP packaging with organized folders
Deliverable: PDF → Gemini-Classified Images + Floor Plans + ZIP

Phase 4: Project Database Module (Days 18-24)
Goal: Build the central project repository with CRUD, search, and export

Tasks:

4.1 Project Service:


# backend/app/services/project_service.py
class ProjectService:
    async def create_from_extraction(extracted_data: dict, job_id: str) -> Project
    async def update_project(project_id: str, updates: dict, user: User) -> Project
    async def add_custom_field(project_id: str, key: str, value: any) -> Project
    async def search_projects(filters: ProjectFilters, pagination: Pagination) -> List[Project]
    async def get_project_with_media(project_id: str) -> ProjectDetail
    async def track_revision(project_id: str, field: str, old: any, new: any, user: User)
4.2 Export Service:


# backend/app/services/export_service.py
class ExportService:
    async def export_to_excel(project_ids: List[str], fields: List[str]) -> bytes
    async def export_to_csv(project_ids: List[str], fields: List[str]) -> str
    async def export_to_pdf(project_ids: List[str], template: str) -> bytes
    async def export_to_json(project_ids: List[str]) -> dict
4.3 API Endpoints:


GET    /api/projects              - List with filters/search
GET    /api/projects/{id}         - Get project detail
PUT    /api/projects/{id}         - Update project (any user)
DELETE /api/projects/{id}         - Delete project (admin only)
POST   /api/projects/{id}/fields  - Add custom field
GET    /api/projects/{id}/history - Get revision history
POST   /api/projects/export       - Export selected projects
4.4 Frontend Pages:

ProjectsListPage.tsx - DataTable with search, filters, sorting
ProjectDetailPage.tsx - View/edit all fields, media gallery, history
ProjectExportPage.tsx - Select projects, choose format, download
CustomFieldsEditor.tsx - Add/edit custom field definitions
4.5 Search & Filters:

Full-text search on name, developer, location
Filter by: emirate, developer, price range, date range, property type
Sort by: name, date processed, price, developer
Deliverable: Fully functional project database with export

Phase 5: Text Generation Module (Days 25-29)
Goal: Complete content generation with QA validation before Sheets push

Tasks:

Implement content extraction from PDF (Gemini Vision)

Connect prompt library to generation

Implement template-specific generation:

OPR template
MJL template (commercial)
Palm Jebel Ali template
QA Validation BEFORE Google Sheets Push:


class ContentQAService:
    async def validate_before_push(
        extracted_data: dict,      # Original PDF data
        generated_content: dict,   # LLM output
        prompt_spec: Prompt        # Template requirements
    ) -> QAResult:
        # 1. Factual accuracy check
        #    - Does generated content match PDF source?
        #    - Are prices, dates, locations accurate?

        # 2. Prompt compliance check
        #    - Character limits respected?
        #    - Required fields present?
        #    - Tone/style correct?

        # 3. Consistency check
        #    - No contradictions within content?
        #    - Project name used consistently?

        # 4. Return: PASS/FAIL with issues list
Only push to Sheets if QA passes:

If QA fails → Show issues to user for review
User can approve override or regenerate
All QA results logged for audit
Connect sheets_manager.py (after QA approval):

Create sheet from template
Populate with validated content
Map JSON fields to cells via template config
Deliverable: PDF → Generated Content → QA Validation → Google Sheet

Phase 6: QA Module (Days 30-34)
Goal: Implement all QA checkpoints

Tasks:

Create qa_service.py:


class QAService:
    async def validate_extraction(extracted: dict, pdf_path: str) -> QAResult
    async def validate_generation(generated: dict, extracted: dict) -> QAResult
    async def validate_sheet(sheet_url: str, generated: dict) -> QAResult
    async def compare_published(approved: dict, page_url: str) -> QAResult
Create web_scraper.py for published page scraping

Build QA API endpoints

Build QA frontend pages:

QAPage.tsx (run comparisons)
QAHistoryPage.tsx (view history)
Deliverable: Multi-stage QA system

Phase 7: Prompt Library + Workflow (Days 35-39)
Goal: Complete prompt management and workflow board

Tasks:

Implement prompt_service.py:

CRUD operations
Version control
Change history
Build prompt management UI:

PromptsPage.tsx (list/filter)
PromptEditorPage.tsx (edit with diff)
Implement workflow board:

Kanban columns: Backlog → In Progress → QA → Done
Drag-and-drop movement
Assignment to users
Build WorkflowPage.tsx

Deliverable: Prompt library + workflow board

Phase 8: Google Cloud Deployment + Auth (Days 40-47)
Goal: Deploy to Google Cloud with Workspace authentication

Tasks:

7.1 Google Workspace OAuth Authentication:


# backend/app/services/auth_service.py
class GoogleAuthService:
    # OAuth 2.0 with Google Identity
    async def verify_google_token(token: str) -> GoogleUser
    async def check_domain_restriction(email: str) -> bool  # @your-domain.com only
    async def get_or_create_user(google_user: GoogleUser) -> User
    async def assign_role(user_id: str, role: str)  # admin or user
Configure OAuth consent screen in Google Cloud Console
Restrict to organization domain (@your-domain.com)
Auto-create user on first login
First user or configured email = admin
7.2 Role-Based Permissions:

Action	Admin	User
View all projects	Yes	Yes
Create new project	Yes	Yes
View processing history	Yes	Yes
Download assets	Yes	Yes
Delete projects	Yes	No
Delete files	Yes	No
Manage users	Yes	No
7.3 Persistent Shared Storage:

All PDFs stored in Google Cloud Storage (GCS)
All processed images stored in GCS
All outputs (Sheets, ZIPs) linked in database
Every user sees full project history
Nothing deleted unless admin explicitly deletes
7.4 Google Cloud Deployment:


# Backend: Cloud Run
Service: pdp-automation-api
Region: us-central1
Memory: 2GB (for PDF processing)
CPU: 2 (for image processing)
Min instances: 1 (always warm)
Max instances: 10

# Frontend: Cloud Run (or Firebase Hosting)
Service: pdp-automation-web

# Database: Cloud SQL (PostgreSQL)
Instance: pdp-automation-db
Region: us-central1

# Storage: Cloud Storage
Bucket: pdp-automation-assets
7.5 Environment & Config:


# Production .env
GOOGLE_CLOUD_PROJECT=pdp-automation-prod
GOOGLE_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=xxx
ALLOWED_DOMAIN=your-domain.com
ADMIN_EMAIL=admin@your-domain.com
DATABASE_URL=postgresql://...cloud-sql-connection...
GCS_BUCKET=pdp-automation-assets
7.6 Polish:

Fix toast notification delay
Built-in documentation (DocsPage.tsx)
End-to-end testing
Accessibility fixes
New Files:

backend/app/services/google_auth.py
backend/app/api/routes/auth.py
frontend/src/components/auth/GoogleLoginButton.tsx
frontend/src/contexts/AuthContext.tsx
Dockerfile (backend)
cloudbuild.yaml
Deliverable: Production system on Google Cloud with Workspace auth

Phase 9: JIRA Integration (Days 48-52)
Goal: Automate workflow triggers from JIRA tickets

Features:

Auto-detect brochures in tickets:

Webhook listener for new JIRA attachments
Filter for PDF brochures (by name pattern or file type)
Auto-download brochure when detected
Automatic processing trigger:

When brochure detected → Create processing job
Link job to JIRA ticket
Update ticket status during processing
Post-processing ticket updates:

Add Google Sheet link to ticket
Attach ZIP file or link to cloud storage
Create follow-up sub-tasks:
"Review generated content"
"Approve for publication"
"Create project page"
JIRA API Integration:


class JiraService:
    async def setup_webhook(project_key: str)
    async def handle_attachment_event(event: dict)
    async def update_ticket(ticket_id: str, comment: str, links: List[str])
    async def create_subtasks(parent_id: str, tasks: List[str])
New Files:

backend/app/services/jira_service.py
backend/app/api/routes/jira_webhook.py
frontend/src/pages/JiraSettingsPage.tsx
Deliverable: JIRA-triggered automated processing pipeline

Critical Files to Modify
Backend (Priority Order)
File	Current State	Action
requirements.txt	Missing deps	Add 15+ packages
app/config.py	Minimal	Expand to 80+ lines
app/api/routes.py	File not saved	Rewrite upload handler
app/services/job_manager.py	Stubbed	Full rewrite with DB
app/services/pdf_processor.py	Partial	Add classification
app/services/sheets_manager.py	Not called	Connect to pipeline
app/models/schemas.py	Missing fields	Add steps array
New Backend Files to Create

app/database.py              - SQLAlchemy setup
app/models/db_models.py      - Database models
app/services/vertex_ai.py    - Gemini integration
app/services/image_classifier.py
app/services/content_generator.py
app/services/qa_service.py
app/services/web_scraper.py
app/services/prompt_service.py
app/services/storage_service.py
app/api/routes/qa.py
app/api/routes/prompts.py
app/api/routes/workflow.py
app/api/routes/auth.py
Frontend (Priority Order)
File	Current State	Action
src/api/client.ts	Hardcoded URL	Use env var
src/hooks/use-toast.ts	16min delay	Fix to 5s
src/App.tsx	3 routes	Expand to 12+ routes
New Frontend Files to Create

src/pages/QAPage.tsx
src/pages/QAHistoryPage.tsx
src/pages/PromptsPage.tsx
src/pages/PromptEditorPage.tsx
src/pages/WorkflowPage.tsx
src/pages/HistoryPage.tsx
src/pages/LoginPage.tsx
src/pages/DocsPage.tsx
src/components/qa/*
src/components/prompts/*
src/components/workflow/*
Environment Configuration
Backend (.env)

# App
DEBUG=false
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pdp_automation

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
GCP_PROJECT_ID=pdp-automation-prod
GCS_BUCKET_NAME=pdp-automation-assets
VERTEX_AI_LOCATION=us-central1

# Google Sheets
TEMPLATE_SHEET_ID=your-template-id

# Security
SECRET_KEY=generate-secure-key
CORS_ORIGINS=http://localhost:5174

# Processing
MAX_UPLOAD_SIZE_MB=50
IMAGE_MAX_KB=500
Frontend (.env)

VITE_API_BASE_URL=http://localhost:8000
Verification Plan
Per-Phase Testing
Phase 1: Upload PDF → Check file saved → Check DB record created

Phase 2: Upload PDF → Verify Gemini API called → Check classification output

Phase 3: Upload PDF → Download ZIP → Verify image categories and specs

Phase 4: Upload PDF → Check Google Sheet created and populated

Phase 5: Run QA comparison → Verify diff output accuracy

Phase 6: Create/edit prompt → Verify version history

Phase 7: Login → Verify protected routes → Full end-to-end flow

End-to-End Test
Upload test PDF brochure
Observe real-time progress through all steps
Verify extracted images are correctly classified
Verify floor plans have extracted data
Verify Google Sheet is populated correctly
Run QA against sheet
Download ZIP and verify contents
DevOps & Observability (NEW - from Engineering Review)
Monitoring Stack
Component	Tool	Purpose
Error Tracking	Sentry	Catch & alert on exceptions
Logging	Cloud Logging	Aggregate logs from all services
Metrics	Cloud Monitoring	Performance metrics, dashboards
Uptime	Cloud Monitoring	Health check alerts
APM	OpenTelemetry	Request tracing
CI/CD Pipeline (Cloud Build)

# cloudbuild.yaml
steps:
  - name: 'python'
    args: ['pip', 'install', '-r', 'requirements.txt']
  - name: 'python'
    args: ['pytest', 'tests/']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/pdp-api', '.']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'pdp-api', '--image', 'gcr.io/$PROJECT_ID/pdp-api']
Testing Strategy
Type	Coverage	Tools
Unit Tests	Services, utilities	pytest
Integration Tests	API endpoints	pytest + httpx
E2E Tests	Full workflows	Playwright
Performance Tests	Load testing	Locust
Security Tests	OWASP Top 10	OWASP ZAP
Health Checks

# Required endpoints
GET /health           # Basic health (DB connection)
GET /health/detailed  # All services (Gemini, GCS, Sheets)
GET /ready           # Readiness probe
Cost Optimization
Cache Gemini responses - 70% reduction on repeated content
Batch API calls - Reduce per-request overhead
Image thumbnail generation - Reduce Vision API calls
Cloud Run cold start - Min 1 instance always warm
Revised Phase Structure (22 weeks)
Phase 0: Security & Foundations (Week 1-2)
Days 1-10 | Goal: Secure foundation before any features

0.1 Google Cloud Setup:

Create project, enable APIs
Service account with minimal permissions
Cloud SQL (PostgreSQL) instance
Cloud Storage bucket
0.2 Authentication (MOVED FROM PHASE 8):

Google Workspace OAuth
Domain restriction (@your-domain.com)
User roles table
Protected API routes
0.3 Observability:

Sentry error tracking
Cloud Logging integration
Basic health endpoints
CI/CD pipeline (Cloud Build)
Deliverable: Secure, authenticated, observable foundation

Phase 1: Core Infrastructure (Week 3-4)
Days 11-20 | Goal: Database, API structure, file handling

(Keep existing content but add testing setup)

Phase 2: Vertex AI + Material Prep (Week 5-7)
Days 21-35 | Combined for efficiency

(Merge existing Phases 2+3)

Phase 3: Project Database + Approval Workflow (Week 8-10)
Days 36-50 | Goal: Central repository with handoff workflow

3.1 Project Database (existing)
3.2 Approval Workflow (NEW):

project_approvals table
Submit/Approve/Reject endpoints
ApprovalQueuePage
Workflow status transitions
3.3 Notifications (NEW):

notifications table
NotificationService
Notification bell component
Email integration (optional)
Phase 4: Content Generation + Preview (Week 11-13)
Days 51-65 | Goal: Generate content with preview before push

4.1 Content Generation (existing)
4.2 Content Preview (NEW):

ContentPreviewPage.tsx
Field-by-field review
Regenerate specific fields
"Push to Sheets" button after review
4.3 Pre-push QA validation

Phase 5: Publishing Workflow (Week 14-15)
Days 66-75 | Goal: Publisher experience**

NEW Phase:

PublishQueuePage
Publication checklists (per site)
Asset download tracking
Mark as published flow
Published URL input
Phase 6: QA Module + Post-Publication (Week 16-17)
Days 76-85

(Existing QA module)

Phase 7: Prompt Library + Workflow Board (Week 18-19)
Days 86-95

(Existing content)

Phase 8: Manager Dashboard + Reports (Week 20)
Days 96-100 | NEW Phase

ManagerDashboardPage
Projects processed metrics
Approval turnaround times
Team velocity reports
ReportsPage with exports
Phase 9: JIRA Integration + Polish (Week 21-22)
Days 101-110

(Existing JIRA integration + final testing)

Future Enhancements (After Initial 9-Phase Build)
Slack marketplace app for notifications
Admin dashboard with analytics
Batch processing for multiple PDFs
Mobile-responsive UI improvements
Multi-language content generation
Stayed in plan mode
You've created the new folder. Let me exit plan mode so I can start creating the documentation structure in PDP Automation v.3.

Claude’s Plan
PDP Automation v.3 - Complete Implementation Plan
APPROACH: Fresh build with comprehensive documentation-first development
STATUS: Gathering documentation before any code is written

PART 1: DOCUMENTATION REPOSITORY STRUCTURE
Documentation Categories
A. DOCUMENTS I WILL CREATE FOR YOU
These will be generated and placed in the new project folder:


docs/
├── 01-architecture/
│   ├── SYSTEM_ARCHITECTURE.md      # Overall system design
│   ├── DATA_FLOW.md                # How data moves through the system
│   ├── API_DESIGN.md               # RESTful API specification
│   ├── DATABASE_SCHEMA.md          # Complete PostgreSQL schema
│   ├── SECURITY_ARCHITECTURE.md    # Auth, permissions, data protection
│   └── INFRASTRUCTURE.md           # Google Cloud components
│
├── 02-modules/
│   ├── PROJECT_DATABASE.md         # Central repository module
│   ├── MATERIAL_PREPARATION.md     # PDF → Images pipeline
│   ├── CONTENT_GENERATION.md       # LLM content creation
│   ├── APPROVAL_WORKFLOW.md        # Marketing approval process
│   ├── PUBLISHING_WORKFLOW.md      # Publisher checklist system
│   ├── QA_MODULE.md                # Quality assurance checkpoints
│   ├── PROMPT_LIBRARY.md           # Version-controlled prompts
│   ├── NOTIFICATIONS.md            # Alert system
│   └── JIRA_INTEGRATION.md         # JIRA webhook handling
│
├── 03-frontend/
│   ├── COMPONENT_LIBRARY.md        # UI component specifications
│   ├── PAGE_SPECIFICATIONS.md      # Every page with wireframes
│   ├── STATE_MANAGEMENT.md         # React Query + Zustand patterns
│   ├── ROUTING.md                  # All routes and guards
│   └── ACCESSIBILITY.md            # WCAG 2.1 AA compliance
│
├── 04-backend/
│   ├── SERVICE_LAYER.md            # All service classes
│   ├── API_ENDPOINTS.md            # OpenAPI specification
│   ├── ERROR_HANDLING.md           # Error codes and responses
│   ├── BACKGROUND_JOBS.md          # Async task processing
│   └── CACHING_STRATEGY.md         # Redis/memory caching
│
├── 05-integrations/
│   ├── GOOGLE_CLOUD_SETUP.md       # Step-by-step GCP configuration
│   ├── VERTEX_AI_INTEGRATION.md    # Gemini API usage patterns
│   ├── GOOGLE_SHEETS_INTEGRATION.md # Sheets API patterns
│   ├── GOOGLE_OAUTH_SETUP.md       # Workspace auth setup
│   ├── JIRA_WEBHOOK_SETUP.md       # JIRA app configuration
│   └── CLOUD_STORAGE_PATTERNS.md   # GCS upload/download patterns
│
├── 06-devops/
│   ├── LOCAL_DEVELOPMENT.md        # Dev environment setup
│   ├── CICD_PIPELINE.md            # Cloud Build configuration
│   ├── DEPLOYMENT_GUIDE.md         # Step-by-step deployment
│   ├── MONITORING_SETUP.md         # Sentry, Cloud Monitoring
│   └── BACKUP_RECOVERY.md          # Disaster recovery plan
│
├── 07-testing/
│   ├── TEST_STRATEGY.md            # Overall testing approach
│   ├── UNIT_TEST_PATTERNS.md       # How to write unit tests
│   ├── INTEGRATION_TESTS.md        # API testing patterns
│   ├── E2E_TEST_SCENARIOS.md       # Playwright test cases
│   └── PERFORMANCE_TESTING.md      # Load testing approach
│
├── 08-user-guides/
│   ├── CONTENT_CREATOR_GUIDE.md    # How to use as content creator
│   ├── MARKETING_MANAGER_GUIDE.md  # Approval workflow guide
│   ├── PUBLISHER_GUIDE.md          # Publishing checklist guide
│   ├── ADMIN_GUIDE.md              # System administration
│   └── DEVELOPER_GUIDE.md          # API integration guide
│
└── 09-reference/
    ├── GLOSSARY.md                 # Terms and definitions
    ├── CHANGELOG.md                # Version history
    ├── TROUBLESHOOTING.md          # Common issues and solutions
    └── FAQ.md                      # Frequently asked questions
B. DOCUMENTS YOU MUST COLLECT
These are external resources I cannot access - you need to gather them:

B.1 GOOGLE CLOUD DOCUMENTATION (Required)
Document	URL	Why Needed
Vertex AI Quickstart	https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform	Understand Gemini API patterns
Gemini API Reference	https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini	Model IDs, parameters, limits
Gemini Vision Guide	https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview	Image understanding specifics
Gemini Pricing	https://cloud.google.com/vertex-ai/generative-ai/pricing	Accurate cost calculations
Cloud Run Docs	https://cloud.google.com/run/docs	Deployment configuration
Cloud SQL Docs	https://cloud.google.com/sql/docs/postgres	PostgreSQL managed service
Cloud Storage Docs	https://cloud.google.com/storage/docs	File storage patterns
Google Sheets API	https://developers.google.com/sheets/api/guides/concepts	Spreadsheet automation
Google OAuth 2.0	https://developers.google.com/identity/protocols/oauth2	Workspace authentication
B.2 JIRA INTEGRATION (Required for Phase 9)
Document	URL	Why Needed
JIRA REST API	https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/	API integration
JIRA Webhooks	https://developer.atlassian.com/cloud/jira/platform/webhooks/	Attachment event handling
JIRA App Development	https://developer.atlassian.com/cloud/jira/platform/getting-started/	OAuth for JIRA
B.3 YOUR COMPANY-SPECIFIC DOCUMENTS (Critical)
Document	Description	Why Needed
Google Sheet Template	Actual template used for OPR/MJL/Palm Jebel Ali	Cell mapping, structure
Brand Guidelines	Tone, voice, terminology for content generation	Prompt engineering
Website Templates	Existing page structures on your websites	Content field mapping
Sample Brochures	3-5 actual PDF brochures from past projects	Testing, extraction patterns
Approval Workflow Doc	Current manual approval process description	Digitize existing workflow
JIRA Project Structure	How JIRA projects/tickets are organized	Webhook filtering logic
User List	Who will use this, their roles, email domains	Permission configuration
MPD Domain Info	@your-domain.com Google Workspace admin access	OAuth domain restriction
B.4 TECHNICAL REFERENCE (Nice to Have)
Document	URL	Why Needed
FastAPI Best Practices	https://fastapi.tiangolo.com/tutorial/	Backend patterns
React Query Docs	https://tanstack.com/query/latest	Data fetching patterns
Tailwind CSS Docs	https://tailwindcss.com/docs	Styling reference
PyMuPDF Docs	https://pymupdf.readthedocs.io/	PDF extraction
OpenCV Python Docs	https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html	Image processing
YOUR DOCUMENT COLLECTION CHECKLIST
Priority 1: Must Have Before Development Starts
 Google Cloud Project created with billing enabled
 Service Account JSON downloaded for Vertex AI + Sheets + Storage
 Google Workspace Admin Access to configure OAuth domain restriction
 At least 1 Google Sheet Template (OPR, MJL, or Palm Jebel Ali)
 3-5 Sample PDF Brochures from actual past projects
 User list with emails and their roles (content, marketing, publishing, admin)
Priority 2: Needed for Module Development
 All Google Sheet Templates (OPR, MJL, Palm Jebel Ali)
 Brand/Tone Guidelines for content generation
 Website page structures showing where content goes
 Current approval workflow documentation (even informal)
 JIRA project/board structure for integration planning
Priority 3: Nice to Have for Polish
 Company logo for the web app branding
 Existing prompts from current Telegram bots (if accessible)
 Sample QA reports from current manual QA process
 Competitor/inspiration web apps you like the UX of
NEXT STEPS
Step 1: Create New Project Folder

mkdir "PDP Automation v.3"
cd "PDP Automation v.3"
Step 2: Create Documentation Structure
I will create all the documentation files in the new folder once you approve this plan.

Step 3: Collect Required Documents
Use the checklist above. Place company-specific documents in:


PDP Automation v.3/
├── reference/
│   ├── google-cloud/           # API docs, pricing PDFs
│   ├── jira/                   # JIRA API docs
│   ├── company/                # Your templates, brochures, guidelines
│   │   ├── sheet-templates/    # Google Sheet templates (exported)
│   │   ├── sample-brochures/   # PDF files for testing
│   │   ├── brand-guidelines/   # Tone, voice, style
│   │   └── workflows/          # Current process descriptions
│   └── technical/              # FastAPI, React, PyMuPDF docs
Step 4: Review & Finalize Documentation
Once I create the docs, we'll review each one for completeness.

Step 5: Begin Implementation
Only after documentation is complete and reviewed.

WHAT I WILL DELIVER
Phase 0: Documentation (Before Any Code)
Deliverables:

40+ documentation files covering every aspect of the system
Complete database schema with all tables, relationships, indexes
API specification with every endpoint documented
Page specifications with UI wireframes in text format
Step-by-step setup guides for all integrations
Test case documents for every module
Format:

All docs in Markdown (GitHub-compatible)
Code examples in every technical doc
Diagrams using ASCII art (portable, no external tools)
Cross-references between related docs
Quality Standards:

Every decision documented with rationale
Every API endpoint with request/response examples
Every database table with sample data
Every UI page with user journey description
PART 2: IMPLEMENTATION PLAN
Executive Summary
Goal: Build a complete 5-module Real Estate PDF Automation System that transforms the current manual workflow into an automated, quality-assured pipeline serving 4 departments.

Current State: ~20-25% implemented (UI scaffolding + partial backend)
Target State: Full production system with all modules + integrations

Estimated Timeline: 100-110 days (~22 weeks) - Revised based on technical review
Estimated Monthly Cost: $273-650/month (Gemini API + Cloud Run + Cloud SQL)

Review Findings (PM + Engineering Audit)
Critical Issues Addressed in This Revision
Issue	Severity	Resolution
Auth too late (was Phase 8)	Critical	Moved to Phase 0.5
Missing Publishing workflow	Critical	Added PublishingModule
Missing Approval UI	Critical	Added ApprovalWorkflow
No observability	Critical	Added monitoring stack
Cost underestimated	High	Corrected budget ($273-650/mo)
Timeline unrealistic	High	Extended to 100+ days
No content preview	High	Added ContentPreviewPage
No notifications	High	Added NotificationService
No testing strategy	High	Added testing phases
No CI/CD	Medium	Added Cloud Build config
Multi-Department Support
Department	Primary Features	Pages Added
Content Creation	Upload, Generate, Preview, Submit	ContentPreviewPage
Marketing Management	Review, Approve/Reject, Dashboard	ApprovalQueuePage, ManagerDashboard
Content Publishing	Download, Checklist, Mark Complete	PublishQueuePage, PublishChecklist
Web Development	API access, Webhooks, Asset CDN	API Docs, Webhook config
User Requirements Summary
From Workflow Document (Mariya's Description)
Old Workflow (Current Pain Points)
Brochure uploaded manually
Images/floor plans/logos extracted via Telegram bot
Text generated by Gemini but must be manually copied to Google Sheets
Image processing in separate workflow with specifications
Manual review by Marketing Manager
Manual page creation in websites (OPR, Aggregators)
Post-publication QA via Telegram bot
New Desired Workflow

PARALLEL PROCESSING:

TEXT PATH:                              VISUAL PATH:
─────────────────────                   ─────────────────────
Brochure Upload                         Brochure Upload
      ↓                                       ↓
Gemini Vision Text Extraction           Image Extraction (specs)
      ↓                                       ↓
QA Checkpoint #1                        Gemini Vision Classification
(extraction accuracy)                         ↓
      ↓                                 Watermark Detection → Removal
Organize into JSON                            ↓
      ↓                                 Floor Plan Extraction
Save to Database                              ↓
      ↓                                 Gemini Vision Data Extraction
Pre-generation Prompts                        ↓
      ↓                                 Deduplication
LLM Text Generation                           ↓
      ↓                                 ZIP Package Output
┌─────────────────────┐
│ QA Checkpoint #2    │  ← CRITICAL GATE
│ - Factual accuracy  │
│ - Prompt compliance │
│ - Character limits  │
│ - Consistency       │
└─────────────────────┘
      ↓
  PASS? ──No──→ User Review → Regenerate
      │
     Yes
      ↓
Google Sheets API Push
      ↓
QA Checkpoint #3
(sheet populated correctly)
      ↓
Marketing Manager Approval
Additional Integration Requirements
Integration	Purpose	Priority
Google Cloud Hosting	Deploy on Cloud Run (serverless, auto-scaling)	Phase 7
Google Workspace Auth	OAuth login restricted to @your-domain.com domain	Phase 7
JIRA	Auto-detect brochures in tickets, create follow-ups	Phase 8
Slack	Marketplace app for notifications	Future
User & Permissions Requirements
Requirement	Implementation
Google OAuth	Login with Google Workspace accounts only
Domain restriction	Only @your-domain.com (or configured domain) can access
Shared visibility	All processed PDFs/projects visible to all users
Persistent history	All uploads, images, outputs saved permanently
Admin-only delete	Only admin role can delete files/projects
User roles	admin (full access), user (view/create only)
5 Core Modules
Module 0: Project Database (Central Hub)
Purpose: Central repository of all processed projects with full CRUD and export

This is the foundation - every processed PDF creates a project record that persists.

Features:

All extracted data stored: Project name, developer, location, pricing, floor plans, property types, amenities, handover dates, payment plans, etc.
Custom fields: Users can add unlimited custom fields per project
Full editing: Any user can correct/update extracted data
Search & filter: Find projects by any field (name, developer, date range, price range, etc.)
Project timeline: Track when processed, who processed, revision history
Export formats: Excel, CSV, PDF reports, JSON (API)
Project Record Schema:


Project:
├── Core Fields (auto-extracted)
│   ├── name, developer, location, emirate
│   ├── starting_price, price_per_sqft
│   ├── handover_date, payment_plan
│   ├── property_types[], unit_sizes[]
│   ├── amenities[], features[]
│   └── total_units, floors, buildings
│
├── Floor Plans (linked)
│   ├── unit_type, bedrooms, sqft
│   ├── living_sqft, balcony_sqft
│   └── image_url, floorplan_pdf_page
│
├── Media (linked)
│   ├── interior_images[], exterior_images[]
│   ├── amenity_images[], logos[]
│   └── original_pdf_url, zip_url
│
├── Generated Content (linked)
│   ├── sheet_url, content_version
│   └── qa_results[], approval_status
│
├── Custom Fields (user-added)
│   └── {key: value} pairs - unlimited
│
└── Metadata
    ├── created_by, created_at
    ├── last_modified_by, last_modified_at
    └── processing_job_id, revision_history[]
UI Components:

ProjectsListPage.tsx - Browse all projects with filters
ProjectDetailPage.tsx - View/edit single project
ProjectExportPage.tsx - Export wizard
CustomFieldsEditor.tsx - Add/edit custom fields
Module 1: Approval & Publishing Workflow (NEW - from PM Review)
Purpose: Formal handoff between Content Creation → Marketing → Publishing

Workflow Stages:


DRAFT → PENDING_APPROVAL → APPROVED → PUBLISHING → PUBLISHED → QA_VERIFIED → COMPLETE
                ↓
           REVISION_REQUESTED (back to Content Creator)
Approval Workflow Features:

Submit for Approval button (Content Creator)
ApprovalQueuePage (Marketing Manager view)
Approve / Request Revision / Reject buttons
Required comments for rejections
Bulk approval for multiple projects
Publishing Workflow Features:

PublishQueuePage (Publisher view)
Per-site checklists (OPR, MJL, Palm Jebel Ali)
Asset download tracking
Mark as published with URL input
Handoff notifications at each stage
Database Additions:


project_approvals (
    id, project_id, status, reviewer_id,
    submitted_at, reviewed_at, comments
)

publication_checklists (
    id, project_id, site_name,
    is_page_created, is_images_uploaded, is_seo_verified,
    published_url, published_by, published_at
)
Module 2: Notifications System (NEW - from PM Review)
Purpose: Keep all departments informed of status changes

Events:

project.created - New project added
project.pending_approval - Ready for marketing review
project.approved - Ready for publishing
project.rejected - Needs revision
qa.failed - QA issues found
deadline.approaching - 24h before deadline
deadline.missed - Overdue projects
Channels:

In-app notifications (required)
Email notifications (optional per user)
Future: Slack integration
Frontend:

Notification bell icon in header
NotificationsPage with history
Mark as read / mark all as read
Module 3: QA Module
Purpose: Multi-stage quality assurance throughout the pipeline

Three QA Checkpoints:

After Text Extraction - Verify extraction accuracy
After Text Generation - Validate generated content quality
After Sheet Population - Confirm correct template filling
Post-Publication QA:

Compare approved Google Sheet against published page URL
Output: Matches, differences, missing info, extra info
Store history for auditing
Module 2: Material Preparation
Purpose: Extract and process all visual assets from PDFs

Features:

Image extraction with category classification (Interior/Exterior/Amenity)
Preset limits: 10 exteriors, 10 interiors, 5 amenities
Logo extraction from first page
Watermark detection and removal (OpenCV inpainting)
Floor plan extraction with Vision LLM data extraction
Floor plan deduplication (1 unit type = 1 floor plan)
Image specs: 300 DPI, max 2450x1400 (Real-ESRGAN deferred to future)
File size: max 500KB per image
Output: WebP + JPG formats, ZIP package
Module 3: Text Generation
Purpose: Generate SEO-optimized content for project pages

Features:

Website selection (OPR, Aggregators - MJL, Palm Jebel Ali)
Template-specific content generation
Field-by-field prompts with character limits
URL slug, SEO metas, image ALT tags, all template fields
Version comparison and reuse
Direct Google Sheets API population (no manual copy/paste)
Templates:

MJL template (for commercial pages)
Palm Jebel Ali template (for others)
Module 4: Prompt Library
Purpose: Centralized, version-controlled prompt management

Features:

Prompts grouped by website and template type
Description and intended use per prompt
Full version control
Change history (who changed what, when)
Pre-generation prompt customization
Technical Architecture
Technology Stack
Layer	Technology
Frontend	React 19 + Vite + TypeScript + Tailwind CSS
Backend	FastAPI + Python 3.10+
Database	PostgreSQL + SQLAlchemy (async)
AI/LLM	Google Vertex AI (Gemini 2.5 Flash) - ALL vision + text tasks
Storage	Google Cloud Storage
Sheets	Google Sheets API + gspread
Image Processing	PyMuPDF (extraction), Pillow (resize/compress), OpenCV (inpainting)
Gemini Model Selection in Vertex AI
Yes, you can select the model in Vertex AI configuration. Available models:

Model ID	Best For	Speed	Cost
gemini-2.5-flash	Most tasks, high-throughput	Fastest	Lower
gemini-2.5-pro	Complex reasoning, highest accuracy	Slower	Higher
gemini-2.5-flash-lite	Simple classification, cost-sensitive	Very Fast	Lowest
Recommended Configuration:


# backend/app/config.py
class Settings:
    # Use the latest, most capable model for each task type
    GEMINI_VISION_MODEL: str = "gemini-2.5-pro"  # For image analysis, extraction
    GEMINI_TEXT_MODEL: str = "gemini-2.5-pro"    # For content generation
    VERTEX_AI_LOCATION: str = "us-central1"       # Check regional availability
Task-to-Model Mapping:

Task	Recommended Model	Why
Image Classification	gemini-2.5-pro	Higher accuracy for categories
Floor Plan Data Extraction	gemini-2.5-pro	Complex data extraction needs best reasoning
Watermark/Logo Detection	gemini-2.5-pro	Precise bounding box detection
Text Extraction from PDF	gemini-2.5-pro	90%+ accuracy on complex documents
Content Generation	gemini-2.5-pro	Best SEO-quality output
QA Comparisons	gemini-2.5-pro	Nuanced difference detection
Non-AI image processing (Pillow/OpenCV):

Watermark removal via OpenCV inpainting (after Gemini detects bbox)
Image resizing/compression to meet 500KB limit
Format conversion (WebP + JPG)
Aspect ratio calculations
Model Updates: Vertex AI automatically provides access to the latest model versions. When Google releases newer models, you simply update the model ID in config.

Sources:

Gemini 2.5 Flash Documentation
Gemini 2.5 Pro Documentation
Image Understanding API
Data Flow Architecture

┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  HomePage │ ProcessingPage │ QAPage │ PromptsPage │ Workflow   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                            │
│  /api/upload │ /api/qa │ /api/prompts │ /api/workflow │ /auth  │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌────────▼───────┐   ┌───────▼───────┐
│ Text Pipeline │   │ Visual Pipeline│   │  QA Service   │
│ - Extraction  │   │ - Image Extract│   │ - Compare     │
│ - Generation  │   │ - Classify     │   │ - Validate    │
│ - Sheets Push │   │ - Floor Plans  │   │ - History     │
└───────┬───────┘   └────────┬───────┘   └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Vertex AI (Gemini)                          │
│     Vision API (classification, extraction, watermark detect)   │
│     Text API (content generation, comparison, QA analysis)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Google Cloud                                │
│         Cloud Storage (PDFs, images) │ Sheets API (output)      │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     PostgreSQL Database                         │
│  Jobs │ Prompts │ Templates │ QA History │ Users │ Workflow    │
└─────────────────────────────────────────────────────────────────┘
Database Schema
Core Tables

-- Users (Google Workspace OAuth)
users (id, google_id, email, name, picture_url, role,
       is_active, created_at, last_login_at)
  -- roles: 'admin' (can delete), 'user' (view/create only)
  -- email must be @your-domain.com domain

-- PROJECTS (Central Database - NEW)
projects (
    id UUID PRIMARY KEY,
    -- Core extracted fields
    name VARCHAR(255) NOT NULL,
    developer VARCHAR(255),
    location VARCHAR(255),
    emirate VARCHAR(100),
    starting_price DECIMAL,
    price_per_sqft DECIMAL,
    handover_date DATE,
    payment_plan TEXT,
    property_types JSONB DEFAULT '[]',  -- ["apartment", "villa", "townhouse"]
    unit_sizes JSONB DEFAULT '[]',       -- [{"type": "1BR", "sqft_min": 500, "sqft_max": 700}]
    amenities JSONB DEFAULT '[]',
    features JSONB DEFAULT '[]',
    total_units INTEGER,
    floors INTEGER,
    buildings INTEGER,
    description TEXT,

    -- Custom fields (user-added, flexible)
    custom_fields JSONB DEFAULT '{}',

    -- Media references
    original_pdf_url VARCHAR(500),
    processed_zip_url VARCHAR(500),

    -- Generated content
    sheet_url VARCHAR(500),
    approval_status VARCHAR(50) DEFAULT 'pending',

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    last_modified_by UUID REFERENCES users(id),
    last_modified_at TIMESTAMP DEFAULT NOW(),
    processing_job_id UUID REFERENCES jobs(id)
)

-- Project floor plans
project_floor_plans (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    unit_type VARCHAR(50),  -- "1BR", "2BR", "Studio", etc.
    bedrooms INTEGER,
    total_sqft DECIMAL,
    living_sqft DECIMAL,
    balcony_sqft DECIMAL,
    image_url VARCHAR(500),
    pdf_page_number INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
)

-- Project images
project_images (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    category VARCHAR(50),  -- "interior", "exterior", "amenity", "logo"
    image_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    alt_text VARCHAR(255),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
)

-- Project revision history (audit trail)
project_revisions (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    change_reason VARCHAR(255)
)

-- Processing jobs
jobs (id, user_id, project_id, status, module, website, template_id,
      input_file_path, output_sheet_url, output_zip_path,
      progress, current_step, extracted_data_json, error_message,
      created_at, completed_at)
  -- Now linked to project_id

-- Job processing steps
job_steps (id, job_id, step_id, label, status, started_at, completed_at)

-- Prompts library with versioning
prompts (id, name, website, template_type, description, content,
         version, is_active, created_by, created_at, updated_at)

prompt_versions (id, prompt_id, version, content, changed_by,
                 change_reason, created_at)

-- Website templates
templates (id, name, website, sheet_template_id, field_mapping_json,
           is_active, created_at)

-- QA comparisons
qa_comparisons (id, job_id, checkpoint_type, input_content,
                comparison_target, result_json, status, created_at)
  -- checkpoint_type: 'extraction', 'generation', 'sheet', 'published'

-- Workflow board
workflow_items (id, job_id, project_name, status, priority,
                assigned_to, notes, created_at, updated_at)
  -- status: 'backlog', 'in_progress', 'qa', 'done'

-- Execution history (audit)
execution_history (id, job_id, user_id, action, details_json, created_at)
Implementation Phases
Phase 0: Prerequisites (Days 1-2)
Goal: Set up Google Cloud infrastructure

Tasks:

Create Google Cloud Project (pdp-automation-prod)
Enable APIs:
Vertex AI API
Google Sheets API
Google Drive API
Cloud Storage API
Create Service Account with roles:
Vertex AI User
Storage Object Admin
Sheets Editor
Download credentials JSON
Create Cloud Storage bucket
Create/configure Google Sheets template
Deliverable: Working credentials, ready to integrate

Phase 1: Core Infrastructure (Days 3-7)
Goal: Fix critical issues, add database, restructure backend

Tasks:

Add missing dependencies to requirements.txt:


sqlalchemy[asyncio], asyncpg, alembic
google-cloud-aiplatform, gspread, google-auth
playwright, beautifulsoup4 (for QA scraping)
Create database models (backend/app/models/db_models.py)

Set up Alembic migrations

Update config.py with comprehensive settings

Fix file upload to actually save files

Fix API response schema (add steps array, fix field names)

Create new route structure:


backend/app/api/routes/
├── upload.py
├── jobs.py
├── qa.py
├── prompts.py
├── templates.py
├── workflow.py
└── auth.py
Deliverable: Working upload + database persistence

Phase 2: Vertex AI Integration (Days 8-12)
Goal: Connect Gemini 2.5 Flash for ALL vision and text processing

Tasks:

Create vertex_ai.py service:


class VertexAIService:
    # Text generation
    async def generate_text(prompt: str) -> str

    # Vision - single image analysis
    async def analyze_image(image_bytes: bytes, prompt: str) -> str

    # Vision - multi-image (PDF pages)
    async def generate_with_images(prompt: str, images: List[bytes]) -> str

    # Vision - bounding box detection (for watermarks)
    async def detect_objects(image_bytes: bytes, target: str) -> List[BBox]
Create image_classifier.py (ALL using Gemini Vision):

Classification: interior/exterior/amenity/floorplan/logo/other
Watermark Detection: Get bounding boxes for removal
Floor Plan Analysis: Extract type, sqft, living sqft, bedrooms
Quality Assessment: Identify blurry/low-res images
Create content_generator.py:

Extract all project info from PDF pages (Vision LLM)
Generate SEO content per template (Text LLM)
Validate against character limits
Deliverable: Working Gemini integration for all AI tasks

Phase 3: Material Preparation Module (Days 13-17)
Goal: Complete image processing pipeline with Gemini Vision

Tasks:

Enhance pdf_processor.py:

Gemini Vision: Classify each extracted image
Gemini Vision: Detect watermark bounding boxes
OpenCV: Remove watermarks via inpainting (non-AI)
Gemini Vision: Extract floor plan data (type, sqft)
Python: Deduplicate floor plans by unit type
Image optimization pipeline (Pillow only, no Real-ESRGAN):

Resize to max dimensions (2450x1400)
Compress iteratively to meet 500KB limit
Export WebP + JPG formats
Gemini can flag low-quality images for manual review
Connect storage_service.py for GCS uploads

Fix output_organizer.py:

Enforce category limits (10 ext, 10 int, 5 amenity)
Proper ZIP packaging with organized folders
Deliverable: PDF → Gemini-Classified Images + Floor Plans + ZIP

Phase 4: Project Database Module (Days 18-24)
Goal: Build the central project repository with CRUD, search, and export

Tasks:

4.1 Project Service:


# backend/app/services/project_service.py
class ProjectService:
    async def create_from_extraction(extracted_data: dict, job_id: str) -> Project
    async def update_project(project_id: str, updates: dict, user: User) -> Project
    async def add_custom_field(project_id: str, key: str, value: any) -> Project
    async def search_projects(filters: ProjectFilters, pagination: Pagination) -> List[Project]
    async def get_project_with_media(project_id: str) -> ProjectDetail
    async def track_revision(project_id: str, field: str, old: any, new: any, user: User)
4.2 Export Service:


# backend/app/services/export_service.py
class ExportService:
    async def export_to_excel(project_ids: List[str], fields: List[str]) -> bytes
    async def export_to_csv(project_ids: List[str], fields: List[str]) -> str
    async def export_to_pdf(project_ids: List[str], template: str) -> bytes
    async def export_to_json(project_ids: List[str]) -> dict
4.3 API Endpoints:


GET    /api/projects              - List with filters/search
GET    /api/projects/{id}         - Get project detail
PUT    /api/projects/{id}         - Update project (any user)
DELETE /api/projects/{id}         - Delete project (admin only)
POST   /api/projects/{id}/fields  - Add custom field
GET    /api/projects/{id}/history - Get revision history
POST   /api/projects/export       - Export selected projects
4.4 Frontend Pages:

ProjectsListPage.tsx - DataTable with search, filters, sorting
ProjectDetailPage.tsx - View/edit all fields, media gallery, history
ProjectExportPage.tsx - Select projects, choose format, download
CustomFieldsEditor.tsx - Add/edit custom field definitions
4.5 Search & Filters:

Full-text search on name, developer, location
Filter by: emirate, developer, price range, date range, property type
Sort by: name, date processed, price, developer
Deliverable: Fully functional project database with export

Phase 5: Text Generation Module (Days 25-29)
Goal: Complete content generation with QA validation before Sheets push

Tasks:

Implement content extraction from PDF (Gemini Vision)

Connect prompt library to generation

Implement template-specific generation:

OPR template
MJL template (commercial)
Palm Jebel Ali template
QA Validation BEFORE Google Sheets Push:


class ContentQAService:
    async def validate_before_push(
        extracted_data: dict,      # Original PDF data
        generated_content: dict,   # LLM output
        prompt_spec: Prompt        # Template requirements
    ) -> QAResult:
        # 1. Factual accuracy check
        #    - Does generated content match PDF source?
        #    - Are prices, dates, locations accurate?

        # 2. Prompt compliance check
        #    - Character limits respected?
        #    - Required fields present?
        #    - Tone/style correct?

        # 3. Consistency check
        #    - No contradictions within content?
        #    - Project name used consistently?

        # 4. Return: PASS/FAIL with issues list
Only push to Sheets if QA passes:

If QA fails → Show issues to user for review
User can approve override or regenerate
All QA results logged for audit
Connect sheets_manager.py (after QA approval):

Create sheet from template
Populate with validated content
Map JSON fields to cells via template config
Deliverable: PDF → Generated Content → QA Validation → Google Sheet

Phase 6: QA Module (Days 30-34)
Goal: Implement all QA checkpoints

Tasks:

Create qa_service.py:


class QAService:
    async def validate_extraction(extracted: dict, pdf_path: str) -> QAResult
    async def validate_generation(generated: dict, extracted: dict) -> QAResult
    async def validate_sheet(sheet_url: str, generated: dict) -> QAResult
    async def compare_published(approved: dict, page_url: str) -> QAResult
Create web_scraper.py for published page scraping

Build QA API endpoints

Build QA frontend pages:

QAPage.tsx (run comparisons)
QAHistoryPage.tsx (view history)
Deliverable: Multi-stage QA system

Phase 7: Prompt Library + Workflow (Days 35-39)
Goal: Complete prompt management and workflow board

Tasks:

Implement prompt_service.py:

CRUD operations
Version control
Change history
Build prompt management UI:

PromptsPage.tsx (list/filter)
PromptEditorPage.tsx (edit with diff)
Implement workflow board:

Kanban columns: Backlog → In Progress → QA → Done
Drag-and-drop movement
Assignment to users
Build WorkflowPage.tsx

Deliverable: Prompt library + workflow board

Phase 8: Google Cloud Deployment + Auth (Days 40-47)
Goal: Deploy to Google Cloud with Workspace authentication

Tasks:

7.1 Google Workspace OAuth Authentication:


# backend/app/services/auth_service.py
class GoogleAuthService:
    # OAuth 2.0 with Google Identity
    async def verify_google_token(token: str) -> GoogleUser
    async def check_domain_restriction(email: str) -> bool  # @your-domain.com only
    async def get_or_create_user(google_user: GoogleUser) -> User
    async def assign_role(user_id: str, role: str)  # admin or user
Configure OAuth consent screen in Google Cloud Console
Restrict to organization domain (@your-domain.com)
Auto-create user on first login
First user or configured email = admin
7.2 Role-Based Permissions:

Action	Admin	User
View all projects	Yes	Yes
Create new project	Yes	Yes
View processing history	Yes	Yes
Download assets	Yes	Yes
Delete projects	Yes	No
Delete files	Yes	No
Manage users	Yes	No
7.3 Persistent Shared Storage:

All PDFs stored in Google Cloud Storage (GCS)
All processed images stored in GCS
All outputs (Sheets, ZIPs) linked in database
Every user sees full project history
Nothing deleted unless admin explicitly deletes
7.4 Google Cloud Deployment:


# Backend: Cloud Run
Service: pdp-automation-api
Region: us-central1
Memory: 2GB (for PDF processing)
CPU: 2 (for image processing)
Min instances: 1 (always warm)
Max instances: 10

# Frontend: Cloud Run (or Firebase Hosting)
Service: pdp-automation-web

# Database: Cloud SQL (PostgreSQL)
Instance: pdp-automation-db
Region: us-central1

# Storage: Cloud Storage
Bucket: pdp-automation-assets
7.5 Environment & Config:


# Production .env
GOOGLE_CLOUD_PROJECT=pdp-automation-prod
GOOGLE_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=xxx
ALLOWED_DOMAIN=your-domain.com
ADMIN_EMAIL=admin@your-domain.com
DATABASE_URL=postgresql://...cloud-sql-connection...
GCS_BUCKET=pdp-automation-assets
7.6 Polish:

Fix toast notification delay
Built-in documentation (DocsPage.tsx)
End-to-end testing
Accessibility fixes
New Files:

backend/app/services/google_auth.py
backend/app/api/routes/auth.py
frontend/src/components/auth/GoogleLoginButton.tsx
frontend/src/contexts/AuthContext.tsx
Dockerfile (backend)
cloudbuild.yaml
Deliverable: Production system on Google Cloud with Workspace auth

Phase 9: JIRA Integration (Days 48-52)
Goal: Automate workflow triggers from JIRA tickets

Features:

Auto-detect brochures in tickets:

Webhook listener for new JIRA attachments
Filter for PDF brochures (by name pattern or file type)
Auto-download brochure when detected
Automatic processing trigger:

When brochure detected → Create processing job
Link job to JIRA ticket
Update ticket status during processing
Post-processing ticket updates:

Add Google Sheet link to ticket
Attach ZIP file or link to cloud storage
Create follow-up sub-tasks:
"Review generated content"
"Approve for publication"
"Create project page"
JIRA API Integration:


class JiraService:
    async def setup_webhook(project_key: str)
    async def handle_attachment_event(event: dict)
    async def update_ticket(ticket_id: str, comment: str, links: List[str])
    async def create_subtasks(parent_id: str, tasks: List[str])
New Files:

backend/app/services/jira_service.py
backend/app/api/routes/jira_webhook.py
frontend/src/pages/JiraSettingsPage.tsx
Deliverable: JIRA-triggered automated processing pipeline

Critical Files to Modify
Backend (Priority Order)
File	Current State	Action
requirements.txt	Missing deps	Add 15+ packages
app/config.py	Minimal	Expand to 80+ lines
app/api/routes.py	File not saved	Rewrite upload handler
app/services/job_manager.py	Stubbed	Full rewrite with DB
app/services/pdf_processor.py	Partial	Add classification
app/services/sheets_manager.py	Not called	Connect to pipeline
app/models/schemas.py	Missing fields	Add steps array
New Backend Files to Create

app/database.py              - SQLAlchemy setup
app/models/db_models.py      - Database models
app/services/vertex_ai.py    - Gemini integration
app/services/image_classifier.py
app/services/content_generator.py
app/services/qa_service.py
app/services/web_scraper.py
app/services/prompt_service.py
app/services/storage_service.py
app/api/routes/qa.py
app/api/routes/prompts.py
app/api/routes/workflow.py
app/api/routes/auth.py
Frontend (Priority Order)
File	Current State	Action
src/api/client.ts	Hardcoded URL	Use env var
src/hooks/use-toast.ts	16min delay	Fix to 5s
src/App.tsx	3 routes	Expand to 12+ routes
New Frontend Files to Create

src/pages/QAPage.tsx
src/pages/QAHistoryPage.tsx
src/pages/PromptsPage.tsx
src/pages/PromptEditorPage.tsx
src/pages/WorkflowPage.tsx
src/pages/HistoryPage.tsx
src/pages/LoginPage.tsx
src/pages/DocsPage.tsx
src/components/qa/*
src/components/prompts/*
src/components/workflow/*
Environment Configuration
Backend (.env)

# App
DEBUG=false
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pdp_automation

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
GCP_PROJECT_ID=pdp-automation-prod
GCS_BUCKET_NAME=pdp-automation-assets
VERTEX_AI_LOCATION=us-central1

# Google Sheets
TEMPLATE_SHEET_ID=your-template-id

# Security
SECRET_KEY=generate-secure-key
CORS_ORIGINS=http://localhost:5174

# Processing
MAX_UPLOAD_SIZE_MB=50
IMAGE_MAX_KB=500
Frontend (.env)

VITE_API_BASE_URL=http://localhost:8000
Verification Plan
Per-Phase Testing
Phase 1: Upload PDF → Check file saved → Check DB record created

Phase 2: Upload PDF → Verify Gemini API called → Check classification output

Phase 3: Upload PDF → Download ZIP → Verify image categories and specs

Phase 4: Upload PDF → Check Google Sheet created and populated

Phase 5: Run QA comparison → Verify diff output accuracy

Phase 6: Create/edit prompt → Verify version history

Phase 7: Login → Verify protected routes → Full end-to-end flow

End-to-End Test
Upload test PDF brochure
Observe real-time progress through all steps
Verify extracted images are correctly classified
Verify floor plans have extracted data
Verify Google Sheet is populated correctly
Run QA against sheet
Download ZIP and verify contents
DevOps & Observability (NEW - from Engineering Review)
Monitoring Stack
Component	Tool	Purpose
Error Tracking	Sentry	Catch & alert on exceptions
Logging	Cloud Logging	Aggregate logs from all services
Metrics	Cloud Monitoring	Performance metrics, dashboards
Uptime	Cloud Monitoring	Health check alerts
APM	OpenTelemetry	Request tracing
CI/CD Pipeline (Cloud Build)

# cloudbuild.yaml
steps:
  - name: 'python'
    args: ['pip', 'install', '-r', 'requirements.txt']
  - name: 'python'
    args: ['pytest', 'tests/']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/pdp-api', '.']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'pdp-api', '--image', 'gcr.io/$PROJECT_ID/pdp-api']
Testing Strategy
Type	Coverage	Tools
Unit Tests	Services, utilities	pytest
Integration Tests	API endpoints	pytest + httpx
E2E Tests	Full workflows	Playwright
Performance Tests	Load testing	Locust
Security Tests	OWASP Top 10	OWASP ZAP
Health Checks

# Required endpoints
GET /health           # Basic health (DB connection)
GET /health/detailed  # All services (Gemini, GCS, Sheets)
GET /ready           # Readiness probe
Cost Optimization
Cache Gemini responses - 70% reduction on repeated content
Batch API calls - Reduce per-request overhead
Image thumbnail generation - Reduce Vision API calls
Cloud Run cold start - Min 1 instance always warm
Revised Phase Structure (22 weeks)
Phase 0: Security & Foundations (Week 1-2)
Days 1-10 | Goal: Secure foundation before any features

0.1 Google Cloud Setup:

Create project, enable APIs
Service account with minimal permissions
Cloud SQL (PostgreSQL) instance
Cloud Storage bucket
0.2 Authentication (MOVED FROM PHASE 8):

Google Workspace OAuth
Domain restriction (@your-domain.com)
User roles table
Protected API routes
0.3 Observability:

Sentry error tracking
Cloud Logging integration
Basic health endpoints
CI/CD pipeline (Cloud Build)
Deliverable: Secure, authenticated, observable foundation

Phase 1: Core Infrastructure (Week 3-4)
Days 11-20 | Goal: Database, API structure, file handling

(Keep existing content but add testing setup)

Phase 2: Vertex AI + Material Prep (Week 5-7)
Days 21-35 | Combined for efficiency

(Merge existing Phases 2+3)

Phase 3: Project Database + Approval Workflow (Week 8-10)
Days 36-50 | Goal: Central repository with handoff workflow

3.1 Project Database (existing)
3.2 Approval Workflow (NEW):

project_approvals table
Submit/Approve/Reject endpoints
ApprovalQueuePage
Workflow status transitions
3.3 Notifications (NEW):

notifications table
NotificationService
Notification bell component
Email integration (optional)
Phase 4: Content Generation + Preview (Week 11-13)
Days 51-65 | Goal: Generate content with preview before push

4.1 Content Generation (existing)
4.2 Content Preview (NEW):

ContentPreviewPage.tsx
Field-by-field review
Regenerate specific fields
"Push to Sheets" button after review
4.3 Pre-push QA validation

Phase 5: Publishing Workflow (Week 14-15)
Days 66-75 | Goal: Publisher experience**

NEW Phase:

PublishQueuePage
Publication checklists (per site)
Asset download tracking
Mark as published flow
Published URL input
Phase 6: QA Module + Post-Publication (Week 16-17)
Days 76-85

(Existing QA module)

Phase 7: Prompt Library + Workflow Board (Week 18-19)
Days 86-95

(Existing content)

Phase 8: Manager Dashboard + Reports (Week 20)
Days 96-100 | NEW Phase

ManagerDashboardPage
Projects processed metrics
Approval turnaround times
Team velocity reports
ReportsPage with exports
Phase 9: JIRA Integration + Polish (Week 21-22)
Days 101-110

(Existing JIRA integration + final testing)

Future Enhancements (After Initial 9-Phase Build)
Slack marketplace app for notifications
Admin dashboard with analytics
Batch processing for multiple PDFs
Mobile-responsive UI improvements
Multi-language content generation
User approved the plan
Excellent! The plan is approved. Let me start creating the documentation structure in your new PDP Automation v.3 folder.

Update Todos

Create documentation folder structure in PDP Automation v.3

Create architecture documentation (6 files)

Create module documentation (9 files)

Create frontend documentation (5 files)

Create backend documentation (5 files)

Create integration documentation (6 files)

Create devops documentation (5 files)

Create testing documentation (5 files)

Create user guides (5 files)

Create reference documentation (4 files)
Bash Check for PDP Automation v.3 folder
IN
ls -la "c:/Users/shahe/" | grep -i "pdp"

OUT
drwxr-xr-x 1 shahe 197610        0 Jan 13 17:51 PDP Automation
drwxr-xr-x 1 shahe 197610        0 Jan 14 18:49 PDP Automation v.2
Bash Search for v.3 folder
IN
find "c:/Users/shahe" -maxdepth 2 -type d -name "*v.3*" 2>/dev/null || dir "c:/Users/shahe" /b /ad 2>nul | findstr /i "v.3"

OUT
c:/Users/shahe/PDP Automation v.2/PDP Automation v.3
Found it. The v.3 folder is at c:/Users/shahe/PDP Automation v.2/PDP Automation v.3. Let me create the documentation structure there.

Bash Create documentation folder structure
IN
cd "c:/Users/shahe/PDP Automation v.2/PDP Automation v.3" && mkdir -p docs/01-architecture docs/02-modules docs/03-frontend docs/04-backend docs/05-integrations docs/06-devops docs/07-testing docs/08-user-guides docs/09-reference reference/google-cloud reference/jira reference/company/sheet-templates reference/company/sample-brochures reference/company/brand-guidelines reference/company/workflows reference/technical

OUT
0
Update Todos

Create documentation folder structure in PDP Automation v.3

Create architecture documentation (6 files)

Create module documentation (9 files)

Create frontend documentation (5 files)

Create backend documentation (5 files)

Create integration documentation (6 files)

Create devops documentation (5 files)

Create testing documentation (5 files)

Create user guides (5 files)

Create reference documentation (4 files)
Now let me create the architecture documentation files. Starting with the main system architecture.

Write SYSTEM_ARCHITECTURE.md
300 lines
# System Architecture

## Overview

PDP Automation v.3 is a **Real Estate PDF Automation System** that transforms PDF brochures into structured, SEO-optimized content and processed images for property detail pages.

### System Purpose

| Input | Processing | Output |
|-------|------------|--------|
| PDF brochure | AI extraction + generation | Google Sheet (content) |
| | | ZIP file (images) |
| | | Project database record |

### Target Users (4 Departments)

| Department | Role | Primary Actions |
|------------|------|-----------------|
| **Content Creation** | Content Creator | Upload PDFs, generate content, submit for approval |
| **Marketing** | Marketing Manager | Review, approve/reject content |
| **Publishing** | Publisher | Download assets, create pages, mark as published |
| **Web Development** | Developer | Access APIs, integrate assets |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USERS (4 Departments)                          │
│  Content Creator │ Marketing Manager │ Publisher │ Web Developer            │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React 19 + Vite)                          │
│                                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Upload    │ │  Projects   │ │   Approval  │ │   Workflow  │           │
│  │    Page     │ │  Database   │ │    Queue    │ │    Board    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Content   │ │   Prompts   │ │     QA      │ │    Admin    │           │
│  │   Preview   │ │   Library   │ │    Module   │ │  Dashboard  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                                             │
│  State: React Query + Zustand │ UI: Tailwind + shadcn/ui                   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ REST API (JSON)
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI + Python 3.10+)                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           API Layer                                  │   │
│  │  /upload │ /projects │ /qa │ /prompts │ /workflow │ /auth │ /jira  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Service Layer                                │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │   │
│  │  │ PDFProcessor │ │ContentGenSvc │ │   QAService  │                 │   │
│  │  │              │ │              │ │              │                 │   │
│  │  │ - Extract    │ │ - Extract    │ │ - Validate   │                 │   │
│  │  │ - Classify   │ │ - Generate   │ │ - Compare    │                 │   │
│  │  │ - Optimize   │ │ - Push       │ │ - Report     │                 │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                 │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │   │
│  │  │ProjectService│ │PromptService │ │NotifyService │                 │   │
│  │  │              │ │              │ │              │                 │   │
│  │  │ - CRUD       │ │ - CRUD       │ │ - In-app     │                 │   │
│  │  │ - Search     │ │ - Versioning │ │ - Email      │                 │   │
│  │  │ - Export     │ │ - History    │ │ - Events     │                 │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Background Jobs (asyncio)                       │   │
│  │  PDF Processing │ Image Classification │ Content Generation          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   PostgreSQL    │ │  Google Cloud   │ │   Vertex AI     │
│   (Cloud SQL)   │ │    Storage      │ │    (Gemini)     │
│                 │ │                 │ │                 │
│ - Users         │ │ - PDFs          │ │ - Vision API    │
│ - Projects      │ │ - Images        │ │ - Text API      │
│ - Prompts       │ │ - ZIPs          │ │ - Classification│
│ - QA Results    │ │ - Thumbnails    │ │ - Extraction    │
│ - Workflow      │ │                 │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
           │                   │
           │                   ▼
           │        ┌─────────────────┐
           │        │  Google Sheets  │
           │        │      API        │
           │        │                 │
           │        │ - Templates     │
           │        │ - Output sheets │
           │        └─────────────────┘
           │
           ▼
┌─────────────────┐
│      JIRA       │
│    (Webhooks)   │
│                 │
│ - Attachments   │
│ - Tickets       │
│ - Sub-tasks     │
└─────────────────┘
```

---

## Technology Stack

### Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | React | 19.x | UI library |
| Build | Vite | 7.x | Build tool |
| Language | TypeScript | 5.x | Type safety |
| Styling | Tailwind CSS | 3.x | Utility-first CSS |
| Components | shadcn/ui | latest | UI component library |
| State | React Query | 5.x | Server state |
| State | Zustand | 4.x | Client state |
| Router | React Router | 7.x | Navigation |
| Icons | Lucide React | latest | Icon library |

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | FastAPI | 0.109+ | API framework |
| Runtime | Python | 3.10+ | Programming language |
| ORM | SQLAlchemy | 2.x | Database ORM |
| Migrations | Alembic | 1.x | DB migrations |
| Validation | Pydantic | 2.x | Data validation |
| PDF | PyMuPDF | 1.23+ | PDF extraction |
| Images | Pillow | 10.x | Image processing |
| Images | OpenCV | 4.9+ | Advanced image ops |
| Google | gspread | 6.x | Sheets API |
| Google | google-cloud-aiplatform | 1.38+ | Vertex AI |
| Google | google-cloud-storage | 2.x | Cloud Storage |

### Infrastructure

| Component | Service | Purpose |
|-----------|---------|---------|
| Compute | Cloud Run | Backend + Frontend hosting |
| Database | Cloud SQL | PostgreSQL managed |
| Storage | Cloud Storage | Files (PDFs, images) |
| AI | Vertex AI | Gemini 2.5 models |
| Auth | Google OAuth | Workspace authentication |
| CI/CD | Cloud Build | Automated deployment |
| Monitoring | Cloud Monitoring | Metrics + alerts |
| Logging | Cloud Logging | Centralized logs |
| Errors | Sentry | Error tracking |

---

## Key Design Decisions

### 1. Why Gemini 2.5 Pro for All AI Tasks?

**Decision:** Use Vertex AI (Gemini 2.5 Pro) for ALL vision and text tasks.

**Rationale:**
- Single provider simplifies billing, monitoring, and debugging
- Gemini 2.5 Pro has 90%+ accuracy on document extraction
- Vision capabilities handle classification, OCR, and bounding box detection
- Native Google Cloud integration reduces authentication complexity
- Model can be upgraded by changing a single config value

**Alternatives Considered:**
- OpenAI GPT-4 Vision: Higher cost, separate billing
- Multi-provider: Complex fallback logic, inconsistent outputs

### 2. Why PostgreSQL over NoSQL?

**Decision:** PostgreSQL with SQLAlchemy async for all data storage.

**Rationale:**
- Relational data: Projects have floor plans, images, approvals (clear relationships)
- JSONB columns: Custom fields get NoSQL flexibility where needed
- Full-text search: PostgreSQL's `tsvector` for project search
- ACID compliance: Critical for approval workflow state transitions
- Cloud SQL: Managed backups, replicas, point-in-time recovery

**Alternatives Considered:**
- MongoDB: Better for unstructured, but our data is mostly structured
- Firestore: Vendor lock-in, weaker querying

### 3. Why Cloud Run over GKE/VMs?

**Decision:** Cloud Run for both backend and frontend.

**Rationale:**
- Serverless: No infrastructure management
- Auto-scaling: 0 to N instances based on traffic
- Cost: Pay per request (with min instances for warm start)
- Simplicity: Docker containers, simple deployment

**Configuration:**
```yaml
Backend:
  memory: 2GB    # PDF processing needs RAM
  cpu: 2         # Image processing is CPU-intensive
  min_instances: 1  # Always warm (no cold start for users)
  max_instances: 10

Frontend:
  memory: 512MB
  cpu: 1
  min_instances: 0  # Can cold start (static content)
```

### 4. Why Google Workspace OAuth?

**Decision:** Google OAuth with domain restriction, not custom auth.

**Rationale:**
- Users already have Google Workspace accounts (@your-domain.com)
- No password management, password reset flows
- MFA handled by Google
- Easy domain restriction (organization-only access)
- Profile photos, names auto-populated

### 5. Why Three QA Checkpoints?

**Decision:** Validate at extraction, generation, and publication stages.

**Rationale:**
- **Checkpoint 1 (Extraction):** Catch PDF parsing errors early
- **Checkpoint 2 (Generation):** Verify LLM output matches source before pushing to Sheets
- **Checkpoint 3 (Publication):** Compare published page to approved content

**Failure Handling:**
- Checkpoint 1 fails → Re-upload with different PDF
- Checkpoint 2 fails → Review/regenerate specific fields
- Checkpoint 3 fails → Alert publisher to fix website

---

## Security Architecture

See [SECURITY_ARCHITECTURE.md](./SECURITY_ARCHITECTURE.md) for detailed security documentation.

### Summary

| Layer | Protection |
|-------|------------|
| **Network** | HTTPS only, Cloud Armor WAF |
| **Auth** | OAuth 2.0 + domain restriction |
| **Authorization** | Role-based (admin/user) |
| **Data** | Encrypted at rest (Cloud SQL, GCS) |
| **Files** | MIME validation, size limits, virus scanning |
| **API** | Rate limiting, input validation |
| **Audit** | All actions logged with user ID |

---

## Scalability Considerations

### Current Design Limits

| Resource | Limit | Mitigation |
|----------|-------|------------|
| PDF size | 50MB | Warn user, compress if possible |
| Images per PDF | 500 | Process in batches |
| Concurrent jobs | 10 per instance | Auto-scale instances |
| Gemini API | 60 req/min | Queue + exponential backoff |
| Sheets API | 100 req/100s | Batch operations |

### Growth Path

| Phase | Users | Projects/Month | Infrastructure |
|-------|-------|----------------|----------------|
| Launch | 10 | 50 | 1 Cloud Run instance |
| 6 months | 25 | 150 | 2-3 instances |
| 1 year | 50+ | 300+ | Consider Kubernetes |

---

## Related Documentation

- [DATA_FLOW.md](./DATA_FLOW.md) - How data moves through the system
- [API_DESIGN.md](./API_DESIGN.md) - RESTful API specification
- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - Complete PostgreSQL schema
- [SECURITY_ARCHITECTURE.md](./SECURITY_ARCHITECTURE.md) - Security measures
- [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) - Google Cloud setup
Write DATABASE_SCHEMA.md
846 lines
# Database Schema

## Overview

PostgreSQL database with SQLAlchemy async ORM. Uses JSONB for flexible fields while maintaining relational integrity for core entities.

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │    projects     │       │      jobs       │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │──┐    │ id (PK)         │
│ google_id       │  │    │ name            │  │    │ project_id (FK) │──┐
│ email           │  │    │ developer       │  │    │ user_id (FK)    │  │
│ name            │  │    │ location        │  │    │ status          │  │
│ role            │  │    │ emirate         │  │    │ progress        │  │
│ created_at      │  │    │ starting_price  │  │    │ current_step    │  │
└─────────────────┘  │    │ ...             │  │    │ created_at      │  │
                     │    │ created_by (FK) │◀─┘    └─────────────────┘  │
                     │    │ custom_fields   │                            │
                     └───▶│ created_at      │◀───────────────────────────┘
                          └─────────────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ project_floor_  │   │ project_images  │   │ project_        │
│ plans           │   │                 │   │ approvals       │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ id (PK)         │   │ id (PK)         │   │ id (PK)         │
│ project_id (FK) │   │ project_id (FK) │   │ project_id (FK) │
│ unit_type       │   │ category        │   │ status          │
│ bedrooms        │   │ image_url       │   │ reviewer_id(FK) │
│ total_sqft      │   │ thumbnail_url   │   │ comments        │
│ living_sqft     │   │ alt_text        │   │ submitted_at    │
│ image_url       │   │ sort_order      │   │ reviewed_at     │
└─────────────────┘   └─────────────────┘   └─────────────────┘

┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│    prompts      │   │ prompt_versions │   │   templates     │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ id (PK)         │──▶│ id (PK)         │   │ id (PK)         │
│ name            │   │ prompt_id (FK)  │   │ name            │
│ website         │   │ version         │   │ website         │
│ template_type   │   │ content         │   │ sheet_template  │
│ content         │   │ changed_by (FK) │   │ field_mapping   │
│ version         │   │ created_at      │   │ is_active       │
│ created_by (FK) │   └─────────────────┘   └─────────────────┘
└─────────────────┘

┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ qa_comparisons  │   │ notifications   │   │ workflow_items  │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ id (PK)         │   │ id (PK)         │   │ id (PK)         │
│ job_id (FK)     │   │ user_id (FK)    │   │ project_id (FK) │
│ checkpoint_type │   │ event_type      │   │ status          │
│ input_content   │   │ title           │   │ priority        │
│ result_json     │   │ message         │   │ assigned_to(FK) │
│ status          │   │ is_read         │   │ notes           │
└─────────────────┘   └─────────────────┘   └─────────────────┘

┌─────────────────┐   ┌─────────────────┐
│ publication_    │   │ project_        │
│ checklists      │   │ revisions       │
├─────────────────┤   ├─────────────────┤
│ id (PK)         │   │ id (PK)         │
│ project_id (FK) │   │ project_id (FK) │
│ site_name       │   │ changed_by (FK) │
│ is_page_created │   │ field_name      │
│ is_images_done  │   │ old_value       │
│ published_url   │   │ new_value       │
│ published_at    │   │ changed_at      │
└─────────────────┘   └─────────────────┘
```

---

## Table Definitions

### users

User accounts authenticated via Google Workspace OAuth.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    picture_url VARCHAR(500),
    role VARCHAR(20) NOT NULL DEFAULT 'user'
        CHECK (role IN ('admin', 'user')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT email_domain_check
        CHECK (email LIKE '%@your-domain.com')  -- Configurable domain
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
```

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| google_id | VARCHAR | Google account ID (from OAuth) |
| email | VARCHAR | Email (must be @your-domain.com) |
| name | VARCHAR | Display name |
| picture_url | VARCHAR | Profile photo URL |
| role | VARCHAR | 'admin' or 'user' |
| is_active | BOOLEAN | Account enabled |
| created_at | TIMESTAMP | Account creation |
| last_login_at | TIMESTAMP | Last login time |

---

### projects

Central repository of all processed real estate projects.

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core extracted fields
    name VARCHAR(255) NOT NULL,
    developer VARCHAR(255),
    location VARCHAR(255),
    emirate VARCHAR(100),
    starting_price DECIMAL(15, 2),
    price_per_sqft DECIMAL(10, 2),
    handover_date DATE,
    payment_plan TEXT,
    description TEXT,

    -- Array fields (JSONB)
    property_types JSONB DEFAULT '[]'::jsonb,
    unit_sizes JSONB DEFAULT '[]'::jsonb,
    amenities JSONB DEFAULT '[]'::jsonb,
    features JSONB DEFAULT '[]'::jsonb,

    -- Numeric fields
    total_units INTEGER,
    floors INTEGER,
    buildings INTEGER,

    -- Custom fields (user-added)
    custom_fields JSONB DEFAULT '{}'::jsonb,

    -- Media references
    original_pdf_url VARCHAR(500),
    processed_zip_url VARCHAR(500),

    -- Generated content
    sheet_url VARCHAR(500),

    -- Workflow status
    workflow_status VARCHAR(50) NOT NULL DEFAULT 'draft'
        CHECK (workflow_status IN (
            'draft',
            'pending_approval',
            'revision_requested',
            'approved',
            'publishing',
            'published',
            'qa_verified',
            'complete'
        )),

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified_by UUID REFERENCES users(id),
    last_modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_job_id UUID REFERENCES jobs(id)
);

-- Indexes for search and filtering
CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_developer ON projects(developer);
CREATE INDEX idx_projects_emirate ON projects(emirate);
CREATE INDEX idx_projects_status ON projects(workflow_status);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);

-- Full-text search index
CREATE INDEX idx_projects_search ON projects
    USING gin(to_tsvector('english',
        coalesce(name, '') || ' ' ||
        coalesce(developer, '') || ' ' ||
        coalesce(location, '')
    ));
```

**JSONB Field Structures:**

```json
// property_types
["apartment", "villa", "townhouse", "penthouse"]

// unit_sizes
[
    {"type": "Studio", "sqft_min": 400, "sqft_max": 550},
    {"type": "1BR", "sqft_min": 650, "sqft_max": 850},
    {"type": "2BR", "sqft_min": 1100, "sqft_max": 1400}
]

// amenities
["Swimming Pool", "Gym", "Kids Play Area", "BBQ Area", "Rooftop Lounge"]

// features
["Smart Home", "Floor-to-ceiling Windows", "Italian Kitchen"]

// custom_fields (user-defined)
{
    "sales_contact": "John Smith",
    "broker_commission": "3%",
    "priority_level": "high"
}
```

---

### project_floor_plans

Floor plan images with extracted data.

```sql
CREATE TABLE project_floor_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Extracted data
    unit_type VARCHAR(50) NOT NULL,  -- "Studio", "1BR", "2BR", etc.
    bedrooms INTEGER,
    total_sqft DECIMAL(10, 2),
    living_sqft DECIMAL(10, 2),
    balcony_sqft DECIMAL(10, 2),

    -- Image reference
    image_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    pdf_page_number INTEGER,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Deduplication: one floor plan per unit type per project
    CONSTRAINT unique_floor_plan_per_type
        UNIQUE (project_id, unit_type)
);

CREATE INDEX idx_floor_plans_project ON project_floor_plans(project_id);
```

---

### project_images

Categorized images extracted from PDFs.

```sql
CREATE TABLE project_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Classification
    category VARCHAR(50) NOT NULL
        CHECK (category IN ('interior', 'exterior', 'amenity', 'logo', 'other')),

    -- Image URLs
    image_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),

    -- Metadata
    alt_text VARCHAR(255),
    sort_order INTEGER DEFAULT 0,
    file_size_kb INTEGER,
    width INTEGER,
    height INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_images_project ON project_images(project_id);
CREATE INDEX idx_images_category ON project_images(project_id, category);
```

**Category Limits (enforced in application):**

| Category | Max Count |
|----------|-----------|
| interior | 10 |
| exterior | 10 |
| amenity | 5 |
| logo | 3 |
| other | unlimited (usually discarded) |

---

### project_approvals

Approval workflow tracking.

```sql
CREATE TABLE project_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending',
            'approved',
            'rejected',
            'revision_requested'
        )),

    -- Actors
    submitted_by UUID REFERENCES users(id),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewer_id UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,

    -- Feedback
    comments TEXT,
    revision_notes TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_approvals_project ON project_approvals(project_id);
CREATE INDEX idx_approvals_status ON project_approvals(status);
CREATE INDEX idx_approvals_reviewer ON project_approvals(reviewer_id);
```

---

### project_revisions

Audit trail for project field changes.

```sql
CREATE TABLE project_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- What changed
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,

    -- Who/when
    changed_by UUID NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_reason VARCHAR(255)
);

CREATE INDEX idx_revisions_project ON project_revisions(project_id);
CREATE INDEX idx_revisions_changed_at ON project_revisions(changed_at DESC);
```

---

### jobs

Background processing jobs.

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id),

    -- Job configuration
    module VARCHAR(50) NOT NULL
        CHECK (module IN ('material_prep', 'text_gen', 'qa', 'full')),
    website VARCHAR(100),
    template_id UUID REFERENCES templates(id),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_step VARCHAR(100),
    error_message TEXT,

    -- Input/Output
    input_file_path VARCHAR(500),
    output_sheet_url VARCHAR(500),
    output_zip_path VARCHAR(500),
    extracted_data JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_jobs_user ON jobs(user_id);
CREATE INDEX idx_jobs_project ON jobs(project_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
```

---

### job_steps

Individual steps within a job.

```sql
CREATE TABLE job_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- Step info
    step_id VARCHAR(50) NOT NULL,  -- 'upload', 'extract', 'classify', etc.
    label VARCHAR(100) NOT NULL,    -- Human-readable label

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_steps_job ON job_steps(job_id);
```

---

### prompts

Version-controlled prompt library.

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identification
    name VARCHAR(255) NOT NULL,
    website VARCHAR(100) NOT NULL,  -- 'opr', 'mjl', 'palm_jebel_ali'
    template_type VARCHAR(100) NOT NULL,  -- 'standard', 'commercial'

    -- Content
    description TEXT,
    content TEXT NOT NULL,

    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_prompt_identity
        UNIQUE (website, template_type, name)
);

CREATE INDEX idx_prompts_website ON prompts(website);
CREATE INDEX idx_prompts_active ON prompts(is_active) WHERE is_active = true;
```

---

### prompt_versions

Historical versions of prompts.

```sql
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    -- Version content
    version INTEGER NOT NULL,
    content TEXT NOT NULL,

    -- Change tracking
    changed_by UUID REFERENCES users(id),
    change_reason VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_prompt_version
        UNIQUE (prompt_id, version)
);

CREATE INDEX idx_prompt_versions_prompt ON prompt_versions(prompt_id);
```

---

### templates

Website template configurations.

```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identification
    name VARCHAR(255) NOT NULL,
    website VARCHAR(100) NOT NULL,

    -- Google Sheets reference
    sheet_template_id VARCHAR(100) NOT NULL,

    -- Field mapping (JSON to Sheets cells)
    field_mapping JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**field_mapping Structure:**

```json
{
    "project_name": "B1",
    "meta_title": "B2",
    "meta_description": "B3",
    "url_slug": "B4",
    "h1": "B5",
    "starting_price": "B6",
    "location": "B7",
    "developer": "B8",
    "handover": "B9",
    "overview": "B10:B15"
}
```

---

### qa_comparisons

QA checkpoint results.

```sql
CREATE TABLE qa_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Checkpoint type
    checkpoint_type VARCHAR(30) NOT NULL
        CHECK (checkpoint_type IN (
            'extraction',   -- After PDF extraction
            'generation',   -- After content generation
            'sheet',        -- After Sheets population
            'published'     -- After page publication
        )),

    -- Comparison data
    input_content JSONB NOT NULL,
    comparison_target JSONB,
    result JSONB NOT NULL,

    -- Summary
    matches INTEGER DEFAULT 0,
    differences INTEGER DEFAULT 0,
    missing INTEGER DEFAULT 0,
    extra INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'passed', 'failed', 'overridden')),
    override_by UUID REFERENCES users(id),
    override_reason TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_qa_project ON qa_comparisons(project_id);
CREATE INDEX idx_qa_type ON qa_comparisons(checkpoint_type);
CREATE INDEX idx_qa_status ON qa_comparisons(status);
```

---

### notifications

In-app notification system.

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Content
    event_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    -- Reference
    reference_type VARCHAR(50),  -- 'project', 'job', 'approval'
    reference_id UUID,

    -- Status
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read)
    WHERE is_read = false;
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
```

**Event Types:**

| Event | Description |
|-------|-------------|
| `project.created` | New project processed |
| `project.pending_approval` | Submitted for review |
| `project.approved` | Approved by marketing |
| `project.rejected` | Rejected with feedback |
| `project.revision_requested` | Changes requested |
| `qa.failed` | QA checkpoint failed |
| `qa.passed` | QA checkpoint passed |
| `deadline.approaching` | 24h before deadline |
| `deadline.missed` | Past deadline |

---

### workflow_items

Kanban board items.

```sql
CREATE TABLE workflow_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Board position
    status VARCHAR(30) NOT NULL DEFAULT 'backlog'
        CHECK (status IN ('backlog', 'in_progress', 'qa', 'done')),
    priority INTEGER DEFAULT 0,
    position INTEGER DEFAULT 0,  -- Order within column

    -- Assignment
    assigned_to UUID REFERENCES users(id),

    -- Notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_workflow_status ON workflow_items(status);
CREATE INDEX idx_workflow_assigned ON workflow_items(assigned_to);
```

---

### publication_checklists

Per-site publication tracking.

```sql
CREATE TABLE publication_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Site
    site_name VARCHAR(100) NOT NULL,  -- 'opr', 'mjl', 'palm_jebel_ali'

    -- Checklist items
    is_page_created BOOLEAN NOT NULL DEFAULT false,
    is_images_uploaded BOOLEAN NOT NULL DEFAULT false,
    is_seo_verified BOOLEAN NOT NULL DEFAULT false,
    is_content_reviewed BOOLEAN NOT NULL DEFAULT false,

    -- Publication
    published_url VARCHAR(500),
    published_by UUID REFERENCES users(id),
    published_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_checklist_per_site
        UNIQUE (project_id, site_name)
);

CREATE INDEX idx_checklist_project ON publication_checklists(project_id);
```

---

### execution_history

Full audit log.

```sql
CREATE TABLE execution_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Actor
    user_id UUID REFERENCES users(id),

    -- Action
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,

    -- Details
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_history_user ON execution_history(user_id);
CREATE INDEX idx_history_resource ON execution_history(resource_type, resource_id);
CREATE INDEX idx_history_created ON execution_history(created_at DESC);

-- Partition by month for large datasets (future optimization)
```

---

## Migrations

### Alembic Setup

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Migration Naming Convention

```
YYYYMMDD_HHMM_description.py

Examples:
20260115_1030_initial_schema.py
20260115_1045_add_notifications.py
20260116_0900_add_publication_checklists.py
```

---

## Query Examples

### Search Projects

```sql
-- Full-text search
SELECT * FROM projects
WHERE to_tsvector('english',
    coalesce(name, '') || ' ' ||
    coalesce(developer, '') || ' ' ||
    coalesce(location, '')
) @@ plainto_tsquery('english', 'Emaar Downtown')
ORDER BY created_at DESC
LIMIT 20;
```

### Get Project with All Relations

```sql
SELECT
    p.*,
    json_agg(DISTINCT pf.*) as floor_plans,
    json_agg(DISTINCT pi.*) FILTER (WHERE pi.category = 'interior') as interior_images,
    json_agg(DISTINCT pi.*) FILTER (WHERE pi.category = 'exterior') as exterior_images,
    pa.status as approval_status,
    u.name as created_by_name
FROM projects p
LEFT JOIN project_floor_plans pf ON pf.project_id = p.id
LEFT JOIN project_images pi ON pi.project_id = p.id
LEFT JOIN project_approvals pa ON pa.project_id = p.id
LEFT JOIN users u ON u.id = p.created_by
WHERE p.id = $1
GROUP BY p.id, pa.status, u.name;
```

### Dashboard Metrics

```sql
-- Projects processed this week
SELECT
    date_trunc('day', created_at) as day,
    COUNT(*) as count
FROM projects
WHERE created_at >= date_trunc('week', NOW())
GROUP BY 1
ORDER BY 1;

-- Approval turnaround time
SELECT
    AVG(EXTRACT(EPOCH FROM (reviewed_at - submitted_at))/3600) as avg_hours
FROM project_approvals
WHERE status IN ('approved', 'rejected')
AND reviewed_at IS NOT NULL
AND submitted_at >= NOW() - INTERVAL '30 days';
```

---

## Related Documentation

- [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) - Overall architecture
- [API_DESIGN.md](./API_DESIGN.md) - API endpoints using these tables
- [DATA_FLOW.md](./DATA_FLOW.md) - How data moves between tables
Prompt is too long

Prompt is too long

continue
Prompt is too long

continue
Prompt is too long