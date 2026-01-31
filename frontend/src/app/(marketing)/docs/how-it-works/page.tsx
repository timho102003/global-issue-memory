import type { Metadata } from "next";
import Link from "next/link";
import { Layers, GitBranch, ArrowRight } from "lucide-react";

export const metadata: Metadata = {
  title: "How It Works",
};

const topics = [
  {
    title: "System Design",
    description:
      "Understand GIM's architecture — how the MCP server, knowledge base, and matching engine connect.",
    href: "/docs/how-it-works/system-design",
    icon: Layers,
  },
  {
    title: "Issue Lifecycle",
    description:
      "Follow an issue from submission through matching, verification, and promotion to the knowledge base.",
    href: "/docs/how-it-works/issue-lifecycle",
    icon: GitBranch,
  },
];

export default function HowItWorksOverview() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        How It Works
      </h1>
      <p className="mb-8 max-w-[600px] text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        A closer look at GIM&apos;s internals — how issues are matched,
        verified, and shared across the developer community.
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {topics.map((topic) => {
          const Icon = topic.icon;
          return (
            <Link
              key={topic.href}
              href={topic.href}
              className="group block rounded-2xl border border-border-light bg-white p-6 shadow-[var(--shadow-card)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[var(--shadow-card-hover)]"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-accent-warm/10">
                <Icon className="h-5 w-5 text-accent-warm" />
              </div>
              <h2 className="mb-2 text-lg font-semibold text-text-primary">
                {topic.title}
              </h2>
              <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
                {topic.description}
              </p>
              <span className="inline-flex items-center gap-1.5 text-[13px] font-medium text-accent-warm transition-all duration-150 group-hover:gap-2">
                Read more
                <ArrowRight className="h-3.5 w-3.5" />
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
