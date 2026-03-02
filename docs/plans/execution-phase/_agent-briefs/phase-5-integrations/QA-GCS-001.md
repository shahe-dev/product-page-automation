# Agent Brief: QA-GCS-001

**Agent ID:** QA-GCS-001
**Agent Name:** GCS Integration QA
**Type:** QA
**Phase:** 5 - Integrations
**Paired Dev Agent:** DEV-GCS-001

---

## Validation Checklist

- [ ] Bucket connections work
- [ ] Direct upload works
- [ ] Resumable upload works
- [ ] Streaming upload works
- [ ] Signed URL generation works
- [ ] Download operations work
- [ ] Lifecycle policies applied
- [ ] No public access
- [ ] Error handling robust
- [ ] Retry logic works

---

## Test Cases

1. Upload small file (<5MB)
2. Upload large file (>50MB)
3. Upload with custom metadata
4. Generate signed URL
5. Verify signed URL expiry
6. Download via signed URL
7. Stream large file download
8. Test temp bucket lifecycle
9. Handle network interruption
10. Handle quota error
11. Verify no public access
12. Test concurrent uploads

---

## Security Tests

- Signed URLs expire correctly
- Cannot access without auth
- Service account permissions minimal
- Audit logs generated

---

## Performance Tests

- Upload speed acceptable
- Download speed acceptable
- Concurrent upload handling
- Memory usage during large files

---

**Begin review.**
