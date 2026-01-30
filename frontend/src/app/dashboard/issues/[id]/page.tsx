"use client";

import { use } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Users } from "lucide-react";
import { ChildIssuesList } from "@/components/issue/child-issues-list";
import { FixBundleCard } from "@/components/issue/fix-bundle-card";
import { TrustSignals } from "@/components/issue/trust-signals";
import { useIssue, useFixBundle } from "@/lib/hooks/use-issues";
import { CATEGORY_DISPLAY } from "@/types";
import type { RootCauseCategory } from "@/types";
import type { BadgeProps } from "@/components/ui/badge";

const CATEGORY_TO_BADGE: Record<RootCauseCategory, BadgeProps["category"]> = {
  environment: "environment",
  model_behavior: "model",
  api_integration: "api",
  code_generation: "codegen",
  framework_specific: "framework",
};

/**
 * Issue Detail page — full-width stacked layout with compact header.
 */
export default function IssueDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: issue, isLoading: issueLoading } = useIssue(id);
  const { data: fixBundle, isLoading: fixBundleLoading } = useFixBundle(id);

  if (issueLoading || !issue) {
    return <IssueDetailSkeleton />;
  }

  const categoryInfo = CATEGORY_DISPLAY[issue.root_cause_category];

  return (
    <main className="flex flex-1 flex-col gap-6 py-6 sm:py-8">
      {/* Breadcrumbs */}
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/dashboard/issues">Issues</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator>/</BreadcrumbSeparator>
          <BreadcrumbItem>
            <BreadcrumbLink href={`/dashboard/issues?category=${issue.root_cause_category}`}>
              {categoryInfo.label}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator>/</BreadcrumbSeparator>
          <BreadcrumbItem>
            <BreadcrumbPage>{issue.canonical_title}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      {/* Compact Issue Header Card */}
      <div className="flex flex-col gap-4 rounded-2xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-card)] sm:p-6">
        {/* Row 1: Badges + Confidence */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              category={CATEGORY_TO_BADGE[issue.root_cause_category]}
            >
              {categoryInfo.label}
            </Badge>
            {issue.child_issue_count > 0 && (
              <Badge variant="secondary">
                <Users className="mr-1 h-3 w-3" />
                {issue.child_issue_count} contribution{issue.child_issue_count !== 1 ? "s" : ""}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <div
              role="meter"
              aria-label="Confidence score"
              aria-valuenow={Math.round(issue.confidence_score * 100)}
              aria-valuemin={0}
              aria-valuemax={100}
              className="h-2 w-20 overflow-hidden rounded-full bg-bg-tertiary"
            >
              <div
                className="h-full rounded-full bg-accent-warm transition-all duration-200"
                style={{ width: `${Math.round(issue.confidence_score * 100)}%` }}
                aria-hidden="true"
              />
            </div>
            <span className="text-sm font-medium text-text-primary">
              {Math.round(issue.confidence_score * 100)}%
            </span>
          </div>
        </div>

        {/* Row 2: Title */}
        <h1 className="text-xl font-semibold leading-snug text-text-primary sm:text-2xl">
          {issue.canonical_title}
        </h1>

        {/* Row 3: Description */}
        <p className="text-sm leading-relaxed text-text-secondary">
          {issue.description}
        </p>

        {/* Row 4: Metadata pills + Trust Signals */}
        {(issue.model_provider || issue.language || issue.framework || issue.verification_count > 0) && (
          <div className="flex flex-wrap items-center gap-3 border-t border-border-light/60 pt-4">
            {/* Metadata pills */}
            {issue.model_provider && issue.model_provider !== "unknown" && (
              <span className="rounded-md bg-bg-tertiary px-2.5 py-1 text-xs font-medium text-text-primary">
                {issue.model_provider.charAt(0).toUpperCase() + issue.model_provider.slice(1)}
              </span>
            )}
            {issue.language && (
              <span className="rounded-md bg-bg-tertiary px-2.5 py-1 text-xs font-medium text-text-primary">
                {issue.language.charAt(0).toUpperCase() + issue.language.slice(1)}
              </span>
            )}
            {issue.framework && (
              <span className="rounded-md bg-bg-tertiary px-2.5 py-1 text-xs font-medium text-text-primary">
                {issue.framework.charAt(0).toUpperCase() + issue.framework.slice(1)}
              </span>
            )}

            {/* Divider before trust signals */}
            {(issue.model_provider || issue.language || issue.framework) && (
              <div className="hidden h-4 w-px bg-border-light sm:block" />
            )}

            {/* Inline trust signals */}
            <TrustSignals
              verificationCount={issue.verification_count}
              successRate={issue.confidence_score}
              lastConfirmedAt={issue.last_confirmed_at}
              variant="inline"
            />
          </div>
        )}
      </div>

      {/* Fix Bundle — full width */}
      {fixBundleLoading ? (
        <FixBundleSkeleton />
      ) : fixBundle ? (
        <FixBundleCard fixBundle={fixBundle} />
      ) : null}

      {/* Community + Child Issues */}
      {issue.child_issue_count > 0 && (
        <>
          <div className="flex items-center gap-2 rounded-xl border border-cat-environment/20 bg-cat-environment/5 px-4 py-3">
            <Users className="h-4 w-4 text-cat-environment" />
            <p className="text-sm text-text-secondary">
              Community has reported{" "}
              <span className="font-medium text-text-primary">
                {issue.child_issue_count}
              </span>{" "}
              similar experience{issue.child_issue_count !== 1 ? "s" : ""}
            </p>
          </div>
          <ChildIssuesList masterIssueId={id} />
        </>
      )}
    </main>
  );
}

/**
 * Full-page skeleton for issue detail loading state — stacked layout.
 */
function IssueDetailSkeleton() {
  return (
    <main className="flex flex-1 flex-col gap-6 py-6 sm:py-8">
      {/* Breadcrumb skeleton */}
      <div className="flex items-center gap-2">
        <div className="h-4 w-14 animate-pulse rounded bg-bg-tertiary" />
        <span className="text-text-muted">/</span>
        <div className="h-4 w-20 animate-pulse rounded bg-bg-tertiary" />
        <span className="text-text-muted">/</span>
        <div className="h-4 w-48 animate-pulse rounded bg-bg-tertiary" />
      </div>

      {/* Compact header skeleton */}
      <div className="rounded-2xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-card)] sm:p-6">
        <div className="flex flex-col gap-4">
          {/* Badges row */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <div className="h-6 w-20 animate-pulse rounded-full bg-bg-tertiary" />
              <div className="h-6 w-28 animate-pulse rounded-full bg-bg-tertiary" />
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-20 animate-pulse rounded-full bg-bg-tertiary" />
              <div className="h-4 w-8 animate-pulse rounded bg-bg-tertiary" />
            </div>
          </div>
          {/* Title */}
          <div className="h-7 w-3/4 animate-pulse rounded bg-bg-tertiary" />
          {/* Description */}
          <div className="flex flex-col gap-2">
            <div className="h-4 w-full animate-pulse rounded bg-bg-tertiary" />
            <div className="h-4 w-2/3 animate-pulse rounded bg-bg-tertiary" />
          </div>
          {/* Metadata row */}
          <div className="flex items-center gap-3 border-t border-border-light/60 pt-4">
            <div className="h-6 w-16 animate-pulse rounded-md bg-bg-tertiary" />
            <div className="h-6 w-14 animate-pulse rounded-md bg-bg-tertiary" />
            <div className="h-6 w-18 animate-pulse rounded-md bg-bg-tertiary" />
            <div className="hidden h-4 w-px bg-border-light sm:block" />
            <div className="h-4 w-28 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-4 w-24 animate-pulse rounded bg-bg-tertiary" />
          </div>
        </div>
      </div>

      {/* Fix bundle skeleton */}
      <FixBundleSkeleton />
    </main>
  );
}

/**
 * Skeleton for the fix bundle card — full-width with section placeholders.
 */
function FixBundleSkeleton() {
  return (
    <div className="flex flex-col gap-6 rounded-2xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-card)] sm:p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="h-5 w-5 animate-pulse rounded bg-bg-tertiary" />
        <div className="h-5 w-36 animate-pulse rounded bg-bg-tertiary" />
      </div>
      {/* Summary */}
      <div className="flex flex-col gap-2">
        <div className="h-4 w-full animate-pulse rounded bg-bg-tertiary" />
        <div className="h-4 w-5/6 animate-pulse rounded bg-bg-tertiary" />
      </div>
      {/* Fix steps */}
      <div className="flex flex-col gap-3">
        <div className="h-4 w-20 animate-pulse rounded bg-bg-tertiary" />
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-xl border border-border-light/60 bg-bg-muted/30 p-4"
          >
            <div className="h-6 w-6 animate-pulse rounded-full bg-bg-tertiary" />
            <div className="h-4 flex-1 animate-pulse rounded bg-bg-tertiary" />
          </div>
        ))}
      </div>
      {/* Code changes */}
      <div className="flex flex-col gap-3">
        <div className="h-4 w-28 animate-pulse rounded bg-bg-tertiary" />
        <div className="h-12 w-full animate-pulse rounded-xl bg-bg-tertiary" />
        <div className="h-12 w-full animate-pulse rounded-xl bg-bg-tertiary" />
      </div>
    </div>
  );
}
