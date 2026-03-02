# Reference Materials Collection Checklist

**Purpose:** This checklist identifies all external reference materials you should gather before/during documentation creation. These materials will help ensure accuracy and provide real-world examples in the documentation.

**Priority:** Complete high-priority items before launching agents. Medium/low priority items can be gathered during documentation review.

---

## High Priority (Complete Before Agent Launch)

### 1. Sample PDF Brochures (3-5 examples)
**Location:** `reference/company/sample-brochures/`
**What to collect:**
- [ ] Sample OPR brochure (standard residential project)
- [ ] Sample MPP brochure (commercial project)
- [ ] Sample Commercial brochure
- [ ] One "good quality" brochure (clear text, organized layout)
- [ ] One "problematic" brochure (encrypted, poor OCR, heavy watermarks) - for troubleshooting docs

**Why needed:**
- Agents can reference real examples in documentation
- Troubleshooting guide can show actual error scenarios
- User guides can include realistic workflows

---

### 2. Google Sheets Templates
**Location:** `reference/company/sheet-templates/`
**What to collect:**
- [ ] Aggregators template (24+ domains)
- [ ] OPR template (opr.ae)
- [ ] MPP template (main-portal.com)
- [ ] ADOP template (abudhabioffplan.ae)
- [ ] ADRE template (secondary-market-portal.com)
- [ ] Commercial template (cre.main-portal.com)
- [ ] Blank template structure (for documentation screenshots)

**Why needed:**
- Integration docs need exact field mappings
- Backend docs need to show template structure
- User guides need to show what output looks like

**Format:** Export as Excel + keep Google Sheets URL

---

### 3. Brand Guidelines & Style Guide
**Location:** `reference/company/brand-guidelines/`
**What to collect:**
- [ ] Content writing guidelines (tone, style, formatting)
- [ ] SEO requirements (character limits, keyword usage)
- [ ] Image specifications (dimensions, file sizes, formats)
- [ ] Naming conventions (projects, files, URLs)

**Why needed:**
- Prompt Library docs need to reference style requirements
- Content Generation docs need character limits
- User guides need to show quality standards

---

### 4. Google Cloud Project Details & Service Account
**Location:** `reference/google-cloud/`
**What to collect:**
- [ ] **GCP Project created with billing enabled** ⭐ CRITICAL
- [ ] **Service Account JSON downloaded** ⭐ CRITICAL (for Sheets + Storage)
- [ ] **Google Workspace Admin Access** ⭐ CRITICAL (to configure OAuth domain restriction)
- [ ] GCP Project ID (production)
- [ ] GCP Project ID (development/staging)
- [ ] Service account email addresses
- [ ] Cloud Run service names
- [ ] Cloud Storage bucket names
- [ ] Neon PostgreSQL connection details (external to GCP)

**Service Account Roles & Permissions:**

**Primary Application Service Account:** `pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com`

Required IAM roles:
1. **`roles/storage.objectAdmin`** - Full access to Cloud Storage bucket (upload PDFs, store processed images)
2. **`roles/cloudtasks.enqueuer`** - Create and enqueue background processing jobs
3. **`roles/secretmanager.secretAccessor`** - Read secrets (Anthropic API key, OAuth secrets, JWT secret, database URL)
4. **`roles/logging.logWriter`** - Write application logs to Cloud Logging
5. **`roles/monitoring.metricWriter`** - Write custom metrics to Cloud Monitoring

**Note:** Anthropic API key should be stored in Secret Manager with name `anthropic-api-key`. Neon PostgreSQL connection string should also be stored in Secret Manager with name `database-url`.

**Google Sheets Service Account:** (can be same as above or separate)
- Enable **Google Workspace Domain-Wide Delegation**
- Scopes: `https://www.googleapis.com/auth/spreadsheets`
- Must be added to each Google Sheet with **Editor permissions**

**Cloud Build Service Account:** `[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com` (auto-created)
- **`roles/run.admin`** - Deploy to Cloud Run
- **`roles/iam.serviceAccountUser`** - Act as runtime service account
- **`roles/storage.admin`** - Access build artifacts

