# Agent Brief: DEV-AUTH-001

**Agent ID:** DEV-AUTH-001
**Agent Name:** Auth Service Agent
**Type:** Development
**Phase:** 1 - Backend Core
**Context Budget:** 55,000 tokens

---

## Mission

Implement the complete authentication and authorization system for PDP Automation v.3, including Google OAuth integration, JWT token management, refresh tokens, and role-based access control (RBAC).

---

## Documentation to Read

### Primary (MUST READ)
1. `docs/05-integrations/GOOGLE_OAUTH_SETUP.md` - OAuth flow and configuration
2. `docs/01-architecture/SECURITY_ARCHITECTURE.md` - Security requirements and patterns

### Secondary (SHOULD READ)
3. `docs/04-backend/API_ENDPOINTS.md` - Auth endpoint specifications
4. `docs/04-backend/ERROR_HANDLING.md` - Error response patterns

### Reference (AS NEEDED)
5. `docs/08-user-guides/ADMIN_GUIDE.md` - User management requirements

---

## Dependencies

**Upstream (Required Before Start):**
- DEV-DB-001: User model, database connection
- DEV-CONFIG-001: JWT_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

**Downstream (Waiting on You):**
- DEV-API-001: Needs auth middleware for protected routes
- DEV-PROJECT-001: Needs get_current_user dependency
- All other backend agents: Need auth decorators

---

## Outputs to Produce

### File 1: `backend/app/services/auth_service.py`
Authentication service with:
- Google OAuth token exchange
- JWT generation and validation
- Refresh token management
- User session handling

### File 2: `backend/app/services/user_service.py`
User management service with:
- Get or create user from OAuth
- User profile management
- Role management (admin only)

### File 3: `backend/app/middleware/auth.py`
Authentication middleware with:
- JWT validation
- Current user extraction
- Token refresh handling

### File 4: `backend/app/middleware/permissions.py`
Authorization decorators:
- @require_admin
- @require_role(roles: list)
- @require_owner_or_admin(resource_user_id_param)

### File 5: `backend/app/api/routes/auth.py`
Auth API routes:
- POST /api/auth/google
- POST /api/auth/refresh
- GET /api/auth/me
- POST /api/auth/logout

---

## Acceptance Criteria

1. **Google OAuth Flow Working:**
   - Accept Google auth code from frontend
   - Exchange for Google tokens
   - Verify token with Google
   - Extract user info (email, name, picture)

2. **JWT Token Management:**
   - Generate JWT with 1-hour expiry
   - Include user_id, email, role in payload
   - Sign with HS256 algorithm
   - Validate signature and expiry

3. **Refresh Token Mechanism:**
   - Generate refresh token (7-day expiry)
   - Store refresh token hash in database
   - Exchange refresh token for new JWT
   - Invalidate on logout

4. **Domain Restriction:**
   - Only allow @your-domain.com email addresses
   - Reject other domains with clear error

5. **Role-Based Access Control:**
   - Support roles: admin, user
   - Decorators for route protection
   - Return 403 for unauthorized access

6. **Audit Logging:**
   - Log all login attempts
   - Log failed authentications
   - Log role changes

---

## Technical Specifications

### OAuth Flow
```python
async def authenticate_google(code: str) -> AuthResponse:
    # 1. Exchange code for Google tokens
    # 2. Verify ID token with Google
    # 3. Extract user info
    # 4. Check domain restriction
    # 5. Get or create user
    # 6. Generate JWT and refresh token
    # 7. Return tokens
```

### JWT Payload
```python
{
    "sub": "user_id_uuid",
    "email": "user@your-domain.com",
    "role": "user",
    "exp": timestamp,
    "iat": timestamp
}
```

### Auth Dependency
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> User:
    token = credentials.credentials
    payload = verify_jwt(token)
    user = await get_user_by_id(payload["sub"])
    return user
```

---

## Error Handling

| Scenario | Status | Error Code |
|----------|--------|------------|
| Invalid Google token | 401 | INVALID_TOKEN |
| Wrong email domain | 403 | DOMAIN_NOT_ALLOWED |
| Expired JWT | 401 | TOKEN_EXPIRED |
| Invalid JWT signature | 401 | INVALID_TOKEN |
| User not found | 401 | USER_NOT_FOUND |
| Insufficient permissions | 403 | FORBIDDEN |

---

## QA Pair

Your outputs will be reviewed by: **QA-AUTH-001**

---

## Output Format

When complete, confirm:
```
AGENT: DEV-AUTH-001
STATUS: COMPLETE
OUTPUTS:
  - backend/app/services/auth_service.py (XXX lines)
  - backend/app/services/user_service.py (XXX lines)
  - backend/app/middleware/auth.py (XXX lines)
  - backend/app/middleware/permissions.py (XXX lines)
  - backend/app/api/routes/auth.py (XXX lines)
NOTES: [Any implementation notes]
```

---

**Begin execution.**
