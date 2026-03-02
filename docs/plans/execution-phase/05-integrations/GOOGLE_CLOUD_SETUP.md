# Google Cloud Platform Setup

## Overview

This guide provides complete instructions for setting up the Google Cloud Platform (GCP) infrastructure for PDP Automation v.3. The system uses multiple GCP services to deliver a scalable, serverless architecture with comprehensive monitoring and security.

**Project Details:**
- **GCP Project ID:** `YOUR-GCP-PROJECT-ID`
- **Region:** `us-central1`
- **Service Account:** `pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com`
- **Bucket:** `gs://pdp-automation-assets-dev`
- **Database:** Neon PostgreSQL (external, serverless)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Google Cloud Platform                    │
│  Project: YOUR-GCP-PROJECT-ID                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────┐      ┌─────────────┐     ┌──────────────┐  │
│  │ Cloud Run  │─────▶│ Cloud Tasks │────▶│ Secret Mgr   │  │
│  │ (Backend)  │      │ (Queue)     │     │ (API Keys)   │  │
│  └────────────┘      └─────────────┘     └──────────────┘  │
│         │                                                     │
│         ├──────────────────┬──────────────────┐             │
│         ▼                  ▼                  ▼             │
│  ┌────────────┐     ┌────────────┐    ┌────────────┐      │
│  │   Cloud    │     │   Cloud    │    │   Cloud    │      │
│  │  Storage   │     │ Monitoring │    │    Build   │      │
│  │   (GCS)    │     │  (Logs)    │    │   (CI/CD)  │      │
│  └────────────┘     └────────────┘    └────────────┘      │
│                                                               │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Neon PostgreSQL │
                   │   (External)    │
                   └─────────────────┘
```

## Prerequisites

Before starting, ensure you have:

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Project Owner or Editor** role
4. **Neon PostgreSQL** database created separately
5. **Anthropic API key** for Secret Manager storage

### Install gcloud CLI

```bash
# macOS
brew install google-cloud-sdk

# Windows (PowerShell)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### Authenticate gcloud

```bash
# Login to your Google account
gcloud auth login

# Set default project
gcloud config set project YOUR-GCP-PROJECT-ID

# Verify configuration
gcloud config list
```

## Step 1: Enable Required APIs

Enable all necessary Google Cloud APIs for the project:

```bash
# Enable core services
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  cloudtasks.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  compute.googleapis.com \
  --project=YOUR-GCP-PROJECT-ID

# Enable Google Workspace APIs
gcloud services enable \
  sheets.googleapis.com \
  drive.googleapis.com \
  oauth2.googleapis.com \
  --project=YOUR-GCP-PROJECT-ID

# Verify enabled APIs
gcloud services list --enabled --project=YOUR-GCP-PROJECT-ID
```

**Expected Output:**
```
NAME                                 TITLE
cloudbuild.googleapis.com            Cloud Build API
cloudresourcemanager.googleapis.com  Cloud Resource Manager API
cloudscheduler.googleapis.com        Cloud Scheduler API
cloudtasks.googleapis.com            Cloud Tasks API
compute.googleapis.com               Compute Engine API
drive.googleapis.com                 Google Drive API
iam.googleapis.com                   Identity and Access Management (IAM) API
logging.googleapis.com               Cloud Logging API
monitoring.googleapis.com            Cloud Monitoring API
oauth2.googleapis.com                Google OAuth2 API
run.googleapis.com                   Cloud Run API
secretmanager.googleapis.com         Secret Manager API
sheets.googleapis.com                Google Sheets API
storage.googleapis.com               Cloud Storage API
```

## Step 2: Create Service Account

Create a dedicated service account for the application:

```bash
# Create service account
gcloud iam service-accounts create pdp-automation-sa \
  --display-name="PDP Automation Service Account" \
  --description="Service account for PDP Automation v.3 backend services" \
  --project=YOUR-GCP-PROJECT-ID

# Verify creation
gcloud iam service-accounts list --project=YOUR-GCP-PROJECT-ID
```

**Expected Output:**
```
DISPLAY NAME                       EMAIL                                                           DISABLED
PDP Automation Service Account     pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com  False
```

## Step 3: Configure IAM Roles

Grant necessary permissions to the service account:

```bash
# Cloud Storage Admin (for file uploads/downloads)
gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Cloud Tasks Enqueuer (for job queue)
gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.enqueuer"

# Secret Manager Secret Accessor (for API keys)
gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Run Invoker (for service-to-service calls)
gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Logs Writer (for Cloud Logging)
gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# Monitoring Metric Writer (for custom metrics)
gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"

# Verify IAM policy
gcloud projects get-iam-policy YOUR-GCP-PROJECT-ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com"
```

## Step 4: Create Cloud Storage Bucket

