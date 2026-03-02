import { useCallback, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { FieldEditorRow, FieldType } from "@/types"

interface AddFieldModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAdd: (name: string, field: Omit<FieldEditorRow, "name">) => void
  existingNames: string[]
  existingRows: number[]
}

const FIELD_TYPES: { value: FieldType; label: string }[] = [
  { value: "GENERATED", label: "Generated" },
  { value: "EXTRACTED", label: "Extracted" },
  { value: "HYBRID", label: "Hybrid" },
  { value: "STATIC", label: "Static" },
]

export function AddFieldModal({
  open,
  onOpenChange,
  onAdd,
  existingNames,
  existingRows,
}: AddFieldModalProps) {
  const [name, setName] = useState("")
  const [row, setRow] = useState("")
  const [section, setSection] = useState("")
  const [charLimit, setCharLimit] = useState("")
  const [required, setRequired] = useState(false)
  const [fieldType, setFieldType] = useState<FieldType>("GENERATED")
  const [errors, setErrors] = useState<string[]>([])

  const resetForm = useCallback(() => {
    setName("")
    setRow("")
    setSection("")
    setCharLimit("")
    setRequired(false)
    setFieldType("GENERATED")
    setErrors([])
  }, [])

  const validate = useCallback((): string[] => {
    const errs: string[] = []

    // Name validation
    if (!name.trim()) {
      errs.push("Field name is required")
    } else if (!/^[a-z][a-z0-9_]*$/.test(name)) {
      errs.push("Field name must be lowercase with underscores (e.g., meta_title)")
    } else if (existingNames.includes(name)) {
      errs.push("A field with this name already exists")
    }

    // Row validation
    const rowNum = parseInt(row, 10)
    if (!row || isNaN(rowNum) || rowNum < 1) {
      errs.push("Row must be a positive integer")
    } else if (existingRows.includes(rowNum) && !name.includes("bullet")) {
      errs.push(`Row ${rowNum} is already in use (unless this is a bullet field)`)
    }

    // Section validation
    if (!section.trim()) {
      errs.push("Section is required")
    }

    // Char limit validation
    if (charLimit) {
      const limit = parseInt(charLimit, 10)
      if (isNaN(limit) || limit < 1) {
        errs.push("Character limit must be a positive integer or empty")
      }
    }

    return errs
  }, [name, row, section, charLimit, existingNames, existingRows])

  const handleSubmit = useCallback(() => {
    const validationErrors = validate()
    if (validationErrors.length > 0) {
      setErrors(validationErrors)
      return
    }

    onAdd(name.trim(), {
      row: parseInt(row, 10),
      section: section.trim(),
      char_limit: charLimit ? parseInt(charLimit, 10) : null,
      required,
      field_type: fieldType,
      is_active: true,
    })

    resetForm()
  }, [name, row, section, charLimit, required, fieldType, validate, onAdd, resetForm])

  const handleOpenChange = useCallback(
    (newOpen: boolean) => {
      if (!newOpen) {
        resetForm()
      }
      onOpenChange(newOpen)
    },
    [onOpenChange, resetForm]
  )

  // Suggest next available row
  const suggestedRow = existingRows.length > 0 ? Math.max(...existingRows) + 1 : 1

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add New Field</DialogTitle>
          <DialogDescription>
            Add a new field definition to this template. Fields define where
            content is written in the Google Sheet.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Validation errors */}
          {errors.length > 0 && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <ul className="list-inside list-disc space-y-1">
                {errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Field name */}
          <div className="space-y-2">
            <Label htmlFor="field-name">Field Name</Label>
            <Input
              id="field-name"
              value={name}
              onChange={(e) => setName(e.target.value.toLowerCase())}
              placeholder="e.g., meta_title, hero_heading"
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">
              Use lowercase letters and underscores only
            </p>
          </div>

          {/* Row number */}
          <div className="space-y-2">
            <Label htmlFor="field-row">Row Number</Label>
            <Input
              id="field-row"
              type="number"
              min={1}
              value={row}
              onChange={(e) => setRow(e.target.value)}
              placeholder={`e.g., ${suggestedRow}`}
            />
            <p className="text-xs text-muted-foreground">
              Suggested next row: {suggestedRow}
            </p>
          </div>

          {/* Section */}
          <div className="space-y-2">
            <Label htmlFor="field-section">Section</Label>
            <Input
              id="field-section"
              value={section}
              onChange={(e) => setSection(e.target.value)}
              placeholder="e.g., SEO, Hero, About"
            />
          </div>

          {/* Two columns: limit and required */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="field-limit">Character Limit</Label>
              <Input
                id="field-limit"
                type="number"
                min={1}
                value={charLimit}
                onChange={(e) => setCharLimit(e.target.value)}
                placeholder="Optional"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="field-required">Required</Label>
              <Select
                value={required ? "yes" : "no"}
                onValueChange={(v) => setRequired(v === "yes")}
              >
                <SelectTrigger id="field-required">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="no">No</SelectItem>
                  <SelectItem value="yes">Yes</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Field type */}
          <div className="space-y-2">
            <Label htmlFor="field-type">Field Type</Label>
            <Select value={fieldType} onValueChange={(v) => setFieldType(v as FieldType)}>
              <SelectTrigger id="field-type">
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
            <p className="text-xs text-muted-foreground">
              Generated = AI creates content, Extracted = from PDF, Hybrid = AI enhances extracted
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Add Field</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
