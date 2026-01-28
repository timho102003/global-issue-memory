import Link from "next/link";
import { Github, Twitter } from "lucide-react";

/**
 * Footer component matching GIM.pen design.
 */
export function Footer() {
  return (
    <footer className="flex flex-col gap-10 bg-[#E8E4D9] px-20 py-[60px]">
      {/* Top Row */}
      <div className="flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#D4A853] to-[#B8860B]">
            <span className="text-xs font-bold text-white">G</span>
          </div>
          <span className="text-lg font-bold text-[#1A1A1A]">GIM</span>
        </div>

        {/* Links */}
        <nav className="flex items-center gap-8">
          <Link href="/docs" className="text-sm text-[#52525B] hover:text-[#1A1A1A]">
            Documentation
          </Link>
          <Link href="/changelog" className="text-sm text-[#52525B] hover:text-[#1A1A1A]">
            Changelog
          </Link>
          <a
            href="https://github.com/your-org/gim"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-[#52525B] hover:text-[#1A1A1A]"
          >
            GitHub
          </a>
          <Link href="/privacy" className="text-sm text-[#52525B] hover:text-[#1A1A1A]">
            Privacy
          </Link>
        </nav>
      </div>

      {/* Divider */}
      <div className="h-px w-full bg-[#D4D0C5]" />

      {/* Bottom Row */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-[#71717A]">
          © 2025 GIM. Open source under MIT License.
        </p>

        {/* Social Links */}
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/your-org/gim"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#71717A] hover:text-[#1A1A1A]"
          >
            <Github className="h-5 w-5" />
          </a>
          <a
            href="https://twitter.com/gim_dev"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#71717A] hover:text-[#1A1A1A]"
          >
            <Twitter className="h-5 w-5" />
          </a>
        </div>
      </div>
    </footer>
  );
}
