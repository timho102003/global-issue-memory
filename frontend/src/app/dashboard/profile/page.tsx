"use client";

import { useState } from "react";
import { LogIn } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GimIdCard } from "@/components/profile/gim-id-card";
import { ContributionHeatmap } from "@/components/profile/contribution-heatmap";
import { McpConfigCard } from "@/components/profile/mcp-config-card";
import { AuthModal } from "@/components/auth";
import { useAuthStore } from "@/stores/auth-store";
import { useProfileStats } from "@/lib/hooks/use-issues";
import { formatNumber } from "@/lib/utils";

/**
 * Profile page matching GIM.pen design (QV9MN).
 * Requires authentication to view.
 */
export default function ProfilePage() {
  const { gimId, isAuthenticated } = useAuthStore();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { data: profileStats } = useProfileStats(gimId);

  // Use real data or defaults
  const stats = {
    totalSearches: profileStats?.total_searches ?? 0,
    totalSubmissions: profileStats?.total_submissions ?? 0,
    totalConfirmations: profileStats?.total_confirmations ?? 0,
    totalReports: profileStats?.total_reports ?? 0,
  };
  const contributions = profileStats?.contributions ?? [];
  const rateLimit = profileStats?.rate_limit ?? {
    daily_searches_used: 0,
    daily_searches_limit: 100,
  };
  const rateLimitPercent = rateLimit.daily_searches_limit > 0
    ? Math.round((rateLimit.daily_searches_used / rateLimit.daily_searches_limit) * 100)
    : 0;

  // Show sign-in prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-6 py-6 sm:py-8">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-bg-muted">
            <LogIn className="h-8 w-8 text-text-muted" />
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-text-primary">
            Sign in to view your profile
          </h2>
          <p className="max-w-md text-sm text-text-secondary">
            Your profile shows your GIM ID, contribution stats, and MCP configuration.
            Sign in or create a GIM ID to access it.
          </p>
          <div className="flex gap-3">
            <Button onClick={() => setShowAuthModal(true)}>
              <LogIn className="h-4 w-4" />
              Sign In
            </Button>
          </div>
        </div>
        <AuthModal
          open={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          defaultView="signin"
          redirectTo="/dashboard/profile"
        />
      </main>
    );
  }

  const displayGimId = gimId!;

  return (
    <main className="flex flex-1 flex-col gap-6 py-6 sm:py-8">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <Avatar
          fallback={displayGimId.slice(0, 2).toUpperCase()}
          size="lg"
        />
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary sm:text-[28px]">
            Profile
          </h1>
          <p className="text-[13px] text-text-secondary">
            Member since January 2025
          </p>
        </div>
      </div>

      {/* Content Row */}
      <div className="flex flex-1 flex-col gap-5 lg:flex-row lg:gap-6">
        {/* Left Column */}
        <div className="flex min-w-0 flex-1 flex-col gap-5 lg:flex-[3]">
          {/* GIM ID Card */}
          <GimIdCard gimId={displayGimId} />

          {/* Stats Card */}
          <Card>
            <CardHeader>
              <CardTitle>Activity Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1 rounded-xl bg-bg-muted p-4 transition-colors hover:bg-bg-tertiary">
                  <span className="text-2xl font-bold tracking-tight text-text-primary">
                    {formatNumber(stats.totalSearches)}
                  </span>
                  <span className="text-xs text-text-muted">Total Searches</span>
                </div>
                <div className="flex flex-col gap-1 rounded-xl bg-bg-muted p-4 transition-colors hover:bg-bg-tertiary">
                  <span className="text-2xl font-bold tracking-tight text-text-primary">
                    {formatNumber(stats.totalSubmissions)}
                  </span>
                  <span className="text-xs text-text-muted">Submissions</span>
                </div>
                <div className="flex flex-col gap-1 rounded-xl bg-bg-muted p-4 transition-colors hover:bg-bg-tertiary">
                  <span className="text-2xl font-bold tracking-tight text-text-primary">
                    {formatNumber(stats.totalConfirmations)}
                  </span>
                  <span className="text-xs text-text-muted">Confirmations</span>
                </div>
                <div className="flex flex-col gap-1 rounded-xl bg-bg-muted p-4 transition-colors hover:bg-bg-tertiary">
                  <span className="text-2xl font-bold tracking-tight text-text-primary">
                    {formatNumber(stats.totalReports)}
                  </span>
                  <span className="text-xs text-text-muted">Reports</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Contribution Heatmap */}
          <ContributionHeatmap data={contributions} />
        </div>

        {/* Right Column */}
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {/* MCP Config */}
          <McpConfigCard gimId={displayGimId} />

          {/* Rate Limit Info */}
          <Card>
            <CardHeader>
              <CardTitle>Rate Limits</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <span className="text-[13px] text-text-secondary">Daily Searches</span>
                <span className="text-[13px] font-medium text-text-primary">
                  {rateLimit.daily_searches_used} / {rateLimit.daily_searches_limit}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-bg-muted">
                <div
                  className="h-full rounded-full bg-[#D4A853] transition-all duration-500"
                  style={{ width: `${rateLimitPercent}%` }}
                />
              </div>
              <p className="text-xs text-text-muted">
                Resets daily at 00:00 UTC
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
