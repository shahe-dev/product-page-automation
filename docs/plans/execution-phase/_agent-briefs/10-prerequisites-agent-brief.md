# Agent Briefing: External Prerequisites & Setup Agent

**Agent ID:** prerequisites-setup-agent
**Batch:** 0 (Pre-Development Foundation)
**Priority:** P0 - CRITICAL - Must complete before ANY development begins
**Est. Context Usage:** 32,000 tokens

---

## ⚠️ CRITICAL MISSION

You are responsible for creating **THE MOST IMPORTANT DOCUMENT** in the entire documentation suite: the **External Prerequisites & Setup Guide**.

This document ensures the developer has **ALL external resources, accesses, accounts, and configurations** set up BEFORE writing a single line of code. Without this document being followed, the developer will hit endless blockers, debugging loops, and "why isn't this working?" moments that could have been avoided.

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/00-prerequisites/`

---

## Your Mission

Create **1 comprehensive, step-by-step guide** that walks through EVERY external setup requirement with:
- ✅ Clear checklist items
- ✅ Exact commands to run
- ✅ Screenshots of where to click (describe in text)
- ✅ What credentials to download and where to store them
- ✅ Common pitfalls and how to avoid them
- ✅ Verification steps to confirm each item is complete

**File to Create:**

`EXTERNAL_SETUP_CHECKLIST.md` (800-1000 lines) - Complete prerequisite setup guide

---

## Document Structure

### Part 1: Overview & Timeline
- What this document is for
- Who needs to complete these steps (user, not the developer agent)
- Estimated time: ~4-6 hours total
- Critical vs optional items
- Dependencies (what must be done before what)

### Part 2: Google Cloud Platform Setup (CRITICAL - 2-3 hours)

**2.1 Create GCP Project**
- Step-by-step instructions
- Enable billing
- Note project ID for later use

**2.2 Enable Required APIs**
Provide exact `gcloud` commands to enable:
- Cloud Run API
- Cloud Storage API
- Cloud Tasks API
- Secret Manager API
- Cloud Build API
- Cloud Logging API
- Cloud Monitoring API
- IAM API
- **Google Sheets API** (CRITICAL - system outputs content to Sheets)
- **Google Drive API** (CRITICAL - system uploads files to shared Drive folder)

**Note:** Vertex AI and Cloud SQL APIs are NOT required - we use Anthropic API (external) and Neon PostgreSQL (external) instead.

**2.3 Create Service Accounts**

**Primary Application Service Account:**
```bash
# Create service account
gcloud iam service-accounts create pdp-automation-sa \
  --display-name="PDP Automation Service Account" \
  --project=YOUR_PROJECT_ID

# Grant ALL required roles
for role in \
  roles/storage.objectAdmin \
  roles/cloudtasks.enqueuer \
  roles/secretmanager.secretAccessor \
  roles/logging.logWriter \
  roles/monitoring.metricWriter; do
  gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:pdp-automation-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="$role"
done

# Download service account key
gcloud iam service-accounts keys create ./credentials/service-account.json \
  --iam-account=pdp-automation-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**CRITICAL:** Explain where to store the JSON file and why it should NEVER be committed to Git.

**2.4 Set Up Cloud Storage Bucket**
```bash
# Create bucket
gsutil mb -p YOUR_PROJECT_ID -c STANDARD -l us-central1 gs://pdp-automation-assets

# Set lifecycle policy (auto-delete temp files after 1 day, uploads after 365 days)
```
Provide the lifecycle JSON configuration.

**2.5 Set Up Neon PostgreSQL Database**

**Why Neon instead of Cloud SQL:**
- Free tier for development ($0/month, 10 GB storage)
- Serverless (scales to zero when inactive, no 24/7 costs)
- Production tier only $19/month vs $450/month for Cloud SQL
- Same PostgreSQL, no migration needed between dev and production

