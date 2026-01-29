"use client";

import Link from "next/link";

interface ProviderListProps {
  data: { name: string; value: number }[];
}

// Provider color mapping matching GIM.pen design
const PROVIDER_COLORS: Record<string, string> = {
  Anthropic: "#3D3D3D",
  OpenAI: "#E8D98E",
  Google: "#9BE9A8",
  Others: "#D4D2CD",
};

/**
 * Provider list component matching GIM.pen design.
 * Shows providers with colored dots and values.
 */
export function ProviderList({ data }: ProviderListProps) {
  // Group smaller providers into "Others"
  const sortedData = [...data].sort((a, b) => b.value - a.value);
  const topProviders = sortedData.slice(0, 3);
  const otherProviders = sortedData.slice(3);
  const othersTotal = otherProviders.reduce((sum, p) => sum + p.value, 0);

  const displayData = [
    ...topProviders,
    ...(othersTotal > 0 ? [{ name: "Others", value: othersTotal }] : []),
  ];

  const getProviderColor = (name: string): string => {
    return PROVIDER_COLORS[name] || PROVIDER_COLORS.Others;
  };

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-card)] sm:p-6 lg:h-auto">
      <h3 className="text-[15px] font-semibold text-text-primary">By Provider</h3>
      <div className="flex flex-1 flex-col gap-3">
        {displayData.length === 0 ? (
          <p className="text-[13px] text-text-secondary">No data available</p>
        ) : (
          displayData.map((provider) => (
            <div
              key={provider.name}
              className="flex items-center justify-between rounded-lg px-2 py-1.5 transition-colors hover:bg-bg-muted/60"
            >
              <div className="flex items-center gap-2.5">
                <div
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: getProviderColor(provider.name) }}
                />
                <span className="text-[13px] text-text-primary">{provider.name}</span>
              </div>
              <span className="text-[13px] font-semibold tabular-nums text-text-primary">
                {provider.value.toLocaleString()}
              </span>
            </div>
          ))
        )}
      </div>
      <Link
        href="/dashboard/issues"
        className="mt-auto text-[13px] font-medium text-text-secondary transition-colors hover:text-text-primary"
      >
        View all
      </Link>
    </div>
  );
}
