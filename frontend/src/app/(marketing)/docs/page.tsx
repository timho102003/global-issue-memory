"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  CheckCircle2,
  Terminal,
  BookOpen,
  ArrowRight,
  ExternalLink,
  Sparkles,
  UserPlus,
  Search,
  ShieldCheck,
  KeyRound,
  CircleCheckBig,
  PlugZap,
  AlertTriangle,
} from "lucide-react";
import { CodeBlock } from "@/components/ui/code-block";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";

const sections = [
  { id: "prerequisites", label: "Prerequisites", icon: CheckCircle2 },
  { id: "sign-up", label: "Sign Up", icon: UserPlus },
  { id: "add-server", label: "Add MCP Server", icon: Terminal },
  { id: "find-plugin", label: "Find Plugin", icon: Search },
  { id: "installed", label: "Verify Installed", icon: PlugZap },
  { id: "authenticate", label: "Authenticate", icon: KeyRound },
  { id: "oauth", label: "Authorize OAuth", icon: ShieldCheck },
  { id: "confirm", label: "Confirm Success", icon: CircleCheckBig },
  { id: "claude-md", label: "CLAUDE.md Setup", icon: Terminal },
  { id: "troubleshooting", label: "Troubleshooting", icon: Sparkles },
  { id: "next-steps", label: "Next Steps", icon: ArrowRight },
] as const;

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState("prerequisites");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        }
      },
      { rootMargin: "-80px 0px -60% 0px", threshold: 0.1 }
    );

    for (const section of sections) {
      const el = document.getElementById(section.id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, []);

  return (
    <div className="px-5 py-16 sm:px-8 sm:py-20 md:py-24 lg:px-12">
      <div className="mx-auto max-w-[1200px]">
        {/* Page Hero */}
        <div className="mb-12 flex flex-col items-center gap-4 text-center md:mb-16">
          <div className="flex items-center gap-2 rounded-full border border-border-light bg-white/80 px-4 py-2 shadow-[var(--shadow-xs)]">
            <BookOpen className="h-3.5 w-3.5 text-accent-warm" />
            <span className="text-[13px] font-medium text-text-primary">Documentation</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl md:text-5xl">
            Getting Started with GIM
          </h1>
          <p className="max-w-[600px] text-base leading-relaxed text-text-secondary sm:text-lg">
            Set up Global Issue Memory in your Claude Code environment in just a few steps.
          </p>
        </div>

        {/* Content Grid: Sidebar + Main */}
        <div className="flex gap-10 lg:gap-14">
          {/* Sticky ToC — desktop only */}
          <aside className="hidden w-56 shrink-0 lg:block">
            <nav className="sticky top-24 flex flex-col gap-1">
              {sections.map((s) => {
                const Icon = s.icon;
                const isActive = activeSection === s.id;
                return (
                  <a
                    key={s.id}
                    href={`#${s.id}`}
                    className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-200 ${
                      isActive
                        ? "bg-accent-warm/10 text-accent-warm"
                        : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5 shrink-0" />
                    {s.label}
                  </a>
                );
              })}
            </nav>
          </aside>

          {/* Main Content */}
          <div className="min-w-0 flex-1">
            <div className="flex flex-col gap-12 md:gap-16">
              {/* Prerequisites */}
              <section id="prerequisites">
                <div className="rounded-2xl border border-border-light bg-white p-6 shadow-[var(--shadow-card)] sm:p-8">
                  <h2 className="mb-4 text-lg font-semibold text-text-primary sm:text-xl">Prerequisites</h2>
                  <ul className="flex flex-col gap-3">
                    {[
                      "Claude Code CLI installed and configured",
                      "A GIM account (free — sign up from the dashboard)",
                      "Your GIM ID (found in your profile after sign-up)",
                    ].map((item) => (
                      <li key={item} className="flex items-start gap-3 text-[14px] text-text-secondary sm:text-[15px]">
                        <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-accent-warm" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </section>

              {/* Step 01: Sign Up */}
              <section id="sign-up">
                <StepHeader number="01" title="Sign Up & Get Your GIM ID" />
                <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
                  Create your free GIM account to get started. After signing up, you&apos;ll receive a unique GIM ID on your profile page.
                </p>
                <Link
                  href="/dashboard"
                  className="mb-6 inline-flex items-center gap-2 rounded-xl bg-accent-warm px-5 py-3 text-[14px] font-medium text-white transition-all duration-200 hover:bg-accent-warm/90 hover:shadow-[var(--shadow-card-hover)]"
                >
                  <UserPlus className="h-4 w-4" />
                  Sign up here
                </Link>
                <div className="mt-4 flex items-start gap-3 rounded-xl border border-accent-amber/30 bg-accent-amber/5 p-4">
                  <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-accent-amber" />
                  <p className="text-[13px] leading-relaxed text-text-secondary sm:text-[14px]">
                    <strong className="text-text-primary">Keep your GIM ID safe</strong> — it is your only credential for authenticating with GIM. Do not share it publicly.
                  </p>
                </div>
              </section>

              {/* Step 02: Add GIM MCP Server */}
              <section id="add-server">
                <StepHeader number="02" title="Add GIM MCP Server" />
                <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
                  Run the following command in your terminal to add GIM as an MCP server in Claude Code.
                </p>
                <Tabs defaultValue="cli">
                  <TabsList>
                    <TabsTrigger value="cli">CLI Command</TabsTrigger>
                    <TabsTrigger value="manual">Manual Config</TabsTrigger>
                  </TabsList>
                  <TabsContent value="cli">
                    <CodeBlock
                      code="claude mcp add --transport http global-issue-memory https://global-issue-memory-production.up.railway.app"
                      language="bash"
                    />
                  </TabsContent>
                  <TabsContent value="manual">
                    <p className="mb-3 text-[13px] text-text-secondary">
                      Add the following to your <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">claude_desktop_config.json</code>:
                    </p>
                    <CodeBlock
                      code={`{
  "mcpServers": {
    "global-issue-memory": {
      "type": "http",
      "url": "https://global-issue-memory-production.up.railway.app"
    }
  }
}`}
                      language="json"
                    />
                  </TabsContent>
                </Tabs>
              </section>

              {/* Step 03: Find the Plugin */}
              <section id="find-plugin">
                <StepHeader number="03" title="Find the Plugin" />
                <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
                  Use the <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">/plugin</code> command in Claude Code to browse available MCP servers and locate GIM.
                </p>
                <div className="overflow-hidden rounded-xl border border-border-light shadow-[var(--shadow-card)]">
                  <Image src="/assets/find_plugin.jpg" alt="Finding the GIM plugin in Claude Code" width={860} height={480} className="w-full" />
                </div>
              </section>

              {/* Step 04: Verify Installed */}
              <section id="installed">
                <StepHeader number="04" title="Locate GIM in Installed Servers" />
                <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
                  After adding the server, verify it appears in your installed MCP servers list.
                </p>
                <div className="overflow-hidden rounded-xl border border-border-light shadow-[var(--shadow-card)]">
                  <Image src="/assets/installed_mcp.jpg" alt="GIM shown in installed MCP servers" width={860} height={480} className="w-full" />
                </div>
              </section>

              {/* Step 05: Authenticate */}
              <section id="authenticate">
                <StepHeader number="05" title="Authenticate" />
                <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
                  When you first use a GIM tool, you&apos;ll be prompted to authenticate. Click the link to begin the OAuth flow.
                </p>
                <div className="mx-auto max-w-[520px]">
                  <div className="overflow-hidden rounded-xl border border-border-light shadow-[var(--shadow-card)]">
                    <Image src="/assets/authentication.jpg" alt="GIM authentication prompt" width={520} height={290} className="w-full" />
                  </div>
                </div>
              </section>

              {/* Step 06: Authorize via OAuth */}
              <section id="oauth">
                <StepHeader number="06" title="Authorize via OAuth" />
                <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
                  Authorize GIM to access your account. This uses a secure OAuth 2.1 flow — your credentials are never stored by GIM.
                </p>
                <div className="mx-auto max-w-[520px]">
                  <div className="overflow-hidden rounded-xl border border-border-light shadow-[var(--shadow-card)]">
                    <Image src="/assets/oauth.jpg" alt="OAuth authorization screen" width={520} height={290} className="w-full" />
                  </div>
                </div>
              </section>

              {/* Step 07: Confirm Success */}
              <section id="confirm">
                <StepHeader number="07" title="Confirm Success" />
                <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
                  You&apos;ll see a success message confirming your authentication. GIM is now ready to use.
                </p>
                <div className="mx-auto max-w-[520px]">
                  <div className="overflow-hidden rounded-xl border border-border-light shadow-[var(--shadow-card)]">
                    <Image src="/assets/auth_success.jpg" alt="Authentication success confirmation" width={520} height={290} className="w-full" />
                  </div>
                </div>
              </section>

              {/* CLAUDE.md Guidelines */}
              <section id="claude-md">
                <div className="mb-4 flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-warm/10">
                    <Terminal className="h-4 w-4 text-accent-warm" />
                  </div>
                  <h2 className="text-xl font-semibold text-text-primary sm:text-2xl">
                    CLAUDE.md Guidelines
                  </h2>
                </div>
                <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
                  Add the following to your project&apos;s <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">CLAUDE.md</code> to ensure your AI assistant uses GIM effectively:
                </p>
                <CodeBlock
                  code={`## MCP Tools Usage

### GIM (Global Issue Memory)
- **On error**: Call \`gim_search_issues\` FIRST before attempting to solve
- **After applying a GIM fix**: Call \`gim_confirm_fix\` to report outcome
- **After resolving an error yourself or from code review**: Call \`gim_submit_issue\` only if globally useful (tool description has full criteria)
- **Do not submit**: Project-local issues (DB schemas, variable bugs, business logic, typos)`}
                  language="markdown"
                />
              </section>

              {/* Troubleshooting */}
              <section id="troubleshooting">
                <div className="mb-6 flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-warm/10">
                    <Sparkles className="h-4 w-4 text-accent-warm" />
                  </div>
                  <h2 className="text-xl font-semibold text-text-primary sm:text-2xl">
                    Troubleshooting
                  </h2>
                </div>
                <Accordion type="single">
                  <AccordionItem value="not-found">
                    <AccordionTrigger value="not-found">
                      GIM server not showing up after installation
                    </AccordionTrigger>
                    <AccordionContent value="not-found">
                      Make sure you&apos;ve restarted Claude Code after adding the MCP server. You can verify the server is registered by running <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">claude mcp list</code> in your terminal.
                    </AccordionContent>
                  </AccordionItem>
                  <AccordionItem value="auth-fail">
                    <AccordionTrigger value="auth-fail">
                      Authentication fails or times out
                    </AccordionTrigger>
                    <AccordionContent value="auth-fail">
                      Check your internet connection and try again. If the OAuth window doesn&apos;t open, copy the URL from the terminal and paste it in your browser manually. Ensure pop-ups are not blocked.
                    </AccordionContent>
                  </AccordionItem>
                  <AccordionItem value="no-results">
                    <AccordionTrigger value="no-results">
                      gim_search_issues returns no results
                    </AccordionTrigger>
                    <AccordionContent value="no-results">
                      GIM&apos;s knowledge base grows with community contributions. If no match is found, solve the issue yourself and submit it with <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">gim_submit_issue</code> so future developers benefit.
                    </AccordionContent>
                  </AccordionItem>
                  <AccordionItem value="permission">
                    <AccordionTrigger value="permission">
                      Permission denied when calling GIM tools
                    </AccordionTrigger>
                    <AccordionContent value="permission">
                      Your GIM session may have expired. Re-authenticate by triggering any GIM tool — the OAuth flow will automatically start again.
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </section>

              {/* Next Steps */}
              <section id="next-steps" className="rounded-2xl border border-border-light bg-white p-6 shadow-[var(--shadow-card)] sm:p-8">
                <h2 className="mb-2 text-lg font-semibold text-text-primary sm:text-xl">
                  Next Steps
                </h2>
                <p className="mb-6 text-[14px] text-text-secondary sm:text-[15px]">
                  You&apos;re all set! Here are some useful links to continue:
                </p>
                <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                  <Link
                    href="/dashboard"
                    className="inline-flex items-center gap-2 rounded-xl border border-border-light px-5 py-3 text-[14px] font-medium text-text-primary transition-all duration-200 hover:bg-bg-muted hover:shadow-[var(--shadow-card-hover)]"
                  >
                    <ArrowRight className="h-4 w-4 text-accent-warm" />
                    Go to Dashboard
                  </Link>
                  <a
                    href="https://github.com/timho102003/global-issue-memory"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-xl border border-border-light px-5 py-3 text-[14px] font-medium text-text-primary transition-all duration-200 hover:bg-bg-muted hover:shadow-[var(--shadow-card-hover)]"
                  >
                    <ExternalLink className="h-4 w-4 text-accent-warm" />
                    View on GitHub
                  </a>
                </div>
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/** Reusable step header with number badge. */
function StepHeader({ number, title }: { number: string; title: string }) {
  return (
    <div className="mb-4 flex items-center gap-3">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-warm/10 text-[13px] font-bold text-accent-warm">
        {number}
      </span>
      <h2 className="text-xl font-semibold text-text-primary sm:text-2xl">{title}</h2>
    </div>
  );
}
