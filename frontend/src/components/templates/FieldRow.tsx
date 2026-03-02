import { Trash2 } from "lucide-react"
import { useCallback } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import type { FieldEditorRow, FieldType } from "@/types"

interface FieldRowProps {
  field: FieldEditorRow
  onUpdate: (updates: Partial<FieldEditorRow>) => void
  onDelete: () => void
}

const FIELD_TYPES: { value: FieldType; label: string }[] = [
  { value: "GENERATED", label: "Generated" },
  { value: "EXTRACTED", label: "Extracted" },
  { value: "HYBRID", label: "Hybrid" },
  { value: "STATIC", label: "Static" },
]

export function FieldRow({ field, onUpdate, onDelete }: FieldRowProps) {
  const handleRowChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = parseInt(e.target.value, 10)
      if (!isNaN(value) && value > 0) {
        onUpdate({ row: value })
      }
    },
    [onUpdate]
  )

  const handleSectionChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onUpdate({ section: e.target.value })
    },
    [onUpdate]
  )

  const handleLimitChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value.trim()
      if (value === "") {
        onUpdate({ char_limit: null })
      } else {
        const num = parseInt(value, 10)
        if (!isNaN(num) && num > 0) {
          onUpdate({ char_limit: num })
        }
      }
    },
    [onUpdate]
  )

  const handleRequiredChange = useCallback(
    (value: string) => {
      onUpdate({ required: value === "yes" })
    },
    [onUpdate]
  )

  const handleTypeChange = useCallback(
    (value: FieldType) => {
      onUpdate({ field_type: value })
    },
    [onUpdate]
  )

  return (
    <div
      className={cn(
        "grid grid-cols-[60px_1fr_150px_80px_80px_120px_60px] gap-2 border-b px-4 py-2 text-sm",
        field.isDirty && "bg-amber-50 dark:bg-amber-950/20",
        field.isNew && "bg-green-50 dark:bg-green-950/20"
      )}
    >
      {/* Row number */}
      <Input
        type="number"
        min={1}
        value={field.row}
        onChange={handleRowChange}
        className="h-8 text-center"
      />

      {/* Field name (read-only) */}
      <div className="flex items-center truncate font-mono text-xs">
        {field.name}
      </div>

      {/* Section */}
      <Input
        value={field.section}
        onChange={handleSectionChange}
        className="h-8"
      />

      {/* Character limit */}
      <Input
        type="number"
        min={1}
        value={field.char_limit ?? ""}
        onChange={handleLimitChange}
        placeholder="-"
        className="h-8 text-center"
      />

      {/* Required */}
      <Select
        value={field.required ? "yes" : "no"}
        onValueChange={handleRequiredChange}
      >
        <SelectTrigger className="h-8">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="yes">Yes</SelectItem>
          <SelectItem value="no">No</SelectItem>
        </SelectContent>
      </Select>

      {/* Field type */}
      <Select value={field.field_type} onValueChange={handleTypeChange}>
        <SelectTrigger className="h-8 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {FIELD_TYPES.map((type) => (
            <SelectItem key={type.value} value={type.value}>
              {type.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Delete button */}
      <Button
        variant="ghost"
        size="icon"
        className="size-8 text-muted-foreground hover:text-destructive"
        onClick={onDelete}
      >
        <Trash2 className="size-4" />
      </Button>
    </div>
  )
}
