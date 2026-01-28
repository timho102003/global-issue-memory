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
import { Checkbox } from "@/components/ui/checkbox";
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
  selectedIds?: string[];
  onSelectionChange?: (ids: string[]) => void;
}

/**
 * Issues table component matching GIM.pen Issue Explorer design.
 */
export function IssuesTable({
  issues,
  selectedIds = [],
  onSelectionChange,
}: IssuesTableProps) {
  const toggleSelection = (id: string) => {
    if (!onSelectionChange) return;
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((i) => i !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  const toggleAll = () => {
    if (!onSelectionChange) return;
    if (selectedIds.length === issues.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(issues.map((i) => i.id));
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow className="border-border-soft hover:bg-transparent">
          <TableHead className="w-12">
            <Checkbox
              checked={selectedIds.length === issues.length && issues.length > 0}
              onChange={toggleAll}
            />
          </TableHead>
          <TableHead>Issue</TableHead>
          <TableHead>Category</TableHead>
          <TableHead>Provider</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Updated</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {issues.map((issue) => {
          const categoryInfo = CATEGORY_DISPLAY[issue.root_cause_category as RootCauseCategory] || DEFAULT_CATEGORY_INFO;
          const statusInfo = STATUS_DISPLAY[issue.status] || { label: "Unknown", variant: "warning" as const };
          const badgeCategory = categoryToBadge[issue.root_cause_category as RootCauseCategory] || "environment";

          return (
            <TableRow key={issue.id}>
              <TableCell>
                <Checkbox
                  checked={selectedIds.includes(issue.id)}
                  onChange={() => toggleSelection(issue.id)}
                />
              </TableCell>
              <TableCell>
                <Link
                  href={`/dashboard/issues/${issue.id}`}
                  className="font-medium text-text-primary hover:text-primary"
                >
                  {issue.canonical_title || "Untitled Issue"}
                </Link>
              </TableCell>
              <TableCell>
                <Badge category={badgeCategory}>
                  {categoryInfo.label}
                </Badge>
              </TableCell>
              <TableCell className="text-text-secondary">
                {issue.environment_coverage.length > 0
                  ? issue.environment_coverage[0]
                  : "-"}
              </TableCell>
              <TableCell className="text-text-secondary">
                {formatPercentage(issue.confidence_score)}
              </TableCell>
              <TableCell className="text-text-muted">
                {formatDate(issue.updated_at)}
              </TableCell>
              <TableCell>
                <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
