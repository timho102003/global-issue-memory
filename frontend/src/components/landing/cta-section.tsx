"use client";

import { Sparkles, Github } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CtaSectionProps {
  onPrimaryClick?: () => void;
  onSecondaryClick?: () => void;
}

/**
 * Final CTA section matching GIM.pen design.
 */
export function CtaSection({ onPrimaryClick, onSecondaryClick }: CtaSectionProps) {
  return (
    <section className="flex flex-col items-center gap-10 bg-gradient-to-b from-[#FDF8E8] to-[#F5F0E6] px-20 py-[120px]">
      <h2 className="text-center text-[48px] font-bold text-[#1A1A1A]">
        Ready to Join the Community?
      </h2>
      <p className="text-center text-xl text-[#52525B]">
        Start contributing and help developers everywhere.
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

      <p className="text-sm text-[#9CA3AF]">
        Open source. Free forever. Built by the community.
      </p>
    </section>
  );
}
