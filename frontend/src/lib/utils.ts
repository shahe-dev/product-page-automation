import { type ClassValue,clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Validate that a URL is safe for rendering as an external link (P3-22).
 * Only allows https:// URLs to prevent javascript:, data:, or protocol-relative attacks.
 */
export function isSafeExternalUrl(url: string | undefined | null): boolean {
  if (!url) return false
  try {
    const parsed = new URL(url)
    return parsed.protocol === "https:"
  } catch {
    return false
  }
}

/**
 * Safely parse a date string, returning null if invalid.
 */
export function safeParseDate(value: string | null | undefined): Date | null {
  if (!value) return null
  try {
    const date = new Date(value)
    return isNaN(date.getTime()) ? null : date
  } catch {
    return null
  }
}

/**
 * Trigger a browser download from a Blob.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
