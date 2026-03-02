import { describe, it, expect, beforeEach, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter, Routes, Route, useLocation } from "react-router-dom"
import { ProtectedRoute } from "@/components/auth/ProtectedRoute"
import * as authStoreModule from "@/stores/auth-store"
import type { User } from "@/types"

vi.mock("@/stores/auth-store", async () => {
  const actual = await vi.importActual<typeof import("@/stores/auth-store")>("@/stores/auth-store")
  return {
    ...actual,
    useAuthStore: vi.fn(() => ({
      isAuthenticated: false,
      token: null,
      user: null,
      logout: vi.fn(),
      login: vi.fn(),
      updateUser: vi.fn(),
    })),
  }
})

function createTestJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }))
  const body = btoa(JSON.stringify(payload))
  return `${header}.${body}.fake-signature`
}

function LocationDisplay() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

describe("ProtectedRoute", () => {
  const mockLogout = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockLogout.mockClear()
  })

  it("renders children when authenticated with valid token", () => {
    const futureExp = Math.floor(Date.now() / 1000) + 3600
    const token = createTestJwt({ exp: futureExp })
    const user: User = {
      id: "123",
      email: "test@example.com",
      name: "Test User",
      role: "user",
    }

    vi.mocked(authStoreModule.useAuthStore).mockReturnValue({
      isAuthenticated: true,
      token,
      user,
      logout: mockLogout,
      login: vi.fn(),
      updateUser: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Protected Content")).toBeInTheDocument()
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument()
  })

  it("redirects to /login when not authenticated", () => {
    vi.mocked(authStoreModule.useAuthStore).mockReturnValue({
      isAuthenticated: false,
      token: null,
      user: null,
      logout: mockLogout,
      login: vi.fn(),
      updateUser: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Login Page")).toBeInTheDocument()
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument()
  })

  it("redirects to /login when token is expired", () => {
    const pastExp = Math.floor(Date.now() / 1000) - 3600
    const token = createTestJwt({ exp: pastExp })
    const user: User = {
      id: "123",
      email: "test@example.com",
      name: "Test User",
      role: "user",
    }

    vi.mocked(authStoreModule.useAuthStore).mockReturnValue({
      isAuthenticated: true,
      token,
      user,
      logout: mockLogout,
      login: vi.fn(),
      updateUser: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Login Page")).toBeInTheDocument()
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument()
  })

  it("calls logout when token is expired", () => {
    const pastExp = Math.floor(Date.now() / 1000) - 3600
    const token = createTestJwt({ exp: pastExp })
    const user: User = {
      id: "123",
      email: "test@example.com",
      name: "Test User",
      role: "user",
    }

    vi.mocked(authStoreModule.useAuthStore).mockReturnValue({
      isAuthenticated: true,
      token,
      user,
      logout: mockLogout,
      login: vi.fn(),
      updateUser: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Login Page")).toBeInTheDocument()
    expect(mockLogout).toHaveBeenCalled()
  })

  it("passes location state to login redirect", () => {
    vi.mocked(authStoreModule.useAuthStore).mockReturnValue({
      isAuthenticated: false,
      token: null,
      user: null,
      logout: mockLogout,
      login: vi.fn(),
      updateUser: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route
            path="/login"
            element={
              <>
                <div>Login Page</div>
                <LocationDisplay />
              </>
            }
          />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Login Page")).toBeInTheDocument()
  })

  it("handles user with no token", () => {
    const user: User = {
      id: "123",
      email: "test@example.com",
      name: "Test User",
      role: "user",
    }

    vi.mocked(authStoreModule.useAuthStore).mockReturnValue({
      isAuthenticated: false,
      token: null,
      user,
      logout: mockLogout,
      login: vi.fn(),
      updateUser: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Login Page")).toBeInTheDocument()
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument()
  })

  it("handles token with no user", () => {
    const futureExp = Math.floor(Date.now() / 1000) + 3600
    const token = createTestJwt({ exp: futureExp })

    vi.mocked(authStoreModule.useAuthStore).mockReturnValue({
      isAuthenticated: false,
      token,
      user: null,
      logout: mockLogout,
      login: vi.fn(),
      updateUser: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Login Page")).toBeInTheDocument()
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument()
  })
})
