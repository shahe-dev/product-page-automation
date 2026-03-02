import { type DragEvent } from "react"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { Project } from "@/types"

import { WorkflowCard } from "./WorkflowCard"

interface StatusColumnProps {
  status: string
  label: string
  projects: Project[]
  color?: string
  onDrop?: (projectId: string, newStatus: string) => void
  onCardClick?: (project: Project) => void
  isDragOver?: boolean
  onDragOver?: (e: DragEvent<HTMLDivElement>) => void
  onDragLeave?: (e: DragEvent<HTMLDivElement>) => void
}

const colorClasses: Record<string, string> = {
  gray: "bg-gray-50 dark:bg-gray-950/50",
  blue: "bg-blue-50 dark:bg-blue-950/50",
  purple: "bg-purple-50 dark:bg-purple-950/50",
  yellow: "bg-yellow-50 dark:bg-yellow-950/50",
  green: "bg-green-50 dark:bg-green-950/50",
  emerald: "bg-emerald-50 dark:bg-emerald-950/50",
  red: "bg-red-50 dark:bg-red-950/50",
}

const borderColorClasses: Record<string, string> = {
  gray: "border-gray-200 dark:border-gray-800",
  blue: "border-blue-200 dark:border-blue-800",
  purple: "border-purple-200 dark:border-purple-800",
  yellow: "border-yellow-200 dark:border-yellow-800",
  green: "border-green-200 dark:border-green-800",
  emerald: "border-emerald-200 dark:border-emerald-800",
  red: "border-red-200 dark:border-red-800",
}

export function StatusColumn({
  status,
  label,
  projects,
  color = "gray",
  onDrop,
  onCardClick,
  isDragOver,
  onDragOver,
  onDragLeave,
}: StatusColumnProps) {
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const projectId = e.dataTransfer.getData("text/plain")
    if (projectId && onDrop) {
      onDrop(projectId, status)
    }
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = "move"
    if (onDragOver) {
      onDragOver(e)
    }
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    if (onDragLeave) {
      onDragLeave(e)
    }
  }

  return (
    <div
      className={cn(
        "flex flex-col min-w-[280px] max-w-[320px] border rounded-lg",
        colorClasses[color],
        borderColorClasses[color],
        "transition-colors duration-200"
      )}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <div className="flex items-center justify-between p-3 border-b">
        <h3 className="font-semibold text-sm">{label}</h3>
        <Badge variant="secondary" className="text-xs">
          {projects.length}
        </Badge>
      </div>

      <div
        className={cn(
          "flex-1 overflow-y-auto p-3 space-y-2",
          "max-h-[calc(100vh-280px)] min-h-[200px]",
          isDragOver && "ring-2 ring-primary ring-offset-2"
        )}
      >
        {projects.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
            No projects
          </div>
        ) : (
          projects.map((project) => (
            <WorkflowCard
              key={project.id}
              project={project}
              onClick={() => onCardClick?.(project)}
            />
          ))
        )}
      </div>
    </div>
  )
}
