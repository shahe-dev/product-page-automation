import { formatDistanceToNow } from "date-fns"
import { GripVertical,MoreVertical } from "lucide-react"
import { type DragEvent } from "react"

import { StatusBadge } from "@/components/common/StatusBadge"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn, safeParseDate } from "@/lib/utils"
import type { Project } from "@/types"

interface WorkflowCardProps {
  project: Project
  onDragStart?: (e: DragEvent<HTMLDivElement>, project: Project) => void
  onClick?: () => void
}

const templateLabels: Record<string, string> = {
  aggregators: "Aggregators",
  opr: "OPR",
  mpp: "MPP",
  adop: "ADOP",
  adre: "ADRE",
  commercial: "Commercial",
}

export function WorkflowCard({ project, onDragStart, onClick }: WorkflowCardProps) {
  const handleDragStart = (e: DragEvent<HTMLDivElement>) => {
    e.dataTransfer.effectAllowed = "move"
    e.dataTransfer.setData("text/plain", project.id)
    if (onDragStart) {
      onDragStart(e, project)
    }
  }

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onClick={onClick}
      className={cn(
        "group relative bg-card border rounded-lg p-3 cursor-pointer",
        "hover:shadow-md hover:border-primary/50 transition-all duration-200",
        "active:opacity-50"
      )}
    >
      <div className="flex items-start gap-2">
        <GripVertical className="size-4 text-muted-foreground mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />

        <div className="flex-1 min-w-0 space-y-2">
          <div className="space-y-1">
            <h4 className="font-semibold text-sm line-clamp-1">{project.name}</h4>
            <p className="text-xs text-muted-foreground line-clamp-1">{project.developer}</p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <StatusBadge status={project.workflow_status} className="text-xs" />
            <Badge variant="secondary" className="text-xs">
              {templateLabels[project.template_type] || project.template_type}
            </Badge>
          </div>

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{(() => {
              const date = safeParseDate(project.updated_at) || safeParseDate(project.created_at)
              return date ? formatDistanceToNow(date, { addSuffix: true }) : ""
            })()}</span>
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="sm" className="size-6 p-0">
              <MoreVertical className="size-4" />
              <span className="sr-only">Open menu</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={(e) => {
              e.stopPropagation()
              onClick?.()
            }}>
              View Details
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => e.stopPropagation()}>
              Move to Next Stage
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => e.stopPropagation()}>
              Assign
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}
