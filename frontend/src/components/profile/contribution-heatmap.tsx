"use client";

import { useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ContributionHeatmapProps {
  data: { date: string; count: number }[];
}

const DAYS_PER_WEEK = 7;
const MAX_WEEKS = 52;
/** Minimum pixel gap between month labels to prevent overlap. */
const MIN_LABEL_GAP_PX = 28;
const CELL_PX = 10;
const GAP_PX = 2;
const COL_PX = CELL_PX + GAP_PX;

const MONTH_ABBREVS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

/** Day-of-week labels: Mon (row 1), Wed (row 3), Fri (row 5) in Sun=0 indexed week. */
const DAY_LABELS: Record<number, string> = {
  1: "Mon",
  3: "Wed",
  5: "Fri",
};

function getColorClass(count: number): string {
  if (count === 0) return "bg-border-soft";
  if (count <= 2) return "bg-[#D4A853]/40";
  if (count <= 5) return "bg-[#D4A853]/60";
  if (count <= 10) return "bg-[#D4A853]/80";
  return "bg-[#D4A853]";
}

/**
 * Returns the start of week (Sunday) for a given date, as a new Date at midnight UTC.
 */
function startOfWeekSunday(date: Date): Date {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() - d.getUTCDay());
  return d;
}

/**
 * Formats a Date as YYYY-MM-DD string using UTC values.
 */
