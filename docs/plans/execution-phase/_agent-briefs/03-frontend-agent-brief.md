# Agent Briefing: Frontend Documentation Agent

**Agent ID:** frontend-docs-agent
**Batch:** 2 (Features)
**Priority:** P1 - User Interface
**Est. Context Usage:** 35,000 tokens

---

## Your Mission

You are a specialized documentation agent responsible for creating **5 frontend documentation files** for the PDP Automation v.3 system. These documents describe the React application, UI components, and user interactions.

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/03-frontend/`

---

## Files You Must Create

1. `COMPONENT_LIBRARY.md` (400-500 lines) - UI component specifications
2. `PAGE_SPECIFICATIONS.md` (500-600 lines) - Every page with wireframes
3. `STATE_MANAGEMENT.md` (300-350 lines) - React Query + Zustand patterns
4. `ROUTING.md` (250-300 lines) - All routes and guards
5. `ACCESSIBILITY.md` (250-300 lines) - WCAG 2.1 AA compliance

**Total Output:** ~1,700-2,050 lines across 5 files

---

## Technology Stack

### Core Frontend Stack
- **Framework:** React 19.x
- **Build Tool:** Vite 7.x
- **Language:** TypeScript 5.x
- **Styling:** Tailwind CSS 4.x
- **UI Library:** shadcn/ui (latest)
- **Icons:** Lucide React
- **Routing:** React Router 7.x
- **State (Server):** React Query 5.x
- **State (Client):** Zustand 4.x
- **Forms:** React Hook Form + Zod validation
- **Tables:** TanStack Table
- **Charts:** Recharts (for dashboard)

---

## Application Pages

### Public Pages
1. **LoginPage** (`/login`)
   - Google OAuth button
   - Domain restriction notice (@your-domain.com only)
   - Redirect after login

### Protected Pages (Require Auth)

2. **HomePage** (`/`)
   - Dashboard overview
   - Quick stats (projects processed this week, pending approvals, etc.)
   - Recent activity feed
   - Quick action buttons

3. **ProcessingPage** (`/processing`)
   - PDF upload form
   - Template type selection (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
   - Template selection
   - Real-time progress tracker
   - Step-by-step status display

4. **ProjectsListPage** (`/projects`)
   - DataTable with search, filters, sorting
   - Filters: emirate, developer, price range, date range, status
   - Bulk actions (export, delete)
   - Pagination
   - Quick view modal

5. **ProjectDetailPage** (`/projects/:id`)
   - View/edit all project fields
   - Image gallery (categorized tabs)
   - Floor plans viewer
   - Revision history timeline
   - Custom fields editor
   - Export button

6. **ContentPreviewPage** (`/projects/:id/preview`)
   - Field-by-field review of generated content
   - Character count per field
   - Regenerate specific fields button
   - "Push to Sheets" button (after QA approval)
   - Side-by-side comparison (extracted vs generated)

7. **ApprovalQueuePage** (`/approvals`)
   - List of projects pending approval
   - Filter by submitter, date
   - Bulk approve/reject
   - Quick review modal with approve/reject/request revision buttons

8. **PublishQueuePage** (`/publishing`)
   - List of approved projects ready for publishing
   - Per-template checklists (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
   - Asset download links
   - Mark as published form (URL input)
   - Publication status tracker

9. **QAPage** (`/qa`)
   - Run QA comparisons
   - Select checkpoint type
   - View QA results (matches, differences, missing, extra)
   - Override QA failures (admin only)

10. **QAHistoryPage** (`/qa/history`)
    - Historical QA results
    - Filter by project, checkpoint type, status
    - View detailed diff reports

11. **PromptsPage** (`/prompts`)
    - List/filter prompts by website, template
    - Search prompts
    - Create new prompt button
    - Edit/delete actions

12. **PromptEditorPage** (`/prompts/:id`)
    - Edit prompt content
    - Preview mode
    - Version diff view
    - Save (creates new version)
    - Change reason input

13. **WorkflowPage** (`/workflow`)
    - Kanban board view
    - Columns: Backlog, In Progress, QA, Done
    - Drag-and-drop cards
    - Assign to user
    - Filter by assignee, priority

14. **HistoryPage** (`/history`)
    - Execution history / audit log
    - Filter by user, action, resource type
    - Export audit log

15. **NotificationsPage** (`/notifications`)
    - List all notifications
    - Mark as read / Mark all as read
    - Filter by type, date
    - Link to referenced resource

16. **ManagerDashboardPage** (`/manager`) - Marketing Managers only
    - Approval metrics and turnaround times
    - Team velocity reports
    - Projects processed statistics
    - Approval queue overview
    - **Note:** This is SEPARATE from AdminDashboardPage - Manager dashboard focuses on approval workflow metrics, while Admin dashboard focuses on system health.

17. **AdminDashboardPage** (`/admin`) - System Admins only
    - User management
    - System health metrics
    - Cost tracking (Anthropic API usage)
    - Job statistics
    - **Note:** This is SEPARATE from ManagerDashboardPage - Admin dashboard focuses on system operations, while Manager dashboard focuses on content workflow.

---

## Component Library

### Layout Components

**`<AppLayout>`**
- Main application layout with header, sidebar, content area
- Responsive (mobile hamburger menu)
- Props: `children`

**`<Header>`**
- App logo
- User profile dropdown
- Notification bell icon
- Quick search bar

**`<Sidebar>`**
- Navigation menu
- Active route highlighting
- Role-based menu items (hide admin links for non-admins)
- Collapsible on mobile

### UI Components (shadcn/ui based)

**`<Button>`**
- Variants: default, destructive, outline, ghost, link
- Sizes: sm, md, lg
- Loading state
- Icon support

**`<Card>`**
- Container for content sections
- Props: `title`, `description`, `footer`, `children`

**`<DataTable>`**
- Generic table with sorting, filtering, pagination
- Column definitions
- Row selection
- Actions menu per row
- Export to CSV button

**`<FileUpload>`**
- Drag-and-drop PDF upload
- File validation (type, size)
- Progress bar during upload
- Error messages

**`<ProgressTracker>`**
- Multi-step progress visualization
- Steps: Upload → Extract → Classify → Generate → QA → Done
- Step states: pending, in_progress, completed, failed
- Current step highlighting

**`<ImageGallery>`**
- Categorized tabs (Interior, Exterior, Amenity, Logo)
- Lightbox on click
- Download all button
- Category limits display

**`<FloorPlanViewer>`**
- Floor plan image display
- Extracted data overlay (bedrooms, sqft)
- Zoom/pan controls

**`<ApprovalCard>`**
- Project summary
- Approve / Reject / Request Revision buttons
- Comments textarea (required for rejection)
- Submitter info

**`<PublicationChecklist>`**
- Per-site checklist items
- Checkbox for each item
- Published URL input
- Mark as published button

**`<KanbanBoard>`**
- Drag-and-drop columns
- Card component for projects
- Add card button
- Filter controls

**`<NotificationBell>`**
- Bell icon with unread count badge
- Dropdown with recent notifications
- "View All" link

**`<PromptEditor>`**
- Code editor with syntax highlighting
- Character counter
- Preview pane
- Version diff viewer

### Form Components

**`<SearchBar>`**
- Full-text search input
- Debounced search
- Clear button

**`<FilterPanel>`**
- Collapsible filter sidebar
- Multiple filter types: select, range, date range
- Apply/Reset buttons

**`<FormField>`**
- Label, input, validation error display
- Integration with React Hook Form

**`<SelectField>`**
- Dropdown select
- Searchable (for long lists)
- Multi-select option

**`<DateRangePicker>`**
- Start and end date selection
- Preset ranges (This Week, Last Month, etc.)

---

## State Management

### Server State (React Query)

**Queries:**
```typescript
// Projects
useProjects(filters: ProjectFilters) // List projects
useProject(id: string) // Get project detail
useProjectHistory(id: string) // Revision history

