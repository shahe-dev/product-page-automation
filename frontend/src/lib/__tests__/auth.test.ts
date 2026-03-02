import { describe, it, expect, beforeEach, vi } from "vitest"
import {
  isTokenExpired,
  isTokenExpiringSoon,
  getTokenExpiryMs,
  buildGoogleOAuthUrl,
  getPostLoginRedirect,
  clearAuthState,
} from "@/lib/auth"
import { useAuthStore } from "@/stores/auth-store"

function createTestJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }))
  const body = btoa(JSON.stringify(payload))
  return `${header}.${body}.fake-signature`
}

describe("auth utilities", () => {
  beforeEach(() => {
    sessionStorage.clear()
    useAuthStore.setState({ user: null, token: null })
  })

  describe("isTokenExpired", () => {
    it("returns false for valid non-expired token", () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600
      const token = createTestJwt({ exp: futureExp })
      expect(isTokenExpired(token)).toBe(false)
    })

    it("returns true for expired token", () => {
      const pastExp = Math.floor(Date.now() / 1000) - 3600
      const token = createTestJwt({ exp: pastExp })
      expect(isTokenExpired(token)).toBe(true)
    })

    it("returns true for malformed token", () => {
      expect(isTokenExpired("not.a.valid.jwt")).toBe(true)
      expect(isTokenExpired("malformed")).toBe(true)
    })

    it("returns true for token without exp claim", () => {
      const token = createTestJwt({ sub: "user123" })
      expect(isTokenExpired(token)).toBe(true)
    })

    it("returns true for token with non-numeric exp", () => {
      const token = createTestJwt({ exp: "invalid" })
      expect(isTokenExpired(token)).toBe(true)
    })
  })

  describe("isTokenExpiringSoon", () => {
    it("returns true for token expiring in less than 5 minutes", () => {
      const expIn2Min = Math.floor(Date.now() / 1000) + 120
      const token = createTestJwt({ exp: expIn2Min })
      expect(isTokenExpiringSoon(token)).toBe(true)
    })

    it("returns false for token expiring in more than 5 minutes", () => {
      const expIn10Min = Math.floor(Date.now() / 1000) + 600
      const token = createTestJwt({ exp: expIn10Min })
      expect(isTokenExpiringSoon(token)).toBe(false)
    })

    it("returns true for malformed token", () => {
      expect(isTokenExpiringSoon("malformed")).toBe(true)
    })

    it("returns true for token without exp claim", () => {
      const token = createTestJwt({ sub: "user123" })
      expect(isTokenExpiringSoon(token)).toBe(true)
    })
  })

  describe("getTokenExpiryMs", () => {
    it("returns correct millisecond timestamp", () => {
      const expSeconds = 1706544000
      const token = createTestJwt({ exp: expSeconds })
      expect(getTokenExpiryMs(token)).toBe(expSeconds * 1000)
    })

    it("returns null for malformed token", () => {
      expect(getTokenExpiryMs("malformed")).toBe(null)
      expect(getTokenExpiryMs("not.valid.jwt")).toBe(null)
    })

    it("returns null for token without exp claim", () => {
      const token = createTestJwt({ sub: "user123" })
      expect(getTokenExpiryMs(token)).toBe(null)
    })
  })

  describe("buildGoogleOAuthUrl", () => {
    const mockUuid = "12345678-1234-1234-1234-123456789abc"

    beforeEach(() => {
      vi.stubEnv("VITE_GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
      vi.stubEnv("VITE_GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")
      vi.spyOn(crypto, "randomUUID").mockReturnValue(mockUuid as `${string}-${string}-${string}-${string}-${string}`)
    })

    it("builds correct OAuth URL with all required parameters", () => {
      const url = buildGoogleOAuthUrl()
      expect(url).toContain("https://accounts.google.com/o/oauth2/v2/auth")
      expect(url).toContain("client_id=test-client-id")
      expect(url).toContain("redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fcallback")
      expect(url).toContain("response_type=code")
      expect(url).toContain("scope=openid+email+profile")
      expect(url).toContain("access_type=offline")
      expect(url).toContain("prompt=consent")
      expect(url).toContain(`state=${mockUuid}`)
    })

    it("stores redirect path in sessionStorage when provided", () => {
      buildGoogleOAuthUrl("/projects")
      expect(sessionStorage.getItem("auth_redirect")).toBe("/projects")
    })

    it("stores oauth state in sessionStorage", () => {
      buildGoogleOAuthUrl()
      expect(sessionStorage.getItem("oauth_state")).toBe(mockUuid)
    })

    it("does not store auth_redirect when no path provided", () => {
      buildGoogleOAuthUrl()
      expect(sessionStorage.getItem("auth_redirect")).toBe(null)
    })
  })

  describe("getPostLoginRedirect", () => {
    it("returns stored redirect path", () => {
      sessionStorage.setItem("auth_redirect", "/projects/123")
      expect(getPostLoginRedirect()).toBe("/projects/123")
    })

    it("returns / when no stored path", () => {
      expect(getPostLoginRedirect()).toBe("/")
    })

    it("removes auth_redirect from sessionStorage after retrieval", () => {
      sessionStorage.setItem("auth_redirect", "/projects")
      getPostLoginRedirect()
      expect(sessionStorage.getItem("auth_redirect")).toBe(null)
    })

    it("sanitizes protocol-relative URLs", () => {
      sessionStorage.setItem("auth_redirect", "//evil.com/phishing")
      expect(getPostLoginRedirect()).toBe("/")
    })

    it("sanitizes URLs that don't start with /", () => {
      sessionStorage.setItem("auth_redirect", "http://evil.com")
      expect(getPostLoginRedirect()).toBe("/")
    })

    it("allows valid absolute paths", () => {
      sessionStorage.setItem("auth_redirect", "/dashboard/admin")
      expect(getPostLoginRedirect()).toBe("/dashboard/admin")
    })
  })

  describe("clearAuthState", () => {
    it("calls logout on auth store", () => {
      const logoutSpy = vi.spyOn(useAuthStore.getState(), "logout")
      clearAuthState()
      expect(logoutSpy).toHaveBeenCalled()
    })

    it("removes auth_redirect from sessionStorage", () => {
      sessionStorage.setItem("auth_redirect", "/projects")
      clearAuthState()
      expect(sessionStorage.getItem("auth_redirect")).toBe(null)
    })

    it("clears both auth state and redirect", () => {
      useAuthStore.setState({
        user: { id: "1", email: "test@example.com", name: "Test", role: "user" },
        token: "test-token",
      })
      sessionStorage.setItem("auth_redirect", "/projects")

      clearAuthState()

      expect(useAuthStore.getState().user).toBe(null)
      expect(useAuthStore.getState().token).toBe(null)
      expect(sessionStorage.getItem("auth_redirect")).toBe(null)
    })
  })
})
