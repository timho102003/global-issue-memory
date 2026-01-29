"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { ChevronDown } from "lucide-react";
import { useDashboardStats } from "@/lib/hooks/use-issues";

const TIME_FILTERS = ["Last 7 days", "Last 30 days", "Last 90 days"] as const;

/**
 * Issues Over Time chart component matching GIM.pen design.
 * Shows bar chart with yellow/gold bars and one highlighted bar.
 */
export function IssuesOverTimeChart() {
  const [filter, setFilter] = useState<typeof TIME_FILTERS[number]>("Last 7 days");
  const [showDropdown, setShowDropdown] = useState(false);
  const { data: stats } = useDashboardStats();

  // Use real time-series data from backend
  const chartData = (() => {
    const rawData = stats?.issues_over_time ?? [];
    const days = filter === "Last 7 days" ? 7 : filter === "Last 30 days" ? 30 : 90;
    const sliced = rawData.slice(-days);

    const data = sliced.map((item) => {
      const date = new Date(item.date + "T00:00:00");
      const dayLabel = days <= 7
        ? date.toLocaleDateString("en-US", { weekday: "short" })
        : date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
      return {
        name: dayLabel,
        value: item.count,
        isHighlighted: false,
      };
    });

    // Highlight the bar with maximum value
    const maxVal = Math.max(...data.map((d) => d.value), 0);
    if (maxVal > 0) {
      const maxIdx = data.findIndex((d) => d.value === maxVal);
      if (maxIdx >= 0) data[maxIdx].isHighlighted = true;
    }

    return data;
  })();

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-card)] sm:p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-semibold text-text-primary">Issues Over Time</h3>
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center gap-1.5 rounded-lg border border-border-light bg-bg-muted px-2.5 py-1.5 text-[11px] font-medium text-text-secondary transition-colors hover:border-border-medium hover:text-text-primary"
          >
            {filter}
            <ChevronDown className="h-3 w-3" />
          </button>
          {showDropdown && (
            <div className="absolute right-0 top-full z-10 mt-1 min-w-[130px] rounded-lg border border-border-light bg-white py-1 shadow-[var(--shadow-md)]">
              {TIME_FILTERS.map((option) => (
                <button
                  key={option}
                  onClick={() => {
                    setFilter(option);
                    setShowDropdown(false);
                  }}
                  className="w-full px-3 py-1.5 text-left text-[11px] text-text-secondary transition-colors hover:bg-bg-muted hover:text-text-primary"
                >
                  {option}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="h-[180px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F0EDE6" />
            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#9C9791" }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#9C9791" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid #E8E6E1",
                borderRadius: "10px",
                fontSize: "12px",
                boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
              }}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.isHighlighted ? "#2D2A26" : "#E8D98E"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
