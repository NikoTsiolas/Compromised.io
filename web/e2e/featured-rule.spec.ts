// The featured-story rule, called directly (no page): which event leads the homepage.
import { expect, test } from "@playwright/test";

import { selectFeatured } from "../lib/featured";
import type { FeedItem } from "../lib/feed";

const item = (id: string, hoursAgo: number, extra: Partial<FeedItem> = {}): FeedItem => ({
  id,
  headline: `[Synthetic] ${id}`,
  url: `https://example.com/${id}`,
  publisher: "Example",
  publishedAt: new Date(Date.parse("2026-11-26T15:00:00Z") - hoursAgo * 3_600_000).toISOString(),
  organization: "Example Org",
  sources: [],
  ...extra,
});
const picture = { url: "https://images.example.com/x.jpg", publisher: "Example" };
const now = new Date("2026-11-26T15:00:00Z");

test("a recent event with a picture leads over a newer one without", () => {
  const items = [item("newest", 1), item("pictured", 5, { image: picture }), item("older", 6)];
  const { lead, cards } = selectFeatured(items, { now });
  expect(lead?.id).toBe("pictured");
  expect(cards.map((c) => c.id)).toEqual(["newest", "older"]);
});

test("a picture never lets a much older event displace the news", () => {
  const items = [item("newest", 1), item("old-pictured", 40, { image: picture })];
  expect(selectFeatured(items, { now }).lead?.id).toBe("newest");
});

test("attacker claims and unnamed events never lead, picture or not", () => {
  const items = [
    item("claim", 1, { image: picture, trust: { status: "claimed", score: 20, outlets: 0 } }),
    item("unnamed", 2, { image: picture, organization: null }),
    item("named", 3),
  ];
  expect(selectFeatured(items, { now }).lead?.id).toBe("named");
});
