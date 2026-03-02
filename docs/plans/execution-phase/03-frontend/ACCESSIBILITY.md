# Accessibility

**Last Updated:** 2026-01-15
**Status:** Active
**Owner:** Frontend Team

---

## Overview

The PDP Automation v.3 application is designed to meet WCAG 2.1 Level AA compliance standards, ensuring accessibility for all users including those using assistive technologies, keyboard-only navigation, and screen readers.

### WCAG 2.1 AA Compliance

This document outlines accessibility requirements, implementation patterns, and testing procedures to ensure the application is usable by everyone.

### Key Principles (POUR)

1. **Perceivable:** Information must be presentable to users in ways they can perceive
2. **Operable:** UI components must be operable by all users
3. **Understandable:** Information and operation must be understandable
4. **Robust:** Content must be robust enough to work with assistive technologies

---

## Keyboard Navigation

### Requirements

All interactive elements must be accessible via keyboard without requiring a mouse.

### Implementation

#### Tab Order

```typescript
// Ensure logical tab order using semantic HTML
export function FormExample() {
  return (
    <form>
      {/* Tab order: 1. Name, 2. Email, 3. Submit */}
      <label htmlFor="name">Name</label>
      <input id="name" type="text" />

      <label htmlFor="email">Email</label>
      <input id="email" type="email" />

      <button type="submit">Submit</button>
    </form>
  )
}
```

#### Focus Indicators

Note: The project uses Tailwind CSS 4.x with CSS-based configuration (@tailwindcss/vite plugin). The following shows the conceptual theme structure:

```css
/* Global focus styles in Tailwind config */
/* Conceptual v3 structure - v4 uses CSS-based @theme configuration in index.css */
module.exports = {
  theme: {
    extend: {
      ringWidth: {
        DEFAULT: '2px',
      },
      ringColor: {
        DEFAULT: '#3b82f6', // Blue-500
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'), // Provides accessible form styles
  ],
}

/* Custom focus styles */
.focus-visible:focus {
  @apply ring-2 ring-blue-500 ring-offset-2 outline-none;
}
```

#### Keyboard Shortcuts

```typescript
// src/hooks/useKeyboardShortcuts.ts
export function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Ctrl/Cmd + K: Open search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        openSearch()
      }

      // Ctrl/Cmd + N: New project
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault()
        navigate('/processing')
      }

      // Escape: Close modal/dialog
      if (e.key === 'Escape') {
        closeCurrentModal()
      }
    }

    document.addEventListener('keydown', handleKeyPress)
    return () => document.removeEventListener('keydown', handleKeyPress)
  }, [])
}
```

#### Skip to Main Content

```typescript
// src/components/layout/AppLayout.tsx
export function AppLayout() {
  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-md"
      >
        Skip to main content
      </a>

      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1">
          <Header />
          <main id="main-content" tabIndex={-1}>
            <Outlet />
          </main>
        </div>
      </div>
    </>
  )
}
```

---

## Screen Reader Support

### Semantic HTML

```typescript
// Use semantic elements for proper structure
export function PageExample() {
  return (
    <>
      <header>
        <nav aria-label="Main navigation">
          {/* Navigation items */}
        </nav>
      </header>

      <main>
        <article>
          <h1>Page Title</h1>
          <section>
            <h2>Section Title</h2>
            {/* Content */}
          </section>
        </article>
      </main>

      <aside aria-label="Sidebar">
        {/* Sidebar content */}
      </aside>

      <footer>
        {/* Footer content */}
      </footer>
    </>
  )
}
```

### ARIA Labels and Descriptions

```typescript
// Icon-only buttons need ARIA labels
export function IconButton() {
  return (
    <button
      aria-label="Close dialog"
      onClick={handleClose}
      className="p-2 rounded-md hover:bg-gray-100"
    >
      <X className="h-5 w-5" />
    </button>
  )
}

// Complex components need descriptions
export function SearchBar() {
  return (
    <div role="search">
      <label htmlFor="search" className="sr-only">
        Search projects
      </label>
      <input
        id="search"
        type="search"
        placeholder="Search..."
        aria-describedby="search-hint"
      />
      <span id="search-hint" className="sr-only">
        Press Enter to search. Results will appear below.
      </span>
    </div>
  )
}
```

