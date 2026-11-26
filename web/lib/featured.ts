// Which events the featured section shows. Chosen by rule, never by hand.
//
// Today's rule ("newest-named"): the newest event with a named organisation that is not an
// attacker claim, preferring one with a publisher picture if it is no more than PICTURE_WINDOW
// older than that newest one, so a picture never lets old news displace today's. Source counts and trust status arrive with the grouping and scoring tickets;
// once they do, switch FEATURED_RULE to "most-sources-24h": the event with the most independent
// sources in the last 24 hours that is confirmed or credibly reported. Either way the next three
// events in feed order become the cards, and the feed continues with the rest.
import type { FeedItem } from "@/lib/feed";

export type FeaturedRule = "newest-named" | "most-sources-24h";

export const FEATURED_RULE: FeaturedRule = "newest-named";
export const CARD_COUNT = 3;
export const PICTURE_WINDOW_HOURS = 24;

export type Featured = {
  lead: FeedItem | null;
  cards: FeedItem[];
  /** Everything else, in feed order. */
  rest: FeedItem[];
};

/** Never an attacker claim, and never an event without a named organisation. */
function eligible(item: FeedItem): boolean {
  return Boolean(item.organization) && item.trust?.status !== "claimed";
}

function outlets(item: FeedItem): number {
  return new Set(item.sources.map((s) => s.publisher)).size;
}

function pickLead(items: FeedItem[], rule: FeaturedRule, now: Date): FeedItem | null {
  const candidates = items.filter(eligible);
  if (rule === "most-sources-24h") {
    const since = now.getTime() - 24 * 3600 * 1000;
    const recent = candidates.filter(
      (i) =>
        Date.parse(i.publishedAt) >= since &&
        (i.trust?.status === "confirmed" || i.trust?.status === "reported"),
    );
    // Stable sort keeps feed order (newest first) among equals; a picture breaks a tie.
    const best = [...recent].sort(
      (a, b) => outlets(b) - outlets(a) || Number(Boolean(b.image)) - Number(Boolean(a.image)),
    )[0];
    if (best) return best;
  }
  const newest = candidates[0];
  if (!newest) return null;
  const since = Date.parse(newest.publishedAt) - PICTURE_WINDOW_HOURS * 3600 * 1000;
  const pictured = candidates.find(
    (i) => i.image && Date.parse(i.publishedAt) >= since,
  );
  return pictured ?? newest;
}

/** `items` arrive newest first, as the feed lists them. */
export function selectFeatured(
  items: FeedItem[],
  { rule = FEATURED_RULE, now = new Date() }: { rule?: FeaturedRule; now?: Date } = {},
): Featured {
  const lead = pickLead(items, rule, now);
  if (!lead) return { lead: null, cards: [], rest: items };
  const others = items.filter((i) => i !== lead);
  return {
    lead,
    cards: others.slice(0, CARD_COUNT),
    rest: others.slice(CARD_COUNT),
  };
}
