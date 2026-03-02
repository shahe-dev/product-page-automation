# Infrastructure Audit Report -- 07-infrastructure

**Date:** 2026-01-29
**Branch:** `feature/phase-11-pymupdf4llm-integration`
**Auditor:** Claude Opus 4.5 (automated)

---

## Summary

| Severity | Count |
|----------|-------|
| P0       | 3     |
| P1       | 5     |
| P2       | 6     |
| P3       | 3     |
| **Total**| **17**|

---

## P0 -- Critical

### Finding: Frontend dist/ Build Artifacts Tracked in Git
- **Severity:** P0
- **File:** `.gitignore`
- **Description:** The root `.gitignore` does not exclude `dist/` or `build/` directories. As a result, the entire `frontend/dist/` directory -- containing 57+ compiled JS/CSS build artifacts -- is tracked in git (visible in `git status` as both staged `A` and untracked `??` files). Build artifacts must never be committed: they bloat the repository, cause merge conflicts, and can leak source structure.
- **Evidence:** Git status shows dozens of entries like:
  ```
  A  frontend/dist/assets/index-Cqmw2Cim.css
  AD frontend/dist/assets/index-CF1ahWb6.js
  ?? frontend/dist/assets/AdminDashboardPage-CjTVBlp7.js
  ```
  Root `.gitignore` contents -- no `dist/` or `build/` entry:
  ```gitignore
  # Environment and secrets
  .env
  .env.*
  .credentials/
  *.key
  *.pem
  # IDE
  .vscode/
  .idea/
  # OS files
  .DS_Store
  Thumbs.db
  # Node (if applicable)
  node_modules/
  # Python (if applicable)
  __pycache__/
  *.pyc
  .venv/
  venv/
  # Logs
  *.log
  ```
- **Fix:** Add the following lines to `.gitignore` and then remove the tracked artifacts with `git rm -r --cached frontend/dist/`:
  ```gitignore
  # Build artifacts
  dist/
  build/
  .coverage
  htmlcov/
  ```

---

### Finding: Hardcoded GCP Project ID in Settings
- **Severity:** P0
- **File:** `backend/app/config/settings.py:64-66`
- **Description:** The `GCP_PROJECT_ID` field has a hardcoded default value of `"YOUR-GCP-PROJECT-ID"`, which is a real GCP project identifier. While this is not a secret per se, hardcoding project identifiers in source code is a deployment risk -- a developer could accidentally deploy against the wrong project. Similarly, `GCS_BUCKET_NAME` defaults to `"pdp-automation-assets-dev"`. These should be required fields without defaults, or the defaults should be clearly empty/placeholder.
- **Evidence:**
  ```python
  GCP_PROJECT_ID: str = Field(
      default="YOUR-GCP-PROJECT-ID",
      description="GCP project ID"
  )
  GCS_BUCKET_NAME: str = Field(
      default="pdp-automation-assets-dev",
      description="Google Cloud Storage bucket"
  )
  ```
- **Fix:** Remove the default values and make these required (use `...` as the default, like other sensitive fields), or use empty string defaults with validation:
  ```python
  GCP_PROJECT_ID: str = Field(..., description="GCP project ID")
  GCS_BUCKET_NAME: str = Field(..., description="Google Cloud Storage bucket")
  ```

---

### Finding: Missing Content-Security-Policy and Strict-Transport-Security Headers in Nginx
- **Severity:** P0
- **File:** `frontend/nginx.conf:7-12`
- **Description:** The nginx configuration includes `X-Frame-Options`, `X-Content-Type-Options`, and `X-XSS-Protection`, but is missing the two most critical security headers: `Content-Security-Policy` (CSP) and `Strict-Transport-Security` (HSTS). Without CSP, the application is vulnerable to XSS via inline scripts and unauthorized resource loading. Without HSTS, connections can be downgraded from HTTPS to HTTP.
- **Evidence:**
  ```nginx
  # Security headers
  add_header X-Frame-Options "SAMEORIGIN" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header X-XSS-Protection "1; mode=block" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
  # No Content-Security-Policy
  # No Strict-Transport-Security
  ```
- **Fix:** Add both headers:
  ```nginx
  add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://accounts.google.com https://oauth2.googleapis.com;" always;
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
  ```
  Note: The CSP policy above is a starting point. Adjust `script-src` and `style-src` directives based on actual application requirements (e.g., if inline styles are used by component libraries, `'unsafe-inline'` for `style-src` may be needed).

---

## P1 -- High

