# Backend Security Audit Report

**Application:** PDP Automation v.3 - FastAPI Backend
**Auditor:** Security Audit Agent
**Date:** 2026-01-29
**Branch:** `feature/phase-11-pymupdf4llm-integration`
**Scope:** All backend API routes, middleware, services, and configuration

---

## Executive Summary

**Overall Risk Level: HIGH**

This audit identified **19 findings** across the backend codebase. Three are P0 (critical) -- live secrets committed to the `.env` file staged in git, a hardcoded fallback API key for internal endpoints, and the OAuth state parameter being optional which disables CSRF protection. Several P1 findings include SQL injection via unsanitized `ilike`, rate limiting bypassed via `X-Forwarded-For` spoofing, unauthenticated read endpoints exposing project data, and error messages leaking internal details in production.

| Severity | Count |
|----------|-------|
| P0 (Critical) | 3 |
| P1 (High) | 8 |
| P2 (Medium) | 5 |
| P3 (Low) | 3 |

---

## Findings

---

## Finding: Live Secrets Committed to Version Control

- **Severity:** P0
- **File:** `backend/.env` (staged in git index)
- **Description:** The `.env` file containing production-grade secrets is staged in the git index. While `.gitignore` lists `.env`, the file was explicitly added with `git add` and appears in the staged files (`AM backend/.env` in `git status`). This means the JWT secret, Google OAuth client secret, and Anthropic API key are all committed and will be pushed to any remote. These secrets are live and usable.
- **Evidence:**
```
# From backend/.env (staged in git)
JWT_SECRET=9385baa421883ff77b5f54c320ce1033e81145c6e81f09db825e16068a2281a1
GOOGLE_CLIENT_SECRET=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
ANTHROPIC_API_KEY=REDACTED_ANTHROPIC_KEY
DATABASE_URL=postgresql+asyncpg://pdpuser:localdevpassword@localhost:5432/pdp_automation
```
- **Fix:**
  1. Run `git rm --cached backend/.env` to unstage the file.
  2. Rotate ALL secrets immediately: JWT_SECRET, GOOGLE_CLIENT_SECRET, ANTHROPIC_API_KEY, database password.
  3. If this branch has been pushed to a remote, use `git filter-branch` or `bfg` to purge the file from history.
  4. Add a pre-commit hook that blocks `.env` files from being staged.

---

## Finding: Hardcoded Internal API Key Fallback

- **Severity:** P0
- **File:** `backend/app/api/routes/internal.py:50`
- **Description:** The internal endpoint authentication uses `getattr(settings, 'INTERNAL_API_KEY', 'development-key')` which falls back to the hardcoded string `'development-key'` when the `INTERNAL_API_KEY` setting is not configured. Since `INTERNAL_API_KEY` is not defined in the `Settings` class or `.env` file, this fallback is ALWAYS used. Any attacker who sends `X-Internal-Auth: development-key` can trigger job processing.
- **Evidence:**
```python
# backend/app/api/routes/internal.py:50
expected_key = getattr(settings, 'INTERNAL_API_KEY', 'development-key')

if x_internal_auth != expected_key:
    # ...
```
The `Settings` class in `backend/app/config/settings.py` has no `INTERNAL_API_KEY` field, so `getattr` always returns the default.
- **Fix:**
  1. Add `INTERNAL_API_KEY: str = Field(..., description="Internal API authentication key")` to the `Settings` class (required field, no default).
  2. Add a strong random value to `.env`: `INTERNAL_API_KEY=<openssl rand -hex 32 output>`.
  3. Remove the hardcoded fallback entirely.

---

## Finding: OAuth State Parameter is Optional -- CSRF Protection Disabled

- **Severity:** P0
- **File:** `backend/app/api/routes/auth.py:48,176`
- **Description:** The `state` field in `GoogleAuthRequest` is `Optional` with a default of `None`. The `/auth/google` endpoint only validates state "if provided" (`if request_body.state`). This means an attacker can omit the state parameter entirely and bypass CSRF protection during the OAuth flow, enabling login CSRF attacks.
- **Evidence:**
```python
# backend/app/api/routes/auth.py:48
class GoogleAuthRequest(BaseModel):
    code: str = Field(..., description="Google OAuth authorization code")
    state: Optional[str] = Field(None, description="OAuth state parameter for CSRF protection")

# backend/app/api/routes/auth.py:176
if request_body.state:
    await auth_service.validate_oauth_state(db, request_body.state)
```
- **Fix:** Make `state` required and always validate it:
```python
class GoogleAuthRequest(BaseModel):
    code: str = Field(..., description="Google OAuth authorization code")
    state: str = Field(..., description="OAuth state parameter for CSRF protection")

# In google_auth endpoint:
await auth_service.validate_oauth_state(db, request_body.state)
```

