import type { MetadataRoute } from "next";

/**
 * Generate robots.txt to control search engine crawling.
 * @see https://nextjs.org/docs/app/api-reference/file-conventions/metadata/robots
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/dashboard/", "/api/", "/auth/"],
      },
    ],
    sitemap: "https://usegim.com/sitemap.xml",
    host: "https://usegim.com",
  };
}
