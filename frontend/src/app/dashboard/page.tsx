"use client";

import { StatsCard } from "@/components/dashboard/stats-card";
import { IssuesOverTimeChart } from "@/components/dashboard/issues-over-time-chart";
import { ProviderList } from "@/components/dashboard/provider-list";
import { ActivityList } from "@/components/dashboard/activity-list";
import { useDashboardStats } from "@/lib/hooks/use-issues";
import { formatNumber } from "@/lib/utils";

/**
 * Dashboard Home page matching GIM.pen design (GKjGj).
 */
export default function DashboardPage() {
  const { data: stats } = useDashboardStats();

  // Calculate percentages for badges
  const totalIssues = stats?.total_issues || 0;
  const resolvedIssues = stats?.resolved_issues || 0;
  const pendingIssues = stats?.active_issues || 0;
  const totalContributors = stats?.total_contributors || 0;

  const resolvedPercent = totalIssues > 0
    ? ((resolvedIssues / totalIssues) * 100).toFixed(1)
    : "0";
  const pendingPercent = totalIssues > 0
    ? ((pendingIssues / totalIssues) * 100).toFixed(1)
    : "0";

  // Transform provider data for list
  const providerData = stats?.issues_by_provider
    ? Object.entries(stats.issues_by_provider).map(([name, value]) => ({
        name,
        value: value as number,
      }))
    : [];

  return (
    <main className="flex flex-1 flex-col gap-6 py-6 sm:py-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary sm:text-[28px]">Dashboard</h1>
          <p className="mt-1 text-[13px] text-text-secondary">
            Welcome back! Here&apos;s your issue overview.
          </p>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <StatsCard
          title="Total Issues"
          value={formatNumber(totalIssues)}
          badge={{ text: "+12%", variant: "success" }}
        />
        <StatsCard
          title="Resolved"
          value={formatNumber(resolvedIssues)}
          badge={{ text: `${resolvedPercent}%`, variant: "success" }}
        />
        <StatsCard
          title="Pending"
          value={formatNumber(pendingIssues)}
          badge={{ text: `${pendingPercent}%`, variant: "warning" }}
        />
        <StatsCard
          title="Contributors"
          value={formatNumber(totalContributors)}
          badge={{ text: "+8 new", variant: "purple" }}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-3 sm:gap-4 lg:grid-cols-[1fr_300px]">
        <IssuesOverTimeChart />
        <ProviderList data={providerData} />
      </div>

      {/* Recent Activity */}
      <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-border-light/80 bg-white shadow-[var(--shadow-card)]">
        <div className="flex items-center justify-between border-b border-border-soft px-5 py-4 sm:px-6 sm:py-5">
          <h2 className="text-[15px] font-semibold text-text-primary">Recent Activity</h2>
          <span className="text-[13px] font-medium text-text-secondary cursor-pointer transition-colors hover:text-text-primary">
            View all
          </span>
        </div>
        <div className="flex-1 overflow-auto">
          <ActivityList activities={stats?.recent_activity || []} />
        </div>
      </div>
    </main>
  );
}
