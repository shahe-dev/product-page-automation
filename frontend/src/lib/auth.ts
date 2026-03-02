import { api } from "@/lib/api"
import { useAuthStore } from "@/stores/auth-store"

const TOKEN_REFRESH_BUFFER_MS = 5 * 60 * 1000 // 5 minutes before expiry

function parseJwt(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split(".")[1]
    if (!base64Url) return null
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/")
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join(""),
    )
    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = parseJwt(token)
  if (!payload || typeof payload.exp !== "number") return true
  const expiryMs = payload.exp * 1000
  return Date.now() >= expiryMs
}

export function isTokenExpiringSoon(token: string): boolean {
  const payload = parseJwt(token)
  if (!payload || typeof payload.exp !== "number") return true
  const expiryMs = payload.exp * 1000
  return Date.now() >= expiryMs - TOKEN_REFRESH_BUFFER_MS
}

export function getTokenExpiryMs(token: string): number | null {
  const payload = parseJwt(token)
  if (!payload || typeof payload.exp !== "number") return null
  return payload.exp * 1000
}

let refreshPromise: Promise<string> | null = null

export async function refreshAccessToken(): Promise<string> {
  // Deduplicate concurrent refresh calls
  if (refreshPromise) return refreshPromise

  refreshPromise = api.auth
    .me()
    .then((response) => {
      const { access_token, user } = response
      useAuthStore.getState().login(access_token, user)
      return access_token
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

export function buildGoogleOAuthUrl(redirectPath?: string): string {
  const clientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID
  const redirectUri = import.meta.env.VITE_GOOGLE_REDIRECT_URI

  if (redirectPath) {
    sessionStorage.setItem("auth_redirect", redirectPath)
  }

  // Generate and persist state for CSRF protection
  const state = crypto.randomUUID()
  sessionStorage.setItem("oauth_state", state)

  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "consent",
    state,
  })

  return `https://accounts.google.com/o/oauth2/v2/auth?${params}`
}

export function getPostLoginRedirect(): string {
  const redirect = sessionStorage.getItem("auth_redirect") || "/"
  sessionStorage.removeItem("auth_redirect")
  // Prevent open redirect via protocol-relative URLs
  if (!redirect.startsWith("/") || redirect.startsWith("//")) {
    return "/"
  }
  return redirect
}

export function clearAuthState(): void {
  useAuthStore.getState().logout()
  sessionStorage.removeItem("auth_redirect")
}
