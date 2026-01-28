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
    <div className="flex items-center gap-6 rounded-xl border border-border-light bg-white px-6 py-4">
      <div className="flex items-center gap-2">
        <Users className="h-4 w-4 text-text-muted" />
        <span className="text-sm text-text-primary">
          <strong>{formatNumber(verificationCount)}</strong>{" "}
          <span className="text-text-secondary">uses</span>
        </span>
      </div>
      <div className="h-4 w-px bg-border" />
      <div className="flex items-center gap-2">
        <ThumbsUp className="h-4 w-4 text-text-muted" />
        <span className="text-sm text-text-primary">
          <strong>{Math.round(successRate * 100)}%</strong>{" "}
          <span className="text-text-secondary">success rate</span>
        </span>
      </div>
      {lastConfirmedAt && (
        <>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-text-muted" />
            <span className="text-sm text-text-secondary">
              Last confirmed {formatRelativeTime(lastConfirmedAt)}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