### Finding: Missing client_max_body_size in Nginx Configuration
- **Severity:** P1
- **File:** `frontend/nginx.conf`
- **Description:** No `client_max_body_size` directive is set. Nginx defaults to 1MB, but the backend `settings.py` configures `MAX_UPLOAD_SIZE_MB=50`. PDF uploads proxied through nginx will fail with `413 Request Entity Too Large` for any file over 1MB.
- **Evidence:** The entire `nginx.conf` has no `client_max_body_size` directive. Meanwhile:
  ```python
  # backend/app/config/settings.py:136-139
  MAX_UPLOAD_SIZE_MB: int = Field(
      default=50,
      description="Maximum file upload size in MB"
  )
  ```
- **Fix:** Add `client_max_body_size` to the server block or the API proxy location:
  ```nginx
  # In the server block or the location /api/ block:
  client_max_body_size 50M;
  ```

---

### Finding: Frontend Docker Compose Uses Production Image Instead of Dev Server
- **Severity:** P1
- **File:** `docker-compose.dev.yml:67-76`
- **Description:** The `docker-compose.dev.yml` file is intended for development but the frontend service builds the full production Dockerfile (multi-stage build to nginx). This means developers get no hot-reload for frontend changes. The backend correctly targets the `dev` stage with `target: dev`, but the frontend has no equivalent dev target.
- **Evidence:**
  ```yaml
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile     # <-- builds prod nginx image
    container_name: pdp-frontend
    ports:
      - "5174:80"
    depends_on:
      - backend
  ```
- **Fix:** Either: (a) add a `dev` stage to `frontend/Dockerfile` that runs `npm run dev` with Vite, or (b) override the command in compose to run Vite dev server with appropriate volume mounts:
  ```yaml
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: build  # stop at build stage (has node installed)
    command: ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
    volumes:
      - ./frontend/src:/app/src
    ports:
      - "5174:5174"
  ```

---

### Finding: Frontend depends_on Lacks Healthcheck Condition
- **Severity:** P1
- **File:** `docker-compose.dev.yml:73-75`
- **Description:** The frontend service uses `depends_on: - backend` without a `condition: service_healthy`. This means Docker Compose will start the frontend as soon as the backend container starts, not when it is actually ready. The backend has a HEALTHCHECK in its Dockerfile, but the compose file does not use it.
- **Evidence:**
  ```yaml
  frontend:
    depends_on:
      - backend          # No condition: service_healthy
  ```
  Compare with the backend service which correctly uses:
  ```yaml
  backend:
    depends_on:
      postgres:
        condition: service_healthy
  ```
- **Fix:**
  ```yaml
  frontend:
    depends_on:
      backend:
        condition: service_healthy
  ```

---

### Finding: No Frontend Tests in CI Pipeline
- **Severity:** P1
- **File:** `.github/workflows/ci.yml:90-115`
- **Description:** The CI pipeline runs ESLint, TypeScript type-checking, and a production build for the frontend, but there is no test step. The `package.json` does not even define a `test` script. For a production application, frontend unit/integration tests should be part of CI. The backend has `pytest` with coverage thresholds, but the frontend has nothing equivalent.
- **Evidence:**
  ```yaml
  frontend-checks:
    steps:
      - name: ESLint
        run: npm run lint
      - name: TypeScript type-check
        run: npx tsc -b
      - name: Production build
        run: npm run build
      # No test step
  ```
  ```json
  // package.json scripts -- no "test" script
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  }
  ```
- **Fix:** Add Vitest (or another test runner), create a `test` script in `package.json`, and add a test step to the CI workflow:
  ```yaml
  - name: Run tests
    run: npm test -- --coverage
  ```

---

### Finding: Frontend .dockerignore Whitelists .env.local
- **Severity:** P1
- **File:** `frontend/.dockerignore:8-9`
- **Description:** The frontend `.dockerignore` excludes `.env.*` but then explicitly re-includes `!.env.local`. This means `.env.local` will be copied into the Docker build context and potentially baked into the production image. Environment-specific files should never be included in Docker images.
- **Evidence:**
  ```
  .env
  .env.*
  !.env.local.example
  !.env.local
  ```
- **Fix:** Remove the `!.env.local` exception. Only the example file should be whitelisted:
  ```
  .env
  .env.*
  !.env.local.example
  ```

---

## P2 -- Medium

### Finding: Vite Source Maps Not Explicitly Disabled for Production
- **Severity:** P2
- **File:** `frontend/vite.config.ts`
- **Description:** The Vite configuration does not explicitly set `build.sourcemap` to `false`. While Vite defaults to no source maps in production, this should be explicitly configured to prevent accidental enablement (e.g., if a developer sets `VITE_SOURCEMAP=true` or if Vite changes defaults). Source maps in production expose application source code.
- **Evidence:**
  ```typescript
  export default defineConfig({
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 5174,
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
    // No build.sourcemap configuration
  })
  ```
- **Fix:** Add explicit source map configuration:
  ```typescript
  export default defineConfig({
    // ...existing config...
    build: {
      sourcemap: false,
    },
  })
  ```

