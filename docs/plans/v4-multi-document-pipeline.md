# PDP Automation v.4: Multi-Document Pipeline

**Version upgrade:** v.3 -> v.4
**Primary feature:** Multi-document support per project

---

## Problem Statement

The current pipeline assumes 1 PDF per job. Real projects often have:
- Main brochure (marketing, renders, amenities)
- Floor plans PDF (detailed unit layouts)
- Supplementary docs (specifications, pricing, location maps)

Current architecture constraints:
- `Job.processing_config["pdf_url"]` = single path
- `ExtractedData.page_number` tracks pages but not source document
- `Project.original_pdf_url` = single URL
- 1:1 Job:Project relationship

---

## Approach Options

### Option A: Multiple Jobs per Project (Recommended)

**Concept:** Keep single-PDF jobs, but allow a Project to aggregate results from multiple jobs.

**Changes Required:**

1. **Add Project-Job many-to-many relationship**
   ```python
   # New association table
   project_jobs = Table(
       "project_jobs",
       Base.metadata,
       Column("project_id", UUID, ForeignKey("projects.id")),
       Column("job_id", UUID, ForeignKey("jobs.id")),
       Column("document_type", String),  # "brochure", "floor_plans", "supplementary"
       Column("is_primary", Boolean, default=False),
   )
   ```

2. **Add document type to Job**
   ```python
   # In Job model
   document_type: Mapped[Optional[str]]  # "brochure", "floor_plans", "supplementary"
   ```

3. **New upload flow**
   - Upload multiple PDFs at once OR add PDFs to existing project
   - Each PDF creates its own Job
   - Jobs can run in parallel
   - Aggregation step merges results into single Project

4. **Merge logic in finalization**
   - Floor plans: union of all floor plan extractions
   - Images: dedupe across all sources (by category)
   - Text: concatenate with source attribution
   - Content generation: uses aggregated data

**Pros:**
- No breaking changes to existing Job/Step architecture
- Jobs can run in parallel (floor plans processing while brochure classifies)
- Easy to add documents incrementally to a project
- Existing single-PDF uploads still work

**Cons:**
- Need merge/aggregation logic
- Cross-document deduplication more complex

---

### Option B: Document Collection Model

**Concept:** Add intermediary `Document` model between Job and extractions.

```python
class Document(Base):
    id: UUID
    job_id: UUID  # Parent job
    file_path: str
    document_type: str  # "brochure", "floor_plans", etc.
    original_filename: str
    page_count: int

class ExtractedData(Base):
    document_id: UUID  # NEW - which PDF this came from
    page_number: int
```

**Pros:**
- Clean attribution (know exactly which PDF each extraction came from)
- Single job processes multiple documents

**Cons:**
- Requires schema migration for ExtractedData
- Pipeline steps need document-aware context
- More complex than Option A

---

### Option C: Multi-PDF Job Redesign

**Concept:** Redesign Job to accept array of PDFs.

```python
# Job.processing_config becomes:
{
    "documents": [
        {"url": "gcs://...", "type": "brochure", "filename": "..."},
        {"url": "gcs://...", "type": "floor_plans", "filename": "..."},
    ]
}
```

**Pros:**
- Cleanest long-term architecture
- Single job = single project intent

**Cons:**
- Breaking change to job creation
- Pipeline context needs per-document tracking
- Harder to parallelize (one job doing everything)

---

## Recommendation: Option A

Option A is the right balance of:
- Minimal disruption to existing architecture
- Parallelizable processing
- Incremental adoption (existing single-PDF uploads still work)
- Clear extension path for the future

---

## Implementation Plan (Option A)

### Phase 1: Schema Changes

**File:** `backend/app/models/database.py`

1. Add `project_jobs` association table
2. Add `document_type` field to `Job` model
3. Add `source_documents` JSONB field to `Project` (array of document metadata)
4. Keep `processing_job_id` as "primary" job for backward compatibility

### Phase 2: Upload Changes

**File:** `backend/app/api/routes/upload.py`

1. Add endpoint: `POST /upload/multi` for batch upload
2. Accept array of files with document_type for each
3. Create separate Job per file
4. Return array of job IDs

Alternative: `POST /upload/add-to-project/{project_id}` to add documents to existing project

### Phase 3: Job Manager Changes

**File:** `backend/app/services/job_manager.py`

1. Add `link_job_to_project(job_id, project_id, document_type)` method
2. Modify `_step_finalize` to:
   - Check if project already exists (linked via project_jobs)
   - If exists: merge results into existing project
   - If not: create new project

3. Add merge logic:
   - Images: append with dedup check
   - Floor plans: append with dedup check
   - Text: concatenate with document attribution
   - Structured data: merge dictionaries

### Phase 4: Aggregation Logic

**New file:** `backend/app/services/project_aggregator.py`

```python
class ProjectAggregator:
    async def aggregate_jobs(self, project_id: UUID, job_ids: list[UUID]) -> Project:
        """Merge results from multiple jobs into single project."""
        pass

    async def merge_images(self, existing: list, new: list) -> list:
        """Dedupe and merge image sets."""
        pass

    async def merge_floor_plans(self, existing: list, new: list) -> list:
        """Dedupe and merge floor plan data."""
        pass
```

