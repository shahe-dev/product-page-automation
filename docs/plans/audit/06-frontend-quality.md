# Frontend Code Quality Audit Report

**Audit Date:** 2026-01-29
**Auditor:** Claude Opus 4.5 (automated)
**Framework:** React 19 / TypeScript / Vite
**Branch:** `feature/phase-11-pymupdf4llm-integration`

---

## Executive Summary

The frontend codebase is well-structured with good use of TypeScript, React Query for server state, and Zustand for client state. However, the audit uncovered **29 findings** spanning type safety gaps, missing error boundaries at page level, complete absence of Zod form validation, several inconsistencies between frontend types and backend/component expectations, and an accessibility gap in the lightbox component. No `any` types were found -- that is a positive signal.

| Severity | Count |
|----------|-------|
| P0 (Critical) | 3 |
| P1 (High) | 8 |
| P2 (Medium) | 12 |
| P3 (Low) | 6 |

---

## P0 -- Critical Findings

### Finding: Auth Store Does Not Restore `isAuthenticated` on Rehydration

- **Severity:** P0
- **File:** `frontend/src/stores/auth-store.ts:42-47`
- **Description:** The Zustand persist middleware only partializes `token` and `user`, but `isAuthenticated` defaults to `false`. On page reload, the store rehydrates `token` and `user` from localStorage, but `isAuthenticated` stays `false` until `login()` is called again. This means every hard refresh logs the user out, as `ProtectedRoute` checks `isAuthenticated` and redirects to `/login`.
- **Evidence:**
```ts
partialize: (state) => ({
  token: state.token,
  user: state.user,
}),
// isAuthenticated is NOT persisted and defaults to false
```
`ProtectedRoute` then does:
```ts
if (!isAuthenticated) {
  return <Navigate to="/login" state={{ from: location }} replace />
}
```
- **Fix:** Either persist `isAuthenticated`, or derive it from `token` and `user` using `onRehydrateStorage`:
```ts
partialize: (state) => ({
  token: state.token,
  user: state.user,
  isAuthenticated: state.isAuthenticated,
}),
```
Or better -- make `isAuthenticated` a derived getter:
```ts
// Replace isAuthenticated state with a derive:
get isAuthenticated() {
  return !!get().token && !!get().user;
}
```

---

### Finding: ProjectStatus Type Mismatch Between Types and Components

- **Severity:** P0
- **File:** `frontend/src/types/index.ts:40-48` vs `frontend/src/components/projects/ProjectFilters.tsx:25-35` vs `frontend/src/components/projects/ProjectDetail.tsx:170-173`
- **Description:** The canonical `ProjectStatus` union type defines 8 values: `draft`, `pending_approval`, `approved`, `revision_requested`, `publishing`, `published`, `qa_verified`, `complete`. But `ProjectFilters.tsx` uses an entirely different set: `draft`, `processing`, `extracted`, `structured`, `content_generated`, `review`, `approved`, `published`, `failed`. And `ProjectDetail.tsx` references `content_generated`, `structured`, `failed` which do not exist in the `ProjectStatus` type. The `QAPage.tsx` filters by `content_generated` and `review` -- also not in the type. This will cause TypeScript narrowing failures or runtime mismatches with the backend.
- **Evidence:**
```ts
// types/index.ts
export type ProjectStatus =
  | "draft" | "pending_approval" | "approved" | "revision_requested"
  | "publishing" | "published" | "qa_verified" | "complete"

// ProjectFilters.tsx -- STATUSES array:
{ value: "processing", label: "Processing" },
{ value: "extracted", label: "Extracted" },
{ value: "structured", label: "Structured" },
{ value: "content_generated", label: "Content Generated" },
{ value: "review", label: "Review" },
{ value: "failed", label: "Failed" },

// ProjectDetail.tsx line 170-173:
const canSubmitForReview =
  project.status === "content_generated" || project.status === "structured"
const canEdit = project.status === "draft" || project.status === "failed"
```
- **Fix:** Align `ProjectStatus` type to include all statuses actually used across the application, matching the backend database schema. Update `StatusBadge` labels accordingly.

