# Agent Briefing: Modules Documentation Agent

**Agent ID:** modules-docs-agent
**Batch:** 2 (Features)
**Priority:** P1 - Core Features
**Est. Context Usage:** 38,000 tokens

---

## Your Mission

You are a specialized documentation agent responsible for creating **8 module documentation files** for the PDP Automation v.3 system. These documents describe all core modules and how they work together.

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/02-modules/`

---

## Files You Must Create

1. `PROJECT_DATABASE.md` (400-500 lines) - Central repository module
2. `MATERIAL_PREPARATION.md` (400-500 lines) - PDF → Images pipeline
3. `CONTENT_GENERATION.md` (350-400 lines) - LLM content creation
4. `APPROVAL_WORKFLOW.md` (300-350 lines) - Marketing approval process
5. `PUBLISHING_WORKFLOW.md` (300-350 lines) - Publisher checklist system
6. `QA_MODULE.md` (350-400 lines) - Quality assurance checkpoints
7. `PROMPT_LIBRARY.md` (300-350 lines) - Version-controlled prompts
8. `NOTIFICATIONS.md` (250-300 lines) - Alert system

**Total Output:** ~2,700-3,150 lines across 8 files

---

## Module 0: Project Database (Central Hub)

**Purpose:** Central repository of all processed projects with full CRUD and export capabilities.

**Core Features:**
- All extracted data stored (name, developer, location, pricing, floor plans, amenities, etc.)
- Custom fields (unlimited user-added fields)
- Full editing by any user
- Search & filter (by any field: name, developer, date range, price range, emirate)
- Project timeline tracking
- Export formats: Excel, CSV, PDF, JSON

**Database Tables:**
- `projects` - Main project table
- `project_floor_plans` - Linked floor plans
- `project_images` - Linked categorized images
- `project_revisions` - Audit trail

**UI Components:**
- `ProjectsListPage.tsx` - Browse with filters
- `ProjectDetailPage.tsx` - View/edit single project
- `ProjectExportPage.tsx` - Export wizard
- `CustomFieldsEditor.tsx` - Add/edit custom fields

**API Endpoints:**
```
GET    /api/projects              - List with filters/search
GET    /api/projects/{id}         - Get project detail
PUT    /api/projects/{id}         - Update project
DELETE /api/projects/{id}         - Delete (admin only)
POST   /api/projects/{id}/fields  - Add custom field
GET    /api/projects/{id}/history - Revision history
POST   /api/projects/export       - Export selected
```

---

## Module 1: Approval & Publishing Workflow

**Purpose:** Formal handoff between Content Creation → Marketing → Publishing

**Workflow States:**
```
DRAFT → PENDING_APPROVAL → APPROVED → PUBLISHING → PUBLISHED → QA_VERIFIED → COMPLETE
               ↓
        REVISION_REQUESTED (back to Content Creator)
```

**Approval Workflow Features:**
- Submit for Approval button (Content Creator)
- `ApprovalQueuePage` (Marketing Manager view)
- Approve / Request Revision / Reject buttons
- Required comments for rejections
- Bulk approval for multiple projects

**Publishing Workflow Features:**
- `PublishQueuePage` (Publisher view)
- Per-template checklists (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
- Asset download tracking
- Mark as published with URL input
- Handoff notifications at each stage

**Database Tables:**
```sql
project_approvals (
    id, project_id, status, reviewer_id,
    submitted_at, reviewed_at, comments
)

