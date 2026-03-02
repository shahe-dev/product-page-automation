import { formatDistanceToNow } from "date-fns"
import { AlertTriangle, Check, Clock, FileText, X } from "lucide-react"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { EmptyState, LoadingSpinner, PageHeader } from "@/components/common"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
import { useApprovalQueue, useApproveProject, useRejectProject } from "@/hooks"
import { safeParseDate } from "@/lib/utils"
import type { Approval } from "@/types"

type StatusFilter = "all" | "pending" | "approved" | "rejected"

const STATUS_BADGE_CONFIG: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
  pending: { variant: "secondary", label: "Pending Review" },
  approved: { variant: "default", label: "Approved" },
  rejected: { variant: "destructive", label: "Rejected" },
}

export default function ApprovalQueuePage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false)
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null)
  const [rejectionReason, setRejectionReason] = useState("")

  const { data: approvals, isLoading, isError, error } = useApprovalQueue(
    statusFilter === "all" ? undefined : { status: statusFilter }
  )
  const approveProject = useApproveProject()
  const rejectProject = useRejectProject()

  const handleApprove = async (approval: Approval) => {
    try {
      await approveProject.mutateAsync(approval.project_id)
      toast.success(`Project "${approval.project_name}" approved`)
    } catch (err) {
      toast.error("Failed to approve project")
      console.error(err)
    }
  }

  const handleOpenRejectDialog = (approval: Approval) => {
    setSelectedApproval(approval)
    setRejectionReason("")
    setRejectDialogOpen(true)
  }

  const handleReject = async () => {
    if (!selectedApproval || !rejectionReason.trim()) {
      toast.error("Please provide a rejection reason")
      return
    }

    try {
      await rejectProject.mutateAsync({
        id: selectedApproval.project_id,
        reason: rejectionReason,
      })
      toast.success(`Project "${selectedApproval.project_name}" rejected`)
      setRejectDialogOpen(false)
      setSelectedApproval(null)
      setRejectionReason("")
    } catch (err) {
      toast.error("Failed to reject project")
      console.error(err)
    }
  }

  const pendingCount = approvals?.filter((a) => a.status === "pending").length ?? 0

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Approvals"
          description="Review and approve project content"
        />
        <LoadingSpinner />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Approvals"
          description="Review and approve project content"
        />
        <Alert variant="destructive">
          <AlertTriangle className="size-4" />
          <AlertTitle>Failed to load approvals</AlertTitle>
          <AlertDescription>
            {error instanceof Error ? error.message : "An unexpected error occurred. Please try again."}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approvals"
        description="Review and approve project content"
      >
        <div className="flex items-center gap-4">
          {pendingCount > 0 && (
            <Badge variant="secondary" className="text-sm">
              {pendingCount} pending
            </Badge>
          )}
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as StatusFilter)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </PageHeader>

      {!approvals || approvals.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No Approvals"
          description={
            statusFilter === "all"
              ? "No projects have been submitted for approval yet."
              : `No ${statusFilter} approvals found.`
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {approvals.map((approval) => {
            const date = safeParseDate(approval.submitted_at)
            const relativeTime = date
              ? formatDistanceToNow(date, { addSuffix: true })
              : ""
            const statusConfig = STATUS_BADGE_CONFIG[approval.status] ?? STATUS_BADGE_CONFIG.pending

            return (
              <Card key={approval.id} className="flex flex-col">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-lg line-clamp-1">
                      {approval.project_name}
                    </CardTitle>
                    <Badge variant={statusConfig.variant}>
                      {statusConfig.label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 space-y-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Clock className="size-4" />
                      <span>Submitted {relativeTime}</span>
                    </div>
                    <div className="text-muted-foreground">
                      By: {approval.submitted_by}
                    </div>
                  </div>

                  <div className="flex gap-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => navigate(`/projects/${approval.project_id}`)}
                    >
                      View Project
                    </Button>
                    {approval.status === "pending" && (
                      <>
                        <Button
                          variant="default"
                          size="sm"
                          className="bg-green-600 hover:bg-green-700"
                          onClick={() => handleApprove(approval)}
                          disabled={approveProject.isPending}
                        >
                          <Check className="size-4" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleOpenRejectDialog(approval)}
                          disabled={rejectProject.isPending}
                        >
                          <X className="size-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Project</DialogTitle>
            <DialogDescription>
              Please provide a reason for rejecting "{selectedApproval?.project_name}".
              This will be sent to the content team.
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
                setSelectedApproval(null)
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
