# Agent Brief: TEST-VISUAL-001

**Agent ID:** TEST-VISUAL-001
**Agent Name:** Visual Regression Test Agent
**Type:** Testing
**Phase:** Testing
**Context Budget:** 45,000 tokens

---

## Mission

Implement visual regression testing for UI components and pages using Storybook and Chromatic/Percy.

---

## Documentation to Read

### Primary
1. `docs/07-testing/E2E_TEST_SCENARIOS.md` - Visual test scenarios
2. `docs/03-frontend/COMPONENT_LIBRARY.md` - Component specs

---

## Dependencies

**Upstream:** Phase 4 (frontend components)
**Downstream:** None

---

## Outputs

### `tests/visual/` - Visual test configurations
### `frontend/.storybook/` - Storybook configuration

---

## Acceptance Criteria

1. **Storybook Setup:**
   - All components have stories
   - Interactive controls
   - Accessibility addon
   - Theme switching
   - Responsive viewports

2. **Visual Regression:**
   - Baseline screenshots
   - Diff detection
   - Review workflow
   - CI integration

3. **Component Stories:**
   - Default state
   - All variants
   - Interactive states
   - Error states
   - Loading states

4. **Page Stories:**
   - Key pages documented
   - Responsive variants
   - Theme variants

5. **CI Integration:**
   - Run on PR
   - Block on visual diff
   - Approval workflow

---

## Storybook Structure

```
frontend/.storybook/
├── main.ts
├── preview.ts
└── manager.ts

frontend/src/components/
├── common/
│   ├── Button.tsx
│   └── Button.stories.tsx
├── layout/
│   ├── Header.tsx
│   └── Header.stories.tsx
└── ...
```

---

## Story Template

```tsx
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  component: Button,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Button',
  },
};

export const Loading: Story = {
  args: {
    isLoading: true,
    children: 'Loading...',
  },
};
```

---

**Begin execution.**