publication_checklists (
    id, project_id, site_name,
    is_page_created, is_images_uploaded, is_seo_verified,
    published_url, published_by, published_at
)
```

---

## Module 2: Notifications System

**Purpose:** Keep all departments informed of status changes

**Events:**
- `project.created` - New project added
- `project.pending_approval` - Ready for marketing review
- `project.approved` - Ready for publishing
- `project.rejected` - Needs revision
- `qa.failed` - QA issues found
- `deadline.approaching` - 24h before deadline
- `deadline.missed` - Overdue projects

**Channels:**
- In-app notifications (required)
- Email notifications (optional per user)
- Future: Slack integration

**Frontend:**
- Notification bell icon in header
- `NotificationsPage` with history
- Mark as read / mark all as read

**Database:**
```sql
notifications (
    id, user_id, event_type, title, message,
    reference_type, reference_id,
    is_read, read_at, created_at
)
```

---

## Module 3: QA Module

**Purpose:** Multi-stage quality assurance throughout the pipeline

**Three QA Checkpoints:**

1. **After Text Extraction** - Verify extraction accuracy
   - Compare extracted data against PDF source
   - Flag missing or incorrect fields
   - User can approve override

2. **After Text Generation** - Validate generated content quality
   - Factual accuracy check (does content match PDF?)
   - Prompt compliance (character limits, required fields)
   - Consistency check (no contradictions)
   - ONLY push to Sheets if QA passes

3. **After Sheet Population** - Confirm correct template filling
   - Compare sheet cells against generated content
   - Verify all fields mapped correctly

**Post-Publication QA:**
- Compare approved Google Sheet against published page URL
- Output: Matches, differences, missing info, extra info
- Store history for auditing

**Database:**
```sql
qa_comparisons (
    id, job_id, checkpoint_type,
    input_content, comparison_target, result_json,
    status, created_at
)
-- checkpoint_type: 'extraction', 'generation', 'sheet', 'published'
```

---

## Module 4: Material Preparation

**Purpose:** Extract and process all visual assets from PDFs

**Pipeline:**
```
PDF Upload → Image Extraction → Classification → Watermark Removal →
Floor Plan Extraction → Deduplication → Optimization → ZIP Package
```

**Features:**
- Image extraction with category classification (Claude Sonnet 4.5 vision)
- Preset limits: 10 exteriors, 10 interiors, 5 amenities, 3 logos
- Watermark detection (Claude Sonnet 4.5 vision) and removal (OpenCV inpainting)
- Floor plan extraction with data extraction (Claude Sonnet 4.5 vision)
- Floor plan deduplication (1 unit type = 1 floor plan)
- Image specs: 300 DPI, max 2450x1400px, dual-tier output (original + LLM-optimized)
- Output: WebP + JPG formats, ZIP package

**Image Categories:**
- Interior (10 max)
- Exterior (10 max)
- Amenity (5 max)
- Logo (3 max)
- Other (discarded)

**Services:**
- `PDFProcessor` - Extract images from PDF
- `ImageClassifier` - Classify via Claude Sonnet 4.5 vision
- `WatermarkDetector` - Detect watermark bounding boxes (Claude Sonnet 4.5)
- `ImageOptimizer` - Resize, compress, convert formats
- `FloorPlanExtractor` - Extract floor plan data (Claude Sonnet 4.5 vision)
- `OutputOrganizer` - Package into ZIP

---

## Module 5: Text Generation

**Purpose:** Generate SEO-optimized content for project pages

**Pipeline:**
```
PDF → Text Extraction (pymupdf4llm) → Structure with Claude Sonnet 4.5 → Organize JSON →
Pre-generation Prompts → Content Generation (Claude Sonnet 4.5) → QA Validation → Google Sheets Push
```

**Extraction Strategy:**
1. **pymupdf4llm** extracts markdown-formatted text from PDF (cost-free, local)
2. **Claude Sonnet 4.5** structures the markdown into JSON according to schema (~90% cost savings vs vision)
3. **Claude Sonnet 4.5 vision** ONLY used for floor plan data extraction (where images are required)

**Features:**
- Template type selection (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
- Template-specific content generation
- Field-by-field prompts with character limits
- URL slug generation
- SEO meta tags generation
- Image ALT tags generation
- Version comparison and reuse
- Direct Google Sheets API population (no manual copy/paste)

**Templates (6 Total):**
- Aggregators template (24+ third-party aggregator domains)
- OPR template (opr.ae)
- MPP template (main-portal.com)
- ADOP template (abudhabioffplan.ae)
- ADRE template (secondary-market-portal.com)
- Commercial template (cre.main-portal.com)

**Services:**
- `PDFExtractor` - Extract text from PDF (pymupdf4llm)
- `DataStructurer` - Structure markdown into JSON (Claude Sonnet 4.5)
- `ContentGenerator` - Generate SEO content (Claude Sonnet 4.5)
- `ContentQAService` - Validate generated content against source (Claude Sonnet 4.5 fact-checker)
- `SheetsManager` - Populate Google Sheets

**QA Validation Before Push:**
```python
class ContentQAService:
    async def validate_before_push(
        extracted_data: dict,      # Original PDF data
        generated_content: dict,   # LLM output
        prompt_spec: Prompt        # Template requirements
    ) -> QAResult:
        # 1. Factual accuracy check
        # 2. Prompt compliance check
        # 3. Consistency check
        # 4. Return: PASS/FAIL with issues list
```

---

## Module 6: Prompt Library

**Purpose:** Centralized, version-controlled prompt management

**Features:**
- Prompts grouped by website and template type
- Description and intended use per prompt
- Full version control (every change tracked)
- Change history (who changed what, when)
- Pre-generation prompt customization
- Prompt reuse across projects

**Database:**
```sql
prompts (
    id, name, website, template_type,
    description, content, version, is_active,
    created_by, created_at, updated_at
)

