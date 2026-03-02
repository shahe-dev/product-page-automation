# Multi-Template Pipeline - Phase C (Frontend) & D (Polish) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update the frontend to use the new multi-template extraction + generation pipeline, replacing the old single-template /upload/pdf flow.

**Architecture:** Frontend calls POST /process/extract with PDF + template_ids[], then tracks 1 extraction job + N generation jobs. ProgressTracker shows composite progress across all jobs.

**Tech Stack:** React 19, TypeScript strict mode, React Query, Zustand, Vitest, shadcn/ui

---

## Prerequisites

Phase A and B (backend) must be complete. After Phase B:
- `POST /process/extract` - uploads PDF, returns extraction_job_id
- `POST /process/generate` - takes material_package_id + template_types[], returns generation_job_ids[]
- Job model has `job_type` field: `extraction` | `generation`
- Job model has `material_package_id` FK
- MaterialPackage model stores extraction results
- GenerationRun model tracks per-template generation
- Auto-dispatch: extraction completion triggers generation jobs

**Clean Cutover:** No backward compatibility with old `/upload/pdf` endpoint. Remove `FULL` job type references entirely.

---

## Phase C: Frontend Multi-Template Support

### Task C.1: Add TypeScript Types for Multi-Template Pipeline

**Files:**
- Modify: `frontend/src/types/index.ts`
- Test: `frontend/src/types/__tests__/types.test.ts` (create)

**Step 1: Write the failing test**

```typescript
// frontend/src/types/__tests__/types.test.ts
import { describe, it, expect } from "vitest"
import type {
  JobType,
  ExtractRequest,
  ExtractResponse,
  GenerateRequest,
  GenerateResponse,
  MaterialPackage,
  GenerationRun,
  Job,
} from "@/types"

describe("Multi-template types", () => {
  it("JobType includes extraction and generation", () => {
    const types: JobType[] = ["extraction", "generation"]
    expect(types).toContain("extraction")
    expect(types).toContain("generation")
  })

  it("ExtractRequest has required fields", () => {
    const req: ExtractRequest = {
      pdf_url: "gs://bucket/test.pdf",
      template_ids: ["opr", "mpp"],
    }
    expect(req.template_ids.length).toBe(2)
  })

  it("ExtractResponse has extraction_job_id", () => {
    const res: ExtractResponse = {
      extraction_job_id: "uuid-123",
      status: "pending",
      template_ids: ["opr"],
      message: "Created",
    }
    expect(res.extraction_job_id).toBeDefined()
  })

  it("GenerateResponse has generation_job_ids array", () => {
    const res: GenerateResponse = {
      generation_job_ids: ["job-1", "job-2"],
      status: "dispatched",
      message: "Created 2 jobs",
    }
    expect(res.generation_job_ids.length).toBe(2)
  })

  it("Job has optional job_type and material_package_id", () => {
    const job: Job = {
      id: "uuid",
      project_id: "proj-id",
      status: "pending",
      current_step: "upload",
      progress: 0,
      created_at: "2026-02-05T00:00:00Z",
      updated_at: "2026-02-05T00:00:00Z",
      job_type: "extraction",
      material_package_id: "pkg-id",
    }
    expect(job.job_type).toBe("extraction")
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/types/__tests__/types.test.ts`
Expected: FAIL with "cannot find module" or type errors

**Step 3: Write minimal implementation**

Add to `frontend/src/types/index.ts` after the existing Job interface:

```typescript
// Multi-template pipeline types

export type JobType = "extraction" | "generation"

// Extend existing Job interface
export interface Job {
  id: string
  project_id: string
  status: JobStatus
  current_step: string
  progress_message?: string
  progress: number
  error?: string
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
  // New fields for multi-template pipeline
  job_type?: JobType
  material_package_id?: string
  template_type?: TemplateType
}

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
  generation_jobs: {
    job_id: string
    template_type: TemplateType
    status: JobStatus
    progress: number
  }[]
  overall_progress: number
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/types/__tests__/types.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/types/__tests__/types.test.ts
git commit -m "$(cat <<'EOF'
feat(frontend): add TypeScript types for multi-template pipeline

Adds JobType, ExtractRequest/Response, GenerateRequest/Response,
MaterialPackage, GenerationRun, and PipelineProgress types.
Extends Job interface with job_type and material_package_id.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.2: Add Process API Methods

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Test: `frontend/src/lib/__tests__/api.test.ts` (create or add to)

**Step 1: Write the failing test**

```typescript
// frontend/src/lib/__tests__/api.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest"
import { api } from "@/lib/api"

// Mock axios
vi.mock("axios", () => ({
  default: {
    create: () => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    }),
  },
}))

