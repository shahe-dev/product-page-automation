# Feasibility Assessment: Dynamic Template Creation & Editing

Date: 2026-02-02

## Feature 1: Create New Templates from UI

### Verdict: NOT FEASIBLE NOW. Do not build.

The 6 template types are hardcoded across **5 layers deep**. Adding a new template type without code deployment requires decoupling all of them simultaneously -- there is no incremental path.

### Coupling inventory (every location that rejects an unknown template type)

| Layer | File | What happens | Fix difficulty |
|-------|------|-------------|----------------|
| Python enum | `enums.py:98-105` | `TemplateType("new_type")` raises ValueError | HIGH - need runtime enum or remove enum entirely |
| DB CHECK constraints | `001_initial_schema.py` (5 places) | INSERT rejected at database level | HIGH - migration to DROP/ALTER constraints on 5 tables |
| ORM columns | `database.py` (5 models: Job, Prompt, Template, PublicationChecklist, GeneratedContent) | SQLAlchemy refuses to persist unknown enum value | HIGH - change from Enum column to String column |
| Field registry | `template_fields.py:443-448` | `get_fields_for_template()` raises ValueError | MEDIUM - add DB fallback |
| Prompt defaults | `prompt_manager.py` (6 methods, ~800 lines) | No default prompts for new type (falls back to generic) | LOW - generic fallback works, just low quality |
| Settings | `settings.py:88-111` | No `TEMPLATE_SHEET_ID_*` env var for new type | MEDIUM - move to DB/JSON config |
| Content generator | `content_generator.py:369-376` | Missing template description in system prompt | LOW - has generic fallback |
| Frontend types | `types/index.ts:53-59` | TypeScript compile error on unknown string | LOW - change to `string` type |
| Frontend dropdowns | `PromptCreateDialog.tsx`, `FileUpload.tsx` | New type doesn't appear in UI | LOW - fetch from API |

**Minimum to make it work:** 5 simultaneous changes (enum, DB constraints, ORM columns, settings, field registry). This is not a feature -- it is an architecture migration.

**Business case is weak:** You have 6 templates for 6 websites. New websites are rare. When one does come, a developer adds an enum value, a migration, a field dict, and a prompt method -- that is a straightforward code task, not a product emergency.

**Recommendation:** Do not pursue. If a 7th template is needed, treat it as a dev task (~2 hours of work).

---

## Feature 2: Edit Existing Templates (Fields, Mappings, Prompts)

### Verdict: PARTIALLY FEASIBLE. Prompts are ready now. Fields and mappings need Phase 2.

### 2A: Edit prompts for existing fields -- WORKS TODAY

The pipeline already supports this:
1. `PromptManager.get_prompt()` checks DB first, falls back to hardcoded defaults
2. Prompt CRUD API exists (`routes/prompts.py`)
3. Frontend prompt editor exists (`PromptEditor.tsx`)

**What's missing:** The prompts table is empty -- hardcoded defaults have never been seeded. Phase 2 Task 7 runs `seed_prompts.py --force` to populate it. After that, admin edits take immediate effect.

### 2B: Edit field definitions (add/remove/reorder fields) -- NEEDS PHASE 2 GROUNDWORK

Currently `template_fields.py` is the sole source of truth. `Template.field_mappings` JSONB exists in DB but is never read at runtime. Phase 2 Task 6 seeds it but the original plan didn't wire it into the pipeline.

**Phase 2 additions (3 DB-first lookups) enable this path:**

| Step | What | Files | Effort |
|------|------|-------|--------|
| 1 | `ContentGenerator` reads from `Template.field_mappings` (DB), falls back to `template_fields.py` | `content_generator.py` | Small -- added to Phase 2 Task 3 |
| 2 | `SheetsManager` reads from `Template.field_mappings` (DB), falls back to `get_cell_mapping()` | `sheets_manager.py` | Small -- added to Phase 2 Task 2 |
| 3 | Grouped prompts endpoint reads from DB when template record exists | `routes/prompts.py` | Small -- added to Phase 2 Task 4 |
| 4 | Template CRUD API: PUT `/templates/{id}/fields` | `routes/templates.py` | Medium -- Phase 3 |
| 5 | Frontend field editor UI | New component | Medium -- Phase 3 |
| 6 | Validation (no duplicate rows, valid sections) | Backend | Small -- Phase 3 |

**Risks:**
- Admin removes a field with existing generated content -> orphaned data (need soft-delete)
- Admin adds a field with no prompt -> UI should flag "missing prompt" and prompt creation

### 2C: Edit cell mappings -- SAME AS 2B

Cell mappings live inside `field_mappings` JSONB. Editing mappings IS editing field definitions -- same data structure, same feature.

---

## Summary

| Feature | Feasible? | When? | Effort |
|---------|-----------|-------|--------|
| Create new template from UI | No | Not recommended | Architecture migration (~2-3 sprints) |
| Edit prompts for existing fields | Yes | After Phase 2 Task 7 seeds DB | Zero additional work |
| Edit field definitions from UI | Yes, with groundwork | Phase 2 (groundwork) + Phase 3 (UI) | 3 small Phase 2 additions + Phase 3 |
| Edit cell mappings from UI | Same as field defs | Same | Same data structure |

---

## Action Items

1. **Phase 2 plan updated** with 3 DB-first lookup additions to Tasks 2, 3, and 4
2. **Do not build Feature 1** -- add new template types via code when needed
3. **Feature 2 prompt editing** is enabled once Phase 2 seed scripts run
4. **Feature 2 field editing** becomes Phase 3 -- enabled by Phase 2 groundwork
