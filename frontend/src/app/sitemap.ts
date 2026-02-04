import type { MetadataRoute } from "next";

/**
 * Generate sitemap for search engine indexing.
 * @see https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://usegim.com";

  // Static marketing pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${baseUrl}/blog`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/blog/context-rot`,
      lastModified: new Date("2026-02-01"),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/terms`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.3,
    },
  ];

  // Documentation pages
  const docPages: MetadataRoute.Sitemap = [
    { url: `${baseUrl}/docs`, priority: 0.9 },
    { url: `${baseUrl}/docs/getting-started`, priority: 0.8 },
    { url: `${baseUrl}/docs/getting-started/sign-up`, priority: 0.7 },
    { url: `${baseUrl}/docs/getting-started/find-plugin`, priority: 0.7 },
    { url: `${baseUrl}/docs/getting-started/add-mcp-server`, priority: 0.7 },
    { url: `${baseUrl}/docs/getting-started/authentication`, priority: 0.7 },
    { url: `${baseUrl}/docs/getting-started/verify-installation`, priority: 0.7 },
    { url: `${baseUrl}/docs/getting-started/claude-md-setup`, priority: 0.7 },
    { url: `${baseUrl}/docs/how-it-works`, priority: 0.8 },
    { url: `${baseUrl}/docs/how-it-works/system-design`, priority: 0.6 },
    { url: `${baseUrl}/docs/how-it-works/issue-lifecycle`, priority: 0.6 },
    { url: `${baseUrl}/docs/troubleshooting`, priority: 0.7 },
  ].map((page) => ({
    ...page,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
  }));

  return [...staticPages, ...docPages];
}
