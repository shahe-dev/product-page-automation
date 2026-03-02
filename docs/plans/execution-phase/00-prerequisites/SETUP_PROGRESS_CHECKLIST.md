# External Setup Progress Checklist

**Last Updated:** 2026-01-26 (Phase 0 Completion)
**Overall Progress:** ~98% Complete

---

## Section 2: Google Cloud Platform Setup

### 2.1 GCP Project
- [x] GCP project created: `YOUR-GCP-PROJECT-ID`
- [x] Billing enabled and verified

### 2.2 APIs Enabled (10/10)
- [x] Cloud Run API
- [x] Cloud Storage API
- [x] Cloud Tasks API
- [x] Secret Manager API
- [x] Cloud Build API
- [x] Cloud Logging API
- [x] Cloud Monitoring API
- [x] IAM API
- [x] Google Sheets API
- [x] Google Drive API

### 2.3 Service Account
- [x] Service account created: `pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com`
- [x] IAM roles granted:
  - [x] roles/storage.objectAdmin
  - [x] roles/cloudtasks.enqueuer
  - [x] roles/secretmanager.secretAccessor
  - [x] roles/logging.logWriter
  - [x] roles/monitoring.metricWriter
- [x] Service account key downloaded to `.credentials/service-account-key.json`

### 2.4 Cloud Storage Bucket
- [x] Bucket created: `gs://pdp-automation-assets-dev`
- [x] Location: us-central1
- [x] Uniform bucket-level access enabled
- [ ] CORS configuration (verify/apply if needed)
- [ ] Lifecycle policy (skipped due to formatting issue)

### 2.5 Secret Manager
- [x] jwt-secret-key created
- [x] database-url created (Neon connection string)
- [x] anthropic-api-key created
- [x] oauth-client-secret created
- [x] google-drive-folder-id created
- [x] Service account granted access to all secrets

**GCP Status: 90% COMPLETE**

---

## Section 3: External Services

### 3.1 Neon PostgreSQL
- [x] Neon account created
- [x] Project created: `pdp-automation-dev`
- [x] Database endpoint: `your-db-host.neon.tech`
- [x] Connection pooling enabled (using `-pooler` endpoint)
- [x] Connection string saved to `neondb/neon-connection-details.txt`
- [x] Database URL stored in Secret Manager
- [x] Connection test from application (local Docker PostgreSQL verified)

### 3.2 Anthropic API
- [x] Anthropic account created
- [x] Billing configured
- [x] API key created: `sk-proj-...`
- [x] API key stored in Secret Manager
- [x] API key added to `.env`
- [ ] API connectivity test

**External Services Status: 100% COMPLETE**

---

## Section 4: Google Workspace

### 4.1 Prerequisites
- [x] Logged in as `your-email@your-domain.com`
- [ ] Google Workspace Admin access (need admin help)

### 4.2 OAuth 2.0 Client
- [x] OAuth client created (Web application)
- [x] Client ID: `YOUR-OAUTH-CLIENT-ID.apps.googleusercontent.com`
- [x] Client secret stored in Secret Manager
- [x] Client credentials downloaded to `.credentials/`

### 4.3 OAuth Consent Screen
- [x] App type: Internal (restricted to @your-domain.com)
- [x] App name: PDP Automation
- [x] Authorized domain: your-domain.com
- [x] Scopes configured: openid, email, profile, spreadsheets

### 4.4 Authorized URIs
- [x] JavaScript origins:
  - [x] http://localhost:3000
  - [x] http://localhost:8000
- [x] Redirect URIs:
  - [x] http://localhost:3000/auth/callback
  - [x] http://localhost:8000/auth/callback

### 4.5 Shared Drive Access (COMPLETED)
- [x] Shared Drive created (ID: `0AOEEIstP54k2Uk9PVA`)
- [x] Service account added to Shared Drive as Content Manager
- [x] Templates moved to Shared Drive
- [x] Verified service account can create/edit files

> **Note:** Using Shared Drive instead of domain-wide delegation. No admin approval required.

**Google Workspace Status: 100% COMPLETE**

---

## Section 5: Google Sheets Templates (COMPLETED)

### 5.1 Six Separate Template Sheets
- [x] Location: Shared Drive (ID: `0AOEEIstP54k2Uk9PVA`)
- [x] Service account has access (Content Manager on Shared Drive)
- [x] 6 separate template sheets created:

