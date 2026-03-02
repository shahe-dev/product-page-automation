import { Bath, Bed, Download, Maximize2, X } from "lucide-react"
import { useState } from "react"

import { EmptyState } from "@/components/common/EmptyState"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn, isSafeExternalUrl } from "@/lib/utils"

interface FloorPlan {
  id: string
  image_url: string
  unit_type: string
  bedrooms: number
  bathrooms: number
  size_sqft: number
  price_from?: number
  price_to?: number
}

interface FloorPlanViewerProps {
  floorPlans: FloorPlan[]
}

export function FloorPlanViewer({ floorPlans }: FloorPlanViewerProps) {
  const [selectedFloorPlan, setSelectedFloorPlan] = useState<FloorPlan | null>(null)
  const [activeTab, setActiveTab] = useState<string>("all")

  // Group by unit type or show all
  const unitTypes = ["all", ...Array.from(new Set(floorPlans.map(fp => fp.unit_type)))]

  const filteredFloorPlans = activeTab === "all"
    ? floorPlans
    : floorPlans.filter(fp => fp.unit_type === activeTab)

  const formatPrice = (price?: number) => {
    if (!price) return null
    return new Intl.NumberFormat("en-AE", {
      style: "currency",
      currency: "AED",
      minimumFractionDigits: 0,
    }).format(price)
  }

  const handleDownload = (floorPlan: FloorPlan) => {
    if (!isSafeExternalUrl(floorPlan.image_url)) return
    const link = document.createElement("a")
    link.href = floorPlan.image_url
    link.download = `${floorPlan.unit_type.replace(/\s+/g, "_")}_floor_plan.webp`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const openFullSize = (floorPlan: FloorPlan) => {
    setSelectedFloorPlan(floorPlan)
  }

  const closeFullSize = () => {
    setSelectedFloorPlan(null)
  }

  if (floorPlans.length === 0) {
    return (
      <EmptyState
        title="No Floor Plans"
        description="No floor plans have been uploaded for this project yet."
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Unit Type Tabs */}
      {unitTypes.length > 1 && (
        <div className="flex gap-2 border-b border-border overflow-x-auto">
          {unitTypes.map((unitType) => (
            <button
              key={unitType}
              onClick={() => setActiveTab(unitType)}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap",
                activeTab === unitType
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {unitType === "all" ? "All Units" : unitType}
            </button>
          ))}
        </div>
      )}

      {/* Floor Plans Grid */}
      {filteredFloorPlans.length === 0 ? (
        <EmptyState
          title="No Floor Plans in This Category"
          description="Try selecting a different unit type."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredFloorPlans.map((floorPlan) => (
            <Card key={floorPlan.id} className="overflow-hidden group">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-lg">{floorPlan.unit_type}</CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDownload(floorPlan)
                  }}
                  title="Download floor plan"
                >
                  <Download className="size-4" />
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Floor Plan Image */}
                <div
                  className="relative aspect-video bg-muted rounded-md overflow-hidden cursor-pointer"
                  onClick={() => openFullSize(floorPlan)}
                >
                  <img
                    src={floorPlan.image_url}
                    alt={floorPlan.unit_type}
                    className="w-full h-full object-contain transition-transform group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <div className="text-white text-sm font-medium px-3 py-2 bg-black/60 rounded-md flex items-center gap-2">
                      <Maximize2 className="size-4" />
                      View Full Size
                    </div>
                  </div>
                </div>

                {/* Floor Plan Details */}
                <div className="space-y-3">
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1.5">
                      <Bed className="size-4 text-muted-foreground" />
                      <span>{floorPlan.bedrooms} BR</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Bath className="size-4 text-muted-foreground" />
                      <span>{floorPlan.bathrooms} BA</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Maximize2 className="size-4 text-muted-foreground" />
                      <span>{floorPlan.size_sqft.toLocaleString()} sqft</span>
                    </div>
                  </div>

                  {/* Price Range */}
                  {(floorPlan.price_from || floorPlan.price_to) && (
                    <div className="text-sm font-medium">
                      {floorPlan.price_from && floorPlan.price_to ? (
                        <span>
                          {formatPrice(floorPlan.price_from)} -{" "}
                          {formatPrice(floorPlan.price_to)}
                        </span>
                      ) : floorPlan.price_from ? (
                        <span>From {formatPrice(floorPlan.price_from)}</span>
                      ) : (
                        <span>Up to {formatPrice(floorPlan.price_to)}</span>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Full Size Modal */}
      {selectedFloorPlan && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4">
          <div className="absolute top-4 right-4 flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/20"
              onClick={() => handleDownload(selectedFloorPlan)}
              title="Download floor plan"
            >
              <Download className="size-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/20"
              onClick={closeFullSize}
            >
              <X className="size-6" />
            </Button>
          </div>

          <div className="max-w-6xl max-h-[90vh] flex flex-col items-center gap-4">
            <img
              src={selectedFloorPlan.image_url}
              alt={selectedFloorPlan.unit_type}
              className="max-w-full max-h-[80vh] object-contain"
            />

            {/* Floor Plan Info */}
            <div className="text-white text-center space-y-2">
              <div className="text-lg font-semibold">
                {selectedFloorPlan.unit_type}
              </div>
              <div className="flex items-center gap-4 justify-center text-sm text-white/80">
                <span className="flex items-center gap-1">
                  <Bed className="size-4" />
                  {selectedFloorPlan.bedrooms} Bedrooms
                </span>
                <span className="flex items-center gap-1">
                  <Bath className="size-4" />
                  {selectedFloorPlan.bathrooms} Bathrooms
                </span>
                <span className="flex items-center gap-1">
                  <Maximize2 className="size-4" />
                  {selectedFloorPlan.size_sqft.toLocaleString()} sqft
                </span>
              </div>
              {(selectedFloorPlan.price_from || selectedFloorPlan.price_to) && (
                <div className="text-sm">
                  {selectedFloorPlan.price_from && selectedFloorPlan.price_to ? (
                    <span>
                      {formatPrice(selectedFloorPlan.price_from)} -{" "}
                      {formatPrice(selectedFloorPlan.price_to)}
                    </span>
                  ) : selectedFloorPlan.price_from ? (
                    <span>From {formatPrice(selectedFloorPlan.price_from)}</span>
                  ) : (
                    <span>Up to {formatPrice(selectedFloorPlan.price_to)}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
