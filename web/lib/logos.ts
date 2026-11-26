// Company logos for the designed tile, from Simple Icons (CC0; the marks remain their owners'
// trademarks). Server-only: the whole icon set stays on the server and only the one path an
// event needs is sent to the browser. A catalog logo key that Simple Icons does not carry
// resolves to null, and the tile draws a lettermark instead.
import * as icons from "simple-icons";

import type { FeedItem, Logo } from "@/lib/feed";

type SimpleIcon = { slug: string; title: string; path: string };

const bySlug = new Map<string, SimpleIcon>(
  Object.values(icons as Record<string, SimpleIcon>)
    .filter((icon) => typeof icon?.slug === "string")
    .map((icon) => [icon.slug, icon]),
);

export function resolveLogo(key: string | null | undefined): Logo | null {
  if (!key) return null;
  const icon = bySlug.get(key);
  return icon ? { title: icon.title, path: icon.path } : null;
}

export function withLogo(item: FeedItem): FeedItem {
  return { ...item, logo: resolveLogo(item.logoKey) };
}