---

### Finding: JobStatus Type Mismatch -- `running` Used But Not Defined

- **Severity:** P0
- **File:** `frontend/src/components/upload/JobStatus.tsx:27-30` vs `frontend/src/types/index.ts:79`
- **Description:** The `JobStatus` type defines: `"pending" | "processing" | "completed" | "failed" | "cancelled"`. But `JobStatus.tsx`'s `JOB_STATUS_CONFIG` map includes a `running` key and omits `processing`. When a job comes back from the backend with `status: "processing"`, the component will crash or show undefined styling because `JOB_STATUS_CONFIG["processing"]` does not exist.
- **Evidence:**
```ts
// types/index.ts
export type JobStatus = "pending" | "processing" | "completed" | "failed" | "cancelled"

// JobStatus.tsx JOB_STATUS_CONFIG:
running: {
  label: "Running",
  className: "bg-blue-100 ..."
},
// "processing" key is MISSING from the map
```
- **Fix:** Replace `running` with `processing` in `JOB_STATUS_CONFIG`, or add both with the same config if the backend can return either value.

---

## P1 -- High Findings

### Finding: ReactQueryDevtools Bundled in Production

- **Severity:** P1
- **File:** `frontend/src/App.tsx:3,60`
- **Description:** `ReactQueryDevtools` is imported unconditionally and rendered in all environments. This adds ~74KB to the production bundle. React Query provides a lazy-loading wrapper for this purpose.
- **Evidence:**
```tsx
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
// ...
<ReactQueryDevtools initialIsOpen={false} />
```
- **Fix:** Conditionally import using the lazy variant:
```tsx
const ReactQueryDevtools = import.meta.env.DEV
  ? React.lazy(() =>
      import("@tanstack/react-query-devtools").then((mod) => ({
        default: mod.ReactQueryDevtools,
      }))
    )
  : () => null

// In render:
<Suspense fallback={null}>
  <ReactQueryDevtools initialIsOpen={false} />
</Suspense>
```

---

### Finding: Error Boundary Only at Root Level

- **Severity:** P1
- **File:** `frontend/src/App.tsx:56-63`
- **Description:** A single `ErrorBoundary` wraps the entire app. If any page component throws, the entire app is replaced with the error fallback, destroying all navigation context. Page-level error boundaries should catch errors within individual routes, allowing the user to navigate away without a full app crash.
- **Evidence:**
```tsx
// App.tsx -- only boundary
<ErrorBoundary>
  <QueryClientProvider client={queryClient}>
    <Router />
    ...
  </QueryClientProvider>
</ErrorBoundary>
```
No `ErrorBoundary` in `AppLayout`, route definitions, or individual pages.
- **Fix:** Add an `ErrorBoundary` wrapper inside `AppLayout` around `<Outlet />`:
```tsx
<main id="main-content" className="flex-1 overflow-y-auto p-6" tabIndex={-1}>
  <ErrorBoundary>
    <Outlet />
  </ErrorBoundary>
</main>
```

---

### Finding: No Zod (or Any) Form Validation

- **Severity:** P1
- **File:** Multiple -- `PromptCreateDialog.tsx`, `PromptEditor.tsx`, `FileUpload.tsx`, `QAPage.tsx`
- **Description:** Zero Zod schemas exist in the frontend codebase. All forms use manual `if (!name.trim())` checks or HTML `required` attributes. This means no structured validation, no type-safe parsing of form data, and no guarantee that data sent to the backend matches API constraints (e.g., character limits, enum values, string length limits).
- **Evidence:**
```bash
# grep for zod in frontend/src returns zero results
```
`PromptCreateDialog.tsx` validates with:
```tsx
if (!name.trim() || !content.trim()) return
```
No character limit validation, no template_type enum validation.
- **Fix:** Install `zod` and create validation schemas for each form:
```ts
import { z } from "zod"

export const createPromptSchema = z.object({
  name: z.string().min(1).max(255),
  template_type: z.enum(["opr", "mpp", "adop", "adre", "aggregators", "commercial"]),
  content_variant: z.string().optional(),
  content: z.string().min(1),
  character_limit: z.number().int().positive().optional(),
})
```
Integrate with `react-hook-form` + `@hookform/resolvers/zod` for the form components.

