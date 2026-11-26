// The first page is Featured (#16): the lead story, image cards, a short list of top stories and
// the widget rail. The full feed, with its categories, is at /feed. Everything from the API is
// rendered as React text, never as HTML.
// Next.js 16 runs with cacheComponents, so the data-fetching parts sit inside <Suspense>.
import { connection } from "next/server";
import { Suspense, ViewTransition } from "react";

import { HomeSkeleton } from "@/components/bencho-pro/home-skeleton";
import { HomeView } from "@/components/feed/home-view";
import { IngestionIndicator, SourceStatus } from "@/components/ingestion-status";
import { SiteHeader } from "@/components/site/site-header";
import { railWidgets } from "@/components/widgets/rail-widgets";
import { listEvents, type EventPage } from "@/lib/api";
import { DEFAULT_TAB, toFeedItem } from "@/lib/feed";
import { withLogo } from "@/lib/logos";
import { loadWidgetFigures } from "@/lib/widgets";

export default function Home() {
  return (
    <>
      <SiteHeader
        current="featured"
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
            <Featured />
          </ViewTransition>
        </Suspense>
      </main>
    </>
  );
}

async function Featured() {
  // Always the latest events, read per request.
  await connection();
  // Started before the events are awaited, so the two load side by side; never throws.
  const figures = loadWidgetFigures();
  let page: EventPage;
  try {
    page = await listEvents(DEFAULT_TAB);
  } catch {
    return (
      <p className="py-12 text-[15px] text-ink-2">
        Events could not be loaded. Please try again in a minute.
      </p>
    );
  }

  // The figures come from the API (#15); one that cannot be loaded is null and its widget
  // shows its quiet empty state.
  const widgets = railWidgets({
    ...(await figures),
    sourceStatus: (
      <Suspense fallback={<p className="text-[13px] text-ink-3">Loading sources…</p>}>
        <SourceStatus />
      </Suspense>
    ),
  });

  return (
    <HomeView items={page.events.map(toFeedItem).map(withLogo)} widgets={widgets} />
  );
}
