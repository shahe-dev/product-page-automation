# Agent Briefing: DevOps Documentation Agent

**Agent ID:** devops-docs-agent
**Batch:** 3 (Operations)
**Priority:** P2 - Operations
**Est. Context Usage:** 36,000 tokens

---

## ⚠️ CRITICAL: Phase 0 Authentication Timing

**IMPORTANT:** Authentication setup was **MOVED FROM PHASE 8 TO PHASE 0** in the revised project plan. This is a key architectural decision.

**What this means for DevOps:**
- Authentication (Google Workspace OAuth, domain restriction, user roles) must be set up **BEFORE any feature development begins**
- Auth infrastructure is part of the foundation (Phase 0: Week 1-2), not a late addition
- This affects local development setup, CI/CD pipeline, and deployment procedures
- All documentation must reflect that auth is a **prerequisite**, not a post-development addition

**Phase 0: Security & Foundations (Week 1-2)**
- 0.2 Authentication (MOVED FROM PHASE 8):
  - Google Workspace OAuth
  - Domain restriction (@your-domain.com)
  - User roles table
  - Protected API routes

This timing change ensures developers have proper authentication context from day 1.

---

## Your Mission

Create **5 DevOps documentation files** covering local development, CI/CD, deployment, monitoring, and disaster recovery.

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/06-devops/`

---

## Files You Must Create

1. `LOCAL_DEVELOPMENT.md` (400-500 lines) - Complete dev environment setup
2. `CICD_PIPELINE.md` (300-350 lines) - Cloud Build configuration
3. `DEPLOYMENT_GUIDE.md` (400-500 lines) - Production deployment steps
4. `MONITORING_SETUP.md` (350-400 lines) - Sentry, Cloud Monitoring, alerts
5. `BACKUP_RECOVERY.md` (300-350 lines) - Backup strategy and DR plan

**Total Output:** ~1,750-2,100 lines across 5 files

---

## 1. Local Development Setup

**Prerequisites:**
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Git

**Backend Setup:**
```bash
# Clone repository
git clone https://github.com/your-org/pdp-automation.git
cd pdp-automation/backend

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Testing, linting

# Set up environment variables
cp .env.example .env
# Edit .env with your local settings

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

**Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local

# Start development server
npm run dev  # Runs on http://localhost:5174
```

**Docker Compose (Complete Stack):**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: pdp_automation
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://dev:dev123@postgres:5432/pdp_automation
      REDIS_URL: redis://redis:6379
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "5174:5174"
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
    depends_on:
      - backend

volumes:
  postgres_data:
```

**Environment Variables:**
```bash
# Backend .env
DEBUG=true
PORT=8000
DATABASE_URL=postgresql+asyncpg://dev:dev123@localhost:5432/pdp_automation
REDIS_URL=redis://localhost:6379
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account-dev.json
GCP_PROJECT_ID=pdp-automation-dev
GCS_BUCKET_NAME=pdp-automation-dev-assets
VERTEX_AI_LOCATION=us-central1
CORS_ORIGINS=http://localhost:5174
MAX_UPLOAD_SIZE_MB=50
SECRET_KEY=dev-secret-key-change-in-production

# Frontend .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_OAUTH_CLIENT_ID=your-dev-client-id.apps.googleusercontent.com
```

**VS Code Configuration:**
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

**Development Workflow:**
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Run tests: `pytest` (backend), `npm test` (frontend)
4. Run linting: `black .` + `flake8` (backend), `npm run lint` (frontend)
5. Commit: `git commit -m "feat: your feature"`
6. Push: `git push origin feature/your-feature`
7. Create PR

---

## 2. CI/CD Pipeline (Cloud Build)

**Trigger Configuration:**
```yaml
# cloudbuild.yaml
steps:
  # Backend tests
  - name: 'python:3.11'
    dir: 'backend'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        pytest tests/ --cov=app --cov-report=term-missing

  # Frontend tests
  - name: 'node:18'
    dir: 'frontend'
    entrypoint: 'npm'
    args: ['install']

  - name: 'node:18'
    dir: 'frontend'
    entrypoint: 'npm'
    args: ['run', 'test']

  # Build backend Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/pdp-api:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/pdp-api:latest'
      - './backend'

  # Push backend image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/pdp-api:$SHORT_SHA'

  # Deploy backend to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'pdp-automation-api'
      - '--image'
      - 'gcr.io/$PROJECT_ID/pdp-api:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

  # Build frontend
  - name: 'node:18'
    dir: 'frontend'
    entrypoint: 'npm'
    args: ['run', 'build']

  # Deploy frontend to Cloud Storage
  - name: 'gcr.io/cloud-builders/gsutil'
    args:
      - '-m'
      - 'rsync'
      - '-r'
      - '-d'
      - 'frontend/dist/'
      - 'gs://pdp-automation-web/'

timeout: 1200s
options:
  machineType: 'N1_HIGHCPU_8'
```

**Branch Policies:**
- `main` → Production deployment
- `staging` → Staging environment
- Feature branches → Run tests only (no deployment)

**GitHub Actions Alternative:**
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
      - name: Frontend tests
        run: |
          cd frontend
          npm install
          npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: pdp-automation-api
          image: gcr.io/${{ secrets.GCP_PROJECT }}/pdp-api:latest
```

---

## 3. Deployment Guide

**Production Deployment Checklist:**
- [ ] Environment variables configured in Secret Manager
- [ ] Database migrations tested
- [ ] Neon PostgreSQL database created and accessible
- [ ] Cloud Storage bucket created
- [ ] Service accounts configured
- [ ] Domain DNS configured
- [ ] Anthropic API key validated and stored in Secret Manager
- [ ] SSL certificates provisioned
- [ ] Monitoring alerts set up
- [ ] Backup schedule configured

**Backend Deployment:**
```bash
# Build and push Docker image
docker build -t gcr.io/pdp-automation-prod/pdp-api:v1.0.0 ./backend
docker push gcr.io/pdp-automation-prod/pdp-api:v1.0.0

