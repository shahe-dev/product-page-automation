# Backend API Routes Audit Report

**Audit Date:** 2026-01-29
**Auditor:** Claude Opus 4.5 (automated)
**Branch:** `feature/phase-11-pymupdf4llm-integration`
**Scope:** All FastAPI route handlers in `backend/app/api/routes/`

---

## Summary

| Severity | Count |
|----------|-------|
| P0 (Critical) | 5 |
| P1 (High) | 9 |
| P2 (Medium) | 14 |
| P3 (Low) | 7 |
| **Total** | **35** |

### Files Reviewed

| File | Routes | Status |
|------|--------|--------|
| `backend/app/api/routes/auth.py` | 7 | Reviewed |
| `backend/app/api/routes/jobs.py` | 6 | Reviewed |
| `backend/app/api/routes/projects.py` | 9 | Reviewed |
| `backend/app/api/routes/upload.py` | 3 | Reviewed |
| `backend/app/api/routes/prompts.py` | 5 | Reviewed |
| `backend/app/api/routes/workflow.py` | 5 | Reviewed |
| `backend/app/api/routes/content.py` | 4 | Reviewed |
| `backend/app/api/routes/qa.py` | 5 | Reviewed |
| `backend/app/api/routes/templates.py` | 3 | Reviewed |
| `backend/app/api/routes/internal.py` | 2 | Reviewed |
| `backend/app/api/dependencies.py` | 5 deps | Reviewed |
| `backend/app/api/dependencies_temp.py` | N/A | Does not exist on disk |
| `backend/app/main.py` | Router registration | Reviewed |
| `backend/app/models/schemas.py` | Pydantic models | Reviewed |

---

## P0 -- Critical Findings

### Finding: SQL Injection via `ilike` with unescaped user input
- **Severity:** P0
- **File:** `backend/app/api/routes/prompts.py:128`
- **Description:** The `search` query parameter is interpolated directly into an `ilike` pattern without escaping SQL wildcard characters (`%`, `_`). A user can inject `%` or `_` wildcards to manipulate query results. While this is not a full SQL injection (parameterized queries prevent that), it is a LIKE injection that can enumerate data and bypass intended search semantics.
- **Evidence:**
  ```python
  if search:
      query = query.where(Prompt.name.ilike(f"%{search}%"))
  ```
- **Fix:** Escape SQL wildcards before interpolation:
  ```python
  if search:
      escaped = search.replace("%", "\\%").replace("_", "\\_")
      query = query.where(Prompt.name.ilike(f"%{escaped}%", escape="\\"))
  ```

---

### Finding: Job deletion endpoint is a no-op (TODO left in production code)
- **Severity:** P0
- **File:** `backend/app/api/routes/jobs.py:493-494`
- **Description:** The `DELETE /jobs/{job_id}` endpoint returns 204 NO_CONTENT but does not actually delete the job. The deletion logic is commented out with a `TODO`. This means calling this endpoint silently succeeds but does nothing, which is a data integrity violation.
- **Evidence:**
  ```python
  # TODO: Implement job deletion in repository
  # await job_manager.job_repo.delete_job(job_id)

  logger.warning(
      f"Job {job_id} deleted by admin {current_user.id}",
  ```
  The logger says "deleted" but nothing was deleted.
- **Fix:** Either implement the deletion or return 501 NOT_IMPLEMENTED. Do not return 204 for an operation that did not happen.

---

### Finding: Upload status endpoint returns hardcoded placeholder data
- **Severity:** P0
- **File:** `backend/app/api/routes/upload.py:436-448`
- **Description:** The `GET /upload/{upload_id}/status` endpoint returns hardcoded placeholder data regardless of the `upload_id` parameter. Any UUID will return a fake "processing" status with a hardcoded timestamp. This endpoint is actively misleading clients.
- **Evidence:**
  ```python
  # TODO: Query job status from database
  # For now, return placeholder

  return {
      "id": str(upload_id),
      "status": "processing",
      "progress": 75,
      "current_step": "Extracting images",
      "created_at": "2026-01-26T00:00:00Z",
      "updated_at": "2026-01-26T00:05:00Z"
  }
  ```
