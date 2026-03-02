# Security Architecture

**Last Updated:** 2026-01-15
**Related Documents:**
- [System Architecture](./SYSTEM_ARCHITECTURE.md)
- [API Design](./API_DESIGN.md)
- [Infrastructure](./INFRASTRUCTURE.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Security Layers](#security-layers)
3. [Authentication](#authentication)
4. [Authorization](#authorization)
5. [Data Protection](#data-protection)
6. [File Upload Security](#file-upload-security)
7. [API Security](#api-security)
8. [Infrastructure Security](#infrastructure-security)
9. [Audit Trail](#audit-trail)
10. [Compliance and Best Practices](#compliance-and-best-practices)
11. [Related Documentation](#related-documentation)

---

## Overview

The PDP Automation v.3 system implements a **defense-in-depth security strategy** with multiple layers of protection. Security is enforced at every level from network infrastructure to application code to data storage.

**Security Goals:**
1. **Authentication** - Verify user identity via Google OAuth
2. **Authorization** - Control access based on roles and permissions
3. **Data Protection** - Encrypt data at rest and in transit
4. **Input Validation** - Prevent injection attacks and malicious uploads
5. **Audit Trail** - Track all actions for compliance and forensics
6. **Rate Limiting** - Prevent abuse and DoS attacks
7. **Secret Management** - Secure storage of API keys and credentials

---

## Security Layers

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Network Security                               │
│ - HTTPS/TLS 1.2+                                       │
│ - Cloud Armor WAF                                       │
│ - DDoS protection                                       │
│ - CORS restrictions                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Authentication                                 │
│ - Google OAuth 2.0                                     │
│ - Domain restriction (@your-domain.com)                         │
│ - JWT tokens (1 hour expiry)                           │
│ - Refresh tokens (7 days)                              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Authorization                                  │
│ - Role-based access control (RBAC)                     │
│ - Resource ownership checks                             │
│ - Admin-only operations                                 │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Input Validation                               │
│ - Pydantic schema validation                            │
│ - File type/size validation                             │
│ - SQL injection prevention                              │
│ - XSS prevention                                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Data Protection                                │
│ - Encrypted at rest (AES-256)                          │
│ - Encrypted in transit (TLS)                            │
│ - Secrets in Secret Manager                             │
│ - No plaintext credentials                              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 6: Audit Trail                                    │
│ - All actions logged with user ID                       │
│ - IP address tracking                                   │
│ - Sensitive operations logged separately                │
│ - 90-day retention                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Authentication

### Google OAuth 2.0

**Why Google OAuth?**
- Users already have Google Workspace accounts (@your-domain.com)
- No password management needed
- MFA handled by Google
- Easy domain restriction
- Profile photos/names auto-populated

### Authentication Flow

```
User clicks "Sign in with Google"
  │
  ▼
Frontend redirects to Google OAuth consent screen
  │
  ▼
User approves access
  │
  ▼
Google redirects back with authorization code
  │
  ▼
Frontend exchanges code for Google token
  │
  ▼
Frontend sends Google token to backend
  │
  ▼
Backend verifies token with Google
  │
  ├─ Invalid token → 401 Unauthorized
  │
  ├─ Domain not @your-domain.com → 403 Forbidden
  │
  └─ Valid token
     │
     ▼
Backend checks if user exists in database
  │
  ├─ User exists → Load user profile
  │
  └─ New user → Create user record
     │
     ▼
Backend generates JWT access token (1 hour expiry)
Backend generates refresh token (7 days expiry)
  │
  ▼
Return tokens and user profile to frontend
  │
  ▼
Frontend stores tokens in memory (not localStorage)
Frontend includes JWT in Authorization header for all requests
```

### JWT Token Structure

**Access Token (1 hour expiry):**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@your-domain.com",
  "name": "John Doe",
  "role": "user",
  "exp": 1642240800,
  "iat": 1642237200
}
```

**Signing:**
- Algorithm: HS256 (HMAC with SHA-256)
- Secret: Stored in Google Secret Manager
- Key rotation: Every 90 days

### Token Validation

**Backend Middleware:**
```python
# app/middleware/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user_id = payload.get("sub")
    user = await db.users.get(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive"
        )

    return user
```

### Token Refresh

**Endpoint:** `POST /api/auth/refresh`

```python
# app/api/routes/auth.py
@router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_REFRESH_SECRET,
            algorithms=["HS256"]
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    user = await db.users.get(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive"
        )

    # Generate new access token
    access_token = create_access_token(user)

    return {"access_token": access_token}
```

---

## Authorization

### Role-Based Access Control (RBAC)

**Roles:**

| Role | Permissions |
|------|-------------|
| **user** | - Create projects<br>- View own projects<br>- Update own projects<br>- Submit for approval<br>- View shared projects |
| **admin** | - All user permissions<br>- View all projects<br>- Approve/reject projects<br>- Delete projects<br>- Manage users<br>- Manage prompts<br>- Manage templates |

### Permission Decorators

```python
# app/middleware/permissions.py
from functools import wraps
from fastapi import HTTPException

def require_role(role: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User, **kwargs):
            if current_user.role != role and current_user.role != "admin":
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires {role} role"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_admin(func):
    @wraps(func)
    async def wrapper(*args, current_user: User, **kwargs):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper

def require_owner_or_admin(func):
    @wraps(func)
    async def wrapper(*args, project_id: str, current_user: User, **kwargs):
        project = await db.projects.get(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this project"
            )

        return await func(*args, project_id=project_id, current_user=current_user, **kwargs)
    return wrapper
```

### Usage Example

```python
# app/api/routes/projects.py
@router.delete("/projects/{project_id}")
@require_admin
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    await project_service.delete_project(project_id)
    return {"message": "Project deleted"}

@router.put("/projects/{project_id}")
@require_owner_or_admin
async def update_project(
    project_id: str,
    updates: ProjectUpdate,
    current_user: User = Depends(get_current_user)
):
    project = await project_service.update_project(project_id, updates, current_user)
    return project
```

---

## Data Protection

### Encryption at Rest

**Database (Neon PostgreSQL):**
- AES-256 encryption for all data at rest
- Managed by Neon (automatic)
- Encrypted backups

**Cloud Storage (GCS):**
- Server-side encryption with Google-managed keys
- AES-256 encryption
- No action required (default)

**Secrets (Secret Manager):**
- AES-256 encryption
- Access logged and audited
- Version history for key rotation

### Encryption in Transit

**HTTPS/TLS:**
- TLS 1.2+ required
- Strict Transport Security (HSTS) headers
- HTTP to HTTPS redirect

**API Calls:**
```python
# app/main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["pdp-automation.com", "*.pdp-automation.com"]
)

# Add security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

### Secret Management

**Google Secret Manager:**

```python
# app/config/settings.py
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/YOUR-GCP-PROJECT-ID/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Load secrets at startup
ANTHROPIC_API_KEY = get_secret("anthropic-api-key")
JWT_SECRET = get_secret("jwt-secret")
JWT_REFRESH_SECRET = get_secret("jwt-refresh-secret")
DATABASE_URL = get_secret("database-url")
```

**Secrets Stored:**
- `anthropic-api-key` - Anthropic API key
- `jwt-secret` - JWT signing secret
- `jwt-refresh-secret` - Refresh token signing secret
- `database-url` - Neon PostgreSQL connection string
- `google-oauth-client-secret` - Google OAuth client secret

**Key Rotation:**
- Rotate secrets every 90 days
- Old secrets kept for 7 days for rollback
- Version history maintained

---

## File Upload Security

### Multi-Layer Validation

```python
# app/services/upload_service.py
from fastapi import UploadFile, HTTPException
import magic
import io

async def validate_pdf_upload(file: UploadFile) -> bytes:
    # 1. Check file extension
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # 2. Read file content
    content = await file.read()

    # 3. Check file size (50MB limit)
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large (max 50MB)"
        )

    # 4. Check MIME type
    mime = magic.from_buffer(content, mime=True)
    if mime != 'application/pdf':
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {mime}. Expected application/pdf"
        )

    # 5. Check magic bytes (PDF header)
    if not content.startswith(b'%PDF-'):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file (missing PDF header)"
        )

    # 6. Check if encrypted
    if b'/Encrypt' in content:
        raise HTTPException(
            status_code=400,
            detail="Encrypted PDFs are not supported"
        )

    # 7. Virus scanning (future: ClamAV integration)
    # await scan_for_viruses(content)

    return content
```

### Secure File Storage

**Upload to GCS:**
```python
# app/services/storage_service.py
from google.cloud import storage
import uuid

async def upload_pdf(file_content: bytes, job_id: str) -> str:
    client = storage.Client()
    bucket = client.bucket("pdp-automation-assets-dev")

    # Generate unique blob path
    blob_path = f"pdfs/{job_id}/original.pdf"
    blob = bucket.blob(blob_path)

    # Set metadata
    blob.metadata = {
        "uploaded_at": datetime.utcnow().isoformat(),
        "job_id": job_id,
        "content_type": "application/pdf"
    }

    # Upload with content type
    blob.upload_from_string(
        file_content,
        content_type="application/pdf"
    )

    # Return public URL (signed URL for temporary access)
    return blob.public_url
```

### File Access Control

**Signed URLs for Temporary Access:**
```python
# Generate signed URL (expires in 1 hour)
def generate_signed_url(blob_path: str, expiration_minutes: int = 60) -> str:
    client = storage.Client()
    bucket = client.bucket("pdp-automation-assets-dev")
    blob = bucket.blob(blob_path)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method="GET"
    )

    return url
```

---

## API Security

### Input Validation with Pydantic

```python
# app/models/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    developer: Optional[str] = Field(None, max_length=255)
    starting_price: Optional[Decimal] = Field(None, gt=0)

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v

    @validator('starting_price')
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Starting price must be positive')
        return v
```

### SQL Injection Prevention

**Parameterized Queries:**
```python
# ✅ SAFE - Parameterized query
async def get_projects_by_developer(developer: str):
    query = "SELECT * FROM projects WHERE developer = :developer"
    return await db.fetch_all(query, {"developer": developer})

# ❌ UNSAFE - String concatenation
async def get_projects_by_developer_unsafe(developer: str):
    query = f"SELECT * FROM projects WHERE developer = '{developer}'"
    return await db.fetch_all(query)
```

**SQLAlchemy ORM (Automatic Parameterization):**
```python
# app/repositories/project_repository.py
from sqlalchemy import select

async def get_projects_by_developer(developer: str):
    stmt = select(Project).where(Project.developer == developer)
    result = await db.execute(stmt)
    return result.scalars().all()
```

### XSS Prevention

**Output Sanitization:**
```python
# app/utils/sanitize.py
import bleach

def sanitize_html(text: str) -> str:
    # Allow no HTML tags (strip all)
    return bleach.clean(text, tags=[], strip=True)

def sanitize_markdown(text: str) -> str:
    # Allow safe markdown
    return bleach.clean(
        text,
        tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li'],
        strip=True
    )
```

### CSRF Protection

**CSRF Tokens for State-Changing Operations:**
```python
# app/middleware/csrf.py
from fastapi import HTTPException, Header

async def verify_csrf_token(
    x_csrf_token: str = Header(None)
):
    if not x_csrf_token:
        raise HTTPException(
            status_code=403,
            detail="CSRF token missing"
        )

    # Verify token against session
    if not verify_token(x_csrf_token):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )
```

### Rate Limiting

**Per-User Request Quotas:**
```python
# app/middleware/rate_limit.py
from fastapi import HTTPException
from redis import asyncio as aioredis
import time

redis_client = aioredis.from_url(settings.REDIS_URL)

async def rate_limit(user_id: str, limit: int, window: int):
    key = f"rate_limit:{user_id}"

    # Get current count
    count = await redis_client.get(key)

    if count is None:
        # First request in window
        await redis_client.setex(key, window, 1)
        return

    count = int(count)

    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(window)}
        )

    # Increment count
    await redis_client.incr(key)

# Usage
@router.post("/upload")
async def upload_pdf(
    file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    await rate_limit(
        current_user.id,
        limit=100 if current_user.role == "user" else 500,
        window=3600  # 1 hour
    )

    # Process upload
    ...
```

**Rate Limits:**

| Role | Requests per Hour | Upload Rate |
|------|-------------------|-------------|
| User | 100 | 5 uploads/hour |
| Admin | 500 | 20 uploads/hour |

---

## Infrastructure Security

### Cloud Armor WAF

**Protection Against:**
- SQL injection
- XSS attacks
- CSRF attacks
- DDoS attacks
- Bot traffic

**Configuration:**
```yaml
# cloud-armor-policy.yaml
name: pdp-automation-waf-policy
rules:
  - priority: 1000
    description: "Rate limit per IP"
    match:
      expr: "origin.region_code != 'AE' && origin.region_code != 'US'"
    action: "rate_based_ban"
    rateLimitOptions:
      conformAction: "allow"
      exceedAction: "deny-429"
      enforceOnKey: "IP"
      rateLimitThreshold:
        count: 100
        intervalSec: 60

  - priority: 2000
    description: "Block SQL injection"
    match:
      expr: "request.path.matches('(?i)(\\'|\\\"|(--)|;|\\|\\||\\band\\b|\\bor\\b)')"
    action: "deny-403"
```

### Network Security

**CORS Configuration:**
```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pdp-automation.com",
        "https://pdp-automation-dev.web.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)
```

### Service Account Permissions

**Cloud Run Service Account:**
```
pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com
```

**IAM Roles:**
- `roles/cloudsql.client` - Database access
- `roles/storage.objectAdmin` - GCS read/write
- `roles/secretmanager.secretAccessor` - Secret access
- `roles/cloudtasks.enqueuer` - Queue tasks
- `roles/logging.logWriter` - Write logs

**Principle of Least Privilege:**
- Service account has minimal required permissions
- No owner or editor roles
- Scoped to specific resources

---

## Audit Trail

### Execution History

**All actions logged:**
```python
# app/services/audit_service.py
async def log_action(
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: str,
    ip_address: str,
    details: dict
):
    await db.execution_history.create({
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details,
        "created_at": datetime.utcnow()
    })

# Usage
@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    await project_service.delete_project(project_id)

    # Log action
    await audit_service.log_action(
        action="project.deleted",
        entity_type="project",
        entity_id=project_id,
        user_id=current_user.id,
        ip_address=request.client.host,
        details={"project_id": project_id}
    )

    return {"message": "Project deleted"}
```

### Sensitive Operations

**Extra logging for:**
- User login/logout
- Project deletion
- Data export
- Permission changes
- Prompt updates

**Retention:**
- Regular logs: 90 days
- Audit logs: 7 years (compliance)
- Sensitive operations: Permanent

---

## Compliance and Best Practices

### OWASP Top 10 Mitigation

| Risk | Mitigation |
|------|------------|
| A01:2021 - Broken Access Control | RBAC, ownership checks, JWT validation |
| A02:2021 - Cryptographic Failures | TLS 1.2+, AES-256 encryption, Secret Manager |
| A03:2021 - Injection | Parameterized queries, Pydantic validation |
| A04:2021 - Insecure Design | Secure by default, defense in depth |
| A05:2021 - Security Misconfiguration | Secure defaults, automated scanning |
| A06:2021 - Vulnerable Components | Dependabot alerts, regular updates |
| A07:2021 - Authentication Failures | Google OAuth, MFA, JWT expiry |
| A08:2021 - Data Integrity Failures | HTTPS, CSRF tokens, signed URLs |
| A09:2021 - Logging Failures | Comprehensive logging, Sentry errors |
| A10:2021 - SSRF | Input validation, allowlist domains |

### Security Best Practices

1. **Never log sensitive data** (passwords, tokens, API keys)
2. **Use environment variables** for configuration
3. **Validate all inputs** at API boundary
4. **Sanitize all outputs** before rendering
5. **Use HTTPS everywhere** (no HTTP)
6. **Rotate secrets regularly** (90 days)
7. **Monitor for anomalies** (unusual traffic, failed logins)
8. **Keep dependencies updated** (automated scanning)
9. **Perform regular security audits** (quarterly)
10. **Have an incident response plan** (documented)

---

## Related Documentation

- [System Architecture](./SYSTEM_ARCHITECTURE.md) - Overall system design
- [Infrastructure](./INFRASTRUCTURE.md) - Google Cloud components
- [API Design](./API_DESIGN.md) - API security patterns

---

**Last Updated:** 2026-01-15
