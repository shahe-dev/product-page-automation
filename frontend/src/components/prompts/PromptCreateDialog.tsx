import { Plus } from "lucide-react"
import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
import { Textarea } from "@/components/ui/textarea"
import { useCreatePrompt } from "@/hooks"

const TEMPLATE_TYPES = [
  { value: "opr", label: "OPR" },
  { value: "mpp", label: "MPP" },
  { value: "adop", label: "ADOP" },
  { value: "adre", label: "ADRE" },
  { value: "aggregators", label: "Aggregators" },
  { value: "commercial", label: "Commercial" },
]

const CONTENT_VARIANTS = [
  { value: "standard", label: "Standard" },
  { value: "luxury", label: "Luxury" },
]

export function PromptCreateDialog() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [templateType, setTemplateType] = useState("opr")
  const [contentVariant, setContentVariant] = useState("standard")
  const [content, setContent] = useState("")
  const [characterLimit, setCharacterLimit] = useState("")

  const createPrompt = useCreatePrompt()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim() || !content.trim()) return

    try {
      const result = await createPrompt.mutateAsync({
        name: name.trim(),
        template_type: templateType,
        content_variant: contentVariant,
        content: content.trim(),
        character_limit: characterLimit ? parseInt(characterLimit, 10) : undefined,
      })

      setOpen(false)
      setName("")
      setContent("")
      setCharacterLimit("")
      navigate(`/prompts/${result.id}`)
    } catch (error) {
      console.error("Failed to create prompt:", error)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 size-4" />
          New Prompt
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Prompt</DialogTitle>
            <DialogDescription>
              Add a new prompt template for content generation.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">
                Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Project Description - Standard"
                required
                maxLength={255}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="template-type">
                  Template Type <span className="text-destructive">*</span>
                </Label>
                <Select value={templateType} onValueChange={setTemplateType}>
                  <SelectTrigger id="template-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TEMPLATE_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="content-variant">Content Variant</Label>
                <Select value={contentVariant} onValueChange={setContentVariant}>
                  <SelectTrigger id="content-variant">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CONTENT_VARIANTS.map((variant) => (
                      <SelectItem key={variant.value} value={variant.value}>
                        {variant.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="character-limit">Character Limit (optional)</Label>
              <Input
                id="character-limit"
                type="number"
                min="0"
                value={characterLimit}
                onChange={(e) => setCharacterLimit(e.target.value)}
                placeholder="e.g., 500"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="content">
                Prompt Content <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter the prompt content. Use {{variable_name}} for template variables."
                className="min-h-[200px] font-mono text-sm"
                required
              />
              <p className="text-xs text-muted-foreground">
                Use curly braces for variables: {"{{"}"project_name{"}},"} {"{{"}"developer_name{"}}"}, etc.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={createPrompt.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!name.trim() || !content.trim() || createPrompt.isPending}
            >
              {createPrompt.isPending ? "Creating..." : "Create Prompt"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
