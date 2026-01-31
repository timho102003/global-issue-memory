import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms & Privacy | GIM",
  description:
    "How GIM works, what we collect, and your rights as a user.",
};

export default function TermsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
