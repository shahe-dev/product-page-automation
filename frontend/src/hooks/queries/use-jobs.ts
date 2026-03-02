import { useQuery } from "@tanstack/react-query"

import { api } from "@/lib/api"

export function useJobs() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.jobs.list(),
    refetchInterval: (query) => {
      const data = query.state.data
      const hasActiveJobs = data?.jobs?.some(
        (j: { status: string }) => j.status === "pending" || j.status === "processing"
      )
      // Poll every 2.5s when there are active jobs for consistent UI updates
      return hasActiveJobs ? 2500 : false
    },
  })
}

export function useJob(id: string | null, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["jobs", id],
    queryFn: () => api.jobs.get(id!),
    enabled: !!id && (options?.enabled ?? true),
    refetchInterval: (query) => {
      const data = query.state.data
      if (data?.status === "completed" || data?.status === "failed") {
        return false
      }
      return 2000
    },
  })
}

// REMOVED: useUploadFile - replaced by useExtractPdf in use-process.ts

export function useJobSteps(id: string | null, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["jobs", id, "steps"],
    queryFn: () => api.jobs.getSteps(id!),
    enabled: !!id && (options?.enabled ?? true),
    refetchInterval: (query) => {
      // Stop polling if all steps are complete or any failed
      const steps = query.state.data
      if (!steps) return 3000
      const allDone = steps.every(
        (s: { status: string }) =>
          s.status === "completed" || s.status === "failed" || s.status === "skipped"
      )
      return allDone ? false : 3000
    },
  })
}
