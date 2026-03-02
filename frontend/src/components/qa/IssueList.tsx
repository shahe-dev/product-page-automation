import { AlertCircle, CheckCircle2, Filter, X } from "lucide-react"
import { useState } from "react"

import { ConfirmDialog } from "@/components/common"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import type { QAIssue } from "@/types"

// Re-export for consumers that imported from here
export type { QAIssue }

interface IssueListProps {
  issues: QAIssue[]
  onIssueClick?: (issue: QAIssue) => void
  onStatusChange?: (id: string, status: "open" | "resolved" | "dismissed") => void
  onBulkAction?: (action: string, ids: string[]) => void
}

const issueTypeColors = {
  factual: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300",
  compliance: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300",
  consistency: "bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-950 dark:text-purple-300",
  quality: "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300",
}

const severityColors = {
  critical: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300",
  major: "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950 dark:text-orange-300",
  minor: "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300",
}

export function IssueList({
  issues,
  onIssueClick,
  onStatusChange,
  onBulkAction,
}: IssueListProps) {
  const [typeFilter, setTypeFilter] = useState<string>("all")
  const [severityFilter, setSeverityFilter] = useState<string>("all")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false)
  const [bulkActionType, setBulkActionType] = useState<"resolve" | "dismiss">("resolve")

  const filteredIssues = issues
    .filter((issue) => typeFilter === "all" || issue.type === typeFilter)
    .filter((issue) => severityFilter === "all" || issue.severity === severityFilter)
    .filter((issue) => statusFilter === "all" || issue.status === statusFilter)
    .sort((a, b) => {
      const severityOrder = { critical: 0, major: 1, minor: 2 }
      return severityOrder[a.severity] - severityOrder[b.severity]
    })

  const openIssues = filteredIssues.filter((i) => i.status === "open")

  const handleBulkResolve = () => {
    setBulkActionType("resolve")
    setConfirmDialogOpen(true)
  }

  const handleBulkDismiss = () => {
    setBulkActionType("dismiss")
    setConfirmDialogOpen(true)
  }

  const confirmBulkAction = () => {
    if (onBulkAction) {
      const openIssueIds = openIssues.map((i) => i.id)
      onBulkAction(bulkActionType, openIssueIds)
    }
    setConfirmDialogOpen(false)
  }

  const countByType = (type: QAIssue["type"]) =>
    issues.filter((i) => i.type === type && i.status === "open").length

  const countBySeverity = (severity: QAIssue["severity"]) =>
    issues.filter((i) => i.severity === severity && i.status === "open").length

  return (
    <>
      <Card className="flex h-full flex-col">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Issues</span>
            <Badge variant="outline" className="ml-2">
              {openIssues.length} open
            </Badge>
          </CardTitle>
          <div className="mt-4 space-y-2">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Critical:</span>
                  <span className="font-semibold text-red-600">
                    {countBySeverity("critical")}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Major:</span>
                  <span className="font-semibold text-orange-600">
                    {countBySeverity("major")}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Minor:</span>
                  <span className="font-semibold text-yellow-600">
                    {countBySeverity("minor")}
                  </span>
                </div>
              </div>
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Factual:</span>
                  <span className="font-semibold">{countByType("factual")}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Compliance:</span>
                  <span className="font-semibold">{countByType("compliance")}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Quality:</span>
                  <span className="font-semibold">{countByType("quality")}</span>
                </div>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex flex-1 flex-col gap-4 overflow-hidden">
          {/* Filters */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Filter className="size-4" />
              <span>Filters</span>
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="factual">Factual</SelectItem>
                <SelectItem value="compliance">Compliance</SelectItem>
                <SelectItem value="consistency">Consistency</SelectItem>
                <SelectItem value="quality">Quality</SelectItem>
              </SelectContent>
            </Select>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="major">Major</SelectItem>
                <SelectItem value="minor">Minor</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="dismissed">Dismissed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Bulk Actions */}
          {openIssues.length > 0 && (
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                className="flex-1"
                onClick={handleBulkResolve}
              >
                <CheckCircle2 className="mr-2 size-4" />
                Resolve All
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="flex-1"
                onClick={handleBulkDismiss}
              >
                <X className="mr-2 size-4" />
                Dismiss All
              </Button>
            </div>
          )}

          {/* Issue List */}
          <div className="flex-1 space-y-2 overflow-y-auto">
            {filteredIssues.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
                <CheckCircle2 className="size-8 text-green-600" />
                <p className="text-sm text-muted-foreground">No issues found</p>
              </div>
            ) : (
              filteredIssues.map((issue) => (
                <button
                  key={issue.id}
                  onClick={() => onIssueClick?.(issue)}
                  className={cn(
                    "w-full rounded-md border p-3 text-left transition-colors hover:bg-muted",
                    issue.status !== "open" && "opacity-60"
                  )}
                >
                  <div className="flex items-start gap-2">
                    <AlertCircle
                      className={cn(
                        "mt-0.5 size-4 shrink-0",
                        issue.severity === "critical" && "text-red-600",
                        issue.severity === "major" && "text-orange-600",
                        issue.severity === "minor" && "text-yellow-600"
                      )}
                    />
                    <div className="flex-1 space-y-2">
                      <div className="flex flex-wrap gap-1">
                        <Badge variant="outline" className={issueTypeColors[issue.type]}>
                          {issue.type}
                        </Badge>
                        <Badge variant="outline" className={severityColors[issue.severity]}>
                          {issue.severity}
                        </Badge>
                      </div>
                      <div>
                        <div className="text-xs font-medium text-muted-foreground">
                          {issue.field}
                        </div>
                        <p className="mt-1 text-sm">{issue.description}</p>
                      </div>
                      {issue.status !== "open" && (
                        <Badge variant="outline" className="text-xs">
                          {issue.status}
                        </Badge>
                      )}
                    </div>
                  </div>
                  {onStatusChange && issue.status === "open" && (
                    <div className="mt-2 flex gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          onStatusChange(issue.id, "resolved")
                        }}
                      >
                        Resolve
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          onStatusChange(issue.id, "dismissed")
                        }}
                      >
                        Dismiss
                      </Button>
                    </div>
                  )}
                </button>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={confirmDialogOpen}
        onOpenChange={setConfirmDialogOpen}
        title={`${bulkActionType === "resolve" ? "Resolve" : "Dismiss"} All Issues`}
        description={`Are you sure you want to ${bulkActionType} all ${openIssues.length} open issues?`}
        confirmLabel={bulkActionType === "resolve" ? "Resolve All" : "Dismiss All"}
        onConfirm={confirmBulkAction}
      />
    </>
  )
}