// Jobs
useJobs() // List user's jobs
useJob(id: string) // Get job status

// Prompts
usePrompts(filters: PromptFilters) // List prompts
usePrompt(id: string) // Get prompt
usePromptVersions(id: string) // Version history

// Approvals
useApprovalQueue() // Pending approvals
useApproval(id: string) // Get approval

// QA
useQAHistory(filters: QAFilters) // QA results
useQAComparison(id: string) // Get QA result

// Notifications
useNotifications() // List notifications
useUnreadCount() // Unread count
```

**Mutations:**
```typescript
// Projects
useCreateProject()
useUpdateProject()
useDeleteProject()

// Jobs
useUploadFile() // Upload PDF and create job

// Prompts
useCreatePrompt()
useUpdatePrompt()

// Approvals
useSubmitForApproval()
useApproveProject()
useRejectProject()

// Notifications
useMarkAsRead()
useMarkAllAsRead()
```

### Client State (Zustand)

**Stores:**
```typescript
// Auth store
interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  login: (token: string) => void
  logout: () => void
}

// UI store
interface UIStore {
  sidebarOpen: boolean
  toggleSidebar: () => void
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
}

// Filter store (persist filters across sessions)
interface FilterStore {
  projectFilters: ProjectFilters
  setProjectFilters: (filters: ProjectFilters) => void
  clearProjectFilters: () => void
}
```

---

## Routing

### Route Configuration

```typescript
// Public routes
/login                          // LoginPage

