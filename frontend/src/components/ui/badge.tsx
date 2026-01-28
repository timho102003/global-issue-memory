import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "success" | "warning" | "error" | "outline";
  category?: "environment" | "model" | "api" | "codegen" | "framework";
}

/**
 * Badge component matching GIM.pen design.
 */
function Badge({ className, variant = "default", category, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
        // Category colors (override variant if provided)
        category && {
          "bg-cat-environment/10 text-cat-environment": category === "environment",
          "bg-cat-model/10 text-cat-model": category === "model",
          "bg-cat-api/10 text-cat-api": category === "api",
          "bg-cat-codegen/10 text-cat-codegen": category === "codegen",
          "bg-cat-framework/10 text-cat-framework": category === "framework",
        },
        // Variant colors (used when no category)
        !category && {
          "bg-primary/10 text-primary": variant === "default",
          "bg-secondary text-secondary-foreground": variant === "secondary",
          "bg-success text-success-foreground": variant === "success",
          "bg-warning text-warning-foreground": variant === "warning",
          "bg-error text-error-foreground": variant === "error",
          "border border-border bg-transparent": variant === "outline",
        },
        className
      )}
      {...props}
    />
  );
}

export { Badge };
