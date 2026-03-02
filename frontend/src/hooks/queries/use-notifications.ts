import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { api } from "@/lib/api"
import type { NotificationsResponse } from "@/types"

export function useNotifications(page = 1, unreadOnly = false) {
  return useQuery<NotificationsResponse>({
    queryKey: ["notifications", page, unreadOnly],
    queryFn: () => api.notifications.list({ page, limit: 20, unread_only: unreadOnly }),
    refetchInterval: 30000,
  })
}

export function useUnreadCount() {
  return useQuery<number>({
    queryKey: ["notifications", "unread-count"],
    queryFn: api.notifications.getUnreadCount,
    refetchInterval: 15000,
  })
}

export function useMarkAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.notifications.markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to mark notification as read")
    },
  })
}

export function useMarkAllAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.notifications.markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      queryClient.setQueryData(["notifications", "unread-count"], 0)
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to mark all notifications as read")
    },
  })
}
