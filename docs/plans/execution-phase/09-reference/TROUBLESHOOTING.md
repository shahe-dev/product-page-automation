# Troubleshooting Guide

Quick solutions to common issues in PDP Automation v.3. If you don't find your issue here, contact your admin or email support@pdp-automation.com.

**Last Updated:** 2026-01-15
**Version:** 0.2.0

---

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Upload & File Issues](#upload--file-issues)
- [Processing Issues](#processing-issues)
- [Content Issues](#content-issues)
- [Authentication & Access Issues](#authentication--access-issues)
- [Workflow Issues](#workflow-issues)
- [Image Issues](#image-issues)
- [Google Sheets Issues](#google-sheets-issues)
- [Performance Issues](#performance-issues)
- [QA & Validation Issues](#qa--validation-issues)
- [System-Wide Issues](#system-wide-issues)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

Before diving into specific issues, try these quick fixes:

1. **Refresh your browser** (Ctrl+R / Cmd+R)
2. **Clear browser cache** (Ctrl+Shift+Delete / Cmd+Shift+Delete)
3. **Log out and log back in** (Forces new session token)
4. **Check your internet connection** (Processing requires stable connection)
5. **Try a different browser** (Chrome and Edge work best)
6. **Disable browser extensions temporarily** (Ad blockers can interfere)

**Still having issues?** Continue to specific sections below.

---

## Upload & File Issues

### 1. PDF Upload Fails with "Invalid File Type"

**Symptoms:**
- Upload button shows error immediately
- Message: "Invalid file type. Only PDF files allowed."
- File appears to be a PDF but won't upload

**Causes:**
- File is not actually a PDF (wrong extension)
- File renamed from another format (.docx, .jpg, .pptx)
- MIME type doesn't match PDF specification
- File corrupted during download or transfer

**Solution:**
1. Right-click file → Properties (Windows) or Get Info (Mac)
2. Verify "Type of file" shows "PDF Document" or "Application/PDF"
3. Try opening file in Adobe Reader or browser
4. If file won't open, it's corrupted - request new copy from source
5. If file opens but won't upload, export as new PDF:
   - Open in Adobe Reader
   - File → Save As → PDF
   - Upload the newly saved file

**Prevention:**
- Always request PDF format from designers (not DOCX/PPTX)
- Don't rename files to change their extension
- Use "Export as PDF" or "Save as PDF" from source application
- Download files completely (don't interrupt downloads)

**Related:** [File Formats Documentation](../01-getting-started/USER_GUIDE.md#supported-file-formats)

---

### 2. Upload Fails with "File Too Large"

**Symptoms:**
- Upload starts but fails at 5-10%
- Message: "File exceeds maximum size of 50MB"
- Progress bar stops and shows error

**Causes:**
- PDF file is larger than 50MB limit
- High-resolution scans or unoptimized images in PDF
- Multiple unnecessary pages included

**Solution:**

**Option A: Compress the PDF**
1. Open PDF in Adobe Acrobat Pro
2. File → Save As Other → Reduced Size PDF
3. Choose "Retain existing" for compatibility
4. Save and upload compressed version

**Option B: Use Online Compression**
1. Visit ilovepdf.com or smallpdf.com
2. Upload PDF and select "Compress PDF"
3. Download compressed version
4. Upload to PDP Automation

**Option C: Request Optimized Version**
1. Contact designer/source
2. Request PDF optimized for web (not print)
3. Ask them to compress images to 150dpi (not 300dpi)

**Prevention:**
- Request "web-optimized" PDFs from designers
- Avoid print-quality PDFs (300dpi) for upload
- Remove unnecessary pages before requesting PDF
- Check file size before requesting brochure creation

**Related:** [PDF Best Practices](../02-processing/PDF_PROCESSING.md#pdf-optimization)

---

### 3. Upload Succeeds but Processing Never Starts

**Symptoms:**
- File uploads to 100% successfully
- Stuck at "Queuing job..." for >2 minutes
- No error message displayed
- Page appears frozen

**Causes:**
- Cloud Tasks queue is full (rare)
- Backend service temporarily down
- Network connection interrupted after upload
- Session expired during upload

**Solution:**
1. Wait 5 minutes (sometimes there's a delay)
2. Refresh the page
3. Check project list - project may have been created
4. If project exists but status is "Pending", wait for processing to start
5. If >10 minutes with no progress, contact admin with:
   - Project ID (if visible)
   - Time of upload
   - File name uploaded

**Admin Solution:**
- Check Cloud Tasks queue depth
- Verify Cloud Run service is running
- Check logs for project ID
- Manually retry job if needed

**Prevention:**
- Don't close browser tab immediately after upload
- Wait for "Processing started" confirmation
- Keep browser tab open during upload
- Use stable internet connection

---

### 4. "Session Expired" Error During Upload

**Symptoms:**
- Upload fails midway with "Session expired"
- Login prompt appears during file upload
- Upload progress resets to 0%

**Causes:**
- Session timeout (24 hours of inactivity)
- Token expired during long upload
- Multiple browser tabs logged in with different accounts

**Solution:**
1. Save your PDF file location (note the path)
2. Click "Login" to re-authenticate
3. After login, return to upload page
4. Upload PDF again (should be quick if cached locally)

**Prevention:**
- Log in fresh before starting large uploads
- Don't leave upload page idle for hours before uploading
- Keep only one browser tab open
- Use "Keep me logged in" option

**Related:** [Authentication Documentation](../01-getting-started/USER_GUIDE.md#authentication)

---

## Processing Issues

### 5. Processing Stuck at "Extracting Images"

**Symptoms:**
- Progress bar stuck at 30-50% for >10 minutes
- "Extracting images from PDF" step showing for extended time
- No error message, just appears frozen

**Causes:**
- PDF contains 200+ high-resolution images (takes time)
- PDF pages are very large (A0 size or 4K scans)
- Image extraction hitting memory limits
- Backend server under heavy load (many jobs running)

**Solution:**

**If <15 minutes:**
1. Be patient - some PDFs genuinely take 10-15 minutes
2. Large brochures (50+ pages, 100+ images) are slower
3. Keep browser tab open and active
4. Don't refresh page (will cancel job)

**If >15 minutes:**
1. Note the project ID from URL
2. Click "Cancel" button if available
3. Wait 2 minutes for cancellation to process
4. Try uploading again
5. If fails again, contact admin with project ID

**Admin Solution:**
- Check Cloud Run logs for project ID
- Look for memory errors or timeouts
- Check if PDF has unusual characteristics (size, page count, image count)
- May need to manually process with increased memory allocation
- Consider splitting PDF if it's unusually large

**Prevention:**
- Request optimized PDFs (not raw scans)
- Compress PDFs before upload if >30MB
- Avoid PDFs with 300+ images
- Upload during off-peak hours if possible

**Related:** [Processing Pipeline Details](../02-processing/PROCESSING_PIPELINE.md)

---

### 6. Processing Fails with "Anthropic API Error"

**Symptoms:**
- Processing fails at extraction or generation step
- Error message mentions "Anthropic API" or "rate limit"
- Multiple projects failing around same time

**Causes:**
- Anthropic API rate limit exceeded (too many requests)
- Anthropic API temporary outage
- API key quota exhausted (monthly limit reached)
- Invalid API response from Anthropic

**Solution:**

**For Users:**
1. Wait 15-30 minutes (rate limits are temporary)
2. Try processing again
3. If still fails, contact admin

**For Admins:**
1. Check Anthropic API dashboard for:
   - Rate limit status
   - Quota remaining
   - Service status
2. If rate limited: wait for limit reset (shown in dashboard)
3. If quota exceeded: upgrade plan or wait for monthly reset
4. If service outage: monitor Anthropic status page
5. Check logs for specific error code

**Prevention:**
- Admins: Monitor API usage and set up alerts at 80% quota
- Admins: Enable rate limit warnings in system
- Users: Don't submit many projects simultaneously
- Users: Avoid regenerating content repeatedly

**Related:** [Anthropic API Integration](../08-api/ANTHROPIC_API_INTEGRATION.md)

---

### 7. Processing Fails with "Encrypted PDF Not Supported"

**Symptoms:**
- Processing fails immediately (within 30 seconds)
- Error: "PDF is encrypted or password-protected"
- File opens fine in PDF reader

**Causes:**
- PDF has security restrictions enabled
- Password protection (even if no password required to open)
- Digital Rights Management (DRM) applied
- PDF saved with encryption for security

**Solution:**

**Option A: Remove Encryption in Adobe Acrobat**
1. Open PDF in Adobe Acrobat Pro
2. File → Properties → Security tab
3. Security Method → Change to "No Security"
4. Save PDF
5. Upload unencrypted version

**Option B: Print to PDF**
1. Open PDF in any PDF reader
2. File → Print
3. Select "Microsoft Print to PDF" (Windows) or "Save as PDF" (Mac)
4. Save new PDF
5. Upload unencrypted version

**Option C: Use Online Tools**
1. Visit ilovepdf.com/unlock-pdf
2. Upload encrypted PDF
3. Download unlocked version
4. Upload to PDP Automation

**Prevention:**
- Request unencrypted PDFs from designers
- Check PDF properties before requesting processing
- Save PDFs without security settings
- Avoid PDFs downloaded from secure portals (they're often encrypted)

---

### 8. Processing Completes but No Content Generated

**Symptoms:**
- Processing shows 100% complete
- Images extracted successfully
- Content fields are empty or show "No content generated"
- No error message displayed

**Causes:**
- Text extraction found insufficient data
- PDF contains only images (no readable text)
- LLM failed to generate content (rare)
- Content filtered by Anthropic safety systems (inappropriate content)

**Solution:**
1. Check extraction results:
   - Project detail page → Extracted Data tab
   - Verify if any text was extracted
2. If no text extracted:
   - PDF may be scanned images with no text layer
   - Request PDF with text layer (not just scanned images)
3. If text extracted but content empty:
   - Try regenerating content manually
   - Click "Regenerate All Content" button
4. If still fails, contact admin with project ID

**Admin Solution:**
- Review Anthropic API logs for content generation requests
- Check if content was filtered for safety reasons
- Verify prompt library is accessible
- Test prompt manually with extracted data
- May need to adjust prompts or use different model

**Prevention:**
- Use PDFs with text layer (not just image scans)
- Ensure brochure contains sufficient project information
- Avoid brochures that are purely visual (infographics only)

**Related:** [Content Generation Details](../03-content-generation/CONTENT_GENERATION.md)

---

## Content Issues

### 9. Generated Content is Inaccurate

**Symptoms:**
- Wrong developer name extracted
- Incorrect starting price (off by 10x or completely wrong)
- Missing amenities that are clearly in brochure
- Wrong location or community name
- Hallucinated information not in PDF

**Causes:**
- PDF text is formatted oddly (OCR confusion)
- Numbers formatted ambiguously (1.2M vs 12M vs 1,200,000)
- LLM misinterpreted extracted text
- Poor quality PDF with unclear text
- LLM hallucinated based on similar projects

**Solution:**

**For Critical Fields (Price, Developer, Location):**
1. Review content preview carefully before submitting
2. Compare generated content against source PDF page-by-page
3. Manually edit incorrect fields:
   - Click field to edit
   - Enter correct information
   - Save changes
4. Document corrections for audit trail

**For Content Fields (Descriptions, Highlights):**
1. Click "Regenerate" button for specific field
2. Try 2-3 times (each generation is slightly different)
3. If still inaccurate, manually edit
4. Consider adding source text as reference for regeneration

**For Systematic Issues (Always Gets Developer Wrong):**
1. Contact admin - may be prompt issue
2. Provide project IDs of affected projects
3. Admin can adjust prompts to improve accuracy

**Prevention:**
- Use high-quality PDFs with clear, readable text
- Ensure critical information (price, developer) is prominently displayed
- Review and validate all content before submitting for approval
- Set up QA checkpoint to catch common errors
- Report patterns of errors to admin for prompt improvements

**Related:** [Content Quality Guidelines](../03-content-generation/CONTENT_QUALITY.md)

---

### 10. Content Doesn't Meet Character Limits

**Symptoms:**
- Meta title is 75 characters (should be 55-60)
- Meta description is 200 characters (should be 150-160)
- Overview is only 300 words (should be 500-800)
- QA validation fails due to length issues

**Causes:**
- Prompt doesn't enforce strict length limits
- LLM interpretation of "approximately X characters"
- Different counting methods (with/without spaces)
- Content naturally shorter/longer due to project details

**Solution:**

**For Too Long:**
1. Manually trim content in preview editor
2. Focus on removing filler words and redundancy
3. Keep core information and keywords
4. Save edited version

**For Too Short:**
1. Click "Regenerate" and specify longer length in custom instruction
2. Manually expand content with additional details from PDF
3. Add relevant keywords for SEO
4. Save edited version

**For Systematic Issues:**
1. Report to admin - prompt may need adjustment
2. Provide examples of affected fields
3. Admin can update prompts to enforce strict limits

**Prevention:**
- Check content preview for character counts (shown below each field)
- Use QA validation to catch length issues before submission
- Set up custom validation rules for your requirements
- Report consistent length issues to admin

**Related:** [SEO Content Requirements](../03-content-generation/SEO_GUIDELINES.md)

---

### 11. Content Contains Inappropriate or Placeholder Text

**Symptoms:**
- Content includes "[PROJECT NAME]" or "[DEVELOPER]" placeholders
- Generic text like "This beautiful project offers amazing amenities"
- Contains errors like "undefined" or "null"
- Repetitive or nonsensical text

**Causes:**
- LLM couldn't extract specific information
- Prompt template variables not properly replaced
- Extraction failed for certain fields
- Bug in content generation pipeline

**Solution:**
1. **Immediate fix:** Manually replace all placeholders with correct information
2. **Root cause:** Check extracted data tab to verify what was extracted
3. **If extraction empty:** Re-upload PDF or adjust extraction parameters
4. **If extraction correct but content wrong:** Contact admin - likely prompt bug

**Admin Solution:**
- Review prompt templates for variable replacement issues
- Check logs for content generation errors
- Test prompt with same extracted data manually
- Fix template variables or prompt logic
- Re-process affected projects if needed

**Prevention:**
- Review content preview before submitting
- Set up QA validation to detect placeholder text
- Report placeholder patterns to admin immediately
- Don't submit projects with obvious placeholders

---

## Authentication & Access Issues

### 12. Can't Login - "Domain Not Allowed"

**Symptoms:**
- Google OAuth login fails
- Error: "Email domain not allowed" or "Access restricted"
- Successfully authenticate with Google but blocked from app
- Redirected back to login page after OAuth

**Causes:**
- Email address is not @your-domain.com domain
- System configured to only allow company emails
- Using personal Gmail account instead of work account

**Solution:**

**For Users:**
1. Verify you're using your @your-domain.com email address
2. Log out of all Google accounts in browser
3. Clear browser cookies for google.com
4. Try login again, selecting correct @your-domain.com account
5. If you need access with different domain, contact admin

**For Admins:**
1. Navigate to Admin → Settings → Authentication
2. View allowed email domains list
3. Add domain to whitelist if approved by management
4. Requires system config change and restart
5. Document approved domain in security policy

**Prevention:**
- Always use company email (@your-domain.com) for work applications
- Bookmark login URL to avoid using personal accounts
- Keep work and personal Google accounts separate in browser

**Related:** [Authentication Setup](../01-getting-started/USER_GUIDE.md#authentication)

---

### 13. "Insufficient Permissions" Error

**Symptoms:**
- Can log in successfully
- Can view projects but can't upload/edit/approve
- Error: "You don't have permission to perform this action"
- Buttons disabled or hidden

**Causes:**
- User role doesn't have required permissions
- Assigned wrong role (e.g., Publisher role but need Content Creator)
- Role permissions changed by admin
- Trying to access admin-only features

**Solution:**

**For Users:**
1. Check your role: Profile menu → Account Settings → Role
2. Review role permissions: Help → User Roles Documentation
3. If role is incorrect, contact admin to update
4. Provide reason for role change request

**For Admins:**
1. Navigate to Admin → User Management
2. Find user in list
3. Check current role assignment
4. Update role if appropriate (get approval first)
5. User must log out and back in for changes to take effect

**Role Permissions Summary:**
- **Content Creator:** Upload, edit, submit for approval
- **Marketing Manager:** Approve/reject projects, view analytics
- **Publisher:** Mark as published, access publishing workflow
- **Admin:** Full system access, user management, settings

**Prevention:**
- Request appropriate role during onboarding
- Understand role permissions before requesting actions
- Don't share accounts (each user should have own access)

**Related:** [Role-Based Access Control](../07-admin/USER_MANAGEMENT.md#roles)

---

## Workflow Issues

### 14. Approval Queue is Empty But Notifications Show Pending

**Symptoms:**
- Notification bell shows "3 pending approvals"
- Click notification to view approvals
- Approval queue page shows no items
- Counter doesn't match displayed items

**Causes:**
- Notifications not marked as read
- Browser cache showing stale data
- Projects were approved/rejected by another manager
- Database sync delay (rare)

**Solution:**
1. Refresh page (Ctrl+R / Cmd+R)
2. Clear browser cache (Ctrl+Shift+Delete)
3. Click notification bell → "Mark all as read"
4. Log out and log back in
5. If counter still wrong after 5 minutes, contact admin

**Admin Solution:**
- Check database for projects in PENDING_APPROVAL state
- Verify notification records match project states
- Run notification cleanup script to remove stale notifications
- Check for database replication lag (if using read replicas)

**Prevention:**
- Regularly mark notifications as read
- Refresh approval queue page before starting reviews
- Don't keep multiple tabs open with same page

**Related:** [Notifications System](../06-workflow/NOTIFICATIONS.md)

---

### 15. Can't Submit Project for Approval

**Symptoms:**
- "Submit for Approval" button is grayed out/disabled
- No error message when clicking button
- Button shows loading spinner but nothing happens
- Form validation errors not displayed

**Causes:**
- Required fields are empty or invalid
- Content doesn't pass validation rules
- Project already submitted (state is PENDING_APPROVAL)
- Session expired
- Network connection issue

**Solution:**
1. Check for validation errors:
   - Scroll through all content fields
   - Look for red error messages or highlighted fields
   - Ensure all required fields have content
2. Verify project state:
   - Check status badge at top of page
   - If already "Pending Approval", can't resubmit
3. Try refreshing content preview
4. Log out and back in (refreshes session)
5. If still fails, contact admin with project ID

**Common Validation Issues:**
- Meta title exceeds 60 characters
- Meta description exceeds 160 characters
- Missing required fields (developer, location, price)
- Invalid URL slug (contains special characters)

**Prevention:**
- Review all validation errors before submitting
- Use content preview to verify all fields populated
- Check character counts for length-limited fields
- Save draft frequently to preserve work

**Related:** [Approval Workflow Guide](../06-workflow/APPROVAL_WORKFLOW.md)

---

### 16. Project Stuck in "Publishing" State for Days

**Symptoms:**
- Project approved 3+ days ago
- State still shows "Publishing"
- No updates from publisher
- Can't contact assigned publisher

**Causes:**
- Publisher hasn't started work yet
- Publisher encountered blocker (missing content, unclear requirements)
- Publisher forgot to update status
- High publishing queue volume

**Solution:**

**For Content Creators:**
1. Check project comments for publisher updates
2. Add comment asking for status update
3. Contact publisher directly via Slack/email (if known)
4. If >5 days with no response, escalate to admin

**For Admins:**
1. View Publishing Dashboard → Sort by oldest first
2. Identify stuck projects
3. Contact assigned publisher for status
4. Reassign to different publisher if needed
5. Update project status based on actual progress

**For Publishers:**
1. Update project status regularly (daily if actively working)
2. Add comments if blocked or delayed
3. Use "Request Clarification" feature if content unclear
4. Mark as published promptly once page is live

**Prevention:**
- Publishers: Set realistic timelines and communicate delays
- Admins: Monitor publishing SLA (target: 48 hours from approval)
- Content Creators: Provide clear, complete content
- Set up automated reminders for projects in Publishing >3 days

**Related:** [Publishing Workflow Guide](../06-workflow/PUBLISHING_WORKFLOW.md)

---

## Image Issues

### 17. Images Not Categorized Correctly

**Symptoms:**
- Interior images classified as exterior
- Amenity images labeled as interior
- Logo images missing from logo folder
- Floor plans not detected

**Causes:**
- Anthropic Vision misclassification (rare but possible)
- Image quality too low (blurry, pixelated)
- Heavy watermark covering entire image (confuses AI)
- Unusual camera angle or composition
- Image is ambiguous (could be multiple categories)

**Solution:**

**If Few Images Misclassified (1-3 images):**
1. Note incorrect images
2. Manually reorganize in downloaded ZIP:
   - Extract ZIP file
   - Move images to correct folders
   - Re-zip with corrected structure
3. Upload corrected ZIP if needed for publishing

**If Many Images Misclassified (10+ images):**
1. Contact admin with project ID
2. Provide specific examples:
   - "Image #12 is swimming pool (amenity) but classified as exterior"
3. Admin can re-process with adjusted classification prompts
4. May indicate systematic issue requiring prompt update

**Admin Solution:**
- Review classification prompts in Prompt Library
- Check classification accuracy metrics across projects
- Test problematic images manually with current prompt
- Adjust prompt if systematic issue identified
- Re-process affected projects with updated prompt

**Prevention:**
- Use high-quality images in PDFs (not compressed/blurry)
- Avoid heavy watermarks that obscure image content
- Use clear, well-lit images
- Report systematic misclassification patterns to admin

**Related:** [Image Classification Details](../02-processing/IMAGE_CLASSIFICATION.md)

---

### 18. Downloaded ZIP is Missing Images

**Symptoms:**
- ZIP file downloads successfully
- Extract ZIP but folders have fewer images than expected
- Specific image types missing entirely (e.g., no logos)
- Image count in ZIP doesn't match project gallery

**Causes:**
- Images filtered out as duplicates
- Images failed optimization step
- Images too small (below minimum size threshold)
- Corrupted images in source PDF
- ZIP generation failed partially

**Solution:**
1. Compare ZIP contents with project image gallery:
   - Count images in each category on website
   - Count images in each ZIP folder
   - Identify which images are missing
2. Check if missing images are:
   - Very small (thumbnails <100px)
   - Duplicates of other images
   - Logos that were detected as watermarks
3. If critical images missing:
   - Contact admin with project ID
   - Specify which images are missing (provide page numbers from PDF)
   - Admin can manually re-extract specific images

**Admin Solution:**
- Review processing logs for image extraction errors
- Check optimization step logs for failures
- Verify minimum image size thresholds are appropriate
- Manually extract missing images from source PDF if needed
- Re-generate ZIP with all images

**Prevention:**
- Review image gallery before downloading ZIP
- Verify image counts match expectations
- Download ZIP immediately after processing (don't wait weeks)
- Report missing images promptly for faster resolution

---

### 19. Images Have Wrong Orientation (Rotated)

**Symptoms:**
- Floor plans displayed sideways or upside down
- Portrait images rotated to landscape
- Downloaded images rotated differently than in gallery

**Causes:**
- PDF stores rotation metadata (not actual rotation)
- EXIF orientation flag set incorrectly
- Browser displays rotation but file doesn't have it
- Automatic rotation based on image content

**Solution:**

**For Floor Plans:**
1. Floor plans should auto-rotate to portrait (current feature)
2. If not rotating correctly, contact admin with project ID
3. Admin can adjust auto-rotation logic

**For Other Images:**
1. Download images from ZIP
2. Manually rotate using image editor (Paint, Photoshop, Preview)
3. Save rotated versions
4. Use corrected images for publishing

**Admin Solution:**
- Check image processing logs for rotation metadata
- Verify EXIF orientation handling in optimization pipeline
- May need to adjust image extraction to respect/ignore EXIF
- Re-process project with corrected orientation settings

**Prevention:**
- Request PDFs with correctly oriented images
- Check image orientation in project gallery before downloading
- Report systematic orientation issues to admin

**Related:** [Image Optimization Pipeline](../02-processing/IMAGE_OPTIMIZATION.md)

---

## Google Sheets Issues

### 20. Google Sheet Not Populating

**Symptoms:**
- Job completes successfully (100%)
- Click Sheet URL - Sheet loads but cells are blank/empty
- No error message displayed
- Sheet template structure looks correct

**Causes:**
- Template field mapping incorrect (fields don't match Sheet structure)
- Google Sheets API rate limit hit (temporary)
- Permission issue (service account can't write to Sheet)
- Sheet URL changed after template setup
- Network timeout during Sheets push

**Solution:**

**For Users:**
1. Verify Sheet URL is correct (check with team)
2. Wait 5 minutes and reload Sheet (sometimes delay)
3. Check if partial data populated (indicates mapping issue)
4. Contact admin with:
   - Project ID
   - Sheet URL
   - Which fields are missing

**For Admins:**
1. Check Admin → Templates → [Website Name]
2. Verify field mappings match current Sheet structure
3. Check Google Sheets API quota in Google Cloud Console:
   - Navigate to APIs & Services → Dashboard
   - Find Sheets API
   - Check quota usage and limits
4. Test Sheet write permissions:
   - Admin → Tools → Test Sheet Connection
   - Enter Sheet URL and test write
5. Review logs for Sheets API errors
6. If mapping incorrect, update template and re-push content

**Permission Fix:**
1. Open Google Sheet
2. Click "Share" button
3. Add service account email with "Editor" access:
   - `pdp-automation@PROJECT_ID.iam.gserviceaccount.com`
4. Save permissions
5. Re-push content from project

**Prevention:**
- Don't change Sheet URLs after template setup
- Keep Sheet structure consistent (don't rename columns)
- Admins: Monitor Sheets API quota usage
- Admins: Set up alerts for quota usage >80%
- Test new templates thoroughly before production use

**Related:** [Google Sheets Integration](../05-integrations/GOOGLE_SHEETS.md)

---

### 21. Sheet Populated But Content Formatting is Wrong

**Symptoms:**
- Content successfully pushed to Sheet
- Formatting looks wrong (no bold, no bullets, extra spaces)
- Numbers formatted as text instead of numbers
- Dates display as serial numbers (e.g., 45123)

**Causes:**
- Sheet template doesn't specify cell formatting
- Rich text not supported in target cells
- Bullet points lost during conversion
- Number/date format not applied to cells

**Solution:**

**For Users:**
1. Manually reformat affected cells in Google Sheet:
   - Select cells → Format menu → Apply formatting
2. Use Find & Replace for bulk fixes:
   - Edit → Find and replace
   - Replace formatting issues (e.g., double spaces)
3. Note formatting issues and report to admin

**For Admins:**
1. Update template to include formatting rules:
   - Admin → Templates → [Website] → Advanced Settings
   - Add cell formatting specifications
2. Test formatting with sample data
3. Re-push content to verify formatting
4. Document formatting requirements in template notes

**Formatting Tips:**
- **Bullet points:** Use • character or numbered lists
- **Bold text:** Not supported in basic Sheets push (use formatting rules)
- **Numbers:** Template should specify number format (currency, decimal places)
- **Dates:** Use date format (MM/DD/YYYY or DD/MM/YYYY) in template

**Prevention:**
- Set up Sheet templates with pre-formatted cells
- Use data validation for number/date fields
- Test templates with sample data before production
- Document formatting expectations in template

---

## Performance Issues

### 22. Website is Slow or Unresponsive

**Symptoms:**
- Pages take 5+ seconds to load
- Buttons don't respond when clicked
- Browser tab freezes or shows "Not Responding"
- Spinning loader doesn't stop

**Causes:**
- High server load (many users processing simultaneously)
- Large project list loading (200+ projects)
- Browser running out of memory
- Network connection slow
- Backend service scaling up (cold start)

**Solution:**

**Immediate Fixes:**
1. Close unnecessary browser tabs
2. Refresh page (Ctrl+R / Cmd+R)
3. Clear browser cache and reload
4. Try in incognito/private window
5. Check your internet speed (speedtest.net)

**For Slow Project List:**
1. Use filters to reduce displayed projects
2. Adjust pagination (show 25 instead of 100 per page)
3. Search for specific project instead of browsing all

**For Slow Processing:**
1. Upload during off-peak hours (early morning, late evening)
2. Process smaller PDFs first
3. Wait for current jobs to complete before starting new ones

**Admin Solution:**
- Check Cloud Run metrics for CPU/memory usage
- Verify auto-scaling is working (should scale up during load)
- Review database query performance (slow queries)
- Check Cloud Tasks queue depth
- May need to increase minimum instance count
- Optimize database indexes for common queries

**Prevention:**
- Close browser tabs you're not actively using
- Don't load all projects at once (use filters)
- Process PDFs one at a time (not batch uploads)
- Use fast, stable internet connection
- Keep browser updated to latest version

**Related:** [Performance Optimization](../07-admin/PERFORMANCE_TUNING.md)

---

### 23. Browser Crashes When Viewing Large Image Galleries

**Symptoms:**
- Click "View Images" on project with 200+ images
- Browser tab freezes or crashes
- "Aw, Snap!" error in Chrome
- "Page Unresponsive" warning

**Causes:**
- Too many high-resolution images loading at once
- Browser running out of memory
- Image gallery not using lazy loading
- Thumbnail generation failed

**Solution:**

**Immediate Fix:**
1. Don't view all images at once
2. Use category filters (view only "Interior" first)
3. Download ZIP instead of viewing in browser
4. View images in smaller batches (25 at a time)

**For Admins:**
1. Implement lazy loading for image gallery
2. Generate smaller thumbnails for gallery view
3. Add pagination to image gallery (25/50/100 per page)
4. Optimize thumbnail size (max 300px width)

**Prevention:**
- For projects with 100+ images, download ZIP instead of browsing
- Use filters to view images by category
- Close other tabs before viewing large galleries
- Use a computer with sufficient RAM (8GB minimum)

---

## QA & Validation Issues

### 24. QA Validation Always Fails

**Symptoms:**
- QA checkpoint fails every time
- Even correct content shows as "QA Failed"
- Can't progress to next workflow stage
- Error message unclear about what's wrong

**Causes:**
- QA validation rules too strict
- Expected format doesn't match generated format
- Minor formatting differences (spaces, punctuation)
- Date/number format variations
- Bug in QA validation logic

**Solution:**

**For Users:**
1. Click "View QA Details" to see comparison:
   - What was expected
   - What was found
   - Difference highlighted
2. Determine if difference is significant:
   - Minor formatting (spaces, commas) → Override
   - Actual content difference (wrong price) → Fix content
3. If minor difference, click "Override QA" with justification:
   - "Date format variation (Q4 2026 vs December 2026)"
   - "Currency formatting difference (AED 1.2M vs AED 1,200,000)"
4. If content actually wrong, fix and re-validate

**For Admins:**
1. Review QA validation rules in Admin → QA Settings
2. Check if rules are too strict (exact match vs. fuzzy match)
3. Adjust tolerance for common variations:
   - Date formats (multiple formats acceptable)
   - Number formats (handle M, K, B suffixes)
   - Text formatting (ignore extra spaces)
4. Test validation rules with sample data
5. Update rules and notify users of changes

**Prevention:**
- Set up realistic QA validation rules
- Use fuzzy matching for text fields (85% similarity threshold)
- Document acceptable variations in QA rules
- Allow users to override minor QA failures with justification
- Review QA override patterns to improve rules

**Related:** [QA Module Documentation](../04-qa/QA_SYSTEM.md)

---

### 25. Post-Publication QA Shows False Positives

**Symptoms:**
- QA compares live page to generated content
- Flags differences that don't exist
- Shows content as "different" when it's identical
- False positives for every project

**Causes:**
- Web scraper not extracting content correctly
- Live page has additional formatting (HTML tags)
- Page uses dynamic content (JavaScript)
- Timing issue (scraping before page fully loads)

**Solution:**

**For Users:**
1. Manually verify flagged differences:
   - Open live page
   - Compare flagged content yourself
   - If identical, override QA
2. Use "Override with Verification" feature:
   - Take screenshot of live page
   - Attach screenshot with override
   - Provide justification

**For Admins:**
1. Review web scraping logic in QA module
2. Check if scraper waits for page load
3. Verify CSS selectors for content extraction
4. Test scraper against live pages manually
5. Adjust comparison logic (ignore HTML tags, extra whitespace)
6. May need to use headless browser for JavaScript-heavy pages

**Prevention:**
- Configure QA scraper for each website's structure
- Test post-publication QA before enabling for all projects
- Document known false positive patterns
- Provide clear override guidelines for publishers

---

## System-Wide Issues

### 26. "Service Unavailable" or 503 Errors

**Symptoms:**
- Website shows "503 Service Unavailable"
- Can't access any pages
- Error appears for all users
- Started suddenly without warning

**Causes:**
- Backend service crashed or restarting
- Cloud Run scaling down to zero (cold start)
- Database connection failure
- Deployment in progress
- Cloud platform outage (rare)

**Solution:**

**For Users:**
1. Wait 2-3 minutes (service may be auto-restarting)
2. Refresh page after waiting
3. Try again in 5 minutes if still down
4. Check status page (if available): status.pdp-automation.com
5. Contact admin if down >10 minutes

**For Admins:**
1. Check Cloud Run service status in Google Cloud Console
2. View recent logs for errors or crashes
3. Check database connection status
4. Verify Cloud Run minimum instances setting
5. Review recent deployments (rollback if needed)
6. Check Google Cloud Status Dashboard for platform issues
7. Manually restart service if needed

**Prevention:**
- Set Cloud Run minimum instances to 1 (prevents cold starts)
- Configure health check endpoints
- Set up monitoring and alerts for service downtime
- Implement graceful degradation for database failures
- Document incident response procedures

**Related:** [Admin Operations Guide](../07-admin/OPERATIONS.md)

---

### 27. All Processing Jobs Failing

**Symptoms:**
- Every new upload fails to process
- Multiple users reporting same issue
- Jobs fail at same step (e.g., extraction)
- Error messages mention external service

**Causes:**
- Anthropic API outage or rate limit hit
- Google Cloud Storage permission issue
- Database connection failure
- Cloud Tasks queue backed up
- API key expired or invalidated

**Solution:**

**For Admins Only:**
1. Check Anthropic API status: status.anthropic.com
2. Verify API key is valid:
   - Admin → Settings → API Keys
   - Test Anthropic connection
3. Check Google Cloud Storage:
   - Verify bucket permissions
   - Test upload/download manually
4. Review Cloud Tasks queue:
   - Check queue depth
   - Look for stuck tasks
5. Check database connection:
   - Test database connectivity
   - Verify connection pool not exhausted
6. Review service logs for specific errors
7. Post system status update for users

**Communication:**
1. Post incident notice on dashboard
2. Email all users about issue and ETA for fix
3. Provide updates every 30-60 minutes
4. Post resolution notice when fixed

**Prevention:**
- Monitor external service status proactively
- Set up alerts for API quota usage
- Implement retry logic with exponential backoff
- Maintain backup API keys
- Document troubleshooting procedures

---

## Getting Help

### When to Contact Admin

Contact your admin if:
- Issue persists after trying solutions in this guide
- Multiple users experiencing same issue
- Data appears lost or corrupted
- System error messages mentioning "database" or "server"
- Security concerns (unauthorized access, data breach)

### What to Include in Support Request

**Essential Information:**
1. **Your Details:**
   - Name and email
   - User role
   - Browser and version (Chrome 119, Firefox 120, etc.)

2. **Issue Details:**
   - What were you doing? (step-by-step)
   - What happened? (specific error message)
   - When did it happen? (date and time)
   - How many times? (one-time or recurring)

3. **Project Information (if applicable):**
   - Project ID
   - Project name
   - PDF file name
   - Processing step where it failed

4. **Screenshots:**
   - Error message screenshot
   - Browser console errors (F12 → Console tab)
   - Network errors (F12 → Network tab)

**Example Good Support Request:**
```
Subject: Processing stuck at extraction - Project #247

Hi Admin,

I'm unable to complete processing for Project #247 (Dubai Hills Estate).

What I did:
1. Uploaded PDF "DHE_Brochure_Final.pdf" (32MB)
2. Processing started successfully
3. Got stuck at "Extracting images" step (45% progress)
4. Waited 20 minutes - no progress
5. Cancelled and retried - same result

Error Details:
- Project ID: 247
- Time: 2026-01-15 14:30 UTC
- Browser: Chrome 119 on Windows 11
- Screenshot attached showing stuck progress

This is urgent as marketing needs this by end of day.

Thanks,
[Your Name]
```

### Escalation Path

1. **Level 1:** Try solutions in this troubleshooting guide (5-10 minutes)
2. **Level 2:** Contact your team lead or experienced colleague (15 minutes)
3. **Level 3:** Submit support request to admin (email or internal system)
4. **Level 4:** Admin escalates to technical team if needed
5. **Level 5:** Emergency support for critical production issues (call admin directly)

### Emergency Contact

**For Critical Issues Only:**
- System completely down (affects all users)
- Data breach or security incident
- Data loss or corruption
- API credentials compromised

Contact: [Admin Emergency Phone/Email]

---

## Additional Resources

- **User Guide:** [/docs/01-getting-started/USER_GUIDE.md](../01-getting-started/USER_GUIDE.md)
- **FAQ:** [/docs/09-reference/FAQ.md](./FAQ.md)
- **Glossary:** [/docs/09-reference/GLOSSARY.md](./GLOSSARY.md)
- **API Documentation:** [/docs/08-api/API_REFERENCE.md](../08-api/API_REFERENCE.md)
- **Changelog:** [/docs/09-reference/CHANGELOG.md](./CHANGELOG.md)

---

**Still need help?** Email support@pdp-automation.com with detailed description of your issue.

**Found a solution not listed here?** Please share it with the team so we can update this guide!
