"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Menu, X, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { docsNavConfig, buildBreadcrumbs } from "./docs-nav-config";
import type { DocsNavItem } from "./docs-nav-config";

export function DocsMobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(() =>
    getExpandedParents(pathname)
  );

  // React 19 pattern: track previous value with state to respond to prop changes
  // See: https://react.dev/learn/you-might-not-need-an-effect#adjusting-some-state-when-a-prop-changes
  const [prevPathname, setPrevPathname] = useState(pathname);
  if (prevPathname !== pathname) {
    setPrevPathname(pathname);
    if (open) {
      setOpen(false);
    }
    const fromPathname = getExpandedParents(pathname);
    let needsUpdate = false;
    for (const key of fromPathname) {
      if (!expanded.has(key)) {
        needsUpdate = true;
        break;
      }
    }
    if (needsUpdate) {
      const next = new Set(expanded);
      for (const key of fromPathname) {
        next.add(key);
      }
      setExpanded(next);
    }
  }

  function toggleSection(title: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(title)) {
        next.delete(title);
      } else {
        next.add(title);
      }
      return next;
    });
  }

  const breadcrumbs = buildBreadcrumbs(pathname);
  const currentTitle =
    breadcrumbs.length > 0
      ? breadcrumbs[breadcrumbs.length - 1].title
      : "Docs";

  return (
    <div className="lg:hidden">
      {/* Top bar */}
      <div className="flex items-center justify-between bg-white/95 px-5 py-3 backdrop-blur-md sm:px-8 border-b border-border-light/60">
        <span className="text-[14px] font-medium text-text-primary truncate mr-3">
          {currentTitle}
        </span>
        <button
          onClick={() => setOpen((prev) => !prev)}
          className="flex items-center justify-center rounded-lg p-1.5 text-text-secondary transition-all duration-200 hover:bg-bg-muted hover:text-text-primary"
          aria-label={open ? "Close navigation" : "Open navigation"}
        >
          {open ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Slide-down drawer */}
      <div
        className={cn(
          "overflow-hidden border-b border-border-light/60 bg-white/95 backdrop-blur-md transition-all duration-300",
          open ? "max-h-[80vh] overflow-y-auto" : "max-h-0 border-b-0"
        )}
      >
        <nav className="flex flex-col gap-0.5 px-5 py-3 sm:px-8">
          {docsNavConfig.map((item) => (
            <MobileNavItem
              key={item.title}
              item={item}
              pathname={pathname}
              isExpanded={expanded.has(item.title)}
              onToggle={() => toggleSection(item.title)}
              onLinkClick={() => setOpen(false)}
            />
          ))}
        </nav>
      </div>
    </div>
  );
}

function MobileNavItem({
  item,
  pathname,
  isExpanded,
  onToggle,
  onLinkClick,
}: {
  item: DocsNavItem;
  pathname: string;
  isExpanded: boolean;
  onToggle: () => void;
  onLinkClick: () => void;
}) {
  const Icon = item.icon;
  const hasChildren = item.children && item.children.length > 0;
  const isActive = item.href === pathname;

  if (!hasChildren) {
    return (
      <Link
        href={item.href ?? "#"}
        onClick={onLinkClick}
        className={cn(
          "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[14px] font-medium transition-all duration-200",
          isActive
            ? "bg-accent-warm/10 text-accent-warm"
            : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
        )}
      >
        <Icon className="h-4 w-4 shrink-0" />
        <span>{item.title}</span>
      </Link>
    );
  }

  return (
    <div>
      {/* Parent row */}
      <div className="flex items-center">
        {item.href ? (
          <Link
            href={item.href}
            onClick={onLinkClick}
            className={cn(
              "flex flex-1 items-center gap-2.5 rounded-lg px-3 py-2 text-[14px] font-medium transition-all duration-200",
              isActive
                ? "bg-accent-warm/10 text-accent-warm"
                : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span>{item.title}</span>
          </Link>
        ) : (
          <button
            onClick={onToggle}
            className={cn(
              "flex flex-1 items-center gap-2.5 rounded-lg px-3 py-2 text-[14px] font-medium transition-all duration-200",
              "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
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
          <ChevronDown
            className={cn(
              "h-4 w-4 transition-transform duration-200",
              isExpanded ? "rotate-0" : "-rotate-90"
            )}
          />
        </button>
      </div>

      {/* Children */}
      {isExpanded && item.children && (
        <div className="flex flex-col gap-0.5">
          {item.children.map((child) => {
            const ChildIcon = child.icon;
            const isChildActive = child.href === pathname;

            return (
              <Link
                key={child.href}
                href={child.href}
                onClick={onLinkClick}
                className={cn(
                  "flex items-center gap-2.5 rounded-lg py-2 pl-8 pr-3 text-[14px] font-medium transition-all duration-200",
                  isChildActive
                    ? "bg-accent-warm/10 text-accent-warm"
                    : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
                )}
              >
                <ChildIcon className="h-4 w-4 shrink-0" />
                <span>{child.title}</span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

/**
 * Returns the set of parent titles that should be expanded
 * based on the current pathname.
 */
function getExpandedParents(pathname: string): Set<string> {
  const expanded = new Set<string>();
  for (const item of docsNavConfig) {
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
