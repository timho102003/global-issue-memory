"use client";

import { Check, Copy, Terminal } from "lucide-react";
import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { FixBundle, EnvAction, VerificationStep } from "@/types";

interface FixBundleCardProps {
  fixBundle: FixBundle;
}

/**
 * Fix Bundle card component matching GIM.pen Issue Detail design.
 */
export function FixBundleCard({ fixBundle }: FixBundleCardProps) {
  const [copiedCommand, setCopiedCommand] = useState<number | null>(null);

  const copyCommand = async (command: string, index: number) => {
    await navigator.clipboard.writeText(command);
    setCopiedCommand(index);
    setTimeout(() => setCopiedCommand(null), 2000);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Fix Bundle</CardTitle>
          <Badge variant="outline">v{fixBundle.version}</Badge>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        {/* Environment Actions */}
        <div className="flex flex-col gap-3">
          <h4 className="text-sm font-medium text-text-primary">
            Environment Actions
          </h4>
          <div className="flex flex-col gap-2">
            {fixBundle.env_actions.map((action: EnvAction, index: number) => (
              <div
                key={action.order}
                className="flex items-center gap-3 rounded-xl bg-bg-muted p-3"
              >
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#3D3D3D] text-xs font-medium text-white">
                  {action.order}
                </div>
                <div className="flex flex-1 flex-col gap-1">
                  <code className="font-mono text-xs text-text-primary">
                    {action.command}
                  </code>
                  <p className="text-xs text-text-muted">{action.explanation}</p>
                </div>
                <button
                  onClick={() => copyCommand(action.command, index)}
                  aria-label="Copy command to clipboard"
                  className="rounded-lg p-1.5 text-text-muted hover:bg-white hover:text-text-primary"
                >
                  {copiedCommand === index ? (
                    <Check className="h-4 w-4 text-success-foreground" aria-hidden="true" />
                  ) : (
                    <Copy className="h-4 w-4" aria-hidden="true" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Verification Steps */}
        <div className="flex flex-col gap-3">
          <h4 className="text-sm font-medium text-text-primary">
            Verification Steps
          </h4>
          <div className="flex flex-col gap-2">
            {fixBundle.verification.map((step: VerificationStep) => (
              <div
                key={step.order}
                className="flex items-start gap-3 rounded-xl border border-border-light p-3"
              >
                <Terminal className="mt-0.5 h-4 w-4 shrink-0 text-text-muted" />
                <div className="flex flex-1 flex-col gap-1">
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

        {/* Code Fix */}
        {fixBundle.code_fix && (
          <div className="flex flex-col gap-3">
            <h4 className="text-sm font-medium text-text-primary">Code Fix</h4>
            <pre className="overflow-x-auto rounded-xl bg-[#1E1E1E] p-4 font-mono text-xs text-white">
              {fixBundle.code_fix}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
