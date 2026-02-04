import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Clock, Calendar } from "lucide-react";

/**
 * Page-specific metadata for the blog listing page.
 * Overrides default metadata from root layout.
 */
export const metadata: Metadata = {
  title: "Blog",
  description:
    "Explore ideas, research, and updates on AI-assisted development, community-driven knowledge bases, and the tools that make collaborative coding better.",
  openGraph: {
    title: "Blog | GIM - Global Issue Memory",
    description:
      "Explore ideas, research, and updates on AI-assisted development, community-driven knowledge bases, and the tools that make collaborative coding better.",
    url: "https://usegim.com/blog",
    type: "website",
  },
  twitter: {
    title: "Blog | GIM - Global Issue Memory",
    description:
      "Explore ideas, research, and updates on AI-assisted development, community-driven knowledge bases, and the tools that make collaborative coding better.",
  },
  alternates: {
    canonical: "https://usegim.com/blog",
  },
};

/**
 * Blog post metadata type.
 */
interface BlogPost {
  slug: string;
  title: string;
  description: string;
  date: string;
  readingTime: string;
  category: string;
  featured?: boolean;
}

/**
 * All published blog posts. Add new entries here.
 */
const posts: BlogPost[] = [
  {
    slug: "context-rot",
    title: "Context Rot: The Silent Killer of AI-Assisted Coding",
    description:
      "As your AI assistant's context window fills up, its performance silently degrades. We explore the research, the real-world impact on developer productivity, and what the community can do about it.",
    date: "Feb 1, 2026",
    readingTime: "12 min read",
    category: "Research",
    featured: true,
  },
];

/**
 * Blog listing page with featured hero and post grid.
 */
