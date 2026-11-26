// Browser seam: the Feed tab (#16). Option A's timeline posts inside Option C's shell: categories
// and a browser-kept Watching list on the left, posts in the middle, widgets on the right; on
// phones a bottom tab bar. Same seeded database as feed.spec.ts (real BleepingComputer, Security
// Affairs and The Hacker News captures plus synthetic items).
import { offline, expect, test, type Page } from "./test";

offline();

test.use({ timezoneId: "America/New_York" });

const ONEPASSWORD =
  "1Password customer data stolen after employee GitHub account breach";
const FLIGHT_CENTRE =
  "Australia’s Flight Centre Data Breach Exposes Customer Records and Passport Details";
const SYNTHETIC_ZERO_DAY = "[Synthetic test item] Windows zero-day exploited in attacks";
const SYNTHETIC_CRITICAL = "[Synthetic test item] Critical Chrome flaw fixed in security update";
const SYNTHETIC_MARKUP = "[Synthetic test item] Builds < 2.4 & AT&T breach renders as text";
const SYNTHETIC_ADOBE =
  "[Synthetic test item] Adobe confirms data breach exposing customer records";
const SYNTHETIC_SLACK = "[Synthetic test item] Slack data breach exposes workspace messages";

const ALL_IN_ORDER = [
  FLIGHT_CENTRE,
  ONEPASSWORD,
  SYNTHETIC_ZERO_DAY,
  SYNTHETIC_CRITICAL,
  SYNTHETIC_MARKUP,
  SYNTHETIC_ADOBE,
  SYNTHETIC_SLACK,
];

const posts = (page: Page) => page.getByRole("region", { name: /posts$/ }).getByRole("article");
const post = (page: Page, headline: string) =>
  posts(page).filter({ has: page.getByRole("link", { name: headline, exact: true }) });
const primaryNav = (page: Page) => page.getByRole("navigation", { name: "Primary" });

