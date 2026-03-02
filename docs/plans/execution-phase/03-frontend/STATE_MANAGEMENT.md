# State Management

**Last Updated:** 2026-01-15
**Status:** Active
**Owner:** Frontend Team

---

## Overview

The PDP Automation v.3 application uses a hybrid state management approach combining React Query 5 for server state and Zustand 4 for client state. This separation provides optimal performance, clear boundaries, and excellent developer experience.

### Technology Stack

- **Server State:** React Query 5.x (TanStack Query)
- **Client State:** Zustand 4.x
- **Persistence:** Zustand persist middleware
- **DevTools:** React Query DevTools

### State Management Philosophy

1. **Server State:** Data from APIs (projects, jobs, prompts, notifications)
2. **Client State:** UI state (sidebar open, theme, filters)
3. **Form State:** React Hook Form (not covered here)
4. **URL State:** React Router (search params, route params)

---

## Server State with React Query

React Query handles all server-side data fetching, caching, synchronization, and background updates.

### Query Client Configuration

```typescript
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
      onError: (error) => {
        console.error('Mutation error:', error)
        toast.error('An error occurred. Please try again.')
      },
    },
  },
})
```

### Provider Setup

```typescript
// src/App.tsx
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

---

## Query Hooks

### Projects Queries

```typescript
// src/hooks/queries/useProjects.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

// List projects with filters
export function useProjects(filters: ProjectFilters) {
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => api.projects.list(filters),
    staleTime: 5 * 60 * 1000,
  })
}

// Get single project
export function useProject(id: string | undefined) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: () => api.projects.get(id!),
    enabled: !!id, // Only fetch if id exists
  })
}

// Get project revision history
export function useProjectHistory(id: string | undefined) {
  return useQuery({
    queryKey: ['projects', id, 'history'],
    queryFn: () => api.projects.getHistory(id!),
    enabled: !!id,
  })
}

// Create project
export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.projects.create,
    onSuccess: (newProject) => {
      // Invalidate projects list to refetch
      queryClient.invalidateQueries({ queryKey: ['projects'] })

      // Optimistically add to cache
      queryClient.setQueryData(['projects', newProject.id], newProject)

      toast.success('Project created successfully')
    },
  })
}

// Update project
export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) =>
      api.projects.update(id, data),
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['projects', id] })

      // Snapshot previous value
      const previousProject = queryClient.getQueryData(['projects', id])

      // Optimistically update cache
      queryClient.setQueryData(['projects', id], (old: Project) => ({
        ...old,
        ...data,
      }))

      return { previousProject }
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousProject) {
        queryClient.setQueryData(
          ['projects', variables.id],
          context.previousProject
        )
      }
    },
    onSettled: (data, error, { id }) => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['projects', id] })
    },
  })
}

// Delete project
export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.projects.delete,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.removeQueries({ queryKey: ['projects', id] })
      toast.success('Project deleted')
    },
  })
}
```

---

### Jobs Queries

```typescript
// src/hooks/queries/useJobs.ts

// List user's jobs
export function useJobs() {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: api.jobs.list,
    refetchInterval: 5000, // Poll every 5s for active jobs
  })
}

// Get job status with polling
export function useJob(
  id: string | null,
  options?: { enabled?: boolean; refetchInterval?: number }
) {
  return useQuery({
    queryKey: ['jobs', id],
    queryFn: () => api.jobs.get(id!),
    enabled: !!id && (options?.enabled ?? true),
    refetchInterval: (data) => {
      // Stop polling when job completes or fails
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false
      }
      return options?.refetchInterval ?? 2000 // Poll every 2s by default
    },
  })
}

// Upload file and create job
export function useUploadFile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (n: number) => void }) =>
      api.upload.pdf(file, onProgress),
    onSuccess: (result) => {
      queryClient.setQueryData(['jobs', result.job_id], result)
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })
}
```

---

### Prompts Queries

```typescript
// src/hooks/queries/usePrompts.ts

// List prompts with filters
export function usePrompts(filters: PromptFilters) {
  return useQuery({
    queryKey: ['prompts', filters],
    queryFn: () => api.prompts.list(filters),
  })
}

// Get single prompt
export function usePrompt(id: string | undefined) {
  return useQuery({
    queryKey: ['prompts', id],
    queryFn: () => api.prompts.get(id!),
    enabled: !!id,
  })
}

