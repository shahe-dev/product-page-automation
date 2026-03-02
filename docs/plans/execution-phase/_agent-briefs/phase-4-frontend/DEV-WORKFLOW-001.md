# Agent Brief: DEV-WORKFLOW-001

**Agent ID:** DEV-WORKFLOW-001
**Agent Name:** Workflow Page Agent
**Type:** Development
**Phase:** 4 - Frontend
**Context Budget:** 55,000 tokens

---

## Mission

Implement workflow management page with Kanban board for content approval and publishing pipeline.

---

## Documentation to Read

### Primary
1. `docs/03-frontend/PAGE_SPECIFICATIONS.md` - Workflow page spec
2. `docs/02-modules/APPROVAL_WORKFLOW.md` - Approval states
3. `docs/02-modules/PUBLISHING_WORKFLOW.md` - Publishing states

### Secondary
1. `docs/08-user-guides/MARKETING_MANAGER_GUIDE.md` - Approval workflow
2. `docs/08-user-guides/PUBLISHER_GUIDE.md` - Publishing workflow

---

## Dependencies

**Upstream:** DEV-FESETUP-001
**Downstream:** None

---

## Outputs

### `frontend/src/pages/WorkflowPage.tsx`
### `frontend/src/components/workflow/KanbanBoard.tsx`
### `frontend/src/components/workflow/WorkflowCard.tsx`
### `frontend/src/components/workflow/StatusColumn.tsx`

---

## Acceptance Criteria

1. **Kanban Board:**
   - Drag-and-drop cards between columns
   - Column headers with counts
   - Scrollable columns
   - Quick filters

2. **Status Columns:**
   - Draft
   - Pending Review
   - In Review
   - Approved
   - Ready to Publish
   - Published
   - Archived

3. **Workflow Card:**
   - Project thumbnail
   - Project name
   - Current assignee
   - Due date (if set)
   - Priority indicator
   - Quick actions

4. **Actions:**
   - Move to next stage
   - Assign to user
   - Add comment
   - Set priority
   - View history

5. **Notifications:**
   - Stage change alerts
   - Assignment notifications
   - Due date reminders

---

## Workflow Rules

- Draft → Pending Review: Auto when QA score >80%
- Pending Review → In Review: Marketing Manager assigns
- In Review → Approved/Draft: Marketing Manager decision
- Approved → Ready to Publish: Publisher picks up
- Ready to Publish → Published: Publisher completes

---

## QA Pair: QA-WORKFLOW-001

---

**Begin execution.**
