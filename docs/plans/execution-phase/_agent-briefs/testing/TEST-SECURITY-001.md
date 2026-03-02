# Agent Brief: TEST-SECURITY-001

**Agent ID:** TEST-SECURITY-001
**Agent Name:** Security Test Agent
**Type:** Testing
**Phase:** Testing
**Context Budget:** 50,000 tokens

---

## Mission

Implement security tests including vulnerability scanning, penetration testing scripts, and security regression tests.

---

## Documentation to Read

### Primary
1. `docs/07-testing/QA_MULTI_AGENT_SYSTEM.md` - Security agent specs
2. `docs/01-architecture/SECURITY_ARCHITECTURE.md` - Security requirements

---

## Dependencies

**Upstream:** Phase 6 (deployed application)
**Downstream:** None

---

## Outputs

### `tests/security/` - Security test suite
### `.github/workflows/security-scan.yml` - Security CI workflow

---

## Acceptance Criteria

1. **Vulnerability Scanning:**
   - Dependency scanning (pip-audit, npm audit)
   - Container scanning (trivy)
   - SAST scanning (bandit, semgrep)
   - Secret detection (gitleaks)

2. **Authentication Tests:**
   - Token validation bypass attempts
   - Session fixation tests
   - Brute force protection
   - Domain restriction bypass

3. **Authorization Tests:**
   - Privilege escalation attempts
   - IDOR (Insecure Direct Object Reference)
   - Role boundary tests
   - Resource access control

4. **Input Validation:**
   - SQL injection tests
   - XSS injection tests
   - Command injection tests
   - Path traversal tests

5. **API Security:**
   - Rate limiting verification
   - CORS configuration
   - Header security
   - Error information leakage

---

## Security Test Categories

```
tests/security/
├── auth/
│   ├── test_token_validation.py
│   ├── test_session_security.py
│   └── test_domain_restriction.py
├── authorization/
│   ├── test_privilege_escalation.py
│   └── test_resource_access.py
├── injection/
│   ├── test_sql_injection.py
│   ├── test_xss.py
│   └── test_command_injection.py
└── api/
    ├── test_rate_limiting.py
    └── test_headers.py
```

---

## CI Security Workflow

```yaml
# .github/workflows/security-scan.yml
- pip-audit (Python dependencies)
- npm audit (Node dependencies)
- trivy (Container scanning)
- bandit (Python SAST)
- gitleaks (Secret detection)
```

---

**Begin execution.**
