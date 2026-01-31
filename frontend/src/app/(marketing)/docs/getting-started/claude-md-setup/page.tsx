import type { Metadata } from "next";
import { CodeBlock } from "@/components/ui/code-block";
import { DocsCallout } from "@/components/docs/docs-callout";

export const metadata: Metadata = {
  title: "CLAUDE.md Setup",
};

export default function ClaudeMdSetupPage() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        CLAUDE.md Setup
      </h1>
      <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        Add the following to your project&apos;s{" "}
        <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
          CLAUDE.md
        </code>{" "}
        to ensure your AI assistant uses GIM effectively.
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

      <div className="mt-6">
        <DocsCallout variant="tip" title="Why add this?">
          These guidelines help your AI assistant know when to search GIM for
          existing solutions and when to contribute new fixes back to the
          community knowledge base.
        </DocsCallout>
      </div>
    </div>
  );
}
