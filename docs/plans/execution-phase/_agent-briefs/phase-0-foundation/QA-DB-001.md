# Agent Brief: QA-DB-001

**Agent ID:** QA-DB-001
**Agent Name:** Database Schema QA
**Type:** QA
**Phase:** 0 - Foundation
**Context Budget:** 40,000 tokens
**Paired Dev Agent:** DEV-DB-001

---

## Mission

Validate the database schema implementation from DEV-DB-001 against requirements, checking for correctness, completeness, performance considerations, and best practices.

---

## Documentation to Read

### Primary (MUST READ)
1. `docs/01-architecture/DATABASE_SCHEMA.md` - Schema specification to validate against
2. `docs/07-testing/QA_MULTI_AGENT_SYSTEM.md` - QA standards and reporting format

---

## Artifacts to Review

You will receive outputs from DEV-DB-001:
1. `backend/alembic/versions/001_initial_schema.py`
2. `backend/app/models/database.py`
3. `backend/app/models/enums.py`

---

## Validation Checklist

### 1. Schema Completeness
- [ ] All 15 required tables are present
- [ ] All columns match the DATABASE_SCHEMA.md specification
- [ ] All data types are appropriate for their purpose
- [ ] No required tables or columns are missing

### 2. Relationships
- [ ] All foreign key relationships are correctly defined
- [ ] Relationship cardinality matches requirements (1:1, 1:N, N:M)
- [ ] Cascade delete/update rules are appropriate
- [ ] No orphan records possible

### 3. Indexes
- [ ] All foreign key columns have indexes
- [ ] Status columns have indexes (for filtering queries)
- [ ] Date columns have indexes (for sorting/range queries)
- [ ] Full-text search indexes on searchable fields
- [ ] No unnecessary duplicate indexes

### 4. Constraints
- [ ] NOT NULL on required fields
- [ ] UNIQUE where specified (email, slug combinations)
- [ ] CHECK constraints on bounded values (confidence 0-1, scores)
- [ ] DEFAULT values appropriate

### 5. JSONB Fields
- [ ] JSONB used for flexible/nested data
- [ ] GIN indexes on JSONB fields that need querying
- [ ] Schema validation comments/documentation present

### 6. Audit & Soft Delete
- [ ] created_at present on all tables
- [ ] updated_at present and auto-updates
- [ ] created_by present where applicable
- [ ] is_active for soft-deletable entities

### 7. Naming Conventions
- [ ] Table names: snake_case, plural
- [ ] Column names: snake_case
- [ ] Index names: ix_{table}_{column}
- [ ] Foreign key constraint names: fk_{table}_{column}
- [ ] No abbreviations or unclear names

### 8. Migration Quality
- [ ] upgrade() creates all objects
- [ ] downgrade() removes all objects
- [ ] Order respects foreign key dependencies
- [ ] Idempotent (can run multiple times safely)

### 9. Performance Considerations
- [ ] No obvious N+1 query risks
- [ ] Appropriate use of lazy/eager loading hints
- [ ] Connection pooling compatible
- [ ] Large text fields use TEXT not VARCHAR

### 10. Security
- [ ] No sensitive data stored in plaintext
- [ ] Audit trail for sensitive operations
- [ ] Row-level security considerations documented

---

## Issue Severity Levels

When reporting issues, classify by severity:

| Severity | Definition | Examples |
|----------|------------|----------|
| **Critical** | Prevents system from functioning | Missing required table, broken FK |
| **High** | Major functionality impacted | Missing index on frequently queried column |
| **Medium** | Minor functionality or performance impact | Suboptimal data type choice |
| **Low** | Code quality or documentation issue | Missing docstring, unclear naming |

---

## Output Format

Produce a QA report in this format:

