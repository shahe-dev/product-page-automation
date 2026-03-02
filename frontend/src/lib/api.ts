import type { AxiosError, AxiosProgressEvent, InternalAxiosRequestConfig } from "axios"
import axios from "axios"

import type {
  ActivityFeedItem,
  AdminStats,
  AdminUser,
  AllowlistEntry,
  ApiError,
  Approval,
  AuthResponse,
  ExtractRequest,
  ExtractResponse,
  FieldAddResponse,
  FieldDefinition,
  FieldDefinitionCreate,
  FieldDefinitionUpdate,
  FieldDeleteResponse,
  FieldsResponse,
  FieldUpdateResponse,
  GenerateRequest,
  GenerateResponse,
  GenerationRun,
  GroupedPromptsResponse,
  Job,
  JobStep,
  MaterialPackage,
  NotificationsResponse,
  PaginatedResponse,
  Project,
  ProjectDataFiles,
  ProjectDetail,
  ProjectFilters,
  Prompt,
  PromptFilters,
  PromptVersion,
  TeamStat,
} from "@/types"

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 300000,
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor: attach auth token and log in development
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Log request in development
  if (import.meta.env.DEV) {
    console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`)
  }

  const stored = sessionStorage.getItem("auth-storage")
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      if (parsed?.state?.token) {
        config.headers.Authorization = `Bearer ${parsed.state.token}`
      }
    } catch {
      // ignore parse errors
    }
  }
  return config
})

// Response interceptor: handle 401 and retry 5xx errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    // Handle 401 - try token refresh before logging out
    if (error.response?.status === 401) {
      const originalConfig = error.config as InternalAxiosRequestConfig & { _retry401?: boolean }
      if (!originalConfig._retry401) {
        originalConfig._retry401 = true
        try {
          // Lazy import to avoid circular dependency (auth.ts imports api.ts)
          const { refreshAccessToken } = await import("@/lib/auth")
          const newToken = await refreshAccessToken()
          if (newToken && originalConfig.headers) {
            originalConfig.headers.Authorization = `Bearer ${newToken}`
            return apiClient(originalConfig)
          }
        } catch {
          // Refresh failed -- fall through to logout
        }
      }
      sessionStorage.removeItem("auth-storage")
      window.dispatchEvent(new CustomEvent("auth:logout"))
      return Promise.reject(error)
    }

    // 5xx retry logic removed -- React Query handles retries (see query-client.ts).
    // Having both Axios and React Query retry causes up to 12 retries (3x4).
    return Promise.reject(error)
  },
)

// --- API methods ---

const auth = {
  getLoginUrl: () =>
    apiClient.get<{ oauth_url: string; state: string }>("/auth/login").then((r) => r.data),

  googleLogin: (code: string, state: string) =>
    apiClient.post<AuthResponse>("/auth/google", { code, state }).then((r) => r.data),

  me: () => apiClient.get<AuthResponse>("/auth/me").then((r) => r.data),

  logout: () => apiClient.post("/auth/logout").then((r) => r.data),
}

const projects = {
  list: (filters?: ProjectFilters) =>
    apiClient
      .get<PaginatedResponse<Project>>("/projects", { params: filters })
      .then((r) => r.data),

  get: (id: string) => apiClient.get<ProjectDetail>(`/projects/${id}`).then((r) => r.data),

  create: (data: Partial<Project>) =>
    apiClient.post<Project>("/projects", data).then((r) => r.data),

  update: (id: string, data: Partial<Project>) =>
    apiClient.patch<Project>(`/projects/${id}`, data).then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/projects/${id}`).then((r) => r.data),

  dataFiles: (id: string) =>
    apiClient.get<ProjectDataFiles>(`/projects/${id}/data-files`).then((r) => r.data),
}

const jobs = {
  list: (params?: { status?: string; limit?: number; offset?: number }) =>
    apiClient
      .get<{ jobs: Job[]; total: number; limit: number; offset: number }>("/jobs", { params })
      .then((r) => r.data),

  get: (id: string) => apiClient.get<Job>(`/jobs/${id}`).then((r) => r.data),

  getSteps: (id: string) =>
    apiClient.get<JobStep[]>(`/jobs/${id}/steps`).then((r) => r.data),
}

