// Browser seam: the trust label, the 0-100 score and the source names, always together (#7),
// and the "How we score" page stating the formula's numbers. Expected numbers are the anchors in
// docs/wiki/trust-labels-and-score.md, written out by hand. The seed holds the real
// BleepingComputer, Security Affairs and The Hacker News captures plus synthetic items.
import { expect, test, type Page } from "@playwright/test";

const eventRows = (page: Page) =>
  page.getByRole("list", { name: "Events" }).getByRole("listitem");

const eventRow = (page: Page, title: string) =>
  eventRows(page).filter({
    has: page.getByRole("link", { name: title, exact: true }),
  });

test("an event shows its label, score and the outlets counted, together", async ({
  page,
}) => {
  await page.goto("/");
  const row = eventRow(
    page,
    "1Password customer data stolen after employee GitHub account breach",
  );

  await expect(row.getByLabel("Trust")).toHaveText(
    "Reported by 3 news outlets · 70/100 · Sources: BleepingComputer, Security Affairs, The Hacker News",
  );
});

test("no row shows a score without its label and sources", async ({ page }) => {
  await page.goto("/");
  const rows = eventRows(page);
  await expect(rows.first()).toBeVisible();

  for (const row of await rows.all()) {
    const text = await row.innerText();
    if (!text.includes("/100")) continue;
    await expect(row.getByLabel("Trust")).toHaveText(
      /^(Confirmed by|Flaw confirmed by|Reported by \d+ news outlets?|Claimed by attackers, not confirmed|Under investigation|Disputed).* · \d{1,3}\/100 · Sources: .+$/,
    );
  }
});

test("'How we score' states the formula's numbers", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "How we score" }).click();

  await expect(page.getByRole("heading", { level: 1 })).toHaveText("How we score");
  const rules = page.getByRole("list", { name: "Formula" });
  await expect(rules.getByRole("listitem")).toHaveText([
    "Claimed by attackers, with no other coverage: 20.",
    "Reported by one news outlet: 50.",
    "Each additional independent news outlet: +10, up to 80 without official confirmation.",
    "Confirmed by an official source (the affected company, a government agency, or a security company's research team): 90.",
    "Official confirmation plus news coverage: 100.",
    "Disputed or retracted by a later source: 10.",
  ]);
  await expect(
    page.getByRole("row", { name: "Ransomware.live Attacker claim 20" }),
  ).toBeVisible();
  await expect(
    page.getByRole("row", { name: "The Record News outlet 50" }),
  ).toBeVisible();
});
