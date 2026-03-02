// ============================================================================
// PDP Automation v.3 - Core Type Definitions
// ============================================================================

// User & Auth
export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  avatar?: string
}

export type UserRole = "admin" | "manager" | "user"

export interface AuthResponse {
  access_token: string
  // TODO: Refresh token should be delivered only via httpOnly cookie, not in JS-accessible response body.
  // Keep this field for backwards compatibility until backend migration is complete.
  refresh_token?: string
  token_type: string
  expires_in: number
  user: User
}

// Projects
export interface Project {
  id: string
  name: string
  developer?: string
  location?: string
  emirate?: string
  workflow_status: ProjectStatus
  template_type: TemplateType
  sheet_url?: string
  thumbnail?: string
  created_at: string
  updated_at: string
  created_by?: {
    id: string
    name: string
    email: string
  } | null
  image_count?: number
  floor_plan_count?: number
  published_url?: string
  published_at?: string
}

export interface ProjectImage {
  id: string
  category: string
  image_url: string
  thumbnail_url?: string
  alt_text?: string
  filename?: string
  width?: number
  height?: number
  file_size?: number
  format?: string
  display_order: number
}

export interface ProjectDataFiles {
  files: Record<string, unknown>
}

export interface ProjectFloorPlan {
  id: string
  unit_type: string
  bedrooms?: number
  bathrooms?: number
  total_sqft?: number
  balcony_sqft?: number
  builtup_sqft?: number
  parsed_data?: Record<string, unknown>
  image_url: string
  display_order: number
}

export interface GenerationRunSummary {
  template_type: string
  status: "pending" | "processing" | "completed" | "failed"
  sheet_url: string | null
  completed_at: string | null
}

export interface ProjectDetail extends Project {
  starting_price?: number
  price_per_sqft?: number
  handover_date?: string
  payment_plan?: string
  description?: string
  property_types?: string[]
  unit_sizes?: (string | Record<string, unknown>)[]
  amenities?: string[]
  features?: string[]
  total_units?: number
  floors?: number
  buildings?: number
  custom_fields?: Record<string, unknown>
  original_pdf_url?: string
  processed_zip_url?: string
  generated_content?: Record<string, unknown>
  published_url?: string
  published_at?: string
  is_active?: boolean
  images: ProjectImage[]
  floor_plans: ProjectFloorPlan[]
  material_package_id?: string
  generation_runs?: GenerationRunSummary[]
}

// Aligned with backend WorkflowStatus enum (enums.py)
export type ProjectStatus =
  | "draft"
  | "pending_approval"
  | "approved"
  | "revision_requested"
  | "publishing"
  | "published"
  | "qa_verified"
  | "complete"

export type TemplateType =
  | "aggregators"
  | "opr"
  | "mpp"
  | "adop"
  | "adre"
  | "commercial"

export interface ProjectFilters {
  search?: string
  emirate?: string
  developer?: string
  status?: ProjectStatus
  page?: number
  per_page?: number
}

// Jobs
export type JobType = "extraction" | "generation"

export interface Job {
  id: string
  project_id?: string | null
  status: JobStatus
  current_step: string
  progress_message?: string  // Granular substep detail (e.g., "Generating: project_name")
  progress: number
  error?: string
  created_at: string
  updated_at: string
  started_at?: string    // When processing began
  completed_at?: string  // When processing ended
  // Multi-template pipeline fields
  job_type?: JobType
  material_package_id?: string
  template_type?: TemplateType
}

export type JobStatus = "pending" | "processing" | "completed" | "failed" | "cancelled"

export type JobStepStatus = "pending" | "in_progress" | "completed" | "failed" | "skipped"

export interface JobStep {
  id: string
  step_id: string
  label: string
  status: JobStepStatus
  result?: Record<string, unknown>
  error_message?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

// Paginated response
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  has_next: boolean
}

// Notifications
export interface Notification {
  id: string
  title: string
  message: string
  read: boolean
  created_at: string
}

// Prompts
export interface Prompt {
  id: string
  name: string
  template_type: string
  content_variant: string
  content?: string
  version: number
  is_active: boolean
  character_limit: number | null
  updated_at: string
  updated_by?: {
    name: string
  } | null
}

export interface PromptVersion {
  version: number
  content: string
  change_reason: string | null
  created_at: string
  created_by: {
    id: string
    name: string
  }
}

export interface PromptFilters {
  search?: string
  template_type?: string
  content_variant?: string
  is_active?: boolean
}

// Dashboard
export interface DashboardStats {
  total_projects: number
  active_projects: number
  completed_projects: number
  pending_approvals: number
  failed_jobs: number
}

export interface ActivityItem {
  id: string
  type: "project_created" | "project_updated" | "job_completed" | "approval_submitted"
  title: string
  description: string
  timestamp: string
  user_name: string
  project_id?: string
}

// Approvals (P3-24: moved from use-approvals.ts)
export interface Approval {
  id: string
  project_id: string
  project_name: string
  submitted_by: string
  submitted_at: string
  status: "pending" | "approved" | "rejected"
  reviewed_by?: string
  reviewed_at?: string
  rejection_reason?: string
}