**Setup Commands:**
```bash
# Create service account
gcloud iam service-accounts create pdp-automation-sa \
  --display-name="PDP Automation Service Account"

# Grant all required roles
for role in \
  roles/storage.objectAdmin \
  roles/cloudtasks.enqueuer \
  roles/secretmanager.secretAccessor \
  roles/logging.logWriter \
  roles/monitoring.metricWriter; do
  gcloud projects add-iam-policy-binding pdp-automation-prod \
    --member="serviceAccount:pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com" \
    --role="$role"
done

# Download service account key (store securely)
gcloud iam service-accounts keys create ./credentials/service-account.json \
  --iam-account=pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com

# Store Anthropic API key in Secret Manager
echo -n "your-anthropic-api-key" | gcloud secrets create anthropic-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Store Neon database URL in Secret Manager
echo -n "postgresql://user:pass@ep-xxxxx.neon.tech/neondb?sslmode=require" | gcloud secrets create database-url \
  --data-file=- \
  --replication-policy="automatic"
```

**Security Best Practices:**
- Use **principle of least privilege** (only grant minimum required permissions)
- Consider **separate service accounts** for different purposes (runtime, sheets, CI/CD)
- **Rotate keys every 90 days**
- Use **Workload Identity** where possible instead of JSON keys
- **Never commit** service account JSON to Git

**Why needed:**
- DevOps docs need exact resource names
- Integration docs need correct endpoints
- Deployment guide needs real configuration
- **Service Account JSON is required for Google Cloud Storage and Sheets integrations**
- **Workspace Admin Access is required for OAuth domain restriction (@your-domain.com only)**
- **Anthropic API key is required for all AI-powered features (document extraction, vision tasks, content generation)**
- **Neon PostgreSQL connection details are required for database access**

**Format:** Create `gcp-resources.md` file with all details

**Security:** Keep Service Account JSON secure, never commit to Git

---

## Medium Priority (Can Gather During Documentation Phase)

### 6. Existing Workflow Documentation
**Location:** `reference/company/workflows/`
**What to collect:**
- [ ] Current manual workflow (if documented)
- [ ] Approval process flowchart
- [ ] Publishing checklist (current version)
- [ ] Team roles and responsibilities
- [ ] Communication channels (Slack, email)

**Why needed:**
- Module docs can show before/after comparison
- User guides can address current pain points
- Training materials can highlight improvements

---

### 7. API Access Credentials (for Testing)
**Location:** Keep secure - don't commit to repo
**What to collect:**
- [ ] Google OAuth Client ID (dev environment)
- [ ] Google OAuth Client Secret (dev environment)
- [ ] Service account JSON file (dev)

**Why needed:**
- Developer guide needs working examples
- Testing docs need valid test credentials
- Local development setup instructions

**Security Note:** Use development/test credentials only. Never commit to repository.

---

### 8. Cost & Usage Data
**Location:** `reference/technical/`
**What to collect:**
- [ ] Current monthly Anthropic API usage (if available)
- [ ] Average brochures processed per month
- [ ] Peak usage periods
- [ ] Budget constraints

**Why needed:**
- Architecture docs can show realistic cost projections
- Performance testing can target realistic load
- Admin guide can show cost monitoring

---

### 9. Error Logs & Common Issues
**Location:** `reference/technical/`
**What to collect:**
- [ ] Cloud Logging exports (last 30 days)
- [ ] Sentry error reports (if already using)
- [ ] Support tickets / user complaints
- [ ] Known issues list

**Why needed:**
- Troubleshooting guide can address real issues
- FAQ can answer actual user questions
- Error handling docs can show realistic scenarios

---

## Low Priority (Nice to Have)

### 10. External Documentation URLs
**Location:** `reference/technical/external-docs.md`
**What to collect:**

