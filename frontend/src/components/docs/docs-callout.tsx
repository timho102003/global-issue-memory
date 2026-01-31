import { Info, AlertTriangle, Lightbulb } from "lucide-react";
import { cn } from "@/lib/utils";

const variants = {
  tip: {
    icon: Lightbulb,
    border: "border-accent-warm/30",
    bg: "bg-accent-warm/5",
    iconColor: "text-accent-warm",
  },
  warning: {
    icon: AlertTriangle,
    border: "border-accent-amber/30",
    bg: "bg-accent-amber/5",
    iconColor: "text-accent-amber",
  },
  info: {
    icon: Info,
    border: "border-info/30",
    bg: "bg-info/5",
    iconColor: "text-info-foreground",
  },
} as const;

interface DocsCalloutProps {
  variant?: keyof typeof variants;
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function DocsCallout({
  variant = "info",
  title,
  children,
  className,
}: DocsCalloutProps) {
  const v = variants[variant];
  const Icon = v.icon;

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-xl border p-4",
        v.border,
        v.bg,
        className
      )}
    >
      <Icon className={cn("mt-0.5 h-5 w-5 shrink-0", v.iconColor)} />
      <div>
        {title && (
          <p className="mb-1 text-[14px] font-semibold text-text-primary">
            {title}
          </p>
        )}
        <div className="text-[13px] leading-relaxed text-text-secondary sm:text-[14px]">
          {children}
        </div>
      </div>
    </div>
  );
}
