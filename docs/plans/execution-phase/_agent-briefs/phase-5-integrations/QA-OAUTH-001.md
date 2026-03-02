# Agent Brief: QA-OAUTH-001

**Agent ID:** QA-OAUTH-001
**Agent Name:** OAuth Integration QA
**Type:** QA
**Phase:** 5 - Integrations
**Paired Dev Agent:** DEV-OAUTH-001

---

## Validation Checklist

- [ ] Authorization URL generated correctly
- [ ] State parameter present
- [ ] Callback handles code exchange
- [ ] Tokens extracted correctly
- [ ] User info extracted correctly
- [ ] Domain restriction enforced
- [ ] Token refresh works
- [ ] Token revocation works
- [ ] CSRF protection (state) works
- [ ] Error handling robust

---

## Test Cases

1. Generate auth URL
2. Successful OAuth flow (mock)
3. Invalid code handling
4. Expired code handling
5. Domain validation (allowed)
6. Domain validation (rejected)
7. Token refresh
8. Token revocation
9. CSRF attack prevention
10. Network error handling
11. Extract all user fields
12. Handle missing profile picture

---

## Security Tests

- State parameter validated
- Tokens not logged
- Redirect URI validated
- Code exchange timeout

---

## Domain Restriction Tests

- @your-domain.com allowed
- @gmail.com rejected
- @otherdomain.com rejected
- Clear error message shown

---

## Integration Tests

- Full OAuth flow end-to-end
- Logout clears tokens
- Re-login after logout
- Multiple device login

---

**Begin review.**
