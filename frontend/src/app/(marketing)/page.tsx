"use client";

import { useRouter } from "next/navigation";
import {
  Hero,
  ProblemSection,
  SolutionSection,
  HowItWorks,
  FeaturesSection,
  FaqSection,
  CtaSection,
} from "@/components/landing";

/**
 * Landing page matching GIM.pen design (Vf7Lq).
 */
export default function LandingPage() {
  const router = useRouter();

  const goToDashboard = () => {
    router.push("/dashboard");
  };

  const goToDocs = () => {
    router.push("/docs");
  };

  return (
    <>
      <Hero onPrimaryClick={goToDashboard} onSecondaryClick={goToDocs} />
      <ProblemSection />
      <SolutionSection />
      <HowItWorks />
      <FeaturesSection />
      <FaqSection />
      <CtaSection onPrimaryClick={goToDashboard} onSecondaryClick={goToDocs} />
    </>
  );
}
