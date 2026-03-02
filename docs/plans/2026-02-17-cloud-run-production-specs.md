# PDP Automation v.3 -- Production Infrastructure Specifications & CI/CD Migration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Provision all infrastructure and deploy PDP Automation v.3 to Cloud Run with automated CI/CD via Cloud Build.

**Architecture:** FastAPI backend on Cloud Run, React SPA on Cloud Storage + Cloud CDN, any managed PostgreSQL 16+ database, Cloud Build for CI/CD triggered by GitHub pushes to `main`. All secrets via GCP Secret Manager.

**Tech Stack:** GCP Cloud Run, PostgreSQL 16+ (any provider), Cloud Storage, Cloud CDN, Cloud Build, Artifact Registry, Secret Manager, Google Cloud Tasks

---

## PART 1: IT TEAM PROVISIONING SPECIFICATIONS

This section is the handoff document for your IT team. It lists every resource, API, IAM role, networking rule, and external service access required to run this application in production.

---

### 1.0 Hardware Requirements Summary

| Component | CPU | RAM | Storage | Scaling | Notes |
|-----------|-----|-----|---------|---------|-------|
| **Backend containers** | 2 vCPU per instance | 2 GiB per instance | Stateless (no disk) | 0-10 instances, auto-scaled | PDF processing (PyMuPDF, OpenCV, Pillow) drives the 2 CPU / 2 GiB requirement. Lighter workloads could use 1 CPU / 1 GiB. |
| **Database** | 1 vCPU (shared OK) | 2 GB minimum | 10 GB SSD, auto-grow to 50 GB | Single instance (no HA needed) | PostgreSQL 16+. Internal tool with <50 concurrent users. JSONB-heavy queries benefit from 2 GB RAM. |
| **Frontend** | None (static files) | None | ~50 MB built assets | N/A | Served from Cloud Storage bucket. No compute. |
| **CI/CD build machine** | 8 vCPU (auto) | Auto | N/A | N/A | Cloud Build managed. E2_HIGHCPU_8 for Docker builds. |
| **Background task queue** | None (managed) | None | N/A | N/A | Cloud Tasks dispatches HTTP callbacks to the backend. |

**Why 2 vCPU / 2 GiB for backend?** The pipeline processes PDFs up to 200 MB. Steps include: PDF text extraction (PyMuPDF), image extraction + classification (OpenCV, Pillow), floor plan analysis, and concurrent Anthropic API calls. Peak memory during a large PDF: ~800 MB for the PDF buffer + extracted images + structured data in memory. The 2 GiB gives comfortable headroom. CPU-bound steps (image resizing, hash computation) benefit from 2 vCPU.

**Why 1 vCPU / 2 GB for database?** 22 tables with UUID primary keys, JSONB columns, GIN indexes, and full-text search. Typical concurrent connections: 10-30 (pool_size=5 x up to 10 backend instances, minus idle). A shared vCPU handles this fine. 2 GB RAM ensures JSONB field indexing and full-text search don't thrash.

---

### 1.1 GCP Project & Billing

| Item | Value |
|------|-------|
| GCP Project ID | `YOUR-GCP-PROJECT-ID` (existing) |
| Billing Account | Must be active with budget alert at $100/month |
| Region | `us-central1` (all GCP resources) |

---

### 1.2 GCP APIs to Enable

The following APIs must be enabled on the project. Some may already be active.

| API | Purpose |
|-----|---------|
| `run.googleapis.com` | Cloud Run (backend hosting) |
| `cloudbuild.googleapis.com` | Cloud Build (CI/CD pipeline) |
| `artifactregistry.googleapis.com` | Artifact Registry (Docker images) |
| `secretmanager.googleapis.com` | Secret Manager (already enabled) |
| `storage.googleapis.com` | Cloud Storage (already enabled) |
| `cloudtasks.googleapis.com` | Cloud Tasks (background job dispatch) |
| `compute.googleapis.com` | Compute Engine (required for Load Balancer, if custom domain) |
| `certificatemanager.googleapis.com` | Certificate Manager (SSL for custom domain, if applicable) |
| `dns.googleapis.com` | Cloud DNS (only if IT manages DNS via GCP) |
| `cloudresourcemanager.googleapis.com` | Resource Manager (IAM operations) |
| `iam.googleapis.com` | IAM (service account management) |
| `logging.googleapis.com` | Cloud Logging (already enabled) |
| `monitoring.googleapis.com` | Cloud Monitoring (uptime checks, alerts) |
| `sheets.googleapis.com` | Google Sheets API (template data read/write) |
| `drive.googleapis.com` | Google Drive API (asset upload/folder management) |

