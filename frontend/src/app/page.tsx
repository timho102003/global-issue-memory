"use client";

import { useState } from "react";
import {
  Header,
  Hero,
  ProblemSection,
  SolutionSection,
  HowItWorks,
  FeaturesSection,
  FaqSection,
  CtaSection,
  Footer,
} from "@/components/landing";
import { AuthModal } from "@/components/auth";

/**
 * Landing page matching GIM.pen design (Vf7Lq).
 */
export default function LandingPage() {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authView, setAuthView] = useState<"signin" | "signup">("signup");

  const openSignUp = () => {
    setAuthView("signup");
    setShowAuthModal(true);
  };

  const openGitHub = () => {
    window.open("https://github.com/your-org/gim", "_blank");
  };

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-bg-gradient-start to-bg-gradient-end">
      <Header onCtaClick={openSignUp} />
      <main className="flex-1">
        <Hero onPrimaryClick={openSignUp} onSecondaryClick={openGitHub} />
        <ProblemSection />
        <SolutionSection />
        <HowItWorks />
        <FeaturesSection />
        <FaqSection />
        <CtaSection onPrimaryClick={openSignUp} onSecondaryClick={openGitHub} />
      </main>
      <Footer />

      <AuthModal
        open={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        defaultView={authView}
      />
    </div>
  );
}
