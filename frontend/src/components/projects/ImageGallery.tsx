import {
  Check,
  ChevronLeft,
  ChevronRight,
  Download,
  Loader2,
  MousePointerClick,
  X,
} from "lucide-react"
import { useCallback, useEffect, useState } from "react"

import { EmptyState } from "@/components/common/EmptyState"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { api } from "@/lib/api"
import { cn, downloadBlob, isSafeExternalUrl } from "@/lib/utils"

interface ProjectImage {
  id: string
  url: string
  thumbnail_url: string
  category: "exterior" | "interior" | "amenity" | "logo" | "floor_plan"
  filename: string
  alt_text?: string
  width?: number
  height?: number
}

interface ImageGalleryProps {
  images: ProjectImage[]
  projectId?: string
}

const categories = [
  { value: "all", label: "All" },
  { value: "exterior", label: "Exterior" },
  { value: "interior", label: "Interior" },
  { value: "amenity", label: "Amenity" },
  { value: "logo", label: "Logo" },
]

export function ImageGallery({ images, projectId }: ImageGalleryProps) {
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [selectMode, setSelectMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isDownloading, setIsDownloading] = useState(false)

  const filteredImages =
    selectedCategory === "all"
      ? images
      : images.filter((img) => img.category === selectedCategory)

  const openLightbox = (index: number) => {
    if (selectMode) return
    setCurrentImageIndex(index)
    setLightboxOpen(true)
  }

  const closeLightbox = () => {
    setLightboxOpen(false)
  }

  const goToPrevious = useCallback(() => {
    setCurrentImageIndex((prev) => (prev > 0 ? prev - 1 : filteredImages.length - 1))
  }, [filteredImages.length])

  const goToNext = useCallback(() => {
    setCurrentImageIndex((prev) => (prev < filteredImages.length - 1 ? prev + 1 : 0))
  }, [filteredImages.length])

  const handleDownload = () => {
    const image = filteredImages[currentImageIndex]
    if (!isSafeExternalUrl(image.url)) return
    const link = document.createElement("a")
    link.href = image.url
    link.download = image.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const selectAll = () => {
    setSelectedIds(new Set(filteredImages.map((img) => img.id)))
  }

  const cancelSelection = () => {
    setSelectMode(false)
    setSelectedIds(new Set())
  }

  const handleBatchDownload = async (ids?: string[]) => {
    if (!projectId) return
    setIsDownloading(true)
    try {
      const params: { category?: string; ids?: string } = {}
      if (ids && ids.length > 0) {
        params.ids = ids.join(",")
      } else if (selectedCategory !== "all") {
        params.category = selectedCategory
      }
      const blob = await api.downloads.assets(projectId, params)
      const suffix = selectedCategory !== "all" ? `_${selectedCategory}` : ""
      downloadBlob(blob, `images${suffix}.zip`)
    } catch (err) {
      console.error("Batch download failed:", err)
    } finally {
      setIsDownloading(false)
    }
  }

  // Keyboard navigation
  useEffect(() => {
    if (!lightboxOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeLightbox()
      } else if (e.key === "ArrowLeft") {
        goToPrevious()
      } else if (e.key === "ArrowRight") {
        goToNext()
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [lightboxOpen, goToNext, goToPrevious])

  // Escape to exit select mode
  useEffect(() => {
    if (!selectMode) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") cancelSelection()
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [selectMode])

  if (images.length === 0) {
    return (
      <EmptyState
        title="No Images"
        description="No images have been uploaded for this project yet."
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Category Tabs + Actions */}
      <div className="flex items-center justify-between border-b border-border">
        <div className="flex gap-2">
          {categories.map((category) => (
            <button
              key={category.value}
              onClick={() => {
                setSelectedCategory(category.value)
                setSelectedIds(new Set())
              }}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                selectedCategory === category.value
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {category.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 pb-2">
          {!selectMode && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectMode(true)}
              disabled={filteredImages.length === 0}
            >
              <MousePointerClick className="size-4 mr-1" />
              Select
            </Button>
          )}
          {projectId && filteredImages.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBatchDownload()}
              disabled={isDownloading}
            >
              {isDownloading ? (
                <Loader2 className="size-4 mr-1 animate-spin" />
              ) : (
                <Download className="size-4 mr-1" />
              )}
              Download All
            </Button>
          )}
        </div>
      </div>

      {/* Image Grid */}
      {filteredImages.length === 0 ? (
        <EmptyState
          title="No Images in This Category"
          description="Try selecting a different category."
        />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {filteredImages.map((image, index) => {
            const isSelected = selectedIds.has(image.id)
            return (
              <Card
                key={image.id}
                className={cn(
                  "group relative aspect-square overflow-hidden cursor-pointer hover:shadow-lg transition-all",
                  selectMode && isSelected && "ring-2 ring-primary ring-offset-2"
                )}
                onClick={() => {
                  if (selectMode) {
                    toggleSelection(image.id)
                  } else {
                    openLightbox(index)
                  }
                }}
              >
                <img
                  src={image.thumbnail_url}
                  alt={image.filename}
                  className="w-full h-full object-cover transition-transform group-hover:scale-105"
                />
                {selectMode && (
                  <div
                    className={cn(
                      "absolute top-2 left-2 size-5 rounded border-2 flex items-center justify-center transition-colors",
                      isSelected
                        ? "bg-primary border-primary text-primary-foreground"
                        : "bg-white/80 border-gray-400"
                    )}
                  >
                    {isSelected && <Check className="size-3" />}
                  </div>
                )}
                {!selectMode && (
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="text-white text-sm font-medium px-3 py-1 bg-black/40 rounded-md">
                      {image.category}
                    </span>
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}

      {/* Selection Action Bar */}
      {selectMode && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-background border rounded-lg shadow-lg px-4 py-3 flex items-center gap-3">
          <span className="text-sm font-medium">{selectedIds.size} selected</span>
          {projectId && selectedIds.size > 0 && (
            <Button
              size="sm"
              onClick={() => handleBatchDownload(Array.from(selectedIds))}
              disabled={isDownloading}
            >
              {isDownloading ? (
                <Loader2 className="size-4 mr-1 animate-spin" />
              ) : (
                <Download className="size-4 mr-1" />
              )}
              Download Selected
            </Button>
          )}
          <Button size="sm" variant="outline" onClick={selectAll}>
            Select All
          </Button>
          <Button size="sm" variant="ghost" onClick={cancelSelection}>
            Cancel
          </Button>
        </div>
      )}

      {/* Lightbox */}
      {lightboxOpen && filteredImages.length > 0 && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={`Image viewer: ${filteredImages[currentImageIndex]?.filename || "image"}`}
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
        >
          {/* Close Button */}
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-4 right-4 text-white hover:bg-white/20"
            onClick={closeLightbox}
          >
            <X className="size-6" />
          </Button>

          {/* Navigation Arrows */}
          {filteredImages.length > 1 && (
            <>
              <Button
                variant="ghost"
                size="icon"
                className="absolute left-4 text-white hover:bg-white/20"
                onClick={goToPrevious}
              >
                <ChevronLeft className="size-8" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-4 text-white hover:bg-white/20"
                onClick={goToNext}
              >
                <ChevronRight className="size-8" />
              </Button>
            </>
          )}

          {/* Main Image */}
          <div className="max-w-6xl max-h-[90vh] flex flex-col items-center gap-4 p-4">
            <img
              src={filteredImages[currentImageIndex].url}
              alt={filteredImages[currentImageIndex].filename}
              className="max-w-full max-h-[70vh] object-contain"
            />

            {/* Image Metadata */}
            <div className="text-white text-center space-y-2">
              <div className="flex items-center gap-4 justify-center">
                <span className="text-sm">
                  {currentImageIndex + 1} / {filteredImages.length}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-white hover:bg-white/20"
                  onClick={handleDownload}
                >
                  <Download className="size-4 mr-2" />
                  Download
                </Button>
              </div>
              <div className="text-sm text-white/80">
                <div className="font-medium">
                  {filteredImages[currentImageIndex].alt_text || filteredImages[currentImageIndex].filename}
                </div>
                <div className="flex items-center gap-4 justify-center mt-1">
                  <span className="capitalize">
                    {filteredImages[currentImageIndex].category}
                  </span>
                  {filteredImages[currentImageIndex].width &&
                    filteredImages[currentImageIndex].height && (
                      <span>
                        {filteredImages[currentImageIndex].width} x{" "}
                        {filteredImages[currentImageIndex].height}
                      </span>
                    )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
