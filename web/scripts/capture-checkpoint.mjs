// Captures the design-checkpoint screenshots in docs/design/checkpoint/.
//
//   BASE_URL=http://127.0.0.1:3000 node scripts/capture-checkpoint.mjs
//   BASE_URL=... EVENT_PATH=/events/3 ONLY=event LOOKS=light,dark,phone-light,phone-dark node ...
//
// EVENT_PATH adds one event's page (#11) as "event"; SEARCH_PATH (default "/search") sets the
// search page's query (#10); ONLY and LOOKS keep just the named pages and looks.
// Needs a running web app built with SAMPLE_PREVIEW=1 (for /preview and /preview/feed) and an
// API with real ingested events. Full-page images of Featured, the Feed and search, real and
// sample, each at
// desktop, phone and tablet width in light and dark. OUT_DIR writes them elsewhere (to review
// before committing). Times are shown as a reader in London would see them.
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

const base = process.env.BASE_URL ?? "http://127.0.0.1:3000";
const out =
  process.env.OUT_DIR ??
  path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../docs/design/checkpoint");
mkdirSync(out, { recursive: true });

const only = (list, names) =>
  names ? list.filter((x) => names.split(",").includes(x.name)) : list;
// Featured and the Feed (#16), on the real feed and on the sample-data preview; search (#10) and
// one event page (#11) on the real feed.
const pages = only(
  [
    { name: "featured", path: "/" },
    { name: "feed", path: "/feed" },
    { name: "search", path: process.env.SEARCH_PATH ?? "/search" },
    { name: "sample-featured", path: "/preview" },
    { name: "sample-feed", path: "/preview/feed" },
    ...(process.env.EVENT_PATH ? [{ name: "event", path: process.env.EVENT_PATH }] : []),
  ],
  process.env.ONLY,
);
const looks = only([
  { name: "light", viewport: { width: 1440, height: 900 }, colorScheme: "light" },
  { name: "dark", viewport: { width: 1440, height: 900 }, colorScheme: "dark" },
  {
    name: "phone-light",
    viewport: { width: 390, height: 844 },
    colorScheme: "light",
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 2,
  },
  {
    name: "phone-dark",
    viewport: { width: 390, height: 844 },
    colorScheme: "dark",
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 2,
  },
  { name: "tablet-light", viewport: { width: 820, height: 1180 }, colorScheme: "light" },
  { name: "tablet-dark", viewport: { width: 820, height: 1180 }, colorScheme: "dark" },
], process.env.LOOKS);

const browser = await chromium.launch();
for (const look of looks) {
  const { name, ...options } = look;
  const context = await browser.newContext({
    reducedMotion: "reduce",
    timezoneId: "Europe/London",
    ...options,
  });
  // Light is the default for every visitor whatever the system setting, so the dark captures
  // choose dark as the theme switch does (next-themes keeps it under "theme").
  const theme = name.endsWith("dark") ? "dark" : "light";
  await context.addInitScript((t) => {
    try {
      localStorage.setItem("theme", t);
    } catch {}
  }, theme);
  for (const p of pages) {
    const page = await context.newPage();
    await page.goto(base + p.path, { waitUntil: "networkidle" });
    // Hydrated: the UTC fallbacks have been replaced by the reader's local times.
    await page.waitForFunction(
      () => ![...document.querySelectorAll("time")].some((t) => t.textContent?.includes("UTC")),
      null,
      { timeout: 30_000 },
    );
    // Open one story's technical details so the expand is part of the record.
    const toggle = page
      .getByRole("region", { name: /(events|posts)$/ })
      .getByRole("button", { name: /^(Technical details|Details)$/ })
      .first();
    if ((await toggle.count()) && (await toggle.isVisible())) await toggle.click();
    // Let lazy pictures below the fold load before the full-page capture.
    await page.evaluate(async () => {
      for (const img of document.querySelectorAll("img")) img.loading = "eager";
      await Promise.all(
        [...document.images].map((img) =>
          img.complete ? null : new Promise((r) => img.addEventListener("load", r, { once: true }) || img.addEventListener("error", r, { once: true })),
        ),
      );
    });
    await page.waitForTimeout(400);
    const file = path.join(out, `${p.name}-${name}.png`);
    // Grow the viewport to the whole page instead of a scrolling full-page capture, so sticky
    // bars stay at the top where a reader sees them.
    const height = await page.evaluate(() => document.documentElement.scrollHeight);
    await page.setViewportSize({ width: options.viewport.width, height });
    await page.waitForTimeout(200);
    await page.screenshot({ path: file });
    await page.setViewportSize(options.viewport);
    console.log(path.relative(process.cwd(), file));
    await page.close();
  }
  await context.close();
}
await browser.close();
