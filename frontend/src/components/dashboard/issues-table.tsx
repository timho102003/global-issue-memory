"use client";

import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { formatDate, formatPercentage } from "@/lib/utils";
import type { MasterIssue, RootCauseCategory } from "@/types";
import { CATEGORY_DISPLAY, STATUS_DISPLAY } from "@/types";

// Map RootCauseCategory to Badge category prop
const categoryToBadge: Record<RootCauseCategory, NonNullable<BadgeProps["category"]>> = {
  environment: "environment",
  model_behavior: "model",
  api_integration: "api",
  code_generation: "codegen",
  framework_specific: "framework",
};

// Fallback display info for unknown categories
const DEFAULT_CATEGORY_INFO = { label: "Other", color: "cat-environment" };

interface IssuesTableProps {
  issues: MasterIssue[];
}

/**
 * Issues table component matching GIM.pen Issue Explorer design.
 * Renders a table on md+ screens, card list on mobile.
 */
export function IssuesTable({ issues }: IssuesTableProps) {
  return (
    <>
      {/* Desktop: table layout */}
      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow className="border-border-soft hover:bg-transparent">
              <TableHead>Issue</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Updated</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {issues.map((issue) => (
              <IssueRow key={issue.id} issue={issue} />
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile: card layout */}
      <div className="divide-y divide-border-soft md:hidden">
        {issues.map((issue) => (
          <IssueCard key={issue.id} issue={issue} />
        ))}
      </div>
    </>
  );
}

/**
 * Single issue row for the desktop table view.
 */
function IssueRow({ issue }: { issue: MasterIssue }) {
  const categoryInfo =
    CATEGORY_DISPLAY[issue.root_cause_category as RootCauseCategory] || DEFAULT_CATEGORY_INFO;
  const statusInfo =
    STATUS_DISPLAY[issue.status] || { label: "Unknown", variant: "warning" as const };
  const badgeCategory =
    categoryToBadge[issue.root_cause_category as RootCauseCategory] || "environment";

  return (
    <TableRow>
      <TableCell>
        <Link
          href={`/dashboard/issues/${issue.id}`}
          className="font-medium text-text-primary transition-colors duration-200 hover:text-primary"
        >
          {issue.canonical_title || "Untitled Issue"}
        </Link>
      </TableCell>
      <TableCell>
        <Badge category={badgeCategory}>{categoryInfo.label}</Badge>
      </TableCell>
      <TableCell className="text-text-secondary">
        {issue.model_provider && issue.model_provider !== "unknown"
          ? issue.model_provider.charAt(0).toUpperCase() + issue.model_provider.slice(1)
          : "-"}
      </TableCell>
      <TableCell className="text-text-secondary">
        {formatPercentage(issue.confidence_score)}
      </TableCell>
      <TableCell className="text-text-muted">{formatDate(issue.updated_at)}</TableCell>
      <TableCell>
        <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
      </TableCell>
    </TableRow>
  );
}

/**
 * Single issue card for the mobile view.
 */
function IssueCard({ issue }: { issue: MasterIssue }) {
  const categoryInfo =
    CATEGORY_DISPLAY[issue.root_cause_category as RootCauseCategory] || DEFAULT_CATEGORY_INFO;
  const statusInfo =
    STATUS_DISPLAY[issue.status] || { label: "Unknown", variant: "warning" as const };
  const badgeCategory =
    categoryToBadge[issue.root_cause_category as RootCauseCategory] || "environment";

  return (
    <Link
      href={`/dashboard/issues/${issue.id}`}
      className="block px-4 py-4 transition-colors duration-200 active:bg-bg-muted/40 sm:px-5"
    >
      {/* Title */}
      <p className="text-sm font-medium leading-snug text-text-primary">
        {issue.canonical_title || "Untitled Issue"}
      </p>

      {/* Badges row */}
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <Badge category={badgeCategory}>{categoryInfo.label}</Badge>
        <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
      </div>

      {/* Metadata row */}
      <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-muted">
        {issue.model_provider && issue.model_provider !== "unknown" && (
          <span>
            {issue.model_provider.charAt(0).toUpperCase() + issue.model_provider.slice(1)}
          </span>
        )}
        <span>{formatPercentage(issue.confidence_score)} confidence</span>
        <span>{formatDate(issue.updated_at)}</span>
      </div>
    </Link>
  );
}
