// Browser seam: the running web app against the API and a database seeded with the real
// BleepingComputer, Security Affairs and The Hacker News captures plus synthetic items (see
// api/tests/fixtures/*/README.md). All three outlets covered the 1Password breach.
// Times are checked in New York so that "local time" is visibly not UTC.
import { offline, expect, test, type Page } from "./test";

offline();


test.use({ timezoneId: "America/New_York" });

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
const SYNTHETIC_ADOBE =
  "[Synthetic test item] Adobe confirms data breach exposing customer records";
const SYNTHETIC_SLACK =
  "[Synthetic test item] Slack data breach exposes workspace messages";

const eventRows = (page: Page) => page.getByRole("article");
const headlines = (page: Page) => eventRows(page).getByRole("heading");
const featured = (page: Page) => page.getByRole("region", { name: "Featured" });
const lead = (page: Page) => featured(page).getByRole("article").first();

test("the All tab lists in-scope events newest first, linking to the publisher", async ({
  page,
}) => {
  await page.goto("/");

  // The featured lead first, then its cards, then the feed (each in publication order).
  await expect(headlines(page)).toHaveText([
    ONEPASSWORD,
    FLIGHT_CENTRE,
    SYNTHETIC_ZERO_DAY,
    SYNTHETIC_CRITICAL,
    SYNTHETIC_MARKUP,
    SYNTHETIC_ADOBE,
    SYNTHETIC_SLACK,
  ]);

  const headline = page.getByRole("link", { name: ONEPASSWORD });
  await expect(headline).toHaveAttribute(
    "href",
    "https://www.bleepingcomputer.com/news/security/1password-customer-data-stolen-after-employee-github-account-breach/",
  );
  await expect(headline).toHaveAttribute("target", "_blank");
  await expect(headline).toHaveAttribute("rel", "noopener noreferrer");
});

test("the featured section leads with a recent named event with a picture, then three cards", async ({
  page,
}) => {
  await page.goto("/");

  const story = lead(page);
  await expect(story.getByRole("heading", { level: 2 })).toHaveText(ONEPASSWORD);
  await expect(story).toContainText("1Password");
  await expect(story).toContainText("Data breach");
  await expect(story).toContainText("BleepingComputer");
  // Flight Centre is newer but has no picture; 1Password, a few hours older, has one (from
  // The Hacker News's feed), so it leads.
  await expect(story).toContainText("3 sources");
  await expect(story).toContainText(/Published .*ago/);

  const cards = featured(page).getByRole("list", { name: "More top stories" });
  await expect(cards.getByRole("heading")).toHaveText([
    FLIGHT_CENTRE,
    SYNTHETIC_ZERO_DAY,
    SYNTHETIC_CRITICAL,
  ]);

  // The feed below continues after the featured stories and never repeats them.
  const feed = page.getByRole("region", { name: "All events" });
  await expect(feed.getByRole("heading", { level: 3 })).toHaveText([
    SYNTHETIC_MARKUP,
    SYNTHETIC_ADOBE,
    SYNTHETIC_SLACK,
  ]);
});

test("an event covered by several outlets names them all under Technical details", async ({
  page,
}) => {
  await page.goto("/");
  const story = lead(page);
  await expect(story).toContainText("BleepingComputer +2 sources");

  await story.getByRole("button", { name: "Technical details" }).click();
  const security = story.getByRole("link", {
    name: "1Password Hacked: Customer Names and Emails Copied, Vaults Untouched",
  });
  await expect(security).toHaveAttribute(
    "href",
    "https://securityaffairs.com/204031/cyber-crime/1password-hacked-customer-names-and-emails-copied-vaults-untouched.html",
  );
  await expect(security).toHaveAttribute("rel", "noopener noreferrer");
  await expect(
    story.getByRole("link", {
      name: "1Password Hacked, Customer Data and Source Code Stolen in GitHub Account Breach",
    }),
  ).toBeVisible();

  // A single-source event names its one publisher and no others.
  const single = eventRows(page).filter({ hasText: FLIGHT_CENTRE });
  await expect(single).not.toContainText("+");
});

