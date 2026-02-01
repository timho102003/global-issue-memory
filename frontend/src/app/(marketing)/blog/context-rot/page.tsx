import Link from "next/link";
import { ArrowLeft, Clock, Calendar, ExternalLink } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Context Rot: The Silent Killer of AI-Assisted Coding | GIM Blog",
  description:
    "As your AI assistant's context window fills up, its performance silently degrades. Research shows even simple tasks suffer. Here's what the community can do.",
};

/**
 * Context Rot — the first GIM blog post.
 */
export default function ContextRotPost() {
  return (
    <article className="px-5 py-12 sm:px-8 sm:py-16 md:py-20 lg:px-12">
      <div className="mx-auto max-w-[720px]">
        {/* Breadcrumb */}
        <Link
          href="/blog"
          className="group mb-10 inline-flex items-center gap-1.5 text-[13px] font-medium text-text-muted transition-colors hover:text-accent-warm"
        >
          <ArrowLeft className="h-3.5 w-3.5 transition-transform duration-200 group-hover:-translate-x-0.5" />
          Back to Blog
        </Link>

        {/* Article header */}
        <header className="mb-10 flex flex-col gap-5 sm:mb-14">
          <span className="self-start rounded-full bg-accent-warm/10 px-3 py-1 text-[11px] font-semibold tracking-wide text-accent-warm uppercase">
            Research
          </span>

          <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl md:text-4xl md:leading-[1.15]">
            Context Rot: The Silent Killer of AI&#8209;Assisted&nbsp;Coding
          </h1>

          <p className="text-base leading-relaxed text-text-secondary sm:text-lg">
            Your AI coding assistant gets worse the longer you use it in a
            session. Not because the model is bad — because its memory is
            overflowing. Here&rsquo;s the research, the real cost, and what we
            can do about it.
          </p>

          <div className="flex flex-wrap items-center gap-4 border-t border-border-light/60 pt-5 text-[13px] text-text-muted">
            <span className="flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" />
              Feb 1, 2026
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              12 min read
            </span>
            <span className="ml-auto text-[12px]">
              By the GIM Team
            </span>
          </div>
        </header>

        {/* ─── Article body ─── */}
        <div className="blog-prose">
          <p>
            Imagine you&rsquo;re three hours into a coding session with your AI
            assistant. The first hour was magic — clean code, sharp
            suggestions, fast iteration. By hour two, the answers started
            getting longer and less precise. Now, in hour three, the
            assistant is confidently generating code that doesn&rsquo;t quite
            work, referencing things you deleted an hour ago, and occasionally
            hallucinating function names that don&rsquo;t exist.
          </p>

          <p>
            You haven&rsquo;t done anything wrong. Your AI assistant is
            suffering from <strong>context rot</strong>.
          </p>

          <HeroIllustration />

          <h2>What Is Context Rot?</h2>

          <p>
            Context rot is the measurable degradation in LLM performance as the
            input context grows longer. It was first described in a{" "}
            <a
              href="https://research.trychroma.com/context-rot"
              target="_blank"
              rel="noopener noreferrer"
            >
              landmark study by Chroma Research
              <ExternalLink className="ml-0.5 inline h-3 w-3 align-baseline" />
            </a>{" "}
            that tested 18 frontier models on tasks ranging from simple word
            replication to multi-hop retrieval. The finding was stark: even on
            deliberately trivial tasks, model performance consistently
            declines as input length increases.
          </p>

          <p>
            This isn&rsquo;t a theoretical edge case. It&rsquo;s what happens
            every time you have a long conversation with an AI coding assistant.
            Every error message you paste, every file you share, every back-and-forth
            exchange — they all accumulate in the context window, and the
            model&rsquo;s ability to use that information degrades
            non-uniformly as it grows.
          </p>

          <blockquote>
            <p>
              &ldquo;What matters more is not whether relevant information
              exists in the context, but how that information is
              presented.&rdquo;
            </p>
          </blockquote>

          <p>
            The Chroma researchers identified four key drivers of context rot:
          </p>

          <ul>
            <li>
              <strong>Needle-question similarity:</strong> When your actual
              question is semantically distant from the relevant answer buried
              in context, performance drops steeply.
            </li>
            <li>
              <strong>Distractors:</strong> Topically related but incorrect
              information — like old error messages and abandoned debugging
              attempts — actively confuse the model.
            </li>
            <li>
              <strong>Haystack structure:</strong> Counterintuitively, models
              perform <em>worse</em> with logically coherent context and{" "}
              <em>better</em> with shuffled, disconnected content — suggesting
              attention mechanisms get lost in structured flow.
            </li>
            <li>
              <strong>Semantic blending:</strong> When the target information
              &ldquo;blends in&rdquo; with surrounding material, retrieval
              accuracy collapses.
            </li>
          </ul>

          <DecayDiagram />

          <h2>The Numbers Are Worse Than You Think</h2>

          <p>
            The Stanford &ldquo;lost-in-the-middle&rdquo; study found that with
            just 20 retrieved documents (roughly 4,000 tokens), LLM accuracy
            drops from 70–75% to 55–60%. Information buried in the middle of
            the context window is essentially invisible.
          </p>

          <p>
            An{" "}
            <a
              href="https://spectrum.ieee.org/ai-coding-degrades"
              target="_blank"
              rel="noopener noreferrer"
            >
              IEEE Spectrum report from January 2026
              <ExternalLink className="ml-0.5 inline h-3 w-3 align-baseline" />
            </a>{" "}
            highlighted that after two years of steady improvements, AI coding
            assistants reached a quality plateau in 2025 — and then started to
            decline. Tasks that once took five hours with AI assistance began
            taking seven or eight. Some developers started reverting to older
            model versions.
          </p>

          <StatCard
            stat="66%"
            label="of developers spend more time fixing 'almost-right' AI code than they saved in the initial generation."
          />

          <p>
            A{" "}
            <a
              href="https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/"
              target="_blank"
              rel="noopener noreferrer"
            >
              METR randomized controlled trial
              <ExternalLink className="ml-0.5 inline h-3 w-3 align-baseline" />
            </a>{" "}
            found something even more unsettling: experienced developers using
            AI tools were <strong>19% slower</strong> than without them — yet
            they <em>believed</em> they were 20% faster. The productivity gain
            is, in many cases, an illusion created by the satisfying feeling of
            rapid code generation, while the downstream debugging cost remains
            hidden.
          </p>

          <h2>Why Bigger Context Windows Don&rsquo;t Help</h2>

          <p>
            The intuitive fix sounds simple: just make the context window
            bigger. Models now support 1M, 2M, even 10M tokens. Problem solved?
          </p>

          <p>
            Not even close. Chroma&rsquo;s research demonstrates that
            performance degrades <em>more severely</em> on complex tasks as
            context grows. A 2M-token context window doesn&rsquo;t give you 2M
            tokens of useful capacity — it gives you the same limited retrieval
            ability buried under exponentially more noise.
          </p>

          <blockquote>
            <p>
              &ldquo;Not only do LLMs perform worse as more tokens are added,
              they exhibit more severe degradation on more complex
              tasks.&rdquo;
            </p>
          </blockquote>

          <p>
            Think of it like a desk. A bigger desk doesn&rsquo;t make you more
            organized — it just gives you more surface area to pile things on.
            The papers you need are still buried under the ones you
            don&rsquo;t.
          </p>

          <ContextWindowDiagram />

          <h2>The Compounding Problem for AI Coding</h2>

          <p>
            Context rot is especially devastating for AI-assisted coding because
            debugging is inherently iterative. Here&rsquo;s the typical
            failure loop:
          </p>

          <ol>
            <li>You encounter an error and paste it into your AI assistant.</li>
            <li>The assistant suggests a fix. It doesn&rsquo;t work.</li>
            <li>
              You paste the new error. The assistant now has two error messages
              and two failed attempts in context — but treats them as fresh
              information.
            </li>
            <li>
              Three iterations later, the context window is filled with stale
              debugging artifacts. The model starts referencing earlier
              (wrong) suggestions, mixing old and new error contexts, and
              generating increasingly confused responses.
            </li>
            <li>
              You start a new chat. You&rsquo;ve burned 30 minutes and
              thousands of tokens on a problem someone else already solved
              yesterday.
            </li>
          </ol>

          <p>
            This isn&rsquo;t a one-off inconvenience. It&rsquo;s a{" "}
            <strong>systemic tax</strong> on every developer using AI tools.
            Research shows that code churn — code rewritten within two weeks —
            has nearly <strong>doubled</strong> since AI assistants became
            prevalent. Each session patch that &ldquo;works for now&rdquo; is
            another piece of technical debt that will trigger the same debugging
            loop for the next person.
          </p>

          <h2>The Silent Failure Mode</h2>

          <p>
            What makes context rot especially dangerous is that it fails{" "}
            <em>silently</em>. Unlike a crash or a type error, context rot
            produces plausible-looking output. The code compiles. The function
            names are real (mostly). The logic seems reasonable. But it&rsquo;s
            subtly wrong in ways that don&rsquo;t surface until production —
            or until another developer inherits your code.
          </p>

          <p>
            GPT-family models tend toward confident hallucination. Claude-family
            models trend toward cautious abstention. Gemini models sometimes
            invent entirely novel words. But all of them share one thing in
            common: <strong>they never tell you they&rsquo;re degraded.</strong>
          </p>

          <FailureModesDiagram />

          <h2>Context Engineering Is Necessary — But Not Sufficient</h2>

          <p>
            The current best practice is called <strong>context engineering</strong>
            — carefully curating what goes into the model&rsquo;s context
            window to maximize signal and minimize noise. This includes:
          </p>

          <ul>
            <li>Structured retrieval of only relevant code snippets</li>
            <li>Summarization of long conversation histories</li>
            <li>Strategic placement of critical information at the beginning and end of context</li>
            <li>Periodic recap injection to re-anchor important constraints</li>
          </ul>

          <p>
            These techniques help. But they share a fundamental limitation:
            they&rsquo;re <strong>per-session solutions to a cross-session
            problem</strong>. Every developer is independently engineering
            their context to solve problems that other developers have already
            solved. The knowledge dies when the chat session ends.
          </p>

          <hr />

          <h2>What If We Could Skip the Rot Entirely?</h2>

          <p>
            Context rot is worst when the AI has to <em>figure things out
            from scratch</em> — loading your entire debugging history into
            context just to rediscover an answer that already exists. What if,
            instead of burning tokens on trial-and-error, your AI assistant
            could instantly retrieve a verified fix?
          </p>

          <p>
            That&rsquo;s the core idea behind{" "}
            <strong>
              <Link href="/" className="text-accent-warm hover:text-accent-gold">
                GIM (Global Issue Memory)
              </Link>
            </strong>
            : a community-powered knowledge layer that plugs directly into your
            AI coding workflow through the{" "}
            <a
              href="https://modelcontextprotocol.io"
              target="_blank"
              rel="noopener noreferrer"
            >
              Model Context Protocol (MCP)
            </a>
            .
          </p>

          <p>
            Instead of each developer independently debugging the same
            issues — filling their context windows with failed attempts — GIM
            gives your AI assistant direct access to a shared memory of
            verified solutions. When an error is encountered:
          </p>

          <ol>
            <li>
              <strong>Search first:</strong> The AI queries GIM for matching
              issues before attempting to solve it from scratch.
            </li>
            <li>
              <strong>Minimal context footprint:</strong> A verified fix
              typically uses ~500 tokens versus the 30,000+ tokens of a full
              debugging conversation. That&rsquo;s a 98% reduction in context
              usage.
            </li>
            <li>
              <strong>Community-verified:</strong> Solutions are submitted by
              developers, tagged with environment metadata (OS, language,
              framework version), and confirmed to work before they&rsquo;re
              surfaced.
            </li>
            <li>
              <strong>Knowledge persists:</strong> Unlike a chat session that
              disappears when you close the tab, GIM&rsquo;s memory is
              permanent and shared.
            </li>
          </ol>

          <GimFlowDiagram />

          <blockquote>
            <p>
              The best debugging conversation is the one that never happens.
            </p>
          </blockquote>

          <h2>From Individual Sessions to Collective Knowledge</h2>

          <p>
            The AI coding ecosystem today is deeply fragmented. Millions of
            developers encounter the same errors, burn the same tokens, and
            arrive at the same solutions — all in isolated chat sessions that
            evaporate immediately after. It&rsquo;s as if every doctor had to
            independently rediscover every treatment from scratch, with no
            medical literature, no case studies, no shared knowledge base.
          </p>

          <p>
            Context rot is a technical constraint we can&rsquo;t eliminate from
            LLMs — at least not yet. But we <em>can</em> dramatically reduce
            how often we trigger it. Every time GIM intercepts a known issue
            before the debugging loop begins, that&rsquo;s one less session
            where context rot has a chance to take hold.
          </p>

          <StatCard
            stat="~500 tokens"
            label="Average context footprint of a GIM fix — vs. 30,000+ tokens for a typical debugging conversation."
          />

          <p>
            The transition from individual context engineering to collective
            issue memory isn&rsquo;t just an optimization. It&rsquo;s a
            fundamental shift in how AI-assisted development works: from every
            developer fighting context rot alone, to a community that{" "}
            <strong>fixes once and helps everyone</strong>.
          </p>

          <hr />

          <h2>What You Can Do</h2>

          <p>
            Context rot isn&rsquo;t going away. But its impact on your work
            doesn&rsquo;t have to grow with it. Here are three things you can do
            today:
          </p>

          <ol>
            <li>
              <strong>Be aware of session length.</strong> If your AI
              assistant&rsquo;s answers are getting worse, it&rsquo;s probably
              not the model — it&rsquo;s the accumulated context. Start a fresh
              session rather than pushing through.
            </li>
            <li>
              <strong>Practice context hygiene.</strong> Only paste what&rsquo;s
              relevant. Summarize long error logs. Remove resolved threads
              before adding new ones.
            </li>
            <li>
              <strong>Join the shared memory.</strong>{" "}
              <Link href="/docs/getting-started" className="text-accent-warm hover:text-accent-gold">
                Set up GIM
              </Link>{" "}
              in your AI workflow. When you solve an error that others might
              hit, submit it. When you encounter one, search first. Build the
              knowledge base that makes context rot less painful for everyone.
            </li>
          </ol>

          <div className="not-prose my-10 rounded-2xl border border-accent-warm/20 bg-gradient-to-br from-bg-highlight to-white p-6 sm:p-8">
            <p className="mb-4 text-base font-semibold text-text-primary sm:text-lg">
              Build together. Fix once. Help everyone.
            </p>
            <p className="mb-5 text-[14px] leading-relaxed text-text-secondary">
              GIM is open-source and free for non-commercial use. Join the
              community of developers building a shared memory for AI coding.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/docs/getting-started"
                className="inline-flex items-center gap-1.5 rounded-full bg-[#2D2A26] px-5 py-2.5 text-[13px] font-semibold text-white no-underline transition-colors duration-200 hover:bg-[#3D3A36]"
              >
                Get Started
              </Link>
              <Link
                href="/"
                className="inline-flex items-center gap-1.5 rounded-full border border-border-medium bg-white px-5 py-2.5 text-[13px] font-semibold text-text-primary no-underline transition-colors duration-200 hover:bg-bg-muted"
              >
                Learn More About GIM
              </Link>
            </div>
          </div>

          <hr />

          <h3>References &amp; Further Reading</h3>

          <ul>
            <li>
              <a
                href="https://research.trychroma.com/context-rot"
                target="_blank"
                rel="noopener noreferrer"
              >
                Context Rot — Chroma Research
              </a>
            </li>
            <li>
              <a
                href="https://spectrum.ieee.org/ai-coding-degrades"
                target="_blank"
                rel="noopener noreferrer"
              >
                Newer AI Coding Assistants Are Failing in Insidious Ways — IEEE Spectrum
              </a>
            </li>
            <li>
              <a
                href="https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Measuring the Impact of Early-2025 AI on Developer Productivity — METR
              </a>
            </li>
            <li>
              <a
                href="https://redis.io/blog/context-rot/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Context Rot Explained &amp; How to Prevent It — Redis
              </a>
            </li>
            <li>
              <a
                href="https://www.augmentcode.com/guides/why-ai-coding-tools-make-experienced-developers-19-slower-and-how-to-fix-it"
                target="_blank"
                rel="noopener noreferrer"
              >
                Why AI Coding Tools Make Experienced Developers 19% Slower — Augment Code
              </a>
            </li>
          </ul>
        </div>
      </div>
    </article>
  );
}