test("the header reaches Featured and the Feed, each with its own URL", async ({ page }) => {
  await page.goto("/");
  await expect(primaryNav(page).getByRole("link", { name: "Featured" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  await primaryNav(page).getByRole("link", { name: "Feed" }).click();
  await expect(page).toHaveURL(/\/feed$/);
  await expect(primaryNav(page).getByRole("link", { name: "Feed" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  // Every event, newest first, as posts; nothing is held back for a featured section.
  await expect(posts(page).getByRole("heading")).toHaveText(ALL_IN_ORDER);

  await primaryNav(page).getByRole("link", { name: "Featured" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("region", { name: "Featured" })).toBeVisible();
});

test("Featured no longer carries the category tabs; the Feed does", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("tab")).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Categories" })).toHaveCount(0);

  await page.goto("/feed");
  await expect(
    page.getByRole("navigation", { name: "Categories" }).getByRole("link"),
  ).toHaveText(["All", "Breaches", "Ransomware", "Under attack", "Update now", "Research", "Trending"]);
});

test("a post follows Option A: avatar, company line, headline, summary, picture, trust, actions", async ({
  page,
}) => {
  await page.goto("/feed");
  const chrome = post(page, SYNTHETIC_CRITICAL);

  // The affected company as avatar, then company · category · local time on one line.
  await expect(chrome.locator("[data-avatar]")).toHaveAttribute("data-avatar", /logo|lettermark/);
  await expect(chrome.locator("p").first()).toContainText(/^Chrome· Vulnerability/);
  await expect(chrome.locator("time").filter({ visible: true })).toHaveCount(1);
  // The original headline, linking to the publisher.
  const link = chrome.getByRole("link", { name: SYNTHETIC_CRITICAL, exact: true });
  await expect(link).toHaveAttribute("target", "_blank");
  await expect(link).toHaveAttribute("rel", "noopener noreferrer");
  // The labelled AI summary and the advice from the source.
  await expect(chrome).toContainText(
    "AI summarySynthetic summary: a serious flaw in Chrome has been fixed in an update.",
  );
  await expect(chrome).toContainText("Advice from sourceSynthetic action: install the latest Chrome update.");
  await expect(chrome.locator("[data-slot=aspect-ratio]")).toHaveCount(1);
  await expect(chrome.getByLabel("Trust")).toContainText("/100");
});

test("sources are named once per post, in the trust line, on both tabs", async ({ page }) => {
  const once = async (headline: string) => {
    const story = page
      .getByRole("article")
      .filter({ has: page.getByRole("link", { name: headline, exact: true }) })
      .first();
    await expect(story.getByLabel("Trust")).toContainText(
      "Sources: BleepingComputer, Security Affairs, The Hacker News",
    );
    // Technical details are closed, so each name appears exactly once in what is shown.
    const text = await story.innerText();
    expect(text.split("Security Affairs").length - 1).toBe(1);
    expect(text).not.toMatch(/\+\d+ sources?/);
  };
  await page.goto("/feed");
  await once(ONEPASSWORD);
  await page.goto("/");
  await once(ONEPASSWORD);
});

test("every post has a picture: the publisher's photo or a tile of exactly the same size", async ({
  page,
}) => {
  await page.goto("/feed");
  const media = posts(page).locator("[data-slot=aspect-ratio]");
  await expect(media).toHaveCount(ALL_IN_ORDER.length);
  // Load every lazy picture, so each has settled into a photo or a tile.
  for (const box of await media.all()) await box.scrollIntoViewIfNeeded();

  const sizes = await media.evaluateAll((els) =>
    els.map((el) => {
      const r = el.getBoundingClientRect();
      return `${Math.round(r.width)}x${Math.round(r.height)}`;
    }),
  );
  expect(new Set(sizes).size).toBe(1);
  expect(sizes[0]).not.toBe("0x0");

  // The synthetic Adobe item's image loads: a credited photo. Slack's is broken: a tile.
  const adobe = post(page, SYNTHETIC_ADOBE);
  await expect(adobe.getByRole("img", { name: "Picture from Dark Reading" })).toBeVisible();
  await expect(adobe.getByText("Image: Dark Reading")).toBeVisible();
  await expect(post(page, SYNTHETIC_SLACK).locator("[data-media]")).toHaveAttribute(
    "data-media",
    "lettermark",
  );
  // No post is text only.
  for (const p of await posts(page).all()) {
    await expect(p.locator("[data-slot=aspect-ratio] img, [data-slot=aspect-ratio] [data-media]")).toHaveCount(1);
  }
});

test("the action row is outlet count, Details, Share and Watch, and nothing invented", async ({
  page,
}) => {
  await page.goto("/feed");
  const story = post(page, ONEPASSWORD);
  const actions = story.getByRole("group", { name: "Actions" });
  await expect(actions).toHaveText(/^3 outlets\s*Details\s*Share\s*Watch$/, { useInnerText: true });
  await expect(actions.getByRole("button")).toHaveCount(3);
  const page_ = (await page.locator("main").innerText()).toLowerCase();
  for (const word of ["like", "repl", "repost", "follower", "views", "retweet"]) {
    expect(page_).not.toContain(word);
  }
});

test("Details opens the technical details in place and closes again", async ({ page }) => {
  await page.goto("/feed");
  const story = post(page, ONEPASSWORD);
  const details = story.getByRole("button", { name: "Details" });
  await expect(details).toHaveAttribute("aria-expanded", "false");
  await expect(story.getByText("CVE identifiers")).toBeHidden();
  await details.click();
  await expect(story.getByRole("button", { name: "Hide details" })).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  await expect(story.getByText("CVE identifiers")).toBeVisible();
  await expect(
    story.getByRole("link", {
      name: "1Password Hacked: Customer Names and Emails Copied, Vaults Untouched",
    }),
  ).toBeVisible();
  // Local time, not UTC: 21:33 UTC is 16:33 in New York.
  await expect(story.getByText("25 Nov 2026, 16:33 EST")).toBeVisible();
  await story.getByRole("button", { name: "Hide details" }).click();
  await expect(story.getByText("CVE identifiers")).toBeHidden();
});

test("categories filter the Feed, each with its own URL; Trending is coming soon", async ({
  page,
}) => {
  await page.goto("/feed");
  const categories = page.getByRole("navigation", { name: "Categories" });
  const category = (name: string) => categories.getByRole("link", { name, exact: true });
  await expect(category("All")).toHaveAttribute("aria-current", "page");

  await category("Research").click();
  await expect(page).toHaveURL(/\/feed\?tab=research$/);
  await expect(category("Research")).toHaveAttribute("aria-current", "page");
  await expect(posts(page).getByRole("heading")).toHaveText([
    "SYS010 malware abuses browser management to spy on Gmail, Outlook",
  ]);

  await category("Under attack").click();
  await expect(page).toHaveURL(/\/feed\?tab=under-attack$/);
  await expect(posts(page).getByRole("heading")).toHaveText([SYNTHETIC_ZERO_DAY]);

  await category("Breaches").click();
  await expect(posts(page).getByRole("heading")).toHaveText([
    FLIGHT_CENTRE,
    ONEPASSWORD,
    SYNTHETIC_MARKUP,
    SYNTHETIC_ADOBE,
    SYNTHETIC_SLACK,
  ]);

  await category("Trending").click();
  await expect(page).toHaveURL(/\/feed\?tab=trending$/);
  await expect(page.getByRole("heading", { name: "Trending is coming soon" })).toBeVisible();
  await expect(posts(page)).toHaveCount(0);

  await category("All").click();
  await expect(page).toHaveURL(/\/feed$/);
  await expect(posts(page)).toHaveCount(ALL_IN_ORDER.length);
});

test("Search is a quiet 'coming soon', not a 404", async ({ page }) => {
  const response = await page.goto("/search");
  expect(response!.status()).toBe(200);
  await expect(page.getByRole("heading", { name: "Search is coming soon" })).toBeVisible();
});

const watchingList = (page: Page) =>
  page.getByRole("list", { name: "Watched companies" }).filter({ visible: true });

test("Watch keeps a company in this browser, across a reload, and the Watching list filters the Feed", async ({
  page,
}) => {
  await page.goto("/feed");
  const watch = post(page, ONEPASSWORD).getByRole("button", { name: "Watch 1Password" });
  await expect(watch).toHaveAttribute("aria-pressed", "false");
  await watch.click();
  await expect(watch).toHaveAttribute("aria-pressed", "true");
  await expect(watch).toHaveText("Watching");
  await expect(watchingList(page).getByRole("listitem")).toHaveText([/^1Password1 post on this page/]);

  await page.reload();
  await expect(
    post(page, ONEPASSWORD).getByRole("button", { name: "Watch 1Password" }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(watchingList(page).getByRole("listitem")).toHaveCount(1);

  await page.getByRole("link", { name: "Show only these" }).click();
  await expect(page).toHaveURL(/\/feed\?watching=1$/);
  await expect(posts(page).getByRole("heading")).toHaveText([ONEPASSWORD]);

  await page.getByRole("button", { name: "Stop watching 1Password" }).click();
  await expect(posts(page)).toHaveCount(0);
  await expect(page.getByText("You are not watching any company yet")).toBeVisible();
});

test.describe("when the browser refuses local storage", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      Object.defineProperty(window, "localStorage", {
        get() {
          throw new DOMException("blocked", "SecurityError");
        },
      });
    });
  });

  test("Watch and the Watching list still work for as long as the page is open", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/feed");
    const watch = post(page, FLIGHT_CENTRE).getByRole("button", { name: /^Watch / });
    await watch.click();
    await expect(watch).toHaveAttribute("aria-pressed", "true");
    await expect(watchingList(page).getByRole("listitem")).toHaveCount(1);

    // Nothing could be kept, so a reload starts empty, and nothing breaks.
    await page.reload();
    await expect(post(page, FLIGHT_CENTRE).getByRole("button", { name: /^Watch / })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(errors).toEqual([]);
  });
});

test("Share uses the browser's share sheet where there is one", async ({ page }) => {
  await page.addInitScript(() => {
    const w = window as unknown as { __shared?: ShareData };
    Object.defineProperty(navigator, "share", {
      value: (data: ShareData) => {
        w.__shared = data;
        return Promise.resolve();
      },
    });
  });
  await page.goto("/feed");
  await post(page, ONEPASSWORD).getByRole("button", { name: "Share" }).click();
  const shared = await page.evaluate(() => (window as unknown as { __shared?: ShareData }).__shared);
  expect(shared).toEqual({
    title: ONEPASSWORD,
    url: "https://www.bleepingcomputer.com/news/security/1password-customer-data-stolen-after-employee-github-account-breach/",
  });
});

test("without a share sheet, Share copies the link and says so", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.addInitScript(() => {
    Object.defineProperty(Navigator.prototype, "share", { value: undefined });
  });
  await page.goto("/feed");
  const story = post(page, ONEPASSWORD);
  // Where the row sits on the page (not the viewport, which scrolls to the button).
  const row = () =>
    story
      .getByRole("group", { name: "Actions" })
      .evaluate((el) => {
        const r = el.getBoundingClientRect();
        return { x: r.x, y: r.y + window.scrollY, width: r.width, height: r.height };
      });
  const before = await row();
  await story.getByRole("button", { name: "Share" }).click();
  await expect(story.getByRole("status")).toHaveText("Link copied");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    "https://www.bleepingcomputer.com/news/security/1password-customer-data-stolen-after-employee-github-account-breach/",
  );
  // The confirmation floats above the button: the row does not move.
  expect(await row()).toEqual(before);
});

