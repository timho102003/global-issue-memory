import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Documentation | GIM",
  description:
    "Set up Global Issue Memory in your Claude Code environment in just a few steps.",
};

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