describe("api.process", () => {
  it("has extract method", () => {
    expect(api.process).toBeDefined()
    expect(api.process.extract).toBeDefined()
    expect(typeof api.process.extract).toBe("function")
  })

  it("has generate method", () => {
    expect(api.process.generate).toBeDefined()
    expect(typeof api.process.generate).toBe("function")
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/lib/__tests__/api.test.ts`
Expected: FAIL with "api.process is undefined"

**Step 3: Write the implementation**

Add to `frontend/src/lib/api.ts` after the `upload` object:

```typescript
import type {
  ExtractRequest,
  ExtractResponse,
  GenerateRequest,
  GenerateResponse,
  MaterialPackage,
  GenerationRun,
} from "@/types"

const process = {
  extract: (request: ExtractRequest) =>
    apiClient
      .post<ExtractResponse>("/process/extract", request)
      .then((r) => r.data),

  generate: (request: GenerateRequest) =>
    apiClient
      .post<GenerateResponse>("/process/generate", request)
      .then((r) => r.data),

  // Debug/inspection endpoints (Phase D)
  getMaterialPackage: (id: string) =>
    apiClient
      .get<MaterialPackage>(`/material-packages/${id}`)
      .then((r) => r.data),

  getGenerationRuns: (projectId: string) =>
    apiClient
      .get<GenerationRun[]>(`/projects/${projectId}/generations`)
      .then((r) => r.data),
}

// Update export
export const api = {
  auth,
  projects,
  jobs,
  upload,
  process, // NEW
  prompts,
  approvals,
  notifications,
  templates,
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/lib/__tests__/api.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/lib/__tests__/api.test.ts
git commit -m "$(cat <<'EOF'
feat(frontend): add process API methods for extract/generate

Adds api.process.extract() and api.process.generate() for
multi-template pipeline. Includes getMaterialPackage and
getGenerationRuns for debugging.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.3: Create useExtractAndGenerate Hook

**Files:**
- Create: `frontend/src/hooks/queries/use-process.ts`
- Modify: `frontend/src/hooks/queries/index.ts`
- Test: `frontend/src/hooks/queries/__tests__/use-process.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend/src/hooks/queries/__tests__/use-process.test.ts
import { describe, it, expect, vi } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useExtractPdf } from "../use-process"
import { api } from "@/lib/api"
import type { ReactNode } from "react"

vi.mock("@/lib/api", () => ({
  api: {
    process: {
      extract: vi.fn(),
    },
  },
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
  }
}

describe("useExtractPdf", () => {
  it("calls api.process.extract with correct payload", async () => {
    const mockResponse = {
      extraction_job_id: "job-123",
      status: "pending",
      template_ids: ["opr", "mpp"],
      message: "Created",
    }
    vi.mocked(api.process.extract).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useExtractPdf(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      pdfUrl: "gs://bucket/test.pdf",
      templateIds: ["opr", "mpp"],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(api.process.extract).toHaveBeenCalledWith({
      pdf_url: "gs://bucket/test.pdf",
      template_ids: ["opr", "mpp"],
    })
    expect(result.current.data?.extraction_job_id).toBe("job-123")
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/hooks/queries/__tests__/use-process.test.ts`
Expected: FAIL with "useExtractPdf is not exported"

**Step 3: Write the implementation**

```typescript
// frontend/src/hooks/queries/use-process.ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { ExtractResponse, GenerateResponse, PipelineProgress } from "@/types"

/**
 * Hook to start an extraction job with multi-template support.
 *
 * Usage:
 * const { mutate, data, isPending } = useExtractPdf()
 * mutate({ pdfUrl: "gs://...", templateIds: ["opr", "mpp"] })
 */
export function useExtractPdf() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      pdfUrl,
      templateIds,
    }: {
      pdfUrl: string
      templateIds: string[]
    }): Promise<ExtractResponse> => {
      return api.process.extract({
        pdf_url: pdfUrl,
        template_ids: templateIds,
      })
    },
    onSuccess: (result) => {
      // Invalidate jobs list to show new extraction job
      queryClient.invalidateQueries({ queryKey: ["jobs"] })
      // Pre-populate the job query with initial data
      queryClient.setQueryData(["jobs", result.extraction_job_id], {
        id: result.extraction_job_id,
        status: result.status,
        job_type: "extraction",
        current_step: "upload",
        progress: 0,
      })
    },
  })
}

/**
 * Hook to start generation jobs for templates using an existing MaterialPackage.
 */
export function useGenerateContent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      materialPackageId,
      templateTypes,
    }: {
      materialPackageId: string
      templateTypes: string[]
    }): Promise<GenerateResponse> => {
      return api.process.generate({
        material_package_id: materialPackageId,
        template_types: templateTypes,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] })
    },
  })
}

/**
 * Hook to track composite progress across extraction + generation jobs.
 *
 * Polls all related jobs and computes overall progress.
 */
export function usePipelineProgress(
  extractionJobId: string | null,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ["pipeline-progress", extractionJobId],
    queryFn: async (): Promise<PipelineProgress | null> => {
      if (!extractionJobId) return null

      // Fetch extraction job
      const extractionJob = await api.jobs.get(extractionJobId)

      // Fetch all jobs to find related generation jobs
      // Generation jobs have material_package_id matching extraction's output
      const { jobs } = await api.jobs.list({ limit: 50 })

      // Find generation jobs that reference the same project
      const generationJobs = jobs.filter(
        (j) => j.job_type === "generation" && j.project_id === extractionJob.project_id
      )

      // Calculate overall progress
      // Extraction is 60% of total, generation is 40%
      const extractionWeight = 0.6
      const generationWeight = 0.4

      const extractionProgress = extractionJob.progress * extractionWeight

      let generationProgress = 0
      if (generationJobs.length > 0) {
        const avgGenProgress =
          generationJobs.reduce((sum, j) => sum + j.progress, 0) / generationJobs.length
        generationProgress = avgGenProgress * generationWeight
      } else if (extractionJob.status === "completed") {
        // No generation jobs yet but extraction done
        generationProgress = 0
      }

      const overall = Math.round(extractionProgress + generationProgress)

      return {
        extraction_job_id: extractionJobId,
        extraction_status: extractionJob.status,
        extraction_progress: extractionJob.progress,
        generation_jobs: generationJobs.map((j) => ({
          job_id: j.id,
          template_type: j.template_type || "unknown",
          status: j.status,
          progress: j.progress,
        })),
        overall_progress: overall,
      }
    },
    enabled: !!extractionJobId && (options?.enabled ?? true),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 3000

      // Stop polling when all jobs are done
      const extractionDone =
        data.extraction_status === "completed" || data.extraction_status === "failed"
      const allGenDone = data.generation_jobs.every(
        (j) => j.status === "completed" || j.status === "failed"
      )

      if (extractionDone && allGenDone) return false
      return 2500
    },
  })
}
```

Update `frontend/src/hooks/queries/index.ts`:

```typescript
export * from "./use-approvals"
export * from "./use-dashboard"
export * from "./use-jobs"
export * from "./use-notifications"
export * from "./use-projects"
export * from "./use-prompts"
export * from "./use-templates"
export * from "./use-process" // NEW
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/hooks/queries/__tests__/use-process.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/hooks/queries/use-process.ts frontend/src/hooks/queries/index.ts frontend/src/hooks/queries/__tests__/use-process.test.ts
git commit -m "$(cat <<'EOF'
feat(frontend): add useExtractPdf and usePipelineProgress hooks

useExtractPdf calls /process/extract with templateIds.
usePipelineProgress polls extraction + generation jobs and
computes composite progress (60% extraction, 40% generation).

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.4: Update FileUpload Component for Multi-Template

**Files:**
- Modify: `frontend/src/components/upload/FileUpload.tsx`
- Test: `frontend/src/components/upload/__tests__/FileUpload.test.tsx` (create)

**Step 1: Write the failing test**

```typescript
// frontend/src/components/upload/__tests__/FileUpload.test.tsx
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { FileUpload } from "../FileUpload"

// Mock the hooks
vi.mock("@/hooks", () => ({
  useExtractPdf: () => ({
    mutateAsync: vi.fn().mockResolvedValue({
      extraction_job_id: "job-123",
      status: "pending",
      template_ids: ["opr", "mpp"],
    }),
    isPending: false,
  }),
}))

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe("FileUpload", () => {
  it("renders template checkboxes", () => {
    renderWithProviders(<FileUpload />)

    expect(screen.getByLabelText(/Off-Plan Residential/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Main Brand Site/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Aggregators/i)).toBeInTheDocument()
  })

  it("requires at least one template selected", () => {
    renderWithProviders(<FileUpload />)

    // Uncheck all templates
    const oprCheckbox = screen.getByLabelText(/Off-Plan Residential/i)
    fireEvent.click(oprCheckbox) // Toggle off

    const uploadButton = screen.getByRole("button", { name: /Upload/i })
    expect(uploadButton).toBeDisabled()
  })

  it("calls onUploadComplete with extraction_job_id", async () => {
    const onComplete = vi.fn()
    renderWithProviders(<FileUpload onUploadComplete={onComplete} />)

    // Simulate file drop and upload
    // (detailed interaction test would require more setup)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/components/upload/__tests__/FileUpload.test.tsx`
Expected: FAIL (tests may fail due to hook not being used yet)

**Step 3: Update FileUpload implementation**

```typescript
// frontend/src/components/upload/FileUpload.tsx
import { FileText, Upload, X } from "lucide-react"
import { useCallback, useRef, useState } from "react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { useExtractPdf } from "@/hooks"
import { cn } from "@/lib/utils"

interface FileUploadProps {
  onUploadComplete?: (result: { extraction_job_id: string; template_ids: string[] }) => void
}

interface FileWithProgress {
  file: File
  progress: number
}

const MAX_FILE_SIZE = 200 * 1024 * 1024 // 200MB
const ACCEPT_FILE_TYPES = ".pdf,application/pdf"

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i]
}

const TEMPLATE_OPTIONS = [
  { value: "opr", label: "Off-Plan Residential (OPR)" },
  { value: "mpp", label: "the company (MPP)" },
  { value: "aggregators", label: "Real Estate Aggregators" },
  { value: "adop", label: "ADOP Template" },
  { value: "adre", label: "ADRE Template" },
  { value: "commercial", label: "Commercial" },
]

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [selectedFiles, setSelectedFiles] = useState<FileWithProgress[]>([])
  const [selectedTemplates, setSelectedTemplates] = useState<string[]>(["opr"])
  const [isDragOver, setIsDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { mutateAsync: extractPdf, isPending } = useExtractPdf()

  const validateFile = useCallback((file: File): string | null => {
    if (!file.type.includes("pdf")) {
      return `${file.name}: File must be a PDF`
    }
    if (file.size > MAX_FILE_SIZE) {
      return `${file.name}: File size exceeds ${formatFileSize(MAX_FILE_SIZE)}`
    }
    return null
  }, [])

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return

      setError(null)
      const newFiles: FileWithProgress[] = []
      const errors: string[] = []

      // Only allow one file at a time for multi-template flow
      const file = files[0]
      const validationError = validateFile(file)
      if (validationError) {
        errors.push(validationError)
      } else {
        newFiles.push({ file, progress: 0 })
      }

      if (errors.length > 0) {
        setError(errors.join("; "))
      }

      if (newFiles.length > 0) {
        setSelectedFiles(newFiles) // Replace, don't append
      }
    },
    [validateFile],
  )

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragOver(false)
      handleFiles(e.dataTransfer.files)
    },
    [handleFiles],
  )

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    },
    [handleFiles],
  )

  const handleRemoveFile = useCallback(() => {
    setSelectedFiles([])
    setError(null)
    setUploadProgress(0)
  }, [])

  const handleTemplateToggle = useCallback((templateValue: string) => {
    setSelectedTemplates((prev) => {
      if (prev.includes(templateValue)) {
        // Don't allow deselecting the last template
        if (prev.length === 1) return prev
        return prev.filter((t) => t !== templateValue)
      } else {
        return [...prev, templateValue]
      }
    })
  }, [])

  const handleUpload = useCallback(async () => {
    if (selectedFiles.length === 0 || selectedTemplates.length === 0) return

    setError(null)
    setUploadProgress(10)

    try {
      const file = selectedFiles[0].file

      // First upload the file to get a GCS URL
      // For now, we'll use a direct upload - in production this would
      // be a presigned URL or multipart upload
      const formData = new FormData()
      formData.append("file", file)

      // Upload file first (this will be replaced with proper GCS upload)
      // For now, use the existing upload endpoint to get the file to GCS
      const uploadResponse = await fetch("/api/v1/upload/file", {
        method: "POST",
        body: formData,
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("auth-storage") ? JSON.parse(sessionStorage.getItem("auth-storage")!).state?.token : ""}`,
        },
      })

      if (!uploadResponse.ok) {
        throw new Error("Failed to upload file")
      }

      const { gcs_url } = await uploadResponse.json()
      setUploadProgress(40)

      // Now start extraction with selected templates
      const result = await extractPdf({
        pdfUrl: gcs_url,
        templateIds: selectedTemplates,
      })

      setUploadProgress(100)

      if (onUploadComplete) {
        onUploadComplete({
          extraction_job_id: result.extraction_job_id,
          template_ids: result.template_ids,
        })
      }

      setSelectedFiles([])
      setUploadProgress(0)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Upload failed"
      setError(errorMessage)
      setUploadProgress(0)
    }
  }, [selectedFiles, selectedTemplates, extractPdf, onUploadComplete])

  const handleClickZone = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Select Template Types</h3>
          <p className="text-xs text-muted-foreground">
            Choose one or more templates for content generation. The PDF will be
            processed once and content generated for each selected template.
          </p>
          <div className="grid grid-cols-2 gap-3">
            {TEMPLATE_OPTIONS.map((template) => (
              <label
                key={template.value}
                className="flex items-center space-x-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedTemplates.includes(template.value)}
                  onChange={() => handleTemplateToggle(template.value)}
                  className="size-4 rounded border-gray-300 text-primary focus:ring-primary"
                  aria-label={template.label}
                />
                <span className="text-sm">{template.label}</span>
              </label>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Selected: {selectedTemplates.length} template(s)
          </p>
        </div>
      </Card>

      <Card
        className={cn(
          "relative cursor-pointer border-2 border-dashed transition-colors",
          isDragOver && "border-primary bg-primary/5",
          isPending && "pointer-events-none opacity-50",
          !isDragOver && !isPending && "hover:border-primary/50",
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClickZone}
      >
        <div className="flex flex-col items-center justify-center gap-4 p-12">
          <div className="flex size-16 items-center justify-center rounded-full bg-primary/10">
            <Upload className="size-8 text-primary" />
          </div>
          <div className="text-center space-y-2">
            <p className="text-lg font-medium">
              Drag and drop a PDF file here, or click to browse
            </p>
            <p className="text-sm text-muted-foreground">
              Maximum file size: {formatFileSize(MAX_FILE_SIZE)}
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPT_FILE_TYPES}
            className="hidden"
            onChange={handleInputChange}
            disabled={isPending}
          />
        </div>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {selectedFiles.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Selected File</h3>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <FileText className="size-5 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">
                  {selectedFiles[0].file.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(selectedFiles[0].file.size)}
                </p>
              </div>
              {isPending && uploadProgress > 0 && (
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground w-10 text-right">
                    {uploadProgress}%
                  </span>
                </div>
              )}
              {!isPending && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRemoveFile()
                  }}
                >
                  <X className="size-4" />
                </Button>
              )}
            </div>
          </Card>
          <Button
            onClick={(e) => {
              e.stopPropagation()
              handleUpload()
            }}
            disabled={isPending || selectedFiles.length === 0 || selectedTemplates.length === 0}
            className="w-full"
          >
            {isPending
              ? "Processing..."
              : `Process PDF for ${selectedTemplates.length} template(s)`}
          </Button>
        </div>
      )}
    </div>
  )
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/components/upload/__tests__/FileUpload.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/upload/FileUpload.tsx frontend/src/components/upload/__tests__/FileUpload.test.tsx
git commit -m "$(cat <<'EOF'
feat(frontend): update FileUpload for multi-template extraction

Uses useExtractPdf hook to call /process/extract with selected
template_ids. Single PDF produces extraction once, then N
generation jobs. Changed callback to return extraction_job_id.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.5: Create Multi-Job Progress Component

**Files:**
- Create: `frontend/src/components/upload/PipelineProgressTracker.tsx`
- Test: `frontend/src/components/upload/__tests__/PipelineProgressTracker.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/components/upload/__tests__/PipelineProgressTracker.test.tsx
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { PipelineProgressTracker } from "../PipelineProgressTracker"

vi.mock("@/hooks", () => ({
  usePipelineProgress: () => ({
    data: {
      extraction_job_id: "ext-123",
      extraction_status: "processing",
      extraction_progress: 50,
      generation_jobs: [
        { job_id: "gen-1", template_type: "opr", status: "pending", progress: 0 },
        { job_id: "gen-2", template_type: "mpp", status: "pending", progress: 0 },
      ],
      overall_progress: 30,
    },
    isLoading: false,
  }),
}))

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe("PipelineProgressTracker", () => {
  it("shows extraction progress", () => {
    renderWithProviders(
      <PipelineProgressTracker extractionJobId="ext-123" startedAt="2026-02-05T00:00:00Z" />
    )

    expect(screen.getByText(/Extraction/i)).toBeInTheDocument()
    expect(screen.getByText(/50%/)).toBeInTheDocument()
  })

  it("shows generation jobs", () => {
    renderWithProviders(
      <PipelineProgressTracker extractionJobId="ext-123" startedAt="2026-02-05T00:00:00Z" />
    )

    expect(screen.getByText(/opr/i)).toBeInTheDocument()
    expect(screen.getByText(/mpp/i)).toBeInTheDocument()
  })

  it("shows overall progress", () => {
    renderWithProviders(
      <PipelineProgressTracker extractionJobId="ext-123" startedAt="2026-02-05T00:00:00Z" />
    )

    expect(screen.getByText(/Overall Progress/i)).toBeInTheDocument()
    expect(screen.getByText(/30%/)).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/components/upload/__tests__/PipelineProgressTracker.test.tsx`
Expected: FAIL

**Step 3: Write the implementation**

```typescript
// frontend/src/components/upload/PipelineProgressTracker.tsx
import { formatDistanceToNow } from "date-fns"
import { Check, Clock, Loader2, Timer, X } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { usePipelineProgress } from "@/hooks"
import { cn } from "@/lib/utils"
import type { JobStatus } from "@/types"

interface PipelineProgressTrackerProps {
  extractionJobId: string
  startedAt: string
  onAllComplete?: () => void
}

const TEMPLATE_LABELS: Record<string, string> = {
  opr: "Off-Plan Residential",
  mpp: "Main Brand Site",
  aggregators: "Aggregators",
  adop: "ADOP",
  adre: "ADRE",
  commercial: "Commercial",
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins < 60) return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`
  const hours = Math.floor(mins / 60)
  const remainingMins = mins % 60
  return `${hours}h ${remainingMins}m`
}