// Get prompt version history
export function usePromptVersions(id: string | undefined) {
  return useQuery({
    queryKey: ['prompts', id, 'versions'],
    queryFn: () => api.prompts.getVersions(id!),
    enabled: !!id,
  })
}

// Update prompt (creates new version)
export function useUpdatePrompt() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, content, reason }: UpdatePromptParams) =>
      api.prompts.update(id, content, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['prompts', id] })
      queryClient.invalidateQueries({ queryKey: ['prompts', id, 'versions'] })
      toast.success('Prompt updated successfully')
    },
  })
}
```

---

### Approvals Queries

```typescript
// src/hooks/queries/useApprovals.ts

// Get approval queue
export function useApprovalQueue() {
  return useQuery({
    queryKey: ['approvals', 'queue'],
    queryFn: api.approvals.getQueue,
    refetchInterval: 30000, // Refresh every 30s
  })
}

// Submit for approval
export function useSubmitForApproval() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (projectId: string) => api.approvals.submit(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals', 'queue'] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Submitted for approval')
    },
  })
}

// Approve project
export function useApproveProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (approvalId: string) => api.approvals.approve(approvalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals', 'queue'] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project approved')
    },
  })
}

// Reject project
export function useRejectProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      api.approvals.reject(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals', 'queue'] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project rejected')
    },
  })
}
```

---

### Notifications Queries

```typescript
// src/hooks/queries/useNotifications.ts

// List notifications
export function useNotifications(options?: { limit?: number }) {
  return useQuery({
    queryKey: ['notifications', options],
    queryFn: () => api.notifications.list(options),
    refetchInterval: 30000, // Refresh every 30s
  })
}

// Get unread count
export function useUnreadCount() {
  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: api.notifications.getUnreadCount,
    refetchInterval: 15000, // Check every 15s
  })
}

// Mark as read
export function useMarkAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.notifications.markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] })
    },
  })
}

// Mark all as read
export function useMarkAllAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.notifications.markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.setQueryData(['notifications', 'unread-count'], 0)
    },
  })
}
```

---

## Client State with Zustand

Zustand manages client-side UI state that doesn't need to be synced with the server.

### Auth Store

```typescript
// src/stores/auth-store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  name: string
  role: 'content_writer' | 'marketing_manager' | 'system_admin'
  avatar?: string
}

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (updates: Partial<User>) => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (token, user) => {
        set({ token, user, isAuthenticated: true })
        // Set token in API client headers
        api.setAuthToken(token)
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false })
        api.clearAuthToken()
        // Clear React Query cache on logout
        queryClient.clear()
      },

      updateUser: (updates) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        }))
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
)
```

---

### UI Store

```typescript
// src/stores/ui-store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIStore {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark') => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',

      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }))
      },

      setSidebarOpen: (open) => {
        set({ sidebarOpen: open })
      },

      setTheme: (theme) => {
        set({ theme })
        // Apply theme to document
        document.documentElement.classList.toggle('dark', theme === 'dark')
      },
    }),
    {
      name: 'ui-storage',
    }
  )
)
```

---

### Filter Store

```typescript
// src/stores/filter-store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ProjectFilters {
  search: string
  emirate: string | null
  developer: string | null
  status: string | null
  priceRange: [number, number] | null
  dateRange: [Date, Date] | null
}

interface FilterStore {
  projectFilters: ProjectFilters
  setProjectFilters: (filters: Partial<ProjectFilters>) => void
  clearProjectFilters: () => void
}

const defaultFilters: ProjectFilters = {
  search: '',
  emirate: null,
  developer: null,
  status: null,
  priceRange: null,
  dateRange: null,
}

