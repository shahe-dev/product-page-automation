# Frontend Security Audit Report

**Project:** PDP Automation v.3
**Scope:** React/TypeScript frontend -- auth flows, token management, XSS, route protection
**Date:** 2026-01-29
**Auditor:** Claude (automated security review)
**Branch:** `feature/phase-11-pymupdf4llm-integration`

---

## Executive Summary

The frontend has a functional OAuth-based authentication flow using Google OAuth 2.0 with JWT tokens. However, there are **3 P0 (critical)** and **4 P1 (high)** findings that must be addressed before production deployment. The most severe issues are: JWT tokens stored in `localStorage` (XSS-exfiltrable), missing OAuth `state` parameter (CSRF during login), and the `ManagerRoute` guard checking the wrong role.

### Finding Counts

| Severity | Count |
|----------|-------|
| P0 (Critical) | 3 |
| P1 (High) | 4 |
| P2 (Medium) | 3 |
| P3 (Low) | 3 |
| **Total** | **13** |

---

## P0 -- Critical Findings

---

## Finding: JWT Token Stored in localStorage (XSS-Exfiltrable)

- **Severity:** P0
- **File:** `frontend/src/stores/auth-store.ts:17-49` and `frontend/src/lib/api.ts:32`
- **Description:** The Zustand auth store uses `persist` middleware with the key `"auth-storage"`, which serializes the JWT access token into `localStorage`. Any XSS vulnerability -- even a single injected script from a third-party dependency -- can read `localStorage.getItem("auth-storage")` and exfiltrate the token. The request interceptor in `api.ts` also reads directly from `localStorage` on every request (line 32). This is the single most impactful vulnerability in the frontend: a stolen JWT grants full API access as the victim user.
- **Evidence:**
  ```typescript
  // auth-store.ts lines 41-48
  {
    name: "auth-storage",
    partialize: (state) => ({
      token: state.token,
      user: state.user,
    }),
  },

  // api.ts lines 32-38
  const token = localStorage.getItem("auth-storage")
  if (token) {
    try {
      const parsed = JSON.parse(token)
      if (parsed?.state?.token) {
        config.headers.Authorization = `Bearer ${parsed.state.token}`
      }
    } catch {
      // ignore parse errors
    }
  }
  ```
- **Fix:** Migrate token delivery to `httpOnly`, `Secure`, `SameSite=Strict` cookies set by the backend on the `/auth/google` and `/auth/me` endpoints. Remove the token from the Zustand persisted state entirely. The browser will attach cookies automatically; the Axios interceptor should stop manually setting the `Authorization` header and instead rely on `withCredentials: true`. If httpOnly cookies are not feasible in the short term, at minimum move to `sessionStorage` (reduces risk from persistent XSS but does not eliminate it).

---

## Finding: OAuth Flow Missing `state` Parameter (Login CSRF)

- **Severity:** P0
- **File:** `frontend/src/lib/auth.ts:63-81` and `frontend/src/pages/AuthCallbackPage.tsx:29-38`
- **Description:** The `buildGoogleOAuthUrl` function constructs the Google OAuth authorization URL without a `state` parameter. The `AuthCallbackPage` does not validate any `state` parameter on the callback. This enables a classic Login CSRF attack: an attacker can craft an authorization URL with their own Google `code`, trick the victim into visiting it, and cause the victim's browser to authenticate as the attacker's account. This can lead to data exposure if the victim then uploads sensitive documents under the attacker-controlled identity.
- **Evidence:**
  ```typescript
  // auth.ts lines 71-78 -- no state parameter
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "consent",
  })

  // AuthCallbackPage.tsx lines 29-38 -- no state validation
  const code = searchParams.get("code")
  if (!code) return

  api.auth
    .googleLogin(code)
    .then((response) => {
      login(response.access_token, response.user)
      // ...
    })
  ```
- **Fix:** Generate a cryptographically random `state` value using `crypto.getRandomValues()`, store it in `sessionStorage`, include it in the OAuth URL as the `state` parameter, and validate it in `AuthCallbackPage` before exchanging the code. Reject the callback if `state` does not match.
  ```typescript
  // In buildGoogleOAuthUrl:
  const state = crypto.randomUUID()
  sessionStorage.setItem("oauth_state", state)
  params.set("state", state)

  // In AuthCallbackPage:
  const expectedState = sessionStorage.getItem("oauth_state")
  const receivedState = searchParams.get("state")
  if (!expectedState || expectedState !== receivedState) {
    setApiError("Invalid state parameter. Authentication rejected.")
    return
  }
  sessionStorage.removeItem("oauth_state")
  ```