### ARIA Live Regions

```typescript
// Announce dynamic content changes
export function ProgressTracker({ currentStep, status }: ProgressTrackerProps) {
  return (
    <div>
      <div className="space-y-4">
        {/* Visual progress display */}
      </div>

      {/* Screen reader announcements */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {status === 'in_progress' &&
          `Currently processing: ${currentStep}`}
        {status === 'completed' &&
          'Processing completed successfully'}
        {status === 'failed' &&
          'Processing failed. Please try again.'}
      </div>
    </div>
  )
}
```

### Form Validation

```typescript
// Accessible form validation
export function FormField({ name, label, error }: FormFieldProps) {
  const id = useId()
  const errorId = `${id}-error`

  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span aria-label="required"> *</span>}
      </label>

      <input
        id={id}
        name={name}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'mt-1 block w-full rounded-md border-gray-300',
          error && 'border-red-500 focus:border-red-500 focus:ring-red-500'
        )}
      />

      {error && (
        <p id={errorId} className="mt-1 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
```

---

## Color Contrast

### Requirements

- **Text:** Minimum 4.5:1 contrast ratio for normal text
- **Large Text:** Minimum 3:1 contrast ratio (18pt+ or 14pt+ bold)
- **UI Components:** Minimum 3:1 contrast ratio for interactive elements

### Tailwind Color Palette (WCAG AA Compliant)

Note: The project uses Tailwind CSS 4.x with CSS-based configuration (@tailwindcss/vite plugin). The following shows the conceptual theme structure:

```typescript
// Conceptual v3 tailwind.config.js - v4 uses CSS-based @theme configuration in index.css
module.exports = {
  theme: {
    extend: {
      colors: {
        // Primary colors with sufficient contrast
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6', // Main primary (4.5:1 on white)
          600: '#2563eb', // Darker for better contrast
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // Success colors
        success: {
          500: '#10b981', // 3.5:1 on white
          600: '#059669', // 4.5:1 on white
        },
        // Error colors
        error: {
          500: '#ef4444', // 3.9:1 on white
          600: '#dc2626', // 4.5:1 on white
        },
        // Warning colors
        warning: {
          500: '#f59e0b', // 2.6:1 on white (needs dark text)
          600: '#d97706', // Better for backgrounds
        },
      },
    },
  },
}
```

### Text Contrast Examples

```typescript
// Good contrast examples
export function TextExamples() {
  return (
    <>
      {/* Normal text: 4.5:1+ */}
      <p className="text-gray-900 bg-white">
        Dark gray on white (13.6:1) ✓
      </p>

      {/* Large text: 3:1+ */}
      <h1 className="text-2xl font-bold text-gray-700 bg-white">
        Medium gray on white (5.7:1) ✓
      </h1>

      {/* Interactive elements: 3:1+ */}
      <button className="bg-blue-600 text-white">
        White on blue (4.5:1) ✓
      </button>

      {/* Avoid low contrast */}
      <p className="text-gray-400 bg-white">
        Light gray on white (2.8:1) ✗ FAILS
      </p>
    </>
  )
}
```

### Status Indicators (Don't Rely on Color Alone)

```typescript
// Use icons + text + color for status
export function StatusBadge({ status }: { status: string }) {
  const config = {
    draft: {
      icon: FileText,
      text: 'Draft',
      className: 'bg-gray-100 text-gray-800',
    },
    approved: {
      icon: CheckCircle,
      text: 'Approved',
      className: 'bg-green-100 text-green-800',
    },
    rejected: {
      icon: XCircle,
      text: 'Rejected',
      className: 'bg-red-100 text-red-800',
    },
  }

  const { icon: Icon, text, className } = config[status]

  return (
    <span className={cn('inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium', className)}>
      <Icon className="h-3 w-3" aria-hidden="true" />
      {text}
    </span>
  )
}
```

---

## Forms and Inputs

### Required Fields

```typescript
// Indicate required fields visually and programmatically
export function RequiredField() {
  return (
    <label htmlFor="project-name" className="block text-sm font-medium text-gray-700">
      Project Name
      <span className="text-red-500" aria-label="required">
        {' '}*
      </span>
    </label>
  )
}
```

