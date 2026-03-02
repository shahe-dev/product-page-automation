import { formatDistanceToNow } from "date-fns"
import { Edit, Eye, MoreVertical, Trash2 } from "lucide-react"
import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { ConfirmDialog } from "@/components/common/ConfirmDialog"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import type { Project } from "@/types"

interface ProjectCardProps {
  project: Project
  onDelete?: (id: string) => void
  className?: string
}

export function ProjectCard({ project, onDelete, className }: ProjectCardProps) {
  const navigate = useNavigate()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleCardClick = () => {
    navigate(`/projects/${project.id}`)
  }

  const handleView = (e: Event) => {
    e.stopPropagation()
    navigate(`/projects/${project.id}`)
  }

  const handleEdit = (e: Event) => {
    e.stopPropagation()
    navigate(`/projects/${project.id}/edit`)
  }

  const handleDeleteClick = (e: Event) => {
    e.stopPropagation()
    setDeleteDialogOpen(true)
  }

  const handleConfirmDelete = async () => {
    if (!onDelete) return

    setIsDeleting(true)
    try {
      await onDelete(project.id)
      setDeleteDialogOpen(false)
    } finally {
      setIsDeleting(false)
    }
  }

  const getProjectInitials = (name: string) => {
    return name
      .split(" ")
      .map((word) => word[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  const relativeTime = (() => {
    try {
      const dateStr = project.updated_at || project.created_at
      if (!dateStr) return ""
      return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
    } catch {
      return ""
    }
  })()

  return (
    <>
      <Card
        className={cn(
          "group cursor-pointer transition-all hover:shadow-lg hover:border-primary/50",
          className
        )}
        onClick={handleCardClick}
      >
        <CardContent className="p-0">
          <div className="relative aspect-video overflow-hidden rounded-t-lg bg-muted">
            {project.thumbnail ? (
              <img
                src={project.thumbnail}
                alt={project.name}
                className="size-full object-cover"
              />
            ) : (
              <div className="flex size-full items-center justify-center bg-gradient-to-br from-primary/20 to-primary/5">
                <span className="text-4xl font-bold text-primary/40">
                  {getProjectInitials(project.name)}
                </span>
              </div>
            )}
            <div className="absolute top-2 right-2 z-10">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-8 bg-background/80 backdrop-blur-sm hover:bg-background"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="size-4" />
                    <span className="sr-only">Open menu</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onSelect={handleView}>
                    <Eye className="mr-2 size-4" />
                    View Details
                  </DropdownMenuItem>
                  <DropdownMenuItem onSelect={handleEdit}>
                    <Edit className="mr-2 size-4" />
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onSelect={handleDeleteClick}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="mr-2 size-4" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          <div className="space-y-3 p-4">
            <div className="space-y-1">
              <h3 className="font-semibold leading-tight truncate">
                {project.name}
              </h3>
              <p className="text-sm text-muted-foreground truncate">
                {project.developer}
              </p>
            </div>

            <div className="flex items-center justify-between gap-2">
              <StatusBadge status={project.workflow_status} />
              <span className="text-xs text-muted-foreground">
                {relativeTime}
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="truncate">{project.location}</span>
              <span>·</span>
              <span className="truncate">{project.emirate}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Project"
        description={`Are you sure you want to delete "${project.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleConfirmDelete}
        loading={isDeleting}
      />
    </>
  )
}
