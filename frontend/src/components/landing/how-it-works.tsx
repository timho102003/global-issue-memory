import { Download, Search, Share2, Heart } from "lucide-react";

/**
 * How It Works section matching GIM.pen design.
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
    <section id="how-it-works" className="flex flex-col items-center gap-[60px] bg-[#F5F0E6] px-20 py-[100px]">
      {/* Header */}
      <div className="flex flex-col items-center gap-4">
        <span className="text-xs font-semibold tracking-[2px] text-[#D4A853]">
          GETTING STARTED
        </span>
        <h2 className="text-center text-[48px] font-bold text-[#1A1A1A]">
          Simple Setup. Immediate Value.
        </h2>
      </div>

      {/* Steps */}
      <div className="flex w-full gap-8">
        {steps.map((step, index) => (
          <div
            key={index}
            className="flex flex-1 flex-col gap-5 rounded-[20px] border border-[#E5E0D5] bg-white p-8"
          >
            <div className="flex items-center gap-4">
              <span className="text-3xl font-bold text-[#D4A853]">{step.number}</span>
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#FEF3C7]">
                <step.icon className="h-5 w-5 text-[#D4A853]" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-[#1A1A1A]">{step.title}</h3>
            <p className="text-base leading-relaxed text-[#52525B]">
              {step.description}
            </p>
            {step.code && (
              <code className="rounded-lg bg-[#1E1E1E] px-4 py-3 font-mono text-sm text-white">
                {step.code}
              </code>
            )}
          </div>
        ))}
      </div>

      {/* Bonus Step */}
      <div className="flex w-full items-center gap-6 rounded-[20px] border border-[#D4A85344] bg-[#FDF5E6] p-8">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[#D4A85322]">
          <Heart className="h-7 w-7 text-[#D4A853]" />
        </div>
        <div className="flex flex-col gap-2">
          <h4 className="text-lg font-semibold text-[#1A1A1A]">
            That&apos;s it. You&apos;re part of the community.
          </h4>
          <p className="text-base text-[#52525B]">
            Every fix you use and share makes the whole community smarter. Together, we&apos;re
            building a global knowledge base for AI development.
          </p>
        </div>
      </div>
    </section>
  );
}
