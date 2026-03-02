import { lazy, Suspense } from "react"
import { createBrowserRouter, RouterProvider } from "react-router-dom"

import { AdminRoute } from "@/components/auth/AdminRoute"
import { ManagerRoute } from "@/components/auth/ManagerRoute"
import { ProtectedRoute } from "@/components/auth/ProtectedRoute"
import { AppLayout } from "@/components/layout/AppLayout"

// Lazy-loaded pages
const LoginPage = lazy(() => import("@/pages/LoginPage"))
const HomePage = lazy(() => import("@/pages/HomePage"))
const ProcessingPage = lazy(() => import("@/pages/ProcessingPage"))
const ProjectsListPage = lazy(() => import("@/pages/ProjectsListPage"))
const ProjectDetailPage = lazy(() => import("@/pages/ProjectDetailPage"))
const ApprovalQueuePage = lazy(() => import("@/pages/ApprovalQueuePage"))
const PublishQueuePage = lazy(() => import("@/pages/PublishQueuePage"))
const QAPage = lazy(() => import("@/pages/QAPage"))
const PromptsPage = lazy(() => import("@/pages/PromptsPage"))
const WorkflowPage = lazy(() => import("@/pages/WorkflowPage"))
const HistoryPage = lazy(() => import("@/pages/HistoryPage"))
const NotificationsPage = lazy(() => import("@/pages/NotificationsPage"))
const ManagerDashboardPage = lazy(() => import("@/pages/ManagerDashboardPage"))
const AdminDashboardPage = lazy(() => import("@/pages/AdminDashboardPage"))
const ContentPreviewPage = lazy(() => import("@/pages/ContentPreviewPage"))
const QAHistoryPage = lazy(() => import("@/pages/QAHistoryPage"))
const PromptEditorPage = lazy(() => import("@/pages/PromptEditorPage"))
const TemplatesPage = lazy(() => import("@/pages/TemplatesPage"))
const AuthCallbackPage = lazy(() => import("@/pages/AuthCallbackPage"))
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"))

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>
  )
}

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>
}

const router = createBrowserRouter([
  // Public
  {
    path: "/login",
    element: (
      <SuspenseWrapper>
        <LoginPage />
      </SuspenseWrapper>
    ),
  },

  {
    path: "/auth/callback",
    element: (
      <SuspenseWrapper>
        <AuthCallbackPage />
      </SuspenseWrapper>
    ),
  },

  // Protected
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <HomePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "processing",
        element: (
          <SuspenseWrapper>
            <ProcessingPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "projects",
        children: [
          {
            index: true,
            element: (
              <SuspenseWrapper>
                <ProjectsListPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: ":id",
            element: (
              <SuspenseWrapper>
                <ProjectDetailPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: ":id/preview",
            element: (
              <SuspenseWrapper>
                <ContentPreviewPage />
              </SuspenseWrapper>
            ),
          },
        ],
      },
      {
        path: "approvals",
        element: (
          <SuspenseWrapper>
            <ApprovalQueuePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "publishing",
        element: (
          <SuspenseWrapper>
            <PublishQueuePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "qa",
        children: [
          {
            index: true,
            element: (
              <SuspenseWrapper>
                <QAPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: "history",
            element: (
              <SuspenseWrapper>
                <QAHistoryPage />
              </SuspenseWrapper>
            ),
          },
        ],
      },
      {
        path: "prompts",
        children: [
          {
            index: true,
            element: (
              <SuspenseWrapper>
                <PromptsPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: ":id",
            element: (
              <SuspenseWrapper>
                <PromptEditorPage />
              </SuspenseWrapper>
            ),
          },
        ],
      },
      {
        path: "workflow",
        element: (
          <SuspenseWrapper>
            <WorkflowPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "history",
        element: (
          <SuspenseWrapper>
            <HistoryPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "notifications",
        element: (
          <SuspenseWrapper>
            <NotificationsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "manager",
        element: (
          <ManagerRoute>
            <SuspenseWrapper>
              <ManagerDashboardPage />
            </SuspenseWrapper>
          </ManagerRoute>
        ),
      },
      {
        path: "admin",
        element: (
          <AdminRoute>
            <SuspenseWrapper>
              <AdminDashboardPage />
            </SuspenseWrapper>
          </AdminRoute>
        ),
      },
      {
        path: "templates",
        element: (
          <AdminRoute>
            <SuspenseWrapper>
              <TemplatesPage />
            </SuspenseWrapper>
          </AdminRoute>
        ),
      },
    ],
  },

  // 404
  {
    path: "*",
    element: (
      <SuspenseWrapper>
        <NotFoundPage />
      </SuspenseWrapper>
    ),
  },
])

export function Router() {
  return <RouterProvider router={router} />
}