- **Fix:** Query the actual job status from the database or return 501 NOT_IMPLEMENTED until the implementation is ready.

---

### Finding: Image upload endpoint has TODO stubs -- files are uploaded to temp but never persisted
- **Severity:** P0
- **File:** `backend/app/api/routes/upload.py:357-359`
- **Description:** The `POST /upload/images` endpoint accepts images, streams them to temp files, but then the temp files are deleted in the `finally` block without ever being uploaded to Cloud Storage or saved to the database. The endpoint returns success with a count of "uploaded" images that were actually discarded.
- **Evidence:**
  ```python
  # TODO: Upload to Cloud Storage
  # TODO: Create thumbnail
  # TODO: Save to database

  uploaded_images.append({
      "filename": file.filename,
      "size_mb": round(file_size_mb, 2),
      "category": category
  })
  ```
  Then in `finally`:
  ```python
  for temp_path in temp_paths:
      if temp_path and os.path.exists(temp_path):
          os.unlink(temp_path)
  ```
- **Fix:** Implement the Cloud Storage upload and database persistence, or return 501 NOT_IMPLEMENTED.

---

### Finding: Internal API key defaults to hardcoded `development-key`
- **Severity:** P0
- **File:** `backend/app/api/routes/internal.py:50`
- **Description:** The internal API authentication falls back to the hardcoded string `development-key` if `INTERNAL_API_KEY` is not set in settings. If this config is not explicitly set in production, any caller with the string `development-key` can invoke the internal process-job endpoint.
- **Evidence:**
  ```python
  expected_key = getattr(settings, 'INTERNAL_API_KEY', 'development-key')
  ```
- **Fix:** Remove the default fallback. Require `INTERNAL_API_KEY` to be set and raise a startup error if missing:
  ```python
  expected_key = settings.INTERNAL_API_KEY  # Must be set; no default
  ```

---

## P1 -- High Findings

### Finding: Error messages leak internal details in projects routes
- **Severity:** P1
- **File:** `backend/app/api/routes/projects.py:113,145,181,294,332,401,473`
- **Description:** Multiple project endpoints include `str(e)` in the HTTP error response detail. This can leak stack traces, database table names, SQL syntax, or internal service errors to the client. This occurs in every except block in the file.
- **Evidence:**
  ```python
  except Exception as e:
      logger.error(f"Failed to list projects: {e}")
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=f"Failed to list projects: {str(e)}"  # Leaks internal error
      )
  ```
- **Fix:** Return a generic error message to the client. The exception details are already logged:
  ```python
  detail="Failed to list projects"  # No str(e)
  ```

---

### Finding: Internal process-job endpoint leaks error details
- **Severity:** P1
- **File:** `backend/app/api/routes/internal.py:185`
- **Description:** The catch-all exception handler includes `str(e)` in the 500 response detail. Even though this is an internal endpoint, error details should not be in the response body since Cloud Tasks logs would capture them.
- **Evidence:**
  ```python
  raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Internal error processing job: {str(e)}"
  )
  ```
- **Fix:** Return a generic message:
  ```python
  detail="Internal error processing job"
  ```

---

### Finding: `prompts.py` update_prompt exception handler swallows HTTPException (404)
- **Severity:** P1
- **File:** `backend/app/api/routes/prompts.py:467-476`
- **Description:** The `except Exception` block in `update_prompt` does not have a preceding `except HTTPException: raise` clause. This means if the prompt is not found (404), the HTTPException raised at line 415-422 is caught by the generic Exception handler and re-raised as a 500 Internal Server Error.
- **Evidence:**
  ```python
  # Lines 408-476: Only one except block
  except Exception as e:
      logger.exception(f"Error updating prompt: {e}")
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail={...}
      )
  ```
  Compare with `create_prompt` which correctly has:
  ```python
  except HTTPException:
      raise
  except Exception as e:
      ...
  ```
- **Fix:** Add `except HTTPException: raise` before the generic handler:
  ```python
  except HTTPException:
      raise
  except Exception as e:
      logger.exception(f"Error updating prompt: {e}")
      ...
  ```

---

