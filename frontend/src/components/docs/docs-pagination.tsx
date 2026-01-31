"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { getAllLeafPages } from "./docs-nav-config";

export function DocsPagination() {
  const pathname = usePathname();
  const pages = getAllLeafPages();
  const currentIndex = pages.findIndex((p) => p.href === pathname);

  if (currentIndex === -1) return null;

  const prev = currentIndex > 0 ? pages[currentIndex - 1] : null;
  const next = currentIndex < pages.length - 1 ? pages[currentIndex + 1] : null;

  return (
    <div className="mt-12 flex items-center justify-between border-t border-border-light pt-6">
      {prev ? (
        <Link
          href={prev.href}
          className="group flex items-center gap-2 text-[13px] font-medium text-text-secondary transition-colors duration-150 hover:text-text-primary"
        >
          <ArrowLeft className="h-3.5 w-3.5 transition-transform duration-150 group-hover:-translate-x-0.5" />
          {prev.title}
        </Link>
      ) : (
        <span />
      )}
      {next ? (
        <Link
          href={next.href}
          className="group flex items-center gap-2 text-[13px] font-medium text-text-secondary transition-colors duration-150 hover:text-text-primary"
        >
          {next.title}
          <ArrowRight className="h-3.5 w-3.5 transition-transform duration-150 group-hover:translate-x-0.5" />
        </Link>
      ) : (
        <span />
      )}
    </div>
  );
}
