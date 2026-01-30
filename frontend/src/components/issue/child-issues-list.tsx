"use client";

import Link from "next/link";
import { ChevronRight, CheckCircle2, XCircle, Clock } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useChildIssues } from "@/lib/hooks/use-issues";
import { formatRelativeTime } from "@/lib/utils";
import type { ChildIssueListItem } from "@/types";

interface ChildIssuesListProps {
  masterIssueId: string;
}

/**
 * List of child issues (contributions) for a master issue.
 * Only renders when children exist; hides itself on empty results.
 */
export function ChildIssuesList({ masterIssueId }: ChildIssuesListProps) {
  const { data, isLoading } = useChildIssues(masterIssueId);

  if (isLoading) {
    return <ChildIssuesListSkeleton />;
  }

  if (!data || data.children.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            Contributions ({data.total})
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-1 p-0 pb-2">
        {data.children.map((child) => (
          <ChildIssueRow
            key={child.id}
            child={child}
            masterIssueId={masterIssueId}
          />
        ))}
      </CardContent>
    </Card>
  );
}

function ChildIssueRow({
  child,
  masterIssueId,
}: {
  child: ChildIssueListItem;
  masterIssueId: string;
}) {
  return (
    <Link
      href={`/dashboard/issues/${masterIssueId}/child/${child.id}`}
      className="group flex items-center gap-3 px-5 py-3 transition-colors duration-150 hover:bg-bg-tertiary/50 sm:px-6"
    >
      {/* Validation status icon */}
      <div className="shrink-0">
        {child.validation_success === true ? (
          <CheckCircle2 className="h-4 w-4 text-success-foreground" />
        ) : child.validation_success === false ? (
          <XCircle className="h-4 w-4 text-error-foreground" />
        ) : (
          <Clock className="h-4 w-4 text-text-muted" />
        )}
      </div>

      {/* Error text */}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-text-primary">
          {child.original_error || "No error message"}
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          {child.provider && (
            <span className="text-xs text-text-muted">{child.provider}</span>
          )}
          {child.language && (
            <span className="text-xs text-text-muted">{child.language}</span>
          )}
          {child.framework && (
            <span className="text-xs text-text-muted">{child.framework}</span>
          )}
          {child.submitted_at && (
            <span className="text-xs text-text-muted">
              {formatRelativeTime(child.submitted_at)}
            </span>
          )}
        </div>
      </div>

      {/* Contribution type badge */}
      {child.contribution_type && (
        <Badge variant="outline" className="hidden shrink-0 sm:inline-flex">
          {child.contribution_type}
        </Badge>
      )}

      {/* Chevron */}
      <ChevronRight className="h-4 w-4 shrink-0 text-text-muted opacity-0 transition-opacity duration-150 group-hover:opacity-100" />
    </Link>
  );
}

/**
 * Skeleton loading state for the child issues list.
 */
function ChildIssuesListSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-5 w-36 animate-pulse rounded bg-bg-tertiary" />
      </CardHeader>
      <CardContent className="flex flex-col gap-1 p-0 pb-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 px-5 py-3 sm:px-6">
            <div className="h-4 w-4 animate-pulse rounded-full bg-bg-tertiary" />
            <div className="min-w-0 flex-1">
              <div className="h-4 w-3/4 animate-pulse rounded bg-bg-tertiary" />
              <div className="mt-1.5 h-3 w-1/2 animate-pulse rounded bg-bg-tertiary" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
