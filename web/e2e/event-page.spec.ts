// Browser seam: each event's own page (#11). The seed holds the real BleepingComputer, Security
// Affairs and The Hacker News captures, whose 1Password stories group into one event with three
// sources, plus synthetic items (labelled as such in their headlines). Expected times are the
// captures' own pubDate values converted by hand to the reader's zone.
import { offline, expect, test, type Page } from "./test";

offline();

// A zone far from UTC, so the timeline visibly uses the reader's local time and date.
test.use({ timezoneId: "Asia/Tokyo" });

const ONEPASSWORD =
  "1Password customer data stolen after employee GitHub account breach";
const ONEPASSWORD_URL =
  "https://www.bleepingcomputer.com/news/security/1password-customer-data-stolen-after-employee-github-account-breach/";
const CHROME = "[Synthetic test item] Critical Chrome flaw fixed in security update";
const ADOBE = "[Synthetic test item] Adobe confirms data breach exposing customer records";

const story = (page: Page, title: string) =>
  page
    .getByRole("article")
    .filter({ has: page.getByRole("link", { name: title, exact: true }) });

/** Opens an event's page the way a reader does: its "Details" link on the homepage. */
async function openEvent(page: Page, title: string) {
  await page.goto("/");
  await story(page, title).getByRole("link", { name: "Details", exact: true }).click();
  await expect(page).toHaveURL(/\/events\/\d+$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
}

test("a feed row's details link opens the event page; its headline still opens the publisher", async ({
  page,
}) => {
  await page.goto("/");
  const row = story(page, ONEPASSWORD);
  await expect(row.getByRole("link", { name: ONEPASSWORD, exact: true })).toHaveAttribute(
    "href",
    ONEPASSWORD_URL,
  );

  await openEvent(page, ONEPASSWORD);

  // The page's headline is the original one and opens the publisher too.
  const headline = page.getByRole("heading", { level: 1 }).getByRole("link");
  await expect(headline).toHaveAttribute("href", ONEPASSWORD_URL);
  await expect(headline).toHaveAttribute("target", "_blank");
});

test("an event's address is stable: opening it directly shows the same event", async ({
  page,
}) => {
  await openEvent(page, ONEPASSWORD);
  const address = page.url();

  await page.goto(address);

  await expect(page.getByRole("heading", { level: 1 })).toHaveText(ONEPASSWORD);
});

test("the page shows the organization, trust label with score and sources", async ({ page }) => {
  await openEvent(page, ONEPASSWORD);
  const event = page.getByRole("main");

  await expect(event).toContainText("1Password");
  await expect(event.getByLabel("Trust")).toHaveText(
    "Reported by 3 news outlets · 70/100 · Sources: BleepingComputer, Security Affairs, The Hacker News",
  );
});

test("the timeline lists every source in publication order at its original time, in local time", async ({
  page,
}) => {
  await openEvent(page, ONEPASSWORD);
  const timeline = page.getByRole("list", { name: "Timeline" });

  // pubDates: Wed 25 Nov 21:33:33 UTC, Thu 26 Nov 09:42:47 UTC, Thu 26 Nov 16:27:25 +0530.
  await expect(timeline.getByRole("listitem")).toHaveText([
    /^26 Nov 2026, 06:33 GMT\+9 · BleepingComputer.*1Password customer data stolen after employee GitHub account breach/,
    /^26 Nov 2026, 18:42 GMT\+9 · Security Affairs.*1Password Hacked: Customer Names and Emails Copied, Vaults Untouched/,
    /^26 Nov 2026, 19:57 GMT\+9 · The Hacker News.*1Password Hacked, Customer Data and Source Code Stolen in GitHub Account Breach/,
  ]);
  await expect(timeline.locator("time").first()).toHaveAttribute(
    "datetime",
    "2026-11-25T21:33:33Z",
  );
  const links = timeline.getByRole("link");
  await expect(links).toHaveCount(3);
  await expect(links.nth(0)).toHaveAttribute("href", ONEPASSWORD_URL);
  await expect(links.nth(1)).toHaveAttribute("href", /^https:\/\/securityaffairs\.com\//);
  await expect(links.nth(2)).toHaveAttribute("href", /^https:\/\/thehackernews\.com\//);
});

test("the page shows the AI summary with its label, the advice from the source and technical details", async ({
  page,
}) => {
  await openEvent(page, CHROME);
  const event = page.getByRole("main");

  await expect(event).toContainText(
    "AI summarySynthetic summary: a serious flaw in Chrome has been fixed in an update.",
  );
  await expect(event).toContainText(
    "Advice from source Synthetic action: install the latest Chrome update.",
  );
  const details = page.getByRole("region", { name: "Technical details" });
  await expect(details).toContainText("CVE identifiers");
  await expect(details).toContainText("Category");
});

test("a rules-only event has no AI label; its technical details say no CVE was named", async ({
  page,
}) => {
  await openEvent(page, ONEPASSWORD);

  await expect(page.getByRole("main")).not.toContainText("AI summary");
  await expect(page.getByRole("region", { name: "Technical details" })).toContainText(
    "CVE identifiersNone named",
  );
});

test("the publisher's picture is shown with its credit; without one, the logo tile", async ({
  page,
}) => {
  await openEvent(page, ADOBE);
  await expect(page.getByRole("img", { name: "Picture from Dark Reading" })).toBeVisible();
  await expect(page.getByRole("main")).toContainText("Image: Dark Reading");

  // The Hacker News's picture is not served in the suite, so the 1Password tile takes its place.
  await openEvent(page, ONEPASSWORD);
  await expect(page.getByRole("img", { name: /^Picture from/ })).toHaveCount(0);
  await expect(page.getByRole("main")).not.toContainText("Image:");
});

test("the page has a title and description for sharing, from stored text, with no publisher photo", async ({
  page,
}) => {
  await openEvent(page, ADOBE);

  await expect(page).toHaveTitle(`${ADOBE} · Compromised`);
  const meta = (selector: string) => page.locator(`head meta[${selector}]`);
  await expect(meta('name="description"')).toHaveAttribute("content", /\S/);
  await expect(meta('property="og:title"')).toHaveAttribute("content", ADOBE);
  await expect(meta('property="og:description"')).toHaveAttribute("content", /\S/);
  await expect(meta('property="og:type"')).toHaveAttribute("content", "article");
  await expect(meta('property="og:image"')).toHaveCount(0);
  await expect(meta('name="twitter:image"')).toHaveCount(0);
});

test("the description is the AI summary when there is one", async ({ page }) => {
  await openEvent(page, CHROME);

  await expect(page.locator('head meta[name="description"]')).toHaveAttribute(
    "content",
    "Synthetic summary: a serious flaw in Chrome has been fixed in an update.",
  );
});

for (const address of ["/events/999999999", "/events/not-an-event"]) {
  test(`an unknown event (${address}) is a proper not-found page`, async ({ page }) => {
    const response = await page.goto(address);

    expect(response?.status()).toBe(404);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Event not found");
    await expect(page.locator('head meta[name="robots"]')).toHaveAttribute(
      "content",
      /noindex/,
    );
    await page.getByRole("link", { name: "Back to the feed" }).click();
    await expect(page).toHaveURL(/\/$/);
  });
}
