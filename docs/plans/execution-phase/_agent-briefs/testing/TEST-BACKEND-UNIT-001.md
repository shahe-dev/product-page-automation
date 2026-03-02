# Agent Brief: TEST-BACKEND-UNIT-001

**Agent ID:** TEST-BACKEND-UNIT-001
**Agent Name:** Backend Unit Test Agent
**Type:** Testing
**Phase:** Testing
**Context Budget:** 50,000 tokens

---

## Mission

Implement comprehensive unit tests for all backend services, repositories, and utilities using pytest with 80%+ coverage.

---

## Documentation to Read

### Primary
1. `docs/07-testing/UNIT_TEST_PATTERNS.md` - Unit test patterns
2. `docs/07-testing/TEST_STRATEGY.md` - Test strategy overview

---

## Dependencies

**Upstream:** Phase 1, Phase 2, Phase 3 (all backend agents)
**Downstream:** TEST-API-INT-001

---

## Outputs

### `tests/unit/services/` - Service unit tests
### `tests/unit/repositories/` - Repository unit tests
### `tests/unit/utils/` - Utility unit tests
### `tests/conftest.py` - Shared fixtures
### `pytest.ini` - Pytest configuration

---

## Coverage Target: 80%

---

## Acceptance Criteria

1. **Service Tests:**
   - Test each public method
   - Mock external dependencies
   - Test error conditions
   - Test edge cases
   - Test async methods

2. **Repository Tests:**
   - Mock database session
   - Test CRUD operations
   - Test query methods
   - Test pagination
   - Test filters

3. **Utility Tests:**
   - Test pure functions
   - Test input validation
   - Test error handling

4. **Test Fixtures:**
   - Database session mock
   - Redis mock (if used)
   - Anthropic client mock
   - GCS client mock
   - Sample data factories

5. **Test Quality:**
   - Descriptive test names
   - Arrange-Act-Assert pattern
   - One assertion per test (when practical)
   - No test interdependency

---

## Test Structure

```
tests/
├── unit/
│   ├── services/
│   │   ├── test_auth_service.py
│   │   ├── test_project_service.py
│   │   ├── test_job_manager.py
│   │   └── ...
│   ├── repositories/
│   │   ├── test_project_repository.py
│   │   └── ...
│   └── utils/
│       ├── test_pdf_helpers.py
│       └── ...
├── conftest.py
└── pytest.ini
```

---

**Begin execution.**
