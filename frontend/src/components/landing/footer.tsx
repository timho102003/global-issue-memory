import Link from "next/link";
import Image from "next/image";
import { Github, Twitter } from "lucide-react";

/**
 * Footer with responsive layout and proper container.
 */
export function Footer() {
  return (
    <footer className="bg-bg-gradient-end px-5 py-10 sm:px-8 sm:py-14 lg:px-12">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-8">
        {/* Top Row */}
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <Image src="/logos/gim.svg" alt="GIM" width={32} height={32} className="h-8 w-8" />
            <span className="hidden text-[13px] font-light tracking-wide text-text-primary sm:inline">Global Issue Memory</span>
            <span className="text-[13px] font-light tracking-wide text-text-primary sm:hidden">GIM</span>
          </div>

          {/* Links */}
          <nav className="flex flex-wrap items-center gap-5 sm:gap-6">
            <Link href="/docs" className="text-[13px] text-text-secondary transition-colors hover:text-text-primary">
              Documentation
            </Link>
<Link href="/terms" className="text-[13px] text-text-secondary transition-colors hover:text-text-primary">
              Terms &amp; Privacy
            </Link>
          </nav>
        </div>

        {/* Divider */}
        <div className="h-px w-full bg-border-medium/50" />

        {/* Bottom Row */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[12px] text-text-muted">
            © 2025–2026 GIM. PolyForm Noncommercial License 1.0.0.
          </p>

          {/* Social Links */}
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/timho102003/global-issue-memory"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-muted transition-colors hover:text-text-primary"
              aria-label="GIM on GitHub"
            >
              <Github className="h-4 w-4" />
            </a>
            <a
              href="https://twitter.com/gim_dev"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-muted transition-colors hover:text-text-primary"
              aria-label="GIM on Twitter"
            >
              <Twitter className="h-4 w-4" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
