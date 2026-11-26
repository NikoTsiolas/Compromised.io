// The homepage is the feed. Everything from the API is rendered as React text, never as HTML.
// Next.js 16 runs with cacheComponents, so the data-fetching parts sit inside <Suspense>.
import { Suspense, ViewTransition } from "react";

import { HomeSkeleton } from "@/components/bencho-pro/home-skeleton";
import { HomeView } from "@/components/feed/home-view";
import { IngestionIndicator, SourceStatus } from "@/components/ingestion-status";
import { SiteHeader } from "@/components/site/site-header";
import { railWidgets } from "@/components/widgets/rail-widgets";
import { listEvents, listTabs, type EventPage, type Tab } from "@/lib/api";
import { DEFAULT_TAB, toFeedItem } from "@/lib/feed";
import { withLogo } from "@/lib/logos";

export default function Home({ searchParams }: PageProps<"/">) {
  return (
    <>
      <SiteHeader
        status={
          <Suspense fallback={null}>
            <IngestionIndicator />
          </Suspense>
        }
      />
      <main className="mx-auto max-w-[1240px] px-4 pb-16 sm:px-6 lg:px-10">
        {/* The skeleton fades out as the content fades in (a Suspense reveal). */}
        <Suspense
          fallback={
            <ViewTransition exit="auto" default="none">
              <HomeSkeleton />
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

function olderHref(tab: string, cursor: string | null) {
  if (!cursor) return undefined;
  const query = new URLSearchParams();
  if (tab !== DEFAULT_TAB) query.set("tab", tab);
  query.set("cursor", cursor);
  return `/?${query}`;
}

async function Feed({
  searchParams,
}: {
  searchParams: PageProps<"/">["searchParams"];
}) {
  const { cursor, tab: requested } = await searchParams;
  let tabs: Tab[];
  let page: EventPage;
  let tab = DEFAULT_TAB;
  try {
    tabs = await listTabs();
    if (typeof requested === "string" && tabs.some((t) => t.id === requested)) {
      tab = requested;
    }
    page = await listEvents(
      tab,
      typeof cursor === "string" ? cursor : undefined,
    );
  } catch {
    return (
      <p className="py-12 text-[15px] text-ink-2">
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
    <HomeView
      items={page.events.map(toFeedItem).map(withLogo)}
      tabs={tabs}
      tab={tab}
      withFeatured={tab === DEFAULT_TAB && typeof cursor !== "string"}
      widgets={widgets}
      olderHref={olderHref(tab, page.next_cursor)}
    />
  );
}
