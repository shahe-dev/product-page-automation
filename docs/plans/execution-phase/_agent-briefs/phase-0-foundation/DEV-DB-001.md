# Agent Brief: DEV-DB-001

**Agent ID:** DEV-DB-001
**Agent Name:** Database Schema Agent
**Type:** Development
**Phase:** 0 - Foundation
**Context Budget:** 50,000 tokens

---

## Mission

Design and implement the complete PostgreSQL database schema for PDP Automation v.3, including all tables, relationships, indexes, constraints, and Alembic migrations.

---

## Documentation to Read

### Primary (MUST READ)
1. `docs/01-architecture/DATABASE_SCHEMA.md` - Complete schema specification

### Secondary (SHOULD READ)
2. `docs/02-modules/PROJECT_DATABASE.md` - Project data requirements
3. `docs/01-architecture/DATA_FLOW.md` - How data flows through the system
4. `docs/04-backend/SERVICE_LAYER.md` - Service patterns that use the database

### Reference (AS NEEDED)
5. `docs/09-reference/GLOSSARY.md` - Term definitions

---

## Dependencies

**Upstream (Required Before Start):** None - This is a foundational agent

**Downstream (Waiting on You):**
- DEV-AUTH-001 (needs User model)
- DEV-PROJECT-001 (needs Project, ProjectImage, ProjectFloorPlan models)
- DEV-JOB-001 (needs Job, JobStep models)
- All other backend agents

---

## Outputs to Produce

### File 1: `backend/alembic/versions/001_initial_schema.py`
Alembic migration file with:
- All `upgrade()` function creating tables
- All `downgrade()` function dropping tables
- Proper dependency ordering

### File 2: `backend/app/models/database.py`
SQLAlchemy ORM models for all 22 tables:

**Core Tables (16):**
- User
- Project
- ProjectImage
- ProjectFloorPlan
- ProjectApproval
- ProjectRevision
- Job
- JobStep
- Prompt
- PromptVersion
- Template
- QAComparison
- Notification
- WorkflowItem
- PublicationChecklist
- ExecutionHistory

**QA Module Tables (3):**
- QACheckpoint
- QAIssue
- QAOverride

**Content Module Tables (3):**
- ExtractedData
- GeneratedContent
- ContentQAResult

### File 3: `backend/app/models/enums.py`
Enum definitions:
- UserRole (admin, user)
- ProjectStatus (draft, active, archived)
- WorkflowStatus (draft, pending_approval, approved, revision_requested, publishing, published, qa_verified, complete)
- JobStatus (pending, processing, completed, failed, cancelled)
- ImageCategory (interior, exterior, amenity, logo, floor_plan, other)
- NotificationType (info, success, warning, error, approval, mention)

---

## Acceptance Criteria

Your work will be validated against these criteria:

1. **All 22 tables created** with correct column names, types, and constraints
2. **Foreign key relationships** properly defined between related tables
3. **Indexes created** for:
   - All foreign keys
   - Status columns (for filtering)
   - Created_at columns (for sorting)
   - Full-text search columns (project name, developer)
4. **JSONB fields** for flexible data:
   - Project.custom_fields
   - Project.extracted_data
   - Project.generated_content
   - ProjectFloorPlan.parsed_data
   - Job.processing_config
   - JobStep.step_data
5. **Audit columns** on all tables:
   - created_at (timestamp, default now)
   - updated_at (timestamp, auto-update)
   - created_by (foreign key to users, nullable)
6. **Soft delete support**:
   - is_active (boolean, default true) on Project, User
7. **Migration is reversible**:
   - upgrade() and downgrade() both work without errors
8. **Naming conventions**:
   - Table names: snake_case, plural (users, projects)
   - Column names: snake_case
   - Index names: ix_{table}_{column}
   - Foreign key names: fk_{table}_{column}

---

## Technical Specifications

### Database Environment Strategy

**Development:** Local PostgreSQL 16 via Docker
```bash
# Start local database
docker-compose up -d postgres

# Connection string for .env
DATABASE_URL=postgresql+asyncpg://pdpuser:localdevpassword@localhost:5432/pdp_automation
```

**Production:** Neon PostgreSQL 16 (serverless)
```bash
# Connection string for production .env
DATABASE_URL=postgresql+asyncpg://your-db-user:PASSWORD@your-db-host.neon.tech/neondb?sslmode=require
```

**Migration is seamless** - same PostgreSQL 16 version, same extensions, same encoding. Only the connection string changes.

### Database Connection
```python
# Use async SQLAlchemy with asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
```

### Base Model Pattern
```python
class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
```

### Table Specifications

Refer to `docs/01-architecture/DATABASE_SCHEMA.md` for complete table specifications including:
- Column types and constraints
- Relationships
- Index requirements
- JSONB schema examples

---

## Quality Standards

- Use type hints with `Mapped[]` for all columns
- Add docstrings to all model classes
- Include `__tablename__` explicitly
- Define `__repr__` for debugging
- Use relationship() with back_populates for bidirectional relationships
- Add CHECK constraints where appropriate (e.g., confidence scores 0.0-1.0)

---

## QA Pair

Your outputs will be reviewed by: **QA-DB-001**

The QA agent will verify:
- Schema matches documentation requirements
- All foreign keys have indexes
- Naming conventions followed
- Migration runs without errors
- No N+1 query risks in relationships

---

## Output Format

When complete, confirm:
```
AGENT: DEV-DB-001
STATUS: COMPLETE
OUTPUTS:
  - backend/alembic/versions/001_initial_schema.py (XXX lines)
  - backend/app/models/database.py (XXX lines)
  - backend/app/models/enums.py (XXX lines)
NOTES: [Any implementation notes or decisions]
```

---

**Begin execution.**