### Finding: `prompts.py` get_prompt exception handler swallows HTTPException (404)
- **Severity:** P1
- **File:** `backend/app/api/routes/prompts.py:237-246`
- **Description:** Same issue as update_prompt. The `get_prompt` handler raises HTTPException for 404 at line 209, but the outer `except Exception` at line 237 catches it and converts it to a 500.
- **Evidence:**
  ```python
  except Exception as e:
      logger.exception(f"Error getting prompt: {e}")
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          ...
      )
  ```
- **Fix:** Add `except HTTPException: raise` before the generic handler.

---

### Finding: `prompts.py` get_prompt_versions exception handler swallows HTTPException (404)
- **Severity:** P1
- **File:** `backend/app/api/routes/prompts.py:550-559`
- **Description:** Same pattern. The 404 raised at line 522 is caught by `except Exception` at line 550 and converted to 500.
- **Fix:** Add `except HTTPException: raise` before the generic handler.

---

### Finding: Multiple list endpoints missing authentication
- **Severity:** P1
- **File:** `backend/app/api/routes/projects.py:49-67`
- **Description:** The `list_projects`, `search_projects`, `get_statistics`, `get_recent_activity`, and `export_projects` endpoints do not require authentication (no `current_user` dependency). Any unauthenticated user can list, search, and export all projects. The `get_project` and `get_project_history` endpoints also lack auth. Compare with `create_project`, `update_project`, and `delete_project` which correctly require `get_current_user`.
- **Evidence:**
  ```python
  @router.get("", response_model=ProjectListResponse)
  async def list_projects(
      # ... query params ...
      service: ProjectService = Depends(get_project_service)
  ):  # No current_user dependency
  ```
- **Fix:** Add `current_user: User = Depends(get_current_user)` to all project endpoints that should be protected.

---

### Finding: `@require_admin` decorator may not work correctly with FastAPI dependency injection
- **Severity:** P1
- **File:** `backend/app/api/routes/prompts.py:256-257`
- **Description:** The `@require_admin` decorator wraps the function and expects `current_user` as a keyword argument. However, FastAPI's dependency injection resolves parameters based on the function signature of the decorated function, not the wrapper. The `@wraps(func)` preserves the original signature, but the wrapper's actual signature (`*args, current_user: User, **kwargs`) may not match what FastAPI expects. This pattern is fragile and can fail silently or cause unexpected 422 errors.
- **Evidence:**
  ```python
  @router.post("", ...)
  @require_admin
  async def create_prompt(
      request: PromptCreate,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db_session)
  ):
  ```
  In `permissions.py`:
  ```python
  @wraps(func)
  async def wrapper(*args, current_user: User, **kwargs):
      if current_user.role != UserRole.ADMIN:
          ...
  ```
- **Fix:** Use FastAPI's `Depends()` pattern instead of decorators. Replace `@require_admin` with the existing `get_current_admin` dependency from `dependencies.py`:
  ```python
  current_user: User = Depends(get_current_admin)
  ```

---

### Finding: Inconsistent dependency sources across route files
- **Severity:** P1
- **File:** Multiple files
- **Description:** Different route files import `get_current_user` and `get_db` from different locations, creating a maintenance hazard and potential for inconsistent behavior:
  - `auth.py`: imports from `app.middleware.auth` and `app.config.database`
  - `jobs.py`: imports from `app.api.dependencies`
  - `projects.py`: imports from `app.api.dependencies` and `app.config.database`
  - `upload.py`: imports from `app.middleware.auth` and `app.config.database`
  - `prompts.py`: imports from `app.middleware.auth` and `app.config.database`
  - `workflow.py`: imports from `app.middleware.auth` and `app.config.database`
  - `content.py`: imports from `app.middleware.auth` and `app.config.database`
  - `qa.py`: imports from `app.middleware.auth` and `app.config.database`
  - `templates.py`: imports from `app.middleware.auth` and `app.config.database`
  - `internal.py`: imports from `app.config.database` and `app.config.settings`
- **Evidence:** `dependencies.py` re-exports `get_db = get_db_session` and re-exports `get_current_user` from `middleware.auth`, but only `jobs.py` and `projects.py` use it.
- **Fix:** All route files should import from `app.api.dependencies` as the single source of truth. This is the purpose of the dependencies module.

---

