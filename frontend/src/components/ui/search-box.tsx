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
            "flex h-10 w-full rounded-xl border border-border bg-white pl-10 pr-4 py-2",
            "text-sm placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
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
