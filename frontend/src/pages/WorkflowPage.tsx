import { LayoutGrid, List } from "lucide-react"
import { useState } from "react"

import { PageHeader } from "@/components/common/PageHeader"
import { Button } from "@/components/ui/button"
import { KanbanBoard } from "@/components/workflow"

type ViewMode = "kanban" | "list"

export default function WorkflowPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("kanban")

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflow"
        description="Track projects through the content pipeline"
      >
        <div className="inline-flex rounded-lg border bg-background p-1">
          <Button
            variant={viewMode === "kanban" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setViewMode("kanban")}
            className="gap-2"
          >
            <LayoutGrid className="size-4" />
            Kanban
          </Button>
          <Button
            variant={viewMode === "list" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setViewMode("list")}
            className="gap-2"
          >
            <List className="size-4" />
            List
          </Button>
        </div>
      </PageHeader>

      {viewMode === "kanban" ? (
        <KanbanBoard />
      ) : (
        <div className="flex items-center justify-center h-96 border border-dashed rounded-lg">
          <p className="text-muted-foreground">List view coming soon</p>
        </div>
      )}
    </div>
  )
}
