import { formatDistanceToNow } from "date-fns"
import {
  Activity,
  Check,
  ChevronDown,
  Database,
  Download,
  Edit,
  ExternalLink,
  FileText,
  Image as ImageIcon,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Send,
  Trash2,
  X,
} from "lucide-react"
import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Separator } from "@/components/ui/separator"
import {
  useDeleteProject,
  useGenerationRuns,
  useProject,
  useSubmitForApproval,
  useUpdateProject,
} from "@/hooks"
import { useGenerateContent } from "@/hooks/queries/use-process"
import { api } from "@/lib/api"
import { cn, downloadBlob, isSafeExternalUrl, safeParseDate } from "@/lib/utils"
import { useAuthStore } from "@/stores/auth-store"
import type { GenerationRunSummary, TemplateType } from "@/types"

import { DataFilesViewer } from "./DataFilesViewer"
import { FloorPlanViewer } from "./FloorPlanViewer"
import { ImageGallery } from "./ImageGallery"

const ALL_TEMPLATE_TYPES: TemplateType[] = [
  "opr",
  "aggregators",
  "mpp",
  "adop",
  "adre",
  "commercial",
]

const TEMPLATE_LABELS: Record<TemplateType, string> = {
  opr: "OPR",
  aggregators: "Aggregators",
  mpp: "MPP",
  adop: "ADOP",
  adre: "ADRE",
  commercial: "Commercial",
}

function getRunStatus(
  templateType: TemplateType,
  projectRuns: GenerationRunSummary[],
  liveRuns: GenerationRunSummary[]
): GenerationRunSummary | undefined {
  // Live polling data takes priority over project snapshot
  const live = liveRuns.find((r) => r.template_type === templateType)
  if (live) return live
  return projectRuns.find((r) => r.template_type === templateType)
}

interface ProjectDetailProps {
  projectId: string
}

type TabValue = "overview" | "images" | "floor-plans" | "data" | "activity"

