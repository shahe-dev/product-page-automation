import { useEffect, useMemo, useRef, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { api } from "@/lib/api"
import { getPostLoginRedirect } from "@/lib/auth"
import { useAuthStore } from "@/stores/auth-store"

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [apiError, setApiError] = useState<string | null>(null)
  const processed = useRef(false)

  const urlError = useMemo(() => {
    const errorParam = searchParams.get("error")
    if (errorParam) return `Google authentication failed: ${errorParam}`
    if (!searchParams.get("code")) return "No authorization code received from Google."
    return null
  }, [searchParams])

  useEffect(() => {
    if (processed.current) return
    if (urlError) return
    processed.current = true

    const code = searchParams.get("code")
    const state = searchParams.get("state")
    if (!code || !state) return

    // State validation is done by the backend (state stored in DB)
    api.auth
      .googleLogin(code, state)
      .then((response) => {
        login(response.access_token, response.user)
        toast.success(`Welcome, ${response.user.name}`)
        const redirect = getPostLoginRedirect()
        navigate(redirect, { replace: true })
      })
      .catch((err) => {
        const raw =
          err?.response?.data?.detail || ""
        const rawLower = typeof raw === "string" ? raw.toLowerCase() : ""
        // Map server errors to safe, user-facing messages (never echo raw details)
        if (rawLower.includes("domain")) {
          setApiError("Only @your-domain.com email addresses are permitted.")
        } else if (rawLower.includes("expired")) {
          setApiError("Authentication session expired. Please try again.")
        } else if (rawLower.includes("invalid")) {
          setApiError("Invalid authentication response. Please try again.")
        } else {
          setApiError("Authentication failed. Please try again.")
        }
      })
  }, [searchParams, login, navigate, urlError])

  const error = urlError || apiError

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center max-w-md space-y-4">
          <h1 className="text-2xl font-bold text-destructive">Authentication Failed</h1>
          <p className="text-muted-foreground">{error}</p>
          <a
            href="/login"
            className="inline-block px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Back to Login
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <LoadingSpinner size="lg" />
        <p className="text-muted-foreground">Completing sign-in...</p>
      </div>
    </div>
  )
}
