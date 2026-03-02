# Database Schema Audit Report

**Audit Date:** 2026-01-29
**Branch:** feature/phase-11-pymupdf4llm-integration
**Auditor:** Claude Opus 4.5 (Automated)
**Scope:** ORM models, Alembic migrations, database configuration, repositories

---

## Executive Summary

22 ORM models were audited across 3 migration files, 2 repository files, 1 Pydantic schema file, and database configuration. The audit found **27 findings** spanning data integrity, performance, correctness, and configuration concerns. The most critical issues are enum drift between ORM models and migration check constraints, missing `ON DELETE` behavior on 17 foreign keys, a missing unique constraint on the `prompts` table, and pervasive use of naive `datetime.utcnow()` in application code that will produce timezone-unaware timestamps despite timezone-aware column definitions.

**Severity Breakdown:**
- P0 (Critical): 4
- P1 (High): 8
- P2 (Medium): 11
- P3 (Low): 4

---

## Finding F01: ImageCategory Enum Drift -- ORM Has Values Not in Migration Check Constraint

- **Severity:** P0
- **File:** `backend/app/models/enums.py:67-76` vs `backend/alembic/versions/001_initial_schema.py:183`
- **Description:** The `ImageCategory` enum in Python defines 8 values (`interior`, `exterior`, `amenity`, `logo`, `floor_plan`, `location_map`, `master_plan`, `other`), but the migration check constraint only allows 6 values (`interior`, `exterior`, `amenity`, `logo`, `floor_plan`, `other`). Inserting a `ProjectImage` with `category='location_map'` or `category='master_plan'` will fail at the database level.
- **Evidence:**
  ```python
  # enums.py
  class ImageCategory(str, enum.Enum):
      INTERIOR = "interior"
      EXTERIOR = "exterior"
      AMENITY = "amenity"
      LOGO = "logo"
      FLOOR_PLAN = "floor_plan"
      LOCATION_MAP = "location_map"   # NOT in migration
      MASTER_PLAN = "master_plan"     # NOT in migration
      OTHER = "other"
  ```
  ```python
  # 001_initial_schema.py:183
  sa.CheckConstraint(
      "category IN ('interior', 'exterior', 'amenity', 'logo', 'floor_plan', 'other')",
      name='check_image_category'
  )
  ```
- **Fix:** Create a new migration (004) that drops and recreates the check constraint:
  ```python
  op.drop_constraint('check_image_category', 'project_images', type_='check')
  op.create_check_constraint(
      'check_image_category', 'project_images',
      "category IN ('interior', 'exterior', 'amenity', 'logo', 'floor_plan', 'location_map', 'master_plan', 'other')"
  )
  ```

---

## Finding F02: UserRole Enum Drift -- Migration Check Constraint Missing 'manager' Role

- **Severity:** P0
- **File:** `backend/alembic/versions/001_initial_schema.py:47` vs `backend/app/models/enums.py:11-13`
- **Description:** The migration check constraint restricts `role` to `('admin', 'user')`, which matches the current Python enum. However, the frontend references a `ManagerRoute` component and a "Manager" sidebar item (see `frontend/src/router/index.tsx:199`, `frontend/src/components/layout/Sidebar.tsx:37`). If a `manager` role is ever needed (which the frontend clearly expects), the DB will reject it. The enum and migration are consistent with each other but inconsistent with the frontend expectations.
- **Evidence:**
  ```python
  # 001_initial_schema.py:47
  sa.CheckConstraint("role IN ('admin', 'user')", name='check_user_role')
  ```
  ```tsx
  // frontend/src/components/layout/Sidebar.tsx:37
  { icon: BarChart, label: "Manager", path: "/manager", roles: ["admin"] }
  ```
- **Fix:** Add a `MANAGER = "manager"` value to `UserRole` enum and create a migration to update the check constraint to include `'manager'`. Alternatively, confirm the frontend manager feature is admin-only and document that decision.

---

## Finding F03: Missing Unique Constraint on Prompts (template_type, content_variant, name, is_active)

