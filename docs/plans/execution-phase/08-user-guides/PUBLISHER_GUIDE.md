# Publisher Guide

**PDP Automation v.3**
*Your complete guide to publishing property content*

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Understanding the Publishing Workflow](#understanding-the-publishing-workflow)
4. [Accessing the Publishing Queue](#accessing-the-publishing-queue)
5. [Downloading Assets](#downloading-assets)
6. [Creating Pages in CMS](#creating-pages-in-cms)
7. [Per-Site Publishing Checklists](#per-site-publishing-checklists)
8. [Marking Projects as Published](#marking-projects-as-published)
9. [Post-Publication QA](#post-publication-qa)
10. [Troubleshooting Common Issues](#troubleshooting-common-issues)
11. [Best Practices](#best-practices)
12. [FAQs](#faqs)

---

## Introduction

### Who Is This Guide For?

This guide is for **Publishers** (Web Developers/CMS Managers) who are responsible for:
- Downloading approved content and assets
- Creating property pages in website CMS
- Uploading images and floor plans
- Ensuring SEO implementation
- Marking projects as published
- Running post-publication quality checks

You bridge the gap between approved content and live websites.

### What You'll Learn

By the end of this guide, you'll be able to:
- Access approved projects ready for publishing
- Download Google Sheets and asset ZIP files
- Create pages using template-specific checklists (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
- Follow per-template checklists
- Mark projects as published with correct URLs
- Run post-publication QA to verify accuracy

---

## Getting Started

### Your Role in the Workflow

```
Content Creator → Marketing Manager → Publisher → Live Website
                                        (YOU)
```

You're the final step before content goes live to the public.

### Key Responsibilities

1. **Asset Management** - Download and organize content files
2. **CMS Publishing** - Create pages in WordPress/custom CMS
3. **SEO Implementation** - Ensure meta tags, schema markup correct
4. **Image Optimization** - Upload and optimize images
5. **Quality Assurance** - Verify published page matches approved content
6. **URL Tracking** - Record published URLs in system

### Access Requirements

- **Email:** @your-domain.com Google Workspace account
- **CMS Access:** WordPress/Admin access to all target websites (OPR, MPP, ADOP, ADRE, CRE, aggregator portals)
- **Google Drive:** Access to shared folders
- **Tools:** FTP client (if needed), image editor (optional)

---

## Understanding the Publishing Workflow

### The Publishing Process

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  1. Marketing approves project                          │
│           ↓                                             │
│  2. Project enters Publishing Queue                     │
│           ↓                                             │
│  3. You download assets (Sheet + ZIP)                   │
│           ↓                                             │
│  4. Create page in website CMS                          │
│           ↓                                             │
│  5. Complete site-specific checklist                    │
│           ↓                                             │
│  6. Enter published URL                                 │
│           ↓                                             │
│  7. Mark as "Published"                                 │
│           ↓                                             │
│  8. Run post-publication QA (optional but recommended)  │
│           ↓                                             │
│  9. Project status: PUBLISHED ✓                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Publishing Timeline

**Target:** Publish within 48 hours of approval

- Download assets: 5 minutes
- Create CMS page: 30-60 minutes (depending on site)
- Upload images: 15-30 minutes
- Review and publish: 15 minutes
- Post-publication QA: 10 minutes

**Total time per project:** 1.5 - 2.5 hours

---

## Accessing the Publishing Queue

### Step 1: Navigate to Publishing

Click **"Publishing"** in the left sidebar:

```
╔══════════════╦══════════════════════════════╗
║              ║                              ║
║  Dashboard   ║   Publishing Queue           ║
║  Processing  ║                              ║
║  Projects    ║   You have 5 projects        ║
║  Approvals   ║   ready to publish           ║
║→ Publishing⁽⁵⁾║                              ║
║              ║                              ║
╚══════════════╩══════════════════════════════╝
```

### Step 2: View Publishing Queue

```
╔════════════════════════════════════════════════════════════╗
║ Publishing Queue              Sort: [Priority ▼]          ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ 🔴 Marina Heights                  URGENT - 36h overdue ║║
║ │ OPR | Dubai Marina                                     ║║
║ │ Approved: Jan 13 at 2:00 PM                            ║║
║ │ [Download Assets] [Start Publishing]                   ║║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ 🟡 Palm Gardens                    Due in 24 hours     ║║
║ │ ADRE | Abu Dhabi                                       ║║
║ │ Approved: Jan 14 at 10:00 AM                           ║║
║ │ [Download Assets] [Start Publishing]                   ║║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ 🟢 Downtown Executive              On track            ║║
║ │ Commercial | Downtown Dubai                            ║║
║ │ Approved: Jan 15 at 9:00 AM                            ║║
║ │ [Download Assets] [Start Publishing]                   ║║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Priority Indicators

- 🔴 **Urgent/Overdue** - Publish immediately
- 🟡 **Due Soon** - Due within 24 hours
- 🟢 **On Track** - Within SLA timeframe

### Filtering Options

Filter by:
- **Template:** Aggregators, OPR, MPP, ADOP, ADRE, Commercial
- **Status:** Pending, In Progress, Published
- **Date:** Approval date range
- **Priority:** Urgent first

---

## Downloading Assets

### What You'll Download

For each project, you'll download:

1. **Google Sheet** - All content and data
2. **ZIP File** - All images and floor plans

### Step 1: Download Google Sheet

Click **"Download Assets"** → **"Open Google Sheet"**:

```
╔════════════════════════════════════════════════════════════╗
║ Marina Heights - Assets                                    ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ 📊 Google Sheet                                            ║
║ Contains: All SEO content, project data, descriptions      ║
║ [Open in Google Sheets] [Download as Excel]               ║
║                                                            ║
║ 📦 Asset ZIP File (45.3 MB)                                ║
║ Contains: 28 images, 3 floor plans                         ║
║ [Download ZIP]                                             ║
║                                                            ║
║ 📄 Original PDF (12.1 MB)                                  ║
║ [Download PDF] (reference only)                            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Step 2: Review Google Sheet Structure

The sheet contains organized content:

```
Google Sheet Tabs:
├─ SEO Content (meta title, description, H1, overview)
├─ Project Details (developer, price, handover, payment plan)
├─ Unit Types (bedroom configs, sizes, prices)
├─ Features (bullet points)
├─ Amenities (bullet points)
├─ Location (community, sub-community, nearby landmarks)
└─ Image Inventory (filenames and categories)
```

**Sheet example:**

| Field | Content | Character Count |
|-------|---------|-----------------|
| Meta Title | Marina Heights \| Luxury Apartments in Dubai Marina | 48/60 |
| Meta Description | Discover luxury waterfront living at Marina Heights... | 152/160 |
| H1 Heading | Marina Heights - Luxury Waterfront Living in Dubai | N/A |
| URL Slug | marina-heights-dubai-marina | N/A |

### Step 3: Download ZIP File

Click **"Download ZIP"**. The ZIP contains:

```
marina-heights-assets.zip
├─ exterior/
│  ├─ exterior_01.png
│  ├─ exterior_02.png
│  └─ ... (10 total)
├─ interior/
│  ├─ interior_01.png
│  ├─ interior_02.png
│  └─ ... (10 total)
├─ amenities/
│  ├─ amenity_01.png
│  └─ ... (5 total)
├─ logos/
│  ├─ logo_01.png
│  └─ ... (3 total)
└─ floor_plans/
   ├─ 1BR_floorplan.png
   ├─ 2BR_floorplan.png
   └─ 3BR_floorplan.png
```

**Image formats:**
- All images: PNG (high quality)
- Watermarks removed
- Optimized for web

### Step 4: Organize Your Files

**Recommended folder structure on your computer:**

```
C:\Publishing\
├─ OPR\
│  └─ Marina Heights\
│     ├─ marina-heights-content.xlsx
│     └─ marina-heights-assets.zip (extracted)
├─ MPP\
├─ ADOP\
├─ ADRE\
└─ Commercial\
```

Keep organized for easy reference during publishing.

---

## Creating Pages in CMS

Publishing steps vary by website. See site-specific sections below.

### General CMS Workflow

**Step 1:** Log into website CMS

**Step 2:** Create new property page/post

**Step 3:** Copy content from Google Sheet:
- Meta title → SEO plugin
- Meta description → SEO plugin
- H1 heading → Page title
- Overview → Main content area
- Features → Bullet list
- Amenities → Bullet list

**Step 4:** Upload images:
- Featured image (hero)
- Image gallery
- Floor plans

**Step 5:** Add structured data:
- Developer name
- Starting price
- Handover date
- Payment plan
- Unit types

**Step 6:** Configure SEO:
- URL slug
- Meta tags
- Schema markup (if applicable)

**Step 7:** Preview page

**Step 8:** Publish

---

## Per-Template Publishing Checklists

### Aggregators Template - Third-Party Portals

**Technology:** Varies by portal (Property Finder, Bayut, Dubizzle, etc.)

#### Publishing Checklist

```
┌──────────────────────────────────────────────────────────┐
│ Aggregators Publishing Checklist                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Portal Selection                                      │
│    ☐ Identify target aggregator portals                  │
│    ☐ Check portal-specific requirements                  │
│    ☐ Verify account access for each portal               │
│                                                          │
│ 2. Content Adaptation                                    │
│    ☐ Adjust content length per portal limits             │
│    ☐ Format descriptions for portal standards            │
│    ☐ Add portal-specific keywords                        │
│                                                          │
│ 3. Images                                                │
│    ☐ Upload images per portal requirements               │
│    ☐ Set primary/featured image                          │
│    ☐ Ensure image dimensions meet portal specs           │
│                                                          │
│ 4. Project Details                                       │
│    ☐ Enter all required fields                           │
│    ☐ Verify pricing format (AED)                         │
│    ☐ Add handover date                                   │
│    ☐ Set property type and category                      │
│                                                          │
│ 5. Publish                                               │
│    ☐ Submit for portal review (if required)              │
│    ☐ Record published URL for each portal                │
│    ☐ Verify listing appears correctly                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

### OPR Template - opr.ae

**Technology:** WordPress with custom theme + Yoast SEO

#### Publishing Checklist

```
┌──────────────────────────────────────────────────────────┐
│ OPR Publishing Checklist - Marina Heights                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Page Setup                                            │
│    ☐ Create new "Property" post type                     │
│    ☐ Enter H1 as post title                              │
│    ☐ Set URL slug (e.g., marina-heights-dubai-marina)    │
│                                                          │
│ 2. Content                                               │
│    ☐ Copy overview text to main content editor           │
│    ☐ Format paragraphs (remove extra line breaks)        │
│    ☐ Add features list (bullet points)                   │
│    ☐ Add amenities list (bullet points)                  │
│    ☐ Add location description                            │
│                                                          │
│ 3. Images                                                │
│    ☐ Upload featured image (hero - use exterior_01)      │
│    ☐ Create gallery (10 exterior + 10 interior images)   │
│    ☐ Upload amenity images to amenities section          │
│    ☐ Upload developer logo                               │
│    ☐ Add alt text to all images                          │
│                                                          │
│ 4. Floor Plans                                           │
│    ☐ Upload floor plan images                            │
│    ☐ Add bedroom/bathroom counts                         │
│    ☐ Add square footage                                  │
│    ☐ Link floor plans to unit types                      │
│                                                          │
│ 5. Project Details (Custom Fields)                       │
│    ☐ Developer name                                      │
│    ☐ Starting price (AED 1,200,000)                      │
│    ☐ Handover date (Q4 2026)                             │
│    ☐ Payment plan (60/40)                                │
│    ☐ Unit types (1, 2, 3 BR)                             │
│    ☐ Total units (250)                                   │
│    ☐ Location (Dubai Marina)                             │
│                                                          │
│ 6. SEO (Yoast)                                           │
│    ☐ SEO Title (copy from sheet)                         │
│    ☐ Meta description (copy from sheet)                  │
│    ☐ Focus keyphrase (e.g., "Dubai Marina apartments")   │
│    ☐ Yoast SEO score: Green                              │
│                                                          │
│ 7. Preview & Publish                                     │
│    ☐ Preview page (desktop)                              │
│    ☐ Preview page (mobile)                               │
│    ☐ Click "Publish"                                     │
│    ☐ Copy published URL                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**URL Structure:**
```
https://opr.ae/properties/[project-slug]
```

---

### MPP Template - main-portal.com

**Technology:** WordPress with custom theme

#### Publishing Checklist

```
┌──────────────────────────────────────────────────────────┐
│ MPP Publishing Checklist                                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Page Setup                                            │
│    ☐ Create new property listing                         │
│    ☐ Enter H1 as post title                              │
│    ☐ Set URL slug                                        │
│                                                          │
│ 2. Content                                               │
│    ☐ Copy overview text                                  │
│    ☐ Add features and amenities                          │
│    ☐ Add location description                            │
│                                                          │
│ 3. Images & Media                                        │
│    ☐ Upload featured image                               │
│    ☐ Create gallery                                      │
│    ☐ Upload floor plans                                  │
│    ☐ Add alt text to all images                          │
│                                                          │
│ 4. Project Details                                       │
│    ☐ Developer name                                      │
│    ☐ Starting price                                      │
│    ☐ Handover date                                       │
│    ☐ Payment plan                                        │
│    ☐ Unit types                                          │
│                                                          │
│ 5. SEO & Publish                                         │
│    ☐ SEO Title and Meta description                      │
│    ☐ Preview and publish                                 │
│    ☐ Copy published URL                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**URL Structure:**
```
https://main-portal.com/properties/[project-slug]
```

---

### ADOP Template - abudhabioffplan.ae

**Technology:** WordPress

#### Publishing Checklist

```
┌──────────────────────────────────────────────────────────┐
│ ADOP Publishing Checklist                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Page Setup                                            │
│    ☐ Create new property listing                         │
│    ☐ Enter H1 as post title                              │
│    ☐ Set URL slug                                        │
│                                                          │
│ 2. Abu Dhabi-Specific Content                            │
│    ☐ Copy overview text                                  │
│    ☐ Add Abu Dhabi location details                      │
│    ☐ Add features and amenities                          │
│                                                          │
│ 3. Images & Media                                        │
│    ☐ Upload featured image                               │
│    ☐ Create gallery                                      │
│    ☐ Upload floor plans                                  │
│    ☐ Add alt text                                        │
│                                                          │
│ 4. Project Details                                       │
│    ☐ Developer name                                      │
│    ☐ Starting price (AED)                                │
│    ☐ Handover date                                       │
│    ☐ Payment plan                                        │
│                                                          │
│ 5. SEO & Publish                                         │
│    ☐ SEO Title and Meta description                      │
│    ☐ Preview and publish                                 │
│    ☐ Copy published URL                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**URL Structure:**
```
https://abudhabioffplan.ae/properties/[project-slug]
```

---

### ADRE Template - secondary-market-portal.com

**Technology:** WordPress

#### Publishing Checklist

```
┌──────────────────────────────────────────────────────────┐
│ ADRE Publishing Checklist                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Page Setup                                            │
│    ☐ Create new property listing                         │
│    ☐ Enter H1 as post title                              │
│    ☐ Set URL slug                                        │
│                                                          │
│ 2. Content                                               │
│    ☐ Copy overview text                                  │
│    ☐ Add Abu Dhabi market context                        │
│    ☐ Add features and amenities                          │
│                                                          │
│ 3. Images & Media                                        │
│    ☐ Upload featured image                               │
│    ☐ Create gallery                                      │
│    ☐ Upload floor plans                                  │
│                                                          │
│ 4. Project Details                                       │
│    ☐ Developer name                                      │
│    ☐ Starting price                                      │
│    ☐ Handover date                                       │
│    ☐ Payment plan                                        │
│                                                          │
│ 5. SEO & Publish                                         │
│    ☐ SEO Title and Meta description                      │
│    ☐ Preview and publish                                 │
│    ☐ Copy published URL                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**URL Structure:**
```
https://secondary-market-portal.com/properties/[project-slug]
```

---

### Commercial Template - cre.main-portal.com

**Technology:** WordPress

#### Publishing Checklist

```
┌──────────────────────────────────────────────────────────┐
│ Commercial Publishing Checklist                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Page Setup                                            │
│    ☐ Create new commercial listing                       │
│    ☐ Select type: Office / Retail / Industrial           │
│    ☐ Enter H1 as post title                              │
│    ☐ Set URL slug                                        │
│                                                          │
│ 2. Content                                               │
│    ☐ Copy overview text                                  │
│    ☐ Add commercial-specific features                    │
│    ☐ Add location and accessibility info                 │
│                                                          │
│ 3. Images & Media                                        │
│    ☐ Upload featured image                               │
│    ☐ Create gallery                                      │
│    ☐ Upload floor plans                                  │
│                                                          │
│ 4. Commercial Details                                    │
│    ☐ Developer name                                      │
│    ☐ Starting price                                      │
│    ☐ Handover date                                       │
│    ☐ Payment plan                                        │
│    ☐ ROI information (if available)                      │
│    ☐ Rental yield (if available)                         │
│                                                          │
│ 5. SEO & Publish                                         │
│    ☐ SEO Title and Meta description                      │
│    ☐ Preview and publish                                 │
│    ☐ Copy published URL                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**URL Structure:**
```
https://cre.main-portal.com/properties/[project-slug]
```

---

## Marking Projects as Published

After publishing the page on the website, return to PDP Automation to mark it as published.

### Step 1: Navigate to Project

In Publishing Queue, click the project you just published.

### Step 2: Enter Published URL

```
╔════════════════════════════════════════════════════════════╗
║ Mark as Published - Marina Heights                        ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Published URL:                                             ║
║ [https://opr.ae/properties/marina-heights-dubai-marina  ] ║
║                                                            ║
║ Published Date: [Jan 15, 2026 ▼]                          ║
║                                                            ║
║ Notes (optional):                                          ║
║ [Published on OPR WordPress. All content and images       │
║  uploaded successfully. SEO optimized.]                    │
║                                                            ║
║ [Cancel]  [Mark as Published]                              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Step 3: Confirm

Click **"Mark as Published"**.

Success message:
```
✓ Project marked as published!
  URL recorded: https://opr.ae/properties/marina-heights-dubai-marina
  Status updated to: Published
```

### Step 4: Verify Status Change

Project moves from Publishing Queue to Published Projects:

```
╔════════════════════════════════════════════════════════════╗
║ Published Projects                                         ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ ✓ Marina Heights                                           ║
║   Published: Jan 15, 2026                                  ║
║   URL: opr.ae/properties/marina-heights-dubai-marina       ║
║   [View Page] [Run QA] [Edit]                              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## Post-Publication QA

**Highly recommended:** Run QA after publishing to verify accuracy.

### Step 1: Initiate QA Check

On published project, click **"Run QA"**:

```
╔════════════════════════════════════════════════════════════╗
║ Post-Publication QA                                        ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ This will scrape the published page and compare it        ║
║ against the approved content from Google Sheets.           ║
║                                                            ║
║ Published URL:                                             ║
║ https://opr.ae/properties/marina-heights-dubai-marina      ║
║                                                            ║
║ [Start QA Check]                                           ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Step 2: Wait for QA to Complete

QA takes 30-60 seconds:

```
Running QA Check...
⏳ Scraping published page
⏳ Extracting meta tags
⏳ Comparing content
⏳ Checking images
⏳ Generating report
```

### Step 3: Review QA Report

```
╔════════════════════════════════════════════════════════════╗
║ QA Report - Marina Heights                                ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Overall Score: 95/100                              PASS ✓  ║
║                                                            ║
║ Meta Tags                                          PASS ✓  ║
║  ✓ Meta title matches                                      ║
║  ✓ Meta description matches                                ║
║  ✓ H1 heading matches                                      ║
║                                                            ║
║ Content                                            PASS ✓  ║
║  ✓ Overview text matches (98% similarity)                  ║
║  ✓ Features present (12/12)                                ║
║  ✓ Amenities present (8/8)                                 ║
║                                                            ║
║ Images                                             WARN ⚠  ║
║  ✓ Featured image present                                  ║
║  ⚠ Gallery: 18/20 images (2 missing)                       ║
║  ✓ Floor plans present (3/3)                               ║
║                                                            ║
║ Structured Data                                    PASS ✓  ║
║  ✓ Developer name matches                                  ║
║  ✓ Starting price matches                                  ║
║  ✓ Handover date matches                                   ║
║                                                            ║
║ Issues Found: 1                                            ║
║  ⚠ 2 gallery images not uploaded                           ║
║                                                            ║
║ [View Detailed Report] [Fix Issues] [Re-run QA]           ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Step 4: Fix Any Issues

If QA finds issues:

1. Note the specific issues (e.g., "2 gallery images missing")
2. Go back to CMS
3. Fix the issues (upload missing images)
4. Re-run QA
5. Confirm all checks pass

### What QA Checks

**Meta Tags:**
- Meta title exact match
- Meta description exact match
- H1 heading exact match
- URL slug matches

**Content:**
- Overview text similarity (allows minor differences)
- Features list completeness
- Amenities list completeness

**Images:**
- Featured image present
- Gallery image count
- Floor plan images present

**Structured Data:**
- Developer name
- Starting price
- Handover date
- Payment plan
- Unit types

**Scoring:**
- 90-100: PASS ✓
- 70-89: WARN ⚠ (minor issues)
- Below 70: FAIL ✗ (requires fixes)

---

## Troubleshooting Common Issues

### Issue 1: Images Won't Upload

**Problem:** CMS rejects image upload or images corrupted

**Solutions:**
1. **Check file size:** Reduce if over 2MB per image
2. **Check format:** CMS may require JPG instead of PNG
3. **Check permissions:** Verify write permissions on uploads folder
4. **Rename files:** Remove special characters from filenames

**Image optimization tools:**
- TinyPNG (online)
- ImageOptim (Mac)
- RIOT (Windows)

---

### Issue 2: Content Formatting Issues

**Problem:** Text doesn't format correctly when pasted from Google Sheet

**Solutions:**
1. **Paste as plain text:** Use Ctrl+Shift+V (or Cmd+Shift+V on Mac)
2. **Remove extra line breaks:** Clean up formatting manually
3. **Use HTML editor:** Switch to HTML view and clean code
4. **Use Word/Notepad:** Paste first into Word, clean, then paste to CMS

---

### Issue 3: SEO Plugin Shows Errors

**Problem:** Yoast SEO or similar plugin shows red/orange indicators

**Common fixes:**
- **"Meta description too short"** → Use exact text from Google Sheet
- **"No focus keyword"** → Add focus keyword (project name + location)
- **"Text too short"** → Ensure all overview text is pasted
- **"No images with alt text"** → Add alt text to all images

---

### Issue 4: Page URL Conflict

**Problem:** "URL slug already exists" error

**Solutions:**
1. Check if page already exists (search in CMS)
2. If duplicate, delete old version or use different slug
3. Add version number: `marina-heights-dubai-marina-2`
4. Contact admin to resolve duplicate

---

### Issue 5: QA Fails After Publishing

**Problem:** Post-publication QA shows multiple failures

**Solutions:**
1. Review detailed QA report for specific issues
2. Common causes:
   - Content not saved properly
   - Images not uploaded
   - Meta tags not configured
   - Page cached (clear cache)
3. Fix issues one by one
4. Re-run QA until passing

---

### Issue 6: Floor Plans Not Displaying

**Problem:** Floor plans uploaded but not showing on page

**Solutions:**
1. Check image paths are correct
2. Verify floor plan section is enabled in template
3. Clear browser cache
4. Check if images are in correct folder
5. Verify custom fields are populated

---

## Best Practices

### 1. Batch Similar Projects

**Efficiency tip:**
- Publish all OPR projects together
- Publish all projects of the same template together
- This keeps you in the same workflow/mindset

**Example schedule:**
- Monday: OPR + MPP projects
- Tuesday: ADOP + ADRE projects
- Wednesday: Aggregators projects
- Thursday: Commercial projects
- Friday: Catch-up and QA verification

### 2. Quality Over Speed

**Don't rush:**
- Better to publish 3 projects perfectly than 5 projects poorly
- QA failures waste more time than careful initial publishing
- Your work represents the brand

### 3. Use Snippets/Templates

**Save time with pre-built snippets:**

**WordPress snippet for property schema:**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{PROJECT_NAME}}",
  "description": "{{META_DESCRIPTION}}",
  "offers": {
    "@type": "Offer",
    "price": "{{STARTING_PRICE}}",
    "priceCurrency": "AED"
  }
}
</script>
```

Replace placeholders with actual values.

### 4. Double-Check URLs

**Before marking as published:**
- Test URL in browser
- Check URL works from different devices
- Verify URL matches expected format
- Ensure no typos in slug

**Common URL mistakes:**
- Extra hyphens: `marina--heights`
- Underscores instead of hyphens: `marina_heights`
- Missing location: `marina-heights` (should be `marina-heights-dubai-marina`)

### 5. Optimize Images Before Upload

**Image optimization checklist:**
- Resize to appropriate dimensions (max 1920px width)
- Compress to reduce file size (aim for under 200KB per image)
- Use correct format (JPG for photos, PNG for logos)
- Add descriptive alt text for accessibility

**Recommended sizes:**
- Hero/Featured: 1920x1080px
- Gallery: 1200x800px
- Floor plans: 1000x1000px
- Logos: 500x500px (transparent background)

### 6. Add Internal Links

**SEO best practice:**
- Link to developer page (if exists)
- Link to location guide
- Link to similar properties
- Link to related blog posts

**Example:**
"Marina Heights by **[Emaar Properties]** is located in **[Dubai Marina]**, one of Dubai's most sought-after communities. See **[similar properties in Dubai Marina]**."

### 7. Test on Mobile

**Always preview on mobile:**
- 60%+ of traffic is mobile
- Images should load properly
- Text should be readable
- Buttons should be tappable

**Mobile testing tools:**
- Browser developer tools (F12 → Toggle device toolbar)
- Real phone testing
- BrowserStack (cross-device testing)

### 8. Keep a Publishing Log

**Track your work:**

| Date | Project | Website | URL | Status | Notes |
|------|---------|---------|-----|--------|-------|
| Jan 15 | Marina Heights | OPR | opr.ae/... | Published | QA: 95% |
| Jan 15 | Palm Gardens | PJA | palmjebeli... | Published | QA: 100% |

This helps track productivity and troubleshoot issues.

---

## FAQs

**Q: How long should publishing take per project?**

A: Average 1.5-2 hours per project. You'll get faster with practice.

---

**Q: What if the Google Sheet has errors?**

A: Don't publish with errors. Send back to marketing manager for correction.

---

**Q: Can I edit content during publishing?**

A: Minor edits (fixing typos) are OK. Major changes need marketing approval.

---

**Q: What if images look low quality?**

A: Contact content creator - they may have higher resolution versions. Don't publish poor quality images.

---

**Q: Should I always run post-publication QA?**

A: Highly recommended, especially for new publishers. Experienced publishers can skip for simple projects.

---

**Q: What if QA keeps failing?**

A: Review the specific issues. Common cause: caching. Clear all caches and re-run QA.

---

**Q: Can I publish to staging first?**

A: Yes! Best practice is staging → QA → production for important projects.

---

**Q: What's the SLA for publishing?**

A: Target 48 hours from approval. Urgent projects should be prioritized.

---

**Q: What if URL slug is too long?**

A: Shorten it while keeping key info. Example: `marina-heights-luxury-waterfront-apartments-dubai-marina` → `marina-heights-dubai-marina`

---

**Q: How do I handle multiple unit types?**

A: Create tabs or sections for each unit type. Include all floor plans.

---

## Need Help?

**Support Resources:**
- This guide
- CMS-specific documentation (WordPress Codex, etc.)
- Internal wiki

**Contact:**
- Email: pdp-support@your-domain.com
- Slack: #pdp-automation channel
- CMS issues: web-dev@your-domain.com

---

**Remember:** You're the bridge between approved content and live websites. Your attention to detail ensures visitors get accurate, professional information about each property. Take pride in your work!

*Last updated: January 15, 2026*
