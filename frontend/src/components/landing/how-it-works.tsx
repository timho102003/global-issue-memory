import { Download, Search, Share2, Heart } from "lucide-react";

/**
 * How It Works section with 3-step cards and responsive grid.
 */
export function HowItWorks() {
  const steps = [
    {
      number: "01",
      icon: Download,
      title: "Install GIM",
      description: "One command to add GIM to your workflow. Works with any AI assistant.",
      code: "pip install gim-mcp",
    },
    {
      number: "02",
      icon: Search,
      title: "Hit an Error",
      description: "When your AI encounters a known issue, GIM automatically suggests verified fixes.",
      code: null,
    },
    {
      number: "03",
      icon: Share2,
      title: "Solve & Share",
      description: "Found a new fix? Share it back. Your solution helps developers everywhere.",
      code: null,
    },
  ];

  return (
    <section id="how-it-works" className="bg-bg-tertiary px-5 py-16 sm:px-8 sm:py-20 md:py-24 lg:px-12">
      <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-12 md:gap-14">
        {/* Header */}
        <div className="flex flex-col items-center gap-3">
          <span className="text-[11px] font-semibold tracking-[2px] text-accent-warm uppercase">
            Getting Started
          </span>
          <h2 className="text-center text-2xl font-bold tracking-tight text-text-primary sm:text-3xl md:text-4xl lg:text-[44px] lg:leading-[1.15]">
            Simple Setup. Immediate Value.
          </h2>
        </div>

        {/* Steps */}
        <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3">
          {steps.map((step, index) => (
            <div
              key={index}
              className="flex flex-col gap-4 rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)] transition-all duration-200 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5 sm:p-7"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold tracking-tight text-accent-warm">{step.number}</span>
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#FEF3C7]">
                  <step.icon className="h-4 w-4 text-accent-warm" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-text-primary">{step.title}</h3>
              <p className="text-[14px] leading-relaxed text-text-secondary">
                {step.description}
              </p>
              {step.code && (
                <code className="rounded-lg bg-[#1E1E1E] px-4 py-2.5 font-mono text-xs text-white sm:text-sm">
                  {step.code}
                </code>
              )}
            </div>
          ))}
        </div>

        {/* Bonus Step */}
        <div className="flex w-full flex-col items-start gap-4 rounded-2xl border border-accent-warm/20 bg-bg-highlight p-6 shadow-[var(--shadow-sm)] sm:flex-row sm:items-center sm:gap-6 sm:p-8">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent-warm/10">
            <Heart className="h-6 w-6 text-accent-warm" />
          </div>
          <div className="flex flex-col gap-1.5">
            <h4 className="text-base font-semibold text-text-primary sm:text-lg">
              That&apos;s it. You&apos;re part of the community.
            </h4>
            <p className="text-[14px] leading-relaxed text-text-secondary">
              Every fix you use and share makes the whole community smarter. Together, we&apos;re
              building a global knowledge base for AI development.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