---

### Finding: Double Retry Logic -- Axios Interceptor + React Query

- **Severity:** P1
- **File:** `frontend/src/lib/api.ts:62-76` and `frontend/src/lib/query-client.ts:8-9`
- **Description:** The Axios response interceptor retries 5xx errors up to 3 times with exponential backoff. Separately, React Query's default config retries failed queries 3 times. This means a single failed request can be retried up to **12 times** (3 Axios retries x 4 React Query attempts) before the user sees an error. For a 500 error with 2s/4s/8s backoff per Axios round, worst case is ~168 seconds of silent retrying.
- **Evidence:**
```ts
// api.ts interceptor:
if (config._retryCount < 3) { ... }

// query-client.ts:
retry: 3,
retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
```
- **Fix:** Pick one retry layer. Recommended: remove the Axios retry interceptor and rely solely on React Query's retry config, which is better integrated with the UI (loading states, error handling).

---

### Finding: `useJobs()` Polls Every 5 Seconds Globally

- **Severity:** P1
- **File:** `frontend/src/hooks/queries/use-jobs.ts:9`
- **Description:** `useJobs()` has `refetchInterval: 5000`, meaning it fires a network request every 5 seconds on any page that mounts this hook. Combined with `useJob()` polling at 2 seconds, the ProcessingPage makes at minimum 2 API calls every 5 seconds plus 1 every 2 seconds. This is aggressive polling that continues even when the user is on an unrelated page if the component stays mounted.
- **Evidence:**
```ts
export function useJobs() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: api.jobs.list,
    refetchInterval: 5000, // Always polls
  })
}
```
- **Fix:** Make polling conditional on component visibility or active jobs:
```ts
refetchInterval: (query) => {
  const data = query.state.data;
  const hasActiveJobs = data?.jobs?.some(
    (j) => j.status === "pending" || j.status === "processing"
  );
  return hasActiveJobs ? 5000 : false;
},
```

---

### Finding: `setAuthToken` and `clearAuthToken` Are No-Ops

- **Severity:** P1
- **File:** `frontend/src/lib/api.ts:82-90`
- **Description:** These functions do nothing but are called from the auth store's `login()` and `logout()` methods. This is dead code that creates a false sense of security. If someone later expects these to actually configure the token, bugs will follow.
- **Evidence:**
```ts
function setAuthToken(_token: string) {
  // Token is read from persisted auth-storage by the request interceptor.
  // No need to set on axios defaults (avoids dual-state).
}

function clearAuthToken() {
  // Token is cleared from persisted auth-storage by the auth store.
  // No need to clear from axios defaults.
}
```
- **Fix:** Remove these functions and remove the calls from `auth-store.ts`. If they exist as documentation of the design decision, add a comment in the auth store instead.

---

### Finding: Inconsistent API Client Usage Across Hooks

- **Severity:** P1
- **File:** `frontend/src/hooks/queries/use-approvals.ts:4`, `frontend/src/hooks/queries/use-dashboard.ts:3` vs others
- **Description:** `use-approvals.ts` and `use-dashboard.ts` import `apiClient` (the raw Axios instance) and make direct HTTP calls, while all other hooks use the `api` namespace object. This inconsistency means these two hooks bypass the structured API layer and its type-safe method signatures.
- **Evidence:**
```ts
// use-approvals.ts
import { apiClient } from "@/lib/api"
// ...
apiClient.get<Approval[]>("/workflow/approvals", { params: filters })

// use-projects.ts (correct pattern)
import { api } from "@/lib/api"
// ...
api.projects.list(filters)
```
- **Fix:** Add `approvals` and `dashboard` namespaces to the `api` object in `lib/api.ts` and update the hooks to use them consistently.