### Finding: `internal.py` JobManager instantiation differs from other files
- **Severity:** P1
- **File:** `backend/app/api/routes/internal.py:65-67`
- **Description:** The `get_job_manager` in `internal.py` creates `JobManager(db)` with a single argument, while `jobs.py` creates `JobManager(job_repo, task_queue)` with two arguments. These are incompatible constructor signatures, meaning one of them will fail at runtime.
- **Evidence:**
  ```python
  # internal.py
  def get_job_manager(db: AsyncSession = Depends(get_db_session)) -> JobManager:
      return JobManager(db)

  # jobs.py
  async def get_job_manager(db = Depends(get_db)) -> JobManager:
      job_repo = JobRepository(db)
      task_queue = TaskQueue()
      return JobManager(job_repo, task_queue)
  ```
- **Fix:** Standardize on one approach. The `jobs.py` pattern with `JobRepository` and `TaskQueue` appears to be the correct one based on the class design.

---

## P2 -- Medium Findings

### Finding: `dependencies_temp.py` referenced in git status but does not exist on disk
- **Severity:** P2
- **File:** `backend/app/api/dependencies_temp.py`
- **Description:** Git status shows this file as ` M backend/app/api/dependencies_temp.py` (modified, unstaged), yet the file does not exist on the filesystem and is not importable. The git index may contain a stale entry. No code in the codebase imports from this module. The file's existence in the git index is confusing and should be cleaned up.
- **Evidence:** `Glob` returns no results for `**/dependencies_temp.py`. `Grep` for `dependencies_temp` across the backend returns no matches.
- **Fix:** Remove from git tracking: `git rm --cached backend/app/api/dependencies_temp.py`

---

### Finding: `upload/pdf` returns 200 instead of 201 for resource creation
- **Severity:** P2
- **File:** `backend/app/api/routes/upload.py:142`
- **Description:** The PDF upload endpoint creates a new job and returns its details, but uses `HTTP_200_OK` instead of `HTTP_201_CREATED`. This is inconsistent with REST conventions and with the `POST /jobs` endpoint which correctly returns 201.
- **Evidence:**
  ```python
  @router.post(
      "/pdf",
      status_code=status.HTTP_200_OK,  # Should be 201
      ...
  )
  ```
- **Fix:** Change to `status_code=status.HTTP_201_CREATED`.

---

### Finding: `upload/images` returns 200 instead of 201 for resource creation
- **Severity:** P2
- **File:** `backend/app/api/routes/upload.py:287`
- **Description:** Same issue as PDF upload. Image upload creates resources but returns 200.
- **Fix:** Change to `status_code=status.HTTP_201_CREATED`.

---

### Finding: Upload responses use raw dicts instead of Pydantic response models
- **Severity:** P2
- **File:** `backend/app/api/routes/upload.py:259-265, 383-389`
- **Description:** Both upload endpoints return raw dictionaries instead of typed Pydantic `response_model` classes. This means:
  1. No OpenAPI schema documentation for the response
  2. No automatic response validation
  3. Internal fields could accidentally leak
- **Evidence:**
  ```python
  return {
      "job_id": str(job.id),
      "status": job.status.value,
      "template_type": template_type,
      "file_size_mb": round(file_size_mb, 2),
      "created_at": job.created_at.isoformat() + "Z"
  }
  ```
- **Fix:** Define Pydantic response models and set `response_model=UploadPdfResponse` on the route decorator.

---

### Finding: `content.py`, `qa.py`, `workflow.py`, `templates.py` return raw dicts from several endpoints
- **Severity:** P2
- **File:** Multiple files
- **Description:** The following endpoints return raw dictionaries without `response_model`:
  - `content.py`: `approve_content` (line 234)
  - `qa.py`: `get_qa_results` (line 184), `resolve_qa_issue` (line 233), `override_qa_issue` (line 291), `get_qa_history` (line 358)
  - `workflow.py`: `move_workflow_item` (line 197), `assign_workflow_item` (line 246), `get_workflow_items` (line 366)
  - `templates.py`: `list_templates` (line 140), `get_template_fields` (line 248)
  - `projects.py`: `search_projects` (line 174), `get_statistics` (line 198), `get_recent_activity` (line 237)
