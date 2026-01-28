"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  onCtaClick?: () => void;
}

/**
 * Landing page header matching GIM.pen design.
 */
export function Header({ onCtaClick }: HeaderProps) {
  return (
    <header className="flex h-20 items-center justify-between px-20">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-gradient-to-br from-[#D4A853] to-[#B8860B]">
          <span className="text-sm font-bold text-white">G</span>
        </div>
        <span className="text-2xl font-bold text-[#1A1A1A]">GIM</span>
      </Link>

      {/* Navigation */}
      <nav className="flex items-center gap-10">
        <a href="#how-it-works" className="text-[15px] text-[#52525B] hover:text-[#1A1A1A]">
          How It Works
        </a>
        <a href="#features" className="text-[15px] text-[#52525B] hover:text-[#1A1A1A]">
          Features
        </a>
        <a href="#faq" className="text-[15px] text-[#52525B] hover:text-[#1A1A1A]">
          FAQ
        </a>
      </nav>

      {/* CTA Button */}
      <Button
        onClick={onCtaClick}
        className="rounded-3xl bg-[#1A1A1A] px-6 py-3 text-[15px] font-semibold text-white hover:bg-[#2A2A2A]"
      >
        Join the Community
      </Button>
    </header>
  );
}
