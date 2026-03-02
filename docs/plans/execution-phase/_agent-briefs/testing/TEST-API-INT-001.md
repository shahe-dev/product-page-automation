# Agent Brief: TEST-API-INT-001

**Agent ID:** TEST-API-INT-001
**Agent Name:** API Integration Test Agent
**Type:** Testing
**Phase:** Testing
**Context Budget:** 55,000 tokens

---

## Mission

Implement API integration tests verifying endpoint behavior, authentication, and data flow using pytest and httpx.

---

## Documentation to Read

### Primary
1. `docs/07-testing/INTEGRATION_TESTS.md` - Integration test patterns
2. `docs/04-backend/API_ENDPOINTS.md` - API specification

---

## Dependencies

**Upstream:** Phase 1, Phase 5 (backend core, integrations)
**Downstream:** TEST-E2E-001

---

## Outputs

### `tests/integration/api/` - API integration tests
### `tests/integration/conftest.py` - Integration fixtures

---

## Coverage Target: 75%

---

## Acceptance Criteria

1. **Authentication Tests:**
   - Login flow
   - Token validation
   - Token refresh
   - Unauthorized access
   - Permission checks

2. **CRUD Tests:**
   - Create resources
   - Read resources
   - Update resources
   - Delete resources
   - List with pagination

3. **Business Logic Tests:**
   - Job creation and processing
   - Content generation flow
   - QA validation flow
   - Workflow transitions

4. **Error Handling:**
   - Validation errors (422)
   - Not found (404)
   - Unauthorized (401)
   - Forbidden (403)
   - Server errors (500)

5. **Test Setup:**
   - Test database (isolated)
   - Seed data fixtures
   - Cleanup after tests
   - Parallel test support

---

## Test Categories

```
tests/integration/api/
├── test_auth_endpoints.py
├── test_projects_endpoints.py
├── test_jobs_endpoints.py
├── test_upload_endpoints.py
├── test_content_endpoints.py
├── test_qa_endpoints.py
├── test_workflow_endpoints.py
└── conftest.py
```

---

**Begin execution.**
