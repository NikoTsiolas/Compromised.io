// Browser seam: the page feels smooth because nothing jumps. Pictures fade in over a box that
// was reserved before they arrived, and cumulative layout shift stays well under the 0.1 that
// counts as "good". The measured values are printed for the design report.
import { offline, expect, test, type Page } from "./test";

offline();


async function cumulativeLayoutShift(page: Page): Promise<number> {
  await page.addInitScript(() => {
    (window as unknown as { __cls: number }).__cls = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries() as (PerformanceEntry & {
        value: number;
        hadRecentInput: boolean;
      })[]) {
        if (!entry.hadRecentInput) (window as unknown as { __cls: number }).__cls += entry.value;
      }
    }).observe({ type: "layout-shift", buffered: true });
  });
  await page.goto("/", { waitUntil: "networkidle" });
  // Scroll through the page so every lazy picture loads, then come back up.
  const height = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < height; y += 400) {
    await page.mouse.wheel(0, 400);
    await page.waitForTimeout(60);
  }
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(800);
  return page.evaluate(() => (window as unknown as { __cls: number }).__cls);
}

test("the homepage barely shifts while it loads on desktop", async ({ page }, info) => {
  const cls = await cumulativeLayoutShift(page);
  info.annotations.push({ type: "CLS desktop", description: cls.toFixed(4) });
  console.log(`CLS desktop: ${cls.toFixed(4)}`);
  expect(cls).toBeLessThan(0.02);
});

test.describe("on a phone", () => {
  test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });

  test("the homepage barely shifts while it loads", async ({ page }, info) => {
    const cls = await cumulativeLayoutShift(page);
    info.annotations.push({ type: "CLS phone", description: cls.toFixed(4) });
    console.log(`CLS phone: ${cls.toFixed(4)}`);
    expect(cls).toBeLessThan(0.02);
  });
});

test("a picture fades in over a box reserved before it arrives", async ({ page }) => {
  let release!: () => void;
  const held = new Promise<void>((r) => (release = r));
  await page.route("https://images.example.com/**", async (route) => {
    await held;
    await route.fulfill({ status: 404, body: "" });
  });
  await page.goto("/");

  const media = page.getByRole("article").filter({ hasText: "Adobe" }).locator("[data-slot=aspect-ratio]");
  const box = await media.boundingBox();
  expect(box!.height).toBeGreaterThan(50);
  const image = media.locator("img");
  expect(await image.evaluate((el) => getComputedStyle(el).opacity)).toBe("0");
  expect(await image.evaluate((el) => getComputedStyle(el).transitionProperty)).toContain("opacity");

  release();
  // Broken: the tile takes the same box, so nothing around it moves.
  await expect(media.locator("[data-media]")).toBeVisible();
  expect((await media.boundingBox())!.height).toBe(box!.height);
});

test("hover and focus states ease rather than snap, from one set of motion tokens", async ({
  page,
}) => {
  await page.goto("/");
  const link = page.getByRole("article").first().getByRole("heading").getByRole("link");
  const transition = await link.evaluate((el) => getComputedStyle(el).transitionDuration);
  expect(transition).not.toBe("0s");
  const tokens = await page.evaluate(() => {
    const s = getComputedStyle(document.documentElement);
    return ["--motion-fast", "--motion-base", "--motion-slow"].map((t) => s.getPropertyValue(t).trim());
  });
  expect(tokens.every(Boolean)).toBe(true);

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload();
  expect(
    await page
      .getByRole("article")
      .first()
      .getByRole("heading")
      .getByRole("link")
      .evaluate((el) => getComputedStyle(el).transitionDuration),
  ).toBe("0s");
});
