# Agent Brief: QA-DRIVE-001

**Agent ID:** QA-DRIVE-001
**Agent Name:** Google Drive QA
**Type:** QA
**Phase:** 5 - Integrations
**Paired Dev Agent:** DEV-DRIVE-001

---

## Validation Checklist

- [ ] Service account authentication works
- [ ] Shared Drive access functioning
- [ ] File upload works
- [ ] File download works
- [ ] Folder creation works
- [ ] Permission sharing works
- [ ] Search functionality works
- [ ] Export functionality works
- [ ] Error handling robust
- [ ] Rate limiting respected

---

## Test Cases

1. Upload file to root
2. Upload file to folder
3. Create nested folders
4. Download file
5. Copy file to another folder
6. Move file between folders
7. Share with user
8. Remove sharing
9. Search by filename
10. Search in specific folder
11. Export Sheet to CSV
12. Handle large file upload

---

## Integration Tests

- Full project folder creation
- File organization workflow
- Multi-user sharing scenario
- Archive and cleanup

---

## Permission Tests

- Verify shared access works
- Verify removed access fails
- Domain-wide sharing
- Public link generation (if needed)

---

**Begin review.**
