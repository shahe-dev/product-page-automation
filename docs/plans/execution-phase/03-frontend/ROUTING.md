# Routing

**Last Updated:** 2026-01-15
**Status:** Active
**Owner:** Frontend Team

---

## Overview

The PDP Automation v.3 application uses React Router 7 for declarative client-side routing with authentication guards, role-based access control, and post-login redirection.

### Technology Stack

- **Router:** React Router 7.x
- **Authentication:** Custom route guards with Zustand
- **Route Types:** Public, Protected, Role-Restricted

---

## Route Configuration

### Complete Route Structure

```typescript
// src/router/index.tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { AdminRoute } from '@/components/auth/AdminRoute'
import { ManagerRoute } from '@/components/auth/ManagerRoute'

export const router = createBrowserRouter([
  // Public Routes
  {
    path: '/login',
    element: <LoginPage />,
  },

  // Protected Routes (All Authenticated Users)
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'processing',
        element: <ProcessingPage />,
      },
      {
        path: 'projects',
        children: [
          {
            index: true,
            element: <ProjectsListPage />,
          },
          {
            path: ':id',
            element: <ProjectDetailPage />,
          },
          {
            path: ':id/preview',
            element: <ContentPreviewPage />,
          },
        ],
      },
      {
        path: 'approvals',
        element: <ApprovalQueuePage />,
      },
      {
        path: 'publishing',
        element: <PublishQueuePage />,
      },
      {
        path: 'qa',
        children: [
          {
            index: true,
            element: <QAPage />,
          },
          {
            path: 'history',
            element: <QAHistoryPage />,
          },
        ],
      },
      {
        path: 'prompts',
        children: [
          {
            index: true,
            element: <PromptsPage />,
          },
          {
            path: ':id',
            element: <PromptEditorPage />,
          },
        ],
      },
      {
        path: 'workflow',
        element: <WorkflowPage />,
      },
      {
        path: 'history',
        element: <HistoryPage />,
      },
      {
        path: 'notifications',
        element: <NotificationsPage />,
      },

      // Role-Restricted Routes
      {
        path: 'manager',
        element: (
          <ManagerRoute>
            <ManagerDashboardPage />
          </ManagerRoute>
        ),
      },
      {
        path: 'admin',
        element: (
          <AdminRoute>
            <AdminDashboardPage />
          </AdminRoute>
        ),
      },
    ],
  },

  // 404 Not Found
  {
    path: '*',
    element: <NotFoundPage />,
  },
])

export function Router() {
  return <RouterProvider router={router} />
}
```

---

## Route Guards

### ProtectedRoute

Ensures user is authenticated before accessing protected pages.

```typescript
// src/components/auth/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    // Redirect to login, but save the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
```

**Features:**
- Checks authentication status from Zustand store
- Preserves intended destination in location state
- Redirects to `/login` if not authenticated
- Uses `replace` to avoid polluting history

---

### AdminRoute

Restricts access to system administrators only.

```typescript
// src/components/auth/AdminRoute.tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'

interface AdminRouteProps {
  children: React.ReactNode
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { user, isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role !== 'system_admin') {
    // User is authenticated but not admin
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
```

**Features:**
- First checks authentication
- Then checks for `system_admin` role
- Redirects to home page if insufficient permissions
- Shows 403 Forbidden message (optional enhancement)

---

### ManagerRoute

Restricts access to marketing managers only.

```typescript
// src/components/auth/ManagerRoute.tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'

interface ManagerRouteProps {
  children: React.ReactNode
}

export function ManagerRoute({ children }: ManagerRouteProps) {
  const { user, isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role !== 'marketing_manager') {
    // User is authenticated but not a marketing manager
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
```

**Note:** This is separate from AdminRoute. Marketing Managers access workflow metrics and approval dashboards, while Admins access system configuration and health monitoring.

---

## Navigation Components

### Sidebar Navigation

