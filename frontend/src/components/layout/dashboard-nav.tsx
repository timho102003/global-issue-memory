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
    <nav className="flex h-[72px] items-center justify-between px-10">
      {/* Logo */}
      <Link href="/dashboard" className="flex items-center gap-2.5 rounded-3xl px-3.5 py-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-gradient-to-br from-[#3D3D3D] to-[#5A5A5A]">
          <span className="text-sm font-bold text-white">G</span>
        </div>
        <span className="text-xl font-bold text-text-primary">GIM</span>
      </Link>

      {/* Nav Tabs */}
      <div className="flex items-center gap-1 rounded-[28px] bg-white p-1.5">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-[22px] px-5 py-2.5 text-sm font-medium transition-colors",
              isActive(item.href)
                ? "bg-[#3D3D3D] text-white"
                : "text-text-secondary hover:text-text-primary"
            )}
          >
            {item.label}
          </Link>
        ))}
      </div>

      {/* Profile Avatar */}
      <div className="flex items-center gap-3">
        <Link href="/dashboard/profile">
          <Avatar
            fallback={gimId?.slice(0, 2).toUpperCase() || "U"}
            size="default"
          />
        </Link>
      </div>
    </nav>
  );
}