---

### Finding: Root .gitignore Missing .coverage, dist/, and build/ Entries
- **Severity:** P2
- **File:** `.gitignore`
- **Description:** Beyond the `dist/` issue (covered in P0), the root `.gitignore` also does not exclude `.coverage`, `htmlcov/`, `build/`, `*.egg-info`, or `pytest_cache`. The `backend/.coverage` file is already tracked in git according to `git status`.
- **Evidence:**
  ```
  A  backend/.coverage
  ```
  The root `.gitignore` has no entries for these patterns.
- **Fix:** Add to `.gitignore`:
  ```gitignore
  # Test / build artifacts
  .coverage
  htmlcov/
  dist/
  build/
  *.egg-info/
  .pytest_cache/
  .mypy_cache/
  ```

---

### Finding: Stale File backend/=0.2.9 Tracked in Git
- **Severity:** P2
- **File:** `backend/=0.2.9`
- **Description:** Git status shows a file `backend/=0.2.9` staged for commit. This appears to be an artifact from a malformed `pip install` command (e.g., `pip install pymupdf4llm>=0.2.9` without quotes, which created a file named `=0.2.9`). This junk file should not be in the repository.
- **Evidence:**
  ```
  A  backend/=0.2.9
  ```
- **Fix:** Remove the file and unstage it:
  ```bash
  git rm --cached backend/=0.2.9
  rm backend/=0.2.9
  ```

---

### Finding: No Production Docker Compose File
- **Severity:** P2
- **File:** `docker-compose.yml` (deleted)
- **Description:** The root-level `docker-compose.yml` was deleted according to git status (`D docker-compose.yml`), and only `docker-compose.dev.yml` remains. There is no production-oriented compose file for staging/production deployments. While Cloud Run may be the production target, a production compose file is useful for local production-mode testing and CI integration testing.
- **Evidence:**
  ```
  D  docker-compose.yml
  ```
- **Fix:** If Cloud Run is the deployment target, document this clearly. Otherwise, create a `docker-compose.prod.yml` with production-appropriate settings (no debug, no volume mounts, proper resource limits).

---

### Finding: Backend Dev Stage Has No HEALTHCHECK
- **Severity:** P2
- **File:** `backend/Dockerfile:24-41`
- **Description:** The backend Dockerfile production stage has a proper `HEALTHCHECK` directive, but the `dev` stage (used by `docker-compose.dev.yml`) does not. While `docker-compose.dev.yml` does not use healthcheck conditions for the backend itself, the frontend's `depends_on` would benefit from it (see related P1 finding).
- **Evidence:**
  ```dockerfile
  # Development stage -- hot-reload, no non-root user, source mounted as volume
  FROM python:3.11-slim AS dev
  # ... no HEALTHCHECK
  EXPOSE 8000
  CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
  ```
- **Fix:** Add a HEALTHCHECK to the dev stage:
  ```dockerfile
  HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
      CMD curl -f http://localhost:8000/health || exit 1
  ```

---

### Finding: Nginx API Proxy Missing Timeouts and Body Size for Uploads
- **Severity:** P2
- **File:** `frontend/nginx.conf:36-42`
- **Description:** The nginx proxy pass to the backend API has no timeout configuration. The backend processes PDFs which can take up to 300 seconds (per `ANTHROPIC_TIMEOUT` and the frontend `VITE_API_TIMEOUT` of 300000ms). Nginx default proxy timeouts are 60 seconds, which means long-running API calls will be terminated by nginx before the backend completes.
- **Evidence:**
  ```nginx
  location /api/ {
      proxy_pass http://backend:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      # No proxy_read_timeout, proxy_send_timeout, proxy_connect_timeout
  }
  ```
- **Fix:** Add appropriate timeout directives:
  ```nginx
  location /api/ {
      proxy_pass http://backend:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_read_timeout 300s;
      proxy_send_timeout 300s;
      proxy_connect_timeout 10s;
      client_max_body_size 50M;
  }
  ```

---

## P3 -- Low

### Finding: Nginx /assets/ Location Overrides Server-Level Security Headers
- **Severity:** P3
- **File:** `frontend/nginx.conf:30-33`
- **Description:** The `/assets/` location block uses `add_header` which, per nginx behavior, overrides all `add_header` directives from the parent server block. This means static assets served from `/assets/` will have the `Cache-Control` header but will lose all security headers (`X-Frame-Options`, `X-Content-Type-Options`, etc.).
- **Evidence:**
  ```nginx
  location /assets/ {
      expires 1y;
      add_header Cache-Control "public, immutable";
      # Security headers from server block are NOT inherited
  }
  ```
