"use client";

/**
 * Card-based skeleton matching the issue card layout with pulse animations.
 */
export function IssuesSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="flex flex-col gap-3 rounded-2xl border border-border-light/80 bg-white p-4 shadow-[var(--shadow-card)] sm:p-5"
        >
          {/* Top row: badge + status + confidence */}
          <div className="flex items-center justify-between">
            <div className="h-6 w-20 animate-pulse rounded-full bg-bg-tertiary" />
            <div className="flex items-center gap-2.5">
              <div className="h-6 w-16 animate-pulse rounded-full bg-bg-tertiary" />
              <div className="flex items-center gap-2">
                <div className="h-1.5 w-16 animate-pulse rounded-full bg-bg-tertiary" />
                <div className="h-3 w-8 animate-pulse rounded bg-bg-tertiary" />
              </div>
            </div>
          </div>

          {/* Title */}
          <div className="flex flex-col gap-1.5">
            <div className="h-4 w-full animate-pulse rounded bg-bg-tertiary" />
            <div className="h-4 w-2/3 animate-pulse rounded bg-bg-tertiary" />
          </div>

          {/* Fix preview block */}
          <div className="flex items-start gap-2 rounded-xl border border-border-soft bg-bg-muted/30 px-3 py-2.5">
            <div className="mt-0.5 h-3.5 w-3.5 animate-pulse rounded bg-bg-tertiary" />
            <div className="flex flex-1 flex-col gap-1">
              <div className="h-3 w-full animate-pulse rounded bg-bg-tertiary" />
              <div className="h-3 w-3/4 animate-pulse rounded bg-bg-tertiary" />
            </div>
          </div>

          {/* Footer metadata */}
          <div className="flex items-center gap-3">
            <div className="h-3 w-14 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-3 w-24 animate-pulse rounded bg-bg-tertiary" />
            <div className="h-3 w-16 animate-pulse rounded bg-bg-tertiary" />
          </div>
        </div>
      ))}
    </div>
  );
}