---

## Finding: ManagerRoute Checks Wrong Role (Broken Access Control)

- **Severity:** P0
- **File:** `frontend/src/components/auth/ManagerRoute.tsx:16`
- **Description:** The `ManagerRoute` component is intended to restrict access to users with the `"manager"` role, but it actually checks for `user?.role !== "admin"`. This means managers are denied access to their own dashboard, while admins (who have a separate `AdminRoute`) are the only ones granted entry. Additionally, the `UserRole` type is defined as `"admin" | "user"` with no `"manager"` value, so even if the check were corrected to `"manager"`, no user could ever match. This is a logic bug that renders the entire manager authorization path non-functional.
- **Evidence:**
  ```typescript
  // ManagerRoute.tsx line 16 -- checks for admin instead of manager
  if (user?.role !== "admin") {
    return <Navigate to="/" replace />
  }

  // types/index.ts line 14 -- no "manager" role exists
  export type UserRole = "admin" | "user"
  ```
- **Fix:** Two changes are required:
  1. Add `"manager"` to the `UserRole` union: `export type UserRole = "admin" | "manager" | "user"`
  2. Fix the `ManagerRoute` guard to accept both managers and admins:
  ```typescript
  if (user?.role !== "manager" && user?.role !== "admin") {
    return <Navigate to="/" replace />
  }
  ```

---

## P1 -- High Findings

---

## Finding: No Token Refresh on 401 -- Immediate Logout Instead

- **Severity:** P1
- **File:** `frontend/src/lib/api.ts:53-58` and `frontend/src/lib/auth.ts:45-61`
- **Description:** The response interceptor handles 401 errors by immediately clearing `localStorage` and dispatching a logout event. It does not attempt to refresh the access token before logging the user out. The `refreshAccessToken` function exists in `auth.ts` (lines 45-61) but is never called by the interceptor or anywhere else in the codebase. This means any token expiration results in immediate session termination with no retry, which is a poor user experience and a security concern because it incentivizes using long-lived tokens as a workaround.
- **Evidence:**
  ```typescript
  // api.ts lines 53-58 -- hard logout, no refresh attempt
  if (error.response?.status === 401) {
    localStorage.removeItem("auth-storage")
    window.dispatchEvent(new CustomEvent("auth:logout"))
    return Promise.reject(error)
  }
  ```
- **Fix:** Before logging out, attempt a token refresh. If refresh succeeds, retry the original request. If refresh fails, then logout.
  ```typescript
  if (error.response?.status === 401 && !config._retry) {
    config._retry = true
    try {
      const newToken = await refreshAccessToken()
      config.headers.Authorization = `Bearer ${newToken}`
      return apiClient(config)
    } catch {
      localStorage.removeItem("auth-storage")
      window.dispatchEvent(new CustomEvent("auth:logout"))
      return Promise.reject(error)
    }
  }
  ```

---

## Finding: Refresh Token Exposed in Frontend Type and Potentially in API Response

- **Severity:** P1
- **File:** `frontend/src/types/index.ts:18`
- **Description:** The `AuthResponse` type includes a `refresh_token` field. If the backend sends the refresh token in the JSON response body, it will be accessible to JavaScript and therefore vulnerable to XSS exfiltration. Refresh tokens are long-lived credentials that should never be exposed to client-side JavaScript. They should only travel in `httpOnly` cookies or be managed entirely server-side.
- **Evidence:**
  ```typescript
  // types/index.ts lines 16-22
  export interface AuthResponse {
    access_token: string
    refresh_token: string    // <-- should not be in JS-accessible response
    token_type: string
    expires_in: number
    user: User
  }
  ```
- **Fix:** Remove `refresh_token` from the `AuthResponse` interface. On the backend, deliver the refresh token only via an `httpOnly` cookie (never in the JSON body). The `/auth/me` endpoint should use the cookie-based refresh token to issue new access tokens.

---

## Finding: AdminRoute and ManagerRoute Do Not Check Token Expiration

