import { Users, ThumbsUp, Clock } from "lucide-react";
import { formatNumber, formatRelativeTime } from "@/lib/utils";

interface TrustSignalsProps {
  verificationCount: number;
  successRate: number;
  lastConfirmedAt?: string;
}

/**
 * Trust signals component showing verification stats.
 */
export function TrustSignals({
  verificationCount,
  successRate,
  lastConfirmedAt,
}: TrustSignalsProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 rounded-2xl border border-border-light/80 bg-white px-5 py-4 shadow-[var(--shadow-card)] sm:gap-6 sm:px-6">
      <div className="flex items-center gap-2">
        <Users className="h-4 w-4 text-text-muted" />
        <span className="text-[13px] text-text-primary">
          <strong>{formatNumber(verificationCount)}</strong>{" "}
          <span className="text-text-secondary">uses</span>
        </span>
      </div>
      <div className="hidden h-4 w-px bg-border-light sm:block" />
      <div className="flex items-center gap-2">
        <ThumbsUp className="h-4 w-4 text-text-muted" />
        <span className="text-[13px] text-text-primary">
          <strong>{Math.round(successRate * 100)}%</strong>{" "}
          <span className="text-text-secondary">success rate</span>
        </span>
      </div>
      {lastConfirmedAt && (
        <>
          <div className="hidden h-4 w-px bg-border-light sm:block" />
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-text-muted" />
            <span className="text-[13px] text-text-secondary">
              Last confirmed {formatRelativeTime(lastConfirmedAt)}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
