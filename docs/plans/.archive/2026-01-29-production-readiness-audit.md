# Production Readiness Audit - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Systematically audit the entire PDP Automation v.3 codebase (backend + frontend) for security vulnerabilities, code quality issues, missing error handling, and production readiness gaps -- then fix every finding.

**Architecture:** Multi-agent parallel audit across 8 tracks. Each track produces a findings file. A consolidation phase merges findings into a prioritized fix list. Fix tasks are then executed in priority order (P0 security > P1 correctness > P2 robustness > P3 quality).

**Tech Stack:** FastAPI 0.115.6, SQLAlchemy 2.0 async, React 19, TypeScript 5.9, PostgreSQL 16, Docker, Google Cloud, Anthropic SDK

**Methodology:** superpowers:systematic-debugging applied to each finding -- observe, hypothesize, verify, fix, confirm.

---

## Phase 1: Parallel Audit (8 tracks, run concurrently)

Each task outputs a findings file to `docs/audit/`. Agents should READ the actual source files, not guess. Every finding must include: file path, line number(s), severity (P0/P1/P2/P3), description, and proposed fix.

---

### Task 1: Backend Security Audit

**Output:** `docs/audit/01-backend-security.md`

**Files to review:**
- `backend/app/api/routes/auth.py` - OAuth flow, token endpoints
- `backend/app/services/auth_service.py` - JWT creation, validation, password hashing
- `backend/app/middleware/auth.py` - Token extraction, validation middleware
- `backend/app/middleware/permissions.py` - Role-based access control
- `backend/app/middleware/rate_limit.py` - Rate limiting implementation
- `backend/app/api/routes/upload.py` - File upload validation
- `backend/app/api/routes/internal.py` - Internal callback endpoints
- `backend/app/config/settings.py` - Secret management, default values
- `backend/app/config/secrets.py` - GCP Secret Manager integration
- `backend/app/main.py` - CORS config, middleware ordering

**Checklist:**
- [ ] JWT secret strength and rotation strategy
- [ ] OAuth state parameter validation (CSRF protection)
- [ ] Token expiration and refresh flow correctness
- [ ] CORS allowed origins -- no wildcard in production
- [ ] Rate limiting bypasses (IP spoofing via headers)
- [ ] File upload: type validation, size limits, filename sanitization, path traversal
- [ ] Internal endpoints: authentication/authorization on callback routes
- [ ] SQL injection via raw queries or string interpolation in SQLAlchemy
- [ ] Secrets in code, logs, or error responses
- [ ] Missing authentication on any route
- [ ] Missing authorization checks (role enforcement)
- [ ] Input validation on all request bodies (Pydantic models)
- [ ] Error responses leaking stack traces or internal details
- [ ] SSRF risks in any URL-accepting endpoints
- [ ] Dependency vulnerabilities (check `requirements.txt` versions)

**Step 1:** Read each file listed above thoroughly.

**Step 2:** For each checklist item, document findings with exact line numbers.

**Step 3:** Write findings to `docs/audit/01-backend-security.md` in this format:
```markdown
## Finding: [Title]
- **Severity:** P0/P1/P2/P3
- **File:** `path/to/file.py:LINE`
- **Description:** What's wrong
- **Evidence:** Code snippet showing the issue
- **Fix:** Exact code change needed
```

---

### Task 2: Backend API & Route Correctness

**Output:** `docs/audit/02-backend-routes.md`

**Files to review:**
- `backend/app/api/routes/auth.py`
- `backend/app/api/routes/jobs.py`
- `backend/app/api/routes/projects.py`
- `backend/app/api/routes/upload.py`
- `backend/app/api/routes/content.py`
- `backend/app/api/routes/qa.py`
- `backend/app/api/routes/prompts.py`
- `backend/app/api/routes/templates.py`
- `backend/app/api/routes/workflow.py`
- `backend/app/api/routes/internal.py`
- `backend/app/api/dependencies.py`
- `backend/app/api/dependencies_temp.py`
- `backend/app/models/schemas.py` (Pydantic request/response models)

**Checklist:**
- [ ] Every route has proper HTTP status codes (201 for create, 204 for delete, 404 for not found)
- [ ] Every route has proper error handling (try/except with appropriate HTTP exceptions)
- [ ] Request body validation via Pydantic models (no raw dict access)
- [ ] Response models defined and consistent (no leaking internal fields)
- [ ] Pagination on list endpoints (offset/limit or cursor-based)
- [ ] Proper use of dependency injection (get_db, get_current_user)
- [ ] No business logic in route handlers (delegated to services)
- [ ] Path parameter validation (UUID format)
- [ ] Query parameter validation and defaults
- [ ] `dependencies_temp.py` -- what is this? Should it exist in production?
- [ ] Route prefix consistency (`/api/v1/...`)
- [ ] OpenAPI schema correctness (tags, descriptions, examples)

