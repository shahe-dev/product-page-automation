import { Code,Eye, Save } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Textarea } from "@/components/ui/textarea"
import { useUpdatePrompt } from "@/hooks"
import type { Prompt } from "@/types"

const TEMPLATE_VARIABLES = [
  "project_name",
  "developer_name",
  "location",
  "emirate",
  "property_type",
  "features",
  "amenities",
  "price_range",
  "bedrooms",
  "size_sqft",
  "completion_date",
]

const SAMPLE_DATA = {
  project_name: "Marina Heights",
  developer_name: "Emaar Properties",
  location: "Dubai Marina",
  emirate: "Dubai",
  property_type: "Apartment",
  features: "Sea view, Smart home, High-floor",
  amenities: "Pool, Gym, Parking, 24/7 Security",
  price_range: "AED 2.5M - 4.2M",
  bedrooms: "1-3",
  size_sqft: "850 - 2,200",
  completion_date: "Q4 2026",
}

interface PromptEditorProps {
  prompt: Prompt
  onSave?: () => void
}

export function PromptEditor({ prompt, onSave }: PromptEditorProps) {
  const [content, setContent] = useState(prompt.content || "")
  const [changeReason, setChangeReason] = useState("")
  const [showPreview, setShowPreview] = useState(false)
  const [showVariables, setShowVariables] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const updatePrompt = useUpdatePrompt()

  const hasUnsavedChanges = content !== (prompt.content || "")

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = ""
      }
    }

    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => window.removeEventListener("beforeunload", handleBeforeUnload)
  }, [hasUnsavedChanges])

  const handleContentChange = (value: string) => {
    setContent(value)

    const textarea = textareaRef.current
    if (textarea) {
      const cursorPos = textarea.selectionStart
      const textBeforeCursor = value.slice(0, cursorPos)
      const lastOpenBrace = textBeforeCursor.lastIndexOf("{{")
      const lastCloseBrace = textBeforeCursor.lastIndexOf("}}")

      if (lastOpenBrace > lastCloseBrace) {
        setShowVariables(true)
      } else {
        setShowVariables(false)
      }
    }
  }

  const insertVariable = (variable: string) => {
    const textarea = textareaRef.current
    if (!textarea) return

    const cursorPos = textarea.selectionStart
    const textBeforeCursor = content.slice(0, cursorPos)
    const textAfterCursor = content.slice(cursorPos)

    const lastOpenBrace = textBeforeCursor.lastIndexOf("{{")
    const beforeBraces = content.slice(0, lastOpenBrace)

    const newContent = `${beforeBraces}{{${variable}}}${textAfterCursor}`
    setContent(newContent)
    setShowVariables(false)

    setTimeout(() => {
      const newCursorPos = lastOpenBrace + variable.length + 4
      textarea.focus()
      textarea.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  const handleSave = async () => {
    if (!changeReason.trim()) {
      toast.error("Please provide a change reason")
      return
    }

    try {
      await updatePrompt.mutateAsync({
        id: prompt.id,
        content,
        reason: changeReason,
      })
      setChangeReason("")
      onSave?.()
    } catch (error) {
      console.error("Failed to update prompt:", error)
    }
  }

  const renderPreview = () => {
    let preview = content
    TEMPLATE_VARIABLES.forEach((variable) => {
      const regex = new RegExp(`\\{\\{${variable}\\}\\}`, "g")
      const value = SAMPLE_DATA[variable as keyof typeof SAMPLE_DATA]
      preview = preview.replace(regex, `[${value}]`)
    })
    return preview
  }

  const renderHighlightedContent = () => {
    const parts = content.split(/({{[^}]*}})/g)
    return parts.map((part, index) => {
      if (part.startsWith("{{") && part.endsWith("}}")) {
        return (
          <span key={index} className="text-blue-600 font-semibold">
            {part}
          </span>
        )
      }
      return <span key={index}>{part}</span>
    })
  }

  const charCount = content.length

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Prompt Content</CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                {charCount} characters
              </span>
              <Button
                variant={showPreview ? "default" : "outline"}
                size="sm"
                onClick={() => setShowPreview(!showPreview)}
              >
                {showPreview ? (
                  <>
                    <Code className="mr-2 size-4" />
                    Edit
                  </>
                ) : (
                  <>
                    <Eye className="mr-2 size-4" />
                    Preview
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {showPreview ? (
            <div className="min-h-[400px] rounded-md border bg-muted/50 p-4 font-mono text-sm whitespace-pre-wrap">
              {renderPreview()}
            </div>
          ) : (
            <div className="relative">
              <Popover open={showVariables} onOpenChange={setShowVariables}>
                <PopoverTrigger asChild>
                  <div>
                    <Textarea
                      ref={textareaRef}
                      value={content}
                      onChange={(e) => handleContentChange(e.target.value)}
                      className="min-h-[400px] font-mono text-sm resize-y"
                      placeholder="Enter prompt content. Use {{variable_name}} for template variables."
                    />
                  </div>
                </PopoverTrigger>
                <PopoverContent className="w-[300px] p-2" align="start">
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-muted-foreground px-2 py-1">
                      Template Variables
                    </p>
                    {TEMPLATE_VARIABLES.map((variable) => (
                      <button
                        key={variable}
                        className="w-full rounded px-2 py-1.5 text-left text-sm hover:bg-accent hover:text-accent-foreground"
                        onClick={() => insertVariable(variable)}
                      >
                        {variable}
                      </button>
                    ))}
                  </div>
                </PopoverContent>
              </Popover>
              <div className="mt-2 rounded-md border bg-muted/30 p-3 text-sm">
                <p className="font-medium mb-1">Syntax Highlighting:</p>
                <div className="whitespace-pre-wrap break-words">
                  {renderHighlightedContent()}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Save Changes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="change-reason">
              Change Reason <span className="text-destructive">*</span>
            </Label>
            <Input
              id="change-reason"
              value={changeReason}
              onChange={(e) => setChangeReason(e.target.value)}
              placeholder="Describe what changed and why..."
              disabled={!hasUnsavedChanges}
            />
          </div>
          <Button
            onClick={handleSave}
            disabled={!hasUnsavedChanges || !changeReason.trim() || updatePrompt.isPending}
            className="w-full sm:w-auto"
          >
            <Save className="mr-2 size-4" />
            {updatePrompt.isPending ? "Saving..." : "Save Changes"}
          </Button>
          {hasUnsavedChanges && (
            <p className="text-sm text-amber-600">
              You have unsaved changes
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
