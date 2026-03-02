import { useState } from "react"
import { Navigate, useLocation } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import { useAuthStore } from "@/stores/auth-store"

export default function LoginPage() {
  const location = useLocation()
  const { isAuthenticated } = useAuthStore()
  const [isLoading, setIsLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const handleGoogleLogin = async () => {
    setIsLoading(true)
    try {
      // Store intended redirect path
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || "/"
      sessionStorage.setItem("auth_redirect", from)

      // Get OAuth URL from backend (state is stored in backend DB)
      const { oauth_url } = await api.auth.getLoginUrl()
      window.location.href = oauth_url
    } catch (error) {
      console.error("Failed to get login URL:", error)
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">PDP Automation</CardTitle>
          <CardDescription>Sign in with your organization Google account</CardDescription>
        </CardHeader>
        <CardContent>
          <Button className="w-full" size="lg" onClick={handleGoogleLogin} disabled={isLoading}>
            {isLoading ? "Redirecting..." : "Sign in with Google"}
          </Button>
          <p className="mt-4 text-center text-xs text-muted-foreground">
            Only @{import.meta.env.VITE_ALLOWED_EMAIL_DOMAIN || "your-domain.com"} accounts are permitted
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