**Google Cloud Documentation:**
- [ ] [Cloud Run Docs](https://cloud.google.com/run/docs)
- [ ] [Cloud Storage Docs](https://cloud.google.com/storage/docs)
- [ ] [Google Sheets API](https://developers.google.com/sheets/api/guides/concepts)
- [ ] [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)

**Anthropic Documentation:**
- [ ] [Anthropic API Quickstart](https://docs.anthropic.com/en/docs/quickstart)
- [ ] [Anthropic API Reference](https://docs.anthropic.com/en/api)
- [ ] [Claude Vision Guide](https://docs.anthropic.com/en/docs/vision)
- [ ] [Anthropic Pricing](https://www.anthropic.com/pricing)

**Database Documentation:**
- [ ] [Neon PostgreSQL Docs](https://neon.tech/docs/introduction)
- [ ] [Neon Connection Pooling](https://neon.tech/docs/connect/connection-pooling)

**Technical Reference:**
- [ ] [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [ ] [React Query Docs](https://tanstack.com/query/latest)
- [ ] [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [ ] [PyMuPDF Docs](https://pymupdf.readthedocs.io/)
- [ ] [pymupdf4llm Docs](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
- [ ] [OpenCV Python Docs](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)

**Why needed:**
- Integration docs can link to official documentation
- Developer guide can reference authoritative sources
- DevOps docs can link to deployment guides

**How to organize:** Create a markdown file with categorized links

---

### 11. Company Branding & UX References
**Location:** `reference/company/`
**What to collect:**
- [ ] Company logo (PNG, SVG formats)
- [ ] Color scheme / brand colors
- [ ] Existing prompts from Telegram bots (if accessible)
- [ ] Sample QA reports from current manual QA process
- [ ] Competitor/inspiration apps (screenshots or URLs)

**Why needed:**
- Frontend docs can show branded UI examples
- User guides can include actual company branding
- Troubleshooting can reference existing QA patterns

---

### 12. Website Page Structures
**Location:** `reference/company/`
**What to collect:**
- [ ] OPR website page structure (where content fields go)
- [ ] MPP website page structure
- [ ] Commercial website page structure
- [ ] Screenshots of published property pages
- [ ] CMS documentation (if available)

**Why needed:**
- Publisher guide needs to show exactly where to place content
- Integration docs need to map fields to page elements
- User guides can show end-to-end workflow

---

### 13. Competitor Analysis
**Location:** `reference/company/`
**What to collect:**
- [ ] How competitors handle property detail pages
- [ ] Industry best practices for real estate content
- [ ] SEO benchmarks

**Why needed:**
- Can enrich user guides with industry context
- Can justify design decisions in architecture docs

---

### 14. Team Feedback & User List
**Location:** `reference/company/`
**What to collect:**
- [ ] **User list with emails and roles** ⭐ IMPORTANT (content, marketing, publishing, admin)
- [ ] Interviews with content creators (pain points)
- [ ] Interviews with marketing managers (approval criteria)
- [ ] Interviews with publishers (publishing checklist needs)
- [ ] Developer team API requirements

**Why needed:**
- User guides tailored to actual needs
- Feature documentation addresses real use cases
- **User list required for permission configuration and initial system setup**

---

### 15. Training Materials (if existing)
**Location:** `reference/company/`
**What to collect:**
- [ ] Existing training presentations
- [ ] Video tutorials (if any)
- [ ] Quick reference cards
- [ ] Onboarding checklists

**Why needed:**
- Can incorporate into new user guides
- Can identify what's missing in current training

---

## Collection Strategy

### Immediate Action Items (Before Launching Agents)
1. **Sample Brochures** (Items 1) - Request from content team
2. **Google Sheets Templates** (Item 2) - Download from Google Drive
3. **GCP Resource Names** (Item 4) - Extract from Cloud Console
4. **Brand Guidelines** (Item 3) - Request from marketing

### During Agent Execution
- Gather medium priority items as agents work on related documentation
- Use placeholders like `[YOUR_PROJECT_ID]` if exact values not available yet
- Update documentation after agents complete

### After Agent Completion
- Fill in any placeholder values
- Add low priority reference materials to enrich documentation
- Update based on team feedback

---

## How to Organize Reference Materials

**Recommended Folder Structure:**
```
reference/
├── google-cloud/
│   ├── gcp-resources.md
│   ├── service-account-dev.json
│   └── deployment-commands.md
├── company/
│   ├── sheet-templates/
│   │   ├── opr-template.xlsx
│   │   ├── mpp-template.xlsx
│   │   └── field-mapping.json
│   ├── sample-brochures/
│   │   ├── sample-opr.pdf
│   │   ├── sample-mpp.pdf
│   │   └── sample-problematic.pdf
│   ├── brand-guidelines/
│   │   ├── content-style-guide.pdf
│   │   └── seo-requirements.md
│   └── workflows/
│       ├── current-approval-process.pdf
│       └── publishing-checklist.xlsx
└── technical/
    ├── api-credentials-dev.md (gitignored)
    ├── cost-analysis.xlsx
    └── error-logs-sample.txt
```

---

## Placeholder Strategy

If you don't have certain reference materials yet, agents can use **placeholders**:

**Example Placeholders:**
- Project ID: `[YOUR_GCP_PROJECT_ID]`
- Bucket Name: `[YOUR_BUCKET_NAME]`
- Template ID: `[YOUR_TEMPLATE_SHEET_ID]`
- Drive Folder ID: `[YOUR_DRIVE_FOLDER_ID]`

**Update Later:** After agents complete, search documentation for `[YOUR_` and replace with actual values.

---

## Questions to Answer Before Launch

Before launching documentation agents, try to answer these:

1. **What are your exact GCP resource names?** (Project ID, Cloud Run services, etc.)
2. **Do you have sample PDF brochures available?** (At least 2-3)
3. **Are Google Sheets templates finalized?** (Or still in development?)
4. **Do you have brand/content guidelines documented?** (Or should agents create generic examples?)
5. **Is Google Drive folder created and shared with organization?** (For processed file sharing)

---

## Impact on Agent Execution

### If Reference Materials Available:
- ✅ Agents can include real examples
- ✅ Configuration guides will be exact
- ✅ User guides will be realistic
- ✅ Troubleshooting will address actual issues

### If Reference Materials Missing:
- ⚠️ Agents will use generic examples
- ⚠️ Placeholders like `[YOUR_PROJECT_ID]` will be used
- ⚠️ You'll need to update documentation after gathering materials
- ⚠️ User guides may be less practical

**Recommendation:** Complete **high priority** items before launching agents. This ensures documentation is immediately usable.

---

## Checklist Status Tracker

Use this to track your progress:

### ⭐ CRITICAL (Must Have Before Development Starts)
- [ ] **Google Cloud Project created with billing enabled**
- [ ] **Service Account JSON downloaded** (for Storage + Sheets)
- [ ] **Anthropic API key with sufficient credits** ($200/month recommended)
- [ ] **Neon PostgreSQL database created** with connection details saved
- [ ] **Google Workspace Admin Access** (for OAuth domain restriction)
- [ ] **At least 1 Google Sheet Template** (OPR, MPP, or Commercial)
- [ ] **3-5 Sample PDF Brochures** from actual past projects
- [ ] **User list with emails and roles** (content, marketing, publishing, admin)

**Est. time: 2-3 hours**

---

### 🔴 High Priority (Complete Before Agent Launch)
- [ ] Sample PDF brochures (3-5) - **30 min**
- [ ] Google Sheets templates (3) - **15 min**
- [ ] Brand guidelines - **15 min**
- [ ] GCP resource details + Service Account - **30 min**
- [ ] Google Drive folder setup - **10 min**

**Est. time: ~2 hours**

---

### 🟡 Medium Priority (Needed for Module Development)
- [ ] All Google Sheet Templates (OPR, MPP, Commercial)
- [ ] Brand/Tone Guidelines for content generation
- [ ] Website page structures showing where content goes
- [ ] Current approval workflow documentation
- [ ] Workflow documentation - **1 hour**
- [ ] API credentials (dev) - **30 min**
- [ ] Cost/usage data - **30 min**
- [ ] Error logs - **1 hour**

**Est. time: ~3 hours**

---

### 🟢 Low Priority (Nice to Have for Polish)
- [ ] Company logo for web app branding
- [ ] Existing prompts from Telegram bots (if accessible)
- [ ] Sample QA reports from current manual process
- [ ] Competitor/inspiration apps for UX reference
- [ ] External documentation URLs (Google Cloud, Anthropic, Neon, etc.)
- [ ] Website page structure screenshots
- [ ] Competitor analysis - **2 hours**
- [ ] Team feedback - **3 hours**
- [ ] Existing training materials - **1 hour**

**Est. time: ~6 hours**

---

**Total Est. Time:**
- **Critical + High Priority:** ~4-5 hours
- **All Items:** ~15 hours

---

B. DOCUMENTS YOU MUST COLLECT
These are external resources I cannot access - you need to gather them:

B.1 GOOGLE CLOUD DOCUMENTATION (Required)
Document	URL	Why Needed
Cloud Run Docs	https://cloud.google.com/run/docs	Deployment configuration
Cloud Storage Docs	https://cloud.google.com/storage/docs	File storage patterns
Google Sheets API	https://developers.google.com/sheets/api/guides/concepts	Spreadsheet automation
Google OAuth 2.0	https://developers.google.com/identity/protocols/oauth2	Workspace authentication

B.1.1 ANTHROPIC API DOCUMENTATION (Required)
Document	URL	Why Needed
Anthropic API Quickstart	https://docs.anthropic.com/en/api/getting-started	API authentication and patterns
Anthropic API Reference	https://docs.anthropic.com/en/api/messages	Model parameters and usage
Claude Vision Guide	https://docs.anthropic.com/en/docs/build-with-claude/vision	Image understanding capabilities
Anthropic Pricing	https://www.anthropic.com/pricing	Accurate cost calculations

B.1.2 DATABASE DOCUMENTATION (Required)
Document	URL	Why Needed
Neon PostgreSQL Docs	https://neon.tech/docs/introduction	Serverless PostgreSQL setup
Neon Connection Pooling	https://neon.tech/docs/connect/connection-pooling	Connection management

B.2 YOUR COMPANY-SPECIFIC DOCUMENTS (Critical)
Document	Description	Why Needed
Google Sheet Template	Actual template used for OPR/MPP/Commercial	Cell mapping, structure
Brand Guidelines	Tone, voice, terminology for content generation	Prompt engineering
Website Templates	Existing page structures on your websites	Content field mapping
Sample Brochures	3-5 actual PDF brochures from past projects	Testing, extraction patterns
Approval Workflow Doc	Current manual approval process description	Digitize existing workflow
User List	Who will use this, their roles, email domains	Permission configuration
Company Domain Info	@your-domain.com Google Workspace admin access	OAuth domain restriction

B.3 TECHNICAL REFERENCE (Nice to Have)
Document	URL	Why Needed
FastAPI Best Practices	https://fastapi.tiangolo.com/tutorial/	Backend patterns
React Query Docs	https://tanstack.com/query/latest	Data fetching patterns
Tailwind CSS Docs	https://tailwindcss.com/docs	Styling reference
PyMuPDF Docs	https://pymupdf.readthedocs.io/	PDF extraction
OpenCV Python Docs	https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html	Image processing

YOUR DOCUMENT COLLECTION CHECKLIST

Priority 1: Must Have Before Development Starts
 Google Cloud Project created with billing enabled
 Service Account JSON downloaded for Sheets + Storage + Drive
 Anthropic API key with sufficient credits
 Neon PostgreSQL database created and connection details saved
 Google Workspace Admin Access to configure OAuth domain restriction
 Google Drive folder created and shared with @your-domain.com organization
 At least 1 Google Sheet Template (OPR, MPP, or Commercial)
 3-5 Sample PDF Brochures from actual past projects
 User list with emails and their roles (content, marketing, publishing, admin)

Priority 2: Needed for Module Development
 All Google Sheet Templates (OPR, MPP, Commercial)
 Brand/Tone Guidelines for content generation
 Website page structures showing where content goes
 Current approval workflow documentation (even informal)

Priority 3: Nice to Have for Polish
 Company logo for the web app branding
 Existing prompts from current Telegram bots (if accessible)
 Sample QA reports from current manual QA process
 Competitor/inspiration web apps you like the UX of


## Ready to Launch?

Once you've gathered **high priority** reference materials (or decided to use placeholders), you're ready to launch the documentation agents!

**Next Step:** Let me know when you're ready, and I'll launch Batch 1 (Architecture + Backend agents) in parallel.