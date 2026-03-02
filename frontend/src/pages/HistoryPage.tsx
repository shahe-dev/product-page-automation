import { formatDistanceToNow } from "date-fns"
import {
  Activity,
  BarChart3,
  CheckCircle,
  Clock,
  FileText,
  XCircle,
} from "lucide-react"
import { useNavigate } from "react-router-dom"

import { EmptyState, LoadingSpinner, PageHeader } from "@/components/common"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { useActivityFeed } from "@/hooks/queries/use-activity"
import { safeParseDate } from "@/lib/utils"

function getActivityIcon(type: string) {
  if (type.includes("approved")) return CheckCircle
  if (type.includes("submitted")) return Clock
  if (type.includes("rejected")) return XCircle
  if (type.includes("completed")) return BarChart3
  if (type.includes("failed")) return XCircle
  return FileText
}

function getActivityColor(type: string) {
  if (type.includes("approved")) return "text-green-500"
  if (type.includes("submitted")) return "text-amber-500"
  if (type.includes("rejected")) return "text-red-500"
  if (type.includes("completed")) return "text-blue-500"
  if (type.includes("failed")) return "text-red-500"
  return "text-muted-foreground"
}

function getTypeBadge(type: string) {
  if (type.includes("approval")) return "Approval"
  if (type.includes("job")) return "Job"
  return "Activity"
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const { data, isLoading } = useActivityFeed()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="History" description="View project processing history" />
        <LoadingSpinner />
      </div>
    )
  }

  const items = data?.items ?? []

  return (
    <div className="space-y-6">
      <PageHeader title="History" description="View project processing history" />

      {items.length === 0 ? (
        <EmptyState
          icon={Activity}
          title="No History"
          description="No activity recorded yet. Processing projects will create history entries."
        />
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const Icon = getActivityIcon(item.type)
            const iconColor = getActivityColor(item.type)
            const date = safeParseDate(item.timestamp)

            return (
              <Card
                key={item.id}
                className={`transition-colors ${item.project_id ? "cursor-pointer hover:bg-muted/50" : ""}`}
                onClick={() => {
                  if (item.project_id) {
                    navigate(`/projects/${item.project_id}`)
                  }
                }}
              >
                <CardContent className="flex items-start gap-3 py-3">
                  <Icon className={`mt-0.5 size-5 shrink-0 ${iconColor}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{item.title}</span>
                      <Badge variant="outline" className="text-xs">
                        {getTypeBadge(item.type)}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground truncate">
                      {item.description}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-xs font-medium">{item.user_name}</div>
                    <div className="text-xs text-muted-foreground">
                      {date ? formatDistanceToNow(date, { addSuffix: true }) : ""}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
