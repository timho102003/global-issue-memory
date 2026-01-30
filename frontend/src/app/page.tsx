"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
  const router = useRouter();

  // "Get Started Free" navigates directly to dashboard (no auth required)
  const goToDashboard = () => {
    router.push("/dashboard");
  };

  // "Join the Community" in header opens sign up modal
  const openSignUp = () => {
    setAuthView("signup");
    setShowAuthModal(true);
  };

  const openGitHub = () => {
    window.open("https://github.com/timho102003/global-issue-memory", "_blank");
  };

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-bg-gradient-start to-bg-gradient-end">
      <Header onCtaClick={openSignUp} />
      <main className="flex-1">
        <Hero onPrimaryClick={goToDashboard} onSecondaryClick={openGitHub} />
        <ProblemSection />
        <SolutionSection />
        <HowItWorks />
        <FeaturesSection />
        <FaqSection />
        <CtaSection onPrimaryClick={goToDashboard} onSecondaryClick={openGitHub} />
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
