// Browser seam: the AI summary, its label and the action line (#8). The seed replays synthetic
// model replies for two synthetic items (api/tests/fixtures/synthetic/enrichment-replies.json);
// the real 1Password event has none and stays on rules.
import { offline, expect, test, type Page } from "./test";

offline();

const story = (page: Page, title: string) =>
  page
    .getByRole("article")
    .filter({ has: page.getByRole("link", { name: title, exact: true }) });

test("an enriched event shows its summary labelled as AI and the stated action line", async ({
  page,
}) => {
  await page.goto("/");
  const card = story(page, "[Synthetic test item] Critical Chrome flaw fixed in security update");

  await expect(card).toContainText(
    "AI summarySynthetic summary: a serious flaw in Chrome has been fixed in an update.",
  );
  await expect(card).toContainText(
    "Advice from source Synthetic action: install the latest Chrome update.",
  );
});

test("an enriched event with no stated action shows no action line", async ({ page }) => {
  await page.goto("/");
  const card = story(page, "[Synthetic test item] Windows zero-day exploited in attacks");

  await expect(card).toContainText("AI summary");
  await expect(card).not.toContainText("Advice from source");
});

test("a rules-only event shows no AI label and no action line", async ({ page }) => {
  await page.goto("/");
  const lead = story(page, "1Password customer data stolen after employee GitHub account breach");

  await expect(lead).toBeVisible();
  await expect(lead).not.toContainText("AI summary");
  await expect(lead).not.toContainText("Advice from source");
});
