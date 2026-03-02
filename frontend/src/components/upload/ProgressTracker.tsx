import { formatDistanceToNow } from "date-fns"
import { Check, Clock, Loader2, Timer, X } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { JobStatus, JobStep, JobType } from "@/types"

interface ProgressTrackerProps {
  currentStep: string
  progressMessage?: string  // Granular substep detail (e.g., "Generating: project_name")
  progress: number
  status: JobStatus
  error?: string
  startedAt: string
  completedAt?: string
  steps?: JobStep[]
  jobType?: JobType  // For job-type-specific step display
  onCancel?: () => void
}

// Extraction-only steps (Phase 1 of multi-template pipeline)
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

// Generation-only steps (Phase 2 of multi-template pipeline)
const GENERATION_STEPS = [
  { step_id: "load_package", label: "Load Material Package" },
  { step_id: "generate_content", label: "Content Generation" },
  { step_id: "populate_sheet", label: "Sheet Population" },
  { step_id: "upload_cloud", label: "Cloud Upload" },
  { step_id: "finalize_generation", label: "Finalization" },
] as const

// Legacy full pipeline steps (for backward compatibility)
const FALLBACK_STEPS = [
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
  { step_id: "generate_content", label: "Content Generation" },
  { step_id: "populate_sheet", label: "Sheet Population" },
  { step_id: "upload_cloud", label: "Cloud Upload" },
  { step_id: "finalize", label: "Finalization" },
] as const

function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`
  }
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins < 60) {
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`
  }
  const hours = Math.floor(mins / 60)
  const remainingMins = mins % 60
  return `${hours}h ${remainingMins}m`
}

