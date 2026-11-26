// What a feed row shows, independent of where the values come from (the API, or the clearly
// labelled sample data on /preview). `undefined` means "this field does not exist yet" and is
// rendered as a quiet empty state; `null` means "looked for and not known".
import type { FeedEvent, VerificationStatus } from "@/lib/api";

export type { VerificationStatus };

export type Trust = {
  status: VerificationStatus;
  /** 0-100, from the published formula. Never shown without its label. */
  score: number;
  /** Distinct news outlets behind the event, for "Reported by N news outlets". */
  outlets: number;
};

export type FeedSource = {
  publisher: string;
  url: string;
  headline: string;
  publishedAt: string;
};

export type FeedItem = {
  id: string;
  headline: string;
  /** The earliest source's article: the headline links here. */
  url: string;
  publisher: string;
  publishedAt: string;
  /** The publisher's own short excerpt, shown until a plain-language summary exists. */
  excerpt?: string;
  organization?: string | null;
  summary?: string | null;
  category?: string | null;
  trust?: Trust | null;
  sources: FeedSource[];
  cves?: string[];
  attackVector?: string | null;
  actionLine?: string | null;
  /** Under active attack right now: earns the red LIVE kicker. */
  live?: boolean;
};

export function toFeedItem(event: FeedEvent): FeedItem {
  const [first] = event.sources;
  const trust =
    event.status && typeof event.score === "number"
      ? {
          status: event.status,
          score: event.score,
          outlets: new Set(event.sources.map((s) => s.publisher)).size,
        }
      : undefined;
  return {
    id: String(event.id),
    headline: event.title,
    url: first?.url ?? "",
    publisher: first?.publisher ?? "",
    publishedAt: event.published_at,
    excerpt: first?.excerpt || undefined,
    organization: event.organization,
    summary: event.summary,
    category: event.category,
    trust,
    sources: event.sources.map((s) => ({
      publisher: s.publisher,
      url: s.url,
      headline: s.headline,
      publishedAt: s.published_at,
    })),
    cves: event.cves,
    attackVector: event.attack_vector,
    actionLine: event.action_line,
  };
}

/** Section tabs from the product page. Slugs are what appears in the URL (?tab=). */
export const TABS = [
  { slug: "all", label: "All" },
  { slug: "breaches", label: "Breaches" },
  { slug: "ransomware", label: "Ransomware" },
  { slug: "under-attack", label: "Under attack" },
  { slug: "update-now", label: "Update now" },
  { slug: "research", label: "Research" },
  { slug: "trending", label: "Trending" },
] as const;

export type TabSlug = (typeof TABS)[number]["slug"];

export function tabFrom(value: unknown): TabSlug {
  return TABS.find((t) => t.slug === value)?.slug ?? "all";
}

/** Plain-language category names for the row kicker. Unknown values are shown as given. */
const CATEGORY_LABELS: Record<string, string> = {
  breach: "Data breach",
  ransomware: "Ransomware",
  exploited_vulnerability: "Under attack",
  vulnerability: "Security flaw",
  malware: "Malware",
  phishing: "Phishing",
  research: "Research",
};

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category.replaceAll("_", " ");
}

// --- time ------------------------------------------------------------------------------------

const clock = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: "UTC",
});

/** "11:50" in UTC. */
export function formatClock(iso: string): string {
  return clock.format(new Date(iso));
}

const day = new Intl.DateTimeFormat("en-GB", {
  weekday: "long",
  day: "numeric",
  month: "long",
  timeZone: "UTC",
});

/** "Thursday 26 November", in UTC like the times beside it. */
export function formatDay(iso: string): string {
  return day.format(new Date(iso)).replace(",", "");
}

function utcDateKey(iso: string): string {
  return iso.slice(0, 10);
}

export type DayGroup = { key: string; label: string; items: FeedItem[] };

/** Consecutive items grouped by UTC calendar day, labelled Today / Yesterday where true. */
export function groupByDay(items: FeedItem[], now: Date = new Date()): DayGroup[] {
  const today = now.toISOString().slice(0, 10);
  const yesterday = new Date(now.getTime() - 86_400_000).toISOString().slice(0, 10);
  const groups: DayGroup[] = [];
  for (const item of items) {
    const key = utcDateKey(new Date(item.publishedAt).toISOString());
    let group = groups.at(-1);
    if (!group || group.key !== key) {
      const prefix = key === today ? "Today" : key === yesterday ? "Yesterday" : null;
      const label = formatDay(item.publishedAt);
      group = { key, label: prefix ? `${prefix} · ${label}` : label, items: [] };
      groups.push(group);
    }
    group.items.push(item);
  }
  return groups;
}
