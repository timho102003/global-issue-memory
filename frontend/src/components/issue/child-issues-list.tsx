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
 * Compute validation summary from child issues.
 */
function getValidationSummary(children: ChildIssueListItem[]) {
  let passed = 0;
  let failed = 0;
  let pending = 0;
  for (const c of children) {
    if (c.validation_success === true) passed++;
    else if (c.validation_success === false) failed++;
    else pending++;
  }
  return { passed, failed, pending, total: children.length };
}

/**
 * List of child issues (contributions) for a master issue.
 * Renders as mini-cards with validation summary, metadata chips, and status badges.
 */
export function ChildIssuesList({ masterIssueId }: ChildIssuesListProps) {
  const { data, isLoading } = useChildIssues(masterIssueId);

  if (isLoading) {
    return <ChildIssuesListSkeleton />;
  }

  if (!data || data.children.length === 0) {
    return null;
  }

  const summary = getValidationSummary(data.children);

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-base">
            Contributions ({data.total})
          </CardTitle>
          {/* Validation summary bar */}
          <div className="flex items-center gap-3 text-xs">
            {summary.passed > 0 && (
              <span className="flex items-center gap-1 text-success-foreground">
                <CheckCircle2 className="h-3.5 w-3.5" />
                {summary.passed} passed
              </span>
            )}
            {summary.failed > 0 && (
              <span className="flex items-center gap-1 text-error-foreground">
                <XCircle className="h-3.5 w-3.5" />
                {summary.failed} failed
              </span>
            )}
            {summary.pending > 0 && (
              <span className="flex items-center gap-1 text-text-muted">
                <Clock className="h-3.5 w-3.5" />
                {summary.pending} pending
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 p-0 px-3 pb-3 sm:px-4 sm:pb-4">
        {data.children.map((child) => (
          <ChildIssueCard
            key={child.id}
            child={child}
            masterIssueId={masterIssueId}
          />
        ))}
      </CardContent>
    </Card>
  );
}

/**
 * Validation badge with color-coded background.
 */
function ValidationBadge({ success }: { success: boolean | null }) {
  if (success === true) {
    return <Badge variant="success">Passed</Badge>;
  }
  if (success === false) {
    return <Badge variant="error">Failed</Badge>;
  }
  return <Badge variant="warning">Pending</Badge>;
}

/**
 * Validation status icon with colored background circle.
 */
function ValidationIcon({ success }: { success: boolean | null }) {
  if (success === true) {
    return (
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-success">
        <CheckCircle2 className="h-4 w-4 text-success-foreground" />
      </div>
    );
  }
  if (success === false) {
    return (
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-error">
        <XCircle className="h-4 w-4 text-error-foreground" />
      </div>
    );
  }
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-warning">
      <Clock className="h-4 w-4 text-warning-foreground" />
    </div>
  );
}

/**
 * Mini-card for a single child issue contribution.
 */
function ChildIssueCard({
  child,
  masterIssueId,
}: {
  child: ChildIssueListItem;
  masterIssueId: string;
}) {
  return (
    <Link
      href={`/dashboard/issues/${masterIssueId}/child/${child.id}`}
      className="group flex items-start gap-3 rounded-xl border border-border-soft bg-white p-3 transition-all duration-200 hover:border-border-medium hover:bg-bg-muted/30 sm:p-4"
    >
      {/* Validation icon */}
      <ValidationIcon success={child.validation_success} />

      {/* Content */}
      <div className="min-w-0 flex-1">
        {/* Error message */}
        <p className="line-clamp-2 text-sm leading-snug text-text-primary">
          {child.original_error || "No error message"}
        </p>

        {/* Metadata chips */}
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {child.provider && (
            <span className="rounded-md bg-bg-tertiary px-1.5 py-0.5 text-[11px] font-medium text-text-secondary">
              {child.provider}
            </span>
          )}
          {child.language && (
            <span className="rounded-md bg-bg-tertiary px-1.5 py-0.5 text-[11px] font-medium text-text-secondary">
              {child.language}
            </span>
          )}
          {child.framework && (
            <span className="rounded-md bg-bg-tertiary px-1.5 py-0.5 text-[11px] font-medium text-text-secondary">
              {child.framework}
            </span>
          )}
          {child.submitted_at && (
            <span className="text-[11px] text-text-muted">
              {formatRelativeTime(child.submitted_at)}
            </span>
          )}
        </div>
      </div>

      {/* Validation badge + chevron */}
      <div className="flex shrink-0 items-center gap-2">
        <ValidationBadge success={child.validation_success} />
        <ChevronRight className="h-4 w-4 text-text-muted opacity-0 transition-opacity duration-150 group-hover:opacity-100" />
      </div>
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
        <div className="flex items-center justify-between">
          <div className="h-5 w-36 animate-pulse rounded bg-bg-tertiary" />
          <div className="flex items-center gap-3">
            <div className="h-4 w-16 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-4 w-16 animate-pulse rounded bg-bg-tertiary" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 p-0 px-3 pb-3 sm:px-4 sm:pb-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-xl border border-border-soft bg-white p-3 sm:p-4"
          >
            <div className="h-8 w-8 animate-pulse rounded-full bg-bg-tertiary" />
            <div className="min-w-0 flex-1">
              <div className="h-4 w-3/4 animate-pulse rounded bg-bg-tertiary" />
              <div className="mt-2 flex gap-1.5">
                <div className="h-5 w-14 animate-pulse rounded-md bg-bg-tertiary" />
                <div className="h-5 w-16 animate-pulse rounded-md bg-bg-tertiary" />
                <div className="h-5 w-12 animate-pulse rounded-md bg-bg-tertiary" />
              </div>
            </div>
            <div className="h-6 w-16 animate-pulse rounded-full bg-bg-tertiary" />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
