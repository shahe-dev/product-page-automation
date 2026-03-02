import { AlertTriangle, CheckCircle, FileText, XCircle } from "lucide-react"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { EmptyState, LoadingSpinner, PageHeader } from "@/components/common"
import type { QAIssue } from "@/components/qa"
import { ComparisonView, IssueList, ScoreDisplay } from "@/components/qa"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useProjects, useRejectProject, useSubmitForApproval } from "@/hooks"

// Mock data structure -- only used during development.
// In production builds, this returns null so components fall through to real API data.
const generateMockQAData = (_projectId: string) => {
  if (!import.meta.env.DEV) return null;
  const mockSourceData = {
    project_name: "Marina Heights Tower",
    developer: "Emaar Properties",
    location: "Dubai Marina",
    description: "A luxury residential tower offering stunning views of the marina and Arabian Gulf. Features world-class amenities including infinity pool, gym, and spa.",
    bedrooms: "1, 2, 3 bedroom apartments",
    price_range: "Starting from AED 1.5M",
    completion_date: "Q4 2024",
    features: "Infinity pool, Gym, Spa, Children's play area, 24/7 security",
  }

  const mockGeneratedData = {
    project_name: "Marina Heights Tower",
    developer: "Emaar Properties PJSC",
    location: "Dubai Marina, Dubai",
    description: "Marina Heights Tower is an ultra-luxury residential development featuring breathtaking panoramic views of the marina and the Arabian Sea. The tower boasts premium amenities including an infinity-edge swimming pool, state-of-the-art fitness center, and luxury spa facilities.",
    bedrooms: "1-bedroom, 2-bedroom, and 3-bedroom apartments",
    price_range: "Starting from AED 1.5 million",
    completion_date: "Q4 2024",
    features: "Infinity-edge pool, State-of-the-art gym, Luxury spa, Children's play area, 24/7 security and concierge",
  }

  const mockIssues: QAIssue[] = [
    {
      id: "1",
      field: "developer",
      type: "factual",
      severity: "minor",
      description: "Developer name expanded with legal entity designation (PJSC). Verify if full legal name is required or simplified version is preferred.",
      source_value: "Emaar Properties",
      generated_value: "Emaar Properties PJSC",
      status: "open",
    },
    {
      id: "2",
      field: "description",
      type: "quality",
      severity: "minor",
      description: "Description uses 'Arabian Sea' instead of 'Arabian Gulf'. Verify geographical terminology preference for consistency.",
      source_value: "Arabian Gulf",
      generated_value: "Arabian Sea",
      status: "open",
    },
    {
      id: "3",
      field: "features",
      type: "consistency",
      severity: "minor",
      description: "Added 'concierge' service not mentioned in source data. Verify if this is a standard amenity or requires source confirmation.",
      status: "open",
    },
  ]

  return {
    sourceData: mockSourceData,
    generatedData: mockGeneratedData,
    issues: mockIssues,
    overallScore: 92,
    fieldScores: {
      project_name: 100,
      developer: 95,
      location: 100,
      description: 90,
      bedrooms: 98,
      price_range: 100,
      completion_date: 100,
      features: 88,
    },
  }
}

