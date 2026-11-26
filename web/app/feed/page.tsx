// The Feed tab (#16): every event as a post, newest first, filtered by category (`?tab=`), by the
// reader's Watching list (`?watching=1`), or showing the widgets on phones (`?view=charts`).
// Everything from the API is rendered as React text, never as HTML. Next.js 16 runs with
// cacheComponents, so the data-fetching part sits inside <Suspense>.
import type { Metadata } from "next";
import { Suspense, ViewTransition } from "react";

import { FeedSkeleton } from "@/components/bencho-pro/feed-skeleton";
import { FeedView } from "@/components/feed/feed-view";
import { IngestionIndicator, SourceStatus } from "@/components/ingestion-status";
import { SiteHeader } from "@/components/site/site-header";
import { railWidgets } from "@/components/widgets/rail-widgets";
import { listEvents, listTabs, MAX_PAGE_SIZE, type EventPage, type Tab } from "@/lib/api";
import { DEFAULT_TAB, toFeedItem } from "@/lib/feed";
import { COMING_SOON_TABS, feedHref } from "@/lib/feed-url";
import { withLogo } from "@/lib/logos";

export const metadata: Metadata = {
  title: "Feed · Compromised",
};

export default function FeedPage({ searchParams }: PageProps<"/feed">) {
  return (
    <>
      <SiteHeader
        current="feed"
        status={
          <Suspense fallback={null}>
            <IngestionIndicator />
          </Suspense>
        }
      />
      <main className="mx-auto max-w-[1240px] px-0 sm:px-6 lg:px-10">
        <Suspense
          fallback={
            <ViewTransition exit="auto" default="none">
              <FeedSkeleton />
            </ViewTransition>
          }
        >
          <ViewTransition enter="auto" default="none">
            <Feed searchParams={searchParams} />
          </ViewTransition>
        </Suspense>
      </main>
    </>
  );
}

async function Feed({ searchParams }: { searchParams: PageProps<"/feed">["searchParams"] }) {
  const { cursor, tab: requested, watching: watchingParam, view } = await searchParams;
  const watching = watchingParam === "1";
  let tabs: Tab[];
  let page: EventPage = { events: [], next_cursor: null };
  let tab = DEFAULT_TAB;
  try {
    tabs = await listTabs();
    if (!watching && typeof requested === "string" && tabs.some((t) => t.id === requested)) {
      tab = requested;
    }
    if (!COMING_SOON_TABS.has(tab)) {
      // The Watching filter runs in the browser, so it looks through as many events as one
      // request allows.
      page = await listEvents(
        tab,
        typeof cursor === "string" ? cursor : undefined,
        watching ? MAX_PAGE_SIZE : undefined,
      );
    }
  } catch {
    return (
      <p className="px-4 py-12 text-[15px] text-ink-2">
        Events could not be loaded. Please try again in a minute.
      </p>
    );
  }

  // Widgets other than source status have no API yet (#15): they get null and say so.
  const widgets = railWidgets({
    frequency: null,
    recentlyExploited: null,
    mostReported: null,
    sourceStatus: (
      <Suspense fallback={<p className="text-[13px] text-ink-3">Loading sources…</p>}>
        <SourceStatus />
      </Suspense>
    ),
  });

  return (
    <FeedView
      items={page.events.map(toFeedItem).map(withLogo)}
      tabs={tabs}
      tab={tab}
      watching={watching}
      view={view === "charts" ? "charts" : "posts"}
      widgets={widgets}
      olderHref={
        page.next_cursor && !watching ? feedHref({ tab, cursor: page.next_cursor }) : undefined
      }
    />
  );
}
