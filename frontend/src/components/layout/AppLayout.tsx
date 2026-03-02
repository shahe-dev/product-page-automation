import { Component, type ErrorInfo, type ReactNode, useEffect } from "react"
import { Outlet, useNavigate } from "react-router-dom"

import { Header } from "./Header"
import { Sidebar } from "./Sidebar"


interface PageErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class PageErrorBoundary extends Component<{ children: ReactNode }, PageErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): PageErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error("PageErrorBoundary caught:", error, errorInfo)
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-8">
          <h2 className="text-xl font-bold mb-4">This page encountered an error</h2>
          <p className="text-muted-foreground mb-6">
            {this.state.error?.message || "An unexpected error occurred."}
          </p>
          <button
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try Again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export function AppLayout() {
  const navigate = useNavigate()

  useEffect(() => {
    const handleAuthLogout = () => {
      navigate("/login", { replace: true })
    }
    window.addEventListener("auth:logout", handleAuthLogout)
    return () => window.removeEventListener("auth:logout", handleAuthLogout)
  }, [navigate])

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md"
      >
        Skip to main content
      </a>

      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main id="main-content" className="flex-1 overflow-y-auto p-6" tabIndex={-1}>
            <PageErrorBoundary>
              <Outlet />
            </PageErrorBoundary>
          </main>
        </div>
      </div>
    </>
  )
}
