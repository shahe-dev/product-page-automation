import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"

export function useQACompare() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.qa.compare,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["qa"] })
    },
  })
}

export function useQAResults(projectId: string | null) {
  return useQuery({
    queryKey: ["qa", "results", projectId],
    queryFn: () => api.qa.results(projectId!),
    enabled: !!projectId,
  })
}

export function useQAHistory(page = 1) {
  return useQuery({
    queryKey: ["qa", "history", page],
    queryFn: () => api.qa.history({ page, limit: 20 }),
  })
}
