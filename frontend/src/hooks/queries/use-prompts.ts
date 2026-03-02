import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { api } from "@/lib/api"
import type { PromptFilters } from "@/types"

export function usePrompts(filters?: PromptFilters) {
  return useQuery({
    queryKey: ["prompts", filters],
    queryFn: () => api.prompts.list(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes - prompts change rarely
    gcTime: 30 * 60 * 1000, // 30 minutes in cache
  })
}

export function useGroupedPrompts(templateType: string | null) {
  return useQuery({
    queryKey: ["prompts", "grouped", templateType],
    queryFn: () => api.prompts.grouped(templateType!),
    enabled: !!templateType,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function usePrompt(id: string | undefined) {
  return useQuery({
    queryKey: ["prompts", id],
    queryFn: () => api.prompts.get(id!),
    enabled: !!id,
  })
}

export function usePromptVersions(id: string | undefined) {
  return useQuery({
    queryKey: ["prompts", id, "versions"],
    queryFn: () => api.prompts.getVersions(id!),
    enabled: !!id,
  })
}

export function useCreatePrompt() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { name: string; template_type: string; content_variant?: string; content: string; character_limit?: number }) =>
      api.prompts.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] })
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create prompt")
    },
  })
}

export function useUpdatePrompt() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, content, reason }: { id: string; content: string; reason: string }) =>
      api.prompts.update(id, content, reason),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["prompts", id] })
      queryClient.invalidateQueries({ queryKey: ["prompts", id, "versions"] })
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update prompt")
    },
  })
}
