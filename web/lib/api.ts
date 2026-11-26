// Client for the Compromised API. Server-side only: API_URL is not exposed to the browser.

export type EventSource = {
  record_id: number;
  publisher: string;
  url: string;
  headline: string;
  excerpt: string;
  published_at: string;
};

/** The verification states in docs/wiki/trust-labels-and-score.md. */
export type VerificationStatus =
  | "confirmed"
  | "reported"
  | "claimed"
  | "investigating"
  | "disputed";

/** Label, score and the outlets counted: always shown together, never the score alone. */
export type Trust = {
  status: VerificationStatus;
  /** Reader-facing wording, e.g. "Reported by 3 news outlets". Show it as sent. */
  label: string;
  /** 0-100, from the formula on the "How we score" page. */
  score: number;
  /** Publishers the score counted, earliest first. */
  sources: string[];
};

/** One event as the API returns it. */
export type FeedEvent = {
  id: number;
  title: string;
  published_at: string;
  first_seen_at: string;
  category: string;
  category_label: string;
  commentary: boolean;
  /** "unknown" when no organization is known. */
  affected_organization: string;
  organization_key: string | null;
  logo_key: string | null;
  tabs: string[];
  /** Plain-language summary written by the model; show it labelled "AI summary". */
  summary: string | null;
  /** Only when a source states the action. */
  action_line: string | null;
  enrichment: "ai" | "rules";
  source_count: number;
  /** Earliest first; the first source's headline is the event title. */
  sources: EventSource[];
  /** Null only before the event is first assessed. */
  trust: Trust | null;
  /** The publisher's own feed image, or null (none, or images switched off). */
  image?: PublisherImage | null;
  /** Every CVE identifier the sources name, sorted (#10). */
  cves?: string[];
  /** How the attack worked, when a source says; null when not identified (#10). */
  attack_vector?: string | null;
  /** Groups a source names or a claim source credits (#10). */
  threat_actors?: string[];
};

export type PublisherImage = {
  url: string;
  publisher: string;
};

/** The confidence formula's numbers as the API's code uses them. */
export type Scoring = {
  claim_only: number;
  one_outlet: number;
  per_extra_outlet: number;
  press_cap: number;
  official: number;
  official_and_press: number;
  disputed: number;
  sources: { name: string; tier: SourceHealth["tier"]; weight: number }[];
};

export type Tab = {
  id: string;
  label: string;
};

export type EventPage = {
  events: FeedEvent[];
  next_cursor: string | null;
};

/** One value a search filter accepts, with its reader-facing label (GET /v1/filters). */
export type FilterOption = { id: string; label: string };

export type SearchFilters = {
  tabs: FilterOption[];
  categories: FilterOption[];
  sources: FilterOption[];
  statuses: FilterOption[];
};

/** A search as the URL and the API both spell it: every key optional, empty means "any". */
export type SearchQuery = {
  q?: string;
  category?: string;
  source?: string;
  status?: string;
  from?: string;
  to?: string;
  cursor?: string;
};

export const SEARCH_KEYS = ["q", "category", "source", "status", "from", "to"] as const;

/** Thrown when the API refuses a search's values (a hand-edited URL, say): HTTP 400 or 422. */
export class RefusedSearch extends Error {}

export type IngestionState = "starting" | "live" | "degraded" | "down";
export type SourceState = "pending" | "ok" | "failing" | "stale";

export type SourceHealth = {
  id: string;
  name: string;
  tier: "official" | "press" | "attacker_claim";
  interval_seconds: number;
  state: SourceState;
  last_attempt_at: string | null;
  last_success_at: string | null;
  consecutive_failures: number;
};

export type IngestionStatus = {
  status: IngestionState;
  last_success_at: string | null;
  sources: SourceHealth[];
};

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export async function getStatus(): Promise<IngestionStatus> {
  return getJson(new URL("/v1/status", API_URL));
}

export async function listEvents(
  tab: string,
  cursor?: string,
  limit?: number,
): Promise<EventPage> {
  const url = new URL("/v1/events", API_URL);
  url.searchParams.set("tab", tab);
  if (cursor) url.searchParams.set("cursor", cursor);
  if (limit) url.searchParams.set("limit", String(limit));
  return getJson(url);
}

/** Published events matching the query and filters, newest first (GET /v1/search). */
export async function searchEvents(query: SearchQuery): Promise<EventPage> {
  const url = new URL("/v1/search", API_URL);
  for (const [key, value] of Object.entries(query)) {
    if (value) url.searchParams.set(key, value);
  }
  const response = await fetch(url, { cache: "no-store" });
  if (response.status === 400 || response.status === 422) throw new RefusedSearch();
  if (!response.ok) throw new Error(`/v1/search request failed: HTTP ${response.status}`);
  return response.json();
}

export async function getFilters(): Promise<SearchFilters> {
  return getJson(new URL("/v1/filters", API_URL));
}

export async function getScoring(): Promise<Scoring> {
  return getJson(new URL("/v1/scoring", API_URL));
}

export async function listTabs(): Promise<Tab[]> {
  return getJson(new URL("/v1/tabs", API_URL));
}

async function getJson<T>(url: URL): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${url.pathname} request failed: HTTP ${response.status}`);
  }
  return response.json();
}
