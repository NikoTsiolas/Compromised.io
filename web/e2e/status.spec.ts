// Browser seam: the live ingestion indicator and each source's last successful check.
// The seed records one successful BleepingComputer check; every other source is unchecked.
import { expect, test } from "@playwright/test";

test("the header shows that ingestion is live", async ({ page }) => {
  await page.goto("/");

  const indicator = page.getByRole("banner").getByRole("status");
  await expect(indicator).toHaveText("Live");
  await expect(indicator).toHaveAttribute("data-status", "live");
});

test("each source shows when it was last checked successfully", async ({
  page,
}) => {
  await page.goto("/");

  const sources = page
    .getByRole("list", { name: "Sources" })
    .getByRole("listitem");
  await expect(sources).toHaveCount(10);

  const bleeping = sources.filter({ hasText: "BleepingComputer" });
  await expect(bleeping).toHaveAttribute("data-state", "ok");
  await expect(bleeping).toContainText("Last checked");
  await expect(bleeping.locator("time")).toHaveAttribute(
    "datetime",
    /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z$/,
  );
  await expect(bleeping).toContainText(/just now|minute/);

  const record = sources.filter({ hasText: "The Record" });
  await expect(record).toHaveAttribute("data-state", "pending");
  await expect(record).toContainText("Not checked yet");
});
