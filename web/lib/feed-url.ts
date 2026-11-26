// Addresses inside the Feed tab. Categories are the API's tab ids (`?tab=research`); the
// Watching filter and the phone Charts view are flags; `cursor` pages back in time.
import { DEFAULT_TAB } from "@/lib/feed";

export const FEED_PATH = "/feed";

/** Categories still being built: shown, but "coming soon". Empty since Trending (#10) landed. */
export const COMING_SOON_TABS: ReadonlySet<string> = new Set<string>();

export type FeedView = "posts" | "charts";

export function feedHref({
  tab = DEFAULT_TAB,
  watching = false,
  view = "posts",
  cursor,
}: {
  tab?: string;
  watching?: boolean;
  view?: FeedView;
  cursor?: string | null;
} = {}): string {
  const query = new URLSearchParams();
  if (tab !== DEFAULT_TAB) query.set("tab", tab);
  if (watching) query.set("watching", "1");
  if (view !== "posts") query.set("view", view);
  if (cursor) query.set("cursor", cursor);
  const q = query.toString();
  return q ? `${FEED_PATH}?${q}` : FEED_PATH;
}
