# Infrastructure

**Last Updated:** 2026-01-15
**Related Documents:**
- [System Architecture](./SYSTEM_ARCHITECTURE.md)
- [Security Architecture](./SECURITY_ARCHITECTURE.md)
- [DevOps](../06-devops/)

---

## Table of Contents

1. [Overview](#overview)
2. [Google Cloud Platform Setup](#google-cloud-platform-setup)
3. [Compute Resources](#compute-resources)
4. [Database](#database)
5. [Storage](#storage)
6. [AI/ML Services](#aiml-services)
7. [Integration Services](#integration-services)
8. [Observability](#observability)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Cost Estimation](#cost-estimation)
11. [Related Documentation](#related-documentation)

---

## Overview

The PDP Automation v.3 system is deployed entirely on **Google Cloud Platform (GCP)** with a serverless-first architecture. All infrastructure is managed using Infrastructure as Code (IaC) principles with Terraform and Cloud Build.

**GCP Project:**
- **Project ID:** `YOUR-GCP-PROJECT-ID`
- **Project Name:** `pdp-automation-dev`
- **Region:** `us-central1`
- **Environment:** Development

**Key Infrastructure Components:**
1. **Cloud Run** - Serverless container hosting (frontend + backend)
2. **Neon PostgreSQL** - Serverless database
3. **Cloud Storage** - Object storage for PDFs and images
4. **Anthropic API** - AI/ML services (external)
5. **Google Workspace APIs** - OAuth, Sheets, Drive
6. **Cloud Build** - CI/CD pipeline
7. **Cloud Monitoring** - Observability and logging

---

## Google Cloud Platform Setup

### Project Configuration

**Project Details:**
```bash
# Project information
gcloud config set project YOUR-GCP-PROJECT-ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  storage-api.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  cloudtasks.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  iam.googleapis.com
```

### Service Account

**Primary Service Account:**
```
pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com
```

**IAM Roles:**
```bash
# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.enqueuer"

gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"
```

**Permissions Summary:**
- `storage.objectAdmin` - Read/write GCS buckets
- `secretmanager.secretAccessor` - Read secrets
- `cloudtasks.enqueuer` - Enqueue background tasks
- `logging.logWriter` - Write logs to Cloud Logging

---

## Compute Resources

### Cloud Run Services

#### Backend API Service

**Service Name:** `pdp-automation-api`
**Runtime:** Python 3.10+ (FastAPI)
**Image:** `gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-api:latest`

**Configuration:**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: pdp-automation-api
  namespace: default
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      serviceAccountName: pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
        - image: gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-api:latest
          ports:
            - containerPort: 8000
          resources:
            limits:
              cpu: "2"
              memory: "2Gi"
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-url
                  key: latest
            - name: ANTHROPIC_API_KEY
              valueFrom:
                secretKeyRef:
                  name: anthropic-api-key
                  key: latest
            - name: GCS_BUCKET
              value: "pdp-automation-assets-dev"
            - name: ENVIRONMENT
              value: "development"
```

**Resource Allocation:**
- **CPU:** 2 vCPU (always allocated, no throttling)
- **Memory:** 2 GB RAM
- **Min Instances:** 1 (always warm, no cold starts)
- **Max Instances:** 10 (auto-scale based on traffic)
- **Container Concurrency:** 80 requests per instance
- **Timeout:** 300 seconds (5 minutes for long-running jobs)

**Scaling Behavior:**
```
Traffic < 80 requests → 1 instance
80-160 requests → 2 instances
160-240 requests → 3 instances
...
Max 10 instances (800 concurrent requests)
```

**Deployment Command:**
```bash
gcloud run deploy pdp-automation-api \
  --image gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-api:latest \
  --platform managed \
  --region us-central1 \
  --service-account pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com \
  --min-instances 1 \
  --max-instances 10 \
  --cpu 2 \
  --memory 2Gi \
  --timeout 300 \
  --allow-unauthenticated
```

#### Frontend Web Service

**Service Name:** `pdp-automation-web`
**Runtime:** Node.js 20+ (React + Vite)
**Image:** `gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-web:latest`

**Configuration:**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: pdp-automation-web
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "5"
    spec:
      serviceAccountName: pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com
      containerConcurrency: 100
      timeoutSeconds: 60
      containers:
        - image: gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-web:latest
          ports:
            - containerPort: 8080
          resources:
            limits:
              cpu: "1"
              memory: "512Mi"
          env:
            - name: API_URL
              value: "https://pdp-automation-api-XXXXXX-uc.a.run.app"
```

**Resource Allocation:**
- **CPU:** 1 vCPU
- **Memory:** 512 MB RAM
- **Min Instances:** 0 (can cold start for cost savings)
- **Max Instances:** 5
- **Container Concurrency:** 100 requests per instance
- **Timeout:** 60 seconds

**Deployment Command:**
```bash
gcloud run deploy pdp-automation-web \
  --image gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-web:latest \
  --platform managed \
  --region us-central1 \
  --service-account pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com \
  --min-instances 0 \
  --max-instances 5 \
  --cpu 1 \
  --memory 512Mi \
  --timeout 60 \
  --allow-unauthenticated
```

---

## Database

### Neon PostgreSQL (Serverless)

**Why Neon?**
- **Serverless:** Scales to zero when inactive (no 24/7 costs)
- **Cost-effective:** $0/month for development, $19/month for production
- **No migration:** Same connection string from dev to prod
- **Auto-scaling:** Automatically adjusts compute based on load
- **Automated backups:** Point-in-time recovery included

**Provider:** Neon (neon.tech)
**Region:** US East 1 (AWS)
**Version:** PostgreSQL 16

**Development Configuration:**
- **Tier:** Free
- **Storage:** 10 GB
- **Compute:** 1 vCPU, 1 GB RAM
- **Auto-pause:** After 5 minutes of inactivity
- **Connections:** 100 (connection pooling)

**Production Configuration:**
- **Tier:** Scale
- **Storage:** 100 GB
- **Compute:** 2 vCPU, 4 GB RAM
- **Auto-scaling:** 1-4 vCPU based on load
- **Connections:** 100 (pooled)
- **Backups:** Daily + point-in-time recovery (7 days)

**Connection String:**
```bash
# Stored in Secret Manager
postgresql://user:password@ep-abc-123.us-east-1.aws.neon.tech/pdp_automation?sslmode=require
```

**Connection Pooling:**
```python
# app/config/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

**Backup Strategy:**
- **Automated:** Daily backups at 2:00 AM UTC
- **Retention:** 7 days (development), 30 days (production)
- **Point-in-time recovery:** Up to 7 days
- **Manual backups:** Before major migrations

---

## Storage

### Google Cloud Storage

**Bucket Name:** `pdp-automation-assets-dev`
**Location:** `us-central1`
**Storage Class:** Standard
**Access:** Service account only (no public access)

**Directory Structure:**
```
gs://pdp-automation-assets-dev/
├── pdfs/
│   └── {job_id}/
│       └── original.pdf
├── images/
│   └── {job_id}/
│       ├── original/
│       │   ├── image_001.jpg
│       │   └── image_002.jpg
│       └── optimized/
│           ├── interior_001.webp
│           └── exterior_001.webp
├── floor_plans/
│   └── {job_id}/
│       ├── floor_plan_1br.jpg
│       └── floor_plan_2br.jpg
└── outputs/
    └── {job_id}/
        └── images.zip
```

**Lifecycle Policies:**
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 365,
          "matchesPrefix": ["pdfs/"]
        }
      }
    ]
  }
}
```

**Policy Explanation:**
- **PDFs:** Delete after 365 days (originals no longer needed)
- **Outputs:** Keep forever (processed assets for publication)

**Versioning:**
```bash
# Enable versioning
gsutil versioning set on gs://pdp-automation-assets-dev
```

**CORS Configuration:**
```json
[
  {
    "origin": ["https://pdp-automation.com"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
```

**Deployment:**
```bash
# Create bucket
gsutil mb -p YOUR-GCP-PROJECT-ID -c STANDARD -l us-central1 gs://pdp-automation-assets-dev

# Set lifecycle policy
gsutil lifecycle set lifecycle.json gs://pdp-automation-assets-dev

# Enable versioning
gsutil versioning set on gs://pdp-automation-assets-dev

# Set CORS
gsutil cors set cors.json gs://pdp-automation-assets-dev
```

---

## AI/ML Services

### Anthropic API

**Why Anthropic API?**
- Already have API credits and key
- Claude Sonnet 4.5: Excellent for document extraction and content generation
- Claude Sonnet 4.5: Multimodal vision for image classification and floor plans
- Simple REST API integration
- Upgradeable via API version parameter

**API Endpoint:** `https://api.anthropic.com/v1/chat/completions`

**Models Used:**

| Model | Use Cases | Context | Cost/1M tokens |
|-------|-----------|---------|----------------|
| Claude Sonnet 4.5 | Text extraction, content generation, QA | 128K | Input: $10, Output: $30 |
| Claude Sonnet 4.5 | Image classification, watermark detection, floor plans | 128K | Input: $5, Output: $15 |

**API Key Storage:**
```bash
# Store in Secret Manager
gcloud secrets create anthropic-api-key \
  --data-file=- \
  --replication-policy=automatic

# Grant access to service account
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**Rate Limiting:**
- Tier-dependent (varies by API usage)
- Implement exponential backoff for retries
- Queue requests during high load

**Cost Optimization:**
- Cache responses where possible (70-90% savings)
- Use Claude Sonnet 4.5 for vision tasks (cheaper than Claude Sonnet 4.5)
- Batch requests when feasible

---

## Integration Services

### Google Workspace APIs

#### 1. Google OAuth

**Purpose:** User authentication
**API:** OAuth 2.0
**Scope:** `openid email profile`

**OAuth Client Configuration:**
```bash
# Client ID and Secret stored in Secret Manager
gcloud secrets create google-oauth-client-id \
  --data-file=- \
  --replication-policy=automatic

gcloud secrets create google-oauth-client-secret \
  --data-file=- \
  --replication-policy=automatic
```

**Domain Restriction:**
- Only allow @your-domain.com domain
- Configured in Google Cloud Console > OAuth consent screen

#### 2. Google Sheets API

**Purpose:** Content output to templates
**API:** Google Sheets API v4
**Scope:** `https://www.googleapis.com/auth/spreadsheets`

**Usage:**
- Create new sheets from templates
- Batch update cells with generated content
- Share sheets with @your-domain.com organization

**Rate Limits:**
- 100 requests per 100 seconds per user
- 500 requests per 100 seconds per project

#### 3. Google Drive API

**Purpose:** File sharing
**API:** Google Drive API v3
**Scope:** `https://www.googleapis.com/auth/drive.file`

**Usage:**
- Share generated ZIPs with @your-domain.com organization
- Organization-wide access for images and floor plans

---

## Observability

### Cloud Logging

**Log Sink Configuration:**
```bash
# Create log sink for errors
gcloud logging sinks create pdp-automation-errors \
  storage.googleapis.com/pdp-automation-logs \
  --log-filter='severity>=ERROR'

# Create log sink for audit trail
gcloud logging sinks create pdp-automation-audit \
  storage.googleapis.com/pdp-automation-audit-logs \
  --log-filter='protoPayload.methodName=~"delete" OR protoPayload.methodName=~"export"'
```

**Log Retention:**
- **Application logs:** 30 days in Cloud Logging
- **Error logs:** 90 days in GCS
- **Audit logs:** 7 years in GCS (compliance)

### Cloud Monitoring

**Dashboards:**
1. **Service Health** - Response times, error rates, uptime
2. **Resource Usage** - CPU, memory, instance count
3. **Job Processing** - Job queue depth, processing time, success rate
4. **Database Performance** - Query latency, connection count, deadlocks

**Alerts:**
```yaml
# Error rate alert
displayName: "High Error Rate"
conditions:
  - displayName: "Error rate > 5%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"'
      comparison: COMPARISON_GT
      thresholdValue: 0.05
      duration: 300s
notificationChannels:
  - "projects/YOUR-GCP-PROJECT-ID/notificationChannels/1234567890"
```

**Notification Channels:**
- Email: dev-team@your-domain.com
- Slack: #pdp-automation-alerts (future)

### Sentry (Error Tracking)

**Purpose:** Detailed error tracking with context
**Integration:** Python SDK

**Configuration:**
```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    environment="development",
    traces_sample_rate=0.1,
    integrations=[FastApiIntegration()]
)
```

**Features:**
- Error grouping and deduplication
- Stack traces with local variables
- User context (user ID, email)
- Breadcrumbs (recent actions leading to error)
- Release tracking

---

## CI/CD Pipeline

### Cloud Build

**Trigger:** Push to `main` branch

**Build Configuration:**
```yaml
# cloudbuild.yaml
steps:
  # Build backend Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-api:$SHORT_SHA'
      - '-t'
      - 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-api:latest'
      - '-f'
      - 'backend/Dockerfile'
      - 'backend/'

  # Push backend image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-api:$SHORT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'pdp-automation-api'
      - '--image'
      - 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-api:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'

  # Build frontend Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-web:$SHORT_SHA'
      - '-t'
      - 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-web:latest'
      - '-f'
      - 'frontend/Dockerfile'
      - 'frontend/'

  # Push frontend image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-web:$SHORT_SHA']

  # Deploy frontend to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'pdp-automation-web'
      - '--image'
      - 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-web:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'

images:
  - 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-api:$SHORT_SHA'
  - 'gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-web:$SHORT_SHA'

timeout: '1200s'
```

**Deployment Stages:**
1. **Build** - Docker image build (5-10 minutes)
2. **Test** - Run unit tests (skipped for now)
3. **Push** - Push to Container Registry (1-2 minutes)
4. **Deploy** - Deploy to Cloud Run (2-3 minutes)
5. **Verify** - Health check (30 seconds)

**Total Deployment Time:** 10-15 minutes

---

## Cost Estimation

### Development Environment

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| Cloud Run (Backend) | 1 instance, 2GB RAM, 2 CPU | ~$50 |
| Cloud Run (Frontend) | 0-1 instances, 512MB RAM | ~$10 |
| Neon PostgreSQL | Free tier, 10 GB | $0 |
| Cloud Storage | 50 GB | ~$1 |
| Cloud Build | 120 builds/month | $0 (free tier) |
| Cloud Logging | 10 GB/month | $0 (free tier) |
| Cloud Monitoring | Basic metrics | $0 (free tier) |
| Anthropic API | 10M tokens/month | ~$100 |
| **Total** | | **~$161/month** |

### Production Environment

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| Cloud Run (Backend) | 2-5 instances, 2GB RAM | ~$150 |
| Cloud Run (Frontend) | 1-2 instances, 512MB | ~$30 |
| Neon PostgreSQL | Scale tier, 100 GB | $19 |
| Cloud Storage | 500 GB | ~$10 |
| Cloud Build | 120 builds/month | $0 (free tier) |
| Cloud Logging | 50 GB/month | ~$2 |
| Cloud Monitoring | Advanced metrics + alerts | ~$10 |
| Anthropic API | 50M tokens/month | ~$500 |
| **Total** | | **~$721/month** |

**Cost Optimization Strategies:**
1. Use min_instances=0 for frontend (cold start acceptable)
2. Cache Anthropic API responses (70-90% savings)
3. Delete old PDFs after 365 days
4. Use Claude Sonnet 4.5 for vision (cheaper than Claude Sonnet 4.5)

---

## Related Documentation

- [System Architecture](./SYSTEM_ARCHITECTURE.md) - Overall system design
- [Security Architecture](./SECURITY_ARCHITECTURE.md) - Security controls
- [DevOps](../06-devops/) - Deployment procedures

---

**Last Updated:** 2026-01-15
