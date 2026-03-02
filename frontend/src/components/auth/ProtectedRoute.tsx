import { useMemo } from "react"
import { Navigate, useLocation } from "react-router-dom"

import { isTokenExpired } from "@/lib/auth"
import { useAuthStore } from "@/stores/auth-store"

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, token, logout } = useAuthStore()
  const location = useLocation()

  const isExpired = useMemo(() => {
    if (isAuthenticated && token) {
      return isTokenExpired(token)
    }
    return false
  }, [isAuthenticated, token])

  if (isExpired) {
    logout()
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
