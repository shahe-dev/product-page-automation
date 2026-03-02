# Plan: Phase 3 - Dynamic Field Editor

**Status:** Complete
**Created:** 2026-02-03
**Last Updated:** 2026-02-03

## Objective
Build an admin UI to edit template field definitions (Template.field_mappings) without code deployment.

## Decisions Log
| # | Decision | Rationale | Agreed |
|---|----------|-----------|--------|
| 1 | Add new endpoints by template_type (not ID) | User spec requires /templates/{template_type}/fields routes; matches how prompts API works | [x] |
| 2 | Keep existing GET /templates and GET /templates/{id} | Backwards compat, already used | [x] |
| 3 | Full field_mappings replace on PUT | Simpler than JSONB patch operations, frontend sends full state | [x] |
| 4 | Soft-delete fields by marking inactive in JSON | Spec says "soft-delete field", implement by adding "is_active: false" to field def | [x] |
| 5 | Validation in backend helper function | Centralize validation logic as validate_field_mappings() | [x] |
| 6 | Add templates API methods to api.ts | Follow existing pattern (prompts, projects, etc.) | [x] |
| 7 | Add /templates route for FieldEditor page | New route at /templates with AdminRoute protection | [x] |
| 8 | Reuse existing UI components (shadcn) | Table, Dialog, Input, Select already available | [x] |

## Constraints
### Must (Hard Requirements)
- Changes persist to Template.field_mappings JSONB in DB
- ContentGenerator and SheetsManager pick up changes immediately (no restart)
- Validation prevents invalid configurations
- No code deployment required for field changes

### Must Not (Explicit Exclusions)
- Modify JSON fallback files
- Require service restart for changes to take effect

### Should (Preferences)
- Inline editing for quick changes
- Drag-to-reorder for row management (deferred - not implemented)
- Unsaved changes warning

## Scope

### In Scope
- Backend CRUD API for template fields
- Frontend field editor component
- Integration with existing PromptsPage
- Tests for both backend and frontend

### Out of Scope
- Prompt editing (already exists)
- Template creation (templates are pre-seeded)
- Field versioning/history

## Files Created/Modified
| File | Action | Description |
|------|--------|-------------|
| `backend/app/api/routes/templates.py` | modified | Added 5 new field CRUD endpoints, Pydantic models, validation helper |
| `backend/tests/test_templates_api.py` | created | 17 test cases covering all endpoints |
| `frontend/src/types/index.ts` | modified | Added FieldDefinition and related types |
| `frontend/src/lib/api.ts` | modified | Added templates API methods |
| `frontend/src/hooks/queries/use-templates.ts` | created | React Query hooks for field CRUD |
| `frontend/src/components/templates/FieldEditor.tsx` | created | Main editor component |
| `frontend/src/components/templates/FieldRow.tsx` | created | Editable row component |
| `frontend/src/components/templates/AddFieldModal.tsx` | created | Add field dialog |
| `frontend/src/components/templates/index.ts` | created | Component exports |
| `frontend/src/pages/TemplatesPage.tsx` | created | Page with template tabs |
| `frontend/src/router/index.tsx` | modified | Added /templates route with AdminRoute |

## Edge Cases
| Scenario | Handling |
|----------|----------|
| Duplicate row numbers | Allow for bullet fields, reject otherwise |
| Missing template in DB | Return 404 |
| Invalid field_type | Return 400 with validation errors |
| Concurrent edits | Last write wins (acceptable for admin tool) |

## Open Questions (RESOLVED)
- [x] Does templates.py already exist? What endpoints? -> YES, has GET /templates, GET /templates/{id}, GET /templates/{id}/fields. Need to ADD field CRUD by template_type
- [x] What's the current Template model structure? -> Template model (database.py:877-919): id, name, template_type, content_variant, sheet_template_url, field_mappings (JSONB), is_active, timestamps
- [x] How does template_fields.py load fields currently? -> Loads from scripts/field_row_mappings.json at module init. Returns FieldDef dataclass with row, section, char_limit, required, field_type
- [x] What React Query patterns are used in frontend? -> Uses @tanstack/react-query with hooks in hooks/queries/. Pattern: useQuery for reads, useMutation for writes with queryClient.invalidateQueries on success

## Execution Checklist

### Task 3.1: Backend API
- [x] Add validate_field_mappings() helper to templates.py
- [x] Add GET /templates/type/{template_type}/fields endpoint
- [x] Add PUT /templates/type/{template_type}/fields endpoint (full replace)
- [x] Add POST /templates/type/{template_type}/fields/{field_name} endpoint (add single field)
- [x] Add DELETE /templates/type/{template_type}/fields/{field_name} endpoint (soft delete)
- [x] Add PATCH /templates/type/{template_type}/fields/{field_name} endpoint (partial update)
- [x] Add Pydantic request/response models

### Task 3.2: Frontend Components
- [x] Add template types to frontend/src/types/index.ts
- [x] Add templates API methods to frontend/src/lib/api.ts
- [x] Create frontend/src/hooks/queries/use-templates.ts
- [x] Create frontend/src/components/templates/FieldEditor.tsx
- [x] Create frontend/src/components/templates/FieldRow.tsx
- [x] Create frontend/src/components/templates/AddFieldModal.tsx
- [x] Create frontend/src/pages/TemplatesPage.tsx

### Task 3.3: Integration
- [x] Add /templates route to router/index.tsx
- [ ] Add navigation link (sidebar or admin menu) - Optional, can be accessed directly at /templates

### Task 3.4: Tests
- [x] Create backend/tests/test_templates_api.py
- [x] Test all CRUD operations
- [x] Test validation error handling

## API Endpoints Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /templates/type/{template_type}/fields | User | Get all field definitions |
| PUT | /templates/type/{template_type}/fields | Admin | Replace all fields |
| POST | /templates/type/{template_type}/fields/{field_name} | Admin | Add single field |
| DELETE | /templates/type/{template_type}/fields/{field_name} | Admin | Soft-delete field |
| PATCH | /templates/type/{template_type}/fields/{field_name} | Admin | Partial update |

## Notes
- Drag-to-reorder functionality was deferred - can be added later with react-dnd or similar
- Frontend route is admin-only via AdminRoute wrapper
- Legacy field_mappings format (string cell references) is handled gracefully in GET endpoint
