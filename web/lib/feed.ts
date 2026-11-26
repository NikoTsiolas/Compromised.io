// What a feed row shows, independent of where the values come from (the API, or the clearly
// labelled sample data on /preview). `undefined` means "this field does not exist yet" and is
// rendered as a quiet empty state; `null` means "looked for and not known".
import type { EventDetail, FeedEvent, PublisherImage, Trust, VerificationStatus } from "@/lib/api";

export type { PublisherImage, Trust, VerificationStatus };

/** A company logo drawn from Simple Icons: the SVG path on a 24x24 grid. */
export type Logo = { title: string; path: string };

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
  /** The API's label, score and source names, shown together and as sent. */
  trust?: Trust | null;
  sources: FeedSource[];
  cves?: string[];
  attackVector?: string | null;
  threatActors?: string[];
  actionLine?: string | null;
  /** Under active attack right now: earns the red LIVE kicker. */
  live?: boolean;
  /** False when the event is in no feed tab (search finds it anyway and says so). */
  inFeed?: boolean;
};

export function toFeedItem(event: FeedEvent | EventDetail): FeedItem {
  const [first] = event.sources;
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
    // Shown exactly as the API sends it: its label, score and source names (#7).
    trust: event.trust,
    sources: event.sources.map((s) => ({
      publisher: s.publisher,
      url: s.url,
      headline: s.headline,
      publishedAt: s.published_at,
    })),
    cves: event.cves,
    attackVector: event.attack_vector,
    threatActors: event.threat_actors,
    actionLine: event.action_line,
    inFeed: event.tabs.length > 0,
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
