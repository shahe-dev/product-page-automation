# Agent Brief: ORCH-INTEGRATION-001

**Agent ID:** ORCH-INTEGRATION-001
**Agent Name:** Integration Orchestrator
**Type:** Orchestrator
**Tier:** 2 (Domain)
**Context Budget:** 80,000 tokens

---

## Mission

Coordinate all external service integration agents in Phase 5, ensure API patterns consistency, and manage authentication flows.

---

## Documentation to Read

### Primary (Always Loaded)
1. `docs/05-integrations/GOOGLE_CLOUD_SETUP.md`
2. `docs/05-integrations/GOOGLE_SHEETS_INTEGRATION.md`
3. `docs/05-integrations/GOOGLE_OAUTH_SETUP.md`
4. `docs/05-integrations/GOOGLE_DRIVE_INTEGRATION.md`
5. `docs/05-integrations/CLOUD_STORAGE_PATTERNS.md`
6. `docs/05-integrations/ANTHROPIC_API_INTEGRATION.md`

---

## Subordinates

- DEV-GCS-001
- DEV-GSHEETS-001
- DEV-DRIVE-001
- DEV-ANTHROPIC-001
- DEV-OAUTH-001

---

## Responsibilities

1. **Integration Coordination:**
   - Sequence integration development
   - Ensure client pattern consistency
   - Coordinate authentication flows
   - Manage API key handling

2. **Error Handling:**
   - Ensure retry patterns consistent
   - Coordinate rate limiting
   - Standardize error responses
   - Manage fallback behaviors

3. **Security:**
   - Verify credential handling
   - Ensure secret management
   - Coordinate OAuth flows
   - Review permission scopes

4. **Cost Management:**
   - Track API usage
   - Optimize call patterns
   - Monitor quotas
   - Coordinate caching

---

## Integration Dependencies

```
DEV-CONFIG-001 (secrets)
    ├── DEV-GCS-001
    ├── DEV-GSHEETS-001
    ├── DEV-DRIVE-001
    ├── DEV-ANTHROPIC-001
    └── DEV-OAUTH-001
```

---

## API Pattern Standards

| Pattern | Implementation |
|---------|---------------|
| Retry | Exponential backoff with jitter |
| Rate Limit | Queue with token bucket |
| Auth | Service account / OAuth 2.0 |
| Error | Wrap in integration exceptions |

---

**Begin orchestration.**