/* ─── Inline SVG illustrations ─── */

/** Hero illustration: context window filling up and degrading. */
function HeroIllustration() {
  return (
    <figure className="my-8 sm:my-10">
      <div className="overflow-hidden rounded-xl border border-border-light/80 bg-gradient-to-br from-bg-muted to-bg-tertiary p-6 sm:p-8">
        <svg
          viewBox="0 0 640 200"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="h-auto w-full"
          aria-label="Illustration showing context window filling up over time, with quality degrading"
        >
          {/* Timeline axis */}
          <line x1="60" y1="170" x2="600" y2="170" stroke="#D4D2CD" strokeWidth="1" />
          <text x="60" y="192" fill="#9C9791" fontSize="10" fontFamily="sans-serif">Session start</text>
          <text x="510" y="192" fill="#9C9791" fontSize="10" fontFamily="sans-serif">3 hours later</text>

          {/* Context window blocks — growing */}
          <rect x="80" y="130" width="40" height="35" rx="4" fill="#D4A853" fillOpacity="0.2" />
          <rect x="80" y="145" width="40" height="20" rx="3" fill="#D4A853" fillOpacity="0.6" />
          <text x="100" y="125" textAnchor="middle" fill="#6B6660" fontSize="9" fontFamily="sans-serif">Clean</text>

          <rect x="180" y="100" width="40" height="65" rx="4" fill="#D4A853" fillOpacity="0.2" />
          <rect x="180" y="115" width="40" height="50" rx="3" fill="#D4A853" fillOpacity="0.5" />
          <rect x="180" y="140" width="40" height="25" rx="2" fill="#F59E0B" fillOpacity="0.3" />

          <rect x="280" y="70" width="40" height="95" rx="4" fill="#D4A853" fillOpacity="0.2" />
          <rect x="280" y="85" width="40" height="80" rx="3" fill="#D4A853" fillOpacity="0.35" />
          <rect x="280" y="105" width="40" height="60" rx="2" fill="#F59E0B" fillOpacity="0.3" />
          <rect x="280" y="130" width="40" height="35" rx="2" fill="#EF4444" fillOpacity="0.2" />

          <rect x="380" y="45" width="40" height="120" rx="4" fill="#D4A853" fillOpacity="0.2" />
          <rect x="380" y="60" width="40" height="105" rx="3" fill="#D4A853" fillOpacity="0.2" />
          <rect x="380" y="80" width="40" height="85" rx="2" fill="#F59E0B" fillOpacity="0.3" />
          <rect x="380" y="110" width="40" height="55" rx="2" fill="#EF4444" fillOpacity="0.3" />

          <rect x="480" y="25" width="40" height="140" rx="4" fill="#D4A853" fillOpacity="0.15" />
          <rect x="480" y="40" width="40" height="125" rx="3" fill="#D4A853" fillOpacity="0.15" />
          <rect x="480" y="60" width="40" height="105" rx="2" fill="#F59E0B" fillOpacity="0.3" />
          <rect x="480" y="90" width="40" height="75" rx="2" fill="#EF4444" fillOpacity="0.35" />

          {/* Quality line — declining */}
          <path
            d="M100 68 C150 70, 195 82, 300 105 S430 140, 500 155"
            stroke="#EF4444"
            strokeWidth="2"
            strokeDasharray="6 4"
            fill="none"
            strokeOpacity="0.7"
          />
          <circle cx="100" cy="68" r="3" fill="#22C55E" />
          <circle cx="500" cy="155" r="3" fill="#EF4444" />
          <text x="45" y="72" fill="#22C55E" fontSize="9" fontFamily="sans-serif" fontWeight="600">High</text>
          <text x="515" y="159" fill="#EF4444" fontSize="9" fontFamily="sans-serif" fontWeight="600">Low</text>

          {/* Legend */}
          <rect x="60" y="12" width="10" height="10" rx="2" fill="#D4A853" fillOpacity="0.5" />
          <text x="76" y="21" fill="#6B6660" fontSize="9" fontFamily="sans-serif">Useful context</text>
          <rect x="170" y="12" width="10" height="10" rx="2" fill="#F59E0B" fillOpacity="0.4" />
          <text x="186" y="21" fill="#6B6660" fontSize="9" fontFamily="sans-serif">Stale/redundant</text>
          <rect x="290" y="12" width="10" height="10" rx="2" fill="#EF4444" fillOpacity="0.35" />
          <text x="306" y="21" fill="#6B6660" fontSize="9" fontFamily="sans-serif">Distractors</text>
          <line x1="400" y1="17" x2="430" y2="17" stroke="#EF4444" strokeWidth="2" strokeDasharray="4 3" />
          <text x="436" y="21" fill="#6B6660" fontSize="9" fontFamily="sans-serif">Output quality</text>
        </svg>
      </div>
      <figcaption>
        As a coding session progresses, useful context is diluted by stale
        debugging artifacts and distractors — while output quality steadily
        declines.
      </figcaption>
    </figure>
  );
}