test("on desktop: categories left, posts in the middle, widgets right", async ({ page }) => {
  await page.goto("/feed");
  const nav = (await page.getByRole("navigation", { name: "Categories" }).boundingBox())!;
  const main = (await page.getByRole("region", { name: "All posts" }).boundingBox())!;
  const rail = (await page.getByRole("complementary", { name: "Widgets" }).boundingBox())!;
  expect(nav.x + nav.width).toBeLessThanOrEqual(main.x);
  expect(main.x + main.width).toBeLessThanOrEqual(rail.x);
  await expect(page.getByRole("navigation", { name: "Tab bar" })).toBeHidden();
  // The rail's side switch belongs to Featured; here the left column is the navigation.
  await expect(page.getByRole("button", { name: /^Move widgets/ })).toHaveCount(0);
});

test("motion uses the shared tokens and stops under reduced motion", async ({ page }) => {
  await page.goto("/feed");
  const headline = posts(page).first().getByRole("heading").getByRole("link");
  expect(await headline.evaluate((el) => getComputedStyle(el).transitionDuration)).not.toBe("0s");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload();
  expect(await headline.evaluate((el) => getComputedStyle(el).transitionDuration)).toBe("0s");
  await expect(posts(page).first().locator("[data-fade-word]")).toHaveCount(0);
});

