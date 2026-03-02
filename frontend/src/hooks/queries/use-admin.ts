import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { AdminStats, AdminUser, AllowlistEntry } from "@/types"

export function useAllowlist() {
  return useQuery<AllowlistEntry[]>({
    queryKey: ["admin", "allowlist"],
    queryFn: api.admin.listAllowlist,
  })
}

export function useAddAllowlistEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.admin.addAllowlistEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "allowlist"] })
    },
  })
}

export function useUpdateAllowlistEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) =>
      api.admin.updateAllowlistEntry(id, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "allowlist"] })
    },
  })
}

export function useRemoveAllowlistEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.admin.removeAllowlistEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "allowlist"] })
    },
  })
}

export function useAdminStats() {
  return useQuery<AdminStats>({
    queryKey: ["admin", "stats"],
    queryFn: api.admin.getStats,
    staleTime: 30_000,
  })
}

export function useAdminUsers() {
  return useQuery<AdminUser[]>({
    queryKey: ["admin", "users"],
    queryFn: api.admin.listUsers,
  })
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      api.admin.updateUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] })
    },
  })
}
