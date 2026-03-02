import { formatDistanceToNow } from "date-fns"
import {
  AlertTriangle,
  Bell,
  Check,
  CheckCheck,
  Info,
  ShieldAlert,
  XCircle,
} from "lucide-react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { EmptyState, LoadingSpinner, PageHeader } from "@/components/common"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  useMarkAllAsRead,
  useMarkAsRead,
  useNotifications,
  useUnreadCount,
} from "@/hooks/queries/use-notifications"
import { safeParseDate } from "@/lib/utils"

const TYPE_ICONS: Record<string, typeof Info> = {
  info: Info,
  success: Check,
  warning: AlertTriangle,
  error: XCircle,
  approval: ShieldAlert,
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const { data, isLoading } = useNotifications()
  const { data: unreadCount } = useUnreadCount()
  const markRead = useMarkAsRead()
  const markAllRead = useMarkAllAsRead()

  const handleMarkAllRead = async () => {
    try {
      await markAllRead.mutateAsync()
      toast.success("All notifications marked as read")
    } catch {
      toast.error("Failed to mark all as read")
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Notifications" description="Stay updated on project activity" />
        <LoadingSpinner />
      </div>
    )
  }

  const items = data?.items ?? []

  return (
    <div className="space-y-6">
      <PageHeader title="Notifications" description="Stay updated on project activity">
        <div className="flex items-center gap-3">
          {(unreadCount ?? 0) > 0 && (
            <Badge variant="secondary">{unreadCount} unread</Badge>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleMarkAllRead}
            disabled={!unreadCount || markAllRead.isPending}
          >
            <CheckCheck className="size-4 mr-2" />
            Mark all read
          </Button>
        </div>
      </PageHeader>

      {items.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="No Notifications"
          description="You're all caught up."
        />
      ) : (
        <div className="space-y-2">
          {items.map((n) => {
            const Icon = TYPE_ICONS[n.type] ?? Info
            const date = safeParseDate(n.created_at)
            return (
              <Card
                key={n.id}
                className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                  !n.is_read ? "border-l-4 border-l-primary" : ""
                }`}
                onClick={async () => {
                  if (!n.is_read) {
                    await markRead.mutateAsync(n.id)
                  }
                  if (n.project_id) {
                    navigate(`/projects/${n.project_id}`)
                  }
                }}
              >
                <CardContent className="flex items-start gap-3 py-3">
                  <Icon className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium ${!n.is_read ? "" : "text-muted-foreground"}`}>
                        {n.title}
                      </span>
                      {!n.is_read && (
                        <span className="size-2 rounded-full bg-primary shrink-0" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground truncate">{n.message}</p>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {date ? formatDistanceToNow(date, { addSuffix: true }) : ""}
                  </span>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