---

## P2 -- Medium Findings

### Finding: `Approval` Type Defined Inline in Hook Instead of Types File

- **Severity:** P2
- **File:** `frontend/src/hooks/queries/use-approvals.ts:5-15`
- **Description:** The `Approval` and `ApprovalFilters` interfaces are defined directly in the hook file rather than in `types/index.ts`. This breaks the project convention where all API types live in a single location and makes it harder to reuse these types in components.
- **Evidence:**
```ts
// use-approvals.ts
export interface Approval {
  id: string
  project_id: string
  // ...
}
```
- **Fix:** Move `Approval` and `ApprovalFilters` interfaces to `frontend/src/types/index.ts` and import from there.

---

### Finding: `QAIssue` Type Defined Inline in Component Instead of Types File

- **Severity:** P2
- **File:** `frontend/src/components/qa/IssueList.tsx:17-26`
- **Description:** Same issue as above. `QAIssue` is defined in and exported from the `IssueList` component file, then re-exported from `qa/index.ts`. This type should live in `types/index.ts`.
- **Evidence:**
```ts
// IssueList.tsx
export interface QAIssue {
  id: string
  field: string
  // ...
}

// qa/index.ts
export type { QAIssue } from "./IssueList"
```
- **Fix:** Move to `types/index.ts`.

---

### Finding: `QAPage.tsx` Uses Hardcoded Mock Data in Production Component

- **Severity:** P2
- **File:** `frontend/src/pages/QAPage.tsx:29-99`
- **Description:** The `generateMockQAData` function returns hardcoded mock data for the QA review flow. This is embedded in the production page component with no feature flag or environment check. Users will see fake data.
- **Evidence:**
```ts
const generateMockQAData = (_projectId: string) => {
  const mockSourceData = {
    project_name: "Marina Heights Tower",
    // ...
  }
  // ...
}
```
- **Fix:** Replace with actual API integration or gate behind `import.meta.env.DEV` with a clear TODO.

---

### Finding: `ProjectDetail.tsx` Uses Hardcoded Mock Data

- **Severity:** P2
- **File:** `frontend/src/components/projects/ProjectDetail.tsx:41-104`
- **Description:** `MOCK_IMAGES`, `MOCK_FLOOR_PLANS`, and `MOCK_ACTIVITY` arrays are hardcoded and always rendered. Same issue as above.
- **Evidence:**
```ts
const MOCK_IMAGES = [
  { id: "1", url: "/placeholder-exterior.jpg", ... },
]
const MOCK_FLOOR_PLANS = [ ... ]
const MOCK_ACTIVITY = [ ... ]
```
- **Fix:** Fetch from API or clearly gate as dev-only.

---

### Finding: QAPage Sets State During Render

- **Severity:** P2
- **File:** `frontend/src/pages/QAPage.tsx:124-126`
- **Description:** The component calls `setIssuesState(qaData.issues)` during render (outside any event handler or effect). This violates React's rules and will cause an infinite re-render loop in strict mode or unpredictable behavior.
- **Evidence:**
```tsx
// Initialize issues when project is selected
if (qaData && issuesState.length === 0 && selectedProjectId) {
  setIssuesState(qaData.issues)
}
```
- **Fix:** Move into a `useEffect`:
```ts
useEffect(() => {
  if (qaData && selectedProjectId) {
    setIssuesState(qaData.issues)
  }
}, [selectedProjectId, qaData])
```

---

### Finding: `useProjects` Missing `staleTime` Consistency for List vs Detail

