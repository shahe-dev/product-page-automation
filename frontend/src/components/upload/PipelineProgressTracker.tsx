import { formatDistanceToNow } from "date-fns"
import { Check, ChevronDown, ChevronRight, Circle, Clock, Loader2, Minus, Timer, X } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { usePipelineProgress } from "@/hooks"
import { cn } from "@/lib/utils"
import type { JobStatus, JobStep, JobStepStatus } from "@/types"

interface PipelineProgressTrackerProps {
  extractionJobId?: string
  startedAt?: string
  onAllComplete?: () => void
  preparing?: boolean
  preparingFilename?: string
}

const TEMPLATE_LABELS: Record<string, string> = {
  opr: "Off-Plan Residential",
  mpp: "Main Brand",
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

function formatStepDuration(step: JobStep): string | null {
  if (!step.started_at) return null
  const start = new Date(step.started_at).getTime()
  if (step.completed_at) {
    const end = new Date(step.completed_at).getTime()
    const secs = Math.max(0, Math.round((end - start) / 1000))
    return formatDuration(secs)
  }
  // Still running - show elapsed
  const secs = Math.max(0, Math.round((Date.now() - start) / 1000))
  return `${formatDuration(secs)}...`
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

function StepStatusIcon({ status }: { status: JobStepStatus }) {
  if (status === "completed") {
    return <Check className="size-3.5 text-green-600 dark:text-green-400" />
  }
  if (status === "failed") {
    return <X className="size-3.5 text-red-600 dark:text-red-400" />
  }
  if (status === "in_progress") {
    return <Loader2 className="size-3.5 text-primary animate-spin" />
  }
  if (status === "skipped") {
    return <Minus className="size-3.5 text-muted-foreground" />
  }
  return <Circle className="size-2.5 text-muted-foreground/40" />
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

function ExtractionStepList({ steps }: { steps: JobStep[] }) {
  const [expanded, setExpanded] = useState(true)

  const completedCount = steps.filter((s) => s.status === "completed").length
  const failedStep = steps.find((s) => s.status === "failed")

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors mb-2"
      >
        {expanded ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
        <span className="font-medium">
          Steps ({completedCount}/{steps.length})
        </span>
      </button>

      {expanded && (
        <div className="space-y-0.5 pl-1">
          {steps.map((step) => (
            <div
              key={step.id}
              className={cn(
                "flex items-center gap-2 py-1 px-2 rounded text-xs",
                step.status === "in_progress" && "bg-primary/5",
                step.status === "failed" && "bg-red-50 dark:bg-red-950/30",
              )}
            >
              <div className="flex size-5 items-center justify-center shrink-0">
                <StepStatusIcon status={step.status} />
              </div>
              <span
                className={cn(
                  "flex-1 truncate",
                  step.status === "pending" && "text-muted-foreground/60",
                  step.status === "in_progress" && "text-foreground font-medium",
                  step.status === "completed" && "text-muted-foreground",
                  step.status === "failed" && "text-red-700 dark:text-red-400 font-medium",
                  step.status === "skipped" && "text-muted-foreground/50 line-through",
                )}
              >
                {step.label}
              </span>
              {step.status === "failed" && step.error_message && (
                <span className="text-red-600 dark:text-red-400 truncate max-w-[200px]" title={step.error_message}>
                  {step.error_message}
                </span>
              )}
              {(step.status === "completed" || step.status === "in_progress") && (
                <span className="text-muted-foreground font-mono shrink-0">
                  {formatStepDuration(step)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {failedStep && !expanded && (
        <div className="text-xs text-red-600 dark:text-red-400 pl-6 mt-1">
          Failed at: {failedStep.label}
          {failedStep.error_message && ` - ${failedStep.error_message}`}
        </div>
      )}
    </div>
  )
}

export function PipelineProgressTracker({
  extractionJobId,
  startedAt,
  onAllComplete,
  preparing,
  preparingFilename,
}: PipelineProgressTrackerProps) {
  const [now, setNow] = useState(() => Date.now())

  const { data: progress, isLoading } = usePipelineProgress(
    extractionJobId ?? null,
    { enabled: !preparing && !!extractionJobId }
  )

  // Update timer every second while running
  useEffect(() => {
    if (!progress) return
    const extractionDone = progress.extraction_status === "completed" || progress.extraction_status === "failed"
    const extractionFailed = progress.extraction_status === "failed"
    const hasGenJobs = progress.generation_jobs.length > 0
    const allGenDone = hasGenJobs &&
      progress.generation_jobs.every((j) => j.status === "completed" || j.status === "failed")
    // Pipeline is done if extraction failed (no gen jobs will come) or all phases finished
    const allDone = extractionFailed || (extractionDone && allGenDone)

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
    if (!startedAt) return null
    try {
      return formatDistanceToNow(new Date(startedAt), { addSuffix: true })
    } catch {
      return null
    }
  }, [startedAt])

  if (preparing || (isLoading && !progress)) {
    return (
      <Card className="p-6 space-y-6">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg">Pipeline Status</h3>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Overall Progress</span>
              <span className="text-muted-foreground">0%</span>
            </div>
            <div className="w-full h-3 bg-muted rounded-full overflow-hidden">
              <div className="h-full w-full bg-primary/30 animate-pulse rounded-full" />
            </div>
          </div>
        </div>
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wider">
            Preparing Pipeline
          </h4>
          <div className="flex items-center gap-3 p-3 rounded-lg bg-primary/5">
            <div className="flex size-6 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Loader2 className="size-4 animate-spin" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="font-medium">
                  {preparing ? "Uploading PDF & creating job..." : "Connecting to pipeline..."}
                </span>
                <Badge variant="outline" className="text-xs bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                  Running
                </Badge>
              </div>
              {preparingFilename && (
                <p className="text-xs text-muted-foreground mt-1">{preparingFilename}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-lg opacity-40">
            <div className="flex size-6 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <Clock className="size-4" />
            </div>
            <div className="flex-1">
              <span className="font-medium">Phase 1: Extraction</span>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-lg opacity-40">
            <div className="flex size-6 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <Clock className="size-4" />
            </div>
            <div className="flex-1">
              <span className="font-medium">Phase 2: Content Generation</span>
            </div>
          </div>
        </div>
      </Card>
    )
  }

  if (!progress) return null

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
            "rounded-lg p-3",
            progress.extraction_status === "processing" && "bg-primary/5",
          )}
        >
          <div className="flex items-center gap-3">
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
              {progress.extraction_progress_message && progress.extraction_status === "processing" && (
                <p className="text-xs text-muted-foreground mt-1.5">
                  {progress.extraction_progress_message}
                </p>
              )}
            </div>
          </div>

          {/* Step-by-step breakdown */}
          {progress.extraction_steps.length > 0 && (
            <ExtractionStepList steps={progress.extraction_steps} />
          )}
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
                  {job.progress_message && job.status === "processing" && (
                    <p className="text-xs text-muted-foreground mt-1.5">
                      {job.progress_message}
                    </p>
                  )}
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
