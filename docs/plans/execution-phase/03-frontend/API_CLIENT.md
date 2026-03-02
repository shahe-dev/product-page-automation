# API Client

**Last Updated:** 2026-01-24
**Status:** Active
**Owner:** Frontend Team

---

## Overview

This document specifies the API client architecture for the PDP Automation v.3 frontend. The client uses Axios with TypeScript for type-safe API calls, integrated with React Query for caching and state management.

### Technology Stack

- **HTTP Client:** Axios 1.x
- **State Management:** React Query 5.x (TanStack Query)
- **Type Generation:** OpenAPI TypeScript (from backend schema)
- **Error Handling:** Custom error classes with Sentry integration

---

## API Client Setup

### Base Configuration

```typescript
// src/lib/api.ts
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for OAuth session
})
```

### Request Interceptor

```typescript
// Add auth token and request tracking
apiClient.interceptors.request.use(
  (config) => {
    // Add request ID for tracing
    config.headers['X-Request-ID'] = crypto.randomUUID()

    // Add auth token if available
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)
```

### Response Interceptor

```typescript
// Handle errors and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<APIErrorResponse>) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        await refreshAccessToken()
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed - redirect to login
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Transform error for consistent handling
    throw transformAPIError(error)
  }
)
```

---

## Type Definitions

### API Response Types

```typescript
// src/types/api.ts

// Standard paginated response
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_next: boolean
}

// Standard error response
export interface APIErrorResponse {
  error_code: string
  message: string
  details?: Record<string, unknown>
  trace_id?: string
}

// Project types
export interface Project {
  id: string
  name: string
  developer: string
  emirate: string
  starting_price: number
  workflow_status: WorkflowStatus
  created_at: string
  updated_at: string
}

export type WorkflowStatus =
  | 'pending_extraction'
  | 'extraction_complete'
  | 'content_generated'
  | 'qa_passed'
  | 'published'
  | 'failed'

// Job types
export interface Job {
  id: string
  project_id: string
  status: JobStatus
  progress: number
  current_step: string
  error_message?: string
  created_at: string
  completed_at?: string
}

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed'
```

---

## API Endpoints

### Typed API Functions

```typescript
// src/lib/api.ts

export const api = {
  // Projects
  projects: {
    list: async (params: ProjectListParams): Promise<PaginatedResponse<Project>> => {
      const { data } = await apiClient.get('/projects', { params })
      return data
    },

    get: async (id: string): Promise<Project> => {
      const { data } = await apiClient.get(`/projects/${id}`)
      return data
    },

    create: async (payload: CreateProjectPayload): Promise<Project> => {
      const { data } = await apiClient.post('/projects', payload)
      return data
    },

    update: async (id: string, payload: UpdateProjectPayload): Promise<Project> => {
      const { data } = await apiClient.patch(`/projects/${id}`, payload)
      return data
    },

    delete: async (id: string): Promise<void> => {
      await apiClient.delete(`/projects/${id}`)
    },
  },

  // Jobs
  jobs: {
    list: async (params: JobListParams): Promise<PaginatedResponse<Job>> => {
      const { data } = await apiClient.get('/jobs', { params })
      return data
    },

    get: async (id: string): Promise<Job> => {
      const { data } = await apiClient.get(`/jobs/${id}`)
      return data
    },

    create: async (payload: CreateJobPayload): Promise<Job> => {
      const { data } = await apiClient.post('/jobs', payload)
      return data
    },

    retry: async (id: string): Promise<Job> => {
      const { data } = await apiClient.post(`/jobs/${id}/retry`)
      return data
    },

    cancel: async (id: string): Promise<void> => {
      await apiClient.post(`/jobs/${id}/cancel`)
    },
  },

  // Upload
  upload: {
    pdf: async (file: File, onProgress?: (progress: number) => void): Promise<UploadResponse> => {
      const formData = new FormData()
      formData.append('file', file)

      const { data } = await apiClient.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            onProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total))
          }
        },
      })
      return data
    },
  },

  // Prompts
  prompts: {
    list: async (params?: PromptListParams): Promise<PaginatedResponse<Prompt>> => {
      const { data } = await apiClient.get('/prompts', { params })
      return data
    },

    get: async (id: string): Promise<Prompt> => {
      const { data } = await apiClient.get(`/prompts/${id}`)
      return data
    },

    create: async (payload: CreatePromptPayload): Promise<Prompt> => {
      const { data } = await apiClient.post('/prompts', payload)
      return data
    },

    update: async (id: string, payload: UpdatePromptPayload): Promise<Prompt> => {
      const { data } = await apiClient.patch(`/prompts/${id}`, payload)
      return data
    },

    activate: async (id: string): Promise<Prompt> => {
      const { data } = await apiClient.post(`/prompts/${id}/activate`)
      return data
    },
  },

  // Health
  health: {
    check: async (): Promise<HealthCheckResponse> => {
      const { data } = await apiClient.get('/health')
      return data
    },
  },

  // Auth
  auth: {
    login: async (): Promise<void> => {
      window.location.href = `${API_BASE_URL}/auth/login`
    },

    logout: async (): Promise<void> => {
      await apiClient.post('/auth/logout')
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    },

    me: async (): Promise<User> => {
      const { data } = await apiClient.get('/auth/me')
      return data
    },
  },
}
```

