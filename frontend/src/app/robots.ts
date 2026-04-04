import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/settings", "/onboard"],
    },
    sitemap: "https://housematch.io/sitemap.xml",
  };
}
