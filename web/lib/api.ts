// Client for the Compromised API. Server-side only: API_URL is not exposed to the browser.

export type EventSource = {
  publisher: string;
  url: string;
  headline: string;
  excerpt: string;
  published_at: string;
};

/** The verification states agreed in docs/wiki/trust-labels-and-score.md. */
export type VerificationStatus =
  | "confirmed"
  | "reported"
  | "claimed"
  | "investigating"
  | "disputed";

/**
 * One event as the API returns it. The optional fields at the end are filled by later tickets
 * (enrichment, grouping, scoring); until the API sends them they are absent and the page shows
 * a quiet empty state.
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
  sources: EventSource[];
  summary?: string | null;
  status?: VerificationStatus | null;
  score?: number | null;
  cves?: string[];
  attack_vector?: string | null;
  action_line?: string | null;
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
