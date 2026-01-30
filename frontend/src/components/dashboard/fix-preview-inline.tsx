"use client";

import { Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FixPreview } from "@/types";

interface FixPreviewInlineProps {
  fixPreview?: FixPreview;
  className?: string;
}

/**
 * Inline fix preview block for issue cards.
 * Shows a green-tinted block with fix summary when available,
 * or a muted placeholder when no fix exists.
 */
export function FixPreviewInline({ fixPreview, className }: FixPreviewInlineProps) {
  if (!fixPreview?.has_fix) {
    return (
      <div
        className={cn(
          "flex items-center gap-2 rounded-xl border border-border-soft bg-bg-muted/50 px-3 py-2.5",
          className,
        )}
      >
        <Wrench className="h-3.5 w-3.5 shrink-0 text-text-muted" />
        <span className="text-xs text-text-muted">No fix available yet</span>
      </div>
    );
  }

  const displayText = fixPreview.summary || fixPreview.first_step || "Fix available";

  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-xl border border-cat-environment/20 bg-cat-environment/5 px-3 py-2.5",
        className,
      )}
    >
      <Wrench className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cat-environment" />
      <p className="line-clamp-2 text-xs leading-relaxed text-text-secondary">
        {displayText}
      </p>
    </div>
  );
}
