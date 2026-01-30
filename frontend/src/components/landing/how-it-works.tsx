import { UserPlus, Terminal, Shield, Heart } from "lucide-react";
import { CodeBlock } from "@/components/ui/code-block";

const cliCommand = `claude mcp add --transport http global-issue-memory https://global-issue-memory-production.up.railway.app`;

const profileMcpConfig = `{
  "mcpServers": {
    "global-issue-memory": {
      "type": "http",
      "url": "https://global-issue-memory-production.up.railway.app"
    }
  }
}`;

/**
 * How It Works section with 3-step setup cards and responsive grid.
 */
export function HowItWorks() {
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
        <div className="grid w-full grid-cols-1 gap-4 sm:gap-5 lg:grid-cols-3">
          {/* Step 1: Sign Up */}
          <div className="flex flex-col gap-4 rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)] transition-all duration-200 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5 sm:p-7">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold tracking-tight text-accent-warm">01</span>
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#FEF3C7]">
                <UserPlus className="h-4 w-4 text-accent-warm" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-text-primary">Sign Up &amp; Get Your GIM ID</h3>
            <p className="text-[14px] leading-relaxed text-text-secondary">
              Create your account at{" "}
              <a
                href="https://global-issue-memory.vercel.app"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-warm underline underline-offset-2 transition-colors duration-150 hover:text-accent-warm/80"
              >
                global-issue-memory.vercel.app
              </a>{" "}
              to get your unique GIM ID.
            </p>
          </div>

          {/* Step 2: Add GIM to Claude Code */}
          <div className="flex flex-col gap-4 rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)] transition-all duration-200 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5 sm:p-7">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold tracking-tight text-accent-warm">02</span>
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#FEF3C7]">
                <Terminal className="h-4 w-4 text-accent-warm" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-text-primary">Add GIM to Your Claude Code</h3>
            <p className="text-[14px] leading-relaxed text-text-secondary">
              Run this command in your terminal:
            </p>
            <CodeBlock code={cliCommand} language="bash" showCopy />
            <p className="text-[14px] leading-relaxed text-text-secondary">
              Or add to your{" "}
              <span className="font-medium text-text-primary">Profile MCP</span> settings:
            </p>
            <CodeBlock code={profileMcpConfig} language="json" showCopy />
          </div>

          {/* Step 3: Authenticate */}
          <div className="flex flex-col gap-4 rounded-2xl border border-border-light/80 bg-white p-6 shadow-[var(--shadow-card)] transition-all duration-200 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5 sm:p-7">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold tracking-tight text-accent-warm">03</span>
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#FEF3C7]">
                <Shield className="h-4 w-4 text-accent-warm" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-text-primary">Authenticate Your Plugin</h3>
            <p className="text-[14px] leading-relaxed text-text-secondary">
              Navigate to{" "}
              <span className="font-mono text-accent-warm">/plugin</span>, select{" "}
              <span className="font-medium text-text-primary">Installed</span>, and authenticate{" "}
              <span className="font-medium text-text-primary">global-issue-memory</span>{" "}
              with your GIM ID.
            </p>
          </div>
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