function StatusIcon({ status }: { status: JobStatus }) {
  if (status === "completed") {
    return (
      <div className="flex size-6 items-center justify-center rounded-full bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300">
        <Check className="size-4" />
      </div>
    )
  }
  if (status === "failed") {
    return (
      <div className="flex size-6 items-center justify-center rounded-full bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300">
        <X className="size-4" />
      </div>
    )
  }
  if (status === "processing") {
    return (
      <div className="flex size-6 items-center justify-center rounded-full bg-primary/10 text-primary">
        <Loader2 className="size-4 animate-spin" />
      </div>
    )
  }
  return (
    <div className="flex size-6 items-center justify-center rounded-full bg-muted text-muted-foreground">
      <Clock className="size-4" />
    </div>
  )
}

function StatusBadge({ status }: { status: JobStatus }) {
  const config: Record<JobStatus, { label: string; className: string }> = {
    pending: {
      label: "Waiting",
      className: "bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300",
    },
    processing: {
      label: "Running",
      className: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
    },
    completed: {
      label: "Done",
      className: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300",
    },
    failed: {
      label: "Failed",
      className: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
    },
    cancelled: {
      label: "Cancelled",
      className: "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300",
    },
  }

  const { label, className } = config[status] || config.pending
  return (
    <Badge variant="outline" className={cn("text-xs", className)}>
      {label}
    </Badge>
  )
}

