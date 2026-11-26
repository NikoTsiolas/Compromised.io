// Browser seam: the running web app against the API and a database seeded with the real
// BleepingComputer capture plus one synthetic item (see api/tests/fixtures/*/README.md).
import { expect, test } from "@playwright/test";

const NEWEST =
  "SYS010 malware abuses browser management to spy on Gmail, Outlook";

test("the feed lists real events newest first, linking to the publisher", async ({
  page,
}) => {
  await page.goto("/");

  const rows = page.getByRole("listitem");
  await expect(rows).toHaveCount(4);
  await expect(rows.nth(0).getByRole("link")).toHaveText(NEWEST);
  await expect(rows.nth(2).getByRole("link")).toHaveText(
    "1Password customer data stolen after employee GitHub account breach",
  );

  const headline = page.getByRole("link", { name: NEWEST });
  await expect(headline).toHaveAttribute(
    "href",
    "https://www.bleepingcomputer.com/news/security/sys010-malware-abuses-browser-management-to-spy-on-gmail-outlook/",
  );
  await expect(headline).toHaveAttribute("target", "_blank");
  await expect(headline).toHaveAttribute("rel", "noopener noreferrer");

  const first = rows.nth(0);
  await expect(first).toContainText("BleepingComputer");
  await expect(first.locator("time")).toHaveAttribute(
    "datetime",
    "2026-11-26T11:50:17Z",
  );
  await expect(first).toContainText("26 Nov 2026, 11:50 UTC");
  await expect(first).toContainText(/\bago\b/);
});

test("text from the API is rendered as text, never as markup", async ({
  page,
}) => {
  await page.goto("/");

  await expect(
    page.getByRole("link", {
      name: "[Synthetic test item] Builds < 2.4 & AT&T render as text",
      exact: true,
    }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => (window as { __injected?: number }).__injected),
  ).toBeUndefined();
});
