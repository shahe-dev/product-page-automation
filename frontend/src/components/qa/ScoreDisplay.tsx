import { TrendingDown, TrendingUp } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

interface ScoreDisplayProps {
  overallScore: number
  fieldScores?: Record<string, number>
  previousScore?: number
}

export function ScoreDisplay({
  overallScore,
  fieldScores,
  previousScore,
}: ScoreDisplayProps) {
  const scoreColor = overallScore >= 80 ? "text-green-600" : overallScore >= 60 ? "text-yellow-600" : "text-red-600"
  const scoreTrend = previousScore !== undefined ? overallScore - previousScore : null

  return (
    <Card>
      <CardHeader>
        <CardTitle>QA Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-start gap-6">
          {/* Circular Score */}
          <div className="flex flex-col items-center">
            <div className="relative size-32">
              <svg className="size-full -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  className="text-muted"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  strokeDasharray={`${2 * Math.PI * 40}`}
                  strokeDashoffset={`${2 * Math.PI * 40 * (1 - overallScore / 100)}`}
                  strokeLinecap="round"
                  className={cn(
                    "transition-all duration-500",
                    overallScore >= 80 ? "text-green-600" : overallScore >= 60 ? "text-yellow-600" : "text-red-600"
                  )}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={cn("text-3xl font-bold", scoreColor)}>
                  {overallScore}
                </span>
                <span className="text-xs text-muted-foreground">Score</span>
              </div>
            </div>
            {scoreTrend !== null && (
              <div className="mt-2 flex items-center gap-1 text-sm">
                {scoreTrend > 0 ? (
                  <>
                    <TrendingUp className="size-4 text-green-600" />
                    <span className="text-green-600">+{scoreTrend.toFixed(1)}</span>
                  </>
                ) : scoreTrend < 0 ? (
                  <>
                    <TrendingDown className="size-4 text-red-600" />
                    <span className="text-red-600">{scoreTrend.toFixed(1)}</span>
                  </>
                ) : (
                  <span className="text-muted-foreground">No change</span>
                )}
              </div>
            )}
          </div>

          {/* Field Scores */}
          {fieldScores && Object.keys(fieldScores).length > 0 && (
            <div className="flex-1 space-y-3">
              <h4 className="text-sm font-medium text-muted-foreground">Field Breakdown</h4>
              <div className="space-y-2">
                {Object.entries(fieldScores)
                  .sort(([, a], [, b]) => b - a)
                  .map(([field, score]) => (
                    <div key={field} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium capitalize">
                          {field.replace(/_/g, " ")}
                        </span>
                        <span className={cn(
                          "font-semibold",
                          score >= 80 ? "text-green-600" : score >= 60 ? "text-yellow-600" : "text-red-600"
                        )}>
                          {score}%
                        </span>
                      </div>
                      <Progress value={score} className="h-2" />
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
