import { formatDistanceToNow } from "date-fns"
import {
  Activity,
  BarChart3,
  CheckCircle,
  Clock,
  FileText,
  Users,
} from "lucide-react"

import { EmptyState, LoadingSpinner, PageHeader } from "@/components/common"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useActivityFeed, useTeamStats } from "@/hooks/queries/use-activity"
import { useWorkflowStats } from "@/hooks"
import { safeParseDate } from "@/lib/utils"

export default function ManagerDashboardPage() {
  const { data: teamStats, isLoading: teamLoading } = useTeamStats()
  const { data: feedData, isLoading: feedLoading } = useActivityFeed()
  const { data: workflowStats } = useWorkflowStats()

  if (teamLoading || feedLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Manager Dashboard" description="Workflow metrics and team overview" />
        <LoadingSpinner />
      </div>
    )
  }

  const byStatus = workflowStats?.by_status ?? {}
  const pendingCount = byStatus["pending_approval"] ?? 0
  const approvedCount = byStatus["approved"] ?? 0
  const publishedCount = byStatus["published"] ?? 0

  return (
    <div className="space-y-6">
      <PageHeader title="Manager Dashboard" description="Workflow metrics and team overview" />

      {/* Workflow Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Projects</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{workflowStats?.total_projects ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pending Approval</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{pendingCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Approved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{approvedCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Published</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{publishedCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Team Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="size-5" />
            Team Activity (Last 7 Days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!teamStats || teamStats.length === 0 ? (
            <EmptyState icon={Users} title="No Team Data" description="No team activity recorded yet." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-3 font-medium">Name</th>
                    <th className="pb-3 font-medium">Projects</th>
                    <th className="pb-3 font-medium">Approvals</th>
                    <th className="pb-3 font-medium">Last Active</th>
                  </tr>
                </thead>
                <tbody>
                  {teamStats.map((stat) => {
                    const lastActive = safeParseDate(stat.last_active)
                    return (
                      <tr key={stat.user_id} className="border-b">
                        <td className="py-3">
                          <div className="font-medium">{stat.name}</div>
                          <div className="text-xs text-muted-foreground">{stat.email}</div>
                        </td>
                        <td className="py-3">
                          <Badge variant="secondary">{stat.projects_this_week}</Badge>
                        </td>
                        <td className="py-3">
                          <Badge variant="outline">{stat.approvals_this_week}</Badge>
                        </td>
                        <td className="py-3 text-muted-foreground">
                          {lastActive ? formatDistanceToNow(lastActive, { addSuffix: true }) : "Never"}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity Feed */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="size-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!feedData?.items || feedData.items.length === 0 ? (
            <EmptyState icon={Activity} title="No Activity" description="No recent activity to display." />
          ) : (
            <div className="space-y-3">
              {feedData.items.slice(0, 10).map((item) => {
                const date = safeParseDate(item.timestamp)
                return (
                  <div key={item.id} className="flex items-start gap-3 rounded-lg border p-3">
                    <div className="mt-0.5">
                      {item.type.includes("approved") ? (
                        <CheckCircle className="size-4 text-green-500" />
                      ) : item.type.includes("submitted") ? (
                        <Clock className="size-4 text-amber-500" />
                      ) : item.type.includes("completed") ? (
                        <BarChart3 className="size-4 text-blue-500" />
                      ) : (
                        <FileText className="size-4 text-muted-foreground" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{item.title}</div>
                      <div className="text-xs text-muted-foreground truncate">
                        {item.description}
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground whitespace-nowrap">
                      <div>{item.user_name}</div>
                      {date && <div>{formatDistanceToNow(date, { addSuffix: true })}</div>}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
