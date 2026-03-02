import type { ColumnDef } from "@tanstack/react-table"
import { Copy, FileText, MoreVertical, ToggleLeft, ToggleRight } from "lucide-react"
import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { DataTable, EmptyState, SearchBar } from "@/components/common"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { usePrompts } from "@/hooks"
import type { Prompt } from "@/types"

const TEMPLATE_TYPES = [
  { value: "all", label: "All Templates" },
  { value: "opr", label: "OPR" },
  { value: "mpp", label: "MPP" },
  { value: "adop", label: "ADOP" },
  { value: "adre", label: "ADRE" },
  { value: "aggregators", label: "Aggregators" },
  { value: "commercial", label: "Commercial" },
]

export function PromptList() {
  const navigate = useNavigate()
  const [search, setSearch] = useState("")
  const [templateType, setTemplateType] = useState<string>("all")
  const [isActive, setIsActive] = useState<boolean | undefined>(undefined)

  const filters = {
    ...(search && { search }),
    ...(templateType !== "all" && { template_type: templateType }),
    ...(isActive !== undefined && { is_active: isActive }),
  }

  const { data, isLoading } = usePrompts(filters)

  const handleRowClick = (prompt: Prompt) => {
    navigate(`/prompts/${prompt.id}`)
  }

  const columns: ColumnDef<Prompt>[] = [
    {
      accessorKey: "name",
      header: "Name",
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue("name")}</div>
      ),
    },
    {
      accessorKey: "template_type",
      header: "Template",
      cell: ({ row }) => {
        const templateType = row.getValue("template_type") as string | undefined
        return (
          <Badge variant="outline" className="uppercase">
            {templateType || "N/A"}
          </Badge>
        )
      },
    },
    {
      accessorKey: "version",
      header: "Version",
      cell: ({ row }) => (
        <div className="text-muted-foreground">
          v{row.getValue("version")}
        </div>
      ),
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => {
        const isActive = row.getValue("is_active") as boolean
        return (
          <Badge variant={isActive ? "default" : "secondary"}>
            {isActive ? "Active" : "Inactive"}
          </Badge>
        )
      },
    },
    {
      accessorKey: "updated_at",
      header: "Last Modified",
      cell: ({ row }) => {
        const dateValue = row.getValue("updated_at") as string | undefined
        if (!dateValue) {
          return <div className="text-sm text-muted-foreground">N/A</div>
        }
        const date = new Date(dateValue)
        if (isNaN(date.getTime())) {
          return <div className="text-sm text-muted-foreground">Invalid date</div>
        }
        return (
          <div className="text-sm text-muted-foreground">
            {date.toLocaleDateString()} {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )
      },
    },
    {
      id: "actions",
      header: "",
      cell: ({ row }) => {
        const prompt = row.original

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="icon" className="size-8">
                <MoreVertical className="size-4" />
                <span className="sr-only">Open menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/prompts/${prompt.id}`)
                }}
              >
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  // Duplicate not yet implemented
                }}
              >
                <Copy className="mr-2 size-4" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  // Toggle active not yet implemented
                }}
              >
                {prompt.is_active ? (
                  <>
                    <ToggleLeft className="mr-2 size-4" />
                    Deactivate
                  </>
                ) : (
                  <>
                    <ToggleRight className="mr-2 size-4" />
                    Activate
                  </>
                )}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <SearchBar
          value={search}
          onChange={setSearch}
          placeholder="Search prompts..."
          className="w-full sm:w-[300px]"
        />
        <div className="flex items-center gap-2">
          <Select value={templateType} onValueChange={setTemplateType}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Template Type" />
            </SelectTrigger>
            <SelectContent>
              {TEMPLATE_TYPES.map((tmpl) => (
                <SelectItem key={tmpl.value} value={tmpl.value}>
                  {tmpl.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={isActive === undefined ? "all" : isActive ? "active" : "inactive"}
            onValueChange={(value) => {
              if (value === "all") setIsActive(undefined)
              else setIsActive(value === "active")
            }}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {!isLoading && data?.items.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No prompts found"
          description="Try adjusting your filters or search query."
        />
      ) : (
        <DataTable
          columns={columns}
          data={data?.items || []}
          loading={isLoading}
          emptyMessage="No prompts found."
          onRowClick={handleRowClick}
        />
      )}
    </div>
  )
}
