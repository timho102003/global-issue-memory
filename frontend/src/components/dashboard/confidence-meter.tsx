"use client";

import { cn } from "@/lib/utils";

interface ConfidenceMeterProps {
  /** Confidence value between 0 and 1 */
  value: number;
  /** Show percentage label alongside the bar */
  showLabel?: boolean;
  className?: string;
}

/**
 * Horizontal progress bar with color coding for confidence scores.
 * Green >80%, amber 50-80%, red <50%.
 */
export function ConfidenceMeter({ value, showLabel = true, className }: ConfidenceMeterProps) {
  const percentage = Math.round(value * 100);
  const colorClass =
    percentage >= 80
      ? "bg-cat-environment"
      : percentage >= 50
        ? "bg-accent-amber"
        : "bg-accent-red";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-bg-tertiary">
        <div
          className={cn("h-full rounded-full transition-all duration-300", colorClass)}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-medium tabular-nums text-text-secondary">
          {percentage}%
        </span>
      )}
    </div>
  );
}
