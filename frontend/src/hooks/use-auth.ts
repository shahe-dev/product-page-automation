import { useMemo } from "react"

import { useAuthStore } from "@/stores/auth-store"
import type { UserRole } from "@/types"

export function useAuth() {
  const { user, isAuthenticated, login, logout } = useAuthStore()

  const hasRole = (role: UserRole): boolean => {
    return user?.role === role
  }

  const hasAnyRole = (roles: UserRole[]): boolean => {
    return user ? roles.includes(user.role) : false
  }

  const isAdmin = useMemo(() => user?.role === "admin", [user])

  return {
    user,
    isAuthenticated,
    login,
    logout,
    hasRole,
    hasAnyRole,
    isAdmin,
  }
}
