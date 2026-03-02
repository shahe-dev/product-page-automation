import { FileText, Upload, X } from "lucide-react"
import { useCallback, useRef, useState } from "react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { useExtractPdf } from "@/hooks"
import { cn } from "@/lib/utils"

interface FileUploadProps {
  onUploadComplete?: (result: { extraction_job_id: string; template_ids: string[] }) => void
  onUploadStarted?: (info: { filename: string; templateIds: string[] }) => void
  onUploadFailed?: () => void
}

interface FileWithProgress {
  file: File
  progress: number
}

const MAX_FILE_SIZE = 200 * 1024 * 1024 // 200MB
const ACCEPT_FILE_TYPES = ".pdf,application/pdf"

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i]
}

const TEMPLATE_OPTIONS = [
  { value: "opr", label: "Off-Plan Residential (OPR)" },
  { value: "mpp", label: "Main Brand Site" },
  { value: "aggregators", label: "Real Estate Aggregators" },
  { value: "adop", label: "ADOP Template" },
  { value: "adre", label: "ADRE Template" },
  { value: "commercial", label: "Commercial" },
]

export function FileUpload({ onUploadComplete, onUploadStarted, onUploadFailed }: FileUploadProps) {
  const [selectedFiles, setSelectedFiles] = useState<FileWithProgress[]>([])
  const [selectedTemplates, setSelectedTemplates] = useState<string[]>(["opr"])
  const [isDragOver, setIsDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { mutateAsync: extractPdf, isPending } = useExtractPdf()

  const validateFile = useCallback((file: File): string | null => {
    if (!file.type.includes("pdf")) {
      return `${file.name}: File must be a PDF`
    }
    if (file.size > MAX_FILE_SIZE) {
      return `${file.name}: File size exceeds ${formatFileSize(MAX_FILE_SIZE)}`
    }
    return null
  }, [])

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return

      setError(null)
      const newFiles: FileWithProgress[] = []
      const errors: string[] = []

      // Only allow one file at a time for multi-template flow
      const file = files[0]
      const validationError = validateFile(file)
      if (validationError) {
        errors.push(validationError)
      } else {
        newFiles.push({ file, progress: 0 })
      }

      if (errors.length > 0) {
        setError(errors.join("; "))
      }

      if (newFiles.length > 0) {
        setSelectedFiles(newFiles) // Replace, don't append
      }
    },
    [validateFile],
  )

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragOver(false)
      handleFiles(e.dataTransfer.files)
    },
    [handleFiles],
  )

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    },
    [handleFiles],
  )

  const handleRemoveFile = useCallback(() => {
    setSelectedFiles([])
    setError(null)
    setUploadProgress(0)
  }, [])

  const handleTemplateToggle = useCallback((templateValue: string) => {
    setSelectedTemplates((prev) => {
      if (prev.includes(templateValue)) {
        // Don't allow deselecting the last template
        if (prev.length === 1) return prev
        return prev.filter((t) => t !== templateValue)
      } else {
        return [...prev, templateValue]
      }
    })
  }, [])

  const handleUpload = useCallback(async () => {
    console.log("[FileUpload] handleUpload called", { selectedFiles: selectedFiles.length, selectedTemplates })
    if (selectedFiles.length === 0 || selectedTemplates.length === 0) {
      console.log("[FileUpload] Early return - no files or templates")
      return
    }

    setError(null)
    setUploadProgress(10)
    onUploadStarted?.({ filename: selectedFiles[0].file.name, templateIds: selectedTemplates })
    console.log("[FileUpload] Starting upload...")

    try {
      const file = selectedFiles[0].file

      // First upload the file to get a GCS URL
      const formData = new FormData()
      formData.append("file", file)

      // Get auth token from storage
      let authToken = ""
      const stored = sessionStorage.getItem("auth-storage")
      if (stored) {
        try {
          const parsed = JSON.parse(stored)
          authToken = parsed?.state?.token || ""
        } catch {
          // ignore parse errors
        }
      }

      // Upload file first
      console.log("[FileUpload] Uploading to /api/v1/upload/file...")
      const uploadResponse = await fetch("/api/v1/upload/file", {
        method: "POST",
        body: formData,
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      })

      console.log("[FileUpload] Upload response status:", uploadResponse.status)
      if (!uploadResponse.ok) {
        const errData = await uploadResponse.json().catch(() => ({}))
        console.error("[FileUpload] Upload failed:", errData)
        throw new Error(typeof errData.detail === "string" ? errData.detail : errData.detail?.message || "Failed to upload file")
      }

      const { gcs_url } = await uploadResponse.json()
      console.log("[FileUpload] Got GCS URL:", gcs_url)
      setUploadProgress(40)

      // Now start extraction with selected templates
      console.log("[FileUpload] Starting extraction with templates:", selectedTemplates)
      const result = await extractPdf({
        pdfUrl: gcs_url,
        templateIds: selectedTemplates,
      })
      console.log("[FileUpload] Extraction result:", result)

      setUploadProgress(100)

      if (onUploadComplete) {
        onUploadComplete({
          extraction_job_id: result.extraction_job_id,
          template_ids: result.template_ids,
        })
      }

      setSelectedFiles([])
      setUploadProgress(0)
    } catch (err) {
      console.error("[FileUpload] Error:", err)
      const errorMessage = err instanceof Error ? err.message : "Upload failed"
      setError(errorMessage)
      setUploadProgress(0)
      onUploadFailed?.()
    }
  }, [selectedFiles, selectedTemplates, extractPdf, onUploadComplete])

  const handleClickZone = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Select Template Types</h3>
          <p className="text-xs text-muted-foreground">
            Choose one or more templates for content generation. The PDF will be
            processed once and content generated for each selected template.
          </p>
          <div className="grid grid-cols-2 gap-3">
            {TEMPLATE_OPTIONS.map((template) => (
              <label
                key={template.value}
                className="flex items-center space-x-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedTemplates.includes(template.value)}
                  onChange={() => handleTemplateToggle(template.value)}
                  className="size-4 rounded border-gray-300 text-primary focus:ring-primary"
                  aria-label={template.label}
                />
                <span className="text-sm">{template.label}</span>
              </label>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Selected: {selectedTemplates.length} template(s)
          </p>
        </div>
      </Card>

      <Card
        className={cn(
          "relative cursor-pointer border-2 border-dashed transition-colors",
          isDragOver && "border-primary bg-primary/5",
          isPending && "pointer-events-none opacity-50",
          !isDragOver && !isPending && "hover:border-primary/50",
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClickZone}
      >
        <div className="flex flex-col items-center justify-center gap-4 p-12">
          <div className="flex size-16 items-center justify-center rounded-full bg-primary/10">
            <Upload className="size-8 text-primary" />
          </div>
          <div className="text-center space-y-2">
            <p className="text-lg font-medium">
              Drag and drop a PDF file here, or click to browse
            </p>
            <p className="text-sm text-muted-foreground">
              Maximum file size: {formatFileSize(MAX_FILE_SIZE)}
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPT_FILE_TYPES}
            className="hidden"
            onChange={handleInputChange}
            disabled={isPending}
          />
        </div>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {selectedFiles.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Selected File</h3>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <FileText className="size-5 text-muted-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">
                  {selectedFiles[0].file.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(selectedFiles[0].file.size)}
                </p>
              </div>
              {isPending && uploadProgress > 0 && (
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground w-10 text-right">
                    {uploadProgress}%
                  </span>
                </div>
              )}
              {!isPending && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRemoveFile()
                  }}
                >
                  <X className="size-4" />
                </Button>
              )}
            </div>
          </Card>
          <Button
            type="button"
            onClick={() => {
              console.log("[FileUpload] Button clicked!", { isPending, filesCount: selectedFiles.length, templates: selectedTemplates })
              handleUpload()
            }}
            disabled={isPending || selectedFiles.length === 0 || selectedTemplates.length === 0}
            className="w-full"
          >
            {isPending
              ? "Processing..."
              : `Process PDF for ${selectedTemplates.length} template(s)`}
          </Button>
        </div>
      )}
    </div>
  )
}