```json
{
  "agent_id": "QA-DB-001",
  "reviewed_agent": "DEV-DB-001",
  "review_timestamp": "2026-01-15T12:00:00Z",
  "artifacts_reviewed": [
    "backend/alembic/versions/001_initial_schema.py",
    "backend/app/models/database.py",
    "backend/app/models/enums.py"
  ],
  "passed": true,
  "score": 92,
  "summary": "Database schema implementation meets requirements with minor suggestions.",
  "checklist_results": {
    "schema_completeness": {"passed": true, "notes": "All 22 tables present"},
    "relationships": {"passed": true, "notes": "FKs correctly defined"},
    "indexes": {"passed": true, "notes": "All required indexes present"},
    "constraints": {"passed": true, "notes": "Appropriate constraints"},
    "jsonb_fields": {"passed": true, "notes": "JSONB used correctly"},
    "audit_soft_delete": {"passed": true, "notes": "Audit columns present"},
    "naming_conventions": {"passed": true, "notes": "Consistent naming"},
    "migration_quality": {"passed": true, "notes": "Reversible migration"},
    "performance": {"passed": true, "notes": "No obvious issues"},
    "security": {"passed": true, "notes": "No plaintext secrets"}
  },
  "issues": [
    {
      "severity": "low",
      "category": "documentation",
      "file": "backend/app/models/database.py",
      "line": 45,
      "description": "Missing docstring on ProjectImage model",
      "recommendation": "Add docstring describing the model purpose"
    }
  ],
  "recommendations": [
    "Consider adding a composite index on (project_id, category) for image filtering",
    "Document the JSONB schema for extracted_data field"
  ]
}
```

---

## Pass/Fail Criteria

| Criteria | Requirement |
|----------|-------------|
| Critical Issues | 0 |
| High Issues | 0 |
| Medium Issues | ≤ 3 |
| Low Issues | ≤ 10 |
| Overall Score | ≥ 85% |

If any Critical or High issues are found, the review **FAILS** and DEV-DB-001 must remediate before proceeding.

---

## Runtime Validation (REQUIRED)

In addition to the checklist above, perform these runtime checks:

### 1. Import Test
```python
# All model modules must import without errors
from app.models.database import (
    Base, User, Project, ProjectImage, ProjectFloorPlan, ProjectApproval,
    ProjectRevision, Job, JobStep, Prompt, PromptVersion, Template,
    QAComparison, Notification, WorkflowItem, PublicationChecklist,
    ExecutionHistory, QACheckpoint, QAIssue, QAOverride, ExtractedData,
    GeneratedContent, ContentQAResult
)
from app.models.enums import (
    UserRole, WorkflowStatus, JobStatus, JobStepStatus, ImageCategory,
    NotificationType, ApprovalAction, TemplateType, ContentVariant
)
```

### 2. Reserved Keyword Check
```python
# Check for SQLAlchemy reserved attribute names
RESERVED_NAMES = ["metadata", "registry", "query", "c"]

for model in [User, Project, Job, ...]:
    for column in model.__table__.columns:
        if column.name in RESERVED_NAMES:
            report_issue("CRITICAL", f"{model.__name__}.{column.name} uses reserved name")
```

### 3. Relationship Integrity Test
```python
# Verify relationships can be traversed
# Check that back_populates references exist
for model in Base.__subclasses__():
    for rel in model.__mapper__.relationships:
        if rel.back_populates:
            target_model = rel.mapper.class_
            assert hasattr(target_model, rel.back_populates), \
                f"{model.__name__}.{rel.key} back_populates {rel.back_populates} not found"
```

### 4. Enum Validation
```python
# Verify all enum values used in CHECK constraints are valid
from app.models.enums import TemplateType, JobStatus, ...

# Ensure CHECK constraint values match enum values
# Example: template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')
# Must match TemplateType enum values
```

### 5. Type Hint Validation
```bash
# Run mypy on model files
mypy backend/app/models/database.py --ignore-missing-imports
mypy backend/app/models/enums.py --ignore-missing-imports
```

### Runtime Validation Results

```
Import Test:           PASS / FAIL (details)
Reserved Names:        PASS / FAIL (details)
Relationship Integrity: PASS / FAIL (details)
Enum Validation:       PASS / FAIL (details)
Type Hints:            PASS / FAIL (details)
```

**Runtime Validation Status:** PASS / FAIL

**Note:** If Runtime Validation fails, the overall QA review FAILS regardless of checklist score.

---

**Begin review.**