test("times are shown in the reader's own time zone without hydration errors", async ({
  page,
}) => {
  const problems: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") problems.push(m.text());
  });
  page.on("pageerror", (e) => problems.push(e.message));
  await page.goto("/");

  const time = lead(page).locator("time").first();
  await expect(time).toHaveAttribute("datetime", "2026-11-25T21:33:33Z");
  // 21:33 UTC is 16:33 in New York.
  await expect(time).toContainText("16:33");
  await expect(time).not.toContainText("UTC");

  await lead(page).getByRole("button", { name: "Technical details" }).click();
  await expect(lead(page).getByText("25 Nov 2026, 16:33 EST")).toBeVisible();
  expect(problems.filter((p) => /hydrat/i.test(p))).toEqual([]);
});

test("a publisher's own image is loaded from the publisher, credited, with no referrer", async ({
  page,
}) => {
  await page.goto("/");

  const adobe = eventRows(page).filter({ hasText: SYNTHETIC_ADOBE });
  const image = adobe.getByRole("img");
  // Pictures below the fold load lazily, when the reader gets near them.
  await adobe.scrollIntoViewIfNeeded();
  await expect(image).toHaveAttribute(
    "src",
    "https://images.example.com/synthetic/loads.png",
  );
  await expect(image).toHaveAttribute("referrerpolicy", "no-referrer");
  await expect
    .poll(() => image.evaluate((el: HTMLImageElement) => el.naturalWidth))
    .toBeGreaterThan(0);
  await expect(adobe.getByText("Image: Dark Reading")).toBeVisible();
});

test("an event whose image is broken or missing gets a designed tile instead", async ({
  page,
}) => {
  await page.goto("/");

  // Broken image URL: the lettermark tile replaces it and the credit goes with it.
  const slack = eventRows(page).filter({ hasText: SYNTHETIC_SLACK });
  const tile = slack.locator("[data-media]");
  await expect(tile).toHaveAttribute("data-media", "lettermark");
  await expect(tile).toHaveText("S");
  await expect(slack.locator("img")).toHaveCount(0);
  await expect(slack.getByText(/^Image:/)).toHaveCount(0);

  // No image in the feed, and a logo the catalog can resolve: the company's logo.
  await expect(lead(page).locator("[data-media]")).toHaveAttribute(
    "data-media",
    "logo",
  );
  await expect(
    lead(page).getByRole("img", { name: "1Password logo" }),
  ).toBeVisible();

  // No image and no logo: a lettermark.
  const windows = eventRows(page).filter({ hasText: SYNTHETIC_ZERO_DAY });
  await expect(windows.locator("[data-media]")).toHaveAttribute(
    "data-media",
    "lettermark",
  );
  await expect(windows.locator("[data-media]")).toHaveText("W");
});

