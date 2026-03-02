# 08 - Test Coverage Audit

**Auditor:** Claude Code (Opus 4.5)
**Date:** 2026-01-29
**Scope:** Backend unit/integration tests, frontend test infrastructure, test configuration
**Branch:** `feature/phase-11-pymupdf4llm-integration`

---

## Executive Summary

The backend has **15 test files** containing approximately **12,500+ lines** of test code covering 12 of 19 services and 2 of 2 integration modules. Test quality is generally **excellent** -- tests use proper mocking patterns, class-based organization, async test patterns, edge case coverage, and error path testing. However, there are significant structural gaps: **zero route-level tests** (0/10), **zero frontend tests** (no test framework installed), **no shared conftest.py** for fixtures, and **no database model tests**. Three critical services (job_manager, content_qa_service, prompt_manager) lack dedicated test files, though content_qa_service and prompt_manager are partially tested within `test_content_generator.py`.

| Category | Covered | Total | Coverage |
|---|---|---|---|
| API Route Tests | 0 | 10 | 0% |
| Service Unit Tests | 14 | 19 | 74% |
| Integration Tests | 2 | 2 | 100% |
| Auth Flow Tests | 1 | 1 | 100% |
| DB Model Tests | 0 | 1 | 0% |
| Frontend Tests | 0 | N/A | 0% |
| Config Tests | 1 | 1 | 100% |

**Overall Risk Rating:** HIGH -- API routes and frontend are completely untested.

---

## 1. Test Infrastructure

### 1.1 pytest Configuration (`backend/pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-branch
markers =
    asyncio: mark test as async
    integration: mark test as integration test
    unit: mark test as unit test
