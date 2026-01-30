"use client";

import { useState, useCallback } from "react";
import { Select } from "@/components/ui/select";
import { SearchBox } from "@/components/ui/search-box";
import { IssuesTable } from "@/components/dashboard/issues-table";
import { Button } from "@/components/ui/button";
import { useIssueSearch } from "@/lib/hooks/use-issues";

const PAGE_SIZE = 10;

/**
 * Generate page numbers with ellipsis for pagination.
 *
 * @param current - Current page (0-indexed)
 * @param total - Total number of pages
 * @returns Array of page numbers and ellipsis markers (-1)
 */
function generatePageNumbers(current: number, total: number): number[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i);
  }

  const pages: number[] = [0];

  if (current > 2) {
    pages.push(-1); // ellipsis
  }

  const start = Math.max(1, current - 1);
  const end = Math.min(total - 2, current + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  if (current < total - 3) {
    pages.push(-1); // ellipsis
  }

  pages.push(total - 1);

  return pages;
}

/**
 * Issue Explorer page matching GIM.pen design (yHuOd).
 */
export default function IssuesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [provider, setProvider] = useState<string>("all");
  const [timeRange, setTimeRange] = useState<string>("all");
  const [page, setPage] = useState(0);

  const isSearchActive = !!search;

  const { data, isLoading } = useIssueSearch({
    query: search || undefined,
    category: category !== "all" ? category : undefined,
    status: status !== "all" ? status : undefined,
    provider: provider !== "all" ? provider : undefined,
    time_range: timeRange !== "all" ? (timeRange as "1d" | "7d" | "30d" | "90d") : undefined,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  });

  const issues = data?.issues ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const rangeStart = page * PAGE_SIZE + 1;
  const rangeEnd = Math.min((page + 1) * PAGE_SIZE, total);
  const showPagination = !isSearchActive && totalPages > 1;

  const resetPage = useCallback(() => setPage(0), []);

  return (
    <main className="flex flex-1 flex-col gap-6 py-6 sm:py-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary sm:text-[28px]">Issues</h1>
      </div>

      {/* Issues Card */}
      <div className="flex flex-col overflow-hidden rounded-2xl border border-border-light/80 bg-white shadow-[var(--shadow-card)]">
        {/* Filters */}
        <div className="flex flex-col gap-3 border-b border-border-soft px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:py-5">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <Select
              value={category}
              onChange={(e) => { setCategory(e.target.value); resetPage(); }}
              className="w-full sm:w-[140px]"
            >
              <option value="all">All Categories</option>
              <option value="environment">Environment</option>
              <option value="model_behavior">Model</option>
              <option value="api_integration">API</option>
              <option value="code_generation">Codegen</option>
              <option value="framework_specific">Framework</option>
            </Select>
            <Select
              value={provider}
              onChange={(e) => { setProvider(e.target.value); resetPage(); }}
              className="w-full sm:w-[140px]"
            >
              <option value="all">All Providers</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="google">Google</option>
              <option value="mistral">Mistral</option>
            </Select>
            <Select
              value={status}
              onChange={(e) => { setStatus(e.target.value); resetPage(); }}
              className="w-full sm:w-[120px]"
            >
              <option value="all">All Status</option>
              <option value="active">Verified</option>
              <option value="superseded">Pending</option>
              <option value="invalid">Declined</option>
            </Select>
            <Select
              value={timeRange}
              onChange={(e) => { setTimeRange(e.target.value); resetPage(); }}
              className="w-full sm:w-[140px]"
            >
              <option value="all">All Time</option>
              <option value="1d">Last 24 Hours</option>
              <option value="7d">Past 7 Days</option>
              <option value="30d">Past 30 Days</option>
              <option value="90d">Past 90 Days</option>
            </Select>
          </div>
          <SearchBox
            placeholder="Search issues..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); resetPage(); }}
            className="w-full sm:w-[260px]"
          />
        </div>

        {/* Issue count */}
        <div className="flex items-center justify-between border-b border-border-soft px-5 py-3 sm:px-6 sm:py-3.5">
          <span className="text-[13px] text-text-muted">
            {isLoading
              ? "Loading..."
              : isSearchActive
                ? `${issues.length} results`
                : total === 0
                  ? "0 issues"
                  : `Showing ${rangeStart}\u2013${rangeEnd} of ${total} issues`}
          </span>
        </div>

        {/* Table / Card list */}
        <div className="flex-1 overflow-auto">
          {isLoading ? (
            <IssuesTableSkeleton />
          ) : (
            <IssuesTable issues={issues} />
          )}
        </div>

        {/* Pagination */}
        {showPagination && (
          <div className="flex items-center justify-center gap-1.5 border-t border-border-soft px-5 py-3 sm:px-6 sm:py-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              Previous
            </Button>

            <div className="flex items-center gap-1">
              {generatePageNumbers(page, totalPages).map((p, idx) =>
                p === -1 ? (
                  <span
                    key={`ellipsis-${idx}`}
                    className="flex h-8 w-8 items-center justify-center text-xs text-text-muted"
                  >
                    &hellip;
                  </span>
                ) : (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium transition-colors duration-150 ${
                      p === page
                        ? "bg-[#2D2A26] text-white"
                        : "text-text-secondary hover:bg-bg-tertiary"
                    }`}
                  >
                    {p + 1}
                  </button>
                )
              )}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
            >
              Next
            </Button>
          </div>
        )}
      </div>
    </main>
  );
}

/**
 * Skeleton loading state — desktop shows table rows, mobile shows cards.
 */
function IssuesTableSkeleton() {
  return (
    <>
      {/* Desktop skeleton */}
      <div className="hidden divide-y divide-border-soft md:block">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 px-6 py-4">
            <div className="flex min-w-0 flex-1 flex-col gap-2">
              <div className="h-4 w-3/4 animate-pulse rounded bg-bg-tertiary" />
            </div>
            <div className="h-6 w-20 animate-pulse rounded-full bg-bg-tertiary" />
            <div className="h-4 w-16 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-4 w-12 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-4 w-20 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-6 w-16 animate-pulse rounded-full bg-bg-tertiary" />
          </div>
        ))}
      </div>

      {/* Mobile skeleton */}
      <div className="divide-y divide-border-soft md:hidden">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex flex-col gap-2.5 px-4 py-4 sm:px-5">
            <div className="h-4 w-full animate-pulse rounded bg-bg-tertiary" />
            <div className="flex gap-2">
              <div className="h-5 w-16 animate-pulse rounded-full bg-bg-tertiary" />
              <div className="h-5 w-14 animate-pulse rounded-full bg-bg-tertiary" />
            </div>
            <div className="flex gap-4">
              <div className="h-3 w-16 animate-pulse rounded bg-bg-tertiary" />
              <div className="h-3 w-20 animate-pulse rounded bg-bg-tertiary" />
              <div className="h-3 w-16 animate-pulse rounded bg-bg-tertiary" />
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