**Steps:**
1. Go to [neon.tech](https://neon.tech)
2. Sign up for free account
3. Click "Create Project"
4. Project name: `pdp-automation`
5. Region: US East 1 (AWS)
6. PostgreSQL version: 16 (latest)
7. Click "Create Project"
8. **SAVE the connection string** shown on screen:
   ```
   postgresql://user:password@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
9. Connection pooling: Enabled by default ✅
10. Backups: Automatic ✅

**CRITICAL:** Store the Neon connection string in Secret Manager (see next section), not in .env files.

**2.6 Set Up Anthropic API**

**Steps:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create account
3. Go to [API Keys](https://console.anthropic.com/settings/keys)
4. Click "Create Key"
5. Name: "PDP Automation Production"
6. **COPY the key** (you won't see it again)
7. Save it securely - will be stored in Secret Manager next

**CRITICAL:** Store the Anthropic API key in Secret Manager (see next section), not in .env files.

**2.7 Set Up Secret Manager**
```bash
# Create secrets for sensitive values
echo -n "your-anthropic-api-key" | gcloud secrets create anthropic-api-key --data-file=-
echo -n "postgresql://user:pass@ep-xxxxx.neon.tech/neondb?sslmode=require" | gcloud secrets create database-url --data-file=-
echo -n "your-jwt-secret-key" | gcloud secrets create jwt-secret-key --data-file=-
echo -n "your-oauth-client-secret" | gcloud secrets create oauth-client-secret --data-file=-

# Grant service account access to ALL secrets
for secret in anthropic-api-key database-url jwt-secret-key oauth-client-secret; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:pdp-automation-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

**2.8 Verification Checklist**
- [ ] GCP project created with billing enabled
- [ ] All 10 required APIs enabled (Cloud Run, Storage, Tasks, Secret Manager, Build, Logging, Monitoring, IAM, **Sheets, Drive**)
- [ ] Service account created with 5 IAM roles
- [ ] Service account JSON downloaded and stored in `./credentials/`
- [ ] Cloud Storage bucket created
- [ ] Neon PostgreSQL database created and connection string saved
- [ ] Anthropic API key created and saved
- [ ] Google Drive folder created and shared with organization
- [ ] All secrets stored in Secret Manager (anthropic-api-key, database-url, jwt-secret-key, oauth-client-secret)
- [ ] Service account has access to all secrets

---

### Part 3: Google Workspace Setup (CRITICAL - 1 hour)

**3.1 Google Workspace Admin Access**
**REQUIREMENT:** You must have Google Workspace Admin privileges for the `@your-domain.com` domain.

If you don't have admin access, you MUST request it from your IT department before proceeding.

**3.2 Create OAuth 2.0 Client**
1. Go to [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" > "OAuth client ID"
3. Application type: **Web application**
4. Name: "PDP Automation Web App"
5. Authorized JavaScript origins:
   - `http://localhost:5174` (local dev)
   - `https://your-production-domain.com` (production)
6. Authorized redirect URIs:
   - `http://localhost:5174/api/auth/callback` (local dev)
   - `https://your-production-domain.com/api/auth/callback` (production)
7. Click "Create"
8. **Download the client ID and client secret** - store in Secret Manager

**3.3 Configure OAuth Consent Screen**
1. Go to [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
2. User Type: **Internal** (restricts to @your-domain.com domain only)
3. App name: "PDP Automation"
4. User support email: your-email@your-domain.com
5. Authorized domains: `your-domain.com`
6. Scopes: Add the following scopes:
   - `openid`
   - `email`
   - `profile`
   - `https://www.googleapis.com/auth/spreadsheets` (for Google Sheets access)

**3.4 Domain-Wide Delegation (for Google Sheets)**
1. Go to [Google Workspace Admin Console](https://admin.google.com)
2. Navigate to Security > API Controls > Domain-wide Delegation
3. Click "Add new"
4. Client ID: (your service account's client ID - found in service account JSON)
5. OAuth Scopes: `https://www.googleapis.com/auth/spreadsheets`
6. Click "Authorize"

**CRITICAL:** Without domain-wide delegation, the service account cannot access Google Sheets on behalf of users.

**3.5 Verification Checklist**
- [ ] Google Workspace Admin access confirmed
- [ ] OAuth 2.0 client created
- [ ] Client ID and secret stored in Secret Manager
- [ ] OAuth consent screen configured as "Internal"
- [ ] Domain-wide delegation enabled for service account
- [ ] Scopes include spreadsheets access

---

### Part 4: Google Sheets Templates (COMPLETED)

**4.1 Six Separate Template Sheets (Already Created)**
Six template sheets have been created in the Shared Drive:

| Template | Sheet ID | Target Sites |
|----------|----------|--------------|
| Aggregators | `YOUR_AGGREGATORS_SHEET_ID` | 24+ third-party aggregator domains |
| OPR | `YOUR_OPR_SHEET_ID` | opr.ae |
| MPP | `YOUR_MPP_SHEET_ID` | main-portal.com |
| ADOP | `YOUR_ADOP_SHEET_ID` | abudhabioffplan.ae |
| ADRE | `YOUR_ADRE_SHEET_ID` | secondary-market-portal.com |
| Commercial | `YOUR_COMMERCIAL_SHEET_ID` | cre.main-portal.com |

**4.2 Template Structure**
Each template must have the following fields (in Column A as labels, Column B for values):

**Required Fields:**
- A1: "Project Name" | B1: (will be filled by automation)
- A2: "Meta Title" | B2:
- A3: "Meta Description" | B3:
- A4: "URL Slug" | B4:
- A5: "H1 Heading" | B5:
- A6: "Developer" | B6:
- A7: "Location" | B7:
- A8: "Starting Price (AED)" | B8:
- A9: "Price per Sqft" | B9:
- A10: "Handover Date" | A10:
- A11: "Payment Plan" | B11:
- A12-A16: "Overview" (multi-line) | B12-B16:
- A17: "Amenities" | B17: (comma-separated list)
- A18: "Property Types" | B18: (e.g., "1BR, 2BR, 3BR")
- A19: "Unit Sizes" | B19: (e.g., "650-1200 sqft")

**4.3 Share Templates with Service Account**
1. Open each template sheet
2. Click "Share" button
3. Add the service account email: `pdp-automation-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com`
4. Give it **Editor** permissions
5. Click "Send"

**CRITICAL:** If you don't share the sheet with the service account, the API will return "403 Forbidden" errors.

**4.4 Store Template IDs**
Template IDs are already available. Store in your environment variables:
```bash
TEMPLATE_SHEET_ID_AGGREGATORS=YOUR_AGGREGATORS_SHEET_ID
TEMPLATE_SHEET_ID_OPR=YOUR_OPR_SHEET_ID
TEMPLATE_SHEET_ID_MPP=YOUR_MPP_SHEET_ID
TEMPLATE_SHEET_ID_ADOP=YOUR_ADOP_SHEET_ID
TEMPLATE_SHEET_ID_ADRE=YOUR_ADRE_SHEET_ID
TEMPLATE_SHEET_ID_COMMERCIAL=YOUR_COMMERCIAL_SHEET_ID
```

**4.5 Verification Checklist**
- [x] 6 Google Sheets templates created in Shared Drive
- [x] Each template has required fields with EN/AR/RU columns
- [x] Service account has access via Shared Drive Content Manager role
- [x] Template IDs documented

---

### Part 5: Local Development Environment (1-2 hours)

**Note:** JIRA integration has been removed from project scope as it adds unnecessary complexity.

**6.1 Install Required Software**

**Operating System Prerequisites:**
- **Windows:** WSL2 (Windows Subsystem for Linux) recommended
- **macOS:** Homebrew package manager
- **Linux:** Native support

**Required Installations:**

1. **Python 3.10+**
   ```bash
   # Verify version
   python3 --version  # Must be 3.10 or higher

   # If not installed:
   # macOS: brew install python@3.10
   # Ubuntu: sudo apt install python3.10 python3.10-venv
   # Windows: Download from python.org
   ```

2. **Node.js 18+**
   ```bash
   # Verify version
   node --version  # Must be 18 or higher

   # If not installed:
   # macOS: brew install node
   # Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   # Windows: Download from nodejs.org
   ```

3. **Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
   - Required for running PostgreSQL and Redis locally

4. **Google Cloud SDK (gcloud CLI)**
   ```bash
   # Install
   # macOS: brew install google-cloud-sdk
   # Linux: curl https://sdk.cloud.google.com | bash
   # Windows: Download installer from cloud.google.com/sdk/docs/install

   # Authenticate
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

5. **Git**
   ```bash
   git --version  # Should be 2.30+
   ```

**6.2 Clone Repository & Set Up Credentials**
```bash
# Clone repository
git clone https://github.com/your-org/pdp-automation.git
cd pdp-automation

# Create credentials directory
mkdir -p credentials

# Move service account JSON here
mv ~/Downloads/service-account.json ./credentials/

# CRITICAL: Add credentials/ to .gitignore
echo "credentials/" >> .gitignore
```

**6.3 Backend Setup**
```bash
cd backend

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing and linting

# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env  # or use your preferred editor
```

**Required .env Variables:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://pdpuser:PASSWORD@localhost:5432/pdp_automation

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
GCP_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=pdp-automation-assets
VERTEX_AI_LOCATION=us-central1

# Google Sheets (6 Templates)
TEMPLATE_SHEET_ID_AGGREGATORS=YOUR_AGGREGATORS_SHEET_ID
TEMPLATE_SHEET_ID_OPR=YOUR_OPR_SHEET_ID
TEMPLATE_SHEET_ID_MPP=YOUR_MPP_SHEET_ID
TEMPLATE_SHEET_ID_ADOP=YOUR_ADOP_SHEET_ID
TEMPLATE_SHEET_ID_ADRE=YOUR_ADRE_SHEET_ID
TEMPLATE_SHEET_ID_COMMERCIAL=YOUR_COMMERCIAL_SHEET_ID

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
ALLOWED_EMAIL_DOMAIN=your-domain.com

# JWT
JWT_SECRET_KEY=generate-a-random-64-character-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Environment
ENVIRONMENT=development
DEBUG=true
```

**6.4 Frontend Setup**
```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local
nano .env.local
```

**Required .env.local Variables:**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_OAUTH_CLIENT_ID=your-client-id
```

**6.5 Start Local Database (Docker)**
```bash
# From project root
docker-compose up -d postgres redis

# Verify containers are running
docker ps

# Run database migrations
cd backend
alembic upgrade head
```

**6.6 Verification Checklist**
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Docker Desktop installed and running
- [ ] gcloud CLI installed and authenticated
- [ ] Repository cloned
- [ ] Service account JSON in `./credentials/`
- [ ] Backend .env file configured with all variables
- [ ] Frontend .env.local file configured
- [ ] PostgreSQL and Redis containers running
- [ ] Database migrations applied

---

### Part 7: External Services & Monitoring (Optional for MVP, Required for Production)

**7.1 Sentry (Error Tracking)**
1. Create account at [sentry.io](https://sentry.io)
2. Create new project: "PDP Automation Backend"
3. Copy DSN (Data Source Name)
4. Add to .env:
   ```bash
   SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
   ```

**7.2 Production Domain & SSL**
- Purchase domain or use existing company domain
- Set up DNS A record pointing to Cloud Run service IP
- Cloud Run automatically provisions SSL certificate

**7.3 Email Service (for notifications - optional)**
- SendGrid or Google Workspace SMTP
- Configure SMTP settings in .env

---

### Part 8: Pre-Development Verification (15 minutes)

**Run this checklist before writing ANY code:**

**Google Cloud:**
- [ ] GCP project created with billing enabled
- [ ] All 8 required APIs enabled (Run, Storage, Tasks, Secret Manager, Build, Logging, Monitoring, IAM)
- [ ] Service account created with 5 IAM roles
- [ ] Service account JSON downloaded and in `./credentials/`
- [ ] Cloud Storage bucket created
- [ ] Secrets stored in Secret Manager (anthropic-api-key, database-url, jwt-secret-key, oauth-client-secret)

**External Services:**
- [ ] Neon PostgreSQL database created and connection string saved
- [ ] Anthropic API key created and saved

**Google Workspace:**
- [ ] OAuth 2.0 client created
- [ ] OAuth consent screen configured as "Internal"
- [ ] Domain-wide delegation enabled
- [ ] Client ID and secret stored

**Google Sheets:**
- [x] 6 template sheets created (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
- [x] Templates accessible via Shared Drive Content Manager role
- [x] Template IDs available in .env.example

**Local Environment:**
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Docker Desktop running
- [ ] gcloud CLI authenticated
- [ ] Repository cloned
- [ ] Backend .env configured
- [ ] Frontend .env.local configured
- [ ] Database containers running
- [ ] Migrations applied

**Test Connectivity:**
```bash
# Test GCP authentication
gcloud auth list

# Test service account
gcloud auth activate-service-account --key-file=./credentials/service-account.json

# Test Cloud Storage access
gsutil ls gs://pdp-automation-assets

# Test Neon PostgreSQL connection
psql "postgresql://user:pass@ep-xxxxx.neon.tech/neondb?sslmode=require" -c "SELECT version();"

# Test Anthropic API (requires anthropic Python package)
python -c "import anthropic; c=anthropic.Anthropic(api_key='YOUR_KEY'); print('API connected')"

# Test Secret Manager access
gcloud secrets versions access latest --secret="anthropic-api-key"
```

If ALL tests pass, you're ready to start development! 🎉

---

## Common Pitfalls & Troubleshooting

### Issue 1: "403 Forbidden" from Google Sheets API
**Cause:** Template not shared with service account
**Fix:** Share each template with `pdp-automation-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com` as Editor

### Issue 2: "Could not authenticate with service account"
**Cause:** Service account JSON not found or invalid
**Fix:**
- Verify file exists at `./credentials/service-account.json`
- Verify `GOOGLE_APPLICATION_CREDENTIALS` path is correct in .env
- Re-download service account key if corrupted

### Issue 3: "Access denied to Secret Manager"
**Cause:** Service account missing secretmanager.secretAccessor role
**Fix:** Grant role:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:pdp-automation-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Issue 5: "OAuth domain restriction failed - user not @your-domain.com"
**Cause:** OAuth consent screen not configured as "Internal"
**Fix:** Go to OAuth consent screen settings and change User Type to "Internal"

### Issue 6: "Neon PostgreSQL connection failed"
**Cause:** Invalid connection string or network issue
**Fix:**
- Verify connection string format is correct (includes `?sslmode=require`)
- Check that Neon project is not paused (free tier auto-pauses after inactivity)
- Test connection from your machine: `psql "YOUR_CONNECTION_STRING" -c "SELECT 1;"`
- Verify connection pooling endpoint is used (ends with `-pooler.`)

### Issue 7: "Anthropic API authentication failed"
**Cause:** Invalid API key or insufficient credits
**Fix:**
- Verify API key is correct (starts with `sk-ant-`)
- Check API key has not been revoked at [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
- Verify account has sufficient credits/billing set up
- Test with curl: `curl https://api.anthropic.com/v1/messages -H "x-api-key: YOUR_API_KEY" -H "anthropic-version: 2023-06-01"`

---

## Security Reminders

**NEVER COMMIT THESE FILES TO GIT:**
- `credentials/service-account.json`
- `.env`
- `.env.local`
- Any files containing API tokens, passwords, or secrets

**Verify .gitignore includes:**
```
credentials/
.env
.env.local
*.json  # Service account keys
```

**Use Secret Manager for Production:**
- Store all secrets in Google Secret Manager
- Access secrets via Secret Manager API, not .env files
- Rotate secrets every 90 days

---

## Timeline Estimate

**Critical Items (Must complete before development):**
- Google Cloud setup: 2-3 hours
- Google Workspace setup: 1 hour
- Google Sheets templates: 30 minutes
- Local environment: 1-2 hours

**Total: 4.5-6.5 hours**

**Optional Items (Can complete during development):**
- Sentry setup: 15 minutes
- Production domain: 30 minutes

---

## Next Steps

Once you've completed ALL items in the Pre-Development Verification checklist:

1. ✅ Mark this document as complete
2. ✅ Verify all credentials are stored securely
3. ✅ Run all connectivity tests
4. ✅ Commit initial `.env.example` and `.env.local.example` files (WITHOUT secrets) to Git
5. ✅ Proceed to Phase 0 development: Authentication & Security

**Important:** Keep this document updated as you discover new prerequisites during development!

---

**Last Updated:** [To be filled by agent]
**Document Version:** 1.0
**Related Documentation:**
- [Architecture > Infrastructure](../01-architecture/INFRASTRUCTURE.md)
- [Integrations > Google Cloud Setup](../05-integrations/GOOGLE_CLOUD_SETUP.md)
- [DevOps > Local Development](../06-devops/LOCAL_DEVELOPMENT.md)
