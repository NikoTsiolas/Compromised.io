// Browser seam: the widget rail beside the feed. Readers can reorder the widgets and move the
// rail to the other side, by pointer or keyboard; the arrangement is kept in this browser only.
// No widget except source status has a real API yet (#15), so the others show a quiet empty
// state here and are populated only on the sample preview.
import { expect, test, type Page } from "@playwright/test";

const rail = (page: Page) => page.getByRole("complementary", { name: "Widgets" });
const widgetTitles = (page: Page) => rail(page).getByRole("heading", { level: 2 });
const feed = (page: Page) => page.getByRole("region", { name: "All events" });

const DEFAULT_ORDER = [
  "Exploited flaws by month",
  "Recently exploited",
  "Most reported organisations",
  "Source status",
];

test("the rail sits to the right of the feed with the default widgets", async ({ page }) => {
  await page.goto("/");

  await expect(widgetTitles(page)).toHaveText(DEFAULT_ORDER);
  const railBox = (await rail(page).boundingBox())!;
  const feedBox = (await feed(page).boundingBox())!;
  expect(railBox.x).toBeGreaterThan(feedBox.x + feedBox.width - 1);
});

test("widgets without a real data source say so quietly, with no invented figures", async ({
  page,
}) => {
  await page.goto("/");

  const chart = rail(page).getByRole("region", { name: "Exploited flaws by month" });
  await expect(chart).toContainText("No figures yet");
  await expect(chart.locator("[data-month]")).toHaveCount(0);
  await expect(
    rail(page).getByRole("region", { name: "Most reported organisations" }),
  ).toContainText("No figures yet");
});

test("source status shows each source's last successful check", async ({ page }) => {
  await page.goto("/");

  const sources = rail(page).getByRole("list", { name: "Sources" }).getByRole("listitem");
  await expect(sources).toHaveCount(10);
  const bleeping = sources.filter({ hasText: "BleepingComputer" });
  await expect(bleeping).toHaveAttribute("data-state", "ok");
  await expect(bleeping.locator("time")).toHaveAttribute(
    "datetime",
    /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z$/,
  );
  await expect(sources.filter({ hasText: "The Record" })).toContainText("Not checked yet");
});

test("a widget moves by keyboard and stays there after a reload", async ({ page }) => {
  await page.goto("/");

  const grip = rail(page).getByRole("button", { name: "Move Source status" });
  await grip.focus();
  await page.keyboard.press("ArrowUp");
  await expect(widgetTitles(page)).toHaveText([
    "Exploited flaws by month",
    "Recently exploited",
    "Source status",
    "Most reported organisations",
  ]);
  await expect(grip).toBeFocused();
  await expect(page.getByRole("status").filter({ hasText: "Source status moved to position 3 of 4" })).toHaveCount(1);

  await page.keyboard.press("Home");
  await expect(widgetTitles(page).first()).toHaveText("Source status");

  await page.reload();
  await expect(widgetTitles(page)).toHaveText([
    "Source status",
    "Exploited flaws by month",
    "Recently exploited",
    "Most reported organisations",
  ]);
});

test("a widget can be dragged to a new place by its handle", async ({ page }) => {
  await page.goto("/");

  const grip = rail(page).getByRole("button", { name: "Move Most reported organisations" });
  const target = rail(page).getByRole("region", { name: "Exploited flaws by month" });
  const from = (await grip.boundingBox())!;
  const to = (await target.boundingBox())!;

  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2);
  await page.mouse.down();
  await page.mouse.move(from.x + from.width / 2, to.y + 4, { steps: 12 });
  await page.mouse.up();

  await expect(widgetTitles(page).first()).toHaveText("Most reported organisations");
  await page.reload();
  await expect(widgetTitles(page).first()).toHaveText("Most reported organisations");
});

test("the rail moves to the left side and is remembered", async ({ page }) => {
  await page.goto("/");

  await rail(page).getByRole("button", { name: "Move widgets to the left" }).click();
  let railBox = (await rail(page).boundingBox())!;
  let feedBox = (await feed(page).boundingBox())!;
  expect(railBox.x + railBox.width).toBeLessThanOrEqual(feedBox.x + 1);

  await page.reload();
  railBox = (await rail(page).boundingBox())!;
  feedBox = (await feed(page).boundingBox())!;
  expect(railBox.x + railBox.width).toBeLessThanOrEqual(feedBox.x + 1);
  await expect(
    rail(page).getByRole("button", { name: "Move widgets to the right" }),
  ).toBeVisible();
});

test("the page works when the browser refuses local storage", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new DOMException("blocked", "SecurityError");
      },
    });
  });
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");

  await expect(widgetTitles(page)).toHaveText(DEFAULT_ORDER);
  await rail(page).getByRole("button", { name: "Move Source status" }).focus();
  await page.keyboard.press("Home");
  await expect(widgetTitles(page).first()).toHaveText("Source status");
  expect(errors).toEqual([]);
});

test("the header shows that ingestion is live", async ({ page }) => {
  await page.goto("/");

  const indicator = page.getByRole("banner").getByRole("status");
  await expect(indicator).toContainText("Live");
  await expect(indicator).toHaveAttribute("data-status", "live");
});