export default function QAPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false)
  const [rejectionReason, setRejectionReason] = useState("")
  const [issuesState, setIssuesState] = useState<QAIssue[]>([])
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  const { data: projectsResponse, isLoading: isLoadingProjects } = useProjects({
    status: undefined,
  })
  const rejectProject = useRejectProject()
  const submitForApproval = useSubmitForApproval()

  // Filter projects that are ready for QA review
  const reviewableProjects =
    projectsResponse?.items.filter(
      (p) => p.workflow_status === "pending_approval" || p.workflow_status === "approved" || p.workflow_status === "qa_verified"
    ) || []

  // Get QA data for selected project
  const qaData = selectedProjectId ? generateMockQAData(selectedProjectId) : null

  // Initialize issues when project is selected (via useEffect to avoid setState during render)
  useEffect(() => {
    if (qaData && issuesState.length === 0 && selectedProjectId) {
      setIssuesState(qaData.issues)
    }
  }, [qaData, issuesState.length, selectedProjectId])

  // Reset issues when project changes
  const handleProjectChange = (projectId: string) => {
    setSelectedProjectId(projectId)
    setIssuesState([])
  }

  const handleIssueStatusChange = (id: string, status: "open" | "resolved" | "dismissed") => {
    setIssuesState((prev) =>
      prev.map((issue) => (issue.id === id ? { ...issue, status } : issue))
    )
  }

  const handleBulkAction = (action: string, ids: string[]) => {
    const newStatus = action === "resolve" ? "resolved" : "dismissed"
    setIssuesState((prev) =>
      prev.map((issue) =>
        ids.includes(issue.id) ? { ...issue, status: newStatus } : issue
      )
    )
    toast.success(`${ids.length} issues ${newStatus}`)
  }

  const handleApprove = async () => {
    if (!selectedProjectId) return

    try {
      await submitForApproval.mutateAsync(selectedProjectId)
      toast.success("Project approved successfully")
      setSelectedProjectId(null)
      setIssuesState([])
    } catch (error) {
      toast.error("Failed to approve project")
      console.error(error)
    }
  }

  const handleReject = async () => {
    if (!selectedProjectId || !rejectionReason.trim()) {
      toast.error("Please provide a rejection reason")
      return
    }

    try {
      await rejectProject.mutateAsync({
        id: selectedProjectId,
        reason: rejectionReason,
      })
      toast.success("Project rejected")
      setRejectDialogOpen(false)
      setRejectionReason("")
      setSelectedProjectId(null)
      setIssuesState([])
    } catch (error) {
      toast.error("Failed to reject project")
      console.error(error)
    }
  }

  const openIssuesCount = issuesState.filter((i) => i.status === "open").length
  const criticalIssuesCount = issuesState.filter(
    (i) => i.status === "open" && i.severity === "critical"
  ).length

  if (isLoadingProjects) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Content QA Review"
          description="Review and validate AI-generated content"
        />
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Content QA Review"
        description="Review and validate AI-generated content"
      >
        <Select value={selectedProjectId || ""} onValueChange={handleProjectChange}>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Select a project to review" />
          </SelectTrigger>
          <SelectContent>
            {reviewableProjects.length === 0 && (
              <div className="px-2 py-3 text-center text-sm text-muted-foreground">
                No projects ready for review
              </div>
            )}
            {reviewableProjects.map((project) => (
              <SelectItem key={project.id} value={project.id}>
                {project.name} - {project.developer}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </PageHeader>

      {!selectedProjectId && (
        <EmptyState
          icon={FileText}
          title="No Project Selected"
          description="Select a project from the dropdown above to begin QA review. Only projects with generated content are available for review."
        />
      )}

      {selectedProjectId && qaData && (
        <>
          {/* QA Score */}
          <ScoreDisplay
            overallScore={qaData.overallScore}
            fieldScores={qaData.fieldScores}
          />

          {/* Critical Issues Alert */}
          {criticalIssuesCount > 0 && (
            <Alert variant="destructive">
              <AlertTriangle className="size-4" />
              <AlertDescription>
                {criticalIssuesCount} critical issue{criticalIssuesCount > 1 ? "s" : ""}{" "}
                must be resolved before approval
              </AlertDescription>
            </Alert>
          )}

          {/* Main Content Area */}
          <div className="flex gap-6">
            {/* Comparison View */}
            <div className="flex-1">
              <ComparisonView
                sourceData={qaData.sourceData}
                generatedData={qaData.generatedData}
                issues={issuesState}
                onIssueClick={(issue) => {
                  // Scroll to issue or highlight it
                  toast.info(`Issue in ${issue.field}: ${issue.description}`)
                }}
              />
            </div>

            {/* Issue List Sidebar */}
            {!isSidebarCollapsed && (
              <div className="w-[400px] shrink-0">
                <IssueList
                  issues={issuesState}
                  onIssueClick={(issue) => {
                    toast.info(`Issue in ${issue.field}: ${issue.description}`)
                  }}
                  onStatusChange={handleIssueStatusChange}
                  onBulkAction={handleBulkAction}
                />
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between rounded-lg border bg-card p-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              >
                {isSidebarCollapsed ? "Show Issues" : "Hide Issues"}
              </Button>
              <div className="text-sm text-muted-foreground">
                {openIssuesCount} open issue{openIssuesCount !== 1 ? "s" : ""}
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="destructive"
                onClick={() => setRejectDialogOpen(true)}
                disabled={rejectProject.isPending}
              >
                <XCircle className="mr-2 size-4" />
                Reject
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  toast.info("Request changes feature coming soon")
                }}
              >
                <AlertTriangle className="mr-2 size-4" />
                Request Changes
              </Button>
              <Button
                onClick={handleApprove}
                disabled={criticalIssuesCount > 0 || submitForApproval.isPending}
                className="bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="mr-2 size-4" />
                Approve
              </Button>
            </div>
          </div>
        </>
      )}

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Project</DialogTitle>
            <DialogDescription>
              Please provide a reason for rejecting this project. This will be sent to the
              content team.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            placeholder="Enter rejection reason..."
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            rows={4}
          />
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setRejectDialogOpen(false)
                setRejectionReason("")
              }}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={!rejectionReason.trim() || rejectProject.isPending}
            >
              {rejectProject.isPending ? "Rejecting..." : "Reject Project"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
