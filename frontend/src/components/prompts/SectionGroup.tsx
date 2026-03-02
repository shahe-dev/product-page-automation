import { ChevronRight } from "lucide-react"
import { useState } from "react"
import { Link } from "react-router-dom"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Textarea } from "@/components/ui/textarea"
import { useCreatePrompt } from "@/hooks"
import { cn } from "@/lib/utils"
import type { PromptSection } from "@/types"

interface SectionGroupProps {
  section: PromptSection
  templateType: string
}

export function SectionGroup({ section, templateType }: SectionGroupProps) {
  const [expanded, setExpanded] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [createFieldName, setCreateFieldName] = useState("")
  const [createCharLimit, setCreateCharLimit] = useState<number | null>(null)
  const [createContent, setCreateContent] = useState("")
  const createMutation = useCreatePrompt()

  const coveragePercent =
    section.field_count > 0
      ? (section.prompts_defined / section.field_count) * 100
      : 0

  const handleInlineCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!createFieldName || !createContent.trim()) return
    try {
      await createMutation.mutateAsync({
        name: createFieldName,
        template_type: templateType,
        content_variant: "standard",
        content: createContent.trim(),
        character_limit: createCharLimit ?? undefined,
      })
      setCreateOpen(false)
      setCreateContent("")
    } catch {
      // Error handled by mutation hook (toast)
    }
  }

  const isNonPromptable = (fieldType?: string) =>
    fieldType === "EXTRACTED" || fieldType === "STATIC"

  return (
    <>
      <Collapsible open={expanded} onOpenChange={setExpanded}>
        <CollapsibleTrigger asChild>
          <div className="flex cursor-pointer items-center justify-between rounded-lg border p-4 hover:bg-muted/50">
            <div className="flex items-center gap-3">
              <ChevronRight
                className={cn(
                  "size-4 transition-transform",
                  expanded && "rotate-90"
                )}
              />
              <h3 className="font-semibold">{section.section}</h3>
              <Badge variant="outline">
                {section.prompts_defined}/{section.field_count}
              </Badge>
            </div>
            <Progress value={coveragePercent} className="h-2 w-24" />
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="rounded-b-lg border-x border-b">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/30">
                  <th className="w-12 p-2 text-left">Row</th>
                  <th className="p-2 text-left">Field</th>
                  <th className="w-20 p-2 text-left">Limit</th>
                  <th className="w-24 p-2 text-left">Status</th>
                  <th className="w-20 p-2 text-left"></th>
                </tr>
              </thead>
              <tbody>
                {section.fields.map((field) => (
                  <tr
                    key={field.field_name}
                    className="border-b last:border-0 hover:bg-muted/20"
                  >
                    <td className="p-2 text-muted-foreground">{field.row}</td>
                    <td className="p-2">
                      <span className="font-mono text-xs">{field.field_name}</span>
                      {field.required && (
                        <Badge
                          variant="destructive"
                          className="ml-2 text-[10px]"
                        >
                          Required
                        </Badge>
                      )}
                      {isNonPromptable(field.field_type) && (
                        <Badge variant="outline" className="ml-2 text-[10px]">
                          {field.field_type}
                        </Badge>
                      )}
                    </td>
                    <td className="p-2 text-muted-foreground">
                      {field.character_limit ?? "-"}
                    </td>
                    <td className="p-2">
                      {field.has_prompt ? (
                        <Badge variant="default">v{field.version}</Badge>
                      ) : isNonPromptable(field.field_type) ? (
                        <Badge variant="outline">N/A</Badge>
                      ) : (
                        <Badge variant="secondary">Missing</Badge>
                      )}
                    </td>
                    <td className="p-2">
                      {field.prompt_id ? (
                        <Link to={`/prompts/${field.prompt_id}`}>
                          <Button variant="ghost" size="sm">
                            Edit
                          </Button>
                        </Link>
                      ) : isNonPromptable(field.field_type) ? null : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setCreateFieldName(field.field_name)
                            setCreateCharLimit(field.character_limit ?? null)
                            setCreateOpen(true)
                          }}
                        >
                          Create
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-2xl">
          <form onSubmit={handleInlineCreate}>
            <DialogHeader>
              <DialogTitle>Create Prompt: {createFieldName}</DialogTitle>
              <DialogDescription>
                Template: {templateType} | Field: {createFieldName}
                {createCharLimit && ` | Limit: ${createCharLimit} chars`}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="inline-content">Prompt Content</Label>
                <Textarea
                  id="inline-content"
                  value={createContent}
                  onChange={(e) => setCreateContent(e.target.value)}
                  placeholder="Enter the prompt content..."
                  className="min-h-[200px] font-mono text-sm"
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!createContent.trim() || createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create Prompt"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  )
}
