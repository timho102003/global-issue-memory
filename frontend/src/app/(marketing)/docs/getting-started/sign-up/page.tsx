import type { Metadata } from "next";
import Link from "next/link";
import { UserPlus } from "lucide-react";
import { DocsCallout } from "@/components/docs/docs-callout";

export const metadata: Metadata = {
  title: "Sign Up",
};

export default function SignUpPage() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Sign Up &amp; Get Your GIM ID
      </h1>
      <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        Create your free GIM account to get started. After signing up,
        you&apos;ll receive a unique GIM ID on your profile page.
      </p>

      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Prerequisites
      </h2>
      <div className="mb-8 rounded-2xl border border-border-light bg-white p-6 shadow-[var(--shadow-card)]">
        <ul className="flex flex-col gap-3">
          {[
            "Claude Code CLI installed and configured",
            "A GIM account (free — sign up from the dashboard)",
            "Your GIM ID (found in your profile after sign-up)",
          ].map((item) => (
            <li
              key={item}
              className="flex items-start gap-3 text-[14px] text-text-secondary sm:text-[15px]"
            >
              <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-accent-warm" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Create Your Account
      </h2>
      <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        Click the button below to navigate to the dashboard and create your
        account.
      </p>
      <Link
        href="/dashboard"
        className="mb-6 inline-flex items-center gap-2 rounded-xl bg-accent-warm px-5 py-3 text-[14px] font-medium text-white transition-all duration-200 hover:bg-accent-warm/90 hover:shadow-[var(--shadow-card-hover)]"
      >
        <UserPlus className="h-4 w-4" />
        Sign up here
      </Link>

      <div className="mt-6">
        <DocsCallout variant="warning" title="Keep your GIM ID safe">
          Your GIM ID is your only credential for authenticating with GIM. Do
          not share it publicly.
        </DocsCallout>
      </div>
    </div>
  );
}
