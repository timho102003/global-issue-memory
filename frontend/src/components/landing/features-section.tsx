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
 * Features section matching GIM.pen design.
 */
export function FeaturesSection() {
  const features = [
    [
      {
        icon: Zap,
        title: "Instant Lookup",
        description: "Search millions of verified fixes in milliseconds.",
      },
      {
        icon: Shield,
        title: "Verified Solutions",
        description: "Every fix tested and confirmed by real developers.",
      },
      {
        icon: Globe,
        title: "Multi-Provider",
        description: "Works with Claude, GPT, Gemini, and more.",
      },
    ],
    [
      {
        icon: Code,
        title: "Code-Aware",
        description: "Understands your stack, suggests relevant fixes.",
      },
      {
        icon: GitBranch,
        title: "Version Tracking",
        description: "Fixes evolve with your dependencies.",
      },
      {
        icon: Lock,
        title: "Privacy First",
        description: "Your code stays local. Only anonymized errors shared.",
      },
    ],
    [
      {
        icon: Terminal,
        title: "MCP Native",
        description: "First-class MCP integration for seamless workflow.",
      },
      {
        icon: Sparkles,
        title: "Smart Matching",
        description: "AI-powered similarity search finds related issues.",
      },
      {
        icon: RefreshCw,
        title: "Auto-Update",
        description: "Fixes improve automatically as community learns.",
      },
    ],
  ];

  return (
    <section
      id="features"
      className="flex flex-col items-center gap-[60px] bg-gradient-to-b from-[#FDF8E8] to-[#F5F0E6] px-20 py-[100px]"
    >
      {/* Header */}
      <div className="flex flex-col items-center gap-4">
        <span className="text-sm font-semibold tracking-[2px] text-[#D4A853]">
          WHY DEVELOPERS LOVE GIM
        </span>
        <h2 className="text-center text-[48px] font-bold text-[#1A1A1A]">
          Built by Developers, for Developers
        </h2>
        <p className="max-w-[700px] text-center text-xl text-[#52525B]">
          Simple tools that respect your workflow and your privacy.
        </p>
      </div>

      {/* Features Grid */}
      <div className="flex w-full justify-center gap-6">
        {features.map((column, colIndex) => (
          <div key={colIndex} className="flex w-[400px] flex-col gap-6">
            {column.map((feature, featureIndex) => (
              <div
                key={featureIndex}
                className="flex flex-col gap-4 rounded-[20px] border border-[#E5E0D5] bg-white p-6"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#D4A85322]">
                  <feature.icon className="h-5 w-5 text-[#D4A853]" />
                </div>
                <h3 className="text-lg font-semibold text-[#1A1A1A]">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-[#52525B]">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}
