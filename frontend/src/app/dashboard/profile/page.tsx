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
import { formatNumber } from "@/lib/utils";

// Generate mock contribution data
function generateMockContributions() {
  const data: { date: string; count: number }[] = [];
  const today = new Date();

  for (let i = 0; i < 365; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);

    // Random contribution count with some variation
    const random = Math.random();
    let count = 0;
    if (random > 0.7) count = Math.floor(Math.random() * 5) + 1;
    if (random > 0.9) count = Math.floor(Math.random() * 10) + 5;

    data.push({
      date: date.toISOString().split("T")[0],
      count,
    });
  }

  return data;
}

const mockContributions = generateMockContributions();

const mockStats = {
  totalSearches: 1247,
  totalSubmissions: 89,
  totalConfirmations: 234,
  totalReports: 12,
};

/**
 * Profile page matching GIM.pen design (QV9MN).
 * Requires authentication to view.
 */
export default function ProfilePage() {
  const { gimId, isAuthenticated } = useAuthStore();
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Show sign-in prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-6 px-10 py-6">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-bg-muted">
            <LogIn className="h-8 w-8 text-text-muted" />
          </div>
          <h1 className="text-2xl font-semibold text-text-primary">
            Sign in to view your profile
          </h1>
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
    <main className="flex flex-1 flex-col gap-6 px-10 py-6">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <Avatar
          fallback={displayGimId.slice(0, 2).toUpperCase()}
          size="lg"
        />
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold text-text-primary">
            GIM User
          </h1>
          <p className="text-sm text-text-secondary">
            Member since January 2025
          </p>
        </div>
      </div>

      {/* Content Row */}
      <div className="flex flex-1 gap-6">
        {/* Left Column */}
        <div className="flex w-[560px] flex-col gap-5">
          {/* GIM ID Card */}
          <GimIdCard gimId={displayGimId} />

          {/* Stats Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Activity Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1 rounded-xl bg-bg-muted p-4">
                  <span className="text-2xl font-bold text-text-primary">
                    {formatNumber(mockStats.totalSearches)}
                  </span>
                  <span className="text-xs text-text-muted">Total Searches</span>
                </div>
                <div className="flex flex-col gap-1 rounded-xl bg-bg-muted p-4">
                  <span className="text-2xl font-bold text-text-primary">
                    {formatNumber(mockStats.totalSubmissions)}
                  </span>
                  <span className="text-xs text-text-muted">Submissions</span>
                </div>
                <div className="flex flex-col gap-1 rounded-xl bg-bg-muted p-4">
                  <span className="text-2xl font-bold text-text-primary">
                    {formatNumber(mockStats.totalConfirmations)}
                  </span>
                  <span className="text-xs text-text-muted">Confirmations</span>
                </div>
                <div className="flex flex-col gap-1 rounded-xl bg-bg-muted p-4">
                  <span className="text-2xl font-bold text-text-primary">
                    {formatNumber(mockStats.totalReports)}
                  </span>
                  <span className="text-xs text-text-muted">Reports</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Contribution Heatmap */}
          <ContributionHeatmap data={mockContributions} />
        </div>

        {/* Right Column */}
        <div className="flex flex-1 flex-col gap-5">
          {/* MCP Config */}
          <McpConfigCard gimId={displayGimId} />

          {/* Rate Limit Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Rate Limits</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-secondary">Daily Searches</span>
                <span className="text-sm font-medium text-text-primary">
                  87 / 100
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-bg-muted">
                <div
                  className="h-full rounded-full bg-[#D4A853]"
                  style={{ width: "87%" }}
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
