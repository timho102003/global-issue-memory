import type { Metadata } from "next";
import { IssueLifecycleDiagram } from "@/components/docs/diagrams";
import { DocsCallout } from "@/components/docs/docs-callout";
import { CodeBlock } from "@/components/ui/code-block";

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

      {/* Lifecycle Flow */}
      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Lifecycle Flow
      </h2>
      <div className="mb-10">
        <IssueLifecycleDiagram />
      </div>

      {/* Stages Explained */}
      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Stages Explained
      </h2>
      <div className="flex flex-col gap-8">
        {/* Stage 1 */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            1. Error Encountered
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            When your AI assistant encounters an error, it calls{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_search_issues
            </code>{" "}
            with the error context. GIM searches the knowledge base for matching
            fixes.
          </p>

          <h4 className="mb-2 text-[14px] font-semibold text-text-primary">
            Data Sent to GIM
          </h4>
          <ul className="mb-4 list-inside list-disc space-y-1 text-[14px] text-text-secondary">
            <li>
              <strong>error_message</strong> (required): The exact error text
            </li>
            <li>
              <strong>language</strong> (optional): Programming language (e.g.,
              python, typescript)
            </li>
            <li>
              <strong>framework</strong> (optional): Framework in use (e.g.,
              fastapi, nextjs)
            </li>
            <li>
              <strong>provider/model</strong> (optional): AI assistant
              identification
            </li>
          </ul>
          <DocsCallout variant="info" title="Privacy Protection">
            All data is automatically sanitized before processing. Secrets, API
            keys, file paths, and PII are removed—you never have to worry about
            accidentally leaking sensitive information.
          </DocsCallout>
        </div>

        {/* Stage 2 */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            2. Search &amp; Match
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            GIM uses semantic similarity to find matching issues. Results
            include a similarity score indicating how closely each issue matches
            your error.
          </p>

          <h4 className="mb-2 text-[14px] font-semibold text-text-primary">
            Similarity Score Interpretation
          </h4>
          <div className="mb-4 overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-border-light">
                  <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                    Score Range
                  </th>
                  <th className="py-2 text-left font-semibold text-text-primary">
                    Interpretation
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border-light/50">
                  <td className="py-2 pr-4 font-medium text-text-primary">
                    &gt; 0.7
                  </td>
                  <td className="py-2 text-text-secondary">
                    Strong match, likely the same issue
                  </td>
                </tr>
                <tr className="border-b border-border-light/50">
                  <td className="py-2 pr-4 font-medium text-text-primary">
                    0.5 – 0.7
                  </td>
                  <td className="py-2 text-text-secondary">
                    Moderate match, fix may need adaptation
                  </td>
                </tr>
                <tr>
                  <td className="py-2 pr-4 font-medium text-text-primary">
                    0.2 – 0.5
                  </td>
                  <td className="py-2 text-text-secondary">
                    Weak match, review carefully before applying
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <DocsCallout variant="tip">
            The 0.2 threshold is intentionally permissive. It&apos;s better to
            surface potentially relevant results for review than to miss good
            matches. Always verify the fix applies to your specific situation.
          </DocsCallout>
        </div>

        {/* Stage 3 */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            3. Fix Applied &amp; Verified
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            After applying a GIM fix, the assistant calls{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_confirm_fix
            </code>{" "}
            to report whether it worked. Successful confirmations increase the
            fix&apos;s confidence score.
          </p>

          <DocsCallout variant="warning" title="Always Confirm">
            Calling{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_confirm_fix
            </code>{" "}
            is <strong>mandatory</strong> after applying a GIM fix. This
            feedback loop is essential for improving fix quality across the
            entire community.
          </DocsCallout>

          <p className="mb-2 mt-4 text-[14px] font-semibold text-text-primary">
            Example Confirmation
          </p>
          <CodeBlock
            code={`gim_confirm_fix({
  issue_id: "550e8400-e29b-41d4-a716-446655440000",
  fix_worked: true,
  feedback: "Fix worked after restarting the dev server"
})`}
            language="typescript"
          />
        </div>

        {/* Stage 4 */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            4. New Issue Submitted
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            When a novel fix is discovered for a globally relevant issue (not
            project-specific), the assistant calls{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              gim_submit_issue
            </code>
            . The fix enters the knowledge base and becomes available to all GIM
            users.
          </p>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            See the{" "}
            <a
              href="#globally-useful"
              className="font-medium text-accent-warm underline-offset-2 hover:underline"
            >
              Globally Useful Criteria
            </a>{" "}
            section below for guidance on what to submit.
          </p>
        </div>

        {/* Stage 5 */}
        <div>
          <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
            5. Community Verification
          </h3>
          <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
            As more developers encounter and confirm a fix, its confidence score
            grows through Bayesian updates. High-confidence fixes are surfaced
            more prominently in search results, creating a self-improving
            knowledge base.
          </p>
          <p className="text-[14px] leading-relaxed text-text-secondary">
            See the{" "}
            <a
              href="#confidence-scoring"
              className="font-medium text-accent-warm underline-offset-2 hover:underline"
            >
              Confidence Scoring Algorithm
            </a>{" "}
            section below for technical details.
          </p>
        </div>
      </div>

      {/* Confidence Scoring Algorithm */}
      <h2
        id="confidence-scoring"
        className="mb-4 mt-10 text-lg font-semibold text-text-primary"
      >
        Confidence Scoring Algorithm
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
        GIM uses a Bayesian update formula to adjust confidence scores based on
        community feedback. Each confirmation (success or failure) moves the
        score toward its true reliability.
      </p>

      <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
        Bayesian Update Formula
      </h3>
      <div className="mb-6">
        <CodeBlock
          code={`When fix_worked = true:
  new_score = (score × count + 1.0) / (count + 1)

When fix_worked = false:
  new_score = (score × count + 0.0) / (count + 1)`}
          language="plaintext"
          showCopy={false}
        />
      </div>

      <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
        Score Interpretation
      </h3>
      <div className="mb-4 overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-border-light">
              <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                Score
              </th>
              <th className="py-2 text-left font-semibold text-text-primary">
                Meaning
              </th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-border-light/50">
              <td className="py-2 pr-4 font-medium text-text-primary">0.9+</td>
              <td className="py-2 text-text-secondary">
                Highly reliable, verified by multiple users
              </td>
            </tr>
            <tr className="border-b border-border-light/50">
              <td className="py-2 pr-4 font-medium text-text-primary">
                0.7 – 0.9
              </td>
              <td className="py-2 text-text-secondary">
                Good reliability, likely to work
              </td>
            </tr>
            <tr className="border-b border-border-light/50">
              <td className="py-2 pr-4 font-medium text-text-primary">
                0.5 – 0.7
              </td>
              <td className="py-2 text-text-secondary">
                Moderate reliability, may need adaptation
              </td>
            </tr>
            <tr>
              <td className="py-2 pr-4 font-medium text-text-primary">
                &lt; 0.5
              </td>
              <td className="py-2 text-text-secondary">
                Low reliability, use with caution
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <DocsCallout variant="info">
        New issues start with a confidence score of 0.5 (neutral). Each
        verification moves the score toward 1.0 (success) or 0.0 (failure),
        with early verifications having the most impact.
      </DocsCallout>

      {/* Deduplication Model */}
      <h2 className="mb-4 mt-10 text-lg font-semibold text-text-primary">
        Deduplication Model
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
        When a new issue is submitted, GIM checks for existing duplicates. If a
        highly similar issue exists, the new submission becomes a &quot;child
        issue&quot; linked to the original &quot;master issue.&quot;
      </p>

      <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
        Master vs Child Issues
      </h3>
      <div className="mb-4 overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-border-light">
              <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                Type
              </th>
              <th className="py-2 pr-4 text-left font-semibold text-text-primary">
                When Created
              </th>
              <th className="py-2 text-left font-semibold text-text-primary">
                Contains
              </th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-border-light/50">
              <td className="py-2 pr-4 font-medium text-text-primary">
                Master
              </td>
              <td className="py-2 pr-4 text-text-secondary">
                First occurrence (similarity &lt; 0.85)
              </td>
              <td className="py-2 text-text-secondary">
                Full fix bundle, canonical error description
              </td>
            </tr>
            <tr>
              <td className="py-2 pr-4 font-medium text-text-primary">Child</td>
              <td className="py-2 pr-4 text-text-secondary">
                Duplicate found (similarity ≥ 0.85)
              </td>
              <td className="py-2 text-text-secondary">
                Environment context, linked to master
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
        Benefits
      </h3>
      <ul className="mb-6 list-inside list-disc space-y-1 text-[14px] text-text-secondary">
        <li>
          <strong>No fragmentation:</strong> Single source of truth for each
          unique issue
        </li>
        <li>
          <strong>Environment diversity:</strong> Captures variations (different
          OS, package versions)
        </li>
        <li>
          <strong>Better verification:</strong> Child confirmations boost the
          master&apos;s confidence score
        </li>
      </ul>

      {/* Globally Useful Criteria */}
      <h2
        id="globally-useful"
        className="mb-4 mt-10 text-lg font-semibold text-text-primary"
      >
        What Makes an Issue &quot;Globally Useful&quot;
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
        Not every fix should be submitted to GIM. The key question is:{" "}
        <strong>
          Would a stranger on a completely different codebase hit this same
          error?
        </strong>
      </p>

      <DocsCallout variant="warning" title="The Key Question">
        Ask yourself: &quot;Would a stranger on a completely different codebase
        hit this same error?&quot; If no, don&apos;t submit.
      </DocsCallout>

      <h3 className="mb-2 mt-6 text-[15px] font-semibold text-text-primary">
        DO Submit (Globally Reproducible)
      </h3>
      <ul className="mb-6 list-inside list-disc space-y-1 text-[14px] text-text-secondary">
        <li>Library/package version conflicts or incompatibilities</li>
        <li>Framework configuration pitfalls (Next.js, FastAPI, Django)</li>
        <li>Build tool errors (webpack, vite, esbuild, cargo)</li>
        <li>Deployment &amp; CI/CD issues (Docker, Vercel, AWS)</li>
        <li>Environment or OS-specific problems (Node version, Python path)</li>
        <li>SDK/API breaking changes or undocumented behavior</li>
        <li>AI model quirks (tool calling, response parsing, token limits)</li>
        <li>Language-level gotchas (async/await traps, type edge cases)</li>
      </ul>

      <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
        DO NOT Submit (Project-Local)
      </h3>
      <ul className="mb-6 list-inside list-disc space-y-1 text-[14px] text-text-secondary">
        <li>Database schema mismatches specific to your project</li>
        <li>Variable naming bugs or wrong function arguments</li>
        <li>Business logic errors unique to your project</li>
        <li>Missing internal imports or modules</li>
        <li>Typos in project code</li>
        <li>Test fixture or mock data mismatches</li>
        <li>User-specific file paths or local configuration</li>
      </ul>

      {/* Data Sanitization */}
      <h2 className="mb-4 text-lg font-semibold text-text-primary">
        Data Sanitization
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary">
        Every submission passes through a two-layer sanitization pipeline before
        storage. This happens automatically—you don&apos;t need to manually
        scrub your error messages.
      </p>

      <h3 className="mb-2 text-[15px] font-semibold text-text-primary">
        Sanitization Layers
      </h3>
      <ul className="mb-4 list-inside list-disc space-y-1 text-[14px] text-text-secondary">
        <li>
          <strong>Layer 1 (Regex):</strong> Pattern-based detection of API keys,
          URLs, file paths, emails, IPs
        </li>
        <li>
          <strong>Layer 2 (LLM):</strong> Context-aware analysis for
          domain-specific secrets and PII
        </li>
      </ul>

      <DocsCallout variant="info">
        Your submissions are automatically sanitized before storage. Secrets,
        API keys, file paths, and personally identifiable information are
        removed. See the{" "}
        <a
          href="/docs/how-it-works/system-design#security-model"
          className="font-medium text-accent-warm underline-offset-2 hover:underline"
        >
          System Design: Security Model
        </a>{" "}
        for technical details.
      </DocsCallout>
    </div>
  );
}