---

## Finding: SQL Injection via Unsanitized ilike Search Parameter

- **Severity:** P1
- **File:** `backend/app/api/routes/prompts.py:128`
- **Description:** The `search` query parameter is interpolated directly into an `ilike` clause using f-string formatting. While SQLAlchemy parameterizes the value, the `%` wildcards wrapping the search term allow users to craft LIKE patterns that can be used for data extraction or denial of service (e.g., `%_%_%_%_%_%` patterns that cause exponential backtracking on large text columns). More critically, special SQL LIKE characters (`%`, `_`) are not escaped, allowing unintended pattern matching.
- **Evidence:**
```python
# backend/app/api/routes/prompts.py:128
if search:
    query = query.where(Prompt.name.ilike(f"%{search}%"))
```
- **Fix:** Escape LIKE special characters before interpolation:
```python
if search:
    escaped = search.replace("%", "\\%").replace("_", "\\_")
    query = query.where(Prompt.name.ilike(f"%{escaped}%"))
```

---

## Finding: Rate Limiting Bypassed via X-Forwarded-For Header Spoofing

- **Severity:** P1
- **File:** `backend/app/middleware/rate_limit.py:166-168` and `backend/app/api/routes/auth.py:103-105`
- **Description:** Both the rate limiter and the auth route blindly trust the `X-Forwarded-For` header to determine client IP. An attacker can set this header to any value, rotating IPs per request to completely bypass rate limiting. The rate limiter uses IP as the key for unauthenticated requests, so auth endpoints (login, token exchange) have no effective rate limiting.
- **Evidence:**
```python
# backend/app/middleware/rate_limit.py:166-168
forwarded = request.headers.get("X-Forwarded-For")
if forwarded:
    ip = forwarded.split(",")[0].strip()

# backend/app/api/routes/auth.py:103-105
forwarded = request.headers.get("X-Forwarded-For")
if forwarded:
    return forwarded.split(",")[0].strip()
```
- **Fix:**
  1. Only trust `X-Forwarded-For` when running behind a known reverse proxy. Add a `TRUSTED_PROXIES` setting.
  2. In production behind Cloud Run/GCR, use the last hop IP or a verified header like `X-Cloud-Trace-Context`.
  3. As an interim fix, use `request.client.host` as the primary source and only fall back to `X-Forwarded-For` if `request.client.host` is in `TRUSTED_PROXIES`.

---

## Finding: Multiple Project Routes Missing Authentication

- **Severity:** P1
- **File:** `backend/app/api/routes/projects.py:49,152,184,211,247`
- **Description:** Five project endpoints have NO authentication dependency: `list_projects`, `search_projects`, `get_statistics`, `get_recent_activity`, and `export_projects`. Any anonymous user can list all projects, search them, view statistics, and export project data. The `get_project` endpoint (line 300) and `get_project_history` (line 405) are also unauthenticated, exposing individual project details and revision history.
- **Evidence:**
```python
# backend/app/api/routes/projects.py:49-66 -- no Depends(get_current_user)
@router.get("", response_model=ProjectListResponse)
async def list_projects(
    search: str | None = Query(None, ...),
    ...
    service: ProjectService = Depends(get_project_service)
):

# Same pattern for /search, /statistics, /activity, /export,
# /{project_id}, /{project_id}/history
```
- **Fix:** Add `current_user: User = Depends(get_current_user)` to all project endpoints that should require authentication.

---

## Finding: Error Responses Leak Internal Details in Production