```typescript
// src/components/layout/Sidebar.tsx
import { NavLink } from 'react-router-dom'

interface MenuItem {
  icon: React.ComponentType<{ className?: string }>
  label: string
  path: string
  badge?: number
  roles: string[]
}

export function Sidebar() {
  const { user } = useAuthStore()
  const { data: approvalCount } = useApprovalQueue()
  const { data: publishCount } = usePublishingQueue()

  const menuItems: MenuItem[] = [
    { icon: Home, label: 'Dashboard', path: '/', roles: ['all'] },
    { icon: Upload, label: 'Processing', path: '/processing', roles: ['all'] },
    { icon: Folder, label: 'Projects', path: '/projects', roles: ['all'] },
    {
      icon: CheckCircle,
      label: 'Approvals',
      path: '/approvals',
      badge: approvalCount,
      roles: ['all'],
    },
    {
      icon: Send,
      label: 'Publishing',
      path: '/publishing',
      badge: publishCount,
      roles: ['all'],
    },
    { icon: Shield, label: 'QA', path: '/qa', roles: ['all'] },
    { icon: FileText, label: 'Prompts', path: '/prompts', roles: ['all'] },
    { icon: Kanban, label: 'Workflow', path: '/workflow', roles: ['all'] },
    { icon: History, label: 'History', path: '/history', roles: ['all'] },
    {
      icon: BarChart,
      label: 'Manager',
      path: '/manager',
      roles: ['marketing_manager'],
    },
    {
      icon: Settings,
      label: 'Admin',
      path: '/admin',
      roles: ['system_admin'],
    },
  ]

  const filteredItems = menuItems.filter(
    (item) => item.roles.includes('all') || item.roles.includes(user?.role)
  )

  return (
    <nav className="p-4 space-y-2">
      {filteredItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-4 py-2 rounded-md text-sm font-medium transition-colors',
              isActive
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
            )
          }
        >
          {({ isActive }) => (
            <>
              <item.icon className="h-5 w-5" />
              <span className="flex-1">{item.label}</span>
              {item.badge && item.badge > 0 && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-red-500 text-white">
                  {item.badge}
                </span>
              )}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
```

**Features:**
- Role-based menu filtering
- Active route highlighting with `NavLink`
- Badge support for notifications
- Icons for visual clarity

---

### Programmatic Navigation

```typescript
// Using useNavigate hook
import { useNavigate } from 'react-router-dom'

function CreateProjectButton() {
  const navigate = useNavigate()
  const createMutation = useCreateProject()

  const handleCreate = async (data: ProjectData) => {
    const project = await createMutation.mutateAsync(data)
    // Navigate to newly created project
    navigate(`/projects/${project.id}`)
  }

  return <Button onClick={handleCreate}>Create Project</Button>
}
```

---

### Link Navigation

```typescript
// Using Link component
import { Link } from 'react-router-dom'

function ProjectCard({ project }: { project: Project }) {
  return (
    <Card>
      <Link
        to={`/projects/${project.id}`}
        className="text-blue-600 hover:text-blue-700 font-medium"
      >
        {project.name}
      </Link>
    </Card>
  )
}
```

---

## Post-Login Redirection

### Login Page Implementation

```typescript
// src/pages/LoginPage.tsx
import { useNavigate, useLocation } from 'react-router-dom'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuthStore()

  const handleGoogleLogin = async () => {
    try {
      const { token, user } = await api.auth.googleLogin()
      login(token, user)

      // Redirect to originally requested page or home
      const from = location.state?.from?.pathname || '/'
      navigate(from, { replace: true })
    } catch (error) {
      toast.error('Login failed')
    }
  }

  // If already authenticated, redirect to home
  const { isAuthenticated } = useAuthStore()
  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return (
    <div>
      <Button onClick={handleGoogleLogin}>Sign in with Google</Button>
    </div>
  )
}
```

**Flow:**
1. User tries to access `/projects/123` without being authenticated
2. `ProtectedRoute` redirects to `/login` with `state={{ from: location }}`
3. User logs in successfully
4. LoginPage reads `location.state.from` and redirects to `/projects/123`
5. If no previous location, redirects to `/` (home)

---

## URL Parameters

### Route Parameters

```typescript
// Access route params with useParams
import { useParams } from 'react-router-dom'

function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: project } = useProject(id)

  return <div>{project?.name}</div>
}
```

---

### Search Parameters

```typescript
// Access and modify search params
import { useSearchParams } from 'react-router-dom'

function ProjectsListPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  const search = searchParams.get('search') || ''
  const status = searchParams.get('status') || 'all'

  const handleSearchChange = (value: string) => {
    setSearchParams((prev) => {
      if (value) {
        prev.set('search', value)
      } else {
        prev.delete('search')
      }
      return prev
    })
  }

  return (
    <div>
      <SearchBar value={search} onChange={handleSearchChange} />
      <ProjectList filters={{ search, status }} />
    </div>
  )
}
```

