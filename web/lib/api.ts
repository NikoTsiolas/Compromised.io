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
  category: string;
  category_label: string;
  commentary: boolean;
  /** "unknown" when no organization is known. */
  affected_organization: string;
  organization_key: string | null;
  logo_key: string | null;
  tabs: string[];
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

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

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
