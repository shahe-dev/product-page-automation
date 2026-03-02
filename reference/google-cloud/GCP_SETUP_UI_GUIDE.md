# Google Cloud Platform Setup Guide (UI-Based)

**Last Updated:** 2026-01-15
**Estimated Time:** 2-3 hours
**Prerequisites:** Google account with billing access

---

## Overview

This guide walks through setting up Google Cloud Platform for PDP Automation v.3 using the web UI (not gcloud CLI). Follow each step carefully to ensure a complete setup.

**What You'll Set Up:**
- ✅ GCP Project with billing
- ✅ 10 required APIs enabled
- ✅ Service account with proper IAM roles
- ✅ Cloud Storage bucket
- ✅ Secret Manager with all secrets
- ✅ Google Workspace OAuth configuration
- ✅ Google Drive folder with organization-wide sharing

---

## Part 1: Create GCP Project

### Step 1.1: Create New Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top (shows "Select a project")
3. Click "NEW PROJECT" button
4. Fill in details:
   - **Project name:** `PDP Automation Production`
   - **Project ID:** `pdp-automation-prod` (note this - you'll need it)
   - **Organization:** Select your organization (example.com)
   - **Location:** Select your organization folder
5. Click "CREATE"
6. Wait for project creation (15-30 seconds)
7. Click "SELECT PROJECT" to switch to the new project

### Step 1.2: Enable Billing

1. In the navigation menu (☰), go to **Billing**
2. Click "LINK A BILLING ACCOUNT"
3. Select your company's billing account
4. Click "SET ACCOUNT"
5. Verify billing is enabled (you should see "Billing account linked" message)

**⚠️ CRITICAL:** Without billing enabled, you cannot use any Google Cloud services.

---

## Part 2: Enable Required APIs

### Step 2.1: Navigate to APIs & Services

1. Click navigation menu (☰)
2. Go to **APIs & Services > Library**

### Step 2.2: Enable Core APIs (Required)

Enable each API by searching for it and clicking "ENABLE":

**1. Cloud Run API**
- Search: "Cloud Run API"
- Click the result
- Click "ENABLE"
- Wait for confirmation (5-10 seconds)

**2. Cloud Storage API**
- Search: "Cloud Storage"
- Click "Cloud Storage API"
- Click "ENABLE"

**3. Cloud Tasks API**
- Search: "Cloud Tasks"
- Click "Cloud Tasks API"
- Click "ENABLE"

**4. Secret Manager API**
- Search: "Secret Manager"
- Click "Secret Manager API"
- Click "ENABLE"

**5. Cloud Build API**
- Search: "Cloud Build"
- Click "Cloud Build API"
- Click "ENABLE"

**6. Cloud Logging API**
- Search: "Cloud Logging"
- Click "Cloud Logging API"
- Click "ENABLE"

**7. Cloud Monitoring API**
- Search: "Cloud Monitoring"
- Click "Stackdriver Monitoring API" or "Cloud Monitoring API"
- Click "ENABLE"

**8. Identity and Access Management (IAM) API**
- Search: "IAM API"
- Click "Identity and Access Management (IAM) API"
- Click "ENABLE"

### Step 2.3: Enable Google Workspace Integration APIs (CRITICAL)

**⚠️ CRITICAL:** These APIs were previously overlooked but are essential for the system to function.

**9. Google Sheets API** 🔴 **CRITICAL**
- Search: "Google Sheets API"
- Click "Google Sheets API"
- Click "ENABLE"
- **Why:** System outputs all generated content to Google Sheets templates

**10. Google Drive API** 🔴 **CRITICAL**
- Search: "Google Drive API"
- Click "Google Drive API"
- Click "ENABLE"
- **Why:** System uploads processed images and floor plans to a shared Drive folder for seamless organization-wide access

### Step 2.4: Verify All APIs Enabled

1. Go to **APIs & Services > Dashboard**
2. Verify you see all 10 APIs in the "Enabled APIs" section:
   - Cloud Run API ✅
   - Cloud Storage API ✅
   - Cloud Tasks API ✅
   - Secret Manager API ✅
   - Cloud Build API ✅
   - Cloud Logging API ✅
   - Cloud Monitoring API ✅
   - IAM API ✅
   - Google Sheets API ✅
   - Google Drive API ✅

**Note:** Vertex AI and Cloud SQL APIs are NOT required - we use OpenAI API (external) and Neon PostgreSQL (external) instead.

---

## Part 3: Create Service Account

### Step 3.1: Create Service Account

1. Go to **IAM & Admin > Service Accounts**
2. Click "CREATE SERVICE ACCOUNT"
3. Fill in details:
   - **Service account name:** `pdp-automation-sa`
   - **Service account ID:** `pdp-automation-sa` (auto-filled)
   - **Description:** "Primary service account for PDP Automation application"
4. Click "CREATE AND CONTINUE"

### Step 3.2: Grant IAM Roles

In the "Grant this service account access to project" section, add these 5 roles:

**Role 1: Storage Object Admin**
- Click "Select a role"
- Search: "Storage Object Admin"
- Select "Storage Object Admin"
- Click "+ ADD ANOTHER ROLE"

**Role 2: Cloud Tasks Enqueuer**
- Click "Select a role"
- Search: "Cloud Tasks Enqueuer"
- Select "Cloud Tasks Enqueuer"
- Click "+ ADD ANOTHER ROLE"

**Role 3: Secret Manager Secret Accessor**
- Click "Select a role"
- Search: "Secret Manager Secret Accessor"
- Select "Secret Manager Secret Accessor"
- Click "+ ADD ANOTHER ROLE"

**Role 4: Logging Log Writer**
- Click "Select a role"
- Search: "Logs Writer"
- Select "Logging Log Writer"
- Click "+ ADD ANOTHER ROLE"

**Role 5: Monitoring Metric Writer**
- Click "Select a role"
- Search: "Monitoring Metric Writer"
- Select "Monitoring Metric Writer"
- Click "CONTINUE"

### Step 3.3: Skip User Access (Optional)

- Click "CONTINUE" (no user access needed)
- Click "DONE"

### Step 3.4: Create Service Account Key (JSON)

1. Find your service account in the list: `pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com`
2. Click the **⋮** (three dots) menu on the right
3. Click "Manage keys"
4. Click "ADD KEY" > "Create new key"
5. Select "JSON" format
6. Click "CREATE"
7. A JSON file will download automatically: `pdp-automation-prod-xxxxx.json`

**⚠️ CRITICAL SECURITY:**
- Save this file in a secure location (e.g., `./credentials/service-account.json`)
- **NEVER commit this file to Git**
- Add `credentials/` to your `.gitignore`
- Anyone with this file has full access to your Google Cloud resources

---

## Part 4: Create Cloud Storage Bucket

### Step 4.1: Create Bucket

1. Go to **Cloud Storage > Buckets**
2. Click "CREATE BUCKET"
3. Fill in details:

**Name your bucket:**
- Bucket name: `pdp-automation-assets` (must be globally unique)
- If taken, try: `pdp-automation-assets-[your-company-name]`

**Choose where to store your data:**
- Location type: **Region**
- Location: **us-central1** (Iowa)

**Choose a storage class:**
- Default storage class: **Standard**

**Control access to objects:**
- Uncheck "Enforce public access prevention"
- Access control: **Uniform**

**Protect object data:**
- Leave defaults (no versioning needed for uploads, enable for processed files)

4. Click "CREATE"

### Step 4.2: Set Lifecycle Policy (Auto-Cleanup)

1. Click on your bucket name: `pdp-automation-assets`
2. Click the "LIFECYCLE" tab
3. Click "ADD A RULE"

**Rule 1: Delete Uploads After 365 Days**
- Action: "Delete object"
- Object conditions:
  - Age: 365 days
  - Matches prefix: `uploads/`
- Click "CONTINUE"
- Click "CREATE"

**Rule 2: Delete Temp Files After 1 Day**
- Click "ADD A RULE" again
- Action: "Delete object"
- Object conditions:
  - Age: 1 day
  - Matches prefix: `temp/`
- Click "CONTINUE"
- Click "CREATE"

---

## Part 5: Set Up Secret Manager

### Step 5.1: Navigate to Secret Manager

1. Go to **Security > Secret Manager**
2. If prompted, click "ENABLE" (Secret Manager API should already be enabled)

### Step 5.2: Create Secrets

Create 4 secrets by following these steps for each:

**Secret 1: OpenAI API Key**
1. Click "CREATE SECRET"
2. Name: `openai-api-key`
3. Secret value: Paste your OpenAI API key (starts with `sk-`)
4. Replication: Automatic
5. Click "CREATE SECRET"

**Secret 2: Database URL**
1. Click "CREATE SECRET"
2. Name: `database-url`
3. Secret value: Paste your Neon PostgreSQL connection string
   ```
   postgresql://user:password@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
4. Replication: Automatic
5. Click "CREATE SECRET"

**Secret 3: JWT Secret Key**
1. Click "CREATE SECRET"
2. Name: `jwt-secret-key`
3. Secret value: Generate a random 64-character string:
   ```bash
   # Generate in terminal:
   openssl rand -hex 32
   ```
4. Replication: Automatic
5. Click "CREATE SECRET"

**Secret 4: OAuth Client Secret**
1. Click "CREATE SECRET"
2. Name: `oauth-client-secret`
3. Secret value: Your Google OAuth client secret (from Part 6)
4. Replication: Automatic
5. Click "CREATE SECRET"

### Step 5.3: Grant Service Account Access to Secrets

For EACH of the 4 secrets:

1. Click on the secret name
2. Click "PERMISSIONS" tab
3. Click "+ GRANT ACCESS"
4. Add principal:
   - New principals: `pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com`
   - Role: "Secret Manager Secret Accessor"
5. Click "SAVE"

Repeat for all 4 secrets:
- `openai-api-key`
- `database-url`
- `jwt-secret-key`
- `oauth-client-secret`

---

## Part 6: Set Up Google Workspace OAuth

### Step 6.1: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. User Type: Select **Internal** (restricts to @example.com domain only)
3. Click "CREATE"

**App information:**
- App name: `PDP Automation`
- User support email: Select your email (@example.com)
- App logo: (optional, can upload later)

**App domain:**
- Application home page: `https://your-production-domain.com` (or leave blank for now)
- Authorized domains: `example.com`

**Developer contact information:**
- Email addresses: Your email (@example.com)

4. Click "SAVE AND CONTINUE"

**Scopes:**
5. Click "ADD OR REMOVE SCOPES"
6. Search and add these scopes:
   - `openid`
   - `email`
   - `profile`
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/drive.file`
7. Click "UPDATE"
8. Click "SAVE AND CONTINUE"

**Summary:**
9. Review and click "BACK TO DASHBOARD"

### Step 6.2: Create OAuth Client ID

1. Go to **APIs & Services > Credentials**
2. Click "CREATE CREDENTIALS" > "OAuth client ID"
3. Application type: **Web application**
4. Name: `PDP Automation Web App`

**Authorized JavaScript origins:**
- Development: `http://localhost:5174`
- Production: `https://your-production-domain.com`

**Authorized redirect URIs:**
- Development: `http://localhost:5174/api/auth/callback`
- Production: `https://your-production-domain.com/api/auth/callback`

5. Click "CREATE"
6. **Save the Client ID and Client Secret** (you'll need these)

### Step 6.3: Enable Domain-Wide Delegation (for Sheets & Drive)

**Why needed:** Allows the service account to access Google Sheets and Drive on behalf of users in the organization.

1. Go to **IAM & Admin > Service Accounts**
2. Click on `pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com`
3. Click "SHOW ADVANCED SETTINGS" at the bottom
4. Find "Domain-wide delegation" section
5. Click "VIEW GOOGLE WORKSPACE ADMIN CONSOLE"

**In Google Workspace Admin Console:**
6. Navigate to **Security > API Controls > Domain-wide Delegation**
7. Click "Add new"
8. Client ID: Copy from service account JSON file (field: `client_id`)
9. OAuth Scopes: Enter both scopes separated by comma:
   ```
   https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.file
   ```
10. Click "AUTHORIZE"

**⚠️ CRITICAL:** Without domain-wide delegation, the service account cannot access Google Sheets or create Drive folders.

---

## Part 7: Set Up Google Drive Folder

### Step 7.1: Create Shared Folder

1. Go to [Google Drive](https://drive.google.com)
2. Click "+ New" > "Folder"
3. Folder name: `PDP Automation - Processed Assets`
4. Click "CREATE"

### Step 7.2: Share with Organization

1. Right-click the folder > "Share"
2. Click "Change" next to "Restricted"
3. Select "Anyone at the company with the link"
4. Permission level: **Viewer** (content managers can view, not edit)
5. Click "Done"

### Step 7.3: Add Service Account as Editor

1. Right-click the folder > "Share"
2. In "Add people and groups" field, enter:
   ```
   pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com
   ```
3. Permission level: **Editor** (service account needs to upload files)
4. Uncheck "Notify people" (no need to email the service account)
5. Click "Share"

### Step 7.4: Get Folder ID

1. Open the folder in Drive
2. Look at the URL in your browser:
   ```
   https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J
                                           ^^^^^^^^^^^^^^^^^^^^
                                           This is the Folder ID
   ```
3. **Copy the Folder ID** - you'll need it for environment variables

**Example:**
- URL: `https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p`
- Folder ID: `1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p`

---

## Part 8: Verification & Testing

### Step 8.1: Verify Service Account Permissions

1. Download the [Cloud Console app](https://console.cloud.google.com/) or use browser
2. Test service account key:

**Test 1: Storage Access**
```bash
gcloud auth activate-service-account --key-file=./credentials/service-account.json
gsutil ls gs://pdp-automation-assets
```
Expected: No errors, empty bucket list (or files if any)

**Test 2: Secret Manager Access**
```bash
gcloud secrets versions access latest --secret="openai-api-key"
```
Expected: Your OpenAI API key displayed

**Test 3: Sheets API Access**
- Create a test Google Sheet
- Share it with `pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com` as Editor
- Use gspread library to write a cell:
```python
import gspread
gc = gspread.service_account(filename='credentials/service-account.json')
sheet = gc.open_by_key('YOUR_TEST_SHEET_ID')
worksheet = sheet.sheet1
worksheet.update_acell('A1', 'Test successful!')
```
Expected: "Test successful!" appears in cell A1

**Test 4: Drive API Access**
```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/drive.file']
credentials = service_account.Credentials.from_service_account_file(
    'credentials/service-account.json',
    scopes=SCOPES
)
drive = build('drive', 'v3', credentials=credentials)

# List files in Drive folder
results = drive.files().list(
    q=f"'YOUR_FOLDER_ID' in parents",
    fields="files(id, name)"
).execute()

print(results.get('files', []))
```
Expected: Empty list (or files if any exist)

### Step 8.2: Checklist

Complete this checklist before proceeding:

**Google Cloud Platform:**
- [ ] Project created: `pdp-automation-prod`
- [ ] Billing account linked
- [ ] All 10 APIs enabled (verified in API Dashboard)
- [ ] Service account created with 5 IAM roles
- [ ] Service account JSON downloaded and stored in `./credentials/`
- [ ] Cloud Storage bucket created: `pdp-automation-assets`
- [ ] Lifecycle policies set (365 days for uploads, 1 day for temp)

**Secret Manager:**
- [ ] 4 secrets created (openai-api-key, database-url, jwt-secret-key, oauth-client-secret)
- [ ] Service account granted access to all 4 secrets

**Google Workspace:**
- [ ] OAuth consent screen configured as "Internal"
- [ ] OAuth client ID created (Web application)
- [ ] Client ID and secret saved
- [ ] Domain-wide delegation enabled for service account
- [ ] Scopes added: spreadsheets, drive.file

**Google Drive:**
- [ ] Shared folder created: "PDP Automation - Processed Assets"
- [ ] Folder shared with organization (Viewer access)
- [ ] Service account added as Editor
- [ ] Folder ID copied and saved

**Testing:**
- [ ] Service account can access Cloud Storage
- [ ] Service account can read secrets
- [ ] Service account can write to Google Sheets (test sheet)
- [ ] Service account can upload to Drive folder (test file)

---

## Part 9: Environment Variables

After completing all steps, update your environment variables:

**Backend (.env):**
```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=pdp-automation-prod
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
GCS_BUCKET_NAME=pdp-automation-assets

# Google Sheets
TEMPLATE_SHEET_ID_OPR=your-opr-template-id
TEMPLATE_SHEET_ID_MJL=your-mjl-template-id
TEMPLATE_SHEET_ID_PALM=your-palm-template-id

# Google Drive (CRITICAL - NEW)
GOOGLE_DRIVE_FOLDER_ID=your-folder-id-from-step-7.4

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=<stored-in-secret-manager>
ALLOWED_EMAIL_DOMAIN=example.com

# Anthropic API
ANTHROPIC_API_KEY=<stored-in-secret-manager>
ANTHROPIC_MODEL=claude-sonnet-4-5-20250514

# Database (Neon PostgreSQL)
DATABASE_URL=<stored-in-secret-manager>

# JWT
JWT_SECRET_KEY=<stored-in-secret-manager>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Frontend (.env.local):**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

---

## Troubleshooting

### Issue 1: "403 Forbidden" from Google Sheets API
**Cause:** Sheet not shared with service account
**Fix:** Share sheet with `pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com` as Editor

### Issue 2: "403 Forbidden" from Google Drive API
**Cause:** Service account lacks Drive folder access
**Fix:** Add service account to Drive folder with Editor permissions

### Issue 3: "Secret not found" error
**Cause:** Service account missing Secret Manager permissions
**Fix:** Grant "Secret Manager Secret Accessor" role to service account for each secret

### Issue 4: "Domain-wide delegation not enabled"
**Cause:** OAuth scopes not authorized in Workspace Admin Console
**Fix:** Follow Step 6.3 to authorize scopes in Admin Console

### Issue 5: "Invalid client" OAuth error
**Cause:** Redirect URI mismatch
**Fix:** Ensure redirect URI in OAuth client matches exactly (including http/https, port)

### Issue 6: Can't enable Google Sheets or Drive API
**Cause:** API name changed or billing not enabled
**Fix:** Search for "Sheets" or "Drive" in API Library, ensure billing is linked

---

## Security Best Practices

**Service Account JSON:**
- Store in `./credentials/` directory
- Add `credentials/` to `.gitignore`
- Never commit to Git or share publicly
- Rotate keys every 90 days
- Use separate service accounts for dev/prod

**Secret Manager:**
- Never hardcode secrets in code
- Always fetch from Secret Manager at runtime
- Use least privilege (only grant access to needed secrets)
- Audit secret access regularly

**OAuth:**
- Keep client secret secure
- Use "Internal" consent screen (restricts to @example.com)
- Implement CSRF protection
- Use HTTPS in production

**Drive Folder:**
- Organization-wide sharing is safe (internal only)
- Service account as Editor (can upload, not delete)
- Content managers as Viewer (can download, not edit)

---

## Cost Estimate

**Free Tier (included):**
- Secret Manager: First 10,000 operations/month free
- Cloud Storage: First 5 GB free
- Cloud Logging: First 50 GB free
- Google Drive: Included in Workspace (no extra cost)
- Google Sheets API: Free (Workspace included)

**Estimated Monthly Costs (Production):**
- Cloud Run: $10-20/month (depends on traffic)
- Cloud Storage: $5-10/month (after free tier)
- Cloud Tasks: $1-3/month
- **Total: $16-33/month**

**Not Included (External Services):**
- Neon PostgreSQL: $0 (dev) to $19/month (prod)
- OpenAI API: Covered by existing credits ($0/month for now)

---

## Next Steps

Once all checklist items are complete:

1. ✅ Test all integrations (Sheets, Drive, Storage, Secrets)
2. ✅ Clone the project repository
3. ✅ Set up environment variables (.env and .env.local)
4. ✅ Start local development environment
5. ✅ Run database migrations
6. ✅ Begin Phase 0 development

---

**Document Version:** 2.0
**Last Updated:** 2026-01-15
**Related Documentation:**
- [Prerequisites Setup](../../docs/00-prerequisites/EXTERNAL_SETUP_CHECKLIST.md)
- [Integrations > Google Cloud](../../docs/05-integrations/GOOGLE_CLOUD_SETUP.md)
- [DevOps > Deployment](../../docs/06-devops/DEPLOYMENT.md)
