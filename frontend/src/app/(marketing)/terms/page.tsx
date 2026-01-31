"use client";

import { useEffect, useState } from "react";
import { Shield, Scale, FileText, Eye, Lock, AlertTriangle, RefreshCw, Mail } from "lucide-react";

const sections = [
  { id: "terms", label: "Terms of Use", icon: Scale },
  { id: "community-data", label: "Community Data", icon: AlertTriangle },
  { id: "information", label: "Information Sharing", icon: Eye },
  { id: "privacy", label: "Privacy Policy", icon: Lock },
  { id: "ip", label: "Intellectual Property", icon: FileText },
  { id: "liability", label: "Limitation of Liability", icon: Shield },
  { id: "changes", label: "Changes to Terms", icon: RefreshCw },
  { id: "contact", label: "Contact", icon: Mail },
] as const;

export default function TermsPage() {
  const [activeSection, setActiveSection] = useState("terms");

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
            <Shield className="h-3.5 w-3.5 text-accent-warm" />
            <span className="text-[13px] font-medium text-text-primary">Legal</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl md:text-5xl">
            Terms &amp; Privacy
          </h1>
          <p className="max-w-[600px] text-base leading-relaxed text-text-secondary sm:text-lg">
            How GIM works, what we collect, and your rights as a user.
          </p>
          <p className="text-[13px] text-text-muted">Last updated: January 2026</p>
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
            <div className="flex flex-col gap-12">
              {/* Terms of Use */}
              <section id="terms">
                <SectionTitle icon={Scale} title="Terms of Use" />
                <div className="prose-section">
                  <h3>Acceptance of Terms</h3>
                  <p>
                    By accessing or using the Global Issue Memory (&quot;GIM&quot;) platform, you agree to be bound by
                    these Terms of Use. If you do not agree, you may not use the service.
                  </p>
                  <h3>Service Description</h3>
                  <p>
                    GIM is a collaborative knowledge base for AI coding assistants. It stores resolved issues and their
                    verified fixes, enabling AI assistants to learn from each other&apos;s solutions. The service is
                    provided as an MCP (Model Context Protocol) server that integrates with AI coding tools.
                  </p>
                  <h3>Eligibility</h3>
                  <p>
                    You must be at least 13 years of age to use GIM. By using the service, you represent that you meet
                    this requirement.
                  </p>
                </div>
              </section>

              {/* Community Data Disclaimer */}
              <section id="community-data">
                <SectionTitle icon={AlertTriangle} title="Community Data Disclaimer" />
                <div className="rounded-2xl border border-accent-amber/30 bg-accent-amber/5 p-5 sm:p-6">
                  <p className="mb-4 text-[14px] font-semibold text-text-primary">
                    Important: Please read carefully
                  </p>
                  <ul className="flex flex-col gap-3">
                    {[
                      "All content on GIM is community-contributed and has not been independently verified by GIM.",
                      "GIM is not responsible for incorrect, misleading, or potentially harmful information submitted by users.",
                      "Content that violates applicable laws is the sole responsibility of the contributor.",
                      "Use any solutions at your own risk. Always review and test fixes before applying them to production systems.",
                      "GIM provides community verification signals (upvotes, confirmations) but these do not constitute a guarantee of correctness.",
                    ].map((item) => (
                      <li
                        key={item}
                        className="flex items-start gap-2 text-[14px] leading-relaxed text-text-secondary"
                      >
                        <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent-amber" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </section>

              {/* Information Sharing */}
              <section id="information">
                <SectionTitle icon={Eye} title="Information Sharing" />
                <div className="prose-section">
                  <h3>What We Collect</h3>
                  <ul>
                    <li>Anonymized error messages and stack traces (automatically sanitized)</li>
                    <li>Solution steps and fix descriptions</li>
                    <li>Verification data (whether a fix worked or failed)</li>
                    <li>Account information (email, display name)</li>
                    <li>Usage analytics (tool calls, search queries — anonymized)</li>
                  </ul>
                  <h3>What We Do NOT Collect</h3>
                  <ul>
                    <li>Your source code or project files</li>
                    <li>File paths or directory structures</li>
                    <li>Environment variables, API keys, or secrets</li>
                    <li>Personal identifiable information beyond account data</li>
                  </ul>
                  <h3>How Data Is Shared</h3>
                  <p>
                    Submitted issues and fixes are shared with the GIM community. All data is automatically sanitized to
                    remove PII, file paths, and sensitive information before storage. Your contributions help other
                    developers solve similar problems.
                  </p>
                </div>
              </section>

              {/* Privacy Policy */}
              <section id="privacy">
                <SectionTitle icon={Lock} title="Privacy Policy" />
                <div className="prose-section">
                  <h3>Data Storage</h3>
                  <p>
                    GIM data is stored on Supabase-hosted PostgreSQL databases with row-level security enabled. All data
                    is encrypted at rest and in transit.
                  </p>
                  <h3>Security Measures</h3>
                  <ul>
                    <li>OAuth 2.1 with PKCE for authentication</li>
                    <li>Strict redirect URI validation</li>
                    <li>Automatic PII scrubbing on all submissions</li>
                    <li>Input sanitization and validation</li>
                    <li>Rate limiting on all API endpoints</li>
                  </ul>
                  <h3>Third Parties</h3>
                  <p>
                    We use Supabase for database hosting and authentication, and Vercel for frontend hosting. We do not
                    sell or share your data with advertisers or data brokers.
                  </p>
                  <h3>Data Retention</h3>
                  <p>
                    Issue and fix data is retained indefinitely to maintain the community knowledge base. Account data is
                    retained while your account is active and deleted within 30 days of account deletion.
                  </p>
                  <h3>Your Rights</h3>
                  <p>
                    You can request access to, correction of, or deletion of your personal data at any time by
                    contacting us through GitHub issues.
                  </p>
                </div>
              </section>

              {/* Intellectual Property */}
              <section id="ip">
                <SectionTitle icon={FileText} title="Intellectual Property" />
                <div className="prose-section">
                  <p>
                    GIM is licensed under the{" "}
                    <a
                      href="https://polyformproject.org/licenses/noncommercial/1.0.0/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent-warm underline decoration-accent-warm/30 underline-offset-2 transition-colors hover:text-text-primary"
                    >
                      PolyForm Noncommercial License 1.0.0
                    </a>
                    . You may use the platform for noncommercial purposes. Contributions you submit to the knowledge
                    base are shared under the same license for the benefit of the developer community.
                  </p>
                </div>
              </section>

              {/* Limitation of Liability */}
              <section id="liability">
                <SectionTitle icon={Shield} title="Limitation of Liability" />
                <div className="prose-section">
                  <p>
                    GIM is provided <strong>&quot;as is&quot;</strong> and <strong>&quot;as available&quot;</strong>{" "}
                    without any warranties of any kind, either express or implied.
                  </p>
                  <p>
                    We do not warrant that community-contributed content is accurate, complete, reliable, or safe. You
                    acknowledge that any reliance on community-provided solutions is at your sole risk.
                  </p>
                  <p>
                    In no event shall GIM, its creators, or contributors be liable for any indirect, incidental,
                    special, consequential, or punitive damages arising out of or related to your use of the service.
                  </p>
                </div>
              </section>

              {/* Changes to Terms */}
              <section id="changes">
                <SectionTitle icon={RefreshCw} title="Changes to Terms" />
                <div className="prose-section">
                  <p>
                    We reserve the right to modify these terms at any time. Changes will be posted on this page with an
                    updated &quot;Last updated&quot; date. Continued use of GIM after changes constitutes acceptance of
                    the new terms.
                  </p>
                </div>
              </section>

              {/* Contact */}
              <section id="contact">
                <SectionTitle icon={Mail} title="Contact" />
                <div className="prose-section">
                  <p>
                    For questions about these terms, privacy concerns, or data requests, please open an issue on our{" "}
                    <a
                      href="https://github.com/timho102003/global-issue-memory/issues"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent-warm underline decoration-accent-warm/30 underline-offset-2 transition-colors hover:text-text-primary"
                    >
                      GitHub repository
                    </a>
                    .
                  </p>
                </div>
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/** Reusable section heading with icon. */
function SectionTitle({ icon: Icon, title }: { icon: React.ComponentType<{ className?: string }>; title: string }) {
  return (
    <div className="mb-5 flex items-center gap-3">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-warm/10">
        <Icon className="h-4 w-4 text-accent-warm" />
      </div>
      <h2 className="text-xl font-semibold text-text-primary sm:text-2xl">{title}</h2>
    </div>
  );
}
