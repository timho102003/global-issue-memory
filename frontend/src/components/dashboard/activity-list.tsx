import { Check, Plus, User } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import type { ActivityItem } from "@/lib/api/issues";

interface ActivityListProps {
  activities: ActivityItem[];
}

type ActivityType = "submission" | "confirmation" | "update" | "contributor";

interface ActivityStyle {
  icon: typeof Check;
  bgColor: string;
  iconColor: string;
  label: (title: string) => string;
}

const activityStyles: Record<ActivityType, ActivityStyle> = {
  confirmation: {
    icon: Check,
    bgColor: "#E3F0E3",
    iconColor: "#4A7A4A",
    label: (title) => `Issue ${title} marked as resolved`,
  },
  submission: {
    icon: Plus,
    bgColor: "#FEF3CD",
    iconColor: "#856404",
    label: (title) => `New issue reported: ${title}`,
  },
  update: {
    icon: Plus,
    bgColor: "#FEF3CD",
    iconColor: "#856404",
    label: (title) => `Issue updated: ${title}`,
  },
  contributor: {
    icon: User,
    bgColor: "#E8E3F0",
    iconColor: "#6B5B8C",
    label: (title) => `New contributor joined: ${title}`,
  },
};

/**
 * Activity list component for dashboard matching GIM.pen design.
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
        const type = activity.type as ActivityType;
        const style = activityStyles[type] || activityStyles.update;
        const Icon = style.icon;

        return (
          <div
            key={activity.id}
            className="flex items-center gap-3 border-b border-border-soft px-5 py-3.5 transition-colors last:border-0 hover:bg-bg-muted/30 sm:px-6 sm:py-4"
          >
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
              style={{ backgroundColor: style.bgColor }}
            >
              <Icon className="h-3.5 w-3.5" style={{ color: style.iconColor }} />
            </div>
            <div className="flex flex-1 flex-col gap-0.5">
              <p className="text-[13px] font-medium text-text-primary">
                {style.label(activity.issue_title)}
              </p>
              <p className="text-[11px] text-text-muted">
                {formatRelativeTime(activity.timestamp)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
