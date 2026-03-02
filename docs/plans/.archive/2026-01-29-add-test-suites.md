# Add Frontend + Backend Test Suites

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish test infrastructure and write meaningful tests for both frontend (Vitest) and backend (pytest API integration tests).

**Architecture:** Frontend uses Vitest + Testing Library with jsdom. Backend uses pytest-asyncio + httpx AsyncClient with in-memory SQLite for isolation.

**Tech Stack:** Vitest 3.x, @testing-library/react, jsdom, pytest-asyncio, httpx, SQLAlchemy async SQLite

---

### Task 1: Frontend Test Infrastructure Setup

**Files:**
- Modify: `frontend/package.json` (add devDependencies + test script)
- Modify: `frontend/vite.config.ts` (add vitest config)
- Modify: `frontend/tsconfig.app.json` (add vitest types)
- Create: `frontend/src/test/setup.ts` (test setup with jest-dom matchers)

**Step 1: Install test dependencies**

Run: `cd frontend && npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @types/testing-library__jest-dom`

**Step 2: Add vitest config to vite.config.ts**

Add test block:
```ts
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: './src/test/setup.ts',
  css: false,
}
```

**Step 3: Create test setup file**

```ts
// frontend/src/test/setup.ts
import '@testing-library/jest-dom/vitest'
```

**Step 4: Update tsconfig.app.json**

Add `"vitest/globals"` to compilerOptions.types array.

**Step 5: Add test script to package.json**

```json
"test": "vitest run",
"test:watch": "vitest",
"test:coverage": "vitest run --coverage"
```

**Step 6: Run vitest to verify setup**

Run: `cd frontend && npx vitest run`
Expected: 0 tests found, no errors

---

### Task 2: Frontend Unit Tests - Auth Utilities

**Files:**
- Create: `frontend/src/lib/__tests__/auth.test.ts`

Test `parseJwt`, `isTokenExpired`, `isTokenExpiringSoon`, `getTokenExpiryMs`, `buildGoogleOAuthUrl`, `clearAuthState`.

Key test cases:
- parseJwt with valid JWT returns decoded payload
- parseJwt with malformed string returns null
- isTokenExpired returns true for expired token
- isTokenExpired returns false for valid token
- isTokenExpired returns true for null/undefined
- isTokenExpiringSoon with token expiring in < 5 min
- buildGoogleOAuthUrl includes state, redirect_uri, client_id params
- clearAuthState removes tokens from sessionStorage

---

### Task 3: Frontend Unit Tests - Auth Store

**Files:**
- Create: `frontend/src/stores/__tests__/auth-store.test.ts`

Test zustand auth store: login sets user+token, logout clears state, isAuthenticated derivation, sessionStorage persistence.

Key test cases:
- Initial state has no user, no token, isAuthenticated=false
- login() sets user and token, isAuthenticated becomes true
- logout() clears user and token, isAuthenticated becomes false
- updateUser() merges user fields
- State persists to sessionStorage

---

### Task 4: Frontend Unit Tests - useAuth Hook

**Files:**
- Create: `frontend/src/hooks/__tests__/use-auth.test.ts`

Test the useAuth hook: hasRole, hasAnyRole, isAdmin derivation.

Key test cases:
- hasRole('admin') returns true when user.role is 'admin'
- hasRole('manager') returns false when user.role is 'user'
- hasAnyRole(['admin','manager']) returns true if user has either
- isAdmin is true only for admin role

---

### Task 5: Frontend Component Test - ProtectedRoute

**Files:**
- Create: `frontend/src/components/auth/__tests__/ProtectedRoute.test.tsx`

Test that ProtectedRoute redirects unauthenticated users to /login and renders children when authenticated.

Key test cases:
- Renders children when user is authenticated with valid token
- Redirects to /login when not authenticated
- Redirects to /login when token is expired

---

### Task 6: Backend Integration Test Infrastructure

**Files:**
- Create: `backend/tests/conftest.py`
- Modify: `backend/requirements.txt` (add aiosqlite if missing)

Create conftest.py with:
- In-memory async SQLite engine
- AsyncSession fixture with transaction rollback
- FastAPI test app with dependency overrides
- httpx AsyncClient fixture
- Auth helper fixtures (create_test_user, get_auth_headers with real JWT)

**Step 1: Check/install aiosqlite**

Run: `cd backend && pip install aiosqlite`

**Step 2: Create conftest.py**

Key fixtures:
```python
@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    async with AsyncSession(db_engine) as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
def auth_headers():
    # Generate real JWT for test user
    ...
```

---

### Task 7: Backend Integration Tests - Auth Routes

**Files:**
- Create: `backend/tests/integration/test_auth_routes.py`

Test cases:
- GET /api/v1/auth/login returns OAuth URL with state param
- POST /api/v1/auth/google with missing state returns 422
- GET /api/v1/auth/me without auth returns 401
- GET /api/v1/auth/me with valid token returns user
- POST /api/v1/auth/refresh with valid refresh token returns new tokens
- POST /api/v1/auth/logout clears session

---

### Task 8: Backend Integration Tests - Project Routes

**Files:**
- Create: `backend/tests/integration/test_project_routes.py`

Test cases:
- GET /api/v1/projects without auth returns 401
- GET /api/v1/projects with auth returns paginated list
- POST /api/v1/projects creates project
- GET /api/v1/projects/{id} returns project details
- PUT /api/v1/projects/{id} updates project
- DELETE /api/v1/projects/{id} requires admin role
- GET /api/v1/projects/search with query filters results
- GET /api/v1/projects/statistics returns stats

---

### Task 9: Backend Integration Tests - Job Routes

**Files:**
- Create: `backend/tests/integration/test_job_routes.py`

Test cases:
- POST /api/v1/jobs creates a job
- GET /api/v1/jobs lists user's jobs
- GET /api/v1/jobs/{id} returns job details
- PUT /api/v1/jobs/{id}/cancel cancels a pending job
- GET /api/v1/jobs/{id}/steps returns processing steps

---

### Task 10: Backend Integration Tests - Upload Routes

**Files:**
- Create: `backend/tests/integration/test_upload_routes.py`

Test cases:
- POST /api/v1/upload/pdf with valid PDF returns job_id
- POST /api/v1/upload/pdf rejects non-PDF files
- POST /api/v1/upload/pdf rejects files over 50MB
- POST /api/v1/upload/pdf without auth returns 401
- POST /api/v1/upload/pdf sanitizes filename (path traversal attempt)

---

### Task 11: Backend Integration Tests - Prompt Routes

**Files:**
- Create: `backend/tests/integration/test_prompt_routes.py`

Test cases:
- GET /api/v1/prompts lists prompts
- POST /api/v1/prompts requires admin
- POST /api/v1/prompts creates prompt
- GET /api/v1/prompts/{id} returns prompt
- PUT /api/v1/prompts/{id} updates prompt
- GET /api/v1/prompts/{id}/versions returns version history
- GET /api/v1/prompts with search escapes LIKE special chars