---

### 1.3 Service Account

| Item | Value |
|------|-------|
| Service Account | `pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com` (existing) |
| Key File | Not needed if workload identity is used on Cloud Run (recommended). Otherwise, generate JSON key and store in Secret Manager. |

**Required IAM Roles on the Runtime Service Account:**

| Role | Purpose |
|------|---------|
| `roles/secretmanager.secretAccessor` | Read secrets at runtime (already granted) |
| `roles/storage.objectAdmin` | Read/write to GCS buckets for assets and frontend (already granted) |
| `roles/cloudtasks.enqueuer` | Enqueue Cloud Tasks for background jobs (already granted) |
| `roles/logging.logWriter` | Write structured logs (already granted) |
| `roles/run.invoker` | (Optional) If Cloud Tasks callback needs to invoke Cloud Run |

**Cloud Build Service Account Roles** (on the default Cloud Build SA or a dedicated one):

| Role | Purpose |
|------|---------|
| `roles/run.admin` | Deploy new Cloud Run revisions |
| `roles/iam.serviceAccountUser` | Act as the runtime service account during deploy |
| `roles/artifactregistry.writer` | Push Docker images |
| `roles/storage.objectAdmin` | Deploy frontend to GCS bucket |
| `roles/secretmanager.secretAccessor` | Read DATABASE_URL during migration step |

---

### 1.4 Database: PostgreSQL 16+ (Provider-Agnostic)

The application requires a managed PostgreSQL database. **Any provider** that meets the requirements below works. The app connects via a single `DATABASE_URL` environment variable using a standard `postgresql+asyncpg://` connection string. Switching providers requires changing one secret -- zero code changes.

**Example providers:** NeonDB (currently used in development), Supabase, Aiven, Google Cloud SQL, AlloyDB, Amazon RDS, Railway, Render, or a self-managed PostgreSQL on a VM.

#### Minimum Requirements

| Requirement | Value | Why |
|-------------|-------|-----|
| Engine version | PostgreSQL 16+ | Uses `gen_random_uuid()` (built-in since PG 13), GIN indexes, JSONB, full-text search, `INET` type |
| CPU | 1 vCPU (shared OK) | <50 concurrent users, mostly CRUD with occasional JSONB queries |
| RAM | 2 GB minimum | GIN indexes on JSONB fields + full-text search index need working memory |
| Storage | 10 GB SSD minimum | 22 tables, mostly JSONB. Grows slowly (property data, not user-generated content at scale) |
| Storage auto-grow | Recommended, cap at 50 GB | Safety net |
| Max connections | 100+ | App uses connection pooling: pool_size=5, max_overflow=10 per backend instance. With 10 instances max = 150 peak connections. A connection pooler (PgBouncer) can reduce this. |
| SSL | Required | All connections must be encrypted in transit |
| Backups | Daily automated, 7-day retention minimum | Standard for any production database |
| Point-in-time recovery | Recommended | Nice to have for data safety, not strictly required |
| Maintenance window | Off-peak hours (e.g., Sunday 04:00 UTC) | Low-traffic internal tool |

#### Connection String Format

```
postgresql+asyncpg://USERNAME:PASSWORD@HOST:PORT/pdp_automation?sslmode=require
```

This value is stored as the `database-url` secret in GCP Secret Manager. The app auto-converts `postgresql://` to `postgresql+asyncpg://` if needed.

#### Schema Overview (22 tables)

| Table Group | Count | Tables | Key Features |
|-------------|-------|--------|--------------|
| Auth | 4 | `users`, `email_allowlist`, `refresh_tokens`, `oauth_states` | UUID PKs, INET type, email domain check constraint |
| Core | 8 | `projects`, `jobs`, `job_steps`, `prompts`, `prompt_versions`, `templates`, `project_images`, `project_floor_plans` | JSONB fields, GIN indexes, full-text search (GIN) |
| Workflow | 4 | `project_approvals`, `project_revisions`, `workflow_items`, `publication_checklists` | Audit trail, unique constraints |
| QA | 4 | `qa_checkpoints`, `qa_issues`, `qa_overrides`, `qa_comparisons` | Numeric scores, confidence decimals |
| Content | 4 | `extracted_data`, `generated_content`, `content_qa_results`, `material_packages`, `generation_runs` | Large JSONB for structured content, TEXT for raw extraction |
| Audit | 1 | `execution_history` | INET, JSONB, append-only |

