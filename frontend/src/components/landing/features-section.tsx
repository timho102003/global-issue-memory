import {
  Zap,
  Shield,
  Globe,
  Code,
  GitBranch,
  Lock,
  Terminal,
  Sparkles,
  RefreshCw,
} from "lucide-react";

/**
 * Features section with responsive 3-column grid.
 */
export function FeaturesSection() {
  const features = [
    { icon: Zap, title: "Instant Lookup", description: "Search millions of verified fixes in milliseconds." },
    { icon: Shield, title: "Verified Solutions", description: "Every fix tested and confirmed by real developers." },
    { icon: Globe, title: "Multi-Provider", description: "Works with Claude, GPT, Gemini, and more." },
    { icon: Code, title: "Code-Aware", description: "Understands your stack, suggests relevant fixes." },
    { icon: GitBranch, title: "Version Tracking", description: "Fixes evolve with your dependencies." },
    { icon: Lock, title: "Privacy First", description: "Your code stays local. Only anonymized errors shared." },
    { icon: Terminal, title: "MCP Native", description: "First-class MCP integration for seamless workflow." },
    { icon: Sparkles, title: "Smart Matching", description: "AI-powered similarity search finds related issues." },
    { icon: RefreshCw, title: "Auto-Update", description: "Fixes improve automatically as community learns." },
  ];

  return (
    <section
      id="features"
      className="bg-gradient-to-b from-bg-gradient-start to-bg-tertiary px-5 py-16 sm:px-8 sm:py-20 md:py-24 lg:px-12"
    >
      <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-12 md:gap-14">
        {/* Header */}
        <div className="flex flex-col items-center gap-3">
          <span className="text-[11px] font-semibold tracking-[2px] text-accent-warm uppercase">
            Why Developers Love GIM
          </span>
          <h2 className="text-center text-2xl font-bold tracking-tight text-text-primary sm:text-3xl md:text-4xl lg:text-[44px] lg:leading-[1.15]">
            Built by Developers, for Developers
          </h2>
          <p className="max-w-[620px] text-center text-[14px] leading-relaxed text-text-secondary sm:text-base md:text-lg">
            Simple tools that respect your workflow and your privacy.
          </p>
        </div>

        {/* Features Grid — flat 3-col responsive */}
        <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3">
          {features.map((feature, index) => (
            <div
              key={index}
              className="flex flex-col gap-3 rounded-2xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-card)] transition-all duration-200 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5 sm:p-6"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-warm/10">
                <feature.icon className="h-5 w-5 text-accent-warm" />
              </div>
              <h3 className="text-[15px] font-semibold text-text-primary">
                {feature.title}
              </h3>
              <p className="text-[13px] leading-relaxed text-text-secondary">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
