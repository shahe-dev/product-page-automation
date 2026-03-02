# Glossary

A comprehensive reference of all technical terms, acronyms, and domain-specific language used in PDP Automation v.3.

**Last Updated:** 2026-01-15
**Version:** 0.2.0

---

## Table of Contents

- [General Terms](#general-terms)
- [Technical Terms](#technical-terms)
- [Real Estate Terms](#real-estate-terms)
- [Google Cloud Terms](#google-cloud-terms)
- [Workflow States](#workflow-states)
- [User Roles](#user-roles)
- [System Modules](#system-modules)
- [File Types](#file-types)
- [API Terms](#api-terms)

---

## General Terms

### PDP

**Definition:** Property Detail Page - A dedicated webpage showcasing all information about a specific real estate development project.

**Usage:** The primary output of the PDP Automation system. Each processed brochure generates content for one PDP.

**Example:** "The PDP for Emaar Beachfront includes 30 optimized images, SEO content, and floor plans."

**See Also:** [Brochure](#brochure), [Content Generation](#content-generation)

---

### Brochure

**Definition:** PDF marketing material provided by real estate developers containing project details, images, floor plans, and pricing information.

**Usage:** The primary input to PDP Automation v.3. Brochures are uploaded, processed, and transformed into structured content.

**Example:** "Upload the Dubai Hills Estate brochure to generate content for all six templates."

**See Also:** [PDF](#pdf), [Extraction](#extraction)

---

### Extraction

**Definition:** The automated process of pulling structured data (text, numbers, dates) from PDF brochures using AI vision technology.

**Usage:** First major step in the processing pipeline. Extracts developer name, starting price, handover date, amenities, etc.

**Example:** "Extraction identified 'Emaar Properties' as the developer and 'Q4 2026' as the handover date."

**See Also:** [Claude Vision](#claude-vision), [OCR](#ocr)

---

### Classification

**Definition:** The process of automatically categorizing images by type: interior, exterior, amenity, logo, floor plan, or location map.

**Usage:** Ensures images are organized correctly for publishers to use in page creation.

**Example:** "Classification identified 15 interior shots, 8 exterior renders, and 12 amenity images."

**See Also:** [Image Processing](#image-processing), [Claude Vision](#claude-vision)

---

### Content Generation

**Definition:** The AI-powered creation of SEO-optimized text content (meta titles, descriptions, overviews, highlights) from extracted data.

**Usage:** Final step in the pipeline. Generates tailored content for each of the six content templates.

**Example:** "Content generation created unique meta descriptions for Aggregators, OPR, MPP, ADOP, ADRE, and Commercial templates."

**See Also:** [LLM](#llm), [Prompt Library](#prompt-library)

---

### Processing Pipeline

**Definition:** The complete sequence of automated steps that transform a PDF brochure into publishable content.

**Usage:** Encompasses upload, extraction, classification, optimization, content generation, and output packaging.

**Example:** "The processing pipeline took 7 minutes to complete for the 45-page brochure."

**See Also:** [Extraction](#extraction), [Classification](#classification), [Content Generation](#content-generation)

---

### Watermark Detection

**Definition:** AI-powered identification and flagging of branded watermarks or logos overlaid on images.

**Usage:** Helps publishers identify which images need watermark removal before publication.

**Example:** "Watermark detection found 'EMAAR' branding on 23 of 30 images."

**See Also:** [Image Processing](#image-processing)

---

## Technical Terms

### API

**Definition:** Application Programming Interface - A set of endpoints that allow external systems to interact with PDP Automation programmatically.

**Usage:** Developers can integrate PDP Automation into other tools and workflows using the REST API.

**Example:** "Use the `/api/projects` endpoint to retrieve all projects programmatically."

**See Also:** [REST](#rest), [Authentication](#authentication)

---

### OAuth

**Definition:** Open Authorization - An industry-standard protocol for secure authentication using Google accounts.

**Usage:** All users must authenticate via Google OAuth. Only @your-domain.com email addresses are permitted.

**Example:** "Click 'Sign in with Google' to authenticate via OAuth 2.0."

**See Also:** [Authentication](#authentication), [JWT](#jwt)

---

### JWT

**Definition:** JSON Web Token - An encrypted token used to maintain user sessions securely.

**Usage:** After OAuth login, the system issues a JWT that expires after 24 hours of inactivity.

**Example:** "The JWT contains your user ID, role, and session expiration timestamp."

**See Also:** [OAuth](#oauth), [Authentication](#authentication)

---

### REST

**Definition:** Representational State Transfer - An architectural style for designing APIs using standard HTTP methods.

**Usage:** The PDP Automation API follows REST principles: GET for retrieval, POST for creation, PATCH for updates.

**Example:** "Send a POST request to `/api/projects` to create a new project."

**See Also:** [API](#api), [HTTP Methods](#http-methods)

---

### Async

**Definition:** Asynchronous - Operations that run in the background without blocking user interactions.

**Usage:** PDF processing, image optimization, and content generation all run asynchronously.

**Example:** "The async processing job allows you to continue working while the brochure is being processed."

**See Also:** [Cloud Tasks](#cloud-tasks), [Processing Pipeline](#processing-pipeline)

---

### JSONB

**Definition:** JSON Binary - A PostgreSQL data type that stores JSON documents efficiently with full indexing support.

**Usage:** Project metadata, custom fields, and prompt versions are stored as JSONB.

**Example:** "Custom fields are stored in the `custom_fields` JSONB column."

**See Also:** [PostgreSQL](#postgresql), [Neon](#neon)

---

### LLM

**Definition:** Large Language Model - Advanced AI system (like Claude Sonnet 4.5) capable of understanding and generating human-like text.

**Usage:** Powers content generation, text extraction, and image classification in PDP Automation.

**Example:** "The LLM generates unique meta descriptions by analyzing extracted project data."

**See Also:** [Anthropic API](#anthropic-api), [Content Generation](#content-generation)

---

### OCR

**Definition:** Optical Character Recognition - Technology that converts images of text into machine-readable text.

**Usage:** Claude Vision performs OCR on PDF pages to extract project details.

**Example:** "OCR extracted 'Starting from AED 1.2M' from the pricing table image."

**See Also:** [Extraction](#extraction), [Claude Vision](#claude-vision)

---

### WebP

**Definition:** Modern image format developed by Google that provides superior compression compared to JPG/PNG.

**Usage:** All images are converted to WebP (alongside JPG fallback) for faster page load times.

**Example:** "Image optimization converted the 4MB JPG to a 380KB WebP file."

**See Also:** [Image Optimization](#image-optimization)

---

## Real Estate Terms

### Developer

**Definition:** The company or organization building and marketing the real estate project.

**Usage:** One of the most critical extracted fields. Used in content generation and filtering.

**Example:** "Emaar Properties, Damac, Dubai Properties, Nakheel"

**See Also:** [Project](#project)

---

### Emirate

**Definition:** One of the seven administrative divisions that make up the United Arab Emirates.

**Usage:** Used for location filtering and SEO targeting.

**Example:** "Dubai, Abu Dhabi, Sharjah, Ajman, Umm Al Quwain, Ras Al Khaimah, Fujairah"

**See Also:** [Location](#location)

---

### Off-Plan

**Definition:** Real estate property sold to buyers before construction is completed.

**Usage:** Primary market segment for PDP Automation. Most brochures are for off-plan projects.

**Example:** "Dubai Hills Estate is an off-plan project with handover in Q4 2026."

**See Also:** [Handover Date](#handover-date)

---

### Handover Date

**Definition:** The expected date when completed properties will be delivered to buyers.

**Usage:** Critical field for buyer decision-making. Extracted from brochure and displayed prominently.

**Example:** "Q4 2026" or "December 2026" or "2026"

**See Also:** [Off-Plan](#off-plan)

---

### Payment Plan

**Definition:** The installment schedule showing how buyers will pay for the property over time.

**Usage:** Extracted as structured data (e.g., 60/40 means 60% during construction, 40% on handover).

**Example:** "60/40 payment plan" or "80/20 payment plan" or "10% down, 90% on completion"

**See Also:** [Starting Price](#starting-price)

---

### Starting Price

**Definition:** The minimum price for units in the project, typically for the smallest unit type.

**Usage:** Key pricing information extracted and validated during QA.

**Example:** "Starting from AED 1.2M" or "Prices from AED 850,000"

**See Also:** [Unit Type](#unit-type)

---

### Unit Type

**Definition:** The configuration of residential units available in the project.

**Usage:** Common types include Studio, 1BR, 2BR, 3BR, 4BR, 5BR, Penthouse, Townhouse, Villa.

**Example:** "Available unit types: Studio, 1BR, 2BR, 3BR"

**See Also:** [Starting Price](#starting-price)

---

### Amenity

**Definition:** Facility or service provided to residents as part of the development.

**Usage:** Extracted as a list and used in content generation to highlight project features.

**Example:** "Swimming pool, Gym, Kids play area, BBQ area, Jogging track, Retail outlets"

**See Also:** [Classification](#classification)

---

### Community

**Definition:** The broader neighborhood or master-planned development where the project is located.

**Usage:** Important for SEO and location-based searches.

**Example:** "Dubai Hills Estate," "Downtown Dubai," "Jumeirah Village Circle"

**See Also:** [Location](#location), [Emirate](#emirate)

---

## Google Cloud Terms

### GCS

**Definition:** Google Cloud Storage - Object storage service where uploaded PDFs and processed images are stored.

**Usage:** All files are stored in GCS buckets with encryption at rest.

**Example:** "The uploaded brochure is stored at `gs://pdp-automation-uploads/project-123/brochure.pdf`"

**See Also:** [Cloud Storage](#cloud-storage)

---

### Cloud Run

**Definition:** Fully managed serverless platform that automatically scales containerized applications.

**Usage:** The PDP Automation backend API runs on Cloud Run, scaling from 0 to 100+ instances based on demand.

**Example:** "The processing endpoint scaled to 5 Cloud Run instances during peak usage."

**See Also:** [Serverless](#serverless)

---

### Cloud Tasks

**Definition:** Managed service for executing asynchronous background jobs with retry logic.

**Usage:** PDF processing jobs are queued in Cloud Tasks to prevent timeouts and enable reliable execution.

**Example:** "The image optimization task is queued in Cloud Tasks with a 30-minute timeout."

**See Also:** [Async](#async), [Processing Pipeline](#processing-pipeline)

---

### Cloud Storage

**Definition:** Google's object storage service for storing files with global accessibility.

**Usage:** Hosts uploaded brochures, processed images, and generated ZIP files.

**Example:** "Download the processed images from Cloud Storage: `gs://pdp-automation-outputs/`"

**See Also:** [GCS](#gcs)

---

### Neon

**Definition:** Serverless PostgreSQL database platform with automatic scaling and branching.

**Usage:** PDP Automation uses Neon to store projects, users, audit logs, and workflow state.

**Example:** "The database connection pool automatically scales based on query load."

**See Also:** [PostgreSQL](#postgresql)

---

### PostgreSQL

**Definition:** Open-source relational database management system.

**Usage:** Primary data store for all application data, replacing the in-memory store from v0.1.0.

**Example:** "All projects are stored in PostgreSQL with JSONB columns for flexible metadata."

**See Also:** [Neon](#neon), [JSONB](#jsonb)

---

## Workflow States

### DRAFT

**Definition:** Initial state when a project is created but content has not been submitted for approval.

**Usage:** Content Creators work on projects in DRAFT state, editing and refining content.

**Example:** "The project is in DRAFT state. Submit it for approval when content is ready."

**See Also:** [Workflow](#workflow), [Content Creator](#content-creator)

---

### PENDING_APPROVAL

**Definition:** State when content has been submitted and is awaiting Marketing Manager review.

**Usage:** Project enters this state when Content Creator clicks "Submit for Approval."

**Example:** "3 projects are PENDING_APPROVAL in the queue."

**See Also:** [Approval Workflow](#approval-workflow), [Marketing Manager](#marketing-manager)

---

### REVISION_REQUESTED

**Definition:** State when Marketing Manager has requested changes to the content before approval.

**Usage:** Content Creator receives notification with feedback and must address issues before resubmitting.

**Example:** "Project moved to REVISION_REQUESTED with feedback: 'Update meta description to include community name.'"

**See Also:** [Approval Workflow](#approval-workflow)

---

### APPROVED

**Definition:** State when Marketing Manager has approved the content for publication.

**Usage:** Project is ready to be assigned to a Publisher for page creation.

**Example:** "Congratulations! Your project has been APPROVED."

**See Also:** [Publishing Workflow](#publishing-workflow)

---

### PUBLISHING

**Definition:** State when Publisher is actively creating the property detail page.

**Usage:** Publisher marks project as PUBLISHING when they start page creation work.

**Example:** "Publisher is working on this project. Current state: PUBLISHING."

**See Also:** [Publisher](#publisher), [Publishing Workflow](#publishing-workflow)

---

### PUBLISHED

**Definition:** State when the property detail page is live on the website.

**Usage:** Publisher marks project as PUBLISHED and provides the live page URL.

**Example:** "Page is now PUBLISHED at https://offplanreviewsdubai.com/dubai-hills-estate"

**See Also:** [QA Module](#qa-module)

---

### QA_VERIFIED

**Definition:** State when post-publication QA has confirmed the live page matches the generated content.

**Usage:** Final validation step before marking project as complete.

**Example:** "QA_VERIFIED: All content matches, images displayed correctly, page loads in <3s."

**See Also:** [QA Module](#qa-module)

---

### COMPLETE

**Definition:** Final state when all workflow steps are finished and validated.

**Usage:** Terminal state. Project requires no further action.

**Example:** "Project workflow is COMPLETE. Total time from upload to publication: 4 days."

**See Also:** [Workflow](#workflow)

---

## User Roles

### Content Creator

**Definition:** User role responsible for uploading brochures, reviewing generated content, and submitting for approval.

**Usage:** Primary day-to-day users of the system. Can manage projects in DRAFT state.

**Example:** "Content Creators can upload PDFs and edit generated content before submission."

**See Also:** [DRAFT](#draft), [PENDING_APPROVAL](#pending_approval)

---

### Marketing Manager

**Definition:** User role responsible for reviewing and approving/rejecting content submissions.

**Usage:** Quality gatekeepers who ensure brand consistency and content accuracy.

**Example:** "Marketing Managers can approve, reject, or request revisions on submitted projects."

**See Also:** [Approval Workflow](#approval-workflow), [APPROVED](#approved)

---

### Publisher

**Definition:** User role responsible for creating live property detail pages on websites.

**Usage:** Takes approved content and images to build and publish pages on CMS platforms.

**Example:** "Publishers receive approved projects and mark them as PUBLISHED when the page goes live."

**See Also:** [Publishing Workflow](#publishing-workflow), [PUBLISHED](#published)

---

### Admin

**Definition:** User role with full system access including user management, settings, and API configuration.

**Usage:** System administrators who manage users, templates, prompts, and troubleshoot issues.

**Example:** "Admins can view audit logs, manage prompt library, and configure API credentials."

**See Also:** [Audit Log](#audit-log), [Prompt Library](#prompt-library)

---

### Developer

**Definition:** Technical user who integrates PDP Automation with external systems using the API.

**Usage:** Can generate API keys, make programmatic requests, and build custom integrations.

**Example:** "Developers can use the REST API to automate project creation from CRM systems."

**See Also:** [API](#api), [REST](#rest)

---

## System Modules

### Project Database (Module 0)

**Definition:** Central repository storing all project data, metadata, and relationships.

**Usage:** Foundation module used by all other modules. Provides CRUD operations for projects.

**Example:** "The Project Database stores 247 projects with full audit history."

**See Also:** [PostgreSQL](#postgresql), [Neon](#neon)

---

### Material Preparation (Module 4)

**Definition:** Pipeline that converts PDF brochures into organized, optimized images.

**Usage:** Handles extraction, classification, watermark detection, optimization, and ZIP packaging.

**Example:** "Material Preparation processed 85 images in 4 minutes."

**See Also:** [Processing Pipeline](#processing-pipeline), [Image Optimization](#image-optimization)

---

### Content Generation (Module 5)

**Definition:** AI-powered module that creates SEO-optimized text content from extracted data.

**Usage:** Generates unique content for six content templates using version-controlled prompts.

**Example:** "Content Generation created meta titles, descriptions, and 800-word overviews for each template."

**See Also:** [LLM](#llm), [Prompt Library](#prompt-library)

---

### Approval Workflow (Module 1)

**Definition:** Multi-step review process ensuring content quality before publication.

**Usage:** Manages state transitions from DRAFT → PENDING_APPROVAL → APPROVED/REVISION_REQUESTED.

**Example:** "The Approval Workflow sent notifications to 2 Marketing Managers."

**See Also:** [Workflow States](#workflow-states), [Marketing Manager](#marketing-manager)

---

### Publishing Workflow (Module 1)

**Definition:** Process tracking page creation from approved content to live publication.

**Usage:** Manages APPROVED → PUBLISHING → PUBLISHED → QA_VERIFIED → COMPLETE states.

**Example:** "The Publishing Workflow includes site-specific checklists for each publisher."

**See Also:** [Publisher](#publisher), [QA Module](#qa-module)

---

### QA Module (Module 3)

**Definition:** Quality assurance system with three validation checkpoints.

**Usage:** Validates content at extraction, generation, and post-publication stages.

**Example:** "QA Module detected a price mismatch: expected 'AED 1.2M' but found 'AED 1.1M'."

**See Also:** [QA_VERIFIED](#qa_verified)

---

### Prompt Library (Module 5)

**Definition:** Version-controlled repository of AI prompts used for extraction and generation.

**Usage:** Enables prompt improvements without code changes. Tracks prompt performance metrics.

**Example:** "Prompt Library v2.3 improved meta description quality by 15%."

**See Also:** [Content Generation](#content-generation), [LLM](#llm)

---

### Notifications (Module 2)

**Definition:** Real-time alert system that notifies users of workflow events.

**Usage:** Sends in-app and email notifications for approvals, rejections, assignments, etc.

**Example:** "Notifications alerted you: 'Your project has been approved!'"

**See Also:** [Approval Workflow](#approval-workflow)

---

## File Types

### PDF

**Definition:** Portable Document Format - Standard format for sharing printable documents.

**Usage:** Only supported input format for brochures. Must be unencrypted and under 50MB.

**Example:** "Upload `Emaar_Beachfront_Brochure.pdf` to start processing."

**See Also:** [Brochure](#brochure)

---

### ZIP

**Definition:** Compressed archive file containing the organized output of processed images.

**Usage:** Generated automatically after image processing. Contains folders for each image category.

**Example:** "Download `project-123-images.zip` containing interior/, exterior/, amenities/ folders."

**See Also:** [Material Preparation](#material-preparation-module-4)

---

### WebP

**Definition:** Modern image format with superior compression and quality.

**Usage:** Primary output format for all images (with JPG fallback for compatibility).

**Example:** "Pool amenity image: `pool.webp` (420KB) and `pool.jpg` (1.2MB)"

**See Also:** [Image Optimization](#image-optimization)

---

## API Terms

### Endpoint

**Definition:** A specific URL path in the API that performs a particular function.

**Usage:** Developers call endpoints to interact with PDP Automation programmatically.

**Example:** "POST `/api/projects` creates a new project."

**See Also:** [API](#api), [REST](#rest)

---

### Rate Limit

**Definition:** Restriction on the number of API requests a user can make within a time period.

**Usage:** Prevents abuse and ensures fair resource allocation. Limits vary by user role.

**Example:** "Content Creators: 60 requests/minute. Developers: 300 requests/minute."

**See Also:** [API](#api)

---

### Authentication

**Definition:** Process of verifying user identity before granting system access.

**Usage:** All API requests require a valid JWT token in the Authorization header.

**Example:** "Include `Authorization: Bearer <your-jwt-token>` in all API requests."

**See Also:** [OAuth](#oauth), [JWT](#jwt)

---

### Webhook

**Definition:** HTTP callback that sends real-time event notifications to external systems.

**Usage:** Coming in v0.4.0. Will notify external systems of project events automatically.

**Example:** "Webhook triggers on 'project.approved' event, sending JSON payload to your endpoint."

**See Also:** [API](#api), [Notifications](#notifications-module-2)

---

## Additional Terms

### Audit Log

**Definition:** Chronological record of all actions performed in the system.

**Usage:** Tracks who did what and when for security, compliance, and troubleshooting.

**Example:** "Audit log shows: 'user@your-domain.com updated project-123 description at 2026-01-15 14:23:45'"

**See Also:** [Admin](#admin)

---

### Custom Fields

**Definition:** User-defined data fields that can be added to projects beyond standard fields.

**Usage:** Allows flexibility for project-specific information without schema changes.

**Example:** "Add custom field 'Internal Project Code' with value 'PROJ-2026-045'."

**See Also:** [JSONB](#jsonb)

---

### Template

**Definition:** Pre-configured mapping that defines how content should be formatted for specific output destinations.

**Usage:** Each of the six content templates has a template defining field mappings and formatting rules.

**Example:** "The OPR template uses 'meta_title' while the Commercial template uses 'listing_title'."

**See Also:** [Content Generation](#content-generation)

---

### Batch Processing

**Definition:** Processing multiple projects or performing actions on multiple items simultaneously.

**Usage:** Marketing Managers can batch approve multiple projects at once.

**Example:** "Batch approved 5 projects from the same developer."

**See Also:** [Marketing Manager](#marketing-manager)

---

### Image Optimization

**Definition:** Process of reducing image file sizes while maintaining visual quality.

**Usage:** Automatically resizes, compresses, and converts images to WebP + JPG formats.

**Example:** "Image optimization reduced total file size from 45MB to 12MB."

**See Also:** [WebP](#webp), [Material Preparation](#material-preparation-module-4)

---

### Response Caching

**Definition:** Anthropic API feature that reuses previous AI responses for identical prompts.

**Usage:** Reduces API costs by 70-90% for repeated content patterns.

**Example:** "Response caching saved $0.42 on this project by reusing similar amenity descriptions."

**See Also:** [Anthropic API](#anthropic-api)

---

### Semantic Versioning

**Definition:** Version numbering scheme using MAJOR.MINOR.PATCH format (e.g., 0.2.0).

**Usage:** System versions and prompt versions follow semantic versioning conventions.

**Example:** "v0.2.0 introduced QA module (minor version bump)"

**See Also:** [Changelog](./CHANGELOG.md)

---

### Claude Vision

**Definition:** AI model (Claude Sonnet 4.5) capable of analyzing images and extracting text and visual information.

**Usage:** Powers PDF extraction, OCR, and image classification.

**Example:** "Claude Vision identified 'Swimming Pool' in the amenity image."

**See Also:** [OCR](#ocr), [Classification](#classification)

---

### Anthropic API

**Definition:** Service providing access to Anthropic's language and vision models.

**Usage:** PDP Automation uses Claude Sonnet 4.5 for content generation and Claude Sonnet 4.5 for image analysis.

**Example:** "Anthropic API processed 247 requests for this project."

**See Also:** [LLM](#llm), [Claude Vision](#claude-vision)

---

## Related Documentation

- **User Guide:** [/docs/01-getting-started/USER_GUIDE.md](../01-getting-started/USER_GUIDE.md)
- **API Reference:** [/docs/08-api/API_REFERENCE.md](../08-api/API_REFERENCE.md)
- **Troubleshooting:** [/docs/09-reference/TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **FAQ:** [/docs/09-reference/FAQ.md](./FAQ.md)
- **Changelog:** [/docs/09-reference/CHANGELOG.md](./CHANGELOG.md)

---

**Have a term that's missing?** Contact your admin or email support@pdp-automation.com to suggest additions to this glossary.