const upload = {
  // File upload to GCS (returns gcs_url for use with /process/extract)
  file: (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData()
    formData.append("file", file)

    return apiClient
      .post<{ gcs_url: string; filename: string; size: number }>("/upload/file", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e: AxiosProgressEvent) => {
          if (onProgress && e.total) {
            onProgress(Math.round((e.loaded * 100) / e.total))
          }
        },
      })
      .then((r) => r.data)
  },
}

const prompts = {
  list: (filters?: PromptFilters) =>
    apiClient
      .get<PaginatedResponse<Prompt>>("/prompts", { params: filters })
      .then((r) => r.data),

  get: (id: string) => apiClient.get<Prompt>(`/prompts/${id}`).then((r) => r.data),

  getVersions: (id: string) =>
    apiClient.get<PromptVersion[]>(`/prompts/${id}/versions`).then((r) => r.data),

  grouped: (templateType: string) =>
    apiClient
      .get<GroupedPromptsResponse>("/prompts/grouped", {
        params: { template_type: templateType },
      })
      .then((r) => r.data),

  create: (data: { name: string; template_type: string; content_variant?: string; content: string; character_limit?: number }) =>
    apiClient.post<Prompt>("/prompts", data).then((r) => r.data),

  update: (id: string, content: string, reason: string) =>
    apiClient.put<Prompt>(`/prompts/${id}`, { content, change_reason: reason }).then((r) => r.data),
}

const approvals = {
  list: (filters?: { status?: string; project_id?: string }) =>
    apiClient
      .get<Approval[]>("/workflow/approvals", { params: filters })
      .then((r) => r.data),

  approve: (id: string) =>
    apiClient.post(`/workflow/approvals/${id}/approve`).then((r) => r.data),

  reject: (id: string, reason: string) =>
    apiClient.post(`/workflow/approvals/${id}/reject`, { reason }).then((r) => r.data),

  submit: (project_id: string) =>
    apiClient.post("/workflow/approvals", { project_id }).then((r) => r.data),
}

const workflow = {
  stats: () =>
    apiClient.get("/workflow/stats").then((r) => r.data),

  moveItem: (itemId: string, data: { workflow_status: string; published_url?: string }) =>
    apiClient.put(`/workflow/items/${itemId}/move`, data).then((r) => r.data),
}

const notifications = {
  list: (options?: { limit?: number; page?: number; unread_only?: boolean }) =>
    apiClient
      .get<NotificationsResponse>("/notifications", { params: options })
      .then((r) => r.data),

  getUnreadCount: () =>
    apiClient.get<{ count: number }>("/notifications/unread-count").then((r) => r.data.count),

  markAsRead: (id: string) =>
    apiClient.put(`/notifications/${id}/read`).then((r) => r.data),

  markAllAsRead: () => apiClient.put("/notifications/read-all").then((r) => r.data),
}

const admin = {
  listAllowlist: () =>
    apiClient.get<AllowlistEntry[]>("/admin/allowlist").then((r) => r.data),

  addAllowlistEntry: (data: { email: string; role: string }) =>
    apiClient.post<AllowlistEntry>("/admin/allowlist", data).then((r) => r.data),

  updateAllowlistEntry: (id: string, data: { role: string }) =>
    apiClient.put<AllowlistEntry>(`/admin/allowlist/${id}`, data).then((r) => r.data),

  removeAllowlistEntry: (id: string) =>
    apiClient.delete(`/admin/allowlist/${id}`).then((r) => r.data),

  getStats: () =>
    apiClient.get<AdminStats>("/admin/stats").then((r) => r.data),

  listUsers: () =>
    apiClient.get<AdminUser[]>("/admin/users").then((r) => r.data),

  updateUserRole: (userId: string, role: string) =>
    apiClient.put(`/admin/users/${userId}/role`, { role }).then((r) => r.data),
}