# Deploy to Cloud Run
gcloud run deploy pdp-automation-api \
  --image gcr.io/pdp-automation-prod/pdp-api:v1.0.0 \
  --region us-central1 \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars "DATABASE_URL=secret:db-url" \
  --set-secrets="JWT_SECRET_KEY=jwt-secret:latest" \
  --allow-unauthenticated

# Run database migrations
gcloud run jobs execute migrate-db \
  --region us-central1 \
  --wait
```

**Frontend Deployment:**
```bash
# Build
cd frontend
npm run build

# Deploy to Cloud Storage
gsutil -m rsync -r -d dist/ gs://pdp-automation-web/

# Set cache control
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" \
  gs://pdp-automation-web/assets/**

gsutil -m setmeta -h "Cache-Control:no-cache" \
  gs://pdp-automation-web/index.html
```

**Database Migration:**
```bash
# Connect to Neon PostgreSQL (production)
export DATABASE_URL="postgresql://user:pass@ep-xxxxx.neon.tech/neondb?sslmode=require"

# Run migrations
cd backend
alembic upgrade head

# Verify
alembic current

# Test connection
psql "$DATABASE_URL" -c "SELECT version();"
```

**Rollback Procedure:**
```bash
# Rollback backend
gcloud run services update-traffic pdp-automation-api \
  --to-revisions=REVISION-NAME=100

# Rollback database
alembic downgrade -1

# Rollback frontend
gsutil -m rsync -r -d frontend-backup/ gs://pdp-automation-web/
```

---

## 4. Monitoring Setup

**Sentry (Error Tracking):**
```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
)
```

**Cloud Monitoring (Metrics):**
```python
# backend/app/middleware/monitoring.py
from prometheus_client import Counter, Histogram
from google.cloud import monitoring_v3

request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration'
)

@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start = time.time()

    response = await call_next(request)
    duration = time.time() - start

    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.observe(duration)

    return response
```

**Alert Policies:**
```yaml
# Cloud Monitoring alerts
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 5% for 5 minutes"
    notification: "page-oncall-engineer"

  - name: "Slow Response Time"
    condition: "p95_latency > 10s for 5 minutes"
    notification: "notify-team-slack"

  - name: "Anthropic API Quota"
    condition: "anthropic_api_usage > 80%"
    notification: "notify-team-email"

  - name: "Database Connection Pool"
    condition: "connection_pool_exhausted"
    notification: "page-oncall-engineer"
```

**Dashboard Metrics:**
- Request rate (req/s)
- Error rate (%)
- Response time (p50, p95, p99)
- Anthropic API calls/cost
- Database query performance
- Background job queue depth
- CPU/memory usage

**Log Aggregation:**
```python
# Cloud Logging integration
import google.cloud.logging

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

logger = logging.getLogger("app")
logger.info("This appears in Cloud Logging", extra={
    "user_id": user.id,
    "job_id": job_id,
    "trace_id": request.headers.get("X-Trace-ID")
})
```

---

## 5. Backup & Recovery

**Database Backups:**
- **Automated daily snapshots** at 3 AM UTC
- **Retention:** 30 days
- **Point-in-time recovery:** Up to 7 days
- **Cross-region replica:** us-west1

```bash
# Manual backup
gcloud sql backups create \
  --instance=pdp-db \
  --description="Pre-migration backup"

# Restore from backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=pdp-db \
  --backup-instance-zone=us-central1

# Export to Cloud Storage
gcloud sql export sql pdp-db \
  gs://pdp-backups/manual-export-$(date +%Y%m%d).sql \
  --database=pdp_automation
```

**File Storage Backups:**
- **Cross-region replication:** Enabled
- **Versioning:** Enabled (restore within 30 days)
- **Lifecycle:** Keep originals forever, delete temp files after 1 day

**Disaster Recovery Plan:**

**Scenario 1: Database Corruption**
1. Identify last known good backup (Neon provides automatic backups)
2. Restore from Neon backup using Neon console (point-in-time recovery)
3. Update backend connection string in Secret Manager if needed
4. Restart backend Cloud Run instances
5. **RTO:** 30 minutes, **RPO:** Point-in-time (Neon provides continuous backup)

**Scenario 2: Region Outage (us-central1)**
1. DNS failover to us-west1
2. Promote read replica to primary
3. Backend auto-scales in new region
4. **RTO:** 5 minutes, **RPO:** 0 (real-time replication)

**Scenario 3: Accidental Data Deletion**
1. Check Cloud Audit Logs for deletion event
2. Restore from latest snapshot
3. Apply transaction logs to recover recent data
4. **RTO:** 1 hour, **RPO:** Depends on when deleted

---

## Document Standards

Each DevOps document must include:
1. Prerequisites
2. Step-by-step instructions
3. Command examples (bash)
4. Configuration files (YAML, Dockerfile)
5. Verification steps
6. Troubleshooting section
7. Security considerations

---

## Quality Checklist

- ✅ All 5 files created
- ✅ Setup steps clear
- ✅ Code examples in Bash/YAML
- ✅ Environment variables documented
- ✅ CI/CD pipeline complete
- ✅ Monitoring configured
- ✅ Backup strategy defined
- ✅ DR plan with RTO/RPO

Begin with `LOCAL_DEVELOPMENT.md`.