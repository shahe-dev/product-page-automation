# Agent Brief: DEV-OAUTH-001

**Agent ID:** DEV-OAUTH-001
**Agent Name:** OAuth Integration Agent
**Type:** Development
**Phase:** 5 - Integrations
**Context Budget:** 50,000 tokens

---

## Mission

Implement Google OAuth 2.0 client for user authentication with domain restriction and token management.

---

## Documentation to Read

### Primary
1. `docs/05-integrations/GOOGLE_OAUTH_SETUP.md` - OAuth configuration
2. `docs/01-architecture/SECURITY_ARCHITECTURE.md` - Security requirements

---

## Dependencies

**Upstream:** DEV-CONFIG-001
**Downstream:** DEV-AUTH-001

---

## Outputs

### `backend/app/integrations/oauth_client.py`

---

## Acceptance Criteria

1. **OAuth Flow:**
   - Generate authorization URL
   - Handle callback with code
   - Exchange code for tokens
   - Extract user info

2. **Token Management:**
   - Access token handling
   - Refresh token storage
   - Token refresh before expiry
   - Token revocation on logout

3. **Domain Restriction:**
   - Validate @your-domain.com domain
   - Reject other domains
   - Clear error message

4. **User Info Extraction:**
   - Email
   - Name
   - Profile picture URL
   - Google user ID

5. **Security:**
   - State parameter for CSRF
   - PKCE flow (if applicable)
   - Secure token storage
   - No tokens in logs

6. **Error Handling:**
   - Handle invalid code
   - Handle expired code
   - Handle revoked access
   - Handle network errors

---

## OAuth Flow

```
1. Frontend redirects to /auth/google
2. Backend generates auth URL with state
3. User authenticates with Google
4. Google redirects to callback URL
5. Backend exchanges code for tokens
6. Backend validates domain
7. Backend creates/updates user
8. Backend issues JWT
9. Frontend receives JWT
```

---

## QA Pair: QA-OAUTH-001

---

**Begin execution.**