export const useFilterStore = create<FilterStore>()(
  persist(
    (set) => ({
      projectFilters: defaultFilters,

      setProjectFilters: (filters) => {
        set((state) => ({
          projectFilters: { ...state.projectFilters, ...filters },
        }))
      },

      clearProjectFilters: () => {
        set({ projectFilters: defaultFilters })
      },
    }),
    {
      name: 'filter-storage',
    }
  )
)
```

---

## Advanced Patterns

### Optimistic Updates

```typescript
// Optimistic update example for toggling favorites
export function useToggleFavorite() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, isFavorite }: ToggleFavoriteParams) =>
      api.projects.toggleFavorite(projectId, isFavorite),

    onMutate: async ({ projectId, isFavorite }) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: ['projects', projectId] })

      // Snapshot previous value
      const previous = queryClient.getQueryData(['projects', projectId])

      // Optimistically update
      queryClient.setQueryData(['projects', projectId], (old: Project) => ({
        ...old,
        isFavorite,
      }))

      return { previous, projectId }
    },

    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previous) {
        queryClient.setQueryData(
          ['projects', context.projectId],
          context.previous
        )
      }
      toast.error('Failed to update favorite')
    },

    onSettled: (data, error, { projectId }) => {
      // Always refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
    },
  })
}
```

---

### Infinite Queries for Pagination

```typescript
// Infinite scroll pagination
export function useInfiniteProjects(filters: ProjectFilters) {
  return useInfiniteQuery({
    queryKey: ['projects', 'infinite', filters],
    queryFn: ({ pageParam = 1 }) =>
      api.projects.list({ ...filters, page: pageParam }),
    getNextPageParam: (lastPage, pages) => {
      if (lastPage.has_next) {
        return pages.length + 1
      }
      return undefined
    },
    initialPageParam: 1,
  })
}

// Usage in component
function ProjectList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteProjects({ status: 'published' })

  return (
    <div>
      {data?.pages.map((page, i) => (
        <div key={i}>
          {page.projects.map(project => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ))}

      {hasNextPage && (
        <Button
          onClick={() => fetchNextPage()}
          loading={isFetchingNextPage}
        >
          Load More
        </Button>
      )}
    </div>
  )
}
```

---

### Dependent Queries

```typescript
// Query B depends on Query A's result
function ProjectWithImages({ projectId }: { projectId: string }) {
  // First query: Get project
  const { data: project } = useProject(projectId)

  // Second query: Get images (only runs if project exists)
  const { data: images } = useQuery({
    queryKey: ['images', project?.imageIds],
    queryFn: () => api.images.getMultiple(project!.imageIds),
    enabled: !!project?.imageIds,
  })

  return (
    <div>
      {project && <ProjectDetails project={project} />}
      {images && <ImageGallery images={images} />}
    </div>
  )
}
```

---

### Prefetching

```typescript
// Prefetch data on hover for instant navigation
function ProjectCard({ project }: { project: Project }) {
  const queryClient = useQueryClient()

  const prefetchProject = () => {
    queryClient.prefetchQuery({
      queryKey: ['projects', project.id],
      queryFn: () => api.projects.get(project.id),
      staleTime: 60000, // 1 minute
    })
  }

  return (
    <Link
      to={`/projects/${project.id}`}
      onMouseEnter={prefetchProject}
      onFocus={prefetchProject}
    >
      {project.name}
    </Link>
  )
}
```

---

## State Management Best Practices

### 1. Query Key Conventions

```typescript
// Use hierarchical query keys
['projects'] // All projects
['projects', { status: 'draft' }] // Filtered projects
['projects', '123'] // Single project
['projects', '123', 'history'] // Project sub-resource
```

### 2. Invalidation Strategies

```typescript
// Invalidate all project queries
queryClient.invalidateQueries({ queryKey: ['projects'] })

// Invalidate specific project
queryClient.invalidateQueries({ queryKey: ['projects', id] })

// Invalidate exact match only
queryClient.invalidateQueries({
  queryKey: ['projects', { status: 'draft' }],
  exact: true
})
```

### 3. Error Handling

```typescript
// Global error handler in QueryClient config
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      onError: (error) => {
        if (error.status === 401) {
          useAuthStore.getState().logout()
          navigate('/login')
        }
      },
    },
  },
})

// Per-query error handling
const { error, isError } = useProject(id)

if (isError) {
  return <ErrorMessage error={error} />
}
```

### 4. Loading States

```typescript
// Combine loading states
function ProjectPage() {
  const { data: project, isLoading: projectLoading } = useProject(id)
  const { data: images, isLoading: imagesLoading } = useImages(id)

  const isLoading = projectLoading || imagesLoading

  if (isLoading) return <LoadingSpinner />

  return <ProjectDetails project={project} images={images} />
}
```

---

## Related Documentation

- [Component Library](./COMPONENT_LIBRARY.md) - UI component specifications
- [Page Specifications](./PAGE_SPECIFICATIONS.md) - Page layouts and wireframes
- [Routing](./ROUTING.md) - Route configuration and guards
- [API Documentation](../01-backend/API_ENDPOINTS.md) - Backend API reference

---

**End of State Management Documentation**
