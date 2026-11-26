// The seeded synthetic feed points at images on images.example.com. The browser suite answers
// those requests itself, so no test ever reaches the network: one URL gets a real (tiny) PNG,
// every other URL an error, to exercise the fallback tile.
import type { Page } from "@playwright/test";

// A 4x3 grey PNG.
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAQAAAADCAIAAAA7ljmRAAAAE0lEQVR4nGP4z8DwHwYYYBwGBgB3vQ7yOJ7OXgAAAABJRU5ErkJggg==",
  "base64",
);

export async function servePublisherImages(page: Page) {
  await page.route("https://images.example.com/**", (route) =>
    route.request().url().endsWith("/synthetic/loads.png")
      ? route.fulfill({ status: 200, contentType: "image/png", body: PNG })
      : route.fulfill({ status: 404, body: "" }),
  );
}
