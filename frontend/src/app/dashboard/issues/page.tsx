"use client";

import { useState, useCallback } from "react";
import { SlidersHorizontal } from "lucide-react";
import { Select } from "@/components/ui/select";
import { SearchBox } from "@/components/ui/search-box";
import { CategoryFilterBar } from "@/components/dashboard/category-filter-bar";
import { IssueCardList } from "@/components/dashboard/issue-card-list";
import { IssuesSkeleton } from "@/components/dashboard/issues-skeleton";
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
 * Issue Explorer page with card-based layout and category pill filters.
 */
export default function IssuesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [provider, setProvider] = useState<string>("all");
  const [timeRange, setTimeRange] = useState<string>("all");
  const [page, setPage] = useState(0);
  const [showFilters, setShowFilters] = useState(false);

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

  const hasSecondaryFilters = provider !== "all" || status !== "all" || timeRange !== "all";

  return (
    <main className="flex flex-1 flex-col gap-6 py-6 sm:py-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary sm:text-[28px]">
          Issues
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          Community-verified fixes for AI coding tool issues
        </p>
      </div>

      {/* Filters Tier 1: Category pills + Search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <CategoryFilterBar
          value={category}
          onChange={(val) => { setCategory(val); resetPage(); }}
        />
        <div className="flex items-center gap-2">
          <SearchBox
            placeholder="Search issues..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); resetPage(); }}
            className="w-full sm:w-[260px]"
          />
          {/* Mobile filter toggle */}
          <button
            onClick={() => setShowFilters((v) => !v)}
            className={`flex h-9 shrink-0 items-center gap-1.5 rounded-lg border px-3 text-xs font-medium transition-colors duration-150 sm:hidden ${
              hasSecondaryFilters || showFilters
                ? "border-primary bg-primary/5 text-primary"
                : "border-border-light bg-white text-text-secondary hover:border-border-medium"
            }`}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            Filters
          </button>
        </div>
      </div>

      {/* Filters Tier 2: Provider, Status, Time Range (collapsible on mobile) */}
      <div className={`flex flex-wrap items-center gap-2 sm:gap-3 ${showFilters ? "" : "hidden sm:flex"}`}>
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

      {/* Issue count */}
      <div className="flex items-center justify-between">
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

      {/* Card list */}
      {isLoading ? (
        <IssuesSkeleton />
      ) : (
        <IssueCardList issues={issues} />
      )}

      {/* Pagination */}
      {showPagination && (
        <div className="flex items-center justify-center gap-1.5 py-2">
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
    </main>
  );
}
