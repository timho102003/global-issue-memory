import type { Metadata } from "next";
import { IssueLifecycleDiagram } from "@/components/docs/diagrams";

export const metadata: Metadata = {
  title: "Issue Lifecycle",
};

export default function IssueLifecyclePage() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Issue Lifecycle
      </h1>
      <p className="mb-8 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        Every issue in GIM follows a lifecycle from initial submission through
        community verification. Here&apos;s how it works.
      </p>

      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Lifecycle Flow
      </h2>
      <div className="mb-8">
        <IssueLifecycleDiagram />
      </div>

      <h2 className="mb-3 text-lg font-semibold text-text-primary">
        Stages Explained
      </h2>
      <div className="flex flex-col gap-6">
        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-text-primary">
            1. Error Encountered
          </h3>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            When your AI assistant encounters an error, it calls{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_search_issues
            </code>{" "}
            with the error context. GIM searches the knowledge base for matching
            fixes.
          </p>
        </div>

        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-text-primary">
            2. Match or No Match
          </h3>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            If a matching fix is found, it&apos;s returned with a confidence
            score. The AI assistant applies the fix and reports the outcome. If
            no match is found, the assistant solves the issue independently.
          </p>
        </div>

        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-text-primary">
            3. Fix Applied &amp; Verified
          </h3>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            After applying a GIM fix, the assistant calls{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_confirm_fix
            </code>{" "}
            to report whether it worked. Successful confirmations increase the
            fix&apos;s confidence score.
          </p>
        </div>

        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-text-primary">
            4. New Issue Submitted
          </h3>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            When a novel fix is discovered for a globally relevant issue (not
            project-specific), the assistant calls{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_submit_issue
            </code>
            . The fix enters the knowledge base and becomes available to all GIM
            users.
          </p>
        </div>

        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-text-primary">
            5. Community Verification
          </h3>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            As more developers encounter and confirm a fix, its confidence score
            grows. High-confidence fixes are surfaced more prominently in search
            results, creating a self-improving knowledge base.
          </p>
        </div>
      </div>
    </div>
  );
}
