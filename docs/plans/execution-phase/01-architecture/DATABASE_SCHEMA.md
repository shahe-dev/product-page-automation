# Database Schema

**Last Updated:** 2026-01-15
**Related Documents:**
- [System Architecture](./SYSTEM_ARCHITECTURE.md)
- [Data Flow](./DATA_FLOW.md)
- [API Design](./API_DESIGN.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Database Technology](#database-technology)
3. [Schema Overview](#schema-overview)
4. [Core Tables](#core-tables)
5. [Relationships](#relationships)
6. [Indexes](#indexes)
7. [Constraints and Validations](#constraints-and-validations)
8. [JSONB Fields](#jsonb-fields)
9. [Full-Text Search](#full-text-search)
10. [Migrations](#migrations)
11. [Related Documentation](#related-documentation)

---

## Overview

The PDP Automation v.3 system uses **Neon PostgreSQL** (serverless) as its primary database. The schema is designed to support:

- **Multi-user collaboration** with role-based access control
- **Project lifecycle tracking** from PDF upload to publication
- **Revision history** for audit trails
- **Flexible custom fields** using JSONB columns
- **Full-text search** for projects and content
- **Background job tracking** with detailed step monitoring
- **QA validation** at multiple checkpoints
- **Version-controlled prompts** for AI content generation

---

## Database Technology

### Neon PostgreSQL

**Provider:** Neon (neon.tech)
**Type:** Serverless PostgreSQL
**Version:** PostgreSQL 16+

**Configuration:**

| Environment | Tier | Storage | Compute | Cost |
|-------------|------|---------|---------|------|
| Development | Free | 10 GB | 1 vCPU, 1 GB RAM | $0/month |
| Production | Scale | 100 GB | 2 vCPU, 4 GB RAM | $19/month |

**Key Features:**
- **Serverless:** Scales to zero when inactive
- **Connection Pooling:** Built-in pooling (max 100 connections)
- **Automated Backups:** Point-in-time recovery included
- **High Availability:** Multi-AZ deployment
- **ACID Compliance:** Full transactional support

**Connection String:**
```
postgresql://user:password@ep-abc-123.us-east-1.aws.neon.tech/pdp_automation?sslmode=require
```

---

## Schema Overview

### Entity Relationship Diagram

```
┌─────────────┐
│    users    │
└──────┬──────┘
       │
       │ 1:N
       │
       ▼
┌─────────────┐      1:N      ┌───────────────────┐
│  projects   │◄───────────────┤ project_images    │
└──────┬──────┘                └───────────────────┘
       │
       │ 1:N                    ┌───────────────────┐
       ├────────────────────────┤ project_floor_plans│
       │                        └───────────────────┘
       │
       │ 1:N                    ┌───────────────────┐
       ├────────────────────────┤ project_approvals │
       │                        └───────────────────┘
       │
       │ 1:N                    ┌───────────────────┐
       ├────────────────────────┤ project_revisions │
       │                        └───────────────────┘
       │
       │ 1:1                    ┌─────────────┐
       └────────────────────────┤    jobs     │
                                └──────┬──────┘
                                       │ 1:N
                                       │
                                       ▼
                                ┌─────────────┐
                                │  job_steps  │
                                └─────────────┘

┌─────────────┐      1:N      ┌───────────────────┐
│   prompts   │◄───────────────┤ prompt_versions   │
└─────────────┘                └───────────────────┘

┌───────────────┐
│qa_comparisons │
└───────────────┘

┌───────────────┐
│ notifications │
└───────────────┘

┌───────────────┐
│workflow_items │
└───────────────┘

┌─────────────┐
│ templates   │
└─────────────┘

┌─────────────────┐
│publication_     │
│checklists       │
└─────────────────┘

┌─────────────────┐
│execution_history│
└─────────────────┘

-- QA Module Tables --

┌───────────────┐      1:N      ┌─────────────┐
│qa_checkpoints │◄───────────────┤  qa_issues  │
└───────────────┘                └──────┬──────┘
                                        │ 1:N
                                        ▼
                                 ┌──────────────┐
                                 │ qa_overrides │
                                 └──────────────┘

-- Content Module Tables --

┌────────────────┐
│ extracted_data │
└────────────────┘

┌─────────────────┐      1:N      ┌──────────────────┐
│generated_content│◄───────────────┤content_qa_results│
└─────────────────┘                └──────────────────┘
```

---

## Core Tables

### users

**Purpose:** Store user accounts authenticated via Google OAuth.

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
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_role ON users(role);

-- Constraints
ALTER TABLE users ADD CONSTRAINT check_email_domain
    CHECK (email ~ '@mpd\.ae$');
```

**Fields:**
- `id` - Internal UUID for user
- `google_id` - Google OAuth user ID (unique)
- `email` - Email address (must be @your-domain.com)
- `name` - Full name from Google profile
- `picture_url` - Profile picture URL from Google
- `role` - User role: `admin` or `user`
- `is_active` - Account status (for soft deletion)
- `created_at` - Account creation timestamp
- `last_login_at` - Last login timestamp

---

### projects

**Purpose:** Central repository for all project data.

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

    -- JSONB fields for flexible data
    property_types JSONB DEFAULT '[]'::jsonb,  -- ["apartment", "villa"]
    unit_sizes JSONB DEFAULT '[]'::jsonb,      -- [{"type": "1BR", "sqft_min": 650}]
    amenities JSONB DEFAULT '[]'::jsonb,       -- ["Pool", "Gym"]
    features JSONB DEFAULT '[]'::jsonb,        -- ["Sea View", "Balcony"]

    -- Numeric fields
    total_units INTEGER,
    floors INTEGER,
    buildings INTEGER,

    -- Custom fields (user-added key-value pairs)
    custom_fields JSONB DEFAULT '{}'::jsonb,

    -- Media URLs
    original_pdf_url VARCHAR(500),
    processed_zip_url VARCHAR(500),
    sheet_url VARCHAR(500),

    -- Generated content
    generated_content JSONB DEFAULT '{}'::jsonb,

    -- Workflow status
    workflow_status VARCHAR(50) NOT NULL DEFAULT 'draft'
        CHECK (workflow_status IN (
            'draft', 'pending_approval', 'revision_requested',
            'approved', 'publishing', 'published', 'qa_verified', 'complete'
        )),

    -- Publication
    published_url VARCHAR(500),
    published_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified_by UUID REFERENCES users(id),
    last_modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_job_id UUID REFERENCES jobs(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_developer ON projects(developer);
CREATE INDEX idx_projects_emirate ON projects(emirate);
CREATE INDEX idx_projects_status ON projects(workflow_status);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX idx_projects_created_by ON projects(created_by);

-- Full-text search index
CREATE INDEX idx_projects_search ON projects
    USING gin(to_tsvector('english',
        coalesce(name, '') || ' ' ||
        coalesce(developer, '') || ' ' ||
        coalesce(location, '') || ' ' ||
        coalesce(description, '')
    ));

-- JSONB indexes for filtering
CREATE INDEX idx_projects_property_types ON projects USING gin(property_types);
CREATE INDEX idx_projects_amenities ON projects USING gin(amenities);
```

**Key Fields:**

**Core Data:**
- `name` - Project name
- `developer` - Developer/builder name
- `location` - Area/neighborhood
- `emirate` - Emirate (Dubai, Abu Dhabi, etc.)
- `starting_price` - Starting price in AED
- `price_per_sqft` - Price per square foot
- `handover_date` - Expected handover date
- `payment_plan` - Payment plan description

**JSONB Arrays:**
- `property_types` - Array of property types
- `unit_sizes` - Array of unit size objects
- `amenities` - Array of amenity strings
- `features` - Array of feature strings

**JSONB Object:**
- `custom_fields` - User-defined key-value pairs
- `generated_content` - AI-generated content fields

**Workflow:**
- `workflow_status` - Current stage in approval workflow
- `published_url` - URL of published page
- `published_at` - Publication timestamp

---

### project_images

**Purpose:** Store categorized images for each project.

```sql
CREATE TABLE project_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Image details
    category VARCHAR(50) NOT NULL
        CHECK (category IN ('interior', 'exterior', 'amenity', 'logo')),
    image_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),

    -- Image metadata
    width INTEGER,
    height INTEGER,
    file_size INTEGER,  -- in bytes
    format VARCHAR(10),  -- jpg, png, webp

    -- Display order
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_project_images_project_id ON project_images(project_id);
CREATE INDEX idx_project_images_category ON project_images(category);
CREATE INDEX idx_project_images_order ON project_images(project_id, display_order);
```

**Categories:**
- `interior` - Interior shots (living room, bedroom, kitchen)
- `exterior` - Building exterior and facade
- `amenity` - Amenities (pool, gym, lobby)
- `logo` - Developer logo

---

### project_floor_plans

**Purpose:** Store floor plan images with extracted data.

```sql
CREATE TABLE project_floor_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Floor plan details
    unit_type VARCHAR(50) NOT NULL,  -- "1BR", "2BR", "3BR", "Studio"
    bedrooms INTEGER,
    bathrooms INTEGER,
    total_sqft DECIMAL(10, 2),
    balcony_sqft DECIMAL(10, 2),
    builtup_sqft DECIMAL(10, 2),

    -- Image
    image_url VARCHAR(500) NOT NULL,

    -- Display order
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_project_floor_plans_project_id ON project_floor_plans(project_id);
CREATE INDEX idx_project_floor_plans_unit_type ON project_floor_plans(unit_type);
CREATE INDEX idx_project_floor_plans_order ON project_floor_plans(project_id, display_order);
```

---

### project_approvals

**Purpose:** Track approval workflow actions.

```sql
CREATE TABLE project_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Approval action
    action VARCHAR(50) NOT NULL
        CHECK (action IN ('submitted', 'approved', 'rejected', 'revision_requested')),

    -- Approver
    approver_id UUID NOT NULL REFERENCES users(id),
    comments TEXT,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_project_approvals_project_id ON project_approvals(project_id);
CREATE INDEX idx_project_approvals_approver_id ON project_approvals(approver_id);
CREATE INDEX idx_project_approvals_created_at ON project_approvals(created_at DESC);
```

---

### project_revisions

**Purpose:** Audit trail for all project field changes.

```sql
CREATE TABLE project_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Change details
    field VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,

    -- Changed by
    changed_by UUID NOT NULL REFERENCES users(id),
    change_reason TEXT,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_project_revisions_project_id ON project_revisions(project_id);
CREATE INDEX idx_project_revisions_field ON project_revisions(field);
CREATE INDEX idx_project_revisions_changed_by ON project_revisions(changed_by);
CREATE INDEX idx_project_revisions_created_at ON project_revisions(created_at DESC);
```

---

### jobs

**Purpose:** Track background processing jobs.

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Job configuration
    user_id UUID NOT NULL REFERENCES users(id),
    template_type VARCHAR(50) NOT NULL
        CHECK (template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')),
    template_id UUID REFERENCES templates(id),

    -- Job status
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0
        CHECK (progress >= 0 AND progress <= 100),
    current_step VARCHAR(100),

    -- Job result
    result JSONB,  -- {project_id, sheet_url, zip_url}
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_completed_at ON jobs(completed_at DESC);
```

**Status Flow:**
```
pending → processing → completed
                    → failed
                    → cancelled
```

---

### job_steps

**Purpose:** Detailed step tracking for each job.

```sql
CREATE TABLE job_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- Step details
    step_id VARCHAR(50) NOT NULL,  -- "upload", "extract_text", etc.
    label VARCHAR(100) NOT NULL,    -- "Upload PDF", "Extract text"
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')),

    -- Step result
    result JSONB,
    error_message TEXT,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_job_steps_job_id ON job_steps(job_id);
CREATE INDEX idx_job_steps_step_id ON job_steps(step_id);
CREATE INDEX idx_job_steps_status ON job_steps(status);
```

**Common Steps:**
1. `upload` - Upload PDF
2. `extract_text` - Extract text from PDF
3. `extract_images` - Extract images from PDF
4. `classify_images` - Classify images by category
5. `extract_floor_plans` - Extract floor plan data
6. `detect_watermarks` - Detect watermarks in images
7. `remove_watermarks` - Remove detected watermarks
8. `optimize_images` - Optimize images for web
9. `generate_content` - Generate SEO content
10. `qa_validation` - Run QA validation
11. `push_to_sheets` - Push content to Google Sheets
12. `package_zip` - Package images into ZIP

---

### prompts

**Purpose:** Version-controlled prompt library for AI content generation.

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Prompt identification
    name VARCHAR(100) NOT NULL,  -- "Meta Description", "Intro Paragraph"
    template_type VARCHAR(50) NOT NULL
        CHECK (template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')),
    content_variant VARCHAR(50) NOT NULL DEFAULT 'standard'
        CHECK (content_variant IN ('standard', 'luxury')),

    -- Prompt content (current version)
    content TEXT NOT NULL,
    character_limit INTEGER,

    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Metadata
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint: one active prompt per (template_type, content_variant, name)
    CONSTRAINT unique_active_prompt
        EXCLUDE (template_type WITH =, content_variant WITH =, name WITH =)
        WHERE (is_active = true)
);

-- Indexes
CREATE INDEX idx_prompts_template_type ON prompts(template_type);
CREATE INDEX idx_prompts_content_variant ON prompts(content_variant);
CREATE INDEX idx_prompts_name ON prompts(name);
CREATE INDEX idx_prompts_active ON prompts(is_active);
```

---

### prompt_versions

**Purpose:** Complete history of prompt changes.

```sql
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,

    -- Version details
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    character_limit INTEGER,

    -- Change tracking
    change_reason TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_prompt_versions_prompt_id ON prompt_versions(prompt_id);
CREATE INDEX idx_prompt_versions_version ON prompt_versions(prompt_id, version DESC);
CREATE INDEX idx_prompt_versions_created_at ON prompt_versions(created_at DESC);
```

---

### templates

**Purpose:** Website template configurations for Google Sheets.

```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Template identification
    name VARCHAR(100) NOT NULL,
    template_type VARCHAR(50) NOT NULL
        CHECK (template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')),
    content_variant VARCHAR(50) NOT NULL DEFAULT 'standard'
        CHECK (content_variant IN ('standard', 'luxury')),

    -- Google Sheets template
    sheet_template_url VARCHAR(500) NOT NULL,
    field_mappings JSONB NOT NULL,  -- {"meta_title": "B2", "meta_description": "B3"}

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_templates_template_type ON templates(template_type);
CREATE INDEX idx_templates_active ON templates(is_active);
```

---

### qa_comparisons

**Purpose:** Store QA checkpoint results.

```sql
CREATE TABLE qa_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Checkpoint type
    checkpoint_type VARCHAR(50) NOT NULL
        CHECK (checkpoint_type IN ('extraction', 'generation', 'publication')),

    -- Comparison result
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('passed', 'failed')),
    matches INTEGER,
    differences INTEGER,
    missing INTEGER,
    extra INTEGER,

    -- Detailed result
    result JSONB,  -- {differences: [...], missing: [...], extra: [...]}

    -- Performed by
    performed_by UUID NOT NULL REFERENCES users(id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_qa_comparisons_project_id ON qa_comparisons(project_id);
CREATE INDEX idx_qa_comparisons_checkpoint_type ON qa_comparisons(checkpoint_type);
CREATE INDEX idx_qa_comparisons_status ON qa_comparisons(status);
CREATE INDEX idx_qa_comparisons_performed_at ON qa_comparisons(performed_at DESC);
```

---

### notifications

**Purpose:** In-app notification system.

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Notification details
    type VARCHAR(50) NOT NULL
        CHECK (type IN ('info', 'success', 'warning', 'error', 'approval', 'mention')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    -- Related entity
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,

    -- Status
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

---

### workflow_items

**Purpose:** Kanban board items for workflow management.

```sql
CREATE TABLE workflow_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Assignment
    assigned_to UUID REFERENCES users(id),

    -- Display order in column
    display_order INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_workflow_items_project_id ON workflow_items(project_id);
CREATE INDEX idx_workflow_items_assigned_to ON workflow_items(assigned_to);
```

---

### publication_checklists

**Purpose:** Per-site publication tracking.

```sql
CREATE TABLE publication_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Publication template
    template_type VARCHAR(50) NOT NULL
        CHECK (template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')),

    -- Checklist items
    items JSONB NOT NULL,  -- [{task: "Upload images", completed: true}]

    -- Status
    all_completed BOOLEAN NOT NULL DEFAULT false,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_publication_checklists_project_id ON publication_checklists(project_id);
CREATE INDEX idx_publication_checklists_template_type ON publication_checklists(template_type);
```

---

### execution_history

**Purpose:** Complete audit log of all system actions.

```sql
CREATE TABLE execution_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Action details
    action VARCHAR(100) NOT NULL,  -- "project.created", "job.completed"
    entity_type VARCHAR(50) NOT NULL,  -- "project", "job", "prompt"
    entity_id UUID NOT NULL,

    -- User context
    user_id UUID REFERENCES users(id),
    ip_address INET,

    -- Action details
    details JSONB,  -- Full details of the action

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_execution_history_action ON execution_history(action);
CREATE INDEX idx_execution_history_entity ON execution_history(entity_type, entity_id);
CREATE INDEX idx_execution_history_user_id ON execution_history(user_id);
CREATE INDEX idx_execution_history_created_at ON execution_history(created_at DESC);

-- Partition by month for performance
CREATE TABLE execution_history_2026_01 PARTITION OF execution_history
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

---

## QA Module Tables

### qa_checkpoints

**Purpose:** Store QA checkpoint definitions and results.

```sql
CREATE TABLE qa_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    checkpoint_type VARCHAR(50) NOT NULL,  -- 'extraction', 'content', 'image', 'final'
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'passed', 'failed', 'skipped'
    score DECIMAL(5, 2),  -- 0.00 to 100.00
    issues_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    checked_at TIMESTAMP WITH TIME ZONE,
    checked_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CHECK (status IN ('pending', 'passed', 'failed', 'skipped')),
    CHECK (checkpoint_type IN ('extraction', 'content', 'image', 'final'))
);

CREATE INDEX idx_qa_checkpoints_project_id ON qa_checkpoints(project_id);
CREATE INDEX idx_qa_checkpoints_status ON qa_checkpoints(status);
```

### qa_issues

**Purpose:** Track QA issues found during validation.

```sql
CREATE TABLE qa_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checkpoint_id UUID REFERENCES qa_checkpoints(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL,  -- 'critical', 'high', 'medium', 'low'
    category VARCHAR(50) NOT NULL,  -- 'missing_data', 'format_error', 'brand_violation', etc.
    field_name VARCHAR(100),
    description TEXT NOT NULL,
    suggestion TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CHECK (severity IN ('critical', 'high', 'medium', 'low'))
);

CREATE INDEX idx_qa_issues_checkpoint_id ON qa_issues(checkpoint_id);
CREATE INDEX idx_qa_issues_project_id ON qa_issues(project_id);
CREATE INDEX idx_qa_issues_severity ON qa_issues(severity);
CREATE INDEX idx_qa_issues_is_resolved ON qa_issues(is_resolved);
```

### qa_overrides

**Purpose:** Store manual QA override decisions.

```sql
CREATE TABLE qa_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID REFERENCES qa_issues(id) ON DELETE CASCADE,
    override_type VARCHAR(20) NOT NULL,  -- 'accept', 'reject', 'defer'
    reason TEXT NOT NULL,
    overridden_by UUID REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CHECK (override_type IN ('accept', 'reject', 'defer'))
);

CREATE INDEX idx_qa_overrides_issue_id ON qa_overrides(issue_id);
```

---

## Content Module Tables

### extracted_data

**Purpose:** Store raw extracted data from PDF processing.

```sql
CREATE TABLE extracted_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    extraction_type VARCHAR(50) NOT NULL,  -- 'text', 'image', 'table', 'metadata'
    raw_content TEXT,
    structured_content JSONB,
    confidence_score DECIMAL(5, 4),  -- 0.0000 to 1.0000
    page_number INTEGER,
    extraction_method VARCHAR(50),  -- 'anthropic_vision', 'pypdf', 'ocr'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CHECK (extraction_type IN ('text', 'image', 'table', 'metadata'))
);

CREATE INDEX idx_extracted_data_project_id ON extracted_data(project_id);
CREATE INDEX idx_extracted_data_job_id ON extracted_data(job_id);
CREATE INDEX idx_extracted_data_type ON extracted_data(extraction_type);
```

### generated_content

**Purpose:** Store AI-generated content with version history.

```sql
CREATE TABLE generated_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,  -- 'title', 'meta_description', 'body_text', etc.
    template_type VARCHAR(50) NOT NULL,
    content_variant VARCHAR(50) NOT NULL DEFAULT 'standard',
    content TEXT NOT NULL,
    prompt_version_id UUID REFERENCES prompt_versions(id),
    generation_params JSONB DEFAULT '{}'::jsonb,
    is_approved BOOLEAN DEFAULT FALSE,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CHECK (template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')),
    CHECK (content_variant IN ('standard', 'luxury'))
);

CREATE INDEX idx_generated_content_project_id ON generated_content(project_id);
CREATE INDEX idx_generated_content_field ON generated_content(field_name);
CREATE INDEX idx_generated_content_template ON generated_content(template_type);
```

### content_qa_results

**Purpose:** Store content-specific QA validation results.

```sql
CREATE TABLE content_qa_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_content_id UUID REFERENCES generated_content(id) ON DELETE CASCADE,
    check_type VARCHAR(50) NOT NULL,  -- 'brand_compliance', 'seo_score', 'readability', 'factual_accuracy'
    passed BOOLEAN NOT NULL,
    score DECIMAL(5, 2),
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CHECK (check_type IN ('brand_compliance', 'seo_score', 'readability', 'factual_accuracy'))
);

CREATE INDEX idx_content_qa_results_content_id ON content_qa_results(generated_content_id);
CREATE INDEX idx_content_qa_results_check_type ON content_qa_results(check_type);
CREATE INDEX idx_content_qa_results_passed ON content_qa_results(passed);
```

---

## Relationships

### One-to-Many Relationships

| Parent Table | Child Table | Relationship |
|--------------|-------------|--------------|
| `users` | `projects` | User creates many projects |
| `projects` | `project_images` | Project has many images |
| `projects` | `project_floor_plans` | Project has many floor plans |
| `projects` | `project_approvals` | Project has many approval actions |
| `projects` | `project_revisions` | Project has many revisions |
| `projects` | `qa_checkpoints` | Project has many QA checkpoints |
| `projects` | `qa_issues` | Project has many QA issues |
| `projects` | `extracted_data` | Project has many extracted data records |
| `projects` | `generated_content` | Project has many generated content records |
| `users` | `jobs` | User creates many jobs |
| `jobs` | `job_steps` | Job has many steps |
| `jobs` | `extracted_data` | Job produces many extracted data records |
| `prompts` | `prompt_versions` | Prompt has many versions |
| `qa_checkpoints` | `qa_issues` | Checkpoint has many issues |
| `qa_issues` | `qa_overrides` | Issue has many overrides |
| `generated_content` | `content_qa_results` | Content has many QA results |

### One-to-One Relationships

| Table 1 | Table 2 | Relationship |
|---------|---------|--------------|
| `projects` | `jobs` | Project may be created by one job |

---

## Indexes

### Primary Indexes

All tables use UUID primary keys with `gen_random_uuid()`:
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

### Foreign Key Indexes

All foreign keys have indexes for join performance:
```sql
CREATE INDEX idx_{table}_{fk_column} ON {table}({fk_column});
```

### Filter Indexes

Common filter fields are indexed:
```sql
-- Status filters
CREATE INDEX idx_projects_status ON projects(workflow_status);
CREATE INDEX idx_jobs_status ON jobs(status);

-- Date filters
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- User filters
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
```

### Full-Text Search Indexes

Full-text search uses GIN indexes with `tsvector`:
```sql
CREATE INDEX idx_projects_search ON projects
    USING gin(to_tsvector('english',
        coalesce(name, '') || ' ' ||
        coalesce(developer, '') || ' ' ||
        coalesce(location, '') || ' ' ||
        coalesce(description, '')
    ));
```

### JSONB Indexes

JSONB columns use GIN indexes for containment queries:
```sql
CREATE INDEX idx_projects_property_types ON projects USING gin(property_types);
CREATE INDEX idx_projects_amenities ON projects USING gin(amenities);
```

---

## Constraints and Validations

### Check Constraints

**Enum-like constraints:**
```sql
-- User role
CHECK (role IN ('admin', 'user'))

-- Workflow status
CHECK (workflow_status IN (
    'draft', 'pending_approval', 'revision_requested',
    'approved', 'publishing', 'published', 'qa_verified', 'complete'
))

-- Job status
CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
```

**Range constraints:**
```sql
-- Job progress
CHECK (progress >= 0 AND progress <= 100)

-- Prices must be positive
CHECK (starting_price > 0)
CHECK (price_per_sqft > 0)
```

### Domain Constraints

**Email domain restriction:**
```sql
ALTER TABLE users ADD CONSTRAINT check_email_domain
    CHECK (email ~ '@mpd\.ae$');
```

### Unique Constraints

**Active prompt constraint:**
```sql
-- Only one active prompt per (template_type, content_variant, name)
CONSTRAINT unique_active_prompt
    EXCLUDE (template_type WITH =, content_variant WITH =, name WITH =)
    WHERE (is_active = true)
```

### Foreign Key Constraints

**Cascade deletes:**
```sql
-- Delete project images when project is deleted
project_id UUID REFERENCES projects(id) ON DELETE CASCADE

-- Set job reference to NULL when job is deleted
processing_job_id UUID REFERENCES jobs(id) ON DELETE SET NULL
```

---

## JSONB Fields

### projects.property_types

**Type:** Array of strings

**Example:**
```json
["apartment", "penthouse", "villa"]
```

**Query:**
```sql
-- Find projects with apartments
SELECT * FROM projects WHERE property_types @> '["apartment"]'::jsonb;
```

### projects.unit_sizes

**Type:** Array of objects

**Example:**
```json
[
  {
    "type": "1BR",
    "sqft_min": 650,
    "sqft_max": 750
  },
  {
    "type": "2BR",
    "sqft_min": 1100,
    "sqft_max": 1300
  }
]
```

**Query:**
```sql
-- Find projects with 1BR units
SELECT * FROM projects WHERE unit_sizes @> '[{"type": "1BR"}]'::jsonb;
```

### projects.custom_fields

**Type:** Object (key-value pairs)

**Example:**
```json
{
  "sales_contact": "John Smith",
  "priority": "high",
  "internal_code": "MB-2026-001"
}
```

**Query:**
```sql
-- Find projects with high priority
SELECT * FROM projects WHERE custom_fields->>'priority' = 'high';
```

### projects.generated_content

**Type:** Object (content fields)

**Example:**
```json
{
  "meta_title": "Marina Bay Residences by Emaar | Dubai Marina",
  "meta_description": "Luxury apartments in Dubai Marina...",
  "h1": "Marina Bay Residences",
  "intro_paragraph": "Experience waterfront living...",
  "url_slug": "marina-bay-residences-dubai-marina"
}
```

---

## Full-Text Search

### Search Implementation

**Index:**
```sql
CREATE INDEX idx_projects_search ON projects
    USING gin(to_tsvector('english',
        coalesce(name, '') || ' ' ||
        coalesce(developer, '') || ' ' ||
        coalesce(location, '') || ' ' ||
        coalesce(description, '')
    ));
```

**Query:**
```sql
-- Search for "marina emaar"
SELECT * FROM projects
WHERE to_tsvector('english',
    coalesce(name, '') || ' ' ||
    coalesce(developer, '') || ' ' ||
    coalesce(location, '') || ' ' ||
    coalesce(description, '')
) @@ to_tsquery('english', 'marina & emaar');
```

**Ranking:**
```sql
-- Search with ranking
SELECT
    id,
    name,
    ts_rank(
        to_tsvector('english',
            coalesce(name, '') || ' ' ||
            coalesce(developer, '') || ' ' ||
            coalesce(location, '')
        ),
        to_tsquery('english', 'marina & emaar')
    ) AS rank
FROM projects
WHERE to_tsvector('english',
    coalesce(name, '') || ' ' ||
    coalesce(developer, '') || ' ' ||
    coalesce(location, '')
) @@ to_tsquery('english', 'marina & emaar')
ORDER BY rank DESC;
```

---

## Migrations

### Alembic Setup

**Directory Structure:**
```
alembic/
  ├── versions/
  │   ├── 001_initial_schema.py
  │   ├── 002_add_custom_fields.py
  │   └── 003_add_qa_tables.py
  ├── env.py
  └── alembic.ini
```

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add custom fields to projects"

# Create empty migration
alembic revision -m "Add custom index"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Example Migration

```python
# alembic/versions/004_add_notifications.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    op.create_table(
        'notifications',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('is_read', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'))
    )

    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_is_read', 'notifications', ['user_id', 'is_read'])

def downgrade():
    op.drop_table('notifications')
```

---

## Related Documentation

- [System Architecture](./SYSTEM_ARCHITECTURE.md) - Overall system design
- [Data Flow](./DATA_FLOW.md) - How data moves through the system
- [API Design](./API_DESIGN.md) - RESTful API specification
- [Service Layer](../04-backend/SERVICE_LAYER.md) - Service implementations

---

**Last Updated:** 2026-01-15