---

### Task 3: Backend Service Layer Audit

**Output:** `docs/audit/03-backend-services.md`

**Files to review:**
- `backend/app/services/job_manager.py` - Job lifecycle, retry logic
- `backend/app/services/pdf_processor.py` - PDF extraction pipeline (if exists, or `backend/app/utils/pdf_helpers.py`)
- `backend/app/services/data_extractor.py` - Regex-based extraction
- `backend/app/services/data_structurer.py` - Claude-based structuring
- `backend/app/services/content_generator.py` - Content generation with Claude
- `backend/app/services/content_qa_service.py` - Content validation
- `backend/app/services/sheets_manager.py` - Google Sheets integration
- `backend/app/services/storage_service.py` - GCS operations
- `backend/app/services/prompt_manager.py` - Prompt CRUD and versioning
- `backend/app/services/auth_service.py` - Auth business logic
- `backend/app/services/floor_plan_extractor.py` - Floor plan processing
- `backend/app/integrations/anthropic_client.py` - Claude API wrapper
- `backend/app/integrations/drive_client.py` - Google Drive wrapper
- `backend/app/background/task_queue.py` - Cloud Tasks integration
- `backend/app/utils/pdf_helpers.py` - PDF utilities
- `backend/app/utils/token_counter.py` - Token counting

**Checklist:**
- [ ] Every service method has proper error handling (no bare except, no swallowed errors)
- [ ] Async/await correctness (no blocking calls in async functions)
- [ ] Database session management (proper commit/rollback/close patterns)
- [ ] External API calls: timeout configuration, retry with backoff, error handling
- [ ] Anthropic client: token limit handling, rate limit handling, model validation
- [ ] Google Sheets: batch update correctness, rate limiting, error recovery
- [ ] File I/O: temp file cleanup, memory management for large PDFs
- [ ] Job manager: state machine correctness, race condition handling
- [ ] Data extractor: regex robustness, edge cases
- [ ] Content generator: prompt injection prevention
- [ ] Storage service: signed URL expiration, bucket permissions
- [ ] Logging: sufficient context for debugging, no PII in logs

---

### Task 4: Database & Schema Audit

**Output:** `docs/audit/04-database-schema.md`

**Files to review:**
- `backend/app/models/database.py` - All 22 ORM models
- `backend/app/models/enums.py` - All enum definitions
- `backend/app/models/schemas.py` - Pydantic schemas
- `backend/alembic/versions/001_initial_schema.py`
- `backend/alembic/versions/002_add_auth_tables.py`
- `backend/alembic/versions/003_enum_column_types.py`
- `backend/app/config/database.py` - Connection configuration
- `backend/app/repositories/` - All repository files

**Checklist:**
- [ ] ORM models match Alembic migrations (no drift)
- [ ] All foreign keys have proper ON DELETE behavior (CASCADE vs SET NULL vs RESTRICT)
- [ ] Indexes cover all common query patterns (check route handlers for query patterns)
- [ ] JSONB fields have appropriate defaults
- [ ] Enum values in code match database check constraints
- [ ] No N+1 query patterns in repositories (check for eager loading)
- [ ] Connection pool configuration (pool_size, max_overflow, pool_timeout)
- [ ] Database session lifecycle (scoped correctly per request)
- [ ] Missing unique constraints (e.g., one active prompt per type+variant+name)
- [ ] Nullable fields that should be NOT NULL
- [ ] Missing indexes on frequently filtered columns
- [ ] Soft delete implementation consistency (is_active on which tables?)

---

### Task 5: Frontend Security & Auth Audit

**Output:** `docs/audit/05-frontend-security.md`

**Files to review:**
- `frontend/src/lib/auth.ts` - OAuth flow
- `frontend/src/lib/api.ts` - Axios client, interceptors
- `frontend/src/stores/auth-store.ts` - Auth state management
- `frontend/src/hooks/use-auth.ts` - Auth hook
- `frontend/src/components/auth/ProtectedRoute.tsx`
- `frontend/src/components/auth/AdminRoute.tsx`
- `frontend/src/components/auth/ManagerRoute.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/AuthCallbackPage.tsx`
- `frontend/src/router/index.tsx` - Route definitions

**Checklist:**
- [ ] Token storage mechanism (localStorage vs httpOnly cookies) -- localStorage is vulnerable to XSS
- [ ] Token included in all API requests via interceptor
- [ ] Token refresh on 401 response (automatic retry)
- [ ] Logout clears all auth state and tokens
- [ ] OAuth callback validates state parameter
- [ ] Protected routes redirect to login when unauthenticated
- [ ] Role-based route protection actually works (AdminRoute, ManagerRoute)
- [ ] No sensitive data in browser console/logs
- [ ] XSS: dangerouslySetInnerHTML usage, unescaped user input rendering
- [ ] CSRF protection (if using cookies)
- [ ] API base URL configuration (no hardcoded localhost in production)

