# Agent Brief: QA-AUTH-001

**Agent ID:** QA-AUTH-001
**Agent Name:** Auth Service QA
**Type:** QA
**Phase:** 1 - Backend Core
**Context Budget:** 45,000 tokens
**Paired Dev Agent:** DEV-AUTH-001

---

## Mission

Validate the authentication implementation against security best practices, OWASP guidelines, and functional requirements.

---

## Documentation to Read

### Primary (MUST READ)
1. `docs/01-architecture/SECURITY_ARCHITECTURE.md` - Security requirements
2. `docs/07-testing/QA_MULTI_AGENT_SYSTEM.md` - QA standards

---

## Artifacts to Review

1. `backend/app/services/auth_service.py`
2. `backend/app/services/user_service.py`
3. `backend/app/middleware/auth.py`
4. `backend/app/middleware/permissions.py`
5. `backend/app/api/routes/auth.py`

---

## Validation Checklist

### 1. OWASP Authentication Guidelines
- [ ] Passwords/tokens not logged
- [ ] Secure token generation (cryptographically random)
- [ ] Proper token storage recommendations
- [ ] Session timeout implemented
- [ ] Account lockout consideration (if applicable)

### 2. JWT Security
- [ ] Strong algorithm (HS256 minimum)
- [ ] Appropriate expiry (not too long)
- [ ] Required claims present (sub, exp, iat)
- [ ] Signature validated before payload access
- [ ] No sensitive data in payload

### 3. OAuth Implementation
- [ ] State parameter for CSRF protection
- [ ] Token exchange server-side only
- [ ] Google token verified
- [ ] Domain restriction enforced

### 4. Refresh Token Security
- [ ] Stored as hash, not plaintext
- [ ] Single-use or rotation implemented
- [ ] Proper invalidation on logout
- [ ] Separate from access token

### 5. Domain Restriction
- [ ] @your-domain.com enforced server-side
- [ ] Clear error message for wrong domain
- [ ] Cannot be bypassed

### 6. Rate Limiting
- [ ] Auth endpoints rate limited
- [ ] Prevents brute force
- [ ] Returns appropriate headers

### 7. Error Handling
- [ ] Generic messages (don't reveal user existence)
- [ ] Consistent error format
- [ ] Proper HTTP status codes
- [ ] No stack traces to client

### 8. Audit Logging
- [ ] Login attempts logged
- [ ] Failed authentications logged
- [ ] No secrets in logs

### 9. Code Quality
- [ ] Type hints present
- [ ] Async/await used correctly
- [ ] No hardcoded secrets
- [ ] Clean separation of concerns

### 10. XSS/CSRF Protection
- [ ] Tokens not in URL
- [ ] HttpOnly cookies (if used)
- [ ] CORS configured correctly

---

## Security Test Cases to Verify

1. **Expired token rejected**
2. **Tampered token rejected**
3. **Wrong domain rejected**
4. **Missing token returns 401**
5. **Non-admin can't access admin routes**
6. **Logout invalidates tokens**
7. **Refresh token works once**

---

## Runtime Validation (REQUIRED)

In addition to the domain-specific checklist above, perform these runtime checks:

- [ ] **Import Test:** All modules import without errors
- [ ] **Reserved Names:** No SQLAlchemy/Pydantic reserved name conflicts
- [ ] **Async Patterns:** No sync-blocking calls in async functions
- [ ] **Type Hints:** mypy passes with --ignore-missing-imports

### Import Validation Script

```python
import sys
sys.path.insert(0, "backend")

def test_auth_imports():
    errors = []

    modules_to_test = [
        ("app.services.auth_service", ["AuthService"]),
        ("app.services.user_service", ["UserService"]),
        ("app.middleware.auth", ["get_current_user", "require_auth"]),
        ("app.middleware.permissions", ["require_role", "Permission"]),
        ("app.api.routes.auth", ["router"]),
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

    return errors if errors else ["PASS: All imports successful"]
```

### Reserved Name Check

Verify these modules don't use reserved names:
- `auth_service.py`: Check no field named `metadata`, `registry`, `query`
- `user_service.py`: Check Pydantic models don't use `model_config` as field

### Async Pattern Check

Verify auth_service.py and middleware/auth.py:
- No `time.sleep()` - should use `asyncio.sleep()`
- No `requests.*` - should use `httpx` with async
- Database calls use `async with session`

### Runtime Validation Results

```
Import Test:      PASS / FAIL (details)
Reserved Names:   PASS / FAIL (details)
Async Patterns:   PASS / FAIL (details)
Type Hints:       PASS / FAIL (details)
```

**Runtime Validation Status:** PASS / FAIL

Note: If Runtime Validation fails, the overall QA review FAILS regardless of checklist score.

---

## Output Format

```json
{
  "agent_id": "QA-AUTH-001",
  "reviewed_agent": "DEV-AUTH-001",
  "review_timestamp": "2026-01-15T12:00:00Z",
  "passed": true,
  "score": 90,
  "checklist_results": {...},
  "runtime_validation": {
    "import_test": "PASS",
    "reserved_names": "PASS",
    "async_patterns": "PASS",
    "type_hints": "PASS"
  },
  "issues": [],
  "security_findings": [],
  "recommendations": []
}
```

---

**Begin review.**
