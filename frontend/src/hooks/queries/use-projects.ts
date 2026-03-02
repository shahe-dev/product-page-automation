import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { GenerationRun, Project, ProjectDataFiles, ProjectDetail, ProjectFilters } from "@/types"

export function useProjects(filters?: ProjectFilters) {
  return useQuery({
    queryKey: ["projects", filters],
    queryFn: () => api.projects.list(filters),
    staleTime: 5 * 60 * 1000,
  })
}

export function useProject(id: string | undefined) {
  return useQuery<ProjectDetail>({
    queryKey: ["projects", id],
    queryFn: () => api.projects.get(id!),
    enabled: !!id,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.projects.create,
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      queryClient.setQueryData(["projects", newProject.id], newProject)
    },
  })
}

export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) =>
      api.projects.update(id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ["projects", id] })
      const previous = queryClient.getQueryData(["projects", id])
      queryClient.setQueryData(["projects", id], (old: Project) => ({
        ...old,
        ...data,
      }))
      return { previous, id }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["projects", context.id], context.previous)
      }
    },
    onSettled: () => {
      // Invalidate all project queries (list + detail) to sync status changes
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.projects.delete,
    onSuccess: (_data, id) => {
      // Mark all project queries as stale WITHOUT triggering refetches or removing
      // cached data. Removing the detail cache here would cause ProjectDetailPage to
      // re-render in loading state (unmounting the dialog) before navigate() fires.
      // The list page will refetch naturally when it mounts.
      queryClient.invalidateQueries({
        queryKey: ["projects"],
        refetchType: "none",
      })
      queryClient.removeQueries({ queryKey: ["generation-runs", id] })
    },
  })
}

export function useProjectDataFiles(projectId: string | undefined) {
  return useQuery<ProjectDataFiles>({
    queryKey: ["project-data-files", projectId],
    queryFn: () => api.projects.dataFiles(projectId!),
    enabled: !!projectId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useGenerationRuns(projectId: string | undefined) {
  return useQuery<GenerationRun[]>({
    queryKey: ["generation-runs", projectId],
    queryFn: () => api.process.getGenerationRuns(projectId!),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data || data.length === 0) return false

      const hasActive = data.some(
        (r) => r.status === "pending" || r.status === "processing"
      )
      return hasActive ? 3000 : false
    },
  })
}
