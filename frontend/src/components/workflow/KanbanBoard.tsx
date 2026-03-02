import { AlertCircle } from "lucide-react"
import { useMemo,useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/common/ConfirmDialog"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { SearchBar } from "@/components/common/SearchBar"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useProjects, useUpdateProject } from "@/hooks/queries/use-projects"
import type { Project, ProjectStatus } from "@/types"

import { StatusColumn } from "./StatusColumn"

interface Column {
  key: string
  label: string
  statuses: ProjectStatus[]
  color: string
}

const COLUMNS: Column[] = [
  { key: "draft", label: "Draft", statuses: ["draft"], color: "gray" },
  { key: "pending_approval", label: "Pending Approval", statuses: ["pending_approval"], color: "yellow" },
  { key: "approved", label: "Approved", statuses: ["approved"], color: "green" },
  { key: "revision_requested", label: "Revision Requested", statuses: ["revision_requested"], color: "orange" },
  { key: "publishing", label: "Publishing", statuses: ["publishing"], color: "blue" },
  { key: "published", label: "Published", statuses: ["published"], color: "emerald" },
  { key: "qa_verified", label: "QA Verified", statuses: ["qa_verified"], color: "teal" },
  { key: "complete", label: "Complete", statuses: ["complete"], color: "emerald" },
]

const VALID_TRANSITIONS: Record<string, ProjectStatus[]> = {
  draft: ["pending_approval"],
  pending_approval: ["approved", "revision_requested"],
  approved: ["publishing"],
  revision_requested: ["draft"],
  publishing: ["published"],
  published: ["qa_verified"],
  qa_verified: ["complete"],
  complete: [],
}

export function KanbanBoard() {
  const navigate = useNavigate()
  const [search, setSearch] = useState("")
  const [templateFilter, setTemplateFilter] = useState<string>("all")
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null)
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean
    projectId: string
    projectName: string
    fromStatus: ProjectStatus
    toStatus: ProjectStatus
  } | null>(null)

  const { data, isLoading, error, refetch } = useProjects({
    per_page: 1000,
  })
  const updateProject = useUpdateProject()

  const projects = useMemo(() => data?.items || [], [data])

  const filteredProjects = useMemo(() => {
    return projects.filter((project) => {
      const matchesSearch =
        search === "" ||
        project.name.toLowerCase().includes(search.toLowerCase()) ||
        (project.developer?.toLowerCase().includes(search.toLowerCase()) ?? false)
      const matchesTemplate = templateFilter === "all" || project.template_type === templateFilter
      return matchesSearch && matchesTemplate
    })
  }, [projects, search, templateFilter])

  const groupedProjects = useMemo(() => {
    const grouped = COLUMNS.reduce((acc, column) => {
      acc[column.key] = filteredProjects.filter((p) =>
        column.statuses.includes(p.workflow_status)
      )
      return acc
    }, {} as Record<string, Project[]>)
    return grouped
  }, [filteredProjects])

  const handleDrop = (projectId: string, targetColumnKey: string) => {
    const project = projects.find((p) => p.id === projectId)
    if (!project) return

    const targetColumn = COLUMNS.find((c) => c.key === targetColumnKey)
    if (!targetColumn) return

    const targetStatus = targetColumn.statuses[0]

    if (project.workflow_status === targetStatus) return

    const allowedTransitions = VALID_TRANSITIONS[project.workflow_status] || []
    if (!allowedTransitions.includes(targetStatus)) {
      toast.error(`Cannot move from ${project.workflow_status} to ${targetStatus}. Invalid transition.`)
      return
    }

    setConfirmDialog({
      open: true,
      projectId: project.id,
      projectName: project.name,
      fromStatus: project.workflow_status,
      toStatus: targetStatus,
    })
  }

  const handleConfirmMove = () => {
    if (!confirmDialog) return

    updateProject.mutate(
      {
        id: confirmDialog.projectId,
        data: { workflow_status: confirmDialog.toStatus },
      },
      {
        onSuccess: () => {
          setConfirmDialog(null)
        },
        onError: (error) => {
          console.error("Failed to update project:", error)
          toast.error("Failed to update project status. Please try again.")
        },
      }
    )
  }

  const handleCardClick = (project: Project) => {
    navigate(`/projects/${project.id}`)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="size-4" />
        <AlertDescription className="flex items-center justify-between">
          <span>Failed to load projects. Please try again.</span>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-4">
        <SearchBar
          value={search}
          onChange={setSearch}
          placeholder="Search projects..."
          className="flex-1"
        />
        <Select value={templateFilter} onValueChange={setTemplateFilter}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Template type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Templates</SelectItem>
            <SelectItem value="aggregators">Aggregators</SelectItem>
            <SelectItem value="opr">OPR</SelectItem>
            <SelectItem value="mpp">MPP</SelectItem>
            <SelectItem value="adop">ADOP</SelectItem>
            <SelectItem value="adre">ADRE</SelectItem>
            <SelectItem value="commercial">Commercial</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>Total: {filteredProjects.length} projects</span>
      </div>

      <div className="overflow-x-auto pb-4">
        <div className="flex gap-4 min-w-max">
          {COLUMNS.map((column) => (
            <StatusColumn
              key={column.key}
              status={column.key}
              label={column.label}
              projects={groupedProjects[column.key] || []}
              color={column.color}
              onDrop={handleDrop}
              onCardClick={handleCardClick}
              isDragOver={dragOverColumn === column.key}
              onDragOver={() => setDragOverColumn(column.key)}
              onDragLeave={() => setDragOverColumn(null)}
            />
          ))}
        </div>
      </div>

      {confirmDialog && (
        <ConfirmDialog
          open={confirmDialog.open}
          onOpenChange={(open) => !open && setConfirmDialog(null)}
          title="Confirm Status Change"
          description={`Move "${confirmDialog.projectName}" from ${confirmDialog.fromStatus} to ${confirmDialog.toStatus}?`}
          confirmLabel="Move"
          onConfirm={handleConfirmMove}
          loading={updateProject.isPending}
        />
      )}
    </div>
  )
}
