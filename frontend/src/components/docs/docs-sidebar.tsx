"use client";

import { useState, useMemo, useCallback } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { docsNavConfig, type DocsNavItem } from "./docs-nav-config";

/**
 * Returns the set of parent titles whose children (or self) match
 * the current pathname, so they auto-expand on navigation.
 */
function getExpandedParents(
  pathname: string,
  items: DocsNavItem[]
): Set<string> {
  const expanded = new Set<string>();
  for (const item of items) {
    if (item.children) {
      const isChildActive = item.children.some(
        (child) => child.href === pathname
      );
      const isParentActive = item.href === pathname;
      if (isChildActive || isParentActive) {
        expanded.add(item.title);
      }
    }
  }
  return expanded;
}

export function DocsSidebar() {
  const pathname = usePathname();

  // User-toggled sections: tracks explicit open / close actions.
  // Key = parent title, value = true (force open) or false (force closed).
  const [userToggles, setUserToggles] = useState<Record<string, boolean>>({});

  // Auto-expanded parents derived from the current pathname.
  const autoExpanded = useMemo(
    () => getExpandedParents(pathname, docsNavConfig),
    [pathname]
  );

  const isExpanded = useCallback(
    (title: string): boolean => {
      // Explicit user toggle takes precedence
      if (title in userToggles) {
        return userToggles[title];
      }
      // Otherwise fall back to auto-expand from pathname
      return autoExpanded.has(title);
    },
    [userToggles, autoExpanded]
  );

  // When the user explicitly toggles, flip current visual state
  const handleToggle = useCallback(
    (title: string) => {
      const currentlyOpen = isExpanded(title);
      setUserToggles((prev) => ({
        ...prev,
        [title]: !currentlyOpen,
      }));
    },
    [isExpanded]
  );

  return (
    <aside className="sticky top-24 hidden w-60 shrink-0 lg:block">
      <nav className="flex flex-col gap-1">
        {docsNavConfig.map((item) => (
          <SidebarItem
            key={item.title}
            item={item}
            pathname={pathname}
            isExpanded={isExpanded(item.title)}
            onToggle={() => handleToggle(item.title)}
          />
        ))}
      </nav>
    </aside>
  );
}

function SidebarItem({
  item,
  pathname,
  isExpanded,
  onToggle,
}: {
  item: DocsNavItem;
  pathname: string;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const Icon = item.icon;
  const hasChildren = item.children && item.children.length > 0;
  const isActive = item.href === pathname;

  if (!hasChildren) {
    return (
      <Link
        href={item.href ?? "#"}
        className={cn(
          "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-200",
          isActive
            ? "bg-accent-warm/10 text-accent-warm"
            : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
        )}
      >
        <Icon className="h-3.5 w-3.5 shrink-0" />
        <span>{item.title}</span>
      </Link>
    );
  }

  return (
    <div>
      <div className="flex items-center">
        {item.href ? (
          <Link
            href={item.href}
            className={cn(
              "flex flex-1 items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-200",
              isActive
                ? "bg-accent-warm/10 text-accent-warm"
                : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
            )}
          >
            <Icon className="h-3.5 w-3.5 shrink-0" />
            <span>{item.title}</span>
          </Link>
        ) : (
          <button
            onClick={onToggle}
            className={cn(
              "flex flex-1 items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-200",
              "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
            )}
          >
            <Icon className="h-3.5 w-3.5 shrink-0" />
            <span>{item.title}</span>
          </button>
        )}
        <button
          onClick={onToggle}
          className="mr-1 flex items-center justify-center rounded-lg p-1.5 text-text-secondary transition-all duration-200 hover:bg-bg-muted hover:text-text-primary"
          aria-label={
            isExpanded ? `Collapse ${item.title}` : `Expand ${item.title}`
          }
        >
          <ChevronRight
            className={cn(
              "h-3.5 w-3.5 transition-transform duration-200",
              isExpanded && "rotate-90"
            )}
          />
        </button>
      </div>

      {isExpanded && item.children && (
        <div className="ml-[18px] mt-0.5 border-l border-border-light pl-4">
          <div className="flex flex-col gap-0.5">
            {item.children.map((child) => {
              const ChildIcon = child.icon;
              const isChildActive = child.href === pathname;

              return (
                <Link
                  key={child.href}
                  href={child.href}
                  className={cn(
                    "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-200",
                    isChildActive
                      ? "bg-accent-warm/10 text-accent-warm"
                      : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
                  )}
                >
                  <ChildIcon className="h-3.5 w-3.5 shrink-0" />
                  <span>{child.title}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
