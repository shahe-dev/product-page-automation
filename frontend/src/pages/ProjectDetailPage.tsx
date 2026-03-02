import { ArrowLeft } from "lucide-react"
import { useNavigate,useParams } from "react-router-dom"

import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ProjectDetail } from "@/components/projects/ProjectDetail"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { useProject } from "@/hooks"

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: project, isLoading, error } = useProject(id)

  if (!id) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertDescription>Invalid project ID</AlertDescription>
        </Alert>
        <Button variant="outline" onClick={() => navigate("/projects")}>
          <ArrowLeft className="size-4 mr-2" />
          Back to Projects
        </Button>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/projects")}
          >
            <ArrowLeft className="size-4" />
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Loading...</h1>
        </div>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/projects")}
          >
            <ArrowLeft className="size-4" />
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Project Not Found</h1>
        </div>
        <Alert variant="destructive">
          <AlertDescription>
            The project you are looking for does not exist or you do not have
            permission to view it.
          </AlertDescription>
        </Alert>
        <Button variant="outline" onClick={() => navigate("/projects")}>
          <ArrowLeft className="size-4 mr-2" />
          Back to Projects
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/projects")}
          className="hover:text-foreground"
        >
          Projects
        </Button>
        <span>/</span>
        <span className="text-foreground font-medium">{project.name}</span>
      </div>

      {/* Back Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate("/projects")}
        className="-ml-2"
      >
        <ArrowLeft className="size-4 mr-2" />
        Back to Projects
      </Button>

      {/* Project Detail Component */}
      <ProjectDetail projectId={id} />
    </div>
  )
}
