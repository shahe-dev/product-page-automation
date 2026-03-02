# Phase 6a -- Local Validation & Due Diligence Guide

## Prerequisites

- Docker Desktop running
- Node 20+ installed locally
- Python 3.11+ installed locally
- `backend/.env` exists with valid values (copy from `backend/.env.example` if missing)

---

## 1. Docker Compose Smoke Test

```bash
# Start all services
docker compose -f docker-compose.dev.yml up -d --build

# Check all 3 containers are running
docker compose -f docker-compose.dev.yml ps

# Expected: pdp-postgres (healthy), pdp-backend (running), pdp-frontend (running)
```

**If postgres fails:** Check port 5432 is not already in use locally.

**If backend fails:** Check `docker logs pdp-backend` -- most likely a missing env var or DB connection issue. The backend requires a valid `backend/.env` file even though `docker-compose.dev.yml` sets `DATABASE_URL` explicitly, because `app.config.get_settings()` reads additional required vars.

**If frontend fails:** Check `docker logs pdp-frontend` -- likely a build failure. Run `cd frontend && npm run build` locally first to isolate.

---

## 2. Health Check Verification

```bash
# Backend health (requires DB connection)
curl http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected","environment":"development"}

# Frontend health (nginx)
curl http://localhost:5174/nginx-health
# Expected: ok

# Frontend serves HTML
curl -s http://localhost:5174 | head -5
# Expected: <!DOCTYPE html> ...
```

---

## 3. Backend Tests (run locally, not in Docker)

Create a virtual environment first (Docker containers don't need one, but local pytest/alembic does):

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=term-missing
```

Note: `.venv/` is excluded by `.dockerignore` and `.gitignore`.

Record the pass/fail count and coverage percentage. The CI threshold is 75%.

**Known issue:** Some tests may require a running postgres. If so, ensure Docker postgres is up:
```bash
docker compose -f docker-compose.dev.yml up -d postgres
```

---

## 4. Frontend Build Verification

```bash
cd frontend
npm ci
npm run lint
npx tsc -b --noEmit
npm run build
```

All four commands must exit 0. The `build` output goes to `frontend/dist/`.

---

## 5. Tear Down

```bash
docker compose -f docker-compose.dev.yml down
# Add -v to also delete the postgres volume if you want a clean slate
```

---

## Due Diligence Checklist

### Credential Alignment

| Location | User | Password | Status |
|----------|------|----------|--------|
| `docker-compose.yml` (root) | pdpuser | localdevpassword | Canonical |
| `docker-compose.dev.yml` | pdpuser | localdevpassword | Aligned |
| `.env.example` (root) | pdpuser | localdevpassword | Aligned |
| `backend/.env.example` | pdpuser | localdevpassword | Fixed (was pdp_user/pdp_password) |
| `backend/.env` | ? | ? | **VERIFY MANUALLY** -- may still have old creds |

**Action:** Open `backend/.env` and confirm `DATABASE_URL` uses `pdpuser:localdevpassword`. If it still has `pdp_user:pdp_password`, update it.

### Security Review

- [x] Backend Dockerfile: non-root user (`appuser`)
- [x] Frontend Dockerfile: non-root user (`appuser` via adduser)
- [x] No secrets baked into images (env vars injected at runtime)
- [x] `.dockerignore` excludes `.env`, `.credentials/`, `.git/`
- [x] Health check endpoints do not expose sensitive data
- [ ] **VERIFY:** `backend/.env` is in `.gitignore` (should already be, but confirm)

### Files Deleted

| File | Reason | Risk |
|------|--------|------|
| `backend/docker-compose.yml` | Superseded by `docker-compose.dev.yml` | Low -- had stale creds, deprecated `version` key, different network name |

If any script or documentation references `backend/docker-compose.yml`, update those references to `docker-compose.dev.yml` at the project root.

### CI Workflow Gaps

| Item | Status | Action Needed |
|------|--------|---------------|
| Backend lint (ruff) | Ready | None |
| Backend tests (pytest + coverage) | Ready | Ensure tests pass at 75%+ locally first |
| Frontend lint (eslint) | Ready | None |
| Frontend type-check (tsc) | Ready | None |
| Frontend build | Ready | None |
| Frontend unit tests (vitest) | **Not configured** | Add vitest to `package.json` when ready, then add test step to CI |
| Integration/E2E tests | Not in scope for 6a | Phase 7 |

### Backend Dockerfile Change

The `pip install --user` pattern was replaced with `pip install --prefix=/install` copied to `/usr/local`. This puts packages in the system Python path, accessible to all users including `appuser`. If the backend image fails to find packages at runtime, this is the first place to look.

### Docker Compose Dev Notes

- The frontend service runs the **production build** via nginx, not the Vite dev server. For hot-reload during active frontend development, run `npm run dev` outside Docker.
- The backend volume-mounts `app/` and `alembic/` for hot-reload via `uvicorn --reload`.
- The `env_file: ./backend/.env` in docker-compose.dev.yml means the backend container reads ALL vars from that file. The explicit `environment:` block overrides `DATABASE_URL` to use the Docker network hostname `postgres` instead of `localhost`.

---

## What Comes Next

### Phase 6b (Cloud Deployment) -- Deferred

- Cloud Run service configs
- Cloud Build pipeline
- Custom domain + SSL
- Min instances configuration

### Phase 6c (Monitoring) -- Deferred

- Sentry error tracking
- PagerDuty alerting
- Application metrics
- Log aggregation

### Immediate Next Steps After Validation

1. Run the smoke test above end-to-end
2. Fix any failures
3. Push branch, confirm GitHub Actions CI passes
4. If CI passes, Phase 6a is complete
