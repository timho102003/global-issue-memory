"use client";

import { use } from "react";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CodeBlock } from "@/components/ui/code-block";
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { FixBundleCard } from "@/components/issue/fix-bundle-card";
import { useChildIssue, useFixBundle } from "@/lib/hooks/use-issues";
import { CATEGORY_DISPLAY } from "@/types";
import type { RootCauseCategory } from "@/types";
import { formatRelativeTime } from "@/lib/utils";

/**
 * Child issue detail page.
 * Only reachable from a master issue page via the contributions list.
 */
export default function ChildIssueDetailPage({
  params,
}: {
  params: Promise<{ id: string; childId: string }>;
}) {
  const { id: masterIssueId, childId } = use(params);
  const { data: child, isLoading: childLoading } = useChildIssue(childId);
  const { data: fixBundle, isLoading: fixBundleLoading } =
    useFixBundle(childId);

  if (childLoading || !child) {
    return <ChildDetailSkeleton />;
  }

  const parentTitle = child.parent_canonical_title || "Parent Issue";
  const parentCategory = child.parent_root_cause_category;
  const categoryInfo = parentCategory
    ? CATEGORY_DISPLAY[parentCategory]
    : null;

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
            <BreadcrumbLink href={`/dashboard/issues/${masterIssueId}`}>
              {parentTitle}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator>/</BreadcrumbSeparator>
          <BreadcrumbItem>
            <BreadcrumbPage>Contribution</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      {/* Content Row */}
      <div className="flex flex-1 flex-col gap-5 lg:flex-row lg:gap-6">
        {/* Left Column */}
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {/* Error Card */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <CardTitle className="text-lg leading-snug sm:text-xl">
                  {child.original_error || "Contribution Detail"}
                </CardTitle>
                {categoryInfo && (
                  <Badge
                    category={
                      (parentCategory?.replace("_", "-") || "environment") as
                        | "environment"
                        | "model"
                        | "api"
                        | "codegen"
                        | "framework"
                    }
                  >
                    {categoryInfo.label}
                  </Badge>
                )}
              </div>
            </CardHeader>
            {child.original_context && (
              <CardContent>
                <p className="text-sm leading-relaxed text-text-secondary">
                  {child.original_context}
                </p>
              </CardContent>
            )}
          </Card>

          {/* Metadata */}
          <Card>
            <CardContent className="flex flex-wrap gap-x-6 gap-y-2 pt-5">
              {child.provider && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-muted">Provider:</span>
                  <span className="font-medium text-text-primary">
                    {child.provider.charAt(0).toUpperCase() +
                      child.provider.slice(1)}
                  </span>
                </div>
              )}
              {child.model && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-muted">Model:</span>
                  <span className="font-medium text-text-primary">
                    {child.model}
                  </span>
                </div>
              )}
              {child.language && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-muted">Language:</span>
                  <span className="font-medium text-text-primary">
                    {child.language.charAt(0).toUpperCase() +
                      child.language.slice(1)}
                  </span>
                </div>
              )}
              {child.framework && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-muted">Framework:</span>
                  <span className="font-medium text-text-primary">
                    {child.framework.charAt(0).toUpperCase() +
                      child.framework.slice(1)}
                  </span>
                </div>
              )}
              {child.submitted_at && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-muted">Submitted:</span>
                  <span className="font-medium text-text-primary">
                    {formatRelativeTime(child.submitted_at)}
                  </span>
                </div>
              )}
              {child.contribution_type && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-muted">Type:</span>
                  <Badge variant="outline">{child.contribution_type}</Badge>
                </div>
              )}
              {child.validation_success !== null &&
                child.validation_success !== undefined && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-text-muted">Validation:</span>
                    <Badge
                      variant={child.validation_success ? "success" : "error"}
                    >
                      {child.validation_success ? "Passed" : "Failed"}
                    </Badge>
                  </div>
                )}
            </CardContent>
          </Card>

          {/* Code Snippet */}
          {child.code_snippet ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Code Snippet</CardTitle>
              </CardHeader>
              <CardContent>
                <CodeBlock
                  code={child.code_snippet}
                  language={child.language || "text"}
                />
              </CardContent>
            </Card>
          ) : null}
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
 * Full-page skeleton for child issue detail loading state.
 */
function ChildDetailSkeleton() {
  return (
    <main className="flex flex-1 flex-col gap-6 py-6 sm:py-8">
      {/* Breadcrumb skeleton */}
      <div className="flex items-center gap-2">
        <div className="h-4 w-14 animate-pulse rounded bg-bg-tertiary" />
        <span className="text-text-muted">/</span>
        <div className="h-4 w-32 animate-pulse rounded bg-bg-tertiary" />
        <span className="text-text-muted">/</span>
        <div className="h-4 w-24 animate-pulse rounded bg-bg-tertiary" />
      </div>

      <div className="flex flex-1 flex-col gap-5 lg:flex-row lg:gap-6">
        {/* Left Column */}
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {/* Error card skeleton */}
          <div className="rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)]">
            <div className="flex items-start justify-between gap-4">
              <div className="flex flex-1 flex-col gap-3">
                <div className="h-6 w-3/4 animate-pulse rounded bg-bg-tertiary" />
                <div className="h-4 w-full animate-pulse rounded bg-bg-tertiary" />
              </div>
              <div className="h-6 w-20 animate-pulse rounded-full bg-bg-tertiary" />
            </div>
          </div>

          {/* Metadata skeleton */}
          <div className="rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)]">
            <div className="flex flex-wrap gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="h-4 w-28 animate-pulse rounded bg-bg-tertiary"
                />
              ))}
            </div>
          </div>

          {/* Code block skeleton */}
          <div className="rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)]">
            <div className="mb-4 h-5 w-28 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-40 w-full animate-pulse rounded-xl bg-bg-tertiary" />
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
