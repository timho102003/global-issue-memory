"use client";

import { SearchX } from "lucide-react";
import { cn } from "@/lib/utils";
import { IssueCard } from "./issue-card";
import type { MasterIssue } from "@/types";

interface IssueCardListProps {
  issues: MasterIssue[];
  className?: string;
}

/**
 * Grid container for issue cards with an empty state.
 */
export function IssueCardList({ issues, className }: IssueCardListProps) {
  if (issues.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-16">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-bg-tertiary">
          <SearchX className="h-5 w-5 text-text-muted" />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-text-secondary">No issues found</p>
          <p className="mt-1 text-xs text-text-muted">
            Try adjusting your filters or search query
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("grid grid-cols-1 gap-4 lg:grid-cols-2", className)}>
      {issues.map((issue) => (
        <IssueCard key={issue.id} issue={issue} />
      ))}
    </div>
  );
}