### Error Messages

```typescript
// Associate error messages with inputs
export function ErrorExample() {
  const [error, setError] = useState('')

  return (
    <div>
      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        aria-invalid={!!error}
        aria-describedby={error ? 'email-error' : undefined}
      />
      {error && (
        <p id="email-error" className="text-red-600 text-sm mt-1" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
```

### Form Submission Feedback

```typescript
// Announce form submission results
export function FormSubmission() {
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle')

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}

      <button
        type="submit"
        disabled={status === 'submitting'}
        aria-busy={status === 'submitting'}
      >
        {status === 'submitting' ? 'Submitting...' : 'Submit'}
      </button>

      {/* Announcement region */}
      <div role="status" aria-live="polite" className="sr-only">
        {status === 'submitting' && 'Form is being submitted'}
        {status === 'success' && 'Form submitted successfully'}
        {status === 'error' && 'Form submission failed. Please try again.'}
      </div>

      {/* Visual feedback */}
      {status === 'success' && (
        <Alert variant="success">
          Form submitted successfully!
        </Alert>
      )}
    </form>
  )
}
```

---

## Interactive Components

### Buttons

```typescript
// Accessible button patterns
export function ButtonExamples() {
  return (
    <>
      {/* Standard button with visible text */}
      <button className="px-4 py-2 bg-blue-600 text-white rounded-md">
        Save Project
      </button>

      {/* Icon button with ARIA label */}
      <button aria-label="Delete project" className="p-2 rounded-md">
        <Trash className="h-5 w-5" />
      </button>

      {/* Button with icon and text */}
      <button className="flex items-center gap-2 px-4 py-2">
        <Download className="h-4 w-4" aria-hidden="true" />
        Download
      </button>

      {/* Loading state */}
      <button disabled aria-busy="true">
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        <span className="sr-only">Loading...</span>
        Processing
      </button>
    </>
  )
}
```

### Dialogs and Modals

```typescript
// src/components/ui/Dialog.tsx
import * as DialogPrimitive from '@radix-ui/react-dialog'

export function Dialog({ open, onOpenChange, title, children }: DialogProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 bg-black/50" />
        <DialogPrimitive.Content
          className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg p-6 max-w-md w-full"
          aria-describedby={undefined} // Only if no description
        >
          <DialogPrimitive.Title className="text-lg font-semibold mb-4">
            {title}
          </DialogPrimitive.Title>

          <div>{children}</div>

          <DialogPrimitive.Close
            className="absolute top-4 right-4"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
```

### Dropdown Menus

```typescript
// Accessible dropdown with keyboard navigation
import * as DropdownMenu from '@radix-ui/react-dropdown-menu'

export function UserMenu() {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button aria-label="User menu" className="p-2 rounded-md">
          <Avatar />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content className="bg-white border rounded-md shadow-lg">
          <DropdownMenu.Item className="px-4 py-2 hover:bg-gray-100">
            Profile
          </DropdownMenu.Item>
          <DropdownMenu.Item className="px-4 py-2 hover:bg-gray-100">
            Settings
          </DropdownMenu.Item>
          <DropdownMenu.Separator className="h-px bg-gray-200" />
          <DropdownMenu.Item className="px-4 py-2 hover:bg-gray-100 text-red-600">
            Logout
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}
```

---

## Data Tables

### Accessible Table Structure

```typescript
// src/components/ui/DataTable.tsx
export function DataTable({ columns, data }: DataTableProps) {
  return (
    <table className="w-full">
      <caption className="sr-only">
        Projects table with {data.length} rows
      </caption>

      <thead>
        <tr>
          {columns.map((column) => (
            <th
              key={column.id}
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
            >
              {column.header}
              {column.sortable && (
                <button
                  aria-label={`Sort by ${column.header}`}
                  className="ml-2"
                >
                  <ArrowUpDown className="h-4 w-4" />
                </button>
              )}
            </th>
          ))}
        </tr>
      </thead>

      <tbody>
        {data.map((row) => (
          <tr key={row.id}>
            {columns.map((column) => (
              <td key={column.id} className="px-6 py-4 text-sm text-gray-900">
                {column.render(row)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

---

## Images and Media

### Alt Text

```typescript
// Meaningful alt text for images
export function ProjectThumbnail({ project }: { project: Project }) {
  return (
    <img
      src={project.thumbnailUrl}
      alt={`${project.name} - ${project.developer} development in ${project.location}`}
      className="w-full h-48 object-cover rounded-lg"
    />
  )
}

