# Handoff Record: DEV-DB-001 -> DEV-AUTH-001

**Handoff ID:** HO-DB-AUTH-001
**Date:** 2026-01-26
**From Agent:** DEV-DB-001 (Database Schema)
**To Agent:** DEV-AUTH-001 (Authentication)

---

## Handoff Summary

Database models required for authentication have been delivered and are ready for use by DEV-AUTH-001.

---

## Delivered Artifacts

### 1. User Model

**File:** `backend/app/models/database.py`
**Lines:** 59-115

```python
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUID]
    google_id: Mapped[str]           # Google OAuth subject ID
    email: Mapped[str]               # @your-domain.com domain enforced
    name: Mapped[str]
    picture_url: Mapped[Optional[str]]
    role: Mapped[UserRole]           # admin, user
    is_active: Mapped[bool]          # Account status
    last_login_at: Mapped[Optional[datetime]]
```

**Key Features:**
- google_id uniquely identifies user from Google OAuth
- email domain constrained to @your-domain.com
- role supports admin and user
- is_active for account suspension
- last_login_at for audit trail

### 2. RefreshToken Model

**File:** `backend/app/models/database.py`
**Lines:** 118-164

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID]
    user_id: Mapped[UUID]            # FK to users
    token_hash: Mapped[str]          # SHA256 hash of token
    expires_at: Mapped[datetime]
    is_revoked: Mapped[bool]
    revoked_at: Mapped[Optional[datetime]]
    ip_address: Mapped[Optional[str]]
    user_agent: Mapped[Optional[str]]
```

**Key Features:**
- Stores hashed tokens (not plaintext)
- Tracks revocation status
- Captures client context (IP, user agent)
- Links to User via FK

### 3. OAuthState Model

**File:** `backend/app/models/database.py`
**Lines:** 167-204

```python
class OAuthState(Base):
    __tablename__ = "oauth_states"

    id: Mapped[UUID]
    state: Mapped[str]               # CSRF token
    redirect_uri: Mapped[str]
    expires_at: Mapped[datetime]
    used: Mapped[bool]
    used_at: Mapped[Optional[datetime]]
```

**Key Features:**
- State parameter for CSRF protection
- Single-use enforcement
- Expiration tracking

### 4. UserRole Enum

**File:** `backend/app/models/enums.py`
**Lines:** 25-30

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
```

---

## Database Constraints

| Table | Constraint | Description |
|-------|------------|-------------|
| users | check_email_domain | `email ~ '@mpd\.ae$'` |
| users | check_user_role | `role IN ('admin', 'user')` |
| users | unique_google_id | Google ID unique |
| users | unique_email | Email unique |

---

## Indexes Available

| Table | Index | Columns |
|-------|-------|---------|
| users | idx_users_email | email |
| users | idx_users_google_id | google_id |
| users | idx_users_role | role |
| refresh_tokens | idx_refresh_tokens_user_id | user_id |
| refresh_tokens | idx_refresh_tokens_token_hash | token_hash |

---

## Migration Status

**File:** `backend/alembic/versions/001_initial_schema.py`
**Status:** Ready to run

Tables created in migration:
- users (lines 34-55)
- refresh_tokens (not in initial - added in separate migration)
- oauth_states (not in initial - added in separate migration)

Note: RefreshToken and OAuthState were added as additional auth tables beyond the original 22-table spec.

---

## Usage Example

```python
from app.models.database import User, RefreshToken, OAuthState
from app.models.enums import UserRole
from app.config import get_db_session

async def create_user(google_id: str, email: str, name: str) -> User:
    async with get_db_context() as db:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            role=UserRole.USER,
            is_active=True
        )
        db.add(user)
        await db.commit()
        return user
```

---

## Configuration Provided

From DEV-CONFIG-001:

| Setting | Purpose |
|---------|---------|
| JWT_SECRET | Token signing key |
| JWT_ALGORITHM | HS256 |
| JWT_EXPIRY_HOURS | Access token lifetime |
| REFRESH_TOKEN_EXPIRY_DAYS | Refresh token lifetime |
| GOOGLE_CLIENT_ID | OAuth client ID |
| GOOGLE_CLIENT_SECRET | OAuth client secret |

---

## Acceptance Confirmation

| Check | Status |
|-------|--------|
| User model accessible | VERIFIED |
| RefreshToken model accessible | VERIFIED |
| OAuthState model accessible | VERIFIED |
| UserRole enum accessible | VERIFIED |
| Email constraint working | VERIFIED |
| Indexes present | VERIFIED |
| Migration ready | VERIFIED |

---

## Next Steps for DEV-AUTH-001

1. Implement `auth_service.py` with:
   - Google OAuth token exchange
   - JWT generation/validation
   - Refresh token rotation

2. Implement `middleware/auth.py` with:
   - get_current_user dependency
   - Permission decorators

3. Implement `api/routes/auth.py` with:
   - /auth/login
   - /auth/google
   - /auth/refresh
   - /auth/logout

---

**Handoff Completed:** 2026-01-26
**Accepted By:** DEV-AUTH-001
