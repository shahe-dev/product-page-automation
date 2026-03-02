import { useQuery } from "@tanstack/react-query"

import { apiClient } from "@/lib/api"
import type { ActivityItem, DashboardStats } from "@/types"

// Note: dashboard endpoints use apiClient directly because they are
// lightweight read-only queries not yet wrapped in the `api` facade.
export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: () =>
      apiClient.get<DashboardStats>("/projects/statistics").then((r) => r.data),
    staleTime: 60 * 1000,
    refetchInterval: 60 * 1000,
  })
}

export function useRecentActivity(limit: number = 10) {
  return useQuery({
    queryKey: ["dashboard", "activity", limit],
    queryFn: () =>
      apiClient
        .get<ActivityItem[]>("/projects/activity", { params: { limit } })
        .then((r) => r.data),
    refetchInterval: 30 * 1000,
  })
}