- **Fix:** Define Pydantic response models for each endpoint and set `response_model` on the decorator.

---

### Finding: `prompts.py` list endpoint returns `{"items": [...]}` without response model or pagination
- **Severity:** P2
- **File:** `backend/app/api/routes/prompts.py:159`
- **Description:** The `list_prompts` endpoint has no pagination (no `limit`/`offset` or `page`/`page_size` params) and no `response_model`. If the prompts table grows, this will return all prompts in a single response. Compare with `jobs.py` which has proper pagination with `JobListResponse`.
- **Evidence:**
  ```python
  return {"items": prompts}  # Returns ALL prompts, no pagination
  ```
- **Fix:** Add `limit` and `offset` query parameters, a `total` count, and a proper `response_model`.

---

### Finding: `projects.py` update_project maps ValueError to 404 instead of 400
- **Severity:** P2
- **File:** `backend/app/api/routes/projects.py:356-361`
- **Description:** When `ProjectService.update_project` raises a `ValueError`, the route returns 404 NOT_FOUND. A `ValueError` typically indicates bad input (400), not a missing resource (404). If the project is not found, the service should raise a different exception.
- **Evidence:**
  ```python
  except ValueError as e:
      logger.warning(f"Validation error updating project {project_id}: {e}")
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,  # Wrong status code
          detail=str(e)
      )
  ```
- **Fix:** Differentiate between "project not found" (404) and "validation error" (400). Use separate exception types in the service layer, or return 400 for ValueError.

---

### Finding: `auth.py` `/login` endpoint does not require authentication but creates DB state
- **Severity:** P2
- **File:** `backend/app/api/routes/auth.py:119-146`
- **Description:** The `/login` endpoint creates an OAuth state record in the database without any authentication or rate limiting at the route level. An attacker could flood this endpoint to fill the database with state records. While there is a global rate limit middleware, this endpoint should have stricter per-IP rate limiting.
- **Evidence:**
  ```python
  @router.get("/login", response_model=OAuthLoginResponse, status_code=status.HTTP_200_OK)
  async def get_oauth_login_url(
      redirect_uri: Optional[str] = None,
      db: AsyncSession = Depends(get_db)
  ):
      state = await auth_service.create_oauth_state(db, final_redirect_uri)
  ```
- **Fix:** Add stricter rate limiting for this endpoint, or use an in-memory store (e.g., Redis with TTL) for OAuth state instead of the database.

---

### Finding: `auth.py` `/login` accepts arbitrary `redirect_uri` without validation
- **Severity:** P2
- **File:** `backend/app/api/routes/auth.py:122,135`
- **Description:** The `redirect_uri` query parameter is accepted without any validation or allowlisting. An attacker could provide a malicious redirect URI to conduct an OAuth redirect attack (open redirect).
- **Evidence:**
  ```python
  redirect_uri: Optional[str] = None,
  ...
  final_redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
  ```
- **Fix:** Validate the `redirect_uri` against an allowlist of trusted URIs:
  ```python
  ALLOWED_REDIRECT_URIS = [settings.GOOGLE_REDIRECT_URI, ...]
  if redirect_uri and redirect_uri not in ALLOWED_REDIRECT_URIS:
      raise HTTPException(status_code=400, detail="Invalid redirect URI")
  ```

---

### Finding: `content.py` `generate_content` uses wrong status code for success path
- **Severity:** P2
- **File:** `backend/app/api/routes/content.py:66`
- **Description:** The `POST /content/generate` endpoint is decorated with `status_code=HTTP_200_OK` but it should use `HTTP_202_ACCEPTED` since content generation is (or would be) an async operation. The endpoint currently returns 501, but when implemented, a 202 with a job/task ID would be the correct pattern.
- **Fix:** Change to `status_code=status.HTTP_202_ACCEPTED` and return a job reference instead of the full content.

---

### Finding: `projects.py` `/export` endpoint has no authentication
- **Severity:** P2
- **File:** `backend/app/api/routes/projects.py:247-249`
- **Description:** The `POST /projects/export` endpoint can export all project data without authentication. This allows unauthenticated users to bulk-export all data.
- **Evidence:**
  ```python
  @router.post("/export")
  async def export_projects(
      export_request: ProjectExportRequest,
      service: ProjectService = Depends(get_project_service)
  ):  # No current_user dependency
  ```
