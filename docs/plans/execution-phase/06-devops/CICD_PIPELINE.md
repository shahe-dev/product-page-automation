# CI/CD Pipeline Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Cloud Build Setup](#cloud-build-setup)
4. [Pipeline Configuration](#pipeline-configuration)
5. [Branch Strategy](#branch-strategy)
6. [Testing Stage](#testing-stage)
7. [Build Stage](#build-stage)
8. [Deployment Stage](#deployment-stage)
9. [Environment Management](#environment-management)
10. [Secrets Management](#secrets-management)
11. [Monitoring & Notifications](#monitoring--notifications)
12. [Troubleshooting](#troubleshooting)
13. [Security Considerations](#security-considerations)

---

## Overview

This guide covers the complete CI/CD pipeline for the PDP Automation system using Google Cloud Build. The pipeline automates testing, building, and deploying both backend and frontend components.

**Pipeline Architecture:**
- **Trigger**: Git push to GitHub repository
- **Test**: Run backend (pytest) and frontend (Vitest) tests
- **Build**: Create Docker image for backend, build static assets for frontend
- **Deploy**: Deploy backend to Cloud Run, frontend to Cloud Storage
- **Duration**: ~8-12 minutes (full pipeline)

**Environments:**
- **Development**: Feature branches (tests only, no deployment)
- **Staging**: `staging` branch → Staging environment
- **Production**: `main` branch → Production environment

---

## Prerequisites

### Required GCP Services

**1. Enable APIs:**
```bash
# Enable required GCP APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudscheduler.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled
```

**2. IAM Permissions:**
```bash
# Grant Cloud Build service account necessary permissions
export PROJECT_ID="YOUR-GCP-PROJECT-ID"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Cloud Run Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/run.admin

# Service Account User
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/iam.serviceAccountUser

# Storage Admin (for frontend deployment)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/storage.admin

# Secret Manager Secret Accessor
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### GitHub Repository Setup

**1. Connect GitHub to Cloud Build:**
```bash
# Navigate to Cloud Build in GCP Console
# https://console.cloud.google.com/cloud-build/triggers

# Click "Connect Repository"
# Select "GitHub (Cloud Build GitHub App)"
# Authenticate with GitHub
# Select repository: your-org/pdp-automation
# Click "Connect"
```

**2. Repository Structure:**
```
pdp-automation/
├── backend/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── src/
│   ├── tests/
│   ├── package.json
│   └── vite.config.ts
├── cloudbuild.yaml           # Main CI/CD pipeline
├── cloudbuild-staging.yaml   # Staging-specific config
└── README.md
```

---

## Cloud Build Setup

### Create Build Triggers

**1. Production Trigger (main branch):**
```bash
gcloud builds triggers create github \
  --name="deploy-production" \
  --repo-name="pdp-automation" \
  --repo-owner="your-org" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --substitutions="_ENVIRONMENT=production,_REGION=us-central1"
```

**2. Staging Trigger (staging branch):**
```bash
gcloud builds triggers create github \
  --name="deploy-staging" \
  --repo-name="pdp-automation" \
  --repo-owner="your-org" \
  --branch-pattern="^staging$" \
  --build-config="cloudbuild-staging.yaml" \
  --substitutions="_ENVIRONMENT=staging,_REGION=us-central1"
```

**3. Test Trigger (all PRs):**
```bash
gcloud builds triggers create github \
  --name="test-pull-requests" \
  --repo-name="pdp-automation" \
  --repo-owner="your-org" \
  --pull-request-pattern="^.*$" \
  --build-config="cloudbuild-test.yaml" \
  --comment-control="COMMENTS_ENABLED"
```

---

## Pipeline Configuration

### Main Pipeline (cloudbuild.yaml)

```yaml
# cloudbuild.yaml - Production Pipeline
substitutions:
  _ENVIRONMENT: production
  _REGION: us-central1
  _SERVICE_NAME: pdp-automation-api
  _FRONTEND_BUCKET: pdp-automation-web
  _MIN_INSTANCES: '1'
  _MAX_INSTANCES: '10'
  _MEMORY: 2Gi
  _CPU: '2'

steps:
  # ========================================
  # PHASE 1: TESTING
  # ========================================

  # Backend: Install dependencies
  - name: 'python:3.11-slim'
    id: 'backend-install'
    dir: 'backend'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "Installing backend dependencies..."
        pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt
    waitFor: ['-']

  # Backend: Run tests
  - name: 'python:3.11-slim'
    id: 'backend-test'
    dir: 'backend'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "Running backend tests..."
        pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

        # Run pytest with coverage
        pytest tests/ \
          --cov=app \
          --cov-report=term-missing \
          --cov-report=xml \
          --junitxml=test-results.xml \
          -v

        # Check coverage threshold (80%)
        coverage report --fail-under=80
    env:
      - 'ENVIRONMENT=test'
      - 'DATABASE_URL=sqlite:///./test.db'
    waitFor: ['backend-install']

  # Frontend: Install dependencies
  - name: 'node:18-alpine'
    id: 'frontend-install'
    dir: 'frontend'
    entrypoint: 'npm'
    args: ['ci']
    waitFor: ['-']

  # Frontend: Lint
  - name: 'node:18-alpine'
    id: 'frontend-lint'
    dir: 'frontend'
    entrypoint: 'npm'
    args: ['run', 'lint']
    waitFor: ['frontend-install']

  # Frontend: Run tests
  - name: 'node:18-alpine'
    id: 'frontend-test'
    dir: 'frontend'
    entrypoint: 'npm'
    args: ['run', 'test', '--', '--coverage', '--run']
    waitFor: ['frontend-install']

  # ========================================
  # PHASE 2: BUILD
  # ========================================

  # Backend: Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    id: 'backend-build'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:latest'
      - '-f'
      - 'backend/Dockerfile'
      - './backend'
    waitFor: ['backend-test']

  # Backend: Push Docker image
  - name: 'gcr.io/cloud-builders/docker'
    id: 'backend-push'
    args:
      - 'push'
      - '--all-tags'
      - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}'
    waitFor: ['backend-build']

  # Frontend: Build production bundle
  - name: 'node:18-alpine'
    id: 'frontend-build'
    dir: 'frontend'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "Building frontend for ${_ENVIRONMENT}..."
        npm run build

        # Verify build output
        ls -la dist/

        # Create build info
        echo "{
          \"version\": \"$SHORT_SHA\",
          \"environment\": \"${_ENVIRONMENT}\",
          \"buildTime\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
        }" > dist/build-info.json
    env:
      - 'VITE_API_BASE_URL=https://api.pdp-automation.com'
      - 'VITE_ENV=${_ENVIRONMENT}'
    secretEnv:
      - 'VITE_GOOGLE_OAUTH_CLIENT_ID'
    waitFor: ['frontend-test']

  # ========================================
  # PHASE 3: DEPLOYMENT
  # ========================================

  # Backend: Run database migrations
  - name: 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}:$SHORT_SHA'
    id: 'backend-migrate'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "Running database migrations..."
        alembic upgrade head
    secretEnv:
      - 'DATABASE_URL'
    waitFor: ['backend-push']

  # Backend: Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    id: 'backend-deploy'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - '${_SERVICE_NAME}'
      - '--image=gcr.io/$PROJECT_ID/${_SERVICE_NAME}:$SHORT_SHA'
      - '--region=${_REGION}'
      - '--platform=managed'
      - '--memory=${_MEMORY}'
      - '--cpu=${_CPU}'
      - '--min-instances=${_MIN_INSTANCES}'
      - '--max-instances=${_MAX_INSTANCES}'
      - '--timeout=300'
      - '--concurrency=80'
      - '--allow-unauthenticated'
      - '--set-env-vars=ENVIRONMENT=${_ENVIRONMENT}'
      - '--set-secrets=DATABASE_URL=database-url:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,JWT_SECRET_KEY=jwt-secret:latest,GOOGLE_OAUTH_CLIENT_SECRET=google-oauth-secret:latest'
      - '--service-account=pdp-api@${PROJECT_ID}.iam.gserviceaccount.com'
    waitFor: ['backend-migrate']

  # Frontend: Deploy to Cloud Storage
  - name: 'gcr.io/cloud-builders/gsutil'
    id: 'frontend-deploy'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "Deploying frontend to gs://${_FRONTEND_BUCKET}..."

        # Sync files (delete removed files)
        gsutil -m rsync -r -d frontend/dist/ gs://${_FRONTEND_BUCKET}/

        # Set cache headers for assets (1 year)
        gsutil -m setmeta \
          -h "Cache-Control:public, max-age=31536000, immutable" \
          gs://${_FRONTEND_BUCKET}/assets/**

        # Set cache headers for index.html (no cache)
        gsutil setmeta \
          -h "Cache-Control:no-cache, no-store, must-revalidate" \
          gs://${_FRONTEND_BUCKET}/index.html

        # Make all files publicly readable
        gsutil -m acl ch -r -u AllUsers:R gs://${_FRONTEND_BUCKET}

        echo "Deployment complete!"
    waitFor: ['frontend-build']

  # ========================================
  # PHASE 4: VERIFICATION
  # ========================================

  # Backend: Smoke test
  - name: 'gcr.io/cloud-builders/curl'
    id: 'backend-verify'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "Verifying backend deployment..."

        # Get service URL
        SERVICE_URL=$(gcloud run services describe ${_SERVICE_NAME} \
          --region=${_REGION} \
          --format='value(status.url)')

        echo "Service URL: $SERVICE_URL"

        # Health check
        for i in {1..5}; do
          if curl -f -s "$SERVICE_URL/health" | grep -q "healthy"; then
            echo "✓ Backend health check passed"
            exit 0
          fi
          echo "Waiting for service to be ready... ($i/5)"
          sleep 10
        done

        echo "✗ Backend health check failed"
        exit 1
    waitFor: ['backend-deploy']

  # Frontend: Verify deployment
  - name: 'gcr.io/cloud-builders/gsutil'
    id: 'frontend-verify'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "Verifying frontend deployment..."

        # Check index.html exists
        if gsutil ls gs://${_FRONTEND_BUCKET}/index.html; then
          echo "✓ Frontend index.html found"
        else
          echo "✗ Frontend index.html not found"
          exit 1
        fi

        # Check build-info.json
        if gsutil cat gs://${_FRONTEND_BUCKET}/build-info.json; then
          echo "✓ Frontend build info verified"
        else
          echo "✗ Frontend build info not found"
          exit 1
        fi
    waitFor: ['frontend-deploy']

# Available secrets from Secret Manager
availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/database-url/versions/latest
      env: 'DATABASE_URL'
    - versionName: projects/$PROJECT_ID/secrets/anthropic-api-key/versions/latest
      env: 'ANTHROPIC_API_KEY'
    - versionName: projects/$PROJECT_ID/secrets/google-oauth-client-id/versions/latest
      env: 'VITE_GOOGLE_OAUTH_CLIENT_ID'

# Build options
options:
  machineType: 'N1_HIGHCPU_8'
  diskSizeGb: 100
  logging: CLOUD_LOGGING_ONLY
  dynamicSubstitutions: true

# Build timeout
timeout: 1200s

# Build tags
tags:
  - 'pdp-automation'
  - '${_ENVIRONMENT}'
  - '$SHORT_SHA'
```

### Test-Only Pipeline (cloudbuild-test.yaml)

```yaml
# cloudbuild-test.yaml - PR Testing (No Deployment)
steps:
  # Backend tests
  - name: 'python:3.11-slim'
    dir: 'backend'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r requirements.txt -r requirements-dev.txt
        pytest tests/ --cov=app --cov-report=term-missing -v

  # Frontend tests
  - name: 'node:18-alpine'
    dir: 'frontend'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        npm ci
        npm run lint
        npm run test -- --coverage --run

options:
  machineType: 'N1_HIGHCPU_4'

timeout: 600s
```

### Staging Pipeline (cloudbuild-staging.yaml)

```yaml
# cloudbuild-staging.yaml - Staging Environment
substitutions:
  _ENVIRONMENT: staging
  _REGION: us-central1
  _SERVICE_NAME: pdp-automation-api-staging
  _FRONTEND_BUCKET: pdp-automation-web-staging
  _MIN_INSTANCES: '0'  # Scale to zero when idle
  _MAX_INSTANCES: '5'
  _MEMORY: 1Gi
  _CPU: '1'

# Use same steps as production but with staging substitutions
# (Include steps from cloudbuild.yaml here)
```

---

## Branch Strategy

### Git Flow

```
main (production)
  ↑
  └── staging (staging environment)
        ↑
        └── feature/* (PR, tests only)
        └── fix/* (PR, tests only)
        └── hotfix/* (emergency fixes)
```

**Branch Rules:**
- `main`: Protected, requires PR approval, triggers production deployment
- `staging`: Protected, requires PR approval, triggers staging deployment
- `feature/*`: Triggers test-only pipeline
- `fix/*`: Triggers test-only pipeline
- `hotfix/*`: Can merge directly to main after review

### Deployment Flow

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Develop and test locally
# (make changes)
git commit -m "feat: add new feature"

# 3. Push and create PR to staging
git push origin feature/new-feature
# Create PR: feature/new-feature → staging

# 4. Tests run automatically (Cloud Build)
# Review code, tests pass → Merge to staging

# 5. Staging deployment triggered
# Test in staging environment

# 6. Create PR to main
# Create PR: staging → main

# 7. Production deployment triggered
# Monitor production
```

---

## Testing Stage

### Backend Testing Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --junitxml=test-results.xml
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

**Coverage Requirements:**
- Minimum coverage: 80%
- Critical modules: 90%+ (auth, pdp generation)
- Test types: Unit, integration, end-to-end

### Frontend Testing Configuration

**vitest.config.ts:**
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/tests/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      statements: 80,
      branches: 80,
      functions: 80,
      lines: 80,
      exclude: [
        'node_modules/',
        'src/tests/',
        '**/*.config.ts'
      ]
    }
  }
});
```

---

## Build Stage

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Build Configuration

**vite.config.ts:**
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@headlessui/react', '@heroicons/react'],
          'utils-vendor': ['axios', '@tanstack/react-query']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
});
```

---

## Deployment Stage

### Cloud Run Configuration

**Service YAML (alternative to gcloud command):**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: pdp-automation-api
  namespace: YOUR-GCP-PROJECT-ID
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: '1'
        autoscaling.knative.dev/maxScale: '10'
        run.googleapis.com/cpu-throttling: 'false'
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      serviceAccountName: pdp-api@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com
      containers:
        - image: gcr.io/YOUR-GCP-PROJECT-ID/pdp-automation-api:latest
          resources:
            limits:
              memory: 2Gi
              cpu: '2'
          env:
            - name: ENVIRONMENT
              value: production
          envFrom:
            - secretRef:
                name: pdp-api-secrets
```

### Cloud Storage Configuration

```bash
# Create bucket
gsutil mb -p YOUR-GCP-PROJECT-ID -c STANDARD -l us-central1 gs://pdp-automation-web

# Enable website configuration
gsutil web set -m index.html -e index.html gs://pdp-automation-web

# Set CORS policy
echo '[{"origin":["*"],"method":["GET","HEAD"],"maxAgeSeconds":3600}]' > cors.json
gsutil cors set cors.json gs://pdp-automation-web

# Enable public access
gsutil iam ch allUsers:objectViewer gs://pdp-automation-web
```

---

## Environment Management

### Secret Manager Setup

```bash
# Create secrets
echo -n "postgresql+asyncpg://user:pass@host/db" | \
  gcloud secrets create database-url --data-file=-

echo -n "sk-your-anthropic-api-key" | \
  gcloud secrets create anthropic-api-key --data-file=-

echo -n "your-jwt-secret-key" | \
  gcloud secrets create jwt-secret --data-file=-

echo -n "your-google-oauth-secret" | \
  gcloud secrets create google-oauth-secret --data-file=-

echo -n "your-client-id.apps.googleusercontent.com" | \
  gcloud secrets create google-oauth-client-id --data-file=-

# Grant access to Cloud Build service account
for secret in database-url anthropic-api-key jwt-secret google-oauth-secret google-oauth-client-id; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

### Environment Variables

**Production:**
```bash
ENVIRONMENT=production
DATABASE_URL=secret:database-url
ANTHROPIC_API_KEY=secret:anthropic-api-key
JWT_SECRET_KEY=secret:jwt-secret
GCP_PROJECT_ID=YOUR-GCP-PROJECT-ID
CORS_ORIGINS=https://pdp-automation.com
```

**Staging:**
```bash
ENVIRONMENT=staging
DATABASE_URL=secret:database-url-staging
ANTHROPIC_API_KEY=secret:anthropic-api-key-dev
JWT_SECRET_KEY=secret:jwt-secret-staging
GCP_PROJECT_ID=YOUR-GCP-PROJECT-ID
CORS_ORIGINS=https://staging.pdp-automation.com
```

---

## Monitoring & Notifications

### Cloud Build Notifications

```bash
# Create Pub/Sub topic
gcloud pubsub topics create cloud-builds

# Create Slack notification
# (Requires Cloud Run service to forward to Slack webhook)
gcloud builds notifications create slack \
  --topic=cloud-builds \
  --slack-webhook-url=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Build Status Badge

```markdown
# Add to README.md
[![Build Status](https://storage.googleapis.com/YOUR_BUCKET/build-status.svg)](https://console.cloud.google.com/cloud-build/builds?project=YOUR-GCP-PROJECT-ID)
```

---

## Troubleshooting

### Common Build Failures

**Issue: Tests fail in CI but pass locally**
```bash
# Solution: Ensure test environment matches
# Check environment variables in cloudbuild.yaml
# Use same Python/Node versions
```

**Issue: Docker build fails (permission denied)**
```bash
# Solution: Grant Cloud Build service account container registry access
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/storage.admin
```

**Issue: Secret Manager access denied**
```bash
# Solution: Grant secretAccessor role
gcloud secrets add-iam-policy-binding <SECRET_NAME> \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### Debugging Builds

```bash
# View build logs
gcloud builds log <BUILD_ID>

# List recent builds
gcloud builds list --limit=10

# View build details
gcloud builds describe <BUILD_ID>

# Cancel running build
gcloud builds cancel <BUILD_ID>
```

---

## Security Considerations

**1. Service Account Permissions**
- Use minimal required permissions
- Separate service accounts for dev/staging/prod
- Regularly audit IAM policies

**2. Secret Management**
- Never commit secrets to Git
- Use Secret Manager for all sensitive data
- Rotate secrets regularly (every 90 days)

**3. Image Security**
- Scan Docker images for vulnerabilities
- Use official base images
- Keep dependencies updated

**4. Network Security**
- Restrict Cloud Run ingress
- Use VPC connectors for private resources
- Enable Cloud Armor for DDoS protection

**5. Audit Logging**
- Enable Cloud Audit Logs
- Monitor build activity
- Alert on suspicious patterns

---

**Last Updated**: 2026-01-15
**Maintained By**: DevOps Team
**Next Review**: 2026-04-15
