import { ChevronDown, ChevronRight, FileText, Loader2 } from "lucide-react"
import { useState } from "react"

import { EmptyState } from "@/components/common/EmptyState"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useProjectDataFiles } from "@/hooks"
import { cn } from "@/lib/utils"

interface DataFilesViewerProps {
  projectId: string
}

const FILE_LABELS: Record<string, string> = {
  "manifest.json": "Manifest",
  "extracted_text.json": "Extracted Text",
  "floor_plans.json": "Floor Plans",
  "structured_data.json": "Structured Data",
}

function CollapsibleSection({
  label,
  defaultOpen = false,
  children,
}: {
  label: string
  defaultOpen?: boolean
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border rounded-md">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium hover:bg-accent transition-colors text-left"
      >
        {open ? (
          <ChevronDown className="size-4 shrink-0" />
        ) : (
          <ChevronRight className="size-4 shrink-0" />
        )}
        {label}
      </button>
      {open && <div className="border-t px-3 py-2">{children}</div>}
    </div>
  )
}

function JsonContent({ data }: { data: unknown }) {
  if (data === null || data === undefined) {
    return <span className="text-muted-foreground italic">null</span>
  }

  if (typeof data !== "object") {
    return (
      <pre className="text-xs font-mono whitespace-pre-wrap break-all">
        {JSON.stringify(data, null, 2)}
      </pre>
    )
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <span className="text-muted-foreground italic">[] (empty array)</span>
    }
    return (
      <div className="space-y-1">
        {data.map((item, idx) => (
          <CollapsibleSection key={idx} label={`[${idx}]`}>
            <JsonContent data={item} />
          </CollapsibleSection>
        ))}
      </div>
    )
  }

  const entries = Object.entries(data as Record<string, unknown>)
  if (entries.length === 0) {
    return <span className="text-muted-foreground italic">{"{}"} (empty object)</span>
  }

  // For leaf-heavy objects (most values are primitives), render as formatted JSON
  const primitiveCount = entries.filter(
    ([, v]) => v === null || typeof v !== "object"
  ).length
  if (primitiveCount > entries.length * 0.7 && entries.length <= 20) {
    return (
      <pre className="text-xs font-mono whitespace-pre-wrap break-all bg-muted/50 rounded p-2">
        {JSON.stringify(data, null, 2)}
      </pre>
    )
  }

  return (
    <div className="space-y-1">
      {entries.map(([key, value]) => {
        if (value === null || typeof value !== "object") {
          return (
            <div key={key} className="flex gap-2 text-xs font-mono py-0.5">
              <span className="text-primary font-semibold shrink-0">{key}:</span>
              <span className="text-muted-foreground break-all">
                {JSON.stringify(value)}
              </span>
            </div>
          )
        }
        return (
          <CollapsibleSection key={key} label={key}>
            <JsonContent data={value} />
          </CollapsibleSection>
        )
      })}
    </div>
  )
}

export function DataFilesViewer({ projectId }: DataFilesViewerProps) {
  const { data, isLoading, error } = useProjectDataFiles(projectId)
  const [activeFile, setActiveFile] = useState<string>("manifest.json")

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <EmptyState
            title="Failed to Load Data Files"
            description="Could not retrieve extraction data from storage."
          />
        </CardContent>
      </Card>
    )
  }

  const files = data?.files || {}
  const availableFiles = Object.keys(FILE_LABELS).filter((name) => name in files)

  if (availableFiles.length === 0) {
    return (
      <Card>
        <CardContent className="py-8">
          <EmptyState
            title="No Data Files"
            description="No extraction data files are available for this project yet."
          />
        </CardContent>
      </Card>
    )
  }

  // If active file is not in available list, switch to first available
  const resolvedActive = availableFiles.includes(activeFile)
    ? activeFile
    : availableFiles[0]

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <FileText className="size-5" />
          Extraction Data
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* File sub-tabs */}
        <div className="flex gap-2 border-b border-border">
          {availableFiles.map((name) => (
            <button
              key={name}
              onClick={() => setActiveFile(name)}
              className={cn(
                "px-3 py-1.5 text-sm font-medium border-b-2 -mb-px transition-colors",
                resolvedActive === name
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {FILE_LABELS[name] || name}
            </button>
          ))}
        </div>

        {/* File content */}
        <div className="max-h-[600px] overflow-y-auto">
          <JsonContent data={files[resolvedActive]} />
        </div>
      </CardContent>
    </Card>
  )
}
