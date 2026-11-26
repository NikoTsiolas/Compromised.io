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

const eventRows = (page: Page) =>
  page.getByRole("list", { name: "Events" }).getByRole("listitem");

test("the All tab lists in-scope events newest first, linking to the publisher", async ({
  page,
}) => {
  await page.goto("/");

  const rows = eventRows(page);
  await expect(rows.getByRole("link")).toHaveText([
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
  await expect(first.locator("time")).toHaveAttribute(
    "datetime",
    "2026-11-25T21:33:33Z",
  );
  await expect(first).toContainText("25 Nov 2026, 21:33 UTC");
  await expect(first).toContainText(/\bago\b/);
});

test("tab links filter the feed through the API", async ({ page }) => {
  await page.goto("/");
  const tabs = page.getByRole("navigation", { name: "Feed tabs" });
  await expect(tabs.getByRole("link")).toHaveText([
    "All",
    "Breaches",
    "Ransomware",
    "Under attack",
    "Update now",
    "Research",
    "Trending",
  ]);
  await expect(tabs.getByRole("link", { name: "All" })).toHaveAttribute(
    "aria-current",
    "page",
  );

  await tabs.getByRole("link", { name: "Research" }).click();
  await expect(page).toHaveURL(/\?tab=research$/);
  await expect(tabs.getByRole("link", { name: "Research" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  await expect(eventRows(page).getByRole("link")).toHaveText([
    "SYS010 malware abuses browser management to spy on Gmail, Outlook",
  ]);

  await tabs.getByRole("link", { name: "Under attack" }).click();
  await expect(page).toHaveURL(/\?tab=under-attack$/);
  await expect(eventRows(page).getByRole("link")).toHaveText([
    SYNTHETIC_ZERO_DAY,
  ]);

  await tabs.getByRole("link", { name: "Breaches" }).click();
  await expect(eventRows(page).getByRole("link")).toHaveText([
    ONEPASSWORD,
    SYNTHETIC_MARKUP,
  ]);

  await tabs.getByRole("link", { name: "Trending" }).click();
  await expect(page.getByText("No events yet.")).toBeVisible();

  await tabs.getByRole("link", { name: "All" }).click();
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
