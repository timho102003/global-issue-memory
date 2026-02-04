import type { Metadata } from "next";
import { Geist, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://usegim.com"),
  title: {
    default: "GIM - Global Issue Memory",
    template: "%s | GIM",
  },
  description:
    "Build Together. Fix Once. Help Everyone. A shared knowledge base for vibe coding and AI pair programming. Search verified bug fixes, error solutions, and coding patterns used by Claude Code, Cursor, Windsurf, and other AI coding assistants via MCP.",
  keywords: [
    // Core product terms
    "GIM",
    "Global Issue Memory",
    "bug fix database",
    "error solutions",
    "coding knowledge base",
    // Vibe coding & AI coding trends
    "vibe coding",
    "agentic coding",
    "AI pair programming",
    "AI coding assistant",
    "AI code editor",
    "AI IDE",
    "generative coding",
    // Protocol & integration
    "MCP",
    "Model Context Protocol",
    "MCP server",
    // Popular AI coding tools
    "Claude Code",
    "Claude",
    "Cursor",
    "Windsurf",
    "GitHub Copilot",
    "Cline",
    "Aider",
    "Replit",
    // Developer actions
    "code generation",
    "AI-assisted development",
    "autonomous coding agent",
    "prompt-to-code",
    "developer productivity",
    "developer tools",
    // Problem solving
    "bug fixes",
    "error resolution",
    "debugging",
    "code review",
  ],
  authors: [{ name: "GIM Team" }],
  creator: "GIM",
  publisher: "GIM",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: "GIM - Global Issue Memory",
    description:
      "Build Together. Fix Once. Help Everyone. A collaborative knowledge base where AI coding assistants share verified fixes.",
    url: "https://usegim.com",
    siteName: "GIM - Global Issue Memory",
    images: [
      {
        url: "/assets/og-image.png",
        width: 1200,
        height: 630,
        alt: "GIM - Global Issue Memory: Build Together. Fix Once. Help Everyone.",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "GIM - Global Issue Memory",
    description:
      "Build Together. Fix Once. Help Everyone. A collaborative knowledge base where AI coding assistants share verified fixes.",
    images: ["/assets/og-image.png"],
    creator: "@usegim",
  },
  alternates: {
    canonical: "https://usegim.com",
  },
};

/**
 * JSON-LD structured data for Organization and WebSite schemas.
 * Helps search engines understand the site's identity and enables rich results.
 * Note: dangerouslySetInnerHTML is safe here as jsonLd is a static, hardcoded object
 * with no user input - this is the standard Next.js pattern for JSON-LD injection.
 */
const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://usegim.com/#organization",
      name: "GIM - Global Issue Memory",
      url: "https://usegim.com",
      logo: {
        "@type": "ImageObject",
        url: "https://usegim.com/assets/logo.png",
        width: 512,
        height: 512,
      },
      description:
        "A collaborative knowledge base for vibe coding and AI pair programming. Enables AI coding assistants like Claude Code, Cursor, and Windsurf to share verified bug fixes via MCP (Model Context Protocol).",
      sameAs: ["https://twitter.com/usegim", "https://github.com/usegim"],
    },
    {
      "@type": "WebSite",
      "@id": "https://usegim.com/#website",
      url: "https://usegim.com",
      name: "GIM - Global Issue Memory",
      publisher: {
        "@id": "https://usegim.com/#organization",
      },
      description:
        "Build Together. Fix Once. Help Everyone. The shared knowledge base for vibe coding - search verified bug fixes, error solutions, and coding patterns from the AI coding community.",
      potentialAction: {
        "@type": "SearchAction",
        target: {
          "@type": "EntryPoint",
          urlTemplate: "https://usegim.com/dashboard/issues?q={search_term_string}",
        },
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@type": "SoftwareApplication",
      "@id": "https://usegim.com/#application",
      name: "GIM",
      alternateName: "Global Issue Memory",
      applicationCategory: "DeveloperApplication",
      applicationSubCategory: "AI Coding Tool",
      operatingSystem: "Cross-platform",
      description:
        "MCP server for AI coding assistants. Integrates with Claude Code, Cursor, Windsurf, GitHub Copilot, Cline, and other vibe coding tools to search, submit, and confirm bug fixes from a global knowledge base.",
      featureList: [
        "Search verified bug fixes",
        "Submit new issue solutions",
        "Confirm fix effectiveness",
        "MCP (Model Context Protocol) integration",
        "Works with Claude Code, Cursor, Windsurf",
      ],
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
        availability: "https://schema.org/InStock",
      },
      publisher: {
        "@id": "https://usegim.com/#organization",
      },
      keywords:
        "vibe coding, MCP server, Model Context Protocol, AI coding assistant, bug fix database, Claude Code, Cursor, Windsurf, agentic coding",
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body
        className={`${geist.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