- **Severity:** P1
- **File:** `backend/app/api/routes/projects.py:113,145,332,366,401` and `backend/app/api/routes/internal.py:185`
- **Description:** Multiple endpoints pass raw exception messages into HTTP response details using `str(e)`. In production, this can expose internal implementation details including database table names, SQL errors, file paths, and stack trace information to attackers.
- **Evidence:**
```python
# backend/app/api/routes/projects.py:113
detail=f"Failed to list projects: {str(e)}"

# backend/app/api/routes/projects.py:145
detail=f"Failed to create project: {str(e)}"

# backend/app/api/routes/internal.py:185
detail=f"Internal error processing job: {str(e)}"
```
- **Fix:** Return generic error messages in responses and log the actual error server-side:
```python
except Exception as e:
    logger.exception(f"Failed to list projects: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An internal error occurred"
    )
```

---

## Finding: File Upload Path Traversal via Filename

- **Severity:** P1
- **File:** `backend/app/api/routes/upload.py:65,218-219`
- **Description:** The uploaded filename is used directly in two places without sanitization: (1) `tempfile.mkstemp(suffix=os.path.splitext(file.filename or "")[1])` uses the file extension from the user-supplied filename, and (2) the Cloud Storage destination path uses the original filename: `f"{current_user.id}/{file.filename}"`. A malicious filename like `../../etc/passwd` or `file.pdf\x00.exe` could potentially be used for path traversal in Cloud Storage or null-byte injection in the temp file suffix.
- **Evidence:**
```python
# backend/app/api/routes/upload.py:65
temp_fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename or "")[1])

# backend/app/api/routes/upload.py:218-219
pdf_url = await storage_service.upload_file(
    source_file=temp_path,
    destination_blob_path=f"{current_user.id}/{file.filename}",
    content_type="application/pdf"
)
```
- **Fix:** Sanitize filenames before use:
```python
import re
import uuid

def sanitize_filename(filename: str) -> str:
    """Remove path separators and dangerous characters."""
    # Strip directory components
    name = os.path.basename(filename)
    # Allow only alphanumeric, dash, underscore, dot
    name = re.sub(r'[^\w\-.]', '_', name)
    # Prevent empty or dot-only names
    if not name or name.startswith('.'):
        name = f"upload_{uuid.uuid4().hex[:8]}"
    return name
```

---

## Finding: Content Type Validation Relies on Client-Supplied Header

- **Severity:** P1
- **File:** `backend/app/api/routes/upload.py:183,340`
- **Description:** File type validation checks `file.content_type` which is set by the client's HTTP request, not by inspecting the actual file content. An attacker can upload any file type (e.g., an executable or HTML file with XSS) by simply setting the `Content-Type` header to `application/pdf`.
- **Evidence:**
```python
# backend/app/api/routes/upload.py:183
if file.content_type not in ALLOWED_PDF_TYPES:
    raise HTTPException(...)

# backend/app/api/routes/upload.py:340
if file.content_type not in ALLOWED_IMAGE_TYPES:
    ...
```
- **Fix:** Validate the actual file content using magic bytes:
```python
import magic  # python-magic

async def validate_file_type(temp_path: str, allowed_mimes: list[str]) -> str:
    """Validate file type by reading magic bytes."""
    detected = magic.from_file(temp_path, mime=True)
    if detected not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail=f"File type mismatch: header says PDF but content is {detected}"
        )
    return detected
```

---

## Finding: Redundant and Conflicting JWT Libraries

- **Severity:** P1
- **File:** `backend/requirements.txt:17-19`
- **Description:** The requirements install both `pyjwt==2.10.1` AND `python-jose[cryptography]==3.3.0`. These are two different JWT libraries that can conflict. `python-jose` 3.3.0 has known vulnerabilities (CVE-2024-33663 and CVE-2024-33664 -- algorithm confusion attacks allowing token forgery). The actual code uses `import jwt` (PyJWT), but `python-jose` is still installed and could be imported accidentally or exploited through dependency confusion.
- **Evidence:**
```
# backend/requirements.txt
pyjwt==2.10.1
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
```
- **Fix:**
  1. Remove `python-jose[cryptography]==3.3.0` from requirements.txt since the code uses `pyjwt`.
  2. Verify no imports reference `jose` anywhere in the codebase.

---

## Finding: No JWT Token Revocation / Blacklisting

