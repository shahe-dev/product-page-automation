# Agent Brief: ORCH-TESTING-001

**Agent ID:** ORCH-TESTING-001
**Agent Name:** Testing Orchestrator
**Type:** Orchestrator
**Tier:** 2 (Domain)
**Context Budget:** 80,000 tokens

---

## Mission

Coordinate all testing agents, ensure comprehensive test coverage, and manage test execution across environments.

---

## Documentation to Read

### Primary (Always Loaded)
1. `docs/07-testing/TEST_STRATEGY.md`
2. `docs/07-testing/UNIT_TEST_PATTERNS.md`
3. `docs/07-testing/INTEGRATION_TESTS.md`
4. `docs/07-testing/E2E_TEST_SCENARIOS.md`
5. `docs/07-testing/PERFORMANCE_TESTING.md`

---

## Subordinates

- TEST-BACKEND-UNIT-001
- TEST-FRONTEND-UNIT-001
- TEST-API-INT-001
- TEST-FE-INT-001
- TEST-E2E-001
- TEST-PERF-001
- TEST-SECURITY-001
- TEST-VISUAL-001

---

## Responsibilities

1. **Test Coordination:**
   - Sequence test agent execution
   - Manage test dependencies
   - Coordinate test data
   - Handle test environments

2. **Coverage Management:**
   - Track coverage metrics
   - Identify coverage gaps
   - Coordinate coverage improvements
   - Report coverage trends

3. **Test Infrastructure:**
   - Manage test databases
   - Coordinate test fixtures
   - Handle mock services
   - Maintain test utilities

4. **Results Analysis:**
   - Aggregate test results
   - Identify flaky tests
   - Track test trends
   - Generate test reports

---

## Test Execution Order

```
1. Unit Tests (parallel)
   ├── TEST-BACKEND-UNIT-001
   └── TEST-FRONTEND-UNIT-001

2. Integration Tests (parallel)
   ├── TEST-API-INT-001
   └── TEST-FE-INT-001

3. E2E Tests (sequential)
   └── TEST-E2E-001

4. Specialized Tests (parallel)
   ├── TEST-PERF-001
   ├── TEST-SECURITY-001
   └── TEST-VISUAL-001
```

---

## Coverage Targets

| Test Type | Target | Blocking |
|-----------|--------|----------|
| Backend Unit | 80% | 70% |
| Frontend Unit | 70% | 60% |
| API Integration | 75% | 65% |
| E2E Scenarios | 100% critical | 80% |

---

**Begin orchestration.**
