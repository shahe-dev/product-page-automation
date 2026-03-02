# Agent Brief: TEST-FRONTEND-UNIT-001

**Agent ID:** TEST-FRONTEND-UNIT-001
**Agent Name:** Frontend Unit Test Agent
**Type:** Testing
**Phase:** Testing
**Context Budget:** 50,000 tokens

---

## Mission

Implement unit tests for all React components, hooks, and stores using Vitest and React Testing Library with 70%+ coverage.

---

## Documentation to Read

### Primary
1. `docs/07-testing/UNIT_TEST_PATTERNS.md` - Unit test patterns
2. `docs/07-testing/TEST_STRATEGY.md` - Test strategy overview

---

## Dependencies

**Upstream:** Phase 4 (all frontend agents)
**Downstream:** TEST-FE-INT-001

---

## Outputs

### `frontend/src/**/*.test.tsx` - Component tests (co-located)
### `frontend/vitest.config.ts` - Vitest configuration

---

## Coverage Target: 70%

---

## Acceptance Criteria

1. **Component Tests:**
   - Render without errors
   - Props passed correctly
   - Events fire correctly
   - Conditional rendering
   - Accessibility attributes

2. **Hook Tests:**
   - State changes correctly
   - Side effects trigger
   - Cleanup runs
   - Error states

3. **Store Tests:**
   - Initial state correct
   - Actions update state
   - Selectors return correct data
   - Persistence works

4. **Test Utilities:**
   - Custom render with providers
   - Mock API responses
   - Mock router
   - Test data factories

5. **Testing Patterns:**
   - Test user interactions
   - Test accessibility
   - Avoid testing implementation
   - Use semantic queries

---

## Test Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   └── Button.test.tsx
│   │   └── ...
│   ├── hooks/
│   │   ├── useProjects.ts
│   │   └── useProjects.test.ts
│   └── stores/
│       ├── auth-store.ts
│       └── auth-store.test.ts
├── vitest.config.ts
└── vitest.setup.ts
```

---

**Begin execution.**