- **Severity:** P1
- **File:** `frontend/src/components/auth/AdminRoute.tsx:9-21` and `frontend/src/components/auth/ManagerRoute.tsx:9-21`
- **Description:** Unlike `ProtectedRoute`, which checks `isTokenExpired(token)` before rendering children, both `AdminRoute` and `ManagerRoute` only check `isAuthenticated` and `user.role`. If a token is expired but still present in the Zustand store (which persists across page reloads via `localStorage`), these routes will render their content. The expired token will fail on the first API call, but the admin/manager UI will briefly be visible and interactive.
- **Evidence:**
  ```typescript
  // AdminRoute.tsx -- no token expiration check
  export function AdminRoute({ children }: AdminRouteProps) {
    const { user, isAuthenticated } = useAuthStore()

    if (!isAuthenticated) {
      return <Navigate to="/login" replace />
    }

    if (user?.role !== "admin") {
      return <Navigate to="/" replace />
    }

    return <>{children}</>
  }
  ```
- **Fix:** Both `AdminRoute` and `ManagerRoute` should either (a) wrap their children in `<ProtectedRoute>` to inherit the expiration check, or (b) import and call `isTokenExpired` directly. Option (a) is cleaner:
  ```typescript
  export function AdminRoute({ children }: AdminRouteProps) {
    const { user } = useAuthStore()

    if (user?.role !== "admin") {
      return <Navigate to="/" replace />
    }

    return <>{children}</>
  }
  // Then in router/index.tsx, nest AdminRoute inside ProtectedRoute:
  // <ProtectedRoute><AdminRoute>...</AdminRoute></ProtectedRoute>
  ```
  Note: In the current router, `AdminRoute` is already a child of a `ProtectedRoute`-wrapped layout, so the parent catches most cases. But if the route structure ever changes, or if direct URL navigation occurs, the explicit check is a defense-in-depth measure.

---

## Finding: Open Redirect via `auth_redirect` in sessionStorage

- **Severity:** P1
- **File:** `frontend/src/lib/auth.ts:67-68,83-86` and `frontend/src/pages/AuthCallbackPage.tsx:37-38`
- **Description:** The `buildGoogleOAuthUrl` function stores a `redirectPath` in `sessionStorage` without validation. After login, `getPostLoginRedirect()` returns whatever was stored and passes it to `navigate()`. While React Router's `navigate()` typically handles relative paths, the stored value originates from `location.state.from.pathname` in `LoginPage.tsx` which is itself derived from the browser's location. If an attacker can influence this value (e.g., via a crafted link that sets `location.state`), they could potentially redirect the user to an unexpected path post-login.
- **Evidence:**
  ```typescript
  // auth.ts lines 83-86
  export function getPostLoginRedirect(): string {
    const redirect = sessionStorage.getItem("auth_redirect") || "/"
    sessionStorage.removeItem("auth_redirect")
    return redirect
  }

  // AuthCallbackPage.tsx lines 37-38
  const redirect = getPostLoginRedirect()
  navigate(redirect, { replace: true })
  ```
- **Fix:** Validate that the redirect path starts with `/` and does not start with `//` (which browsers interpret as protocol-relative URLs). Reject any absolute URLs or protocol-relative URLs:
  ```typescript
  export function getPostLoginRedirect(): string {
    const redirect = sessionStorage.getItem("auth_redirect") || "/"
    sessionStorage.removeItem("auth_redirect")
    if (!redirect.startsWith("/") || redirect.startsWith("//")) {
      return "/"
    }
    return redirect
  }
  ```

---

## P2 -- Medium Findings

---

## Finding: Error Messages from API Rendered Directly in DOM

- **Severity:** P2
- **File:** `frontend/src/pages/AuthCallbackPage.tsx:19,53-57`
- **Description:** The error parameter from Google's OAuth redirect (`searchParams.get("error")`) is interpolated into a string and rendered in the DOM. While React's JSX rendering auto-escapes text content (preventing script injection), the Google error parameter value is user-controlled URL data. If this component were ever refactored to use `dangerouslySetInnerHTML` or a markdown renderer, it would become an XSS vector. Similarly, the API error message (`err?.response?.data?.detail`) is rendered directly (line 42-43). Backend error messages should be treated as untrusted.
- **Evidence:**
  ```typescript
  // AuthCallbackPage.tsx line 19
  if (errorParam) return `Google authentication failed: ${errorParam}`

  // AuthCallbackPage.tsx line 42
  const message =
    err?.response?.data?.detail || "Authentication failed. Please try again."
  ```
- **Fix:** Sanitize or map error codes to known safe messages rather than reflecting raw URL parameters or API error strings:
  ```typescript
  const ERROR_MESSAGES: Record<string, string> = {
    access_denied: "Access was denied. Please try again.",
    invalid_scope: "Invalid permissions requested.",
  }
  if (errorParam) return ERROR_MESSAGES[errorParam] || "Google authentication failed."
  ```

