// Browser seam: the running web app against the API and a database seeded with the real
// BleepingComputer, Security Affairs and The Hacker News captures plus synthetic items (see
// api/tests/fixtures/*/README.md). All three outlets covered the 1Password breach.
import { expect, test, type Page } from "@playwright/test";

const ONEPASSWORD =
  "1Password customer data stolen after employee GitHub account breach";
const FLIGHT_CENTRE =
  "Australia’s Flight Centre Data Breach Exposes Customer Records and Passport Details";
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
    FLIGHT_CENTRE,
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

  const first = rows.nth(1);
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
    FLIGHT_CENTRE,
    ONEPASSWORD,
    SYNTHETIC_MARKUP,
  ]);

  await tabs.getByRole("link", { name: "Trending" }).click();
  await expect(page.getByText("No events yet.")).toBeVisible();

  await tabs.getByRole("link", { name: "All" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(eventRows(page)).toHaveCount(5);
});

test("an event covered by several outlets shows its other sources", async ({
  page,
}) => {
  await page.goto("/");

  const row = eventRows(page).filter({ hasText: ONEPASSWORD });
  await expect(row).toContainText("3 sources");
  await row.getByText("3 sources").click();

  const others = row.getByRole("list", { name: "Other sources" });
  await expect(others.getByRole("link")).toHaveText([
    "Security Affairs: 1Password Hacked: Customer Names and Emails Copied, Vaults Untouched",
    "The Hacker News: 1Password Hacked, Customer Data and Source Code Stolen in GitHub Account Breach",
  ]);
  await expect(
    others.getByRole("link", { name: /^Security Affairs/ }),
  ).toHaveAttribute(
    "href",
    "https://securityaffairs.com/204031/cyber-crime/1password-hacked-customer-names-and-emails-copied-vaults-untouched.html",
  );

  // A single-source event has nothing to expand.
  await expect(
    eventRows(page).filter({ hasText: FLIGHT_CENTRE }),
  ).not.toContainText("sources");
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
