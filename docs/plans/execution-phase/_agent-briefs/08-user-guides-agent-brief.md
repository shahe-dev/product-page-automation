# Agent Briefing: User Guides Documentation Agent

**Agent ID:** user-guides-docs-agent
**Batch:** 4 (User-Facing)
**Priority:** P3 - User Documentation
**Est. Context Usage:** 37,000 tokens

---

## Your Mission

Create **5 user guide documentation files** for all 4 user departments (Content Creators, Marketing Managers, Publishers, Developers, plus Admin).

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/08-user-guides/`

---

## Files You Must Create

1. `CONTENT_CREATOR_GUIDE.md` (400-500 lines) - Complete guide for content creators
2. `MARKETING_MANAGER_GUIDE.md` (350-400 lines) - Approval workflow guide
3. `PUBLISHER_GUIDE.md` (350-400 lines) - Publishing workflow guide
4. `ADMIN_GUIDE.md` (400-500 lines) - System administration guide
5. `DEVELOPER_GUIDE.md` (400-500 lines) - API integration guide for web developers

**Total Output:** ~1,900-2,300 lines across 5 files

---

## Target Audience Profiles

### Content Creator
- **Role:** Upload PDFs, review generated content, submit for approval
- **Technical Level:** Basic computer skills
- **Primary Pages:** Processing, Projects, Content Preview
- **Goals:** Quick processing, accurate content, easy submission

### Marketing Manager
- **Role:** Review content, approve/reject, request revisions
- **Technical Level:** Intermediate
- **Primary Pages:** Approval Queue, Projects, QA History
- **Goals:** Fast review, quality assurance, clear feedback

### Publisher
- **Role:** Download assets, create pages, mark as published
- **Technical Level:** Intermediate to advanced (website CMS knowledge)
- **Primary Pages:** Publishing Queue, Projects
- **Goals:** Easy asset access, clear checklists, URL tracking

### Admin
- **Role:** User management, system monitoring, troubleshooting
- **Technical Level:** Advanced
- **Primary Pages:** Admin Dashboard, History, All modules
- **Goals:** System health, user management, audit trails

### Developer (Web Team)
- **Role:** Integrate with PDP Automation API
- **Technical Level:** Advanced (programming)
- **Primary Focus:** API endpoints, webhooks, data formats
- **Goals:** Easy integration, clear documentation, reliable APIs

---

## 1. Content Creator Guide

**Table of Contents:**
1. Getting Started
2. Logging In (Google OAuth)
3. Uploading a PDF Brochure
4. Monitoring Processing Progress
5. Reviewing Generated Content
6. Editing Project Information
7. Submitting for Approval
8. Handling Revision Requests
9. Viewing Your Projects
10. Common Issues & Solutions

**Key Workflows:**

### Uploading a PDF
```
Step 1: Click "Processing" in sidebar
Step 2: Click "Browse Files" or drag PDF into upload area
Step 3: Select template type (Aggregators, OPR, MPP, ADOP, ADRE, or Commercial)
Step 4: Select template type
Step 5: Click "Generate Content"
Step 6: Wait for processing (5-10 minutes)
```

**What Happens During Processing:**
- ✓ PDF uploaded to secure cloud storage
- ✓ Text extracted from all pages
- ✓ Images extracted and classified (interior, exterior, amenity, logo)
- ✓ Floor plans identified and data extracted
- ✓ Watermarks detected and removed
- ✓ SEO content generated
- ✓ Google Sheet created and populated
- ✓ ZIP file packaged with all assets

### Reviewing Content
```
After processing completes:
Step 1: Click "View Preview" button
Step 2: Review each field (meta title, description, H1, overview, etc.)
Step 3: Check character counts (ensure within limits)
Step 4: If changes needed:
        - Click "Regenerate" for specific field
        - Edit field manually
Step 5: When satisfied, click "Push to Sheets"
Step 6: Wait for QA validation (30 seconds)
Step 7: If QA passes, proceed to submit for approval
```

### Submitting for Approval
```
Step 1: Go to project detail page
Step 2: Verify all information is correct
Step 3: Click "Submit for Approval" button
Step 4: Add optional notes for marketing manager
Step 5: Click "Confirm"
Step 6: Wait for marketing approval (notification will arrive)
```

**Screenshots:** Include annotated screenshots for each major step

---

## 2. Marketing Manager Guide

**Table of Contents:**
1. Overview of Approval Process
2. Accessing the Approval Queue
3. Reviewing a Project
4. Approving Projects
5. Requesting Revisions
6. Rejecting Projects
7. Bulk Approval
8. Viewing QA Reports
9. Managing Approval Backlog

**Key Workflows:**

### Reviewing a Project
```
Step 1: Click "Approvals" in sidebar (badge shows count)
Step 2: Click on project in queue
Step 3: Review generated content:
        - Meta title (60 chars max)
        - Meta description (160 chars max)
        - URL slug
        - H1 heading
        - Overview (500-1000 words)
        - Features, amenities, location details
