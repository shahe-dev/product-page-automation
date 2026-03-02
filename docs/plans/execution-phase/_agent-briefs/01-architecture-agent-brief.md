# Agent Briefing: Architecture Documentation Agent

**Agent ID:** architecture-docs-agent
**Batch:** 1 (Foundation)
**Priority:** P0 - Critical Foundation
**Est. Context Usage:** 40,000 tokens

---

## Your Mission

You are a specialized documentation agent responsible for creating **6 core architecture documentation files** for the PDP Automation v.3 system. These documents form the foundation that all other documentation will reference.

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/01-architecture/`

---

## Files You Must Create

1. `SYSTEM_ARCHITECTURE.md` (300-400 lines) - Overall system design
2. `DATA_FLOW.md` (200-300 lines) - How data moves through the system
3. `API_DESIGN.md` (400-500 lines) - RESTful API specification
4. `DATABASE_SCHEMA.md` (800-900 lines) - Complete PostgreSQL schema
5. `SECURITY_ARCHITECTURE.md` (300-400 lines) - Auth, permissions, data protection
6. `INFRASTRUCTURE.md` (300-400 lines) - Google Cloud components

**Total Output:** ~2,500-3,000 lines across 6 files

---

## System Overview

**PDP Automation v.3** is a Real Estate PDF Automation System that transforms PDF brochures into structured, SEO-optimized content and processed images for property detail pages.

### Purpose
Automate the manual workflow of extracting data from real estate PDF brochures, generating content, and publishing to websites.

### Target Users (4 Departments)
1. **Content Creation** - Upload PDFs, generate content, submit for approval
2. **Marketing** - Review and approve/reject content
3. **Publishing** - Download assets, create pages, mark as published
4. **Web Development** - Access APIs, integrate assets

### Core Workflow
```
PDF Upload → Parallel Processing → QA Validation → Approval → Publishing

PARALLEL PROCESSING:
├── TEXT PATH: Extract → Organize → Generate → Push to Sheets
└── VISUAL PATH: Extract → Classify → Optimize → Package ZIP
```

---

## Technology Stack

### Frontend
- **Framework:** React 19 + Vite
- **Language:** TypeScript 5.x
- **Styling:** Tailwind CSS 4.x + shadcn/ui
- **State:** React Query 5.x (server) + Zustand 4.x (client)
- **Router:** React Router 7.x
- **Icons:** Lucide React

### Backend
- **Framework:** FastAPI 0.109+
- **Runtime:** Python 3.10+
- **ORM:** SQLAlchemy 2.x (async) + Alembic 1.x
- **Validation:** Pydantic 2.x
- **PDF:** PyMuPDF 1.23+
- **Images:** Pillow 10.x + OpenCV 4.9+
- **Google:** gspread 6.x, google-cloud-aiplatform 1.38+, google-cloud-storage 2.x

### Infrastructure
- **Compute:** Cloud Run (serverless, auto-scaling)
- **Database:** Neon PostgreSQL (serverless, managed)
- **Storage:** Google Cloud Storage (PDFs, images, ZIPs)
- **AI:** Anthropic API (Claude Sonnet 4.5 for text and vision)
- **Auth:** Google OAuth (Workspace domain-restricted to @your-domain.com)
- **CI/CD:** Cloud Build
- **Monitoring:** Cloud Monitoring + Logging + Sentry

---

## Key Design Decisions

### 1. Why Anthropic API (Claude Sonnet 4.5) for AI Tasks?
- **Already have API credits and key** - no additional setup needed
- **Claude Sonnet 4.5:** Excellent at document extraction and content generation (128K context)
- **Claude Sonnet 4.5:** Multimodal vision capabilities for image classification, OCR, floor plans
- Industry-leading accuracy on structured data extraction
- Simple REST API, easy integration
- Model upgradeable via API version parameter

### 2. Why Neon PostgreSQL over Cloud SQL?
- **Serverless:** Scales to zero when inactive (no 24/7 sunk costs)
- **Cost-effective:** $0/month for development (10 GB free tier), $19/month for production
- **Relational data:** Projects have floor plans, images, approvals (requires proper relationships)
- **JSONB columns:** Flexible custom fields without schema changes
- **Full-text search:** Built-in `tsvector` capabilities for searching projects
- **ACID compliance:** Critical for approval workflow integrity
- **Managed backups:** Automatic point-in-time recovery included
- **No migration:** Same connection string from development to production

### 3. Why Cloud Run over GKE/VMs?
- Serverless: no infrastructure management
- Auto-scaling: 0 to N instances based on traffic
- Cost: pay per request (with min instances for warm start)
- Simplicity: Docker containers, simple deployment

**Configuration:**
```yaml
Backend:
  memory: 2GB    # PDF processing needs RAM
  cpu: 2         # Image processing is CPU-intensive
  min_instances: 1  # Always warm
  max_instances: 10

