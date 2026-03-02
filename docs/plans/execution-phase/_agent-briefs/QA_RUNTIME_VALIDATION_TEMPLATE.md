# QA Runtime Validation Template

**Version:** 1.0
**Created:** 2026-01-26
**Purpose:** Standard runtime validation requirements for all QA agents

---

## Overview

This template defines runtime validation checks that ALL QA agents must perform in addition to their domain-specific validation checklists.

**Why Runtime Validation?**

Structural review alone is insufficient. Phase 0 revealed issues that only manifest at runtime:
- Reserved keyword conflicts (`metadata` field in SQLAlchemy model)
- Async/sync compatibility issues (`QueuePool` with async engine)
- Configuration parsing errors (JSON array format for list fields)
- Missing supporting files (Alembic configuration)

---

## Required Runtime Checks

### 1. Import Validation (ALL QA Agents)

```python
# Attempt to import all modules produced by the paired DEV agent
import sys
sys.path.insert(0, "backend")

def test_imports():
    errors = []

    # Replace with actual module paths from DEV agent outputs
    modules_to_test = [
        ("app.models.database", ["User", "Project", "Job"]),
        ("app.config.settings", ["Settings", "get_settings"]),
        ("app.services.auth_service", ["AuthService"]),
    ]

    for module_path, exports in modules_to_test:
        try:
            module = __import__(module_path, fromlist=exports)
            for export in exports:
                if not hasattr(module, export):
                    errors.append(f"FAIL: {module_path}.{export} not found")
        except ImportError as e:
            errors.append(f"FAIL: Cannot import {module_path} - {e}")
        except Exception as e:
            errors.append(f"FAIL: Error loading {module_path} - {e}")

    return errors
```

**Pass Criteria:** Zero import errors

---

### 2. Reserved Keyword Check (Database/Model QA Agents)

```python
# SQLAlchemy reserved attribute names
SQLALCHEMY_RESERVED = [
    "metadata",      # DeclarativeBase.metadata
    "registry",      # DeclarativeBase.registry
    "query",         # Query attribute
    "c",             # Column collection shorthand
]

# Pydantic reserved field names
PYDANTIC_RESERVED = [
    "model_config",
    "model_fields",
    "model_computed_fields",
    "model_extra",
    "model_fields_set",
]

def check_reserved_names(model_class):
    issues = []
    for attr_name in dir(model_class):
        if attr_name in SQLALCHEMY_RESERVED:
            # Check if it's a user-defined column, not the base attribute
            if hasattr(model_class, '__table__'):
                if attr_name in model_class.__table__.columns:
                    issues.append(f"CRITICAL: {model_class.__name__}.{attr_name} conflicts with SQLAlchemy reserved name")
    return issues
```

**Pass Criteria:** Zero reserved name conflicts

---

### 3. Configuration Load Test (Config QA Agents)

```python
import os

def test_configuration_loading():
    # Set minimal test environment
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
    os.environ.setdefault("JWT_SECRET", "test-secret-minimum-32-characters-long")
    os.environ.setdefault("GOOGLE_CLIENT_ID", "test.apps.googleusercontent.com")
    os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-secret-value")
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")
    # ... other required fields with test values

    try:
        from app.config.settings import Settings
        settings = Settings()
        return "PASS: Configuration loads successfully"
    except Exception as e:
        return f"FAIL: Configuration error - {e}"
```

**Pass Criteria:** Configuration loads without validation errors using test values

---

### 4. Async Pattern Validation (Backend QA Agents)

```python
import ast
import inspect

SYNC_PATTERNS_IN_ASYNC = [
    "time.sleep",           # Use asyncio.sleep
    "requests.get",         # Use httpx or aiohttp
    "requests.post",
    "open(",                # Use aiofiles
    ".connect()",           # Check if sync DB connect
]

def check_async_patterns(file_path):
    issues = []
    with open(file_path) as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            # Check function body for sync patterns
            func_source = ast.unparse(node)
            for pattern in SYNC_PATTERNS_IN_ASYNC:
                if pattern in func_source:
                    issues.append(f"WARNING: {file_path}:{node.name} may use sync pattern '{pattern}' in async function")

    return issues
```

**Pass Criteria:** No sync-blocking calls in async functions

---

### 5. Migration Validation (Database QA Agents)

```python
def validate_alembic_setup():
    issues = []

    # Check required files exist
    required_files = [
        "backend/alembic.ini",
        "backend/alembic/env.py",
        "backend/alembic/script.py.mako",
    ]

    for file_path in required_files:
        if not os.path.exists(file_path):
            issues.append(f"CRITICAL: Missing {file_path}")

    # Try to parse env.py
    if os.path.exists("backend/alembic/env.py"):
        try:
            with open("backend/alembic/env.py") as f:
                compile(f.read(), "env.py", "exec")
        except SyntaxError as e:
            issues.append(f"CRITICAL: alembic/env.py has syntax error - {e}")

    return issues
```

**Pass Criteria:** All Alembic files exist and are syntactically valid

---

### 6. Type Hint Validation (ALL QA Agents)

```bash
# Run mypy on produced files
mypy backend/app/services/auth_service.py --ignore-missing-imports --no-error-summary

# Expected: No errors or only import-related warnings
```

**Pass Criteria:** No type errors (import warnings acceptable)

---

## Integration into QA Brief

Add this section to every QA agent brief:

```markdown
## Runtime Validation (REQUIRED)

In addition to the domain-specific checklist above, perform these runtime checks:

- [ ] **Import Test:** All modules import without errors
- [ ] **Reserved Names:** No SQLAlchemy/Pydantic reserved name conflicts
- [ ] **Config Load:** Configuration loads with test values (if applicable)
- [ ] **Async Patterns:** No sync-blocking calls in async functions
- [ ] **Migration Setup:** Alembic files exist and parse (if applicable)
- [ ] **Type Hints:** mypy passes with --ignore-missing-imports

### Runtime Validation Results

```
Import Test:      PASS / FAIL (details)
Reserved Names:   PASS / FAIL (details)
Config Load:      PASS / FAIL / N/A
Async Patterns:   PASS / FAIL (details)
Migration Setup:  PASS / FAIL / N/A
Type Hints:       PASS / FAIL (details)
```

**Runtime Validation Status:** PASS / FAIL

Note: If Runtime Validation fails, the overall QA review FAILS regardless of checklist score.
```

---

## Failure Escalation

If runtime validation fails:

1. **Document the specific failure** in the QA report
2. **Categorize severity:**
   - Import errors = CRITICAL (blocks all downstream)
   - Reserved names = CRITICAL (will fail at runtime)
   - Config errors = HIGH (blocks application startup)
   - Async issues = MEDIUM (may cause performance issues)
   - Type errors = LOW (documentation/maintenance issue)
3. **Return to DEV agent** for remediation before proceeding

---

## Lessons from Phase 0

| Issue Found | Root Cause | Prevention |
|-------------|------------|------------|
| `metadata` field conflict | SQLAlchemy reserves this name | Reserved name check |
| `QueuePool` with async engine | Sync pool class used | Async pattern validation |
| `ALLOWED_ORIGINS` parse error | Comma-separated vs JSON array | Config load test |
| Missing `alembic/env.py` | Not in DEV agent outputs | Migration validation |

---

**Document Status:** Active
**Maintained By:** QA Team