/** Decay diagram: the four drivers of context rot. */
function DecayDiagram() {
  return (
    <figure className="my-8 sm:my-10">
      <div className="overflow-hidden rounded-xl border border-border-light/80 bg-gradient-to-br from-bg-muted to-bg-tertiary p-6 sm:p-8">
        <svg
          viewBox="0 0 640 240"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="h-auto w-full"
          aria-label="Four drivers of context rot"
        >
          {/* Center node */}
          <circle cx="320" cy="120" r="48" fill="#2D2A26" />
          <text x="320" y="114" textAnchor="middle" fill="#D4A853" fontSize="11" fontWeight="700" fontFamily="sans-serif">Context</text>
          <text x="320" y="130" textAnchor="middle" fill="#D4A853" fontSize="11" fontWeight="700" fontFamily="sans-serif">Rot</text>

          {/* Node 1: Needle-Question Similarity */}
          <line x1="272" y1="105" x2="155" y2="60" stroke="#D4D2CD" strokeWidth="1" />
          <circle cx="130" cy="50" r="36" fill="white" stroke="#D4A853" strokeWidth="1.5" />
          <text x="130" y="45" textAnchor="middle" fill="#2D2A26" fontSize="8.5" fontWeight="600" fontFamily="sans-serif">Needle-Query</text>
          <text x="130" y="57" textAnchor="middle" fill="#6B6660" fontSize="8" fontFamily="sans-serif">Similarity</text>

          {/* Node 2: Distractors */}
          <line x1="368" y1="105" x2="485" y2="60" stroke="#D4D2CD" strokeWidth="1" />
          <circle cx="510" cy="50" r="36" fill="white" stroke="#EF4444" strokeWidth="1.5" strokeOpacity="0.6" />
          <text x="510" y="47" textAnchor="middle" fill="#2D2A26" fontSize="8.5" fontWeight="600" fontFamily="sans-serif">Distractors</text>
          <text x="510" y="59" textAnchor="middle" fill="#6B6660" fontSize="8" fontFamily="sans-serif">(stale errors)</text>

          {/* Node 3: Haystack Structure */}
          <line x1="275" y1="140" x2="155" y2="190" stroke="#D4D2CD" strokeWidth="1" />
          <circle cx="130" cy="195" r="36" fill="white" stroke="#F59E0B" strokeWidth="1.5" strokeOpacity="0.6" />
          <text x="130" y="190" textAnchor="middle" fill="#2D2A26" fontSize="8.5" fontWeight="600" fontFamily="sans-serif">Haystack</text>
          <text x="130" y="202" textAnchor="middle" fill="#6B6660" fontSize="8" fontFamily="sans-serif">Structure</text>

          {/* Node 4: Semantic Blending */}
          <line x1="365" y1="140" x2="485" y2="190" stroke="#D4D2CD" strokeWidth="1" />
          <circle cx="510" cy="195" r="36" fill="white" stroke="#8B5CF6" strokeWidth="1.5" strokeOpacity="0.6" />
          <text x="510" y="190" textAnchor="middle" fill="#2D2A26" fontSize="8.5" fontWeight="600" fontFamily="sans-serif">Semantic</text>
          <text x="510" y="202" textAnchor="middle" fill="#6B6660" fontSize="8" fontFamily="sans-serif">Blending</text>
        </svg>
      </div>
      <figcaption>
        The four drivers of context rot identified by Chroma Research — each
        contributes to non-uniform performance degradation.
      </figcaption>
    </figure>
  );
}

