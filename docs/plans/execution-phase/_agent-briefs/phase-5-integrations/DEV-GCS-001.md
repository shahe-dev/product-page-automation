# Agent Brief: DEV-GCS-001

**Agent ID:** DEV-GCS-001
**Agent Name:** GCS Integration Agent
**Type:** Development
**Phase:** 5 - Integrations
**Context Budget:** 50,000 tokens

---

## Mission

Implement Google Cloud Storage integration for file uploads, downloads, and lifecycle management with signed URLs.

---

## Documentation to Read

### Primary
1. `docs/05-integrations/GOOGLE_CLOUD_SETUP.md` - GCP configuration
2. `docs/05-integrations/CLOUD_STORAGE_PATTERNS.md` - Storage patterns

---

## Dependencies

**Upstream:** DEV-CONFIG-001
**Downstream:** DEV-PDF-001, DEV-IMGOPT-001

---

## Outputs

### `backend/app/services/storage_service.py`

---

## Acceptance Criteria

1. **Bucket Management:**
   - Initialize bucket connection
   - Bucket existence validation
   - Multiple bucket support (temp, output, archive)

2. **Upload Operations:**
   - Direct upload (small files <5MB)
   - Resumable upload (large files)
   - Streaming upload
   - Content type detection
   - Custom metadata

3. **Download Operations:**
   - Direct download
   - Signed URL generation (configurable expiry)
   - Range requests support
   - Streaming download

4. **Lifecycle Management:**
   - Temp files auto-delete (24 hours)
   - Archive after processing
   - Version history (optional)

5. **Security:**
   - Service account authentication
   - Uniform bucket-level access
   - No public access
   - Audit logging

6. **Error Handling:**
   - Retry on transient failures
   - Handle quota errors
   - Graceful degradation

---

## Bucket Structure

```
pdp-automation-temp/      (24h lifecycle)
  ├── uploads/{job_id}/
  └── processing/{job_id}/

pdp-automation-output/    (permanent)
  ├── projects/{project_id}/
  │   ├── images/
  │   └── documents/
  └── exports/

pdp-automation-archive/   (30d lifecycle)
  └── jobs/{job_id}/
```

---

## QA Pair: QA-GCS-001

---

**Begin execution.**