function formatDate(date: Date): string {
  const y = date.getUTCFullYear();
  const m = String(date.getUTCMonth() + 1).padStart(2, "0");
  const d = String(date.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/**
 * GitHub-style contribution heatmap with axis labels and data-driven date range.
 */
export function ContributionHeatmap({ data }: ContributionHeatmapProps) {
  const countMap = useMemo(
    () => new Map(data.map((d) => [d.date, d.count])),
    [data]
  );

  const totalContributions = useMemo(
    () => data.reduce((sum, d) => sum + d.count, 0),
    [data]
  );

  /**
   * Compute the date range and build week groups.
   *
   * Strategy: End date is today. Start date is the earlier of
   * (a) the first contribution date or (b) today minus MAX_WEEKS*7 days,
   * capped to at most MAX_WEEKS weeks. The start is aligned to Sunday
   * so each column is a complete week.
   */
  const { weekGroups, monthLabels } = useMemo(() => {
    const today = new Date();
    const todayUTC = new Date(
      Date.UTC(today.getFullYear(), today.getMonth(), today.getDate())
    );

    // The absolute earliest start (52 weeks before end-of-current-week)
    const maxStart = new Date(todayUTC);
    maxStart.setUTCDate(maxStart.getUTCDate() - MAX_WEEKS * DAYS_PER_WEEK + 1);
    const maxStartSunday = startOfWeekSunday(maxStart);

    // Always use the full 52-week range so the grid is consistent
    const rangeStart = maxStartSunday;

    // Build cells from rangeStart through today
    const cells: { date: string; count: number; dow: number }[] = [];
    const cursor = new Date(rangeStart);
    while (cursor <= todayUTC) {
      const dateStr = formatDate(cursor);
      cells.push({
        date: dateStr,
        count: countMap.get(dateStr) || 0,
        dow: cursor.getUTCDay(),
      });
      cursor.setUTCDate(cursor.getUTCDate() + 1);
    }

    // Group into weeks (each week is an array of 7 slots, some may be null for partial weeks)
    type CellOrNull = { date: string; count: number; dow: number } | null;
    const weeks: CellOrNull[][] = [];
    let currentWeek: CellOrNull[] = [];

    // Pad the first week if it doesn't start on Sunday
    if (cells.length > 0) {
      const firstDow = cells[0].dow;
      for (let i = 0; i < firstDow; i++) {
        currentWeek.push(null);
      }
    }

    for (const cell of cells) {
      if (currentWeek.length === DAYS_PER_WEEK) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
      currentWeek.push(cell);
    }

    // Pad the last week if incomplete
    while (currentWeek.length < DAYS_PER_WEEK) {
      currentWeek.push(null);
    }
    if (currentWeek.length > 0) {
      weeks.push(currentWeek);
    }

    // Compute month labels with overlap prevention.
    // Only emit a label if it is at least MIN_LABEL_GAP_PX away from the previous one.
    const labels: { weekIndex: number; label: string }[] = [];
    let lastMonth = -1;
    let lastLabelPx = -MIN_LABEL_GAP_PX;

    for (let wi = 0; wi < weeks.length; wi++) {
      const firstCell = weeks[wi].find((c) => c !== null);
      if (!firstCell) continue;

      const [, monthStr] = firstCell.date.split("-");
      const month = parseInt(monthStr, 10) - 1;

      if (month !== lastMonth) {
        const px = wi * COL_PX;
        if (px - lastLabelPx >= MIN_LABEL_GAP_PX) {
          labels.push({ weekIndex: wi, label: MONTH_ABBREVS[month] });
          lastLabelPx = px;
        }
        lastMonth = month;
      }
    }

    return { weekGroups: weeks, monthLabels: labels };
  }, [data, countMap]);

  // Empty state: no contributions (data may contain entries with count 0)
  if (totalContributions === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Contributions</CardTitle>
            <span className="text-sm text-text-muted">0 total</span>
          </div>
        </CardHeader>
        <CardContent>
          <p className="py-6 text-center text-sm text-text-muted">
            No contributions yet.
          </p>
        </CardContent>
      </Card>
    );
  }

  const cellSize = "h-[10px] w-[10px]";
  const gapClass = "gap-[2px]";
  const labelWidth = "w-[26px]";

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
        <div className="flex flex-col gap-1 overflow-x-auto">
          {/* Month labels row */}
          <div className="flex">
            {/* Spacer to align with Y-axis label column */}
            <div className={cn("shrink-0", labelWidth)} />
            <div className="relative flex-1" style={{ height: 16 }}>
              {monthLabels.map(({ weekIndex, label }) => (
                <span
                  key={`${label}-${weekIndex}`}
                  className="absolute text-[10px] leading-none text-text-muted"
                  style={{
                    left: weekIndex * COL_PX,
                  }}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* Grid: Y-axis labels + heatmap cells */}
          <div className="flex">
            {/* Y-axis day labels */}
            <div
              className={cn(
                "flex shrink-0 flex-col",
                gapClass,
                labelWidth
              )}
            >
              {Array.from({ length: DAYS_PER_WEEK }).map((_, rowIdx) => (
                <div
                  key={rowIdx}
                  className={cn(
                    cellSize,
                    "flex items-center text-[10px] leading-none text-text-muted"
                  )}
                >
                  {DAY_LABELS[rowIdx] ?? ""}
                </div>
              ))}
            </div>

            {/* Heatmap grid: weeks as columns, days as rows */}
            <div className={cn("flex", gapClass)}>
              {weekGroups.map((week, weekIndex) => (
                <div key={weekIndex} className={cn("flex flex-col", gapClass)}>
                  {week.map((day, dayIndex) => (
                    <div
                      key={`${weekIndex}-${dayIndex}`}
                      className={cn(
                        cellSize,
                        "rounded-sm",
                        day ? getColorClass(day.count) : "bg-transparent"
                      )}
                      title={
                        day
                          ? `${day.date}: ${day.count} contributions`
                          : undefined
                      }
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="mt-3 flex items-center justify-end gap-1.5 text-[10px] text-text-muted">
            <span>Less</span>
            <div className="flex gap-[2px]">
              <div className="h-[10px] w-[10px] rounded-sm bg-border-soft" />
              <div className="h-[10px] w-[10px] rounded-sm bg-[#D4A853]/40" />
              <div className="h-[10px] w-[10px] rounded-sm bg-[#D4A853]/60" />
              <div className="h-[10px] w-[10px] rounded-sm bg-[#D4A853]/80" />
              <div className="h-[10px] w-[10px] rounded-sm bg-[#D4A853]" />
            </div>
            <span>More</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
