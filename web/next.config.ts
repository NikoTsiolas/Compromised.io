import type { NextConfig } from "next";

// The sample-data preview (app/preview/page.preview.tsx) is a route only in development or when
// SAMPLE_PREVIEW=1 is set for a build (the browser suite does this). A production build without
// it does not contain the route or its sample values at all.
const samplePreview =
  process.env.NODE_ENV !== "production" || process.env.SAMPLE_PREVIEW === "1";

// Content security policy, sent as a header. Nonces are not used: Next.js applies them only to
// fully dynamic pages, and this app uses partial prerendering, so inline scripts (the theme and
// widget-arrangement scripts that run before first paint) need 'unsafe-inline'. Pictures are
// publishers' own images, loaded by the reader's browser from whichever https host the publisher
// names, so img-src allows any https origin and nothing over plain http.
const isDev = process.env.NODE_ENV !== "production";
const contentSecurityPolicy = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: https:",
  "font-src 'self'",
  `connect-src 'self'${isDev ? " ws: wss:" : ""}`,
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "upgrade-insecure-requests",
].join("; ");

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: contentSecurityPolicy },
          // No page or picture request tells a publisher which page the reader came from.
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "X-Content-Type-Options", value: "nosniff" },
        ],
      },
    ];
  },
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  pageExtensions: samplePreview
    ? ["preview.tsx", "tsx", "ts", "jsx", "js"]
    : ["tsx", "ts", "jsx", "js"],
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
