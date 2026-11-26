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

/**
 * One event as the API returns it. The optional fields at the end (CVEs, attack vector) are
 * filled by later tickets; until the API sends them they are absent and the page shows a quiet
 * empty state.
 */
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
  cves?: string[];
  attack_vector?: string | null;
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

/** Widget figures (#15). Spike months are decided by the API's `spike_rule`. */
export type KevMonth = {
  month: string;
  count: number;
  spike: boolean;
  notable: {
    cve: string;
    title: string;
    organization: string;
    people_use: boolean;
    ransomware: boolean;
  }[];
};

export type ExploitedByMonth = {
  months: KevMonth[];
  spike_rule: string;
  catalog: {
    version: string | null;
    declared_count: number | null;
    entries: number;
    fetched_at: string;
  } | null;
};

export type RecentlyExploited = {
  items: { cve: string; product: string; logo_key: string | null; added_on: string }[];
};

export type MostReported = {
  window_days: number;
  items: { name: string; key: string | null; logo_key: string | null; count: number }[];
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

export async function getScoring(): Promise<Scoring> {
  return getJson(new URL("/v1/scoring", API_URL));
}

export async function listTabs(): Promise<Tab[]> {
  return getJson(new URL("/v1/tabs", API_URL));
}

export async function getExploitedByMonth(): Promise<ExploitedByMonth> {
  return getJson(new URL("/v1/widgets/exploited-by-month", API_URL));
}

export async function getRecentlyExploited(): Promise<RecentlyExploited> {
  return getJson(new URL("/v1/widgets/recently-exploited", API_URL));
}

export async function getMostReported(): Promise<MostReported> {
  return getJson(new URL("/v1/widgets/most-reported", API_URL));
}

async function getJson<T>(url: URL): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${url.pathname} request failed: HTTP ${response.status}`);
  }
  return response.json();
}
