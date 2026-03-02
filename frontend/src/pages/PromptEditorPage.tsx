import { ArrowLeft } from "lucide-react"
import { useNavigate, useParams } from "react-router-dom"

import { EmptyState, LoadingSpinner, PageHeader } from "@/components/common"
import { PromptEditor, VersionHistory } from "@/components/prompts"
import { Button } from "@/components/ui/button"
import { usePrompt } from "@/hooks"

export default function PromptEditorPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: prompt, isLoading, error } = usePrompt(id)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Loading..." />
        <LoadingSpinner />
      </div>
    )
  }

  if (error || !prompt) {
    return (
      <div className="space-y-6">
        <PageHeader title="Not Found" />
        <EmptyState
          title="Prompt not found"
          description="The prompt you are looking for does not exist."
          action={
            <Button onClick={() => navigate("/prompts")}>
              <ArrowLeft className="mr-2 size-4" />
              Back to Prompts
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader title={prompt.name}>
        <Button variant="outline" onClick={() => navigate("/prompts")}>
          <ArrowLeft className="mr-2 size-4" />
          Back to Prompts
        </Button>
      </PageHeader>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <PromptEditor prompt={prompt} />
        </div>
        <div className="lg:col-span-1">
          <VersionHistory promptId={prompt.id} currentContent={prompt.content || ""} />
        </div>
      </div>
    </div>
  )
}