- **Severity:** P0
- **File:** `backend/app/models/database.py:791-796`
- **Description:** The `Prompt` model docstring explicitly states "One active prompt per (template_type, content_variant, name) combination" but there is no unique constraint or partial unique index enforcing this. Multiple active prompts with the same (template_type, content_variant, name) can exist, leading to ambiguous prompt resolution.
- **Evidence:**
  ```python
  class Prompt(Base, TimestampMixin):
      """
      Version-controlled prompt library for AI content generation.
      One active prompt per (template_type, content_variant, name) combination.
      """
      # ...
      __table_args__ = (
          Index("idx_prompts_template_type", "template_type"),
          Index("idx_prompts_content_variant", "content_variant"),
          Index("idx_prompts_name", "name"),
          Index("idx_prompts_active", "is_active"),
          # NO unique constraint!
      )
  ```
- **Fix:** Add a partial unique index in a new migration:
  ```python
  op.execute("""
      CREATE UNIQUE INDEX uq_prompts_active_per_type_variant_name
      ON prompts (template_type, content_variant, name)
      WHERE is_active = true
  """)
  ```
  And add the corresponding index to the ORM model `__table_args__`.

---

## Finding F04: datetime.utcnow() Used Everywhere -- Produces Timezone-Naive Timestamps

- **Severity:** P0
- **File:** `backend/app/repositories/job_repository.py:209,226,229,263,291,294,331,354,426,448` and `backend/app/repositories/project_repository.py:112,126,355`
- **Description:** All DateTime columns are defined with `timezone=True` and use `server_default=func.now()` (which produces timezone-aware timestamps). However, application-level updates use `datetime.utcnow()` which returns timezone-naive datetime objects. When SQLAlchemy stores these, PostgreSQL will interpret them as local time (or raise errors depending on driver configuration). This creates inconsistency between server-generated and application-generated timestamps.
- **Evidence:**
  ```python
  # job_repository.py:209
  "updated_at": datetime.utcnow()  # naive datetime

  # database.py:49 -- column definition expects tz-aware
  updated_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),  # expects timezone-aware
      server_default=func.now(),
  )
  ```