asyncio_mode = auto
```

**Assessment:** Well-configured. Uses `--cov=app` for coverage reporting, `--cov-branch` for branch coverage, `--strict-markers` to catch typos in markers, `asyncio_mode = auto` for seamless async test support. The `term-missing` and `html` coverage reports are both enabled.

### 1.2 conftest.py

**Status: MISSING**

No `conftest.py` exists in `backend/tests/`. Each test file independently creates its own fixtures (mock_settings, mock_anthropic_client, etc.), leading to significant duplication across files. At least 8 test files define their own `mock_settings` fixture with near-identical code.

### 1.3 pyproject.toml / setup.cfg

**Status: MISSING**

No `pyproject.toml` or `setup.cfg` exists. Test configuration is entirely in `pytest.ini`, which is functional but limits extensibility.

### 1.4 Frontend Test Infrastructure

**Status: NOT PRESENT**

`frontend/package.json` has no test script (`scripts` contains only `dev`, `build`, `lint`, `preview`). No test framework is installed -- no `vitest`, `jest`, `@testing-library/react`, or similar dependencies. No test files exist anywhere in `frontend/src/`.

---

## 2. Test File Inventory

### 2.1 Backend Test Files

| # | File | Lines | Modules Tested | Quality |
|---|---|---|---|---|
| 1 | `tests/test_anthropic_client.py` | 664 | AnthropicService, token_counter | Excellent |
| 2 | `tests/test_content_generator.py` | 1,276 | ContentGenerator, ContentQAService, PromptManager | Excellent |
| 3 | `tests/test_data_extractor.py` | 1,257 | DataExtractor | Excellent |
| 4 | `tests/test_data_structurer.py` | 1,174 | DataStructurer | Excellent |
| 5 | `tests/services/test_data_structurer.py` | 511 | DataStructurer (validation focus) | Good |
| 6 | `tests/test_drive_client.py` | 1,161 | DriveClient | Excellent |
| 7 | `tests/test_sheets_manager.py` | 1,194 | SheetsManager | Excellent |
| 8 | `tests/test_storage_service.py` | 829 | StorageService | Excellent |
| 9 | `tests/test_pdf_processor.py` | 966 | PDFProcessor, pdf_helpers | Excellent |
| 10 | `tests/test_auth_service.py` | 157 | AuthService | Adequate |
| 11 | `tests/test_config.py` | 238 | Settings, configuration | Good |
| 12 | `tests/test_floor_plan.py` | 982 | FloorPlanExtractor | Excellent |
| 13 | `tests/test_image_classifier.py` | 863 | DeduplicationService, ImageClassifier | Excellent |
| 14 | `tests/test_image_optimizer.py` | 682 | ImageOptimizer, OutputOrganizer | Excellent |
| 15 | `tests/test_watermark.py` | 1,016 | WatermarkDetector, WatermarkRemover | Excellent |

### 2.2 Frontend Test Files

**None.** Zero test files found in `frontend/src/`.

---

## 3. Coverage Matrix

### 3.1 API Routes Coverage

| Route File | Test File | Status |
|---|---|---|
| `routes/auth.py` | -- | NOT TESTED |
| `routes/jobs.py` | -- | NOT TESTED |
| `routes/projects.py` | -- | NOT TESTED |
| `routes/upload.py` | -- | NOT TESTED |
| `routes/content.py` | -- | NOT TESTED |
| `routes/qa.py` | -- | NOT TESTED |
| `routes/prompts.py` | -- | NOT TESTED |
| `routes/templates.py` | -- | NOT TESTED |
| `routes/workflow.py` | -- | NOT TESTED |
| `routes/internal.py` | -- | NOT TESTED |

**0 of 10 routes have any test coverage.** No FastAPI `TestClient` usage, no request/response validation tests, no auth middleware tests at the route level.

### 3.2 Services Coverage

| Service File | Test File | Status | Notes |
|---|---|---|---|
| `data_structurer.py` | `test_data_structurer.py` + `services/test_data_structurer.py` | TESTED | Two test files; comprehensive |
| `data_extractor.py` | `test_data_extractor.py` | TESTED | 1,257 lines; regex extraction thorough |
| `content_generator.py` | `test_content_generator.py` | TESTED | Includes ContentQAService + PromptManager |
| `content_qa_service.py` | `test_content_generator.py` | PARTIAL | Tested within content_generator tests |
| `prompt_manager.py` | `test_content_generator.py` | PARTIAL | Tested within content_generator tests |
| `sheets_manager.py` | `test_sheets_manager.py` | TESTED | 1,194 lines; field mapping, rate limiting |
| `storage_service.py` | `test_storage_service.py` | TESTED | GCS operations with mocked SDK |
| `auth_service.py` | `test_auth_service.py` | TESTED | JWT creation, verification, hashing |
| `floor_plan_extractor.py` | `test_floor_plan.py` | TESTED | Vision OCR, dedup, text fallback |
| `pdf_processor.py` | `test_pdf_processor.py` | TESTED | Triple extraction, pymupdf4llm integration |
| `image_classifier.py` | `test_image_classifier.py` | TESTED | Claude Vision classification |
| `image_optimizer.py` | `test_image_optimizer.py` | TESTED | Batch optimization, ZIP creation |
| `watermark_detector.py` | `test_watermark.py` | TESTED | Detection, batch processing |
| `watermark_remover.py` | `test_watermark.py` | TESTED | Mask creation, quality scoring |
| `deduplication_service.py` | `test_image_classifier.py` | TESTED | pHash, similarity, within classifier tests |
| `output_organizer.py` | `test_image_optimizer.py` | TESTED | Directory structure, within optimizer tests |
| `job_manager.py` | -- | NOT TESTED | Critical gap |
| `user_service.py` | -- | NOT TESTED | |
| `project_service.py` | -- | NOT TESTED | |

### 3.3 Integrations Coverage

| Integration File | Test File | Status | Notes |
|---|---|---|---|
| `integrations/anthropic_client.py` | `test_anthropic_client.py` | TESTED | 664 lines; retry logic, vision, cost tracking |
| `integrations/drive_client.py` | `test_drive_client.py` | TESTED | 1,161 lines; comprehensive GDrive ops |
| `background/task_queue.py` | -- | NOT TESTED | Background job processing untested |

### 3.4 Other Coverage

| Module | Test File | Status |
|---|---|---|
| `app/config.py` | `test_config.py` | TESTED |
| `app/utils/pdf_helpers.py` | `test_pdf_processor.py` | TESTED |
| `app/utils/token_counter.py` | `test_anthropic_client.py` | TESTED |
| `app/models/database.py` | -- | NOT TESTED |
| `app/middleware/rate_limit.py` | -- | NOT TESTED |
| `app/main.py` | -- | NOT TESTED |

---

## 4. Detailed Quality Assessment

### 4.1 test_anthropic_client.py (664 lines) -- Excellent

**Strengths:**
- Proper exception initialization using real `httpx.Response` objects (not bare mocks), avoiding false positives from incorrect mock shapes.
- Helper functions (`create_rate_limit_error`, `create_authentication_error`, etc.) reduce test boilerplate.
- Exponential backoff verification checks delay ranges with jitter: `assert 1.0 <= delays[0] <= 1.5`.
- Session usage tracking across multiple requests verifies cumulative state.
- Tests `temperature=0.0` edge case explicitly (falsy-but-valid value).
- Token counter utilities tested separately with boundary cases.
- Class-based organization: 9 test classes covering initialization, messages, vision, retry, session tracking, close, text tokens, image tokens, cost, formatting.

**Mocking Patterns:**
- `patch("app.integrations.anthropic_client.get_settings")` for settings isolation.
- `AsyncMock` for async API calls with `side_effect` for multi-call scenarios.
- `patch("app.integrations.anthropic_client.asyncio.sleep")` to avoid real delays.

**Edge Cases Covered:**
- Rate limit (429), timeout, 5xx server errors trigger retry.
- Authentication (401), bad request (400), 4xx errors do NOT retry.
- Retry exhaustion after `MAX_RETRIES`.
- Zero tokens, empty/None text input.
- Image scaling for dimension constraints.
- Cost precision at 1M token scale.

### 4.2 test_content_generator.py (1,276 lines) -- Excellent

**Strengths:**
- Tests three distinct services in one file: ContentGenerator, ContentQAService, PromptManager.
- Field-level character limit enforcement with retry-on-over-limit testing.
- Brand compliance checks: prohibited terms ("world-class", "prime location"), incorrect terminology ("flat" vs "apartment").
- SEO scoring: project name presence, meta length optimization, suboptimal length flagging.
- Factual accuracy: mismatched project name/developer/location detection.
- Prompt variable substitution with missing data defaults and list formatting.
- Price formatting across ranges (K, M notation).
- Inter-field delay verification (9 delays for 10 fields).
- Retry constants validated (`MAX_RETRIES == 3`, `RETRY_DELAY_BASE == 1.0`).

**Mocking Patterns:**
- `patch("app.services.content_generator.anthropic.AsyncAnthropic")` with `side_effect` for rate limit/timeout retry chains.
- `nonlocal call_count` pattern for selective failure simulation.
- `patch("app.services.content_generator.asyncio.sleep")` for delay verification.

**Edge Cases Covered:**
- Content exceeding character limits triggers stricter prompt with "CRITICAL" keyword.
- Partial failure in `generate_all` (9 successes + 1 error).
- Missing data defaults ("Unknown Project", "Price on request").
- Rate limit retry success, timeout retry success, all-retries-exhausted exception.

### 4.3 test_data_extractor.py (1,257 lines) -- Excellent

**Strengths:**
- Pure regex extraction with no API mocks needed -- tests are fast and deterministic.
- Real-estate domain expertise reflected in test fixtures (AED pricing, BR formats, UAE locations).
- Every extraction method has dedicated test class: project_name, developer, location, prices, bedrooms, completion_date, amenities, payment_plan, property_type.
- Page context windowing tested with boundary conditions (first page, last page, missing pages, zero window).
- Data class tests verify structure of FieldResult, LocationResult, PriceResult, PaymentPlanResult.
- Constants verified: `UAE_EMIRATES` (7 entries), `DUBAI_COMMUNITIES` (30+ entries), `KNOWN_DEVELOPERS` (10+ entries).

**Edge Cases Covered:**
- Price filtering (outlier removal, per-sqft vs property prices).
- Bedroom format normalization (BR, Bedroom, B/R, Studio).
- Date format variations (Q4 2026, March 2028, year-only).
- Payment plan synonym handling ("reservation" as down payment).
- Multi-word emirates ("Abu Dhabi").
- JVC abbreviation recognition.
- Generic header filtering ("Overview" not treated as project name).
- Page order preservation in `_combine_pages`.

### 4.4 test_data_structurer.py (1,174 lines, root level) -- Excellent

**Strengths:**
- Comprehensive Claude API integration testing with retry logic.
- JSON response parsing with markdown fence cleaning.
- Field validation: negative prices, min > max, bedroom format, property type, floor count, date formats.
- Missing field detection across all 19 schema fields.
- Cost calculation with token-level precision.
- Input truncation testing at `MAX_INPUT_CHARS` boundary.
- FieldConfidence threshold boundary testing (0.69 vs 0.70).
- Type conversion testing (string-to-int, float-to-int).
- Null string conversion ("null", "None" strings to Python None).
- Direct value parsing (without confidence wrapper).

**Mocking Patterns:**
- `patch("app.services.data_structurer.anthropic.AsyncAnthropic")` with `MagicMock` for response shaping.
- `side_effect` lists for retry simulation with `RateLimitError`, `InternalServerError`, `APITimeoutError`.
- Capture callbacks (`async def capture_call`) for prompt inspection.

### 4.5 tests/services/test_data_structurer.py (511 lines) -- Good

**Strengths:**
- Focused on validation logic: confidence scoring, field validation, type conversion, cost calculation.
- Tests validation with realistic property data.
- Covers retry exhaustion, JSON parse error handling, markdown fence cleaning.
- Overall confidence calculation excludes zero scores.

**Note:** Overlaps significantly with root-level `test_data_structurer.py`. The root-level file is more comprehensive (1,174 lines vs 511 lines). Both files import and test the same `DataStructurer` class.

### 4.6 test_drive_client.py (1,161 lines) -- Excellent

**Strengths:**
- 14 test classes covering every DriveClient operation.
- `supportsAllDrives=True` verification across all operations (critical for Shared Drive support).
- Retry logic: 429 rate limit, 5xx server errors, non-retryable 404, max retries.
- Folder traversal: existing paths, not-found paths, `create_if_missing`, empty paths.
- Google Workspace exports: Doc-to-PDF, Sheet-to-CSV, Sheet-to-Excel.
- Pagination handling in folder listing.
- Edge cases: special characters in filenames, quotes, no-parent folders, trailing slashes, empty folders.

### 4.7 test_sheets_manager.py (1,194 lines) -- Excellent

**Strengths:**
- 10+ test classes covering initialization, field mapping, sheet creation, population, validation, sharing, rate limiting.
- All 6 template types tested for sheet creation.
- Rate limiting: backoff calculation formula, retry on 429, exhaustion, timing verification.
- Field mapping returns defensive copy (mutation protection).
- Whitespace stripping in validation, None cell handling, empty dict handling.
- Data class independence verification (separate list instances).
- Exception class hierarchy testing.
- Template accessibility validation (all accessible, partial, all missing).

### 4.8 test_storage_service.py (829 lines) -- Excellent

**Strengths:**
- Complete GCS operation coverage: upload (bytes, path, file-like, metadata), download (bytes, file), signed URLs, delete (file, folder), list, exists, metadata, copy, move.
- Lazy initialization pattern testing (client and bucket properties).
- Resumable upload threshold testing for large files.
- Multi-chunk copy (rewrite token continuation).
- Move operation atomicity (delete not called if copy fails).
- Path builder helpers for upload/temp/processed/image/floor_plan paths.
- Content type auto-detection (PDF, JPG, PNG, ZIP, unknown).
- Error handling for NotFound and GoogleCloudError across all operations.

### 4.9 test_pdf_processor.py (966 lines) -- Excellent

**Strengths:**
- Creates real PDF documents using PyMuPDF (`fitz`) for integration-level testing.
- Triple extraction method: embedded images, page renders, text (pymupdf4llm).
- Image helper tests: validate_pdf_bytes, is_valid_embedded_image, image_bytes_to_pil, pil_to_bytes, create_llm_optimized, get_image_dimensions, detect_format.
- LLM optimization: downscaling, aspect ratio preservation, JPEG compression, quality parameter effects.
- pymupdf4llm integration: page_text_map population, 0-indexed to 1-indexed conversion, failure fallback.
- Edge cases: corrupted PDFs, oversized PDFs, empty PDFs, max_pages limits.
- Data class default and independence testing (ExtractionResult list/dict factories).

### 4.10 test_auth_service.py (157 lines) -- Adequate

**Strengths:**
- JWT token creation and verification for both access and refresh tokens.
- Domain validation (allowed vs disallowed domains).
- Refresh token hashing (SHA256, deterministic).
- JTI uniqueness generation.
- Token expiry and type claims verification.

**Weaknesses:**
- Only 157 lines -- the thinnest test file in the suite.
- No error path testing for expired tokens.
- No testing of token refresh flow.
- No testing of Google OAuth integration flow.
- No role-based access control testing.
- Uses `User` model directly, but no database interaction testing.
- Placeholder tests for database session context and connection pool (empty test bodies).

### 4.11 test_config.py (238 lines) -- Good

**Strengths:**
- Validates Settings construction with correct and invalid parameters.
- DATABASE_URL protocol validation (rejects non-PostgreSQL).
- JWT_SECRET minimum length enforcement.
- ENVIRONMENT enum validation.
- ANTHROPIC_TEMPERATURE range validation.
- ALLOWED_ORIGINS comma-separated parsing.
- Template sheet ID lookup by name.
- Sync database URL property (strips `+asyncpg`).

**Weaknesses:**
- Placeholder tests for database session and connection pool (bodies are `pass`).
- No testing of `.env` file loading or environment variable precedence.

### 4.12 test_floor_plan.py (982 lines) -- Excellent

**Strengths:**
- 7 test classes covering initialization, extraction, parsing, text fallback, merging, media type detection, source tracking, deduplication.
- Per-field source tracking ("floor_plan_image" vs "text_fallback") verified comprehensively.
- Deduplication at 95% threshold with identical vs distinct image verification.
- Vision response parsing: valid JSON, markdown-fenced JSON, invalid JSON, partial data.
- Text fallback: unit type patterns (Studio, 1BR, 2BR, 3BR, Penthouse, "3 bed").
- Adjacent page context for text extraction (+/- 1 page).
- Merge priority: vision data always wins; text only fills gaps; room dimensions never from text.
- `create_distinct_image()` helper generates genuinely different pixel patterns.

### 4.13 test_image_classifier.py (863 lines) -- Excellent

**Strengths:**
- Tests both DeduplicationService and ImageClassifier.
- Perceptual hashing (pHash) for image similarity.
- Category classification via Claude Vision API.
- Category limits and deduplication logic.
- Media type detection across image formats.
- Async test patterns throughout.

### 4.14 test_image_optimizer.py (682 lines) -- Excellent

**Strengths:**
- Batch optimization with resize/aspect ratio preservation.
- RGBA-to-RGB conversion for JPEG output.
- DPI metadata injection.
- LLM tier dimensions (small, medium, large).
- ZIP package creation with manifest JSON.
- Integration tests: full pipeline, 20-image batch, mixed success/error.

### 4.15 test_watermark.py (1,016 lines) -- Excellent

**Strengths:**
- WatermarkDetector: initialization, JSON response parsing, detect with/without watermark, API errors, coordinate scaling, batch detection.
- WatermarkRemover: mask creation, quality scoring, bytes-to-cv2 conversion.
- Data class testing for detection results.

---

## 5. Checklist Assessment

### 5.1 API Route Tests
**Rating: P1 CRITICAL -- 0/10 routes tested**

No route-level tests exist. Missing entirely:
- Request validation (Pydantic model parsing, required fields)
- Response shape verification (status codes, JSON structure)
- Auth middleware testing (protected routes, role requirements)
- Error response codes (400, 401, 403, 404, 422, 500)
- Query parameter handling
- File upload handling (multipart form data)
- Pagination parameters

### 5.2 Service Unit Tests
**Rating: Mostly Covered -- 14/19 services tested**

Tested (14): data_structurer, data_extractor, content_generator, content_qa_service (partial), prompt_manager (partial), sheets_manager, storage_service, auth_service, floor_plan_extractor, pdf_processor, image_classifier, image_optimizer, watermark_detector, watermark_remover

Not Tested (5):
- **job_manager.py** -- P1 CRITICAL: Orchestrates entire processing pipeline
- **user_service.py** -- P2: User CRUD operations
- **project_service.py** -- P2: Project CRUD operations
- **deduplication_service.py** -- Tested within test_image_classifier.py (adequate)
- **output_organizer.py** -- Tested within test_image_optimizer.py (adequate)

### 5.3 Integration Tests
**Rating: P2 IMPORTANT -- Integration tests exist but lack scope**

The test files include integration-style tests (full pipeline tests in test_image_optimizer.py, test_pdf_processor.py), but there are no true end-to-end integration tests that test service interactions through the API layer. All external API calls (Anthropic, Google Drive, Google Sheets, GCS) are mocked.

### 5.4 Auth Flow Tests
**Rating: P2 IMPORTANT -- Partially covered**

`test_auth_service.py` covers JWT mechanics but lacks:
- Google OAuth callback flow
- Token refresh flow
- Expired token handling
- Role-based access control
- Session management

### 5.5 DB Model Tests
**Rating: P2 IMPORTANT -- Not present**

No tests for `app/models/database.py`. Missing:
- ORM model instantiation and defaults
- Relationship integrity
- Enum field handling
- Migration compatibility
- Constraint validation

### 5.6 Frontend Component Tests
**Rating: P1 CRITICAL -- Not present**

No test framework installed. No test files exist. The frontend has 50+ components, 10 pages, 6 hooks, 3 stores -- all untested.

### 5.7 Test Fixtures / conftest.py
**Rating: P2 IMPORTANT -- Missing conftest.py**

Each test file creates its own fixtures independently, resulting in duplicated `mock_settings`, `mock_anthropic_client`, and similar fixtures across 8+ files. A shared `conftest.py` would reduce ~200 lines of duplication and ensure consistent mock configurations.

### 5.8 Async Test Patterns
**Rating: GOOD**

All async tests use `@pytest.mark.asyncio` correctly. `pytest.ini` has `asyncio_mode = auto`. `AsyncMock` is used throughout for async API calls. No issues with event loop management.

### 5.9 Mocking Patterns
**Rating: EXCELLENT**

Consistent use of `unittest.mock` across all test files:
- `patch()` context managers for module-level dependencies
- `AsyncMock` for all async operations
- `MagicMock` / `Mock` with proper `spec` arguments
- `side_effect` lists for multi-call retry simulation
- Proper exception initialization (e.g., `httpx.Response` for Anthropic errors)
- No global state mutation; all patches are scoped

### 5.10 Error Simulation
**Rating: EXCELLENT**

Error handling is tested consistently across modules:
- Rate limit errors (429) with retry
- Server errors (5xx) with retry
- Client errors (4xx) without retry
- Authentication errors (401)
- Timeout errors
- `NotFound` exceptions (GCS, Google Drive)
- `GoogleCloudError` exceptions
- Invalid/corrupted input (PDFs, images, JSON)
- Missing credentials and configuration
- Retry exhaustion

### 5.11 Test Configuration
**Rating: GOOD**

`pytest.ini` is well-configured with coverage, markers, and async mode. Missing:
- No `conftest.py` for shared fixtures
- No `pyproject.toml` for modern Python tooling
- No `.coveragerc` for coverage exclusion patterns
- No CI test matrix for Python version compatibility

---

## 6. Gap Analysis

### P1 -- Critical Gaps

| # | Gap | Risk | Recommendation |
|---|---|---|---|
| 1 | **Zero route-level tests (0/10)** | API contract violations, auth bypasses, and input validation failures will not be caught | Create `tests/test_routes/` with FastAPI `TestClient`. Start with `test_routes_upload.py` (file upload flows), `test_routes_auth.py` (OAuth + JWT middleware), and `test_routes_jobs.py` (job CRUD + status transitions). |
| 2 | **Zero frontend tests** | UI regressions, broken state management, and API integration failures will only be found manually | Install `vitest` + `@testing-library/react`. Add `test` script to `package.json`. Start with critical path: `ProtectedRoute`, `use-auth`, `api.ts`, `FileUpload`. |
| 3 | **job_manager.py untested** | Central orchestration service that coordinates PDF processing, image classification, content generation, and Google Sheets output | Create `test_job_manager.py` testing job lifecycle: creation, status transitions, error recovery, partial failure handling. |

### P2 -- Important Gaps

| # | Gap | Risk | Recommendation |
|---|---|---|---|
| 4 | **No conftest.py** | Fixture duplication (~200 lines) increases maintenance burden and risks inconsistent mock configurations | Extract shared fixtures: `mock_settings`, `mock_anthropic_client`, `sample_project_data`, `mock_user` into `tests/conftest.py`. |
| 5 | **No DB model tests** | Schema migrations may break ORM assumptions; enum mismatches go undetected | Create `test_models.py` testing model instantiation, enum fields, relationship definitions, and default values. |
| 6 | **Auth flow incomplete** | OAuth callback, token refresh, expired token, and RBAC are not tested | Extend `test_auth_service.py` with expired token, refresh flow, and role verification tests. |
| 7 | **task_queue.py untested** | Background job processing failures won't be caught | Create `test_task_queue.py` for queue operations, job dispatch, and error handling. |
| 8 | **user_service.py untested** | User CRUD operations (create, lookup, role updates) are unverified | Create `test_user_service.py` with mocked database session. |
| 9 | **project_service.py untested** | Project lifecycle management is unverified | Create `test_project_service.py` with mocked database session. |
| 10 | **Duplicate test file** | Both `tests/test_data_structurer.py` (1,174 lines) and `tests/services/test_data_structurer.py` (511 lines) test the same module | Consolidate into one file. The root-level file is more comprehensive; the services/ version adds minor validation tests that should be merged. |

### P3 -- Nice to Have

| # | Gap | Impact | Recommendation |
|---|---|---|---|
| 11 | **No rate_limit middleware tests** | Middleware behavior at threshold boundaries unknown | Add `test_rate_limit.py` testing sliding window, threshold enforcement, and header responses. |
| 12 | **No .coveragerc** | Coverage reports include test files and migrations | Add `.coveragerc` with `omit` patterns for `tests/*`, `alembic/*`, `__init__.py`. |
| 13 | **No test for main.py** | App startup, CORS configuration, and middleware registration untested | Add startup/shutdown event tests. |
| 14 | **Placeholder tests in test_config.py** | Two test methods with `pass` bodies exist | Remove or implement the placeholder tests (`test_database_session_context`, `test_connection_pool_status`). |
| 15 | **No parametrized tests** | Many test methods repeat similar patterns with different data | Convert extraction tests (prices, bedrooms, dates) to `@pytest.mark.parametrize`. |
| 16 | **No mutation testing** | High line coverage may mask weak assertions | Consider `mutmut` or `cosmic-ray` for mutation testing on critical services. |

---

## 7. Test Quality Patterns Summary

### What is Done Well

1. **Class-based test organization** -- Most test files use test classes grouped by feature area, making it easy to navigate and run subsets.
2. **Comprehensive error path testing** -- Every external API integration tests rate limits, timeouts, server errors, and auth errors.
3. **Retry logic verification** -- Retry count, backoff delays, and exhaustion are verified with mock side_effect chains.
4. **Data class testing** -- All custom data classes (StructuredProject, GeneratedField, FloorPlanData, etc.) have creation, default, and independence tests.
5. **Boundary condition testing** -- Prices, dates, character limits, image dimensions, and confidence thresholds are tested at exact boundaries.
6. **Domain-specific assertions** -- Tests reflect real UAE real estate knowledge (AED pricing, Dubai communities, developer names, bedroom formats).
7. **Async patterns** -- Consistent `@pytest.mark.asyncio` + `AsyncMock` usage throughout with no event loop issues.

### What Needs Improvement

1. **Missing conftest.py** -- Fixture duplication is the single most impactful quick win.
2. **No route tests** -- The API layer is completely blind; any request validation or auth middleware bug ships undetected.
3. **No frontend tests** -- The React application has zero test coverage.
4. **job_manager is untested** -- The central orchestration service has no tests despite being the most critical coordination point.
5. **Auth testing is shallow** -- JWT mechanics work, but the full OAuth flow and RBAC are not tested.

---

## 8. Recommended Priority Order

1. **Create `tests/conftest.py`** with shared fixtures (1-2 hours)
2. **Create route tests** for `auth.py`, `upload.py`, `jobs.py` using FastAPI `TestClient` (1-2 days)
3. **Create `test_job_manager.py`** for orchestration pipeline (4-6 hours)
4. **Install vitest + @testing-library/react** in frontend and add first tests for auth + API layer (1 day)
5. **Create DB model tests** with SQLAlchemy model validation (2-4 hours)
6. **Extend auth tests** with expired token, refresh flow, and RBAC (2-4 hours)
7. **Consolidate duplicate data_structurer tests** into single file (1 hour)
8. **Add task_queue, user_service, project_service tests** (1 day)

---

*End of Test Coverage Audit*
