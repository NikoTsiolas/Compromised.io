// The seeded synthetic feed points at images on images.example.com, and real captured feeds
// point at publishers' own image hosts. The browser suite answers every request that is not for
// the app itself, so no test ever reaches the network: one synthetic URL gets a real (tiny)
// PNG, everything else an error, which exercises the fallback tile.
import type { Page } from "@playwright/test";

// A 4x3 grey PNG.
export const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAQAAAADCAIAAAA7ljmRAAAAE0lEQVR4nGP4z8DwHwYYYBwGBgB3vQ7yOJ7OXgAAAABJRU5ErkJggg==",
  "base64",
);

const isApp = (url: URL) => url.hostname === "127.0.0.1" || url.hostname === "localhost";

export async function servePublisherImages(page: Page) {
  await page.route(
    (url) => !isApp(url),
    (route) =>
      route.request().url() === "https://images.example.com/synthetic/loads.png"
        ? route.fulfill({ status: 200, contentType: "image/png", body: PNG })
        : route.fulfill({ status: 404, body: "" }),
  );
}