---

## Finding: Missing Content-Security-Policy Header

- **Severity:** P2
- **File:** `frontend/nginx.conf:7-12`
- **Description:** The nginx configuration includes several security headers (`X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`) but is missing a `Content-Security-Policy` (CSP) header. CSP is the primary defense-in-depth mechanism against XSS. Without it, any injected script (from a supply-chain attack on an npm dependency, or a future `dangerouslySetInnerHTML` usage) will execute without restriction.
- **Evidence:**
  ```nginx
  # Security headers
  add_header X-Frame-Options "SAMEORIGIN" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header X-XSS-Protection "1; mode=block" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
  # No Content-Security-Policy header
  ```
- **Fix:** Add a CSP header. Start with a restrictive policy and relax as needed:
  ```nginx
  add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://accounts.google.com; font-src 'self'; frame-ancestors 'none';" always;
  ```
  Note: `'unsafe-inline'` for styles is needed because many CSS-in-JS solutions and the `<style>` tag in `ContentPreviewPage.tsx` require it. If possible, migrate to nonce-based CSP for styles.

---

## Finding: Inline `<style>` Tag in ContentPreviewPage Weakens CSP

- **Severity:** P2
- **File:** `frontend/src/pages/ContentPreviewPage.tsx:260-276`
- **Description:** An inline `<style>` element is used for print media styles. This requires `'unsafe-inline'` in the CSP `style-src` directive, which weakens the protection against CSS injection attacks. While this is common practice, it is worth noting as it prevents adopting a strict CSP.
- **Evidence:**
  ```typescript
  // ContentPreviewPage.tsx lines 260-276
  <style>{`
    @media print {
      body {
        print-color-adjust: exact;
        -webkit-print-color-adjust: exact;
      }
      // ...
    }
  `}</style>
  ```
- **Fix:** Move print styles to a separate CSS file (e.g., `print.css`) imported in the component, or use a CSS module. This allows removing `'unsafe-inline'` from the CSP `style-src` directive.

---

## P3 -- Low Findings

---

## Finding: Console Logging of API Request Details in Development Mode

- **Severity:** P3
- **File:** `frontend/src/lib/api.ts:28-29,69-70`
- **Description:** The request interceptor logs API method and URL to the console in development mode. While gated behind `import.meta.env.DEV`, this is worth noting: (a) if the environment variable is misconfigured in a staging/production build, sensitive endpoint paths will appear in the console; (b) several other files log errors to `console.error` unconditionally (e.g., `ProjectDetail.tsx:124`, `KanbanBoard.tsx:131`, `PromptEditor.tsx:123`), which could leak internal API structure to anyone with DevTools open.
- **Evidence:**
  ```typescript
  // api.ts lines 28-29
  if (import.meta.env.DEV) {
    console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`)
  }

  // ProjectDetail.tsx line 124 -- unconditional console.error
  console.error("Failed to submit for review:", err)
  ```
- **Fix:** Replace unconditional `console.error` calls with a centralized logger that can be silenced in production. Consider using a logging library (e.g., `loglevel`) that supports log-level filtering based on environment.

---

## Finding: `sheet_url` Rendered as Unvalidated External Link

- **Severity:** P3
- **File:** `frontend/src/components/projects/ProjectDetail.tsx:297,323` and `frontend/src/pages/ContentPreviewPage.tsx:139`
- **Description:** The `project.sheet_url` field is rendered as an `<a href>` without validating that it points to a Google Sheets domain. If a backend bug or data corruption causes `sheet_url` to contain a `javascript:` URI or a phishing URL, clicking it would execute arbitrary code or navigate to a malicious site. The `rel="noopener noreferrer"` attribute is correctly set, which mitigates the `window.opener` attack, but does not prevent navigation to arbitrary URLs.
- **Evidence:**
  ```tsx
  // ProjectDetail.tsx line 297
  <a
    href={project.sheet_url}
    target="_blank"
    rel="noopener noreferrer"
  >
  ```
- **Fix:** Validate `sheet_url` before rendering. Only allow URLs matching `https://docs.google.com/spreadsheets/`:
  ```typescript
  const isValidSheetUrl = (url: string) =>
    url.startsWith("https://docs.google.com/spreadsheets/")

  {project.sheet_url && isValidSheetUrl(project.sheet_url) && (
    <a href={project.sheet_url} ...>
  )}
  ```

