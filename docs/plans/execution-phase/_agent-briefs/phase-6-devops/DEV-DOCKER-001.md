# Agent Brief: DEV-DOCKER-001

**Agent ID:** DEV-DOCKER-001
**Agent Name:** Docker Agent
**Type:** Development
**Phase:** 6 - DevOps
**Context Budget:** 50,000 tokens

---

## Mission

Create Docker configurations for backend and frontend services with multi-stage builds and development compose files.

**IMPORTANT:** Local development uses Docker PostgreSQL 16. Production uses Neon PostgreSQL 16. The docker-compose.yml must match Neon's configuration for seamless migration. See `docs/00-prerequisites/SETUP_PROGRESS_CHECKLIST.md` Section 9 for migration strategy.

---

## Documentation to Read

### Primary
1. `docs/06-devops/LOCAL_DEVELOPMENT.md` - Local dev setup
2. `docs/06-devops/DEPLOYMENT_GUIDE.md` - Deployment requirements

---

## Dependencies

**Upstream:** None (DevOps entry point)
**Downstream:** DEV-CICD-001, DEV-CLOUDRUN-001

---

## Outputs

### `backend/Dockerfile`
### `frontend/Dockerfile`
### `docker-compose.yml`
### `docker-compose.dev.yml`

---

## Acceptance Criteria

1. **Backend Dockerfile:**
   - Multi-stage build
   - Python 3.11 base
   - Poetry for dependencies
   - Non-root user
   - Health check endpoint
   - Optimized layer caching

2. **Frontend Dockerfile:**
   - Multi-stage build
   - Node 20 for build
   - Nginx for serving
   - Static file caching headers
   - Gzip compression

3. **docker-compose.yml (production):**
   - Backend service
   - Frontend service
   - Network configuration
   - Volume mounts for persistence
   - Environment variable injection

4. **docker-compose.dev.yml:**
   - Hot reload for backend
   - Hot reload for frontend
   - Local PostgreSQL 16 (must match Neon version)
   - Encoding: UTF-8, Collation: C.UTF-8 (must match Neon)
   - Local Redis (if needed)
   - Volume mounts for code

5. **Security:**
   - No secrets in images
   - Non-root users
   - Minimal base images
   - Regular security updates

---

## Backend Dockerfile Structure

```dockerfile
# Stage 1: Dependencies
FROM python:3.11-slim as deps
...

# Stage 2: Build
FROM deps as build
...

# Stage 3: Production
FROM python:3.11-slim as production
...
```

---

## QA Pair: QA-DOCKER-001

---

**Begin execution.**
