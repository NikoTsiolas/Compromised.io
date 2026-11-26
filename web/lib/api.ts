// Client for the Compromised API. Server-side only: API_URL is not exposed to the browser.

export type EventSource = {
  record_id: number;
  publisher: string;
  url: string;
  headline: string;
  excerpt: string;
  published_at: string;
};

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
): Promise<EventPage> {
  const url = new URL("/v1/events", API_URL);
  url.searchParams.set("tab", tab);
  if (cursor) url.searchParams.set("cursor", cursor);
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
