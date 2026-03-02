# Agent Brief: DEV-STATE-001

**Agent ID:** DEV-STATE-001
**Agent Name:** State Management Agent
**Type:** Development
**Phase:** 4 - Frontend
**Context Budget:** 50,000 tokens

---

## Mission

Implement global state management with Zustand, API client setup, and custom hooks for data fetching.

---

## Documentation to Read

### Primary
1. `docs/03-frontend/STATE_MANAGEMENT.md` - State architecture

### Secondary
1. `docs/04-backend/API_ENDPOINTS.md` - API specification

---

## Dependencies

**Upstream:** DEV-FESETUP-001
**Downstream:** All page agents

---

## Outputs

### `frontend/src/stores/index.ts`
### `frontend/src/stores/ui-store.ts`
### `frontend/src/lib/api.ts`
### `frontend/src/hooks/useProjects.ts`
### `frontend/src/hooks/useJobs.ts`
### `frontend/src/hooks/useAuth.ts`

---

## Acceptance Criteria

1. **Store Index:**
   - Export all stores
   - Store composition helpers
   - Devtools integration

2. **UI Store:**
   - Sidebar collapsed state
   - Theme preference
   - Toast notifications queue
   - Modal stack management
   - Loading indicators

3. **API Client:**
   - Axios instance with base URL
   - Auth interceptor (add token)
   - Error interceptor (handle 401)
   - Request/response logging (dev)
   - Retry logic for 5xx

4. **useProjects Hook:**
   - Fetch project list (with cache)
   - Fetch single project
   - Create project
   - Update project
   - Delete project
   - Optimistic updates

5. **useJobs Hook:**
   - Fetch job list
   - Fetch job status
   - Create job
   - Cancel job
   - Subscribe to updates

6. **useAuth Hook:**
   - Current user
   - Login action
   - Logout action
   - Refresh token
   - Permission check

7. **Performance:**
   - Memoized selectors
   - Avoid unnecessary re-renders
   - Proper cache invalidation

---

## QA Pair: QA-STATE-001

---

**Begin execution.**
