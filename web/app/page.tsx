// The homepage is the feed. Everything from the API is rendered as React text, never as HTML.
// Next.js 16 runs with cacheComponents, so the data-fetching part sits inside <Suspense>.
import { Suspense } from "react";

import { FeedSkeleton } from "@/components/feed/feed-skeleton";
import { FeedView } from "@/components/feed/feed-view";
import { SiteHeader } from "@/components/site/site-header";
import { listEvents, type EventPage } from "@/lib/api";
import { tabFrom, toFeedItem } from "@/lib/feed";

export default function Home({ searchParams }: PageProps<"/">) {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-[1120px] px-4 pb-16 sm:px-6 lg:px-10">
        <Suspense fallback={<FeedSkeleton />}>
          <Feed searchParams={searchParams} />
        </Suspense>
      </main>
    </>
  );
}

async function Feed({
  searchParams,
}: {
  searchParams: PageProps<"/">["searchParams"];
}) {
  const { cursor, tab } = await searchParams;
  let page: EventPage;
  try {
    page = await listEvents(typeof cursor === "string" ? cursor : undefined);
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
      tab={tabFrom(tab)}
      olderHref={
        page.next_cursor
          ? `/?cursor=${encodeURIComponent(page.next_cursor)}`
          : undefined
      }
    />
  );
}
