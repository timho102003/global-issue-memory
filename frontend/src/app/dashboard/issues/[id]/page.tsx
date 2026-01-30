"use client";

import { use } from "react";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { ChildIssuesList } from "@/components/issue/child-issues-list";
import { FixBundleCard } from "@/components/issue/fix-bundle-card";
import { TrustSignals } from "@/components/issue/trust-signals";
import { useIssue, useFixBundle } from "@/lib/hooks/use-issues";
import { CATEGORY_DISPLAY } from "@/types";
import type { RootCauseCategory } from "@/types";

/**
 * Issue Detail page matching GIM.pen design (qnZGX).
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

      {/* Content Row */}
      <div className="flex flex-1 flex-col gap-5 lg:flex-row lg:gap-6">
        {/* Left Column */}
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {/* Issue Card */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <CardTitle className="text-lg leading-snug sm:text-xl">
                  {issue.canonical_title}
                </CardTitle>
                <Badge
                  category={issue.root_cause_category.replace("_", "-") as "environment" | "model" | "api" | "codegen" | "framework"}
                >
                  {categoryInfo.label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-text-secondary">
                {issue.description}
              </p>
            </CardContent>
          </Card>

          {/* Metadata */}
          {(issue.model_provider || issue.language || issue.framework) && (
            <Card>
              <CardContent className="flex flex-wrap gap-x-6 gap-y-2 pt-5">
                {issue.model_provider && issue.model_provider !== "unknown" && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-text-muted">Provider:</span>
                    <span className="font-medium text-text-primary">
                      {issue.model_provider.charAt(0).toUpperCase() + issue.model_provider.slice(1)}
                    </span>
                  </div>
                )}
                {issue.language && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-text-muted">Language:</span>
                    <span className="font-medium text-text-primary">
                      {issue.language.charAt(0).toUpperCase() + issue.language.slice(1)}
                    </span>
                  </div>
                )}
                {issue.framework && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-text-muted">Framework:</span>
                    <span className="font-medium text-text-primary">
                      {issue.framework.charAt(0).toUpperCase() + issue.framework.slice(1)}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Trust Signals */}
          <TrustSignals
            verificationCount={issue.verification_count}
            successRate={issue.confidence_score}
            lastConfirmedAt={issue.last_confirmed_at}
          />

          {/* Child Issues (Contributions) */}
          {issue.child_issue_count > 0 && (
            <ChildIssuesList masterIssueId={id} />
          )}
        </div>

        {/* Right Column - Fix Bundle */}
        <div className="w-full lg:w-[380px]">
          {fixBundleLoading ? (
            <FixBundleSkeleton />
          ) : fixBundle ? (
            <FixBundleCard fixBundle={fixBundle} />
          ) : null}
        </div>
      </div>
    </main>
  );
}

/**
 * Full-page skeleton for issue detail loading state.
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

      <div className="flex flex-1 flex-col gap-5 lg:flex-row lg:gap-6">
        {/* Left Column */}
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {/* Issue Card skeleton */}
          <div className="rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)]">
            <div className="flex items-start justify-between gap-4">
              <div className="flex flex-1 flex-col gap-3">
                <div className="h-6 w-3/4 animate-pulse rounded bg-bg-tertiary" />
                <div className="h-4 w-full animate-pulse rounded bg-bg-tertiary" />
                <div className="h-4 w-2/3 animate-pulse rounded bg-bg-tertiary" />
              </div>
              <div className="h-6 w-20 animate-pulse rounded-full bg-bg-tertiary" />
            </div>
          </div>

          {/* Code block skeleton */}
          <div className="rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)]">
            <div className="mb-4 h-5 w-24 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-40 w-full animate-pulse rounded-xl bg-bg-tertiary" />
          </div>

          {/* Trust signals skeleton */}
          <div className="flex items-center gap-6 rounded-2xl border border-border-light/80 bg-white px-6 py-4 shadow-[var(--shadow-card)]">
            <div className="h-4 w-28 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-4 w-24 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-4 w-32 animate-pulse rounded bg-bg-tertiary" />
          </div>
        </div>

        {/* Right Column skeleton */}
        <div className="w-full lg:w-[380px]">
          <FixBundleSkeleton />
        </div>
      </div>
    </main>
  );
}

/**
 * Skeleton for the fix bundle sidebar card.
 */
function FixBundleSkeleton() {
  return (
    <div className="rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)]">
      <div className="mb-4 h-5 w-32 animate-pulse rounded bg-bg-tertiary" />
      <div className="flex flex-col gap-3">
        <div className="h-4 w-full animate-pulse rounded bg-bg-tertiary" />
        <div className="h-4 w-5/6 animate-pulse rounded bg-bg-tertiary" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-bg-tertiary" />
      </div>
      <div className="mt-6 flex flex-col gap-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="h-5 w-5 animate-pulse rounded-full bg-bg-tertiary" />
            <div className="h-4 flex-1 animate-pulse rounded bg-bg-tertiary" />
          </div>
        ))}
      </div>
    </div>
  );
}