---

### Task 6: Frontend Code Quality Audit

**Output:** `docs/audit/06-frontend-quality.md`

**Files to review:**
- `frontend/src/types/index.ts` - TypeScript interfaces
- `frontend/src/hooks/queries/` - All React Query hooks
- `frontend/src/stores/` - All Zustand stores
- `frontend/src/components/common/` - Shared components
- `frontend/src/components/projects/` - Project components
- `frontend/src/components/prompts/` - Prompt components
- `frontend/src/components/qa/` - QA components
- `frontend/src/components/upload/` - Upload components
- `frontend/src/components/workflow/` - Workflow components
- `frontend/src/components/layout/` - Layout components
- `frontend/src/pages/` - All 19 page components
- `frontend/src/App.tsx` - Root component
- `frontend/src/lib/query-client.ts` - React Query config
- `frontend/src/lib/utils.ts` - Utility functions

**Checklist:**
- [ ] TypeScript types match backend API responses (no `any` types)
- [ ] React Query hooks: proper cache keys, stale times, error handling
- [ ] Error boundaries at appropriate levels (not just root)
- [ ] Loading states for all async operations
- [ ] Empty states for lists with no data
- [ ] Form validation with Zod schemas matching backend constraints
- [ ] Proper cleanup in useEffect hooks (abort controllers, unsubscribe)
- [ ] No memory leaks (event listeners, intervals, subscriptions)
- [ ] Accessibility: aria labels, keyboard navigation, focus management
- [ ] Responsive design: mobile breakpoints, touch targets
- [ ] Bundle size: unnecessary imports, tree-shaking issues
- [ ] Console errors or warnings in development
- [ ] Dead code: unused components, hooks, or types

---

### Task 7: Infrastructure & DevOps Audit

**Output:** `docs/audit/07-infrastructure.md`

**Files to review:**
- `backend/Dockerfile` - Backend Docker build
- `frontend/Dockerfile` - Frontend Docker build
- `docker-compose.dev.yml` - Local dev environment
- `.github/workflows/ci.yml` - CI/CD pipeline
- `frontend/nginx.conf` - Nginx configuration
- `frontend/vite.config.ts` - Vite build config
- `backend/app/config/settings.py` - Environment config
- `.dockerignore` files
- `.gitignore` (check if exists)

**Checklist:**
- [ ] Docker: multi-stage build correctness, no dev deps in production
- [ ] Docker: non-root user in production images
- [ ] Docker: healthcheck endpoints configured
- [ ] Docker: no secrets baked into images
- [ ] Docker Compose: proper service dependencies, healthchecks
- [ ] Nginx: security headers (X-Frame-Options, CSP, HSTS, etc.)
- [ ] Nginx: rate limiting, request size limits
- [ ] Nginx: proper proxy_pass to backend
- [ ] CI/CD: all checks run (lint, type-check, test, build)
- [ ] CI/CD: no secrets in workflow files
- [ ] Vite: production source maps disabled
- [ ] Environment variables: all required vars documented
- [ ] `.gitignore`: .env, node_modules, __pycache__, .coverage, dist/
- [ ] No committed dist/ files or build artifacts

---

### Task 8: Test Coverage Audit

**Output:** `docs/audit/08-test-coverage.md`

**Files to review:**
- `backend/tests/` - All test files
- `backend/tests/services/` - Service tests
- Check for `frontend/src/**/*.test.ts` or `frontend/src/**/*.spec.ts`

**Checklist:**
- [ ] Every API route has at least one happy path test
- [ ] Every API route has error case tests (400, 401, 403, 404)
- [ ] Every service has unit tests with mocked dependencies
- [ ] Integration tests for critical paths (upload -> process -> generate -> publish)
- [ ] Auth flow tested end-to-end (login, token refresh, logout)
- [ ] Database model tests (CRUD operations, constraints, cascading deletes)
- [ ] Frontend: any tests at all? (likely missing based on no test script in package.json)
- [ ] Test fixtures and factories for common data
- [ ] Async test patterns correct (pytest-asyncio configuration)
- [ ] Mocking patterns consistent and correct
- [ ] Missing test categories identified with priority

---

## Phase 2: Consolidation

### Task 9: Merge Audit Findings

**Files:**
- Read: `docs/audit/01-backend-security.md` through `docs/audit/08-test-coverage.md`
- Create: `docs/audit/00-master-findings.md`

**Step 1:** Read all 8 audit reports.

**Step 2:** Deduplicate findings that appear across multiple tracks.

