import { ArrowLeft, ExternalLink, Printer } from "lucide-react"
import { useNavigate, useParams } from "react-router-dom"

import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { useGenerationRuns, useProject } from "@/hooks"
import { isSafeExternalUrl } from "@/lib/utils"

export default function ContentPreviewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: project, isLoading, error } = useProject(id)
  const { data: generationRuns } = useGenerationRuns(id)

  const handlePrint = () => {
    window.print()
  }

  if (!id) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertDescription>Invalid project ID</AlertDescription>
        </Alert>
        <Button variant="outline" onClick={() => navigate("/projects")}>
          <ArrowLeft className="size-4 mr-2" />
          Back to Projects
        </Button>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(`/projects/${id}`)}
          >
            <ArrowLeft className="size-4" />
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Loading...</h1>
        </div>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load project content. Please try again.
          </AlertDescription>
        </Alert>
        <Button variant="outline" onClick={() => navigate(`/projects/${id}`)}>
          <ArrowLeft className="size-4 mr-2" />
          Back to Project
        </Button>
      </div>
    )
  }

  // Find the latest completed generation run with content
  const latestRun = generationRuns?.find(
    (r) => r.status === "completed" && r.generated_content
  )
  const content = latestRun?.generated_content ?? project.generated_content ?? {}

  const hasContent =
    Object.keys(content).length > 0 ||
    project.sheet_url ||
    project.workflow_status === "approved" ||
    project.workflow_status === "publishing" ||
    project.workflow_status === "published" ||
    project.workflow_status === "qa_verified" ||
    project.workflow_status === "complete"

  if (!hasContent) {
    return (
      <div className="space-y-6">
        <Alert>
          <AlertDescription>
            Content has not been generated for this project yet.
          </AlertDescription>
        </Alert>
        <Button variant="outline" onClick={() => navigate(`/projects/${id}`)}>
          <ArrowLeft className="size-4 mr-2" />
          Back to Project
        </Button>
      </div>
    )
  }

  // Extract content fields with fallbacks
  const title = (content.project_name as string) || project.name || "Property Title"
  const description = (content.description as string) || (content.project_description as string) || ""
  const features = extractList(content.features || content.key_features)
  const amenities = extractList(content.amenities)
  const locationDetails = (content.location_overview as string) || (content.location as string) || ""
  const priceInfo = (content.price_range as string) || (content.starting_price as string) || ""
  const paymentPlan = (content.payment_plan as string) || (content.payment_plans as string) || ""

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between print:hidden">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(`/projects/${id}`)}
        >
          <ArrowLeft className="size-4 mr-2" />
          Back to Project
        </Button>

        <div className="flex items-center gap-2">
          {latestRun && (
            <Badge variant="secondary">
              {latestRun.template_type?.toUpperCase() ?? ""}
            </Badge>
          )}
          {project.sheet_url && isSafeExternalUrl(project.sheet_url) && (
            <Button variant="outline" size="sm" asChild>
              <a
                href={project.sheet_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="size-4 mr-2" />
                Open in Sheets
              </a>
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={handlePrint}>
            <Printer className="size-4 mr-2" />
            Print
          </Button>
        </div>
      </div>

      {/* Content Preview */}
      <Card className="print:shadow-none print:border-0">
        <CardHeader>
          <CardTitle className="text-3xl">{title}</CardTitle>
          <p className="text-muted-foreground">{project.developer}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Description */}
          {description && (
            <>
              <section>
                <h2 className="text-xl font-semibold mb-3">Description</h2>
                <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                  {description}
                </p>
              </section>
              <Separator />
            </>
          )}

          {/* Key Features */}
          {features.length > 0 && (
            <>
              <section>
                <h2 className="text-xl font-semibold mb-3">Key Features</h2>
                <ul className="space-y-2">
                  {features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-primary mt-1.5">-</span>
                      <span className="text-muted-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>
              </section>
              <Separator />
            </>
          )}

          {/* Amenities */}
          {amenities.length > 0 && (
            <>
              <section>
                <h2 className="text-xl font-semibold mb-3">Amenities</h2>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {amenities.map((amenity, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-primary mt-1.5">-</span>
                      <span className="text-muted-foreground">{amenity}</span>
                    </li>
                  ))}
                </ul>
              </section>
              <Separator />
            </>
          )}

          {/* Location Details */}
          {(locationDetails || project.location) && (
            <>
              <section>
                <h2 className="text-xl font-semibold mb-3">Location</h2>
                {locationDetails && (
                  <p className="text-muted-foreground leading-relaxed whitespace-pre-line mb-4">
                    {locationDetails}
                  </p>
                )}
                <div className="grid grid-cols-2 gap-4">
                  {project.location && (
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Area</div>
                      <div className="font-medium">{project.location}</div>
                    </div>
                  )}
                  {project.emirate && (
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Emirate</div>
                      <div className="font-medium">{project.emirate}</div>
                    </div>
                  )}
                </div>
              </section>
              <Separator />
            </>
          )}

          {/* Price Information */}
          {priceInfo && (
            <>
              <section>
                <h2 className="text-xl font-semibold mb-3">Price Information</h2>
                <p className="text-muted-foreground leading-relaxed">
                  {priceInfo}
                </p>
              </section>
              <Separator />
            </>
          )}

          {/* Payment Plans */}
          {paymentPlan && (
            <section>
              <h2 className="text-xl font-semibold mb-3">Payment Plans</h2>
              <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                {paymentPlan}
              </p>
            </section>
          )}

          {/* Remaining content fields as key-value pairs */}
          {Object.keys(content).length > 0 && (
            <>
              <Separator />
              <section>
                <h2 className="text-xl font-semibold mb-3">All Generated Fields</h2>
                <div className="space-y-3">
                  {Object.entries(content)
                    .filter(([, v]) => v != null && String(v).trim() !== "")
                    .map(([key, value]) => (
                      <div key={key} className="rounded border p-3">
                        <div className="text-xs font-medium text-muted-foreground mb-1">
                          {key.replace(/_/g, " ")}
                        </div>
                        <div className="text-sm whitespace-pre-line">
                          {Array.isArray(value)
                            ? value.join(", ")
                            : typeof value === "object"
                              ? JSON.stringify(value, null, 2)
                              : String(value)}
                        </div>
                      </div>
                    ))}
                </div>
              </section>
            </>
          )}
        </CardContent>
      </Card>

      {/* Print Styles */}
      <style>{`
        @media print {
          body {
            print-color-adjust: exact;
            -webkit-print-color-adjust: exact;
          }
          .print\\:hidden {
            display: none !important;
          }
          .print\\:shadow-none {
            box-shadow: none !important;
          }
          .print\\:border-0 {
            border: 0 !important;
          }
        }
      `}</style>
    </div>
  )
}

function extractList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String)
  if (typeof value === "string" && value.trim()) {
    return value.split(/[,;\n]/).map((s) => s.trim()).filter(Boolean)
  }
  return []
}
