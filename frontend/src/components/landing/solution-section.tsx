import { X, Check, Zap, Users, Shield, RefreshCw } from "lucide-react";

/**
 * Solution section matching GIM.pen design.
 */
export function SolutionSection() {
  const withoutGim = [
    "Spend hours debugging the same issue",
    "Burn tokens on repeated problems",
    "Context windows filled with noise",
    "Solutions lost in chat history",
  ];

  const withGim = [
    "Instant access to verified fixes",
    "Community-validated solutions",
    "Clean context, focused assistance",
    "Solutions preserved and improved",
  ];

  const benefits = [
    {
      icon: Zap,
      title: "Instant Fixes",
      description: "Get working solutions in seconds, not hours",
    },
    {
      icon: Users,
      title: "Community Verified",
      description: "Every fix tested by real developers",
    },
    {
      icon: Shield,
      title: "Privacy First",
      description: "Your code stays private, only solutions shared",
    },
    {
      icon: RefreshCw,
      title: "Always Learning",
      description: "The community grows smarter together",
    },
  ];

  return (
    <section className="flex flex-col items-center gap-[60px] bg-gradient-to-b from-[#FDF8E8] to-[#F5F0E6] px-20 py-[100px]">
      {/* Header */}
      <div className="flex flex-col items-center gap-4">
        <span className="text-xs font-semibold tracking-[2px] text-[#D4A853]">
          HOW GIM HELPS
        </span>
        <h2 className="text-center text-[48px] font-bold text-[#1A1A1A]">
          A Shared Memory for All of Us
        </h2>
        <p className="max-w-[700px] text-center text-lg leading-[1.6] text-[#52525B]">
          When your AI solves something new, GIM remembers. When you hit a known issue,
          GIM helps instantly. We all learn from each other.
        </p>
      </div>

      {/* Before/After Comparison */}
      <div className="flex w-full gap-6">
        {/* Without GIM */}
        <div className="flex flex-1 flex-col gap-5 rounded-[20px] border border-[#E5E0D5] bg-white p-8">
          <h3 className="text-lg font-semibold text-[#1A1A1A]">Without GIM</h3>
          <div className="flex flex-col gap-3">
            {withoutGim.map((item, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100">
                  <X className="h-3 w-3 text-red-500" />
                </div>
                <span className="text-sm text-[#52525B]">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* With GIM */}
        <div className="flex flex-1 flex-col gap-5 rounded-[20px] border border-[#D4A85366] bg-white p-8">
          <h3 className="text-lg font-semibold text-[#1A1A1A]">With GIM</h3>
          <div className="flex flex-col gap-3">
            {withGim.map((item, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-green-100">
                  <Check className="h-3 w-3 text-green-600" />
                </div>
                <span className="text-sm text-[#52525B]">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Benefits Grid */}
      <div className="flex w-full gap-5">
        {benefits.map((benefit, index) => (
          <div
            key={index}
            className="flex flex-1 flex-col items-center gap-3 rounded-2xl bg-[#F9F6F0] p-6"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#D4A85322]">
              <benefit.icon className="h-5 w-5 text-[#D4A853]" />
            </div>
            <h4 className="font-semibold text-[#1A1A1A]">{benefit.title}</h4>
            <p className="text-center text-sm text-[#52525B]">{benefit.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
