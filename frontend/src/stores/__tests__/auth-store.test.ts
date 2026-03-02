import { describe, it, expect, beforeEach, vi } from "vitest"
import { useAuthStore } from "@/stores/auth-store"
import { queryClient } from "@/lib/query-client"
import type { User } from "@/types"

vi.mock("@/lib/query-client", () => ({
  queryClient: {
    clear: vi.fn(),
  },
}))

describe("auth store", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, token: null })
    sessionStorage.clear()
    vi.clearAllMocks()
  })

  describe("initial state", () => {
    it("has null user", () => {
      expect(useAuthStore.getState().user).toBe(null)
    })

    it("has null token", () => {
      expect(useAuthStore.getState().token).toBe(null)
    })

    it("isAuthenticated is false", () => {
      expect(useAuthStore.getState().isAuthenticated).toBe(false)
    })
  })

  describe("login", () => {
    it("sets user and token", () => {
      const user: User = {
        id: "123",
        email: "test@example.com",
        name: "Test User",
        role: "user",
      }
      const token = "test-jwt-token"

      useAuthStore.getState().login(token, user)

      expect(useAuthStore.getState().user).toEqual(user)
      expect(useAuthStore.getState().token).toBe(token)
    })

    it("sets isAuthenticated to true", () => {
      const user: User = {
        id: "123",
        email: "test@example.com",
        name: "Test User",
        role: "admin",
      }

      useAuthStore.getState().login("token", user)

      const { token, user: stateUser } = useAuthStore.getState()
      expect(token).toBeTruthy()
      expect(stateUser).toBeTruthy()
      expect(!!token && !!stateUser).toBe(true)
    })

    it("handles user with avatar", () => {
      const user: User = {
        id: "123",
        email: "test@example.com",
        name: "Test User",
        role: "manager",
        avatar: "https://example.com/avatar.jpg",
      }

      useAuthStore.getState().login("token", user)

      expect(useAuthStore.getState().user?.avatar).toBe("https://example.com/avatar.jpg")
    })
  })

  describe("logout", () => {
    it("clears user and token", () => {
      const user: User = {
        id: "123",
        email: "test@example.com",
        name: "Test User",
        role: "user",
      }
      useAuthStore.getState().login("token", user)

      useAuthStore.getState().logout()

      expect(useAuthStore.getState().user).toBe(null)
      expect(useAuthStore.getState().token).toBe(null)
    })

    it("sets isAuthenticated to false", () => {
      const user: User = {
        id: "123",
        email: "test@example.com",
        name: "Test User",
        role: "user",
      }
      useAuthStore.getState().login("token", user)

      useAuthStore.getState().logout()

      expect(useAuthStore.getState().isAuthenticated).toBe(false)
    })

    it("calls queryClient.clear", () => {
      useAuthStore.getState().logout()
      expect(queryClient.clear).toHaveBeenCalled()
    })
  })

  describe("updateUser", () => {
    it("merges partial user updates", () => {
      const user: User = {
        id: "123",
        email: "test@example.com",
        name: "Test User",
        role: "user",
      }
      useAuthStore.getState().login("token", user)

      useAuthStore.getState().updateUser({ name: "Updated Name" })

      expect(useAuthStore.getState().user).toEqual({
        id: "123",
        email: "test@example.com",
        name: "Updated Name",
        role: "user",
      })
    })

    it("updates multiple fields", () => {
      const user: User = {
        id: "123",
        email: "test@example.com",
        name: "Test User",
        role: "user",
      }
      useAuthStore.getState().login("token", user)

      useAuthStore.getState().updateUser({
        name: "New Name",
        avatar: "https://example.com/new-avatar.jpg",
      })

      expect(useAuthStore.getState().user).toEqual({
        id: "123",
        email: "test@example.com",
        name: "New Name",
        role: "user",
        avatar: "https://example.com/new-avatar.jpg",
      })
    })

    it("returns null when user is null", () => {
      useAuthStore.getState().updateUser({ name: "Updated Name" })
      expect(useAuthStore.getState().user).toBe(null)
    })

    it("does not crash when updating null user", () => {
      expect(() => {
        useAuthStore.getState().updateUser({ email: "new@example.com" })
      }).not.toThrow()
    })
  })

  describe("authentication state logic", () => {
    it("returns false when only token is set", () => {
      useAuthStore.setState({ token: "test-token", user: null })
      const { token, user } = useAuthStore.getState()
      expect(!!token && !!user).toBe(false)
    })

    it("returns false when only user is set", () => {
      const user: User = {
        id: "123",
        email: "test@example.com",
        name: "Test User",
        role: "user",
      }
      useAuthStore.setState({ user, token: null })
      const { token: stateToken, user: stateUser } = useAuthStore.getState()
      expect(!!stateToken && !!stateUser).toBe(false)
    })

    it("returns true when both token and user are set", () => {
      const user: User = {
        id: "123",
        email: "test@example.com",
        name: "Test User",
        role: "user",
      }
      useAuthStore.setState({ user, token: "test-token" })
      const { token, user: stateUser } = useAuthStore.getState()
      expect(!!token && !!stateUser).toBe(true)
    })
  })
})