---

## Error Handling

### Custom Error Classes

```typescript
// src/lib/errors.ts

export class APIError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public details?: Record<string, unknown>,
    public traceId?: string
  ) {
    super(message)
    this.name = 'APIError'
  }

  isValidationError(): boolean {
    return this.code === 'VALIDATION_ERROR'
  }

  isNotFound(): boolean {
    return this.status === 404
  }

  isRateLimited(): boolean {
    return this.status === 429
  }
}

export function transformAPIError(error: AxiosError<APIErrorResponse>): APIError {
  const response = error.response

  if (!response) {
    return new APIError(
      'NETWORK_ERROR',
      'Network error. Please check your connection.',
      0
    )
  }

  const { error_code, message, details, trace_id } = response.data

  return new APIError(
    error_code || 'UNKNOWN_ERROR',
    message || 'An unexpected error occurred.',
    response.status,
    details,
    trace_id
  )
}
```

### Error Handling in Components

```typescript
// Using React Query error handling
function ProjectsList() {
  const { data, error, isLoading } = useProjects({ status: 'published' })

  if (isLoading) return <Skeleton />

  if (error) {
    if (error instanceof APIError) {
      if (error.isNotFound()) {
        return <EmptyState message="No projects found" />
      }
      return <ErrorMessage code={error.code} message={error.message} />
    }
    return <ErrorMessage message="Something went wrong" />
  }

  return <ProjectsTable data={data.items} />
}
```

---

## Request Patterns

### Query Parameters

```typescript
// Pagination and filtering
interface ProjectListParams {
  page?: number
  limit?: number
  sort?: string
  search?: string
  developer?: string
  emirate?: string
  status?: WorkflowStatus
  price_min?: number
  price_max?: number
}

// Usage
const projects = await api.projects.list({
  page: 1,
  limit: 20,
  sort: '-created_at',
  developer: 'Emaar',
  status: 'published',
})
```

### File Uploads with Progress

```typescript
// Upload PDF with progress tracking
function UploadForm() {
  const [progress, setProgress] = useState(0)
  const uploadMutation = useUploadPDF()

  const handleUpload = async (file: File) => {
    await uploadMutation.mutateAsync({
      file,
      onProgress: setProgress,
    })
  }

  return (
    <div>
      <FileDropzone onDrop={handleUpload} />
      {progress > 0 && <ProgressBar value={progress} />}
    </div>
  )
}
```

### Optimistic Updates

```typescript
// Update project with optimistic UI
const updateMutation = useMutation({
  mutationFn: ({ id, data }: { id: string; data: UpdateProjectPayload }) =>
    api.projects.update(id, data),

  onMutate: async ({ id, data }) => {
    await queryClient.cancelQueries({ queryKey: ['projects', id] })

    const previousProject = queryClient.getQueryData<Project>(['projects', id])

    queryClient.setQueryData(['projects', id], (old: Project) => ({
      ...old,
      ...data,
    }))

    return { previousProject }
  },

  onError: (err, variables, context) => {
    if (context?.previousProject) {
      queryClient.setQueryData(['projects', variables.id], context.previousProject)
    }
  },

  onSettled: (data, error, { id }) => {
    queryClient.invalidateQueries({ queryKey: ['projects', id] })
  },
})
```

---

## WebSocket Integration

### Real-time Job Updates

```typescript
// src/lib/websocket.ts
import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

export function connectWebSocket(token: string): Socket {
  if (socket) return socket

  socket = io(import.meta.env.VITE_WS_URL, {
    auth: { token },
    transports: ['websocket'],
  })

  socket.on('connect', () => {
    console.log('WebSocket connected')
  })

  socket.on('disconnect', () => {
    console.log('WebSocket disconnected')
  })

  return socket
}

// React hook for job updates
export function useJobUpdates(jobId: string, onUpdate: (job: Job) => void) {
  useEffect(() => {
    if (!socket) return

    socket.on(`job:${jobId}`, onUpdate)

    return () => {
      socket?.off(`job:${jobId}`, onUpdate)
    }
  }, [jobId, onUpdate])
}
```

---

## Testing

### Mocking API Calls

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/projects', () => {
    return HttpResponse.json({
      items: [
        { id: '1', name: 'Test Project', developer: 'Emaar' },
      ],
      total: 1,
      page: 1,
      limit: 20,
      has_next: false,
    })
  }),

  http.post('/api/projects', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      id: crypto.randomUUID(),
      ...body,
      created_at: new Date().toISOString(),
    }, { status: 201 })
  }),
]
```

---

## Related Documentation

- [State Management](./STATE_MANAGEMENT.md) - React Query integration
- [Component Architecture](./COMPONENT_ARCHITECTURE.md) - Component patterns
- [API Design](../01-architecture/API_DESIGN.md) - Backend API specification
- [Error Handling](../04-backend/ERROR_HANDLING.md) - Error response formats
