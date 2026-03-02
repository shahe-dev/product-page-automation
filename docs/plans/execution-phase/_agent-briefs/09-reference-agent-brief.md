# Agent Briefing: Reference Documentation Agent

**Agent ID:** reference-docs-agent
**Batch:** 4 (User-Facing)
**Priority:** P3 - Reference Material
**Est. Context Usage:** 32,000 tokens

---

## Your Mission

Create **4 reference documentation files** providing glossary, changelog, troubleshooting guide, and FAQ.

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/09-reference/`

---

## Files You Must Create

1. `GLOSSARY.md` (300-350 lines) - Terms, acronyms, and definitions
2. `CHANGELOG.md` (250-300 lines) - Version history and release notes
3. `TROUBLESHOOTING.md` (400-500 lines) - Common issues and solutions
4. `FAQ.md` (350-400 lines) - Frequently asked questions

**Total Output:** ~1,300-1,550 lines across 4 files

---

## 1. Glossary

**Purpose:** Define all technical terms, acronyms, and domain-specific language used in PDP Automation v.3.

**Categories:**
- General Terms
- Technical Terms
- Real Estate Terms
- Google Cloud Terms
- Workflow States
- User Roles

**Format:**
```markdown
## [Term]

**Definition:** Brief explanation

**Usage:** How it's used in the system

**Example:** Concrete example

**See Also:** Related terms
```

**Key Terms to Define:**

### General Terms
- **PDP** - Property Detail Page
- **Brochure** - PDF marketing material for real estate projects
- **Extraction** - Process of pulling data from PDF
- **Classification** - Categorizing images (interior, exterior, etc.)
- **Generation** - Creating SEO content from extracted data

### Technical Terms
- **API** - Application Programming Interface
- **OAuth** - Open Authorization protocol
- **JWT** - JSON Web Token (authentication)
- **REST** - Representational State Transfer
- **Async** - Asynchronous (non-blocking operations)
- **JSONB** - JSON Binary (PostgreSQL data type)
- **GCS** - Google Cloud Storage
- **Cloud Run** - Serverless compute platform
- **Neon PostgreSQL** - Serverless PostgreSQL database

### Real Estate Terms
- **Developer** - Company building the project (e.g., Emaar)
- **Emirate** - Administrative division in UAE (e.g., Dubai, Abu Dhabi)
- **Off-Plan** - Property sold before construction completes
- **Handover Date** - When property is delivered to buyer
- **Payment Plan** - Installment schedule (e.g., 60/40, 80/20)
- **Starting Price** - Minimum price for units in project
- **Unit Type** - Apartment configuration (Studio, 1BR, 2BR, etc.)
- **Amenity** - Facility provided (Pool, Gym, etc.)

### Workflow States
- **DRAFT** - Content creator working on project
- **PENDING_APPROVAL** - Submitted to marketing for review
- **REVISION_REQUESTED** - Marketing requested changes
- **APPROVED** - Ready for publishing
- **PUBLISHING** - Publisher creating page
- **PUBLISHED** - Live on website
- **QA_VERIFIED** - Post-publication QA passed
- **COMPLETE** - Workflow finished

### User Roles
- **Content Creator** - Uploads PDFs, reviews content
- **Marketing Manager** - Approves/rejects content
- **Publisher** - Creates pages, marks as published
- **Admin** - Manages system, users, settings
- **Developer** - Integrates with API

### Modules
- **Project Database** - Central repository (Module 0)
- **Material Preparation** - PDF → Images pipeline (Module 4)
- **Content Generation** - LLM content creation (Module 5)
- **Approval Workflow** - Marketing review (Module 1)
- **Publishing Workflow** - Page creation tracking (Module 1)
- **QA Module** - Quality assurance (Module 3)
- **Prompt Library** - Version-controlled prompts (Module 5)
- **Notifications** - Alert system (Module 2)

---

## 2. Changelog

**Purpose:** Track all version releases, features added, bugs fixed, and breaking changes.

**Format:**
```markdown
## [Version] - YYYY-MM-DD

### Added
- New features

### Changed
- Improvements to existing features

### Fixed
- Bug fixes

### Deprecated
- Features being phased out

### Removed
- Removed features

