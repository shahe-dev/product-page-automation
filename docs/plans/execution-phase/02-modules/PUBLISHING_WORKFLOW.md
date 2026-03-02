# Module: Publishing Workflow

**Module Number:** 4
**Category:** Workflow Management
**Last Updated:** 2026-01-15
**Status:** Core Module

---

## Table of Contents

1. [Overview](#overview)
2. [Purpose & Goals](#purpose--goals)
3. [Key Features](#key-features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [Publishing Checklists](#publishing-checklists)
7. [API Endpoints](#api-endpoints)
8. [UI Components](#ui-components)
9. [Workflow Diagrams](#workflow-diagrams)
10. [Code Examples](#code-examples)
11. [Configuration](#configuration)
12. [Related Documentation](#related-documentation)

---

## Overview

The **Publishing Workflow Module** manages the post-approval publication process across multiple target sites. It provides Publishers with structured checklists, asset download tracking, publication verification, and final handoff to QA. Each template type (Aggregators, OPR, MPP, ADOP, ADRE, Commercial) has its own checklist ensuring consistent publication standards.

**Position in System:** Final workflow stage after Marketing Manager approval, before QA verification.

---

## Purpose & Goals

### Primary Purpose

Provide Publishers with a structured, trackable workflow for publishing approved content to live websites, ensuring all required steps are completed and verified before marking projects as published.

### Goals

1. **Consistency:** Standardized checklists ensure uniform publication quality
2. **Accountability:** Track who published what and when
3. **Asset Management:** Streamline asset downloads and uploads
4. **Verification:** Confirm all publication steps completed
5. **URL Tracking:** Record published page URLs for QA validation
6. **Multi-Site Support:** Handle different website templates and requirements
7. **Progress Visibility:** Real-time status updates for stakeholders

---

## Key Features

### Core Capabilities

- ✅ **Publish Queue** - Dedicated view for approved projects awaiting publication
- ✅ **Site-Specific Checklists** - Customized steps for Aggregators, OPR, MPP, ADOP, ADRE, Commercial
- ✅ **Asset Download Tracking** - Monitor which assets have been downloaded
- ✅ **Step-by-Step Progress** - Track completion of each publication task
- ✅ **URL Submission** - Record published page URL for verification
- ✅ **Publication Verification** - Confirm page is live before marking complete
- ✅ **Batch Publishing** - Manage multiple projects simultaneously
- ✅ **Rollback Capability** - Unpublish and return to approved state if needed
- ✅ **Deadline Tracking** - Monitor publication SLAs
- ✅ **Handoff to QA** - Automatic transition to QA verification after publication

### Publishing Checklists by Template Type

**Aggregators (24+ third-party domains):**
1. Download project assets
2. Add to aggregator database
3. Upload thumbnail image
4. Configure comparison filters
5. Add pricing data
6. Set featured status
7. Publish and verify listing

**OPR (opr.ae):**
1. Download assets (images, floor plans, ZIP)
2. Create new project page in WordPress
3. Upload hero image and gallery images
4. Upload floor plans
5. Populate content from Google Sheet
6. Set meta title and description
7. Configure URL slug
8. Add internal links
9. Verify SEO settings
10. Publish page and record URL

**MPP (main-portal.com):**
1. Download assets
2. Create project listing
3. Upload property images
4. Populate content from Google Sheet
5. Configure SEO tags
6. Add location map
7. Publish and record URL

**ADOP (abudhabioffplan.ae):**
1. Download assets
2. Create project listing
3. Upload property images
4. Populate content from Google Sheet
5. Configure SEO tags
6. Add location map
7. Publish and record URL

**ADRE (secondary-market-portal.com):**
1. Download assets
2. Create ready property listing
3. Upload property images
4. Populate content from Google Sheet
5. Configure SEO tags
6. Publish and record URL

**Commercial (cre.main-portal.com):**
1. Download assets
2. Create project listing
3. Upload commercial property images
4. Add business amenities section
5. Populate ROI calculator data
6. Configure commercial SEO tags
7. Add location map
8. Publish and record URL

---

## Architecture

### Components Involved

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND LAYER                             │
├─────────────────────────────────────────────────────────┤
│ • PublishQueuePage.tsx       - Publisher queue view    │
│ • PublishChecklistPanel.tsx  - Step-by-step checklist  │
│ • AssetDownloadPanel.tsx     - Asset management        │
│ • PublishVerification.tsx    - URL verification        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           API LAYER (FastAPI)                           │
├─────────────────────────────────────────────────────────┤
│ • /api/publishing/queue      - Get publish queue       │
│ • /api/publishing/start      - Start publishing        │
│ • /api/publishing/checklist  - Update checklist step   │
│ • /api/publishing/complete   - Mark as published       │
│ • /api/publishing/verify     - Verify URL is live      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│            SERVICE LAYER (Python)                       │
├─────────────────────────────────────────────────────────┤
│ • PublishingService          - Business logic          │
│ • ChecklistManager           - Checklist templates     │
│ • URLVerificationService     - Verify page is live     │
│ • AssetDownloadTracker       - Track asset downloads   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│         DATABASE (Neon PostgreSQL)                      │
├─────────────────────────────────────────────────────────┤
│ • publication_checklists     - Checklist state         │
│ • publication_assets         - Asset download tracking │
│ • published_pages            - Published URLs          │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: `publication_checklists`

**Purpose:** Track publication checklist completion

```sql
CREATE TABLE publication_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    approval_id UUID REFERENCES project_approvals(id),

    -- Template Information
    template_type VARCHAR(50) NOT NULL,  -- 'aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial'
    checklist_template VARCHAR(50) NOT NULL,  -- Template version

    -- Checklist Steps (JSONB for flexibility)
    steps JSONB NOT NULL,
    -- Example:
    -- [
    --   {
    --     "id": "download_assets",
    --     "title": "Download assets (images, floor plans, ZIP)",
    --     "completed": true,
    --     "completed_at": "2025-01-15T10:00:00Z",
    --     "completed_by": "user_id"
    --   },
    --   {
    --     "id": "create_page",
    --     "title": "Create new project page in WordPress",
    --     "completed": false,
    --     "required": true
    --   }
    -- ]

    -- Progress Tracking
    total_steps INTEGER NOT NULL,
    completed_steps INTEGER DEFAULT 0,
    completion_percentage DECIMAL(5, 2),

    -- Publisher Assignment
    publisher_id UUID REFERENCES users(id),
    started_at TIMESTAMP,

    -- Publication Details
    published_url TEXT,
    published_at TIMESTAMP,

    -- Verification
    url_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    verification_status VARCHAR(50),  -- 'pending', 'verified', 'failed'

    -- Metadata
    notes TEXT,
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_approval FOREIGN KEY (approval_id) REFERENCES project_approvals(id),
    CONSTRAINT valid_template_type CHECK (template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial'))
);

CREATE INDEX idx_pub_checklists_project ON publication_checklists(project_id);
CREATE INDEX idx_pub_checklists_publisher ON publication_checklists(publisher_id);
CREATE INDEX idx_pub_checklists_template_type ON publication_checklists(template_type);
CREATE INDEX idx_pub_checklists_status ON publication_checklists(completed_steps, total_steps);
```

---

### Table: `publication_assets`

**Purpose:** Track asset downloads by Publishers

```sql
CREATE TABLE publication_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    checklist_id UUID REFERENCES publication_checklists(id),

    -- Asset Details
    asset_type VARCHAR(50) NOT NULL,
    -- Types: 'images_zip', 'floor_plans_zip', 'google_sheet', 'individual_image'

    asset_name VARCHAR(255),
    asset_url TEXT NOT NULL,
    file_size_bytes BIGINT,

    -- Download Tracking
    downloaded BOOLEAN DEFAULT false,
    downloaded_at TIMESTAMP,
    downloaded_by UUID REFERENCES users(id),
    download_count INTEGER DEFAULT 0,

    -- Upload Tracking
    uploaded_to_site BOOLEAN DEFAULT false,
    uploaded_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_checklist FOREIGN KEY (checklist_id) REFERENCES publication_checklists(id)
);

CREATE INDEX idx_pub_assets_project ON publication_assets(project_id);
CREATE INDEX idx_pub_assets_checklist ON publication_assets(checklist_id);
CREATE INDEX idx_pub_assets_downloaded ON publication_assets(downloaded);
```

---

### Table: `published_pages`

**Purpose:** Record published page URLs and metadata

```sql
CREATE TABLE published_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    checklist_id UUID REFERENCES publication_checklists(id),

    -- Page Information
    template_type VARCHAR(50) NOT NULL,
    page_url TEXT NOT NULL,
    page_title VARCHAR(255),
    meta_description VARCHAR(255),

    -- CMS Details (if applicable)
    cms_post_id VARCHAR(100),  -- WordPress post ID, etc.
    cms_status VARCHAR(50),    -- 'draft', 'published', 'scheduled'

    -- SEO
    canonical_url TEXT,
    robots_meta VARCHAR(50),   -- 'index,follow', etc.

    -- Performance
    page_load_time_ms INTEGER,
    mobile_friendly BOOLEAN,

    -- Verification
    is_live BOOLEAN DEFAULT false,
    last_verified_at TIMESTAMP,
    verification_error TEXT,

    -- Publisher
    published_by UUID REFERENCES users(id),
    published_at TIMESTAMP DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_checklist FOREIGN KEY (checklist_id) REFERENCES publication_checklists(id),
    CONSTRAINT unique_project_template UNIQUE (project_id, template_type)
);

CREATE INDEX idx_published_pages_project ON published_pages(project_id);
CREATE INDEX idx_published_pages_template_type ON published_pages(template_type);
CREATE INDEX idx_published_pages_url ON published_pages(page_url);
CREATE INDEX idx_published_pages_live ON published_pages(is_live);
```

---

## Publishing Checklists

### OPR Checklist Template

```json
{
  "template_id": "opr_v1",
  "template_type": "opr",
  "estimated_duration_minutes": 30,
  "steps": [
    {
      "id": "download_assets",
      "title": "Download all assets (images, floor plans, ZIP)",
      "description": "Download ZIP package from Google Drive",
      "required": true,
      "order": 1
    },
    {
      "id": "create_page",
      "title": "Create new project page in WordPress",
      "description": "Use 'Off-Plan Project' template",
      "required": true,
      "order": 2
    },
    {
      "id": "upload_hero_image",
      "title": "Upload hero image",
      "description": "Use first exterior image as hero",
      "required": true,
      "order": 3
    },
    {
      "id": "upload_gallery",
      "title": "Upload gallery images",
      "description": "Upload all interior and exterior images to gallery",
      "required": true,
      "order": 4
    },
    {
      "id": "upload_floor_plans",
      "title": "Upload floor plans",
      "description": "Add all floor plans to floor plan section",
      "required": true,
      "order": 5
    },
    {
      "id": "populate_content",
      "title": "Populate content from Google Sheet",
      "description": "Copy all content fields from Sheet to WordPress",
      "required": true,
      "order": 6
    },
    {
      "id": "set_meta_tags",
      "title": "Set meta title and description",
      "description": "Use SEO fields from Google Sheet",
      "required": true,
      "order": 7
    },
    {
      "id": "configure_url",
      "title": "Configure URL slug",
      "description": "Use suggested slug from Google Sheet",
      "required": true,
      "order": 8
    },
    {
      "id": "add_internal_links",
      "title": "Add internal links",
      "description": "Link to developer page and location page",
      "required": false,
      "order": 9
    },
    {
      "id": "verify_seo",
      "title": "Verify SEO settings",
      "description": "Check Yoast SEO score (target: green)",
      "required": true,
      "order": 10
    },
    {
      "id": "publish_page",
      "title": "Publish page",
      "description": "Click 'Publish' and record URL",
      "required": true,
      "order": 11
    }
  ]
}
```

---

### Commercial Checklist Template

```json
{
  "template_id": "commercial_v1",
  "template_type": "commercial",
  "estimated_duration_minutes": 25,
  "steps": [
    {
      "id": "download_assets",
      "title": "Download all assets",
      "required": true,
      "order": 1
    },
    {
      "id": "create_listing",
      "title": "Create commercial project listing",
      "required": true,
      "order": 2
    },
    {
      "id": "upload_images",
      "title": "Upload commercial property images",
      "required": true,
      "order": 3
    },
    {
      "id": "add_amenities",
      "title": "Add business amenities section",
      "required": true,
      "order": 4
    },
    {
      "id": "populate_roi",
      "title": "Populate ROI calculator data",
      "required": false,
      "order": 5
    },
    {
      "id": "configure_seo",
      "title": "Configure commercial SEO tags",
      "required": true,
      "order": 6
    },
    {
      "id": "add_map",
      "title": "Add location map",
      "required": true,
      "order": 7
    },
    {
      "id": "publish",
      "title": "Publish and record URL",
      "required": true,
      "order": 8
    }
  ]
}
```

---

## API Endpoints

### Queue Management

#### `GET /api/publishing/queue`

**Description:** Get publishing queue for Publisher

**Query Parameters:**
```typescript
{
  template_type?: 'aggregators' | 'opr' | 'mpp' | 'adop' | 'adre' | 'commercial';
  status?: 'pending' | 'in_progress' | 'completed';
}
```

**Response:**
```json
{
  "queue": [
    {
      "project_id": "uuid",
      "project_name": "Downtown Elite Residence",
      "template_type": "opr",
      "approval_id": "uuid",
      "approved_at": "2025-01-15T14:30:00Z",
      "checklist_id": "uuid",
      "progress": {
        "completed_steps": 3,
        "total_steps": 11,
        "percentage": 27
      },
      "publisher_id": "uuid",
      "started_at": "2025-01-15T15:00:00Z",
      "estimated_completion": "2025-01-15T15:30:00Z"
    }
  ]
}
```

---

### Publishing Actions

#### `POST /api/publishing/start`

**Description:** Start publishing a project

**Request Body:**
```json
{
  "project_id": "uuid",
  "approval_id": "uuid",
  "template_type": "opr"
}
```

**Response:**
```json
{
  "checklist_id": "uuid",
  "template_type": "opr",
  "total_steps": 11,
  "steps": [
    {
      "id": "download_assets",
      "title": "Download all assets",
      "completed": false,
      "required": true,
      "order": 1
    }
  ],
  "assets": [
    {
      "asset_type": "images_zip",
      "asset_name": "downtown-elite-assets.zip",
      "asset_url": "https://storage.googleapis.com/...",
      "file_size_bytes": 8900000
    }
  ]
}
```

---

#### `PUT /api/publishing/checklist/{checklist_id}/step`

**Description:** Update checklist step completion

**Request Body:**
```json
{
  "step_id": "download_assets",
  "completed": true,
  "notes": "All assets downloaded successfully"
}
```

**Response:**
```json
{
  "checklist_id": "uuid",
  "step_id": "download_assets",
  "completed": true,
  "completed_at": "2025-01-15T15:05:00Z",
  "progress": {
    "completed_steps": 1,
    "total_steps": 11,
    "percentage": 9
  }
}
```

---

#### `POST /api/publishing/complete`

**Description:** Mark project as published

**Request Body:**
```json
{
  "checklist_id": "uuid",
  "published_url": "https://offplanreviews.com/projects/downtown-elite-residence",
  "cms_post_id": "12345",
  "notes": "Published successfully, all steps completed"
}
```

**Response:**
```json
{
  "success": true,
  "published_page_id": "uuid",
  "published_url": "https://offplanreviews.com/projects/downtown-elite-residence",
  "published_at": "2025-01-15T15:30:00Z",
  "verification_status": "pending",
  "next_step": "qa_verification"
}
```

---

#### `POST /api/publishing/verify-url`

**Description:** Verify published URL is live

**Request Body:**
```json
{
  "published_page_id": "uuid"
}
```

**Response:**
```json
{
  "is_live": true,
  "status_code": 200,
  "page_title": "Downtown Elite Residence | Off-Plan Dubai",
  "meta_description": "Luxury residential tower by Emaar...",
  "page_load_time_ms": 850,
  "mobile_friendly": true,
  "verified_at": "2025-01-15T15:35:00Z"
}
```

---

## UI Components

### PublishQueuePage.tsx

**Location:** `frontend/src/pages/PublishQueuePage.tsx`

**Features:**
- Table of approved projects awaiting publication
- Filter by template type (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
- Sort by approval date, priority
- Quick actions: Start Publishing
- Progress indicators for in-progress publications

---

### PublishChecklistPanel.tsx

**Location:** `frontend/src/components/PublishChecklistPanel.tsx`

**Features:**
- Step-by-step checklist display
- Check/uncheck steps
- Progress bar
- Required vs optional step indicators
- Notes field for each step
- Asset download links

---

### AssetDownloadPanel.tsx

**Location:** `frontend/src/components/AssetDownloadPanel.tsx`

**Features:**
- List of all project assets
- Download buttons with file size
- Download status indicators
- Bulk download all option
- Google Drive folder link

---

## Workflow Diagrams

### Publishing Workflow

```
APPROVED PROJECT
       │
       ▼
┌──────────────────────────────────┐
│  Publisher Queue                 │
│  - View approved projects        │
│  - Select project to publish     │
└──────────┬───────────────────────┘
           │
           │ Click "Start Publishing"
           ▼
┌──────────────────────────────────┐
│  Load Checklist Template         │
│  - Aggregators: 7 steps          │
│  - OPR: 10 steps                 │
│  - MPP: 7 steps                  │
│  - ADOP: 7 steps                 │
│  - ADRE: 6 steps                 │
│  - Commercial: 8 steps           │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Step 1: Download Assets         │
│  ✅ Downloaded                    │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Step 2: Create Page             │
│  ✅ Created                       │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Step 3: Upload Images           │
│  ✅ Uploaded                      │
└──────────┬───────────────────────┘
           │
          ...
           │
           ▼
┌──────────────────────────────────┐
│  Step 11: Publish Page           │
│  ✅ Published                     │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Submit Published URL            │
│  - Enter page URL                │
│  - Verify URL is live            │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  URL Verification                │
│  - HTTP status check (200 OK)   │
│  - Page title verification       │
│  - Mobile-friendly check         │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Mark as Published               │
│  - Update project status         │
│  - Trigger QA notification       │
│  - Record completion time        │
└──────────┬───────────────────────┘
           │
           ▼
    HANDOFF TO QA
```

---

## Code Examples

### Backend: Publishing Service

```python
# backend/app/services/publishing_service.py
from typing import Dict, List
from uuid import UUID
import httpx
from app.models.publication_checklist import PublicationChecklist
from app.services.checklist_manager import ChecklistManager
from app.services.url_verification_service import URLVerificationService

class PublishingService:
    def __init__(self, db):
        self.db = db
        self.checklist_manager = ChecklistManager()
        self.url_verifier = URLVerificationService()

    async def start_publishing(
        self,
        project_id: UUID,
        approval_id: UUID,
        publisher_id: UUID,
        template_type: str
    ) -> Dict:
        """Initiate publishing workflow"""

        # Load checklist template
        template = self.checklist_manager.get_template(template_type)

        # Create checklist record
        checklist = PublicationChecklist(
            project_id=project_id,
            approval_id=approval_id,
            publisher_id=publisher_id,
            template_type=template_type,
            checklist_template=template['template_id'],
            steps=template['steps'],
            total_steps=len(template['steps']),
            started_at=datetime.utcnow(),
            estimated_duration_minutes=template['estimated_duration_minutes']
        )

        self.db.add(checklist)
        await self.db.commit()

        # Get project assets
        assets = await self._get_project_assets(project_id)

        return {
            'checklist_id': checklist.id,
            'template_type': template_type,
            'steps': template['steps'],
            'assets': assets
        }

    async def complete_publishing(
        self,
        checklist_id: UUID,
        published_url: str,
        cms_post_id: str = None
    ) -> Dict:
        """Mark project as published"""

        checklist = await self._get_checklist(checklist_id)

        # Verify all required steps completed
        incomplete_required = self._check_required_steps(checklist.steps)
        if incomplete_required:
            raise ValueError(
                f"Required steps not completed: {incomplete_required}"
            )

        # Verify URL is live
        verification = await self.url_verifier.verify_url(published_url)

        if not verification['is_live']:
            raise ValueError(
                f"URL verification failed: {verification['error']}"
            )

        # Create published page record
        published_page = PublishedPage(
            project_id=checklist.project_id,
            checklist_id=checklist_id,
            template_type=checklist.template_type,
            page_url=published_url,
            cms_post_id=cms_post_id,
            is_live=True,
            published_by=checklist.publisher_id,
            published_at=datetime.utcnow()
        )

        self.db.add(published_page)

        # Update checklist
        checklist.published_url = published_url
        checklist.published_at = datetime.utcnow()
        checklist.url_verified = True
        checklist.verified_at = datetime.utcnow()

        await self.db.commit()

        # Notify QA team
        await self._notify_qa_team(checklist.project_id, published_url)

        return {
            'success': True,
            'published_url': published_url,
            'verification': verification
        }
```

---

## Configuration

### Environment Variables

```bash
# Publishing Settings
PUBLISHING_SLA_DAYS=3
ENABLE_URL_VERIFICATION=true
URL_VERIFICATION_TIMEOUT_SECONDS=10

# Checklist Templates
AGGREGATORS_CHECKLIST_VERSION=v1
OPR_CHECKLIST_VERSION=v1
MPP_CHECKLIST_VERSION=v1
ADOP_CHECKLIST_VERSION=v1
ADRE_CHECKLIST_VERSION=v1
COMMERCIAL_CHECKLIST_VERSION=v1

# Asset Management
ENABLE_ASSET_DOWNLOAD_TRACKING=true
ASSET_DOWNLOAD_TIMEOUT_MINUTES=30
```

---

## Related Documentation

### Core Documentation
- [Modules > Approval Workflow](./APPROVAL_WORKFLOW.md) - Previous workflow stage
- [Modules > QA Module](./QA_MODULE.md) - Next workflow stage
- [Modules > Project Database](./PROJECT_DATABASE.md) - Status updates

### Integration Points
- [Integrations > Google Drive](../05-integrations/GOOGLE_DRIVE.md) - Asset downloads
- [Modules > Notifications](./NOTIFICATIONS.md) - Status alerts

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Backend Team
**Contact:** backend-team@your-domain.com