Step 4: Check extracted data against PDF:
        - Developer name
        - Starting price
        - Handover date
        - Payment plan
Step 5: Review images (click gallery):
        - 10 exterior images
        - 10 interior images
        - 5 amenity images
        - 3 logo images
Step 6: Check floor plans and data
Step 7: Make decision: Approve / Request Revision / Reject
```

### Requesting Revisions
```
Step 1: Click "Request Revision" button
Step 2: Add specific comments:
        - Which fields need changes
        - What's incorrect
        - What the correct information should be
Step 3: Click "Submit Revision Request"
Step 4: Project returns to content creator
Step 5: You'll be notified when resubmitted
```

### Approval Best Practices
- Review within 24 hours to meet SLA
- Be specific in revision comments
- Use "Bulk Approve" for multiple simple projects
- Check QA reports before approving
- Flag projects with missing critical info

---

## 3. Publisher Guide

**Table of Contents:**
1. Understanding the Publishing Workflow
2. Accessing the Publishing Queue
3. Downloading Assets
4. Creating Pages in CMS
5. Per-Site Checklists
6. Marking Projects as Published
7. Post-Publication QA
8. Troubleshooting Common Issues

**Key Workflows:**

### Publishing a Project
```
Step 1: Click "Publishing" in sidebar
Step 2: Select project from queue
Step 3: Download assets:
        - Google Sheet (content)
        - ZIP file (images, floor plans)
Step 4: Create page in website CMS (based on template type)
Step 5: Complete site-specific checklist:
        ☐ Page created
        ☐ Images uploaded
        ☐ SEO verified (meta tags)
        ☐ Content reviewed
Step 6: Enter published URL
Step 7: Click "Mark as Published"
Step 8: Run post-publication QA (optional but recommended)
```

### Per-Site Checklists

**OPR (Off-Plan Residences):**
- [ ] Project page created in WordPress
- [ ] Hero image set (featured image)
- [ ] Gallery uploaded (10 exterior + 10 interior)
- [ ] Floor plans uploaded
- [ ] Developer logo added
- [ ] SEO meta tags filled
- [ ] Schema markup added
- [ ] Internal links to developer page
- [ ] Published URL recorded

**MPP (main-portal.com):**
- [ ] Project page created
- [ ] Gallery uploaded
- [ ] SEO meta tags filled
- [ ] Published URL recorded

**Commercial (cre.main-portal.com):**
- [ ] Project added to commercial database
- [ ] Featured on homepage (if high priority)
- [ ] Contact form configured
- [ ] Similar projects linked

**ADOP/ADRE (Abu Dhabi sites):**
- [ ] Project page created
- [ ] Location map embedded
- [ ] Abu Dhabi-specific content verified

### Post-Publication QA
```
Step 1: Click "Run QA" on published project
Step 2: Enter published page URL
Step 3: System scrapes page and compares:
        - Meta title matches approved content
        - Meta description matches
        - H1 matches
        - Overview text matches
        - Images count correct
Step 4: Review QA report:
        - Matches: ✓ 45
        - Differences: ⚠ 2
        - Missing: ✗ 1
Step 5: Fix any issues and re-run QA
```

---

## 4. Admin Guide

**Table of Contents:**
1. User Management
2. Monitoring System Health
3. Viewing Audit Logs
4. Managing Prompts
5. Troubleshooting Failed Jobs
6. Managing Custom Fields
7. Export & Reports
8. Cost Tracking (Anthropic API)
9. Security & Access Control

**Key Responsibilities:**

### User Management
```
Add User:
Step 1: Go to Admin Dashboard → Users
Step 2: Click "Add User" (they must have @your-domain.com email)
Step 3: User signs in with Google OAuth
Step 4: Assign role: Admin or User
Step 5: User granted permissions:
        - User: Can view, create, edit own projects
        - Admin: Can delete, manage users, access audit logs

Deactivate User:
Step 1: Find user in list
Step 2: Click "Deactivate"
Step 3: User loses access immediately
Step 4: Their projects remain in system
```

### Monitoring System Health
- **Dashboard Metrics:**
  - Projects processed this week
  - Pending approvals
  - Failed jobs (requires attention)
  - Anthropic API usage & cost
  - Database size
  - Storage usage

- **Alert Notifications:**
  - Job failure rate > 10%
  - Anthropic API quota > 80%
  - Database connection pool exhausted
  - Error rate > 5%

### Troubleshooting Failed Jobs
```
Step 1: View failed jobs list
Step 2: Click on failed job
Step 3: Read error message:
        - "PDF encrypted" → Ask user to provide unencrypted PDF
        - "Anthropic quota exceeded" → Wait 1 hour or increase quota
        - "Invalid PDF structure" → PDF corrupted, ask for new file