**Migration tool:** Alembic (14 migration files). `alembic upgrade head` must run against the database before first deployment to create all tables and indexes.

---

### 1.5 Cloud Run Backend

| Specification | Value | Notes |
|---------------|-------|-------|
| Service Name | `pdp-backend` | |
| Region | `us-central1` | |
| Container Port | `8000` | FastAPI + Uvicorn |
| CPU | 2 vCPU | Required for PDF processing (PyMuPDF, OpenCV, Pillow) |
| Memory | 2 GiB | 200 MB PDF uploads + image processing in memory |
| Min Instances | 0 | Cost optimization; accepts 3-5s cold starts |
| Max Instances | 10 | Safety cap |
| Concurrency | 80 requests/container | |
| Request Timeout | 300s (5 min) | PDF extraction pipeline can take 2-3 minutes |
| Health Check | `GET /health` returns 200 | |
| Ingress | All traffic (public) | OAuth protects API endpoints |
| Authentication | Allow unauthenticated | App handles auth via JWT |
| Execution Environment | Gen2 (default) | |
| Service Account | `pdp-automation-sa@...` | |

**Database connection:** Standard TCP via `DATABASE_URL` env var (injected from Secret Manager). No special sidecar or proxy needed -- the app connects directly to the PostgreSQL host over SSL.

---

### 1.6 Cloud Storage Buckets

| Bucket | Purpose | Access | Notes |
|--------|---------|--------|-------|
| `pdp-automation-assets-dev` | Backend assets (PDFs, images, exports) | Private (service account only) | Already exists |
| `pdp-automation-frontend` | Frontend SPA static files | Public read (`allUsers` with `objectViewer`) | NEW -- needs creation |

**Frontend bucket configuration:**
- Uniform bucket-level access: Enabled
- Web hosting: `index.html` as main page, `index.html` as error page (SPA routing)
- CORS: Allow `GET` from `pdp.your-domain.com` and Cloud Run backend URL
- Cache: `no-cache` on `index.html`, `public, max-age=31536000, immutable` on `/assets/*`

---

### 1.7 Artifact Registry

| Specification | Value |
|---------------|-------|
| Repository Name | `pdp-automation` |
| Format | Docker |
| Region | `us-central1` |
| Cleanup Policy | Keep last 10 images per tag (optional, saves storage) |

---

### 1.8 Secret Manager Secrets

All secrets must exist in Secret Manager. The backend reads them at startup via environment variables.

| Secret Name | Description | Currently Exists? |
|-------------|-------------|-------------------|
| `database-url` | Standard PostgreSQL connection string (`postgresql+asyncpg://user:pass@host:port/dbname?sslmode=require`). Works with any PostgreSQL provider. | Yes |
| `anthropic-api-key` | Anthropic Claude API key | Yes |
| `jwt-secret-key` | JWT signing secret (min 32 chars, generate with `openssl rand -hex 32`) | Yes |
| `oauth-client-secret` | Google OAuth client secret | Yes |
| `google-drive-folder-id` | Google Drive root folder ID for generated documents | Yes |
| `internal-api-key` | Internal API key for Cloud Tasks callbacks (generate with `openssl rand -hex 32`) | **NEW -- must create** |

---

### 1.9 Cloud Tasks Queue

| Specification | Value |
|---------------|-------|
| Queue Name | `pdp-job-queue` (or existing name) |
| Region | `us-central1` |
| Max Dispatches Per Second | 10 |
| Max Concurrent Dispatches | 5 |
| Min Backoff | 10s |
| Max Backoff | 300s |
| Max Attempts | 3 |

The queue dispatches HTTP POST requests to the Cloud Run backend's internal callback endpoint (`/api/v1/internal/...`), authenticated via `INTERNAL_API_KEY` header.

---

### 1.10 Networking & Custom Domain

**Option A: No custom domain (cheapest)**
- Frontend URL: `https://storage.googleapis.com/pdp-automation-frontend/index.html`
- Backend URL: `https://pdp-backend-HASH-uc.a.run.app`
- Cost: $0 extra