// Protected routes (require auth)
/                               // HomePage
/processing                     // ProcessingPage
/projects                       // ProjectsListPage
/projects/:id                   // ProjectDetailPage
/projects/:id/preview           // ContentPreviewPage

/approvals                      // ApprovalQueuePage
/publishing                     // PublishQueuePage

/qa                             // QAPage
/qa/history                     // QAHistoryPage

/prompts                        // PromptsPage
/prompts/:id                    // PromptEditorPage

/workflow                       // WorkflowPage
/history                        // HistoryPage
/notifications                  // NotificationsPage

// Role-restricted routes
/manager                        // ManagerDashboardPage (Marketing Managers only)
/admin                          // AdminDashboardPage (System Admins only)

// Fallback
*                               // 404 NotFoundPage
```

### Route Guards

**`<ProtectedRoute>`**
- Checks if user is authenticated
- Redirects to `/login` if not
- Stores intended destination for post-login redirect

**`<AdminRoute>`**
- Checks if user has admin role
- Redirects to `/` if not admin

**`<ManagerRoute>`**
- Checks if user has manager role
- Redirects to `/` if not manager
- Used for ManagerDashboardPage access control

### Navigation Structure

```
Sidebar Menu:
├── Dashboard (/)
├── Processing (/processing)
├── Projects (/projects)
├── Approvals (/approvals) - Badge with count
├── Publishing (/publishing) - Badge with count
├── QA (/qa)
├── Prompts (/prompts)
├── Workflow (/workflow)
├── History (/history)
├── Manager (/manager) - Marketing Managers only
└── Admin (/admin) - System Admins only

Header:
├── Search (global project search)
├── Notifications (bell icon with unread count)
└── User Menu
    ├── Profile
    ├── Settings
    └── Logout