- **Fix:** Add `current_user: User = Depends(get_current_user)`.

---

### Finding: `internal.py` process-job does not validate UUID format of `job_id`
- **Severity:** P2
- **File:** `backend/app/api/routes/internal.py:88`
- **Description:** The `job_id` field in `ProcessJobRequest` is typed as `str`, and `UUID(request.job_id)` is called without error handling. If an invalid UUID string is passed, this will raise a `ValueError` that propagates as a 500 error instead of a 422 validation error.
- **Evidence:**
  ```python
  class ProcessJobRequest(BaseModel):
      job_id: str  # Should be UUID type
      pdf_path: str

  # Then in handler:
  job_id = UUID(request.job_id)  # No try/except, will crash on bad input
  ```
- **Fix:** Change the Pydantic model to use `UUID` type:
  ```python
  class ProcessJobRequest(BaseModel):
      job_id: UUID
      pdf_path: str
  ```

---

### Finding: `routes/__init__.py` does not export `internal` module
- **Severity:** P2
- **File:** `backend/app/api/routes/__init__.py:3-13`
- **Description:** The `__init__.py` imports and exports `auth`, `projects`, `jobs`, `upload`, `content`, `qa`, `prompts`, `templates`, `workflow` but does not include `internal`. However, `main.py` imports `internal` from `app.api.routes`. This works because Python resolves the import, but the `__init__.py` is inconsistent.
- **Evidence:**
  ```python
  from . import (
      auth, projects, jobs, upload, content, qa, prompts, templates, workflow,
  )
  __all__ = [
      "auth", "projects", "jobs", "upload", "content", "qa", "prompts", "templates", "workflow",
  ]
  ```
  Missing: `internal`.
- **Fix:** Add `internal` to both the import and `__all__`.

---

## P3 -- Low Findings

### Finding: Duplicate `get_job_or_404` definitions
- **Severity:** P3
- **File:** `backend/app/api/routes/jobs.py:169-203` and `backend/app/api/dependencies.py:95-132`
- **Description:** `get_job_or_404` is defined in both `jobs.py` and `dependencies.py` with different implementations. The `jobs.py` version uses `JobManager`, while `dependencies.py` uses direct SQLAlchemy queries. Only the `jobs.py` version is used in routes.
- **Fix:** Remove the duplicate in `jobs.py` and use the shared one from `dependencies.py`, or vice versa.

---

### Finding: Duplicate `PaginationParams` definitions
- **Severity:** P3
- **File:** `backend/app/api/dependencies.py:135-146` and `backend/app/models/schemas.py:261-275`
- **Description:** `PaginationParams` is defined in both `dependencies.py` (as a class) and `schemas.py` (as a Pydantic BaseModel). They have different implementations -- `dependencies.py` is a plain class with `__init__`, while `schemas.py` is a Pydantic model with validators. Only `schemas.py` version is used in `projects.py`.
- **Fix:** Remove the duplicate from `dependencies.py` and standardize on the `schemas.py` version.

---

### Finding: `auth.py` uses different router prefix pattern than other files
- **Severity:** P3
- **File:** `backend/app/api/routes/auth.py:31`
- **Description:** The auth router uses `prefix="/auth"` and is registered in `main.py` with `prefix="/api/v1"`, resulting in `/api/v1/auth/...`. This is consistent with other routers. No issue, but the router tag casing is inconsistent: auth uses `tags=["Authentication"]` (capitalized) while all others use lowercase (`tags=["jobs"]`, `tags=["projects"]`, etc.).
- **Evidence:**
  ```python
  # auth.py
  router = APIRouter(prefix="/auth", tags=["Authentication"])

  # jobs.py
  router = APIRouter(prefix="/jobs", tags=["jobs"])
  ```
- **Fix:** Use consistent casing for tags. Either all capitalized or all lowercase.

---

