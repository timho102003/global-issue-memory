"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { BookOpen, ChevronDown } from "lucide-react";
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
      {/* Card-style trigger button */}
      <button
        onClick={() => setOpen((prev) => !prev)}
        className={cn(
          "flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left transition-all duration-200",
          "bg-white shadow-[var(--shadow-card)] active:scale-[0.99]",
          open
            ? "border-accent-warm/30 ring-1 ring-accent-warm/20 shadow-[var(--shadow-card-hover)]"
            : "border-border-light hover:shadow-[var(--shadow-card-hover)]"
        )}
        aria-label={open ? "Close navigation" : "Open navigation"}
        aria-expanded={open}
      >
        {/* Accent icon badge */}
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-warm/10">
          <BookOpen className="h-4 w-4 text-accent-warm" />
        </div>

        {/* Two-line label */}
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-medium uppercase tracking-wider text-text-secondary">
            Navigate
          </div>
          <div className="truncate text-[14px] font-semibold text-text-primary">
            {currentTitle}
          </div>
        </div>

        {/* Chevron indicator */}
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-text-secondary transition-transform duration-300",
            open && "rotate-180"
          )}
        />
      </button>

      {/* Backdrop overlay */}
      <div
        className={cn(
          "fixed inset-0 z-10 bg-text-primary/10 backdrop-blur-[2px] transition-opacity duration-300",
          open
            ? "opacity-100"
            : "pointer-events-none opacity-0"
        )}
        onClick={() => setOpen(false)}
        aria-hidden="true"
      />

      {/* Dropdown panel */}
      <div
        className={cn(
          "relative z-20 mt-2 rounded-xl border border-border-light bg-white shadow-[var(--shadow-md)] transition-all duration-300 ease-out",
          open
            ? "max-h-[70vh] opacity-100"
            : "pointer-events-none max-h-0 overflow-hidden border-transparent opacity-0 shadow-none"
        )}
      >
        <nav
          className={cn(
            "flex flex-col overflow-y-auto overscroll-contain px-2 py-2",
            open && "max-h-[70vh]"
          )}
        >
          {docsNavConfig.map((item, sectionIndex) => (
            <div key={item.title}>
              {sectionIndex > 0 && (
                <div className="mx-3 my-1 h-px bg-border-soft" />
              )}
              <MobileNavItem
                item={item}
                pathname={pathname}
                isExpanded={expanded.has(item.title)}
                onToggle={() => toggleSection(item.title)}
                onLinkClick={() => setOpen(false)}
              />
            </div>
          ))}
        </nav>

        {/* Bottom fade gradient for scroll hint */}
        {open && (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-6 rounded-b-xl bg-gradient-to-t from-white to-transparent" />
        )}
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
  const containsActive =
    hasChildren && item.children!.some((child) => child.href === pathname);

  if (!hasChildren) {
    return (
      <Link
        href={item.href ?? "#"}
        onClick={onLinkClick}
        className={cn(
          "flex min-h-[44px] items-center gap-3 rounded-lg px-3 text-[14px] font-semibold transition-all duration-200",
          isActive
            ? "bg-accent-warm/8 text-accent-warm"
            : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
        )}
      >
        <div
          className={cn(
            "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors duration-200",
            isActive ? "bg-accent-warm/15" : "bg-bg-tertiary"
          )}
        >
          <Icon className="h-3.5 w-3.5" />
        </div>
        <span>{item.title}</span>
      </Link>
    );
  }

  return (
    <div>
      {/* Section header */}
      <div className="flex items-center">
        {item.href ? (
          <Link
            href={item.href}
            onClick={onLinkClick}
            className={cn(
              "flex min-h-[44px] flex-1 items-center gap-3 rounded-lg px-3 text-[14px] font-semibold transition-all duration-200",
              isActive || containsActive
                ? "bg-bg-highlight text-text-primary"
                : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
            )}
          >
            <div
              className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors duration-200",
                isActive || containsActive
                  ? "bg-accent-warm/15"
                  : "bg-bg-tertiary"
              )}
            >
              <Icon className="h-3.5 w-3.5" />
            </div>
            <span>{item.title}</span>
          </Link>
        ) : (
          <button
            onClick={onToggle}
            className={cn(
              "flex min-h-[44px] flex-1 items-center gap-3 rounded-lg px-3 text-[14px] font-semibold transition-all duration-200",
              containsActive
                ? "bg-bg-highlight text-text-primary"
                : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
            )}
          >
            <div
              className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors duration-200",
                containsActive ? "bg-accent-warm/15" : "bg-bg-tertiary"
              )}
            >
              <Icon className="h-3.5 w-3.5" />
            </div>
            <span>{item.title}</span>
          </button>
        )}
        <button
          onClick={onToggle}
          className="mr-1 flex min-h-[44px] items-center justify-center rounded-lg px-2 text-text-secondary transition-all duration-200 hover:bg-bg-muted hover:text-text-primary"
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

      {/* Children with connector line */}
      <div
        className={cn(
          "overflow-hidden transition-all duration-300 ease-out",
          isExpanded ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className="relative ml-[26px] border-l border-border-soft pl-3 py-0.5">
          {item.children!.map((child, index) => {
            const isChildActive = child.href === pathname;

            return (
              <Link
                key={child.href}
                href={child.href}
                onClick={onLinkClick}
                className={cn(
                  "relative flex min-h-[44px] items-center rounded-lg px-3 text-[13px] font-medium transition-all duration-200",
                  isChildActive
                    ? "bg-accent-warm/8 text-accent-warm"
                    : "text-text-secondary hover:bg-bg-muted hover:text-text-primary"
                )}
                style={{
                  transitionDelay: isExpanded ? `${index * 30}ms` : "0ms",
                }}
              >
                {/* Active dot indicator on connector line */}
                {isChildActive && (
                  <div className="absolute -left-[15px] top-1/2 -translate-y-1/2">
                    <div className="h-1.5 w-1.5 rounded-full bg-accent-warm" />
                  </div>
                )}
                <span>{child.title}</span>
              </Link>
            );
          })}
        </div>
      </div>
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
