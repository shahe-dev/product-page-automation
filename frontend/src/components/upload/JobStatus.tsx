import { formatDistanceToNow } from "date-fns"
import { Clock,Eye, RefreshCw } from "lucide-react"
import { useMemo } from "react"
import { Link } from "react-router-dom"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { Job, JobStatus as JobStatusType } from "@/types"

interface JobStatusProps {
  job: Job
  compact?: boolean
  onRetry?: (jobId: string) => void
}

const JOB_STATUS_CONFIG: Record<
  JobStatusType,
  { label: string; className: string }
> = {
  pending: {
    label: "Pending",
    className: "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-900 dark:text-gray-300 dark:border-gray-800",
  },
  processing: {
    label: "Processing",
    className: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-900",
  },
  completed: {
    label: "Completed",
    className: "bg-green-100 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-900",
  },
  failed: {
    label: "Failed",
    className: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-900",
  },
  cancelled: {
    label: "Cancelled",
    className: "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950 dark:text-orange-300 dark:border-orange-900",
  },
}

export function JobStatus({ job, compact = false, onRetry }: JobStatusProps) {
  const statusConfig = JOB_STATUS_CONFIG[job.status]

  const timeAgo = useMemo(() => {
    try {
      return formatDistanceToNow(new Date(job.created_at), { addSuffix: true })
    } catch {
      return "N/A"
    }
  }, [job.created_at])

  const truncatedJobId = useMemo(() => {
    return job.id.length > 8 ? `${job.id.slice(0, 8)}...` : job.id
  }, [job.id])

  if (compact) {
    return (
      <Card className="p-4">
        <div className="flex items-center gap-3">
          <div className="flex-1 min-w-0 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground">
                {truncatedJobId}
              </span>
              <Badge variant="outline" className={cn(statusConfig.className, "text-xs")}>
                {statusConfig.label}
              </Badge>
              {job.job_type && (
                <Badge
                  variant="secondary"
                  className={cn(
                    "text-xs",
                    job.job_type === "extraction" && "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
                    job.job_type === "generation" && "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300",
                  )}
                >
                  {job.job_type === "extraction" ? "Extraction" : `Generation: ${job.template_type || "?"}`}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{job.current_step}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{job.progress}%</span>
            {job.project_id && (
              <Link to={`/projects/${job.project_id}`}>
                <Button variant="ghost" size="sm">
                  <Eye className="size-4" />
                </Button>
              </Link>
            )}
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1 flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-sm font-mono">{truncatedJobId}</h3>
            <Badge variant="outline" className={statusConfig.className}>
              {statusConfig.label}
            </Badge>
            {job.job_type && (
              <Badge
                variant="secondary"
                className={cn(
                  "text-xs",
                  job.job_type === "extraction" && "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
                  job.job_type === "generation" && "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300",
                )}
              >
                {job.job_type === "extraction" ? "Extraction" : `Generation: ${job.template_type || "?"}`}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="size-3" />
            <span>{timeAgo}</span>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Current Step</span>
          <span className="font-medium">{job.current_step || "Initializing..."}</span>
        </div>
        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full transition-all",
              job.status === "completed" && "bg-green-500",
              job.status === "failed" && "bg-red-500",
              (job.status === "pending" || job.status === "processing") && "bg-primary",
              job.status === "cancelled" && "bg-orange-500",
            )}
            style={{ width: `${job.progress}%` }}
          />
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Progress</span>
          <span className="font-medium">{job.progress}%</span>
        </div>
      </div>

      {job.error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-md">
          <p className="text-xs text-red-700 dark:text-red-400">{job.error}</p>
        </div>
      )}

      <div className="flex items-center gap-2 pt-2">
        {job.project_id ? (
          <Link to={`/projects/${job.project_id}`} className="flex-1">
            <Button variant="outline" size="sm" className="w-full">
              <Eye className="size-4 mr-2" />
              View Project
            </Button>
          </Link>
        ) : (
          <Button variant="outline" size="sm" className="flex-1" disabled>
            <Eye className="size-4 mr-2" />
            {job.status === "completed" ? "Project Pending" : "Processing..."}
          </Button>
        )}
        {job.status === "failed" && onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onRetry(job.id)}
            className="flex-1"
          >
            <RefreshCw className="size-4 mr-2" />
            Retry
          </Button>
        )}
      </div>
    </Card>
  )
}
