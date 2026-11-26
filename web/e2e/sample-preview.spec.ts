// The sample-data preview shows the components later tickets fill, with invented values, under a
// banner that cannot be missed. It is built only when SAMPLE_PREVIEW=1 (never in production).
import { PNG } from "./images";
import { offline, expect, test, type Page } from "./test";

// The sample claim carries a picture on purpose; serve a real one, so only the rule can hide it.
const serveClaimPicture = (page: Page) =>
  page.route("https://images.example.com/sample/claim-screenshot.png", (route) =>
    route.fulfill({ status: 200, contentType: "image/png", body: PNG }),
  );

offline();

test("the preview is labelled as sample data and shows every populated field", async ({
  page,
}) => {
  await page.goto("/preview");

  const notice = page.getByRole("note", { name: "Sample data notice" });
  await expect(notice).toContainText("Sample data");
  await expect(notice).toContainText("None of it is real.");
  await page.mouse.wheel(0, 1500);
  await expect(notice).toBeInViewport();
  const rows = page.getByRole("article");
  await expect(rows.first()).toBeVisible();
  await expect(
    page.getByText("Claimed by attackers, not confirmed").filter({ visible: true }).first(),
  ).toBeVisible();
  await expect(page.getByText("AI summary").first()).toBeVisible();
  await expect(page.getByText("Advice from source").first()).toBeVisible();
  await expect(
    page.getByText("Confirmed by the company").filter({ visible: true }).first(),
  ).toBeVisible();

  const headlines = await rows.getByRole("heading").getByRole("link").all();
  expect(headlines.length).toBeGreaterThan(0);
  for (const link of headlines) {
    expect(await link.getAttribute("href")).toMatch(/^https:\/\/example\.com\//);
  }
});

test("the exploitation chart highlights spike months and reads out each month by keyboard", async ({
  page,
}) => {
  await page.goto("/preview");
  const chart = page.getByRole("region", { name: "Exploited flaws by month" });
  const months = chart.locator("[data-month]");
  await expect(months).toHaveCount(12);
  const spikes = chart.locator("[data-month][data-spike]");
  expect(await spikes.count()).toBeGreaterThan(0);
  // Spike months carry their value as a visible label, so colour is never the only signal.
  await expect(spikes.first()).toContainText(/\d+/);

  // One tab stop; arrow keys move between months; the tooltip follows focus.
  await chart.getByRole("button", { name: /^November 2026/ }).focus();
  const tooltip = chart.getByRole("tooltip");
  await expect(tooltip).toContainText("November 2026");
  await page.keyboard.press("Home");
  await expect(chart.getByRole("button", { name: /^December 2025/ })).toBeFocused();
  await expect(tooltip).toContainText("December 2025");

  const spike = await spikes.first().getAttribute("data-month");
  await page.keyboard.press("End");
  const spikeButton = chart.getByRole("button", { name: new RegExp(`^${spike}.*spike`) });
  await spikeButton.focus();
  await expect(tooltip).toContainText("Notable");

  // Every value is also available as a table.
  await expect(chart.getByRole("table")).toHaveCount(1);
  // Only the frequency view exists until the other two are confirmed.
  await expect(chart.getByRole("radio")).toHaveCount(0);
});

test("the chart tooltip also appears on hover", async ({ page }) => {
  await page.goto("/preview");
  const chart = page.getByRole("region", { name: "Exploited flaws by month" });
  await chart.locator("[data-month][data-spike]").first().hover();
  await expect(chart.getByRole("tooltip")).toContainText("Notable");
});

test("the Feed preview carries the same banner and shows Option A posts with sample values", async ({
  page,
}) => {
  await serveClaimPicture(page);
  await page.goto("/preview/feed");
  await expect(page.getByRole("note", { name: "Sample data notice" })).toContainText(
    "None of it is real.",
  );
  const posts = page.getByRole("region", { name: "All posts" }).getByRole("article");
  await expect(posts.first()).toBeVisible();
  await expect(page.getByText("Advice from source").first()).toBeVisible();
  // Attacker claims never show a photo: the tile, whatever a source sent.
  const claim = posts.filter({ has: page.locator('[data-slot=trust][data-status="claimed"]') }).first();
  await expect(claim.locator("[data-slot=aspect-ratio] img")).toHaveCount(0);
  await expect(claim.locator("[data-slot=aspect-ratio] [data-media]")).toHaveCount(1);
  for (const link of await posts.getByRole("heading").getByRole("link").all()) {
    expect(await link.getAttribute("href")).toMatch(/^https:\/\/example\.com\//);
  }
});

test("on Featured too, an attacker claim gets the tile even when a source sent a picture", async ({
  page,
}) => {
  await serveClaimPicture(page);
  await page.goto("/preview");
  const claim = page
    .getByRole("article")
    .filter({ has: page.locator('[data-slot=trust][data-status="claimed"]') })
    .first();
  await expect(claim.locator("[data-slot=aspect-ratio] img")).toHaveCount(0);
  await expect(claim.locator("[data-slot=aspect-ratio] [data-media]")).toHaveCount(1);
});
