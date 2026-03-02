import { GripVertical } from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

import { DiffHighlighter } from "./DiffHighlighter"
import type { QAIssue } from "./IssueList"

interface ComparisonViewProps {
  sourceData: Record<string, string>
  generatedData: Record<string, string>
  issues?: QAIssue[]
  onIssueClick?: (issue: QAIssue) => void
}

export function ComparisonView({
  sourceData,
  generatedData,
  issues = [],
  onIssueClick,
}: ComparisonViewProps) {
  const leftPanelRef = useRef<HTMLDivElement>(null)
  const rightPanelRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [splitPosition, setSplitPosition] = useState(50)

  const containerRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = () => {
    setIsDragging(true)
  }

  // Use document-level listeners so dragging continues even when cursor leaves the container
  useEffect(() => {
    if (!isDragging) return

    const handleDocumentMouseMove = (e: MouseEvent) => {
      const container = containerRef.current
      if (!container) return
      const rect = container.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percentage = (x / rect.width) * 100
      setSplitPosition(Math.max(20, Math.min(80, percentage)))
    }

    const handleDocumentMouseUp = () => {
      setIsDragging(false)
    }

    document.addEventListener("mousemove", handleDocumentMouseMove)
    document.addEventListener("mouseup", handleDocumentMouseUp)
    return () => {
      document.removeEventListener("mousemove", handleDocumentMouseMove)
      document.removeEventListener("mouseup", handleDocumentMouseUp)
    }
  }, [isDragging])

  const handleScroll = (source: "left" | "right") => {
    if (source === "left" && leftPanelRef.current && rightPanelRef.current) {
      rightPanelRef.current.scrollTop = leftPanelRef.current.scrollTop
    } else if (source === "right" && leftPanelRef.current && rightPanelRef.current) {
      leftPanelRef.current.scrollTop = rightPanelRef.current.scrollTop
    }
  }

  const allFields = Array.from(
    new Set([...Object.keys(sourceData), ...Object.keys(generatedData)])
  ).sort()

  const getFieldIssues = (field: string) =>
    issues.filter((issue) => issue.field === field && issue.status === "open")

  const hasFieldIssue = (field: string) => getFieldIssues(field).length > 0

  const getFieldSeverity = (field: string): "critical" | "major" | "minor" | undefined => {
    const fieldIssues = getFieldIssues(field)
    if (fieldIssues.some((i) => i.severity === "critical")) return "critical"
    if (fieldIssues.some((i) => i.severity === "major")) return "major"
    if (fieldIssues.some((i) => i.severity === "minor")) return "minor"
    return undefined
  }

  const renderFieldContent = (field: string, value: string, isSource: boolean) => {
    const fieldIssues = getFieldIssues(field)
    const otherValue = isSource ? generatedData[field] : sourceData[field]

    if (!isSource && fieldIssues.length > 0 && otherValue && value && value !== otherValue) {
      const severity = getFieldSeverity(field)
      return (
        <DiffHighlighter
          original={otherValue}
          modified={value}
          severity={severity}
          onClick={() => fieldIssues[0] && onIssueClick?.(fieldIssues[0])}
        />
      )
    }

    return <p className="whitespace-pre-wrap break-words text-sm">{value || "-"}</p>
  }

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Content Comparison</CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        <div
          ref={containerRef}
          className="relative flex h-[600px]"
        >
          {/* Left Panel - Source Content */}
          <div style={{ width: `${splitPosition}%` }} className="flex flex-col">
            <div className="mb-2 rounded-md bg-muted px-3 py-2">
              <h3 className="text-sm font-semibold">Source Content</h3>
            </div>
            <div
              ref={leftPanelRef}
              className="flex-1 space-y-4 overflow-y-auto pr-2"
              onScroll={() => handleScroll("left")}
            >
              {allFields.map((field) => (
                <div key={field} className="space-y-1">
                  <div
                    className={cn(
                      "flex items-center gap-2 text-xs font-medium text-muted-foreground",
                      hasFieldIssue(field) && "text-red-600"
                    )}
                  >
                    <span className="capitalize">{field.replace(/_/g, " ")}</span>
                    {hasFieldIssue(field) && (
                      <span className="rounded-full bg-red-100 px-2 py-0.5 text-red-700 dark:bg-red-950 dark:text-red-300">
                        {getFieldIssues(field).length} issue
                        {getFieldIssues(field).length > 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                  {renderFieldContent(field, sourceData[field] || "", true)}
                </div>
              ))}
            </div>
          </div>

          {/* Drag Handle */}
          <div
            className="group relative flex w-2 cursor-col-resize items-center justify-center hover:bg-muted"
            onMouseDown={handleMouseDown}
          >
            <Separator orientation="vertical" className="absolute inset-y-0" />
            <div className="z-10 rounded-full bg-border p-1 opacity-0 transition-opacity group-hover:opacity-100">
              <GripVertical className="size-4 text-muted-foreground" />
            </div>
          </div>

          {/* Right Panel - Generated Content */}
          <div style={{ width: `${100 - splitPosition}%` }} className="flex flex-col">
            <div className="mb-2 rounded-md bg-muted px-3 py-2">
              <h3 className="text-sm font-semibold">Generated Content</h3>
            </div>
            <div
              ref={rightPanelRef}
              className="flex-1 space-y-4 overflow-y-auto pl-2"
              onScroll={() => handleScroll("right")}
            >
              {allFields.map((field) => (
                <div key={field} className="space-y-1">
                  <div
                    className={cn(
                      "flex items-center gap-2 text-xs font-medium text-muted-foreground",
                      hasFieldIssue(field) && "text-red-600"
                    )}
                  >
                    <span className="capitalize">{field.replace(/_/g, " ")}</span>
                    {hasFieldIssue(field) && (
                      <span className="rounded-full bg-red-100 px-2 py-0.5 text-red-700 dark:bg-red-950 dark:text-red-300">
                        {getFieldIssues(field).length} issue
                        {getFieldIssues(field).length > 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                  {renderFieldContent(field, generatedData[field] || "", false)}
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
