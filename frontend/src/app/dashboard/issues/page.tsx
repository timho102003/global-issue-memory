"use client";

import { useState } from "react";
import { Select } from "@/components/ui/select";
import { SearchBox } from "@/components/ui/search-box";
import { IssuesTable } from "@/components/dashboard/issues-table";
import { useIssueSearch } from "@/lib/hooks/use-issues";
import type { MasterIssue, IssueStatus, RootCauseCategory } from "@/types";

/**
 * Issue Explorer page matching GIM.pen design (yHuOd).
 */
export default function IssuesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [provider, setProvider] = useState<string>("all");
  const [timeRange, setTimeRange] = useState<string>("all");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data, isLoading } = useIssueSearch({
    query: search || undefined,
    category: category !== "all" ? category : undefined,
    status: status !== "all" ? status : undefined,
    provider: provider !== "all" ? provider : undefined,
    time_range: timeRange !== "all" ? (timeRange as "7d" | "30d" | "90d") : undefined,
    limit: 20,
  });

  const issues = data?.issues ?? [];

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
              onChange={(e) => setCategory(e.target.value)}
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
              onChange={(e) => setProvider(e.target.value)}
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
              onChange={(e) => setStatus(e.target.value)}
              className="w-full sm:w-[120px]"
            >
              <option value="all">All Status</option>
              <option value="active">Verified</option>
              <option value="superseded">Pending</option>
              <option value="invalid">Declined</option>
            </Select>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="w-full sm:w-[140px]"
            >
              <option value="all">All Time</option>
              <option value="7d">Past 7 Days</option>
              <option value="30d">Past 30 Days</option>
              <option value="90d">Past 90 Days</option>
            </Select>
          </div>
          <SearchBox
            placeholder="Search issues..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-[260px]"
          />
        </div>

        {/* Table Header */}
        <div className="flex items-center justify-between border-b border-border-soft px-5 py-3 sm:px-6 sm:py-3.5">
          <span className="text-[13px] text-text-muted">
            {isLoading
              ? "Loading..."
              : selectedIds.length > 0
                ? `${selectedIds.length} selected`
                : `${issues.length} issues`}
          </span>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-auto">
          {isLoading ? (
            <IssuesTableSkeleton />
          ) : (
            <IssuesTable
              issues={issues}
              selectedIds={selectedIds}
              onSelectionChange={setSelectedIds}
            />
          )}
        </div>
      </div>
    </main>
  );
}

/**
 * Skeleton loading state for the issues table.
 */
function IssuesTableSkeleton() {
  return (
    <div className="divide-y divide-border-soft">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-5 py-4 sm:px-6">
          {/* Checkbox placeholder */}
          <div className="h-4 w-4 animate-pulse rounded bg-bg-tertiary" />
          {/* Title + description */}
          <div className="flex min-w-0 flex-1 flex-col gap-2">
            <div className="h-4 w-3/4 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-3 w-1/2 animate-pulse rounded bg-bg-tertiary" />
          </div>
          {/* Category badge */}
          <div className="hidden h-6 w-20 animate-pulse rounded-full bg-bg-tertiary sm:block" />
          {/* Confidence */}
          <div className="hidden h-4 w-12 animate-pulse rounded bg-bg-tertiary md:block" />
          {/* Count */}
          <div className="hidden h-4 w-8 animate-pulse rounded bg-bg-tertiary lg:block" />
        </div>
      ))}
    </div>
  );
}
