import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

/**
 * Stats card component matching GIM.pen dashboard design.
 */
export function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  className,
}: StatsCardProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-[20px] bg-white p-6",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm text-text-secondary">{title}</span>
        {Icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-bg-muted">
            <Icon className="h-4 w-4 text-text-secondary" />
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold text-text-primary">{value}</span>
        {trend && (
          <span
            className={cn(
              "text-sm font-medium",
              trend.isPositive ? "text-success-foreground" : "text-error-foreground"
            )}
          >
            {trend.isPositive ? "+" : ""}{trend.value}%
          </span>
        )}
      </div>
      {subtitle && (
        <span className="text-xs text-text-muted">{subtitle}</span>
      )}
    </div>
  );
}
