import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { ExtractResponse, GenerateResponse, PipelineProgress, TemplateType } from "@/types"

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

      // Fetch extraction job + steps in parallel
      const [extractionJob, extractionSteps, { jobs }] = await Promise.all([
        api.jobs.get(extractionJobId),
        api.jobs.getSteps(extractionJobId),
        api.jobs.list({ limit: 50 }),
      ])

      // Find generation jobs that reference the same project or material package
      const generationJobs = jobs.filter(
        (j) =>
          j.job_type === "generation" &&
          (
            (extractionJob.project_id && j.project_id === extractionJob.project_id) ||
            (extractionJob.material_package_id && j.material_package_id === extractionJob.material_package_id)
          )
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
        extraction_completed_at: extractionJob.completed_at || null,
        extraction_steps: extractionSteps,
        extraction_current_step: extractionJob.current_step || null,
        extraction_progress_message: extractionJob.progress_message || null,
        generation_jobs: generationJobs.map((j) => ({
          job_id: j.id,
          template_type: (j.template_type || "unknown") as TemplateType,
          status: j.status,
          progress: j.progress,
          progress_message: j.progress_message || null,
        })),
        overall_progress: overall,
      }
    },
    enabled: !!extractionJobId && (options?.enabled ?? true),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 3000

      // Stop polling when pipeline is terminal
      const extractionDone =
        data.extraction_status === "completed" || data.extraction_status === "failed"
      const extractionFailed = data.extraction_status === "failed"
      const hasGenJobs = data.generation_jobs.length > 0
      const allGenDone = hasGenJobs && data.generation_jobs.every(
        (j) => j.status === "completed" || j.status === "failed"
      )

      // If extraction failed, no gen jobs will be created -- stop polling
      if (extractionFailed || (extractionDone && allGenDone)) return false

      // Safety timeout: if extraction completed 30+ seconds ago and still no
      // generation jobs found, stop polling (prevents infinite wait on stale data)
      if (extractionDone && !hasGenJobs && data.extraction_completed_at) {
        const completedAgo = Date.now() - new Date(data.extraction_completed_at).getTime()
        if (completedAgo > 30_000) return false
      }

      return 2500
    },
  })
}
