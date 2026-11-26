// Browser seam: search and filters (#10), from the header on desktop and on a phone. Seed: the
// real BleepingComputer, Security Affairs and The Hacker News captures plus synthetic items
// (playwright.config.ts).

import { offline, expect, test, type Page } from "./test";

offline();

const ONEPASSWORD =
  "1Password customer data stolen after employee GitHub account breach";
const FLIGHT_CENTRE =
  "Australia’s Flight Centre Data Breach Exposes Customer Records and Passport Details";

const results = (page: Page) => page.getByRole("region", { name: "Search results" });
const headlines = (page: Page) => results(page).getByRole("article").getByRole("heading");

test("the header search opens the results for the query", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Open search" }).click();
  await page.getByRole("searchbox", { name: "Search" }).fill("1Password");
  await page.keyboard.press("Enter");

  await expect(page).toHaveURL(/\/search\?q=1Password$/);
  await expect(headlines(page)).toHaveText([ONEPASSWORD]);
  // The same row as the feed: trust label and technical details included.
  await expect(results(page).getByRole("article")).toContainText("Reported by 3 news outlets");
  // The query stays in the page's own field, ready to refine.
  await expect(page.getByRole("searchbox", { name: "Search events" })).toHaveValue("1Password");
});

test("filters combine with the query and with each other", async ({ page }) => {
  await page.goto("/search?q=breach");
  await expect(headlines(page)).toContainText([FLIGHT_CENTRE, ONEPASSWORD]);

  await page.getByLabel("Category", { exact: true }).selectOption({ label: "Data breach" });
  await expect(page).toHaveURL(/category=data_breach/);
  await page.getByLabel("Source", { exact: true }).selectOption({ label: "The Hacker News" });
  await expect(page).toHaveURL(/source=thehackernews/);
  await expect(headlines(page)).toHaveText([ONEPASSWORD]);

  // A date range that ends before the breach leaves nothing, and says so.
  await page.getByLabel("To", { exact: true }).fill("2026-11-01");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page).toHaveURL(/to=2026-11-01/);
  await expect(results(page)).toContainText("No events match");

  await page.getByRole("link", { name: "Clear filters" }).click();
  await expect(page).toHaveURL(/\/search\?q=breach$/);
  await expect(headlines(page)).toContainText([FLIGHT_CENTRE, ONEPASSWORD]);
});

test("hostile text in the query is searched as text and shown as text", async ({ page }) => {
  const hostile = `<img src=x onerror="document.title='owned'"> ' OR 1=1 --`;
  await page.goto(`/search?q=${encodeURIComponent(hostile)}`);
  await expect(results(page)).toContainText("No events match");
  await expect(page.getByRole("searchbox", { name: "Search events" })).toHaveValue(hostile);
  expect(await page.title()).not.toBe("owned");
});

test.describe("on a phone", () => {
  test.use({ viewport: { width: 375, height: 812 }, hasTouch: true, isMobile: true });

  test("the header's search link leads to a search with filters that fit the screen", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Search" }).click();
    await expect(page).toHaveURL(/\/search$/);

    const field = page.getByRole("searchbox", { name: "Search events" });
    await field.fill("Flight Centre");
    await page.getByLabel("Status", { exact: true }).selectOption({ label: "Reported" });
    await expect(page).toHaveURL(/status=reported/);
    await expect(page).toHaveURL(/q=Flight\+Centre/);
    await expect(headlines(page)).toHaveText([FLIGHT_CENTRE]);

    // Nothing runs off the side of the screen.
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });
});

test("the Trending tab lists ranked events or says nothing is trending", async ({ page }) => {
  // The category tabs live in the Feed since #16.
  await page.goto("/feed?tab=trending");
  await expect(
    page
      .getByRole("navigation", { name: "Categories" })
      .getByRole("link", { name: "Trending", exact: true }),
  ).toHaveAttribute("aria-current", "page");
  const region = page.getByRole("region", { name: "Trending posts" });
  // Trending depends on the clock (the last 72 hours), so either state is right here; the API
  // seam checks the order (api/tests/api/test_trending.py).
  await expect(
    region.getByRole("article").first().or(region.getByText("Nothing is trending")),
  ).toBeVisible();
});
