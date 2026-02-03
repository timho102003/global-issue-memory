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
  title: "GIM - Global Issue Memory",
  description: "Build Together. Fix Once. Help Everyone. A collaborative knowledge base where AI coding assistants share verified fixes.",
  metadataBase: new URL("https://usegim.com"),
  keywords: ["AI", "coding assistant", "bug fixes", "developer tools", "MCP", "Claude", "Cursor", "Windsurf"],
  authors: [{ name: "GIM Team" }],
  creator: "GIM",
  publisher: "GIM",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: "GIM - Global Issue Memory",
    description: "Build Together. Fix Once. Help Everyone. A collaborative knowledge base where AI coding assistants share verified fixes.",
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
    description: "Build Together. Fix Once. Help Everyone. A collaborative knowledge base where AI coding assistants share verified fixes.",
    images: ["/assets/og-image.png"],
    creator: "@usegim",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geist.variable} ${jetbrainsMono.variable} antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
