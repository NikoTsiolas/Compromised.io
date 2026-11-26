// Captures the design-checkpoint screenshots in docs/design/checkpoint/.
//
//   BASE_URL=http://127.0.0.1:3000 node scripts/capture-checkpoint.mjs
//
// Needs a running web app built with SAMPLE_PREVIEW=1 (for /preview) and an API with real
// ingested events. Full-page images of the real feed and the sample-data preview, each in
// light, dark and at phone width.
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

const base = process.env.BASE_URL ?? "http://127.0.0.1:3000";
const out = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../docs/design/checkpoint",
);
mkdirSync(out, { recursive: true });

const pages = [
  { name: "feed", path: "/" },
  { name: "sample-preview", path: "/preview" },
];
const looks = [
  { name: "light", viewport: { width: 1280, height: 900 }, colorScheme: "light" },
  { name: "dark", viewport: { width: 1280, height: 900 }, colorScheme: "dark" },
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
];

const browser = await chromium.launch();
for (const look of looks) {
  const { name, ...options } = look;
  const context = await browser.newContext({ reducedMotion: "reduce", ...options });
  for (const p of pages) {
    const page = await context.newPage();
    await page.goto(base + p.path, { waitUntil: "networkidle" });
    // Open one row's Technical details so the expand is part of the record.
    const toggle = page.getByRole("button", { name: "Technical details" }).nth(1);
    if (await toggle.count()) await toggle.click();
    await page.waitForTimeout(300);
    const file = path.join(out, `${p.name}-${name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    console.log(path.relative(process.cwd(), file));
    await page.close();
  }
  await context.close();
}
await browser.close();
