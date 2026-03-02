# Integration Tests for PDP Automation v.3 Backend API

This directory contains HTTP-level integration tests for all FastAPI routes.

## Test Files

1. **test_auth_routes.py** - Authentication endpoints (`/api/v1/auth/*`)
   - Tests for `/auth/me`, `/auth/logout`, `/auth/logout/all`
   - Verifies JWT authentication and user info retrieval

2. **test_project_routes.py** - Project management endpoints (`/api/v1/projects/*`)
   - Tests CRUD operations, filtering, pagination
   - Tests access control (admin vs regular users)

3. **test_job_routes.py** - Background job endpoints (`/api/v1/jobs/*`)
   - Tests job creation, listing, status tracking
   - Tests job cancellation and step details

4. **test_upload_routes.py** - File upload endpoints (`/api/v1/upload/*`)
   - Tests PDF upload with validation (file type, size, path traversal)
   - Tests filename sanitization

5. **test_prompt_routes.py** - Prompt management endpoints (`/api/v1/prompts/*`)
   - Tests prompt CRUD operations
   - Tests admin-only access control
   - Tests versioning

## Running Tests

Run all integration tests:
```bash
cd backend
python -m pytest tests/integration/ -v
```

Run specific test file:
```bash
python -m pytest tests/integration/test_auth_routes.py -v
```

Run tests without auth (fastest):
```bash
python -m pytest tests/integration/ -k "without_auth" -v
```

## Test Infrastructure

Tests use fixtures from `tests/conftest.py`:

- **test_engine** - Async SQLite in-memory database with all tables created
- **test_db** - AsyncSession with automatic rollback after each test
- **client** - httpx AsyncClient with database dependency override
- **test_user / admin_user / manager_user** - User model instances with roles
- **auth_headers / admin_headers / manager_headers** - JWT Bearer token headers

## Test Coverage

Current status: **22/65 tests passing** (33.8%)

Passing tests:
- All "without auth" tests (verify 403 status for missing credentials)
- All "invalid token" tests (verify 401 for bad tokens)

Known issues:
- Tests requiring database interaction with user fixtures need the test_engine fixture to be properly scoped
- SQLite compatibility for PostgreSQL-specific features handled in conftest.py

## Auth Behavior Notes

- Missing Authorization header: **403 Forbidden** (HTTPBearer default)
- Invalid/expired token: **401 Unauthorized**
- Valid token, insufficient permissions: **403 Forbidden**

This matches FastAPI's HTTPBearer security scheme behavior.
