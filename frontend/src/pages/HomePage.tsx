import { formatDistanceToNow } from "date-fns"
import {
  Activity,
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  ChevronRight,
  Clock,
  FileText,
  FolderKanban,
  FolderOpen,
  MessageSquare,
  Plus,
  Upload,
} from "lucide-react"
import { useNavigate } from "react-router-dom"

import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { PageHeader } from "@/components/common/PageHeader"
import { StatCard } from "@/components/common/StatCard"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { useDashboardStats, useRecentActivity } from "@/hooks"
import { safeParseDate } from "@/lib/utils"

export default function HomePage() {
  const navigate = useNavigate()

  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats()
  const { data: activities, isLoading: activitiesLoading } = useRecentActivity(5)

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "project_created":
        return FolderOpen
      case "project_updated":
        return FileText
      case "job_completed":
        return CheckCircle2
      case "approval_submitted":
        return MessageSquare
      default:
        return Activity
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Overview of your projects and recent activity"
      >
        <Button onClick={() => navigate("/processing")} className="gap-2">
          <Plus className="size-4" />
          New Project
        </Button>
      </PageHeader>

      {statsError && (
        <Alert variant="destructive">
          <AlertTriangle className="size-4" />
          <AlertTitle>Error loading dashboard stats</AlertTitle>
          <AlertDescription>
            {statsError instanceof Error
              ? statsError.message
              : "Failed to load dashboard statistics. Please try again."}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statsLoading ? (
          <>
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="flex items-center justify-center py-10">
                  <LoadingSpinner size="sm" />
                </CardContent>
              </Card>
            ))}
          </>
        ) : (
          <>
            <StatCard
              title="Total Projects"
              value={stats?.total_projects ?? 0}
              icon={FolderOpen}
              variant="default"
            />
            <StatCard
              title="Active Projects"
              value={stats?.active_projects ?? 0}
              icon={Activity}
              variant="success"
            />
            <StatCard
              title="Pending Approvals"
              value={stats?.pending_approvals ?? 0}
              icon={Clock}
              variant="warning"
            />
            <StatCard
              title="Failed Jobs"
              value={stats?.failed_jobs ?? 0}
              icon={AlertTriangle}
              variant="danger"
            />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {activitiesLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : !activities || activities.length === 0 ? (
              <div className="text-center py-8">
                <Activity className="mx-auto size-12 text-muted-foreground/50" />
                <p className="mt-4 text-sm text-muted-foreground">
                  No recent activity to display
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {activities.map((activity, index) => {
                  const Icon = getActivityIcon(activity.type)
                  const date = safeParseDate(activity.timestamp)
                  const relativeTime = date
                    ? formatDistanceToNow(date, { addSuffix: true })
                    : ""

                  return (
                    <div key={activity.id}>
                      {index > 0 && <Separator className="my-4" />}
                      <div className="flex gap-4">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                          <Icon className="size-5 text-primary" />
                        </div>
                        <div className="flex-1 space-y-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p className="font-medium leading-tight">
                              {activity.title}
                            </p>
                            <time className="text-xs text-muted-foreground whitespace-nowrap">
                              {relativeTime}
                            </time>
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {activity.description}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{activity.user_name}</span>
                            {activity.project_id && (
                              <>
                                <span>·</span>
                                <Button
                                  variant="link"
                                  size="sm"
                                  className="h-auto p-0 text-xs"
                                  onClick={() =>
                                    navigate(`/projects/${activity.project_id}`)
                                  }
                                >
                                  View Project
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Button
                variant="outline"
                className="w-full justify-between h-auto py-4"
                onClick={() => navigate("/processing")}
              >
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10">
                    <Upload className="size-5 text-primary" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Upload PDF</p>
                    <p className="text-xs text-muted-foreground">
                      Start a new project
                    </p>
                  </div>
                </div>
                <ChevronRight className="size-4 text-muted-foreground" />
              </Button>

              <Button
                variant="outline"
                className="w-full justify-between h-auto py-4"
                onClick={() => navigate("/projects")}
              >
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-blue-500/10">
                    <FolderKanban className="size-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">View Projects</p>
                    <p className="text-xs text-muted-foreground">
                      Browse all projects
                    </p>
                  </div>
                </div>
                <ChevronRight className="size-4 text-muted-foreground" />
              </Button>

              <Button
                variant="outline"
                className="w-full justify-between h-auto py-4"
                onClick={() => navigate("/approvals")}
              >
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-yellow-500/10">
                    <CheckCircle2 className="size-5 text-yellow-600 dark:text-yellow-400" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Approvals Queue</p>
                    <p className="text-xs text-muted-foreground">
                      Review pending content
                    </p>
                  </div>
                </div>
                <ChevronRight className="size-4 text-muted-foreground" />
              </Button>

              <Button
                variant="outline"
                className="w-full justify-between h-auto py-4"
                onClick={() => navigate("/prompts")}
              >
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-purple-500/10">
                    <Briefcase className="size-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Manage Prompts</p>
                    <p className="text-xs text-muted-foreground">
                      Configure AI prompts
                    </p>
                  </div>
                </div>
                <ChevronRight className="size-4 text-muted-foreground" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