prompt_versions (
    id, prompt_id, version, content,
    changed_by, change_reason, created_at
)
```

**UI Components:**
- `PromptsPage.tsx` - List/filter prompts
- `PromptEditorPage.tsx` - Edit with diff view
- `PromptVersionHistory.tsx` - View change history

**API Endpoints:**
```
GET    /api/prompts               - List prompts
GET    /api/prompts/{id}          - Get prompt
POST   /api/prompts               - Create prompt
PUT    /api/prompts/{id}          - Update (creates new version)
GET    /api/prompts/{id}/versions - Version history
```

---

## Workflow Diagrams

### Parallel Processing Workflow

```
                    BROCHURE UPLOAD
                           |
        ┌──────────────────┴──────────────────┐
        │                                     │
   TEXT PATH                            VISUAL PATH
        │                                     │
        ▼                                     ▼
   pymupdf4llm                          Image Extraction
Markdown Extraction                          │
        │                                     ▼
        ▼                                 Claude Sonnet 4.5
QA Checkpoint #1                       Classification
(extraction completeness)                    │
        │                                     ▼
        ▼                              Watermark Detection
  Claude Sonnet 4.5                           → Removal (OpenCV)
Structure to JSON                            │
        │                                     ▼
        ▼                              Floor Plan Extraction
Save to Database                             │
        │                                     ▼
        ▼                                 Claude Sonnet 4.5
Pre-generation Prompts                 Data Extraction
        │                              + Price Lookup
        ▼                                     │
Claude Sonnet 4.5                                  ▼
Text Generation                        Save to Database
        │                                     │
        ▼                                     ▼
┌───────────────────────┐              Deduplication
│  QA Checkpoint #2     │                    │
│  (Claude Sonnet 4.5)        │                    ▼
│  - Factual accuracy   │              ZIP Package Output
│  - Source matching    │                    │
│  - No hallucinations  │                    ▼
└───────────────────────┘              Google Drive Upload
        │                              (images, floor plans, ZIP)
        ▼                                     │
    PASS? ──No──→ User Review → Regenerate   │
        │                                     │
       Yes                                    │
        │                                     │
        └─────────────────┬───────────────────┘
                          │
                          ▼
                Google Sheets API Push
                          │
                          ▼
                 QA Checkpoint #3
              (sheet populated correctly)
                          │
                          ▼
             Marketing Manager Approval
```

### Approval Workflow

```
Content Creator                Marketing Manager              Publisher
       |                              |                            |
       | 1. Submit for Approval       |                            |
       |----------------------------->|                            |
       |                              |                            |
       |                              | 2. Review Content          |
       |                              |                            |
       |                              | 3. Approve/Reject/Request  |
       |                              |    Revision                |
       |                              |                            |
       |<-----------------------------|                            |
       | (if revision requested)      |                            |
       |                              |                            |
       | 4. Update & Resubmit         |                            |
       |----------------------------->|                            |
       |                              |                            |
       |                              | 5. Approve                 |
       |                              |--------------------------->|
       |                              |                            |
       |                              |                            | 6. Download Assets
       |                              |                            |
       |                              |                            | 7. Create Page
       |                              |                            |
       |                              |                            | 8. Mark as Published
       |                              |                            |
       |<----------------------------------------------------------|
       |                   Notification: Published
```

---

## Document Structure Standards

Each module document must include:

1. **Header**
   - Module name and number
   - Last updated date
   - Related documents

2. **Overview** (2-3 sentences)

3. **Purpose & Goals**

4. **Key Features** (bulleted list)

5. **Architecture**
   - Components involved
   - Data flow
   - Services

6. **Database Schema** (relevant tables)

7. **API Endpoints** (if applicable)

8. **UI Components** (if applicable)

9. **Workflow Diagrams** (ASCII art)

10. **Code Examples** (implementation snippets)

11. **Configuration** (settings, environment variables)

12. **Related Documentation** (cross-references)

---

## Cross-References

Your documents will reference:
- **Architecture docs** (01-architecture/) - for system design
- **Backend docs** (04-backend/) - for service implementation
- **Frontend docs** (03-frontend/) - for UI components
- **Integration docs** (05-integrations/) - for external APIs
- **Testing docs** (07-testing/) - for test cases

---

## Quality Checklist

Before marking complete, verify:
- ✅ All 9 files created
- ✅ File names match exactly
- ✅ Each module clearly explained
- ✅ Workflow diagrams included
- ✅ Database schemas documented
- ✅ API endpoints listed
- ✅ UI components identified
- ✅ Code examples provided
- ✅ Cross-references valid
- ✅ No placeholder sections

---

## Start Creating Documents

Begin with `PROJECT_DATABASE.md` as it's the foundation module, then proceed to the others. Maintain consistency in structure and detail level across all 9 documents.