"use client";

import Image from "next/image";
import Link from "next/link";

interface ProviderListProps {
  data: { name: string; value: number }[];
}

/** Maps provider names to their logo file in /logos/ */
const PROVIDER_LOGOS: Record<string, string> = {
  Anthropic: "/logos/anthropic.svg",
  OpenAI: "/logos/openai.svg",
  xAI: "/logos/xai.svg",
  Meta: "/logos/meta.svg",
  Groq: "/logos/groq.svg",
};

/** Fallback dot color for providers without a logo */
const PROVIDER_COLORS: Record<string, string> = {
  Google: "#4285F4",
  Mistral: "#F54E42",
  Others: "#D4D2CD",
};

/**
 * Provider list component matching GIM.pen design.
 * Shows providers with logos (or colored dots as fallback) and values.
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
                <div className="flex h-5 w-5 shrink-0 items-center justify-center">
                  {PROVIDER_LOGOS[provider.name] ? (
                    <Image
                      src={PROVIDER_LOGOS[provider.name]}
                      alt={provider.name}
                      width={20}
                      height={20}
                      className="h-5 w-5 object-contain"
                    />
                  ) : (
                    <div
                      className="h-2.5 w-2.5 rounded-full"
                      style={{
                        backgroundColor:
                          PROVIDER_COLORS[provider.name] || PROVIDER_COLORS.Others,
                      }}
                    />
                  )}
                </div>
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