```

---

## Accessibility (WCAG 2.1 AA)

### Requirements

1. **Keyboard Navigation**
   - All interactive elements accessible via keyboard
   - Tab order logical
   - Skip to main content link
   - Focus indicators visible

2. **Screen Reader Support**
   - Semantic HTML (`<nav>`, `<main>`, `<article>`)
   - ARIA labels for icon-only buttons
   - ARIA live regions for dynamic content (notifications, progress)
   - Alt text for all images

3. **Color Contrast**
   - Text: 4.5:1 minimum ratio
   - UI components: 3:1 minimum ratio
   - Don't rely on color alone to convey information

4. **Forms**
   - Labels associated with inputs
   - Error messages announced by screen readers
   - Required fields indicated
   - Validation errors displayed inline

5. **Responsive Design**
   - Mobile-friendly (touch targets 44x44px minimum)
   - No horizontal scrolling
   - Text resizable to 200% without loss of functionality

6. **Error Handling**
   - Clear error messages
   - Suggest corrections
   - Preserve user input on errors

---

## Page Wireframes (ASCII Art)

### HomePage (Dashboard)

```
┌──────────────────────────────────────────────────────────────┐
│ [Logo]  PDP Automation    [Search]    [🔔 3]  [User ▼]      │
├──────────────────────────────────────────────────────────────┤
│         │                                                     │
│ [☰ Nav] │  Dashboard                        [Upload PDF]     │
│         │                                                     │
│ Home    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│ Process │  │  Projects   │ │   Pending   │ │  Published  │  │
│ Project │  │  This Week  │ │  Approvals  │ │  This Month │  │
│ Approve │  │     24      │ │      8      │ │     42      │  │
│ Publish │  └─────────────┘ └─────────────┘ └─────────────┘  │
│ QA      │                                                     │
│ Prompts │  Recent Activity                                   │
│ Workflw │  ┌──────────────────────────────────────────────┐  │
│ History │  │ • Project "Marina Bay" approved   (2h ago)   │  │
│ Admin   │  │ • QA passed for "Downtown Towers" (4h ago)   │  │
│         │  │ • New upload: "Palm Residences"   (5h ago)   │  │
│         │  └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### ProcessingPage

```
┌──────────────────────────────────────────────────────────────┐
│ Upload & Process                                              │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Drag & Drop PDF Here                                   │ │
│  │  or [Browse Files]                                      │ │
│  │                                                          │ │
│  │  Max 50MB • PDF only                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Website: [OPR ▼]                                            │
│  Template: [Standard Residential ▼]                          │
│                                                               │
│  [Generate Content]                                          │
│                                                               │
│  Progress: ▓▓▓▓▓▓░░░░ 60%                                    │
│  Current Step: Extracting images...                          │
│                                                               │
│  Steps:                                                       │
│  ✓ Upload PDF                                                │
│  ✓ Extract text                                              │
│  ◉ Extract images      (in progress)                         │
│  ○ Classify images                                           │
│  ○ Generate content                                          │
│  ○ QA validation                                             │
│  ○ Push to Sheets                                            │
└──────────────────────────────────────────────────────────────┘
```

### ProjectsListPage

```
┌──────────────────────────────────────────────────────────────┐
│ Projects                                      [+ New Project] │
├──────────────────────────────────────────────────────────────┤
│ [Search...]                      [Filters ▼] [Export ▼]      │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ Name          │ Developer │ Location │ Status │ Date     │  │
│ ├───────────────────────────────────────────────────────────│  │
│ │ Marina Bay    │ Emaar     │ Dubai    │ Pub    │ Jan 10   │  │
│ │ Downtown      │ Damac     │ Dubai    │ App    │ Jan 9    │  │
│ │ Palm Res      │ Nakheel   │ Dubai    │ Draft  │ Jan 8    │  │
│ └─────────────────────────────────────────────────────────┘  │
│ [<] [1] [2] [3] [>]                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## Code Examples

### Protected Route Setup

```typescript
// src/components/auth/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
```

### React Query Hook

```typescript
// src/hooks/useProjects.ts
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useProjects(filters: ProjectFilters) {
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => api.projects.list(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
```

---

## Document Structure Standards

Each frontend document must include:
1. Header with last updated date
2. Overview section
3. Technology stack (if applicable)
4. Component/page specifications
5. Code examples (TypeScript)
6. Wireframes (ASCII art)
7. Accessibility notes
8. Related documentation links

---

## Quality Checklist

- ✅ All 5 files created
- ✅ All pages documented with wireframes
- ✅ All components listed with props
- ✅ State management patterns clear
- ✅ Routing configuration complete
- ✅ Accessibility requirements specified
- ✅ Code examples in TypeScript
- ✅ Cross-references valid

---

Begin with `COMPONENT_LIBRARY.md`, then proceed systematically through the other files.