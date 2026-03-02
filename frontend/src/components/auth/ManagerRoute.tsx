import { useMemo } from "react"
import { Navigate } from "react-router-dom"

import { isTokenExpired } from "@/lib/auth"
import { useAuthStore } from "@/stores/auth-store"

interface ManagerRouteProps {
  children: React.ReactNode
}

export function ManagerRoute({ children }: ManagerRouteProps) {
  const { isAuthenticated, token, logout } = useAuthStore()

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

  // All authenticated users can access manager-level pages
  return <>{children}</>
}
