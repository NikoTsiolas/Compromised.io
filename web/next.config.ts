import type { NextConfig } from "next";

// The sample-data preview (app/preview/page.preview.tsx) is a route only in development or when
// SAMPLE_PREVIEW=1 is set for a build (the browser suite does this). A production build without
// it does not contain the route or its sample values at all.
const samplePreview =
  process.env.NODE_ENV !== "production" || process.env.SAMPLE_PREVIEW === "1";

const nextConfig: NextConfig = {
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
