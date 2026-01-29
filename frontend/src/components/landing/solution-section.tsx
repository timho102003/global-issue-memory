import { X, Check, Zap, Users, Shield, RefreshCw } from "lucide-react";

/**
 * Solution section with before/after comparison and benefits grid.
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
    <section className="bg-gradient-to-b from-bg-gradient-start to-bg-tertiary px-5 py-16 sm:px-8 sm:py-20 md:py-24 lg:px-12">
      <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-12 md:gap-14">
        {/* Header */}
        <div className="flex flex-col items-center gap-3">
          <span className="text-[11px] font-semibold tracking-[2px] text-accent-warm uppercase">
            How GIM Helps
          </span>
          <h2 className="text-center text-2xl font-bold tracking-tight text-text-primary sm:text-3xl md:text-4xl lg:text-[44px] lg:leading-[1.15]">
            A Shared Memory for All of Us
          </h2>
          <p className="max-w-[620px] text-center text-[14px] leading-relaxed text-text-secondary sm:text-base md:text-lg">
            When your AI solves something new, GIM remembers. When you hit a known issue,
            GIM helps instantly. We all learn from each other.
          </p>
        </div>

        {/* Before/After Comparison */}
        <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5">
          {/* Without GIM */}
          <div className="flex flex-col gap-5 rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)] sm:p-8">
            <h3 className="text-[15px] font-semibold text-text-primary">Without GIM</h3>
            <div className="flex flex-col gap-3">
              {withoutGim.map((item, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-50">
                    <X className="h-3 w-3 text-red-400" />
                  </div>
                  <span className="text-[13px] text-text-secondary">{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* With GIM */}
          <div className="flex flex-col gap-5 rounded-2xl border border-accent-warm/30 bg-white p-6 shadow-[var(--shadow-card)] sm:p-8">
            <h3 className="text-[15px] font-semibold text-text-primary">With GIM</h3>
            <div className="flex flex-col gap-3">
              {withGim.map((item, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-green-50">
                    <Check className="h-3 w-3 text-green-600" />
                  </div>
                  <span className="text-[13px] text-text-secondary">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Benefits Grid */}
        <div className="grid w-full grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          {benefits.map((benefit, index) => (
            <div
              key={index}
              className="flex flex-col items-center gap-2.5 rounded-2xl bg-bg-muted p-5 transition-colors hover:bg-white hover:shadow-[var(--shadow-card)] sm:gap-3 sm:p-6"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-warm/10">
                <benefit.icon className="h-5 w-5 text-accent-warm" />
              </div>
              <h4 className="text-[14px] font-semibold text-text-primary">{benefit.title}</h4>
              <p className="text-center text-[12px] leading-relaxed text-text-secondary sm:text-[13px]">{benefit.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
