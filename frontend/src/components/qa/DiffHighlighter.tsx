import { cn } from "@/lib/utils"

interface DiffHighlighterProps {
  original: string
  modified: string
  severity?: "critical" | "major" | "minor"
  onClick?: () => void
}

interface DiffPart {
  value: string
  type: "unchanged" | "removed" | "added"
}

function computeWordDiff(original: string, modified: string): DiffPart[] {
  const originalWords = original.split(/(\s+)/)
  const modifiedWords = modified.split(/(\s+)/)

  const result: DiffPart[] = []
  let i = 0
  let j = 0

  while (i < originalWords.length || j < modifiedWords.length) {
    if (i >= originalWords.length) {
      // Remaining words are additions
      result.push({ value: modifiedWords[j], type: "added" })
      j++
    } else if (j >= modifiedWords.length) {
      // Remaining words are removals
      result.push({ value: originalWords[i], type: "removed" })
      i++
    } else if (originalWords[i] === modifiedWords[j]) {
      // Words match
      result.push({ value: originalWords[i], type: "unchanged" })
      i++
      j++
    } else {
      // Check if next words match (simple lookahead)
      const nextOriginalMatch = modifiedWords.indexOf(originalWords[i], j)
      const nextModifiedMatch = originalWords.indexOf(modifiedWords[j], i)

      if (nextOriginalMatch !== -1 && (nextModifiedMatch === -1 || nextOriginalMatch < nextModifiedMatch)) {
        // Word was added
        result.push({ value: modifiedWords[j], type: "added" })
        j++
      } else if (nextModifiedMatch !== -1) {
        // Word was removed
        result.push({ value: originalWords[i], type: "removed" })
        i++
      } else {
        // Both changed, show removal then addition
        result.push({ value: originalWords[i], type: "removed" })
        result.push({ value: modifiedWords[j], type: "added" })
        i++
        j++
      }
    }
  }

  return result
}

export function DiffHighlighter({
  original,
  modified,
  severity = "minor",
  onClick,
}: DiffHighlighterProps) {
  const diff = computeWordDiff(original, modified)

  const severityClasses = {
    critical: "border-red-500",
    major: "border-orange-500",
    minor: "border-yellow-500",
  }

  return (
    <div
      className={cn(
        "rounded-md border-2 border-l-4 bg-muted/50 p-3 transition-colors hover:bg-muted",
        severityClasses[severity],
        onClick && "cursor-pointer"
      )}
      onClick={onClick}
    >
      <div className="break-words text-sm">
        {diff.map((part, index) => {
          if (part.type === "unchanged") {
            return <span key={index}>{part.value}</span>
          } else if (part.type === "removed") {
            return (
              <span
                key={index}
                className="bg-red-100 text-red-800 line-through dark:bg-red-950 dark:text-red-300"
              >
                {part.value}
              </span>
            )
          } else {
            return (
              <span
                key={index}
                className="bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300"
              >
                {part.value}
              </span>
            )
          }
        })}
      </div>
    </div>
  )
}
