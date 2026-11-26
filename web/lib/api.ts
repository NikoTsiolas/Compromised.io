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
 * One event as the API returns it. Fields after `sources` are filled by later tickets
 * (entities, enrichment, classification, scoring); until the API sends them they are absent
 * and the page shows a quiet empty state.
 */
export type FeedEvent = {
  id: number;
  title: string;
  published_at: string;
  first_seen_at: string;
  sources: EventSource[];
  organization?: string | null;
  summary?: string | null;
  category?: string | null;
  status?: VerificationStatus | null;
  score?: number | null;
  cves?: string[];
  attack_vector?: string | null;
  action_line?: string | null;
};

export type EventPage = {
  events: FeedEvent[];
  next_cursor: string | null;
};

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export async function listEvents(
  cursor?: string,
  limit?: number,
): Promise<EventPage> {
  const url = new URL("/v1/events", API_URL);
  if (cursor) url.searchParams.set("cursor", cursor);
  if (limit) url.searchParams.set("limit", String(limit));
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`events request failed: HTTP ${response.status}`);
  }
  return response.json();
}
