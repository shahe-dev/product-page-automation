import { formatDistanceToNow } from "date-fns"
import { ExternalLink, Globe, Send } from "lucide-react"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { EmptyState, LoadingSpinner, PageHeader } from "@/components/common"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useMoveWorkflowItem, useProjects } from "@/hooks"
import { isSafeExternalUrl, safeParseDate } from "@/lib/utils"

export default function PublishQueuePage() {
  const navigate = useNavigate()
  const [publishDialogOpen, setPublishDialogOpen] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [publishedUrl, setPublishedUrl] = useState("")

  const { data: projectsResponse, isLoading } = useProjects({ status: undefined })
  const moveItem = useMoveWorkflowItem()

  // Filter projects in publishing-ready statuses
  const publishableProjects =
    projectsResponse?.items.filter(
      (p) =>
        p.workflow_status === "approved" ||
        p.workflow_status === "publishing" ||
        p.workflow_status === "published"
    ) ?? []

  const handleMarkPublished = async () => {
    if (!selectedProjectId || !publishedUrl.trim()) {
      toast.error("Please enter the published URL")
      return
    }

    try {
      await moveItem.mutateAsync({
        itemId: selectedProjectId,
        status: "published",
        published_url: publishedUrl.trim(),
      })
      toast.success("Project marked as published")
      setPublishDialogOpen(false)
      setSelectedProjectId(null)
      setPublishedUrl("")
    } catch {
      toast.error("Failed to mark as published")
    }
  }

  const handleMoveToPublishing = async (projectId: string) => {
    try {
      await moveItem.mutateAsync({ itemId: projectId, status: "publishing" })
      toast.success("Moved to publishing")
    } catch {
      toast.error("Failed to move to publishing")
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Publishing Queue" description="Publish approved content to target sites" />
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Publishing Queue" description="Publish approved content to target sites" />

      {publishableProjects.length === 0 ? (
        <EmptyState
          icon={Globe}
          title="No Projects Ready"
          description="No approved projects are ready for publishing. Approve projects first via the approval queue."
        />
      ) : (
        <div className="space-y-3">
          {publishableProjects.map((project) => {
            const updatedDate = safeParseDate(project.updated_at)
            const isApproved = project.workflow_status === "approved"
            const isPublishing = project.workflow_status === "publishing"
            const isPublished = project.workflow_status === "published"

            return (
              <Card key={project.id}>
                <CardContent className="flex items-center gap-4 py-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="font-medium cursor-pointer hover:underline"
                        onClick={() => navigate(`/projects/${project.id}`)}
                      >
                        {project.name}
                      </span>
                      <StatusBadge status={project.workflow_status} />
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {project.developer}
                      {updatedDate && (
                        <> -- updated {formatDistanceToNow(updatedDate, { addSuffix: true })}</>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {project.sheet_url && isSafeExternalUrl(project.sheet_url) && (
                      <Button variant="outline" size="sm" asChild>
                        <a href={project.sheet_url} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="size-4 mr-1" />
                          Sheet
                        </a>
                      </Button>
                    )}

                    {isApproved && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleMoveToPublishing(project.id)}
                        disabled={moveItem.isPending}
                      >
                        <Send className="size-4 mr-1" />
                        Start Publishing
                      </Button>
                    )}

                    {isPublishing && (
                      <Button
                        size="sm"
                        onClick={() => {
                          setSelectedProjectId(project.id)
                          setPublishedUrl("")
                          setPublishDialogOpen(true)
                        }}
                      >
                        <Globe className="size-4 mr-1" />
                        Mark Published
                      </Button>
                    )}

                    {isPublished && project.published_url && isSafeExternalUrl(project.published_url) && (
                      <Button variant="outline" size="sm" asChild>
                        <a href={project.published_url} target="_blank" rel="noopener noreferrer">
                          <Globe className="size-4 mr-1" />
                          View Live
                        </a>
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Mark Published Dialog */}
      <Dialog open={publishDialogOpen} onOpenChange={setPublishDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Mark as Published</DialogTitle>
            <DialogDescription>
              Enter the URL where this project's content has been published.
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="https://example.com/project-page"
            value={publishedUrl}
            onChange={(e) => setPublishedUrl(e.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setPublishDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleMarkPublished}
              disabled={!publishedUrl.trim() || moveItem.isPending}
            >
              {moveItem.isPending ? "Saving..." : "Confirm Published"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
