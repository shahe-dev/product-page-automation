import { X } from "lucide-react"

import { SearchBar } from "@/components/common/SearchBar"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useFilterStore } from "@/stores/filter-store"
import type { ProjectStatus } from "@/types"

const EMIRATES = [
  "Dubai",
  "Abu Dhabi",
  "Sharjah",
  "Ajman",
  "Umm Al Quwain",
  "Ras Al Khaimah",
  "Fujairah",
]

const STATUSES: { value: ProjectStatus; label: string }[] = [
  { value: "draft", label: "Draft" },
  { value: "pending_approval", label: "Pending Approval" },
  { value: "approved", label: "Approved" },
  { value: "revision_requested", label: "Revision Requested" },
  { value: "publishing", label: "Publishing" },
  { value: "published", label: "Published" },
  { value: "qa_verified", label: "QA Verified" },
  { value: "complete", label: "Complete" },
]

export function ProjectFilters() {
  const { projectFilters, setProjectFilters, clearProjectFilters } =
    useFilterStore()

  const hasActiveFilters =
    projectFilters.search ||
    projectFilters.status ||
    projectFilters.emirate ||
    projectFilters.developer

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <SearchBar
          value={projectFilters.search || ""}
          onChange={(value) => setProjectFilters({ search: value })}
          placeholder="Search projects..."
          className="flex-1"
        />

        <div className="flex flex-wrap gap-2">
          <Select
            value={projectFilters.status || "all"}
            onValueChange={(value) =>
              setProjectFilters({
                status: value === "all" ? undefined : (value as ProjectStatus),
              })
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              {STATUSES.map((status) => (
                <SelectItem key={status.value} value={status.value}>
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={projectFilters.emirate || "all"}
            onValueChange={(value) =>
              setProjectFilters({
                emirate: value === "all" ? undefined : value,
              })
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Emirate" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Emirates</SelectItem>
              {EMIRATES.map((emirate) => (
                <SelectItem key={emirate} value={emirate}>
                  {emirate}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearProjectFilters}
              className="gap-2"
            >
              <X className="size-4" />
              Clear
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