- **Fix:** Either repeat the security headers in the `/assets/` block, or use the `more_set_headers` module from nginx-extras, or move security headers to an `include` file:
  ```nginx
  location /assets/ {
      expires 1y;
      add_header Cache-Control "public, immutable";
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  }
  ```

---

### Finding: CI Pipeline Does Not Build Docker Images
- **Severity:** P3
- **File:** `.github/workflows/ci.yml`
- **Description:** The CI pipeline runs linting, type-checking, and tests, but never builds the Docker images. A Dockerfile syntax error or a missing dependency in the Docker build would not be caught until deployment. Adding a `docker build` step would catch these issues early.
- **Evidence:** The workflow file has no `docker build` or `docker compose build` steps.
- **Fix:** Add a Docker build job:
  ```yaml
  docker-build:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-checks]
    steps:
      - uses: actions/checkout@v4
      - name: Build backend image
        run: docker build -t pdp-backend ./backend
      - name: Build frontend image
        run: docker build -t pdp-frontend ./frontend
  ```

---

### Finding: Backend .dockerignore Missing node_modules Entry
- **Severity:** P3
- **File:** `backend/.dockerignore`
- **Description:** While the backend is a Python project and unlikely to have `node_modules/`, best practice is to include it in `.dockerignore` as a safety measure, especially since the root `.dockerignore` does include it. This is a minor consistency issue.
- **Evidence:**
  ```
  # backend/.dockerignore -- no node_modules/ entry
  ```
- **Fix:** Add `node_modules/` to `backend/.dockerignore` for consistency.

---

## Passed Checks

The following checklist items passed review:

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Multi-stage builds | PASS | Both backend and frontend use multi-stage builds. Backend: builder -> dev/prod. Frontend: build -> nginx. Dev dependencies excluded from production images. |
| 2 | Non-root user in production | PASS | Backend creates `appuser` (UID 1000) with `USER appuser`. Frontend creates `appuser` (UID 1001) with `USER appuser`. |
| 3 | HEALTHCHECK directives | PASS | Backend prod: `curl -f http://localhost:8000/health`. Frontend: `wget -qO- http://127.0.0.1:80/nginx-health`. Both have interval, timeout, start-period, retries. |
| 4 | No secrets baked into images | PASS | No `ENV` with real secrets. No `COPY .env`. Settings use `pydantic_settings` with env vars. |
| 5 | .dockerignore coverage | PASS (partial) | All three `.dockerignore` files exclude `.env`, `.git`, tests, caches. Frontend excludes `dist/` and `node_modules/`. See P1 for `.env.local` exception. |
| 6 | Compose service dependencies | PARTIAL | Backend -> postgres uses `condition: service_healthy`. Frontend -> backend uses plain `depends_on` (see P1). |
| 7 | Volume mounts and networks | PASS | Named volumes for postgres data and uploads. Custom network `pdp-network`. Source code mounted for hot-reload in backend. |
| 10 | Nginx proxy_pass to backend | PASS | `location /api/` proxies to `http://backend:8000` with proper headers. |
| 11 | Nginx SPA routing | PASS | `try_files $uri $uri/ /index.html` in root location block. |
| 12 | Nginx gzip configuration | PASS | Gzip enabled with appropriate types, compression level 6, min length 256 bytes. |
| 14 | No hardcoded secrets in CI | PASS | CI uses `ci-test-secret-key-minimum-32-characters-long` for JWT (test-only value), and `localdevpassword` for postgres (dev-only). No production secrets. |
| 15 | CI caching | PASS | pip cache via `actions/setup-python` with `cache: pip`. npm cache via `actions/setup-node` with `cache: npm`. Both with correct `cache-dependency-path`. |
| 17 | VITE_ env var prefix | PASS | All frontend env vars use `VITE_` prefix: `VITE_API_BASE_URL`, `VITE_API_TIMEOUT`, `VITE_GOOGLE_OAUTH_CLIENT_ID`, `VITE_GOOGLE_REDIRECT_URI`, `VITE_ALLOWED_EMAIL_DOMAIN`. |

---

## Remediation Priority

1. **Immediate (P0):** Remove `frontend/dist/` from git tracking, add `dist/` to `.gitignore`. Add CSP and HSTS headers to nginx. Remove hardcoded GCP project ID default.
2. **This sprint (P1):** Add `client_max_body_size` to nginx. Fix frontend compose for dev workflow. Add healthcheck condition for frontend. Set up frontend test framework. Remove `.env.local` from `.dockerignore` whitelist.
3. **Next sprint (P2):** Explicitly disable source maps. Clean up `.gitignore`. Remove stale `=0.2.9` file. Add HEALTHCHECK to dev stage. Add nginx proxy timeouts. Decide on production compose file.
4. **Backlog (P3):** Fix nginx header inheritance in `/assets/`. Add Docker build to CI. Backend `.dockerignore` consistency.
