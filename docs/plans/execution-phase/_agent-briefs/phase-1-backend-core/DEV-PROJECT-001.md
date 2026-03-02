# Agent Brief: DEV-PROJECT-001

**Agent ID:** DEV-PROJECT-001
**Agent Name:** Project Service Agent
**Type:** Development
**Phase:** 1 - Backend Core
**Context Budget:** 55,000 tokens

---

## Mission

Implement the complete project management service with CRUD operations, search, filtering, pagination, revision tracking, and custom fields support.

---

## Documentation to Read

### Primary (MUST READ)
1. `docs/02-modules/PROJECT_DATABASE.md` - Project data model and requirements
2. `docs/04-backend/SERVICE_LAYER.md` - Service patterns and conventions

### Secondary (SHOULD READ)
3. `docs/04-backend/API_ENDPOINTS.md` - Project API specifications
4. `docs/01-architecture/DATA_FLOW.md` - Data flow patterns

---

## Dependencies

**Upstream:**
- DEV-DB-001: Project, ProjectRevision models
- DEV-CONFIG-001: Database connection

**Downstream:**
- DEV-API-001: Needs project service for routes
- Frontend agents: Need project API

---

## Outputs to Produce

### File 1: `backend/app/services/project_service.py`
Project business logic service

### File 2: `backend/app/repositories/project_repository.py`
Database operations for projects

### File 3: `backend/app/api/routes/projects.py`
Project API endpoints

### File 4: `backend/app/models/schemas.py` (project schemas)
Pydantic models for project requests/responses

---

## Acceptance Criteria

1. **Full CRUD Operations:**
   - Create project with validation
   - Read single project by ID
   - Update project (partial updates)
   - Soft delete (set is_active=false)

2. **Search with Full-Text:**
   - Search by project name
   - Search by developer name
   - PostgreSQL full-text search

3. **Multi-Field Filtering:**
   - Filter by status
   - Filter by developer
   - Filter by emirate
   - Filter by price range (min/max)
   - Filter by date range (created_at)

4. **Pagination:**
   - Consistent response format
   - Total count included
   - Page and page_size parameters
   - Default 50 items per page

5. **Revision Tracking:**
   - Log all field changes
   - Store old_value, new_value
   - Track changed_by user
   - Query revision history

6. **Custom Fields:**
   - Add arbitrary key-value pairs
   - Stored in JSONB
   - Queryable

7. **Soft Deletion:**
   - is_active flag
   - Deleted projects excluded from queries
   - Admin can view deleted

---

## API Endpoints

```
GET    /api/v1/projects              List with filters
POST   /api/v1/projects              Create new
GET    /api/v1/projects/{id}         Get single
PUT    /api/v1/projects/{id}         Update
DELETE /api/v1/projects/{id}         Soft delete
GET    /api/v1/projects/{id}/history Revision history
POST   /api/v1/projects/{id}/fields  Add custom field
POST   /api/v1/projects/export       Export to CSV
```

---

## QA Pair

Your outputs will be reviewed by: **QA-PROJECT-001**

---

**Begin execution.**