Step 4: If recoverable, click "Retry Job"
Step 5: If not, mark as "Cancelled" and notify user
```

### Managing Prompts
```
Updating a Prompt:
Step 1: Go to Prompts page
Step 2: Find prompt (e.g., "OPR Meta Description")
Step 3: Click "Edit"
Step 4: Modify prompt text
Step 5: Add change reason (e.g., "Improved clarity")
Step 6: Click "Save" (creates new version)
Step 7: New projects use updated prompt
Step 8: Old projects can be regenerated with new prompt
```

---

## 5. Developer Guide (API Integration)

**Table of Contents:**
1. API Overview
2. Authentication
3. Uploading Files
4. Retrieving Project Data
5. Webhooks (Coming Soon)
6. Error Handling
7. Rate Limits
8. Code Examples (Python, JavaScript, cURL)
9. Testing in Sandbox

**Authentication:**
```bash
# Get OAuth token (backend integration)
POST https://api.pdp-automation.com/api/auth/google
Content-Type: application/json

{
  "token": "google_oauth_token_here"
}

# Response
{
  "access_token": "eyJhbGc...",
  "refresh_token": "refresh_token",
  "user": {...}
}

# Use token in requests
GET https://api.pdp-automation.com/api/projects
Authorization: Bearer eyJhbGc...
```

**Upload PDF via API:**
```python
import requests

# Upload PDF
files = {'file': open('brochure.pdf', 'rb')}
data = {
    'website': 'opr',
    'template_id': 'template-uuid'
}
headers = {'Authorization': 'Bearer YOUR_TOKEN'}

response = requests.post(
    'https://api.pdp-automation.com/api/upload',
    files=files,
    data=data,
    headers=headers
)

job_id = response.json()['job_id']
print(f"Job created: {job_id}")
```

**Poll Job Status:**
```python
import time

while True:
    response = requests.get(
        f'https://api.pdp-automation.com/api/jobs/{job_id}',
        headers=headers
    )

    status = response.json()['status']
    progress = response.json()['progress']

    print(f"Status: {status}, Progress: {progress}%")

    if status in ['completed', 'failed']:
        break

    time.sleep(5)

# Get result
if status == 'completed':
    result = response.json()['result']
    sheet_url = result['sheet_url']
    zip_url = result['zip_url']
    print(f"Sheet: {sheet_url}")
    print(f"Assets: {zip_url}")
```

**Retrieve Project Data:**
```javascript
// JavaScript example
const response = await fetch(
  'https://api.pdp-automation.com/api/projects/PROJECT_ID',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

const project = await response.json();

console.log('Project:', project.name);
console.log('Developer:', project.developer);
console.log('Starting Price:', project.starting_price);
console.log('Images:', project.images.length);
console.log('Floor Plans:', project.floor_plans.length);
```

**Error Handling:**
```python
try:
    response = requests.post(url, ...)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    error = response.json()
    print(f"Error: {error['error_code']}")
    print(f"Message: {error['message']}")

    if error['error_code'] == 'GEMINI_QUOTA_EXCEEDED':
        print(f"Retry after: {error['retry_after']} seconds")
        time.sleep(error['retry_after'])
        # Retry request
```

**Rate Limits:**
- Anonymous: 5 requests/hour
- Authenticated: 50 requests/hour
- Admin: Unlimited

**Webhooks (Future):**
```
Webhook Events:
- project.created
- project.completed
- project.approved
- project.published

Webhook Payload:
POST https://your-app.com/webhook
{
  "event": "project.completed",
  "project_id": "uuid",
  "timestamp": "2026-01-14T10:30:00Z",
  "data": {...}
}
```

---

## Document Structure Standards

Each user guide must include:
1. **Introduction** - Who is this guide for?
2. **Getting Started** - First-time setup
3. **Step-by-Step Workflows** - Numbered, clear instructions
4. **Screenshots** - Annotated images showing each step (use ASCII art as placeholder)
5. **Common Issues** - Troubleshooting section
6. **Best Practices** - Tips for efficient use
7. **FAQs** - Frequently asked questions

**Tone:**
- Friendly and approachable
- Assume minimal technical knowledge (except Developer Guide)
- Use "you" language
- Include real examples
- Avoid jargon (or explain when necessary)

---

## Quality Checklist

- ✅ All 5 files created
- ✅ Each guide tailored to user role
- ✅ Step-by-step workflows clear
- ✅ Screenshots/wireframes included
- ✅ Troubleshooting sections
- ✅ Code examples (Developer Guide)
- ✅ Friendly, approachable tone
- ✅ Real-world examples

Begin with `CONTENT_CREATOR_GUIDE.md`.