- **Severity:** P2
- **File:** `backend/app/services/auth_service.py:282-307`
- **Description:** JWT access tokens cannot be revoked before expiration. If a user's account is compromised or deactivated, their existing access tokens remain valid until expiry (1 hour). The `verify_token` method only checks the signature and expiration -- it does not check if the token has been revoked or if the user is still active. While the auth middleware (`get_current_user`) does check `user.is_active`, the per-request database lookup is the only protection.
- **Evidence:**
```python
# backend/app/services/auth_service.py:295-307
def verify_token(self, token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            self.jwt_secret,
            algorithms=[self.jwt_algorithm]
        )
        return payload  # No revocation check, no DB lookup
```
- **Fix:** Implement a token blacklist (Redis-backed for production) or reduce JWT expiry to 15 minutes and rely on refresh token rotation. Alternatively, include `jti` checks against a revocation list on the `/logout/all` path.

---

## Finding: In-Memory Rate Limiter Does Not Work Across Workers

- **Severity:** P2
- **File:** `backend/app/middleware/rate_limit.py:27-98`
- **Description:** The rate limiter uses an in-memory dictionary (`defaultdict(list)`) scoped to a single process. If the application runs with multiple workers (the `Settings` class supports `WORKERS > 1`), each worker has its own independent rate limit store. An attacker can simply rotate requests across workers to multiply effective limits. The code even acknowledges this with a comment: "For production with multiple workers, use Redis instead."
- **Evidence:**
```python
# backend/app/middleware/rate_limit.py:27-36
class RateLimitStore:
    """
    In-memory rate limit store with sliding window.
    For production with multiple workers, use Redis instead.
    """
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
```
- **Fix:** Replace with Redis-backed rate limiting using a library like `slowapi` or a custom Redis implementation before deploying to production with multiple workers.

---

## Finding: Auth Rate Limits Too Permissive

- **Severity:** P2
- **File:** `backend/app/middleware/rate_limit.py:103-106`
- **Description:** Authentication endpoints allow 20 attempts per minute for login and token exchange. Combined with the `X-Forwarded-For` spoofing vulnerability, this effectively provides no brute-force protection. Even without IP spoofing, 20 attempts/minute is excessively permissive for OAuth code exchange.
- **Evidence:**
```python
# backend/app/middleware/rate_limit.py:103-106
RATE_LIMITS = {
    "/api/v1/auth/google": (20, 60),      # 20 attempts per minute
    "/api/v1/auth/refresh": (30, 60),     # 30 refreshes per minute
    "/api/v1/auth/login": (20, 60),       # 20 login URL requests per minute
```
The comment says "increased from 5/10 for dev workflow."
- **Fix:** Reduce auth rate limits to 5-10 per minute for production. Use exponential backoff (increasing delay after failed attempts). Implement account lockout after N consecutive failures.

---

## Finding: Refresh Token Cookie Missing Domain and Path Restrictions

- **Severity:** P2
- **File:** `backend/app/api/routes/auth.py:202-209`
- **Description:** The refresh token cookie is set without `domain` or `path` restrictions. Without a `path` restriction, the cookie is sent with every request to the domain, not just auth endpoints. The `secure` flag is only set in production (`settings.is_production`), meaning in development the cookie is transmitted over HTTP in cleartext.
- **Evidence:**
```python
# backend/app/api/routes/auth.py:202-209
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=settings.is_production,
    samesite="lax",
    max_age=settings.REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60,
)
```
- **Fix:** Add `path="/api/v1/auth"` to restrict cookie scope. Add an explicit `domain` setting. Consider always setting `secure=True` even in development (use HTTPS in dev too).

---

## Finding: OAuth URL Encoding Lacks Proper Escaping

- **Severity:** P2
- **File:** `backend/app/services/auth_service.py:156-157`
- **Description:** The OAuth URL is built using simple string concatenation without URL-encoding parameter values. If any parameter contains special characters (particularly the `redirect_uri` or `state`), the URL will be malformed and potentially exploitable via open redirect.
- **Evidence:**
```python
# backend/app/services/auth_service.py:156-157
query = "&".join(f"{k}={v}" for k, v in params.items())
return f"{self.auth_uri}?{query}"
```
- **Fix:** Use `urllib.parse.urlencode` for proper URL encoding:
```python
from urllib.parse import urlencode
query = urlencode(params)
return f"{self.auth_uri}?{query}"
```