### Finding: `auth.py` `/health` endpoint duplicates the global health check
- **Severity:** P3
- **File:** `backend/app/api/routes/auth.py:428-440`
- **Description:** There is an auth-specific health check at `/api/v1/auth/health` in addition to the global `/health` endpoint in `main.py`. The auth health check does not actually verify auth-service-specific resources (e.g., Google OAuth connectivity, JWT signing key availability).
- **Evidence:**
  ```python
  @router.get("/health", status_code=status.HTTP_200_OK)
  async def auth_health_check():
      return {
          "status": "healthy",
          "service": "authentication",
          "timestamp": datetime.utcnow().isoformat()
      }
  ```
- **Fix:** Either remove it (redundant with global health check) or make it actually verify auth dependencies.

---

### Finding: `datetime.utcnow()` is deprecated
- **Severity:** P3
- **File:** `backend/app/api/routes/auth.py:439`, `backend/app/api/routes/projects.py:269`, `backend/app/api/routes/qa.py:227,284`, `backend/app/api/routes/content.py:223`
- **Description:** `datetime.utcnow()` is deprecated in Python 3.12+ in favor of `datetime.now(datetime.UTC)`. While functional, this will emit deprecation warnings.
- **Fix:** Replace with `datetime.now(datetime.UTC)` or `datetime.now(timezone.utc)`.

---

### Finding: `workflow.py` uses `last_modified_by` as a proxy for "assigned_to"
- **Severity:** P3
- **File:** `backend/app/api/routes/workflow.py:85-89,237`
- **Description:** The workflow endpoints use `Project.last_modified_by` as the "assigned to" field. This conflates "who last edited the project" with "who is assigned to work on it." If a user edits a project without being assigned, the assignment changes. This is a data modeling concern that should be flagged.
- **Evidence:**
  ```python
  # assign_workflow_item
  project.last_modified_by = assignee.id  # Overloading last_modified_by as assignment
  ```
- **Fix:** Add a dedicated `assigned_to` column on the `Project` model.

---

### Finding: Inconsistent error response formats
- **Severity:** P3
- **File:** Multiple files
- **Description:** Error responses use two different formats across the codebase:
  1. Structured format with `error_code`/`message`/`details` dict (used in `upload.py`, `prompts.py`, `content.py`, `qa.py`, `templates.py`, `workflow.py`)
  2. Plain string detail (used in `auth.py`, `jobs.py`, `projects.py`, `internal.py`)
- **Evidence:**
  ```python
  # Format 1 (structured):
  detail={"error_code": "NOT_FOUND", "message": f"Project {item_id} not found"}

  # Format 2 (string):
  detail=f"Job {job_id} not found"
  ```
- **Fix:** Standardize on one format. The structured format is preferable for client-side error handling. Create a shared error response helper function.

---

## Checklist Summary

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Proper HTTP status codes (201/204/404) | PARTIAL | Upload endpoints use 200 instead of 201; job delete returns 204 but does nothing |
| 2 | Error handling with HTTPException | PARTIAL | `prompts.py` swallows HTTPException in 3 handlers; error details leaked in `projects.py` |
| 3 | Pydantic request body validation | PASS | All request bodies use Pydantic models |
| 4 | Response models (no internal field leaks) | PARTIAL | 15+ endpoints return raw dicts without response_model |
| 5 | Pagination on list endpoints | PARTIAL | `prompts.py` list has no pagination; others are properly paginated |
| 6 | Dependency injection (get_db, get_current_user) | PARTIAL | 7 project endpoints lack auth; inconsistent import sources |
| 7 | No business logic in route handlers | PARTIAL | `prompts.py` contains direct SQLAlchemy queries and DB commits (no service layer); `workflow.py`, `content.py`, `qa.py`, `templates.py` same pattern |
| 8 | Path parameter validation (UUID) | PASS | All path params use `UUID` type annotation |
| 9 | Query parameter validation and defaults | PASS | Proper `ge`/`le` constraints and defaults |
| 10 | `dependencies_temp.py` status | N/A | File does not exist on disk; stale git index entry |
| 11 | Route prefix consistency (/api/v1/...) | PASS | All routers registered with `prefix="/api/v1"` in `main.py` |
| 12 | OpenAPI tags and descriptions | PARTIAL | Tags present but inconsistent casing; most routes have summaries |

---

## Appendix: Route Inventory

