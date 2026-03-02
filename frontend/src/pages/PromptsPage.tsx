import { AlertTriangle, LayoutGrid, List } from "lucide-react"
import { useState } from "react"

import { PageHeader } from "@/components/common"
import { PromptCreateDialog, PromptList, SectionGroup } from "@/components/prompts"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useGroupedPrompts } from "@/hooks"
import { useAuthStore } from "@/stores/auth-store"
import type { TemplateType } from "@/types"

const TEMPLATE_TABS: { value: TemplateType; label: string }[] = [
  { value: "aggregators", label: "Aggregators" },
  { value: "opr", label: "OPR" },
  { value: "mpp", label: "MPP" },
  { value: "adop", label: "ADOP" },
  { value: "adre", label: "ADRE" },
  { value: "commercial", label: "Commercial" },
]

type ViewMode = "grouped" | "list"

export default function PromptsPage() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === "admin"
  const [activeTemplate, setActiveTemplate] = useState<TemplateType>("aggregators")
  const [viewMode, setViewMode] = useState<ViewMode>("grouped")
  const { data, isLoading, isError, error } = useGroupedPrompts(
    viewMode === "grouped" ? activeTemplate : null
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title="Prompt Management"
        description="Manage and version control your content generation prompts."
      >
        <div className="flex items-center gap-2">
          <div className="flex rounded-md border">
            <Button
              variant={viewMode === "grouped" ? "secondary" : "ghost"}
              size="sm"
              className="rounded-r-none"
              onClick={() => setViewMode("grouped")}
            >
              <LayoutGrid className="mr-1 size-4" />
              Grouped
            </Button>
            <Button
              variant={viewMode === "list" ? "secondary" : "ghost"}
              size="sm"
              className="rounded-l-none"
              onClick={() => setViewMode("list")}
            >
              <List className="mr-1 size-4" />
              List
            </Button>
          </div>
          {isAdmin && <PromptCreateDialog />}
        </div>
      </PageHeader>

      {viewMode === "grouped" ? (
        <>
          {/* Template type tabs */}
          <Tabs
            value={activeTemplate}
            onValueChange={(v) => setActiveTemplate(v as TemplateType)}
          >
            <TabsList className="w-full justify-start">
              {TEMPLATE_TABS.map((tab) => (
                <TabsTrigger key={tab.value} value={tab.value}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          {/* Coverage summary */}
          {data && (
            <div className="flex items-center gap-4 rounded-lg border bg-muted/30 p-4">
              <div className="flex-1">
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-medium">Coverage</span>
                  <span className="text-muted-foreground">
                    {data.total_prompts_defined}/{data.promptable_fields ?? data.total_fields} prompts
                    defined ({data.total_fields} total fields)
                  </span>
                </div>
                <Progress value={data.coverage_percent} className="h-2" />
              </div>
              <Badge
                variant={
                  data.coverage_percent >= 80
                    ? "default"
                    : data.coverage_percent >= 60
                      ? "secondary"
                      : "destructive"
                }
                className="text-lg"
              >
                {data.coverage_percent.toFixed(1)}%
              </Badge>
            </div>
          )}

          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="size-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          )}

          {/* Error state */}
          {isError && (
            <Alert variant="destructive">
              <AlertTriangle className="size-4" />
              <AlertTitle>Failed to load prompts</AlertTitle>
              <AlertDescription>
                {error instanceof Error ? error.message : "An unexpected error occurred. Please try again."}
              </AlertDescription>
            </Alert>
          )}

          {/* Sections */}
          {data && (
            <div className="space-y-2">
              {data.sections.map((section) => (
                <SectionGroup key={section.section} section={section} templateType={activeTemplate} />
              ))}
            </div>
          )}
        </>
      ) : (
        <PromptList />
      )}
    </div>
  )
}