export function ProjectDetail({ projectId }: ProjectDetailProps) {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const isAdmin = user?.role === "admin"
  const { data: project, isLoading, error } = useProject(projectId)
  const { mutateAsync: updateProject } = useUpdateProject()
  const { mutateAsync: deleteProject, isPending: isDeleting } = useDeleteProject()
  const { mutateAsync: submitForApproval, isPending: isSubmitting } = useSubmitForApproval()
  const { data: liveRuns } = useGenerationRuns(projectId)
  const { mutateAsync: generateContent, isPending: isGenerating } = useGenerateContent()

  const [activeTab, setActiveTab] = useState<TabValue>("overview")
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false)
  const [selectedTemplates, setSelectedTemplates] = useState<Set<TemplateType>>(new Set())
  const [isDownloading, setIsDownloading] = useState(false)

  const handleEdit = () => {
    navigate(`/projects/${projectId}/edit`)
  }

  const handleSubmitForReview = async () => {
    try {
      await submitForApproval(projectId)
    } catch (err) {
      console.error("Failed to submit for review:", err)
    }
  }

  const handleDelete = async () => {
    setDeleteError(null)
    try {
      await deleteProject(projectId)
      setDeleteDialogOpen(false)
      navigate("/projects", { replace: true })
    } catch (err: unknown) {
      // Extract backend error detail from axios response if available
      let msg = "Failed to delete project. Please try again."
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } }
        const detail = axiosErr.response?.data?.detail
        const status = axiosErr.response?.status
        if (detail) {
          msg = detail
        } else if (status) {
          msg = `Server returned status ${status}`
        }
      } else if (err instanceof Error) {
        msg = err.message
      }
      console.error("[ProjectDetail] Delete failed:", err)
      setDeleteError(msg)
    }
  }

  const handleRetry = async () => {
    try {
      await updateProject({ id: projectId, data: { workflow_status: "draft" } })
    } catch (err) {
      console.error("Failed to retry project:", err)
    }
  }

  const handleGenerate = async () => {
    if (!project?.material_package_id || selectedTemplates.size === 0) return
    try {
      await generateContent({
        materialPackageId: project.material_package_id,
        templateTypes: Array.from(selectedTemplates),
      })
      setGenerateDialogOpen(false)
      setSelectedTemplates(new Set())
    } catch (err) {
      console.error("Failed to start generation:", err)
    }
  }

  const toggleTemplate = (t: TemplateType) => {
    setSelectedTemplates((prev) => {
      const next = new Set(prev)
      if (next.has(t)) {
        next.delete(t)
      } else {
        next.add(t)
      }
      return next
    })
  }

  const handleDownloadAssets = async (category?: string) => {
    setIsDownloading(true)
    try {
      const params = category && category !== "all" ? { category } : undefined
      const blob = await api.downloads.assets(projectId, params)
      const projectName = project?.name?.replace(/\s+/g, "_") || projectId
      const suffix = category && category !== "all" ? `_${category}` : ""
      downloadBlob(blob, `${projectName}${suffix}_assets.zip`)
    } catch (err) {
      console.error("Download failed:", err)
    } finally {
      setIsDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error || !project) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load project details. Please try again.
        </AlertDescription>
      </Alert>
    )
  }

  const tabs = [
    { value: "overview", label: "Overview", icon: FileText },
    { value: "images", label: "Images", icon: ImageIcon },
    { value: "floor-plans", label: "Floor Plans", icon: Layers },
    { value: "data", label: "Data", icon: Database },
    { value: "activity", label: "Activity", icon: Activity },
  ] as const

  const canSubmitForReview = project.workflow_status === "draft"
  const canEdit = project.workflow_status === "draft" || project.workflow_status === "revision_requested"
  const canRetry = project.workflow_status === "revision_requested"

  // Merge generation runs from project snapshot + live polling
  const projectRuns: GenerationRunSummary[] = project.generation_runs ?? []
  const liveRunsSummary: GenerationRunSummary[] = (liveRuns ?? []).map((r) => ({
    template_type: r.template_type,
    status: r.status,
    sheet_url: r.sheet_url,
    completed_at: r.completed_at,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold">{project.name}</h2>
            <StatusBadge status={project.workflow_status} />
          </div>
          <p className="text-sm text-muted-foreground">{project.developer}</p>
        </div>

        <div className="flex items-center gap-2">
          {(project.images?.length > 0 || project.floor_plans?.length > 0) && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" disabled={isDownloading}>
                  {isDownloading ? (
                    <Loader2 className="size-4 mr-2 animate-spin" />
                  ) : (
                    <Download className="size-4 mr-2" />
                  )}
                  Download
                  <ChevronDown className="size-4 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleDownloadAssets("all")}>
                  Download All Assets (ZIP)
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {project.images?.some((img) => img.category === "exterior") && (
                  <DropdownMenuItem onClick={() => handleDownloadAssets("exterior")}>
                    Exterior Images
                  </DropdownMenuItem>
                )}
                {project.images?.some((img) => img.category === "interior") && (
                  <DropdownMenuItem onClick={() => handleDownloadAssets("interior")}>
                    Interior Images
                  </DropdownMenuItem>
                )}
                {project.images?.some((img) => img.category === "amenity") && (
                  <DropdownMenuItem onClick={() => handleDownloadAssets("amenity")}>
                    Amenity Images
                  </DropdownMenuItem>
                )}
                {project.floor_plans?.length > 0 && (
                  <DropdownMenuItem onClick={() => handleDownloadAssets("floor_plan")}>
                    Floor Plans
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {canEdit && (
            <Button variant="outline" onClick={handleEdit}>
              <Edit className="size-4 mr-2" />
              Edit
            </Button>
          )}
          {canSubmitForReview && (
            <Button onClick={handleSubmitForReview} disabled={isSubmitting}>
              <Send className="size-4 mr-2" />
              {isSubmitting ? "Submitting..." : "Submit for Review"}
            </Button>
          )}
          {canRetry && (
            <Button variant="outline" onClick={handleRetry}>
              <RefreshCw className="size-4 mr-2" />
              Retry
            </Button>
          )}
          {isAdmin && (
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(true)}
            >
              <Trash2 className="size-4 mr-2" />
              Delete
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value as TabValue)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                activeTab === tab.value
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="size-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Property Info */}
          <Card>
            <CardHeader>
              <CardTitle>Property Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-muted-foreground mb-1">Location</div>
                  <div className="font-medium">{project.location}</div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Emirate</div>
                  <div className="font-medium">{project.emirate}</div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Template Type</div>
                  <div className="font-medium capitalize">
                    {project.template_type}
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Created By</div>
                  <div className="font-medium">{project.created_by?.name || "Unknown"}</div>
                </div>
              </div>
              <Separator />
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-muted-foreground mb-1">Created</div>
                  <div className="font-medium">
                    {(() => {
                      const date = safeParseDate(project.created_at)
                      return date ? formatDistanceToNow(date, { addSuffix: true }) : "-"
                    })()}
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Last Updated</div>
                  <div className="font-medium">
                    {(() => {
                      const date = safeParseDate(project.updated_at) || safeParseDate(project.created_at)
                      return date ? formatDistanceToNow(date, { addSuffix: true }) : "-"
                    })()}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Generated Content -- per-template status dashboard */}
          <Card>
            <CardHeader>
              <CardTitle>Generated Content</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                {ALL_TEMPLATE_TYPES.map((tt) => {
                  const run = getRunStatus(tt, projectRuns, liveRunsSummary)
                  return (
                    <div
                      key={tt}
                      className="flex items-center justify-between py-1.5 text-sm"
                    >
                      <span className="font-medium">{TEMPLATE_LABELS[tt]}</span>
                      <div className="flex items-center gap-2">
                        {!run && (
                          <span className="text-muted-foreground">--</span>
                        )}
                        {run?.status === "completed" && (
                          <>
                            <Badge
                              variant="default"
                              className="bg-green-600 hover:bg-green-600"
                            >
                              <Check className="size-3 mr-1" />
                              Completed
                            </Badge>
                            {isSafeExternalUrl(run.sheet_url) && (
                              <a
                                href={run.sheet_url!}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center text-xs text-primary hover:underline"
                              >
                                View Sheet
                                <ExternalLink className="size-3 ml-1" />
                              </a>
                            )}
                          </>
                        )}
                        {run?.status === "processing" && (
                          <Badge variant="secondary">
                            <Loader2 className="size-3 mr-1 animate-spin" />
                            Processing
                          </Badge>
                        )}
                        {run?.status === "pending" && (
                          <Badge variant="outline">Pending</Badge>
                        )}
                        {run?.status === "failed" && (
                          <Badge variant="destructive">
                            <X className="size-3 mr-1" />
                            Failed
                          </Badge>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {project.material_package_id && (
                <>
                  <Separator />
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      setSelectedTemplates(new Set())
                      setGenerateDialogOpen(true)
                    }}
                  >
                    <Plus className="size-4 mr-2" />
                    Generate for Template
                  </Button>
                </>
              )}

              {!project.material_package_id && (
                <div className="text-xs text-muted-foreground pt-1">
                  Extraction must complete before generating content.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === "images" && (
        <ImageGallery
          projectId={projectId}
          images={(project.images || []).map((img) => ({
            id: img.id,
            url: img.image_url,
            thumbnail_url: img.thumbnail_url || img.image_url,
            category: img.category as "exterior" | "interior" | "amenity" | "logo" | "floor_plan",
            filename: img.filename || img.alt_text || `${img.category}-${img.display_order + 1}.${img.format || "webp"}`,
            alt_text: img.alt_text,
            width: img.width,
            height: img.height,
          }))}
        />
      )}

      {activeTab === "floor-plans" && (
        <FloorPlanViewer
          floorPlans={(project.floor_plans || []).map((fp) => ({
            id: fp.id,
            image_url: fp.image_url,
            unit_type: fp.unit_type,
            bedrooms: fp.bedrooms || 0,
            bathrooms: fp.bathrooms || 0,
            size_sqft: Number(fp.total_sqft) || 0,
          }))}
        />
      )}

      {activeTab === "data" && (
        <DataFilesViewer projectId={projectId} />
      )}

      {activeTab === "activity" && (
        <Card>
          <CardHeader>
            <CardTitle>Activity Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              Activity tracking coming soon.
            </div>
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onOpenChange={(open) => {
          setDeleteDialogOpen(open)
          if (!open) setDeleteError(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Project</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this project? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {deleteError && (
            <Alert variant="destructive">
              <AlertDescription>{deleteError}</AlertDescription>
            </Alert>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Generate for Template Dialog */}
      <Dialog open={generateDialogOpen} onOpenChange={setGenerateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate for Template</DialogTitle>
            <DialogDescription>
              Select which template types to generate content for.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            {ALL_TEMPLATE_TYPES.map((tt) => {
              const run = getRunStatus(tt, projectRuns, liveRunsSummary)
              const isCompleted = run?.status === "completed"
              const isActive = run?.status === "processing" || run?.status === "pending"
              const disabled = isCompleted || isActive

              return (
                <label
                  key={tt}
                  className={cn(
                    "flex items-center gap-3 rounded-md border px-3 py-2 text-sm transition-colors",
                    disabled
                      ? "cursor-not-allowed opacity-60 bg-muted"
                      : "cursor-pointer hover:bg-accent"
                  )}
                >
                  <input
                    type="checkbox"
                    className="size-4 rounded border-input accent-primary"
                    checked={selectedTemplates.has(tt)}
                    disabled={disabled}
                    onChange={() => toggleTemplate(tt)}
                  />
                  <span className="flex-1 font-medium">{TEMPLATE_LABELS[tt]}</span>
                  {isCompleted && (
                    <Badge
                      variant="default"
                      className="bg-green-600 hover:bg-green-600 text-xs"
                    >
                      <Check className="size-3 mr-1" />
                      Done
                    </Badge>
                  )}
                  {isActive && (
                    <Badge variant="secondary" className="text-xs">
                      <Loader2 className="size-3 mr-1 animate-spin" />
                      In Progress
                    </Badge>
                  )}
                </label>
              )
            })}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setGenerateDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleGenerate}
              disabled={selectedTemplates.size === 0 || isGenerating}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="size-4 mr-2 animate-spin" />
                  Starting...
                </>
              ) : (
                <>Generate ({selectedTemplates.size})</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
