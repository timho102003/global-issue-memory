"use client";

import { useState } from "react";
import { Header, Footer } from "@/components/landing";
import { AuthModal } from "@/components/auth";

/**
 * Shared shell for marketing pages (Header + Footer + AuthModal).
 */
export function MarketingShell({ children }: { children: React.ReactNode }) {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authView, setAuthView] = useState<"signin" | "signup">("signup");

  const openSignUp = () => {
    setAuthView("signup");
    setShowAuthModal(true);
  };

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-bg-gradient-start to-bg-gradient-end">
      <Header onCtaClick={openSignUp} />
      <main className="flex-1">{children}</main>
      <Footer />
      <AuthModal
        open={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        defaultView={authView}
      />
    </div>
  );
}
