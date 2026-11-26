// What a feed row shows, independent of where the values come from (the API, or the clearly
// labelled sample data on /preview). `undefined` means "this field does not exist yet" and is
// rendered as a quiet empty state; `null` means "looked for and not known".
import type { FeedEvent, PublisherImage, VerificationStatus } from "@/lib/api";

export type { PublisherImage, VerificationStatus };

/** A company logo drawn from Simple Icons: the SVG path on a 24x24 grid. */
export type Logo = { title: string; path: string };

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
  /** The API's plain-language name for the category, when it sends one. */
  categoryName?: string;
  logoKey?: string | null;
  /** Filled on the server from logoKey (lib/logos.ts); null when the catalog has no logo. */
  logo?: Logo | null;
  /** Loaded by the browser straight from the publisher, with credit; never by our server. */
  image?: PublisherImage | null;
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
    organization:
      event.affected_organization === "unknown" ? null : event.affected_organization,
    summary: event.summary,
    category: event.category,
    categoryName: event.category_label,
    logoKey: event.logo_key,
    image: event.image ?? null,
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

/** Section tabs come from the API (GET /v1/tabs); this is the fallback label for "all". */
export const DEFAULT_TAB = "all";

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
