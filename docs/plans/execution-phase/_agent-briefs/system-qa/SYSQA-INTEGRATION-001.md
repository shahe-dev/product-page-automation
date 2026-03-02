# Agent Brief: SYSQA-INTEGRATION-001

**Agent ID:** SYSQA-INTEGRATION-001
**Agent Name:** Integration QA Agent
**Type:** System QA
**Context Budget:** 50,000 tokens

---

## Mission

Validate integration points between services, verify API contracts, and ensure cross-component compatibility.

---

## Documentation to Read

### Primary
1. `docs/07-testing/QA_MULTI_AGENT_SYSTEM.md` - Integration QA specs
2. `docs/07-testing/INTEGRATION_TESTS.md` - Integration test patterns

---

## Triggers

- PR creation
- Pre-merge check
- Post-deployment

---

## Responsibilities

1. **API Contract Validation:**
   - Request/response schema
   - Status codes
   - Error formats
   - Headers

2. **Service Integration:**
   - Database connectivity
   - External API calls
   - Message queue operations
   - Cache operations

3. **Data Flow Validation:**
   - End-to-end data paths
   - Transformation accuracy
   - State consistency
   - Transaction integrity

4. **Compatibility Checks:**
   - Frontend-backend alignment
   - API version compatibility
   - Database migration impact

---

## Integration Points

| Integration | Validation |
|-------------|------------|
| Frontend ↔ Backend | API contract match |
| Backend ↔ Database | Schema alignment |
| Backend ↔ GCS | Upload/download flow |
| Backend ↔ Sheets | Template population |
| Backend ↔ Anthropic | Request/response format |
| PDFProcessor ↔ FloorPlanExtractor | `page_text_map` passed via JobManager context |

---

## Test Scenarios

1. **Happy Path:** Full data flow succeeds
2. **Partial Failure:** Graceful degradation
3. **Timeout:** Proper timeout handling
4. **Invalid Data:** Validation rejection
5. **Recovery:** Retry and recovery

---

## Output Format

```json
{
  "status": "pass|warn|fail",
  "integration_tests": {
    "passed": 45,
    "failed": 2,
    "skipped": 1
  },
  "api_contracts": {
    "valid": 12,
    "mismatched": 0
  },
  "issues": []
}
```

---

**Begin monitoring.**
