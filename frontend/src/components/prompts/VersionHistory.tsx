import { History, RotateCcw } from "lucide-react"
import { useState } from "react"

import { ConfirmDialog, EmptyState, LoadingSpinner } from "@/components/common"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { usePromptVersions, useUpdatePrompt } from "@/hooks"
import { cn } from "@/lib/utils"
import type { PromptVersion } from "@/types"

interface VersionHistoryProps {
  promptId: string
  currentContent: string
}

export function VersionHistory({ promptId, currentContent }: VersionHistoryProps) {
  const { data: versions, isLoading } = usePromptVersions(promptId)
  const updatePrompt = useUpdatePrompt()
  const [selectedVersion, setSelectedVersion] = useState<PromptVersion | null>(null)
  const [showDiff, setShowDiff] = useState(false)
  const [confirmRestore, setConfirmRestore] = useState<PromptVersion | null>(null)

  const handleViewVersion = (version: PromptVersion) => {
    setSelectedVersion(version)
    setShowDiff(true)
  }

  const handleRestore = async (version: PromptVersion) => {
    try {
      await updatePrompt.mutateAsync({
        id: promptId,
        content: version.content,
        reason: `Restored from version ${version.version}`,
      })
      setConfirmRestore(null)
    } catch (error) {
      console.error("Failed to restore version:", error)
    }
  }

  const calculateDiff = (oldContent: string, newContent: string) => {
    const oldLines = (oldContent || "").split("\n")
    const newLines = (newContent || "").split("\n")
    const maxLines = Math.max(oldLines.length, newLines.length)
    const diff: Array<{ type: "added" | "removed" | "unchanged"; content: string }> = []

    for (let i = 0; i < maxLines; i++) {
      const oldLine = oldLines[i]
      const newLine = newLines[i]

      if (oldLine === newLine) {
        diff.push({ type: "unchanged", content: oldLine || "" })
      } else {
        if (oldLine !== undefined) {
          diff.push({ type: "removed", content: oldLine })
        }
        if (newLine !== undefined) {
          diff.push({ type: "added", content: newLine })
        }
      }
    }

    return diff
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="size-5" />
            Version History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner />
        </CardContent>
      </Card>
    )
  }

  if (!versions || !Array.isArray(versions) || versions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="size-5" />
            Version History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={History}
            title="No version history"
            description="Changes will appear here once you save updates."
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="size-5" />
            Version History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-4">
              {(versions || []).map((version, index) => {
                const isLatest = index === 0
                const date = new Date(version.created_at)
                const isValidDate = !isNaN(date.getTime())

                return (
                  <div key={version.version} className="relative">
                    {index < versions.length - 1 && (
                      <div className="absolute left-4 top-12 h-full w-px bg-border" />
                    )}
                    <div className="flex gap-4">
                      <div className="relative flex size-8 shrink-0 items-center justify-center rounded-full border-2 border-background bg-muted">
                        <div className={cn(
                          "size-3 rounded-full",
                          isLatest ? "bg-primary" : "bg-muted-foreground"
                        )} />
                      </div>
                      <div className="flex-1 space-y-2 pb-8">
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">
                              Version {version.version}
                            </span>
                            {isLatest && (
                              <Badge variant="default" className="text-xs">
                                Current
                              </Badge>
                            )}
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {isValidDate ? `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : "Invalid date"}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {version.change_reason}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          by {version.created_by.name}
                        </p>
                        <div className="flex items-center gap-2 pt-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleViewVersion(version)}
                          >
                            View Content
                          </Button>
                          {!isLatest && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setConfirmRestore(version)}
                            >
                              <RotateCcw className="mr-2 size-3" />
                              Restore
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <Dialog open={showDiff} onOpenChange={setShowDiff}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>
              Version {selectedVersion?.version} Content
            </DialogTitle>
            <DialogDescription>
              {selectedVersion?.change_reason}
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[500px]">
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-semibold mb-2">Diff with Current</h4>
                <div className="rounded-md border bg-muted/50 p-4 font-mono text-xs">
                  {selectedVersion && calculateDiff(selectedVersion.content, currentContent).map((line, index) => (
                    <div
                      key={index}
                      className={cn(
                        "px-2 py-0.5",
                        line.type === "added" && "bg-green-100 dark:bg-green-900/30 text-green-900 dark:text-green-100",
                        line.type === "removed" && "bg-red-100 dark:bg-red-900/30 text-red-900 dark:text-red-100"
                      )}
                    >
                      <span className="mr-2 text-muted-foreground">
                        {line.type === "added" ? "+" : line.type === "removed" ? "-" : " "}
                      </span>
                      {line.content || "\u00A0"}
                    </div>
                  ))}
                </div>
              </div>
              <Separator />
              <div>
                <h4 className="text-sm font-semibold mb-2">Full Content</h4>
                <div className="rounded-md border bg-muted/50 p-4 font-mono text-xs whitespace-pre-wrap">
                  {selectedVersion?.content}
                </div>
              </div>
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!confirmRestore}
        onOpenChange={(open) => !open && setConfirmRestore(null)}
        title="Restore Version"
        description={`Are you sure you want to restore version ${confirmRestore?.version}? This will create a new version with the restored content.`}
        confirmLabel="Restore"
        onConfirm={() => confirmRestore && handleRestore(confirmRestore)}
        loading={updatePrompt.isPending}
      />
    </>
  )
}
