# Agent Brief: DEV-UPLOAD-001

**Agent ID:** DEV-UPLOAD-001
**Agent Name:** Upload UI Agent
**Type:** Development
**Phase:** 4 - Frontend
**Context Budget:** 55,000 tokens

---

## Mission

Implement file upload interface with drag-and-drop, progress tracking, and job status monitoring.

---

## Documentation to Read

### Primary
1. `docs/03-frontend/PAGE_SPECIFICATIONS.md` - Upload/Processing page
2. `docs/08-user-guides/CONTENT_CREATOR_GUIDE.md` - Upload workflow

### Secondary
1. `docs/04-backend/API_ENDPOINTS.md` - Upload API
2. `docs/02-modules/MATERIAL_PREPARATION.md` - Processing steps

---

## Dependencies

**Upstream:** DEV-FESETUP-001, DEV-AUTHUI-001
**Downstream:** DEV-PROJDETAIL-001

---

## Outputs

### `frontend/src/pages/ProcessingPage.tsx`
### `frontend/src/components/upload/FileUpload.tsx`
### `frontend/src/components/upload/ProgressTracker.tsx`
### `frontend/src/components/upload/JobStatus.tsx`
### `frontend/src/hooks/queries/use-jobs.ts`

---

## Acceptance Criteria

1. **File Upload:**
   - Drag-and-drop zone
   - Click to browse
   - PDF file type validation
   - File size validation (max 50MB)
   - Multiple file selection
   - Preview before upload

2. **Progress Tracker:**
   - Multi-step progress indicator
   - Current step highlighted
   - Estimated time remaining
   - Cancel button

3. **Job Status:**
   - Real-time status updates (WebSocket/polling)
   - Step-by-step breakdown
   - Error display with details
   - Retry failed jobs
   - View completed job results

4. **Job Store:**
   - Active jobs list
   - Job progress state
   - Polling/WebSocket connection
   - Create job action
   - Cancel job action

5. **UX:**
   - Clear visual feedback
   - Non-blocking (can navigate away)
   - Return to see progress

---

## Processing Steps Display

```
1. Uploading files...
2. Extracting images from PDF
3. Classifying images
4. Detecting watermarks
5. Processing floor plans
6. Optimizing images
7. Extracting text
8. Structuring data
9. Generating content
10. Creating output sheet
```

---

## QA Pair: QA-UPLOAD-001

---

**Begin execution.**