---

## Finding: Open Redirect via Custom redirect_uri Parameter

- **Severity:** P1
- **File:** `backend/app/api/routes/auth.py:121,135`
- **Description:** The `/auth/login` endpoint accepts a `redirect_uri` query parameter from the user which is used directly in the OAuth flow. An attacker can supply any URL (e.g., `https://evil.com/steal-token`) as the redirect URI, potentially capturing OAuth authorization codes. The redirect URI is stored in the database `OAuthState` table but is never validated against a whitelist.
- **Evidence:**
```python
# backend/app/api/routes/auth.py:121,135
async def get_oauth_login_url(
    redirect_uri: Optional[str] = None,
    ...
):
    final_redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
    state = await auth_service.create_oauth_state(db, final_redirect_uri)
    oauth_url = auth_service.get_oauth_url(state, final_redirect_uri)
```
- **Fix:** Validate `redirect_uri` against a whitelist of allowed URIs:
```python
ALLOWED_REDIRECT_URIS = {settings.GOOGLE_REDIRECT_URI}

if redirect_uri and redirect_uri not in ALLOWED_REDIRECT_URIS:
    raise HTTPException(
        status_code=400,
        detail="Invalid redirect URI"
    )
```

---

## Finding: dependencies_temp.py Referenced in Git Status but Does Not Exist

- **Severity:** P3
- **File:** `backend/app/api/dependencies_temp.py`
- **Description:** The git status shows `dependencies_temp.py` as modified (` M backend/app/api/dependencies_temp.py`), but the file does not exist on disk. This suggests it was deleted but the deletion was not staged, or it is a git tracking artifact. The filename itself ("temp dependencies") suggests this file may have contained insecure shortcuts (e.g., a no-op auth dependency that bypasses authentication during development). The file should be formally removed and its history reviewed.
- **Evidence:**
```
# From git status:
 M backend/app/api/dependencies_temp.py

# File read attempt: File does not exist.
```
- **Fix:**
  1. Run `git rm backend/app/api/dependencies_temp.py` if it is tracked.
  2. Review git history for this file to ensure no insecure auth bypasses were used.
  3. Search the codebase for any imports of `dependencies_temp` to ensure nothing references it.

---

## Finding: /config/info Endpoint Protected Only by DEBUG Flag

- **Severity:** P3
- **File:** `backend/app/main.py:135-161`
- **Description:** The `/config/info` endpoint returns configuration details including GCP project ID, GCS bucket name, allowed origins, and feature flags. Protection relies solely on the `DEBUG` flag, with no authentication required. If `DEBUG=true` is accidentally left enabled in production (which the `.env` currently has), this configuration information is publicly accessible.
- **Evidence:**
```python
# backend/app/main.py:135-141
@app.get("/config/info")
async def config_info():
    if not settings.DEBUG:
        return JSONResponse(
            status_code=403,
            content={"error": "Configuration info only available in debug mode"}
        )
    # Returns GCP project, bucket, model, features...
```
- **Fix:** Add authentication to the endpoint AND check the debug flag:
```python
@app.get("/config/info")
async def config_info(current_user: User = Depends(get_current_admin)):
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Not available")
    ...
```

---

## Finding: Internal Health Endpoint Has No Authentication

- **Severity:** P3
- **File:** `backend/app/api/routes/internal.py:189-197`
- **Description:** The `/api/v1/internal/health` endpoint is accessible without any authentication. While health endpoints are commonly unauthenticated, this one is under the `/internal` prefix which suggests it should not be publicly accessible. It confirms the existence and reachability of the internal service, which is useful for reconnaissance.
- **Evidence:**
```python
# backend/app/api/routes/internal.py:189-197
@router.get("/health")
async def internal_health():
    """
    Internal health check endpoint.
    Used by Cloud Tasks to verify the service is reachable.
    Does not require authentication.
    """
    return {"status": "ok", "service": "pdp-automation-internal"}
```
- **Fix:** If this endpoint is only for Cloud Tasks, protect it with the same `verify_internal_auth` dependency, or restrict access at the network/firewall level. Alternatively, move it to a separate port not exposed publicly.

---