### Security
- Security improvements
```

**Version History:**

### v0.3.0 - 2026-01-20 (Planned)
**Added:**
- Publishing workflow with per-site checklists
- Post-publication QA comparison
- Manager dashboard with metrics
- Batch approval for multiple projects

**Changed:**
- Improved image optimization (faster processing)
- Enhanced QA validation (more accurate)
- Updated Anthropic prompts for better content

**Fixed:**
- Fixed toast notification delay (16min → 5s)
- Fixed file upload size limit enforcement
- Fixed database connection pool exhaustion

### v0.2.0 - 2026-01-14 (Current)
**Added:**
- QA module with 3 checkpoints
- Content preview before Sheets push
- Prompt library with version control
- Workflow board (Kanban)
- Audit log for all actions
- Custom fields support

**Changed:**
- Migrated from in-memory to PostgreSQL database
- Improved error handling
- Added rate limiting per user role

**Fixed:**
- PDF extraction for encrypted files (now shows error)
- Image classification accuracy improved
- Floor plan deduplication working correctly

### v0.1.0 - 2026-01-07 (Initial Release)
**Added:**
- PDF upload and processing
- Text extraction via Claude Vision
- Image classification (interior, exterior, amenity, logo)
- Floor plan extraction with data
- Content generation for 6 template types (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
- Google Sheets API integration
- Google OAuth authentication
- Basic approval workflow
- Real-time progress tracking

---

## 3. Troubleshooting

**Purpose:** Help users diagnose and fix common issues.

**Format:**
```markdown
### [Issue Title]

**Symptoms:**
- Observable behavior
- Error messages

**Cause:**
- Why this happens

**Solution:**
- Step-by-step fix

**Prevention:**
- How to avoid in future
```

**Common Issues:**

### 1. PDF Upload Fails with "Invalid File Type"
**Symptoms:**
- Upload button shows error
- Message: "Invalid file type. Only PDF files allowed."

**Cause:**
- File is not a PDF (wrong extension or MIME type)
- File renamed but is actually a different format

**Solution:**
1. Verify file is actually a PDF (not just renamed .docx or .jpg)
2. Try opening file in Adobe Reader to confirm it's valid
3. If file won't open, request new PDF from source

**Prevention:**
- Always request PDF format from designers
- Don't rename files to change extension

### 2. Processing Stuck at "Extracting Images"
**Symptoms:**
- Progress bar stuck at 30%
- "Extracting images" step showing for >10 minutes

**Causes:**
- PDF has 500+ images (exceeds limit)
- PDF pages are very high resolution (e.g., 4K scans)
- Backend server is under heavy load

**Solution:**
1. Wait 15 minutes (some PDFs take time)
2. If still stuck, cancel job and retry
3. If fails again, contact admin
4. Admin can check logs for specific error

**Prevention:**
- Use optimized PDFs (not raw scans)
- Compress PDFs before upload if >30MB

### 3. Generated Content is Inaccurate
**Symptoms:**
- Wrong developer name
- Incorrect starting price
- Missing amenities

**Cause:**
- PDF text is unclear or formatted oddly
- OCR misread numbers or text
- LLM hallucinated information

**Solution:**
1. Review content preview carefully
2. Regenerate specific fields if needed
3. Manually edit incorrect fields
4. Submit for QA validation
5. If QA fails, fix and re-validate

**Prevention:**
- Use high-quality PDFs with clear text
- Review content before submitting for approval

### 4. Can't Login - "Domain Not Allowed"
**Symptoms:**
- Google OAuth shows error
- Message: "Email domain not allowed"

**Cause:**
- Email is not @your-domain.com
- System restricted to company domain

**Solution:**
1. Verify you're using @your-domain.com email
2. If you need access with different domain, contact admin
3. Admin can whitelist additional domains (requires config change)

**Prevention:**
- Always use company email for login

### 5. Approval Queue is Empty But Notifications Show Pending
**Symptoms:**
- Notification bell shows "3 pending approvals"
- Approval queue page shows no items

**Cause:**
- Notifications not marked as read
- Cache issue

**Solution:**
1. Refresh page (Ctrl+R / Cmd+R)
2. Clear browser cache
3. Mark all notifications as read
4. If persists, contact admin to check database

### 6. Images Not Categorized Correctly
**Symptoms:**
- Interior images classified as exterior
- Logo images missing

**Cause:**
- Claude Vision misclassification (rare)
- Image quality too low
- Watermark covering entire image

**Solution:**
1. Review image gallery in project detail
2. Manually reclassify images (if feature available)
3. If critical images missing, ask admin to reprocess with different prompt

**Prevention:**
- Use high-quality images in PDFs
- Avoid heavy watermarks

### 7. Google Sheet Not Populating
**Symptoms:**
- Job completes but Sheet is empty
- Sheet URL works but cells are blank

**Cause:**
- Template field mapping incorrect
- Sheets API rate limit hit
- Permission issue with service account

**Solution:**
1. Check Sheet URL (is it correct template?)
2. Verify template field mapping in Admin → Templates
3. Contact admin to check Sheets API quota
4. Admin can manually re-push content

### 8. QA Validation Always Fails
**Symptoms:**
- QA checkpoint fails every time
- Even correct content shows as "failed"

**Cause:**
- QA validation rules too strict
- Expected format doesn't match generated format

**Solution:**
1. Review QA comparison details (what fields differ?)
2. If minor formatting differences, click "Override QA"
3. Contact admin to adjust QA validation rules

---

## 4. FAQ

**Purpose:** Answer the most frequently asked questions.

**Categories:**
- General Questions
- Processing Questions
- Content Questions
- Workflow Questions
- Technical Questions
- Billing Questions

**Format:**
```markdown
### Q: Question here?