**Option B: Custom domain `pdp.your-domain.com` (recommended)**
- Requires: External Application Load Balancer + Cloud CDN + SSL Certificate
- DNS: `pdp.your-domain.com` A record pointing to Load Balancer IP
- IT must configure DNS (or delegate a subdomain to Cloud DNS)
- Backend: Map `/api/*` to Cloud Run backend NEG
- Frontend: Map `/*` to GCS backend bucket

| Load Balancer Component | Specification |
|------------------------|---------------|
| Type | External Application Load Balancer (global) |
| Frontend IP | Static global IP (reserve one) |
| SSL Certificate | Google-managed certificate for `pdp.your-domain.com` |
| URL Map | `/api/*` -> Cloud Run NEG, `/*` -> GCS backend bucket |
| Cloud CDN | Enabled on frontend backend bucket only |

---

### 1.11 External Service Access (Firewall / Egress)

The Cloud Run backend makes outbound HTTPS calls to these services. If your corporate network or VPC has egress restrictions, these must be allowed.

| Service | Endpoints | Purpose |
|---------|-----------|---------|
| Anthropic API | `api.anthropic.com:443` | AI content generation (Claude) |
| Google Sheets API | `sheets.googleapis.com:443` | Read/write template data |
| Google Drive API | `www.googleapis.com:443`, `drive.googleapis.com:443` | File upload, folder creation |
| Google Cloud Storage | `storage.googleapis.com:443` | Asset storage |
| Google OAuth | `oauth2.googleapis.com:443`, `accounts.google.com:443` | User authentication |
| Google Cloud Tasks | `cloudtasks.googleapis.com:443` | Background job dispatch |
| Google Secret Manager | `secretmanager.googleapis.com:443` | Secret retrieval |
| PostgreSQL provider | Provider-specific hostname, port 5432 (typically) | Database connectivity. Example: `*.neon.tech:5432`, `*.supabase.co:5432`, or Cloud SQL private IP |

---

### 1.12 Google Workspace Permissions

The **service account** (`pdp-automation-sa@...`) needs access to:

| Resource | Permission | How to Grant |
|----------|------------|-------------|
| 6 Google Sheets (template spreadsheets) | Editor | Share each sheet with the service account email |
| 1 Google Drive Shared Drive or Folder | Contributor / Content Manager | Share the Drive folder with the service account email |

**Sheet IDs (non-secret, passed as env vars):**

| Template | Env Var | Sheet ID |
|----------|---------|----------|
| Aggregators | `TEMPLATE_SHEET_ID_AGGREGATORS` | `YOUR_AGGREGATORS_SHEET_ID` |
| OPR | `TEMPLATE_SHEET_ID_OPR` | `YOUR_OPR_SHEET_ID` |
| MPP | `TEMPLATE_SHEET_ID_MPP` | `YOUR_MPP_SHEET_ID` |
| ADOP | `TEMPLATE_SHEET_ID_ADOP` | `YOUR_ADOP_SHEET_ID` |
| ADRE | `TEMPLATE_SHEET_ID_ADRE` | `YOUR_ADRE_SHEET_ID` |
| Commercial | `TEMPLATE_SHEET_ID_COMMERCIAL` | `YOUR_COMMERCIAL_SHEET_ID` |

---

### 1.13 Google OAuth Configuration

| Item | Value | Notes |
|------|-------|-------|
| OAuth Client ID | `YOUR-OAUTH-CLIENT-ID.apps.googleusercontent.com` | Already configured |
| Authorized Redirect URIs | Must add production URI: `https://your-app.your-domain.com/auth/callback` (or Cloud Storage URL equivalent) | **IT / developer action required in Google Cloud Console** |
| Authorized JavaScript Origins | Must add: `https://your-app.your-domain.com` | **IT / developer action required** |
| Email domain restriction | `@your-domain.com` only | Enforced in app code + DB constraint |

---

### 1.14 Cloud Build Trigger

| Specification | Value |
|---------------|-------|
| Trigger Name | `deploy-production` |
| Source | GitHub repository (connected via Cloud Build GitHub App) |
| Branch | `^main$` (exact match) |
| Build Config | `cloudbuild.yaml` (in repo root) |
| Region | `us-central1` |