Frontend:
  memory: 512MB
  cpu: 1
  min_instances: 0  # Can cold start
```

### 4. Why Google Workspace OAuth?
- Users already have Google Workspace accounts (@your-domain.com)
- No password management needed
- MFA handled by Google
- Easy domain restriction
- Profile photos/names auto-populated

### 5. Why Three QA Checkpoints?
- **Checkpoint 1 (Extraction):** Catch PDF parsing errors early
- **Checkpoint 2 (Generation):** Verify LLM output matches source before Sheets push
- **Checkpoint 3 (Publication):** Compare published page to approved content

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React 19 + Vite)                   │
│  HomePage │ ProcessingPage │ QAPage │ PromptsPage │ Workflow   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API (JSON)
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
│ - Extraction  │  │ - Image Extract│  │ - Compare     │
│ - Generation  │  │ - Classify    │  │ - Validate    │
│ - Sheets Push │  │ - Floor Plans │  │ - History     │
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
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Database Schema (Core Tables)

### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,  -- Must be @your-domain.com
    name VARCHAR(255) NOT NULL,
    picture_url VARCHAR(500),
    role VARCHAR(20) NOT NULL DEFAULT 'user'  -- 'admin' or 'user'
        CHECK (role IN ('admin', 'user')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);
```

### projects (Central Repository)
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,

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

    -- JSONB fields
    property_types JSONB DEFAULT '[]',  -- ["apartment", "villa"]
    unit_sizes JSONB DEFAULT '[]',      -- [{"type": "1BR", "sqft_min": 650}]
    amenities JSONB DEFAULT '[]',
    features JSONB DEFAULT '[]',

    -- Numeric
    total_units INTEGER,
    floors INTEGER,
    buildings INTEGER,

    -- Custom fields (user-added)
    custom_fields JSONB DEFAULT '{}',

    -- Media
    original_pdf_url VARCHAR(500),
    processed_zip_url VARCHAR(500),
    sheet_url VARCHAR(500),

    -- Workflow
    workflow_status VARCHAR(50) NOT NULL DEFAULT 'draft'
        CHECK (workflow_status IN (
            'draft', 'pending_approval', 'revision_requested',
            'approved', 'publishing', 'published', 'qa_verified', 'complete'
        )),

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified_by UUID REFERENCES users(id),
    last_modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_job_id UUID REFERENCES jobs(id)
);

-- Critical indexes
CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_developer ON projects(developer);
CREATE INDEX idx_projects_emirate ON projects(emirate);
CREATE INDEX idx_projects_status ON projects(workflow_status);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);

-- Full-text search
CREATE INDEX idx_projects_search ON projects
    USING gin(to_tsvector('english',
        coalesce(name, '') || ' ' ||
        coalesce(developer, '') || ' ' ||
        coalesce(location, '')
    ));
