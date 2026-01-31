import { MarketingShell } from "@/components/layout/marketing-shell";

/**
 * Layout for public marketing pages — shared Header, Footer & AuthModal.
 */
export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MarketingShell>{children}</MarketingShell>;
}
