"use client";

import { useState } from "react";
import { SignInModal } from "./sign-in-modal";
import { SignUpModal } from "./sign-up-modal";

type AuthView = "signin" | "signup";

interface AuthModalProps {
  open: boolean;
  onClose: () => void;
  defaultView?: AuthView;
}

/**
 * Unified Auth Modal that manages switching between Sign In and Sign Up.
 */
export function AuthModal({ open, onClose, defaultView = "signin" }: AuthModalProps) {
  const [view, setView] = useState<AuthView>(defaultView);

  const handleSwitchToSignIn = () => setView("signin");
  const handleSwitchToSignUp = () => setView("signup");

  if (view === "signin") {
    return (
      <SignInModal
        open={open}
        onClose={onClose}
        onSwitchToSignUp={handleSwitchToSignUp}
      />
    );
  }

  return (
    <SignUpModal
      open={open}
      onClose={onClose}
      onSwitchToSignIn={handleSwitchToSignIn}
    />
  );
}