**A:** Detailed answer with examples.
```

**Sample FAQs:**

### General Questions

**Q: What is PDP Automation v.3?**
A: PDP Automation v.3 is a system that automatically transforms real estate PDF brochures into SEO-optimized content and processed images for property detail pages. It uses AI (Anthropic API with Claude Sonnet 4.5) to extract data, classify images, and generate content.

**Q: Who can use the system?**
A: Only users with @your-domain.com email addresses can access the system. There are 4 user roles: Content Creators, Marketing Managers, Publishers, and Admins.

**Q: How long does processing take?**
A: Average processing time is 5-10 minutes for a typical brochure (25 pages, 30 images). Large brochures (50+ pages, 100+ images) can take up to 20 minutes.

**Q: What file formats are supported?**
A: Only PDF files. Maximum file size is 50MB. PDFs must not be encrypted or password-protected.

**Q: Is my data secure?**
A: Yes. All files are stored in Google Cloud Storage with encryption at rest. Access is restricted via Google OAuth. All actions are logged for audit.

### Processing Questions

**Q: Why did my job fail?**
A: Common reasons:
- PDF is encrypted (solution: provide unencrypted version)
- File corrupted (solution: re-export from source)
- File too large >50MB (solution: compress or split)
- Anthropic API quota exceeded (solution: wait 1 hour or contact admin)

**Q: Can I cancel a job in progress?**
A: Yes. Click "Cancel" on the processing page. Note: Partial results may be saved.

**Q: Can I process the same PDF multiple times?**
A: Yes, but it creates a new project each time. Useful if you need to regenerate content with updated prompts.

**Q: What happens to images in the PDF?**
A: Images are:
1. Extracted from PDF
2. Classified by type (interior, exterior, amenity, logo)
3. Watermarks detected and removed
4. Optimized (resized, compressed, converted to WebP + JPG)
5. Packaged in ZIP file with organized folders

### Content Questions

**Q: Can I edit generated content?**
A: Yes. In the Content Preview page, you can:
- Edit any field manually
- Regenerate specific fields
- Add/remove custom fields

**Q: How accurate is the AI?**
A: Claude Vision has 90%+ accuracy on text extraction. Content generation quality depends on prompt quality. Always review generated content before submitting.

**Q: Can I use custom prompts?**
A: Admins can create/edit prompts in the Prompt Library. Regular users use system prompts. Contact admin if you need a custom prompt.

**Q: What character limits apply?**
A: Common limits:
- Meta title: 60 characters
- Meta description: 160 characters
- H1: 70 characters
- Overview: 500-1000 words
- URL slug: 50 characters

### Workflow Questions

**Q: How long does approval take?**
A: SLA is 24 hours. Most approvals happen within 4-6 hours during business hours.

**Q: What if I need urgent approval?**
A: Contact the marketing manager directly via Slack/email and provide project link.

**Q: Can I skip the approval process?**
A: No. All projects require marketing approval to ensure quality and brand consistency.

**Q: What happens if my project is rejected?**
A: You receive a notification with feedback. Fix the issues and resubmit. The approval request history is preserved.

### Technical Questions

**Q: Can I access the API?**
A: Yes. Web developers can integrate with the REST API. See Developer Guide for details.

**Q: Are webhooks available?**
A: Coming soon in v0.4.0. You'll be able to subscribe to events like "project.completed", "project.approved", etc.

**Q: What happens if the system goes down?**
A: All processing jobs are queued in Cloud Tasks and will automatically resume when the system comes back online. No data is lost.

**Q: How do I report a bug?**
A: Contact your admin or email support@pdp-automation.com with:
- What you were doing
- What happened (include error message)
- Screenshots if possible

### Billing Questions

**Q: How much does it cost per brochure?**
A: Approximately $0.56 per brochure (Anthropic API costs). This includes all processing steps.

**Q: Can costs be reduced?**
A: Yes. The system uses response caching which reduces costs by 70-90% for repeated content patterns.

**Q: Who pays for the Anthropic API usage?**
A: Costs are billed to the company's Anthropic account (covered by existing API credits). Admins can view cost reports in the Admin Dashboard.

---

## Document Structure Standards

- **Glossary:** Alphabetical order within each category
- **Changelog:** Reverse chronological (newest first)
- **Troubleshooting:** Organized by severity (critical issues first)
- **FAQ:** Organized by category, most common questions first

**Tone:**
- Clear and concise
- Avoid technical jargon (or explain when necessary)
- Use real examples
- Link to related documentation

---

## Quality Checklist

- ✅ All 4 files created
- ✅ Glossary comprehensive (50+ terms)
- ✅ Changelog follows semantic versioning
- ✅ Troubleshooting covers top 10 issues
- ✅ FAQ answers common questions (30+)
- ✅ Clear, concise language
- ✅ Cross-references to other docs
- ✅ Real examples provided

Begin with `GLOSSARY.md`.