**Step 3:** Create master findings list sorted by priority:
```markdown
# Master Audit Findings

## P0 - Security (fix immediately)
1. [Finding title] - [Source audit track] - [File:Line]

## P1 - Correctness (fix before shipping)
1. ...

## P2 - Robustness (fix for production readiness)
1. ...

## P3 - Quality (fix for maintainability)
1. ...

## Summary
- Total findings: N
- P0: N, P1: N, P2: N, P3: N
- Estimated fix tasks: N
```

**Step 4:** For each finding, include the exact fix (code change) from the original audit report.

---

## Phase 3: Fix Implementation

Fixes are executed in priority order. Each fix task follows TDD where applicable (write test, verify fail, implement fix, verify pass, commit).

### Task 10: Fix P0 Security Issues

**Prereq:** Task 9 complete.

**Step 1:** Read `docs/audit/00-master-findings.md`, extract all P0 items.

**Step 2:** For each P0 finding, apply the systematic-debugging approach:
1. **Observe:** Read the problematic code, confirm the issue exists
2. **Hypothesize:** Confirm the proposed fix is correct
3. **Fix:** Apply the code change
4. **Verify:** Run relevant tests, confirm fix works and doesn't break anything

**Step 3:** After all P0 fixes, run full backend test suite:
```bash
cd backend && python -m pytest tests/ -v --tb=short
```

**Step 4:** Commit P0 fixes:
```bash
git add -A
git commit -m "fix(security): resolve P0 security audit findings"
```

---

### Task 11: Fix P1 Correctness Issues

**Prereq:** Task 10 complete.

**Step 1:** Read `docs/audit/00-master-findings.md`, extract all P1 items.

**Step 2:** For each P1 finding:
1. Read the code, confirm issue
2. Write a test that exposes the bug (if testable)
3. Apply the fix
4. Run the test, confirm pass

**Step 3:** Run full test suite.

**Step 4:** Commit:
```bash
git add -A
git commit -m "fix(correctness): resolve P1 correctness audit findings"
```

---

### Task 12: Fix P2 Robustness Issues

**Prereq:** Task 11 complete.

**Step 1:** Read `docs/audit/00-master-findings.md`, extract all P2 items.

**Step 2:** Apply fixes following the same observe-hypothesize-fix-verify pattern.

**Step 3:** Run full test suite.

**Step 4:** Commit:
```bash
git add -A
git commit -m "fix(robustness): resolve P2 robustness audit findings"
```

---

### Task 13: Fix P3 Quality Issues

**Prereq:** Task 12 complete.

**Step 1:** Read `docs/audit/00-master-findings.md`, extract all P3 items.

**Step 2:** Apply fixes.

**Step 3:** Run linters and formatters:
```bash
cd backend && ruff check . --fix && ruff format .
cd frontend && npx eslint . --fix && npx prettier --write src/
```

**Step 4:** Run full test suites.

**Step 5:** Commit:
```bash
git add -A
git commit -m "refactor(quality): resolve P3 quality audit findings"
```

---

## Phase 4: Verification

### Task 14: Final Verification Pass

**Prereq:** Tasks 10-13 complete.

**Step 1:** Run backend test suite with coverage:
```bash
cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

**Step 2:** Run backend linters:
```bash
cd backend && ruff check . && ruff format --check .
```

**Step 3:** Build frontend:
```bash
cd frontend && npm run build
```

**Step 4:** Run frontend lint:
```bash
cd frontend && npx eslint .
```

**Step 5:** Verify Docker builds:
```bash
docker build -f backend/Dockerfile -t pdp-backend-test backend/
docker build -f frontend/Dockerfile -t pdp-frontend-test frontend/
```

**Step 6:** Write final verification report to `docs/audit/FINAL-VERIFICATION.md`:
```markdown
# Final Verification Report

## Test Results
- Backend tests: PASS/FAIL (X/Y passed)
- Backend coverage: X%
- Backend lint: PASS/FAIL
- Frontend build: PASS/FAIL
- Frontend lint: PASS/FAIL
- Docker build (backend): PASS/FAIL
- Docker build (frontend): PASS/FAIL

## Remaining Issues
- [Any issues that could not be fixed]

## Production Readiness Assessment
- [GO/NO-GO with justification]
```

---

## Execution Notes

**Phase 1 (Tasks 1-8):** All 8 audit tasks are independent and MUST run in parallel using superpowers:dispatching-parallel-agents. Each agent reads source files and writes its findings report.

**Phase 2 (Task 9):** Sequential. Reads all 8 reports and consolidates.

**Phase 3 (Tasks 10-13):** Sequential by priority. Each task depends on the previous.

**Phase 4 (Task 14):** Sequential. Final verification after all fixes.

**Total tasks:** 14
**Parallelizable:** Tasks 1-8 (Phase 1)
**Sequential:** Tasks 9-14 (Phases 2-4)