- **Severity:** P2
- **File:** `frontend/src/hooks/queries/use-projects.ts:6-11` vs `14-19`
- **Description:** `useProjects` (list) has `staleTime: 5 * 60 * 1000` but `useProject` (single) has no `staleTime`, meaning it uses the global default (also 5 min). This is fine but fragile -- if the global default changes, the single-project hook behavior changes silently. More importantly, the `useUpdateProject` optimistic update pattern means the list query may show stale data for up to 5 minutes after an update because only the individual project query is invalidated in `onSettled`.
- **Evidence:**
```ts
// useUpdateProject -- only invalidates the specific project
onSettled: (_data, _error, { id }) => {
  queryClient.invalidateQueries({ queryKey: ["projects", id] })
},
```
- **Fix:** Also invalidate the list query in `onSettled`:
```ts
onSettled: (_data, _error, { id }) => {
  queryClient.invalidateQueries({ queryKey: ["projects", id] })
  queryClient.invalidateQueries({ queryKey: ["projects"] })
},
```

---

### Finding: `KanbanBoard` Fetches All Projects (`per_page: 1000`)

- **Severity:** P2
- **File:** `frontend/src/components/workflow/KanbanBoard.tsx:64-66`
- **Description:** The Kanban board fetches up to 1000 projects in a single request. This will cause performance issues and slow load times as the project count grows. The board does client-side filtering, so the full dataset is held in memory.
- **Evidence:**
```ts
const { data, isLoading, error, refetch } = useProjects({
  per_page: 1000,
})
```
- **Fix:** Implement server-side filtering or add a more reasonable limit with pagination, or use a virtual scroll for the column contents.

---

### Finding: `ProcessingPage` Auto-Navigates After 2s Without Cancel

- **Severity:** P2
- **File:** `frontend/src/pages/ProcessingPage.tsx:35-41`
- **Description:** When a job completes, the page auto-navigates to the project detail page after a 2-second delay using `setTimeout`. There is no way for the user to cancel this, and the timer is not cleared on unmount, which could cause a React state update on an unmounted component.
- **Evidence:**
```ts
useEffect(() => {
  if (activeJob?.status === "completed" && activeJob.project_id) {
    setTimeout(() => {
      navigate(`/projects/${activeJob.project_id}`)
    }, 2000)
  }
}, [activeJob?.status, activeJob?.project_id, navigate])
```
- **Fix:** Store the timeout ID and clear it in the effect cleanup:
```ts
useEffect(() => {
  if (activeJob?.status === "completed" && activeJob.project_id) {
    const timeoutId = setTimeout(() => {
      navigate(`/projects/${activeJob.project_id}`)
    }, 2000)
    return () => clearTimeout(timeoutId)
  }
}, [activeJob?.status, activeJob?.project_id, navigate])
```

---

### Finding: `ComparisonView` Drag Handler Missing `mouseup` on Document

- **Severity:** P2
- **File:** `frontend/src/components/qa/ComparisonView.tsx:29-45`
- **Description:** The split-pane drag logic listens for `onMouseUp` and `onMouseLeave` on the container div. If the user drags the handle and releases the mouse outside the container (e.g., over a different element or outside the browser window), the drag state is never cleared and the panel keeps resizing on subsequent mouse movements.
- **Evidence:**
```tsx
<div
  onMouseMove={handleMouseMove}
  onMouseUp={handleMouseUp}
  onMouseLeave={handleMouseUp}
>
```
- **Fix:** When `isDragging` becomes true, attach `mousemove` and `mouseup` listeners to `document` via `useEffect`, and clean them up. This is the standard pattern for drag interactions.

---

### Finding: `PromptEditor` Uses `alert()` for Validation

- **Severity:** P2
- **File:** `frontend/src/components/prompts/PromptEditor.tsx:110`
- **Description:** The save handler uses `window.alert()` for validation feedback. This blocks the main thread and provides a poor UX. The app already has toast infrastructure via Sonner.
- **Evidence:**
```ts
if (!changeReason.trim()) {
  alert("Please provide a change reason")
  return
}
```
- **Fix:** Replace with toast notification:
```ts
import { toast } from "sonner"
// ...
if (!changeReason.trim()) {
  toast.error("Please provide a change reason")
  return
}
```