Create the storage bucket with appropriate lifecycle policies:

```bash
# Create bucket in us-central1
gcloud storage buckets create gs://pdp-automation-assets-dev \
  --location=us-central1 \
  --uniform-bucket-level-access \
  --project=YOUR-GCP-PROJECT-ID

# Set lifecycle policy for automatic cleanup
cat > lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 365,
          "matchesPrefix": ["uploads/"]
        }
      },
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 1,
          "matchesPrefix": ["temp/"]
        }
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {
          "age": 90,
          "matchesPrefix": ["processed/"]
        }
      }
    ]
  }
}
EOF

# Apply lifecycle policy
gcloud storage buckets update gs://pdp-automation-assets-dev \
  --lifecycle-file=lifecycle.json

# Set CORS policy for frontend uploads
cat > cors.json << 'EOF'
[
  {
    "origin": ["https://pdp-automation-frontend-*.run.app"],
    "method": ["GET", "POST", "PUT"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gcloud storage buckets update gs://pdp-automation-assets-dev \
  --cors-file=cors.json

# Verify bucket configuration
gcloud storage buckets describe gs://pdp-automation-assets-dev
```

## Step 5: Configure Secret Manager

Store sensitive credentials in Secret Manager:

```bash
# Create secret for Anthropic API key
echo -n "sk-your-anthropic-api-key-here" | gcloud secrets create anthropic-api-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=YOUR-GCP-PROJECT-ID

# Create secret for Neon database URL
echo -n "postgresql://user:password@ep-xxxx.neon.tech/neondb?sslmode=require" | \
  gcloud secrets create database-url \
  --data-file=- \
  --replication-policy="automatic" \
  --project=YOUR-GCP-PROJECT-ID

# Create secret for JWT secret key
openssl rand -base64 32 | gcloud secrets create jwt-secret-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=YOUR-GCP-PROJECT-ID

# Create secret for Google OAuth credentials
cat > google-oauth-credentials.json << 'EOF'
{
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret",
  "redirect_uris": ["https://your-app.run.app/api/auth/callback"]
}
EOF

gcloud secrets create google-oauth-credentials \
  --data-file=google-oauth-credentials.json \
  --replication-policy="automatic" \
  --project=YOUR-GCP-PROJECT-ID

# Create secret for Google Sheets service account
gcloud secrets create google-sheets-credentials \
  --data-file=sheets-service-account.json \
  --replication-policy="automatic" \
  --project=YOUR-GCP-PROJECT-ID

# Grant service account access to all secrets
for secret in anthropic-api-key database-url jwt-secret-key google-oauth-credentials google-sheets-credentials; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=YOUR-GCP-PROJECT-ID
done

# List all secrets
gcloud secrets list --project=YOUR-GCP-PROJECT-ID
```

## Step 6: Create Cloud Tasks Queue

Set up the job processing queue:

```bash
# Create Cloud Tasks queue
gcloud tasks queues create pdp-job-queue \
  --location=us-central1 \
  --max-dispatches-per-second=10 \
  --max-concurrent-dispatches=5 \
  --max-attempts=3 \
  --min-backoff=60s \
  --max-backoff=3600s \
  --project=YOUR-GCP-PROJECT-ID

# Verify queue creation
gcloud tasks queues describe pdp-job-queue \
  --location=us-central1 \
  --project=YOUR-GCP-PROJECT-ID
```

**Expected Output:**
```
name: projects/YOUR-GCP-PROJECT-ID/locations/us-central1/queues/pdp-job-queue
rateLimits:
  maxConcurrentDispatches: 5
  maxDispatchesPerSecond: 10.0
retryConfig:
  maxAttempts: 3
  maxBackoff: 3600s
  maxDoublings: 16
  minBackoff: 60s
state: RUNNING
```

## Step 7: Deploy Backend to Cloud Run

Deploy the FastAPI backend service:

```bash
# Build container image
cd backend
gcloud builds submit --tag gcr.io/YOUR-GCP-PROJECT-ID/pdp-backend:latest \
  --project=YOUR-GCP-PROJECT-ID

# Deploy to Cloud Run
gcloud run deploy pdp-backend \
  --image gcr.io/YOUR-GCP-PROJECT-ID/pdp-backend:latest \
  --platform managed \
  --region us-central1 \
  --service-account pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --max-instances 10 \
  --min-instances 1 \
  --concurrency 80 \
  --port 8000 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=YOUR-GCP-PROJECT-ID,GCS_BUCKET_NAME=pdp-automation-assets-dev" \
  --set-secrets "DATABASE_URL=database-url:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,JWT_SECRET_KEY=jwt-secret-key:latest" \
  --allow-unauthenticated \
  --project=YOUR-GCP-PROJECT-ID

# Get service URL
gcloud run services describe pdp-backend \
  --region us-central1 \
  --format="value(status.url)" \
  --project=YOUR-GCP-PROJECT-ID
```