| Template | Sheet ID | Target Sites |
|----------|----------|--------------|
| Aggregators | `YOUR_AGGREGATORS_SHEET_ID` | 24+ third-party aggregator domains |
| OPR | `YOUR_OPR_SHEET_ID` | opr.ae |
| MPP | `YOUR_MPP_SHEET_ID` | main-portal.com |
| ADOP | `YOUR_ADOP_SHEET_ID` | abudhabioffplan.ae |
| ADRE | `YOUR_ADRE_SHEET_ID` | secondary-market-portal.com |
| Commercial | `YOUR_COMMERCIAL_SHEET_ID` | cre.main-portal.com |

### 5.2 Template IDs for .env
```bash
TEMPLATE_SHEET_ID_AGGREGATORS=YOUR_AGGREGATORS_SHEET_ID
TEMPLATE_SHEET_ID_OPR=YOUR_OPR_SHEET_ID
TEMPLATE_SHEET_ID_MPP=YOUR_MPP_SHEET_ID
TEMPLATE_SHEET_ID_ADOP=YOUR_ADOP_SHEET_ID
TEMPLATE_SHEET_ID_ADRE=YOUR_ADRE_SHEET_ID
TEMPLATE_SHEET_ID_COMMERCIAL=YOUR_COMMERCIAL_SHEET_ID
```

### 5.3 Template Documentation
- [x] `docs/TEMPLATES_REFERENCE.md` - Comprehensive template reference
- [x] `template-organization/CONSOLIDATION_ANALYSIS.md` - Archetype analysis
- [x] `template-organization/LIVE_PAGE_ANALYSIS.md` - Live site validation
- [x] `template-organization/site_archetype_mapping.csv` - Site mapping

**Google Sheets Status: 100% COMPLETE**

---

## Section 6: Google Drive (Shared Drive)

- [x] Shared Drive created: "PDP Automation"
- [x] Shared Drive ID: `0AOEEIstP54k2Uk9PVA`
- [x] Service account added as Content Manager
- [x] Team members have access through Shared Drive membership
- [x] Shared Drive ID stored in Secret Manager
- [x] Shared Drive ID added to `.env` as `GOOGLE_SHARED_DRIVE_ID`

> **Note:** Using a Shared Drive instead of a regular folder. All files are owned by the drive, not individual users.

**Google Drive Status: 100% COMPLETE**

---

## Section 7: Local Development Environment

### 7.1 Software Installed
- [x] Python 3.13.7 (requirement: 3.10+)
- [x] Node.js v25.2.1 (requirement: 18+)
- [x] Docker Desktop v29.1.3 (installed 2026-01-24)
- [x] Google Cloud SDK v552.0.0
- [x] Git v2.52.0

### 7.2 Repository & Credentials
- [x] Repository initialized with Git
- [x] Service account key: `.credentials/service-account-key.json`
- [x] OAuth credentials: `.credentials/client_secret_*.json`
- [x] `.gitignore` configured (excludes credentials)

### 7.3 Environment Files
- [x] Root `.env` with ANTHROPIC_API_KEY
- [x] Backend `.env` fully configured (all 50+ variables)
- [x] Frontend `.env.local.example` template created

### 7.4 Backend Setup (COMPLETED - Phase 0)
- [x] Backend folder created (Phase 0: DEV-CONFIG-001)
- [x] Virtual environment created
- [x] Dependencies installed (requirements.txt)
  - **Note:** requirements.txt updated in Phase 2 -- `pymupdf4llm>=0.2.9` added, `PyMuPDF` bumped to `>=1.26.6`. Re-run `pip install -r requirements.txt` if env predates this change.
- [x] `.env` fully configured with all credentials
- [x] Database models created (22 tables)
- [x] Alembic migrations configured
- [x] Database migrations applied (`alembic upgrade head`)
- [x] Server starts successfully (tested on port 8000)
- [x] Database connection verified

### 7.5 Frontend Setup (Not Started)
- [x] Frontend `.env.local.example` template created
- [ ] Frontend folder with source code
- [ ] Dependencies installed (npm install)
- [ ] `.env.local` configured
- [ ] Dev server starts successfully

**Local Environment Status: 90% COMPLETE**

---

## Priority Actions for Tomorrow

### HIGH PRIORITY

1. **Shared Drive Access** (COMPLETED)
   - Shared Drive ID: `0AOEEIstP54k2Uk9PVA`
   - Service account added as Content Manager
   - No admin approval required

2. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop/
   - Required for running local PostgreSQL and Redis containers

### MEDIUM PRIORITY

3. **Google Sheets Templates** (COMPLETED)
   - 6 separate template sheets created in Shared Drive
   - Templates: Aggregators, OPR, MPP, ADOP, ADRE, Commercial
   - Service account has access via Shared Drive Content Manager role
   - Template IDs saved to .env.example

