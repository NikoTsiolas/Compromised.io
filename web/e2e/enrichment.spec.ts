// Browser seam: the AI summary, its label and the action line (#8). The seed replays synthetic
// model replies for two synthetic items (api/tests/fixtures/synthetic/enrichment-replies.json);
// the real 1Password event has none and stays on rules.
import { expect, test, type Page } from "@playwright/test";

const eventRow = (page: Page, title: string) =>
  page
    .getByRole("list", { name: "Events" })
    .getByRole("listitem")
    .filter({ has: page.getByRole("link", { name: title, exact: true }) });

test("an enriched event shows its summary labelled as AI and the stated action line", async ({
  page,
}) => {
  await page.goto("/");
  const row = eventRow(
    page,
    "[Synthetic test item] Critical Chrome flaw fixed in security update",
  );

  await expect(row).toContainText(
    "AI summary: Synthetic summary: a serious flaw in Chrome has been fixed in an update.",
  );
  await expect(row).toContainText(
    "Action: Synthetic action: install the latest Chrome update.",
  );
});

test("an enriched event with no stated action shows no action line", async ({ page }) => {
  await page.goto("/");
  const row = eventRow(page, "[Synthetic test item] Windows zero-day exploited in attacks");

  await expect(row).toContainText("AI summary:");
  await expect(row).not.toContainText("Action:");
});

test("a rules-only event shows no AI label and no action line", async ({ page }) => {
  await page.goto("/");
  const row = eventRow(
    page,
    "1Password customer data stolen after employee GitHub account breach",
  );

  await expect(row).toBeVisible();
  await expect(row).not.toContainText("AI summary");
  await expect(row).not.toContainText("Action:");
});
