"use client";

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
import { cn } from "@/lib/utils";

interface ChartCardProps {
  title: string;
  data: { name: string; value: number }[];
  className?: string;
  colors?: string[];
}

const DEFAULT_COLORS = [
  "#D4A853",
  "#10B981",
  "#8B5CF6",
  "#06B6D4",
  "#F59E0B",
  "#EC4899",
];

/**
 * Chart card component for dashboard.
 */
export function ChartCard({ title, data, className, colors = DEFAULT_COLORS }: ChartCardProps) {
  return (
    <div className={cn("flex flex-col gap-4 rounded-[20px] bg-white p-6", className)}>
      <h3 className="text-sm font-medium text-text-secondary">{title}</h3>
      <div className="h-[180px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F0EDE6" />
            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: "#9C9791" }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: "#9C9791" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid #E8E6E1",
                borderRadius: "8px",
                fontSize: "12px",
              }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