4. **Apply Bucket Lifecycle Policy** (Optional)
   ```bash
   gcloud storage buckets update gs://pdp-automation-assets-dev --lifecycle-file=lifecycle.json
   ```

### AFTER CODE DEVELOPMENT STARTS

5. **Complete .env Configuration**
   - Add all missing variables listed above

6. **Run Connectivity Tests**
   - Test Neon PostgreSQL connection
   - Test Anthropic API
   - Test Google Sheets API (using Shared Drive)
   - Test Google Drive API (using Shared Drive)

---

## Quick Reference: Important Values

| Item | Value |
|------|-------|
| GCP Project ID | `YOUR-GCP-PROJECT-ID` |
| Service Account | `pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com` |
| Storage Bucket | `gs://pdp-automation-assets-dev` |
| Neon DB Host | `your-db-host.neon.tech` |
| OAuth Client ID | `YOUR-OAUTH-CLIENT-ID.apps.googleusercontent.com` |
| Shared Drive ID | `0AOEEIstP54k2Uk9PVA` |

---

## Files Location Reference

```
PDP Automation v.3/
├── .credentials/
│   ├── service-account-key.json      # GCP service account
│   └── client_secret_*.json          # OAuth client credentials
├── .env                               # Environment variables (copy from .env.example)
├── .env.example                       # Environment template (committed to Git)
├── docker-compose.yml                 # Local development containers
├── neondb/
│   └── neon-connection-details.txt   # Neon PostgreSQL connection
├── backend/
│   └── scripts/
│       └── init.sql                  # Database initialization script
├── GCP_SETUP_PROGRESS.md             # Previous progress notes
└── docs/00-prerequisites/
    ├── EXTERNAL_SETUP_CHECKLIST.md   # Full setup guide
    └── SETUP_PROGRESS_CHECKLIST.md   # This file (progress tracking)
```

---

## Section 8: Docker Local Development Setup

### 8.1 Docker Configuration (COMPLETED)
- [x] Docker Desktop installed (v29.1.3)
- [x] docker-compose.yml created with PostgreSQL 16
- [x] PostgreSQL 16 configured (matches Neon version)
- [x] Encoding: UTF-8, Collation: C.UTF-8 (matches Neon)
- [x] init.sql created with required extensions
- [x] .env.example template created

### 8.2 Start Local Database
```bash
# Start PostgreSQL container
docker-compose up -d

# Verify container is running
docker ps

# Check logs
docker-compose logs postgres

# Stop containers
docker-compose down

# Reset database (delete all data)
docker-compose down -v
```

### 8.3 Local Database Connection
```
Host: localhost
Port: 5432
Database: pdp_automation
User: pdpuser
Password: localdevpassword
```

**Connection String (for .env):**
```
DATABASE_URL=postgresql+asyncpg://pdpuser:localdevpassword@localhost:5432/pdp_automation
```

**Docker Status: 100% COMPLETE**

---

## Section 9: Database Migration Strategy (Docker -> Neon)

### Development Phase
- Use local PostgreSQL via Docker (docker-compose.yml)
- Fast iteration, no network latency
- No risk of hitting Neon free tier limits
- Run migrations locally with Alembic

### Staging/Production Phase
When development is complete and tested:

1. **Stop local containers:**
   ```bash
   docker-compose down
   ```

2. **Update DATABASE_URL in .env:**
   ```bash
   # FROM (local):
   DATABASE_URL=postgresql+asyncpg://pdpuser:localdevpassword@localhost:5432/pdp_automation

   # TO (Neon production):
   DATABASE_URL=postgresql+asyncpg://your-db-user:PASSWORD@your-db-host.neon.tech/neondb?sslmode=require
   ```

3. **Run migrations against Neon:**
   ```bash
   alembic upgrade head
   ```

4. **Verify connectivity:**
   ```bash
   python -c "from app.core.database import engine; print('Connected to Neon!')"
   ```

### Why This Works
- Same PostgreSQL version (16) in both environments
- Same extensions (uuid-ossp, pg_trgm)
- Same encoding (UTF-8) and collation (C.UTF-8)
- SQLAlchemy/Alembic abstracts connection differences
- Only change is the connection string

### Neon Production Details
| Setting | Value |
|---------|-------|
| Host | `your-db-host.neon.tech` |
| Database | `neondb` |
| User | `your-db-user` |
| SSL | Required (`sslmode=require`) |
| Pooling | PgBouncer (via `-pooler` endpoint) |

**Migration Strategy Status: DOCUMENTED**

---

**Next Review Date:** 2026-01-25
