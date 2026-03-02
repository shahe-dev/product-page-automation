import { useMemo } from "react"
import { Navigate } from "react-router-dom"

import { isTokenExpired } from "@/lib/auth"
import { useAuthStore } from "@/stores/auth-store"

interface AdminRouteProps {
  children: React.ReactNode
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { user, isAuthenticated, token, logout } = useAuthStore()

  const isExpired = useMemo(() => {
    if (isAuthenticated && token) {
      return isTokenExpired(token)
    }
    return false
  }, [isAuthenticated, token])

  if (isExpired) {
    logout()
    return <Navigate to="/login" replace />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role !== "admin") {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
