# Module: Project Database

**Module Number:** 0
**Category:** Data Management
**Last Updated:** 2026-01-15
**Status:** Core Module

---

## Table of Contents

1. [Overview](#overview)
2. [Purpose & Goals](#purpose--goals)
3. [Key Features](#key-features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [UI Components](#ui-components)
8. [Data Flow](#data-flow)
9. [Code Examples](#code-examples)
10. [Configuration](#configuration)
11. [Related Documentation](#related-documentation)

---

## Overview

The **Project Database** is the central repository of all processed real estate projects in the PDP Automation system. It stores comprehensive project information including metadata, content, images, floor plans, and full edit history, providing a complete CRUD interface for managing projects throughout their lifecycle.

**Position in System:** Hub module connecting all other modules (material preparation, content generation, approval workflow, QA, and publishing).

---

## Purpose & Goals

### Primary Purpose

Serve as the single source of truth for all project data, enabling:
- Centralized storage of extracted and generated project information
- Full-text search and advanced filtering across all fields
- Complete audit trail of all changes
- Data export in multiple formats (Excel, CSV, PDF, JSON)
- Custom field extensibility for organization-specific requirements

### Goals

1. **Data Integrity:** Maintain accurate, version-controlled project records
2. **Accessibility:** Enable quick search and retrieval by any team member
3. **Flexibility:** Support custom fields without schema migrations
4. **Auditability:** Track all changes with user attribution and timestamps
5. **Export Capability:** Provide data in formats needed by stakeholders

---

## Key Features

### Core Capabilities

- ✅ **Full CRUD Operations** - Create, read, update, delete projects
- ✅ **Advanced Search** - Full-text search across all fields
- ✅ **Multi-Field Filtering** - Filter by developer, location, price range, date, emirate, status
- ✅ **Custom Fields** - Unlimited user-defined fields without database changes
- ✅ **Revision History** - Complete audit trail of all edits
- ✅ **Batch Operations** - Bulk updates and exports
- ✅ **Data Export** - Export to Excel, CSV, PDF, JSON
- ✅ **Image Management** - Link and manage categorized images
- ✅ **Floor Plan Management** - Associate floor plans with metadata
- ✅ **Permission Control** - Role-based access (view, edit, admin)

### Data Categories Stored

**Essential Fields:**
- Project name, developer, location, emirate
- Starting price, price per sqft, handover date
- Payment plan, property types, unit sizes
- Project status, timeline, completion percentage

**Content Fields:**
- Meta title, meta description, URL slug
- H1 heading, overview text (multi-paragraph)
- Amenities list, FAQ sections
- SEO keywords, alt tags

**Media Assets:**
- Categorized images (interior, exterior, amenity, logo)
- Floor plans with extracted data
- Links to Google Drive folders
- ZIP package download URLs

**Metadata:**
- Created date, updated date, user attribution
- Source PDF information
- Processing status, QA results
- Approval status, publication status

---

## Architecture

### Components Involved

```
┌─────────────────────────────────────────────────────┐
│              FRONTEND LAYER                         │
├─────────────────────────────────────────────────────┤
│ • ProjectsListPage.tsx    - Browse/search projects │
│ • ProjectDetailPage.tsx   - View/edit single       │
│ • ProjectExportPage.tsx   - Export wizard          │
│ • CustomFieldsEditor.tsx  - Manage custom fields   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              API LAYER (FastAPI)                    │
├─────────────────────────────────────────────────────┤
│ • /api/projects              - CRUD operations     │
│ • /api/projects/search       - Full-text search    │
│ • /api/projects/export       - Data export         │
│ • /api/projects/{id}/history - Revision tracking   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            SERVICE LAYER (Python)                   │
├─────────────────────────────────────────────────────┤
│ • ProjectService       - Business logic            │
│ • ProjectRepository    - Data access               │
│ • ExportService        - Format conversion         │
│ • SearchService        - Full-text indexing        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│         DATABASE (Neon PostgreSQL)                  │
├─────────────────────────────────────────────────────┤
│ • projects              - Main project table       │
│ • project_floor_plans   - Floor plan metadata      │
│ • project_images        - Image categorization     │
│ • project_revisions     - Audit trail              │
│ • custom_fields         - User-defined fields      │
└─────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: `projects`

**Purpose:** Main project storage table

```sql
CREATE TABLE projects (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    developer VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    emirate VARCHAR(100),

    -- Pricing
    starting_price DECIMAL(15, 2),
    price_per_sqft DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'AED',

    -- Dates
    handover_date DATE,
    launch_date DATE,

    -- Property Details
    property_types TEXT[],  -- Array: ['1BR', '2BR', '3BR', 'Villa']
    unit_sizes TEXT,        -- e.g., "650-1200 sqft"
    total_units INTEGER,

    -- Payment
    payment_plan TEXT,

    -- Content (SEO-optimized)
    meta_title VARCHAR(60),
    meta_description VARCHAR(160),
    url_slug VARCHAR(255) UNIQUE,
    h1_heading VARCHAR(255),
    overview TEXT,
    amenities TEXT[],       -- Array of amenity names

    -- FAQs (JSON array)
    faqs JSONB DEFAULT '[]',  -- [{"question": "...", "answer": "..."}]

    -- Custom Fields (extensible)
    custom_fields JSONB DEFAULT '{}',  -- {"field_name": "value", ...}

    -- Media Links
    google_drive_folder_url TEXT,
    zip_package_url TEXT,

    -- Status Tracking
    status VARCHAR(50) DEFAULT 'draft',
    -- Status values: draft, processing, pending_approval, approved,
    --                publishing, published, archived

    -- Processing Metadata
    source_pdf_url TEXT,
    processing_job_id UUID,
    extraction_quality_score DECIMAL(3, 2),  -- 0.00 to 1.00

    -- Workflow Status
    is_qa_approved BOOLEAN DEFAULT false,
    is_marketing_approved BOOLEAN DEFAULT false,
    is_published BOOLEAN DEFAULT false,
    published_url TEXT,
    published_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),

    -- Indexes for performance
    CONSTRAINT valid_price CHECK (starting_price >= 0),
    CONSTRAINT valid_quality CHECK (extraction_quality_score BETWEEN 0 AND 1)
);

-- Indexes
CREATE INDEX idx_projects_name ON projects USING gin(to_tsvector('english', name));
CREATE INDEX idx_projects_developer ON projects(developer);
CREATE INDEX idx_projects_location ON projects(location);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX idx_projects_price ON projects(starting_price);
CREATE INDEX idx_projects_custom_fields ON projects USING gin(custom_fields);
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

    -- Extracted Data (from Claude Sonnet 4.5 vision)
    extracted_data JSONB,          -- Raw extraction: dimensions, features, etc.

    -- File References
    image_url TEXT NOT NULL,
    google_drive_url TEXT,
    gcs_blob_path TEXT,

    -- Metadata
    is_duplicate BOOLEAN DEFAULT false,
    quality_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_floor_plans_project ON project_floor_plans(project_id);
CREATE INDEX idx_floor_plans_unit_type ON project_floor_plans(unit_type);
```

---

### Table: `project_images`

**Purpose:** Categorized image storage

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

    -- Storage Locations
    gcs_blob_path TEXT NOT NULL,
    google_drive_url TEXT,
    public_url TEXT,

    -- Metadata
    classification_confidence DECIMAL(3, 2),
    alt_text TEXT,
    has_watermark BOOLEAN DEFAULT false,
    watermark_removed BOOLEAN DEFAULT false,

    -- Order for display
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT valid_category CHECK (category IN ('interior', 'exterior', 'amenity', 'logo', 'other'))
);

CREATE INDEX idx_images_project ON project_images(project_id);
CREATE INDEX idx_images_category ON project_images(category);
CREATE INDEX idx_images_display_order ON project_images(project_id, display_order);
```

---

### Table: `project_revisions`

**Purpose:** Complete audit trail of all changes

```sql
CREATE TABLE project_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Change Details
    changed_fields JSONB,  -- {"field_name": {"old": "...", "new": "..."}}
    change_summary TEXT,

    -- User Attribution
    user_id UUID REFERENCES users(id),
    user_email VARCHAR(255),

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),

    -- Change Type
    change_type VARCHAR(50),
    -- Types: 'created', 'updated', 'approved', 'published', 'archived'

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_revisions_project ON project_revisions(project_id, created_at DESC);
CREATE INDEX idx_revisions_user ON project_revisions(user_id);
```

---

### Table: `custom_fields`

**Purpose:** Define user-created custom fields

```sql
CREATE TABLE custom_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Field Definition
    field_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    -- Types: 'text', 'number', 'date', 'boolean', 'select', 'multiselect'

    -- Options (for select/multiselect)
    options JSONB DEFAULT '[]',  -- ["Option 1", "Option 2", ...]

    -- Validation
    is_required BOOLEAN DEFAULT false,
    default_value TEXT,

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_field_type CHECK (field_type IN ('text', 'number', 'date', 'boolean', 'select', 'multiselect'))
);

CREATE INDEX idx_custom_fields_name ON custom_fields(field_name);
```

---

## API Endpoints

### Project CRUD

#### `GET /api/projects`

**Description:** List projects with filtering and pagination

**Query Parameters:**
```typescript
{
  page?: number;           // Default: 1
  limit?: number;          // Default: 20, max: 100
  search?: string;         // Full-text search
  developer?: string;      // Filter by developer
  location?: string;       // Filter by location
  emirate?: string;        // Filter by emirate
  status?: string;         // Filter by status
  min_price?: number;      // Minimum price
  max_price?: number;      // Maximum price
  created_after?: string;  // ISO date
  created_before?: string; // ISO date
  sort_by?: string;        // Field to sort by
  sort_order?: 'asc'|'desc'; // Sort direction
}
```

**Response:**
```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "Downtown Elite Residence",
      "developer": "Emaar Properties",
      "location": "Downtown Dubai",
      "starting_price": 1200000,
      "status": "published",
      "created_at": "2025-01-10T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "limit": 20,
    "pages": 8
  }
}
```

---

#### `GET /api/projects/{id}`

**Description:** Get detailed project information

**Response:**
```json
{
  "id": "uuid",
  "name": "Downtown Elite Residence",
  "developer": "Emaar Properties",
  "location": "Downtown Dubai",
  "emirate": "Dubai",
  "starting_price": 1200000,
  "price_per_sqft": 1850,
  "handover_date": "2026-06-30",
  "property_types": ["1BR", "2BR", "3BR", "Penthouse"],
  "amenities": ["Infinity Pool", "Gym", "Spa", "Concierge"],
  "overview": "Luxury residential tower...",
  "meta_title": "Downtown Elite Residence | Off-Plan Dubai",
  "url_slug": "downtown-elite-residence",
  "status": "published",
  "images": {
    "interior": 10,
    "exterior": 8,
    "amenity": 5
  },
  "floor_plans": 4,
  "google_drive_folder_url": "https://drive.google.com/...",
  "custom_fields": {
    "sales_office_location": "Business Bay"
  },
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-12T15:30:00Z"
}
```

---

#### `POST /api/projects`

**Description:** Create new project

**Request Body:**
```json
{
  "name": "Project Name",
  "developer": "Developer Name",
  "location": "Location",
  "starting_price": 1000000,
  "source_pdf_url": "gs://bucket/uploads/job-123/original.pdf"
}
```

**Response:** 201 Created with full project object

---

#### `PUT /api/projects/{id}`

**Description:** Update project (tracks revision)

**Request Body:** Partial project update
```json
{
  "starting_price": 1150000,
  "handover_date": "2026-12-31"
}
```

**Response:** 200 OK with updated project object

---

#### `DELETE /api/projects/{id}`

**Description:** Soft delete project (admin only)

**Response:** 204 No Content

---

### Search & Filter

#### `POST /api/projects/search`

**Description:** Advanced full-text search with filters

**Request Body:**
```json
{
  "query": "luxury waterfront",
  "filters": {
    "developer": ["Emaar", "Nakheel"],
    "emirate": "Dubai",
    "min_price": 500000,
    "max_price": 3000000,
    "property_types": ["2BR", "3BR"],
    "handover_after": "2025-12-31"
  },
  "sort": {
    "field": "starting_price",
    "order": "asc"
  },
  "page": 1,
  "limit": 20
}
```

**Response:** Same as GET /api/projects

---

### Export

#### `POST /api/projects/export`

**Description:** Export projects to various formats

**Request Body:**
```json
{
  "project_ids": ["uuid1", "uuid2"],  // Or "all" for all projects
  "format": "excel",  // 'excel', 'csv', 'pdf', 'json'
  "fields": ["name", "developer", "price", "status"],  // Optional
  "filters": {}  // Optional: same as search filters
}
```

**Response:**
```json
{
  "download_url": "https://storage.googleapis.com/.../export.xlsx",
  "expires_at": "2025-01-15T12:00:00Z",
  "file_size_bytes": 245760
}
```

---

### Revision History

#### `GET /api/projects/{id}/history`

**Description:** Get complete revision history

**Response:**
```json
{
  "revisions": [
    {
      "id": "uuid",
      "change_type": "updated",
      "change_summary": "Updated starting price",
      "changed_fields": {
        "starting_price": {
          "old": 1000000,
          "new": 1150000
        }
      },
      "user_email": "editor@your-domain.com",
      "created_at": "2025-01-12T15:30:00Z"
    }
  ]
}
```

---

### Custom Fields

#### `GET /api/custom-fields`

**Description:** List all custom field definitions

#### `POST /api/custom-fields`

**Description:** Create new custom field

**Request Body:**
```json
{
  "field_name": "sales_office_location",
  "display_name": "Sales Office Location",
  "field_type": "text",
  "is_required": false
}
```

---

## UI Components

### ProjectsListPage.tsx

**Location:** `frontend/src/pages/ProjectsListPage.tsx`

**Features:**
- Searchable data table with all projects
- Inline filters (developer, location, price range, status)
- Sortable columns
- Bulk selection for exports
- Quick actions: View, Edit, Export

**Key Libraries:**
- `@tanstack/react-table` - Data table
- `react-query` - Data fetching
- `zustand` - State management

---

### ProjectDetailPage.tsx

**Location:** `frontend/src/pages/ProjectDetailPage.tsx`

**Features:**
- Full project information display
- Inline editing (all fields)
- Image gallery with category tabs
- Floor plan viewer
- Revision history timeline
- Quick actions: Save, Submit for Approval, Export

---

### ProjectExportPage.tsx

**Location:** `frontend/src/pages/ProjectExportPage.tsx`

**Features:**
- Export format selection (Excel, CSV, PDF, JSON)
- Field selection (choose which columns to export)
- Filter application (export filtered subset)
- Progress indicator
- Download link generation

---

### CustomFieldsEditor.tsx

**Location:** `frontend/src/components/CustomFieldsEditor.tsx`

**Features:**
- Add new custom fields
- Define field types and validation
- Set default values
- Delete unused fields

---

## Data Flow

### Project Creation Flow

```
1. User uploads PDF
        ↓
2. Text extraction (pymupdf4llm) → Claude Sonnet 4.5 structures data
        ↓
3. ProjectService.create() → Insert into projects table
        ↓
4. Image classification → Insert into project_images table
        ↓
5. Floor plan extraction → Insert into project_floor_plans table
        ↓
6. Upload to Google Drive → Update google_drive_folder_url
        ↓
7. Create revision record (change_type: 'created')
        ↓
8. Return complete project object to frontend
```

---

### Project Update Flow

```
1. User edits fields in ProjectDetailPage
        ↓
2. Frontend calls PUT /api/projects/{id}
        ↓
3. ProjectService.update()
        ├── Fetch current project state
        ├── Calculate changed fields (diff)
        ├── Update projects table
        ├── Insert revision record
        └── Trigger notifications (if status changed)
        ↓
4. Return updated project + revision info
        ↓
5. Frontend refreshes display
```

---

## Code Examples

### Backend: Project Service

```python
# backend/app/services/project_service.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.project import Project
from app.models.project_revision import ProjectRevision
from app.schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(
        self,
        data: ProjectCreate,
        user_id: UUID
    ) -> Project:
        """Create new project and record creation"""

        # Create project
        project = Project(
            **data.dict(),
            created_by=user_id,
            updated_by=user_id,
            status='draft'
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        # Record revision
        revision = ProjectRevision(
            project_id=project.id,
            user_id=user_id,
            change_type='created',
            change_summary=f'Project "{project.name}" created',
            changed_fields={}
        )
        self.db.add(revision)
        await self.db.commit()

        return project

    async def update_project(
        self,
        project_id: UUID,
        data: ProjectUpdate,
        user_id: UUID
    ) -> Project:
        """Update project and track changes"""

        # Fetch current project
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError("Project not found")

        # Calculate changes
        changed_fields = {}
        for field, new_value in data.dict(exclude_unset=True).items():
            old_value = getattr(project, field)
            if old_value != new_value:
                changed_fields[field] = {
                    "old": old_value,
                    "new": new_value
                }
                setattr(project, field, new_value)

        # Update metadata
        project.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(project)

        # Record revision if changes made
        if changed_fields:
            revision = ProjectRevision(
                project_id=project.id,
                user_id=user_id,
                change_type='updated',
                change_summary=f'Updated {len(changed_fields)} field(s)',
                changed_fields=changed_fields
            )
            self.db.add(revision)
            await self.db.commit()

        return project

    async def search_projects(
        self,
        query: str,
        filters: Dict[str, Any],
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Project], int]:
        """Full-text search with filters"""

        # Build query
        stmt = select(Project)

        # Full-text search
        if query:
            stmt = stmt.where(
                Project.name.ilike(f'%{query}%') |
                Project.developer.ilike(f'%{query}%') |
                Project.location.ilike(f'%{query}%')
            )

        # Apply filters
        if filters.get('developer'):
            stmt = stmt.where(Project.developer.in_(filters['developer']))

        if filters.get('emirate'):
            stmt = stmt.where(Project.emirate == filters['emirate'])

        if filters.get('min_price'):
            stmt = stmt.where(Project.starting_price >= filters['min_price'])

        if filters.get('max_price'):
            stmt = stmt.where(Project.starting_price <= filters['max_price'])

        # Count total
        count_result = await self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        )
        total = count_result.scalar()

        # Pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        # Execute
        result = await self.db.execute(stmt)
        projects = result.scalars().all()

        return projects, total
```

---

### Frontend: Projects List Component

```typescript
// frontend/src/pages/ProjectsListPage.tsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/lib/api';
import { DataTable } from '@/components/DataTable';
import { SearchBar } from '@/components/SearchBar';
import { FilterPanel } from '@/components/FilterPanel';

export function ProjectsListPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({});
  const [page, setPage] = useState(1);

  // Fetch projects
  const { data, isLoading } = useQuery({
    queryKey: ['projects', searchQuery, filters, page],
    queryFn: () => projectsApi.list({
      search: searchQuery,
      ...filters,
      page,
      limit: 20
    })
  });

  const columns = [
    { accessorKey: 'name', header: 'Project Name' },
    { accessorKey: 'developer', header: 'Developer' },
    { accessorKey: 'location', header: 'Location' },
    {
      accessorKey: 'starting_price',
      header: 'Price (AED)',
      cell: (info) => info.getValue().toLocaleString()
    },
    { accessorKey: 'status', header: 'Status' },
    { accessorKey: 'created_at', header: 'Created', cell: (info) => formatDate(info.getValue()) }
  ];

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Projects Database</h1>

      <div className="flex gap-4 mb-6">
        <SearchBar
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search projects, developers, locations..."
        />
        <FilterPanel filters={filters} onChange={setFilters} />
      </div>

      <DataTable
        columns={columns}
        data={data?.projects || []}
        pagination={{
          page,
          total: data?.pagination.total || 0,
          onPageChange: setPage
        }}
        isLoading={isLoading}
      />
    </div>
  );
}
```

---

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Project Settings
MAX_CUSTOM_FIELDS=50
MAX_PROJECT_IMAGES=50
MAX_FLOOR_PLANS=20

# Export Settings
EXPORT_SIGNED_URL_EXPIRY_MINUTES=60
MAX_EXPORT_SIZE_MB=50
```

### Feature Flags

```python
# backend/app/config.py
class Settings(BaseSettings):
    # Features
    ENABLE_CUSTOM_FIELDS: bool = True
    ENABLE_EXPORT_PDF: bool = True
    ENABLE_BULK_OPERATIONS: bool = True

    # Limits
    MAX_PROJECTS_PER_PAGE: int = 100
    MAX_EXPORT_PROJECTS: int = 1000

    # Performance
    ENABLE_QUERY_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 300
```

---

## Related Documentation

### Core Documentation
- [Architecture > Data Model](../01-architecture/DATA_MODEL.md) - Database design decisions
- [Architecture > API Design](../01-architecture/API_DESIGN.md) - API patterns and conventions
- [Backend > Database](../04-backend/DATABASE.md) - Schema migrations and management

### Integration Points
- [Modules > Material Preparation](./MATERIAL_PREPARATION.md) - Image/floor plan linking
- [Modules > Content Generation](./CONTENT_GENERATION.md) - Content storage
- [Modules > Approval Workflow](./APPROVAL_WORKFLOW.md) - Status updates
- [Modules > QA Module](./QA_MODULE.md) - Quality tracking

### Frontend
- [Frontend > Pages](../03-frontend/PAGES.md) - UI implementation
- [Frontend > State Management](../03-frontend/STATE_MANAGEMENT.md) - Data flow

### Testing
- [Testing > Unit Tests](../07-testing/UNIT_TESTS.md) - Service and repository tests
- [Testing > Integration Tests](../07-testing/INTEGRATION_TESTS.md) - API endpoint tests

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Backend Team
**Contact:** backend-team@your-domain.com
