"use client";

import Image from "next/image";
import Link from "next/link";

interface ProviderListProps {
  data: { name: string; value: number }[];
}

/** Maps lowercase provider names to their logo file in /logos/ */
const PROVIDER_LOGOS: Record<string, string> = {
  anthropic: "/logos/anthropic.svg",
  openai: "/logos/openai.svg",
  xai: "/logos/xai.svg",
  meta: "/logos/meta.svg",
  groq: "/logos/groq.svg",
  github: "/logos/github.svg",
  "github-crawler": "/logos/github.svg",
};

/** Display names for providers (API may return lowercase) */
const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  anthropic: "Anthropic",
  openai: "OpenAI",
  xai: "xAI",
  meta: "Meta",
  groq: "Groq",
  google: "Google",
  mistral: "Mistral",
  github: "GitHub",
  "github-crawler": "GitHub Crawler",
};

/** Provider names to exclude from the list */
const EXCLUDED_PROVIDERS = new Set(["unknown", "others"]);

/** Fallback dot color for providers without a logo */
const PROVIDER_COLORS: Record<string, string> = {
  google: "#4285F4",
  mistral: "#F54E42",
  others: "#D4D2CD",
};

/**
 * Provider list component matching GIM.pen design.
 * Shows providers with logos (or colored dots as fallback) and values.
 */
export function ProviderList({ data }: ProviderListProps) {
  // Filter out excluded providers and sort by value
  const displayData = [...data]
    .filter((p) => !EXCLUDED_PROVIDERS.has(p.name.toLowerCase()))
    .sort((a, b) => b.value - a.value);

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
                  {PROVIDER_LOGOS[provider.name.toLowerCase()] ? (
                    <Image
                      src={PROVIDER_LOGOS[provider.name.toLowerCase()]}
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
                          PROVIDER_COLORS[provider.name.toLowerCase()] || PROVIDER_COLORS.others,
                      }}
                    />
                  )}
                </div>
                <span className="text-[13px] text-text-primary">
                  {PROVIDER_DISPLAY_NAMES[provider.name.toLowerCase()] || provider.name}
                </span>
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
