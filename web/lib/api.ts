// Client for the Compromised API. Server-side only: API_URL is not exposed to the browser.

export type EventSource = {
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
  sources: EventSource[];
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
  const response = await fetch(new URL("/v1/status", API_URL), {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`status request failed: HTTP ${response.status}`);
  }
  return response.json();
}

export async function listEvents(cursor?: string): Promise<EventPage> {
  const url = new URL("/v1/events", API_URL);
  if (cursor) url.searchParams.set("cursor", cursor);
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`events request failed: HTTP ${response.status}`);
  }
  return response.json();
}
