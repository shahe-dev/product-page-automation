import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { ApprovalFilters } from "@/types"

export function useApprovalQueue(filters?: ApprovalFilters) {
  return useQuery({
    queryKey: ["approvals", filters],
    queryFn: () => api.approvals.list(filters),
  })
}

export function useApproveProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => api.approvals.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] })
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })
}

export function useRejectProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      api.approvals.reject(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] })
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })
}

export function useSubmitForApproval() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (project_id: string) => api.approvals.submit(project_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] })
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })
}
