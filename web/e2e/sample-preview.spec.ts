// The sample-data preview shows the components later tickets fill, with invented values, under a
// banner that cannot be missed. It is built only when SAMPLE_PREVIEW=1 (never in production).
import { expect, test } from "@playwright/test";

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
  await expect(
    page.getByText("Confirmed by the company").filter({ visible: true }).first(),
  ).toBeVisible();

  const headlines = await rows.getByRole("heading").getByRole("link").all();
  expect(headlines.length).toBeGreaterThan(0);
  for (const link of headlines) {
    expect(await link.getAttribute("href")).toMatch(
      /^https:\/\/example\.com\//,
    );
  }
});
