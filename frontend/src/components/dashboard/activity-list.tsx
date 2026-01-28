import { FileText, CheckCircle, RefreshCw } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import type { ActivityItem } from "@/lib/api/issues";

interface ActivityListProps {
  activities: ActivityItem[];
}

const activityIcons = {
  submission: FileText,
  confirmation: CheckCircle,
  update: RefreshCw,
};

const activityLabels = {
  submission: "New issue submitted",
  confirmation: "Fix confirmed",
  update: "Issue updated",
};

/**
 * Activity list component for dashboard.
 */
export function ActivityList({ activities }: ActivityListProps) {
  if (activities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="text-text-secondary">No recent activity</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {activities.map((activity) => {
        const Icon = activityIcons[activity.type];
        return (
          <div
            key={activity.id}
            className="flex items-start gap-3 border-b border-border-soft p-4 last:border-0"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-bg-muted">
              <Icon className="h-4 w-4 text-text-secondary" />
            </div>
            <div className="flex flex-1 flex-col gap-0.5">
              <p className="text-sm text-text-primary">
                {activityLabels[activity.type]}
              </p>
              <p className="text-xs text-text-secondary line-clamp-1">
                {activity.issue_title}
              </p>
            </div>
            <span className="text-xs text-text-muted">
              {formatRelativeTime(activity.timestamp)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