**URL Example:** `/projects?search=marina&status=published`

---

## Breadcrumbs

```typescript
// src/components/layout/Breadcrumbs.tsx
import { Link, useMatches } from 'react-router-dom'

export function Breadcrumbs() {
  const matches = useMatches()

  const breadcrumbs = matches
    .filter((match) => match.handle?.breadcrumb)
    .map((match) => ({
      label: match.handle.breadcrumb(match.data),
      path: match.pathname,
    }))

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm">
      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={crumb.path}>
          {index > 0 && <ChevronRight className="h-4 w-4 text-gray-400" />}
          {index === breadcrumbs.length - 1 ? (
            <span className="text-gray-900 font-medium">{crumb.label}</span>
          ) : (
            <Link
              to={crumb.path}
              className="text-gray-500 hover:text-gray-700"
            >
              {crumb.label}
            </Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  )
}

// Route configuration with breadcrumb handles
{
  path: 'projects/:id',
  element: <ProjectDetailPage />,
  handle: {
    breadcrumb: (data) => data.project.name,
  },
}
```

---

## 404 Not Found Page

```typescript
// src/pages/NotFoundPage.tsx
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900">404</h1>
        <p className="mt-4 text-xl text-gray-600">Page not found</p>
        <p className="mt-2 text-gray-500">
          The page you're looking for doesn't exist.
        </p>
        <Link
          to="/"
          className="mt-6 inline-block px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Go to Dashboard
        </Link>
      </div>
    </div>
  )
}
```

---

## Route-Based Code Splitting

```typescript
// Lazy load routes for better performance
import { lazy, Suspense } from 'react'

const ProjectsListPage = lazy(() => import('@/pages/ProjectsListPage'))
const ProjectDetailPage = lazy(() => import('@/pages/ProjectDetailPage'))
const AdminDashboardPage = lazy(() => import('@/pages/AdminDashboardPage'))

// Wrap in Suspense
{
  path: 'projects',
  element: (
    <Suspense fallback={<LoadingSpinner />}>
      <ProjectsListPage />
    </Suspense>
  ),
}
```

---

## Navigation Menu Structure

```
Main Navigation (Sidebar):
├── Dashboard (/)
├── Processing (/processing)
├── Projects (/projects)
│   ├── List View (/projects)
│   ├── Detail (/projects/:id)
│   └── Preview (/projects/:id/preview)
├── Approvals (/approvals) - Badge with count
├── Publishing (/publishing) - Badge with count
├── QA (/qa)
│   ├── Run QA (/qa)
│   └── History (/qa/history)
├── Prompts (/prompts)
│   ├── List (/prompts)
│   └── Editor (/prompts/:id)
├── Workflow (/workflow)
├── History (/history)
├── Manager (/manager) - Marketing Managers only
└── Admin (/admin) - System Admins only

Header Navigation:
├── Search (global)
├── Notifications (/notifications)
└── User Menu
    ├── Profile
    ├── Settings
    └── Logout
```

---

## Accessibility Features

### Skip to Main Content

```typescript
// src/components/layout/AppLayout.tsx
export function AppLayout() {
  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-md"
      >
        Skip to main content
      </a>

      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1">
          <Header />
          <main id="main-content" tabIndex={-1}>
            <Outlet />
          </main>
        </div>
      </div>
    </>
  )
}
```

---

### Focus Management

```typescript
// Focus management on route change
import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

export function useFocusOnNavigate() {
  const location = useLocation()

  useEffect(() => {
    // Focus main content on route change
    const main = document.getElementById('main-content')
    main?.focus()
  }, [location.pathname])
}
```

---

## Related Documentation

- [Component Library](./COMPONENT_LIBRARY.md) - UI component specifications
- [Page Specifications](./PAGE_SPECIFICATIONS.md) - Page layouts and wireframes
- [State Management](./STATE_MANAGEMENT.md) - React Query and Zustand patterns
- [Accessibility](./ACCESSIBILITY.md) - WCAG compliance guidelines

---

**End of Routing Documentation**