---

## Finding: Image Download Uses Unvalidated URL

- **Severity:** P3
- **File:** `frontend/src/components/projects/ImageGallery.tsx:61-68`
- **Description:** The `handleDownload` function creates an `<a>` element with `href` set to `image.url` and programmatically clicks it to trigger a download. The `image.url` comes from API data. If the API returns a malicious URL (e.g., `javascript:alert(1)` or a data URI), the `link.click()` could execute it. The risk is low because the data originates from a trusted API, but defense-in-depth suggests validating the URL scheme.
- **Evidence:**
  ```typescript
  // ImageGallery.tsx lines 61-68
  const handleDownload = () => {
    const image = filteredImages[currentImageIndex]
    const link = document.createElement("a")
    link.href = image.url
    link.download = image.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
  ```
- **Fix:** Validate that `image.url` starts with `https://` before triggering the download:
  ```typescript
  const handleDownload = () => {
    const image = filteredImages[currentImageIndex]
    if (!image.url.startsWith("https://")) return
    // ... rest of download logic
  }
  ```

---

## Checklist Summary

| # | Check Item | Status | Notes |
|---|-----------|--------|-------|
| 1 | Token storage mechanism | FAIL | Uses `localStorage` via Zustand persist -- vulnerable to XSS. See P0 finding. |
| 2 | Token in all API requests via interceptor | PASS | Request interceptor reads from `localStorage` and sets `Authorization: Bearer`. |
| 3 | Token refresh on 401 | FAIL | 401 triggers immediate logout. `refreshAccessToken()` exists but is never called. See P1 finding. |
| 4 | Logout clears all auth state | PASS | `logout()` clears token, user, `isAuthenticated` in Zustand, clears React Query cache, and the interceptor clears `localStorage`. |
| 5 | OAuth callback validates state parameter | FAIL | No `state` parameter generated or validated. See P0 finding. |
| 6 | Protected routes redirect when unauthenticated | PASS | `ProtectedRoute` redirects to `/login` with `from` location state. |
| 7 | Role-based route guards check correct roles | FAIL | `ManagerRoute` checks `"admin"` instead of `"manager"`. `UserRole` type lacks `"manager"`. See P0 finding. |
| 8 | No sensitive data logged to console | WARN | Dev-gated `console.debug` for API calls. Multiple unconditional `console.error` calls. See P3 finding. |
| 9 | XSS vectors | PASS | No `dangerouslySetInnerHTML`, no `innerHTML`, no `eval()`, no `new Function()`. React auto-escaping is in effect. |
| 10 | API base URL configuration | PASS | Uses `import.meta.env.VITE_API_BASE_URL` with fallback to `"/api/v1"` (relative). No hardcoded `localhost`. |
| 11 | Token expiration handling | PARTIAL | `ProtectedRoute` checks expiration. `AdminRoute`/`ManagerRoute` do not. `isTokenExpiringSoon` exists but is unused. See P1 finding. |
| 12 | Race conditions in auth state | PASS | `refreshAccessToken()` deduplicates concurrent calls via `refreshPromise`. Zustand persist handles multi-tab via `localStorage` events (built-in). However, the refresh function is currently unused. |

---

## Recommendations (Priority Order)

1. **[IMMEDIATE]** Fix `ManagerRoute` role check -- this is a copy-paste bug that is trivial to fix and completely breaks manager authorization.
2. **[IMMEDIATE]** Add OAuth `state` parameter generation and validation to prevent login CSRF.
3. **[SHORT-TERM]** Migrate token storage from `localStorage` to `httpOnly` cookies. This requires backend changes to set cookies on auth endpoints and frontend changes to use `withCredentials: true`.
4. **[SHORT-TERM]** Wire up the existing `refreshAccessToken()` function in the 401 interceptor.
5. **[SHORT-TERM]** Add `"manager"` to the `UserRole` type union.
6. **[SHORT-TERM]** Remove `refresh_token` from the `AuthResponse` TypeScript type and ensure the backend does not send it in the response body.
7. **[MEDIUM-TERM]** Add `Content-Security-Policy` header to `nginx.conf`.
8. **[MEDIUM-TERM]** Validate external URLs (`sheet_url`, `image.url`) before rendering as `href` attributes.
9. **[LOW]** Replace unconditional `console.error` calls with an environment-aware logger.
10. **[LOW]** Move inline `<style>` to external CSS to enable stricter CSP.

---

*End of audit report.*
