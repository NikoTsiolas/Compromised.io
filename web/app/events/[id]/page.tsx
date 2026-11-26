// One event's own page (#11) at /events/<id>. The id is the API's event id, stable as sources
// join the event. Proxy (proxy.ts) answers unknown ids with a 404 and the ids of events deleted by
// regrouping with a 308 before this page renders; the checks below cover the rare case where
// that changes between the two requests. Next.js 16 runs with cacheComponents, so the data
// sits inside <Suspense>. Everything from the API is rendered as React text, never as HTML.
import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";
import { Suspense, ViewTransition } from "react";

import { EventSkeleton } from "@/components/event/event-skeleton";
import { EventView } from "@/components/event/event-view";
import { IngestionIndicator } from "@/components/ingestion-status";
import { SiteHeader } from "@/components/site/site-header";
import { getEvent, type EventDetail } from "@/lib/api";
import { describeEvent, eventPath } from "@/lib/event";
import { toFeedItem } from "@/lib/feed";
import { withLogo } from "@/lib/logos";

export async function generateMetadata({
  params,
}: PageProps<"/events/[id]">): Promise<Metadata> {
  const { id } = await params;
  let event: EventDetail | null;
  try {
    event = await getEvent(id);
  } catch {
    return { title: "Compromised" };
  }
  if (!event) return { title: "Event not found · Compromised", robots: { index: false } };

  // Plain stored text only. No image: a publisher's photo is theirs to show beside their own
  // story, not ours to put on a share card.
  const description = describeEvent(event);
  return {
    title: `${event.title} · Compromised`,
    description,
    // Events outside every feed tab (commentary, out-of-scope advisories) keep their page but
    // stay out of search results, as they stay out of the feed.
    robots: event.tabs.length === 0 ? { index: false } : undefined,
    openGraph: {
      type: "article",
      siteName: "Compromised",
      title: event.title,
      description,
      publishedTime: event.published_at,
    },
    twitter: { card: "summary", title: event.title, description },
  };
}

export default function EventPage({ params }: PageProps<"/events/[id]">) {
  return (
    <>
      <SiteHeader
        status={
          <Suspense fallback={null}>
            <IngestionIndicator />
          </Suspense>
        }
      />
      <main className="mx-auto max-w-[1240px] px-4 pt-6 pb-16 sm:px-6 sm:pt-8 lg:px-10">
        {/* The skeleton fades out as the event fades in (a Suspense reveal), as on the feed. */}
        <Suspense
          fallback={
            <ViewTransition exit="auto" default="none">
              <EventSkeleton />
            </ViewTransition>
          }
        >
          <ViewTransition enter="auto" default="none">
            <EventContent params={params} />
          </ViewTransition>
        </Suspense>
      </main>
    </>
  );
}

async function EventContent({ params }: { params: PageProps<"/events/[id]">["params"] }) {
  const { id } = await params;
  let event: EventDetail | null;
  try {
    event = await getEvent(id);
  } catch {
    return (
      <p className="py-12 text-[15px] text-ink-2">
        This event could not be loaded. Please try again in a minute.
      </p>
    );
  }
  if (!event) notFound();
  if (String(event.id) !== id) permanentRedirect(eventPath(event.id));
  return <EventView item={withLogo(toFeedItem(event))} />;
}
