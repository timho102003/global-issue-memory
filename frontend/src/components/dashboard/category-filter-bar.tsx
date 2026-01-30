"use client";

import { cn } from "@/lib/utils";
import type { RootCauseCategory } from "@/types";

interface CategoryPill {
  value: string;
  label: string;
  dotColor?: string;
}

const CATEGORIES: CategoryPill[] = [
  { value: "all", label: "All" },
  { value: "environment", label: "Environment", dotColor: "bg-cat-environment" },
  { value: "model_behavior", label: "Model", dotColor: "bg-cat-model" },
  { value: "api_integration", label: "API", dotColor: "bg-cat-api" },
  { value: "code_generation", label: "Codegen", dotColor: "bg-cat-codegen" },
  { value: "framework_specific", label: "Framework", dotColor: "bg-cat-framework" },
];

interface CategoryFilterBarProps {
  value: string;
  onChange: (category: string) => void;
  className?: string;
}

/**
 * Horizontal scrollable pill buttons for category filtering.
 * Each pill has a colored dot matching the category color.
 */
export function CategoryFilterBar({ value, onChange, className }: CategoryFilterBarProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-1.5 overflow-x-auto scrollbar-none",
        className,
      )}
    >
      {CATEGORIES.map((cat) => {
        const isActive = value === cat.value;
        return (
          <button
            key={cat.value}
            onClick={() => onChange(cat.value)}
            className={cn(
              "flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-200",
              isActive
                ? "bg-text-primary text-white shadow-sm"
                : "bg-white text-text-secondary hover:bg-bg-tertiary hover:text-text-primary border border-border-light/80",
            )}
          >
            {cat.dotColor && (
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  cat.dotColor,
                  isActive ? "opacity-100" : "opacity-60",
                )}
              />
            )}
            {cat.label}
          </button>
        );
      })}
    </div>
  );
}
