"use client";

import { FileText, CheckCircle, AlertCircle, Users } from "lucide-react";
import { StatsCard } from "@/components/dashboard/stats-card";
import { ChartCard } from "@/components/dashboard/chart-card";
import { ActivityList } from "@/components/dashboard/activity-list";
import { useDashboardStats } from "@/lib/hooks/use-issues";
import { formatNumber } from "@/lib/utils";

// Mock data for development
const mockStats = {
  total_issues: 1247,
  resolved_issues: 892,
  active_issues: 355,
  total_contributors: 234,
  issues_by_category: {
    environment: 420,
    model_behavior: 312,
    api_integration: 215,
    code_generation: 180,
    framework_specific: 120,
  },
  issues_by_provider: {
    OpenAI: 456,
    Anthropic: 389,
    Google: 234,
    Mistral: 98,
    Local: 70,
  },
  recent_activity: [
    {
      id: "1",
      type: "submission" as const,
      issue_title: "LangChain @tool decorator causing schema validation errors",
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    },
    {
      id: "2",
      type: "confirmation" as const,
      issue_title: "OpenAI function calling returns malformed JSON",
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    },
    {
      id: "3",
      type: "update" as const,
      issue_title: "Anthropic Claude tool_use requires specific response format",
      timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    },
    {
      id: "4",
      type: "submission" as const,
      issue_title: "Pydantic v2 model_dump() incompatible with older codebases",
      timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    },
  ],
};

/**
 * Dashboard Home page matching GIM.pen design (GKjGj).
 */
export default function DashboardPage() {
  const { data: stats, isLoading } = useDashboardStats();

  // Use mock data if no real data
  const displayStats = stats || mockStats;

  const chartData = Object.entries(displayStats.issues_by_category).map(
    ([name, value]) => ({
      name: name.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase()),
      value,
    })
  );

  const providerData = Object.entries(displayStats.issues_by_provider).map(
    ([name, value]) => ({
      name,
      value,
    })
  );

  return (
    <main className="flex flex-1 flex-col gap-6 px-10 py-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[32px] font-semibold text-text-primary">Dashboard</h1>
          <p className="text-sm text-text-secondary">
            Welcome back! Here&apos;s your issue overview.
          </p>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        <StatsCard
          title="Total Issues"
          value={formatNumber(displayStats.total_issues)}
          icon={FileText}
          trend={{ value: 12, isPositive: true }}
        />
        <StatsCard
          title="Resolved"
          value={formatNumber(displayStats.resolved_issues)}
          icon={CheckCircle}
          trend={{ value: 8, isPositive: true }}
        />
        <StatsCard
          title="Active"
          value={formatNumber(displayStats.active_issues)}
          icon={AlertCircle}
          trend={{ value: 3, isPositive: false }}
        />
        <StatsCard
          title="Contributors"
          value={formatNumber(displayStats.total_contributors)}
          icon={Users}
          trend={{ value: 15, isPositive: true }}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-[1fr_320px] gap-4">
        <ChartCard
          title="Issues by Category"
          data={chartData}
          colors={["#10B981", "#8B5CF6", "#06B6D4", "#F59E0B", "#EC4899"]}
        />
        <ChartCard
          title="By Provider"
          data={providerData}
          className="h-[280px]"
        />
      </div>

      {/* Recent Activity */}
      <div className="flex flex-1 flex-col overflow-hidden rounded-[20px] bg-white">
        <div className="flex items-center justify-between border-b border-border-soft px-6 py-5">
          <h2 className="font-medium text-text-primary">Recent Activity</h2>
          <span className="text-sm text-text-muted">
            {displayStats.recent_activity.length} items
          </span>
        </div>
        <div className="flex-1 overflow-auto">
          <ActivityList activities={displayStats.recent_activity} />
        </div>
      </div>
    </main>
  );
}
