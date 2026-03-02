# Agent Brief: DEV-GSHEETS-001

**Agent ID:** DEV-GSHEETS-001
**Agent Name:** Google Sheets Integration Agent
**Type:** Development
**Phase:** 5 - Integrations
**Context Budget:** 55,000 tokens

---

## Mission

Implement Google Sheets API client with Shared Drive access, batch operations, and template management.

---

## Documentation to Read

### Primary
1. `docs/05-integrations/GOOGLE_SHEETS_INTEGRATION.md` - Sheets API patterns

### Secondary
1. `docs/05-integrations/GOOGLE_CLOUD_SETUP.md` - Service account setup

---

## Dependencies

**Upstream:** DEV-CONFIG-001
**Downstream:** DEV-SHEETS-001 (service layer)

---

## Outputs

### `backend/app/integrations/sheets_client.py`

---

## Acceptance Criteria

1. **Authentication:**
   - Service account with Shared Drive access
   - All files owned by Shared Drive (ID: 0AOEEIstP54k2Uk9PVA)
   - Token refresh handling

2. **Spreadsheet Operations:**
   - Create spreadsheet
   - Copy from template
   - Share with users/groups
   - Get spreadsheet metadata

3. **Sheet Operations:**
   - Read range
   - Write range (single and batch)
   - Append rows
   - Clear range
   - Format cells

4. **Batch Operations:**
   - batchUpdate for multiple operations
   - Reduce API calls
   - Handle partial failures

5. **Rate Limiting:**
   - Implement exponential backoff
   - Respect quota limits (100 requests/100sec)
   - Queue operations if needed

6. **Error Handling:**
   - Handle API errors gracefully
   - Retry on transient errors
   - Log all operations

---

## API Methods

```python
class SheetsClient:
    def create_spreadsheet(title, template_id=None)
    def share(spreadsheet_id, email, role)
    def read_range(spreadsheet_id, range)
    def write_range(spreadsheet_id, range, values)
    def batch_update(spreadsheet_id, requests)
    def append_rows(spreadsheet_id, range, values)
    def format_range(spreadsheet_id, range, format)
```

---

## QA Pair: QA-GSHEETS-001

---

**Begin execution.**