/** Context window size vs. effective capacity. */
function ContextWindowDiagram() {
  return (
    <figure className="my-8 sm:my-10">
      <div className="overflow-hidden rounded-xl border border-border-light/80 bg-gradient-to-br from-bg-muted to-bg-tertiary p-6 sm:p-8">
        <svg
          viewBox="0 0 640 180"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="h-auto w-full"
          aria-label="Comparison showing bigger context windows don't proportionally increase effective capacity"
        >
          {/* Bar group: 8K context */}
          <rect x="80" y="50" width="100" height="100" rx="8" fill="#D4A853" fillOpacity="0.15" stroke="#D4A853" strokeWidth="1" strokeOpacity="0.3" />
          <rect x="80" y="95" width="100" height="55" rx="6" fill="#D4A853" fillOpacity="0.5" />
          <text x="130" y="40" textAnchor="middle" fill="#2D2A26" fontSize="11" fontWeight="600" fontFamily="sans-serif">8K tokens</text>
          <text x="130" y="125" textAnchor="middle" fill="#2D2A26" fontSize="9" fontFamily="sans-serif">~55% usable</text>

          {/* Bar group: 128K context */}
          <rect x="260" y="20" width="120" height="130" rx="8" fill="#D4A853" fillOpacity="0.15" stroke="#D4A853" strokeWidth="1" strokeOpacity="0.3" />
          <rect x="260" y="100" width="120" height="50" rx="6" fill="#D4A853" fillOpacity="0.5" />
          <text x="320" y="12" textAnchor="middle" fill="#2D2A26" fontSize="11" fontWeight="600" fontFamily="sans-serif">128K tokens</text>
          <text x="320" y="128" textAnchor="middle" fill="#2D2A26" fontSize="9" fontFamily="sans-serif">~35% usable</text>

          {/* Bar group: 1M context */}
          <rect x="460" y="10" width="120" height="140" rx="8" fill="#D4A853" fillOpacity="0.15" stroke="#D4A853" strokeWidth="1" strokeOpacity="0.3" />
          <rect x="460" y="105" width="120" height="45" rx="6" fill="#D4A853" fillOpacity="0.5" />
          <text x="520" y="7" textAnchor="middle" fill="#2D2A26" fontSize="11" fontWeight="600" fontFamily="sans-serif">1M tokens</text>
          <text x="520" y="131" textAnchor="middle" fill="#2D2A26" fontSize="9" fontFamily="sans-serif">~20% usable</text>

          {/* Labels */}
          <text x="130" y="172" textAnchor="middle" fill="#9C9791" fontSize="9" fontFamily="sans-serif">Good enough</text>
          <text x="320" y="172" textAnchor="middle" fill="#9C9791" fontSize="9" fontFamily="sans-serif">Diminishing returns</text>
          <text x="520" y="172" textAnchor="middle" fill="#9C9791" fontSize="9" fontFamily="sans-serif">Mostly noise</text>
        </svg>
      </div>
      <figcaption>
        Bigger context windows create a false sense of capacity. Effective
        retrieval accuracy shrinks as the window grows.
      </figcaption>
    </figure>
  );
}