// Decorative images use empty alt
export function DecorativeIcon() {
  return (
    <img src="/pattern.svg" alt="" role="presentation" />
  )
}
```

### Video Captions

```typescript
// Provide captions for video content
export function VideoPlayer({ src, captions }: VideoPlayerProps) {
  return (
    <video controls>
      <source src={src} type="video/mp4" />
      <track
        kind="captions"
        src={captions}
        srcLang="en"
        label="English"
        default
      />
      Your browser does not support the video tag.
    </video>
  )
}
```

---

## Responsive Design

### Mobile Accessibility

```typescript
// Touch targets minimum 44x44px
export function MobileButton() {
  return (
    <button
      className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-md bg-blue-600 text-white"
      aria-label="Add new project"
    >
      <Plus className="h-5 w-5" />
    </button>
  )
}
```

### Text Resizing

```css
/* Support browser text zoom up to 200% */
/* Use relative units (rem, em) instead of px */
.text-base {
  font-size: 1rem; /* 16px base */
}

.text-lg {
  font-size: 1.125rem; /* 18px */
}

/* Avoid fixed heights that break at 200% zoom */
.flexible-container {
  min-height: 3rem; /* Not height: 3rem */
}
```

---

## Testing Procedures

### Automated Testing

```bash
# Install accessibility testing tools
npm install --save-dev @axe-core/react jest-axe

# Run accessibility tests
npm run test:a11y
```

```typescript
// src/tests/accessibility.test.tsx
import { axe, toHaveNoViolations } from 'jest-axe'
import { render } from '@testing-library/react'

expect.extend(toHaveNoViolations)

describe('Accessibility', () => {
  it('should have no violations on LoginPage', async () => {
    const { container } = render(<LoginPage />)
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have no violations on ProjectsListPage', async () => {
    const { container } = render(<ProjectsListPage />)
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
```

### Manual Testing Checklist

#### Keyboard Navigation
- [ ] All interactive elements reachable via Tab key
- [ ] Tab order is logical
- [ ] Focus indicators visible
- [ ] No keyboard traps
- [ ] Skip to main content link works
- [ ] Escape key closes modals/dropdowns

#### Screen Reader
- [ ] Test with NVDA (Windows) or VoiceOver (Mac)
- [ ] All images have appropriate alt text
- [ ] Form labels announced correctly
- [ ] Error messages announced
- [ ] Dynamic content changes announced (ARIA live)
- [ ] Page title describes current page

#### Color Contrast
- [ ] Run WebAIM Contrast Checker
- [ ] Text meets 4.5:1 ratio
- [ ] UI components meet 3:1 ratio
- [ ] Status not conveyed by color alone

#### Zoom and Reflow
- [ ] Test at 200% browser zoom
- [ ] No horizontal scrolling at 320px width
- [ ] Content remains readable and functional
- [ ] Touch targets minimum 44x44px on mobile

---

## Tools and Resources

### Browser Extensions
- **axe DevTools:** Automated accessibility testing
- **WAVE:** Web accessibility evaluation tool
- **Lighthouse:** Chrome DevTools audit
- **Color Contrast Analyzer:** Check color ratios

### Screen Readers
- **NVDA:** Free Windows screen reader
- **JAWS:** Popular Windows screen reader
- **VoiceOver:** Built-in macOS/iOS screen reader
- **TalkBack:** Android screen reader

### Documentation
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [WebAIM Resources](https://webaim.org/resources/)
- [A11y Project](https://www.a11yproject.com/)

---

## Related Documentation

- [Component Library](./COMPONENT_LIBRARY.md) - UI component specifications
- [Page Specifications](./PAGE_SPECIFICATIONS.md) - Page layouts and wireframes
- [State Management](./STATE_MANAGEMENT.md) - React Query and Zustand patterns
- [Routing](./ROUTING.md) - Route configuration and guards

---

**End of Accessibility Documentation**