## Checklist Coverage Summary

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | JWT secret strength and rotation | PARTIAL | 32-byte secret validated at startup; no rotation mechanism |
| 2 | OAuth state parameter (CSRF) | FAIL | State is optional -- P0 finding |
| 3 | Token expiration and refresh flow | PASS | 1hr access, 7-day refresh, rotation on use, hashed storage |
| 4 | CORS allowed origins | PASS | No wildcard; configured per-environment |
| 5 | Rate limiting bypasses | FAIL | X-Forwarded-For spoofing -- P1 finding |
| 6 | File upload validation | PARTIAL | Size limits good; content-type client-trusted; filename not sanitized |
| 7 | Internal endpoint auth | FAIL | Hardcoded fallback key -- P0 finding |
| 8 | SQL injection | PARTIAL | SQLAlchemy ORM used throughout; ilike injection via search -- P1 finding |
| 9 | Secrets in code/logs | FAIL | Live secrets in staged .env -- P0 finding |
| 10 | Missing authentication | FAIL | 7 project endpoints unauthenticated -- P1 finding |
| 11 | Missing authorization | PASS | Role checks present on admin-only endpoints |
| 12 | Input validation (Pydantic) | PASS | All request bodies use Pydantic models with Field validation |
| 13 | Error response leakage | FAIL | str(e) in responses -- P1 finding |
| 14 | SSRF risks | LOW RISK | OAuth redirect_uri accepts arbitrary URLs -- P1 finding |
| 15 | Dependency vulnerabilities | FAIL | python-jose 3.3.0 has known CVEs -- P1 finding |

---

## Files Reviewed

| File | Status |
|------|--------|
| `backend/app/api/routes/auth.py` | Reviewed |
| `backend/app/services/auth_service.py` | Reviewed |
| `backend/app/middleware/rate_limit.py` | Reviewed |
| `backend/app/api/routes/upload.py` | Reviewed |
| `backend/app/api/routes/internal.py` | Reviewed |
| `backend/app/config/settings.py` | Reviewed |
| `backend/app/main.py` | Reviewed |
| `backend/app/api/dependencies_temp.py` | Does not exist (finding logged) |
| `backend/app/middleware/auth.py` | Reviewed |
| `backend/app/middleware/permissions.py` | Reviewed |
| `backend/app/config/secrets.py` | Reviewed |
| `backend/app/api/dependencies.py` | Reviewed |
| `backend/app/api/routes/projects.py` | Reviewed |
| `backend/app/api/routes/jobs.py` | Reviewed |
| `backend/app/api/routes/prompts.py` | Reviewed |
| `backend/app/api/routes/content.py` | Reviewed |
| `backend/app/api/routes/qa.py` | Reviewed |
| `backend/app/api/routes/workflow.py` | Reviewed |
| `backend/app/api/routes/templates.py` | Reviewed |
| `backend/app/models/database.py` | Reviewed |
| `backend/requirements.txt` | Reviewed |
| `backend/.env` | Reviewed |
| `backend/.env.example` | Reviewed |
| `.gitignore` | Reviewed |

---

## Recommended Remediation Priority

1. **Immediate (before next deploy):**
   - Unstage `.env` from git and rotate all secrets (P0)
   - Add `INTERNAL_API_KEY` as required setting, remove hardcoded fallback (P0)
   - Make OAuth `state` parameter required (P0)

2. **This sprint:**
   - Add authentication to unauthenticated project endpoints (P1)
   - Sanitize filenames in upload routes (P1)
   - Fix error message leakage (P1)
   - Remove `python-jose` from requirements (P1)
   - Validate `redirect_uri` against whitelist (P1)
   - Escape LIKE wildcards in search (P1)
   - Fix rate limiter IP trust (P1)
   - Add magic-byte file type validation (P1)

3. **Next sprint:**
   - Implement Redis-backed rate limiting (P2)
   - Add JWT revocation/blacklist mechanism (P2)
   - Restrict refresh token cookie path (P2)
   - Fix OAuth URL encoding (P2)
   - Tighten auth rate limits (P2)

4. **Backlog:**
   - Clean up `dependencies_temp.py` from git tracking (P3)
   - Add auth to `/config/info` endpoint (P3)
   - Restrict internal health endpoint (P3)
