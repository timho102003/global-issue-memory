"use client";

import { useState } from "react";
import { Select } from "@/components/ui/select";
import { SearchBox } from "@/components/ui/search-box";
import { IssuesTable } from "@/components/dashboard/issues-table";
import { useIssueSearch } from "@/lib/hooks/use-issues";
import type { MasterIssue, IssueStatus, RootCauseCategory } from "@/types";

// Mock data for development
const mockIssues: MasterIssue[] = [
  {
    id: "1",
    canonical_title: "LangChain @tool decorator causing schema validation errors",
    description: "The @tool decorator fails to generate valid JSON schema",
    root_cause_category: "api_integration",
    confidence_score: 0.92,
    child_issue_count: 24,
    environment_coverage: ["Claude", "GPT-4"],
    verification_count: 156,
    status: "active",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
  },
  {
    id: "2",
    canonical_title: "OpenAI function calling returns malformed JSON",
    description: "Intermittent JSON parsing failures with function_call response",
    root_cause_category: "model_behavior",
    confidence_score: 0.88,
    child_issue_count: 18,
    environment_coverage: ["GPT-4", "GPT-3.5"],
    verification_count: 89,
    status: "active",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: "3",
    canonical_title: "Pydantic v2 model_dump() incompatible with older codebases",
    description: "Migration from v1 to v2 breaks existing serialization",
    root_cause_category: "environment",
    confidence_score: 0.95,
    child_issue_count: 42,
    environment_coverage: ["Python 3.10+"],
    verification_count: 234,
    status: "active",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
  },
  {
    id: "4",
    canonical_title: "FastAPI dependency injection fails with async context",
    description: "Dependencies using asynccontextmanager don't properly cleanup",
    root_cause_category: "framework_specific",
    confidence_score: 0.76,
    child_issue_count: 8,
    environment_coverage: ["FastAPI 0.100+"],
    verification_count: 45,
    status: "superseded",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  },
  {
    id: "5",
    canonical_title: "Claude tool_use requires specific response format",
    description: "Tool results must follow exact schema structure",
    root_cause_category: "api_integration",
    confidence_score: 0.91,
    child_issue_count: 15,
    environment_coverage: ["Claude 3"],
    verification_count: 112,
    status: "active",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
  },
];

/**
 * Issue Explorer page matching GIM.pen design (yHuOd).
 */
export default function IssuesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [provider, setProvider] = useState<string>("all");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data, isLoading } = useIssueSearch({
    query: search || undefined,
    category: category !== "all" ? category : undefined,
    status: status !== "all" ? status : undefined,
    provider: provider !== "all" ? provider : undefined,
    limit: 20,
  });

  // Use mock data if no real data
  const issues = data?.issues || mockIssues;

  return (
    <main className="flex flex-1 flex-col gap-6 px-10 py-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-[32px] font-semibold text-text-primary">Issues</h1>
      </div>

      {/* Issues Card */}
      <div className="flex flex-1 flex-col overflow-hidden rounded-3xl bg-white">
        {/* Filters */}
        <div className="flex items-center justify-between border-b border-border-soft px-6 py-5">
          <div className="flex items-center gap-3">
            <Select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-[140px]"
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
              className="w-[140px]"
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
              className="w-[120px]"
            >
              <option value="all">All Status</option>
              <option value="active">Verified</option>
              <option value="superseded">Pending</option>
              <option value="invalid">Declined</option>
            </Select>
          </div>
          <SearchBox
            placeholder="Search issues..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-[280px]"
          />
        </div>

        {/* Table Header */}
        <div className="flex items-center justify-between border-b border-border-soft px-6 py-3.5">
          <span className="text-sm text-text-muted">
            {selectedIds.length > 0
              ? `${selectedIds.length} selected`
              : `${issues.length} issues`}
          </span>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-auto">
          <IssuesTable
            issues={issues}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
          />
        </div>
      </div>
    </main>
  );
}
