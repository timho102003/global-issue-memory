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
  const unverifiedIssues = stats?.unverified_issues || 0;
  const totalContributors = stats?.total_contributors || 0;

  const resolvedPercent = totalIssues > 0
    ? ((resolvedIssues / totalIssues) * 100).toFixed(1)
    : "0";
  const unverifiedPercent = totalIssues > 0
    ? ((unverifiedIssues / totalIssues) * 100).toFixed(1)
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
          tooltip="Total number of unique master issues tracked"
        />
        <StatsCard
          title="Verified"
          value={formatNumber(resolvedIssues)}
          badge={{ text: `${resolvedPercent}%`, variant: "success" }}
          tooltip="Issues with at least one verification (verification_count >= 1)"
        />
        <StatsCard
          title="Unverified"
          value={formatNumber(unverifiedIssues)}
          badge={{ text: `${unverifiedPercent}%`, variant: "warning" }}
          tooltip="Issues with no verifications yet"
        />
        <StatsCard
          title="Contributors"
          value={formatNumber(totalContributors)}
          tooltip="Unique providers that have submitted child issues"
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
