# Agent Brief: DEV-QAPAGE-001

**Agent ID:** DEV-QAPAGE-001
**Agent Name:** QA Page Agent
**Type:** Development
**Phase:** 4 - Frontend
**Context Budget:** 55,000 tokens

---

## Mission

Implement content QA review page with side-by-side comparison, diff highlighting, and issue management.

---

## Documentation to Read

### Primary
1. `docs/03-frontend/PAGE_SPECIFICATIONS.md` - QA page spec
2. `docs/02-modules/QA_MODULE.md` - QA validation rules

### Secondary
1. `docs/08-user-guides/MARKETING_MANAGER_GUIDE.md` - Review workflow

---

## Dependencies

**Upstream:** DEV-FESETUP-001
**Downstream:** DEV-WORKFLOW-001

---

## Outputs

### `frontend/src/pages/QAPage.tsx`
### `frontend/src/components/qa/ComparisonView.tsx`
### `frontend/src/components/qa/DiffHighlighter.tsx`
### `frontend/src/components/qa/IssueList.tsx`

---

## Acceptance Criteria

1. **Comparison View:**
   - Source (PDF content) on left
   - Generated content on right
   - Synced scrolling
   - Field-by-field comparison

2. **Diff Highlighting:**
   - Highlight factual differences
   - Color-coded severity
   - Click to navigate to issue
   - Inline comments

3. **Issue List:**
   - Categorized issues (factual, compliance, consistency)
   - Severity badges
   - Status (open, resolved, dismissed)
   - Bulk actions
   - Filter by type/severity

4. **Review Actions:**
   - Approve content
   - Request changes
   - Add comments
   - Assign to team member

5. **Scoring Display:**
   - Overall QA score
   - Per-field scores
   - Score breakdown
   - Historical comparison

---

## QA Issue Types

- Factual: Data doesn't match source
- Compliance: Brand/legal violation
- Consistency: Internal contradiction
- Quality: Grammar, style issues

---

## QA Pair: QA-QAPAGE-001

---

**Begin execution.**
