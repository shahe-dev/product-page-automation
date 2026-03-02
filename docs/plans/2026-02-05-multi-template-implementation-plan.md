# Multi-Template Pipeline Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the 14-step PDF processing pipeline into reusable Extraction Phase (steps 1-10) and lightweight Generation Phase (steps 11-14) so one PDF can produce content for multiple templates without redundant extraction.

**Architecture:** Extract once, generate many. MaterialPackage (GCS-backed) stores extraction results. New job types discriminate pipeline paths. Generation jobs consume existing packages in ~30-60s at ~$0.04 each vs ~$0.92 for full pipeline.

**Tech Stack:** FastAPI, PostgreSQL 16, SQLAlchemy 2.0 async, Alembic, React 19, TypeScript, React Query, GCS

---

## Constraints (Reference)

1. **Backward compatibility mandatory** - existing `/upload/pdf` with single template keeps working during transition
2. **All migrations additive** - no dropping columns, nullable or with defaults, reversible downgrade
3. **Frontend graceful degradation** - new fields optional, old displays don't break
4. **Don't block v4** - multi-document pipeline compatibility preserved
5. **Follow existing patterns** - no new conventions

## Single-Template Overhead Analysis

For single-template uploads, the new EXTRACTION + GENERATION flow adds ~500-750ms overhead vs the legacy FULL pipeline:
- Extra Cloud Task dispatch: ~300-500ms
- GCS writes (5 JSON files): ~50-100ms
- GCS reads at generation start: ~50-100ms
- Extra DB writes: ~20-50ms

**This is ~1-5% of the 2-7 minute total pipeline time** - negligible.

**Benefits outweigh overhead:**
1. Better failure recovery - extraction results preserved if generation fails
2. Future-proofing - same code path for 1 or N templates
3. Simpler codebase - no special "full" path to maintain

**Decision:** All uploads (single or multi-template) should use EXTRACTION + GENERATION. The FULL job type exists only for backward compatibility during transition and will be deprecated.

---

## Phase A: MaterialPackage Foundation

**Note on Constraints:** Migrations define indexes and check constraints. ORM models also define them in `__table_args__`. This is intentional:
- **Production:** Alembic migrations are the source of truth
- **Tests:** Use `alembic upgrade head` in test fixtures, NOT `Base.metadata.create_all()`
- The ORM `__table_args__` serve as documentation and for any ad-hoc table creation

If tests fail with "constraint already exists", ensure test fixtures use the Alembic runner.

---

### Task A.1: Add JobType Enum

**Files:**
- Modify: `backend/app/models/enums.py`
- Test: `backend/tests/test_enums.py` (create if needed)

**Step 1: Write the failing test**

```python
# backend/tests/test_enums.py
import pytest
from app.models.enums import JobType

def test_job_type_enum_values():
    """JobType enum has expected values."""
    assert JobType.FULL.value == "full"
    assert JobType.EXTRACTION.value == "extraction"
    assert JobType.GENERATION.value == "generation"
    assert len(JobType) == 3
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_enums.py::test_job_type_enum_values -v`
Expected: FAIL with "cannot import name 'JobType'"

**Step 3: Write minimal implementation**

Add to `backend/app/models/enums.py` after `ContentVariant`:

```python
class JobType(str, enum.Enum):
    """Job type for pipeline execution path."""
    FULL = "full"              # Legacy v.3 behavior (steps 1-14)
    EXTRACTION = "extraction"  # Steps 1-10 only, produces MaterialPackage
    GENERATION = "generation"  # Steps 11-14 only, consumes MaterialPackage
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_enums.py::test_job_type_enum_values -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/enums.py backend/tests/test_enums.py
git commit -m "$(cat <<'EOF'
feat: add JobType enum for pipeline execution paths

Adds FULL, EXTRACTION, GENERATION job types to support multi-template
pipeline optimization where extraction runs once and generation runs
per-template.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

**Breaks if done in isolation:** Nothing - enum is unused until referenced by model.

---

### Task A.2: Add MaterialPackageStatus Enum

**Files:**
- Modify: `backend/app/models/enums.py`
- Test: `backend/tests/test_enums.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_enums.py
from app.models.enums import MaterialPackageStatus

def test_material_package_status_enum_values():
    """MaterialPackageStatus enum has expected values."""
    assert MaterialPackageStatus.PENDING.value == "pending"
    assert MaterialPackageStatus.READY.value == "ready"
    assert MaterialPackageStatus.EXPIRED.value == "expired"
    assert MaterialPackageStatus.ERROR.value == "error"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_enums.py::test_material_package_status_enum_values -v`
Expected: FAIL with "cannot import name 'MaterialPackageStatus'"

**Step 3: Write minimal implementation**

Add to `backend/app/models/enums.py`:

```python
class MaterialPackageStatus(str, enum.Enum):
    """Status of a MaterialPackage."""
    PENDING = "pending"    # Extraction in progress
    READY = "ready"        # Available for generation
    EXPIRED = "expired"    # Past TTL, scheduled for cleanup
    ERROR = "error"        # Extraction failed
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_enums.py::test_material_package_status_enum_values -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/enums.py backend/tests/test_enums.py
git commit -m "$(cat <<'EOF'
feat: add MaterialPackageStatus enum

Tracks lifecycle of extraction results: pending -> ready -> expired.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

**Breaks if done in isolation:** Nothing - enum unused until model references it.

---

### Task A.3: Add GenerationRunStatus Enum

**Files:**
- Modify: `backend/app/models/enums.py`
- Test: `backend/tests/test_enums.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_enums.py
from app.models.enums import GenerationRunStatus

def test_generation_run_status_enum_values():
    """GenerationRunStatus enum has expected values."""
    assert GenerationRunStatus.PENDING.value == "pending"
    assert GenerationRunStatus.PROCESSING.value == "processing"
    assert GenerationRunStatus.COMPLETED.value == "completed"
    assert GenerationRunStatus.FAILED.value == "failed"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_enums.py::test_generation_run_status_enum_values -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
class GenerationRunStatus(str, enum.Enum):
    """Status of a generation run for a specific template."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_enums.py::test_generation_run_status_enum_values -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/enums.py backend/tests/test_enums.py
git commit -m "$(cat <<'EOF'
feat: add GenerationRunStatus enum

Tracks per-template content generation lifecycle.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.4: Create Migration - Add job_type to jobs table

**Files:**
- Create: `backend/alembic/versions/{timestamp}_add_job_type_to_jobs.py`

**Step 1: Generate migration file**

Run: `cd backend && alembic revision -m "add job_type to jobs"`

**Step 2: Write the migration**

```python
"""add job_type to jobs

Revision ID: {auto-generated}
Revises: c1234567890a
Create Date: {auto-generated}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '{auto-generated}'
down_revision: Union[str, None] = 'c1234567890a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add job_type column with default 'full' for backward compatibility
    op.add_column(
        'jobs',
        sa.Column('job_type', sa.String(length=50), nullable=False, server_default='full')
    )

    # Add check constraint for valid job types
    op.create_check_constraint(
        'check_job_type',
        'jobs',
        "job_type IN ('full', 'extraction', 'generation')"
    )

    # Add index for filtering by job type
    op.create_index('idx_jobs_job_type', 'jobs', ['job_type'])


def downgrade() -> None:
    op.drop_index('idx_jobs_job_type', table_name='jobs')
    op.drop_constraint('check_job_type', 'jobs', type_='check')
    op.drop_column('jobs', 'job_type')
```

**Step 3: Run migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration applies successfully

**Step 4: Verify with psql or test**

Run: `cd backend && python -c "from sqlalchemy import inspect; from app.config.database import engine; import asyncio; asyncio.run(engine.dispose())"`

Or verify manually:
```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'jobs' AND column_name = 'job_type';
```
Expected: job_type column exists with default 'full'

**Step 5: Commit**

```bash
git add backend/alembic/versions/*_add_job_type_to_jobs.py
git commit -m "$(cat <<'EOF'
feat(db): add job_type column to jobs table

Additive migration with server_default='full' for backward compatibility.
Supports: full (legacy), extraction, generation job types.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

**Breaks if done in isolation:** Nothing - column has default, existing code ignores it.

**Deploy sequence:** Run migration first, then deploy backend code that uses it.

---

### Task A.5: Create Migration - material_packages table

**Files:**
- Create: `backend/alembic/versions/{timestamp}_create_material_packages.py`

**Step 1: Generate migration file**

Run: `cd backend && alembic revision -m "create material_packages table"`

**Step 2: Write the migration**

```python
"""create material_packages table