## Step 8: Deploy Frontend to Cloud Run

Deploy the React frontend:

```bash
# Build frontend with backend URL
cd frontend
VITE_API_URL=$(gcloud run services describe pdp-backend \
  --region us-central1 \
  --format="value(status.url)" \
  --project=YOUR-GCP-PROJECT-ID)

# Create Dockerfile for frontend
cat > Dockerfile << 'EOF'
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOF

# Build and deploy
gcloud builds submit --tag gcr.io/YOUR-GCP-PROJECT-ID/pdp-frontend:latest \
  --build-arg VITE_API_URL=$VITE_API_URL \
  --project=YOUR-GCP-PROJECT-ID

gcloud run deploy pdp-frontend \
  --image gcr.io/YOUR-GCP-PROJECT-ID/pdp-frontend:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5 \
  --min-instances 0 \
  --port 8080 \
  --allow-unauthenticated \
  --project=YOUR-GCP-PROJECT-ID
```

## Step 9: Configure Cloud Monitoring

Set up monitoring and alerting:

```bash
# Create log-based metric for errors
gcloud logging metrics create backend_errors \
  --description="Count of backend error logs" \
  --log-filter='resource.type="cloud_run_revision"
    resource.labels.service_name="pdp-backend"
    severity>=ERROR' \
  --project=YOUR-GCP-PROJECT-ID

# Create uptime check for backend
gcloud monitoring uptime-checks create https-uptime-check \
  --display-name="PDP Backend Uptime" \
  --resource-type=uptime-url \
  --monitored-resource=url \
  --host=$(gcloud run services describe pdp-backend \
    --region us-central1 \
    --format="value(status.url)" \
    --project=YOUR-GCP-PROJECT-ID | sed 's|https://||') \
  --path=/health \
  --period=60 \
  --timeout=10s \
  --project=YOUR-GCP-PROJECT-ID

# Create notification channel (email)
gcloud alpha monitoring channels create \
  --display-name="PDP Alerts Email" \
  --type=email \
  --channel-labels=email_address=alerts@your-domain.com \
  --project=YOUR-GCP-PROJECT-ID

# Create alert policy for high error rate
CHANNEL_ID=$(gcloud alpha monitoring channels list \
  --filter="displayName='PDP Alerts Email'" \
  --format="value(name)" \
  --project=YOUR-GCP-PROJECT-ID)

gcloud alpha monitoring policies create \
  --notification-channels=$CHANNEL_ID \
  --display-name="High Error Rate Alert" \
  --condition-display-name="Error count > 10" \
  --condition-threshold-value=10 \
  --condition-threshold-duration=300s \
  --condition-metric-filter='metric.type="logging.googleapis.com/user/backend_errors"
    resource.type="cloud_run_revision"' \
  --project=YOUR-GCP-PROJECT-ID
```

## Step 10: Configure Cloud Build (CI/CD)

Set up automatic deployments from GitHub:

```bash
# Connect GitHub repository
gcloud beta builds triggers create github \
  --name=pdp-backend-deploy \
  --repo-name=pdp-automation \
  --repo-owner=your-github-org \
  --branch-pattern="^main$" \
  --build-config=backend/cloudbuild.yaml \
  --project=YOUR-GCP-PROJECT-ID

# Create cloudbuild.yaml for backend
cat > backend/cloudbuild.yaml << 'EOF'
steps:
  # Build container
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/pdp-backend:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/pdp-backend:latest'
      - '.'
    dir: 'backend'

  # Push container
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/pdp-backend:$COMMIT_SHA'

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'pdp-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/pdp-backend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'

images:
  - 'gcr.io/$PROJECT_ID/pdp-backend:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/pdp-backend:latest'

timeout: '1200s'
EOF

# Grant Cloud Build service account necessary permissions
PROJECT_NUMBER=$(gcloud projects describe YOUR-GCP-PROJECT-ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

## Environment Variables Reference

Configure these environment variables in Cloud Run:

```bash
# Backend Environment Variables
GOOGLE_CLOUD_PROJECT=YOUR-GCP-PROJECT-ID
GCS_BUCKET_NAME=pdp-automation-assets-dev
CLOUD_TASKS_QUEUE=pdp-job-queue
CLOUD_TASKS_LOCATION=us-central1
ALLOWED_EMAIL_DOMAIN=your-domain.com
ANTHROPIC_MODEL=claude-sonnet-4-5-20241022
ENVIRONMENT=production

