"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface GimIdCardProps {
  gimId: string;
}

/**
 * GIM ID card component with copy functionality.
 */
export function GimIdCard({ gimId }: GimIdCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(gimId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Your GIM ID</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-3 rounded-xl bg-bg-muted p-4">
          <code className="flex-1 font-mono text-sm text-text-primary">
            {gimId}
          </code>
          <button
            onClick={handleCopy}
            className="rounded-lg p-2 text-text-muted hover:bg-white hover:text-text-primary"
            title="Copy GIM ID"
          >
            {copied ? (
              <Check className="h-4 w-4 text-success-foreground" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </button>
        </div>
        <p className="mt-3 text-xs text-text-muted">
          This is your unique identifier. Keep it safe - you&apos;ll need it to sign in.
        </p>
      </CardContent>
    </Card>
  );
}
