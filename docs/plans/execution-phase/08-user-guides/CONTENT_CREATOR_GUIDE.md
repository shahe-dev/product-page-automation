# Content Creator Guide

**PDP Automation v.3**
*Your complete guide to creating and managing property content*

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Logging In](#logging-in)
4. [Uploading a PDF Brochure](#uploading-a-pdf-brochure)
5. [Monitoring Processing Progress](#monitoring-processing-progress)
6. [Reviewing Generated Content](#reviewing-generated-content)
7. [Editing Project Information](#editing-project-information)
8. [Submitting for Approval](#submitting-for-approval)
9. [Handling Revision Requests](#handling-revision-requests)
10. [Viewing Your Projects](#viewing-your-projects)
11. [Common Issues & Solutions](#common-issues--solutions)
12. [Best Practices](#best-practices)
13. [FAQs](#faqs)

---

## Introduction

### Who Is This Guide For?

This guide is for **Content Creators** who are responsible for:
- Uploading property PDF brochures
- Reviewing AI-generated content
- Ensuring content accuracy and quality
- Submitting projects for marketing approval

You don't need any technical expertise to use this system. If you can use email and upload files, you're ready to go!

### What You'll Learn

By the end of this guide, you'll be able to:
- Upload PDF brochures and initiate processing
- Monitor the AI content generation process
- Review and edit generated content
- Submit projects for approval
- Handle revision requests from marketing managers

---

## Getting Started

### System Requirements

- **Browser:** Chrome, Firefox, Safari, or Edge (latest version)
- **Internet Connection:** Stable broadband connection
- **Email:** @your-domain.com Google Workspace account
- **Files:** PDF brochures (recommended: under 50MB)

### First-Time Setup

Before you can start creating content, you'll need:

1. **Access to the system** - Your admin will grant you access
2. **Google account** - Your @your-domain.com email must be whitelisted
3. **Basic training** - Review this guide and watch the onboarding video

That's it! No software installation required.

---

## Logging In

### Step 1: Navigate to the Application

Open your browser and go to:
```
https://pdp-automation.your-domain.com
```

### Step 2: Click "Sign In with Google"

You'll see the login screen:

```
╔════════════════════════════════════════════╗
║                                            ║
║        PDP AUTOMATION v.3                  ║
║                                            ║
║   ┌──────────────────────────────────┐    ║
║   │  🔐 Sign in with Google          │    ║
║   └──────────────────────────────────┘    ║
║                                            ║
║   Authorized users only                    ║
║   Requires @your-domain.com email                   ║
║                                            ║
╚════════════════════════════════════════════╝
```

### Step 3: Authenticate with Google

1. Click the "Sign in with Google" button
2. Select your @your-domain.com Google account
3. Allow the requested permissions
4. You'll be redirected to the dashboard

**Note:** If you see an error message, contact your admin to verify your account is whitelisted.

---

## Uploading a PDF Brochure

This is where the magic begins! Follow these steps to upload a property brochure.

### Step 1: Navigate to Processing Page

Click **"Processing"** in the left sidebar:

```
╔══════════════╦══════════════════════════════╗
║              ║                              ║
║  Dashboard   ║   Welcome, Sarah!            ║
║  Processing  ║                              ║
║  Projects    ║   Ready to create content?   ║
║  Approvals   ║                              ║
║              ║                              ║
╚══════════════╩══════════════════════════════╝
```

### Step 2: Choose Your Upload Method

You have two options:

**Option A: Drag and Drop**
```
╔════════════════════════════════════════════╗
║                                            ║
║   📄 Drag PDF here or click to browse     ║
║                                            ║
║      Supported: PDF files up to 50MB      ║
║                                            ║
╚════════════════════════════════════════════╝
```

**Option B: Browse Files**
1. Click "Browse Files" button
2. Navigate to your PDF in the file dialog
3. Select the file and click "Open"

### Step 3: Select Template

Choose which template this project is for:

```
┌────────────────────────────────────────┐
│ Select Template:                       │
│                                        │
│  ( ) Aggregators (24+ domains)        │
│  ( ) OPR (opr.ae)                     │
│  ( ) MPP (main-portal.com)    │
│  ( ) ADOP (abudhabioffplan.ae)        │
│  ( ) ADRE (secondary-market-portal.com)      │
│  ( ) Commercial (commercial.main-portal.com)    │
└────────────────────────────────────────┘
```

**Template Descriptions:**
- **Aggregators:** Content for 24+ third-party aggregator domains
- **OPR:** Off-Plan Residences website (opr.ae)
- **MPP:** the company (main-portal.com)
- **ADOP:** Abu Dhabi Off Plan website (abudhabioffplan.ae)
- **ADRE:** Abu Dhabi Real Estate website (secondary-market-portal.com)
- **Commercial:** Commercial properties (cre.main-portal.com)

### Step 4: Select Content Variant

Choose the appropriate content variant:

```
┌────────────────────────────────────────┐
│ Select Content Variant:                │
│                                        │
│  ( ) Standard                          │
│  ( ) Luxury                            │
└────────────────────────────────────────┘
```

**Content Variant Differences:**
- **Standard:** Standard tone and style for most properties
- **Luxury:** Premium tone for high-end villas and luxury developments

### Step 5: Click "Generate Content"

Review your selections:
```
╔════════════════════════════════════════════╗
║ File: marina_heights_brochure.pdf         ║
║ Size: 12.3 MB                              ║
║ Template: OPR (opr.ae)                     ║
║ Content Variant: Standard                  ║
║                                            ║
║  [Cancel]  [Generate Content →]            ║
╚════════════════════════════════════════════╝
```

Click **"Generate Content"** to start processing.

### Step 6: Processing Begins

You'll see a confirmation message:
```
✓ Upload successful!
  Processing started. This usually takes 5-10 minutes.
  You'll receive a notification when complete.
```

---

## Monitoring Processing Progress

### Understanding the Processing Pipeline

When you upload a PDF, the system performs these steps automatically:

```
Step 1: Upload PDF ────────────────────── ✓ Complete (10 seconds)
         │
Step 2: Extract Text ──────────────────── ⏳ Processing...
         │
Step 3: Extract Images ────────────────── ⏱️ Pending
         │
Step 4: Classify Images ───────────────── ⏱️ Pending
         │
Step 5: Detect Floor Plans ────────────── ⏱️ Pending
         │
Step 6: Remove Watermarks ─────────────── ⏱️ Pending
         │
Step 7: Generate SEO Content ──────────── ⏱️ Pending
         │
Step 8: Create Google Sheet ───────────── ⏱️ Pending
         │
Step 9: Package ZIP File ──────────────── ⏱️ Pending
         │
        ✓ COMPLETE
```

### Viewing Real-Time Progress

Navigate to **Processing > Active Jobs** to see live updates:

```
╔════════════════════════════════════════════════════════╗
║ Active Jobs                                            ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ marina_heights_brochure.pdf                           ║
║ ████████████░░░░░░░░░░ 60% - Extracting images       ║
║ Started: 2 minutes ago                                 ║
║ Estimated completion: 3 minutes                        ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

### What Happens During Each Step?

**Step 1: Upload PDF (10 seconds)**
- Your PDF is securely uploaded to cloud storage
- File is scanned for corruption or encryption

**Step 2: Extract Text (30 seconds)**
- OCR technology reads all text from PDF pages
- Text is cleaned and structured

**Step 3: Extract Images (1-2 minutes)**
- All images are extracted at high resolution
- Images are saved in PNG format

**Step 4: Classify Images (2-3 minutes)**
- AI identifies image types:
  - 10 exterior images (building facades)
  - 10 interior images (apartments, rooms)
  - 5 amenity images (pool, gym, etc.)
  - 3 logo images (developer logos)

**Step 5: Detect Floor Plans (1 minute)**
- Floor plan images are identified
- Bedroom/bathroom counts extracted
- Square footage data captured

**Step 6: Remove Watermarks (1-2 minutes)**
- AI detects and removes watermarks
- Clean images saved for publishing

**Step 7: Generate SEO Content (2-3 minutes)**
- AI generates optimized content:
  - Meta title (60 characters)
  - Meta description (160 characters)
  - H1 heading
  - Overview (500-1000 words)
  - Features and amenities
  - Location description

**Step 8: Create Google Sheet (30 seconds)**
- Structured data exported to Google Sheets
- Sheet shared with team

**Step 9: Package ZIP File (30 seconds)**
- All images and floor plans packaged
- ZIP file ready for download

### Notifications

You'll receive notifications when:
- ✓ Processing completes successfully
- ✗ Processing fails (with error details)
- ⚠ Warning: Quality issues detected

Check the notification bell icon in the top right:
```
🔔 (3)
```

---

## Reviewing Generated Content

After processing completes, it's time to review the AI-generated content.

### Step 1: Access Content Preview

From the notification or your Projects page, click **"View Preview"**:

```
╔════════════════════════════════════════════════════════╗
║ Project: Marina Heights                               ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Status: ✓ Processing Complete                         ║
║                                                        ║
║ [View Preview]  [Download Assets]                     ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

### Step 2: Review SEO Fields

Check each field carefully:

#### Meta Title
```
┌─────────────────────────────────────────────────────┐
│ Meta Title                                 48/60    │
├─────────────────────────────────────────────────────┤
│ Marina Heights | Luxury Apartments in Dubai Marina  │
│                                                     │
│ ✓ Character count OK                                │
│ [Regenerate]  [Edit]                                │
└─────────────────────────────────────────────────────┘
```

**What to Check:**
- Is the project name correct?
- Does it include key location?
- Character count under 60?

#### Meta Description
```
┌─────────────────────────────────────────────────────┐
│ Meta Description                          152/160   │
├─────────────────────────────────────────────────────┤
│ Discover luxury living at Marina Heights with      │
│ stunning 1, 2 & 3 bedroom apartments. Starting     │
│ from AED 1.2M. Prime Dubai Marina location.        │
│                                                     │
│ ✓ Character count OK                                │
│ [Regenerate]  [Edit]                                │
└─────────────────────────────────────────────────────┘
```

**What to Check:**
- Compelling and accurate?
- Includes starting price?
- Character count under 160?

#### H1 Heading
```
┌─────────────────────────────────────────────────────┐
│ H1 Heading                                          │
├─────────────────────────────────────────────────────┤
│ Marina Heights - Luxury Waterfront Living           │
│                                                     │
│ [Regenerate]  [Edit]                                │
└─────────────────────────────────────────────────────┘
```

#### Overview Text
```
┌─────────────────────────────────────────────────────┐
│ Overview                                  847 words │
├─────────────────────────────────────────────────────┤
│ Marina Heights represents the pinnacle of luxury   │
│ waterfront living in Dubai Marina. This stunning   │
│ residential development offers sophisticated 1, 2  │
│ and 3 bedroom apartments with breathtaking views   │
│ of the Arabian Gulf...                              │
│                                                     │
│ [Read Full] [Regenerate] [Edit]                     │
└─────────────────────────────────────────────────────┘
```

**What to Check:**
- Word count 500-1000 words?
- Accurate project details?
- Professional and engaging tone?

### Step 3: Review Extracted Data

Scroll down to verify factual data:

```
╔════════════════════════════════════════════╗
║ Project Details                            ║
╠════════════════════════════════════════════╣
║ Developer: Emaar Properties                ║
║ Starting Price: AED 1,200,000              ║
║ Handover: Q4 2026                          ║
║ Payment Plan: 60/40                        ║
║ Unit Types: 1, 2, 3 BR                     ║
║ Total Units: 250                           ║
╚════════════════════════════════════════════╝
```

**Compare against the original PDF** - Are all details correct?

### Step 4: Review Images

Click **"View Gallery"** to see extracted images:

```
╔════════════════════════════════════════════╗
║ Image Gallery                              ║
╠════════════════════════════════════════════╣
║ Exterior (10)                              ║
║ [img] [img] [img] [img] [img]             ║
║ [img] [img] [img] [img] [img]             ║
║                                            ║
║ Interior (10)                              ║
║ [img] [img] [img] [img] [img]             ║
║ [img] [img] [img] [img] [img]             ║
║                                            ║
║ Amenities (5)                              ║
║ [img] [img] [img] [img] [img]             ║
║                                            ║
║ Logos (3)                                  ║
║ [img] [img] [img]                          ║
╚════════════════════════════════════════════╝
```

**What to Check:**
- Are images classified correctly?
- All images clear and high quality?
- Watermarks removed successfully?

### Step 5: Review Floor Plans

```
╔════════════════════════════════════════════╗
║ Floor Plans                                ║
╠════════════════════════════════════════════╣
║ 1 Bedroom | 650 sqft | 1 Bath             ║
║ [View Floor Plan]                          ║
║                                            ║
║ 2 Bedroom | 1,100 sqft | 2 Bath           ║
║ [View Floor Plan]                          ║
║                                            ║
║ 3 Bedroom | 1,650 sqft | 3 Bath           ║
║ [View Floor Plan]                          ║
╚════════════════════════════════════════════╝
```

**What to Check:**
- Bedroom/bathroom counts correct?
- Square footage accurate?

---

## Editing Project Information

If you spot any errors or want to make changes:

### Regenerating Specific Fields

For SEO content fields, you can regenerate them:

**Step 1:** Click **"Regenerate"** next to the field
**Step 2:** Wait 10-15 seconds for new content
**Step 3:** Review the new version
**Step 4:** Keep it or regenerate again

```
Regenerating Meta Description...
⏳ Please wait (this takes ~10 seconds)

New version generated! Compare:

Old: "Discover luxury living at Marina Heights..."
New: "Experience waterfront luxury at Marina Heights..."

[Keep New] [Revert to Old] [Regenerate Again]
```

### Manual Editing

For precise control, edit fields manually:

**Step 1:** Click **"Edit"** next to any field
**Step 2:** Type your changes
**Step 3:** Character counter updates in real-time
**Step 4:** Click **"Save"**

```
┌─────────────────────────────────────────────────────┐
│ Edit Meta Title                           55/60     │
├─────────────────────────────────────────────────────┤
│ [Marina Heights | Luxury Dubai Marina Apartments]  │
│                                                     │
│ ⚠ Warning: Stay under 60 characters                │
│                                                     │
│ [Cancel]  [Save Changes]                            │
└─────────────────────────────────────────────────────┘
```

### Editing Structured Data

For developer name, prices, dates, etc.:

**Step 1:** Click **"Edit Details"**
**Step 2:** Update fields in the form
**Step 3:** Click **"Save"**

```
╔════════════════════════════════════════════╗
║ Edit Project Details                       ║
╠════════════════════════════════════════════╣
║ Developer: [Emaar Properties            ]  ║
║ Starting Price: [1200000                ]  ║
║ Currency: [AED ▼]                          ║
║ Handover: [Q4 2026                      ]  ║
║ Payment Plan: [60/40                    ]  ║
║                                            ║
║ [Cancel]  [Save Changes]                   ║
╚════════════════════════════════════════════╝
```

---

## Submitting for Approval

Once you're satisfied with the content, submit it for marketing approval.

### Step 1: Run QA Validation

Before submitting, push content to Google Sheets and run QA:

```
╔════════════════════════════════════════════╗
║ Ready to Submit?                           ║
╠════════════════════════════════════════════╣
║ ✓ All fields reviewed                      ║
║ ✓ Images verified                          ║
║ ✓ Data checked                             ║
║                                            ║
║ [Push to Sheets] → [Run QA] → [Submit]    ║
╚════════════════════════════════════════════╝
```

**Step 1:** Click **"Push to Sheets"**
- Content exported to Google Sheet
- Takes ~10 seconds

**Step 2:** Click **"Run QA"**
- System validates content quality
- Checks character limits
- Verifies required fields
- Takes ~30 seconds

### Step 2: Review QA Results

```
╔════════════════════════════════════════════╗
║ QA Validation Results                      ║
╠════════════════════════════════════════════╣
║ ✓ Meta title: 48/60 characters             ║
║ ✓ Meta description: 152/160 characters     ║
║ ✓ H1 heading: Present                      ║
║ ✓ Overview: 847 words (target: 500-1000)   ║
║ ✓ Developer name: Present                  ║
║ ✓ Starting price: Present                  ║
║ ✓ Images: 28 total                         ║
║ ✓ Floor plans: 3 types                     ║
║                                            ║
║ Overall: PASS ✓                            ║
╚════════════════════════════════════════════╝
```

**If QA Fails:**
```
╔════════════════════════════════════════════╗
║ QA Validation Results                      ║
╠════════════════════════════════════════════╣
║ ✗ Meta description: 175/160 characters     ║
║   → Too long, please shorten               ║
║                                            ║
║ ⚠ Overview: 350 words (target: 500-1000)   ║
║   → Consider adding more detail            ║
║                                            ║
║ Overall: FAIL ✗                            ║
║                                            ║
║ [Fix Issues] [Submit Anyway]               ║
╚════════════════════════════════════════════╝
```

Fix the issues and run QA again.

### Step 3: Submit for Approval

Once QA passes:

**Step 1:** Click **"Submit for Approval"**

**Step 2:** Add notes for marketing manager (optional):
```
┌─────────────────────────────────────────────────────┐
│ Notes for Marketing Manager (optional)              │
├─────────────────────────────────────────────────────┤
│ [PDF had some unclear pricing details. I used      │
│  the starting price from page 3. Please verify     │
│  with sales team if needed.                        ]│
│                                                     │
│                                                     │
│ [Cancel]  [Submit for Approval]                     │
└─────────────────────────────────────────────────────┘
```

**Step 3:** Click **"Submit for Approval"**

**Step 4:** Confirmation message appears:
```
✓ Submitted for approval!
  Marketing manager will review within 24 hours.
  You'll receive a notification when approved or if revisions are needed.
```

---

## Handling Revision Requests

If the marketing manager requests revisions, you'll receive a notification.

### Step 1: Review Revision Request

Click the notification to see details:

```
╔════════════════════════════════════════════════════════╗
║ Revision Requested: Marina Heights                    ║
╠════════════════════════════════════════════════════════╣
║ From: Jessica Adams (Marketing Manager)               ║
║ Date: Jan 14, 2026 at 3:45 PM                         ║
║                                                        ║
║ Comments:                                              ║
║ "Great work overall! Please make these changes:       ║
║                                                        ║
║  1. Update starting price to AED 1.35M (not 1.2M)     ║
║  2. Handover date should be Q1 2027 (delayed)         ║
║  3. Meta description is too generic - add more        ║
║     details about waterfront location                 ║
║                                                        ║
║ Please resubmit when updated. Thanks!"                ║
║                                                        ║
║ [View Project] [Start Revisions]                      ║
╚════════════════════════════════════════════════════════╝
```

### Step 2: Make Requested Changes

Navigate to the project and make the updates:

1. Update starting price: AED 1,350,000
2. Update handover: Q1 2027
3. Edit meta description with more location details

### Step 3: Resubmit

After making changes:

**Step 1:** Click **"Push to Sheets"** (update the sheet)
**Step 2:** Click **"Run QA"** (validate again)
**Step 3:** Click **"Resubmit for Approval"**

Add a response note:
```
┌─────────────────────────────────────────────────────┐
│ Response to Revision Request                        │
├─────────────────────────────────────────────────────┤
│ [All requested changes made:                        │
│  ✓ Starting price updated to AED 1.35M             │
│  ✓ Handover changed to Q1 2027                     │
│  ✓ Meta description enhanced with waterfront       │
│    details                                          ]│
│                                                     │
│ [Resubmit for Approval]                             │
└─────────────────────────────────────────────────────┘
```

The project returns to the marketing manager's approval queue.

---

## Viewing Your Projects

### Projects Dashboard

Access all your projects from **Projects** in the sidebar:

```
╔════════════════════════════════════════════════════════╗
║ My Projects                               [+ New]     ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Filter: [All ▼] [OPR ▼] [Status ▼]      🔍 Search     ║
║                                                        ║
║ ┌──────────────────────────────────────────────────┐ ║
║ │ Marina Heights                        In Approval │ ║
║ │ Dubai Marina | OPR | Submitted Jan 14            │ ║
║ │ [View] [Edit]                                     │ ║
║ └──────────────────────────────────────────────────┘ ║
║                                                        ║
║ ┌──────────────────────────────────────────────────┐ ║
║ │ Palm Gardens                          Processing  │ ║
║ │ ADRE | Uploaded Jan 15                            │ ║
║ │ ████████░░░░░░ 40%                                │ ║
║ └──────────────────────────────────────────────────┘ ║
║                                                        ║
║ ┌──────────────────────────────────────────────────┐ ║
║ │ Downtown Views                        Published   │ ║
║ │ Downtown Dubai | OPR | Published Jan 10           │ ║
║ │ [View] [Google Sheet] [Assets]                    │ ║
║ └──────────────────────────────────────────────────┘ ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

### Project Status Indicators

- **Processing** - AI is generating content
- **Review** - Ready for your review
- **In Approval** - Submitted to marketing
- **Revision Requested** - Needs updates
- **Approved** - Ready for publishing
- **Published** - Live on website

### Filtering and Searching

Use filters to find projects quickly:
- **Template:** Aggregators, OPR, MPP, ADOP, ADRE, Commercial
- **Status:** Processing, In Approval, Approved, etc.
- **Date Range:** Last 7 days, Last 30 days, Custom
- **Search:** Search by project name or developer

---

## Common Issues & Solutions

### Issue 1: Upload Failed

**Error:** "Upload failed: File too large"

**Solution:**
- PDF files must be under 50MB
- Try compressing your PDF using Adobe Acrobat or online tools
- If still too large, contact your admin

---

**Error:** "Upload failed: Invalid file type"

**Solution:**
- Only PDF files are supported
- If you have Word/PowerPoint files, convert to PDF first

---

### Issue 2: Processing Stuck

**Symptom:** Progress bar stuck at same percentage for 10+ minutes

**Solution:**
1. Refresh the page (processing continues in background)
2. If still stuck after refresh, click "Cancel Processing"
3. Re-upload the PDF
4. If problem persists, contact support

---

### Issue 3: Poor Quality Images

**Symptom:** Extracted images are blurry or low resolution

**Cause:** The original PDF has low-resolution images

**Solution:**
- Request higher quality PDF from developer
- Images can't be better quality than source PDF

---

### Issue 4: Incorrect Data Extraction

**Symptom:** Starting price, handover date, or other details are wrong

**Cause:** PDF text is unclear or formatted unusually

**Solution:**
1. Edit the incorrect fields manually
2. Add a note when submitting: "PDF unclear, verified with sales team"
3. For future PDFs from same developer, note the issue pattern

---

### Issue 5: Missing Floor Plans

**Symptom:** No floor plans detected

**Cause:** Floor plans not clearly labeled or too small in PDF

**Solution:**
1. Check PDF - are floor plans visible?
2. If yes, manually upload floor plans:
   - Click "Add Floor Plan"
   - Upload image
   - Enter bedroom/bathroom/sqft data
3. If no, request floor plans from developer

---

### Issue 6: QA Validation Fails

**Error:** "Meta description exceeds 160 characters"

**Solution:**
1. Click "Edit" on meta description
2. Shorten the text (delete less important words)
3. Keep the key selling points
4. Run QA again

---

**Error:** "Overview word count too low (350 words, need 500+)"

**Solution:**
1. Click "Regenerate" to get longer version
2. Or click "Edit" and add more details manually
3. Run QA again

---

### Issue 7: Can't Submit for Approval

**Error:** "Cannot submit: QA validation required"

**Solution:**
1. Click "Push to Sheets" first
2. Then click "Run QA"
3. Fix any QA issues
4. Then you can submit

---

## Best Practices

### 1. Review PDFs Before Uploading

**Quick pre-check:**
- Is the PDF complete? (no missing pages)
- Is text selectable? (not just scanned images)
- Are images clear and high resolution?
- Is pricing information clearly stated?

This saves time on revisions later!

### 2. Choose the Right Template

**Choose the right template for your target website:**
- Use "Aggregators" for third-party property portals
- Use "OPR" for opr.ae listings
- Use "MPP" for main-portal.com
- Use "ADOP" for abudhabioffplan.ae
- Use "ADRE" for secondary-market-portal.com
- Use "Commercial" for cre.main-portal.com

The template affects SEO content generation and field requirements.

### 3. Review Content Thoroughly

**Don't rush the review step:**
- Read the entire overview (don't just skim)
- Verify all numbers against the PDF
- Check that meta description is compelling
- Make sure developer name is spelled correctly

### 4. Add Helpful Notes

**When submitting, add context:**
```
Good: "PDF pricing unclear - verified AED 1.2M with Sarah from sales"
Bad: "Done"
```

This helps marketing managers review faster.

### 5. Respond to Revisions Quickly

**Target: Make revisions within 4 hours**
- Marketing managers need content quickly
- Fast turnaround = faster publishing
- Set up notification alerts

### 6. Organize Your PDFs

**File naming convention:**
```
Good: "Marina_Heights_Dubai_Marina_2026.pdf"
Bad: "brochure_final_v3_FINAL.pdf"
```

Descriptive names help when you need to reference original PDFs later.

### 7. Keep Track of Patterns

**Learn from each project:**
- Which developers provide good PDFs?
- Which PDFs need manual corrections?
- Common issues with specific sources?

Share these insights with your team.

---

## FAQs

### General Questions

**Q: How long does processing take?**

A: Typically 5-10 minutes. Complex PDFs with many pages may take up to 15 minutes.

---

**Q: Can I upload multiple PDFs at once?**

A: Not yet. Upload one at a time. Batch upload is coming in a future update.

---

**Q: What happens to my original PDF?**

A: It's stored securely in cloud storage and linked to your project. You can download it anytime from the project details page.

---

### Content Questions

**Q: Can I change the AI-generated content?**

A: Yes! You can edit any field manually or regenerate specific fields.

---

**Q: What if the AI gets something completely wrong?**

A: Edit it manually. The AI is very good but not perfect. Your review is crucial!

---

**Q: How do I know if my meta description is good?**

A: It should:
- Be under 160 characters
- Include project name and location
- Mention starting price if available
- Be compelling and readable

---

### Approval Questions

**Q: How long does marketing approval take?**

A: Marketing managers aim to review within 24 hours. You'll get a notification when approved.

---

**Q: What happens if my project is rejected?**

A: You'll receive specific feedback on what needs to change. Make the updates and resubmit.

---

**Q: Can I cancel a submission?**

A: Yes, if marketing hasn't reviewed it yet. Click "Recall Submission" on the project page.

---

### Technical Questions

**Q: Why can't I log in?**

A: Your @your-domain.com email must be whitelisted by an admin. Contact your manager.

---

**Q: The page won't load. What should I do?**

A:
1. Check your internet connection
2. Try refreshing the page
3. Clear browser cache
4. Try a different browser
5. Contact support if issue persists

---

**Q: Can I access this from my phone?**

A: The system works on mobile browsers, but we recommend using a desktop/laptop for the best experience, especially when reviewing content.

---

### Workflow Questions

**Q: Can I save a draft without submitting?**

A: Yes! All your changes are automatically saved. You can come back anytime and submit later.

---

**Q: What if I accidentally submit too early?**

A: If marketing hasn't reviewed it yet, click "Recall Submission" and make your changes.

---

**Q: Can I see the Google Sheet before submitting?**

A: Yes! Click "Push to Sheets" first. This creates the sheet without submitting for approval.

---

## Need More Help?

### Support Resources

**Documentation:**
- This guide (you're reading it!)
- Video tutorials (coming soon)
- System changelog

**Contact Support:**
- Email: pdp-support@your-domain.com
- Slack: #pdp-automation channel
- Direct: Your admin or marketing manager

**Training:**
- New user onboarding (1 hour session)
- Advanced content review workshop
- Monthly Q&A sessions

---

**Happy content creating!** Remember, you're not just uploading PDFs - you're creating the first impression potential buyers have of these properties. Your attention to detail makes a real difference.

*Last updated: January 15, 2026*