### Phase 5: Frontend Changes

**Files:** `frontend/src/pages/`, `frontend/src/components/upload/`

1. Multi-file upload UI with document type selector
2. Project view showing document sources
3. "Add document" action on existing projects

---

## Database Migration

```sql
-- Add document_type to jobs (free-form text, not enum)
ALTER TABLE jobs ADD COLUMN document_type VARCHAR(100);
ALTER TABLE jobs ADD COLUMN parent_project_id UUID REFERENCES projects(id) ON DELETE SET NULL;

-- Create project_jobs association
CREATE TABLE project_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    document_type VARCHAR(100),  -- Free-form: "brochure", "floor plans", "specs", etc.
    is_primary BOOLEAN DEFAULT FALSE,
    processing_order INTEGER DEFAULT 0,  -- For merge priority
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, job_id)
);

-- Add source_documents to projects
ALTER TABLE projects ADD COLUMN source_documents JSONB DEFAULT '[]'::jsonb;

-- Index for fast lookup
CREATE INDEX idx_project_jobs_project ON project_jobs(project_id);
CREATE INDEX idx_jobs_parent_project ON jobs(parent_project_id);
```

---

## API Changes

### New Endpoints

```
POST /upload/batch
  - files: File[] (multipart)
  - document_types: string[] (JSON in form data, free-form labels)
  - Returns: { job_ids: UUID[], project_id: UUID }
  - Creates parallel jobs, all linked to same new project

POST /projects/{project_id}/add-document
  - file: File (multipart)
  - document_type: string (free-form: "floor plans", "pricing sheet", etc.)
  - Returns: { job_id: UUID, will_reprocess: boolean }
  - Triggers re-processing after extraction completes

GET /projects/{project_id}/documents
  - Returns: [{ job_id, document_type, filename, status, extracted_at, is_primary }]

POST /projects/{project_id}/reprocess
  - Manually trigger re-aggregation and content regeneration
  - Used after adding documents or if merge failed
  - Returns: { job_id: UUID } (new aggregation job)
```

### Re-processing Flow (Add Document to Completed Project)

1. User uploads new PDF via `POST /projects/{project_id}/add-document`
2. New Job created with `parent_project_id = project_id`
3. Job processes through extraction/classification/optimization steps
4. On finalization, instead of creating new Project:
   - Link job to existing project via `project_jobs`
   - Run `ProjectAggregator.merge_into_project(project_id, job_id)`
   - Re-run content generation with merged data
   - Update Google Sheet with new/updated content
5. Project status temporarily set to `REPROCESSING`, then back to `COMPLETED`

---

## Critical Files to Modify

| File | Changes |
|------|---------|
| `backend/app/models/database.py` | Add project_jobs table, document_type field |
| `backend/app/api/routes/upload.py` | Add batch upload, add-to-project endpoints |
| `backend/app/services/job_manager.py` | Modify finalize to support merge |
| `backend/app/services/project_aggregator.py` | NEW - merge logic |
| `backend/alembic/versions/xxx_multi_doc.py` | Migration script |
| `frontend/src/components/upload/` | Multi-file UI |

---

## Verification

1. Upload single PDF - works as before (regression test)
2. Upload batch of 2 PDFs - creates 2 jobs, 1 project with merged results
3. Add floor plans PDF to existing project - merges floor plan data
4. Cross-document dedup - same floor plan in brochure and floor_plans.pdf only appears once
5. Document attribution - can trace which images came from which source

---

## User Decisions

1. **Document type taxonomy**: Flexible tagging (free-form field, user enters whatever they want)
2. **Add to completed projects**: Yes, with re-processing (re-run content generation with merged data)
3. **Processing order**: Parallel (process all documents simultaneously)

---

## Merge Behavior

When same data exists in multiple documents:
- **Floor plans**: Keep all unique, dedupe by pHash (95% threshold)
- **Images**: Keep all unique per category, dedupe within category
- **Text/specs**: Concatenate with source attribution (document type + filename)
- **Structured data**: Later document overwrites earlier for same field (user can re-order priority)

---

## v.4 Release Notes (Draft)

### Breaking Changes
- None for existing single-PDF workflows

### New Features
- **Multi-document projects**: Upload multiple PDFs per project (brochure + floor plans + specs)
- **Batch upload**: Upload all documents at once with parallel processing
- **Add to project**: Add documents to existing/completed projects with automatic re-processing
- **Document tagging**: Free-form document type labels (not fixed taxonomy)
- **Cross-document deduplication**: Floor plans and images deduplicated across all source PDFs
- **Source attribution**: Track which document each extraction came from

### Database Changes
- New `project_jobs` table (many-to-many relationship)
- New columns: `jobs.document_type`, `jobs.parent_project_id`
- New column: `projects.source_documents` (JSONB array)

### Migration Path
- v.3 projects continue to work (single job per project)
- No data migration required for existing projects
- New features available immediately after schema migration