---

### Finding: `KanbanBoard` Uses `alert()` for Error/Validation

- **Severity:** P2
- **File:** `frontend/src/components/workflow/KanbanBoard.tsx:105,132`
- **Description:** Same issue -- `alert()` is used for invalid transitions and failed updates.
- **Evidence:**
```ts
alert(`Cannot move from ${project.status} to ${targetStatus}. Invalid transition.`)
// ...
alert("Failed to update project status. Please try again.")
```
- **Fix:** Replace with `toast.error()` from Sonner.

---

### Finding: Lightbox Missing Focus Trap and ARIA Attributes

- **Severity:** P2
- **File:** `frontend/src/components/projects/ImageGallery.tsx:148-225`
- **Description:** The lightbox overlay is rendered as a plain `<div>` without `role="dialog"`, `aria-modal="true"`, or `aria-label`. There is no focus trap, so keyboard users can tab behind the lightbox to interact with hidden content. The close button lacks an explicit `aria-label`.
- **Evidence:**
```tsx
<div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center">
  <Button variant="ghost" size="icon" ... onClick={closeLightbox}>
    <X className="size-6" />
  </Button>
```
No `role="dialog"`, no `aria-modal`, no `aria-label` on close button.
- **Fix:** Add ARIA attributes and implement a focus trap:
```tsx
<div
  role="dialog"
  aria-modal="true"
  aria-label="Image lightbox"
  className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
>
  <Button ... aria-label="Close lightbox">
```
Consider using Radix Dialog or a focus-trap library.

---

## P3 -- Low Findings

### Finding: `ConfirmDialog` Handler Wrapper Is Unnecessary

- **Severity:** P3
- **File:** `frontend/src/components/common/ConfirmDialog.tsx:34-36`
- **Description:** `handleConfirm` wraps `onConfirm` with no additional logic. This is dead indirection.
- **Evidence:**
```ts
const handleConfirm = () => {
  onConfirm();
};
```
- **Fix:** Pass `onConfirm` directly to the button's `onClick`.

---

### Finding: `hasRole` and `hasAnyRole` Recreated on Every Render

- **Severity:** P3
- **File:** `frontend/src/hooks/use-auth.ts:9-15`
- **Description:** `hasRole` and `hasAnyRole` are plain functions created on every render. While not expensive, wrapping in `useCallback` with `[user]` dependency would avoid unnecessary child re-renders if passed as props.
- **Evidence:**
```ts
const hasRole = (role: UserRole): boolean => {
  return user?.role === role
}
const hasAnyRole = (roles: UserRole[]): boolean => {
  return user ? roles.includes(user.role) : false
}
```
- **Fix:** Wrap with `useCallback`:
```ts
const hasRole = useCallback((role: UserRole) => user?.role === role, [user])
```

---

### Finding: UI Store Persists Toasts and Modal Stack via Missing Exclusion

- **Severity:** P3
- **File:** `frontend/src/stores/ui-store.ts:83-89`
- **Description:** The `partialize` correctly excludes `toasts`, `modalStack`, and `globalLoading` from persistence. This is correct, but if someone adds a new transient field and forgets to exclude it, it will be persisted. Consider using a whitelist pattern more explicitly documented.
- **Evidence:**
```ts
partialize: (state) => ({
  sidebarOpen: state.sidebarOpen,
  theme: state.theme,
}),
```
This is actually correct. No fix needed -- noting for documentation awareness.

---

### Finding: `SearchBar` Debounce Timeout Ref Type Should Use `ReturnType<typeof setTimeout>`

- **Severity:** P3
- **File:** `frontend/src/components/common/SearchBar.tsx:21`
- **Description:** `timeoutRef` is typed as `number | null`, which works in browser environments (where `setTimeout` returns `number`). However, the more portable pattern is `ReturnType<typeof setTimeout>` which works in both Node and browser type environments. This is a minor type hygiene issue.
- **Evidence:**
```ts
const timeoutRef = useRef<number | null>(null)
```
- **Fix:**
```ts
const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
```