/** Model failure modes comparison. */
function FailureModesDiagram() {
  return (
    <figure className="my-8 sm:my-10">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {[
          {
            model: "GPT family",
            behavior: "Confident hallucination",
            description: "Generates plausible but incorrect code with high confidence scores.",
            color: "#EF4444",
            bgColor: "rgba(239,68,68,0.06)",
          },
          {
            model: "Claude family",
            behavior: "Cautious abstention",
            description: "Tends to refuse or hedge when uncertain — safer but still degraded.",
            color: "#D4A853",
            bgColor: "rgba(212,168,83,0.06)",
          },
          {
            model: "Gemini family",
            behavior: "Novel invention",
            description: "Sometimes generates entirely new tokens not present in the input.",
            color: "#8B5CF6",
            bgColor: "rgba(139,92,246,0.06)",
          },
        ].map((item) => (
          <div
            key={item.model}
            className="rounded-xl border border-border-light/80 p-5"
            style={{ backgroundColor: item.bgColor }}
          >
            <div
              className="mb-2 text-[11px] font-semibold uppercase tracking-wide"
              style={{ color: item.color }}
            >
              {item.model}
            </div>
            <div className="mb-1.5 text-[14px] font-semibold text-text-primary">
              {item.behavior}
            </div>
            <p className="text-[13px] leading-relaxed text-text-secondary">
              {item.description}
            </p>
          </div>
        ))}
      </div>
      <figcaption>
        Different model families degrade differently — but none warn you
        when it&rsquo;s happening.
      </figcaption>
    </figure>
  );
}

