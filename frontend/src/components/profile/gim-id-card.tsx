"use client";

import { useState } from "react";
import { Copy, Check, Eye, EyeOff } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface GimIdCardProps {
  gimId: string;
}

/**
 * Masks a GIM ID to show only first 4 and last 4 characters.
 */
function maskGimId(id: string): string {
  if (id.length <= 8) return id;
  return `${id.slice(0, 4)}${"*".repeat(id.length - 8)}${id.slice(-4)}`;
}

/**
 * GIM ID card component with copy and visibility toggle.
 */
export function GimIdCard({ gimId }: GimIdCardProps) {
  const [copied, setCopied] = useState(false);
  const [visible, setVisible] = useState(false);

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
        <div className="flex items-center gap-2 rounded-xl bg-bg-muted p-4">
          <code className="flex-1 font-mono text-sm text-text-primary">
            {visible ? gimId : maskGimId(gimId)}
          </code>
          <button
            onClick={() => setVisible((v) => !v)}
            className="rounded-lg p-2 text-text-muted transition-colors duration-150 hover:bg-white hover:text-text-primary"
            title={visible ? "Hide GIM ID" : "Show GIM ID"}
          >
            {visible ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={handleCopy}
            className="rounded-lg p-2 text-text-muted transition-colors duration-150 hover:bg-white hover:text-text-primary"
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
