"use client";

import Link from "next/link";
import { Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { ConfidenceMeter } from "./confidence-meter";
import { formatRelativeTime } from "@/lib/utils";
import type { MasterIssue, RootCauseCategory } from "@/types";
import { CATEGORY_DISPLAY, STATUS_DISPLAY } from "@/types";

const categoryToBadge: Record<RootCauseCategory, NonNullable<BadgeProps["category"]>> = {
  environment: "environment",
  model_behavior: "model",
  api_integration: "api",
  code_generation: "codegen",
  framework_specific: "framework",
};

const DEFAULT_CATEGORY_INFO = { label: "Other", color: "cat-environment" };

interface IssueCardProps {
  issue: MasterIssue;
  className?: string;
}

/**
 * Card component for a single issue in the issues list.
 * Surfaces fix preview, confidence, and contribution count directly.
 */
export function IssueCard({ issue, className }: IssueCardProps) {
  const categoryInfo =
    CATEGORY_DISPLAY[issue.root_cause_category as RootCauseCategory] || DEFAULT_CATEGORY_INFO;
  const statusInfo =
    STATUS_DISPLAY[issue.status] || { label: "Unknown", variant: "warning" as const };
  const badgeCategory =
    categoryToBadge[issue.root_cause_category as RootCauseCategory] || "environment";

  const providerDisplay =
    issue.model_provider && issue.model_provider !== "unknown"
      ? issue.model_provider.charAt(0).toUpperCase() + issue.model_provider.slice(1)
      : null;

  return (
    <Link
      href={`/dashboard/issues/${issue.id}`}
      className={cn(
        "group flex flex-col gap-3 rounded-2xl border border-border-light/80 bg-white p-4 sm:p-5",
        "shadow-[var(--shadow-card)] transition-all duration-200",
        "hover:shadow-[var(--shadow-card-hover)] hover:border-border-medium",
        className,
      )}
    >
      {/* Top row: category badge + status + confidence */}
      <div className="flex items-center justify-between gap-2">
        <Badge category={badgeCategory}>{categoryInfo.label}</Badge>
        <div className="flex items-center gap-2.5">
          <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
          <ConfidenceMeter value={issue.confidence_score} />
        </div>
      </div>

      {/* Title */}
      <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-text-primary group-hover:text-primary transition-colors duration-200">
        {issue.canonical_title || "Untitled Issue"}
      </h3>

      {/* Footer: metadata */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-muted">
        {providerDisplay && <span>{providerDisplay}</span>}
        {issue.child_issue_count > 0 && (
          <span className="flex items-center gap-1 text-text-secondary">
            <Users className="h-3 w-3" />
            {issue.child_issue_count} contribution{issue.child_issue_count !== 1 ? "s" : ""}
          </span>
        )}
        {issue.verification_count > 0 && (
          <span className="text-cat-environment">
            {issue.verification_count} verified
          </span>
        )}
        {issue.updated_at && (
          <span>{formatRelativeTime(issue.updated_at)}</span>
        )}
      </div>
    </Link>
  );
}