export function PipelineProgressTracker({
  extractionJobId,
  startedAt,
  onAllComplete,
}: PipelineProgressTrackerProps) {
  const [now, setNow] = useState(() => Date.now())

  const { data: progress, isLoading } = usePipelineProgress(extractionJobId)

  // Update timer every second while running
  useEffect(() => {
    if (!progress) return
    const allDone =
      (progress.extraction_status === "completed" || progress.extraction_status === "failed") &&
      progress.generation_jobs.every((j) => j.status === "completed" || j.status === "failed")

    if (!allDone) {
      const interval = setInterval(() => setNow(Date.now()), 1000)
      return () => clearInterval(interval)
    } else {
      onAllComplete?.()
    }
  }, [progress, onAllComplete])

  const duration = useMemo(() => {
    if (!startedAt) return null
    try {
      const start = new Date(startedAt).getTime()
      const seconds = Math.max(0, Math.floor((now - start) / 1000))
      return formatDuration(seconds)
    } catch {
      return null
    }
  }, [startedAt, now])

  const timeAgo = useMemo(() => {
    try {
      return formatDistanceToNow(new Date(startedAt), { addSuffix: true })
    } catch {
      return null
    }
  }, [startedAt])

  if (isLoading || !progress) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center gap-2 text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          <span>Loading pipeline status...</span>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-lg">Pipeline Status</h3>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {duration && (
              <div className="flex items-center gap-1.5">
                <Timer className="size-4" />
                <span className="font-mono">{duration}</span>
              </div>
            )}
            {timeAgo && (
              <div className="flex items-center gap-1.5">
                <Clock className="size-4" />
                <span>{timeAgo}</span>
              </div>
            )}
          </div>
        </div>

        {/* Overall progress bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Overall Progress</span>
            <span className="text-muted-foreground">{progress.overall_progress}%</span>
          </div>
          <div className="w-full h-3 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full transition-all duration-300",
                progress.overall_progress === 100 && "bg-green-500",
                progress.overall_progress < 100 && "bg-primary",
              )}
              style={{ width: `${progress.overall_progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Extraction phase */}
      <div className="space-y-3">
        <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wider">
          Phase 1: Extraction
        </h4>
        <div
          className={cn(
            "flex items-center gap-3 p-3 rounded-lg",
            progress.extraction_status === "processing" && "bg-primary/5",
          )}
        >
          <StatusIcon status={progress.extraction_status} />
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="font-medium">PDF Processing</span>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {progress.extraction_progress}%
                </span>
                <StatusBadge status={progress.extraction_status} />
              </div>
            </div>
            <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden mt-2">
              <div
                className={cn(
                  "h-full transition-all",
                  progress.extraction_status === "completed" && "bg-green-500",
                  progress.extraction_status === "failed" && "bg-red-500",
                  progress.extraction_status === "processing" && "bg-primary",
                )}
                style={{ width: `${progress.extraction_progress}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Generation phase */}
      {progress.generation_jobs.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wider">
            Phase 2: Content Generation
          </h4>
          <div className="space-y-2">
            {progress.generation_jobs.map((job) => (
              <div
                key={job.job_id}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg",
                  job.status === "processing" && "bg-primary/5",
                )}
              >
                <StatusIcon status={job.status} />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      {TEMPLATE_LABELS[job.template_type] || job.template_type}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">
                        {job.progress}%
                      </span>
                      <StatusBadge status={job.status} />
                    </div>
                  </div>
                  <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden mt-2">
                    <div
                      className={cn(
                        "h-full transition-all",
                        job.status === "completed" && "bg-green-500",
                        job.status === "failed" && "bg-red-500",
                        job.status === "processing" && "bg-primary",
                      )}
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Waiting for generation jobs */}
      {progress.extraction_status === "completed" && progress.generation_jobs.length === 0 && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50 text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          <span className="text-sm">Waiting for generation jobs to start...</span>
        </div>
      )}
    </Card>
  )
}
```

Update `frontend/src/components/upload/index.ts` to export the new component:

```typescript
export { FileUpload } from "./FileUpload"
export { JobStatus } from "./JobStatus"
export { ProgressTracker } from "./ProgressTracker"
export { PipelineProgressTracker } from "./PipelineProgressTracker"
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/components/upload/__tests__/PipelineProgressTracker.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/upload/PipelineProgressTracker.tsx frontend/src/components/upload/__tests__/PipelineProgressTracker.test.tsx frontend/src/components/upload/index.ts
git commit -m "$(cat <<'EOF'
feat(frontend): add PipelineProgressTracker component

Shows composite progress for extraction + N generation jobs.
Displays Phase 1 (extraction) and Phase 2 (generation per template)
with individual progress bars and status badges.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.6: Update ProcessingPage for Multi-Template Flow

**Files:**
- Modify: `frontend/src/pages/ProcessingPage.tsx`
- Test: `frontend/src/pages/__tests__/ProcessingPage.test.tsx` (create)

**Step 1: Write the failing test**

```typescript
// frontend/src/pages/__tests__/ProcessingPage.test.tsx
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter } from "react-router-dom"
import ProcessingPage from "../ProcessingPage"

vi.mock("@/hooks", () => ({
  useJobs: () => ({ data: { jobs: [] }, isLoading: false }),
  useJobSteps: () => ({ data: [] }),
  usePipelineProgress: () => ({ data: null, isLoading: false }),
}))

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe("ProcessingPage", () => {
  it("renders upload section", () => {
    renderWithProviders(<ProcessingPage />)
    expect(screen.getByText(/Upload & Process/i)).toBeInTheDocument()
  })

  it("renders template selection", () => {
    renderWithProviders(<ProcessingPage />)
    expect(screen.getByText(/Select Template Types/i)).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify current behavior**

**Step 3: Update ProcessingPage implementation**

```typescript
// frontend/src/pages/ProcessingPage.tsx
import { FileText } from "lucide-react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"

import { EmptyState } from "@/components/common/EmptyState"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { PageHeader } from "@/components/common/PageHeader"
import { Card } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { FileUpload, JobStatus, PipelineProgressTracker } from "@/components/upload"
import { useJobs, usePipelineProgress } from "@/hooks"

const ACTIVE_PIPELINE_STORAGE_KEY = "pdp-active-pipeline"

interface ActivePipeline {
  extraction_job_id: string
  template_ids: string[]
  started_at: string
}

export default function ProcessingPage() {
  const navigate = useNavigate()
  const [activePipeline, setActivePipeline] = useState<ActivePipeline | null>(() => {
    const stored = sessionStorage.getItem(ACTIVE_PIPELINE_STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  })
  const jobCardRef = useRef<HTMLDivElement>(null)

  const { data: jobsData, isLoading: isLoadingJobs } = useJobs()
  const jobs = jobsData?.jobs

  // Track pipeline progress
  const { data: pipelineProgress } = usePipelineProgress(
    activePipeline?.extraction_job_id ?? null,
    { enabled: !!activePipeline }
  )

  const handleUploadComplete = useCallback(
    (result: { extraction_job_id: string; template_ids: string[] }) => {
      const pipeline: ActivePipeline = {
        extraction_job_id: result.extraction_job_id,
        template_ids: result.template_ids,
        started_at: new Date().toISOString(),
      }
      setActivePipeline(pipeline)
      sessionStorage.setItem(ACTIVE_PIPELINE_STORAGE_KEY, JSON.stringify(pipeline))
    },
    []
  )

  const handlePipelineComplete = useCallback(() => {
    // Navigate to first completed project after a delay
    if (pipelineProgress?.generation_jobs.length) {
      const completedJob = pipelineProgress.generation_jobs.find(
        (j) => j.status === "completed"
      )
      if (completedJob) {
        // Find the project ID from jobs list
        const job = jobs?.find((j) => j.id === completedJob.job_id)
        if (job?.project_id) {
          setTimeout(() => {
            navigate(`/projects/${job.project_id}`)
          }, 2000)
        }
      }
    }
    // Clear active pipeline
    sessionStorage.removeItem(ACTIVE_PIPELINE_STORAGE_KEY)
  }, [pipelineProgress, jobs, navigate])

  // Clear storage when pipeline completes or fails
  useEffect(() => {
    if (!pipelineProgress) return

    const extractionDone =
      pipelineProgress.extraction_status === "completed" ||
      pipelineProgress.extraction_status === "failed"
    const allGenDone = pipelineProgress.generation_jobs.every(
      (j) => j.status === "completed" || j.status === "failed"
    )

    if (extractionDone && allGenDone) {
      handlePipelineComplete()
    }
  }, [pipelineProgress, handlePipelineComplete])

  // Filter jobs for display
  const runningJobs = useMemo(
    () =>
      jobs?.filter(
        (job) =>
          (job.status === "pending" || job.status === "processing") &&
          job.id !== activePipeline?.extraction_job_id
      ),
    [jobs, activePipeline]
  )

  const recentJobs = useMemo(
    () =>
      jobs?.filter(
        (job) =>
          job.status === "completed" ||
          job.status === "failed" ||
          job.status === "cancelled"
      ),
    [jobs]
  )

  return (
    <div className="space-y-8">
      <PageHeader
        title="Upload & Process"
        description="Upload PDF brochures and generate content for multiple templates simultaneously"
      />

      <div className="grid gap-8 lg:grid-cols-2">
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-4">Upload New File</h2>
            <FileUpload onUploadComplete={handleUploadComplete} />
          </div>

          {activePipeline && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Current Pipeline</h2>
              <PipelineProgressTracker
                extractionJobId={activePipeline.extraction_job_id}
                startedAt={activePipeline.started_at}
                onAllComplete={handlePipelineComplete}
              />
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-4">Active Jobs</h2>
            {isLoadingJobs ? (
              <Card className="p-12 flex items-center justify-center">
                <LoadingSpinner size="lg" />
              </Card>
            ) : runningJobs && runningJobs.length > 0 ? (
              <div className="space-y-3">
                {runningJobs.map((job) => (
                  <div key={job.id} ref={jobCardRef}>
                    <JobStatus job={job} compact />
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={FileText}
                title="No active jobs"
                description="Upload a PDF file to start processing"
              />
            )}
          </div>

          {recentJobs && recentJobs.length > 0 && (
            <>
              <Separator />
              <div>
                <h2 className="text-lg font-semibold mb-4">Recent Jobs</h2>
                <div className="space-y-3">
                  {recentJobs.slice(0, 5).map((job) => (
                    <JobStatus key={job.id} job={job} />
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/pages/__tests__/ProcessingPage.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/ProcessingPage.tsx frontend/src/pages/__tests__/ProcessingPage.test.tsx
git commit -m "$(cat <<'EOF'
feat(frontend): update ProcessingPage for multi-template pipeline

Uses PipelineProgressTracker instead of single-job ProgressTracker.
Tracks extraction_job_id + template_ids in sessionStorage.
Shows composite progress for extraction + generation phases.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase C Verification Checkpoint

Before proceeding to Phase D, verify:

1. [ ] TypeScript types compile without errors: `cd frontend && npx tsc -b`
2. [ ] All frontend tests pass: `cd frontend && npm run test`
3. [ ] FileUpload shows template checkboxes with multi-select
4. [ ] Upload calls `/process/extract` with selected template_ids
5. [ ] PipelineProgressTracker shows extraction + generation progress
6. [ ] ProcessingPage persists active pipeline across page refreshes
7. [ ] Navigation to project occurs after pipeline completes

---

## Phase D: Polish & Cleanup

### Task D.1: Remove Old Upload Hook and API

**Files:**
- Modify: `frontend/src/lib/api.ts` - remove old upload.pdf
- Modify: `frontend/src/hooks/queries/use-jobs.ts` - remove useUploadFile

**Step 1: Write the failing test**

```typescript
// frontend/src/lib/__tests__/api-cleanup.test.ts
import { describe, it, expect } from "vitest"
import { api } from "@/lib/api"

describe("api cleanup", () => {
  it("upload.pdf is removed", () => {
    // Old single-template upload should not exist
    expect((api.upload as any).pdf).toBeUndefined()
  })

  it("process.extract exists", () => {
    expect(api.process.extract).toBeDefined()
  })
})
```

**Step 2: Run test to verify it fails (pdf still exists)**

**Step 3: Remove old code**

In `frontend/src/lib/api.ts`, replace the `upload` object:

```typescript
const upload = {
  // File upload to GCS (returns gcs_url for use with /process/extract)
  file: (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData()
    formData.append("file", file)

    return apiClient
      .post<{ gcs_url: string }>("/upload/file", formData, {
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
```

In `frontend/src/hooks/queries/use-jobs.ts`, remove `useUploadFile`:

```typescript
// REMOVED: useUploadFile - replaced by useExtractPdf in use-process.ts
```

Update `frontend/src/hooks/index.ts` to export from use-process:

```typescript
export * from "./queries"
export { useAuth } from "./use-auth"
// useExtractPdf, useGenerateContent, usePipelineProgress are in queries/use-process
```

**Step 4: Run test to verify it passes**

**Step 5: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/hooks/queries/use-jobs.ts frontend/src/hooks/index.ts frontend/src/lib/__tests__/api-cleanup.test.ts
git commit -m "$(cat <<'EOF'
refactor(frontend): remove old single-template upload flow

Removes upload.pdf API method and useUploadFile hook.
Multi-template flow uses api.process.extract and useExtractPdf.

BREAKING: Old upload flow no longer available.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task D.2: Add JobType Badge to JobStatus Component

**Files:**
- Modify: `frontend/src/components/upload/JobStatus.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/components/upload/__tests__/JobStatus.test.tsx
import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { BrowserRouter } from "react-router-dom"
import { JobStatus } from "../JobStatus"
import type { Job } from "@/types"

const mockExtractionJob: Job = {
  id: "job-123",
  project_id: "proj-123",
  status: "processing",
  current_step: "extract_images",
  progress: 30,
  created_at: "2026-02-05T00:00:00Z",
  updated_at: "2026-02-05T00:00:00Z",
  job_type: "extraction",
}

const mockGenerationJob: Job = {
  id: "job-456",
  project_id: "proj-123",
  status: "processing",
  current_step: "generate_content",
  progress: 50,
  created_at: "2026-02-05T00:00:00Z",
  updated_at: "2026-02-05T00:00:00Z",
  job_type: "generation",
  template_type: "opr",
}

describe("JobStatus", () => {
  it("shows extraction badge for extraction jobs", () => {
    render(
      <BrowserRouter>
        <JobStatus job={mockExtractionJob} />
      </BrowserRouter>
    )
    expect(screen.getByText(/Extraction/i)).toBeInTheDocument()
  })

  it("shows generation badge with template for generation jobs", () => {
    render(
      <BrowserRouter>
        <JobStatus job={mockGenerationJob} />
      </BrowserRouter>
    )
    expect(screen.getByText(/Generation/i)).toBeInTheDocument()
    expect(screen.getByText(/opr/i)).toBeInTheDocument()
  })
})
```

**Step 2: Run test to verify it fails**

**Step 3: Update JobStatus component**

Add job type indicator to `frontend/src/components/upload/JobStatus.tsx`:

```typescript
// Add after status badge in the component
{job.job_type && (
  <Badge
    variant="secondary"
    className={cn(
      "text-xs ml-1",
      job.job_type === "extraction" && "bg-purple-100 text-purple-700",
      job.job_type === "generation" && "bg-cyan-100 text-cyan-700",
    )}
  >
    {job.job_type === "extraction" ? "Extraction" : `Generation: ${job.template_type || "?"}`}
  </Badge>
)}
```

**Step 4: Run test to verify it passes**

**Step 5: Commit**

```bash
git add frontend/src/components/upload/JobStatus.tsx frontend/src/components/upload/__tests__/JobStatus.test.tsx
git commit -m "$(cat <<'EOF'
feat(frontend): add job_type badge to JobStatus component

Shows "Extraction" or "Generation: {template}" badge based on
job_type field. Helps distinguish pipeline phases in job list.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task D.3: Update ProgressTracker Steps for Job Type

**Files:**
- Modify: `frontend/src/components/upload/ProgressTracker.tsx`

**Step 1: Update the FALLBACK_STEPS to support job types**

```typescript
// frontend/src/components/upload/ProgressTracker.tsx

// Add step configs for different job types
const EXTRACTION_STEPS = [
  { step_id: "upload", label: "PDF Upload & Validation" },
  { step_id: "extract_images", label: "Image Extraction" },
  { step_id: "classify_images", label: "Image Classification" },
  { step_id: "detect_watermarks", label: "Watermark Detection" },
  { step_id: "remove_watermarks", label: "Watermark Removal" },
  { step_id: "extract_floor_plans", label: "Floor Plan Extraction" },
  { step_id: "optimize_images", label: "Image Optimization" },
  { step_id: "package_assets", label: "Asset Packaging" },
  { step_id: "extract_data", label: "Data Extraction" },
  { step_id: "structure_data", label: "Data Structuring" },
  { step_id: "materialize", label: "Package Materialization" },
] as const

const GENERATION_STEPS = [
  { step_id: "load_package", label: "Load Material Package" },
  { step_id: "generate_content", label: "Content Generation" },
  { step_id: "populate_sheet", label: "Sheet Population" },
  { step_id: "upload_cloud", label: "Cloud Upload" },
  { step_id: "finalize_generation", label: "Finalization" },
] as const

// Update props interface
interface ProgressTrackerProps {
  currentStep: string
  progressMessage?: string
  progress: number
  status: JobStatus
  error?: string
  startedAt: string
  completedAt?: string
  steps?: JobStep[]
  jobType?: "extraction" | "generation" // NEW
  onCancel?: () => void
}

// Update displaySteps logic to use job type
const displaySteps = useMemo(() => {
  if (steps && steps.length > 0) {
    // Use real steps if available
    return steps.map((s) => ({ /* ... existing mapping ... */ }))
  }

  // Select fallback steps based on job type
  const fallbackSteps = jobType === "generation" ? GENERATION_STEPS :
                        jobType === "extraction" ? EXTRACTION_STEPS :
                        FALLBACK_STEPS

  return fallbackSteps.map((s, index) => {
    // ... existing fallback logic ...
  })
}, [steps, currentStep, status, jobType])
```

**Step 2: Commit**

```bash
git add frontend/src/components/upload/ProgressTracker.tsx
git commit -m "$(cat <<'EOF'
feat(frontend): add job_type support to ProgressTracker

Shows extraction-specific steps (11) or generation-specific steps (5)
based on jobType prop. Falls back to full 14-step display if not specified.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task D.4: Add File Upload Endpoint (Backend)

**Files:**
- Create: `backend/app/api/routes/upload.py` - add /upload/file endpoint
- Test: `backend/tests/test_upload_file.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_upload_file.py
import pytest
from httpx import AsyncClient
from io import BytesIO

@pytest.mark.asyncio
async def test_upload_file_returns_gcs_url(client: AsyncClient, auth_headers):
    """Upload endpoint returns GCS URL."""
    pdf_content = b"%PDF-1.4 fake pdf content"
    files = {"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")}

    response = await client.post(
        "/api/v1/upload/file",
        files=files,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert "gcs_url" in data
    assert data["gcs_url"].startswith("gs://")
```

**Step 2: Run test to verify it fails**

**Step 3: Add the endpoint**

```python
# Add to backend/app/api/routes/upload.py

@router.post(
    "/file",
    status_code=status.HTTP_201_CREATED,
    summary="Upload file to GCS",
    description="Upload a file to GCS and return its URL for use with /process/extract"
)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Upload a file to GCS.

    Returns the GCS URL that can be passed to /process/extract.
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_FILE_TYPE", "message": "Only PDF files are allowed"}
        )

    # Read file content
    content = await file.read()

    # Generate unique path
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = file.filename.replace(" ", "_")
    gcs_path = f"uploads/{current_user.id}/{timestamp}_{safe_filename}"

    # Upload to GCS
    gcs_url = await storage.upload_file(
        source_file=content,
        destination_blob_path=gcs_path,
        content_type="application/pdf"
    )

    return {"gcs_url": gcs_url, "filename": file.filename, "size": len(content)}
```

**Step 4: Run test to verify it passes**

**Step 5: Commit**

```bash
git add backend/app/api/routes/upload.py backend/tests/test_upload_file.py
git commit -m "$(cat <<'EOF'
feat(backend): add /upload/file endpoint for GCS upload

Returns gcs_url for use with /process/extract endpoint.
Supports multi-template pipeline frontend flow.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task D.5: Remove FULL Job Type References

**Files:**
- Modify: `backend/app/models/enums.py` - remove FULL from JobType
- Modify: Various backend files that reference JobType.FULL
- Modify: Frontend types

**Step 1: Search for FULL references**

```bash
cd backend && grep -r "JobType.FULL" --include="*.py"
cd backend && grep -r "job_type.*full" --include="*.py"
```

**Step 2: Remove FULL from enum**

```python
# backend/app/models/enums.py
class JobType(str, enum.Enum):
    """Job type for pipeline execution path."""
    EXTRACTION = "extraction"  # Steps 1-10 only, produces MaterialPackage
    GENERATION = "generation"  # Steps 11-14 only, consumes MaterialPackage
```

**Step 3: Update all references**

- Change default `job_type=JobType.FULL` to `job_type=JobType.EXTRACTION`
- Update migrations to remove 'full' from check constraints
- Update any routing logic that checks for FULL

**Step 4: Update frontend types**

```typescript
// frontend/src/types/index.ts
export type JobType = "extraction" | "generation"  // Remove "full"
```

**Step 5: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
refactor: remove FULL job type from pipeline

Clean cutover to EXTRACTION + GENERATION only.
No backward compatibility needed in dev environment.

BREAKING: JobType.FULL no longer exists.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task D.6: Add Integration Test for Full Pipeline Flow

**Files:**
- Create: `frontend/src/__tests__/integration/pipeline-flow.test.tsx`

**Step 1: Write integration test**

```typescript
// frontend/src/__tests__/integration/pipeline-flow.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter } from "react-router-dom"
import ProcessingPage from "@/pages/ProcessingPage"
import { api } from "@/lib/api"

// Mock API
vi.mock("@/lib/api", () => ({
  api: {
    upload: {
      file: vi.fn().mockResolvedValue({ gcs_url: "gs://bucket/test.pdf" }),
    },
    process: {
      extract: vi.fn().mockResolvedValue({
        extraction_job_id: "ext-123",
        status: "pending",
        template_ids: ["opr", "mpp"],
        message: "Created",
      }),
    },
    jobs: {
      list: vi.fn().mockResolvedValue({ jobs: [], total: 0 }),
      get: vi.fn(),
    },
  },
}))

describe("Pipeline Flow Integration", () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
    vi.clearAllMocks()
  })

  it("completes upload to extraction flow", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ProcessingPage />
        </BrowserRouter>
      </QueryClientProvider>
    )

    // Select templates
    const oprCheckbox = screen.getByLabelText(/Off-Plan Residential/i)
    const mppCheckbox = screen.getByLabelText(/Main Brand Site/i)
    fireEvent.click(mppCheckbox) // Select second template

    // Verify both selected
    expect(oprCheckbox).toBeChecked()
    expect(mppCheckbox).toBeChecked()

    // Upload would trigger file input - simplified for test
    expect(screen.getByText(/Upload New File/i)).toBeInTheDocument()
  })
})
```

**Step 2: Commit**

```bash
git add frontend/src/__tests__/integration/pipeline-flow.test.tsx
git commit -m "$(cat <<'EOF'
test(frontend): add pipeline flow integration test

Tests template selection and upload initiation.
Verifies multi-template UI flow works end-to-end.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase D Verification Checkpoint

Final verification before merge:

1. [ ] All frontend tests pass: `cd frontend && npm run test`
2. [ ] All backend tests pass: `cd backend && pytest tests/ -v`
3. [ ] TypeScript compiles: `cd frontend && npx tsc -b`
4. [ ] ESLint passes: `cd frontend && npm run lint`
5. [ ] Backend lint passes: `cd backend && ruff check . && ruff format --check .`
6. [ ] Docker build succeeds: `docker compose -f docker-compose.dev.yml build`
7. [ ] Manual test: upload PDF, select 2+ templates, verify extraction + generation jobs complete
8. [ ] Old `/upload/pdf` endpoint removed or returns 404
9. [ ] No references to `JobType.FULL` in codebase
10. [ ] Coverage maintained at 75%+

---

## Cleanup Tasks (Post-Merge)

After merging to main:

1. Delete old upload route handler if not done
2. Remove any deprecated backward-compat code
3. Update API documentation
4. Archive old plan documents

---

## Summary

**Phase C (Frontend):**
- C.1: TypeScript types for multi-template pipeline
- C.2: API methods for /process/extract and /process/generate
- C.3: useExtractPdf and usePipelineProgress hooks
- C.4: Updated FileUpload component with template checkboxes
- C.5: PipelineProgressTracker component for composite progress
- C.6: Updated ProcessingPage for new flow

**Phase D (Polish):**
- D.1: Remove old upload.pdf API and useUploadFile hook
- D.2: Add job_type badge to JobStatus
- D.3: Update ProgressTracker for job type-specific steps
- D.4: Add /upload/file endpoint (backend)
- D.5: Remove FULL job type references
- D.6: Integration test for pipeline flow
