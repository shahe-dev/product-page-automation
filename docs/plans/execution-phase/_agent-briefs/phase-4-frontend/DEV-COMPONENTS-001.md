# Agent Brief: DEV-COMPONENTS-001

**Agent ID:** DEV-COMPONENTS-001
**Agent Name:** Shared Components Agent
**Type:** Development
**Phase:** 4 - Frontend
**Context Budget:** 60,000 tokens

---

## Mission

Implement shared UI component library including common components and layout components following shadcn/ui patterns.

---

## Documentation to Read

### Primary
1. `docs/03-frontend/COMPONENT_LIBRARY.md` - Component specifications
2. `docs/03-frontend/ACCESSIBILITY.md` - A11y requirements

---

## Dependencies

**Upstream:** DEV-FESETUP-001
**Downstream:** All page agents

---

## Outputs

### Common Components
- `frontend/src/components/common/Button.tsx`
- `frontend/src/components/common/Input.tsx`
- `frontend/src/components/common/Select.tsx`
- `frontend/src/components/common/Modal.tsx`
- `frontend/src/components/common/Table.tsx`
- `frontend/src/components/common/Card.tsx`
- `frontend/src/components/common/Badge.tsx`
- `frontend/src/components/common/Alert.tsx`

### Layout Components
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/Layout.tsx`

---

## Acceptance Criteria

1. **Button:**
   - Variants: primary, secondary, outline, ghost, destructive
   - Sizes: sm, md, lg
   - Loading state
   - Disabled state
   - Icon support

2. **Input:**
   - Types: text, email, password, number
   - Error state with message
   - Helper text
   - Prefix/suffix icons
   - Disabled state

3. **Select:**
   - Single and multi-select
   - Searchable option
   - Group options
   - Clear selection

4. **Modal:**
   - Sizes: sm, md, lg, full
   - Close on overlay click (configurable)
   - Close on escape
   - Focus trap
   - Scroll lock

5. **Table:**
   - Sortable columns
   - Selectable rows
   - Pagination
   - Empty state
   - Loading state

6. **Layout:**
   - Responsive header
   - Collapsible sidebar
   - Main content area
   - Footer (optional)

7. **All Components:**
   - Full TypeScript types
   - Storybook stories
   - Unit tests
   - WCAG 2.1 AA compliant

---

## QA Pair: QA-COMPONENTS-001

---

**Begin execution.**
