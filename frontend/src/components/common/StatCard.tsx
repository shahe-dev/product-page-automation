import { cva, type VariantProps } from "class-variance-authority";
import { ArrowDown, ArrowUp, type LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const statCardVariants = cva("", {
  variants: {
    variant: {
      default: "bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400",
      success: "bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400",
      warning: "bg-yellow-100 text-yellow-600 dark:bg-yellow-950 dark:text-yellow-400",
      danger: "bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

interface StatCardProps extends VariantProps<typeof statCardVariants> {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  className?: string;
}

export function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  variant = "default",
  className,
}: StatCardProps) {
  const isPositiveTrend = trend?.startsWith("+");
  const isNegativeTrend = trend?.startsWith("-");

  return (
    <Card className={cn("", className)}>
      <CardContent className="flex items-start justify-between gap-4 pt-6">
        <div className="flex-1 space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <div className="flex items-baseline gap-2">
            <p className="text-3xl font-bold tracking-tight">{value}</p>
            {trend && (
              <span
                className={cn(
                  "inline-flex items-center gap-1 text-sm font-medium",
                  isPositiveTrend && "text-green-600 dark:text-green-400",
                  isNegativeTrend && "text-red-600 dark:text-red-400"
                )}
              >
                {isPositiveTrend && <ArrowUp className="size-3" />}
                {isNegativeTrend && <ArrowDown className="size-3" />}
                {trend}
              </span>
            )}
          </div>
        </div>
        <div
          className={cn(
            "flex size-12 shrink-0 items-center justify-center rounded-full",
            statCardVariants({ variant })
          )}
        >
          <Icon className="size-6" />
        </div>
      </CardContent>
    </Card>
  );
}
