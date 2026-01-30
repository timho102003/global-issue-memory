"use client";

import { useState, type ReactNode } from "react";
import {
  Check,
  Copy,
  ChevronDown,
  ChevronRight,
  FileCode,
  ListChecks,
  Play,
  Settings,
  Terminal,
  Wrench,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { CodeBlock } from "@/components/ui/code-block";
import type { FixBundle, EnvAction, VerificationStep, CodeChange } from "@/types";

interface FixBundleCardProps {
  fixBundle: FixBundle;
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

/**
 * Reusable section heading with icon + title.
 */
function SectionHeading({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2">
      {icon}
      <h4 className="text-sm font-semibold text-text-primary">{title}</h4>
    </div>
  );
}

/**
 * Renders step text with inline backtick code highlighted.
 * Splits on `...` patterns and wraps matched segments in <code>.
 */
function StepContent({ text }: { text: string }) {
  const parts = text.split(/(`[^`]+`)/g);
  return (
    <span>
      {parts.map((part, i) =>
        part.startsWith("`") && part.endsWith("`") ? (
          <code
            key={i}
            className="font-mono rounded bg-bg-tertiary px-1.5 py-0.5 text-xs text-text-primary"
          >
            {part.slice(1, -1)}
          </code>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
}

const CHANGE_TYPE_VARIANT: Record<CodeChange["change_type"], "success" | "warning" | "error"> = {
  add: "success",
  modify: "warning",
  delete: "error",
};

const CHANGE_TYPE_LABEL: Record<CodeChange["change_type"], string> = {
  add: "Added",
  modify: "Modified",
  delete: "Deleted",
};

/**
 * Collapsible per-file code change block with before/after diffs.
 */
function CodeChangeBlock({
  change,
  defaultOpen,
}: {
  change: CodeChange;
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-xl border border-border-light/80 bg-white">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={`Toggle code diff for ${change.file_path}`}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors duration-150 hover:bg-bg-muted/30"
      >
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-text-muted" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-text-muted" />
        )}
        <FileCode className="h-4 w-4 shrink-0 text-text-muted" />
        <span className="min-w-0 flex-1 truncate font-mono text-xs text-text-primary">
          {change.file_path}
        </span>
        <Badge variant={CHANGE_TYPE_VARIANT[change.change_type]}>
          {CHANGE_TYPE_LABEL[change.change_type]}
        </Badge>
      </button>

      {open && (
        <div className="border-t border-border-light/60 px-4 py-4">
          {change.explanation && (
            <p className="mb-3 text-sm leading-relaxed text-text-secondary">
              {change.explanation}
            </p>
          )}

          {/* Before / After side-by-side on desktop, stacked on mobile */}
          {(change.before || change.after) && (
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {change.before && (
                <div className="min-w-0">
                  <p className="mb-1.5 text-xs font-medium text-text-muted">
                    Before
                  </p>
                  <CodeBlock code={change.before} showCopy={false} />
                </div>
              )}
              {change.after && (
                <div className="min-w-0">
                  <p className="mb-1.5 text-xs font-medium text-text-muted">
                    After
                  </p>
                  <CodeBlock code={change.after} />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

/**
 * Fix Bundle card — full-width, sectioned layout with structured code diffs.
 */
export function FixBundleCard({ fixBundle }: FixBundleCardProps) {
  const [copiedCommand, setCopiedCommand] = useState<number | null>(null);

  const copyCommand = async (command: string, index: number) => {
    try {
      await navigator.clipboard.writeText(command);
      setCopiedCommand(index);
      setTimeout(() => setCopiedCommand(null), 2000);
    } catch {
      // Clipboard API may fail if page is not focused or lacks permissions
    }
  };

  const hasCodeChanges =
    fixBundle.code_changes && fixBundle.code_changes.length > 0;
  const hasCodeFix = !!fixBundle.code_fix;
  const hasEnvActions =
    fixBundle.env_actions && fixBundle.env_actions.length > 0;
  const hasVerification =
    fixBundle.verification && fixBundle.verification.length > 0;

  return (
    <div className="flex flex-col gap-6 rounded-2xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-card)] sm:p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Wrench className="h-5 w-5 text-accent-warm" />
        <h3 className="text-base font-semibold text-text-primary">
          Recommended Fix
        </h3>
        {fixBundle.version && (
          <Badge variant="outline">v{fixBundle.version}</Badge>
        )}
      </div>

      {/* Summary */}
      {fixBundle.summary && (
        <p className="text-sm leading-relaxed text-text-secondary">
          {fixBundle.summary}
        </p>
      )}

      {/* Fix Steps */}
      {fixBundle.fix_steps && fixBundle.fix_steps.length > 0 && (
        <div className="flex flex-col gap-3">
          <SectionHeading
            icon={<ListChecks className="h-4 w-4 text-text-muted" />}
            title="Fix Steps"
          />
          <div className="flex flex-col gap-2">
            {fixBundle.fix_steps.map((step: string, index: number) => (
              <div
                key={index}
                className="flex items-start gap-3 rounded-xl border border-border-light/60 bg-bg-muted/30 p-4"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-warm/10 text-xs font-medium text-accent-warm">
                  {index + 1}
                </span>
                <span className="min-w-0 pt-0.5 text-sm leading-relaxed text-text-secondary">
                  <StepContent text={step} />
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Code Changes (preferred) or Code Fix (fallback) */}
      {hasCodeChanges && (
        <div className="flex flex-col gap-3">
          <SectionHeading
            icon={<FileCode className="h-4 w-4 text-text-muted" />}
            title="Code Changes"
          />
          <div className="flex flex-col gap-2">
            {fixBundle.code_changes.map((change: CodeChange, index: number) => (
              <CodeChangeBlock
                key={`${change.file_path}-${change.change_type}-${index}`}
                change={change}
                defaultOpen={index === 0}
              />
            ))}
          </div>
        </div>
      )}

      {!hasCodeChanges && hasCodeFix && (
        <div className="flex flex-col gap-3">
          <SectionHeading
            icon={<FileCode className="h-4 w-4 text-text-muted" />}
            title="Code Fix"
          />
          <CodeBlock code={fixBundle.code_fix!} />
        </div>
      )}

      {/* Environment Setup */}
      {hasEnvActions && (
        <div className="flex flex-col gap-3">
          <SectionHeading
            icon={<Settings className="h-4 w-4 text-text-muted" />}
            title="Environment Setup"
          />
          <div className="flex flex-col gap-2">
            {fixBundle.env_actions.map(
              (action: EnvAction, index: number) => (
                <div
                  key={action.order}
                  className="flex items-center gap-3 rounded-xl bg-bg-muted p-3"
                >
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-text-primary text-xs font-medium text-white">
                    {action.order}
                  </div>
                  <div className="flex min-w-0 flex-1 flex-col gap-1">
                    <code className="font-mono text-xs text-text-primary">
                      {action.command}
                    </code>
                    <p className="text-xs text-text-muted">
                      {action.explanation}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => copyCommand(action.command, index)}
                    aria-label="Copy command to clipboard"
                    className="rounded-lg p-1.5 text-text-muted transition-colors duration-150 hover:bg-white hover:text-text-primary"
                  >
                    {copiedCommand === index ? (
                      <Check
                        className="h-4 w-4 text-success-foreground"
                        aria-hidden="true"
                      />
                    ) : (
                      <Copy className="h-4 w-4" aria-hidden="true" />
                    )}
                  </button>
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* Verification */}
      {hasVerification && (
        <div className="flex flex-col gap-3">
          <SectionHeading
            icon={<Play className="h-4 w-4 text-text-muted" />}
            title="Verification"
          />
          <div className="flex flex-col gap-2">
            {fixBundle.verification.map((step: VerificationStep) => (
              <div
                key={step.order}
                className="flex items-start gap-3 rounded-xl border border-border-light/60 p-3"
              >
                <Terminal className="mt-0.5 h-4 w-4 shrink-0 text-text-muted" />
                <div className="flex min-w-0 flex-1 flex-col gap-1">
                  <code className="font-mono text-xs text-text-primary">
                    {step.command}
                  </code>
                  <p className="text-xs text-text-muted">
                    Expected: {step.expected_output}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
