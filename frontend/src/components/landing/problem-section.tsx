import { Repeat, Ban } from "lucide-react";

/**
 * Problem section with responsive layout and proper container.
 */
export function ProblemSection() {
  const problems = [
    {
      icon: Repeat,
      title: "Repeat Debugging",
      description:
        "The same errors hit developers worldwide, each one burning tokens and time solving what's already been solved.",
    },
    {
      icon: Ban,
      title: "Context Pollution",
      description:
        "Long debugging sessions fill context windows with noise, making AI assistants less effective over time.",
    },
  ];

  return (
    <section className="bg-bg-tertiary px-5 py-16 sm:px-8 sm:py-20 md:py-24 lg:px-12">
      <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-12 md:gap-14">
        {/* Header */}
        <div className="flex flex-col items-center gap-3">
          <span className="text-[11px] font-semibold tracking-[2px] text-accent-gold uppercase">
            The Challenge
          </span>
          <h2 className="max-w-[700px] text-center text-2xl font-bold tracking-tight text-text-primary sm:text-3xl md:text-4xl lg:text-[44px] lg:leading-[1.15]">
            We&apos;ve All Been There
          </h2>
        </div>

        {/* Problem Cards */}
        <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5">
          {problems.map((problem, index) => (
            <div
              key={index}
              className="flex flex-col gap-4 rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)] transition-all duration-200 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5 sm:p-8"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#FEF3C7]">
                <problem.icon className="h-5 w-5 text-accent-warm" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary">{problem.title}</h3>
              <p className="text-[14px] leading-relaxed text-text-secondary">
                {problem.description}
              </p>
            </div>
          ))}
        </div>

        {/* Closer */}
        <div className="w-full rounded-2xl border border-accent-warm/20 bg-white px-6 py-6 shadow-[var(--shadow-sm)] sm:px-10 sm:py-8">
          <p className="text-center text-base font-medium text-text-primary sm:text-lg">
            What if we could share what works — and skip what doesn&apos;t?
          </p>
        </div>
      </div>
    </section>
  );
}
