# Google Cloud Platform Setup Guide (UI-Based)
**For PDP Automation v.3**

---

## Overview

This guide walks through setting up Google Cloud Platform via the web UI for the PDP Automation system.

**Time Required:** ~2-3 hours
**Cost:** ~$5-10/month (Cloud Run + Storage + minimal API calls)

**What You'll Set Up:**
- Google Cloud Project
- Service Accounts with proper permissions
- Cloud Storage bucket
- Secret Manager (for OpenAI API key, Neon DB connection)
- Google Sheets API access
- Google Drive API access (for file sharing)

**What You WON'T Set Up:**
- ❌ Cloud SQL (using Neon PostgreSQL instead)
- ❌ Vertex AI (using OpenAI API instead)
- ❌ JIRA integration (removed from project scope)

---

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your **@example.com** Google Workspace account
3. Click the project dropdown at the top
4. Click **"New Project"**
5. Project name: `pdp-automation-prod`
6. Organization: Select your organization (the company)
7. Location: Keep default or select your organization
8. Click **"Create"**
9. Wait 30-60 seconds for project creation
10. **Switch to the new project** using the project dropdown

---

## Step 2: Enable Billing

1. In the left sidebar, go to **Billing**
2. Click **"Link a billing account"**
3. Select your company billing account (or create one)
4. Confirm billing is enabled

**💡 Note:** You'll only pay for what you use. Expected monthly cost: $5-10 for development, $20-30 for production.

---

## Step 3: Enable Required APIs

Go to **APIs & Services > Library** and enable these APIs:

### Core APIs (Required)
1. **Cloud Run API** - `run.googleapis.com`
   - Search for "Cloud Run API"
   - Click **"Enable"**

2. **Cloud Storage API** - `storage.googleapis.com`
   - Search for "Cloud Storage"
   - Click **"Enable"**

3. **Cloud Tasks API** - `cloudtasks.googleapis.com`
   - Search for "Cloud Tasks"
   - Click **"Enable"**

4. **Secret Manager API** - `secretmanager.googleapis.com`
   - Search for "Secret Manager"
   - Click **"Enable"**

5. **Cloud Build API** - `cloudbuild.googleapis.com`
   - Search for "Cloud Build"
   - Click **"Enable"**

6. **Cloud Logging API** - `logging.googleapis.com`
   - Usually enabled by default
   - Verify it's enabled

7. **Cloud Monitoring API** - `monitoring.googleapis.com`
   - Usually enabled by default
   - Verify it's enabled

### Google Workspace Integration APIs (CRITICAL)
8. **Google Sheets API** - `sheets.googleapis.com`
   - Search for "Google Sheets API"
   - Click **"Enable"**
   - ⚠️ **CRITICAL:** System outputs content to Google Sheets

9. **Google Drive API** - `drive.googleapis.com`
   - Search for "Google Drive API"
   - Click **"Enable"**
   - ⚠️ **CRITICAL:** System uploads files to shared Drive folder

---

## Step 4: Create Service Account

### 4.1 Create the Service Account

1. Go to **IAM & Admin > Service Accounts**
2. Click **"Create Service Account"**
3. Service account name: `pdp-automation-sa`
4. Service account ID: `pdp-automation-sa` (auto-filled)
5. Description: `PDP Automation Service Account for API access`
6. Click **"Create and Continue"**

### 4.2 Grant IAM Roles

Add these roles to the service account:

1. **Storage Object Admin** - `roles/storage.objectAdmin`
   - Full access to Cloud Storage bucket

2. **Cloud Tasks Enqueuer** - `roles/cloudtasks.enqueuer`
   - Create background jobs

3. **Secret Manager Secret Accessor** - `roles/secretmanager.secretAccessor`
   - Read secrets (OpenAI key, Neon DB connection)

4. **Logs Writer** - `roles/logging.logWriter`
   - Write application logs

5. **Monitoring Metric Writer** - `roles/monitoring.metricWriter`
   - Write custom metrics

After adding all roles, click **"Continue"** then **"Done"**

### 4.3 Download Service Account Key

1. Find your new service account in the list
2. Click the **three dots menu** (⋮) on the right
3. Select **"Manage keys"**
4. Click **"Add Key" > "Create new key"**
5. Select **JSON** format
6. Click **"Create"**
7. **SAVE the JSON file securely** - you'll need it later
8. Rename it to `service-account.json`
9. Store in `./credentials/` folder (create folder if needed)

