import { cn } from "@/lib/utils";
import { Info } from "lucide-react";

type BadgeVariant = "success" | "warning" | "purple";

interface StatsCardProps {
  title: string;
  value: string | number;
  badge?: {
    text: string;
    variant: BadgeVariant;
  };
  tooltip?: string;
  className?: string;
}

const badgeStyles: Record<BadgeVariant, string> = {
  success: "bg-[#E3F0E3] text-[#4A7A4A]",
  warning: "bg-[#FEF3CD] text-[#856404]",
  purple: "bg-[#E8E3F0] text-[#6B5B8C]",
};

/**
 * Stats card component matching GIM.pen dashboard design.
 */
export function StatsCard({
  title,
  value,
  badge,
  tooltip,
  className,
}: StatsCardProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-2xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-card)] transition-all duration-200 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5",
        className
      )}
    >
      <span className="inline-flex items-center gap-1 text-[13px] font-medium text-text-secondary">
        {title}
        {tooltip && (
          <span className="group relative">
            <Info className="h-3.5 w-3.5 text-text-secondary/60 transition-colors group-hover:text-text-secondary" />
            <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1.5 w-48 -translate-x-1/2 rounded-lg bg-text-primary px-3 py-2 text-[11px] leading-snug text-white opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100">
              {tooltip}
            </span>
          </span>
        )}
      </span>
      <div className="flex items-center gap-3">
        <span className="text-3xl font-bold tracking-tight text-text-primary">{value}</span>
        {badge && (
          <span
            className={cn(
              "rounded-full px-2.5 py-0.5 text-[11px] font-semibold",
              badgeStyles[badge.variant]
            )}
          >
            {badge.text}
          </span>
        )}
      </div>
    </div>
  );
}
