import { Plus } from "lucide-react"
import { useNavigate } from "react-router-dom"

import { PageHeader } from "@/components/common/PageHeader"
import { ProjectFilters } from "@/components/projects/ProjectFilters"
import { ProjectList } from "@/components/projects/ProjectList"
import { Button } from "@/components/ui/button"

export default function ProjectsListPage() {
  const navigate = useNavigate()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Projects"
        description="Browse and manage all your projects"
      >
        <Button onClick={() => navigate("/processing")} className="gap-2">
          <Plus className="size-4" />
          New Project
        </Button>
      </PageHeader>

      <ProjectFilters />

      <ProjectList />
    </div>
  )
}
