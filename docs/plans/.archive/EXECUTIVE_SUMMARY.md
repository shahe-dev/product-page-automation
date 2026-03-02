# PDP Automation v.3 - Executive Summary

**System:** Real Estate PDF Automation Platform
**Organization:** the company (your-domain.com)
**Status:** Planning complete, implementation ready

---

## What It Does

Transforms PDF property brochures into structured, SEO-optimized content and processed images for property detail pages. Eliminates the manual workflow of extracting data from PDFs, generating content, and publishing to websites.

---

## C-Suite Brief

### Business Problem
Manual PDF processing costs 2-4 hours per property. Content quality varies. No standardized QA. Scaling requires linear headcount growth.

### Solution
Automated pipeline: PDF upload -> parallel processing (text + images) -> QA validation -> approval workflow -> ready-to-publish assets.

### Business Value
| Metric | Impact |
|--------|--------|
| Time per property | 2-4 hours -> 15-20 minutes (human review only) |
| Anthropic costs | 90% reduction via smart model selection |
| Quality | Triple QA validation eliminates errors |
| Scale | Process unlimited properties without headcount |
| Consistency | Version-controlled prompts ensure brand compliance |

### Investment
- **Infrastructure:** GCP free/low tiers (Cloud Run, Neon PostgreSQL, Cloud Storage)
- **Variable costs:** Anthropic API (~$0.50-2.00 per property)
- **Fixed costs:** Minimal - serverless architecture scales with usage

### Risk Mitigation
- All processing logged and auditable
- Rollback capability on prompt changes
- Human approval gates before publication

---

## Head of Development Brief

### Architecture
4-tier serverless architecture on Google Cloud Platform.

| Layer | Technology |
|-------|------------|
| Frontend | React 19 + Vite + TypeScript, Tailwind CSS, shadcn/ui, React Query, Zustand |
| Backend | FastAPI (async), Python 3.10+, SQLAlchemy 2.x, Pydantic 2.x |
| Database | Neon PostgreSQL (serverless) |
| Storage | Google Cloud Storage |
| Compute | Google Cloud Run (auto-scaling) |
| AI/ML | Anthropic API (Claude Sonnet 4.5 text and vision) |
| Auth | Google OAuth (domain-restricted) |

### Key Technical Decisions
1. **PyMuPDF for extraction** - Cost-free vs Claude extraction (90% savings)
2. **Parallel processing** - Text and image paths run concurrently (50-70% faster)
3. **Serverless-first** - Zero infrastructure management, pay-per-request
4. **API-first** - OpenAPI spec auto-generated, enables future integrations

### Processing Pipeline
```
PDF Upload
  |
  +-- TEXT PATH: Extract (pymupdf4llm) -> Structure (Claude) -> Generate -> QA -> Sheets
  |         |
  |         +-- page_text_map ----+
  |                               |
  +-- VISUAL PATH: Extract Images -> Classify (Claude Vision) -+-> Remove Watermarks -> Optimize -> ZIP
  |                                                             |
  |                                                             +-> Floor Plans (Claude + page_text_map)
  |
  v
QA Validation (3 checkpoints) -> Approval Workflow -> Publishing
```
Note: Text extraction produces a per-page text map (`page_text_map`) that feeds into
floor plan extraction as a fallback data source alongside Claude Vision OCR.

### Database Schema
22 tables across core schema and modules:
- **Core** (16): users, projects, project_images, project_floor_plans, project_approvals, project_revisions, jobs, job_steps, prompts, prompt_versions, templates, qa_comparisons, notifications, workflow_items, publication_checklists, execution_history
- **QA Module** (+3): qa_checkpoints, qa_issues, qa_overrides
- **Content Module** (+3): extracted_data, generated_content, content_qa_results

### Scale Targets
| Phase | Timeline | Capacity |
|-------|----------|----------|
| 1 | Month 1-3 | 10 users, 50 projects/month |
| 2 | Month 4-6 | 25 users, 150 projects/month |
| 3 | Month 7-12 | 50 users, 300 projects/month |

### Integration Points
- Google Sheets API (content output)
- Google Drive API (asset storage)
- Google Cloud Storage (file processing)
- Anthropic API (content generation + image classification)

---

## Head of Content Brief

### Workflow Overview
1. **Upload** - Content team uploads PDF brochure
2. **Auto-Extract** - System extracts text and images from PDF
3. **Auto-Generate** - System generates SEO content for selected template
4. **Review** - Marketing reviews generated content and images
5. **Approve/Revise** - Marketing approves or requests changes
6. **Publish** - Publishing team downloads assets and creates pages

### Content Templates Supported
| Template | Use Case | Style |
|----------|----------|-------|
| Aggregators (24+ domains) | Syndicated listings | Broad appeal, SEO-optimized, standard/luxury variants |
| OPR (opr.ae) | Off-plan investment | Investment-focused, analytical, data-driven |
| MPP (main-portal.com) | Premium residential | Sophisticated, lifestyle-focused, premium tone |
| ADOP (abudhabioffplan.ae) | Abu Dhabi off-plan | Market-focused, capital city benefits |
| ADRE (secondary-market-portal.com) | Abu Dhabi general | Comprehensive, market-leading authority |
| Commercial (commercial.main-portal.com) | Commercial properties | ROI-oriented, business-focused, professional |

### Generated Content Fields
- Meta title and description
- URL slug
- H1 heading
- Overview text (multi-paragraph)
- Amenities lists
- FAQ sections
- SEO keywords
- Image alt tags

### Image Processing
- Automatic classification (interior, exterior, amenity, logo)
- Watermark detection and removal
- Floor plan data extraction (unit type, bedrooms, sqft)
- Optimization (WebP/JPG, compression, resizing)
- Organized ZIP output

### Quality Assurance
| Checkpoint | Validation |
|------------|------------|
| 1 - Extraction | Verify PDF parsing accuracy |
| 2 - Generation | Verify content matches extracted data |
| 3 - Publication | Compare published page to source |

### Prompt Management
- Version-controlled prompt library
- Edit history with rollback capability
- A/B testing potential
- Brand compliance enforcement

### User Roles
| Role | Permissions |
|------|-------------|
| Content Creator | Upload, configure, submit for approval |
| Marketing | Review, approve, request revisions |
| Publisher | Download assets, mark as published |
| Admin | Manage prompts, view all projects |

---

## Key User Stories

**Content Creator:**
- Upload PDF and receive auto-extracted structured data
- Select template and generate SEO content
- Submit for marketing approval

**Marketing Team:**
- Review generated content against source PDF
- Approve or request specific revisions
- Track approval status across projects

**Publisher:**
- Download optimized images in organized ZIP
- Access content via Google Sheets
- Mark projects as published

**Developer:**
- Access all project data via REST API
- Automate integrations with external systems
- Retrieve processing status programmatically

---

## Implementation Status

**Complete:**
- System architecture
- Database schema design
- API specifications
- GCP infrastructure (90%)
- Documentation

**Completed:**
- Shared Drive configured (ID: `0AOEEIstP54k2Uk9PVA`)

**Ready to begin:**
- Code implementation

---

*Document generated: January 2026*
