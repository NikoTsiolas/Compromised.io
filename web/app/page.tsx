// The homepage is the feed. Everything from the API is rendered as React text, never as HTML.
// Next.js 16 runs with cacheComponents, so the data-fetching part sits inside <Suspense>.
import { Suspense } from "react";

import { FeedSkeleton } from "@/components/feed/feed-skeleton";
import { FeedView } from "@/components/feed/feed-view";
import { IngestionIndicator, SourceHealthList } from "@/components/ingestion-status";
import { SiteHeader } from "@/components/site/site-header";
import { listEvents, listTabs, type EventPage, type Tab } from "@/lib/api";
import { DEFAULT_TAB, toFeedItem } from "@/lib/feed";

export default function Home({ searchParams }: PageProps<"/">) {
  return (
    <>
      <SiteHeader
        statusSlot={
          <Suspense fallback={null}>
            <IngestionIndicator />
          </Suspense>
        }
      />
      <main className="mx-auto max-w-[1120px] px-4 pb-16 sm:px-6 lg:px-10">
        <Suspense fallback={<FeedSkeleton />}>
          <Feed searchParams={searchParams} />
        </Suspense>
        <section aria-labelledby="sources-heading" className="mt-12">
          <h2 id="sources-heading">Sources</h2>
          <Suspense fallback={null}>
            <SourceHealthList />
          </Suspense>
        </section>
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

  return (
    <FeedView
      items={page.events.map(toFeedItem)}
      tabs={tabs}
      tab={tab}
      olderHref={olderHref(tab, page.next_cursor)}
    />
  );
}