export function ProgressTracker({
  currentStep,
  progressMessage,
  progress,
  status,
  error,
  startedAt,
  completedAt,
  steps,
  jobType,
  onCancel,
}: ProgressTrackerProps) {
  // For live duration updates
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    // Update every second while job is running
    if (status === "pending" || status === "processing") {
      const interval = setInterval(() => setNow(Date.now()), 1000)
      return () => clearInterval(interval)
    }
  }, [status])

  // Use real steps if available, otherwise use fallback based on job type
  const displaySteps = useMemo(() => {
    if (steps && steps.length > 0) {
      return steps.map((s) => ({
        step_id: s.step_id,
        label: s.label,
        status: s.status,
        result: s.result,
        error_message: s.error_message,
        started_at: s.started_at,
        completed_at: s.completed_at,
      }))
    }

    // Select fallback steps based on job type
    const fallbackSteps = jobType === "generation" ? GENERATION_STEPS :
                          jobType === "extraction" ? EXTRACTION_STEPS :
                          FALLBACK_STEPS

    // Fallback: infer status from currentStep
    return fallbackSteps.map((s, index) => {
      const currentIndex = fallbackSteps.findIndex((f) => f.step_id === currentStep)
      let inferredStatus: JobStep["status"] = "pending"
      if (status === "completed") {
        inferredStatus = "completed"
      } else if (status === "failed") {
        if (index < currentIndex) inferredStatus = "completed"
        else if (index === currentIndex) inferredStatus = "failed"
      } else {
        if (index < currentIndex) inferredStatus = "completed"
        else if (index === currentIndex) inferredStatus = "in_progress"
      }
      return {
        step_id: s.step_id,
        label: s.label,
        status: inferredStatus,
        result: undefined,
        error_message: undefined,
        started_at: undefined,
        completed_at: undefined,
      }
    })
  }, [steps, currentStep, status, jobType])

  // Calculate duration
  const duration = useMemo(() => {
    if (!startedAt) return null
    try {
      const start = new Date(startedAt).getTime()
      const end = completedAt ? new Date(completedAt).getTime() : now
      const seconds = Math.max(0, Math.floor((end - start) / 1000))
      return formatDuration(seconds)
    } catch {
      return null
    }
  }, [startedAt, completedAt, now])

  // Human-readable time since start
  const timeAgo = useMemo(() => {
    try {
      return formatDistanceToNow(new Date(startedAt), { addSuffix: true })
    } catch {
      return null
    }
  }, [startedAt])

  const canCancel = status === "pending" || status === "processing"

  // Find the currently active step for showing detail
  const activeStepIndex = displaySteps.findIndex((s) => s.status === "in_progress")

  return (
    <Card className="p-6 space-y-6">
      {/* Header with progress and timing */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-lg">Processing Status</h3>
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

        <div className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Overall Progress</span>
            <span className="text-muted-foreground">{progress}%</span>
          </div>
          <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full transition-all duration-300",
                status === "completed" && "bg-green-500",
                status === "failed" && "bg-red-500",
                status === "cancelled" && "bg-orange-500",
                (status === "pending" || status === "processing") && "bg-primary",
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Step list */}
      <div className="space-y-2">
        {displaySteps.map((step, index) => {
          const isActive = step.status === "in_progress"
          const isCompleted = step.status === "completed"
          const isFailed = step.status === "failed"
          const isSkipped = step.status === "skipped"

          return (
            <div
              key={step.step_id}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg transition-colors",
                isActive && "bg-primary/5",
              )}
            >
              {/* Status icon */}
              <div
                className={cn(
                  "flex size-6 items-center justify-center rounded-full flex-shrink-0 mt-0.5",
                  isCompleted && "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300",
                  isFailed && "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
                  isActive && "bg-primary/10 text-primary",
                  isSkipped && "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400",
                  step.status === "pending" && "bg-muted text-muted-foreground",
                )}
              >
                {isCompleted && <Check className="size-4" />}
                {isFailed && <X className="size-4" />}
                {isActive && <Loader2 className="size-4 animate-spin" />}
                {isSkipped && <span className="text-xs">-</span>}
                {step.status === "pending" && (
                  <span className="text-xs font-medium">{index + 1}</span>
                )}
              </div>

              {/* Step info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p
                    className={cn(
                      "text-sm font-medium",
                      isActive && "text-foreground",
                      isCompleted && "text-muted-foreground",
                      isFailed && "text-red-700 dark:text-red-300",
                      isSkipped && "text-gray-500 dark:text-gray-400 line-through",
                      step.status === "pending" && "text-muted-foreground",
                    )}
                  >
                    {step.label}
                  </p>
                  {/* Show step timing or result */}
                  <span className="text-xs text-muted-foreground">
                    {isCompleted && step.started_at && step.completed_at && (
                      formatStepDuration(step.started_at, step.completed_at)
                    )}
                    {isCompleted && step.result && Object.keys(step.result).length > 0 && !step.started_at && (
                      formatStepResult(step.result)
                    )}
                  </span>
                </div>

                {/* Granular progress message for active step */}
                {isActive && progressMessage && (
                  <p className="text-xs text-primary mt-1 animate-pulse">
                    {progressMessage}
                  </p>
                )}

                {/* Error message for failed step */}
                {isFailed && (step.error_message || (index === activeStepIndex && error)) && (
                  <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                    {step.error_message || error}
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Cancel button */}
      {canCancel && onCancel && (
        <div className="pt-4 border-t">
          <Button variant="destructive" size="sm" onClick={onCancel} className="w-full">
            Cancel Processing
          </Button>
        </div>
      )}
    </Card>
  )
}

// Format step result data into a readable summary
function formatStepResult(result: Record<string, unknown>): string {
  const parts: string[] = []

  // Common result fields
  if (typeof result.total === "number") {
    parts.push(`${result.total} items`)
  }
  if (typeof result.extracted === "number") {
    parts.push(`${result.extracted} extracted`)
  }
  if (typeof result.classified === "number") {
    parts.push(`${result.classified} classified`)
  }
  if (typeof result.removed === "number" && result.removed > 0) {
    parts.push(`${result.removed} removed`)
  }
  if (typeof result.fields_generated === "number") {
    parts.push(`${result.fields_generated} fields`)
  }
  if (typeof result.images === "number") {
    parts.push(`${result.images} images`)
  }

  return parts.length > 0 ? parts.join(", ") : ""
}

// Format step duration from timestamps
function formatStepDuration(startedAt: string, completedAt: string): string {
  try {
    const start = new Date(startedAt).getTime()
    const end = new Date(completedAt).getTime()
    const seconds = Math.max(0, Math.floor((end - start) / 1000))
    if (seconds < 60) {
      return `${seconds}s`
    }
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`
  } catch {
    return ""
  }
}
