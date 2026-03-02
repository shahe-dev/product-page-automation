# Agent Brief: DEV-AUTHUI-001

**Agent ID:** DEV-AUTHUI-001
**Agent Name:** Auth UI Agent
**Type:** Development
**Phase:** 4 - Frontend
**Context Budget:** 50,000 tokens

---

## Mission

Implement authentication UI including login page, auth state management, and protected route wrapper.

---

## Documentation to Read

### Primary
1. `docs/03-frontend/PAGE_SPECIFICATIONS.md` - Login page spec
2. `docs/03-frontend/STATE_MANAGEMENT.md` - Auth store design

### Secondary
1. `docs/05-integrations/GOOGLE_OAUTH_SETUP.md` - OAuth flow

---

## Dependencies

**Upstream:** DEV-FESETUP-001
**Downstream:** DEV-DASHBOARD-001, DEV-UPLOAD-001

---

## Outputs

### `frontend/src/pages/LoginPage.tsx`
### `frontend/src/stores/auth-store.ts`
### `frontend/src/lib/auth.ts`
### `frontend/src/components/layout/ProtectedRoute.tsx`

---

## Acceptance Criteria

1. **Login Page:**
   - Clean, centered design
   - Google Sign-In button
   - Loading state during auth
   - Error display for failures
   - Redirect after success

2. **Auth Store (Zustand):**
   - User state (id, email, name, role)
   - isAuthenticated flag
   - isLoading flag
   - Login/logout actions
   - Token management
   - Persist to localStorage

3. **Auth Utilities:**
   - Token refresh logic
   - API client with auth headers
   - Token expiry detection

4. **Protected Route:**
   - Redirect to login if unauthenticated
   - Show loading during auth check
   - Pass user context to children

5. **Security:**
   - No sensitive data in localStorage
   - Token refresh before expiry
   - Clear state on logout

---

## QA Pair: QA-AUTHUI-001

---

**Begin execution.**