test("type is Helvetica Neue first, with monospace for times", async ({
  page,
}) => {
  await page.goto("/");
  const first = lead(page);

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

  // Trust is filled now (#7): the API's own label, never a placeholder or an invented value.
  await expect(lead(page)).not.toContainText("Not yet assessed");
  await expect(lead(page).getByLabel("Trust")).toContainText("Reported by 3 news outlets");
  // CVEs and the attack vector are still to come: quiet empty states under the details.
  await lead(page).getByRole("button", { name: "Technical details" }).click();
  await expect(lead(page)).toContainText("Not extracted yet");
  await expect(lead(page)).toContainText("Not identified yet");
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
  await expect(featured(page)).toHaveCount(0);
  await expect(headlines(page)).toHaveText([
    "SYS010 malware abuses browser management to spy on Gmail, Outlook",
  ]);

  await tab("Under attack").click();
  await expect(page).toHaveURL(/\?tab=under-attack$/);
  await expect(headlines(page)).toHaveText([SYNTHETIC_ZERO_DAY]);

  await tab("Breaches").click();
  await expect(headlines(page)).toHaveText([
    FLIGHT_CENTRE,
    ONEPASSWORD,
    SYNTHETIC_MARKUP,
    SYNTHETIC_ADOBE,
    SYNTHETIC_SLACK,
  ]);

  await tab("Trending").click();
  await expect(eventRows(page)).toHaveCount(0);
  await expect(page.getByText("Nothing under Trending yet")).toBeVisible();

  await tab("All").click();
  await expect(page).toHaveURL(/\/$/);
  await expect(eventRows(page)).toHaveCount(7);
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

test("technical details expand inline under the story and collapse again", async ({
  page,
}) => {
  await page.goto("/");
  const first = lead(page);
  const toggle = first.getByRole("button", { name: "Technical details" });

  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(first.getByText("CVE identifiers")).toBeHidden();

  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(first.getByText("CVE identifiers")).toBeVisible();
  const source = first.getByRole("link", { name: ONEPASSWORD }).last();
  await expect(source).toHaveAttribute("rel", "noopener noreferrer");

  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(first.getByText("CVE identifiers")).toBeHidden();
});

test("the lead headline fades in word by word, and not at all under reduced motion", async ({
  page,
}) => {
  const words = () =>
    lead(page)
      .getByRole("heading", { level: 2 })
      .locator("[data-fade-word]");
  const animation = () =>
    words()
      .first()
      .evaluate((el) => getComputedStyle(el).animationName);

  await page.goto("/");
  await expect(words().first()).toBeVisible();
  expect(await animation()).not.toBe("none");
  // Ordinary feed rows never fade.
  const row = page
    .getByRole("region", { name: "All events" })
    .getByRole("article")
    .first();
  await expect(row.locator("[data-fade-word]")).toHaveCount(0);

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload();
  expect(await animation()).toBe("none");
  await expect(lead(page).getByRole("heading", { level: 2 })).toHaveText(
    ONEPASSWORD,
  );
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
  expect(await background()).toBe("rgb(255, 255, 255)");

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

test.describe("when the operating system prefers dark", () => {
  test.use({ colorScheme: "dark" });

  test("a first-time visitor still gets the white page", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).not.toHaveClass(/\bdark\b/);
    expect(
      await page.evaluate(() => getComputedStyle(document.body).backgroundColor),
    ).toBe("rgb(255, 255, 255)");
    await expect(page.getByRole("switch", { name: "Dark theme" })).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });
});

test.describe("at phone width", () => {
  test.use({ viewport: { width: 375, height: 812 }, hasTouch: true });

  test("featured stories, then the widgets, then the feed, all within the screen", async ({
    page,
  }) => {
    await page.goto("/");

    const overflow = await page.evaluate(
      () =>
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth,
    );
    expect(overflow).toBe(0);

    const top = async (role: "region" | "complementary", name: string) =>
      (await page.getByRole(role, { name }).boundingBox())!.y;
    const featuredTop = await top("region", "Featured");
    const widgetsTop = await top("complementary", "Widgets");
    const feedTop = await top("region", "All events");
    expect(featuredTop).toBeLessThan(widgetsTop);
    expect(widgetsTop).toBeLessThan(feedTop);

    // Widgets stack and are not draggable on phones.
    await expect(
      page.getByRole("button", { name: /^Move / }).filter({ visible: true }),
    ).toHaveCount(0);

    await expect(page.getByRole("link", { name: "Search" })).toBeVisible();
    await expect(
      page.getByRole("switch", { name: "Dark theme" }),
    ).toBeVisible();

    const tabs = page.getByRole("tablist", { name: "Sections" });
    const scrolls = await tabs.evaluate(
      (el) => el.parentElement!.scrollWidth > el.parentElement!.clientWidth,
    );
    expect(scrolls).toBe(true);

    const toggle = lead(page).getByRole("button", {
      name: "Technical details",
    });
    const box = await toggle.boundingBox();
    expect(box!.height).toBeGreaterThanOrEqual(44);
    await toggle.tap();
    await expect(lead(page).getByText("CVE identifiers")).toBeVisible();
  });
});

test("the content security policy lets pictures load only over https, with no referrer", async ({
  page,
}) => {
  const response = await page.goto("/");
  const csp = response!.headers()["content-security-policy"];
  const imgSrc = csp.split(";").map((d) => d.trim()).find((d) => d.startsWith("img-src"));
  expect(imgSrc).toBe("img-src 'self' data: https:");
  expect(csp).toContain("object-src 'none'");
  expect(csp).toContain("frame-ancestors 'none'");
  expect(response!.headers()["referrer-policy"]).toBe("no-referrer");
});
