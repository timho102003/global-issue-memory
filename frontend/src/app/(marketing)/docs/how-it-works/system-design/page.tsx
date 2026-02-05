import type { Metadata } from "next";
import { ArchitectureDiagram } from "@/components/docs/diagrams";
import { DocsCallout } from "@/components/docs/docs-callout";
import { CodeBlock } from "@/components/ui/code-block";

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

      {/* Architecture Overview */}
      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Architecture Overview
      </h2>
      <div className="mb-10">
        <ArchitectureDiagram />
      </div>

      {/* Data Flow */}
      <h2 className="mb-3 text-lg font-semibold text-text-primary">
        Data Flow
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
        When your AI assistant encounters an error, the following sequence
        occurs:
      </p>
      <ol className="mb-4 list-inside list-decimal space-y-2 text-[14px] text-text-secondary">
        <li>AI assistant encounters an error during coding</li>
        <li>
          Calls an MCP tool (e.g.,{" "}
          <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
            gim_search_issues
          </code>
          )
        </li>
        <li>GIM Server receives the request and sanitizes input</li>
        <li>Generates semantic embedding via Gemini</li>
        <li>Performs vector search in Qdrant</li>
        <li>Returns ranked results to the AI assistant</li>
      </ol>
      <div className="mb-10">
        <DocsCallout variant="info" title="MCP Protocol">
          GIM uses the Model Context Protocol (MCP), an open standard that
          allows AI assistants to interact with external tools securely. Your AI
          assistant calls GIM tools like regular functions—no manual
          configuration required.
        </DocsCallout>
      </div>

      {/* Core Components */}
      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Core Components
      </h2>
      <div className="flex flex-col gap-8">
        {/* MCP Server */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            MCP Server
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            The GIM MCP server acts as the bridge between your IDE and the
            knowledge base. It exposes tools that your AI assistant calls
            automatically when handling errors.
          </p>

          <h4 className="mb-2 text-[14px] font-semibold text-text-primary">
            Available Tools
          </h4>
          <div className="mb-4 overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-border-light">
                  <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                    Tool
                  </th>
                  <th className="py-2 text-left font-semibold text-text-primary">
                    Purpose
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border-light/50">
                  <td className="py-2 pr-4">
                    <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                      gim_search_issues
                    </code>
                  </td>
                  <td className="py-2 text-text-secondary">
                    Find existing solutions for an error
                  </td>
                </tr>
                <tr className="border-b border-border-light/50">
                  <td className="py-2 pr-4">
                    <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                      gim_get_fix_bundle
                    </code>
                  </td>
                  <td className="py-2 text-text-secondary">
                    Get detailed fix for a matched issue
                  </td>
                </tr>
                <tr className="border-b border-border-light/50">
                  <td className="py-2 pr-4">
                    <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                      gim_submit_issue
                    </code>
                  </td>
                  <td className="py-2 text-text-secondary">
                    Submit a new resolved issue
                  </td>
                </tr>
                <tr className="border-b border-border-light/50">
                  <td className="py-2 pr-4">
                    <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                      gim_confirm_fix
                    </code>
                  </td>
                  <td className="py-2 text-text-secondary">
                    Report fix outcome (success/failure)
                  </td>
                </tr>
                <tr>
                  <td className="py-2 pr-4">
                    <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                      gim_report_usage
                    </code>
                  </td>
                  <td className="py-2 text-text-secondary">
                    Manual analytics events
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="mb-2 text-[14px] font-semibold text-text-primary">
            Example Tool Call
          </p>
          <CodeBlock
            code={`gim_search_issues({
  error_message: "ModuleNotFoundError: No module named 'numpy'",
  language: "python",
  framework: "fastapi"
})`}
            language="typescript"
          />
        </div>

        {/* Knowledge Base */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            Knowledge Base
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            Issues and their fixes are stored with semantic embeddings, enabling
            fuzzy matching even when error messages differ slightly between
            environments. Each entry includes the error context, the fix, and
            community verification data.
          </p>

          <h4 className="mb-2 text-[14px] font-semibold text-text-primary">
            Dual Storage Architecture
          </h4>
          <div className="mb-4 overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-border-light">
                  <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                    Storage
                  </th>
                  <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                    Type
                  </th>
                  <th className="py-2 text-left font-semibold text-text-primary">
                    Purpose
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border-light/50">
                  <td className="py-2 pr-4 font-medium text-text-primary">
                    Supabase
                  </td>
                  <td className="py-2 pr-4 text-text-secondary">
                    Relational (PostgreSQL)
                  </td>
                  <td className="py-2 text-text-secondary">
                    Issue metadata, fix bundles, user data
                  </td>
                </tr>
                <tr>
                  <td className="py-2 pr-4 font-medium text-text-primary">
                    Qdrant
                  </td>
                  <td className="py-2 pr-4 text-text-secondary">
                    Vector Database
                  </td>
                  <td className="py-2 text-text-secondary">
                    Semantic embeddings for search
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            This dual-storage approach separates concerns: relational storage
            handles CRUD operations, relationships, and structured queries,
            while vector storage enables fast semantic similarity matching.
          </p>
        </div>

        {/* Embedding Engine */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            Embedding Engine
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            GIM uses Google&apos;s{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gemini-embedding-001
            </code>{" "}
            model to generate 3072-dimensional semantic embeddings. Rather than
            embedding just the error message, GIM combines multiple fields into
            a single embedding:
          </p>
          <ul className="mb-4 list-inside list-disc space-y-1 text-[14px] text-text-secondary">
            <li>Error message</li>
            <li>Root cause analysis</li>
            <li>Fix summary</li>
          </ul>
          <DocsCallout variant="info" title="Why Combined Embeddings">
            Combining error message, root cause, and fix summary into a single
            embedding captures semantic relationships between what went wrong
            and how to fix it. This improves match quality compared to
            embedding the error message alone.
          </DocsCallout>
        </div>

        {/* Matching Engine */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            Matching Engine
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            When you encounter an error, GIM uses embedding-based semantic
            search to find similar issues in the knowledge base. Results are
            ranked by relevance and community confidence score, so the most
            reliable fixes surface first.
          </p>

          <h4 className="mb-2 text-[14px] font-semibold text-text-primary">
            Technical Details
          </h4>
          <ul className="mb-4 list-inside list-disc space-y-1 text-[14px] text-text-secondary">
            <li>
              <strong>Algorithm:</strong> Cosine similarity
            </li>
            <li>
              <strong>Search threshold:</strong> 0.2 (permissive for broad
              matching)
            </li>
            <li>
              <strong>Quantization:</strong> INT8 scalar for performance
            </li>
            <li>
              <strong>Ranking:</strong> Similarity score × confidence score
            </li>
          </ul>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            The low threshold (0.2) is intentional—it&apos;s better to return
            potentially relevant results for the AI to evaluate than to miss
            good matches. The confidence score helps surface verified fixes over
            unverified ones.
          </p>
        </div>

        {/* Deduplication Engine */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            Deduplication Engine
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            Before a new issue is added to the knowledge base, GIM checks for
            existing duplicates using semantic similarity. This keeps the
            knowledge base clean and ensures fixes are consolidated rather than
            fragmented.
          </p>

          <h4 className="mb-2 text-[14px] font-semibold text-text-primary">
            Deduplication Logic
          </h4>
          <ul className="mb-4 list-inside list-disc space-y-1 text-[14px] text-text-secondary">
            <li>
              <strong>Threshold:</strong> 0.85 similarity
            </li>
            <li>
              If similarity ≥ 0.85: Create child issue linked to existing master
            </li>
            <li>If similarity &lt; 0.85: Create new master issue</li>
          </ul>
          <DocsCallout variant="tip">
            Child issues add environment diversity (different OS, package
            versions, frameworks) without fragmenting the knowledge base. The
            master issue remains the single source of truth.
          </DocsCallout>
        </div>
      </div>

      {/* Security Model */}
      <h2 className="mb-4 mt-10 text-lg font-semibold text-text-primary">
        Security Model
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
        GIM automatically sanitizes all content before storage to protect
        sensitive information. The sanitization pipeline has two layers:
      </p>

      <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
        Two-Layer Sanitization Pipeline
      </h3>
      <div className="mb-4 overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-border-light">
              <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                Layer
              </th>
              <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                Method
              </th>
              <th className="py-2 text-left font-semibold text-text-primary">
                What It Catches
              </th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-border-light/50">
              <td className="py-2 pr-4 font-medium text-text-primary">
                Layer 1
              </td>
              <td className="py-2 pr-4 text-text-secondary">
                Deterministic (Regex)
              </td>
              <td className="py-2 text-text-secondary">
                API keys, URLs, file paths, emails, IPs
              </td>
            </tr>
            <tr>
              <td className="py-2 pr-4 font-medium text-text-primary">
                Layer 2
              </td>
              <td className="py-2 pr-4 text-text-secondary">
                LLM-based (Gemini)
              </td>
              <td className="py-2 text-text-secondary">
                Context-aware secrets, domain-specific PII
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
        Layer 1 uses pattern matching for known secret formats (AWS keys, JWT
        tokens, etc.). Layer 2 uses an LLM to identify context-dependent
        sensitive data that regex can&apos;t catch, like custom variable names
        containing passwords or internal service endpoints.
      </p>

      <div className="mb-10">
        <DocsCallout variant="warning" title="What Gets Sanitized">
          API keys, passwords, file paths, email addresses, IP addresses,
          database connection strings, and domain-specific identifiers are
          automatically removed before storage. Your code snippets are safe to
          share.
        </DocsCallout>
      </div>

      {/* Rate Limiting */}
      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Rate Limiting
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
        GIM implements rate limiting to ensure fair usage and system stability.
        Limits are applied per-user and reset daily.
      </p>

      <div className="mb-4 overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-border-light">
              <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                Operation
              </th>
              <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                Rate Limited
              </th>
              <th className="py-2 text-left font-semibold text-text-primary">
                Default Limit
              </th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-border-light/50">
              <td className="py-2 pr-4">
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                  gim_search_issues
                </code>
              </td>
              <td className="py-2 pr-4 text-text-secondary">Yes</td>
              <td className="py-2 text-text-secondary">100/day</td>
            </tr>
            <tr className="border-b border-border-light/50">
              <td className="py-2 pr-4">
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                  gim_get_fix_bundle
                </code>
              </td>
              <td className="py-2 pr-4 text-text-secondary">Yes</td>
              <td className="py-2 text-text-secondary">100/day</td>
            </tr>
            <tr className="border-b border-border-light/50">
              <td className="py-2 pr-4">
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                  gim_submit_issue
                </code>
              </td>
              <td className="py-2 pr-4 text-text-secondary">No</td>
              <td className="py-2 text-text-secondary">Unlimited</td>
            </tr>
            <tr>
              <td className="py-2 pr-4">
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                  gim_confirm_fix
                </code>
              </td>
              <td className="py-2 pr-4 text-text-secondary">No</td>
              <td className="py-2 text-text-secondary">Unlimited</td>
            </tr>
          </tbody>
        </table>
      </div>

      <DocsCallout variant="info">
        Limits reset daily at midnight UTC. Submissions and confirmations are
        unlimited to encourage knowledge sharing and feedback.
      </DocsCallout>
    </div>
  );
}
