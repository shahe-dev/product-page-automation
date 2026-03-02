import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { api } from "@/lib/api"
import type { FieldDefinition, FieldDefinitionCreate, FieldDefinitionUpdate } from "@/types"

export function useTemplates(filters?: { template_type?: string; is_active?: boolean }) {
  return useQuery({
    queryKey: ["templates", filters],
    queryFn: () => api.templates.list(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useTemplateFields(templateType: string | null, contentVariant: string = "standard") {
  return useQuery({
    queryKey: ["templates", templateType, "fields", contentVariant],
    queryFn: () => api.templates.getFields(templateType!, contentVariant),
    enabled: !!templateType,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useUpdateTemplateFields() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      templateType,
      fields,
      contentVariant = "standard",
    }: {
      templateType: string
      fields: Record<string, FieldDefinition>
      contentVariant?: string
    }) => api.templates.updateFields(templateType, fields, contentVariant),
    onSuccess: (_data, { templateType, contentVariant }) => {
      queryClient.invalidateQueries({ queryKey: ["templates", templateType, "fields", contentVariant] })
      queryClient.invalidateQueries({ queryKey: ["templates"] })
      toast.success("Field definitions updated successfully")
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update field definitions")
    },
  })
}

export function useAddTemplateField() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      templateType,
      fieldName,
      field,
      contentVariant = "standard",
    }: {
      templateType: string
      fieldName: string
      field: FieldDefinitionCreate
      contentVariant?: string
    }) => api.templates.addField(templateType, fieldName, field, contentVariant),
    onSuccess: (_data, { templateType, contentVariant, fieldName }) => {
      queryClient.invalidateQueries({ queryKey: ["templates", templateType, "fields", contentVariant] })
      toast.success(`Field "${fieldName}" added successfully`)
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to add field")
    },
  })
}

export function useDeleteTemplateField() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      templateType,
      fieldName,
      contentVariant = "standard",
    }: {
      templateType: string
      fieldName: string
      contentVariant?: string
    }) => api.templates.deleteField(templateType, fieldName, contentVariant),
    onSuccess: (_data, { templateType, contentVariant, fieldName }) => {
      queryClient.invalidateQueries({ queryKey: ["templates", templateType, "fields", contentVariant] })
      toast.success(`Field "${fieldName}" deleted`)
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to delete field")
    },
  })
}

export function useUpdateTemplateField() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      templateType,
      fieldName,
      updates,
      contentVariant = "standard",
    }: {
      templateType: string
      fieldName: string
      updates: FieldDefinitionUpdate
      contentVariant?: string
    }) => api.templates.updateField(templateType, fieldName, updates, contentVariant),
    onSuccess: (_data, { templateType, contentVariant }) => {
      queryClient.invalidateQueries({ queryKey: ["templates", templateType, "fields", contentVariant] })
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update field")
    },
  })
}
