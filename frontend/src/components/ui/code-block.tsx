"use client";

import { useState, type HTMLAttributes } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface CodeBlockProps extends HTMLAttributes<HTMLPreElement> {
  code: string;
  language?: string;
  showCopy?: boolean;
}

/**
 * CodeBlock component for displaying code snippets.
 */
function CodeBlock({
  code,
  language = "bash",
  showCopy = true,
  className,
  ...props
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative min-w-0 max-w-full">
      <pre
        className={cn(
          "w-0 min-w-full overflow-x-auto rounded-xl bg-[#1E1E1E] p-4 font-mono text-xs text-white sm:text-sm",
          className
        )}
        {...props}
      >
        <code>{code}</code>
      </pre>
      {showCopy && (
        <button
          type="button"
          onClick={handleCopy}
          className="absolute right-3 top-3 rounded-lg p-2 text-white/60 hover:bg-white/10 hover:text-white"
          title="Copy to clipboard"
        >
          {copied ? (
            <Check className="h-4 w-4" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </button>
      )}
    </div>
  );
}

export { CodeBlock };
