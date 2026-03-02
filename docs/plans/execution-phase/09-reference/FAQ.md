# Frequently Asked Questions (FAQ)

Quick answers to common questions about PDP Automation v.3. Can't find what you're looking for? Check the [Troubleshooting Guide](./TROUBLESHOOTING.md) or contact support.

**Last Updated:** 2026-01-15
**Version:** 0.2.0

---

## Table of Contents

- [General Questions](#general-questions)
- [Processing Questions](#processing-questions)
- [Content Questions](#content-questions)
- [Workflow Questions](#workflow-questions)
- [Technical Questions](#technical-questions)
- [Billing & Cost Questions](#billing--cost-questions)
- [Integration Questions](#integration-questions)

---

## General Questions

### Q: What is PDP Automation v.3?

**A:** PDP Automation v.3 is an intelligent system that transforms real estate PDF brochures into publication-ready content and optimized images for property detail pages. It uses advanced AI technology (Anthropic's Claude Sonnet 4.5) to extract data from brochures, classify images, and generate SEO-optimized content tailored for six content templates: Aggregators (24+ property domains), OPR (opr.ae), MPP (main-portal.com), ADOP (abudhabioffplan.ae), ADRE (secondary-market-portal.com), and Commercial (cre.main-portal.com).

**Key Features:**
- Automated text extraction from PDFs
- AI-powered image classification and optimization
- SEO content generation (meta titles, descriptions, overviews)
- Multi-stage approval workflow
- Quality assurance validation
- Google Sheets integration for content delivery

**Related:** [User Guide](../01-getting-started/USER_GUIDE.md)

---

### Q: Who can use the system?

**A:** PDP Automation v.3 is currently available only to users with @your-domain.com email addresses. Access is controlled through Google OAuth authentication, ensuring secure, organization-only access.

**User Roles:**
- **Content Creators:** Upload brochures, edit content, submit for approval (most common role)
- **Marketing Managers:** Review and approve/reject submitted content
- **Publishers:** Create live pages from approved content
- **Admins:** Manage users, system settings, and troubleshoot issues
- **Developers:** Integrate with the API for custom workflows

Contact your admin to request access or a role change.

**Related:** [Role Permissions Guide](../07-admin/USER_MANAGEMENT.md#roles)

---

### Q: How long does processing take?

**A:** Processing time varies based on brochure size and complexity:

**Typical Processing Times:**
- **Small brochure** (10-20 pages, 15-25 images): 3-5 minutes
- **Medium brochure** (25-35 pages, 30-50 images): 5-10 minutes
- **Large brochure** (40-60 pages, 60-100 images): 10-20 minutes
- **Very large brochure** (70+ pages, 150+ images): 20-30 minutes

**Processing Steps:**
1. Upload to cloud storage: 5-10%
2. Text extraction: 10-30%
3. Image extraction: 30-50%
4. Image classification: 50-60%
5. Image optimization: 60-75%
6. Content generation: 75-90%
7. Packaging outputs: 90-95%
8. Finalization: 95-100%

**Factors Affecting Speed:**
- PDF file size and page count
- Image count and resolution
- Current system load (number of concurrent jobs)
- Network connection speed (for upload)

**Related:** [Processing Pipeline Documentation](../02-processing/PROCESSING_PIPELINE.md)

---

### Q: What file formats are supported?

**A:** Currently, **only PDF files** are supported.

**File Requirements:**
- Format: PDF (.pdf extension)
- Maximum size: 50MB
- Must not be encrypted or password-protected
- Must contain readable text (not just scanned images)
- Maximum 500 images per PDF

**Not Supported:**
- Microsoft Word (.docx, .doc)
- PowerPoint (.pptx, .ppt)
- Image files (.jpg, .png)
- Compressed archives (.zip, .rar)

**Tip:** If your brochure is in another format, export or convert it to PDF before uploading.

**Related:** [PDF Processing Guide](../02-processing/PDF_PROCESSING.md)

---

### Q: Is my data secure?

**A:** Yes, security is a top priority in PDP Automation v.3.

**Security Measures:**
- **Authentication:** Google OAuth 2.0 with domain restriction (@your-domain.com only)
- **Encryption:** All files stored in Google Cloud Storage with encryption at rest
- **Access Control:** Role-based permissions (RBAC) limiting what each user can do
- **Audit Logging:** Every action tracked with user attribution and timestamps
- **HTTPS Only:** All communication encrypted in transit (TLS 1.3)
- **API Security:** JWT tokens with 24-hour expiration, rate limiting per role
- **Data Isolation:** Projects accessible only by authorized users
- **Regular Backups:** Daily automated backups with 30-day retention

**Data Storage:**
- Uploaded PDFs: Google Cloud Storage (GCS)
- Processed images: Google Cloud Storage (GCS)
- Project data: Neon PostgreSQL (serverless, encrypted)
- Session tokens: Encrypted, server-side storage

**Compliance:**
- SOC 2 Type II (Google Cloud Platform)
- GDPR compliant (data residency controls available)

**Related:** [Security Documentation](../07-admin/SECURITY.md)

---

### Q: Can I use this system for projects outside UAE?

**A:** Yes, the system works for real estate projects anywhere in the world. However, it's optimized for UAE market terminology and conventions.

**Current Optimization:**
- UAE locations (Dubai, Abu Dhabi, Sharjah, etc.)
- AED currency formatting
- UAE-specific terminology (off-plan, handover, emirate)
- Payment plan conventions common in UAE (60/40, 80/20)

**Using for Other Markets:**
- Content generation may need manual review for local terminology
- Currency and number formatting may need adjustment
- Custom prompts can be created for specific markets (contact admin)
- Template field mappings can be customized per region

**Related:** [Content Customization Guide](../03-content-generation/CUSTOMIZATION.md)

---

### Q: What happens if I accidentally delete a project?

**A:** Projects cannot be deleted by regular users (Content Creators, Marketing Managers, Publishers). Only Admins have delete permissions.

**If Admin Deletes Project:**
- Deleted projects are soft-deleted (marked as deleted, not permanently removed)
- Soft-deleted projects retained for 90 days
- Admin can restore deleted projects within 90-day window
- After 90 days, projects are permanently deleted
- Audit log preserves record of deletion (who, when, why)

**To Restore Deleted Project:**
1. Contact admin immediately
2. Provide project name or ID
3. Admin navigates to: Admin → Deleted Projects
4. Admin clicks "Restore" on project
5. Project returns to original state with all data intact

**Best Practice:** Don't rely on deletion as primary method. Use project status/archiving instead.

**Related:** [Project Management Guide](../05-projects/PROJECT_MANAGEMENT.md)

---

## Processing Questions

### Q: Why did my job fail?

**A:** Processing jobs can fail for several reasons. Here are the most common causes and solutions:

**Common Failure Reasons:**

1. **Encrypted or Password-Protected PDF (Most Common)**
   - Error: "PDF is encrypted or password-protected"
   - Solution: Provide unencrypted version ([See guide](./TROUBLESHOOTING.md#7-processing-fails-with-encrypted-pdf-not-supported))

2. **File Too Large (>50MB)**
   - Error: "File exceeds maximum size"
   - Solution: Compress PDF or request optimized version

3. **Corrupted File**
   - Error: "Invalid PDF structure" or "Cannot read file"
   - Solution: Re-export PDF from source application

4. **Anthropic API Rate Limit**
   - Error: "Rate limit exceeded" or "Too many requests"
   - Solution: Wait 15-30 minutes and retry

5. **Insufficient Text in PDF**
   - Error: "Could not extract sufficient data"
   - Solution: Ensure PDF has readable text (not just scanned images)

6. **Network Timeout**
   - Error: "Upload timeout" or "Connection lost"
   - Solution: Check internet connection and retry

**How to Diagnose:**
1. Check error message in notification or project detail page
2. Review project processing log (if available)
3. Verify file meets requirements (PDF, <50MB, unencrypted)
4. Try opening PDF in Adobe Reader to verify it's valid
5. Contact admin if error message is unclear

**Related:** [Troubleshooting Processing Issues](./TROUBLESHOOTING.md#processing-issues)

---

### Q: Can I cancel a job in progress?

**A:** Yes, you can cancel processing jobs at any point before completion.

**How to Cancel:**
1. Navigate to project detail page
2. Click "Cancel Processing" button (visible while job is running)
3. Confirm cancellation when prompted
4. Wait 30-60 seconds for cancellation to process
5. Page will refresh showing "Cancelled" status

**What Happens When You Cancel:**
- Processing stops immediately (within 30 seconds)
- Partial results are saved (e.g., extracted text, some images)
- Project status changes to "Cancelled"
- You can restart processing by clicking "Retry Processing"

**Important Notes:**
- Cancelled jobs still consume API quota for completed steps
- Partial data may be incomplete or inconsistent
- Better to let job fail naturally if there's an error
- Can't cancel jobs that are already 95%+ complete (finishing up)

**Use Cases for Cancellation:**
- Uploaded wrong PDF file
- Noticed critical error in brochure during processing
- Processing taking unusually long (>30 minutes)
- Need to make changes before processing continues

**Related:** [Processing Controls](../02-processing/PROCESSING_CONTROLS.md)

---

### Q: Can I process the same PDF multiple times?

**A:** Yes, you can process the same PDF brochure multiple times. Each upload creates a new, independent project.

**Use Cases:**
- **Prompt improvements:** Regenerate content with updated AI prompts
- **Error correction:** Re-process after fixing issues in source PDF
- **Content variations:** Generate different content versions for A/B testing
- **Template updates:** Re-process for new website template requirements

**What's Different Each Time:**
- New project ID assigned
- New processing timestamp
- Content may vary slightly (AI generation is non-deterministic)
- Images extracted identically (same source = same images)

**Important Notes:**
- Each processing consumes API quota (costs ~$0.56 per brochure)
- Previous versions not automatically deleted (manual cleanup needed)
- Duplicate projects can clutter project list (use search/filters)
- Consider using "Regenerate Content" feature instead of full re-processing

**Best Practice:**
- Use "Regenerate Content" for minor adjustments (faster, cheaper)
- Use full re-processing only when PDF content changed or major prompt updates

**Related:** [Content Regeneration Guide](../03-content-generation/REGENERATION.md)

---

### Q: What happens to images in the PDF?

**A:** Images undergo a comprehensive processing pipeline to prepare them for publication.

**Image Processing Steps:**

1. **Extraction (30-50% progress)**
   - All images extracted from PDF with original quality
   - Image metadata preserved (dimensions, format, page number)
   - Minimum size filter applied (images <100px excluded)

2. **Classification (50-60% progress)**
   - AI categorizes each image using Anthropic Vision (Claude Sonnet 4.5)
   - Categories: Interior, Exterior, Amenity, Logo, Floor Plan, Location Map
   - Confidence score assigned to each classification

3. **Watermark Detection (55-65% progress)**
   - AI identifies images with visible watermarks or branding
   - Flagged images marked for review by publisher
   - Does not remove watermarks (manual removal required)

4. **Deduplication (60-65% progress)**
   - Duplicate images identified using perceptual hashing
   - Only best quality version of duplicates kept
   - Floor plan variations preserved (different sizes/layouts)

5. **Optimization (60-75% progress)**
   - Images resized to multiple sizes (thumbnail, medium, large)
   - Converted to WebP format (primary) + JPG fallback
   - Compressed with quality settings (WebP: 85%, JPG: 90%)
   - File size reduced by 60-80% on average

6. **Organization (90-95% progress)**
   - Images sorted into category-based folders
   - Standardized naming: `{category}-{index}.{format}`
   - ZIP archive created with organized structure

**Output Structure:**
```
project-123-images.zip
├── interior/
│   ├── interior-001.webp
│   ├── interior-001.jpg
│   └── ...
├── exterior/
├── amenities/
├── floor_plans/
├── logos/
└── maps/
```

**Image Statistics (Typical Brochure):**
- Input: 30-40 images, 45MB total
- Output: 30-40 images × 2 formats, 12MB total
- Size reduction: 70-75%
- Processing time: 4-6 minutes

**Related:** [Image Processing Pipeline](../02-processing/IMAGE_PROCESSING.md)

---

### Q: Why are some images missing from the output?

**A:** Images may be excluded from the final output for several reasons:

**Common Reasons:**

1. **Too Small (Below Minimum Size)**
   - Threshold: 100px width or height
   - Reason: Tiny images are usually decorative elements or artifacts
   - Excluded: Icons, bullets, small logos (<100px)

2. **Identified as Duplicates**
   - Same image appears multiple times in PDF
   - Only highest quality version kept
   - Excluded: Lower resolution duplicates

3. **Failed Optimization**
   - Image corrupted or invalid format
   - Cannot be converted to WebP/JPG
   - Rare, but happens with unusual image formats

4. **Classified as Non-Content**
   - AI determines image is not relevant (decorative background, page numbers)
   - Very rare false positives

5. **Processing Error**
   - Individual image failed during extraction
   - Other images processed successfully
   - Error logged but doesn't stop overall processing

**How to Verify:**
1. View project image gallery (all extracted images displayed)
2. Compare gallery count with ZIP file count
3. Check if missing images are very small or duplicates
4. Review processing log for specific image errors

**If Critical Images Missing:**
1. Contact admin with project ID
2. Specify which images are missing (provide PDF page numbers)
3. Admin can manually extract and add missing images
4. Or re-process with adjusted extraction settings

**Related:** [Image Troubleshooting](./TROUBLESHOOTING.md#image-issues)

---

### Q: How accurate is the AI at extracting data?

**A:** Anthropic Vision (Claude Sonnet 4.5) has high accuracy for text extraction, but performance varies by PDF quality and content clarity.

**Accuracy Benchmarks:**

**Text Extraction:**
- Clean, typed text: 95-98% accuracy
- Tables and structured data: 90-95% accuracy
- Handwritten text: 60-70% accuracy (not recommended)
- Arabic text: 70-80% accuracy (English preferred)

**Data Field Extraction:**
- Developer name: 98% accuracy
- Project name: 95% accuracy
- Location (emirate): 95% accuracy
- Starting price: 92% accuracy (number format variations)
- Handover date: 90% accuracy (date format variations)
- Amenities list: 85% accuracy (may miss minor amenities)

**Image Classification:**
- Interior vs Exterior: 95% accuracy
- Amenity detection: 95% accuracy
- Logo isolation: 92% accuracy
- Floor plan detection: 98% accuracy

**Factors Affecting Accuracy:**
- PDF quality (higher quality = better accuracy)
- Text clarity and size (larger, clearer text = better)
- Layout complexity (simple layouts = better)
- Language (English = best, Arabic = lower)
- Image quality (high-res images = better classification)

**Best Practices for Maximum Accuracy:**
- Use high-quality, text-based PDFs (not scans)
- Ensure text is at least 10pt font size
- Use clear, consistent formatting
- Provide English-language brochures when possible
- Always review extracted data before submitting for approval

**Related:** [Content Quality Guidelines](../03-content-generation/CONTENT_QUALITY.md)

---

## Content Questions

### Q: Can I edit generated content?

**A:** Yes, absolutely! All generated content is fully editable before submission.

**How to Edit Content:**

1. **Navigate to Content Preview:**
   - Project detail page → "Review Content" tab
   - Or click "Edit Content" from project list

2. **Edit Any Field:**
   - Click field to edit inline
   - Type or paste new content
   - Character count updates in real-time
   - Save changes (auto-saves after 2 seconds)

3. **Field-by-Field Editing:**
   - Meta title: Click to edit, 55-60 character limit
   - Meta description: Click to edit, 150-160 character limit
   - H1 headline: Click to edit, 50-70 character limit
   - Overview: Click to edit, rich text editor, 500-800 words
   - Highlights: Add/remove/edit bullet points
   - URL slug: Click to edit, auto-formats (lowercase, hyphens)

4. **Regenerate Individual Fields:**
   - Don't like AI-generated content for one field?
   - Click "Regenerate" icon next to field
   - New content generated in 5-10 seconds
   - Can regenerate multiple times until satisfied

5. **Regenerate All Content:**
   - Click "Regenerate All" button
   - All fields regenerated with latest prompts
   - Takes 30-60 seconds
   - Previous content lost (save copy if needed)

**Editing Tips:**
- Edit before submitting for approval (can't edit during approval)
- Maintain SEO best practices (keyword density, readability)
- Stay within character limits (validation prevents saving if exceeded)
- Use spell-check before submitting
- Save frequently (or rely on auto-save)

**Related:** [Content Editing Guide](../03-content-generation/CONTENT_EDITING.md)

---

### Q: How does content generation work for different templates?

**A:** PDP Automation generates unique, tailored content for six content templates, each with its own tone, SEO strategy, and target audience.

**Content Templates:**

**1. Aggregators (24+ property domains)**
- **Tone:** Professional, informative, comprehensive
- **Focus:** Broad market appeal, property features, location benefits
- **Content Style:** Detailed, SEO-optimized for multiple domains
- **SEO Keywords:** "[community] properties," "[developer] Dubai," "off-plan investment"
- **Target Audience:** General property seekers across 24+ aggregator sites
- **Content Variant:** Standard or Luxury

**2. OPR (opr.ae)**
- **Tone:** Professional, informative, analytical
- **Focus:** Investment potential, developer reputation, location analysis
- **Content Style:** Detailed, data-driven, comparative
- **SEO Keywords:** "off-plan Dubai," "[developer] properties," "[community] reviews"
- **Target Audience:** Investors, buyers researching off-plan opportunities

**3. MPP (main-portal.com)**
- **Tone:** Premium, sophisticated, authoritative
- **Focus:** urban, urban convenience, premium features
- **Content Style:** Refined, benefit-oriented, lifestyle-focused
- **SEO Keywords:** "Dubai real estate," "urban living," "premium properties"
- **Target Audience:** Discerning buyers seeking quality urban residences

**4. ADOP (abudhabioffplan.ae)**
- **Tone:** Professional, informative, market-focused
- **Focus:** Abu Dhabi off-plan opportunities, capital city benefits
- **Content Style:** Clear, investment-oriented, location-focused
- **SEO Keywords:** "Abu Dhabi off-plan," "[developer] Abu Dhabi," "capital investment"
- **Target Audience:** Investors and buyers interested in Abu Dhabi market

**5. ADRE (secondary-market-portal.com)**
- **Tone:** Authoritative, comprehensive, market-leading
- **Focus:** Abu Dhabi real estate market, diverse property options
- **Content Style:** Professional, detailed, market-informed
- **SEO Keywords:** "Abu Dhabi real estate," "[community] properties," "UAE capital"
- **Target Audience:** Buyers seeking Abu Dhabi properties across segments

**6. Commercial (cre.main-portal.com)**
- **Tone:** Business-focused, professional, ROI-oriented
- **Focus:** Commercial investment, business potential, tenant appeal
- **Content Style:** Data-driven, investment-focused, professional
- **SEO Keywords:** "commercial real estate Dubai," "office space," "retail investment"
- **Target Audience:** Commercial investors, business owners, corporate tenants

**How Differentiation Works:**
- **Different Prompts:** Each template has custom prompts in Prompt Library
- **Template Variations:** Field mappings and formats customized per template
- **Keyword Optimization:** SEO keywords tailored to template's search strategy
- **Content Length:** Some templates prefer longer/shorter content for specific fields
- **Custom Fields:** Templates can have unique custom fields (e.g., "Investment Rating" for OPR only)
- **Content Variants:** Aggregators template supports Standard and Luxury variants

**Content Generated Per Template:**
- Meta title (unique)
- Meta description (unique)
- H1 headline (unique)
- URL slug (template-specific format)
- Overview/description (completely different content)
- Highlights (prioritized differently per template)
- Custom fields (template-specific)

**Example - Same Project, Different Descriptions:**

**OPR:**
"Beachfront by Emaar presents an exceptional investment opportunity in Dubai Harbour, offering 60/40 payment plans and Q4 2026 handover. Developer reputation and waterfront location position this project as a strong investment choice..."

**MPP:**
"Experience refined coastal living at Beachfront by Emaar in Dubai Harbour. This prestigious development offers premium residences with exceptional amenities, world-class design, and an unrivaled waterfront address..."

**Commercial:**
"Beachfront by Emaar presents prime commercial opportunities in Dubai Harbour. Ground-floor retail and F&B spaces benefit from high foot traffic, waterfront positioning, and proximity to a growing residential community..."

**Related:** [Multi-Template Content Strategy](../03-content-generation/MULTI_TEMPLATE_STRATEGY.md)

---

### Q: What character limits apply to content fields?

**A:** Each content field has specific character limits based on SEO best practices and CMS requirements.

**Standard Field Limits:**

| Field | Minimum | Optimal | Maximum | Hard Limit |
|-------|---------|---------|---------|------------|
| Meta Title | 50 | 55-60 | 60 | 70 |
| Meta Description | 140 | 150-160 | 160 | 170 |
| H1 Headline | 40 | 50-70 | 70 | 80 |
| URL Slug | 20 | 30-50 | 50 | 60 |
| Overview | 400 | 500-800 | 1000 | 1500 |
| Highlight (per bullet) | 30 | 50-100 | 120 | 150 |

**Why These Limits?**

**Meta Title (55-60 characters):**
- Google displays ~60 characters in search results
- Longer titles get truncated with "..."
- Mobile displays ~50 characters

**Meta Description (150-160 characters):**
- Google displays ~160 characters in search results
- Mobile displays ~120 characters
- Longer descriptions get truncated

**H1 Headline (50-70 characters):**
- Should be concise and scannable
- Mobile displays ~50 characters comfortably
- Longer headlines may wrap awkwardly

**URL Slug (30-50 characters):**
- Shorter URLs are more shareable
- Easier to remember and type
- Better for SEO (focused keywords)

**Overview (500-800 words):**
- Sufficient for SEO (500+ words preferred)
- Not too long (user attention span)
- Detailed enough for conversion

**Character Count Display:**
- Real-time character counter shown below each field
- Color coding: Green (optimal), Yellow (acceptable), Red (exceeds limit)
- Validation prevents saving if exceeds hard limit

**Handling Overages:**
- System shows warning if content exceeds optimal length
- Can still save if within hard limit
- QA validation may flag as warning (not failure)
- Trim unnecessary words, use concise language

**Related:** [SEO Content Requirements](../03-content-generation/SEO_GUIDELINES.md)

---

### Q: Can I use custom prompts?

**A:** Custom prompt creation depends on your user role.

**For Regular Users (Content Creators, Marketing Managers, Publishers):**
- Cannot create custom prompts directly
- Use system prompts managed by admins
- Can request custom prompts via support ticket
- Requests evaluated by admin for approval

**For Admins:**
- Full access to Prompt Library
- Can create, edit, version, and test prompts
- Can assign prompts to specific users or projects
- Can A/B test different prompt versions

**How to Request Custom Prompt:**
1. Identify specific need:
   - "I need shorter, punchier meta descriptions"
   - "Content should emphasize eco-friendly features"
   - "Generate content for luxury market (higher-end language)"
2. Provide examples:
   - Show current output vs. desired output
   - Include 2-3 concrete examples
3. Explain use case:
   - For specific website/template
   - For specific developer/project type
   - For specific marketing campaign
4. Submit request:
   - Email admin with details
   - Include project IDs demonstrating issue
   - Specify urgency (standard vs. urgent)

**Admin Prompt Creation Process:**
1. Review request and examples
2. Create draft prompt in Prompt Library
3. Test with sample projects
4. Compare output quality (A/B test)
5. Deploy as new prompt version
6. Monitor performance and iterate

**Prompt Types:**
- **Extraction prompts:** How to pull data from PDFs
- **Classification prompts:** How to categorize images
- **Generation prompts:** How to create content for each field
- **QA prompts:** How to validate content quality

**Best Practice:**
- Provide specific, actionable feedback (not "content is bad")
- Include examples of good vs. bad output
- Be patient - prompt optimization takes time and testing
- Understand that some requests may not be feasible

**Related:** [Prompt Library Guide](../05-projects/PROMPT_LIBRARY.md)

---

### Q: Why does generated content sometimes have placeholders like "[PROJECT NAME]"?

**A:** Placeholder text appears when the AI cannot extract or generate specific information.

**Common Reasons:**

1. **Extraction Failed:**
   - Specific data not found in PDF (e.g., no payment plan mentioned)
   - OCR misread or skipped that section
   - Data formatted in unexpected way

2. **Template Variable Issue:**
   - Prompt template uses variable (e.g., `{{developer}}`)
   - Variable not replaced due to missing extracted data
   - Bug in variable replacement logic (rare)

3. **Generation Error:**
   - AI couldn't generate content for that field
   - Safety filters blocked generated content
   - Timeout during generation

**How to Fix:**

**Immediate Fix:**
1. Review extracted data (Project → Extracted Data tab)
2. If data is there but placeholder remains:
   - Manually edit field and replace placeholder
3. If data is missing:
   - Manually add data to extracted fields
   - Regenerate content for affected field

**Long-Term Fix:**
1. Report pattern to admin (e.g., "Payment plan always shows placeholder")
2. Admin can adjust extraction or generation prompts
3. Re-process project with updated prompts

**Prevention:**
- Use high-quality PDFs with clear, complete information
- Ensure all critical data prominently displayed in brochure
- Review extracted data before generating content
- Always review content preview before submitting

**Related:** [Content Troubleshooting](./TROUBLESHOOTING.md#content-issues)

---

## Workflow Questions

### Q: How long does approval take?

**A:** Approval time depends on Marketing Manager availability and queue depth.

**Service Level Agreement (SLA):**
- **Target:** 24 hours (1 business day)
- **Typical:** 4-6 hours during business hours
- **Urgent:** <2 hours (must be flagged as urgent with justification)

**Factors Affecting Approval Time:**
- Current queue depth (how many projects awaiting approval)
- Time submitted (submitted at 4pm = next morning)
- Project complexity (simple projects approved faster)
- Content quality (well-prepared projects approved faster)
- Marketing Manager workload

**Approval Process:**
1. Submit for Approval (Content Creator) - Instant
2. Notification sent to Marketing Managers - Within 5 seconds
3. Marketing Manager reviews queue - Varies
4. Marketing Manager reviews project - 5-15 minutes per project
5. Approval/rejection decision - Instant
6. Notification sent to Content Creator - Within 5 seconds

**Queue Visibility:**
- Marketing Managers can see queue depth
- Content Creators can't see their position in queue
- Admins can view approval metrics and SLA compliance

**Expediting Approval:**
- Use "Urgent" flag (sparingly, requires justification)
- Ensure content is complete and high-quality (faster review)
- Submit during business hours (9am-5pm GST)
- Contact Marketing Manager directly via Slack (for genuine urgent needs only)

**Approval Metrics (System-Wide Averages):**
- 70% approved within 4 hours
- 90% approved within 24 hours
- 5% require revisions (extended timeline)
- Average review time: 8 minutes per project

**Related:** [Approval Workflow Guide](../06-workflow/APPROVAL_WORKFLOW.md)

---

### Q: What if I need urgent approval?

**A:** For genuinely urgent situations, there are expedited approval options.

**When to Use Urgent Approval:**
- Client deadline within 24 hours
- Website launch scheduled imminently
- Developer requested specific publication date
- Marketing campaign going live soon
- Executive/management request

**When NOT to Use:**
- Poor planning (submitted late)
- Personal convenience
- Routine projects
- More than 25% of your submissions (indicates process issue)

**How to Request Urgent Approval:**

**Option 1: Flag as Urgent (In-System)**
1. Before submitting, toggle "Urgent" flag
2. Select reason from dropdown (required)
3. Add justification note (required): "Client deadline 3pm today, confirmed by [Manager Name]"
4. Submit for approval
5. Urgent projects appear at top of approval queue

**Option 2: Direct Communication**
1. Submit project normally
2. Contact Marketing Manager via Slack/email
3. Provide:
   - Project ID
   - Project name
   - Specific deadline
   - Business justification
   - Link to project
4. Marketing Manager prioritizes accordingly

**Option 3: Escalate to Admin (Emergency Only)**
1. For true emergencies (client escalation, executive request)
2. Contact admin via phone/Slack
3. Admin can reassign to available Marketing Manager
4. Or admin can approve directly (if appropriate)

**Urgent Approval SLA:**
- **Target:** 2 hours
- **Typical:** 30-60 minutes
- **Emergency:** <30 minutes

**Best Practices:**
- Plan ahead - don't rely on urgent approvals regularly
- Prepare high-quality content (urgent doesn't mean low quality accepted)
- Respect Marketing Managers' time
- Provide genuine business justification
- Follow up if no response within SLA

**Consequences of Misuse:**
- Frequent urgent requests may be deprioritized
- Admin may limit urgent flag access
- Impacts team relationships and trust

**Related:** [Urgent Request Guidelines](../06-workflow/URGENT_REQUESTS.md)

---

### Q: Can I skip the approval process?

**A:** No, all projects must go through Marketing Manager approval before publication. This is a non-negotiable quality control step.

**Why Approval is Required:**

1. **Brand Consistency:** Ensures all content aligns with brand voice and standards
2. **Accuracy:** Catches factual errors before publication
3. **SEO Quality:** Verifies content meets SEO requirements
4. **Legal Compliance:** Prevents publication of misleading or non-compliant content
5. **Quality Assurance:** Maintains high standards across all published content

**Who Cannot Skip Approval:**
- Content Creators
- Publishers
- Developers (via API)
- Admins (should follow process too)

**No Exceptions:**
- Not even for "minor updates"
- Not even for "republishing existing content"
- Not even for "urgent client requests"
- Not even for "simple projects"

**Alternative: Fast-Track for Trusted Content:**
- For high-quality, low-risk projects
- Marketing Managers can batch-approve multiple projects at once
- Or use "Quick Approve" feature (faster review, same process)
- Contact Marketing Manager about eligibility

**Rationale:**
- Protects company reputation
- Prevents costly publication errors
- Ensures consistent user experience
- Maintains SEO quality standards
- Required for audit compliance

**If You Regularly Need Faster Approval:**
1. Improve content quality (fewer revisions = faster approval)
2. Build trust with Marketing Managers (proven track record)
3. Submit earlier (more time for review)
4. Use batch submission (multiple projects reviewed together)

**Related:** [Workflow Overview](../06-workflow/WORKFLOW_OVERVIEW.md)

---

### Q: What happens if my project is rejected?

**A:** Project rejection is a normal part of the quality control process. Don't take it personally - it's about ensuring content quality.

**Rejection Process:**

1. **Marketing Manager Reviews Project**
2. **Identifies Issues:**
   - Factual errors (wrong price, developer, location)
   - Content quality (poor writing, missing info)
   - SEO issues (keyword stuffing, poor meta description)
   - Brand voice (doesn't match standards)
3. **Selects "Request Revisions"**
4. **Provides Feedback:**
   - Specific issues identified
   - Clear instructions for fixing
   - Examples of correct approach (if helpful)
5. **You Receive Notification:**
   - Email notification
   - In-app notification with feedback
6. **Project State Changes:**
   - From: PENDING_APPROVAL
   - To: REVISION_REQUESTED

**What You Should Do:**

1. **Read Feedback Carefully:**
   - Understand all issues identified
   - Ask for clarification if anything unclear (via comments)

2. **Make Requested Changes:**
   - Address each issue specifically
   - Don't just fix one and resubmit
   - Verify changes are accurate

3. **Document Changes:**
   - Add comment noting what was changed
   - "Fixed: Updated starting price to AED 1.2M (was 1.1M), revised meta description to include 'Dubai Harbour' keyword"

4. **Resubmit for Approval:**
   - Click "Resubmit for Approval"
   - Project returns to PENDING_APPROVAL state
   - Returns to approval queue (may not be immediate priority)

**Approval History Preserved:**
- All approval requests tracked
- Previous feedback visible in timeline
- Shows response to feedback (important for trust-building)

**Common Rejection Reasons:**

1. **Factual Errors (40% of rejections)**
   - Wrong price, developer, location, handover date
   - Solution: Cross-reference with source PDF

2. **Poor Content Quality (25%)**
   - Generic content, placeholders, grammatical errors
   - Solution: Manually edit and polish content

3. **SEO Issues (20%)**
   - Missing keywords, wrong character count, poor meta description
   - Solution: Follow SEO guidelines, use keyword research

4. **Incomplete Content (15%)**
   - Missing required fields, placeholder text, empty sections
   - Solution: Complete all fields before submitting

**How to Reduce Rejections:**
- Review content preview thoroughly before submitting
- Use QA validation to catch errors early
- Follow content quality guidelines
- Learn from previous rejections (don't repeat mistakes)
- Ask for feedback on draft before formal submission (if possible)

**Rejection Metrics:**
- System average: 15% of submissions require revisions
- Top performers: <5% rejection rate
- After revision: 95% approved on second submission

**Related:** [Handling Revisions Guide](../06-workflow/REVISION_HANDLING.md)

---

### Q: How does the publishing workflow work?

**A:** The publishing workflow tracks the journey from approved content to live webpage.

**Publishing Workflow States:**

**1. APPROVED → PUBLISHING**
- Marketing Manager approves project
- Project moves to Publishing Queue
- Publisher claims/assigned project
- Publisher marks as "Publishing" when starting work

**2. PUBLISHING (Active Work)**
- Publisher accesses approved content and images
- Publisher creates page in CMS (WordPress, Webflow, etc.)
- Publisher follows site-specific checklist:
  - Content added to correct fields
  - Images uploaded and optimized
  - Meta tags configured
  - URL slug set correctly
  - Internal linking added
  - Categories/tags assigned
  - Mobile preview checked
- Publisher saves draft in CMS

**3. PUBLISHING → PUBLISHED**
- Publisher publishes page in CMS
- Publisher copies live page URL
- Publisher returns to PDP Automation
- Publisher marks project as "Published"
- Publisher pastes live page URL
- System sends notification to Content Creator

**4. PUBLISHED → QA_VERIFIED**
- Automated post-publication QA runs (if enabled)
- System fetches live page content
- Compares live content against source content
- Checks:
  - All fields present and match
  - Images display correctly
  - Page loads successfully (<3s)
  - No broken links
  - Mobile-responsive
- If QA passes: Auto-mark as QA_VERIFIED
- If QA fails: Publisher notified to review

**5. QA_VERIFIED → COMPLETE**
- Final validation complete
- Project marked as COMPLETE
- Workflow finished
- Project archived or marked done

**Publishing Dashboard Features:**
- Queue view (all approved projects awaiting publishing)
- Assigned projects (projects assigned to you)
- In-progress projects (currently publishing)
- Completed projects (published this week/month)
- Site-specific filters (filter by target website)

**Template-Specific Checklists:**
Each content template has a custom checklist ensuring proper page creation:

**Aggregators (24+ domains):**
- [ ] Publish to all configured aggregator domains
- [ ] Verify syndication across platforms
- [ ] Check content variant (Standard/Luxury)
- [ ] Confirm images distributed correctly
- [ ] Validate SEO tags per domain

**OPR / MPP / ADOP / ADRE:**
- [ ] Add content to project custom post type
- [ ] Upload images to media library
- [ ] Set featured image
- [ ] Configure meta tags (Yoast SEO)
- [ ] Add to appropriate category
- [ ] Link to developer page
- [ ] Add location map embed
- [ ] Preview on mobile
- [ ] Publish

**Commercial:**
- [ ] Add to commercial listings section
- [ ] Include ROI/yield data if available
- [ ] Tag with property type (retail, office, warehouse)
- [ ] Add tenant appeal section
- [ ] Verify investment metrics displayed

**Publishing Metrics:**
- Average time to publish: 30-45 minutes per project
- SLA: 48 hours from approval to publication
- Typical: 24-36 hours

**Related:** [Publishing Workflow Guide](../06-workflow/PUBLISHING_WORKFLOW.md)

---

## Technical Questions

### Q: Can I access the API?

**A:** Yes, the PDP Automation API is available for developers and integrations.

**Who Can Access:**
- Users with "Developer" role
- Admins
- Approved external systems (via service accounts)

**How to Get Access:**
1. Request Developer role from admin
2. Provide use case justification:
   - What integration are you building?
   - Why API access needed?
   - What endpoints will you use?
3. Admin reviews and approves request
4. Admin assigns Developer role
5. You generate API key in system

**Generating API Key:**
1. Login to PDP Automation
2. Navigate to: Profile → API Keys
3. Click "Generate New API Key"
4. Provide key name (e.g., "CRM Integration")
5. Select permissions scope (read-only, read-write, admin)
6. Click "Generate"
7. **Copy key immediately** (only shown once)
8. Store securely (treat like password)

**API Features:**
- RESTful API design (standard HTTP methods)
- JSON request/response format
- JWT-based authentication
- Rate limiting (300 requests/minute for developers)
- Webhooks (coming in v0.4.0)
- OpenAPI/Swagger documentation

**Common Use Cases:**
- Automated project creation from CRM
- Bulk content export for reporting
- Custom dashboard integrations
- Third-party tool integrations
- CI/CD pipelines

**API Documentation:**
- **Full API Reference:** [/docs/08-api/API_REFERENCE.md](../08-api/API_REFERENCE.md)
- **Developer Guide:** [/docs/08-api/DEVELOPER_GUIDE.md](../08-api/DEVELOPER_GUIDE.md)
- **Authentication Guide:** [/docs/08-api/AUTHENTICATION.md](../08-api/AUTHENTICATION.md)
- **Swagger UI:** https://pdp-automation.example.com/api/docs

**Rate Limits by Role:**
- Developer: 300 requests/minute
- Admin: 300 requests/minute
- Regular Users (via UI): 60 requests/minute

**Best Practices:**
- Use API keys, not personal credentials
- Rotate API keys every 90 days
- Implement exponential backoff for retries
- Cache responses when appropriate
- Monitor rate limit headers
- Handle errors gracefully

**Related:** [API Documentation](../08-api/API_REFERENCE.md)

---

### Q: Are webhooks available?

**A:** Webhooks are coming soon in version 0.4.0 (planned for Q2 2026).

**What are Webhooks?**
Webhooks are HTTP callbacks that send real-time event notifications to your external systems automatically.

**Planned Webhook Events:**
- `project.created` - New project created
- `project.processing_started` - Processing began
- `project.processing_completed` - Processing finished successfully
- `project.processing_failed` - Processing failed with error
- `project.submitted_for_approval` - Submitted for review
- `project.approved` - Approved by Marketing Manager
- `project.revision_requested` - Revisions requested
- `project.published` - Published to website
- `project.qa_verified` - Post-publication QA passed
- `project.completed` - Workflow finished

**How Webhooks Will Work:**
1. Configure webhook endpoint URL in your system
2. Register webhook in PDP Automation (Admin → Webhooks)
3. Select events to subscribe to
4. System sends HTTP POST to your endpoint when events occur
5. Your endpoint receives JSON payload with event data
6. Your endpoint responds with 200 OK to acknowledge

**Example Webhook Payload:**
```json
{
  "event": "project.approved",
  "timestamp": "2026-01-15T14:30:00Z",
  "project_id": "247",
  "project_name": "Dubai Hills Estate",
  "approved_by": "manager@your-domain.com",
  "approved_at": "2026-01-15T14:30:00Z"
}
```

**Use Cases:**
- Notify team via Slack when project approved
- Trigger CI/CD pipeline when content published
- Update CRM when project completed
- Send email notifications via custom service
- Log events to external analytics platform

**Current Workaround (Until Webhooks Available):**
- Poll API periodically (every 5-15 minutes)
- Use API endpoints: `GET /api/projects?status=APPROVED`
- Check for new/updated projects since last poll
- Less efficient than webhooks but functional

**Related:** [Webhook Documentation (Coming Soon)](../08-api/WEBHOOKS.md)

---

### Q: What happens if the system goes down?

**A:** PDP Automation is built on Google Cloud Platform with high availability and automatic recovery.

**System Architecture:**
- **Backend:** Cloud Run (serverless, auto-scales, self-healing)
- **Database:** Neon PostgreSQL (99.95% uptime SLA, automatic failover)
- **Storage:** Google Cloud Storage (99.9% uptime SLA, geo-redundant)
- **Task Queue:** Cloud Tasks (durable, persistent, automatic retry)

**If System Goes Down:**

**1. Active Processing Jobs:**
- Jobs queued in Cloud Tasks (not lost)
- Jobs automatically resume when system recovers
- No data loss - all state saved in database
- May experience delay but will complete successfully

**2. User Sessions:**
- Active sessions preserved in database
- Auto-login when system recovers (if within 24-hour token validity)
- May need to refresh page

**3. Uploaded Files:**
- Files safely stored in Cloud Storage (separate from backend)
- Not affected by backend downtime
- Accessible once system recovers

**4. Notifications:**
- Queued notifications delivered once system recovers
- May experience delay (5-30 minutes typical)

**Recovery Process:**

**Automatic (Most Common):**
1. Cloud Run detects service failure
2. Automatically restarts service (30-60 seconds)
3. Health checks pass
4. Service resumes normal operation
5. Queued jobs resume processing

**Manual (Rare):**
1. Admin receives monitoring alert
2. Admin investigates logs and metrics
3. Admin takes corrective action:
   - Restart service
   - Rollback deployment
   - Scale up resources
   - Fix configuration issue
4. System returns to normal
5. Post-incident review conducted

**Communication During Outage:**
- Status page updated: status.pdp-automation.com (if configured)
- Email sent to all users (for outages >30 minutes)
- In-app banner displayed when system recovers
- Post-incident report shared (for significant outages)

**Typical Recovery Times:**
- Minor issues (service crash): 1-2 minutes
- Database connection issues: 2-5 minutes
- External service outage (Anthropic): Wait for service recovery
- Major incident: 15-60 minutes

**Data Safety:**
- Daily automated backups (30-day retention)
- Point-in-time recovery available (up to 7 days)
- Geo-redundant storage (data replicated across regions)
- Zero data loss in 99.9% of incidents

**What You Should Do:**
1. Wait 5 minutes
2. Refresh page
3. Check status page (if available)
4. Contact admin if down >10 minutes
5. Don't spam support (creates more load)

**Related:** [System Reliability Documentation](../07-admin/RELIABILITY.md)

---

### Q: How do I report a bug?

**A:** Bug reports help improve the system for everyone. Here's how to submit effective bug reports.

**How to Report a Bug:**

**Option 1: In-App Feedback (Recommended)**
1. Click "Help" menu → "Report Bug"
2. Fill out bug report form:
   - What you were doing (step-by-step)
   - What you expected to happen
   - What actually happened
   - Screenshot (auto-captured if available)
   - Browser info (auto-captured)
3. Click "Submit"
4. Receive ticket number for tracking

**Option 2: Email Support**
- To: support@pdp-automation.com
- Subject: "Bug Report: [Brief Description]"
- Include information below

**Option 3: Contact Admin Directly**
- Slack, Teams, or email
- For urgent/critical bugs only
- Include same information as email

**Information to Include:**

**Essential:**
1. **What you were doing (steps to reproduce):**
   ```
   1. Logged in as Content Creator
   2. Opened project #247
   3. Clicked "Edit Content"
   4. Changed meta title
   5. Clicked "Save"
   6. Error appeared
   ```

2. **What happened (actual result):**
   - Exact error message
   - Unexpected behavior
   - Screenshot of issue

3. **What you expected (expected result):**
   - "Content should save successfully"
   - "Page should load without errors"

4. **When it happened:**
   - Date and time
   - First occurrence or recurring?

**Helpful (if available):**
- Project ID (if bug related to specific project)
- Browser and version (Chrome 119, Firefox 120, etc.)
- Operating system (Windows 11, macOS 14, etc.)
- Screenshots or screen recording
- Browser console errors (F12 → Console tab, screenshot any red errors)
- Network errors (F12 → Network tab, look for failed requests)

**Example Bug Report:**

**Subject:** Bug Report: Cannot save edited meta title

**Body:**
```
Description:
When editing meta title for a project, clicking Save shows error message
and content is not saved.

Steps to Reproduce:
1. Login as Content Creator (john@your-domain.com)
2. Navigate to Project #247 (Dubai Hills Estate)
3. Click "Review Content" tab
4. Click meta title field to edit
5. Change title from "Dubai Hills Estate by Emaar" to "Dubai Hills Estate -
   Luxury Living by Emaar"
6. Click "Save" button
7. Error message appears: "Failed to save content"

Expected Result:
Content should save successfully and show confirmation message.

Actual Result:
Error message displayed, content not saved, changes lost.

Environment:
- Browser: Chrome 119.0.6045.199
- OS: Windows 11
- User: john@your-domain.com (Content Creator role)
- Time: 2026-01-15 14:45:00 GST

Screenshots:
[Attached: error-screenshot.png]

Console Errors:
[Attached: console-errors.png]
```

**Bug Severity:**
- **Critical:** System down, data loss, security issue → Report immediately to admin
- **High:** Feature completely broken, affects all users → Report within 1 hour
- **Medium:** Feature partially broken, workaround available → Report within 1 day
- **Low:** Cosmetic issue, minor inconvenience → Report when convenient

**What Happens After Reporting:**
1. Ticket created and assigned ticket number
2. Admin reviews and prioritizes (within 4 hours for critical bugs)
3. Admin investigates and attempts to reproduce
4. Fix implemented and deployed
5. You notified when fix is deployed
6. Admin may ask for additional information

**Follow-Up:**
- Reference ticket number in all communications
- Respond promptly to admin questions
- Test fix when notified and confirm resolved

**Bug Tracking:**
- View your submitted bugs: Profile → My Tickets
- See bug status: Open, In Progress, Resolved, Closed
- Add comments or additional info to existing tickets

**Related:** [Support Documentation](../01-getting-started/SUPPORT.md)

---

## Billing & Cost Questions

### Q: How much does it cost per brochure?

**A:** Processing costs are primarily Anthropic API usage. The average cost is approximately **$0.56 per brochure**.

**Cost Breakdown (Typical 30-page Brochure):**

**Text Extraction:**
- Model: Claude Sonnet 4.5 Vision
- Pages: 30 pages × 1 image per page
- Cost: ~$0.15 (vision API)

**Image Classification:**
- Model: Claude Sonnet 4.5 Vision
- Images: 40 images
- Cost: ~$0.12 (vision API)

**Content Generation:**
- Model: Claude Sonnet 4.5
- Fields: 15-20 fields × 6 templates
- Cost: ~$0.25 (text generation)

**Image Optimization:**
- Service: Google Cloud Functions
- Cost: ~$0.02 (compute + storage)

**Storage:**
- PDF + images stored in GCS
- Cost: ~$0.01/month (storage)

**Total: ~$0.56 per brochure**

**Cost Variations:**

**Small Brochure (15 pages, 20 images):**
- Cost: ~$0.30

**Large Brochure (60 pages, 100 images):**
- Cost: ~$1.20

**Very Large Brochure (100+ pages, 200+ images):**
- Cost: ~$2.50

**Factors Affecting Cost:**
- Page count (more pages = more text extraction)
- Image count (more images = more classification)
- Content regeneration (each regeneration costs extra)
- Multi-template content (6 templates = 6x content generation cost)

**Cost Reduction Features:**

**Response Caching (70-90% savings):**
- Anthropic caches similar prompts automatically
- Repeated content patterns reused across projects
- Example: All projects asking for "Write meta title" with similar data
- Cached requests cost 10% of original cost
- Typical savings: $0.40 per brochure (70% reduction)

**Actual Average Cost (with caching): ~$0.16-$0.30 per brochure**

**Monthly Cost Estimates:**

**Low Volume (10 projects/month):**
- Without caching: $5.60/month
- With caching: $1.60-$3.00/month

**Medium Volume (50 projects/month):**
- Without caching: $28/month
- With caching: $8-$15/month

**High Volume (200 projects/month):**
- Without caching: $112/month
- With caching: $32-$60/month

**Who Pays:**
- Costs billed to company's Anthropic account
- Covered by existing API credits/subscription
- No per-user billing (organizational account)

**Cost Monitoring:**
- Admins can view cost reports: Admin → Analytics → Costs
- Cost breakdown by project, user, time period
- Alerts when approaching budget thresholds

**Related:** [Cost Analysis Guide](../07-admin/COST_ANALYSIS.md)

---

### Q: Can costs be reduced further?

**A:** Yes, beyond response caching, there are several strategies to reduce processing costs.

**Cost Reduction Strategies:**

**1. Optimize PDF Quality (Reduces Cost 10-20%)**
- Use text-based PDFs (not scanned images)
- Compress images before PDF creation
- Remove unnecessary pages (cover pages, contact info)
- Typical savings: $0.05-$0.10 per brochure

**2. Batch Processing (Reduces Cost 5-10%)**
- Process multiple projects from same developer together
- Shared context improves caching effectiveness
- Typical savings: $0.03-$0.06 per brochure

**3. Selective Regeneration (Avoid Waste)**
- Don't regenerate all content repeatedly
- Regenerate only specific fields that need adjustment
- Each full regeneration costs ~$0.20
- Each field regeneration costs ~$0.02

**4. Use Smaller Models for Classification (Coming Soon)**
- Claude Sonnet 4.5-mini for image classification (75% cost reduction)
- Maintains 90%+ accuracy
- Potential savings: $0.08 per brochure

**5. Pre-Extract Developer Data (Reduces Cost 15-25%)**
- Maintain database of known developers, communities
- Skip extraction for known entities
- Focus extraction on unique project details
- Typical savings: $0.08-$0.12 per brochure

**6. Optimize Prompts (Reduces Cost 10-15%)**
- Shorter, more focused prompts
- Reduced output tokens
- Admins continuously optimize prompts
- Typical savings: $0.05-$0.08 per brochure

**7. Use Local Image Processing (Reduces Cost 100% for Images)**
- Replace Anthropic classification with local ML model
- Requires setup and training
- Potential savings: $0.12 per brochure (classification only)

**Cost vs. Quality Trade-offs:**
- Cheaper models = lower accuracy (not recommended for production)
- Shorter prompts = less detailed content (may require manual editing)
- Skipping QA = potential errors published (costly to fix later)

**Recommended Approach:**
1. Enable response caching (already enabled)
2. Optimize PDFs before upload
3. Don't regenerate content unnecessarily
4. Review extracted data before generating content
5. Use batch processing when possible

**Not Recommended:**
- Using cheaper models (GPT-3.5) - accuracy suffers significantly
- Skipping image classification - publishers need organized images
- Reducing content quality - SEO and user experience suffer

**Admin Cost Controls:**
- Set monthly budget limits (alert when approaching)
- Rate limiting prevents cost spikes from abuse
- Cost reporting shows top spenders (identify optimization opportunities)
- Cost analysis by project type (identify expensive patterns)

**Related:** [Cost Optimization Guide](../07-admin/COST_OPTIMIZATION.md)

---

### Q: Who pays for the Anthropic API usage?

**A:** Anthropic API costs are covered by the company's organizational account.

**Billing Structure:**

**Company-Level Billing:**
- Central Anthropic account owned by company
- All projects billed to company account
- Users don't need individual Anthropic accounts
- No per-user charges

**Payment Method:**
- Company credit card on file with Anthropic
- Monthly invoicing
- Costs included in overall API budget

**Budget Allocation:**
- IT/Technology budget
- Marketing operations budget
- Or allocated per department (if tracked)

**Cost Visibility:**

**For Users:**
- No individual cost tracking (users don't see costs)
- Focus on productivity, not cost

**For Admins:**
- Full cost visibility in Admin Dashboard
- Cost reports by user, project, time period
- Can identify high-cost activities
- Can set budget alerts

**For Finance/Management:**
- Monthly cost reports available
- Exportable to CSV/PDF for accounting
- Cost breakdown by department (if configured)

**Typical Organizational Costs:**
- Small team (5 users, 50 projects/month): $15-30/month
- Medium team (15 users, 200 projects/month): $60-120/month
- Large team (30 users, 500 projects/month): $150-300/month

**Cost Control Measures:**
- Rate limiting prevents abuse
- Budget alerts notify admin when approaching limits
- Admin can disable features if needed (e.g., disable regeneration)
- Admins can investigate and address unusual cost spikes

**API Quota:**
- Anthropic account has monthly quota (e.g., $500/month)
- Quota shared across all users
- If quota exceeded, processing paused until next month or quota increased
- Admins receive alerts at 80%, 90%, 100% quota usage

**Cost Justification:**
- Average manual content creation: 2-3 hours/project × $25/hour = $50-75
- PDP Automation: $0.30/project + 15 minutes review = ~$6-7 total cost
- **Savings: $40-70 per project (85-90% cost reduction)**

**Related:** [Budget Management Guide](../07-admin/BUDGET_MANAGEMENT.md)

---

## Integration Questions

### Q: Can I integrate PDP Automation with our CRM?

**A:** Yes, PDP Automation can integrate with CRM systems via the REST API.

**Common CRM Integrations:**
- Salesforce
- HubSpot
- Zoho CRM
- Pipedrive
- Custom in-house CRM

**Integration Use Cases:**

**1. Automatic Project Creation:**
- New property lead enters CRM
- Trigger creates project in PDP Automation
- PDF brochure attached to CRM record is auto-uploaded
- Processing starts automatically

**2. Status Sync:**
- Project status updates in PDP Automation
- Sync status back to CRM deal/opportunity
- CRM shows: "Content in Progress," "Content Approved," "Page Published"

**3. Content Export:**
- Generated content exported to CRM
- Stored in custom fields or notes
- Sales team can access content for client communication

**4. Analytics:**
- Track which projects generated from which CRM opportunities
- Measure conversion rates (CRM lead → published page)

**Integration Methods:**

**Option 1: Direct API Integration**
- Your developers build integration using PDP Automation API
- Custom code (Python, Node.js, etc.)
- Hosted on your infrastructure
- Full control and customization

**Option 2: Zapier/Make (No-Code)**
- Use Zapier or Make.com to connect CRM and PDP Automation
- No coding required
- Pre-built triggers and actions
- Limited customization
- (Requires PDP Automation Zapier integration - coming soon)

**Option 3: Webhooks (Coming in v0.4.0)**
- CRM sends webhook to PDP Automation on new opportunity
- PDP Automation sends webhook to CRM on status changes
- Real-time, event-driven integration
- Most efficient approach

**Example Salesforce Integration Flow:**
1. Sales rep creates Opportunity in Salesforce
2. Brochure PDF attached to Opportunity
3. Salesforce Flow/Process Builder triggers webhook to PDP Automation
4. PDP Automation creates project and processes brochure
5. On completion, PDP Automation sends webhook back to Salesforce
6. Salesforce updates Opportunity with generated content link
7. Sales rep notified content is ready

**API Endpoints for CRM Integration:**
- `POST /api/projects` - Create new project
- `POST /api/projects/{id}/upload` - Upload brochure
- `GET /api/projects/{id}` - Get project status
- `GET /api/projects/{id}/content` - Get generated content
- `PATCH /api/projects/{id}` - Update project metadata

**Authentication:**
- Use service account API key (not personal key)
- Store key securely in CRM or integration platform
- Rotate key every 90 days

**Security Considerations:**
- Don't expose API key in client-side code
- Use HTTPS only
- Implement rate limiting on your side
- Log all API calls for audit

**Getting Started:**
1. Contact admin to request Developer access
2. Generate API key
3. Review API documentation
4. Build proof-of-concept integration
5. Test thoroughly in staging environment
6. Deploy to production with monitoring

**Need Help?**
- API support available from admin
- Example integration code available (Python, Node.js)
- Can schedule integration kickoff call with technical team

**Related:** [API Integration Guide](../08-api/INTEGRATION_GUIDE.md), [CRM Integration Examples](../08-api/CRM_EXAMPLES.md)

---

### Q: Can I export data to Excel or Google Sheets?

**A:** Yes, data can be exported in multiple ways.

**Export Options:**

**1. Project Data Export (CSV/Excel)**
- Navigate to: Project List
- Select projects (or select all)
- Click "Export" button
- Choose format: CSV or Excel
- Download includes:
  - Project ID, name, developer, location
  - Status, created date, updated date
  - Assigned users
  - Processing stats (time, cost)
  - Custom fields

**2. Generated Content Export**
- Navigate to: Project Detail → Content tab
- Click "Export Content" button
- Choose format:
  - **CSV:** All fields in tabular format
  - **JSON:** Structured data (for developers)
  - **Google Sheets:** Direct push to Sheet
- Download or opens Google Sheet

**3. Google Sheets Integration (Built-In)**
- System automatically pushes content to Google Sheets
- Template-based mapping (admin configures)
- Real-time or on-demand push
- Each website has dedicated Sheet template

**4. API Export (Programmatic)**
- Use API to fetch data programmatically
- Export to any format you need
- Automate regular exports (daily, weekly)
- Example: `GET /api/projects?fields=name,developer,content`

**5. Audit Log Export**
- Admins can export audit logs
- CSV format
- Includes all actions with timestamps and users
- For compliance and analysis

**Export Formats:**

**CSV:**
- Universal compatibility
- Importable to Excel, Google Sheets, databases
- Plain text, easy to process

**Excel (.xlsx):**
- Rich formatting
- Multiple sheets (one per website)
- Formulas and styling preserved

**JSON:**
- For developers
- Structured, hierarchical data
- Easy to parse programmatically

**Google Sheets:**
- Live, collaborative document
- Auto-updates when content changes
- Shareable with team

**Common Export Use Cases:**

**Reporting:**
- Export monthly project data for management reports
- Analyze processing times, costs, approval rates
- Identify bottlenecks and optimization opportunities

**Content Management:**
- Export content for review by external stakeholders
- Bulk edit content in Excel, re-import via API
- Maintain content archive

**Analytics:**
- Export data to BI tools (Tableau, Power BI)
- Analyze trends (processing time, approval rates)
- Create custom dashboards

**Backup:**
- Export all data periodically for backup
- Store in separate system for disaster recovery

**Migration:**
- Export data when moving to new system
- Import to other tools or databases

**How to Export Project List to Excel:**
1. Navigate to Project List
2. Apply filters if needed (e.g., last month's projects)
3. Click "Select All" (or select specific projects)
4. Click "Export" button
5. Choose "Excel (.xlsx)"
6. Click "Download"
7. Open in Excel

**How to Export Content to Google Sheets:**
1. Navigate to Project Detail → Content tab
2. Click "Export to Google Sheets"
3. Choose template (or create new Sheet)
4. Click "Push to Sheet"
5. Sheet opens with content populated
6. Share Sheet with team

**Export Limitations:**
- Image galleries not included in CSV/Excel (download ZIP separately)
- Very large exports (1000+ projects) may take time
- Google Sheets has 10 million cell limit (won't be issue for normal use)

**Related:** [Data Export Guide](../05-projects/DATA_EXPORT.md)

---

## Still Have Questions?

**Can't find what you're looking for?**

- **Search Documentation:** Use documentation search feature
- **Troubleshooting Guide:** [/docs/09-reference/TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Glossary:** [/docs/09-reference/GLOSSARY.md](./GLOSSARY.md)
- **User Guide:** [/docs/01-getting-started/USER_GUIDE.md](../01-getting-started/USER_GUIDE.md)

**Contact Support:**
- **Email:** support@pdp-automation.com
- **In-App:** Help menu → Contact Support
- **Admin:** Contact your admin directly (Slack, email)

**Submit Feedback:**
- Help menu → Submit Feedback
- Suggest new features, improvements, or documentation topics

**Training Resources:**
- Video tutorials (coming soon)
- Onboarding guide for new users
- Role-specific training materials

---

**Have a question that should be added to this FAQ?**
Email support@pdp-automation.com with your question and we'll add it in the next update!