test.describe("on a phone", () => {
  test.use({ viewport: { width: 375, height: 812 }, hasTouch: true, isMobile: true });

  test("categories scroll sideways, the tab bar leads to every place, and nothing is covered", async ({
    page,
  }) => {
    await page.goto("/feed");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      ),
    ).toBe(0);
    await expect(primaryNav(page).getByRole("link", { name: "Feed" })).toBeVisible();

    const row = page.getByRole("tablist", { name: "Sections" });
    expect(
      await row.evaluate((el) => el.parentElement!.scrollWidth > el.parentElement!.clientWidth),
    ).toBe(true);
    await page.getByRole("tab", { name: "Under attack" }).tap();
    await expect(page).toHaveURL(/\/feed\?tab=under-attack$/);
    await expect(posts(page).getByRole("heading")).toHaveText([SYNTHETIC_ZERO_DAY]);
    await page.getByRole("tab", { name: "All" }).tap();
    await expect(posts(page)).toHaveCount(ALL_IN_ORDER.length);

    const bar = page.getByRole("navigation", { name: "Tab bar" });
    expect(
      await bar.getByRole("link").evaluateAll((els) => els.map((el) => el.getAttribute("aria-label"))),
    ).toEqual([
      "Featured",
      "Feed",
      "Search",
      "Watching",
      "Charts",
    ]);
    await expect(bar.getByRole("link", { name: "Feed" })).toHaveAttribute("aria-current", "page");
    for (const box of await bar.getByRole("link").all()) {
      expect((await box.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    }

    // The widgets wait behind Charts.
    await expect(page.getByRole("complementary", { name: "Widgets" })).toBeHidden();

    // Scrolled to the end, the last post's actions sit above the tab bar.
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    const last = posts(page).last().getByRole("group", { name: "Actions" });
    const lastBox = (await last.boundingBox())!;
    const barBox = (await bar.locator(".tbb").boundingBox())!;
    expect(lastBox.y + lastBox.height).toBeLessThanOrEqual(barBox.y);

    const details = posts(page).first().getByRole("button", { name: "Details" });
    expect((await details.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    // On phones Watch sits in the post's header (Option C) and the action row fits one line.
    const first = posts(page).first();
    await expect(first.getByRole("button", { name: /^Watch / })).toHaveCount(1);
    const watchBox = (await first.getByRole("button", { name: /^Watch / }).boundingBox())!;
    const headlineBox = (await first.getByRole("heading").boundingBox())!;
    expect(watchBox.y + watchBox.height).toBeLessThanOrEqual(headlineBox.y + 8);
    const rowItems = await first
      .getByRole("group", { name: "Actions" })
      .locator(":scope > *")
      .evaluateAll((els) =>
        els
          .filter((e) => e.getClientRects().length)
          .map((e) => {
            const r = e.getBoundingClientRect();
            return r.y + r.height / 2;
          }),
      );
    // Every item's middle on the same line (within a few pixels).
    expect(Math.max(...rowItems) - Math.min(...rowItems)).toBeLessThan(6);

    await bar.getByRole("link", { name: "Charts" }).tap();
    await expect(page).toHaveURL(/\/feed\?view=charts$/);
    await expect(page.getByRole("complementary", { name: "Widgets" })).toBeVisible();
    await expect(posts(page).first()).toBeHidden();

    await bar.getByRole("link", { name: "Watching" }).tap();
    await expect(page).toHaveURL(/\/feed\?watching=1$/);
    await expect(page.getByText("You are not watching any company yet")).toBeVisible();
  });
});

test.describe("on a tablet", () => {
  test.use({ viewport: { width: 820, height: 1180 }, hasTouch: true });

  test("categories in a left column beside the posts, widgets behind Charts", async ({ page }) => {
    await page.goto("/feed");
    const nav = (await page.getByRole("navigation", { name: "Categories" }).boundingBox())!;
    const main = (await page.getByRole("region", { name: "All posts" }).boundingBox())!;
    expect(nav.x + nav.width).toBeLessThanOrEqual(main.x);
    await expect(page.getByRole("navigation", { name: "Tab bar" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "Widgets" })).toBeHidden();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      ),
    ).toBe(0);
  });
});