### auth.py (prefix: /api/v1/auth)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| GET | /login | None | OAuthLoginResponse | 200 |
| POST | /google | None | AuthResponse | 200 |
| POST | /refresh | None | RefreshResponse | 200 |
| GET | /me | JWT | UserResponse | 200 |
| POST | /logout | JWT | LogoutResponse | 200 |
| POST | /logout/all | JWT | LogoutResponse | 200 |
| GET | /health | None | dict | 200 |

### jobs.py (prefix: /api/v1/jobs)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| POST | / | JWT | JobResponse | 201 |
| GET | / | JWT | JobListResponse | 200 |
| GET | /{job_id} | JWT+Owner | JobResponse | 200 |
| GET | /{job_id}/status | JWT+Owner | JobStatusResponse | 200 |
| GET | /{job_id}/steps | JWT+Owner | List[JobStepResponse] | 200 |
| POST | /{job_id}/cancel | JWT+Owner | JobResponse | 200 |
| DELETE | /{job_id} | JWT+Admin | None | 204 (broken) |

### projects.py (prefix: /api/v1/projects)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| GET | / | **NONE** | ProjectListResponse | 200 |
| POST | / | JWT | ProjectDetailSchema | 201 |
| GET | /search | **NONE** | list (no model) | 200 |
| GET | /statistics | **NONE** | dict | 200 |
| GET | /activity | **NONE** | list | 200 |
| POST | /export | **NONE** | Response (file) | 200 |
| GET | /{project_id} | **NONE** | ProjectDetailSchema | 200 |
| PUT | /{project_id} | JWT | ProjectDetailSchema | 200 |
| DELETE | /{project_id} | JWT+Admin | None | 204 |
| GET | /{project_id}/history | **NONE** | List[ProjectRevisionSchema] | 200 |
| POST | /{project_id}/fields | JWT | ProjectDetailSchema | 200 |

### upload.py (prefix: /api/v1/upload)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| POST | /pdf | JWT | dict (no model) | 200 (should be 201) |
| POST | /images | JWT | dict (no model) | 200 (should be 201) |
| GET | /{upload_id}/status | JWT | dict (hardcoded) | 200 |

### prompts.py (prefix: /api/v1/prompts)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| GET | / | JWT | dict (no model) | 200 |
| GET | /{prompt_id} | JWT | PromptResponse | 200 |
| POST | / | JWT+Admin | PromptResponse | 201 |
| PUT | /{prompt_id} | JWT+Admin | PromptResponse | 200 |
| GET | /{prompt_id}/versions | JWT | dict (no model) | 200 |

### workflow.py (prefix: /api/v1/workflow)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| GET | /board | JWT | WorkflowBoard | 200 |
| PUT | /items/{item_id}/move | JWT | dict (no model) | 200 |
| PUT | /items/{item_id}/assign | JWT | dict (no model) | 200 |
| GET | /stats | JWT | WorkflowStats | 200 |
| GET | /items | JWT | dict (no model) | 200 |

### content.py (prefix: /api/v1/content)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| POST | /generate | JWT | ContentResponse | 200 (returns 501) |
| GET | /{project_id} | JWT | ContentResponse | 200 |
| PUT | /{content_id}/approve | JWT | dict (no model) | 200 |
| POST | /regenerate | JWT | -- | 200 (returns 501) |

### qa.py (prefix: /api/v1/qa)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| POST | /compare | JWT | QACompareResponse | 200 (returns 501) |
| GET | /{project_id}/results | JWT | dict (no model) | 200 |
| POST | /issues/{issue_id}/resolve | JWT | dict (no model) | 200 |
| POST | /issues/{issue_id}/override | JWT+Admin | dict (no model) | 200 |
| GET | /history | JWT | dict (no model) | 200 |

### templates.py (prefix: /api/v1/templates)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| GET | / | JWT | dict (no model) | 200 |
| GET | /{template_id} | JWT | TemplateDetail | 200 |
| GET | /{template_id}/fields | JWT | dict (no model) | 200 |

### internal.py (prefix: /api/v1/internal)
| Method | Path | Auth | Response Model | Status |
|--------|------|------|----------------|--------|
| POST | /process-job | API Key | dict (no model) | 200 |
| GET | /health | None | dict | 200 |

---

*End of audit report.*
