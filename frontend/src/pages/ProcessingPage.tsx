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
    if (stored) {
      try {
        return JSON.parse(stored)
      } catch {
        return null
      }
    }
    return null
  })
  const [preparingFilename, setPreparingFilename] = useState<string | null>(null)
  const jobCardRef = useRef<HTMLDivElement>(null)

  const { data: jobsData, isLoading: isLoadingJobs } = useJobs()
  const jobs = jobsData?.jobs

  // Track pipeline progress
  const { data: pipelineProgress } = usePipelineProgress(
    activePipeline?.extraction_job_id ?? null,
    { enabled: !!activePipeline }
  )

  const handleUploadStarted = useCallback(
    (info: { filename: string; templateIds: string[] }) => {
      setPreparingFilename(info.filename)
    },
    []
  )

  const handleUploadComplete = useCallback(
    (result: { extraction_job_id: string; template_ids: string[] }) => {
      setPreparingFilename(null)
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

  const handleDismissPipeline = useCallback(() => {
    sessionStorage.removeItem(ACTIVE_PIPELINE_STORAGE_KEY)
    setActivePipeline(null)
    setPreparingFilename(null)
  }, [])

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
    const extractionFailed = pipelineProgress.extraction_status === "failed"
    const hasGenJobs = pipelineProgress.generation_jobs.length > 0
    const allGenDone = hasGenJobs && pipelineProgress.generation_jobs.every(
      (j) => j.status === "completed" || j.status === "failed"
    )

    // If extraction failed, no gen jobs will come -- treat pipeline as done
    if (extractionFailed || (extractionDone && allGenDone)) {
      handlePipelineComplete()
      return
    }

    // Safety timeout: if extraction done 30s+ ago with no gen jobs, auto-dismiss
    if (extractionDone && !hasGenJobs && pipelineProgress.extraction_completed_at) {
      const completedAgo = Date.now() - new Date(pipelineProgress.extraction_completed_at).getTime()
      if (completedAgo > 30_000) {
        handlePipelineComplete()
      }
    }
  }, [pipelineProgress, handlePipelineComplete])

  // Filter jobs for display - exclude current pipeline's extraction job
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
            <FileUpload
              onUploadComplete={handleUploadComplete}
              onUploadStarted={handleUploadStarted}
              onUploadFailed={() => setPreparingFilename(null)}
            />
          </div>

          {(preparingFilename || activePipeline) && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Current Pipeline</h2>
                {activePipeline && (
                  <button
                    type="button"
                    onClick={handleDismissPipeline}
                    className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Dismiss
                  </button>
                )}
              </div>
              {activePipeline ? (
                <PipelineProgressTracker
                  extractionJobId={activePipeline.extraction_job_id}
                  startedAt={activePipeline.started_at}
                  onAllComplete={handlePipelineComplete}
                />
              ) : (
                <PipelineProgressTracker
                  preparing
                  preparingFilename={preparingFilename ?? undefined}
                />
              )}
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