export default function BlogPage() {
  const featured = posts.find((p) => p.featured);
  const rest = posts.filter((p) => !p.featured);

  return (
    <section className="px-5 py-16 sm:px-8 sm:py-20 md:py-24 lg:px-12">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-14 md:gap-16">
        {/* Page header */}
        <div className="flex flex-col items-center gap-4">
          <span className="text-[11px] font-semibold tracking-[2px] text-accent-gold uppercase">
            Blog
          </span>
          <h1 className="max-w-[700px] text-center text-3xl font-bold tracking-tight text-text-primary sm:text-4xl md:text-5xl md:leading-[1.15]">
            Ideas, Research &amp; Updates
          </h1>
          <p className="max-w-[540px] text-center text-[15px] leading-relaxed text-text-secondary sm:text-base">
            Exploring the frontier of AI-assisted development, community-driven
            knowledge, and the tools that make it work.
          </p>
        </div>

        {/* Featured post hero card */}
        {featured && (
          <Link
            href={`/blog/${featured.slug}`}
            className="group relative flex flex-col overflow-hidden rounded-2xl border border-border-light/80 bg-white shadow-[var(--shadow-card)] transition-all duration-300 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5 md:flex-row"
          >
            {/* Decorative illustration area */}
            <div className="relative flex items-center justify-center bg-gradient-to-br from-bg-tertiary to-bg-highlight p-8 md:w-[45%] md:p-12">
              <FeaturedIllustration />
              <div className="absolute right-4 top-4">
                <span className="rounded-full bg-accent-warm/10 px-3 py-1 text-[11px] font-semibold tracking-wide text-accent-warm uppercase">
                  {featured.category}
                </span>
              </div>
            </div>

            {/* Content */}
            <div className="flex flex-1 flex-col justify-center gap-5 p-6 sm:p-8 md:p-10">
              <div className="flex items-center gap-4 text-[12px] text-text-muted">
                <span className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5" />
                  {featured.date}
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5" />
                  {featured.readingTime}
                </span>
              </div>

              <h2 className="text-xl font-bold tracking-tight text-text-primary transition-colors duration-200 group-hover:text-accent-warm sm:text-2xl md:text-[28px] md:leading-[1.2]">
                {featured.title}
              </h2>

              <p className="text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
                {featured.description}
              </p>

              <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-accent-warm transition-all duration-200 group-hover:gap-2.5">
                Read article
                <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
              </span>
            </div>
          </Link>
        )}

        {/* Post grid (for future posts) */}
        {rest.length > 0 && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {rest.map((post) => (
              <Link
                key={post.slug}
                href={`/blog/${post.slug}`}
                className="group flex flex-col overflow-hidden rounded-2xl border border-border-light/80 bg-white shadow-[var(--shadow-card)] transition-all duration-300 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5"
              >
                <div className="flex h-40 items-center justify-center bg-gradient-to-br from-bg-tertiary to-bg-highlight">
                  <span className="rounded-full bg-accent-warm/10 px-3 py-1 text-[11px] font-semibold tracking-wide text-accent-warm uppercase">
                    {post.category}
                  </span>
                </div>
                <div className="flex flex-1 flex-col gap-3 p-5 sm:p-6">
                  <div className="flex items-center gap-3 text-[12px] text-text-muted">
                    <span>{post.date}</span>
                    <span>{post.readingTime}</span>
                  </div>
                  <h3 className="text-base font-semibold tracking-tight text-text-primary transition-colors duration-200 group-hover:text-accent-warm sm:text-lg">
                    {post.title}
                  </h3>
                  <p className="text-[13px] leading-relaxed text-text-secondary line-clamp-3">
                    {post.description}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Coming soon note when few posts */}
        {posts.length <= 1 && (
          <div className="flex flex-col items-center gap-2 py-4">
            <div className="h-px w-16 bg-gradient-to-r from-transparent via-border-medium to-transparent" />
            <p className="text-[13px] text-text-muted">
              More articles coming soon. Stay tuned.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

/* ─── Featured post illustration (inline SVG) ─── */
function FeaturedIllustration() {
  return (
    <svg
      viewBox="0 0 320 220"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="h-auto w-full max-w-[280px] opacity-90"
      aria-hidden="true"
    >
      {/* Background glow */}
      <circle cx="160" cy="110" r="90" fill="#D4A853" fillOpacity="0.06" />
      <circle cx="160" cy="110" r="60" fill="#D4A853" fillOpacity="0.04" />

      {/* Terminal window */}
      <rect x="60" y="40" width="200" height="140" rx="12" fill="#2D2A26" />
      <rect x="60" y="40" width="200" height="28" rx="12" fill="#3D3A36" />
      <rect x="60" y="56" width="200" height="12" fill="#3D3A36" />
      <circle cx="78" cy="54" r="4" fill="#EF4444" fillOpacity="0.8" />
      <circle cx="92" cy="54" r="4" fill="#F59E0B" fillOpacity="0.8" />
      <circle cx="106" cy="54" r="4" fill="#22C55E" fillOpacity="0.8" />

      {/* Code lines fading out (context rot visual) */}
      <rect x="78" y="80" width="80" height="3" rx="1.5" fill="#D4A853" fillOpacity="0.9" />
      <rect x="78" y="90" width="120" height="3" rx="1.5" fill="#D4A853" fillOpacity="0.7" />
      <rect x="78" y="100" width="95" height="3" rx="1.5" fill="#D4A853" fillOpacity="0.5" />
      <rect x="78" y="110" width="140" height="3" rx="1.5" fill="#D4A853" fillOpacity="0.35" />
      <rect x="78" y="120" width="70" height="3" rx="1.5" fill="#D4A853" fillOpacity="0.2" />
      <rect x="78" y="130" width="110" height="3" rx="1.5" fill="#D4A853" fillOpacity="0.1" />
      <rect x="78" y="140" width="85" height="3" rx="1.5" fill="#D4A853" fillOpacity="0.05" />

      {/* Decay arrow */}
      <path
        d="M240 78 L240 152"
        stroke="#EF4444"
        strokeWidth="1.5"
        strokeDasharray="4 3"
        strokeOpacity="0.5"
      />
      <path
        d="M236 148 L240 156 L244 148"
        stroke="#EF4444"
        strokeWidth="1.5"
        strokeOpacity="0.5"
        fill="none"
      />
      <text x="244" y="86" fill="#EF4444" fillOpacity="0.6" fontSize="8" fontFamily="monospace">
        quality
      </text>
      <text x="244" y="155" fill="#EF4444" fillOpacity="0.4" fontSize="8" fontFamily="monospace">
        decay
      </text>
    </svg>
  );
}
