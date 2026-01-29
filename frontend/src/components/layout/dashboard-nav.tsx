"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/avatar";
import { useAuthStore } from "@/stores/auth-store";

/**
 * Dashboard navigation component matching GIM.pen design.
 */
export function DashboardNav() {
  const pathname = usePathname();
  const { gimId } = useAuthStore();

  const navItems = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/dashboard/issues", label: "Issues" },
    { href: "/dashboard/profile", label: "Profile" },
  ];

  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/dashboard";
    }
    return pathname.startsWith(href);
  };

  return (
    <nav className="sticky top-0 z-30 w-full backdrop-blur-md bg-bg-gradient-start/80">
      <div className="mx-auto flex h-14 max-w-[1040px] items-center justify-between px-4 sm:h-16 sm:px-6">
        {/* Logo — no extra padding so the G icon aligns with content below */}
        <Link href="/dashboard" className="flex items-center gap-2 transition-opacity hover:opacity-80 sm:gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-[8px] bg-gradient-to-br from-[#2D2A26] to-[#4A4A4A] shadow-sm sm:h-8 sm:w-8 sm:rounded-[10px]">
            <span className="text-xs font-bold text-white sm:text-sm">G</span>
          </div>
          <span className="text-base font-bold tracking-tight text-text-primary sm:text-lg">GIM</span>
        </Link>

        {/* Nav Tabs */}
        <div className="flex items-center gap-0.5 rounded-full bg-white/80 p-1 shadow-[var(--shadow-nav)] ring-1 ring-border-soft/60">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-full px-3 py-1.5 text-[12px] font-medium transition-all duration-200 sm:px-5 sm:py-2 sm:text-[13px]",
                isActive(item.href)
                  ? "bg-[#2D2A26] text-white shadow-sm"
                  : "text-text-secondary hover:text-text-primary hover:bg-black/[0.03]"
              )}
            >
              {item.label}
            </Link>
          ))}
        </div>

        {/* Profile Avatar */}
        <Link
          href="/dashboard/profile"
          className="transition-transform duration-200 hover:scale-105"
        >
          <Avatar
            fallback={gimId?.slice(0, 2).toUpperCase() || "U"}
            size="sm"
            className="sm:h-10 sm:w-10 sm:text-sm"
          />
        </Link>
      </div>
      {/* Subtle bottom border */}
      <div className="mx-auto max-w-[1040px] px-4 sm:px-6">
        <div className="h-px bg-gradient-to-r from-transparent via-border-light to-transparent" />
      </div>
    </nav>
  );
}
