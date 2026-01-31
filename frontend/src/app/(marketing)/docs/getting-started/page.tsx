import type { Metadata } from "next";
import Link from "next/link";
import {
  UserPlus,
  Terminal,
  Search,
  PlugZap,
  KeyRound,
  FileCode,
  ArrowRight,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Getting Started",
};

const steps = [
  {
    number: "01",
    title: "Sign Up",
    description: "Create your free GIM account and get your unique GIM ID.",
    href: "/docs/getting-started/sign-up",
    icon: UserPlus,
  },
  {
    number: "02",
    title: "Add MCP Server",
    description: "Add GIM as an MCP server in your Claude Code environment.",
    href: "/docs/getting-started/add-mcp-server",
    icon: Terminal,
  },
  {
    number: "03",
    title: "Find Plugin",
    description: "Locate GIM in the available MCP plugins list.",
    href: "/docs/getting-started/find-plugin",
    icon: Search,
  },
  {
    number: "04",
    title: "Verify Installation",
    description: "Confirm GIM appears in your installed MCP servers.",
    href: "/docs/getting-started/verify-installation",
    icon: PlugZap,
  },
  {
    number: "05",
    title: "Authentication",
    description: "Authenticate with GIM via the secure OAuth 2.1 flow.",
    href: "/docs/getting-started/authentication",
    icon: KeyRound,
  },
  {
    number: "06",
    title: "CLAUDE.md Setup",
    description: "Configure your CLAUDE.md to use GIM tools effectively.",
    href: "/docs/getting-started/claude-md-setup",
    icon: FileCode,
  },
];

export default function GettingStartedOverview() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Getting Started
      </h1>
      <p className="mb-8 max-w-[600px] text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        Set up Global Issue Memory in your Claude Code environment in just a few
        steps. Follow this guide from start to finish.
      </p>

      <div className="flex flex-col gap-3">
        {steps.map((step) => {
          const Icon = step.icon;
          return (
            <Link
              key={step.href}
              href={step.href}
              className="group flex items-center gap-4 rounded-xl border border-border-light bg-white p-4 shadow-[var(--shadow-card)] transition-all duration-200 hover:shadow-[var(--shadow-card-hover)] sm:p-5"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-warm/10 text-[13px] font-bold text-accent-warm">
                {step.number}
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-[15px] font-semibold text-text-primary">
                  {step.title}
                </h2>
                <p className="text-[13px] text-text-secondary">
                  {step.description}
                </p>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-text-muted transition-all duration-150 group-hover:translate-x-0.5 group-hover:text-accent-warm" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
