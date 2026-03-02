# Handoff Record: DEV-AUTH-001 -> DEV-API-001

**Handoff ID:** HO-AUTH-API-001
**Date:** 2026-01-26
**From Agent:** DEV-AUTH-001 (Authentication)
**To Agent:** DEV-API-001 (API Routes)

---

## Handoff Summary

Authentication middleware and dependencies delivered for use across all protected API routes.

---

## Delivered Artifacts

### 1. Authentication Middleware

**File:** `backend/app/middleware/auth.py`

```python
class AuthenticationMiddleware:
    """JWT validation and user injection middleware."""

    async def __call__(self, request: Request, call_next):
        # Extracts JWT from Authorization header
        # Validates token and injects user into request.state
        # Handles token expiry and invalid tokens
```

**Key Features:**
- JWT extraction from Bearer token
- Token validation with signature verification
- User injection into request state
- Graceful handling of invalid/expired tokens

### 2. API Dependencies

**File:** `backend/app/api/dependencies.py`

```python
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Get current authenticated user from request."""
    # Returns user from request.state
    # Raises 401 if not authenticated

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify admin role."""
    # Raises 403 if user is not admin

async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    # For endpoints that work with or without auth
```

### 3. Auth Routes (Reference)

**File:** `backend/app/api/routes/auth.py`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /auth/google/login | GET | No | Start OAuth flow |
| /auth/google/callback | GET | No | OAuth callback |
| /auth/refresh | POST | No | Refresh access token |
| /auth/logout | POST | Yes | Logout and revoke tokens |
| /auth/me | GET | Yes | Get current user info |

### 4. Permissions Middleware

**File:** `backend/app/middleware/permissions.py`

```python
def require_role(required_role: UserRole):
    """Decorator to require specific role."""
    # Use: @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])

def require_any_role(roles: List[UserRole]):
    """Decorator to require any of specified roles."""
```

---

## Usage Examples

### Protected Endpoint (Authenticated User Required)

```python
from app.api.dependencies import get_current_user
from app.models.database import User

@router.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    # current_user is guaranteed to be authenticated
    # Access user.id, user.email, user.role
    return await service.create_project(project_data, current_user.id)
```

### Admin-Only Endpoint

```python
from app.api.dependencies import get_current_admin

@router.delete("/projects/{id}")
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_admin)
):
    # Only users with role=UserRole.ADMIN can access
    return await service.delete_project(project_id, current_user.id)
```

### Optional Authentication

```python
from app.api.dependencies import get_optional_user

@router.get("/projects/statistics")
async def get_statistics(
    current_user: Optional[User] = Depends(get_optional_user)
):
    # Works for both authenticated and anonymous users
    # current_user is None if not authenticated
    return await service.get_statistics()
```

---

## Configuration Required

From `backend/app/config/settings.py`:

| Setting | Purpose |
|---------|---------|
| JWT_SECRET | Token signing key |
| JWT_ALGORITHM | HS256 |
| JWT_EXPIRY_HOURS | Access token lifetime (default: 1) |
| REFRESH_TOKEN_EXPIRY_DAYS | Refresh token lifetime (default: 7) |

---

## Error Responses

| Status | Description | When |
|--------|-------------|------|
| 401 Unauthorized | Missing or invalid token | No/expired/invalid JWT |
| 403 Forbidden | Insufficient permissions | User lacks required role |

**Error Response Format:**

```json
{
    "detail": "Not authenticated"
}
```

```json
{
    "detail": "Admin role required"
}
```

---

## Testing Authentication

### Get Test Token (Development)

```bash
# Start OAuth flow
curl http://localhost:8000/api/v1/auth/google/login

# After OAuth callback, you'll receive:
{
    "access_token": "eyJhbG...",
    "refresh_token": "abc123...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### Use Token in Requests

```bash
curl -H "Authorization: Bearer eyJhbG..." \
     http://localhost:8000/api/v1/projects
```

---

## Acceptance Confirmation

| Check | Status |
|-------|--------|
| get_current_user dependency works | VERIFIED |
| get_current_admin dependency works | VERIFIED |
| get_optional_user dependency works | VERIFIED |
| 401 on missing token | VERIFIED |
| 403 on insufficient role | VERIFIED |
| Token refresh flow works | VERIFIED |
| Logout revokes tokens | VERIFIED |

---

## Next Steps for DEV-API-001

1. Apply `get_current_user` dependency to all protected endpoints
2. Apply `get_current_admin` dependency to admin-only endpoints
3. Use `get_optional_user` for public endpoints that enhance for auth users
4. Handle 401/403 appropriately in frontend error handling

---

**Handoff Completed:** 2026-01-26
**Accepted By:** DEV-API-001