**GitHub App:** The [Google Cloud Build GitHub App](https://github.com/apps/google-cloud-build) must be installed on the repository and authorized for the GCP project.

---

### 1.15 Monitoring & Alerting

| Item | Specification |
|------|---------------|
| Uptime Check | HTTPS GET `https://pdp-backend-HASH.a.run.app/health` every 5 min |
| Budget Alert | $50 (50%), $90 (90%), $100 (100%) thresholds on project billing |
| Error Rate Alert | Notify if 5xx error rate > 5% over 5 min window |
| Latency Alert | Notify if p95 latency > 10s over 5 min window (PDF processing excluded) |
| Log-Based Alerts | Filter `severity>=ERROR` in Cloud Run logs |

---

### 1.16 Cost Estimate (Monthly)

| Service | Configuration | Est. Monthly Cost |
|---------|---------------|-------------------|
| Cloud Run Backend | min=0, max=10, 2 CPU, 2Gi, ~100K req/month | $12 |
| PostgreSQL Database | Varies by provider | $0-$30 (NeonDB free tier: $0; paid tiers: $19-$30; Cloud SQL small: $26; Supabase Pro: $25) |
| Cloud Storage (assets) | 5 GB stored, 20 GB egress | $3 |
| Cloud Storage (frontend) | 1 GB stored, 50 GB egress | $6 |
| Cloud CDN | 50 GB cache egress | $4 |
| Artifact Registry | 5 GB images | $0.50 |
| Secret Manager | 7 secrets, ~50K accesses | $0.15 |
| Cloud Build | 50 builds/month @ 10 min | $0.20 |
| Cloud Tasks | ~10K tasks/month | $0.01 |
| Load Balancer (if custom domain) | 5 forwarding rules, 50 GB | $22 |
| **Total (without LB, free DB)** | | **~$26/month** |
| **Total (with LB + paid DB)** | | **~$78/month** |

---

## PART 2: CI/CD MIGRATION IMPLEMENTATION PLAN

Everything below is the engineering work to be done once IT provisions the resources above.

---

### Task 1: Create .gcloudignore

**Files:**
- Create: `.gcloudignore`

**Step 1: Create the file**

```
.git/
.github/
.vscode/
.claude/
node_modules/
__pycache__/
*.pyc
.env
.env.*
docs/
*.md
qa_reports/
.coverage
backend/.coverage
frontend/dist/
backend/uploads/
floor-plan-tool/
ralph-wiggum-windows/
nul
tmp_openapi.json
```

**Step 2: Commit**

```bash
git add .gcloudignore
git commit -m "chore: add .gcloudignore for Cloud Build optimization"
```

---

### Task 2: Verify Frontend API URL Handling

**Files:**
- Verify: `frontend/src/lib/api.ts`
- Verify: `frontend/vite.config.ts`

**Step 1: Verify current behavior**

The frontend already uses `VITE_API_BASE_URL` env var:
```typescript
baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
```

In production with Cloud Storage hosting, the frontend can't proxy to the backend. The `VITE_API_BASE_URL` must be set at build time to the full Cloud Run backend URL (e.g., `https://pdp-backend-HASH.a.run.app/api/v1`).

No code change needed -- it already supports this.

**Step 2: Verify CORS allows production origin**

In `backend/app/config/settings.py`, the `ALLOWED_ORIGINS` field already accepts a comma-separated string from env vars. Cloud Run deploy will set:
```
ALLOWED_ORIGINS=https://your-app.your-domain.com,https://storage.googleapis.com
```

No code change needed.

---

### Task 3: Add INTERNAL_API_KEY to Secret Manager

**Files:**
- None (infrastructure only)

**Step 1: Generate and store the key**

```bash
# Generate a secure key
INTERNAL_KEY=$(openssl rand -hex 32)

# Store in Secret Manager
gcloud secrets create internal-api-key \
  --replication-policy="automatic"
echo -n "$INTERNAL_KEY" | gcloud secrets versions add internal-api-key --data-file=-
```

**Step 2: Grant access to service account**

```bash
gcloud secrets add-iam-policy-binding internal-api-key \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

### Task 4: Create cloudbuild.yaml

**Files:**
- Create: `cloudbuild.yaml`

**Step 1: Write the Cloud Build pipeline**

```yaml
# PDP Automation v.3 -- Cloud Build CI/CD Pipeline
# Triggers on push to main branch
# Steps: build backend -> push image -> run migrations -> deploy backend -> build frontend -> deploy frontend

substitutions:
  _REGION: us-central1
  _BACKEND_SERVICE: pdp-backend
  _FRONTEND_BUCKET: pdp-automation-frontend
  _ARTIFACT_REPO: pdp-automation
  _SERVICE_ACCOUNT: pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: E2_HIGHCPU_8

steps:
  # Step 1: Build backend Docker image
  - name: gcr.io/cloud-builders/docker
    id: build-backend
    args:
      - build
      - -t
      - ${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_ARTIFACT_REPO}/backend:${SHORT_SHA}
      - -t
      - ${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_ARTIFACT_REPO}/backend:latest
      - ./backend

  # Step 2: Push backend image to Artifact Registry
  - name: gcr.io/cloud-builders/docker
    id: push-backend
    waitFor: [build-backend]
    args:
      - push
      - --all-tags
      - ${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_ARTIFACT_REPO}/backend

  # Step 3: Run Alembic migrations against the database
  # DATABASE_URL is read from Secret Manager via --set-secrets
  - name: gcr.io/google.com/cloudsdktool/cloud-sdk
    id: run-migrations
    waitFor: [push-backend]
    entrypoint: bash
    args:
      - -c
      - |
        gcloud run jobs create migration-${SHORT_SHA} \
          --image=${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_ARTIFACT_REPO}/backend:${SHORT_SHA} \
          --region=${_REGION} \
          --service-account=${_SERVICE_ACCOUNT} \
          --set-secrets=DATABASE_URL=database-url:latest \
          --command="alembic","upgrade","head" \
          --max-retries=0 \
          --task-timeout=300s \
          --quiet
        gcloud run jobs execute migration-${SHORT_SHA} --region=${_REGION} --wait
        gcloud run jobs delete migration-${SHORT_SHA} --region=${_REGION} --quiet

  # Step 4: Deploy backend to Cloud Run
  - name: gcr.io/google.com/cloudsdktool/cloud-sdk
    id: deploy-backend
    waitFor: [run-migrations]
    entrypoint: bash
    args:
      - -c
      - |
        gcloud run deploy ${_BACKEND_SERVICE} \
          --image=${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_ARTIFACT_REPO}/backend:${SHORT_SHA} \
          --region=${_REGION} \
          --platform=managed \
          --allow-unauthenticated \
          --service-account=${_SERVICE_ACCOUNT} \
          --set-secrets=DATABASE_URL=database-url:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,JWT_SECRET=jwt-secret-key:latest,GOOGLE_CLIENT_SECRET=oauth-client-secret:latest,GOOGLE_DRIVE_ROOT_FOLDER_ID=google-drive-folder-id:latest,INTERNAL_API_KEY=internal-api-key:latest \
          --set-env-vars=ENVIRONMENT=production,DEBUG=false,GCP_PROJECT_ID=${PROJECT_ID},GCS_BUCKET_NAME=pdp-automation-assets-dev,ALLOWED_ORIGINS=https://your-app.your-domain.com,ALLOWED_EMAIL_DOMAIN=your-domain.com,GOOGLE_CLIENT_ID=YOUR-OAUTH-CLIENT-ID.apps.googleusercontent.com,TEMPLATE_SHEET_ID_AGGREGATORS=YOUR_AGGREGATORS_SHEET_ID,TEMPLATE_SHEET_ID_OPR=YOUR_OPR_SHEET_ID,TEMPLATE_SHEET_ID_MPP=YOUR_MPP_SHEET_ID,TEMPLATE_SHEET_ID_ADOP=YOUR_ADOP_SHEET_ID,TEMPLATE_SHEET_ID_ADRE=YOUR_ADRE_SHEET_ID,TEMPLATE_SHEET_ID_COMMERCIAL=YOUR_COMMERCIAL_SHEET_ID,GOOGLE_REDIRECT_URI=https://your-app.your-domain.com/auth/callback \
          --cpu=2 \
          --memory=2Gi \
          --min-instances=0 \
          --max-instances=10 \
          --port=8000 \
          --timeout=300s \
          --concurrency=80

  # Step 5: Get backend URL for frontend build
  - name: gcr.io/google.com/cloudsdktool/cloud-sdk
    id: get-backend-url
    waitFor: [deploy-backend]
    entrypoint: bash
    args:
      - -c
      - |
        BACKEND_URL=$(gcloud run services describe ${_BACKEND_SERVICE} --region=${_REGION} --format='value(status.url)')
        echo "$BACKEND_URL/api/v1" > /workspace/backend_url.txt
        echo "Backend URL: $BACKEND_URL"

  # Step 6: Build frontend with production API URL
  - name: node:20-alpine
    id: build-frontend
    waitFor: [get-backend-url]
    dir: frontend
    entrypoint: sh
    args:
      - -c
      - |
        VITE_API_BASE_URL=$(cat /workspace/backend_url.txt)
        export VITE_API_BASE_URL
        npm ci
        npm run build

  # Step 7: Deploy frontend to Cloud Storage
  - name: gcr.io/google.com/cloudsdktool/cloud-sdk
    id: deploy-frontend
    waitFor: [build-frontend]
    entrypoint: bash
    args:
      - -c
      - |
        gsutil -m rsync -r -d frontend/dist/ gs://${_FRONTEND_BUCKET}/
        gsutil -m setmeta -h "Cache-Control:public, max-age=31536000, immutable" "gs://${_FRONTEND_BUCKET}/assets/**"
        gsutil setmeta -h "Cache-Control:no-cache" "gs://${_FRONTEND_BUCKET}/index.html"

timeout: 1800s
```

**Step 2: Commit**

```bash
git add cloudbuild.yaml
git commit -m "feat: add Cloud Build CI/CD pipeline for Cloud Run deployment"
```

---

### Task 5: Update Google OAuth Redirect URI for Production

**Files:**
- No code changes needed

**Step 1: The GOOGLE_REDIRECT_URI is already configurable via env var**

The default is `http://localhost:5174/auth/callback`. In production, Cloud Run env var will override it to `https://your-app.your-domain.com/auth/callback`.

**Step 2: Update Google Cloud Console**

In Google Cloud Console > APIs & Services > Credentials > OAuth 2.0 Client IDs:
- Add `https://your-app.your-domain.com/auth/callback` to Authorized redirect URIs
- Add `https://your-app.your-domain.com` to Authorized JavaScript origins
- If using Cloud Storage URL directly (no custom domain), also add that URL

---

### Task 6: Create Artifact Registry Repository

**Files:** None (infrastructure only)

```bash
gcloud artifacts repositories create pdp-automation \
  --repository-format=docker \
  --location=us-central1 \
  --description="PDP Automation container images"
```

---

### Task 7: Create Frontend Storage Bucket

**Files:** None (infrastructure only)

```bash
gcloud storage buckets create gs://pdp-automation-frontend \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update gs://pdp-automation-frontend \
  --web-main-page-suffix=index.html \
  --web-error-page=index.html

gcloud storage buckets add-iam-policy-binding gs://pdp-automation-frontend \
  --member=allUsers \
  --role=roles/storage.objectViewer
```

---

### Task 8: Provision Database

**Files:** None (infrastructure only)

Use any PostgreSQL 16+ provider. Ensure:

1. Create a database named `pdp_automation`
2. Create an application user (not superuser) with full privileges on `pdp_automation`
3. Enable SSL connections
4. Note the connection string: `postgresql+asyncpg://USER:PASS@HOST:PORT/pdp_automation?sslmode=require`
5. Store the connection string in Secret Manager:

```bash
echo -n "postgresql+asyncpg://USER:PASS@HOST:PORT/pdp_automation?sslmode=require" | \
  gcloud secrets versions add database-url --data-file=-
```

6. Ensure the database host is reachable from Cloud Run (most managed providers are publicly accessible over SSL; if using a private network, configure VPC connector on Cloud Run)

---

### Task 9: Install Cloud Build GitHub App & Create Trigger

**Files:** None (infrastructure only)

**Step 1: Install GitHub App**
- Navigate to https://github.com/apps/google-cloud-build
- Install on the repository
- Authorize for GCP project `YOUR-GCP-PROJECT-ID`

**Step 2: Create trigger**

```bash
gcloud builds triggers create github \
  --name="deploy-production" \
  --repo-name="pdp-automation-v3" \
  --repo-owner="YOUR_GITHUB_ORG" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --region=us-central1
```

---

### Task 10: Manual First Deployment & Verification

**Step 1: Run initial deployment**

```bash
gcloud builds submit --config=cloudbuild.yaml --region=us-central1
```

**Step 2: Verify deployment**

```bash
# Backend health check
BACKEND_URL=$(gcloud run services describe pdp-backend --region=us-central1 --format='value(status.url)')
curl -s "$BACKEND_URL/health" | python -m json.tool

# Check Cloud Run logs for startup errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=pdp-backend" --limit=20 --format="table(timestamp,textPayload)"

# Verify frontend loads
curl -s "https://storage.googleapis.com/pdp-automation-frontend/index.html" | head -5
```

**Step 3: Smoke test checklist**

1. `curl $BACKEND_URL/health` returns 200
2. Backend logs show "Application configuration loaded" with `environment: production`
3. Frontend loads in browser at Cloud Storage URL
4. Login via Google OAuth works (redirect URI must be registered)
5. API calls from frontend to backend succeed (check browser Network tab)
6. No CORS errors in browser console
7. Create a test project to verify database writes work
8. Upload a test PDF to verify GCS access works

---

### Task 11: Set Up Monitoring

**Files:** None (infrastructure only)

```bash
# Budget alert
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="PDP Automation Budget" \
  --budget-amount=100 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100

# Uptime check
gcloud monitoring uptime create pdp-backend-health \
  --resource-type=uptime-url \
  --host=pdp-backend-HASH.a.run.app \
  --path=/health \
  --check-interval=300s
```

---

## PART 3: ROLLBACK PROCEDURES

### Backend Rollback

```bash
# List recent revisions
gcloud run revisions list --service=pdp-backend --region=us-central1 --limit=5

# Route 100% traffic to previous revision
gcloud run services update-traffic pdp-backend \
  --region=us-central1 \
  --to-revisions=PREVIOUS_REVISION=100
```

### Frontend Rollback

```bash
# Rebuild from previous commit
git checkout PREVIOUS_SHA -- frontend/
VITE_API_BASE_URL=https://... npm run build
gsutil -m rsync -r -d dist/ gs://pdp-automation-frontend/
```

### Database Rollback

```bash
# Alembic downgrade (run from backend container or locally with DATABASE_URL set)
alembic downgrade -1
```

---

## PART 4: ENVIRONMENT VARIABLES REFERENCE

Complete list of all environment variables the backend requires. Secrets are injected from Secret Manager; non-secrets are set as plain env vars on Cloud Run.

### From Secret Manager (sensitive)

| Env Var | Secret Name | Description |
|---------|-------------|-------------|
| `DATABASE_URL` | `database-url` | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | `anthropic-api-key` | Anthropic Claude API key |
| `JWT_SECRET` | `jwt-secret-key` | JWT signing key (min 32 chars) |
| `GOOGLE_CLIENT_SECRET` | `oauth-client-secret` | Google OAuth client secret |
| `GOOGLE_DRIVE_ROOT_FOLDER_ID` | `google-drive-folder-id` | Drive root folder ID |
| `INTERNAL_API_KEY` | `internal-api-key` | Cloud Tasks callback auth key |

### Plain Environment Variables (non-sensitive)

| Env Var | Value | Description |
|---------|-------|-------------|
| `ENVIRONMENT` | `production` | Runtime environment |
| `DEBUG` | `false` | Disable debug mode |
| `GCP_PROJECT_ID` | `YOUR-GCP-PROJECT-ID` | GCP project |
| `GCS_BUCKET_NAME` | `pdp-automation-assets-dev` | Asset storage bucket |
| `ALLOWED_ORIGINS` | `https://your-app.your-domain.com` | CORS allowed origins (comma-separated) |
| `ALLOWED_EMAIL_DOMAIN` | `your-domain.com` | OAuth email domain filter |
| `GOOGLE_CLIENT_ID` | `663387846263-...googleusercontent.com` | OAuth client ID |
| `GOOGLE_REDIRECT_URI` | `https://your-app.your-domain.com/auth/callback` | OAuth redirect URI |
| `TEMPLATE_SHEET_ID_AGGREGATORS` | `1rkD9WU-...` | Google Sheet ID |
| `TEMPLATE_SHEET_ID_OPR` | `1SBQOj3...` | Google Sheet ID |
| `TEMPLATE_SHEET_ID_MPP` | `1zJbKNr...` | Google Sheet ID |
| `TEMPLATE_SHEET_ID_ADOP` | `1GcEmNt...` | Google Sheet ID |
| `TEMPLATE_SHEET_ID_ADRE` | `1f8cqeN...` | Google Sheet ID |
| `TEMPLATE_SHEET_ID_COMMERCIAL` | `1jVHxZU...` | Google Sheet ID |
