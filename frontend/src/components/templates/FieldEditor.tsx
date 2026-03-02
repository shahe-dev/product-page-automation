import { AlertCircle, Plus, Save } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useTemplateFields, useUpdateTemplateFields } from "@/hooks/queries/use-templates"
import type { FieldDefinition, FieldEditorRow, TemplateType } from "@/types"

import { AddFieldModal } from "./AddFieldModal"
import { FieldRow } from "./FieldRow"

interface FieldEditorProps {
  templateType: TemplateType
  contentVariant?: string
}

export function FieldEditor({ templateType, contentVariant = "standard" }: FieldEditorProps) {
  const { data, isLoading, error } = useTemplateFields(templateType, contentVariant)
  const updateFields = useUpdateTemplateFields()

  // Local state for editing
  const [localFields, setLocalFields] = useState<FieldEditorRow[]>([])
  const [hasChanges, setHasChanges] = useState(false)
  const [addModalOpen, setAddModalOpen] = useState(false)

  // Sync remote data to local state
  useEffect(() => {
    if (data?.fields) {
      const rows: FieldEditorRow[] = Object.entries(data.fields)
        .map(([name, field]) => ({
          name,
          ...field,
          isDirty: false,
          isNew: false,
        }))
        .sort((a, b) => a.row - b.row)
      setLocalFields(rows)
      setHasChanges(false)
    }
  }, [data])

  // Group fields by section
  const sections = useMemo(() => {
    const grouped = new Map<string, FieldEditorRow[]>()
    for (const field of localFields) {
      if (!field.is_active) continue // Skip soft-deleted fields
      const section = field.section || "Unknown"
      if (!grouped.has(section)) {
        grouped.set(section, [])
      }
      grouped.get(section)!.push(field)
    }
    return grouped
  }, [localFields])

  // Handle field update
  const handleFieldUpdate = useCallback((name: string, updates: Partial<FieldEditorRow>) => {
    setLocalFields((prev) =>
      prev.map((f) => (f.name === name ? { ...f, ...updates, isDirty: true } : f))
    )
    setHasChanges(true)
  }, [])

  // Handle field delete (soft delete)
  const handleFieldDelete = useCallback((name: string) => {
    setLocalFields((prev) =>
      prev.map((f) => (f.name === name ? { ...f, is_active: false, isDirty: true } : f))
    )
    setHasChanges(true)
  }, [])

  // Handle add new field
  const handleAddField = useCallback((name: string, field: Omit<FieldEditorRow, "name">) => {
    setLocalFields((prev) => [
      ...prev,
      { name, ...field, isDirty: true, isNew: true },
    ].sort((a, b) => a.row - b.row))
    setHasChanges(true)
    setAddModalOpen(false)
  }, [])

  // Save all changes
  const handleSave = useCallback(async () => {
    // Convert local fields back to API format
    const fields: Record<string, FieldDefinition> = {}
    for (const field of localFields) {
      fields[field.name] = {
        row: field.row,
        section: field.section,
        char_limit: field.char_limit,
        required: field.required,
        field_type: field.field_type,
        is_active: field.is_active,
      }
    }

    await updateFields.mutateAsync({
      templateType,
      fields,
      contentVariant,
    })
    setHasChanges(false)
  }, [localFields, templateType, contentVariant, updateFields])

  // Prompt before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasChanges) {
        e.preventDefault()
        e.returnValue = ""
      }
    }
    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => window.removeEventListener("beforeunload", handleBeforeUnload)
  }, [hasChanges])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="size-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="size-4" />
        <AlertDescription>
          Failed to load fields: {error.message}
        </AlertDescription>
      </Alert>
    )
  }

  const activeFieldCount = localFields.filter((f) => f.is_active).length
  const dirtyFieldCount = localFields.filter((f) => f.isDirty).length

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {activeFieldCount} fields
          {dirtyFieldCount > 0 && (
            <span className="ml-2 text-amber-600">
              ({dirtyFieldCount} unsaved changes)
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAddModalOpen(true)}
          >
            <Plus className="mr-1 size-4" />
            Add Field
          </Button>
          <Button
            size="sm"
            disabled={!hasChanges || updateFields.isPending}
            onClick={handleSave}
          >
            <Save className="mr-1 size-4" />
            {updateFields.isPending ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>

      {/* Unsaved changes warning */}
      {hasChanges && (
        <Alert>
          <AlertCircle className="size-4" />
          <AlertDescription>
            You have unsaved changes. Click "Save Changes" to persist them.
          </AlertDescription>
        </Alert>
      )}

      {/* Field table */}
      <div className="rounded-lg border">
        <div className="grid grid-cols-[60px_1fr_150px_80px_80px_120px_60px] gap-2 border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground">
          <div>Row</div>
          <div>Field Name</div>
          <div>Section</div>
          <div>Limit</div>
          <div>Required</div>
          <div>Type</div>
          <div></div>
        </div>
        <ScrollArea className="h-[500px]">
          {Array.from(sections.entries()).map(([sectionName, fields]) => (
            <div key={sectionName}>
              <div className="border-b bg-muted/30 px-4 py-1.5 text-xs font-semibold text-muted-foreground">
                {sectionName} ({fields.length})
              </div>
              {fields.map((field) => (
                <FieldRow
                  key={field.name}
                  field={field}
                  onUpdate={(updates) => handleFieldUpdate(field.name, updates)}
                  onDelete={() => handleFieldDelete(field.name)}
                />
              ))}
            </div>
          ))}
        </ScrollArea>
      </div>

      {/* Add field modal */}
      <AddFieldModal
        open={addModalOpen}
        onOpenChange={setAddModalOpen}
        onAdd={handleAddField}
        existingNames={localFields.map((f) => f.name)}
        existingRows={localFields.filter((f) => f.is_active).map((f) => f.row)}
      />
    </div>
  )
}
