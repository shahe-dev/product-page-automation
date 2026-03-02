# Agent Brief: DEV-DRIVE-001

**Agent ID:** DEV-DRIVE-001
**Agent Name:** Google Drive Integration Agent
**Type:** Development
**Phase:** 5 - Integrations
**Context Budget:** 50,000 tokens

---

## Mission

Implement Google Drive API client for file management, folder organization, and permission handling.

---

## Documentation to Read

### Primary
1. `docs/05-integrations/GOOGLE_DRIVE_INTEGRATION.md` - Drive API patterns

### Secondary
1. `docs/05-integrations/GOOGLE_CLOUD_SETUP.md` - Service account setup

---

## Dependencies

**Upstream:** DEV-CONFIG-001
**Downstream:** DEV-IMGOPT-001

---

## Outputs

### `backend/app/integrations/drive_client.py`

---

## Acceptance Criteria

1. **Authentication:**
   - Service account authentication
   - Shared Drive access (ID: 0AOEEIstP54k2Uk9PVA)
   - No impersonation needed - direct access via Shared Drive membership

2. **File Operations:**
   - Upload file to folder
   - Download file
   - Copy file
   - Move file
   - Delete file
   - Get file metadata

3. **Folder Operations:**
   - Create folder
   - List folder contents
   - Get folder by path
   - Nested folder creation

4. **Permission Management:**
   - Share with user
   - Share with domain
   - Remove permissions
   - Transfer ownership

5. **Search:**
   - Search by name
   - Search by type
   - Search in folder

6. **Export:**
   - Export Google Docs to PDF
   - Export Sheets to Excel/CSV

---

## Folder Structure

```
PDP Automation/
├── Projects/
│   └── {project_name}/
│       ├── Source/
│       ├── Images/
│       └── Output/
├── Templates/
└── Archive/
```

---

## QA Pair: QA-DRIVE-001

---

**Begin execution.**
