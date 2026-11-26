// Browser seam: the running web app against the API and a database seeded with the real
// BleepingComputer capture plus synthetic items (see api/tests/fixtures/*/README.md).
import { expect, test, type Page } from "@playwright/test";

const ONEPASSWORD =
  "1Password customer data stolen after employee GitHub account breach";
const SYNTHETIC_MARKUP =
  "[Synthetic test item] Builds < 2.4 & AT&T breach renders as text";
const SYNTHETIC_ZERO_DAY =
  "[Synthetic test item] Windows zero-day exploited in attacks";
const SYNTHETIC_CRITICAL =
  "[Synthetic test item] Critical Chrome flaw fixed in security update";

const eventRows = (page: Page) => page.getByRole("article");
const headlines = (page: Page) => eventRows(page).getByRole("heading");

test("the All tab lists in-scope events newest first, linking to the publisher", async ({
  page,
}) => {
  await page.goto("/");

  const rows = eventRows(page);
  await expect(headlines(page)).toHaveText([
    ONEPASSWORD,
    SYNTHETIC_ZERO_DAY,
    SYNTHETIC_CRITICAL,
    SYNTHETIC_MARKUP,
  ]);

  const headline = page.getByRole("link", { name: ONEPASSWORD });
  await expect(headline).toHaveAttribute(
    "href",
    "https://www.bleepingcomputer.com/news/security/1password-customer-data-stolen-after-employee-github-account-breach/",
  );
  await expect(headline).toHaveAttribute("target", "_blank");
  await expect(headline).toHaveAttribute("rel", "noopener noreferrer");

  const first = rows.nth(0);
  await expect(first).toContainText("1Password");
  await expect(first).toContainText("Data breach");
  await expect(first).toContainText("BleepingComputer");
  const time = first.locator("time").first();
  await expect(time).toHaveAttribute("datetime", "2026-11-25T21:33:33Z");
  await expect(time).toContainText("21:33");
  await expect(first).toContainText(/ ago|yesterday/);
});

test("type is Helvetica Neue first, with monospace for times", async ({
  page,
}) => {
  await page.goto("/");
  const first = page.getByRole("article").first();

  const headlineFont = await first
    .getByRole("heading")
    .evaluate((el) => getComputedStyle(el).fontFamily);
  expect(headlineFont).toMatch(/^"Helvetica Neue"/);

  const timeFont = await first
    .locator("time")
    .first()
    .evaluate((el) => getComputedStyle(el).fontFamily);
  expect(timeFont).toMatch(/monospace/);
});

test("fields that later tickets fill show a quiet empty state, never invented values", async ({
  page,
}) => {
  await page.goto("/");
  const first = page.getByRole("article").first();

  await expect(first).toContainText("Not yet assessed");
  await expect(first).not.toContainText("/100");
  await expect(page.getByText("Sample data")).toHaveCount(0);
});

test("section tabs come from the API, each with its own URL, and filter the feed", async ({
  page,
}) => {
  await page.goto("/");
  const tab = (name: string) => page.getByRole("tab", { name });
  await expect(page.getByRole("tab")).toHaveText([
    "All",
    "Breaches",
    "Ransomware",
    "Under attack",
    "Update now",
    "Research",
    "Trending",
  ]);
  await expect(tab("All")).toHaveAttribute("aria-selected", "true");

  await tab("Research").click();
  await expect(page).toHaveURL(/\?tab=research$/);
  await expect(tab("Research")).toHaveAttribute("aria-selected", "true");
  await expect(headlines(page)).toHaveText([
    "SYS010 malware abuses browser management to spy on Gmail, Outlook",
  ]);

  await tab("Under attack").click();
  await expect(page).toHaveURL(/\?tab=under-attack$/);
  await expect(headlines(page)).toHaveText([SYNTHETIC_ZERO_DAY]);

  await tab("Breaches").click();
  await expect(headlines(page)).toHaveText([ONEPASSWORD, SYNTHETIC_MARKUP]);

  await tab("Trending").click();
  await expect(eventRows(page)).toHaveCount(0);
  await expect(page.getByText("Nothing under Trending yet")).toBeVisible();

  await tab("All").click();
  await expect(page).toHaveURL(/\/$/);
  await expect(eventRows(page)).toHaveCount(4);
});

test("text from the API is rendered as text, never as markup", async ({
  page,
}) => {
  await page.goto("/");

  await expect(
    page.getByRole("link", { name: SYNTHETIC_MARKUP, exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => (window as { __injected?: number }).__injected),
  ).toBeUndefined();
});

test("technical details expand inline under the row and collapse again", async ({
  page,
}) => {
  await page.goto("/");
  const first = page.getByRole("article").first();
  const toggle = first.getByRole("button", { name: "Technical details" });

  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(first.getByText("CVE identifiers")).toBeHidden();

  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(first.getByText("CVE identifiers")).toBeVisible();
  await expect(first.getByText("25 Nov 2026, 21:33 UTC")).toBeVisible();
  const source = first.getByRole("link", { name: ONEPASSWORD }).last();
  await expect(source).toHaveAttribute("rel", "noopener noreferrer");

  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(first.getByText("CVE identifiers")).toBeHidden();
});

test("the theme switch moves between light and dark and is remembered", async ({
  page,
}) => {
  await page.goto("/");
  const html = page.locator("html");
  const toggle = page.getByRole("switch", { name: "Dark theme" });
  const background = () =>
    page.evaluate(() => getComputedStyle(document.body).backgroundColor);

  await expect(toggle).toHaveAttribute("aria-checked", "false");
  expect(await background()).toBe("rgb(246, 245, 241)");

  await toggle.click();
  await expect(html).toHaveClass(/\bdark\b/);
  await expect(toggle).toHaveAttribute("aria-checked", "true");
  expect(await background()).toBe("rgb(17, 17, 17)");

  await page.reload();
  await expect(html).toHaveClass(/\bdark\b/);
  await expect(toggle).toHaveAttribute("aria-checked", "true");

  await toggle.click();
  await expect(html).not.toHaveClass(/\bdark\b/);
});

test.describe("at phone width", () => {
  test.use({ viewport: { width: 375, height: 812 }, hasTouch: true });

  test("the feed fits the screen, tabs scroll sideways and rows still expand", async ({
    page,
  }) => {
    await page.goto("/");

    const overflow = await page.evaluate(
      () =>
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth,
    );
    expect(overflow).toBe(0);

    const first = page.getByRole("article").first();
    await expect(
      first.getByRole("link", { name: ONEPASSWORD }).first(),
    ).toBeVisible();
    await expect(
      first.getByText("Not yet assessed").filter({ visible: true }),
    ).toHaveCount(1);
    await expect(page.getByRole("link", { name: "Search" })).toBeVisible();
    await expect(
      page.getByRole("switch", { name: "Dark theme" }),
    ).toBeVisible();

    const tabs = page.getByRole("tablist", { name: "Sections" });
    const scrolls = await tabs.evaluate(
      (el) => el.parentElement!.scrollWidth > el.parentElement!.clientWidth,
    );
    expect(scrolls).toBe(true);

    const toggle = first.getByRole("button", { name: "Technical details" });
    const box = await toggle.boundingBox();
    expect(box!.height).toBeGreaterThanOrEqual(44);
    await toggle.tap();
    await expect(first.getByText("CVE identifiers")).toBeVisible();
  });
});
