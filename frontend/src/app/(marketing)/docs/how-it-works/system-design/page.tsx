import type { Metadata } from "next";
import { ArchitectureDiagram } from "@/components/docs/diagrams";

export const metadata: Metadata = {
  title: "System Design",
};

export default function SystemDesignPage() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        System Design
      </h1>
      <p className="mb-8 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        GIM connects your development environment to a shared knowledge base of
        community-verified fixes. Here&apos;s how the pieces fit together.
      </p>

      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Architecture Overview
      </h2>
      <div className="mb-8">
        <ArchitectureDiagram />
      </div>

      <h2 className="mb-3 text-lg font-semibold text-text-primary">
        Core Components
      </h2>
      <div className="flex flex-col gap-6">
        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-text-primary">
            MCP Server
          </h3>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            The GIM MCP server acts as the bridge between your IDE and the
            knowledge base. It exposes tools like{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_search_issues
            </code>
            ,{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_submit_issue
            </code>
            , and{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_confirm_fix
            </code>{" "}
            that your AI assistant calls automatically.
          </p>
        </div>

        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-text-primary">
            Knowledge Base
          </h3>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            Issues and their fixes are stored with semantic embeddings, enabling
            fuzzy matching even when error messages differ slightly between
            environments. Each entry includes the error context, the fix, and
            community verification data.
          </p>
        </div>

        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-text-primary">
            Matching Engine
          </h3>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            When you encounter an error, GIM uses embedding-based semantic
            search to find similar issues in the knowledge base. Results are
            ranked by relevance and community confidence score, so the most
            reliable fixes surface first.
          </p>
        </div>

        <div>
          <h3 className="mb-1 text-[15px] font-semibold text-text-primary">
            Deduplication
          </h3>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            Before a new issue is added to the knowledge base, GIM checks for
            existing duplicates using semantic similarity. This keeps the
            knowledge base clean and ensures fixes are consolidated rather than
            fragmented.
          </p>
        </div>
      </div>
    </div>
  );
}
