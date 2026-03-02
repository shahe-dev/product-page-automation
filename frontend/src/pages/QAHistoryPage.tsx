import { formatDistanceToNow } from "date-fns"
import { History, Search } from "lucide-react"
import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { EmptyState, LoadingSpinner, PageHeader } from "@/components/common"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useQAHistory } from "@/hooks/queries/use-qa"
import { safeParseDate } from "@/lib/utils"

export default function QAHistoryPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQAHistory(page)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="QA History" description="Historical QA results and diff reports" />
        <LoadingSpinner />
      </div>
    )
  }

  const items = data?.items ?? []
  const totalPages = data?.pages ?? 1

  return (
    <div className="space-y-6">
      <PageHeader title="QA History" description="Historical QA results and diff reports" />

      {items.length === 0 ? (
        <EmptyState
          icon={History}
          title="No QA Results"
          description="No QA comparisons have been performed yet. Run a QA comparison from the QA Review page."
        />
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-3 font-medium">Checkpoint</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Matches</th>
                  <th className="pb-3 font-medium">Diffs</th>
                  <th className="pb-3 font-medium">Missing</th>
                  <th className="pb-3 font-medium">Performed</th>
                  <th className="pb-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item: Record<string, string | number>) => {
                  const date = safeParseDate(item.performed_at as string)
                  return (
                    <tr key={item.id as string} className="border-b">
                      <td className="py-3">
                        <Badge variant="outline">{item.checkpoint_type as string}</Badge>
                      </td>
                      <td className="py-3">
                        <Badge
                          variant={item.status === "completed" ? "default" : "secondary"}
                        >
                          {item.status as string}
                        </Badge>
                      </td>
                      <td className="py-3 text-green-600 font-medium">
                        {item.matches != null ? String(item.matches) : "-"}
                      </td>
                      <td className="py-3 text-amber-600 font-medium">
                        {item.differences != null ? String(item.differences) : "-"}
                      </td>
                      <td className="py-3 text-red-600 font-medium">
                        {item.missing != null ? String(item.missing) : "-"}
                      </td>
                      <td className="py-3 text-muted-foreground">
                        {date ? formatDistanceToNow(date, { addSuffix: true }) : "-"}
                      </td>
                      <td className="py-3">
                        {item.project_id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/projects/${item.project_id}`)}
                          >
                            <Search className="size-4 mr-1" />
                            View
                          </Button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