/** GIM flow: search → retrieve → skip the rot. */
function GimFlowDiagram() {
  return (
    <figure className="my-8 sm:my-10">
      <div className="overflow-hidden rounded-xl border border-accent-warm/20 bg-gradient-to-br from-bg-highlight to-white p-6 sm:p-8">
        <svg
          viewBox="0 0 640 160"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="h-auto w-full"
          aria-label="GIM flow: error occurs, search GIM, get verified fix, skip debugging loop"
        >
          {/* Step 1 */}
          <rect x="20" y="40" width="120" height="80" rx="12" fill="white" stroke="#D4D2CD" strokeWidth="1" />
          <text x="80" y="72" textAnchor="middle" fill="#EF4444" fontSize="18" fontFamily="sans-serif">!</text>
          <text x="80" y="92" textAnchor="middle" fill="#2D2A26" fontSize="10" fontWeight="600" fontFamily="sans-serif">Error occurs</text>
          <text x="80" y="106" textAnchor="middle" fill="#9C9791" fontSize="8" fontFamily="sans-serif">e.g. CORS, import</text>

          {/* Arrow 1 */}
          <path d="M145 80 L175 80" stroke="#D4A853" strokeWidth="1.5" />
          <path d="M172 76 L180 80 L172 84" fill="#D4A853" />

          {/* Step 2 */}
          <rect x="185" y="40" width="120" height="80" rx="12" fill="white" stroke="#D4A853" strokeWidth="1.5" />
          <text x="245" y="68" textAnchor="middle" fill="#D4A853" fontSize="16" fontFamily="monospace" fontWeight="700">GIM</text>
          <text x="245" y="86" textAnchor="middle" fill="#2D2A26" fontSize="10" fontWeight="600" fontFamily="sans-serif">Search issues</text>
          <text x="245" y="100" textAnchor="middle" fill="#9C9791" fontSize="8" fontFamily="sans-serif">~500 tokens</text>

          {/* Arrow 2 */}
          <path d="M310 80 L340 80" stroke="#D4A853" strokeWidth="1.5" />
          <path d="M337 76 L345 80 L337 84" fill="#D4A853" />

          {/* Step 3 */}
          <rect x="350" y="40" width="120" height="80" rx="12" fill="white" stroke="#22C55E" strokeWidth="1.5" />
          <text x="410" y="70" textAnchor="middle" fill="#22C55E" fontSize="18" fontFamily="sans-serif">&#10003;</text>
          <text x="410" y="90" textAnchor="middle" fill="#2D2A26" fontSize="10" fontWeight="600" fontFamily="sans-serif">Verified fix</text>
          <text x="410" y="104" textAnchor="middle" fill="#9C9791" fontSize="8" fontFamily="sans-serif">Applied instantly</text>

          {/* Arrow 3 */}
          <path d="M475 80 L505 80" stroke="#22C55E" strokeWidth="1.5" />
          <path d="M502 76 L510 80 L502 84" fill="#22C55E" />

          {/* Step 4 */}
          <rect x="515" y="40" width="110" height="80" rx="12" fill="#22C55E" fillOpacity="0.08" stroke="#22C55E" strokeWidth="1" strokeOpacity="0.4" />
          <text x="570" y="74" textAnchor="middle" fill="#2D2A26" fontSize="10" fontWeight="600" fontFamily="sans-serif">Context stays</text>
          <text x="570" y="90" textAnchor="middle" fill="#22C55E" fontSize="10" fontWeight="700" fontFamily="sans-serif">clean</text>
          <text x="570" y="106" textAnchor="middle" fill="#9C9791" fontSize="8" fontFamily="sans-serif">No rot triggered</text>

          {/* Crossed-out alternative path */}
          <path
            d="M80 125 Q320 155 570 125"
            stroke="#EF4444"
            strokeWidth="1"
            strokeDasharray="4 3"
            strokeOpacity="0.35"
          />
          <text x="320" y="150" textAnchor="middle" fill="#EF4444" fillOpacity="0.5" fontSize="9" fontFamily="sans-serif">
            Without GIM: 30K tokens of debugging → context rot
          </text>
        </svg>
      </div>
      <figcaption>
        With GIM, the AI searches for a verified fix before entering a
        debugging loop — keeping the context window clean.
      </figcaption>
    </figure>
  );
}

/** Highlighted statistic card used inline in the article. */
function StatCard({ stat, label }: { stat: string; label: string }) {
  return (
    <div className="my-8 flex items-start gap-5 rounded-xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-sm)] sm:my-10 sm:items-center sm:p-6">
      <span className="shrink-0 text-2xl font-bold tracking-tight text-accent-warm sm:text-3xl">
        {stat}
      </span>
      <p className="text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        {label}
      </p>
    </div>
  );
}
