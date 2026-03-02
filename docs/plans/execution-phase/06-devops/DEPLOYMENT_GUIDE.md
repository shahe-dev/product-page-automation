# Production Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Infrastructure Setup](#infrastructure-setup)
5. [Database Deployment](#database-deployment)
6. [Backend Deployment](#backend-deployment)
7. [Frontend Deployment](#frontend-deployment)
8. [Domain & SSL Configuration](#domain--ssl-configuration)
9. [Post-Deployment Verification](#post-deployment-verification)
10. [Rollback Procedures](#rollback-procedures)
11. [Scaling Configuration](#scaling-configuration)
12. [Troubleshooting](#troubleshooting)
13. [Security Considerations](#security-considerations)

---

## Overview

This guide provides comprehensive instructions for deploying the PDP Automation system to production on Google Cloud Platform. The deployment uses a serverless architecture for maximum scalability and minimal operational overhead.

**Production Architecture:**
- **Backend**: FastAPI on Cloud Run (us-central1)
- **Frontend**: React SPA on Cloud Storage + Cloud CDN
- **Database**: Neon PostgreSQL (serverless, us-central-1)
- **Storage**: Cloud Storage (regional bucket)
- **AI**: Anthropic API (Claude Sonnet 4.5)
- **Monitoring**: Cloud Monitoring + Sentry
- **Domain**: Custom domain with SSL via Cloud Load Balancer

**Key Characteristics:**
- Zero-downtime deployments via traffic splitting
- Auto-scaling based on demand (min 1, max 10 instances)
- Multi-region disaster recovery capability
- Automated backups and point-in-time recovery

---

## Prerequisites

### Required Accounts & Access

**1. GCP Project:**
```bash
export PROJECT_ID="YOUR-GCP-PROJECT-ID"
export REGION="us-central1"

# Set default project
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

# Verify access
gcloud projects describe $PROJECT_ID
```

**2. Required Permissions:**
- Owner or Editor role on GCP project
- Cloud Run Admin
- Storage Admin
- Secret Manager Admin
- IAM Admin

**3. External Services:**
- Neon PostgreSQL account (https://neon.tech)
- Anthropic API account (https://console.anthropic.com)
- Google OAuth credentials (https://console.cloud.google.com/apis/credentials)
- Domain registrar access (for DNS configuration)
- Sentry account (https://sentry.io)

### Required Tools

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Verify installation
gcloud --version

# Install additional components
gcloud components install beta

# Authenticate
gcloud auth login
gcloud auth application-default login
```

---

## Pre-Deployment Checklist

### Infrastructure Checklist

- [ ] GCP project created and billing enabled
- [ ] Required APIs enabled (Cloud Run, Storage, Secret Manager, etc.)
- [ ] Service accounts created with proper IAM roles
- [ ] Neon PostgreSQL database created and accessible
- [ ] Anthropic API key obtained and validated
- [ ] Google OAuth credentials configured (Phase 0 - Critical!)
- [ ] Domain purchased and DNS accessible
- [ ] Sentry project created for error tracking

### Security Checklist

- [ ] All secrets stored in Secret Manager (never in code)
- [ ] Service account keys rotated
- [ ] IAM policies reviewed and minimized
- [ ] Google Workspace domain restriction enabled (@your-domain.com)
- [ ] CORS origins configured correctly
- [ ] Rate limiting configured
- [ ] Audit logging enabled

### Application Checklist

- [ ] Database schema migrations tested
- [ ] Environment variables documented
- [ ] API endpoints tested in staging
- [ ] Frontend build tested and optimized
- [ ] Authentication flow tested (Google OAuth)
- [ ] File upload/download tested
- [ ] AI generation tested (Anthropic integration)
- [ ] Email notifications configured

### Monitoring Checklist

- [ ] Cloud Monitoring dashboards created
- [ ] Alert policies configured
- [ ] Sentry DSN configured
- [ ] Log aggregation configured
- [ ] Uptime checks configured
- [ ] Notification channels configured (email, Slack)

---

## Infrastructure Setup

### 1. Enable Required APIs

```bash
# Enable all required GCP APIs
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudtasks.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  compute.googleapis.com \
  sql.googleapis.com \
  containerregistry.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled | grep -E "run|storage|secret"
```

### 2. Create Service Accounts

```bash
# Backend API service account
gcloud iam service-accounts create pdp-api \
  --display-name="PDP Automation API" \
  --description="Service account for Cloud Run backend"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:pdp-api@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:pdp-api@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:pdp-api@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.enqueuer"

# Frontend deployment service account
gcloud iam service-accounts create pdp-frontend-deploy \
  --display-name="PDP Frontend Deployer" \
  --description="Service account for frontend deployments"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:pdp-frontend-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

### 3. Create Storage Buckets

```bash
# Frontend assets bucket
gsutil mb -p $PROJECT_ID \
  -c STANDARD \
  -l $REGION \
  -b on \
  gs://pdp-automation-web

# User uploads bucket
gsutil mb -p $PROJECT_ID \
  -c STANDARD \
  -l $REGION \
  gs://pdp-automation-uploads

# Backups bucket
gsutil mb -p $PROJECT_ID \
  -c STANDARD \
  -l $REGION \
  gs://pdp-automation-backups

# Set lifecycle policies
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 90,
          "matchesPrefix": ["temp/"]
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://pdp-automation-uploads
```

### 4. Configure Secret Manager

```bash
# Database connection string
echo -n "postgresql+asyncpg://user:password@ep-xxxx.us-central-1.aws.neon.tech/neondb?sslmode=require" | \
  gcloud secrets create database-url \
  --data-file=- \
  --replication-policy="automatic"

# Anthropic API key
echo -n "sk-your-anthropic-api-key-here" | \
  gcloud secrets create anthropic-api-key \
  --data-file=- \
  --replication-policy="automatic"

# JWT secret key
openssl rand -base64 32 | tr -d '\n' | \
  gcloud secrets create jwt-secret \
  --data-file=- \
  --replication-policy="automatic"

# Google OAuth secret (Phase 0)
echo -n "your-google-oauth-client-secret" | \
  gcloud secrets create google-oauth-secret \
  --data-file=- \
  --replication-policy="automatic"

# Google OAuth client ID
echo -n "your-client-id.apps.googleusercontent.com" | \
  gcloud secrets create google-oauth-client-id \
  --data-file=- \
  --replication-policy="automatic"

# Sentry DSN
echo -n "https://your-sentry-dsn@sentry.io/project-id" | \
  gcloud secrets create sentry-dsn \
  --data-file=- \
  --replication-policy="automatic"

# Verify secrets
gcloud secrets list
```

---

## Database Deployment

### 1. Create Neon PostgreSQL Database

**Using Neon Console (https://console.neon.tech):**

1. Create new project: "PDP Automation Production"
2. Select region: AWS us-central-1 (closest to GCP us-central1)
3. PostgreSQL version: 15
4. Create database: `pdp_automation`

**Connection Details:**
```bash
# Save these values securely
NEON_HOST=ep-xxxx-xxxx.us-central-1.aws.neon.tech
NEON_DATABASE=neondb
NEON_USER=your_username
NEON_PASSWORD=your_password

# Full connection string
DATABASE_URL="postgresql+asyncpg://${NEON_USER}:${NEON_PASSWORD}@${NEON_HOST}/${NEON_DATABASE}?sslmode=require"
```

### 2. Configure Database

```bash
# Connect to database
psql "postgresql://${NEON_USER}:${NEON_PASSWORD}@${NEON_HOST}/${NEON_DATABASE}?sslmode=require"

# Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For indexing

# Create application user (if needed)
CREATE ROLE pdp_api WITH LOGIN PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE neondb TO pdp_api;

# Exit
\q
```

### 3. Run Database Migrations

```bash
# Clone repository
git clone https://github.com/your-org/pdp-automation.git
cd pdp-automation/backend

# Set up Python environment
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set database URL
export DATABASE_URL="postgresql+asyncpg://..."

# Run migrations
alembic upgrade head

# Verify current version
alembic current
# Output: (head)

# View migration history
alembic history --verbose
```

### 4. Seed Production Data

```bash
# Create admin user (Phase 0 - for initial setup)
python scripts/create_admin.py \
  --email admin@your-domain.com \
  --name "Admin User" \
  --role admin

# Create initial roles and permissions
python scripts/seed_roles.py

# Output:
# ✓ Created admin role
# ✓ Created manager role
# ✓ Created user role
```

### 5. Configure Database Backup (Neon)

**Neon provides automatic backups:**
- Continuous backup (point-in-time recovery)
- Retention: 7 days (free tier) or 30 days (paid)
- Restore via Neon console or API

**Manual backup script:**
```bash
#!/bin/bash
# scripts/backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pdp_automation_${DATE}.sql"

# Dump database
pg_dump "$DATABASE_URL" > "$BACKUP_FILE"

# Upload to Cloud Storage
gsutil cp "$BACKUP_FILE" gs://pdp-automation-backups/

# Clean up local file
rm "$BACKUP_FILE"

echo "Backup completed: gs://pdp-automation-backups/${BACKUP_FILE}"
```

---

## Backend Deployment

### 1. Build Docker Image

```bash
# Navigate to repository
cd pdp-automation

# Build Docker image
docker build -t gcr.io/$PROJECT_ID/pdp-automation-api:v1.0.0 ./backend

# Tag as latest
docker tag gcr.io/$PROJECT_ID/pdp-automation-api:v1.0.0 \
  gcr.io/$PROJECT_ID/pdp-automation-api:latest

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/pdp-automation-api:v1.0.0
docker push gcr.io/$PROJECT_ID/pdp-automation-api:latest

# Verify image
gcloud container images list --repository=gcr.io/$PROJECT_ID
```

### 2. Deploy to Cloud Run

```bash
# Deploy backend API
gcloud run deploy pdp-automation-api \
  --image=gcr.io/$PROJECT_ID/pdp-automation-api:v1.0.0 \
  --region=$REGION \
  --platform=managed \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=10 \
  --timeout=300 \
  --concurrency=80 \
  --port=8000 \
  --allow-unauthenticated \
  --service-account=pdp-api@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID},REGION=${REGION}" \
  --set-secrets="DATABASE_URL=database-url:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,JWT_SECRET_KEY=jwt-secret:latest,GOOGLE_OAUTH_CLIENT_SECRET=google-oauth-secret:latest,SENTRY_DSN=sentry-dsn:latest" \
  --labels="app=pdp-automation,tier=backend,env=production"

# Get service URL
gcloud run services describe pdp-automation-api \
  --region=$REGION \
  --format='value(status.url)'

# Output: https://pdp-automation-api-xxxx-uc.a.run.app
```

### 3. Configure Custom Domain for Backend

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service=pdp-automation-api \
  --domain=api.pdp-automation.com \
  --region=$REGION

# Get DNS records to configure
gcloud run domain-mappings describe \
  --domain=api.pdp-automation.com \
  --region=$REGION

# Add DNS records to your domain registrar:
# Type: A, Name: api, Value: <IP address>
# Type: AAAA, Name: api, Value: <IPv6 address>
```

### 4. Configure Traffic Splitting (Zero-Downtime Deployments)

```bash
# Deploy new version without traffic
gcloud run deploy pdp-automation-api \
  --image=gcr.io/$PROJECT_ID/pdp-automation-api:v1.1.0 \
  --region=$REGION \
  --no-traffic

# Gradually shift traffic (canary deployment)
gcloud run services update-traffic pdp-automation-api \
  --region=$REGION \
  --to-revisions=LATEST=10,PREVIOUS=90

# Monitor metrics, then shift more traffic
gcloud run services update-traffic pdp-automation-api \
  --region=$REGION \
  --to-revisions=LATEST=50,PREVIOUS=50

# Complete rollout
gcloud run services update-traffic pdp-automation-api \
  --region=$REGION \
  --to-latest
```

---

## Frontend Deployment

### 1. Build Production Bundle

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm ci --production=false

# Create production environment file
cat > .env.production <<EOF
VITE_API_BASE_URL=https://api.pdp-automation.com
VITE_GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
VITE_OAUTH_REDIRECT_URI=https://pdp-automation.com/auth/callback
VITE_ENV=production
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
EOF

# Build optimized production bundle
npm run build

# Verify build output
ls -lh dist/
# Should see: index.html, assets/, favicon.ico, etc.

# Test build locally (optional)
npm run preview
```

### 2. Deploy to Cloud Storage

```bash
# Sync files to Cloud Storage
gsutil -m rsync -r -d dist/ gs://pdp-automation-web/

# Set cache headers for assets (1 year cache)
gsutil -m setmeta \
  -h "Cache-Control:public, max-age=31536000, immutable" \
  'gs://pdp-automation-web/assets/**'

# Set cache headers for index.html (no cache)
gsutil setmeta \
  -h "Cache-Control:no-cache, no-store, must-revalidate" \
  -h "Pragma:no-cache" \
  -h "Expires:0" \
  gs://pdp-automation-web/index.html

# Set proper content types
gsutil -m setmeta -h "Content-Type:text/html" gs://pdp-automation-web/index.html
gsutil -m setmeta -h "Content-Type:text/css" 'gs://pdp-automation-web/assets/*.css'
gsutil -m setmeta -h "Content-Type:application/javascript" 'gs://pdp-automation-web/assets/*.js'

# Make bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://pdp-automation-web

# Verify deployment
gsutil ls -lh gs://pdp-automation-web/
```

### 3. Configure Website Hosting

```bash
# Set main page and error page
gsutil web set -m index.html -e index.html gs://pdp-automation-web

# Configure CORS (if needed)
cat > cors.json <<EOF
[
  {
    "origin": ["https://api.pdp-automation.com"],
    "method": ["GET", "HEAD", "POST"],
    "responseHeader": ["Content-Type", "Authorization"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://pdp-automation-web
```

### 4. Configure Load Balancer & CDN

```bash
# Reserve static IP address
gcloud compute addresses create pdp-web-ip \
  --global

# Get IP address
gcloud compute addresses describe pdp-web-ip \
  --global \
  --format='value(address)'

# Create backend bucket
gcloud compute backend-buckets create pdp-web-backend \
  --gcs-bucket-name=pdp-automation-web \
  --enable-cdn

# Create URL map
gcloud compute url-maps create pdp-web-url-map \
  --default-backend-bucket=pdp-web-backend

# Create managed SSL certificate
gcloud compute ssl-certificates create pdp-web-cert \
  --domains=pdp-automation.com,www.pdp-automation.com \
  --global

# Create HTTPS proxy
gcloud compute target-https-proxies create pdp-web-https-proxy \
  --url-map=pdp-web-url-map \
  --ssl-certificates=pdp-web-cert

# Create forwarding rule
gcloud compute forwarding-rules create pdp-web-https-rule \
  --address=pdp-web-ip \
  --global \
  --target-https-proxy=pdp-web-https-proxy \
  --ports=443

# Create HTTP to HTTPS redirect (optional)
gcloud compute url-maps create pdp-web-http-redirect \
  --default-url-redirect-redirect-response-code=301 \
  --default-url-redirect-https-redirect

gcloud compute target-http-proxies create pdp-web-http-proxy \
  --url-map=pdp-web-http-redirect

gcloud compute forwarding-rules create pdp-web-http-rule \
  --address=pdp-web-ip \
  --global \
  --target-http-proxy=pdp-web-http-proxy \
  --ports=80
```

---

## Domain & SSL Configuration

### 1. DNS Configuration

**Add DNS records at your domain registrar:**

```
# A record for root domain
Type: A
Name: @
Value: <static-ip-from-load-balancer>
TTL: 300

# A record for www subdomain
Type: A
Name: www
Value: <static-ip-from-load-balancer>
TTL: 300

# CNAME for backend API (if using Cloud Run domain mapping)
Type: CNAME
Name: api
Value: ghs.googlehosted.com
TTL: 300
```

### 2. Verify SSL Certificate Provisioning

```bash
# Check SSL certificate status
gcloud compute ssl-certificates describe pdp-web-cert \
  --global \
  --format='value(managed.status)'

# Wait for ACTIVE status (can take 10-60 minutes)
# Status: PROVISIONING → ACTIVE

# Verify certificate details
gcloud compute ssl-certificates describe pdp-web-cert \
  --global
```

### 3. Test HTTPS Connection

```bash
# Test SSL configuration
curl -I https://pdp-automation.com

# Expected response:
# HTTP/2 200
# content-type: text/html
# cache-control: no-cache
# ...

# Test SSL certificate
openssl s_client -connect pdp-automation.com:443 -servername pdp-automation.com

# Should show valid certificate chain
```

---

## Post-Deployment Verification

### 1. Backend Health Checks

```bash
# Test health endpoint
curl https://api.pdp-automation.com/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "database": "connected",
#   "timestamp": "2026-01-15T10:30:00Z"
# }

# Test API documentation
curl https://api.pdp-automation.com/docs
# Should return HTML for Swagger UI

# Test authentication (Phase 0)
curl https://api.pdp-automation.com/api/auth/login
# Should return OAuth redirect URL
```

### 2. Frontend Verification

```bash
# Test frontend loading
curl -I https://pdp-automation.com

# Expected response:
# HTTP/2 200
# content-type: text/html
# cache-control: no-cache
# x-goog-stored-content-length: <size>

# Test asset loading
curl -I https://pdp-automation.com/assets/index-xxxxx.js
# Should have cache-control: max-age=31536000
```

### 3. End-to-End Tests

**Manual Testing Checklist:**
- [ ] Navigate to https://pdp-automation.com
- [ ] Click "Login with Google" (Phase 0)
- [ ] Verify @your-domain.com domain restriction
- [ ] Create a new PDP
- [ ] Upload a file
- [ ] Generate AI content (Anthropic)
- [ ] Download PDP as PDF
- [ ] Test on mobile device
- [ ] Test in different browsers (Chrome, Firefox, Safari)

**Automated Testing:**
```bash
# Run E2E tests against production
cd frontend
npm run test:e2e:prod

# Or using Playwright
npx playwright test --config=playwright.prod.config.ts
```

### 4. Performance Verification

```bash
# Test API response time
time curl https://api.pdp-automation.com/health

# Expected: < 200ms

# Test frontend load time
curl -w "@curl-format.txt" -o /dev/null -s https://pdp-automation.com

# curl-format.txt:
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_starttransfer:  %{time_starttransfer}\n
time_total:  %{time_total}\n
```

### 5. Security Verification

```bash
# Test HTTPS redirect
curl -I http://pdp-automation.com
# Should return 301 redirect to https://

# Test CORS headers
curl -H "Origin: https://evil.com" https://api.pdp-automation.com/health
# Should not include Access-Control-Allow-Origin header

# Test domain restriction (Phase 0)
# Attempt login with non-@your-domain.com email
# Should be rejected
```

---

## Rollback Procedures

### Backend Rollback

**Option 1: Traffic Splitting (Instant)**
```bash
# Rollback to previous revision
gcloud run services update-traffic pdp-automation-api \
  --region=$REGION \
  --to-revisions=PREVIOUS=100

# Or to specific revision
gcloud run services update-traffic pdp-automation-api \
  --region=$REGION \
  --to-revisions=pdp-automation-api-00042-abc=100
```

**Option 2: Deploy Previous Image**
```bash
# Deploy previous Docker image version
gcloud run deploy pdp-automation-api \
  --image=gcr.io/$PROJECT_ID/pdp-automation-api:v1.0.0 \
  --region=$REGION
```

### Database Rollback

**Rollback Migration:**
```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# View revision history
alembic history

# Restore from Neon backup (if needed)
# Use Neon console: Project → Backups → Restore
```

### Frontend Rollback

**Restore Previous Deployment:**
```bash
# Option 1: Restore from backup
gsutil -m rsync -r -d gs://pdp-automation-backups/frontend-v1.0.0/ gs://pdp-automation-web/

# Option 2: Re-deploy previous version from Git
git checkout v1.0.0
cd frontend
npm ci
npm run build
gsutil -m rsync -r -d dist/ gs://pdp-automation-web/

# Clear CDN cache
gcloud compute url-maps invalidate-cdn-cache pdp-web-url-map \
  --path="/*"
```

---

## Scaling Configuration

### Backend Auto-Scaling

```bash
# Update scaling settings
gcloud run services update pdp-automation-api \
  --region=$REGION \
  --min-instances=1 \
  --max-instances=10 \
  --concurrency=80 \
  --cpu-throttling

# For higher traffic
gcloud run services update pdp-automation-api \
  --region=$REGION \
  --min-instances=3 \
  --max-instances=50 \
  --concurrency=80
```

### Database Scaling (Neon)

**Neon auto-scales automatically:**
- Compute: Auto-scales based on demand
- Storage: Auto-grows with data
- Max compute: Configurable in Neon console

**Manual configuration:**
1. Go to Neon console → Project → Settings
2. Adjust "Compute size" limits
3. Configure "Auto-suspend" delay

### CDN Caching

```bash
# Configure CDN cache settings
gcloud compute backend-buckets update pdp-web-backend \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC \
  --default-ttl=3600 \
  --max-ttl=86400

# Invalidate cache after deployment
gcloud compute url-maps invalidate-cdn-cache pdp-web-url-map \
  --path="/*" \
  --async
```

---

## Troubleshooting

### Backend Issues

**Issue: Service fails to start**
```bash
# Check logs
gcloud run services logs pdp-automation-api \
  --region=$REGION \
  --limit=50

# Common causes:
# - Database connection failure
# - Missing secrets
# - Invalid environment variables

# Verify secrets
gcloud secrets versions access latest --secret=database-url
```

**Issue: High latency**
```bash
# Check Cloud Run metrics
gcloud run services describe pdp-automation-api \
  --region=$REGION \
  --format='value(status.latestReadyRevisionName)'

# Increase resources
gcloud run services update pdp-automation-api \
  --region=$REGION \
  --memory=4Gi \
  --cpu=4
```

### Frontend Issues

**Issue: 404 on client-side routes**
```bash
# Ensure all routes serve index.html
gsutil web set -m index.html -e index.html gs://pdp-automation-web

# For Load Balancer, add URL rewrite rule
```

**Issue: Assets not loading**
```bash
# Check CORS configuration
gsutil cors get gs://pdp-automation-web

# Verify public access
gsutil iam get gs://pdp-automation-web
```

### Database Issues

**Issue: Connection pool exhausted**
```bash
# Increase max connections in Neon console
# Or reduce connection pool size in backend:
# DB_POOL_SIZE=10
# DB_MAX_OVERFLOW=5
```

---

## Security Considerations

**1. Service Accounts**
- Use minimal required permissions
- Rotate service account keys every 90 days
- Audit IAM policies regularly

**2. Secrets Management**
- All secrets in Secret Manager
- Enable secret rotation
- Never log secret values

**3. Network Security**
- Enable VPC Service Controls (optional)
- Configure Cloud Armor for DDoS protection
- Use private IPs for backend-to-database connections

**4. Authentication (Phase 0)**
- Google Workspace OAuth only
- Domain restriction: @your-domain.com
- Regular security audits

**5. Compliance**
- Enable audit logging
- Regular security scans
- Data encryption at rest and in transit
- GDPR/data protection compliance

---

**Last Updated**: 2026-01-15
**Maintained By**: DevOps Team
**Next Review**: 2026-04-15
