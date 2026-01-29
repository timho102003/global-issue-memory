"use client";

import { Sparkles, Github } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CtaSectionProps {
  onPrimaryClick?: () => void;
  onSecondaryClick?: () => void;
}

/**
 * Final CTA section with responsive layout.
 */
export function CtaSection({ onPrimaryClick, onSecondaryClick }: CtaSectionProps) {
  return (
    <section className="bg-gradient-to-b from-bg-gradient-start to-bg-tertiary px-5 py-16 sm:px-8 sm:py-20 md:py-28 lg:px-12">
      <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-8">
        <h2 className="text-center text-2xl font-bold tracking-tight text-text-primary sm:text-3xl md:text-4xl lg:text-[44px] lg:leading-[1.15]">
          Ready to Join the Community?
        </h2>
        <p className="text-center text-[14px] text-text-secondary sm:text-base md:text-lg">
          Start contributing and help developers everywhere.
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
            <Github className="h-4 w-4" />
            View on GitHub
          </Button>
        </div>

        <p className="text-[13px] text-text-muted">
          Open source. Free forever. Built by the community.
        </p>
      </div>
    </section>
  );
}
