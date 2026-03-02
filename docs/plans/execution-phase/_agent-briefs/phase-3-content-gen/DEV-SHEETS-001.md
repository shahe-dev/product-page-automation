# Agent Brief: DEV-SHEETS-001

**Agent ID:** DEV-SHEETS-001
**Agent Name:** Sheets Manager Agent
**Type:** Development
**Phase:** 3 - Content Generation
**Context Budget:** 55,000 tokens

---

## Mission

Implement Google Sheets integration for content output including template management, field mapping, and batch operations using Shared Drive.

---

## Documentation to Read

### Primary
1. `docs/05-integrations/GOOGLE_SHEETS_INTEGRATION.md` - Sheets API patterns
2. `docs/02-modules/CONTENT_GENERATION.md` - Content output requirements

### Secondary
1. `docs/05-integrations/GOOGLE_CLOUD_SETUP.md` - Service account setup

---

## Dependencies

**Upstream:** DEV-CONTENT-001
**Downstream:** (End of content generation pipeline)

---

## Outputs

### `backend/app/services/sheets_manager.py`

---

## Acceptance Criteria

1. **Template Management:**
   - Create sheets from predefined templates (6 total)
   - Aggregators template structure (24+ aggregator domains)
   - OPR template structure (opr.ae)
   - MPP template structure (main-portal.com)
   - ADOP template structure (abudhabioffplan.ae)
   - ADRE template structure (secondary-market-portal.com)
   - Commercial template structure (cre.main-portal.com)

2. **Field Mapping:**
   - Map content fields to specific cells per template
   - Handle all content fields
   - Support custom field mappings

3. **Batch Operations:**
   - Batch update API calls (reduce quota usage)
   - Handle 100+ cells per update
   - Retry on quota errors

4. **Shared Drive Access:**
   - Use service account with Shared Drive membership
   - All sheets created in Shared Drive (ID: 0AOEEIstP54k2Uk9PVA)
   - Files owned by Shared Drive, accessible to all members

5. **Sharing:**
   - Share with project creator (editor)
   - Share with team folder
   - Set appropriate permissions

6. **Validation:**
   - Read-back validation after write
   - Verify all fields written correctly
   - Report any write failures

7. **Rate Limiting:**
   - Handle Sheets API rate limits
   - Implement exponential backoff
   - Queue operations if needed

---

## Sheet Template Structure

All 6 templates share a common structure with EN/AR/RU language columns:

```
Template Structure (All 6):
- Row 1: Headers (Field, EN, AR, RU)
- Row 2+: Content fields with values per language
- Includes: Project Name, Developer, Location, Meta fields, Overview, Amenities, etc.
```

**Template IDs (in Shared Drive 0AOEEIstP54k2Uk9PVA):**
- Aggregators: `YOUR_AGGREGATORS_SHEET_ID`
- OPR: `YOUR_OPR_SHEET_ID`
- MPP: `YOUR_MPP_SHEET_ID`
- ADOP: `YOUR_ADOP_SHEET_ID`
- ADRE: `YOUR_ADRE_SHEET_ID`
- Commercial: `YOUR_COMMERCIAL_SHEET_ID`

---

## QA Pair: QA-SHEETS-001

---

**Begin execution.**
