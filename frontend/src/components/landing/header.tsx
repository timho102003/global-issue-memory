"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  onCtaClick?: () => void;
}

/**
 * Landing page header with sticky blur and responsive mobile menu.
 */
export function Header({ onCtaClick }: HeaderProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-md bg-bg-gradient-start/80">
      <div className="relative mx-auto flex h-16 max-w-[1200px] items-center justify-between px-5 sm:px-8 lg:px-12">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-80">
          <Image src="/logos/gim.svg" alt="GIM" width={36} height={36} className="h-9 w-9" />
          <span className="hidden text-[14px] font-light tracking-wide text-text-primary sm:inline">Global Issue Memory</span>
          <span className="text-[14px] font-light tracking-wide text-text-primary sm:hidden">GIM</span>
        </Link>

        {/* Desktop Navigation — absolutely centered */}
        <nav className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-8 md:flex">
          <a href="/#how-it-works" className="text-[13px] font-medium text-text-secondary transition-colors hover:text-text-primary">
            How It Works
          </a>
          <a href="/#features" className="text-[13px] font-medium text-text-secondary transition-colors hover:text-text-primary">
            Features
          </a>
          <a href="/#faq" className="text-[13px] font-medium text-text-secondary transition-colors hover:text-text-primary">
            FAQ
          </a>
          <Link href="/docs" className="text-[13px] font-medium text-text-secondary transition-colors hover:text-text-primary">
            Docs
          </Link>
        </nav>

        {/* Desktop CTA */}
        <Button
          onClick={onCtaClick}
          size="sm"
          className="hidden md:inline-flex"
        >
          Join the Community
        </Button>

        {/* Mobile Menu Toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-text-secondary transition-colors hover:bg-black/[0.04] hover:text-text-primary md:hidden"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="border-t border-border-light/60 bg-white/95 backdrop-blur-md md:hidden">
          <div className="mx-auto flex max-w-[1200px] flex-col gap-1 px-5 py-4 sm:px-8">
            <a
              href="/#how-it-works"
              onClick={() => setMobileOpen(false)}
              className="rounded-lg px-4 py-2.5 text-[14px] font-medium text-text-secondary transition-colors hover:bg-bg-muted hover:text-text-primary"
            >
              How It Works
            </a>
            <a
              href="/#features"
              onClick={() => setMobileOpen(false)}
              className="rounded-lg px-4 py-2.5 text-[14px] font-medium text-text-secondary transition-colors hover:bg-bg-muted hover:text-text-primary"
            >
              Features
            </a>
            <a
              href="/#faq"
              onClick={() => setMobileOpen(false)}
              className="rounded-lg px-4 py-2.5 text-[14px] font-medium text-text-secondary transition-colors hover:bg-bg-muted hover:text-text-primary"
            >
              FAQ
            </a>
            <Link
              href="/docs"
              onClick={() => setMobileOpen(false)}
              className="rounded-lg px-4 py-2.5 text-[14px] font-medium text-text-secondary transition-colors hover:bg-bg-muted hover:text-text-primary"
            >
              Docs
            </Link>
            <div className="mt-2 px-4">
              <Button onClick={onCtaClick} size="sm" className="w-full">
                Join the Community
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Bottom border */}
      <div className="mx-auto max-w-[1200px] px-5 sm:px-8 lg:px-12">
        <div className="h-px bg-gradient-to-r from-transparent via-border-light to-transparent" />
      </div>
    </header>
  );
}