# Secrets (mounted from Secret Manager)
DATABASE_URL=database-url:latest
ANTHROPIC_API_KEY=anthropic-api-key:latest
JWT_SECRET_KEY=jwt-secret-key:latest
GOOGLE_OAUTH_CLIENT_ID=google-oauth-credentials:latest
GOOGLE_OAUTH_CLIENT_SECRET=google-oauth-credentials:latest
```

## Cost Optimization Tips

1. **Cloud Run Auto-scaling**
   - Set `--min-instances=1` for backend (keep warm)
   - Set `--min-instances=0` for frontend (scale to zero)
   - Use `--max-instances` to control costs

2. **Cloud Storage Lifecycle**
   - Auto-delete temp files after 1 day
   - Move old files to Nearline storage after 90 days
   - Delete old uploads after 365 days

3. **Cloud Tasks**
   - Set `--max-concurrent-dispatches=5` to control parallelism
   - Use appropriate backoff settings to avoid retries

4. **Secret Manager**
   - Use automatic replication (cheaper than multi-region)
   - Access secrets at startup, cache in memory

5. **Monitoring**
   - Use log-based metrics (free up to 50 GB/month)
   - Set appropriate alert thresholds to avoid noise

## Security Considerations

1. **Service Account Permissions**
   - Follow principle of least privilege
   - Use separate service accounts for different services
   - Regularly audit IAM permissions

2. **Secret Management**
   - Never commit secrets to Git
   - Rotate secrets regularly (every 90 days)
   - Use Secret Manager for all sensitive data

3. **Network Security**
   - Enable VPC Connector for Cloud Run (optional)
   - Use Cloud Armor for DDoS protection
   - Implement rate limiting at application level

4. **Authentication**
   - Use OAuth 2.0 for user authentication
   - Validate JWT tokens on every request
   - Restrict access to `@your-domain.com` domain only

5. **Data Protection**
   - Enable uniform bucket-level access
   - Use signed URLs for temporary access
   - Encrypt sensitive data before storage

## Troubleshooting

### Issue: Cloud Run deployment fails

```bash
# Check service logs
gcloud logging read "resource.type=cloud_run_revision
  resource.labels.service_name=pdp-backend" \
  --limit 50 \
  --format json \
  --project=YOUR-GCP-PROJECT-ID

# Check service status
gcloud run services describe pdp-backend \
  --region us-central1 \
  --project=YOUR-GCP-PROJECT-ID

# Verify service account permissions
gcloud projects get-iam-policy YOUR-GCP-PROJECT-ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com"
```

### Issue: Cannot access secrets

```bash
# Test secret access
gcloud secrets versions access latest \
  --secret=anthropic-api-key \
  --project=YOUR-GCP-PROJECT-ID

# Grant access to service account
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=YOUR-GCP-PROJECT-ID
```

### Issue: Cloud Tasks not enqueueing

```bash
# Check queue status
gcloud tasks queues describe pdp-job-queue \
  --location=us-central1 \
  --project=YOUR-GCP-PROJECT-ID

# List tasks in queue
gcloud tasks list \
  --queue=pdp-job-queue \
  --location=us-central1 \
  --project=YOUR-GCP-PROJECT-ID

# Purge queue (if needed)
gcloud tasks queues purge pdp-job-queue \
  --location=us-central1 \
  --project=YOUR-GCP-PROJECT-ID
```

### Issue: Storage bucket access denied

```bash
# Check bucket IAM policy
gcloud storage buckets get-iam-policy gs://pdp-automation-assets-dev

# Grant storage access
gcloud storage buckets add-iam-policy-binding gs://pdp-automation-assets-dev \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Test upload
echo "test" | gcloud storage cp - gs://pdp-automation-assets-dev/test.txt
```

### Issue: High Cloud Run costs

```bash
# Check Cloud Run metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"
    resource.labels.service_name="pdp-backend"' \
  --project=YOUR-GCP-PROJECT-ID

# Check instance count over time
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/instance_count"
    resource.labels.service_name="pdp-backend"' \
  --project=YOUR-GCP-PROJECT-ID

# Adjust scaling settings
gcloud run services update pdp-backend \
  --region us-central1 \
  --max-instances 5 \
  --concurrency 100 \
  --project=YOUR-GCP-PROJECT-ID
```

## Next Steps

After completing the GCP setup:

1. Configure [Google OAuth Setup](GOOGLE_OAUTH_SETUP.md) for user authentication
2. Set up [Google Sheets Integration](GOOGLE_SHEETS_INTEGRATION.md) for content export
3. Configure [Google Drive Integration](GOOGLE_DRIVE_INTEGRATION.md) for file sharing
4. Set up [Anthropic API Integration](ANTHROPIC_API_INTEGRATION.md) for AI processing
5. Review [Cloud Storage Patterns](CLOUD_STORAGE_PATTERNS.md) for best practices

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Cloud Tasks Documentation](https://cloud.google.com/tasks/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)