for (const theme of ["light", "dark"] as const) {
  test(`text on the Feed meets WCAG AA contrast in the ${theme} theme`, async ({ page }) => {
    await page.addInitScript((t) => {
      try {
        localStorage.setItem("theme", t);
      } catch {}
    }, theme);
    await page.setViewportSize({ width: 820, height: 1180 });
    await page.goto("/feed");
    await expect(posts(page).first()).toBeVisible();
    // Every visible text node in the header, navigation, posts and tab bar, against the first
    // opaque background behind it (pictures excluded: their credit chip is measured by
    // scripts/contrast.mjs against the worst case).
    const { failures, checked } = await page.evaluate(() => {
      const parse = (c: string) => {
        const m = c.match(/rgba?\(([^)]+)\)/);
        if (!m) return null;
        const [r, g, b, a = "1"] = m[1].split(/[ ,/]+/).filter(Boolean);
        return [Number(r), Number(g), Number(b), Number(a)];
      };
      const lum = ([r, g, b]: number[]) => {
        const f = (v: number) => {
          const c = v / 255;
          return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
        };
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
      };
      const background = (el: Element | null): number[] => {
        for (let e = el; e; e = e.parentElement) {
          const c = parse(getComputedStyle(e).backgroundColor);
          if (c && c[3] > 0.5) return c;
        }
        return [255, 255, 255, 1];
      };
      const out: string[] = [];
      let checked = 0;
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        const el = n.parentElement!;
        if (!n.textContent?.trim() || el.closest("[data-slot=aspect-ratio], [aria-hidden=true], .sr-only, script, style"))
          continue;
        const cs = getComputedStyle(el);
        if (cs.visibility === "hidden" || Number(cs.opacity) === 0 || !el.getClientRects().length) continue;
        const fg = parse(cs.color)!;
        const bg = background(el);
        const [hi, lo] = [lum(fg), lum(bg)].sort((a, b) => b - a);
        const ratio = (hi + 0.05) / (lo + 0.05);
        checked++;
        if (ratio < 4.5) out.push(`${ratio.toFixed(2)} "${n.textContent.trim().slice(0, 40)}"`);
      }
      return { failures: out, checked };
    });
    expect(checked).toBeGreaterThan(100);
    expect(failures).toEqual([]);
  });
}
