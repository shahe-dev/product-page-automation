# Agent Brief: TEST-FE-INT-001

**Agent ID:** TEST-FE-INT-001
**Agent Name:** Frontend Integration Test Agent
**Type:** Testing
**Phase:** Testing
**Context Budget:** 50,000 tokens

---

## Mission

Implement frontend integration tests verifying page flows, API interactions, and state management using React Testing Library.

---

## Documentation to Read

### Primary
1. `docs/07-testing/INTEGRATION_TESTS.md` - Integration test patterns

---

## Dependencies

**Upstream:** Phase 4 (frontend agents)
**Downstream:** TEST-E2E-001

---

## Outputs

### `frontend/tests/integration/` - Integration tests

---

## Acceptance Criteria

1. **Page Flow Tests:**
   - Login to dashboard
   - Upload to processing
   - Dashboard to project detail
   - QA review flow
   - Workflow transitions

2. **API Integration:**
   - Mock server responses
   - Loading states
   - Error states
   - Success states

3. **State Management:**
   - Store updates on API response
   - Optimistic updates
   - Error recovery
   - Cache invalidation

4. **Multi-Component:**
   - Filter + List interaction
   - Form + Validation
   - Modal + Parent
   - Tab + Content

5. **Test Setup:**
   - MSW for API mocking
   - Router provider
   - Store provider
   - Test utilities

---

## Test Categories

```
frontend/tests/integration/
├── auth-flow.test.tsx
├── upload-flow.test.tsx
├── project-detail-flow.test.tsx
├── qa-review-flow.test.tsx
├── workflow-flow.test.tsx
└── setup.ts
```

---

**Begin execution.**