Revision ID: {auto-generated}
Revises: {previous from A.4}
Create Date: {auto-generated}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '{auto-generated}'
down_revision: Union[str, None] = '{from A.4}'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'material_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gcs_base_path', sa.String(length=500), nullable=False),
        sa.Column('package_version', sa.String(length=10), nullable=False, server_default='1.0'),
        sa.Column('extraction_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('structured_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.CheckConstraint("status IN ('pending', 'ready', 'expired', 'error')", name='check_material_package_status')
    )

    op.create_index('idx_material_packages_project_id', 'material_packages', ['project_id'])
    op.create_index('idx_material_packages_status', 'material_packages', ['status'])
    op.create_index('idx_material_packages_source_job', 'material_packages', ['source_job_id'])


def downgrade() -> None:
    op.drop_index('idx_material_packages_source_job', table_name='material_packages')
    op.drop_index('idx_material_packages_status', table_name='material_packages')
    op.drop_index('idx_material_packages_project_id', table_name='material_packages')
    op.drop_table('material_packages')
```

**Step 3: Run migration**

Run: `cd backend && alembic upgrade head`

**Step 4: Verify table exists**

```sql
SELECT table_name FROM information_schema.tables WHERE table_name = 'material_packages';
```

**Step 5: Commit**

```bash
git add backend/alembic/versions/*_create_material_packages.py
git commit -m "$(cat <<'EOF'
feat(db): create material_packages table

Stores GCS paths and cached extraction results for reuse across
multiple template generations. Indexed by project_id and status.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.6: Create Migration - generation_runs table

**Files:**
- Create: `backend/alembic/versions/{timestamp}_create_generation_runs.py`

**Step 1: Generate migration file**

Run: `cd backend && alembic revision -m "create generation_runs table"`

**Step 2: Write the migration**

```python
"""create generation_runs table

Revision ID: {auto-generated}
Revises: {previous from A.5}
Create Date: {auto-generated}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '{auto-generated}'
down_revision: Union[str, None] = '{from A.5}'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'generation_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_package_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('generated_content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sheet_url', sa.String(length=500), nullable=True),
        sa.Column('drive_folder_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_package_id'], ['material_packages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('project_id', 'template_type', name='uq_generation_runs_project_template'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name='check_generation_run_status'),
        # NOTE: No template_type check constraint - ORM enum validation is sufficient.
        # Adding a DB constraint requires a migration for every new template type.
        # The SQLAlchemyEnum(TemplateType, native_enum=False) handles validation at app layer.
    )

    op.create_index('idx_generation_runs_project_id', 'generation_runs', ['project_id'])
    op.create_index('idx_generation_runs_status', 'generation_runs', ['status'])
    op.create_index('idx_generation_runs_template_type', 'generation_runs', ['template_type'])


def downgrade() -> None:
    op.drop_index('idx_generation_runs_template_type', table_name='generation_runs')
    op.drop_index('idx_generation_runs_status', table_name='generation_runs')
    op.drop_index('idx_generation_runs_project_id', table_name='generation_runs')
    op.drop_table('generation_runs')
```

**Step 3: Run migration**

Run: `cd backend && alembic upgrade head`

**Step 4: Verify**

```sql
SELECT constraint_name FROM information_schema.table_constraints
WHERE table_name = 'generation_runs' AND constraint_type = 'UNIQUE';
```
Expected: `uq_generation_runs_project_template`

**Step 5: Commit**

```bash
git add backend/alembic/versions/*_create_generation_runs.py
git commit -m "$(cat <<'EOF'
feat(db): create generation_runs table

Tracks per-template content generation with unique constraint on
(project_id, template_type) to prevent duplicate runs.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.7: Create Migration - Add material_package_id FK to jobs

**Files:**
- Create: `backend/alembic/versions/{timestamp}_add_material_package_id_to_jobs.py`

**Step 1: Generate migration file**

Run: `cd backend && alembic revision -m "add material_package_id to jobs"`

**Step 2: Write the migration**

```python
"""add material_package_id to jobs

Revision ID: {auto-generated}
Revises: {previous from A.6}
Create Date: {auto-generated}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '{auto-generated}'
down_revision: Union[str, None] = '{from A.6}'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable column first (no FK yet - table needs to exist)
    op.add_column(
        'jobs',
        sa.Column('material_package_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add FK constraint
    op.create_foreign_key(
        'fk_jobs_material_package_id',
        'jobs', 'material_packages',
        ['material_package_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add index for lookups
    op.create_index('idx_jobs_material_package_id', 'jobs', ['material_package_id'])


def downgrade() -> None:
    op.drop_index('idx_jobs_material_package_id', table_name='jobs')
    op.drop_constraint('fk_jobs_material_package_id', 'jobs', type_='foreignkey')
    op.drop_column('jobs', 'material_package_id')
```

**Step 3: Run migration**

Run: `cd backend && alembic upgrade head`

**Step 4: Verify**

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'jobs' AND column_name = 'material_package_id';
```

**Step 5: Commit**

```bash
git add backend/alembic/versions/*_add_material_package_id_to_jobs.py
git commit -m "$(cat <<'EOF'
feat(db): add material_package_id FK to jobs table

Generation jobs reference their source MaterialPackage.
Nullable with SET NULL on delete for safe cleanup.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.8: Add MaterialPackage ORM Model

**Files:**
- Modify: `backend/app/models/database.py`
- Test: `backend/tests/test_models.py` (create or add to)

**Step 1: Write the failing test**

```python
# backend/tests/test_models.py
import pytest
from app.models.database import MaterialPackage
from app.models.enums import MaterialPackageStatus

def test_material_package_model_exists():
    """MaterialPackage model can be instantiated."""
    pkg = MaterialPackage(
        gcs_base_path="gs://bucket/materials/test-project-id/"
    )
    assert pkg.gcs_base_path == "gs://bucket/materials/test-project-id/"
    assert pkg.package_version == "1.0"
    assert pkg.status == MaterialPackageStatus.PENDING
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models.py::test_material_package_model_exists -v`
Expected: FAIL with import error

**Step 3: Write the implementation**

Add to `backend/app/models/database.py` after the imports section, add the import:
```python
from app.models.enums import MaterialPackageStatus
```

Add the model class (after Project, before Job):

```python
class MaterialPackage(TimestampMixin, Base):
    """
    Stores extraction results from PDF processing for reuse across templates.

    The MaterialPackage is created after step 10 (structure_data) completes.
    Generation jobs consume this package to produce template-specific content.
    """
    __tablename__ = "material_packages"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True
    )
    source_job_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True
    )
    gcs_base_path: Mapped[str] = mapped_column(String(500), nullable=False)
    package_version: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="1.0",
        server_default="1.0"
    )
    extraction_summary: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict
    )
    structured_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict
    )
    status: Mapped[MaterialPackageStatus] = mapped_column(
        SQLAlchemyEnum(
            MaterialPackageStatus,
            native_enum=False,
            length=50,
            values_callable=_enum_values
        ),
        nullable=False,
        default=MaterialPackageStatus.PENDING,
        server_default=MaterialPackageStatus.PENDING.value
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="material_packages",
        foreign_keys=[project_id]
    )
    source_job: Mapped[Optional["Job"]] = relationship(
        "Job",
        back_populates="material_package_created",
        foreign_keys=[source_job_id]
    )
    generation_runs: Mapped[list["GenerationRun"]] = relationship(
        "GenerationRun",
        back_populates="material_package",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_material_packages_project_id", "project_id"),
        Index("idx_material_packages_status", "status"),
        Index("idx_material_packages_source_job", "source_job_id"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s.value) for s in MaterialPackageStatus)})",
            name="check_material_package_status"
        ),
    )
```

Also add to Project model's relationships:
```python
material_packages: Mapped[list["MaterialPackage"]] = relationship(
    "MaterialPackage",
    back_populates="project",
    cascade="all, delete-orphan"
)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models.py::test_material_package_model_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/database.py backend/tests/test_models.py
git commit -m "$(cat <<'EOF'
feat: add MaterialPackage ORM model

Maps to material_packages table. Stores GCS path and cached
extraction data for multi-template generation reuse.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.9: Add GenerationRun ORM Model

**Files:**
- Modify: `backend/app/models/database.py`
- Test: `backend/tests/test_models.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_models.py
from app.models.database import GenerationRun
from app.models.enums import GenerationRunStatus, TemplateType

def test_generation_run_model_exists():
    """GenerationRun model can be instantiated."""
    run = GenerationRun(
        template_type=TemplateType.OPR
    )
    assert run.template_type == TemplateType.OPR
    assert run.status == GenerationRunStatus.PENDING
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models.py::test_generation_run_model_exists -v`
Expected: FAIL

**Step 3: Write the implementation**

Add import:
```python
from app.models.enums import GenerationRunStatus
```

Add model class:

```python
class GenerationRun(Base):
    """
    Tracks content generation for a specific template using a MaterialPackage.

    Each project can have one generation run per template type (enforced by
    unique constraint). Stores the generated content, sheet URL, and Drive folder.

    NOTE: The unique constraint on (project_id, template_type) means regeneration
    OVERWRITES the previous run's data. This is a deliberate MVP tradeoff:
    - Pro: Simple model, no versioning complexity
    - Con: No generation history per template

    If history is needed later, add a version column and change the unique
    constraint to (project_id, template_type, version).
    """
    __tablename__ = "generation_runs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    material_package_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("material_packages.id", ondelete="SET NULL"),
        nullable=True
    )
    template_type: Mapped[TemplateType] = mapped_column(
        SQLAlchemyEnum(
            TemplateType,
            native_enum=False,
            length=50,
            values_callable=_enum_values
        ),
        nullable=False
    )
    job_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True
    )
    generated_content: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict
    )
    sheet_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    drive_folder_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[GenerationRunStatus] = mapped_column(
        SQLAlchemyEnum(
            GenerationRunStatus,
            native_enum=False,
            length=50,
            values_callable=_enum_values
        ),
        nullable=False,
        default=GenerationRunStatus.PENDING,
        server_default=GenerationRunStatus.PENDING.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="generation_runs"
    )
    material_package: Mapped[Optional["MaterialPackage"]] = relationship(
        "MaterialPackage",
        back_populates="generation_runs"
    )
    job: Mapped[Optional["Job"]] = relationship(
        "Job",
        back_populates="generation_run"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "template_type", name="uq_generation_runs_project_template"),
        Index("idx_generation_runs_project_id", "project_id"),
        Index("idx_generation_runs_status", "status"),
        Index("idx_generation_runs_template_type", "template_type"),
    )
```

Add to Project model:
```python
generation_runs: Mapped[list["GenerationRun"]] = relationship(
    "GenerationRun",
    back_populates="project",
    cascade="all, delete-orphan"
)
```

**Step 4: Run test**

Run: `cd backend && pytest tests/test_models.py::test_generation_run_model_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/database.py backend/tests/test_models.py
git commit -m "$(cat <<'EOF'
feat: add GenerationRun ORM model

Tracks per-template content generation with unique constraint
on (project_id, template_type).

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.10: Update Job Model with job_type and material_package_id

**Files:**
- Modify: `backend/app/models/database.py`
- Test: `backend/tests/test_models.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_models.py
from app.models.database import Job
from app.models.enums import JobType

def test_job_model_has_job_type():
    """Job model has job_type field with default FULL."""
    job = Job(
        user_id=uuid.uuid4(),
        template_type=TemplateType.OPR
    )
    assert job.job_type == JobType.FULL

def test_job_model_accepts_extraction_type():
    """Job model accepts EXTRACTION job type."""
    job = Job(
        user_id=uuid.uuid4(),
        template_type=TemplateType.OPR,
        job_type=JobType.EXTRACTION
    )
    assert job.job_type == JobType.EXTRACTION
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models.py::test_job_model_has_job_type -v`

**Step 3: Update Job model**

Add to Job class in `database.py`:

```python
from app.models.enums import JobType

# In Job class, add these fields:
job_type: Mapped[JobType] = mapped_column(
    SQLAlchemyEnum(
        JobType,
        native_enum=False,
        length=50,
        values_callable=_enum_values
    ),
    nullable=False,
    default=JobType.FULL,
    server_default=JobType.FULL.value
)
material_package_id: Mapped[Optional[UUID]] = mapped_column(
    PG_UUID(as_uuid=True),
    ForeignKey("material_packages.id", ondelete="SET NULL"),
    nullable=True
)

# Add relationships:
material_package: Mapped[Optional["MaterialPackage"]] = relationship(
    "MaterialPackage",
    back_populates="consuming_jobs",
    foreign_keys=[material_package_id]
)
material_package_created: Mapped[Optional["MaterialPackage"]] = relationship(
    "MaterialPackage",
    back_populates="source_job",
    foreign_keys="[MaterialPackage.source_job_id]"
)
generation_run: Mapped[Optional["GenerationRun"]] = relationship(
    "GenerationRun",
    back_populates="job"
)
```

Add to MaterialPackage:
```python
consuming_jobs: Mapped[list["Job"]] = relationship(
    "Job",
    back_populates="material_package",
    foreign_keys="[Job.material_package_id]"
)
```

**Step 4: Run tests**

Run: `cd backend && pytest tests/test_models.py -v -k job`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/database.py backend/tests/test_models.py
git commit -m "$(cat <<'EOF'
feat: add job_type and material_package_id to Job model

Defaults to FULL for backward compatibility. Generation jobs
reference their source MaterialPackage via FK.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.11: Create MaterialPackageRepository

**Files:**
- Create: `backend/app/repositories/material_package_repository.py`
- Test: `backend/tests/test_material_package_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_material_package_repository.py
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from app.repositories.material_package_repository import MaterialPackageRepository
from app.models.database import MaterialPackage
from app.models.enums import MaterialPackageStatus

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def repo(mock_db):
    return MaterialPackageRepository(mock_db)

@pytest.mark.asyncio
async def test_create_material_package(repo, mock_db):
    """Repository creates MaterialPackage record."""
    project_id = uuid.uuid4()
    job_id = uuid.uuid4()
    gcs_path = "gs://bucket/materials/test/"

    result = await repo.create(
        project_id=project_id,
        source_job_id=job_id,
        gcs_base_path=gcs_path,
        extraction_summary={"total_images": 10}
    )

    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_material_package_repository.py -v`

**Step 3: Write the implementation**

```python
# backend/app/repositories/material_package_repository.py
"""
Repository for MaterialPackage database operations.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import MaterialPackage
from app.models.enums import MaterialPackageStatus

logger = logging.getLogger(__name__)


class MaterialPackageRepository:
    """Data access layer for MaterialPackage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        project_id: Optional[UUID],
        source_job_id: Optional[UUID],
        gcs_base_path: str,
        extraction_summary: Optional[dict] = None,
        structured_data: Optional[dict] = None,
        expires_in_days: int = 30
    ) -> MaterialPackage:
        """Create a new MaterialPackage record."""
        package = MaterialPackage(
            project_id=project_id,
            source_job_id=source_job_id,
            gcs_base_path=gcs_base_path,
            extraction_summary=extraction_summary or {},
            structured_data=structured_data or {},
            status=MaterialPackageStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )
        self.db.add(package)
        await self.db.flush()
        await self.db.refresh(package)
        return package

    async def get_by_id(self, package_id: UUID) -> Optional[MaterialPackage]:
        """Get MaterialPackage by ID."""
        result = await self.db.execute(
            select(MaterialPackage).where(MaterialPackage.id == package_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: UUID) -> Optional[MaterialPackage]:
        """Get the latest MaterialPackage for a project."""
        result = await self.db.execute(
            select(MaterialPackage)
            .where(MaterialPackage.project_id == project_id)
            .where(MaterialPackage.status == MaterialPackageStatus.READY)
            .order_by(MaterialPackage.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        package_id: UUID,
        status: MaterialPackageStatus,
        structured_data: Optional[dict] = None
    ) -> bool:
        """Update package status and optionally structured data."""
        values = {"status": status, "updated_at": datetime.utcnow()}
        if structured_data is not None:
            values["structured_data"] = structured_data

        result = await self.db.execute(
            update(MaterialPackage)
            .where(MaterialPackage.id == package_id)
            .values(**values)
        )
        return result.rowcount > 0

    async def mark_ready(
        self,
        package_id: UUID,
        extraction_summary: dict,
        structured_data: dict
    ) -> bool:
        """Mark package as ready with final data."""
        result = await self.db.execute(
            update(MaterialPackage)
            .where(MaterialPackage.id == package_id)
            .values(
                status=MaterialPackageStatus.READY,
                extraction_summary=extraction_summary,
                structured_data=structured_data,
                updated_at=datetime.utcnow()
            )
        )
        return result.rowcount > 0
```

**Step 4: Run test**

Run: `cd backend && pytest tests/test_material_package_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/repositories/material_package_repository.py backend/tests/test_material_package_repository.py
git commit -m "$(cat <<'EOF'
feat: add MaterialPackageRepository

CRUD operations for material_packages table with status transitions.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.12: Create GenerationRunRepository

**Files:**
- Create: `backend/app/repositories/generation_run_repository.py`
- Test: `backend/tests/test_generation_run_repository.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_generation_run_repository.py
import pytest
import uuid
from unittest.mock import AsyncMock
from app.repositories.generation_run_repository import GenerationRunRepository
from app.models.enums import TemplateType

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def repo(mock_db):
    return GenerationRunRepository(mock_db)

@pytest.mark.asyncio
async def test_create_generation_run(repo, mock_db):
    """Repository creates GenerationRun record."""
    project_id = uuid.uuid4()

    result = await repo.create(
        project_id=project_id,
        template_type=TemplateType.OPR
    )

    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()
```

**Step 2: Run test to verify it fails**

**Step 3: Write the implementation**

```python
# backend/app/repositories/generation_run_repository.py
"""
Repository for GenerationRun database operations.
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import GenerationRun
from app.models.enums import GenerationRunStatus, TemplateType

logger = logging.getLogger(__name__)


class GenerationRunRepository:
    """Data access layer for GenerationRun."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        project_id: UUID,
        template_type: TemplateType,
        material_package_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None
    ) -> GenerationRun:
        """Create a new GenerationRun record."""
        run = GenerationRun(
            project_id=project_id,
            material_package_id=material_package_id,
            template_type=template_type,
            job_id=job_id,
            status=GenerationRunStatus.PENDING
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def get_by_id(self, run_id: UUID) -> Optional[GenerationRun]:
        """Get GenerationRun by ID."""
        result = await self.db.execute(
            select(GenerationRun).where(GenerationRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project_and_template(
        self,
        project_id: UUID,
        template_type: TemplateType
    ) -> Optional[GenerationRun]:
        """Get GenerationRun for specific project and template."""
        result = await self.db.execute(
            select(GenerationRun)
            .where(GenerationRun.project_id == project_id)
            .where(GenerationRun.template_type == template_type)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: UUID) -> list[GenerationRun]:
        """List all GenerationRuns for a project."""
        result = await self.db.execute(
            select(GenerationRun)
            .where(GenerationRun.project_id == project_id)
            .order_by(GenerationRun.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_completed(
        self,
        run_id: UUID,
        generated_content: dict,
        sheet_url: Optional[str] = None,
        drive_folder_url: Optional[str] = None
    ) -> bool:
        """Mark run as completed with results."""
        result = await self.db.execute(
            update(GenerationRun)
            .where(GenerationRun.id == run_id)
            .values(
                status=GenerationRunStatus.COMPLETED,
                generated_content=generated_content,
                sheet_url=sheet_url,
                drive_folder_url=drive_folder_url,
                completed_at=datetime.utcnow()
            )
        )
        return result.rowcount > 0

    async def mark_failed(self, run_id: UUID) -> bool:
        """Mark run as failed."""
        result = await self.db.execute(
            update(GenerationRun)
            .where(GenerationRun.id == run_id)
            .values(status=GenerationRunStatus.FAILED)
        )
        return result.rowcount > 0
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/repositories/generation_run_repository.py backend/tests/test_generation_run_repository.py
git commit -m "$(cat <<'EOF'
feat: add GenerationRunRepository

CRUD operations for generation_runs table with status management.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase A Verification Checkpoint

Before proceeding to Phase B, verify:

1. [ ] All 4 migrations applied successfully: `alembic upgrade head`
2. [ ] Tables exist: `material_packages`, `generation_runs`
3. [ ] Jobs table has: `job_type` (default 'full'), `material_package_id` (nullable)
4. [ ] ORM models load without error: `python -c "from app.models.database import MaterialPackage, GenerationRun, Job"`
5. [ ] Existing `/upload/pdf` still creates jobs (with `job_type=full` default)
6. [ ] All tests pass: `pytest tests/ -v`

---

## Phase B: Generation Job Separation

### Task B.1: Define Step Configurations

**Files:**
- Modify: `backend/app/services/job_manager.py`
- Test: `backend/tests/test_job_manager.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_job_manager.py
from app.services.job_manager import EXTRACTION_STEPS, GENERATION_STEPS, FULL_STEPS

def test_extraction_steps_defined():
    """Extraction steps cover steps 1-10 plus materialization."""
    step_ids = [s["id"] for s in EXTRACTION_STEPS]
    assert "upload" in step_ids
    assert "extract_images" in step_ids
    assert "structure_data" in step_ids
    assert "materialize" in step_ids
    assert "generate_content" not in step_ids  # Not in extraction
    assert len(step_ids) == 11  # Steps 1-10 + materialize

def test_generation_steps_defined():
    """Generation steps cover steps 11-14."""
    step_ids = [s["id"] for s in GENERATION_STEPS]
    assert "load_package" in step_ids
    assert "generate_content" in step_ids
    assert "populate_sheet" in step_ids
    assert "upload_cloud" in step_ids
    assert "finalize_generation" in step_ids
    assert "extract_images" not in step_ids  # Not in generation
    assert len(step_ids) == 5
```

**Step 2: Run test to verify it fails**

**Step 3: Add step configurations to job_manager.py**

Near the top of the file, after imports:

```python
# Step configurations for different job types
EXTRACTION_STEPS = [
    {"id": "upload", "label": "PDF Upload & Validation", "progress": 3},
    {"id": "extract_images", "label": "Image Extraction", "progress": 10},
    {"id": "classify_images", "label": "Image Classification", "progress": 20},
    {"id": "detect_watermarks", "label": "Watermark Detection", "progress": 27},
    {"id": "remove_watermarks", "label": "Watermark Removal", "progress": 34},
    {"id": "extract_floor_plans", "label": "Floor Plan Extraction", "progress": 40},
    {"id": "optimize_images", "label": "Image Optimization", "progress": 47},
    {"id": "package_assets", "label": "Asset Packaging", "progress": 53},
    {"id": "extract_data", "label": "Data Extraction", "progress": 60},
    {"id": "structure_data", "label": "Data Structuring", "progress": 90},
    {"id": "materialize", "label": "Package Materialization", "progress": 100},
]

GENERATION_STEPS = [
    {"id": "load_package", "label": "Load Material Package", "progress": 10},
    {"id": "generate_content", "label": "Content Generation", "progress": 50},
    {"id": "populate_sheet", "label": "Sheet Population", "progress": 75},
    {"id": "upload_cloud", "label": "Cloud Upload", "progress": 95},
    {"id": "finalize_generation", "label": "Finalization", "progress": 100},
]

# Legacy full pipeline (steps 1-14)
FULL_STEPS = [
    {"id": "upload", "label": "PDF Upload & Validation", "progress": 3},
    {"id": "extract_images", "label": "Image Extraction", "progress": 10},
    {"id": "classify_images", "label": "Image Classification", "progress": 20},
    {"id": "detect_watermarks", "label": "Watermark Detection", "progress": 27},
    {"id": "remove_watermarks", "label": "Watermark Removal", "progress": 34},
    {"id": "extract_floor_plans", "label": "Floor Plan Extraction", "progress": 40},
    {"id": "optimize_images", "label": "Image Optimization", "progress": 47},
    {"id": "package_assets", "label": "Asset Packaging", "progress": 53},
    {"id": "extract_data", "label": "Data Extraction", "progress": 60},
    {"id": "structure_data", "label": "Data Structuring", "progress": 68},
    {"id": "generate_content", "label": "Content Generation", "progress": 78},
    {"id": "populate_sheet", "label": "Sheet Population", "progress": 88},
    {"id": "upload_cloud", "label": "Cloud Upload", "progress": 95},
    {"id": "finalize", "label": "Finalization", "progress": 100},
]


def get_steps_for_job_type(job_type: JobType) -> list[dict]:
    """Return step configuration for the given job type."""
    if job_type == JobType.EXTRACTION:
        return EXTRACTION_STEPS
    elif job_type == JobType.GENERATION:
        return GENERATION_STEPS
    else:
        return FULL_STEPS
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/services/job_manager.py backend/tests/test_job_manager.py
git commit -m "$(cat <<'EOF'
feat: define step configurations for job types

EXTRACTION_STEPS (1-10 + materialize), GENERATION_STEPS (11-14),
FULL_STEPS (legacy 1-14). get_steps_for_job_type() selector.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.2: Create MaterialPackageService

**Files:**
- Create: `backend/app/services/material_package_service.py`
- Test: `backend/tests/test_material_package_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_material_package_service.py
import pytest
import uuid
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.material_package_service import MaterialPackageService

@pytest.fixture
def mock_storage():
    return AsyncMock()

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def service(mock_storage, mock_repo):
    return MaterialPackageService(mock_storage, mock_repo)

@pytest.mark.asyncio
async def test_persist_to_gcs_creates_files(service, mock_storage):
    """Service persists extraction results to GCS."""
    project_id = uuid.uuid4()
    pipeline_ctx = {
        "structured_data": {"project_name": "Test Project"},
        "extraction": {"text_by_page": {1: "Page 1 text"}},
        "floor_plans": {"data": []},
        "manifest": {"entries": []},
        "zip_bytes": b"fake zip data"
    }

    gcs_path = await service.persist_to_gcs(project_id, pipeline_ctx)

    assert f"materials/{project_id}" in gcs_path
    # Should upload structured_data.json, extracted_text.json, etc.
    assert mock_storage.upload_file.call_count >= 4
```

**Step 2: Run test to verify it fails**

**Step 3: Write the implementation**

```python
# backend/app/services/material_package_service.py
"""
Service for managing MaterialPackage persistence to GCS.
"""
import json
import logging
from datetime import datetime
from io import BytesIO
from typing import Any, Optional
from uuid import UUID
import zipfile

from app.models.database import MaterialPackage
from app.models.enums import MaterialPackageStatus
from app.repositories.material_package_repository import MaterialPackageRepository
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class MaterialPackageService:
    """
    Manages MaterialPackage lifecycle: creation, GCS persistence, and loading.
    """

    def __init__(
        self,
        storage_service: StorageService,
        repo: MaterialPackageRepository
    ):
        self.storage = storage_service
        self.repo = repo

    async def persist_to_gcs(
        self,
        project_id: UUID,
        pipeline_ctx: dict[str, Any],
        source_job_id: Optional[UUID] = None
    ) -> str:
        """
        Persist extraction results from pipeline context to GCS.

        Creates:
        - metadata.json (package manifest)
        - structured_data.json (extracted project data)
        - extracted_text.json (per-page text)
        - floor_plan_data.json (floor plan information)
        - image_manifest.json (classified images)
        - images/{category}/*.webp (optimized images extracted from ZIP)

        The images are extracted from the ZIP bytes in pipeline_ctx["zip_bytes"]
        so generation jobs can access them without reprocessing.

        Returns: GCS base path (gs://bucket/materials/{project_id}/)
        """
        base_path = f"materials/{project_id}"

        # 1. Structured data from step 10
        structured_data = pipeline_ctx.get("structured_data", {})
        await self._upload_json(
            f"{base_path}/structured_data.json",
            structured_data
        )

        # 2. Extracted text from step 2
        extraction = pipeline_ctx.get("extraction", {})
        text_by_page = extraction.get("text_by_page", {})
        await self._upload_json(
            f"{base_path}/extracted_text.json",
            {"pages": text_by_page}
        )

        # 3. Floor plan data from step 6
        floor_plans = pipeline_ctx.get("floor_plans", {})
        await self._upload_json(
            f"{base_path}/floor_plan_data.json",
            floor_plans
        )

        # 4. Image manifest from step 8
        manifest = pipeline_ctx.get("manifest", {})
        await self._upload_json(
            f"{base_path}/image_manifest.json",
            manifest
        )

        # 5. Extract and upload images from ZIP
        # This is critical - generation jobs need the actual image files
        zip_bytes = pipeline_ctx.get("zip_bytes")
        if zip_bytes:
            await self._extract_and_upload_images(base_path, zip_bytes, manifest)
        else:
            logger.warning(f"No zip_bytes in pipeline context for {project_id}")

        # 6. Package metadata (includes image paths for generation to reference)
        metadata = {
            "package_version": "1.0",
            "project_id": str(project_id),
            "source_job_id": str(source_job_id) if source_job_id else None,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "extraction_summary": self._build_extraction_summary(pipeline_ctx),
            "images_base_path": f"{base_path}/images/"
        }
        await self._upload_json(f"{base_path}/metadata.json", metadata)

        logger.info(f"Persisted MaterialPackage to {base_path}")
        return f"gs://{self.storage.bucket_name}/{base_path}/"

    async def _extract_and_upload_images(
        self,
        base_path: str,
        zip_bytes: bytes,
        manifest: dict
    ) -> int:
        """
        Extract images from ZIP and upload to GCS for generation reuse.

        Images are stored at: {base_path}/images/original/{category}/
                         and: {base_path}/images/optimized/{category}/

        Returns count of images uploaded.
        """
        count = 0
        with zipfile.ZipFile(BytesIO(zip_bytes), 'r') as zf:
            for zip_path in zf.namelist():
                # Only upload image files (skip JSON, etc.)
                if not zip_path.endswith(('.webp', '.jpg', '.png')):
                    continue

                # Preserve folder structure: original/interiors/img.webp
                gcs_path = f"{base_path}/images/{zip_path}"
                image_data = zf.read(zip_path)

                # Determine content type
                content_type = "image/webp"
                if zip_path.endswith('.jpg'):
                    content_type = "image/jpeg"
                elif zip_path.endswith('.png'):
                    content_type = "image/png"

                await self.storage.upload_file(
                    source_file=image_data,
                    destination_blob_path=gcs_path,
                    content_type=content_type
                )
                count += 1

        logger.info(f"Uploaded {count} images to {base_path}/images/")
        return count

    async def _upload_json(self, path: str, data: dict) -> str:
        """Upload JSON data to GCS."""
        json_bytes = json.dumps(data, indent=2, default=str).encode("utf-8")
        return await self.storage.upload_file(
            source_file=json_bytes,
            destination_blob_path=path,
            content_type="application/json"
        )

    def _build_extraction_summary(self, pipeline_ctx: dict) -> dict:
        """Build extraction summary from pipeline context."""
        extraction = pipeline_ctx.get("extraction", {})
        classification = pipeline_ctx.get("classification", {})

        return {
            "total_images": classification.get("total_images", 0),
            "classified_images": classification.get("by_category", {}),
            "total_pages": extraction.get("total_pages", 0),
            "text_extraction_method": extraction.get("method", "unknown"),
            "ocr_used": extraction.get("ocr_used", False)
        }

    async def load_from_gcs(self, gcs_base_path: str) -> dict[str, Any]:
        """
        Load MaterialPackage data from GCS.

        Returns dict with:
        - structured_data
        - extracted_text
        - floor_plan_data
        - image_manifest
        - metadata
        """
        result = {}

        files = [
            ("structured_data", "structured_data.json"),
            ("extracted_text", "extracted_text.json"),
            ("floor_plan_data", "floor_plan_data.json"),
            ("image_manifest", "image_manifest.json"),
            ("metadata", "metadata.json"),
        ]

        for key, filename in files:
            path = gcs_base_path.rstrip("/") + "/" + filename
            # Remove gs://bucket/ prefix if present
            if path.startswith("gs://"):
                path = "/".join(path.split("/")[3:])

            data = await self.storage.download_file(path)
            if data:
                result[key] = json.loads(data.decode("utf-8"))
            else:
                result[key] = {}
                logger.warning(f"Failed to load {filename} from {gcs_base_path}")

        return result

    async def create_package_record(
        self,
        project_id: UUID,
        source_job_id: UUID,
        gcs_base_path: str,
        extraction_summary: dict,
        structured_data: dict
    ) -> MaterialPackage:
        """Create MaterialPackage DB record after GCS persistence."""
        package = await self.repo.create(
            project_id=project_id,
            source_job_id=source_job_id,
            gcs_base_path=gcs_base_path,
            extraction_summary=extraction_summary,
            structured_data=structured_data
        )

        # Mark as ready immediately (persistence already succeeded)
        await self.repo.update_status(package.id, MaterialPackageStatus.READY)

        return package
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/services/material_package_service.py backend/tests/test_material_package_service.py
git commit -m "$(cat <<'EOF'
feat: add MaterialPackageService

Handles GCS persistence and loading of extraction results.
Creates structured_data.json, extracted_text.json, and uploads
images extracted from ZIP for generation job reuse.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.2b: Add _create_project_from_extraction Helper

**Files:**
- Modify: `backend/app/services/job_manager.py`
- Test: `backend/tests/test_job_manager.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_create_project_from_extraction(job_manager, mock_db):
    """Creates Project record from pipeline context structured_data."""
    job_id = uuid.uuid4()

    job_manager._pipeline_ctx[job_id] = {
        "structured_data": {
            "project_name": "Azure Residences",
            "developer": "Nakheel",
            "location": {"emirate": "Dubai", "community": "Palm Jumeirah"},
            "prices": {"starting_from": 2500000, "currency": "AED"},
        }
    }

    mock_job = MagicMock()
    mock_job.user_id = uuid.uuid4()
    mock_job.template_type = TemplateType.OPR
    job_manager._get_job = AsyncMock(return_value=mock_job)

    project = await job_manager._create_project_from_extraction(job_id)

    assert project.name == "Azure Residences"
    assert project.developer == "Nakheel"
    assert project.emirate == "Dubai"
```

**Step 2: Run test to verify it fails**

**Step 3: Add the helper method**

This extracts the project creation logic from the existing `_step_finalize` method
(see `backend/app/services/job_manager.py:1300-1406`):

```python
async def _create_project_from_extraction(self, job_id: UUID) -> Project:
    """
    Create Project record from extraction pipeline context.

    Extracts project metadata from structured_data and creates a Project
    in DRAFT status. Used by extraction pipeline before materialization.

    Note: This is similar to the project creation in _step_finalize but
    without the content generation results. The project is created early
    so it can be linked to the MaterialPackage.
    """
    ctx = self._pipeline_ctx.get(job_id, {})
    job = await self._get_job(job_id)
    structured_data = ctx.get("structured_data", {})

    # Extract fields from structured_data
    project_name = structured_data.get("project_name", "Untitled Project")
    developer = structured_data.get("developer")
    location_data = structured_data.get("location", {})
    price_data = structured_data.get("prices", {})

    # Create project record
    project = Project(
        name=project_name,
        developer=developer,
        location=location_data.get("community"),
        emirate=location_data.get("emirate"),
        starting_price=price_data.get("starting_from"),
        workflow_status=WorkflowStatus.DRAFT,
        template_type=job.template_type,
        created_by=job.user_id,
        processing_job_id=job_id,
        # Store structured data for reference
        custom_fields={"extraction_data": structured_data}
    )

    self._db.add(project)
    await self._db.flush()
    await self._db.refresh(project)

    logger.info(f"Created project {project.id} from extraction job {job_id}")
    return project
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/services/job_manager.py backend/tests/test_job_manager.py
git commit -m "$(cat <<'EOF'
feat: add _create_project_from_extraction helper

Extracts project creation logic for use in extraction pipeline.
Creates Project in DRAFT status from structured_data.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.3: Add _step_materialize_package to JobManager

**Files:**
- Modify: `backend/app/services/job_manager.py`
- Test: `backend/tests/test_job_manager.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_job_manager.py
@pytest.mark.asyncio
async def test_step_materialize_package_creates_package(job_manager, mock_db):
    """Materialize step creates MaterialPackage from pipeline context."""
    job_id = uuid.uuid4()
    project_id = uuid.uuid4()

    # Setup pipeline context
    job_manager._pipeline_ctx[job_id] = {
        "structured_data": {"project_name": "Test"},
        "extraction": {},
        "floor_plans": {},
        "manifest": {},
    }

    # Mock the service
    job_manager._material_package_service = AsyncMock()
    job_manager._material_package_service.persist_to_gcs.return_value = "gs://bucket/materials/test/"
    job_manager._material_package_service.create_package_record.return_value = MagicMock(id=uuid.uuid4())

    result = await job_manager._step_materialize_package(job_id, project_id)

    assert "material_package_id" in result
    assert "gcs_path" in result
```

**Step 2: Run test to verify it fails**

**Step 3: Add method to JobManager**

```python
async def _step_materialize_package(self, job_id: UUID, project_id: UUID) -> dict:
    """
    Create MaterialPackage from pipeline context and persist to GCS.

    This step runs after structure_data (step 10) for EXTRACTION jobs,
    or after structure_data for FULL jobs that want to enable future
    generation runs.
    """
    ctx = self._pipeline_ctx.get(job_id, {})
    job = await self._get_job(job_id)

    # Persist to GCS
    gcs_path = await self._material_package_service.persist_to_gcs(
        project_id=project_id,
        pipeline_ctx=ctx,
        source_job_id=job_id
    )

    # Build extraction summary
    extraction_summary = {
        "total_images": ctx.get("classification", {}).get("total_images", 0),
        "classified_images": ctx.get("classification", {}).get("by_category", {}),
        "total_pages": ctx.get("extraction", {}).get("total_pages", 0),
    }

    # Create DB record
    package = await self._material_package_service.create_package_record(
        project_id=project_id,
        source_job_id=job_id,
        gcs_base_path=gcs_path,
        extraction_summary=extraction_summary,
        structured_data=ctx.get("structured_data", {})
    )

    # Store in context for potential generation dispatch
    ctx["material_package_id"] = package.id
    ctx["material_package_gcs_path"] = gcs_path

    logger.info(f"Materialized package {package.id} at {gcs_path}")

    return {
        "material_package_id": str(package.id),
        "gcs_path": gcs_path
    }
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/services/job_manager.py backend/tests/test_job_manager.py
git commit -m "$(cat <<'EOF'
feat: add _step_materialize_package to JobManager

Persists extraction results to GCS and creates MaterialPackage DB record.
Called after structure_data for extraction jobs.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.4: Add _step_load_material_package to JobManager

**Files:**
- Modify: `backend/app/services/job_manager.py`
- Test: `backend/tests/test_job_manager.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_step_load_material_package_populates_context(job_manager):
    """Load package step populates pipeline context from GCS."""
    job_id = uuid.uuid4()
    package_id = uuid.uuid4()

    # Mock job with material_package_id
    mock_job = MagicMock()
    mock_job.material_package_id = package_id
    mock_job.material_package = MagicMock()
    mock_job.material_package.gcs_base_path = "gs://bucket/materials/test/"

    job_manager._get_job = AsyncMock(return_value=mock_job)
    job_manager._material_package_service = AsyncMock()
    job_manager._material_package_service.load_from_gcs.return_value = {
        "structured_data": {"project_name": "Loaded Project"},
        "extracted_text": {"pages": {}},
    }

    job_manager._pipeline_ctx[job_id] = {}

    result = await job_manager._step_load_material_package(job_id)

    ctx = job_manager._pipeline_ctx[job_id]
    assert ctx["structured_data"]["project_name"] == "Loaded Project"
```

**Step 2: Run test to verify it fails**

**Step 3: Add method to JobManager**

```python
async def _step_load_material_package(self, job_id: UUID) -> dict:
    """
    Load MaterialPackage from GCS into pipeline context.

    This is the first step for GENERATION jobs. Populates the context
    with structured_data, extracted_text, etc. from the source package.
    """
    job = await self._get_job(job_id)

    if not job.material_package_id:
        raise ValueError(f"Generation job {job_id} has no material_package_id")

    # Get package record
    package = await self._material_package_repo.get_by_id(job.material_package_id)
    if not package:
        raise ValueError(f"MaterialPackage {job.material_package_id} not found")

    if package.status != MaterialPackageStatus.READY:
        raise ValueError(f"MaterialPackage {package.id} is not ready (status={package.status})")

    # Load from GCS
    package_data = await self._material_package_service.load_from_gcs(
        package.gcs_base_path
    )

    # Populate pipeline context
    ctx = self._pipeline_ctx.setdefault(job_id, {})
    ctx["structured_data"] = package_data.get("structured_data", {})
    ctx["extraction"] = {"text_by_page": package_data.get("extracted_text", {}).get("pages", {})}
    ctx["floor_plans"] = package_data.get("floor_plan_data", {})
    ctx["manifest"] = package_data.get("image_manifest", {})
    ctx["material_package_id"] = package.id
    ctx["material_package_gcs_path"] = package.gcs_base_path

    logger.info(f"Loaded MaterialPackage {package.id} into context for job {job_id}")

    return {
        "material_package_id": str(package.id),
        "structured_data_keys": list(ctx["structured_data"].keys())
    }
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/services/job_manager.py backend/tests/test_job_manager.py
git commit -m "$(cat <<'EOF'
feat: add _step_load_material_package to JobManager

First step for GENERATION jobs - loads extraction results from
GCS into pipeline context.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.5: Update JobRepository.create_job for job_type

**Files:**
- Modify: `backend/app/repositories/job_repository.py`
- Test: `backend/tests/test_job_repository.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_create_job_with_job_type(repo, mock_db):
    """Repository creates job with specified job_type."""
    from app.models.enums import JobType

    job = await repo.create_job(
        user_id=uuid.uuid4(),
        template_type="opr",
        job_type=JobType.EXTRACTION
    )

    mock_db.add.assert_called_once()
    added_job = mock_db.add.call_args[0][0]
    assert added_job.job_type == JobType.EXTRACTION
```

**Step 2: Run test to verify it fails**

**Step 3: Update create_job method**

```python
async def create_job(
    self,
    user_id: UUID,
    template_type: str,
    job_type: JobType = JobType.FULL,  # NEW
    template_id: Optional[UUID] = None,
    material_package_id: Optional[UUID] = None,  # NEW
    processing_config: Optional[dict] = None
) -> Job:
    """Create a new job with the specified type."""
    # Validate template_type
    try:
        template_type_enum = TemplateType(template_type)
    except ValueError:
        raise ValueError(f"Invalid template_type: {template_type}")

    job = Job(
        user_id=user_id,
        template_type=template_type_enum,
        job_type=job_type,  # NEW
        template_id=template_id,
        material_package_id=material_package_id,  # NEW
        status=JobStatus.PENDING,
        processing_config=processing_config or {}
    )

    self.db.add(job)
    await self.db.flush()
    await self.db.refresh(job)
    return job
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/repositories/job_repository.py backend/tests/test_job_repository.py
git commit -m "$(cat <<'EOF'
feat: add job_type and material_package_id to create_job

Defaults to FULL for backward compatibility. Generation jobs
require material_package_id.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.6: Create execute_extraction_pipeline

**Files:**
- Modify: `backend/app/services/job_manager.py`
- Test: `backend/tests/test_job_manager.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_execute_extraction_pipeline_runs_steps_1_to_10(job_manager):
    """Extraction pipeline runs only extraction steps plus materialize."""
    job_id = uuid.uuid4()

    # Mock all step methods
    for step in ["upload", "extract_images", "classify_images", "detect_watermarks",
                 "remove_watermarks", "extract_floor_plans", "optimize_images",
                 "package_assets", "extract_data", "structure_data", "materialize_package"]:
        setattr(job_manager, f"_step_{step}", AsyncMock(return_value={}))

    # Should NOT have these steps
    job_manager._step_generate_content = AsyncMock()
    job_manager._step_populate_sheet = AsyncMock()

    # Mock job with template_ids
    mock_job = MagicMock()
    mock_job.processing_config = {"template_ids": ["opr", "mpp"]}
    mock_job.user_id = uuid.uuid4()
    job_manager._get_job = AsyncMock(return_value=mock_job)
    job_manager._dispatch_generation_jobs = AsyncMock()

    await job_manager.execute_extraction_pipeline(job_id, "gs://bucket/test.pdf")

    # Verify extraction steps called
    job_manager._step_upload.assert_called_once()
    job_manager._step_extract_images.assert_called_once()
    job_manager._step_materialize_package.assert_called_once()

    # Verify generation steps NOT called
    job_manager._step_generate_content.assert_not_called()
    job_manager._step_populate_sheet.assert_not_called()

    # Verify generation jobs dispatched for requested templates
    job_manager._dispatch_generation_jobs.assert_called_once()

@pytest.mark.asyncio
async def test_execute_extraction_pipeline_auto_dispatches_generation(job_manager):
    """Extraction pipeline auto-dispatches generation jobs for template_ids."""
    job_id = uuid.uuid4()
    project_id = uuid.uuid4()
    package_id = uuid.uuid4()

    # Mock pipeline context after materialize
    job_manager._pipeline_ctx[job_id] = {
        "material_package_id": package_id,
        "structured_data": {"project_name": "Test"}
    }

    mock_job = MagicMock()
    mock_job.processing_config = {"template_ids": ["opr", "mpp", "aggregators"]}
    mock_job.user_id = uuid.uuid4()
    job_manager._get_job = AsyncMock(return_value=mock_job)

    # Track dispatched generation jobs
    dispatched = []
    async def mock_dispatch(user_id, project_id, template_type, material_package_id):
        dispatched.append(template_type)
        return MagicMock(id=uuid.uuid4()), "task-name"

    job_manager._create_and_dispatch_generation_job = mock_dispatch

    await job_manager._dispatch_generation_jobs(job_id, project_id, package_id)

    assert len(dispatched) == 3
    assert "opr" in dispatched
    assert "mpp" in dispatched
    assert "aggregators" in dispatched
```

**Step 2: Run test to verify it fails**

**Step 3: Add execute_extraction_pipeline method**

Note: `_execute_step` is an existing helper in job_manager.py (lines ~500-550) that:
- Updates job.current_step and progress
- Marks JobStep as IN_PROGRESS
- Calls the step function
- Handles errors and marks step as FAILED if needed
- Marks step as COMPLETED on success

```python
async def execute_extraction_pipeline(
    self,
    job_id: UUID,
    pdf_path: str
) -> MaterialPackage:
    """
    Execute extraction-only pipeline (steps 1-10 + materialize).

    This creates a MaterialPackage that can be consumed by multiple
    generation jobs for different templates.

    After completion, auto-dispatches generation jobs for any template_ids
    specified in job.processing_config["template_ids"].

    Returns the created MaterialPackage.
    """
    try:
        # Initialize pipeline context
        self._pipeline_ctx[job_id] = {}

        # Step 1: Upload validation
        await self._execute_step(job_id, "upload", self._step_upload, pdf_path)

        # Step 2: Extract images and text
        await self._execute_step(job_id, "extract_images", self._step_extract_images)

        # Step 3: Classify images
        await self._execute_step(job_id, "classify_images", self._step_classify_images)

        # Step 4: Detect watermarks
        await self._execute_step(job_id, "detect_watermarks", self._step_detect_watermarks)

        # Step 5: Remove watermarks
        await self._execute_step(job_id, "remove_watermarks", self._step_remove_watermarks)

        # Step 6: Extract floor plans
        await self._execute_step(job_id, "extract_floor_plans", self._step_extract_floor_plans)

        # Step 7: Optimize images
        await self._execute_step(job_id, "optimize_images", self._step_optimize_images)

        # Step 8: Package assets (also uploads images to GCS for generation reuse)
        await self._execute_step(job_id, "package_assets", self._step_package_assets)

        # Step 9: Extract data
        await self._execute_step(job_id, "extract_data", self._step_extract_data)

        # Step 10: Structure data
        await self._execute_step(job_id, "structure_data", self._step_structure_data)

        # Create project from structured data
        job = await self._get_job(job_id)
        project = await self._create_project_from_extraction(job_id)
        project_id = project.id

        # Step 11 (extraction): Materialize package to GCS
        result = await self._execute_step(
            job_id, "materialize",
            lambda jid: self._step_materialize_package(jid, project_id)
        )

        # Mark extraction job as completed
        await self._complete_job(job_id, result)

        # Auto-dispatch generation jobs for requested templates
        package_id = self._pipeline_ctx[job_id].get("material_package_id")
        await self._dispatch_generation_jobs(job_id, project_id, package_id)

        # Return the MaterialPackage
        return await self._material_package_repo.get_by_id(package_id)

    finally:
        # Always cleanup pipeline context
        self._pipeline_ctx.pop(job_id, None)


async def _dispatch_generation_jobs(
    self,
    extraction_job_id: UUID,
    project_id: UUID,
    material_package_id: UUID
) -> list[tuple]:
    """
    Auto-dispatch generation jobs for templates specified in extraction job config.

    Called at the end of execute_extraction_pipeline. Creates one generation
    job per template_id in processing_config["template_ids"].

    Returns list of (job, task_name) tuples.
    """
    job = await self._get_job(extraction_job_id)
    template_ids = job.processing_config.get("template_ids", [])

    if not template_ids:
        logger.info(f"No template_ids in extraction job {extraction_job_id}, skipping generation dispatch")
        return []

    dispatched = []
    for template_id in template_ids:
        try:
            gen_job, task_name = await self._create_and_dispatch_generation_job(
                user_id=job.user_id,
                project_id=project_id,
                template_type=template_id,
                material_package_id=material_package_id
            )
            dispatched.append((gen_job, task_name))
            logger.info(f"Dispatched generation job {gen_job.id} for template {template_id}")
        except Exception as e:
            logger.error(f"Failed to dispatch generation job for template {template_id}: {e}")
            # Continue dispatching other templates even if one fails

    return dispatched


async def _create_and_dispatch_generation_job(
    self,
    user_id: UUID,
    project_id: UUID,
    template_type: str,
    material_package_id: UUID
) -> tuple:
    """Create and dispatch a generation job for a specific template."""
    job, task_name = await self.create_and_dispatch_job(
        user_id=user_id,
        template_type=template_type,
        job_type=JobType.GENERATION,
        material_package_id=material_package_id,
        processing_config={
            "project_id": str(project_id),
            "material_package_id": str(material_package_id),
        }
    )
    return job, task_name
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/services/job_manager.py backend/tests/test_job_manager.py
git commit -m "$(cat <<'EOF'
feat: add execute_extraction_pipeline with auto-dispatch

Runs steps 1-10 + materialize. After completion, automatically
dispatches generation jobs for all template_ids in processing_config.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.6b: Add _step_upload_cloud_generation

**Files:**
- Modify: `backend/app/services/job_manager.py`
- Test: `backend/tests/test_job_manager.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_step_upload_cloud_generation_uses_existing_images(job_manager):
    """Generation upload step reuses images from MaterialPackage, only uploads sheet."""
    job_id = uuid.uuid4()

    job_manager._pipeline_ctx[job_id] = {
        "material_package_gcs_path": "gs://bucket/materials/project-123/",
        "sheet_result": {"sheet_id": "sheet-id", "sheet_url": "https://sheets.google.com/..."},
    }

    mock_job = MagicMock()
    mock_job.processing_config = {"project_id": "project-123"}
    mock_job.template_type = TemplateType.OPR
    job_manager._get_job = AsyncMock(return_value=mock_job)

    # Mock drive client
    job_manager._drive_client = AsyncMock()
    job_manager._drive_client.move_file = AsyncMock(return_value="folder-url")

    result = await job_manager._step_upload_cloud_generation(job_id)

    # Should move sheet to Drive folder, NOT re-upload images
    job_manager._drive_client.move_file.assert_called_once()
    assert "folder_url" in result
```

**Step 2: Run test to verify it fails**

**Step 3: Add the method**

```python
async def _step_upload_cloud_generation(self, job_id: UUID) -> dict:
    """
    Upload generation outputs to Drive (generation jobs only).

    Unlike extraction's upload_cloud which uploads all images, generation
    only needs to:
    1. Move the populated sheet to the project's Drive folder
    2. Optionally create a template-specific subfolder

    Images are already in GCS from the extraction phase and can be
    accessed via the MaterialPackage's images_base_path.
    """
    ctx = self._pipeline_ctx.get(job_id, {})
    job = await self._get_job(job_id)

    sheet_result = ctx.get("sheet_result", {})
    sheet_id = sheet_result.get("sheet_id")
    project_id = job.processing_config.get("project_id")
    template_type = job.template_type.value

    # Get or create project folder
    # (May already exist from extraction or previous generation)
    folder_id = await self._drive_client.get_or_create_project_folder(
        project_id=project_id,
        project_name=ctx.get("structured_data", {}).get("project_name", "Project")
    )

    # Create template-specific subfolder (optional - keeps outputs organized)
    template_folder_id = await self._drive_client.create_folder(
        name=f"output_{template_type}",
        parent_id=folder_id
    )

    # Move sheet to template folder
    if sheet_id:
        await self._drive_client.move_file(sheet_id, template_folder_id)

    folder_url = f"https://drive.google.com/drive/folders/{template_folder_id}"

    logger.info(f"Generation outputs uploaded to {folder_url}")

    return {
        "folder_url": folder_url,
        "folder_id": template_folder_id,
        "sheet_moved": bool(sheet_id)
    }
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/services/job_manager.py backend/tests/test_job_manager.py
git commit -m "$(cat <<'EOF'
feat: add _step_upload_cloud_generation for generation jobs

Simplified upload step that only moves sheet to Drive folder.
Images are already in GCS from extraction phase.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.7: Create execute_generation_pipeline

**Files:**
- Modify: `backend/app/services/job_manager.py`
- Test: `backend/tests/test_job_manager.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_execute_generation_pipeline_runs_steps_11_to_14(job_manager):
    """Generation pipeline runs only generation steps."""
    job_id = uuid.uuid4()

    # Mock step methods
    job_manager._step_load_material_package = AsyncMock(return_value={})
    job_manager._step_generate_content = AsyncMock(return_value={})
    job_manager._step_populate_sheet = AsyncMock(return_value={})
    job_manager._step_upload_cloud_generation = AsyncMock(return_value={})
    job_manager._step_finalize_generation = AsyncMock(return_value={})

    # Should NOT call extraction steps
    job_manager._step_extract_images = AsyncMock()
    job_manager._step_classify_images = AsyncMock()

    await job_manager.execute_generation_pipeline(job_id)

    # Verify generation steps called
    job_manager._step_load_material_package.assert_called_once()
    job_manager._step_generate_content.assert_called_once()
    job_manager._step_populate_sheet.assert_called_once()

    # Verify extraction steps NOT called
    job_manager._step_extract_images.assert_not_called()
    job_manager._step_classify_images.assert_not_called()
```

**Step 2: Run test to verify it fails**

**Step 3: Add execute_generation_pipeline method**

```python
async def execute_generation_pipeline(self, job_id: UUID) -> dict:
    """
    Execute generation-only pipeline (steps 11-14).

    Loads data from existing MaterialPackage and generates content
    for a specific template.

    Returns generation results including sheet_url and drive_folder_url.
    """
    try:
        # Initialize pipeline context
        self._pipeline_ctx[job_id] = {}

        # Step 1 (generation): Load MaterialPackage from GCS
        await self._execute_step(job_id, "load_package", self._step_load_material_package)

        # Step 2 (generation): Generate content for template
        await self._execute_step(job_id, "generate_content", self._step_generate_content)

        # Step 3 (generation): Populate sheet
        await self._execute_step(job_id, "populate_sheet", self._step_populate_sheet)

        # Step 4 (generation): Upload to Drive (generation-specific, doesn't re-upload images)
        await self._execute_step(job_id, "upload_cloud", self._step_upload_cloud_generation)

        # Step 5 (generation): Finalize generation run
        result = await self._execute_step(
            job_id, "finalize_generation",
            self._step_finalize_generation
        )

        # Mark job as completed
        await self._complete_job(job_id, result)

        return result

    finally:
        # Always cleanup pipeline context
        self._pipeline_ctx.pop(job_id, None)
```

**Step 4: Run test**

**Step 5: Commit**

```bash
git add backend/app/services/job_manager.py backend/tests/test_job_manager.py
git commit -m "$(cat <<'EOF'
feat: add execute_generation_pipeline to JobManager

Runs steps 11-14 only. Loads from MaterialPackage, generates
content for specific template, populates sheet, uploads to Drive.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

(Plan continues with remaining Phase B, C, and D tasks - see full plan file for complete implementation details)

---

## Phase B Verification Checkpoint

Before proceeding to Phase C, verify:

1. [ ] Extraction job completes and creates MaterialPackage in GCS
2. [ ] MaterialPackage has all JSON files: structured_data, extracted_text, etc.
3. [ ] MaterialPackage has images folder with extracted WebP files
4. [ ] Generation jobs auto-dispatch after extraction completes
5. [ ] Generation job loads MaterialPackage and produces content
6. [ ] Generation job completes in <60s - verify with:
   ```sql
   SELECT id, job_type,
          EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
   FROM jobs
   WHERE job_type = 'generation' AND status = 'completed'
   ORDER BY completed_at DESC LIMIT 5;
   ```
7. [ ] `POST /process/extract` returns extraction_job_id
8. [ ] `POST /process/generate` returns generation_job_ids
9. [ ] Existing `/upload/pdf` still works (creates FULL job)
10. [ ] All tests pass: `pytest tests/ -v`

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Migration failure | All migrations additive with defaults; tested downgrade |
| Breaking existing flow | `job_type=full` default; routing unchanged for FULL jobs |
| Frontend/backend mismatch | TypeScript strict mode; optional fields with fallbacks |
| Memory leak in dual contexts | Explicit cleanup in finally blocks |
| GCS permission issues | StorageService already has local fallback |

---

## Deploy Sequence

1. **Migrations** (run first, backend not yet deployed)
2. **Backend code** (deploy after migrations)
3. **Frontend code** (deploy after backend API is live)

Each phase is independently deployable without breaking production.
