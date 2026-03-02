import { ChevronLeft, ChevronRight,FolderOpen } from "lucide-react"
import { useNavigate } from "react-router-dom"

import { EmptyState } from "@/components/common/EmptyState"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { useDeleteProject,useProjects } from "@/hooks"
import { useFilterStore } from "@/stores/filter-store"

import { ProjectCard } from "./ProjectCard"

export function ProjectList() {
  const navigate = useNavigate()
  const { projectFilters, setProjectFilters } = useFilterStore()

  const { data, isLoading, error, refetch } = useProjects({
    ...projectFilters,
    page: projectFilters.page || 1,
    per_page: projectFilters.per_page || 12,
  })

  const deleteProject = useDeleteProject()

  const handleDelete = async (id: string) => {
    await deleteProject.mutateAsync(id)
  }

  const handlePageChange = (newPage: number) => {
    setProjectFilters({ page: newPage })
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="overflow-hidden">
              <CardContent className="p-0">
                <div className="aspect-video bg-muted animate-pulse" />
                <div className="space-y-3 p-4">
                  <div className="space-y-2">
                    <div className="h-5 bg-muted rounded animate-pulse" />
                    <div className="h-4 bg-muted rounded w-2/3 animate-pulse" />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="h-6 bg-muted rounded w-20 animate-pulse" />
                    <div className="h-4 bg-muted rounded w-16 animate-pulse" />
                  </div>
                  <div className="h-4 bg-muted rounded w-3/4 animate-pulse" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error loading projects</AlertTitle>
        <AlertDescription className="flex items-center justify-between">
          <span>
            {error instanceof Error
              ? error.message
              : "Failed to load projects. Please try again."}
          </span>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        icon={FolderOpen}
        title="No projects found"
        description={
          projectFilters.search || projectFilters.status || projectFilters.emirate
            ? "Try adjusting your filters to see more results."
            : "Get started by uploading your first PDF to create a project."
        }
        action={
          <Button onClick={() => navigate("/processing")}>Upload PDF</Button>
        }
      />
    )
  }

  const { items: projects, page, total, has_next } = data
  const totalPages = Math.ceil(total / (projectFilters.per_page || 12))

  return (
    <div className="space-y-6">
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <ProjectCard
            key={project.id}
            project={project}
            onDelete={handleDelete}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {page} of {totalPages} ({total} total projects)
          </p>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
            >
              <ChevronLeft className="size-4 mr-1" />
              Previous
            </Button>

            <div className="hidden sm:flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNumber: number
                if (totalPages <= 5) {
                  pageNumber = i + 1
                } else if (page <= 3) {
                  pageNumber = i + 1
                } else if (page >= totalPages - 2) {
                  pageNumber = totalPages - 4 + i
                } else {
                  pageNumber = page - 2 + i
                }

                return (
                  <Button
                    key={pageNumber}
                    variant={page === pageNumber ? "default" : "outline"}
                    size="sm"
                    className="size-9 p-0"
                    onClick={() => handlePageChange(pageNumber)}
                  >
                    {pageNumber}
                  </Button>
                )
              })}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(page + 1)}
              disabled={!has_next}
            >
              Next
              <ChevronRight className="size-4 ml-1" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
