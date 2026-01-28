"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ContributionHeatmapProps {
  data: { date: string; count: number }[];
}

/**
 * GitHub-style contribution heatmap component.
 */
export function ContributionHeatmap({ data }: ContributionHeatmapProps) {
  // Generate last 52 weeks of data
  const weeks = 52;
  const daysPerWeek = 7;

  // Create a map of date -> count for quick lookup
  const countMap = new Map(data.map((d) => [d.date, d.count]));

  // Generate dates for the heatmap
  const today = new Date();
  const cells: { date: string; count: number }[] = [];

  for (let i = weeks * daysPerWeek - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split("T")[0];
    cells.push({
      date: dateStr,
      count: countMap.get(dateStr) || 0,
    });
  }

  // Group by weeks
  const weekGroups: typeof cells[] = [];
  for (let i = 0; i < cells.length; i += daysPerWeek) {
    weekGroups.push(cells.slice(i, i + daysPerWeek));
  }

  const getColorClass = (count: number) => {
    if (count === 0) return "bg-bg-muted";
    if (count <= 2) return "bg-[#D4A853]/30";
    if (count <= 5) return "bg-[#D4A853]/50";
    if (count <= 10) return "bg-[#D4A853]/70";
    return "bg-[#D4A853]";
  };

  const totalContributions = data.reduce((sum, d) => sum + d.count, 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Contributions</CardTitle>
          <span className="text-sm text-text-muted">
            {totalContributions} total
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-1 overflow-x-auto pb-2">
          {weekGroups.map((week, weekIndex) => (
            <div key={weekIndex} className="flex flex-col gap-1">
              {week.map((day, dayIndex) => (
                <div
                  key={`${weekIndex}-${dayIndex}`}
                  className={cn(
                    "h-3 w-3 rounded-sm",
                    getColorClass(day.count)
                  )}
                  title={`${day.date}: ${day.count} contributions`}
                />
              ))}
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center justify-end gap-2 text-xs text-text-muted">
          <span>Less</span>
          <div className="flex gap-1">
            <div className="h-3 w-3 rounded-sm bg-bg-muted" />
            <div className="h-3 w-3 rounded-sm bg-[#D4A853]/30" />
            <div className="h-3 w-3 rounded-sm bg-[#D4A853]/50" />
            <div className="h-3 w-3 rounded-sm bg-[#D4A853]/70" />
            <div className="h-3 w-3 rounded-sm bg-[#D4A853]" />
          </div>
          <span>More</span>
        </div>
      </CardContent>
    </Card>
  );
}
