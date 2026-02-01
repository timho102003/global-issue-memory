import type { Metadata } from "next";
import { BookOpen } from "lucide-react";
import { DocsSidebar } from "@/components/docs/docs-sidebar";
import { DocsMobileNav } from "@/components/docs/docs-mobile-nav";
import { DocsBreadcrumb } from "@/components/docs/docs-breadcrumb";
import { DocsPagination } from "@/components/docs/docs-pagination";

export const metadata: Metadata = {
  title: {
    template: "%s | GIM Docs",
    default: "Documentation | GIM",
  },
  description:
    "Learn how to set up and use Global Issue Memory in your development workflow.",
};

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="px-5 py-8 sm:px-8 sm:py-12 lg:px-12">
      <div className="mx-auto max-w-[1200px]">
        {/* Documentation pill */}
        <div className="mb-8 flex justify-center">
          <div className="flex items-center gap-2 rounded-full border border-border-light bg-white/80 px-4 py-2 shadow-[var(--shadow-xs)]">
            <BookOpen className="h-3.5 w-3.5 text-accent-warm" />
            <span className="text-[13px] font-medium text-text-primary">
              Documentation
            </span>
          </div>
        </div>

        {/* Mobile navigation */}
        <div className="relative z-20 mb-6">
          <DocsMobileNav />
        </div>

        {/* Two-column layout */}
        <div className="flex gap-10 lg:gap-14">
          <DocsSidebar />
          <main className="min-w-0 flex-1">
            <DocsBreadcrumb />
            {children}
            <DocsPagination />
          </main>
        </div>
      </div>
    </div>
  );
}
