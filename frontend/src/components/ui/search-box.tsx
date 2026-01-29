"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SearchBoxProps extends InputHTMLAttributes<HTMLInputElement> {}

/**
 * SearchBox component matching GIM.pen design.
 */
const SearchBox = forwardRef<HTMLInputElement, SearchBoxProps>(
  ({ className, ...props }, ref) => {
    return (
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          ref={ref}
          type="search"
          className={cn(
            "flex h-9 w-full rounded-lg border border-border-light bg-white pl-9 pr-4 py-1.5",
            "text-[13px] placeholder:text-text-muted transition-colors duration-150",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30 focus-visible:border-border-medium",
            "hover:border-border-medium",
            "disabled:cursor-not-allowed disabled:opacity-50",
            className
          )}
          {...props}
        />
      </div>
    );
  }
);
SearchBox.displayName = "SearchBox";

export { SearchBox };
