import { cn } from "@/lib/utils";

interface FlowNodeProps {
  label: string;
  sublabel?: string;
  variant?: "start" | "decision" | "action" | "success";
  className?: string;
}

function FlowNode({ label, sublabel, variant = "action", className }: FlowNodeProps) {
  const styles = {
    start: "border-accent-warm/30 bg-accent-warm/10",
    decision: "border-accent-amber/30 bg-accent-amber/10",
    action: "border-border-light bg-white",
    success: "border-accent-green/30 bg-accent-green/5",
  };

  return (
    <div
      className={cn(
        "rounded-xl border px-4 py-3 text-center shadow-[var(--shadow-xs)]",
        styles[variant],
        className
      )}
    >
      <p className="text-[13px] font-semibold text-text-primary">{label}</p>
      {sublabel && (
        <p className="mt-0.5 text-[11px] text-text-muted">{sublabel}</p>
      )}
    </div>
  );
}

function DownArrow() {
  return (
    <div className="flex flex-col items-center">
      <div className="h-5 w-px bg-border-medium" />
      <div className="h-0 w-0 border-x-[4px] border-t-[6px] border-x-transparent border-t-border-medium" />
    </div>
  );
}

function ArrowLabel({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-center">
      <div className="h-3 w-px bg-border-medium" />
      <span className="text-[10px] font-medium text-text-muted">{text}</span>
      <div className="h-3 w-px bg-border-medium" />
      <div className="h-0 w-0 border-x-[4px] border-t-[6px] border-x-transparent border-t-border-medium" />
    </div>
  );
}

export function IssueLifecycleDiagram() {
  return (
    <div className="rounded-2xl border border-border-light bg-bg-muted/50 p-4 sm:p-6">
      <div className="flex flex-col items-center gap-0">
        <FlowNode label="Error Encountered" variant="start" className="w-full max-w-[220px]" />
        <DownArrow />
        <FlowNode label="Search GIM" sublabel="gim_search_issues" variant="action" className="w-full max-w-[220px]" />
        <DownArrow />
        <FlowNode label="Match Found?" variant="decision" className="w-full max-w-[220px]" />

        {/* Branch */}
        <div className="mt-1 grid w-full max-w-[480px] grid-cols-2 gap-4">
          {/* Yes branch */}
          <div className="flex flex-col items-center gap-0">
            <ArrowLabel text="Yes" />
            <FlowNode label="Apply Fix" variant="action" className="w-full" />
            <DownArrow />
            <FlowNode label="Verify &amp; Confirm" sublabel="gim_confirm_fix" variant="success" className="w-full" />
          </div>

          {/* No branch */}
          <div className="flex flex-col items-center gap-0">
            <ArrowLabel text="No" />
            <FlowNode label="Solve Manually" variant="action" className="w-full" />
            <DownArrow />
            <FlowNode label="Submit to GIM" sublabel="gim_submit_issue" variant="success" className="w-full" />
          </div>
        </div>

        <DownArrow />
        <FlowNode label="Knowledge Base Updated" variant="start" className="w-full max-w-[220px]" />
      </div>
    </div>
  );
}