export interface ApprovalFilters {
  status?: "pending" | "approved" | "rejected"
  project_id?: string
}

// QA Issues (P3-24: moved from IssueList.tsx)
export interface QAIssue {
  id: string
  field: string
  type: "factual" | "compliance" | "consistency" | "quality"
  severity: "critical" | "major" | "minor"
  description: string
  source_value?: string
  generated_value?: string
  status: "open" | "resolved" | "dismissed"
}

// Grouped Prompts Response (for template-based prompt management)
export interface PromptFieldSummary {
  field_name: string
  row: number
  character_limit: number | null
  required: boolean
  field_type?: FieldType
  has_prompt: boolean
  prompt_id: string | null
  version: number | null
  content_preview: string | null
}

export interface PromptSection {
  section: string
  field_count: number
  prompts_defined: number
  fields: PromptFieldSummary[]
}

export interface GroupedPromptsResponse {
  template_type: string
  total_fields: number
  promptable_fields?: number
  total_prompts_defined: number
  coverage_percent: number
  sections: PromptSection[]
}

// Template Field Definitions (for Dynamic Field Editor)
export type FieldType = "GENERATED" | "EXTRACTED" | "HYBRID" | "STATIC"

export interface FieldDefinition {
  row: number
  section: string
  char_limit: number | null
  required: boolean
  field_type: FieldType
  is_active: boolean
}

export interface FieldDefinitionCreate {
  row: number
  section: string
  char_limit?: number | null
  required?: boolean
  field_type?: FieldType
}

export interface FieldDefinitionUpdate {
  row?: number
  section?: string
  char_limit?: number | null
  required?: boolean
  field_type?: FieldType
}

export interface FieldsResponse {
  template_type: string
  field_count: number
  fields: Record<string, FieldDefinition>
}

export interface FieldUpdateResponse {
  updated: boolean
  field_count: number
}

export interface FieldDeleteResponse {
  deleted: boolean
  field_name: string
}

export interface FieldAddResponse {
  added: boolean
  field_name: string
}

// For local state in FieldEditor
export interface FieldEditorRow extends FieldDefinition {
  name: string
  isDirty?: boolean
  isNew?: boolean
}

// Email Allowlist (admin)
export interface AllowlistEntry {
  id: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface AllowlistEntryCreate {
  email: string
  role: UserRole
}

// Admin Dashboard
export interface AdminStats {
  user_count: number
  active_jobs: number
  failed_jobs_24h: number
  total_projects: number
  projects_by_status: Record<string, number>
}

export interface AdminUser {
  id: string
  email: string
  name: string
  role: UserRole
  last_login_at: string | null
  project_count: number
}

// Activity Feed
export interface ActivityFeedItem {
  id: string
  type: string
  title: string
  description: string
  timestamp: string | null
  user_name: string
  project_id: string | null
}

export interface TeamStat {
  user_id: string
  name: string
  email: string
  projects_this_week: number
  approvals_this_week: number
  last_active: string | null
}

// Notification detail (for notifications page)
export interface NotificationItem {
  id: string
  type: string
  title: string
  message: string
  project_id: string | null
  job_id: string | null
  is_read: boolean
  created_at: string | null
}

export interface NotificationsResponse {
  items: NotificationItem[]
  total: number
  page: number
  limit: number
}

// API Error
export interface ApiError {
  detail: string
  status_code: number
}

// ============================================================================
// Multi-Template Pipeline Types
// ============================================================================

// Process API types
export interface ExtractRequest {
  pdf_url: string
  template_ids: string[]
}

export interface ExtractResponse {
  extraction_job_id: string
  status: string
  template_ids: string[]
  message: string
}

export interface GenerateRequest {
  material_package_id: string
  template_types: string[]
}

export interface GenerateResponse {
  generation_job_ids: string[]
  status: string
  message: string
}

// MaterialPackage for inspection/debugging
export interface MaterialPackage {
  id: string
  project_id: string | null
  source_job_id: string | null
  gcs_base_path: string
  package_version: string
  extraction_summary: Record<string, unknown>
  structured_data: Record<string, unknown>
  status: "pending" | "ready" | "expired" | "error"
  created_at: string
  updated_at: string
  expires_at: string | null
}

// GenerationRun for tracking per-template status
export interface GenerationRun {
  id: string
  project_id: string
  material_package_id: string | null
  template_type: TemplateType
  job_id: string | null
  generated_content: Record<string, unknown> | null
  sheet_url: string | null
  drive_folder_url: string | null
  status: "pending" | "processing" | "completed" | "failed"
  created_at: string
  completed_at: string | null
}

// Composite job tracking for UI
export interface PipelineProgress {
  extraction_job_id: string
  extraction_status: JobStatus
  extraction_progress: number
  extraction_completed_at: string | null
  extraction_steps: JobStep[]
  extraction_current_step: string | null
  extraction_progress_message: string | null
  generation_jobs: {
    job_id: string
    template_type: TemplateType
    status: JobStatus
    progress: number
    progress_message: string | null
  }[]
  overall_progress: number
}