const activity = {
  feed: (params?: { page?: number; limit?: number }) =>
    apiClient
      .get<{ items: ActivityFeedItem[]; page: number; limit: number }>("/activity/feed", {
        params,
      })
      .then((r) => r.data),

  teamStats: () =>
    apiClient.get<TeamStat[]>("/activity/team-stats").then((r) => r.data),
}

const qa = {
  compare: (projectId: string) =>
    apiClient
      .post("/qa/compare", {
        project_id: projectId,
        checkpoint_type: "generation",
      })
      .then((r) => r.data),

  results: (projectId: string) =>
    apiClient.get(`/qa/${projectId}/results`).then((r) => r.data),

  history: (params?: { page?: number; limit?: number; project_id?: string }) =>
    apiClient.get("/qa/history", { params }).then((r) => r.data),
}

// Multi-template pipeline API
const process = {
  extract: (request: ExtractRequest) =>
    apiClient
      .post<ExtractResponse>("/process/extract", request)
      .then((r) => r.data),

  generate: (request: GenerateRequest) =>
    apiClient
      .post<GenerateResponse>("/process/generate", request)
      .then((r) => r.data),

  // Debug/inspection endpoints
  getMaterialPackage: (id: string) =>
    apiClient
      .get<MaterialPackage>(`/process/material-packages/${id}`)
      .then((r) => r.data),

  getGenerationRuns: (projectId: string) =>
    apiClient
      .get<GenerationRun[]>(`/process/projects/${projectId}/generations`)
      .then((r) => r.data),
}

const downloads = {
  assets: (projectId: string, params?: { category?: string; ids?: string }) =>
    apiClient
      .get(`/downloads/projects/${projectId}/assets`, {
        params,
        responseType: "blob",
      })
      .then((r) => r.data as Blob),
}

const templates = {
  // List all templates
  list: (params?: { template_type?: string; content_variant?: string; is_active?: boolean }) =>
    apiClient
      .get<{ items: Array<{ id: string; name: string; template_type: string; field_count?: number; is_active: boolean }> }>("/templates", { params })
      .then((r) => r.data),

  // Get field definitions by template type
  getFields: (templateType: string, contentVariant: string = "standard") =>
    apiClient
      .get<FieldsResponse>(`/templates/type/${templateType}/fields`, {
        params: { content_variant: contentVariant },
      })
      .then((r) => r.data),

  // Replace all field definitions
  updateFields: (
    templateType: string,
    fields: Record<string, FieldDefinition>,
    contentVariant: string = "standard"
  ) =>
    apiClient
      .put<FieldUpdateResponse>(`/templates/type/${templateType}/fields`, { fields }, {
        params: { content_variant: contentVariant },
      })
      .then((r) => r.data),

  // Add a single field
  addField: (
    templateType: string,
    fieldName: string,
    field: FieldDefinitionCreate,
    contentVariant: string = "standard"
  ) =>
    apiClient
      .post<FieldAddResponse>(`/templates/type/${templateType}/fields/${fieldName}`, field, {
        params: { content_variant: contentVariant },
      })
      .then((r) => r.data),

  // Soft-delete a field
  deleteField: (templateType: string, fieldName: string, contentVariant: string = "standard") =>
    apiClient
      .delete<FieldDeleteResponse>(`/templates/type/${templateType}/fields/${fieldName}`, {
        params: { content_variant: contentVariant },
      })
      .then((r) => r.data),

  // Update a single field
  updateField: (
    templateType: string,
    fieldName: string,
    updates: FieldDefinitionUpdate,
    contentVariant: string = "standard"
  ) =>
    apiClient
      .patch<FieldUpdateResponse>(`/templates/type/${templateType}/fields/${fieldName}`, updates, {
        params: { content_variant: contentVariant },
      })
      .then((r) => r.data),
}

export const api = {
  activity,
  admin,
  approvals,
  auth,
  downloads,
  jobs,
  notifications,
  process,
  projects,
  prompts,
  qa,
  templates,
  upload,
  workflow,
}

export { apiClient }
