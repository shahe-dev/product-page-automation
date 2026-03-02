# Agent Brief: DEV-PROMPTS-001

**Agent ID:** DEV-PROMPTS-001
**Agent Name:** Prompts Page Agent
**Type:** Development
**Phase:** 4 - Frontend
**Context Budget:** 50,000 tokens

---

## Mission

Implement prompt management page for viewing, editing, and versioning content generation prompts.

---

## Documentation to Read

### Primary
1. `docs/03-frontend/PAGE_SPECIFICATIONS.md` - Prompts page spec
2. `docs/02-modules/PROMPT_LIBRARY.md` - Prompt management

### Secondary
1. `docs/08-user-guides/ADMIN_GUIDE.md` - Admin workflows

---

## Dependencies

**Upstream:** DEV-FESETUP-001
**Downstream:** None (Admin feature)

---

## Outputs

### `frontend/src/pages/PromptsPage.tsx`
### `frontend/src/components/prompts/PromptList.tsx`
### `frontend/src/components/prompts/PromptEditor.tsx`
### `frontend/src/components/prompts/VersionHistory.tsx`

---

## Acceptance Criteria

1. **Prompt List:**
   - All prompts by category
   - Template association
   - Active/inactive status
   - Last modified date
   - Quick actions

2. **Prompt Editor:**
   - Monaco/CodeMirror editor
   - Syntax highlighting for variables
   - Variable autocomplete
   - Character count
   - Preview output
   - Test with sample data

3. **Version History:**
   - List all versions
   - Diff between versions
   - Rollback to version
   - Version notes

4. **Admin Controls:**
   - Create new prompt
   - Duplicate prompt
   - Archive prompt
   - Set as active

5. **Variable System:**
   - {{project_name}}
   - {{developer_name}}
   - {{location}}
   - etc.

---

## QA Pair: QA-PROMPTS-001

---

**Begin execution.**
