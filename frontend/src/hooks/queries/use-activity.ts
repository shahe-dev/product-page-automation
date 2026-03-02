import { useQuery } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { ActivityFeedItem, TeamStat } from "@/types"

export function useActivityFeed(page = 1) {
  return useQuery<{ items: ActivityFeedItem[] }>({
    queryKey: ["activity", "feed", page],
    queryFn: () => api.activity.feed({ page, limit: 30 }),
    staleTime: 30_000,
  })
}

export function useTeamStats() {
  return useQuery<TeamStat[]>({
    queryKey: ["activity", "team-stats"],
    queryFn: api.activity.teamStats,
    staleTime: 60_000,
  })
}
