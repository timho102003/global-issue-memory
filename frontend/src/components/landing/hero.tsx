"use client";

import { Sparkles, Github, ArrowRight, Users, CheckCircle, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeroProps {
  onPrimaryClick?: () => void;
  onSecondaryClick?: () => void;
}

/**
 * Hero section matching GIM.pen design.
 */
export function Hero({ onPrimaryClick, onSecondaryClick }: HeroProps) {
  return (
    <section className="flex flex-col items-center gap-10 px-20 py-[100px] pb-[120px]">
      {/* Badge */}
      <div className="flex items-center gap-2 rounded-full border border-[#E5E0D5] bg-white px-4 py-2">
        <Sparkles className="h-3.5 w-3.5 text-[#D4A853]" />
        <span className="text-[13px] font-medium text-[#1A1A1A]">
          Open Source Community
        </span>
      </div>

      {/* Headline */}
      <h1 className="max-w-[1000px] text-center text-[56px] font-bold leading-[1.1] text-[#1A1A1A]">
        Build Together. Fix Once. Help Everyone.
      </h1>

      {/* Subline */}
      <p className="max-w-[700px] text-center text-xl leading-[1.5] text-[#52525B]">
        GIM is an open community where developers share verified solutions. When your AI
        solves something new, it helps the next developer instantly.
      </p>

      {/* CTAs */}
      <div className="flex items-center gap-4">
        <Button
          onClick={onPrimaryClick}
          className="flex items-center gap-2 rounded-3xl bg-[#D4A853] px-8 py-4 text-base font-semibold text-white hover:bg-[#C49843]"
        >
          <Sparkles className="h-4 w-4" />
          Get Started Free
        </Button>
        <Button
          onClick={onSecondaryClick}
          variant="outline"
          className="flex items-center gap-2 rounded-3xl border-[#D4D0C5] px-8 py-4 text-base font-semibold text-[#1A1A1A] hover:bg-[#F5F0E6]"
        >
          <Github className="h-4 w-4" />
          View on GitHub
        </Button>
      </div>

      {/* Trust Badges */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-1.5">
          <Users className="h-4 w-4 text-[#52525B]" />
          <span className="text-sm text-[#52525B]">2,500+ developers</span>
        </div>
        <div className="flex items-center gap-1.5">
          <CheckCircle className="h-4 w-4 text-[#52525B]" />
          <span className="text-sm text-[#52525B]">10,000+ fixes shared</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Shield className="h-4 w-4 text-[#52525B]" />
          <span className="text-sm text-[#52525B]">Privacy-first</span>
        </div>
      </div>
    </section>
  );
}
