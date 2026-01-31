import { Monitor, Cable, Server, Database } from "lucide-react";
import { cn } from "@/lib/utils";

const nodes = [
  {
    icon: Monitor,
    title: "Developer IDE",
    subtitle: "Claude Code CLI",
  },
  {
    icon: Cable,
    title: "MCP Client",
    subtitle: "Tool invocation layer",
  },
  {
    icon: Server,
    title: "GIM Server",
    subtitle: "Matching & deduplication",
  },
  {
    icon: Database,
    title: "Knowledge Base",
    subtitle: "Embeddings & verified fixes",
  },
];

function Arrow({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center justify-center text-text-muted", className)}>
      {/* Horizontal arrow for desktop */}
      <div className="hidden lg:flex items-center">
        <div className="h-px w-8 bg-border-medium" />
        <div className="h-0 w-0 border-y-[5px] border-l-[8px] border-y-transparent border-l-border-medium" />
      </div>
      {/* Vertical arrow for mobile */}
      <div className="flex lg:hidden flex-col items-center">
        <div className="w-px h-6 bg-border-medium" />
        <div className="h-0 w-0 border-x-[5px] border-t-[8px] border-x-transparent border-t-border-medium" />
      </div>
    </div>
  );
}

export function ArchitectureDiagram() {
  return (
    <div className="rounded-2xl border border-border-light bg-bg-muted/50 p-4 sm:p-6">
      <div className="flex flex-col items-center gap-2 lg:flex-row lg:justify-center lg:gap-0">
        {nodes.map((node, i) => {
          const Icon = node.icon;
          return (
            <div key={node.title} className="flex flex-col items-center lg:flex-row">
              {i > 0 && <Arrow />}
              <div className="flex w-full max-w-[200px] flex-col items-center rounded-xl border border-border-light bg-white p-4 shadow-[var(--shadow-card)] lg:w-[180px]">
                <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-accent-warm/10">
                  <Icon className="h-4.5 w-4.5 text-accent-warm" />
                </div>
                <p className="text-center text-[13px] font-semibold text-text-primary">
                  {node.title}
                </p>
                <p className="text-center text-[11px] text-text-muted">
                  {node.subtitle}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