- **Fix:** Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)` throughout the codebase. Import `from datetime import timezone` where needed. `datetime.utcnow()` is deprecated as of Python 3.12.

---

## Finding F05: 17 Foreign Keys Missing ON DELETE Behavior

- **Severity:** P1
- **File:** `backend/app/models/database.py` (multiple locations)
- **Description:** 17 foreign keys to `users.id`, `templates.id`, and `prompt_versions.id` have no `ondelete` specification, defaulting to `NO ACTION` / `RESTRICT`. Deleting a user who has created projects, prompts, approvals, revisions, jobs, QA checkpoints, or generated content will fail with a foreign key violation. This is especially problematic since users have an `is_active` soft-delete field but the FK constraints prevent hard deletes if ever needed.
- **Evidence:**
  The following FKs lack `ondelete`:
  ```
  database.py:296   Project.created_by -> users.id
  database.py:300   Project.last_modified_by -> users.id
  database.py:521   ProjectApproval.approver_id -> users.id
  database.py:573   ProjectRevision.changed_by -> users.id
  database.py:616   Job.user_id -> users.id
  database.py:622   Job.template_id -> templates.id
  database.py:774   Prompt.created_by -> users.id
  database.py:779   Prompt.updated_by -> users.id
  database.py:829   PromptVersion.created_by -> users.id
  database.py:935   QAComparison.performed_by -> users.id
  database.py:1046  WorkflowItem.assigned_to -> users.id
  database.py:1130  ExecutionHistory.user_id -> users.id
  database.py:1197  QACheckpoint.checked_by -> users.id
  database.py:1251  QAIssue.resolved_by -> users.id
  database.py:1302  QAOverride.overridden_by -> users.id
  database.py:1401  GeneratedContent.prompt_version_id -> prompt_versions.id
  database.py:1411  GeneratedContent.approved_by -> users.id
  ```
- **Fix:** For audit/attribution FKs (created_by, changed_by, approved_by, etc.), use `ondelete="SET NULL"` and ensure the columns are nullable. For operational FKs like `Job.user_id`, decide between `SET NULL` (preserving orphaned jobs) or `CASCADE` (deleting related jobs). For `Job.template_id` and `GeneratedContent.prompt_version_id`, use `SET NULL` to preserve history even if the template/version is removed.

---

## Finding F06: Migration FK Behavior Drift from ORM Models

- **Severity:** P1
- **File:** `backend/alembic/versions/001_initial_schema.py:98` vs `backend/app/models/database.py:616`
- **Description:** In the ORM model, `Job.user_id` has `ForeignKey("users.id")` with no ondelete. In migration 001, it's also `sa.ForeignKeyConstraint(['user_id'], ['users.id'])` with no ondelete. These are consistent. However, the `projects.created_by` and `projects.last_modified_by` FKs in the migration also lack ondelete -- but the ORM model also lacks it, so they match. The real drift is that the migration for `Job.user_id` (line 98) does not specify ondelete, which means RESTRICT in PostgreSQL, preventing user deletion if they have any jobs. This is the same issue as F05 but specifically noting the migration/ORM alignment.
- **Evidence:**
  ```python
  # 001_initial_schema.py:98
  sa.ForeignKeyConstraint(['user_id'], ['users.id']),  # NO ondelete

  # database.py:616
  ForeignKey("users.id"),  # NO ondelete -- matches migration but both are wrong
  ```
- **Fix:** Once the desired ON DELETE behavior is decided (F05), create a migration to add `ON DELETE SET NULL` or `ON DELETE CASCADE` to all affected foreign keys.

---

## Finding F07: Duplicate Base Class Definition

- **Severity:** P1
- **File:** `backend/app/config/database.py:28-30` vs `backend/app/models/database.py:37-39`
- **Description:** There are two `Base` classes defined: one in `app.config.database` (plain `DeclarativeBase`) and one in `app.models.database` (`AsyncAttrs, DeclarativeBase`). The models use the one from `app.models.database`, but `initialize_database()` in `app.config.database` calls `Base.metadata.create_all` using the local `Base` which has NO models registered against it. This means the `initialize_database()` function is a no-op -- it will create zero tables.
- **Evidence:**
  ```python
  # config/database.py:28
  class Base(DeclarativeBase):
      """Base class for all database models."""
      pass

  # models/database.py:37
  class Base(AsyncAttrs, DeclarativeBase):
      """Base class for all database models with async support."""
      pass
  ```
- **Fix:** Remove the `Base` class from `config/database.py` and import it from `app.models.database` instead. Update `initialize_database()` to use the correct Base:
  ```python
  from app.models.database import Base
  ```

---

## Finding F08: PublicationChecklist.items JSONB Field Missing Default

- **Severity:** P1
- **File:** `backend/app/models/database.py:1087`
- **Description:** The `PublicationChecklist.items` JSONB field is `nullable=False` but has no `server_default`. Inserting a row without explicitly providing `items` will fail with a NOT NULL violation. All other mandatory JSONB fields in the schema have `server_default` values.
- **Evidence:**
  ```python
  items: Mapped[dict] = mapped_column(JSONB, nullable=False)
  # Compare with other JSONB fields:
  # property_types has server_default=text("'[]'::jsonb")
  # custom_fields has server_default=text("'{}'::jsonb")
  ```
- **Fix:** Add a server default:
  ```python
  items: Mapped[dict] = mapped_column(
      JSONB,
      nullable=False,
      server_default=text("'[]'::jsonb")
  )
  ```
  And create a migration to add the server default to the existing column.

---

## Finding F09: Template.field_mappings JSONB Field Missing Default

- **Severity:** P1
- **File:** `backend/app/models/database.py:881`
- **Description:** `Template.field_mappings` is `nullable=False` with no `server_default`. Same issue as F08 -- inserting without explicitly providing field_mappings will fail.
- **Evidence:**
  ```python
  field_mappings: Mapped[dict] = mapped_column(JSONB, nullable=False)
  ```
- **Fix:** Add `server_default=text("'{}'::jsonb")` to the column definition and create a corresponding migration.

---

## Finding F10: ProjectFloorPlan.parsed_data JSONB Without Default

- **Severity:** P2
- **File:** `backend/app/models/database.py:469`
- **Description:** `ProjectFloorPlan.parsed_data` is nullable (which is acceptable since it's Optional), but has no server_default. When data is not yet parsed, the value will be NULL rather than an empty object. This is a design choice, but inconsistent with other JSONB fields in the schema that use empty arrays/objects as defaults.
- **Evidence:**
  ```python
  parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB)
  # No server_default
  ```
- **Fix:** Either add `server_default=text("'{}'::jsonb")` for consistency, or document the intentional use of NULL to distinguish "not yet parsed" from "parsed but empty." This is acceptable as-is if the NULL semantics are intentional.

---

## Finding F11: Job.processing_config JSONB Without Default

- **Severity:** P2
- **File:** `backend/app/models/database.py:624`
- **Description:** `Job.processing_config` is nullable with no server default. Same as F10 -- acceptable if NULL means "no config provided" but inconsistent with other JSONB patterns in the schema.
- **Evidence:**
  ```python
  processing_config: Mapped[Optional[dict]] = mapped_column(JSONB)
  ```
- **Fix:** Consider adding `server_default=text("'{}'::jsonb")` for consistency. The `JobRepository.create_job()` already defaults to `{}` at the application level (line 66: `processing_config=processing_config or {}`), suggesting the intent is never-null.

---

## Finding F12: N+1 Query Risk in QA and Workflow Routes

- **Severity:** P1
- **File:** `backend/app/api/routes/qa.py:109,140,217,264` and `backend/app/api/routes/workflow.py:116,165,219`
- **Description:** Several route handlers query `Project` and `QAIssue` models without any `selectinload` options, then potentially access related objects (e.g., project.images, project.creator). If the route handler or serializer accesses lazy-loaded relationships, each access triggers a separate database query. The repository layer correctly uses `selectinload`, but direct queries in route handlers do not.
- **Evidence:**
  ```python
  # qa.py:109
  result = await db.execute(select(Project).where(Project.id == request.project_id))
  # No selectinload -- accessing project.images later will trigger N+1

  # workflow.py:116
  query = select(Project).where(Project.is_active.is_(True))
  # No selectinload for list queries
  ```
- **Fix:** Add `selectinload` options for any relationships that will be accessed in the response:
  ```python
  result = await db.execute(
      select(Project)
      .options(selectinload(Project.creator), selectinload(Project.images))
      .where(Project.id == request.project_id)
  )
  ```

---

## Finding F13: No Composite Index for Prompt Lookup by (template_type, content_variant, name)

- **Severity:** P1
- **File:** `backend/app/models/database.py:791-796`
- **Description:** Prompts are likely queried by the combination of `(template_type, content_variant, name)` to find the active prompt for a given template and variant. There are only individual indexes on each column, not a composite index. The query planner may not combine these efficiently.
- **Evidence:**
  ```python
  __table_args__ = (
      Index("idx_prompts_template_type", "template_type"),
      Index("idx_prompts_content_variant", "content_variant"),
      Index("idx_prompts_name", "name"),
      Index("idx_prompts_active", "is_active"),
      # Missing: composite index for the common lookup pattern
  )
  ```
- **Fix:** Add a composite index:
  ```python
  Index("idx_prompts_lookup", "template_type", "content_variant", "name", "is_active"),
  ```

---

## Finding F14: Missing Index on generated_content(project_id, template_type, content_variant)

- **Severity:** P2
- **File:** `backend/app/models/database.py:1430-1434`
- **Description:** `GeneratedContent` will commonly be queried by `(project_id, template_type, content_variant)` to find all generated content for a specific project and template combination. Only individual column indexes exist.
- **Evidence:**
  ```python
  __table_args__ = (
      Index("idx_generated_content_project_id", "project_id"),
      Index("idx_generated_content_field", "field_name"),
      Index("idx_generated_content_template", "template_type"),
      # No composite index for common query pattern
  )
  ```
- **Fix:** Add a composite index:
  ```python
  Index("idx_generated_content_project_template", "project_id", "template_type", "content_variant"),
  ```

---

## Finding F15: Missing Index on notifications(user_id, created_at) for User Notification Feed

- **Severity:** P2
- **File:** `backend/app/models/database.py:1015-1018`
- **Description:** The notification feed for a user is typically queried as `WHERE user_id = ? ORDER BY created_at DESC`. There is an index on `(user_id, is_read)` but not on `(user_id, created_at DESC)`. The `created_at` index is a standalone single-column index, not useful for the user-specific feed query.
- **Evidence:**
  ```python
  __table_args__ = (
      Index("idx_notifications_user_id", "user_id"),
      Index("idx_notifications_is_read", "user_id", "is_read"),
      Index("idx_notifications_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
  )
  ```
- **Fix:** Add a composite index for the feed query:
  ```python
  Index("idx_notifications_user_feed", "user_id", "created_at", postgresql_ops={"created_at": "DESC"}),
  ```

---

## Finding F16: Session Auto-Commit in get_db_session May Cause Unexpected Commits

- **Severity:** P1
- **File:** `backend/app/config/database.py:99-107`
- **Description:** The `get_db_session` dependency auto-commits on success (`await session.commit()`). This means any query execution -- even read-only operations -- will trigger a commit. If a route handler reads data and makes no changes, a commit is unnecessary overhead. More critically, if a route handler needs to do its own transaction management (e.g., partial commits), the auto-commit on exit will commit partial work that should have been rolled back.
- **Evidence:**
  ```python
  async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
      async with async_session_factory() as session:
          try:
              yield session
              await session.commit()  # Always commits on success
          except Exception:
              await session.rollback()
              raise
          finally:
              await session.close()
  ```
- **Fix:** Two options: (a) Remove the auto-commit and require explicit commits in route handlers (preferred for fine-grained control), or (b) Keep auto-commit but document this behavior clearly and ensure route handlers that need multi-step transactions use `session.begin_nested()` for savepoints.

---

## Finding F17: JobRepository Commits Individually -- Breaks Unit of Work Pattern

- **Severity:** P1
- **File:** `backend/app/repositories/job_repository.py:73,108,236,266,312,334,357,458`
- **Description:** The `JobRepository` calls `await self.db.commit()` after every single operation (create, update, status change). This conflicts with the `get_db_session` dependency which also auto-commits at the end of the request. Double-committing is wasteful but not harmful. However, the bigger issue is that if a route handler calls multiple repository methods that should be atomic, each one commits independently, breaking the unit-of-work pattern.
- **Evidence:**
  ```python
  # job_repository.py:73
  async def create_job(...) -> Job:
      self.db.add(job)
      await self.db.commit()  # Commits immediately

  # Compare with project_repository.py:55
  async def create(...) -> Project:
      self.db.add(project)
      await self.db.flush()  # Correct -- flushes but doesn't commit
  ```
- **Fix:** Replace `self.db.commit()` with `self.db.flush()` in all repository methods. Let the session lifecycle manager (the FastAPI dependency) handle commits. This matches the pattern already used in `ProjectRepository`.

---

## Finding F18: Soft Delete Inconsistency -- Tables Missing is_active

- **Severity:** P2
- **File:** `backend/app/models/database.py` (multiple tables)
- **Description:** Only `User`, `Project`, `Prompt`, and `Template` have `is_active` fields for soft delete. Other tables that reference soft-deletable entities (e.g., `Job`, `WorkflowItem`, `ExecutionHistory`) do not have soft delete. If a project is soft-deleted, its related `WorkflowItem` rows remain visible. Queries filtering by `is_active` on projects will exclude them, but direct queries on workflow_items will still return items for inactive projects.
- **Evidence:**
  Tables WITH `is_active`: `users`, `projects`, `prompts`, `templates`
  Tables WITHOUT but arguably should have: `jobs` (a cancelled job is different from a deleted one), `workflow_items` (should be hidden when project is inactive)
- **Fix:** For `workflow_items`, join through `project.is_active` in queries rather than adding a separate flag. For `jobs`, consider whether soft delete is needed or if the `status = CANCELLED` enum value suffices. Document the soft-delete strategy in a schema design doc.

---

## Finding F19: No Index on qa_issues(project_id, is_resolved) for Dashboard Queries

- **Severity:** P2
- **File:** `backend/app/models/database.py:1270-1275`
- **Description:** Dashboard queries likely filter QA issues by `project_id` and `is_resolved` simultaneously (e.g., "show me unresolved issues for this project"). There are separate indexes on `project_id` and `is_resolved` but no composite.
- **Evidence:**
  ```python
  __table_args__ = (
      Index("idx_qa_issues_checkpoint_id", "checkpoint_id"),
      Index("idx_qa_issues_project_id", "project_id"),
      Index("idx_qa_issues_severity", "severity"),
      Index("idx_qa_issues_is_resolved", "is_resolved"),
  )
  ```
- **Fix:** Add a composite index:
  ```python
  Index("idx_qa_issues_project_unresolved", "project_id", "is_resolved"),
  ```

---

## Finding F20: PromptVersion Missing Unique Constraint on (prompt_id, version)

- **Severity:** P2
- **File:** `backend/app/models/database.py:846-850`
- **Description:** There is an index on `(prompt_id, version)` but it is not a unique index. The same version number could be inserted twice for the same prompt, creating data corruption. The prompt versioning code increments `prompt.version + 1` and creates a PromptVersion record, but without a unique constraint, concurrent requests could create duplicate versions.
- **Evidence:**
  ```python
  __table_args__ = (
      Index("idx_prompt_versions_prompt_id", "prompt_id"),
      Index("idx_prompt_versions_version", "prompt_id", "version",
            postgresql_ops={"version": "DESC"}),
      # This is a non-unique index -- allows duplicates
  )
  ```
- **Fix:** Add a unique constraint:
  ```python
  sa.UniqueConstraint('prompt_id', 'version', name='uq_prompt_version_per_prompt'),
  ```

---

## Finding F21: Connection Pool Configuration -- pool_recycle=3600 May Be Too Long for Cloud Run

- **Severity:** P2
- **File:** `backend/app/config/settings.py:37`
- **Description:** The default `pool_recycle=3600` (1 hour) is reasonable for long-running servers but may cause issues on Cloud Run where instances can be scaled to zero and back. Cloud SQL connections may be terminated by the proxy or load balancer before 1 hour. A shorter recycle time (e.g., 300-600 seconds) would be safer for Cloud Run deployments.
- **Evidence:**
  ```python
  DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Connection recycle time")
  ```
- **Fix:** Change default to 300 seconds for Cloud Run compatibility:
  ```python
  DATABASE_POOL_RECYCLE: int = Field(default=300, description="Connection recycle time")
  ```
  The `pool_pre_ping=True` setting (already enabled) mitigates stale connections, but recycling proactively is still better.

---

## Finding F22: Redundant Indexes on Unique Columns

- **Severity:** P3
- **File:** `backend/app/models/database.py:110-112`
- **Description:** The `users` table has explicit indexes on `email` and `google_id`, but both columns already have `unique=True` which creates implicit unique indexes. The explicit indexes are redundant and waste storage/write overhead.
- **Evidence:**
  ```python
  email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
  # ...
  __table_args__ = (
      Index("idx_users_email", "email"),       # redundant with unique=True
      Index("idx_users_google_id", "google_id"), # redundant with unique=True
  )
  ```
  Same issue in `refresh_tokens`:
  ```python
  token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
  # ...
  Index("idx_refresh_tokens_token_hash", "token_hash"),  # redundant
  ```
- **Fix:** Remove the redundant explicit indexes. The unique constraints already provide B-tree indexes:
  ```python
  __table_args__ = (
      # Remove idx_users_email and idx_users_google_id
      Index("idx_users_role", "role"),
  )
  ```

---

## Finding F23: ProjectFloorPlan Missing updated_at Timestamp

- **Severity:** P2
- **File:** `backend/app/models/database.py:442-494`
- **Description:** `ProjectFloorPlan` does not use `TimestampMixin` and only has `created_at`. If floor plan data (unit_type, bedrooms, parsed_data, etc.) is ever updated, there is no audit trail of when the update occurred. Other entities like `ProjectImage` also lack `updated_at`, but images are less likely to be modified after creation.
- **Evidence:**
  ```python
  class ProjectFloorPlan(Base):  # No TimestampMixin
      # ...
      created_at: Mapped[datetime] = mapped_column(...)
      # No updated_at
  ```
- **Fix:** Either add `TimestampMixin` to `ProjectFloorPlan` or add an explicit `updated_at` column if floor plan data is mutable. If floor plans are immutable (delete + recreate), this is acceptable as-is.

---

## Finding F24: QACheckpoint.checkpoint_metadata Uses Column Aliasing That May Cause Confusion

- **Severity:** P3
- **File:** `backend/app/models/database.py:1188-1193`
- **Description:** The `checkpoint_metadata` Python attribute maps to a DB column named `metadata`. This aliasing can cause confusion -- Python code uses `checkpoint.checkpoint_metadata` but raw SQL queries use `metadata`. The name `metadata` also conflicts with SQLAlchemy's internal `MetaData` class name, which is likely why it was aliased.
- **Evidence:**
  ```python
  checkpoint_metadata: Mapped[dict] = mapped_column(
      "metadata",  # DB column is 'metadata'
      JSONB,
      nullable=False,
      server_default=text("'{}'::jsonb")
  )
  ```
- **Fix:** This is an intentional workaround and acceptable. Consider renaming the DB column to `checkpoint_metadata` in a future migration for consistency, but the current approach works correctly.

---

## Finding F25: execution_history.entity_id Has No FK Constraint (Polymorphic Reference)

- **Severity:** P2
- **File:** `backend/app/models/database.py:1125`
- **Description:** `ExecutionHistory.entity_id` is a UUID that references different tables depending on `entity_type` ("project", "job", "prompt"). Since it's a polymorphic reference, there is no FK constraint. This means entity_id can reference non-existent records (e.g., after a hard delete), and there's no way to enforce referential integrity at the database level.
- **Evidence:**
  ```python
  entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
  # No ForeignKey -- intentional for polymorphic reference
  ```
- **Fix:** This is a known trade-off with polymorphic audit tables. Acceptable as-is, but add a comment in the model documenting this design decision. Consider adding application-level validation that entity_id references a valid record before insertion.

---

## Finding F26: WorkflowItem Should Have Unique Constraint on project_id

- **Severity:** P2
- **File:** `backend/app/models/database.py:1056-1058`
- **Description:** Each project should appear at most once in the workflow/kanban board. There is no unique constraint on `project_id`, allowing the same project to appear in multiple workflow positions, which would corrupt the kanban board display.
- **Evidence:**
  ```python
  __table_args__ = (
      Index("idx_workflow_items_project_id", "project_id"),  # not unique
      Index("idx_workflow_items_assigned_to", "assigned_to"),
  )
  ```
- **Fix:** Make the project_id index unique, or add a unique constraint:
  ```python
  sa.UniqueConstraint('project_id', name='uq_workflow_items_project_id'),
  ```

---

## Finding F27: Database URL Validation Allows Non-Async URLs

- **Severity:** P3
- **File:** `backend/app/config/settings.py:165-177`
- **Description:** The `DATABASE_URL` validator accepts both `postgresql://` and `postgresql+asyncpg://` URLs. However, the engine is created with `create_async_engine`, which requires an async driver. If a user provides `postgresql://` (without `+asyncpg`), the engine creation will fail at runtime with a confusing error.
- **Evidence:**
  ```python
  @field_validator("DATABASE_URL")
  @classmethod
  def validate_database_url(cls, v: str) -> str:
      if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
          raise ValueError(...)
      return v
  ```
- **Fix:** Either reject non-async URLs:
  ```python
  if not v.startswith("postgresql+asyncpg://"):
      raise ValueError("DATABASE_URL must use the asyncpg driver (postgresql+asyncpg://)")
  ```
  Or auto-convert:
  ```python
  if v.startswith("postgresql://"):
      v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
  return v
  ```

---

## Finding F28: Missing Index on job_steps(job_id, step_id) Composite

- **Severity:** P3
- **File:** `backend/app/models/database.py:725-729`
- **Description:** `JobRepository.get_job_step()` and `update_job_step()` query by `(job_id, step_id)`. There are individual indexes on each column but no composite index for this common query pattern.
- **Evidence:**
  ```python
  __table_args__ = (
      Index("idx_job_steps_job_id", "job_id"),
      Index("idx_job_steps_step_id", "step_id"),
      Index("idx_job_steps_status", "status"),
  )
  ```
  ```python
  # job_repository.py:178-184
  result = await self.db.execute(
      select(JobStep).where(
          and_(
              JobStep.job_id == job_id,
              JobStep.step_id == step_id
          )
      )
  )
  ```
- **Fix:** Add a composite index (and consider making it unique since each job should have at most one step with a given step_id):
  ```python
  Index("idx_job_steps_job_step", "job_id", "step_id", unique=True),
  ```

---

## Summary Table

| ID | Finding | Severity | Category |
|----|---------|----------|----------|
| F01 | ImageCategory enum drift (2 values missing from check constraint) | P0 | Data Integrity |
| F02 | UserRole missing 'manager' role (frontend expects it) | P0 | Data Integrity |
| F03 | Prompts missing unique constraint on active prompt per type/variant/name | P0 | Data Integrity |
| F04 | datetime.utcnow() produces naive timestamps with tz-aware columns | P0 | Correctness |
| F05 | 17 foreign keys missing ON DELETE behavior | P1 | Data Integrity |
| F06 | Migration FK behavior drift matches ORM but both are wrong | P1 | Data Integrity |
| F07 | Duplicate Base class definition (config vs models) | P1 | Correctness |
| F08 | PublicationChecklist.items JSONB missing server_default | P1 | Data Integrity |
| F09 | Template.field_mappings JSONB missing server_default | P1 | Data Integrity |
| F10 | ProjectFloorPlan.parsed_data JSONB inconsistent default strategy | P2 | Consistency |
| F11 | Job.processing_config JSONB inconsistent default strategy | P2 | Consistency |
| F12 | N+1 query risk in QA and Workflow route handlers | P1 | Performance |
| F13 | Missing composite index for prompt lookup pattern | P1 | Performance |
| F14 | Missing composite index on generated_content lookup | P2 | Performance |
| F15 | Missing composite index on notifications user feed | P2 | Performance |
| F16 | Session auto-commit on all requests (including reads) | P1 | Architecture |
| F17 | JobRepository breaks unit-of-work with per-method commits | P1 | Architecture |
| F18 | Soft delete inconsistency across tables | P2 | Consistency |
| F19 | Missing composite index on qa_issues(project_id, is_resolved) | P2 | Performance |
| F20 | PromptVersion missing unique constraint on (prompt_id, version) | P2 | Data Integrity |
| F21 | pool_recycle=3600 may be too long for Cloud Run | P2 | Configuration |
| F22 | Redundant indexes on unique columns | P3 | Performance |
| F23 | ProjectFloorPlan missing updated_at timestamp | P2 | Audit Trail |
| F24 | QACheckpoint metadata column aliasing | P3 | Consistency |
| F25 | ExecutionHistory polymorphic entity_id with no FK | P2 | Data Integrity |
| F26 | WorkflowItem missing unique constraint on project_id | P2 | Data Integrity |
| F27 | DATABASE_URL validator allows non-async URLs | P3 | Configuration |
| F28 | Missing composite index on job_steps(job_id, step_id) | P3 | Performance |

---

## Recommended Priority

### Immediate (P0 -- Block deployment)
1. **F01**: Fix ImageCategory check constraint via new migration
2. **F03**: Add partial unique index on prompts
3. **F04**: Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)`

### Short-term (P1 -- Fix before production)
4. **F05/F06**: Define and implement ON DELETE policy for all 17 FKs
5. **F07**: Fix duplicate Base class
6. **F08/F09**: Add JSONB server defaults
7. **F13**: Add composite index for prompt lookups
8. **F16/F17**: Fix session/commit lifecycle
9. **F12**: Add selectinload to route-level queries

### Medium-term (P2 -- Fix during next sprint)
10. **F02**: Decide on manager role
11. **F14/F15/F19**: Add missing composite indexes
12. **F20/F26**: Add missing unique constraints
13. **F21**: Tune pool_recycle for Cloud Run

### Low priority (P3 -- Backlog)
14. **F22**: Remove redundant indexes
15. **F24/F27/F28**: Minor consistency improvements
