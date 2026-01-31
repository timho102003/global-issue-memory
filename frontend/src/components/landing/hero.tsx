"use client";

import { Sparkles, BookOpen, Github, Users, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeroProps {
  onPrimaryClick?: () => void;
  onSecondaryClick?: () => void;
}

/**
 * Hero section with responsive typography and proper container.
 */
export function Hero({ onPrimaryClick, onSecondaryClick }: HeroProps) {
  return (
    <section className="px-5 py-16 sm:px-8 sm:py-20 md:py-28 lg:px-12">
      <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-8 md:gap-10">
        {/* Badge */}
        <div className="flex items-center gap-2 rounded-full border border-border-light bg-white/80 px-4 py-2 shadow-[var(--shadow-xs)]">
          <Sparkles className="h-3.5 w-3.5 text-accent-warm" />
          <span className="text-[13px] font-medium text-text-primary">
            Open Source Community
          </span>
        </div>

        {/* Headline */}
        <h1 className="max-w-[900px] text-center text-3xl font-bold leading-[1.12] tracking-tight text-text-primary sm:text-4xl md:text-5xl lg:text-[44px]">
          Build Together. Fix Once. Help Everyone.
        </h1>

        {/* Subline */}
        <p className="max-w-[620px] text-center text-base leading-relaxed text-text-secondary sm:text-lg md:text-xl">
          Global Issue Memory (GIM) is an open community where developers share verified solutions. When your AI
          solves something new, it helps the next developer instantly.
        </p>

        {/* CTAs */}
        <div className="flex flex-col items-center gap-3 sm:flex-row sm:gap-4">
          <Button
            onClick={onPrimaryClick}
            className="w-full bg-accent-warm px-8 py-4 text-[15px] font-semibold text-white shadow-md hover:bg-accent-gold sm:w-auto"
          >
            <Sparkles className="h-4 w-4" />
            Get Started Free
          </Button>
          <Button
            onClick={onSecondaryClick}
            variant="outline"
            className="w-full border-border-light px-8 py-4 text-[15px] font-semibold text-text-primary hover:bg-bg-muted sm:w-auto"
          >
            <BookOpen className="h-4 w-4" />
            How to Install
          </Button>
        </div>

        {/* Trust Badges */}
        <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6">
          <div className="flex items-center gap-1.5">
            <Github className="h-4 w-4 text-text-muted" />
            <span className="text-[13px] text-text-secondary">Open Source</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Users className="h-4 w-4 text-text-muted" />
            <span className="text-[13px] text-text-secondary">Community-Driven</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Shield className="h-4 w-4 text-text-muted" />
            <span className="text-[13px] text-text-secondary">Privacy-first</span>
          </div>
        </div>
      </div>
    </section>
  );
}