**⚠️ SECURITY WARNING:**
- Never commit this file to Git
- Never share publicly
- Keep in a secure location
- Add `credentials/` to `.gitignore`

---

## Step 5: Enable Google Workspace Domain-Wide Delegation

This allows the service account to access Google Sheets and Drive on behalf of users.

### 5.1 Get Service Account Client ID

1. Go to **IAM & Admin > Service Accounts**
2. Click on `pdp-automation-sa@...` service account
3. Find the **"Unique ID"** (numeric, like `1234567890123456789`)
4. **Copy this number** - you'll need it in the next step

### 5.2 Configure Domain-Wide Delegation

1. Go to [Google Workspace Admin Console](https://admin.google.com)
2. You must be a **Workspace Admin** to proceed
3. Navigate to **Security > Access and data control > API Controls**
4. Scroll down to **Domain-wide Delegation**
5. Click **"Manage Domain-Wide Delegation"**
6. Click **"Add new"**
7. Client ID: Paste the **Unique ID** from step 5.1
8. OAuth Scopes: Add these scopes (comma-separated):
   ```
   https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.file
   ```
9. Click **"Authorize"**

**What these scopes allow:**
- `spreadsheets` - Read and write Google Sheets
- `drive.file` - Create and manage files in Google Drive

---

## Step 6: Create Google Drive Folder for File Sharing

### 6.1 Create the Folder

1. Go to [Google Drive](https://drive.google.com)
2. Sign in with your **@example.com** account
3. Click **"New" > "Folder"**
4. Folder name: `PDP Automation - Processed Assets`
5. Click **"Create"**

### 6.2 Share with Organization

1. Right-click the folder
2. Click **"Share"**
3. Click **"Advanced"** (or gear icon)
4. Click **"Change"** next to "Who has access"
5. Select **"Anyone at the company with the link"**
6. Permission: **"Can view"** (or "Can edit" if you want people to organize files)
7. Click **"Save"** then **"Done"**

### 6.3 Get Folder ID

1. Open the folder in Google Drive
2. Look at the URL in your browser:
   ```
   https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J
                                           ^^^^^^^^^^^^^^^^^^^^
                                           This is the Folder ID
   ```
3. **Copy the Folder ID** (the part after `/folders/`)
4. Save it - you'll add it to `.env` as `GOOGLE_DRIVE_FOLDER_ID`

### 6.4 Share Folder with Service Account

1. Right-click the folder
2. Click **"Share"**
3. In "Add people" field, paste your service account email:
   ```
   pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com
   ```
4. Permission: **"Editor"**
5. Uncheck **"Notify people"**
6. Click **"Share"**

---

## Step 7: Create Cloud Storage Bucket

1. Go to **Cloud Storage > Buckets**
2. Click **"Create Bucket"**
3. Name your bucket: `pdp-automation-assets`
   - Must be globally unique
   - Use format: `pdp-automation-assets-[your-org-name]`
4. Location type: **Region**
5. Region: **us-central1** (Iowa - cheapest)
6. Storage class: **Standard**
7. Access control: **Uniform** (recommended)
8. Protection tools:
   - Uncheck "Enforce public access prevention"
   - We'll control access via IAM
9. Click **"Create"**

### 7.1 Set Lifecycle Policy (Auto-Cleanup)

1. Click on your bucket
2. Go to **Lifecycle** tab
3. Click **"Add a rule"**
4. Rule 1 - Delete temp files:
   - Action: **Delete object**
   - Condition: **Age** = 1 day
   - Object prefix: `temp/`
5. Click **"Create"**
6. Add another rule for uploads:
   - Action: **Delete object**
   - Condition: **Age** = 365 days
   - Object prefix: `uploads/`
7. Click **"Create"**

---

## Step 8: Set Up Secret Manager

Store sensitive credentials securely.

### 8.1 Create Secrets

Go to **Security > Secret Manager** and create these secrets:

#### Secret 1: OpenAI API Key
1. Click **"Create Secret"**
2. Name: `openai-api-key`
3. Secret value: Your OpenAI API key (starts with `sk-...`)
4. Regions: **Automatic**
5. Click **"Create Secret"**

#### Secret 2: Neon Database URL
1. Click **"Create Secret"**
2. Name: `database-url`
3. Secret value: Your Neon PostgreSQL connection string
   ```
   postgresql://user:password@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
4. Regions: **Automatic**
5. Click **"Create Secret"**

#### Secret 3: JWT Secret Key
1. Click **"Create Secret"**
2. Name: `jwt-secret-key`
3. Secret value: Generate a random string (e.g., use: `openssl rand -base64 32`)
4. Regions: **Automatic**
5. Click **"Create Secret"**

#### Secret 4: Google OAuth Client Secret
(You'll create this after Step 9)

### 8.2 Grant Service Account Access

For each secret:
1. Click on the secret name
2. Go to **Permissions** tab
3. Click **"Grant Access"**
4. New principals: `pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com`
5. Role: **Secret Manager Secret Accessor**
6. Click **"Save"**

---

## Step 9: Configure OAuth 2.0 for User Authentication

### 9.1 Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. User type: **Internal** (restricts to @example.com domain only)
3. Click **"Create"**
4. App information:
   - App name: `PDP Automation`
   - User support email: Your email
   - App logo: (optional)
5. App domain:
   - Application home page: `https://your-app-domain.com` (or leave blank for now)
6. Authorized domains: `example.com`
7. Developer contact: Your email
8. Click **"Save and Continue"**
9. Scopes: Click **"Add or Remove Scopes"**
   - Select: `openid`, `email`, `profile`
   - Click **"Update"**
10. Click **"Save and Continue"**
11. Summary: Click **"Back to Dashboard"**

### 9.2 Create OAuth Client ID

1. Go to **APIs & Services > Credentials**
2. Click **"Create Credentials" > "OAuth client ID"**
3. Application type: **Web application**
4. Name: `PDP Automation Web Client`
5. Authorized JavaScript origins:
   - `http://localhost:5173` (local dev)
   - `https://your-production-domain.com` (add when you have it)
6. Authorized redirect URIs:
   - `http://localhost:5173/api/auth/callback`
   - `https://your-production-domain.com/api/auth/callback`
7. Click **"Create"**
8. **Copy the Client ID and Client Secret**
9. Save them securely

### 9.3 Store OAuth Secret in Secret Manager

1. Go back to **Secret Manager**
2. Create secret: `oauth-client-secret`
3. Secret value: Paste the OAuth Client Secret from step 9.2
4. Click **"Create Secret"**
5. Grant service account access (same as step 8.2)

---

## Step 10: Verification Checklist

Before proceeding to development, verify:

### Google Cloud Project
- [ ] Project created: `pdp-automation-prod`
- [ ] Billing enabled

### APIs Enabled (9 total)
- [ ] Cloud Run API
- [ ] Cloud Storage API
- [ ] Cloud Tasks API
- [ ] Secret Manager API
- [ ] Cloud Build API
- [ ] Cloud Logging API
- [ ] Cloud Monitoring API
- [ ] **Google Sheets API** ✅
- [ ] **Google Drive API** ✅

### Service Account
- [ ] Service account created: `pdp-automation-sa`
- [ ] 5 IAM roles granted
- [ ] Service account JSON downloaded and saved securely
- [ ] Domain-wide delegation configured with Sheets + Drive scopes

### Google Drive
- [ ] Shared folder created: "PDP Automation - Processed Assets"
- [ ] Folder shared with entire @example.com organization
- [ ] Folder ID copied
- [ ] Service account has Editor access to folder

### Cloud Storage
- [ ] Bucket created: `pdp-automation-assets-[org]`
- [ ] Lifecycle rules configured (auto-delete temp files)

### Secret Manager (4 secrets)
- [ ] `openai-api-key` created
- [ ] `database-url` created (Neon connection string)
- [ ] `jwt-secret-key` created
- [ ] `oauth-client-secret` created
- [ ] Service account has access to all secrets

### OAuth Configuration
- [ ] OAuth consent screen configured as "Internal"
- [ ] OAuth client ID created
- [ ] Client ID and secret saved

---

## Step 11: Environment Variables Setup

Create a `.env` file in your backend directory with these values:

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=<from-secret-manager>

# Anthropic API
ANTHROPIC_API_KEY=<from-secret-manager>
ANTHROPIC_MODEL=claude-sonnet-4-5-20250514

# Google Cloud
GOOGLE_CLOUD_PROJECT=pdp-automation-prod
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
GCS_BUCKET_NAME=pdp-automation-assets-[your-org]

# Google Drive
GOOGLE_DRIVE_FOLDER_ID=<folder-id-from-step-6.3>

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=<from-step-9.2>
GOOGLE_OAUTH_CLIENT_SECRET=<from-secret-manager>
ALLOWED_EMAIL_DOMAIN=example.com

# JWT
JWT_SECRET_KEY=<from-secret-manager>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# App
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
```

**Security:** Never commit this `.env` file to Git. Use `.env.example` (without actual values) for reference.

---

## Step 12: Test Connectivity

### Test Service Account Access

```bash
# Authenticate with service account
gcloud auth activate-service-account \
  --key-file=./credentials/service-account.json

# Test Cloud Storage access
gsutil ls gs://pdp-automation-assets-[your-org]

# Test Secret Manager access
gcloud secrets versions access latest --secret="openai-api-key"
```

### Test Neon Database Connection

```bash
# Install psql if needed
# Windows: Download from https://www.postgresql.org/download/windows/
# Mac: brew install postgresql

# Test connection
psql "postgresql://user:pass@ep-xxxxx.neon.tech/neondb?sslmode=require" -c "SELECT version();"
```

### Test OpenAI API

```bash
# Install OpenAI Python package
pip install openai

# Test API
python -c "import openai; openai.api_key='YOUR_KEY'; print(openai.Model.list())"
```

### Test Google Sheets Access (Python)

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name(
    './credentials/service-account.json', scope
)
client = gspread.authorize(creds)

# Test by listing accessible sheets
print("Connection successful!")
```

### Test Google Drive Access (Python)

```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = './credentials/service-account.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

drive_service = build('drive', 'v3', credentials=credentials)

# Test by listing files in the folder
folder_id = 'YOUR_FOLDER_ID'
results = drive_service.files().list(
    q=f"'{folder_id}' in parents",
    pageSize=10
).execute()

print(f"Found {len(results.get('files', []))} files in folder")
```

---

## Troubleshooting

### Error: "API has not been enabled"
**Solution:** Go back to Step 3 and enable the specific API mentioned in the error.

### Error: "Permission denied" when accessing Google Sheets
**Solution:**
1. Verify domain-wide delegation is configured (Step 5)
2. Verify scopes include `https://www.googleapis.com/auth/spreadsheets`
3. Share the specific sheet with service account email

### Error: "Permission denied" when accessing Google Drive
**Solution:**
1. Verify Drive API is enabled
2. Verify domain-wide delegation includes `drive.file` scope
3. Verify folder is shared with service account (Step 6.4)

### Error: "Bucket not found"
**Solution:** Double-check bucket name in `.env` matches the bucket you created.

### Error: "Secret not found"
**Solution:** Verify secret names exactly match:
- `openai-api-key` (not `openai_api_key`)
- `database-url` (not `database_url`)

---

## Cost Estimate

**Development (First Month):**
- Cloud Storage: ~$1
- Cloud Run (minimal usage): ~$2-5
- Cloud Tasks: ~$1
- API calls: <$1
- **Total: ~$5-10/month**

**Production (Ongoing):**
- Cloud Storage: ~$5-10
- Cloud Run: ~$10-20 (depends on traffic)
- Cloud Tasks: ~$2-5
- API calls: ~$2-5
- **Total: ~$20-40/month**

**External Services:**
- Neon PostgreSQL: $0 (dev), $19/month (prod)
- OpenAI API: Covered by existing credits

**Grand Total: $5-10/month (dev), $40-60/month (prod)**

---

## Security Reminders

**Never commit to Git:**
- `credentials/service-account.json`
- `.env`
- Any file containing API keys or secrets

**Add to .gitignore:**
```
credentials/
.env
.env.local
*.json  # Catches service account keys
```

**Rotate secrets every 90 days:**
- Service account keys
- JWT secret
- OAuth client secret

---

## Next Steps

Once all verification items are checked:

1. ✅ Set up Neon PostgreSQL database (separate guide)
2. ✅ Get OpenAI API key (separate guide)
3. ✅ Clone project repository
4. ✅ Configure `.env` file
5. ✅ Run database migrations
6. ✅ Start development server

**You're now ready to develop!** 🎉