---

### Finding: `DataTable` Skeleton Rows Use Index as Key

- **Severity:** P3
- **File:** `frontend/src/components/common/DataTable.tsx:122-130`
- **Description:** The skeleton loading rows use array indices as keys. While acceptable for static skeleton content (it never reorders), it is a lint warning in some configurations.
- **Evidence:**
```tsx
Array.from({ length: pagination?.pageSize || 5 }).map((_, i) => (
  <tr key={i} className="border-b">
```
- **Fix:** Acceptable as-is since skeletons are static. Suppress lint warning with a comment if needed.

---

### Finding: No Error Handling Callbacks on Mutation Hooks

- **Severity:** P3
- **File:** `frontend/src/hooks/queries/use-prompts.ts:43-53`, `use-notifications.ts:24-29`
- **Description:** Mutations like `useUpdatePrompt`, `useMarkAsRead`, `useMarkAllAsRead`, `useCreatePrompt` do not have `onError` callbacks. Error handling is left to the consuming component. This is acceptable if all consumers handle errors, but several components only use `console.error` in their `catch` blocks without user-facing feedback (e.g., `VersionHistory.tsx:47`, `PromptEditor.tsx:123`).
- **Evidence:**
```ts
// use-prompts.ts useUpdatePrompt -- no onError
export function useUpdatePrompt() {
  return useMutation({
    mutationFn: ...,
    onSuccess: ..., // no onError
  })
}

// VersionHistory.tsx
} catch (error) {
  console.error("Failed to restore version:", error)
}
```
- **Fix:** Add global `onError` in mutation defaults or add toast notifications in each mutation's `onError`.

---

## Checklist Summary

| # | Check Item | Status | Notes |
|---|-----------|--------|-------|
| 1 | No `any` types | PASS | Zero `any` types found in `src/` |
| 2 | React Query cache keys include dependencies | PASS | All hooks include filters/IDs in query keys |
| 3 | React Query `staleTime` configured | PARTIAL | Some hooks set explicit staleTime, others rely on global default. `useProject` and `usePromptVersions` have no explicit staleTime |
| 4 | Error boundaries at page level | FAIL | Only root-level ErrorBoundary exists |
| 5 | Loading states for async operations | PASS | All data-fetching components show loading spinners or skeletons |
| 6 | Empty states for zero-item lists | PASS | `EmptyState` component used throughout (projects, prompts, jobs, versions) |
| 7 | Form validation with Zod | FAIL | Zero Zod schemas. All validation is ad-hoc |
| 8 | `useEffect` cleanup | PARTIAL | `SearchBar` and `PromptEditor` clean up properly. `ProcessingPage` auto-nav timeout is not cleaned up |
| 9 | Memory leaks (listeners/intervals) | PASS | `addEventListener` calls have matching `removeEventListener` in cleanup |
| 10 | Accessibility (aria-labels, keyboard nav) | PARTIAL | `LoadingSpinner` has `role="status"` and `aria-label`. Sidebar has `aria-label="Main navigation"`. Skip-to-content link present. Lightbox missing focus trap and ARIA. Icon-only buttons mostly have `sr-only` spans |
| 11 | Dead code | PARTIAL | `setAuthToken`/`clearAuthToken` are no-ops. `isSidebarCollapsed` in QAPage is unused state logic never connected to layout |
| 12 | React Query devtools dev-only | FAIL | Bundled unconditionally |
| 13 | Zustand store design | PARTIAL | Good partialize usage. `isAuthenticated` not derived/persisted (P0 bug). Filter store persists search text to localStorage unnecessarily |
| 14 | Consistent error handling | PARTIAL | Mix of `apiClient` vs `api` usage. No global mutation error handler |
| 15 | Type safety vs backend | FAIL | `ProjectStatus` and `JobStatus` mismatches between type definitions and actual usage in components |