```

### Other Core Tables
- `project_floor_plans` - Floor plan images with extracted data
- `project_images` - Categorized images (interior/exterior/amenity/logo)
- `project_approvals` - Approval workflow tracking
- `project_revisions` - Audit trail for field changes
- `jobs` - Background processing jobs
- `job_steps` - Individual steps within jobs
- `prompts` + `prompt_versions` - Version-controlled prompt library
- `templates` - Website template configurations
- `qa_comparisons` - QA checkpoint results
- `notifications` - In-app notification system
- `workflow_items` - Kanban board items
- `publication_checklists` - Per-site publication tracking
- `execution_history` - Full audit log

---

## API Design

### Core Endpoints

**Authentication & Users:**
- `POST /api/auth/google` - Google OAuth callback
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

**File Upload & Jobs:**
- `POST /api/upload` - Upload PDF and create job
- `GET /api/jobs/{job_id}` - Get job status and result
- `GET /api/jobs` - List user's jobs

**Projects (Central Database):**
- `GET /api/projects` - List projects (paginated, filterable)
- `GET /api/projects/{id}` - Get project detail
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project (admin only)
- `POST /api/projects/{id}/fields` - Add custom field
- `GET /api/projects/{id}/history` - Get revision history
- `POST /api/projects/export` - Export selected projects

**Prompts:**
- `GET /api/prompts` - List prompts
- `GET /api/prompts/{id}` - Get prompt
- `POST /api/prompts` - Create prompt
- `PUT /api/prompts/{id}` - Update prompt (creates new version)
- `GET /api/prompts/{id}/versions` - Get version history

**QA:**
- `POST /api/qa/compare` - Run QA comparison
- `GET /api/qa/history` - Get QA history

**Workflow:**
- `GET /api/workflow/items` - Get Kanban board items
- `PUT /api/workflow/items/{id}` - Update item (move column, assign)

**Templates:**
- `GET /api/templates` - List website templates

**Health:**
- `GET /health` - Basic health check
- `GET /readiness` - Readiness check (DB, Redis, GCS)

---

## Security Architecture

### Layers of Security

1. **Network Security**
   - HTTPS only (TLS 1.2+)
   - Cloud Armor WAF
   - CORS restrictions
   - Rate limiting (5-50 req/hour based on role)

2. **Authentication**
   - Google OAuth 2.0
   - Domain restriction (@your-domain.com only)
   - JWT tokens (1 hour expiry)
   - Refresh tokens (7 days)

3. **Authorization**
   - Role-based access control (admin/user)
   - Resource ownership checks
   - Admin-only operations (delete, manage users)

4. **Data Protection**
   - Encrypted at rest (Cloud SQL, GCS)
   - Encrypted in transit (TLS)
   - Secrets in Secret Manager
   - API key rotation (monthly)

5. **File Upload Security**
   - Extension validation (.pdf only)
   - MIME type check (application/pdf)
   - Magic bytes validation (PDF header)
   - File size limit (50MB)
   - Virus scanning (future: ClamAV)

6. **API Security**
   - Input validation (Pydantic)
   - SQL injection prevention (parameterized queries)
   - XSS prevention (sanitize outputs)
   - CSRF protection
   - Request/response logging

7. **Audit Trail**
   - All actions logged with user ID
   - IP address tracking
   - Sensitive operations (delete, export) logged separately
   - 90-day retention

---

## Infrastructure Components

### Google Cloud Resources

**Compute:**
- **Cloud Run (Backend):** `pdp-automation-api`
  - Region: us-central1
  - Memory: 2GB, CPU: 2
  - Min instances: 1, Max: 10
  - Auto-scaling based on CPU/memory

- **Cloud Run (Frontend):** `pdp-automation-web`
  - Region: us-central1
  - Memory: 512MB, CPU: 1
  - Min instances: 0, Max: 5

**Database:**
- **Neon PostgreSQL (Serverless):** `pdp-automation`
  - Provider: Neon (neon.tech)
  - Region: US East 1 (AWS)
  - Development: Free tier (10 GB storage, auto-pause after inactivity)
  - Production: Scale tier ($19/month, 100 GB storage)
  - Connection pooling: Enabled
  - Automated backups: Included with point-in-time recovery

**Storage:**
- **Cloud Storage:** `pdp-automation-assets`
  - Location: us-central1
  - Storage class: Standard
  - Lifecycle: Delete after 365 days (PDFs), Keep forever (outputs)
  - Versioning: Enabled

**AI/ML:**
- **Anthropic API:** Claude Sonnet 4.5 (text + vision unified)
  - Endpoint: api.anthropic.com/v1
  - Model: `claude-sonnet-4-5-20241022` (extraction, generation, classification, OCR)
  - Rate limit: Depends on API tier
  - Cost: Covered by existing API credits

**Integrations:**
- **Google Sheets API:** Content output to templates
- **Google Drive API:** File sharing (images, floor plans, ZIPs auto-shared with @your-domain.com organization)
- **Google OAuth:** Authentication (Workspace domain-restricted)

**Observability:**
- **Cloud Monitoring:** Metrics, dashboards, alerts
- **Cloud Logging:** Centralized logs
- **Sentry:** Error tracking
- **Cloud Trace:** Request tracing

**Security:**
- **Secret Manager:** API keys (Anthropic API key), credentials
- **Cloud Armor:** WAF, DDoS protection
- **IAM:** Service account permissions

---

## Scaling Considerations

### Current Design Limits
- **PDF size:** 50MB max
- **Images per PDF:** 500 max (process in batches)
- **Concurrent jobs:** 10 per instance
- **Anthropic API:** Rate limit varies by tier (queue + exponential backoff)
- **Sheets API:** 100 req/100s (batch operations)

### Growth Path
| Phase | Users | Projects/Month | Infrastructure |
|-------|-------|----------------|----------------|
| Launch | 10 | 50 | 1 Cloud Run instance |
| 6 months | 25 | 150 | 2-3 instances |
| 1 year | 50+ | 300+ | Consider Kubernetes |

---

## Templates & Standards

### Document Structure
Each architecture document must include:
1. **Header:** Title, last updated date, related docs
2. **Overview:** 2-3 sentence summary
3. **Table of Contents:** For documents >200 lines
4. **Main Content:** Sections with clear headings
5. **Code Examples:** Where applicable (with syntax highlighting)
6. **Diagrams:** ASCII art for visual representation
7. **Related Documentation:** Links to other relevant docs
8. **Footer:** Last updated timestamp

### Markdown Standards
- Use `#` for h1, `##` for h2, `###` for h3, etc.
- Code blocks with language: ` ```python ` ` ```sql ` ` ```yaml `
- Tables for structured data
- Lists for sequential items
- Emphasis: `**bold**` for important, `*italic*` for emphasis
- Links: `[Link Text](./relative/path.md)`

### ASCII Diagram Standards
```
┌─────────┐      ┌─────────┐
│ Service │─────▶│ Service │
│    A    │      │    B    │
└─────────┘      └─────────┘
     │
     ▼
┌─────────┐
│Database │
└─────────┘
```

---

## Cross-References

Your documents will be referenced by:
- **Module docs** (02-modules/) - for workflow integration
- **Backend docs** (04-backend/) - for service implementation
- **Integration docs** (05-integrations/) - for external APIs
- **DevOps docs** (06-devops/) - for deployment
- **Testing docs** (07-testing/) - for test requirements

---

## Quality Checklist

Before marking complete, verify:
- ✅ All 6 files created
- ✅ File names match exactly (case-sensitive)
- ✅ Markdown formatting valid
- ✅ Code examples include language tags
- ✅ ASCII diagrams render correctly
- ✅ Cross-references use relative paths
- ✅ No placeholder "TODO" sections
- ✅ Last updated dates included
- ✅ Tables formatted properly
- ✅ All technical details accurate

---

## Start Creating Documents

Begin with `SYSTEM_ARCHITECTURE.md`, then proceed to the other 5 files. Ensure consistency in tone, formatting, and technical depth across all documents.

Good luck! Your work forms the foundation for all other documentation agents.