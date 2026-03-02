# External Prerequisites & Setup Guide

**Document Type:** Pre-Development Setup Guide
**Priority:** P0 - CRITICAL
**Last Updated:** 2026-01-15
**Estimated Time:** 4-6 hours total

---

## Table of Contents

1. [Overview](#overview)
2. [Google Cloud Platform Setup](#google-cloud-platform-setup)
3. [External Services Setup](#external-services-setup)
4. [Google Workspace Setup](#google-workspace-setup)
5. [Google Sheets Templates](#google-sheets-templates)
6. [Google Drive Setup](#google-drive-setup)
7. [Local Development Environment](#local-development-environment)
8. [Pre-Development Verification](#pre-development-verification)
9. [Common Pitfalls & Troubleshooting](#common-pitfalls--troubleshooting)
10. [Security Reminders](#security-reminders)

---

## Overview

### Purpose

This document ensures you have **ALL external resources, accounts, and configurations** set up BEFORE writing a single line of code. Without completing these prerequisites, you will encounter blockers that prevent successful development and deployment.

### Who Needs This

- **Project Lead/Admin:** Must complete sections 2-6 (external setup)
- **Developers:** Must complete section 7 (local environment)
- **DevOps:** Must verify all sections before deployment

### Timeline

**Critical Items (Must complete before development):**
- Google Cloud Platform setup: 2-3 hours
- External Services setup: 30 minutes
- Google Workspace setup: 1 hour
- Google Sheets templates: 30 minutes
- Google Drive setup: 15 minutes
- Local environment setup: 1-2 hours

**Total: 4.5-6.5 hours**

### Dependencies

Complete these steps in order:
1. GCP Project → Service Accounts → APIs
2. External Services (Neon, Anthropic) -> Secret Manager
3. Google Workspace OAuth → Shared Drive Access
4. Google Sheets Templates → Share with Service Account
5. Google Drive Folder → Share with Organization
6. Local Environment → Credentials → Testing

---

## Google Cloud Platform Setup

### 2.1 Create GCP Project

**Estimated Time:** 15 minutes

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project dropdown at the top
3. Click "New Project"
4. Enter project details:
   - **Project name:** `PDP Automation`
   - **Project ID:** `YOUR-GCP-PROJECT-ID` (or your custom ID)
   - **Organization:** Select your organization
5. Click "Create"
6. Enable billing:
   - Navigate to "Billing" in the left menu
   - Link a billing account
   - Confirm billing is active

**Verification:**
```bash
gcloud projects describe YOUR-GCP-PROJECT-ID
```

---

### 2.2 Enable Required APIs

**Estimated Time:** 10 minutes

Enable all required Google Cloud APIs:

```bash
# Set your project ID
export PROJECT_ID="YOUR-GCP-PROJECT-ID"

# Enable all required APIs
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  cloudtasks.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  iam.googleapis.com \
  sheets.googleapis.com \
  drive.googleapis.com \
  --project=$PROJECT_ID
```

**APIs Enabled:**
- ✅ **Cloud Run API** - Backend and frontend hosting
- ✅ **Cloud Storage API** - File storage
- ✅ **Cloud Tasks API** - Background job queue
- ✅ **Secret Manager API** - Secure credential storage
- ✅ **Cloud Build API** - CI/CD pipeline
- ✅ **Cloud Logging API** - Application logs
- ✅ **Cloud Monitoring API** - Metrics and alerts
- ✅ **IAM API** - Identity and access management
- ✅ **Google Sheets API** - Content output (CRITICAL)
- ✅ **Google Drive API** - File sharing (CRITICAL)

**Note:** We do NOT use:
- [ ] Vertex AI API (using Anthropic API instead)
- ❌ Cloud SQL API (using Neon PostgreSQL instead)

**Verification:**
```bash
gcloud services list --enabled --project=$PROJECT_ID | grep -E "(run|storage|tasks|secret|build|logging|monitoring|iam|sheets|drive)"
```

---

### 2.3 Create Service Accounts

**Estimated Time:** 15 minutes

#### Create Primary Application Service Account

```bash
# Create service account
gcloud iam service-accounts create pdp-automation-sa \
  --display-name="PDP Automation Service Account" \
  --project=$PROJECT_ID

# Grant all required IAM roles
for role in \
  roles/storage.objectAdmin \
  roles/cloudtasks.enqueuer \
  roles/secretmanager.secretAccessor \
  roles/logging.logWriter \
  roles/monitoring.metricWriter; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:pdp-automation-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="$role"
done
```

#### Download Service Account Key

**CRITICAL:** This file contains sensitive credentials!

```bash
# Create credentials directory
mkdir -p ./credentials

# Download service account key
gcloud iam service-accounts keys create ./credentials/service-account.json \
  --iam-account=pdp-automation-sa@${PROJECT_ID}.iam.gserviceaccount.com

# Secure the file (Unix/Linux/macOS)
chmod 600 ./credentials/service-account.json
```

**Windows Users:**
```powershell
# Create directory
New-Item -ItemType Directory -Force -Path .\credentials

# Download key (use gcloud command above)
# Then set file permissions
icacls .\credentials\service-account.json /inheritance:r /grant:r "$($env:USERNAME):(R)"
```

**Service Account Email:**
```
pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com
```

**Storage Location:**
- Local development: `./credentials/service-account.json`
- **NEVER commit to Git** - Add to `.gitignore`

**Verification:**
```bash
gcloud iam service-accounts describe pdp-automation-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

---

### 2.4 Set Up Cloud Storage Bucket

**Estimated Time:** 10 minutes

```bash
# Create bucket
gsutil mb \
  -p $PROJECT_ID \
  -c STANDARD \
  -l us-central1 \
  gs://pdp-automation-assets-dev

# Enable uniform bucket-level access
gsutil uniformbucketlevelaccess set on gs://pdp-automation-assets-dev

# Set CORS configuration (for frontend uploads)
cat > cors.json << 'EOF'
[
  {
    "origin": ["http://localhost:5174", "https://your-production-domain.com"],
    "method": ["GET", "POST", "PUT", "DELETE"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://pdp-automation-assets-dev
```

#### Set Lifecycle Policy (Auto-Cleanup)

```bash
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
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://pdp-automation-assets-dev
```

**Lifecycle Rules:**
- Original PDF uploads: Auto-delete after 365 days
- Temporary processing files: Auto-delete after 1 day
- Processed assets: Keep indefinitely

**Bucket Structure:**
```
gs://pdp-automation-assets-dev/
├── uploads/           # Original PDF uploads
│   └── {job_id}/
│       └── original.pdf
├── processed/         # Final processed assets
│   └── {project_id}/
│       ├── images/
│       ├── floor_plans/
│       └── output.zip
└── temp/              # Temporary files (auto-deleted)
    └── {job_id}/
```

**Verification:**
```bash
gsutil ls gs://pdp-automation-assets-dev
gsutil lifecycle get gs://pdp-automation-assets-dev
```

---

### 2.5 Set Up Secret Manager

**Estimated Time:** 15 minutes

**Important:** You'll add secrets here AFTER setting up external services (Neon, Anthropic).

#### Create Secrets

```bash
# Generate a secure JWT secret key
JWT_SECRET=$(openssl rand -base64 64)

# Create JWT secret
echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# Placeholder for database URL (will update after Neon setup)
echo -n "placeholder" | gcloud secrets create database-url \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# Placeholder for Anthropic API key (will update after Anthropic setup)
echo -n "placeholder" | gcloud secrets create anthropic-api-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# Placeholder for OAuth client secret (will update after Google Workspace setup)
echo -n "placeholder" | gcloud secrets create oauth-client-secret \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID
```

#### Grant Service Account Access

```bash
# Grant access to all secrets
for secret in jwt-secret-key database-url anthropic-api-key oauth-client-secret; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:pdp-automation-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID
done
```

**Verification:**
```bash
gcloud secrets list --project=$PROJECT_ID
gcloud secrets describe jwt-secret-key --project=$PROJECT_ID
```

---

### 2.6 Checklist: GCP Setup Complete

- [ ] GCP project created: `YOUR-GCP-PROJECT-ID`
- [ ] Billing enabled
- [ ] All 10 APIs enabled (Run, Storage, Tasks, Secrets, Build, Logging, Monitoring, IAM, Sheets, Drive)
- [ ] Service account created: `pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com`
- [ ] Service account granted 5 IAM roles
- [ ] Service account JSON key downloaded to `./credentials/service-account.json`
- [ ] Cloud Storage bucket created: `gs://pdp-automation-assets-dev`
- [ ] Bucket CORS configured
- [ ] Bucket lifecycle policy set
- [ ] Secret Manager secrets created (jwt, database, anthropic, oauth)
- [ ] Service account granted access to all secrets

---

## External Services Setup

### 3.1 Neon PostgreSQL Database

**Estimated Time:** 10 minutes

#### Why Neon?

- **Free tier:** $0/month for development (10 GB storage, 100 hours compute)
- **Serverless:** Scales to zero when inactive (no 24/7 costs)
- **Production-ready:** Only $19/month vs $450/month for Cloud SQL
- **Same PostgreSQL:** No migration needed between dev and production
- **Automatic backups:** Built-in backup and recovery

#### Setup Steps

1. **Create Account**
   - Go to [neon.tech](https://neon.tech)
   - Click "Sign up" (use Google account for easy access)
   - Verify email address

2. **Create Project**
   - Click "Create Project"
   - **Project name:** `pdp-automation-dev`
   - **Region:** US East 1 (AWS) - lowest latency to us-central1
   - **PostgreSQL version:** 16 (latest)
   - Click "Create Project"

3. **Save Connection String**

   Neon will display your connection string. **COPY THIS IMMEDIATELY** - it contains the password:

   ```
   postgresql://user:password@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

4. **Enable Connection Pooling (Recommended)**
   - In Neon dashboard, go to "Connection Details"
   - Select "Pooled connection"
   - Use the pooled endpoint for production (ends with `-pooler.`)

5. **Store in Secret Manager**

   ```bash
   # Update the database-url secret
   echo -n "postgresql://user:password@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require" | \
   gcloud secrets versions add database-url --data-file=-
   ```

**Connection String Format:**
```
postgresql://[user]:[password]@[host]/[database]?sslmode=require
```

**Features Included:**
- ✅ Automatic connection pooling
- ✅ Daily backups (retained 7 days on free tier)
- ✅ Auto-pause after inactivity (free tier only)
- ✅ SSL/TLS encryption
- ✅ Branching (dev/staging/prod)

**Verification:**
```bash
# Test connection (requires psql client)
psql "postgresql://user:pass@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require" -c "SELECT version();"
```

---

### 3.2 Anthropic API

**Estimated Time:** 10 minutes

#### Why Anthropic Claude?

- **Claude Sonnet 4.5:** Best-in-class text extraction and content generation (200K context)
- **Claude Sonnet 4.5 Vision:** Superior vision capabilities for image classification and floor plans
- **Cost-effective:** ~$0.10-$0.30 per document (using pymupdf4llm reduces costs by 90%)
- **Reliable:** High uptime and consistent quality

#### Setup Steps

1. **Create Account**
   - Go to [console.anthropic.com](https://console.anthropic.com)
   - Sign up or log in
   - Complete email verification

2. **Set Up Billing**
   - Navigate to "Settings" -> "Billing"
   - Add payment method
   - Set up usage limits (recommended: $50/month for development)

3. **Create API Key**
   - Go to [API Keys](https://console.anthropic.com/settings/keys)
   - Click "Create Key"
   - **Name:** "PDP Automation Production"
   - Click "Create"
   - **COPY THE KEY IMMEDIATELY** (you won't see it again)

4. **Store in Secret Manager**

   ```bash
   # Update the anthropic-api-key secret
   echo -n "sk-ant-xxxxxxxxxxxxxxxxxxxxx" | \
   gcloud secrets versions add anthropic-api-key --data-file=-
   ```

**API Key Format:**
```
sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Models Used:**
- **Claude Sonnet 4.5** (`claude-sonnet-4-5-20241022`) - Text and vision tasks

**Cost Estimates (per project):**
- Text extraction (pymupdf4llm, local): $0.00
- Content generation (Claude Sonnet 4.5): $0.05-$0.10
- Image classification (Claude Sonnet 4.5 Vision): $0.05-$0.10
- Floor plans (Claude Sonnet 4.5 Vision): $0.05-$0.10
- **Total per project:** $0.15-$0.30

**Verification:**
```bash
# Test API (requires curl and jq)
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: sk-ant-xxxxx" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-5-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}' | jq '.content'
```

---

### 3.3 Checklist: External Services Complete

- [ ] Neon PostgreSQL account created
- [ ] Neon project created: `pdp-automation-dev`
- [ ] Connection string saved securely
- [ ] Connection pooling enabled
- [ ] Database URL stored in Secret Manager
- [ ] Anthropic account created
- [ ] Billing configured with usage limits
- [ ] API key created and copied
- [ ] API key stored in Secret Manager
- [ ] Connectivity tests passed

---

## Google Workspace Setup

### 4.1 Prerequisites

**CRITICAL REQUIREMENT:** You must have **Google Workspace Admin** privileges for the `@your-domain.com` domain.

If you don't have admin access:
1. Contact your IT department
2. Request "Google Workspace Admin" role
3. Explain you need to configure OAuth and Shared Drive access
4. Wait for approval before proceeding

**Verification:**
- Go to [admin.google.com](https://admin.google.com)
- If you can access the admin console, you have sufficient privileges

---

### 4.2 Create OAuth 2.0 Client

**Estimated Time:** 15 minutes

1. **Navigate to Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Select project: `YOUR-GCP-PROJECT-ID`
   - Navigate to "APIs & Services" → "Credentials"

2. **Create OAuth Client ID**
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure the consent screen first (see section 4.3)
   - **Application type:** Web application
   - **Name:** `PDP Automation Web App`

3. **Configure Authorized Origins**

   Add these JavaScript origins:
   ```
   http://localhost:5174
   https://your-production-domain.com
   ```

4. **Configure Redirect URIs**

   Add these redirect URIs:
   ```
   http://localhost:5174/api/auth/callback
   https://your-production-domain.com/api/auth/callback
   ```

5. **Save and Download**
   - Click "Create"
   - **Download the JSON** (contains client ID and secret)
   - **Save the Client ID** - you'll need it for frontend
   - **Save the Client Secret** - you'll store it in Secret Manager

6. **Store Client Secret in Secret Manager**

   ```bash
   # Update oauth-client-secret
   echo -n "GOCSPX-xxxxxxxxxxxxxxxxxx" | \
   gcloud secrets versions add oauth-client-secret --data-file=-
   ```

**Client ID Format:**
```
123456789012-xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
```

**Client Secret Format:**
```
GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx
```

---

### 4.3 Configure OAuth Consent Screen

**Estimated Time:** 10 minutes

1. **Navigate to Consent Screen**
   - In Google Cloud Console, go to "APIs & Services" → "OAuth consent screen"

2. **Select User Type**
   - Choose **"Internal"** (restricts access to @your-domain.com domain only)
   - Click "Create"

3. **Fill App Information**
   - **App name:** `PDP Automation`
   - **User support email:** `your-email@your-domain.com`
   - **App logo:** (optional) Upload company logo
   - **Application home page:** `https://your-domain.com` (or leave blank for dev)
   - **Authorized domains:** `your-domain.com`
   - **Developer contact:** `your-email@your-domain.com`

4. **Configure Scopes**

   Click "Add or Remove Scopes" and add:
   - `openid` - OpenID Connect authentication
   - `email` - User email address
   - `profile` - User profile information
   - `https://www.googleapis.com/auth/spreadsheets` - Google Sheets access

5. **Save and Continue**
   - Review all settings
   - Click "Save and Continue"
   - No need to add test users (Internal apps don't require this)

**Verification:**
- User type should show "Internal"
- Publishing status should show "In production"
- Authorized domains should include `your-domain.com`

---

### 4.4 Configure Shared Drive Access

**Estimated Time:** 5 minutes

**Purpose:** Grant the service account access to the Shared Drive for file and sheet management.

> **Note:** We use a Shared Drive instead of domain-wide delegation. This is simpler and doesn't require Google Workspace admin approval.

**Shared Drive ID:** `0AOEEIstP54k2Uk9PVA`

1. **Open Shared Drive**
   - Go to [Google Drive](https://drive.google.com)
   - Click "Shared drives" in the left sidebar
   - Open the "PDP Automation" Shared Drive

2. **Add Service Account as Member**
   - Click the gear icon (settings) or right-click the Shared Drive name
   - Click "Manage members"
   - Click "Add members"
   - Enter the service account email: `pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com`
   - Set role to **Content Manager** (can add, edit, move, and delete files)
   - Click "Send"

3. **Verification**
   - Service account should appear in the members list
   - Role should show "Content Manager"

**Benefits of Shared Drive approach:**
- No Google Workspace admin approval required
- All files owned by the drive (not individuals)
- Files persist even if uploader leaves organization
- Team members automatically have access through drive membership
- Simpler permission management

---

### 4.5 Checklist: Google Workspace Complete

- [ ] Google Workspace Admin access verified
- [ ] OAuth 2.0 client created
- [ ] Client ID saved: `123456789012-xxx.apps.googleusercontent.com`
- [ ] Client secret stored in Secret Manager
- [ ] Authorized JavaScript origins configured (localhost + production)
- [ ] Authorized redirect URIs configured
- [ ] OAuth consent screen configured as "Internal"
- [ ] Consent screen authorized domain: `your-domain.com`
- [ ] OAuth scopes include: openid, email, profile, spreadsheets
- [ ] Shared Drive created (ID: `0AOEEIstP54k2Uk9PVA`)
- [ ] Service account added to Shared Drive as Content Manager

---

## Google Sheets Templates

### 5.1 Overview

**Purpose:** Create reusable Google Sheets templates for each target site's content structure.

**Templates Needed (6 Total):**
1. **Aggregators Template** - 24+ third-party aggregator domains
2. **OPR Template** - opr.ae (Off-Plan Reviews)
3. **MPP Template** - main-portal.com
4. **ADOP Template** - abudhabioffplan.ae
5. **ADRE Template** - secondary-market-portal.com
6. **Commercial Template** - cre.main-portal.com

**Estimated Time:** 60 minutes total (10 minutes per template)

---

### 5.2 Template Sheet IDs (CREATED)

Six separate template sheets have been created in the Shared Drive:

| Template | Sheet ID | Target Sites |
|----------|----------|--------------|
| Aggregators | `YOUR_AGGREGATORS_SHEET_ID` | 24+ third-party aggregator domains |
| OPR | `YOUR_OPR_SHEET_ID` | opr.ae |
| MPP | `YOUR_MPP_SHEET_ID` | main-portal.com |
| ADOP | `YOUR_ADOP_SHEET_ID` | abudhabioffplan.ae |
| ADRE | `YOUR_ADRE_SHEET_ID` | secondary-market-portal.com |
| Commercial | `YOUR_COMMERCIAL_SHEET_ID` | cre.main-portal.com |

Each template contains columns for EN, AR, and RU languages.
Location: Shared Drive `0AOEEIstP54k2Uk9PVA`

---

### 5.3 Share Templates with Service Account

**CRITICAL:** The service account MUST have Editor access to write data.

For EACH template:

1. **Open the template sheet**
2. **Click "Share" button** (top-right)
3. **Add service account email:**
   ```
   pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com
   ```
4. **Set permission level:** Editor
5. **Uncheck "Notify people"** (it's a service account)
6. **Click "Share"**

**Verification:**
- Service account should appear in the "People with access" list
- Permission should show "Editor"

---

### 5.4 Store Template IDs

Extract the Google Sheet ID from each template's URL:

**URL Format:**
```
https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit#gid=0
```

**Example:**
```
https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit#gid=0
                                        ^^^^^^^^^^^^^^^^^^^
                                        This is the Sheet ID
```

**Save these IDs for your .env file:**
```bash
TEMPLATE_SHEET_ID_AGGREGATORS=YOUR_AGGREGATORS_SHEET_ID
TEMPLATE_SHEET_ID_OPR=YOUR_OPR_SHEET_ID
TEMPLATE_SHEET_ID_MPP=YOUR_MPP_SHEET_ID
TEMPLATE_SHEET_ID_ADOP=YOUR_ADOP_SHEET_ID
TEMPLATE_SHEET_ID_ADRE=YOUR_ADRE_SHEET_ID
TEMPLATE_SHEET_ID_COMMERCIAL=YOUR_COMMERCIAL_SHEET_ID
```

---

### 5.5 Checklist: Google Sheets Complete

- [x] Aggregators template created (24+ aggregator domains)
- [x] OPR template created (opr.ae)
- [x] MPP template created (main-portal.com)
- [x] ADOP template created (abudhabioffplan.ae)
- [x] ADRE template created (secondary-market-portal.com)
- [x] Commercial template created (cre.main-portal.com)
- [x] All 6 templates in Shared Drive
- [x] Service account has Content Manager access via Shared Drive
- [x] Template IDs extracted and saved
- [ ] Connectivity test passed (can read/write to templates)

---

## Google Drive Setup

### 6.1 Overview

**Purpose:** Create a shared Google Drive folder where processed images and floor plans are uploaded automatically for the entire @your-domain.com organization to access.

**Estimated Time:** 15 minutes

---

### 6.2 Create Shared Drive Folder

1. **Create Root Folder**
   - Go to [Google Drive](https://drive.google.com)
   - Click "New" → "Folder"
   - Name: `PDP Automation - Processed Assets`
   - Click "Create"

2. **Share with Organization**
   - Right-click the folder → "Share"
   - Click "Change" next to "Restricted"
   - Select **"Anyone at the company with the link"**
   - Set permission: **Viewer** (users can view and download, not edit)
   - Click "Done"

3. **Add Service Account as Editor**
   - Click "Share" again
   - Add service account email:
     ```
     pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com
     ```
   - Set permission: **Editor** (service account needs to upload files)
   - Uncheck "Notify people"
   - Click "Share"

4. **Get Folder ID**

   Open the folder and copy the ID from the URL:

   **URL Format:**
   ```
   https://drive.google.com/drive/folders/[FOLDER_ID]
   ```

   **Example:**
   ```
   https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
                                           This is the Folder ID
   ```

5. **Save Folder ID**

   Add to your .env file:
   ```bash
   GOOGLE_DRIVE_FOLDER_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz
   ```

---

### 6.3 Folder Structure

The automation will create this structure automatically:

```
PDP Automation - Processed Assets/
├── Project Name 1/
│   ├── Images/
│   │   ├── image_1.jpg
│   │   ├── image_2.jpg
│   │   └── ...
│   ├── Floor Plans/
│   │   ├── floor_plan_1.jpg
│   │   └── floor_plan_2.jpg
│   └── output.zip
├── Project Name 2/
│   ├── Images/
│   ├── Floor Plans/
│   └── output.zip
└── ...
```

**Access:**
- Any @your-domain.com user can view and download files
- Publishers can easily access assets for website creation
- No manual file distribution needed

---

### 6.4 Checklist: Google Drive Complete

- [ ] Root folder created: "PDP Automation - Processed Assets"
- [ ] Folder shared with entire organization (@your-domain.com) as Viewer
- [ ] Service account added as Editor
- [ ] Folder ID extracted and saved
- [ ] Folder structure documented for team

---

## Local Development Environment

### 7.1 Prerequisites Check

**Estimated Time:** 1-2 hours

Before proceeding, ensure your operating system is ready:

**Operating System Requirements:**
- **Windows:** Windows 10/11 with WSL2 (recommended) or native Windows
- **macOS:** macOS 11 Big Sur or later
- **Linux:** Ubuntu 20.04+, Debian 11+, or equivalent

---

### 7.2 Install Required Software

#### Install Python 3.10+

**macOS (Homebrew):**
```bash
brew install python@3.10
python3 --version  # Should show 3.10.x or higher
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
python3 --version
```

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. Check "Add Python to PATH"
4. Verify: `python --version`

---

#### Install Node.js 18+

**macOS (Homebrew):**
```bash
brew install node
node --version  # Should show v18.x or higher
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node --version
```

**Windows:**
1. Download from [nodejs.org](https://nodejs.org/)
2. Run installer
3. Verify: `node --version`

---

#### Install Docker Desktop

**All Platforms:**
1. Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. Install and start Docker Desktop
3. Verify:
   ```bash
   docker --version
   docker ps
   ```

**Usage:** Docker runs PostgreSQL and Redis containers for local development.

---

#### Install Google Cloud SDK

**macOS (Homebrew):**
```bash
brew install google-cloud-sdk
gcloud version
```

**Ubuntu/Debian:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud version
```

**Windows:**
1. Download installer from [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
2. Run installer
3. Verify: `gcloud version`

**Initialize gcloud:**
```bash
gcloud init
gcloud auth login
gcloud config set project YOUR-GCP-PROJECT-ID
```

---

#### Install Git

**macOS (Homebrew):**
```bash
brew install git
git --version
```

**Ubuntu/Debian:**
```bash
sudo apt install git
git --version
```

**Windows:**
Download from [git-scm.com](https://git-scm.com/download/win)

---

### 7.3 Clone Repository & Set Up Credentials

```bash
# Clone repository (update with actual repo URL)
git clone https://github.com/mpd-ae/pdp-automation.git
cd pdp-automation

# Create credentials directory
mkdir -p credentials

# Move service account JSON here
# If you downloaded it to ~/Downloads:
mv ~/Downloads/service-account.json ./credentials/

# Verify file exists
ls -la ./credentials/service-account.json

# CRITICAL: Add to .gitignore
cat >> .gitignore << 'EOF'

# Credentials - NEVER COMMIT
credentials/
*.json
.env
.env.local
EOF
```

---

### 7.4 Backend Setup

```bash
cd backend

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Testing and linting tools

# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use VS Code: code .env
```

#### Configure Backend .env

```bash
# ====================
# DATABASE
# ====================
DATABASE_URL=postgresql+asyncpg://pdpuser:PASSWORD@localhost:5432/pdp_automation

# ====================
# GOOGLE CLOUD
# ====================
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
GCP_PROJECT_ID=YOUR-GCP-PROJECT-ID
GCS_BUCKET_NAME=pdp-automation-assets-dev

# ====================
# ANTHROPIC API
# ====================
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-sonnet-4-5-20241022

# ====================
# GOOGLE SHEETS (6 Templates)
# ====================
TEMPLATE_SHEET_ID_AGGREGATORS=YOUR_AGGREGATORS_SHEET_ID
TEMPLATE_SHEET_ID_OPR=YOUR_OPR_SHEET_ID
TEMPLATE_SHEET_ID_MPP=YOUR_MPP_SHEET_ID
TEMPLATE_SHEET_ID_ADOP=YOUR_ADOP_SHEET_ID
TEMPLATE_SHEET_ID_ADRE=YOUR_ADRE_SHEET_ID
TEMPLATE_SHEET_ID_COMMERCIAL=YOUR_COMMERCIAL_SHEET_ID

# ====================
# GOOGLE DRIVE
# ====================
GOOGLE_DRIVE_FOLDER_ID=your-drive-folder-id

# ====================
# GOOGLE OAUTH
# ====================
GOOGLE_OAUTH_CLIENT_ID=123456789012-xxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxx
ALLOWED_EMAIL_DOMAIN=your-domain.com

# ====================
# JWT
# ====================
JWT_SECRET_KEY=your-generated-secret-key-from-secret-manager
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ====================
# ENVIRONMENT
# ====================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# ====================
# NEON DATABASE (Production)
# ====================
# Uncomment for production:
# DATABASE_URL=postgresql://user:pass@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
```

---

### 7.5 Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local
nano .env.local  # or: code .env.local
```

#### Configure Frontend .env.local

```bash
# API Base URL
VITE_API_BASE_URL=http://localhost:8000

# Google OAuth Client ID (from Google Workspace setup)
VITE_GOOGLE_OAUTH_CLIENT_ID=123456789012-xxxxx.apps.googleusercontent.com

# Environment
VITE_ENVIRONMENT=development
```

---

### 7.6 Start Local Database

```bash
# From project root
cd ..

# Start PostgreSQL and Redis containers
docker-compose up -d postgres redis

# Verify containers are running
docker ps

# Expected output:
# CONTAINER ID   IMAGE         STATUS         PORTS
# xxxxx          postgres:16   Up 10 seconds  0.0.0.0:5432->5432/tcp
# xxxxx          redis:7       Up 10 seconds  0.0.0.0:6379->6379/tcp
```

#### Run Database Migrations

```bash
cd backend

# Run migrations
alembic upgrade head

# Verify database tables created
psql postgresql://pdpuser:PASSWORD@localhost:5432/pdp_automation -c "\dt"
```

**Expected tables:**
- users
- projects
- project_floor_plans
- project_images
- project_approvals
- publication_checklists
- notifications
- qa_comparisons
- prompts
- prompt_versions

---

### 7.7 Start Development Servers

#### Terminal 1: Backend

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in 1234 ms

➜  Local:   http://localhost:5174/
➜  Network: use --host to expose
```

#### Access Application

- **Frontend:** http://localhost:5174
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger UI)

---

### 7.8 Checklist: Local Environment Complete

**Software Installed:**
- [ ] Python 3.10+ installed and verified
- [ ] Node.js 18+ installed and verified
- [ ] Docker Desktop installed and running
- [ ] Google Cloud SDK installed and authenticated
- [ ] Git installed and verified

**Repository Setup:**
- [ ] Repository cloned
- [ ] Service account JSON in `./credentials/`
- [ ] `.gitignore` includes `credentials/`

**Backend Setup:**
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (requirements.txt)
- [ ] `.env` file configured with all variables
- [ ] Database containers running
- [ ] Migrations applied successfully
- [ ] Backend server starts without errors

**Frontend Setup:**
- [ ] Dependencies installed (npm install)
- [ ] `.env.local` configured
- [ ] Frontend dev server starts without errors

**Connectivity:**
- [ ] Can access frontend at http://localhost:5174
- [ ] Can access backend API at http://localhost:8000
- [ ] Can access API docs at http://localhost:8000/docs

---

## Pre-Development Verification

### 8.1 Connectivity Tests

Run these tests to verify all external services are accessible:

#### Test 1: GCP Authentication

```bash
# List projects (should include yours)
gcloud projects list

# Verify active project
gcloud config get-value project
# Expected: YOUR-GCP-PROJECT-ID
```

#### Test 2: Service Account

```bash
# Activate service account
gcloud auth activate-service-account \
  --key-file=./credentials/service-account.json

# Test Cloud Storage access
gsutil ls gs://pdp-automation-assets-dev
# Expected: Empty bucket or list of folders
```

#### Test 3: Neon PostgreSQL

```bash
# Test connection (replace with your connection string)
psql "postgresql://user:pass@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require" \
  -c "SELECT version();"

# Expected: PostgreSQL 16.x version info
```

#### Test 4: Anthropic API

```bash
# Test API call (requires curl and jq)
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-5-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}' \
  | jq '.content'

# Expected: JSON response with content array
```

#### Test 5: Secret Manager

```bash
# List secrets
gcloud secrets list --project=YOUR-GCP-PROJECT-ID

# Test access (should print your API key)
gcloud secrets versions access latest \
  --secret="anthropic-api-key" \
  --project=YOUR-GCP-PROJECT-ID
```

#### Test 6: Google Sheets API

Create a test Python script:

```python
# test_sheets.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name(
    './credentials/service-account.json', scope
)
gc = gspread.authorize(creds)

# Try to open your OPR template
sheet = gc.open_by_key('YOUR_OPR_TEMPLATE_ID')
print(f"✅ Successfully accessed: {sheet.title}")
```

Run it:
```bash
pip install gspread oauth2client
python test_sheets.py
```

#### Test 7: Google Drive API

```python
# test_drive.py
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/drive.file']
creds = service_account.Credentials.from_service_account_file(
    './credentials/service-account.json', scopes=SCOPES
)
service = build('drive', 'v3', credentials=creds)

# List files in your shared folder
results = service.files().list(
    q=f"'YOUR_DRIVE_FOLDER_ID' in parents",
    fields="files(id, name)"
).execute()
print(f"✅ Found {len(results.get('files', []))} files in Drive folder")
```

Run it:
```bash
pip install google-api-python-client google-auth
python test_drive.py
```

---

### 8.2 Final Checklist

**Before writing ANY code, verify:**

**Google Cloud:**
- [ ] GCP project exists and billing is enabled
- [ ] All 10 APIs enabled (Run, Storage, Tasks, Secrets, Build, Logging, Monitoring, IAM, Sheets, Drive)
- [ ] Service account created with 5 IAM roles
- [ ] Service account JSON downloaded to `./credentials/`
- [ ] Cloud Storage bucket created and accessible
- [ ] All secrets created in Secret Manager
- [ ] Service account has access to all secrets

**External Services:**
- [ ] Neon PostgreSQL database created
- [ ] Connection string stored in Secret Manager
- [ ] Database connection test passed
- [ ] Anthropic account created with billing
- [ ] Anthropic API key stored in Secret Manager
- [ ] API call test passed

**Google Workspace:**
- [ ] Google Workspace Admin access confirmed
- [ ] OAuth 2.0 client created
- [ ] Client ID and secret saved
- [ ] OAuth consent screen configured as "Internal"
- [ ] Shared Drive configured (ID: 0AOEEIstP54k2Uk9PVA)
- [ ] Service account added to Shared Drive as Content Manager

**Google Sheets:**
- [x] 6 templates created (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
- [x] All templates have required fields with EN/AR/RU columns
- [x] Service account has access via Shared Drive Content Manager role
- [x] Template IDs saved
- [ ] Sheets API test passed

**Google Drive:**
- [ ] Shared folder created
- [ ] Folder shared with @your-domain.com organization
- [ ] Service account added as Editor
- [ ] Folder ID saved
- [ ] Drive API test passed

**Local Environment:**
- [ ] All software installed (Python, Node, Docker, gcloud, Git)
- [ ] Repository cloned
- [ ] Backend .env configured
- [ ] Frontend .env.local configured
- [ ] Database containers running
- [ ] Migrations applied
- [ ] Backend server starts successfully
- [ ] Frontend dev server starts successfully

**Connectivity Tests:**
- [ ] GCP authentication test passed
- [ ] Service account test passed
- [ ] Neon PostgreSQL test passed
- [ ] Anthropic API test passed
- [ ] Secret Manager test passed
- [ ] Google Sheets API test passed
- [ ] Google Drive API test passed

**If ALL items are checked, you're ready to start development!** 🎉

---

## Common Pitfalls & Troubleshooting

### Issue 1: "403 Forbidden" from Google Sheets API

**Symptoms:**
```
googleapiclient.errors.HttpError: <HttpError 403 "The caller does not have permission">
```

**Causes:**
1. Template not in the Shared Drive
2. Service account not added to Shared Drive
3. Wrong template ID

**Solutions:**
1. Move template to the Shared Drive (ID: 0AOEEIstP54k2Uk9PVA)
2. Verify service account is a member of the Shared Drive with Content Manager role
3. Double-check template ID from URL

---

### Issue 2: "Could not authenticate with service account"

**Symptoms:**
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**Causes:**
1. Service account JSON not found
2. `GOOGLE_APPLICATION_CREDENTIALS` path incorrect
3. File permissions too restrictive

**Solutions:**
1. Verify file exists: `ls ./credentials/service-account.json`
2. Check .env path matches actual file location
3. Fix permissions:
   ```bash
   chmod 600 ./credentials/service-account.json
   ```

---

### Issue 3: "Access denied to Secret Manager"

**Symptoms:**
```
google.api_core.exceptions.PermissionDenied: 403 Permission denied on resource
```

**Cause:** Service account missing `secretmanager.secretAccessor` role

**Solution:**
```bash
gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

### Issue 4: "OAuth domain restriction failed"

**Symptoms:**
```
User email does not match allowed domain: @your-domain.com
```

**Cause:** OAuth consent screen not configured as "Internal"

**Solution:**
1. Go to "APIs & Services" → "OAuth consent screen"
2. Change "User Type" to "Internal"
3. Verify "Authorized domains" includes `your-domain.com`

---

### Issue 5: "Neon PostgreSQL connection failed"

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Causes:**
1. Invalid connection string
2. Database paused (free tier auto-pauses)
3. Network/firewall issue

**Solutions:**
1. Verify connection string format includes `?sslmode=require`
2. Go to Neon dashboard and wake up the database
3. Test from your machine:
   ```bash
   psql "YOUR_CONNECTION_STRING" -c "SELECT 1;"
   ```
4. Use pooled endpoint (ends with `-pooler.`)

---

### Issue 6: "Anthropic API authentication failed"

**Symptoms:**
```
anthropic.AuthenticationError: Invalid API key provided
```

**Causes:**
1. Invalid API key
2. API key revoked
3. Insufficient credits

**Solutions:**
1. Verify key starts with `sk-ant-`
2. Check key status at [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
3. Add billing/credits at [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing)
4. Test with curl:
   ```bash
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: YOUR_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"claude-sonnet-4-5-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
   ```

---

### Issue 7: "Docker containers won't start"

**Symptoms:**
```
Error: Cannot connect to the Docker daemon
```

**Solutions:**
1. Verify Docker Desktop is running
2. Restart Docker Desktop
3. Check Docker status:
   ```bash
   docker info
   ```
4. On Linux, start Docker service:
   ```bash
   sudo systemctl start docker
   ```

---

### Issue 8: "Alembic migration failed"

**Symptoms:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: password authentication failed
```

**Solutions:**
1. Verify `DATABASE_URL` in .env is correct
2. Check PostgreSQL container is running:
   ```bash
   docker ps | grep postgres
   ```
3. Reset database:
   ```bash
   docker-compose down -v
   docker-compose up -d postgres
   alembic upgrade head
   ```

---

### Issue 9: "Frontend can't connect to backend"

**Symptoms:**
- Frontend shows network errors
- API calls return 404 or CORS errors

**Solutions:**
1. Verify backend is running on port 8000
2. Check `VITE_API_BASE_URL` in .env.local matches backend URL
3. Verify CORS configuration in backend allows `http://localhost:5174`
4. Test backend directly:
   ```bash
   curl http://localhost:8000/api/health
   ```

---

## Security Reminders

### Files to NEVER Commit to Git

**CRITICAL:** The following files contain sensitive credentials and MUST NEVER be committed:

- `credentials/service-account.json` - GCP service account key
- `.env` - Backend environment variables
- `.env.local` - Frontend environment variables
- Any file ending in `.json` in the credentials directory
- Any file containing API keys, passwords, or secrets

### Verify .gitignore

Ensure your `.gitignore` includes:

```gitignore
# Credentials - NEVER COMMIT
credentials/
.env
.env.local
*.key
*.pem
*.json  # Service account keys

# Environment files
.env.*
!.env.example
!.env.local.example

# IDE
.vscode/
.idea/
*.swp
*.swo

# Dependencies
node_modules/
venv/
__pycache__/

# Build outputs
dist/
build/
*.pyc
```

### Production Secret Management

**For Production:**

1. **Use Secret Manager** - Store all secrets in Google Secret Manager
2. **Never use .env files** - Access secrets via Secret Manager API
3. **Rotate secrets** - Change credentials every 90 days
4. **Audit access** - Review who accessed secrets in Cloud Console
5. **Use separate credentials** - Dev, staging, and production should have different keys

**Example: Access secrets at runtime**
```python
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/YOUR-GCP-PROJECT-ID/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# In production, load secrets from Secret Manager
ANTHROPIC_API_KEY = get_secret("anthropic-api-key")
DATABASE_URL = get_secret("database-url")
```

### Credential Rotation Schedule

| Credential | Rotation Frequency | Method |
|------------|-------------------|--------|
| Service Account Key | 90 days | Create new key, update Secret Manager, delete old |
| Anthropic API Key | 180 days | Generate new key at console.anthropic.com |
| JWT Secret Key | 90 days | Generate new random string, update Secret Manager |
| OAuth Client Secret | 180 days | Regenerate in Google Cloud Console |
| Database Password | 90 days | Update in Neon dashboard, update Secret Manager |

### Security Checklist

- [ ] All secrets stored in Secret Manager (production)
- [ ] No credentials in .env files (production)
- [ ] .gitignore prevents credential commits
- [ ] Service account key file permissions set to 600
- [ ] OAuth consent screen set to "Internal" only
- [ ] Domain restriction enforced (@your-domain.com)
- [ ] Database uses SSL/TLS (sslmode=require)
- [ ] API keys have usage limits set
- [ ] Monitoring alerts configured for suspicious activity
- [ ] Rotation schedule documented and followed

---

## Next Steps

### You're Ready When...

✅ All items in [Pre-Development Verification](#81-connectivity-tests) are checked
✅ All connectivity tests pass
✅ Local development environment runs without errors
✅ You can access the frontend and backend
✅ You understand how to rotate credentials

### Proceed To...

1. **Phase 0:** Authentication & Security Implementation
2. **Phase 1:** Database Schema & Core Services
3. **Phase 2:** PDF Processing & Content Generation
4. **Phase 3:** Frontend Development

### Keep This Document Updated

As you encounter issues or discover new prerequisites:
1. Document the solution in the Troubleshooting section
2. Update the verification checklist
3. Share with the team
4. Commit changes (documentation only, never credentials)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-15
**Maintained By:** Engineering Team
**Contact:** dev-team@your-domain.com

**Related Documentation:**
- [Architecture > Infrastructure](../01-architecture/INFRASTRUCTURE.md)
- [Integrations > Google Cloud Setup](../05-integrations/GOOGLE_CLOUD_SETUP.md)
- [Integrations > Anthropic API Integration](../05-integrations/ANTHROPIC_API_INTEGRATION.md)
- [DevOps > Deployment Guide](../06-devops/DEPLOYMENT.md)

---

**Remember:** Security is everyone's responsibility. When in doubt, ask! 🔒
