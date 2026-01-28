import { Repeat, Ban, AlertTriangle } from "lucide-react";

/**
 * Problem section matching GIM.pen design.
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
    <section className="flex flex-col items-center gap-[60px] bg-[#F5F0E6] px-20 py-[100px]">
      {/* Header */}
      <div className="flex flex-col items-center gap-4">
        <span className="text-xs font-semibold tracking-[2px] text-[#B8860B]">
          THE CHALLENGE
        </span>
        <h2 className="max-w-[800px] text-center text-[48px] font-bold text-[#1A1A1A]">
          We&apos;ve All Been There
        </h2>
      </div>

      {/* Problem Cards */}
      <div className="flex w-full gap-6">
        {problems.map((problem, index) => (
          <div
            key={index}
            className="flex flex-1 flex-col gap-5 rounded-[20px] border border-[#E5E0D5] bg-white p-8"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#FEF3C7]">
              <problem.icon className="h-6 w-6 text-[#D4A853]" />
            </div>
            <h3 className="text-xl font-semibold text-[#1A1A1A]">{problem.title}</h3>
            <p className="text-base leading-relaxed text-[#52525B]">
              {problem.description}
            </p>
          </div>
        ))}
      </div>

      {/* Closer */}
      <div className="flex items-center justify-center rounded-2xl border border-[#D4A85333] bg-white px-12 py-8">
        <p className="text-center text-xl font-medium text-[#1A1A1A]">
          What if we could share what works — and skip what doesn&apos;t?
        </p>
      </div>
    </section>
  );
}
