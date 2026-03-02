import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"

interface WorkflowStats {
  total_projects: number
  by_status: Record<string, number>
  by_assignee: Record<string, number>
  avg_processing_time_hours: number
}

export function useWorkflowStats() {
  return useQuery<WorkflowStats>({
    queryKey: ["workflow", "stats"],
    queryFn: api.workflow.stats,
    staleTime: 30_000,
  })
}

export function useMoveWorkflowItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      itemId,
      status,
      published_url,
    }: {
      itemId: string
      status: string
      published_url?: string
    }) =>
      api.workflow.moveItem(itemId, {
        workflow_status: status,
        published_url,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow"] })
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })
}
